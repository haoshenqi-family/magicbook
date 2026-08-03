"""Shared pytest fixtures for the AI reading companion.

Strategy:
- Unit tests (crypto, providers, memory helpers) need no DB — they test pure functions.
- Model/route tests need a calibre-web app with a temp DB. We initialize the
  module-level `ub.session` and `cps.app` once per test session using a temp
  CALIBRE_DBPATH, then clean AI tables between tests for isolation.
"""
import os
import sys
import tempfile

import pytest

# Ensure the workspace root is importable
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

# ---------------------------------------------------------------------------
# Environment must be set at MODULE level, before any test module (or conftest
# itself) imports `cps`. cps/constants.py computes CONFIG_DIR from
# CALIBRE_DBPATH at import time — if a test file does `import cps.ai` at module
# scope, it triggers `import cps` before the session fixture runs, and the env
# would still be unset, pointing calibre-web at a real (non-temp) app.db.
# ---------------------------------------------------------------------------
_CFG_DIR = tempfile.mkdtemp(prefix="cw_config_")
os.environ["CALIBRE_DBPATH"] = _CFG_DIR
os.environ["FLASK_DEBUG"] = "1"
# Point AI data storage at an isolated SQLite file. create_app() calls
# load_dotenv(), which would otherwise pick up the repo's .env (MySQL) and try
# to connect in the test env. python-dotenv won't override an already-set var.
os.environ["AI_DATABASE_URL"] = "sqlite:///{0}/ai_companion.db".format(_CFG_DIR)


@pytest.fixture(scope="session")
def _app_instance(tmp_path_factory):
    """Initialize calibre-web's global app + ub.session once per session.

    Uses a temp directory (set at module level via CALIBRE_DBPATH) for the
    settings DB so we don't clobber any real config. Background threads
    (scheduler, updater) are disabled to prevent pytest from hanging on
    non-daemon threads.
    """
    # Disable APScheduler so it doesn't spawn a background thread that blocks exit
    from cps.services import background_scheduler
    background_scheduler.use_APScheduler = False

    # Disable the updater thread (also non-daemon, would block pytest exit)
    import cps
    cps.updater_thread.start = lambda: None

    # calibre-web's cli_param.init() calls argparse.parse_args() on sys.argv,
    # which conflicts with pytest's own flags (e.g. -v triggers --version).
    # Clear sys.argv to a bare program name so argparse uses all defaults.
    saved_argv = sys.argv
    sys.argv = ["cps"]
    try:
        from cps import create_app, ub
        app = create_app()
    finally:
        sys.argv = saved_argv

    # Initialize the independent AI data layer (lazy by default, but make it
    # deterministic here so seeding + cleanup always have tables available).
    from cps.ai.database import init_ai_db, remove_session
    init_ai_db()
    app.teardown_appcontext(lambda exc: remove_session())

    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    # Pretend the calibre DB is configured. The admin blueprint's
    # before_app_request redirects all requests to admin.db_configuration
    # when config.db_configured is False (which it is, since there's no
    # metadata.db in the test env).
    try:
        from cps import config as cw_config
        cw_config.db_configured = True
    except Exception:
        pass

    # Force standard (non-LDAP) login for the test env. LDAP is not part of
    # the test scope; when the simpleldap module is installed the login route
    # otherwise tries to bind against a (nonexistent) LDAP server and fails.
    try:
        from cps import constants
        cw_config.config_login_type = constants.LOGIN_STANDARD
        from cps import services
        services.ldap = None
    except Exception:
        pass

    # Register blueprints (create_app doesn't register them; main() does, but
    # we don't call main() in tests). layout.html references urls from search
    # and tasks, so we need those registered.
    from cps.web import web
    from cps.basic import basic
    from cps.jinjia import jinjia
    from cps.about import about
    from cps.search import search
    app.register_blueprint(jinjia)
    app.register_blueprint(web)
    app.register_blueprint(basic)
    app.register_blueprint(about)
    app.register_blueprint(search)
    try:
        from cps.tasks_status import tasks
        app.register_blueprint(tasks)
    except ImportError:
        pass
    try:
        from cps.admin import admi
        app.register_blueprint(admi)
    except ImportError:
        pass
    try:
        from cps.shelf import shelf
        app.register_blueprint(shelf)
    except ImportError:
        pass
    try:
        from cps.editbooks import editbook
        app.register_blueprint(editbook)
    except ImportError:
        pass
    try:
        from cps.ai.routes import aichat
        app.register_blueprint(aichat)
    except ImportError:
        pass  # cps.ai not yet created

    # AI tables are created by cps.ai.database.init_ai_db() inside create_app()
    # (they live on their own AiBase + AI_DATABASE_URL engine, not ub.Base).
    # Seed AI default config (providers + AiConfig row) if the package supports it.
    # seed_default_config() is added in a later task; guard against both
    # ImportError (package not yet present) and AttributeError (function not
    # yet defined) so early-task tests still run.
    try:
        from cps import ai
        if hasattr(ai, "seed_default_config"):
            ai.seed_default_config()
    except ImportError:
        pass
    yield app


@pytest.fixture
def app(_app_instance):
    """Per-test app fixture. Cleans AI tables before yielding for isolation."""
    # If a prior test left the sessions in a rolled-back state, recover first
    # so our cleanup queries don't themselves raise PendingRollbackError.
    try:
        from cps.ub import session as ub_session
        ub_session.rollback()
    except Exception:
        pass
    from cps.ai.database import get_session
    ai_session = get_session()
    try:
        ai_session.rollback()
    except Exception:
        pass
    try:
        from cps.ai.models import (AiConfig, AiProvider, AiConversation,
                                   AiMessage, AiUserMemory)
        # Wipe AI tables clean before each test (order matters for FK cascades)
        for model in (AiMessage, AiConversation, AiUserMemory, AiProvider):
            ai_session.query(model).delete()
        # Reset config to defaults
        cfg = ai_session.query(AiConfig).first()
        if cfg:
            cfg.enabled = False
            cfg.memory_enabled = True
            cfg.default_provider = "deepseek"
            cfg.default_model = "deepseek-chat"
            cfg.memory_extract_interval = 10
            cfg.system_prompt_extra = ""
        ai_session.commit()
    except ImportError:
        pass  # cps.ai not yet created (early in test setup)
    yield _app_instance


@pytest.fixture
def ai_session(app):
    """Direct access to the independent AI data session for assertions."""
    from cps.ai.database import get_session
    return get_session()


@pytest.fixture
def client(app):
    """Unauthenticated test client."""
    return app.test_client()


@pytest.fixture
def admin_client(app):
    """Test client logged in as the default admin user (password: admin123).

    We do NOT follow_redirects on login: calibre-web redirects to
    ``web.index`` after a successful login, and ``web.index`` queries
    ``calibre_db.session`` which is None in the test env (no calibre
    metadata.db). The login itself succeeds and sets the session cookie in
    the 302 response, so the client is authenticated for subsequent requests.
    """
    client = app.test_client()
    rv = client.post("/login",
                     data={"username": "admin", "password": "admin123"})
    assert rv.status_code == 302, f"login did not redirect: {rv.status_code}"
    # Login sets config.config_is_initial=False, which triggers save()→load(),
    # which resets db_configured to False (no metadata.db in test env).
    # Re-set it so the admin blueprint's before_app_request doesn't redirect.
    try:
        from cps import config as cw_config
        cw_config.db_configured = True
    except Exception:
        pass
    return client


@pytest.fixture
def ub_session(app):
    """Direct access to the calibre-web ub.session for DB assertions."""
    from cps.ub import session as s
    return s

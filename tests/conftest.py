"""Shared pytest fixtures for the AI reading companion.

Strategy:
- Unit tests (crypto, providers, memory helpers) need no DB — they test pure functions.
- Model/route tests need a calibre-web app with a temp DB. We initialize the
  module-level `ub.session` and `cps.app` once per test session using a temp
  CALIBRE_DBPATH, then clean AI tables between tests for isolation.
"""
import os
import sys

import pytest

# Ensure the workspace root is importable
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)


@pytest.fixture(scope="session")
def _app_instance(tmp_path_factory):
    """Initialize calibre-web's global app + ub.session once per session.

    Uses a temp directory for the settings DB so we don't clobber any real config.
    Background threads (scheduler, updater) are disabled to prevent pytest from
    hanging on non-daemon threads.
    """
    db_dir = tmp_path_factory.mktemp("cw_config")
    os.environ["CALIBRE_DBPATH"] = str(db_dir)
    os.environ["FLASK_DEBUG"] = "1"

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

    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    # Register blueprints (create_app doesn't register them; main() does, but
    # we don't call main() in tests). Register the ones needed for testing.
    from cps.web import web
    from cps.basic import basic
    from cps.jinjia import jinjia
    from cps.about import about
    app.register_blueprint(jinjia)
    app.register_blueprint(web)
    app.register_blueprint(basic)
    app.register_blueprint(about)
    try:
        from cps.ai.routes import aichat
        app.register_blueprint(aichat)
    except ImportError:
        pass  # cps.ai not yet created

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
    from cps.ub import session as ub_session
    # If a prior test left the session in a rolled-back state, recover first
    # so our cleanup queries don't themselves raise PendingRollbackError.
    try:
        ub_session.rollback()
    except Exception:
        pass
    try:
        from cps.ai.models import (AiConfig, AiProvider, AiConversation,
                                   AiMessage, AiUserMemory)
        # Wipe AI tables clean before each test (order matters for FK cascades)
        for model in (AiMessage, AiConversation, AiUserMemory, AiProvider):
            ub_session.query(model).delete()
        # Reset config to defaults
        cfg = ub_session.query(AiConfig).first()
        if cfg:
            cfg.enabled = False
            cfg.memory_enabled = True
            cfg.default_provider = "deepseek"
            cfg.default_model = "deepseek-chat"
            cfg.memory_extract_interval = 10
            cfg.system_prompt_extra = ""
        ub_session.commit()
    except ImportError:
        pass  # cps.ai not yet created (early in test setup)
    yield _app_instance


@pytest.fixture
def client(app):
    """Unauthenticated test client."""
    return app.test_client()


@pytest.fixture
def admin_client(app):
    """Test client logged in as the default admin user (password: admin123)."""
    client = app.test_client()
    rv = client.post("/login",
                     data={"name": "admin", "password": "admin123"},
                     follow_redirects=True)
    assert rv.status_code == 200, f"login failed: {rv.status_code}"
    return client


@pytest.fixture
def ub_session(app):
    """Direct access to the calibre-web ub.session for DB assertions."""
    from cps.ub import session as s
    return s

"""Independent data layer for the AI reading companion.

Why this module exists:
- The AI tables (ai_*) used to live on calibre-web's ``ub.Base`` / SQLite
  ``app.db``. The feature now requires AI data to be stored independently
  (configurable via ``AI_DATABASE_URL`` in ``.env``, e.g. MySQL), while the
  calibre library / user system stays on SQLite.
- Keeping a separate declarative base + engine means AI storage can never
  accidentally write to the calibre book DB, and can be pointed at MySQL
  without touching upstream calibre-web.

Connection resolution order:
1. ``AI_DATABASE_URL`` env var set -> use it verbatim (mysql/pymysql, sqlite).
2. Otherwise -> fall back to a dedicated SQLite file ``ai_companion.db`` next
   to calibre-web's own ``app.db`` so the app still works out of the box and
   tests/CI run without a MySQL server.
"""
import logging
import os
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

log = logging.getLogger("cps.ai.db")

# All AI models inherit this base; it is NOT calibre-web's ub.Base.
AiBase = declarative_base()

# Calibre-web ships its web server on a gevent WSGIServer (single OS thread,
# many greenlets) or tornado (synchronous WSGI). The default thread-local
# scoped_session would hand the SAME SQLAlchemy session to every concurrent
# request on the same thread — two SSE streams would share one identity map,
# and one request's teardown would close the other's in-flight session.
# Using the greenlet id as the scope keeps sessions isolated per concurrent
# request; without gevent we fall back to the default thread scope (fine for
# process-per-worker deployments).
try:  # pragma: no cover - depends on deployment extras
    import gevent
    from greenlet import getcurrent as _greenlet_current
    _SCOPEFUNC = _greenlet_current
except ImportError:  # pragma: no cover
    _SCOPEFUNC = None

_engine = None
_session_factory = None
_initialized = False
_init_lock = threading.Lock()


def _default_sqlite_url():
    """Point the fallback SQLite file next to calibre-web's app.db."""
    from cps import ub
    app_db_dir = os.path.dirname(ub.app_DB_path) if ub.app_DB_path else "."
    return "sqlite:///{0}".format(
        os.path.join(app_db_dir, "ai_companion.db"))


def _load_env():
    """Load the repo ``.env`` so ``AI_DATABASE_URL`` is honored for local runs.

    Optional dependency; container deployments inject the same vars via
    docker-compose ``env_file`` so this is only a convenience for bare-metal.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:  # pragma: no cover - python-dotenv is optional
        pass


def init_ai_db():
    """Create the engine + tables for AI data.

    Idempotent and thread-safe. Called lazily on first ``get_session()`` so the
    AI data layer needs no wiring inside calibre-web's ``create_app`` (keeping
    upstream code untouched); ``main()`` also calls it explicitly for clarity.

    If ``AI_DATABASE_URL`` is configured but the database cannot be reached we
    deliberately raise instead of silently falling back, so data never ends up
    somewhere unexpected. Without an env var we use the local SQLite fallback.
    """
    global _engine, _session_factory, _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        _load_env()

        url = os.environ.get("AI_DATABASE_URL", "").strip()
        if not url:
            url = _default_sqlite_url()
            log.info("AI_DATABASE_URL not set, using local SQLite: %s", url)

        connect_args = {}
        if url.startswith("mysql"):
            # Keep connections alive across pool recycles so a long-lived app
            # doesn't hit stale MySQL connections.
            connect_args = {"charset": "utf8mb4"}

        _engine = create_engine(url, echo=False, pool_pre_ping=True,
                                connect_args=connect_args)
        _session_factory = scoped_session(sessionmaker(bind=_engine),
                                          scopefunc=_SCOPEFUNC)
        AiBase.metadata.create_all(_engine)
        _initialized = True
        log.info("AI data layer initialized: %s", url.split("://")[0] + "://...")
        _migrate_legacy_sqlite()


def _migrate_legacy_sqlite():
    """One-time, best-effort copy of legacy ai_* rows from calibre-web's
    ``app.db`` into the new independent AI data store.

    Why: before this change the ai_* tables lived on ``ub.Base`` in the same
    SQLite ``app.db``. Upgrading to the independent store (MySQL or a fresh
    ai_companion.db) would otherwise silently orphan all existing conversations,
    messages, memories and provider API keys.

    The copy only runs when the NEW store has no conversation rows yet (so it
    never clobbers data after the user has already started using the new store)
    and the LEGACY app.db still has the tables. Failures are logged and never
    block startup.
    """
    if _engine is None:
        return
    try:
        from sqlalchemy import inspect, text as sa_text
        from cps import ub
        legacy = ub.session.get_bind()
        insp = inspect(legacy)
        ai_tables = [t for t in ("ai_config", "ai_provider", "ai_conversation",
                                 "ai_message", "ai_user_memory")
                     if insp.has_table(t)]
        if not ai_tables:
            return

        new_sess = _session_factory()
        has_data = new_sess.execute(
            sa_text("SELECT 1 FROM ai_conversation LIMIT 1")).first()
        if has_data:
            return  # new store already in use

        # Read via a dedicated connection so SQLAlchemy 1.x (Engine.execute)
        # and 2.0 (Connection.execute) both work.
        with legacy.connect() as conn:
            migrated = 0
            for table in ("ai_provider", "ai_config", "ai_conversation",
                          "ai_message", "ai_user_memory"):
                if table not in ai_tables:
                    continue
                rows = conn.execute(
                    sa_text(f"SELECT * FROM {table}")).fetchall()
                if not rows:
                    continue
                cols = list(rows[0]._mapping.keys())
                placeholders = ", ".join(f":{c}" for c in cols)
                col_list = ", ".join(cols)
                stmt = sa_text(
                    f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})")
                for row in rows:
                    new_sess.execute(stmt, dict(row._mapping))
                    migrated += 1
        new_sess.commit()
        log.info("Migrated %d legacy AI rows from app.db to the new store",
                 migrated)
    except Exception as e:  # never block startup over a best-effort migration
        log.warning("legacy AI data migration skipped: %s", e)


def get_session():
    """Return the AI scoped session.

    Lazily initializes the data layer on first use so nothing needs to wire
    this into calibre-web's ``create_app``. Raises RuntimeError only if the
    data source itself cannot be reached.
    """
    if not _initialized or _session_factory is None:
        init_ai_db()
    return _session_factory()


def remove_session():
    """Release the scoped session for the current context (thread/greenlet)."""
    if _session_factory is not None:
        _session_factory.remove()


def is_initialized():
    return _initialized

"""AI reading companion subpackage for calibre-web.

All AI-related code (providers, chat API, memory, authentik OAuth) lives here
to minimize intrusion into upstream calibre-web.

``seed_default_config()`` ensures the ``AiConfig`` and ``AiProvider`` tables
have their default rows (deepseek provider, disabled by default). It is safe
to call multiple times — it only inserts missing rows. ``ub.session`` is read
lazily so this module can be imported before ``create_app()`` runs.
"""
import json
import logging

from . import registry  # noqa: F401 — registers built-in providers on import
from .models import (AiConfig, AiProvider, AiConversation, AiMessage,
                     AiUserMemory)

log = logging.getLogger("cps.ai")


def ensure_ai_tables():
    """Create the AI tables if they don't exist yet.

    calibre-web's ``ub.init_db()`` runs ``Base.metadata.create_all(engine)``
    during ``create_app()``, but ``cps.ai.models`` is only imported *after*
    that (from ``cps/main.py``), so the AI models were not yet registered on
    ``Base.metadata`` when ``create_all`` ran. As a result the AI tables were
    never created and any query against them raised
    ``OperationalError: no such table: ...`` (this was the root cause of the
    ``/ai/admin`` 500 on production).

    This function is called at import time of ``cps.ai`` (which happens after
    ``create_app()`` in the normal ``main()`` startup path, so ``ub.session``
    is already bound to an engine). It is safe to call multiple times —
    ``create_all`` with an explicit ``tables=`` list is idempotent.
    """
    try:
        from cps.ub import session as ub_session, Base
        engine = ub_session.bind
        if engine is None:
            # Session not bound yet (imported before create_app); defer.
            return
        Base.metadata.create_all(engine, tables=[
            AiConfig.__table__,
            AiProvider.__table__,
            AiConversation.__table__,
            AiMessage.__table__,
            AiUserMemory.__table__,
        ])
    except Exception as e:
        log.warning("ensure_ai_tables failed: %s", e)


def seed_default_config():
    """Ensure the ai_config singleton and default providers exist in the DB.

    Safe to call multiple times — it only inserts missing rows. Reads
    ``cps.ub.session`` lazily so it works even when this package was imported
    before the app/session was initialized.
    """
    from cps.ub import session as ub_session
    try:
        cfg = ub_session.query(AiConfig).first()
        if cfg is None:
            cfg = AiConfig()
            ub_session.add(cfg)

        # Ensure the deepseek provider row exists
        dsp = ub_session.query(AiProvider).filter_by(provider_name="deepseek").first()
        if dsp is None:
            dsp = AiProvider()
            dsp.provider_name = "deepseek"
            dsp.display_name = "DeepSeek"
            dsp.api_base = "https://api.deepseek.com"
            dsp.api_key_encrypted = ""
            dsp.models_json = json.dumps([
                {"id": "deepseek-chat", "label": "DeepSeek Chat (V3)"},
                {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner (R1)"},
            ])
            dsp.active = True
            ub_session.add(dsp)

        ub_session.commit()
    except Exception as e:
        log.warning("seed_default_config failed: %s", e)
        try:
            ub_session.rollback()
        except Exception:
            pass


# On import: (1) make sure the AI tables exist, then (2) seed default config.
# Both are no-ops if the app/session isn't ready yet or the tables already
# exist. In the normal startup path (cps/main.py) this import happens after
# create_app(), so ub.session is bound and everything works.
ensure_ai_tables()
seed_default_config()

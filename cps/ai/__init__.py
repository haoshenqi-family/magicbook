"""AI reading companion subpackage for calibre-web.

All AI-related code (providers, chat API, memory, authentik OAuth) lives here
to minimize intrusion into upstream calibre-web.

``seed_default_config()`` ensures the ``AiConfig`` and ``AiProvider`` tables
have their default rows (deepseek provider, disabled by default). It is safe
to call multiple times — it only inserts missing rows. The AI data session is
read lazily so this module can be imported before the AI data layer initializes.
"""
import json
import logging

from . import registry  # noqa: F401 — registers built-in providers on import
from .models import (AiConfig, AiProvider, AiConversation, AiMessage,
                     AiUserMemory)  # noqa: F401

log = logging.getLogger("cps.ai")


def seed_default_config():
    """Ensure the ai_config singleton and default providers exist in the DB.

    Safe to call multiple times — it only inserts missing rows. Uses the
    independent AI data session (cps.ai.database) so AI config never touches
    calibre-web's system app.db.

    Note: on the very first import (before the AI data layer has initialized)
    this is a no-op via the guard below; it runs for real once the data layer
    is ready (see the module-level call at the bottom).
    """
    from .database import get_session
    ub_session = get_session()
    try:
        cfg = ub_session.query(AiConfig).first()
        if cfg is None:
            cfg = AiConfig()
            ub_session.add(cfg)

        # Ensure default provider rows exist (deepseek + generic openai-compatible).
        defaults = [
            {
                "provider_name": "deepseek",
                "display_name": "DeepSeek",
                "api_base": "https://api.deepseek.com",
                "models": [
                    {"id": "deepseek-chat", "label": "DeepSeek Chat (V3)"},
                    {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner (R1)"},
                ],
            },
            {
                "provider_name": "openai",
                "display_name": "OpenAI Compatible",
                "api_base": "",
                "models": [
                    {"id": "gpt-4o", "label": "GPT-4o"},
                    {"id": "gpt-4o-mini", "label": "GPT-4o mini"},
                ],
            },
        ]
        for d in defaults:
            row = ub_session.query(AiProvider).filter_by(
                provider_name=d["provider_name"]).first()
            if row is None:
                row = AiProvider()
                row.provider_name = d["provider_name"]
                row.display_name = d["display_name"]
                row.api_base = d["api_base"]
                row.api_key_encrypted = ""
                row.models_json = json.dumps(d["models"])
                row.active = True
                ub_session.add(row)

        ub_session.commit()
    except Exception as e:
        log.warning("seed_default_config failed: %s", e)
        try:
            ub_session.rollback()
        except Exception:
            pass


# On import, seed the default config. The AI tables themselves are created by
# cps.ai.database.init_ai_db() (lazy, on first get_session()) on the
# INDEPENDENT AI data store — never on calibre-web's system app.db. Seeding is
# a no-op until the data layer is ready (get_session initializes it lazily).
try:
    seed_default_config()
except Exception as e:  # pragma: no cover - data layer not ready yet
    log.debug("deferred seed_default_config: %s", e)

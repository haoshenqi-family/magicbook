"""Provider registry — maps provider names to provider classes.

The registry holds the *classes* (not instances) so callers can instantiate
with runtime config (api_base, api_key) read from the ``AiProvider`` DB row.
"""
import logging
from typing import Dict, List, Type

from .base import BaseProvider
from .deepseek import DeepSeekProvider
from .openai_compat import OpenAICompatProvider

log = logging.getLogger("cps.ai.registry")

_PROVIDER_CLASSES: Dict[str, Type[BaseProvider]] = {}


def register_provider_class(name: str, cls: Type[BaseProvider]) -> None:
    """Register a provider class under the given name."""
    _PROVIDER_CLASSES[name] = cls


def list_providers() -> List[str]:
    """Return the names of all registered provider classes."""
    return list(_PROVIDER_CLASSES.keys())


def get_provider(name: str, api_base: str, api_key: str,
                 **kwargs) -> BaseProvider:
    """Instantiate a provider by name with the given config.

    Unknown (custom) names fall back to the generic OpenAI-compatible provider,
    so an admin can register arbitrarily-named providers in the UI without
    writing a Python class for each.
    """
    cls = _PROVIDER_CLASSES.get(name)
    if cls is None:
        # Unknown/custom names are treated as OpenAI-compatible so the admin
        # can register arbitrary providers in the UI. Log so a typo'd built-in
        # name (e.g. 'deepseekk') is still discoverable in the logs.
        log.warning("unknown provider name '%s', falling back to OpenAI-compatible",
                    name)
        cls = OpenAICompatProvider
    return cls(api_base=api_base, api_key=api_key, **kwargs)


# Register built-in providers at import time
register_provider_class("deepseek", DeepSeekProvider)
register_provider_class("openai", OpenAICompatProvider)

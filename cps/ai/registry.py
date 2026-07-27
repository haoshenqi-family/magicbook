"""Provider registry — maps provider names to provider classes.

The registry holds the *classes* (not instances) so callers can instantiate
with runtime config (api_base, api_key) read from the ``AiProvider`` DB row.
"""
from typing import Dict, List, Type

from .base import BaseProvider
from .deepseek import DeepSeekProvider


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

    Raises KeyError if the name is not registered.
    """
    try:
        cls = _PROVIDER_CLASSES[name]
    except KeyError:
        raise KeyError(f"unknown provider: {name}")
    return cls(api_base=api_base, api_key=api_key, **kwargs)


# Register built-in providers at import time
register_provider_class("deepseek", DeepSeekProvider)

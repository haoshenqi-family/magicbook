"""Abstract base for AI providers and the ModelInfo dataclass.

A provider implements ``chat()`` which returns either a streaming generator
(yielding string deltas) or a full string when ``stream=False``. Providers are
registered in ``cps.ai.registry`` and instantiated from an
``cps.ai.models.AiProvider`` DB row (api_base + decrypted api_key).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, List, Dict, Union


@dataclass
class ModelInfo:
    """Metadata about a single model offered by a provider."""
    id: str
    label: str = ""
    context_window: int = 0  # 0 = unknown
    supports_streaming: bool = True


class BaseProvider(ABC):
    """Abstract AI provider. Subclasses implement the chat() call."""

    #: Whether an API key is mandatory. Set to False for providers whose
    #: endpoint needs no auth (e.g. a local OpenAI-compatible gateway like
    #: Ollama/vLLM). get_active_provider() consults this before rejecting.
    requires_key = True

    @property
    @abstractmethod
    def name(self) -> str:
        """Short provider identifier, e.g. 'deepseek'."""

    @abstractmethod
    def available_models(self) -> List[ModelInfo]:
        """Return the list of models this provider offers."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], model: str,
             stream: bool = True, **kwargs) -> Union[Generator[str, None, None], str]:
        """Send a chat completion request.

        Args:
            messages: OpenAI-format message list [{"role","content"}, ...]
            model: model id to use
            stream: if True, return a generator yielding content deltas;
                    if False, return the full response string
            **kwargs: passed through to the underlying API (e.g. temperature)

        Raises:
            RuntimeError: on HTTP errors or malformed responses.
        """

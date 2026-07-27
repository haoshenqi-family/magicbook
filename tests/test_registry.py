"""Tests for the provider registry and default config seeding."""
import json

import pytest

from cps.ai.registry import get_provider, register_provider_class, list_providers
from cps.ai.deepseek import DeepSeekProvider


class TestRegistry:
    def test_list_providers_includes_deepseek(self):
        names = list_providers()
        assert "deepseek" in names

    def test_get_provider_by_name(self):
        p = get_provider("deepseek", api_base="https://api.deepseek.com",
                         api_key="sk-test")
        assert isinstance(p, DeepSeekProvider)
        assert p.name == "deepseek"

    def test_get_unknown_provider_raises(self):
        with pytest.raises(KeyError, match="unknown"):
            get_provider("nonexistent", api_base="", api_key="")

    def test_register_custom_provider(self):
        from cps.ai.base import BaseProvider, ModelInfo

        class FakeProvider(BaseProvider):
            def __init__(self, api_base="", api_key="", **kwargs):
                self._api_base = api_base
                self._api_key = api_key
            @property
            def name(self):
                return "fake"
            def available_models(self):
                return [ModelInfo(id="fake-1", label="Fake One")]
            def chat(self, messages, model, stream=True, **kwargs):
                yield "fake reply"

        register_provider_class("fake", FakeProvider)
        try:
            assert "fake" in list_providers()
            p = get_provider("fake", api_base="", api_key="")
            assert isinstance(p, FakeProvider)
            assert p.available_models()[0].id == "fake-1"
        finally:
            # Don't leak the test provider into other tests
            from cps.ai.registry import _PROVIDER_CLASSES
            _PROVIDER_CLASSES.pop("fake", None)


class TestSeedDefaultConfig:
    def test_seed_creates_ai_config_singleton(self, app):
        from cps.ub import session
        from cps.ai.models import AiConfig
        from cps.ai import seed_default_config

        # Wipe any existing config
        session.query(AiConfig).delete()
        session.commit()

        seed_default_config()

        cfg = session.query(AiConfig).first()
        assert cfg is not None
        assert cfg.default_provider == "deepseek"
        assert cfg.default_model == "deepseek-chat"

    def test_seed_creates_deepseek_provider_row(self, app):
        from cps.ub import session
        from cps.ai.models import AiProvider
        from cps.ai import seed_default_config

        # Wipe providers
        session.query(AiProvider).delete()
        session.commit()

        seed_default_config()

        prov = session.query(AiProvider).filter_by(provider_name="deepseek").first()
        assert prov is not None
        assert prov.api_base == "https://api.deepseek.com"
        assert prov.active is True
        models = json.loads(prov.models_json)
        ids = [m["id"] for m in models]
        assert "deepseek-chat" in ids

    def test_seed_is_idempotent(self, app):
        """Running seed_default_config twice should not duplicate rows."""
        from cps.ub import session
        from cps.ai.models import AiConfig, AiProvider
        from cps.ai import seed_default_config

        session.query(AiConfig).delete()
        session.query(AiProvider).delete()
        session.commit()

        seed_default_config()
        seed_default_config()

        assert session.query(AiConfig).count() == 1
        assert session.query(AiProvider).filter_by(provider_name="deepseek").count() == 1

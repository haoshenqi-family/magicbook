"""R252：书籍详情页整本成本摘要。

Why 这里同时测纯函数与接线：金额一旦算错不会抛异常，只会静默给读者一个错误报价。
翻译按 token、TTS 按字符/缓存段，二者不能混成同一种计费；费率缺失时也不能把
“不知道”渲染成 0。
"""
import os
from types import SimpleNamespace

from jinja2 import Environment

from cps.reading_insight.cost import build_book_cost_summary

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DETAIL = os.path.join(ROOT, "cps", "templates", "detail.html")
WEB = os.path.join(ROOT, "cps", "web.py")

RATES = {
    "creditsPer1kToken": 10,
    "tts": {"enabled": True, "charsPerCredit": 50},
}
PAYLOAD = {"billableCharCount": 4001, "billableParagraphCount": 101}


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _render_cost_block(cost):
    src = _read(DETAIL)
    start = src.index("{% set _cost = entry.book_cost_summary %}")
    end = src.index("{% if entry.identifiers", start)
    template = Environment().from_string(src[start:end])
    return template.render(entry=SimpleNamespace(book_cost_summary=cost))


def test_uncached_book_shows_full_generation_costs_only():
    result = build_book_cost_summary(PAYLOAD, readiness=None, rates=RATES)

    assert result["translate"] == {
        "tokens": 1001,
        "fullCredits": 11,
        "cachedCredits": None,
        "cached": False,
    }
    assert result["tts"]["chars"] == 4001
    assert result["tts"]["segments"] == 101
    assert result["tts"]["fullCredits"] == 80
    assert result["tts"]["cachedCredits"] is None
    assert result["tts"]["cached"] is False


def test_translation_cached_reading_is_zero_plus_full_price():
    readiness = {"translate": {"ready": True, "done": 101, "total": 101}}
    result = build_book_cost_summary(PAYLOAD, readiness=readiness, rates=RATES)

    assert result["translate"]["cached"] is True
    assert result["translate"]["cachedCredits"] == 0
    assert result["translate"]["fullCredits"] == 11


def test_tts_cached_listening_is_one_credit_per_cached_segment():
    readiness = {"tts": {"ready": True, "done": 101, "total": 101}}
    result = build_book_cost_summary(PAYLOAD, readiness=readiness, rates=RATES)

    assert result["tts"]["cached"] is True
    assert result["tts"]["cachedSegments"] == 101
    assert result["tts"]["cachedCredits"] == 101
    assert result["tts"]["fullCredits"] == 80
    assert result["tts"]["segments"] == 101


def test_both_cached_keep_cached_and_original_prices_side_by_side():
    readiness = {
        "translate": {"ready": True, "done": 101, "total": 101},
        "tts": {"ready": True, "done": 101, "total": 101},
    }
    result = build_book_cost_summary(PAYLOAD, readiness=readiness, rates=RATES)

    assert (result["translate"]["cachedCredits"],
            result["translate"]["fullCredits"]) == (0, 11)
    assert (result["tts"]["cachedCredits"],
            result["tts"]["fullCredits"]) == (101, 80)


def test_rate_unavailable_keeps_scale_but_never_guesses_zero():
    result = build_book_cost_summary(PAYLOAD, readiness=None, rates=None)

    assert result["translate"]["tokens"] == 1001
    assert result["translate"]["fullCredits"] is None
    assert result["tts"]["chars"] == 4001
    assert result["tts"]["fullCredits"] is None


def test_explicit_tts_disabled_means_full_generation_is_free():
    rates = {"creditsPer1kToken": 10, "tts": {"enabled": False, "charsPerCredit": 50}}
    result = build_book_cost_summary(PAYLOAD, rates=rates)

    assert result["tts"]["fullCredits"] == 0
    assert result["tts"]["billingEnabled"] is False


def test_missing_tts_rate_is_unavailable_not_free():
    """旧版 billing 响应没有 tts 字段时，不能把全文生成误写成 0 积分。"""
    result = build_book_cost_summary(PAYLOAD, rates={"creditsPer1kToken": 10})

    assert result["tts"]["fullCredits"] is None
    assert result["tts"]["billingEnabled"] is None


def test_old_insight_snapshot_falls_back_to_raw_counts():
    result = build_book_cost_summary(
        {"charCount": 4000, "paragraphCount": 100},
        rates=RATES,
    )

    assert result["translate"]["tokens"] == 1000
    assert result["tts"]["chars"] == 4000
    assert result["tts"]["segments"] == 100


def test_detail_template_renders_cached_value_next_to_original_price():
    src = _read(DETAIL)

    assert 'id="book-cost-summary"' in src
    assert 'data-kind="translate"' in src
    assert 'data-kind="tts"' in src
    assert "约 {{ \"{:,}\".format(_cost.translate.tokens) }} tokens" in src
    assert "缓存阅读 {{ \"{:,}\".format(_cost.translate.cachedCredits) }} 积分" in src
    assert "缓存收听 {{ \"{:,}\".format(_cost.tts.cachedCredits) }} 积分" in src
    assert src.count("全文生成原价约") >= 2
    assert "TTS 不按 token" in src
    assert "约 {{ \"{:,}\".format(_cost.tts.chars) }} 字符" in src
    assert "约 {{ \"{:,}\".format(_cost.tts.segments) }} 段" in src
    assert "全文生成费率暂不可得" in src
    assert "全文生成费率暂不可得" in src


def test_cost_block_renders_cached_and_original_prices_together():
    readiness = {
        "translate": {"ready": True, "done": 101, "total": 101},
        "tts": {"ready": True, "done": 101, "total": 101},
    }
    cost = build_book_cost_summary(PAYLOAD, readiness=readiness, rates=RATES)
    html = _render_cost_block(cost)

    assert "约 1,001 tokens" in html
    assert "缓存阅读 0 积分" in html
    assert "全文生成原价约 11 积分" in html
    assert "约 4,001 字符" in html
    assert "TTS 不按 token，约 101 段" in html
    assert "缓存收听 101 积分" in html
    assert "全文生成原价约 80 积分" in html


def test_cost_block_marks_unavailable_rates_without_zero():
    cost = build_book_cost_summary(PAYLOAD, rates=None)
    html = _render_cost_block(cost)

    assert "全文生成费率暂不可得" in html
    assert "0 积分" not in html


def test_cached_translation_keeps_zero_cost_when_full_rate_is_unavailable():
    readiness = {"translate": {"ready": True, "done": 101, "total": 101}}
    cost = build_book_cost_summary(PAYLOAD, readiness=readiness, rates=None)
    html = _render_cost_block(cost)

    assert "缓存阅读 0 积分" in html
    assert "全文生成费率暂不可得" in html


def test_detail_cost_block_sits_after_cache_badges():
    src = _read(DETAIL)
    assert src.index('id="cache-ready-all"') < src.index('id="book-cost-summary"')


def test_show_book_injects_cost_summary_with_short_billing_timeout():
    src = _read(WEB)
    start = src.index("entry.book_cost_summary = None")
    block = src[start:src.index("return render_title_template", start)]

    assert "role_viewer" in block
    assert "build_book_cost_summary" in block
    assert "_credit_billing_rates(timeout=2)" in block
    assert "entry.cache_readiness" in block
    assert "find-translations" not in block
    assert "cached-check" not in block


def test_credit_billing_lookup_honors_detail_timeout(app, monkeypatch):
    import cps.web as web

    calls = []

    def fake_proxy(path, payload, timeout, label, **kwargs):
        calls.append((path, timeout))
        return '{"result":{"creditsPer1kToken":10,"tts":{"enabled":true,"charsPerCredit":50}}}', 200, {}

    old_cache = dict(web._credit_billing_cache)
    web._credit_billing_cache.update({"fetched_at": 0.0, "rates": None})
    monkeypatch.setattr(web, "_moonwell_proxy", fake_proxy)
    try:
        rates = web._credit_billing_rates(timeout=2)
        assert rates["creditsPer1kToken"] == 10
        assert calls == [("/credit/billing", 2)]
        # 5 分钟进程缓存命中后不应再次跨公网请求。
        assert web._credit_billing_rates(timeout=2) == rates
        assert calls == [("/credit/billing", 2)]
    finally:
        web._credit_billing_cache.clear()
        web._credit_billing_cache.update(old_cache)


def test_detail_template_compiles(app):
    with app.test_request_context("/book/1"):
        app.jinja_env.get_template("detail.html")

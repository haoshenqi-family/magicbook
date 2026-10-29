"""书籍详情页的整本成本摘要（R252/R253）。

Why 独立纯函数：详情页已经持有内容速览与缓存齐备快照，成本只该做算术，
不能为了显示一个数字重新解析整本 EPUB 或逐段探测 moon-well 缓存。

计费口径：
- 翻译按 token，公式与 moon-well R222 一致；
- 翻译与 TTS 的缓存复用都按 1 积分/段（R231/R213）；
- TTS 不按 token，全文生成按字符。
"""
import math

CHARS_PER_TOKEN = 4
# moon-well R213/R231 固定缓存复用规则：翻译与收听命中都收 1 积分/段。
TRANSLATION_CACHED_CREDITS_PER_SEGMENT = 1
TTS_CACHED_LISTEN_CREDITS = 1


def _as_int(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _token_credits(tokens, rates):
    if not isinstance(rates, dict):
        return None
    per1k = _as_int(rates.get("creditsPer1kToken"))
    if per1k <= 0:
        return None
    # R222：按实际用量比例计费，向上取整到 1 积分；不再“不足千按千”。
    return int(math.ceil(tokens * per1k / 1000.0))


def _tts_full_credits(chars, rates):
    if not isinstance(rates, dict):
        return None, None
    tts = rates.get("tts")
    if not isinstance(tts, dict) or "enabled" not in tts:
        # 旧版/不完整的 billing 响应不能伪装成“TTS 免费”。
        return None, None
    if not tts.get("enabled"):
        return 0, False
    per_credit = _as_int(tts.get("charsPerCredit"))
    if per_credit <= 0:
        return None, None
    return chars // per_credit, True


def build_book_cost_summary(payload, readiness=None, rates=None):
    """返回详情页成本摘要；积分不可得时保留规模数字并置 null。

    `payload` 是 `book_insight` 的快照。旧快照没有去重字段时回退到全书统计，
    保证升级后已有书也能立即显示，不因 schema 差异报错。
    """
    payload = payload or {}
    readiness = readiness or {}
    chars = _as_int(payload.get("billableCharCount") or payload.get("charCount"))
    tokens = int(math.ceil(chars / float(CHARS_PER_TOKEN))) if chars else 0
    tts_readiness = readiness.get("tts") or {}
    tts_ready = bool(tts_readiness.get("ready"))
    tts_cached_segments = _as_int(tts_readiness.get("total")) if tts_ready else 0
    segments = _as_int(
        tts_cached_segments
        or payload.get("billableParagraphCount")
        or payload.get("paragraphCount")
    )

    translate_readiness = readiness.get("translate") or {}
    translate_ready = bool(translate_readiness.get("ready"))
    translate_cached_segments = (
        _as_int(translate_readiness.get("total")) if translate_ready else 0
    )
    tts_full, tts_billing_enabled = _tts_full_credits(chars, rates)

    return {
        "translate": {
            "tokens": tokens,
            "fullCredits": _token_credits(tokens, rates),
            "cachedCredits": (
                translate_cached_segments * TRANSLATION_CACHED_CREDITS_PER_SEGMENT
                if translate_ready else None
            ),
            "cached": translate_ready,
            "cachedSegments": translate_cached_segments,
            "cachedPerSegment": TRANSLATION_CACHED_CREDITS_PER_SEGMENT,
        },
        "tts": {
            "chars": chars,
            "segments": segments,
            "fullCredits": tts_full,
            "cachedCredits": (tts_cached_segments * TTS_CACHED_LISTEN_CREDITS
                              if tts_ready else None),
            "cached": tts_ready,
            "cachedSegments": tts_cached_segments,
            "cachedPerSegment": TTS_CACHED_LISTEN_CREDITS,
            "billingEnabled": tts_billing_enabled,
        },
    }

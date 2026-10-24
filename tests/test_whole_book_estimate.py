"""R214 C：整本任务代价估算（cps/reading_insight/service.estimate）单测。

Why 每个分支都要钉：「约 N 积分 / 约 X 小时」是管理员决定是否下单的唯一依据，算错就是
错误结论；而「取不到就显示 0」会把「查不到」伪装成「已经翻完」，正是 LLD §8 禁止的
静默降级。反向变异示例：去掉 text_hash 去重 → billable 变 3（本该 2）；
lookup 异常改成返回 cached=0 → test_lookup_failure_never_reports_zero 报红。
"""
import pytest

from cps.reading_insight import service as svc

PARAGRAPHS = [
    ("Chapter 1", "Hello world."),
    ("Chapter 1", "Hello world."),          # 重复段落：两条链路的台账都按 text_hash 唯一
    ("Chapter 2", "Second paragraph here."),
]
UNIQUE_CHARS = len("Hello world.") + len("Second paragraph here.")   # 34

RATES = {"creditsPer1kToken": 10, "tts": {"enabled": True, "charsPerCredit": 10}}


def _patch(monkeypatch, *, paragraphs=None, history=(None, 0), rates=True, active=None):
    paragraphs = PARAGRAPHS if paragraphs is None else paragraphs
    monkeypatch.setattr(svc, "get_or_build", lambda book_id, book_format: {
        "chapters": [{"title": "Chapter 1"}, {"title": "Chapter 2"}],
        "paragraphCount": 3, "charCount": 50, "englishWordCount": 8,
        "aiSummary": None,
    })
    monkeypatch.setattr(svc, "_book_file",
                        lambda book_id, book_format: (object(), "/tmp/does-not-matter.epub"))
    import cps.reading_translation.parser as job_parser
    monkeypatch.setattr(job_parser, "extract_epub_paragraphs",
                        lambda path: list(paragraphs))
    monkeypatch.setattr(svc, "active_jobs", lambda book_id, book_format: active or {})
    monkeypatch.setattr(svc, "_history_rate", lambda kind: history)
    if rates is not None:
        monkeypatch.setattr(svc, "_estimate_credits",
                            _wrap_credits(svc._estimate_credits, RATES))
    return paragraphs


def _wrap_credits(original, rates):
    """把费率注入 _estimate_credits（正常路径由路由层从 /credit/billing 取）。"""
    def inner(kind, *, chars, words, rates=None, coverage_known=False):
        return original(kind, chars=chars, words=words, rates=rates_holder[0],
                        coverage_known=coverage_known)
    rates_holder = [rates]
    return inner


def test_translate_estimate_dedups_and_reports_coverage(monkeypatch):
    """去重后 2 段、命中 1 段 → 只剩 1 段要处理；积分按未缓存段字符算。"""
    _patch(monkeypatch)
    lookup = lambda texts: {texts[0]: "你好世界。"}   # 只有第一段有缓存
    result = svc.estimate(337, "epub", "translate", lookup=lookup, rates=None)

    assert result["kind"] == "translate"
    assert result["mutatesOriginal"] is False
    assert result["units"]["billable"] == 2, "重复段落被算了两遍"
    assert result["units"]["paragraphs"] == 3
    assert result["coverage"] == {"known": True, "cached": 1, "total": 2}
    # 只剩 "Second paragraph here." 22 字 → tokens 5.5 → 1k 一档 → 10 积分
    assert result["credits"]["estimated"] == 10
    assert result["credits"]["upperBound"] == 11
    assert result["duration"] == {"known": True, "basis": "constant", "samples": 0,
                                  "seconds": 10}, "常量兜底 10s/段 × 剩 1 段"


def test_tts_never_probes_coverage(monkeypatch):
    """拍板③：朗读不做缓存探针，coverage 固定 known=false 且给出原因。"""
    _patch(monkeypatch)
    called = {"lookup": 0}
    result = svc.estimate(337, "epub", "tts",
                          lookup=lambda texts: called.__setitem__("lookup", called["lookup"] + 1) or {},
                          rates=None)
    assert called["lookup"] == 0, "朗读链路不该调翻译缓存查询"
    assert result["coverage"] == {"known": False, "reason": "tts-cache-not-batchable"}
    # 34 字 / 每 10 字 1 积分 = 3（向下取整，全 miss 上限）
    assert result["credits"]["estimated"] == 3
    assert result["credits"]["upperBound"] == 3
    assert result["duration"]["seconds"] == 6, "3.0s/段 × 去重后 2 段"


def test_word_detail_uses_cached_check_only(monkeypatch):
    """详解覆盖率只走 cached-check；5 个去重词命中 2 → 需生成 3。"""
    _patch(monkeypatch)
    probes = []

    def check(words):
        probes.append(list(words))
        return {"requested": len(words), "cached": 2, "missing": words[2:], "notWordLike": []}

    result = svc.estimate(337, "epub", "wordDetail", check=check, rates=None)
    assert probes, "cached-check 没被调用"
    assert result["units"]["billable"] == 5
    assert result["coverage"] == {"known": True, "cached": 2, "total": 5}
    # 3 词 × 4000 token = 12000 → ceil(12) × 10 = 120
    assert result["credits"]["estimated"] == 120
    assert result["credits"]["upperBound"] == 132
    # 详解没有实测常量：宁可不给数字，也不编一个
    assert result["duration"]["known"] is False
    assert result["duration"]["reason"] == "no-history"


def test_lookup_failure_never_reports_zero(monkeypatch):
    """缓存查询失败 → coverage.known=false（不许显示 0），积分标成全书上界。"""
    _patch(monkeypatch)

    def boom(texts):
        raise RuntimeError("moon-well down")

    result = svc.estimate(337, "epub", "translate", lookup=boom, rates=None)
    assert result["coverage"] == {"known": False, "reason": "cache-lookup-unavailable"}
    assert result["credits"]["reason"] == "full-text-upper-bound"


def test_rate_unavailable_is_explicit(monkeypatch):
    """费率取不到 → credits.known=false（不显示猜测数字），规模与耗时照常给。"""
    _patch(monkeypatch, rates=None)
    result = svc.estimate(337, "epub", "translate", lookup=lambda texts: {}, rates=None)
    assert result["credits"] == {"known": False, "reason": "rate-unavailable"}
    assert result["units"]["billable"] == 2


def test_tts_not_billed_is_its_own_reason(monkeypatch):
    """TTS 关闭计费时给专属原因，不与「费率不可得」混为一谈。"""
    _patch(monkeypatch, rates=None)
    result = svc.estimate(337, "epub", "tts", rates={"creditsPer1kToken": 10,
                                                      "tts": {"enabled": False,
                                                              "charsPerCredit": 10}})
    assert result["credits"] == {"known": False, "reason": "tts-not-billed"}


def test_history_rate_beats_constant(monkeypatch):
    """有历史中位数就用历史，并回传样本数（面板要写「基于最近 N 个批次」）。"""
    _patch(monkeypatch, history=(4.0, 7))
    result = svc.estimate(337, "epub", "translate", lookup=lambda texts: {}, rates=None)
    assert result["duration"] == {"known": True, "basis": "history", "samples": 7,
                                  "seconds": 8}, "4.0s/段 × 剩 2 段"


def test_active_job_snapshot_is_passed_through(monkeypatch):
    """页面据此直接进进度态（LLD §7.5）——快照必须原样透传。"""
    active = {"translate": {"jobId": "j1", "status": "RUNNING", "total": 10, "done": 4}}
    _patch(monkeypatch, active=active)
    result = svc.estimate(337, "epub", "translate", lookup=lambda texts: {}, rates=None)
    assert result["activeJobs"] == active


def test_unsupported_kind_raises():
    with pytest.raises(ValueError):
        svc.estimate(337, "epub", "music")


def test_empty_paragraphs_raises(monkeypatch):
    _patch(monkeypatch, paragraphs=[])
    with pytest.raises(ValueError):
        svc.estimate(337, "epub", "translate", lookup=lambda texts: {})


def test_history_rate_swallows_query_errors(app, monkeypatch):
    """台账查询失败只该退化成「没有实测样本」，不该把整个估算打成 500。

    反向变异：去掉 _history_rate 里的 try/except → 本测试抛 RuntimeError。
    """
    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(svc.ub.session, "query", boom)
    assert svc._history_rate("translate") == (None, 0)


def test_active_jobs_swallows_query_errors(app, monkeypatch):
    """活跃批次快照是锦上添花：查不到就当没有，不能让面板整块挂掉。"""
    import cps.cw_login as cw_login

    class _User(object):
        id = 7

    monkeypatch.setattr(svc, "_book_file", lambda *a: (object(), "/tmp/x.epub"))
    monkeypatch.setattr(svc, "_fingerprint", lambda path: "fp")
    monkeypatch.setattr(cw_login, "current_user", _User())

    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(svc.ub.session, "query", boom)
    assert svc.active_jobs(1, "epub") == {"translate": None, "tts": None, "wordDetail": None}

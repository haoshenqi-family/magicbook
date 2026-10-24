# cps/reading_insight/service.py — R214 B：内容速览缓存 + AI 简介生成（LLD §2/§4）。
#
# Why 缓存表：详情页高频、EPUB 解析 O(全书)；(book_id, book_format) 唯一，
# fingerprint 失效自动重建（LLD §2）。
# Why AI 简介走 moon-well 的 book-intro ability（按正文入参、不吃 moon-well bookId）：
# 本仓 AI 对话通道已退役（/ai/chat 全 410），且两侧 bookId 不同源（R197/R200 踩过），
# 跨仓契约见 moon-well R207。上游不可用时失败可见透传，不静默变「暂无简介」（LLD §8）。
import json
import math
import statistics

from .. import calibre_db, logger, ub
from ..reading_job.service_base import ACTIVE_STATUSES, JobServiceBase
from ..reading_translation.timeutil import as_utc, now_utc
from . import parser as insight_parser
from .models import BookInsight

log = logger.create()

SCHEMA_VERSION = 1


def _ensure_tables():
    # 懒建（reading_job/service_base.py:73 同款）：app.db 由运行环境持有，不进版本库。
    bind = ub.session.get_bind()
    ub.Base.metadata.create_all(bind, tables=[BookInsight.__table__])


def _book_file(book_id, book_format):
    # 复用 job 基类的正文定位/指纹原语（LLD §2）：缓存键必须与三个 job 的
    # 「同一本书同一格式」口径逐字一致，否则两套指纹会对不上。_book_file 不触碰
    # 实例状态，以未绑定函数调用；_fingerprint 本就是 staticmethod。
    return JobServiceBase._book_file(None, book_id, book_format)


def _fingerprint(path):
    return JobServiceBase._fingerprint(path)


def _find_row(book_id, book_format):
    return (ub.session.query(BookInsight)
            .filter(BookInsight.book_id == int(book_id),
                    BookInsight.book_format == book_format)
            .first())


def _payload_of(row):
    payload = json.loads(row.payload_json)
    payload.setdefault("aiSummary", None)
    payload["builtAt"] = int(row.built_at.timestamp()) if row.built_at else None
    return payload


def get_or_build(book_id, book_format):
    """速览 payload：fingerprint 命中直接回缓存，否则解析重建并覆盖写。"""
    book_id = int(book_id)
    book_format = (book_format or "epub").lower()
    _book, path = _book_file(book_id, book_format)
    fingerprint = _fingerprint(path)
    _ensure_tables()
    row = _find_row(book_id, book_format)
    if row and row.fingerprint == fingerprint and row.last_error is None:
        payload = _payload_of(row)
        payload["bookId"] = book_id
        payload["bookFormat"] = book_format
        payload["fingerprint"] = fingerprint
        return payload

    try:
        payload = insight_parser.parse(path)
    except Exception as error:
        # 失败可见（LLD §8）：last_error 落库便于排查，向上传「解析失败: 原文」。
        if row is not None:
            row.last_error = str(error)
            ub.session.commit()
        raise ValueError("内容速览解析失败: %s" % error)

    # 正文指纹变化但管理员生成过简介 → 保留 aiSummary（拍板⑦无「重新生成」按钮，
    # 丢掉就再也拿不回来；简介以书目元数据+首章为主，正文小改不动摇它）。
    if row is not None:
        try:
            old = json.loads(row.payload_json)
            if old.get("aiSummary"):
                payload["aiSummary"] = old["aiSummary"]
        except (TypeError, ValueError):
            pass

    payload.setdefault("aiSummary", None)
    payload["bookId"] = book_id
    payload["bookFormat"] = book_format
    payload["fingerprint"] = fingerprint
    payload["builtAt"] = int(now_utc().timestamp())

    if row is None:
        row = BookInsight(book_id=book_id, book_format=book_format)
        ub.session.add(row)
    row.fingerprint = fingerprint
    row.payload_json = json.dumps(payload, ensure_ascii=False)
    row.schema_version = SCHEMA_VERSION
    row.built_at = now_utc()
    row.last_error = None
    ub.session.commit()
    return payload


def _save_ai_summary(book_id, book_format, ai_summary):
    """只 UPDATE payload_json 里的 aiSummary 键（LLD §2），不动其余内容。"""
    row = _find_row(book_id, book_format)
    if row is None:
        raise ValueError("book insight is unavailable")
    payload = json.loads(row.payload_json)
    payload["aiSummary"] = ai_summary
    row.payload_json = json.dumps(payload, ensure_ascii=False)
    ub.session.commit()


def _unwrap_result(response, label):
    """解 moon-well Result 包装取 result；失败抛带上游原文案的 ValueError。

    与 web._word_detail_unwrap 同一形态契约（三元组响应、透传 message）——
    接口故障若被降级成「没生成出来」，页面就把故障显示成「暂无简介」，
    用户报回来的永远是错误结论（LLD §8：禁止静默降级）。
    """
    if not isinstance(response, tuple) or len(response) < 2:
        raise ValueError("%s service unavailable" % label)
    body, status = response[0], response[1]
    try:
        data = json.loads(body)
    except (TypeError, ValueError):
        raise ValueError("%s returned unreadable response" % label)
    message = data.get("message") if isinstance(data, dict) else None
    if status >= 400 or (isinstance(data, dict) and data.get("success") is False):
        raise ValueError(message or "%s failed (HTTP %s)" % (label, status))
    result = data.get("result") if isinstance(data, dict) else None
    return result or {}


def generate_summary(book_id, book_format):
    """管理员触发的 AI 简介（拍板④不自动跑；拍板⑦已生成即定稿、无「重新生成」）。"""
    book_id = int(book_id)
    book_format = (book_format or "epub").lower()
    payload = get_or_build(book_id, book_format)
    if payload.get("aiSummary"):
        return payload["aiSummary"]

    book, _path = _book_file(book_id, book_format)
    authors = " & ".join(a.name for a in (book.authors or []))
    series = book.series[0].name if book.series else ""
    excerpt_text = "\n\n".join(e["text"] for e in payload.get("excerpt") or [])
    context = {
        "title": book.title or "",
        "author": authors,
        "series": series,
        "toc": [ch["title"] for ch in payload.get("chapters") or []],
        "excerpt": excerpt_text[:insight_parser.EXCERPT_MAX_CHARS],
    }

    # 延迟导入：web 模块加载末尾才挂路由，模块级互引会成环。
    from cps.web import _moonwell_proxy
    response = _moonwell_proxy("/book/ai/ability/book-intro", context, 60, "book intro")
    result = _unwrap_result(response, "book-intro")
    text = (result.get("content") or result.get("text") or "").strip()
    if not text:
        raise ValueError("book-intro returned empty content")
    ai_summary = {
        "text": text,
        "model": result.get("model") or "",
        "generatedAt": int(now_utc().timestamp()),
    }
    _save_ai_summary(book_id, book_format, ai_summary)
    return ai_summary


# ---------------------------------------------------------------------------
# 子项 C：整本任务代价估算（LLD §5）
#
# Why 只读：estimate 绝不建批次、不 publish、不写缓存——面板是「先预案后执行」里的
# 预案（R176 preview 同源纪律）。探进度若变成下单，管理员看到的第一个数字就是账单。
# Why 依赖注入 lookup/check/rates：三个闭包都要在请求线程内定格 moon-well 令牌
# （后台线程无 Flask 上下文，R75 的实踩形态），service 因此不认识 HTTP。
# ---------------------------------------------------------------------------

ESTIMATE_KINDS = ("translate", "tts", "wordDetail")

# LLD §5.2 常量兜底（秒/单位）。详解没有经过实测的常量，宁可不给数字也不编一个。
DURATION_FALLBACK_SECONDS = {"translate": 10.0, "tts": 3.0}
DURATION_SAMPLE_LIMIT = 20
DURATION_MIN_UNITS = 30
DURATION_MIN_SAMPLES = 3
# LLD §5.3 粗算口径：chars/4 → token；详解单词 token 当量沿用 R176 预览页现值。
CHARS_PER_TOKEN = 4
TOKENS_PER_WORD_DETAIL = 4000
UPPER_BOUND_FACTOR = 1.1
# 与 reading_translation/service.py 的进度回收同口径（每批 200 段）：一次性把整本书
# 塞进单次 find-translations 会造出 MB 级请求体，20s 超时后接口整体 503。
COVERAGE_CHUNK = 200

_DURATION_SPEC = {
    # kind: (单位计数字段, 进度已完成字段)
    "translate": ("published_count", "completed_count"),
    "tts": ("done_count", "done_count"),
    "wordDetail": ("published_words", "covered_words"),
}


def _job_models():
    """延迟导入三张台账模型：模块级导入会把三条链路全拖进 reading_insight 的命名空间。"""
    from ..reading_translation.models import TranslationJob
    from ..reading_tts.models import ReadingTtsJob
    from ..reading_word_detail.models import WordDetailJob
    return {"translate": TranslationJob, "tts": ReadingTtsJob, "wordDetail": WordDetailJob}


def _dedup_texts(paragraphs):
    """按 text_hash 去重后的段落文本（整本翻译/朗读的真实计费单位）。

    Why 必须去重：两条链路的台账都按 text_hash 唯一（TranslationJobItem 的 unique 字典、
    ReadingTtsJobItem 的 uq(job_id,text_hash)）。拿全书段落数当工作量会把重复段落算两遍，
    耗时与积分一起虚高。
    """
    from ..reading_translation.parser import text_hash

    seen, texts = set(), []
    for _chapter, text in paragraphs:
        digest = text_hash(text)
        if digest in seen:
            continue
        seen.add(digest)
        texts.append(text)
    return texts


def _distinct_words(paragraphs):
    """去重词表（小写），与 reading_word_detail/service.py 的 distinct_words 逐字同口径。"""
    seen, words = set(), []
    for _chapter, text in paragraphs:
        for match in insight_parser.WORD_RE.findall(text or ""):
            key = match.lower()
            if key in seen:
                continue
            seen.add(key)
            words.append(key)
    return words


def _history_rate(kind):
    """最近完成批次的「秒/单位」中位数；样本不足回 None（LLD §5.2）。

    Why 量级过滤：3 段的小批次里固定开销（解压、建连）占九成，能把中位数带偏一个量级。
    """
    models = _job_models()
    model = models[kind]
    unit_field = _DURATION_SPEC[kind][0]
    try:
        rows = (ub.session.query(model)
                .filter(model.status == "COMPLETED")
                .order_by(model.created_at.desc())
                .limit(DURATION_SAMPLE_LIMIT).all())
    except Exception as error:
        # Why 不冒泡：这是「样本」不是「结论」——台账查不到（表缺失/库忙）只该退化成
        # 「没有实测样本」，不该让整个估算 500。R214 验收实测：一条后台查询把面板打死，
        # 管理员看到的是「估算失败 500」，而不是「耗时按常量估算」。
        log.warning("whole-book estimate: history sampling failed for %s: %s", kind, error)
        return None, 0
    samples = []
    for row in rows:
        units = int(getattr(row, unit_field) or 0)
        if units < DURATION_MIN_UNITS:
            continue
        elapsed = (as_utc(row.updated_at) - as_utc(row.created_at)).total_seconds()
        if elapsed > 0:
            samples.append(elapsed / units)
    if len(samples) < DURATION_MIN_SAMPLES:
        return None, len(samples)
    return statistics.median(samples), len(samples)


def _translate_coverage(texts, lookup):
    """翻译覆盖率：返回 (coverage, 未缓存字符数)。失败按 known=false 上交，不报 0。"""
    if lookup is None:
        return {"known": False, "reason": "cache-lookup-unavailable"}, sum(len(t) for t in texts)
    cached, miss_chars = 0, 0
    for start in range(0, len(texts), COVERAGE_CHUNK):
        chunk = texts[start:start + COVERAGE_CHUNK]
        try:
            found = lookup(chunk) or {}
        except Exception as error:
            # 纪律：查不到就说查不到（LLD §8），显示 0 会让管理员以为全书都还没翻。
            log.warning("whole-book estimate: translation cache lookup failed: %s", error)
            return ({"known": False, "reason": "cache-lookup-unavailable"},
                    sum(len(t) for t in texts))
        for text in chunk:
            if found.get(text):
                cached += 1
            else:
                miss_chars += len(text)
    return {"known": True, "cached": cached, "total": len(texts)}, miss_chars


def _word_detail_coverage(words, check):
    """详解覆盖率：只走 cached-check（**不是** GET /vocabulary/detail/{word}）。

    Why: 后者 miss 时现场生成并计费，用它探进度等于把「查进度」变成「下单」
    （reading_word_detail/service.py preview 的同一条边界）。
    """
    if check is None:
        return {"known": False, "reason": "cache-lookup-unavailable"}
    cached = 0
    for start in range(0, len(words), COVERAGE_CHUNK):
        chunk = words[start:start + COVERAGE_CHUNK]
        try:
            probe = check(chunk) or {}
        except Exception as error:
            log.warning("whole-book estimate: word detail cached-check failed: %s", error)
            return {"known": False, "reason": "cache-lookup-unavailable"}
        cached += int(probe.get("cached") or 0)
    return {"known": True, "cached": min(cached, len(words)), "total": len(words)}


def _estimate_duration(kind, units):
    """耗时估算：历史中位数优先，其次 LLD §5.2 常量，都没有就明说不知道。"""
    rate, samples = _history_rate(kind)
    if rate is not None:
        return {"known": True, "basis": "history", "samples": samples,
                "seconds": int(round(rate * units))}
    fallback = DURATION_FALLBACK_SECONDS.get(kind)
    if fallback is None:
        return {"known": False, "basis": None, "samples": samples, "seconds": None,
                "reason": "no-history"}
    return {"known": True, "basis": "constant", "samples": samples,
            "seconds": int(round(fallback * units))}


def _estimate_credits(kind, chars, words, rates, coverage_known):
    """积分粗算（LLD §5.3）；费率由 moon-well /credit/billing 回传，本仓不镜像常量。"""
    if not rates:
        return {"known": False, "reason": "rate-unavailable"}
    if kind == "tts":
        tts = rates.get("tts") or {}
        if not tts.get("enabled"):
            return {"known": False, "reason": "tts-not-billed"}
        per_credit = int(tts.get("charsPerCredit") or 0)
        if per_credit <= 0:
            return {"known": False, "reason": "rate-unavailable"}
        estimated = chars // per_credit
        return {"known": True, "estimated": estimated, "upperBound": estimated,
                "rate": {"charsPerCredit": per_credit}}
    per1k = rates.get("creditsPer1kToken")
    if not per1k:
        return {"known": False, "reason": "rate-unavailable"}
    tokens = words * TOKENS_PER_WORD_DETAIL if kind == "wordDetail" else chars / CHARS_PER_TOKEN
    estimated = int(math.ceil(tokens / 1000.0) * per1k)
    result = {"known": True, "estimated": estimated,
              "upperBound": int(math.ceil(estimated * UPPER_BOUND_FACTOR)),
              "rate": {"per1kToken": per1k}}
    if not coverage_known:
        # 覆盖率未知时只能按全书算，告诉前端这是上界而不是「预计」。
        result["reason"] = "full-text-upper-bound"
    return result


def active_jobs(book_id, book_format):
    """三种整本链路的未终态批次快照（LLD §7.5：有活跃批次直接进进度态）。"""
    book_format = (book_format or "epub").lower()
    try:
        _book, path = _book_file(book_id, book_format)
        fingerprint = _fingerprint(path)
    except Exception:
        return {}
    # 延迟导入：cw_login 在请求线程外取 current_user 会抛 RuntimeError。
    from ..cw_login import current_user

    user_id = getattr(current_user, "id", None)
    if user_id is None:
        return {}
    models = _job_models()
    snapshot = {}
    for kind, model in models.items():
        try:
            job = (ub.session.query(model)
                   .filter(model.user_id == user_id,
                           model.book_id == int(book_id),
                           model.book_fingerprint == fingerprint,
                           model.status.in_(ACTIVE_STATUSES))
                   .order_by(model.created_at.desc()).first())
        except Exception as error:
            # 同 _history_rate：活跃快照是「锦上添花」，查不到就当没有，
            # 不能因为它把「代价面板」整块打成 500。
            log.warning("whole-book estimate: active job lookup failed for %s: %s", kind, error)
            snapshot[kind] = None
            continue
        if job is None:
            snapshot[kind] = None
            continue
        total_field, done_field = ("total_count", _DURATION_SPEC[kind][1])
        if kind == "wordDetail":
            total_field = "target_words"
        snapshot[kind] = {"jobId": job.id, "status": job.status,
                          "total": int(getattr(job, total_field) or 0),
                          "done": int(getattr(job, done_field) or 0)}
    return snapshot


def estimate(book_id, book_format, kind, lookup=None, check=None, rates=None):
    """整本任务代价面板的数据源（LLD §4.3 / §5）。

    返回的每个分支都自带 `known`：前端遇到 known=false 只显示灰色说明句，
    绝不显示 0 或占位数字（「不显示猜测数字」是这一块的核心口径）。
    """
    kind = str(kind or "translate")
    if kind not in ESTIMATE_KINDS:
        raise ValueError("unsupported estimate kind: %s" % kind)
    book_id = int(book_id)
    book_format = (book_format or "epub").lower()

    payload = get_or_build(book_id, book_format)
    _book, path = _book_file(book_id, book_format)
    from ..reading_translation.parser import extract_epub_paragraphs

    paragraphs = extract_epub_paragraphs(path)
    if not paragraphs:
        raise ValueError("no translatable paragraphs found")

    units = {
        "chapters": len(payload.get("chapters") or []),
        "paragraphs": int(payload.get("paragraphCount") or 0),
        "chars": int(payload.get("charCount") or 0),
        "englishWords": int(payload.get("englishWordCount") or 0),
    }

    if kind == "wordDetail":
        targets = _distinct_words(paragraphs)
        units["billable"] = len(targets)
        coverage = _word_detail_coverage(targets, check)
        remaining_words = len(targets)
        if coverage.get("known"):
            remaining_words = max(0, len(targets) - int(coverage.get("cached") or 0))
        credits = _estimate_credits(kind, chars=0, words=remaining_words,
                                    rates=rates, coverage_known=bool(coverage.get("known")))
        duration = _estimate_duration(kind, remaining_words)
    else:
        texts = _dedup_texts(paragraphs)
        unique_chars = sum(len(t) for t in texts)
        units["billable"] = len(texts)
        if kind == "translate":
            coverage, miss_chars = _translate_coverage(texts, lookup)
            remaining = len(texts)
            if coverage.get("known"):
                remaining = max(0, len(texts) - int(coverage.get("cached") or 0))
            credits = _estimate_credits(kind, chars=miss_chars, words=0, rates=rates,
                                        coverage_known=bool(coverage.get("known")))
            duration = _estimate_duration(kind, remaining)
        else:
            # 拍板③：朗读不查缓存覆盖率（命中与否都要合成，且不算缓存探针）。
            coverage = {"known": False, "reason": "tts-cache-not-batchable"}
            credits = _estimate_credits(kind, chars=unique_chars, words=0, rates=rates,
                                        coverage_known=False)
            duration = _estimate_duration(kind, len(texts))

    return {"kind": kind, "units": units, "mutatesOriginal": False,
            "coverage": coverage, "duration": duration, "credits": credits,
            "activeJobs": active_jobs(book_id, book_format)}

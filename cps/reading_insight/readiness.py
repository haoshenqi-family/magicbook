# cps/reading_insight/readiness.py — 整本能力缓存齐备标识（R241）
#
# Why（业务意图）：整本翻译、整本朗读、全文单词详解三条链路的产物都落在 moon-well
# 的永久缓存里（译文/音频按段落、详解按词）。一本书三项缓存都备齐时，读者翻译与
# 查词几乎零成本、朗读也只按「缓存命中 1 积分/段」计——这正是「这本书可以便宜地
# 学」的信号，应当让读者在书页上直接看见，而不是自己去点三个整本任务试。
#
# Why 判定走本仓台账而不是实时探上游缓存：书页是高频读路径，整本探测要解析整本
# EPUB 再分批扫三层缓存（R214 代价面板正因如此才做成按需、R238 又为它加了后台
# 快照）。三条链路各自的批次表本来就是「这本书这一版正文跑到 100% 且没有失败」的
# 执行台账，对它做一次本地查询即可零上游调用、零额外解析地把标识秒出来。
# 代价是「缓存事后被上游清掉」时标识会滞后——缓存本身是加速器（moon-well 段落缓存
# 的降级口径），真正开跑仍以缓存实况为准；本标识只承诺「跑过且跑满了」，不承诺
# 「此刻逐段探测过」。
#
# 边界（与 R214 LLD §8「失败可见」同源）：查询失败不外抛、不把书页打成 500，
# 只把该书对应项降级为「未备齐」；台账表不存在（新库、从未跑过整本任务）同理。
from sqlalchemy import func

from .. import logger
from .service import _book_file, _fingerprint, _job_models

log = logger.create()

KINDS = ("translate", "tts", "wordDetail")
# 单书历史批次数（force 重跑/换用户重跑）通常个位数；给个上限只为防脏数据把整表拉出来。
ROW_LIMIT = 50


def _counts(kind, row):
    """(已完成, 总量) —— 三条链路的「完成」字段各不相同（见 LLD §3）。

    Why 不是统一的 done/total：整本翻译记 completed_count（缓存命中直接置 COMPLETED）、
    整本朗读记 done_count、全文详解记 covered_words（含首批就命中的词）。
    """
    if kind == "translate":
        return int(row.completed_count or 0), int(row.total_count or 0)
    if kind == "tts":
        return int(row.done_count or 0), int(row.total_count or 0)
    return int(row.covered_words or 0), int(row.target_words or 0)


def _empty(result=None):
    snapshot = {kind: {"ready": False, "done": 0, "total": 0} for kind in KINDS}
    if result is not None:
        snapshot.update(result)
    snapshot["all"] = all(snapshot[kind]["ready"] for kind in KINDS)
    return snapshot


def book_readiness(book_id, book_format, fingerprint=None):
    """一本书的整本能力备齐快照；任何一项查不到都只判该项为 False。

    返回 `{"translate": {"ready", "done", "total"}, ..., "all": bool}`。
    Why 带计数：详情页的小标 hover 时要能说出「307/307 段」而不是一句空口「已缓存」。
    Why 允许传入 fingerprint：show_book 里的 `get_or_build` 已经定位过文件并算过指纹
    （payload 里带 `fingerprint`），复用它可以少一次 calibre 取书 + stat——详情页是
    高频读路径，同一请求里重复做同一件事没有收益。
    """
    book_format = (book_format or "epub").lower()
    if not fingerprint:
        try:
            _book, path = _book_file(book_id, book_format)
            fingerprint = _fingerprint(path)
        except Exception as error:
            # 文件不可读/格式不支持：不是这一页该拦的错误（详情页自己会提示书不可用），
            # 标识静默不出即可。归档书也走这条路（`_book_file` 不过滤归档，这里只是
            # 兜住取不到的情况），口径见 L3 §3。
            log.debug("cache readiness: book file unavailable for %s/%s: %s",
                      book_id, book_format, error)
            return _empty()

    # 延迟取 ub.session / 模型：本模块被 web 在请求期导入，模块级绑定会拖进循环引用。
    from .. import ub

    models = _job_models()
    result = {}
    for kind in KINDS:
        model = models[kind]
        try:
            # Why 过滤下推到 SQL：换书/换格式/换用户重跑会在同一本书上堆多行，
            # 先把「这一版正文 + 这一种格式 + 已完成」筛干净，再按新到旧找第一条跑满的。
            # 大小写用 lower 兜住存量数据（现行 service 写入的是大写格式，老行可能小写）。
            rows = (ub.session.query(model)
                    .filter(model.book_id == int(book_id),
                            model.book_fingerprint == fingerprint,
                            model.status == "COMPLETED",
                            func.lower(model.book_format) == book_format)
                    .order_by(model.created_at.desc())
                    .limit(ROW_LIMIT).all())
        except Exception as error:
            # 台账表缺失/库忙：标识少亮一个，不影响书页其余部分（同 active_jobs 纪律）。
            # Why 区分「表还没建」：新库从未跑过整本任务时三张表本就不存在，每次打开
            # 详情页都打一条 warning 只会把日志变成噪声；真故障（库忙/连接断）仍要看得见。
            message = str(error).lower()
            if "no such table" in message or "doesn't exist" in message:
                log.debug("cache readiness: %s table absent for book %s", kind, book_id)
            else:
                log.warning("cache readiness: %s job lookup failed for book %s: %s",
                            kind, book_id, error)
            result[kind] = {"ready": False, "done": 0, "total": 0}
            continue
        hit = {"ready": False, "done": 0, "total": 0}
        for row in rows:
            done, total = _counts(kind, row)
            # total == 0 不算备齐：没有可处理单元只说明没跑成，不说明缓存有内容。
            # 不满足就继续看更早的批次：COMPLETED 在现行代码里恒等于「跑满」，
            # 但存量数据或人工改状态可能留下 done<total 的行，不能被它一票否决。
            if total > 0 and done >= total:
                hit = {"ready": True, "done": done, "total": total}
                if kind == "wordDetail":
                    # 详解的分母是「本次补缺词数」（预览时已缓存的词不进 target_words），
                    # 悬停要能说清全书口径，否则「200/200 词」会被读成「全书只有 200 词」。
                    hit["wholeWords"] = int(row.distinct_words or 0)
                break
        result[kind] = hit

    return _empty(result)

"""全文单词详解（R176）：给一本书把「查不到详解的词」补进 moon-well 详解缓存。

Why 与整本翻译/整本朗读并列而非另起一套：形制（job/item 台账 + 请求线程定格 token
+ 查询时懒回收 + 页面轮询）已经被那两条链路验证过，本链路唯一的新东西是
**进度口径＝词覆盖率而不是任务状态**（见 get_progress 的 Why）。

Why 不自己判断哪些词「该做详解」：词形过滤（缩略形/连字符/单字母噪声）只允许存在于
moon-well 发布内核 `WordDetailWarmService.publishItems` 一处。magicbook 若在这里
「顺手」也过滤一遍，同一本书在两个入口下会得出不同的待生成集合，页面显示的
「还缺 N 个」与实际入队数就对不上——那正是 R171/R173 反复踩过的双份口径。
"""

import json
import re
import threading
import uuid
from datetime import timedelta

from .. import logger, ub
from ..cw_login import current_user
from ..reading_job.service_base import JobServiceBase
from ..reading_translation.parser import extract_epub_paragraphs
from ..reading_translation.service import _commit_with_retry, _thread_db_session
from ..reading_translation.timeutil import as_utc, now_utc
from .models import WordDetailJob, WordDetailJobItem, WordDetailPreview

log = logger.create()

# 与 moon-well ReadingVocabularyService.extractWords 逐字同口径（\b[A-Za-z][A-Za-z'’-]*\b）。
# Why 复制而不是「更聪明」地排除缩略形：缩略形照抽，交由 moon-well 内核统一过滤并计数，
# 过滤规则只有一处才能保证「预览说缺多少」＝「入队发多少」。
WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'’-]*\b")

# 一批 200 词：moon-well 侧 warm-publish-by-words 建议批次，也是台账 item 的粒度。
BATCH_SIZE = 200
# 单次覆盖率探针词数上限，与 moon-well MAX_WORDS_PER_REQUEST 同值（超过会被服务端直接拒）。
PROBE_CHUNK = 2000
# 单词详解的粗算 token：R109 生产实测均值（单次 ~21.6s、约 4,000 tokens）。
# UI 上必须标成「粗算」，它是决策用的量级，不是账单。
ESTIMATED_TOKENS_PER_WORD = 4000
# 预览快照命中窗口。缓存只会增长，过期后返回旧「缺失数」会持续高估成本；
# 因此过期后由下一次打开页面在后台刷新，而不是永久复用第一份结果。
PREVIEW_READY_TTL_SECONDS = 10 * 60
# 失败后短时间内重复打开页面不反复打 moon-well；用户显式刷新或窗口过后再试。
PREVIEW_RETRY_SECONDS = 60


class WordDetailBatchService(JobServiceBase):
    """按书补缺单词详解：预览（只读）→ 入队（建台账 + 后台发布）→ 覆盖率进度。

    台账原语（建表、正文定位、指纹、幂等复用、停滞判定与僵尸关闭、按属主取批次）在
    `cps/reading_job/service_base.py`；本类只留详解链路特有的抽词口径、覆盖率进度与分批发布。
    """

    job_model = WordDetailJob
    item_model = WordDetailJobItem
    extra_tables = (WordDetailPreview,)
    missing_job_error = "word detail job is unavailable"
    log_prefix = "word-detail batch:"
    job_log = log

    def __init__(self):
        super().__init__()
        # 预览建行/失效/起线程必须在同一进程内串行，避免两个标签页同时把同一本书
        # 重新初始化成两条后台任务。
        self._preview_lock = threading.Lock()

    @staticmethod
    def distinct_words(paragraphs):
        """正文 → 去重词表（小写、保持首现顺序）。

        Why 小写去重：详解缓存按词目（lowercase lemma）建键，`Don't`/`don't`/`DON'T`
        是同一个查询键；保留首现顺序只是让批次切分可复现。
        """
        seen = set()
        words = []
        for _, text in paragraphs:
            for match in WORD_RE.findall(text or ""):
                key = match.lower()
                if key in seen:
                    continue
                seen.add(key)
                words.append(key)
        return words

    def _book_words(self, book_id, book_format):
        """抽正文 → 去重词表（preview 与 start 共用同一条取词路径）。"""
        book, path = self._book_file(book_id, book_format)
        words = self.distinct_words(extract_epub_paragraphs(path))
        if not words:
            raise ValueError("no extractable words found")
        return book, path, words

    # ------------------------------------------------------------------
    # ① 预览：只读，绝不入队、绝不触发生成
    # ------------------------------------------------------------------

    def preview(self, book_id, book_format, check, force=False):
        """返回预览快照；缓存未命中时立即建后台任务并返回 RUNNING。

        Why 必须有这一步：真小说的去重词通常 5k~15k，扣掉已缓存还剩多少**没有实测样本**，
        而详解是全仓最贵的调用且按发起者计费。管理员必须看到数字之后再点第二次
        （沿用 R118 US4「先预案后执行」的同一原则）。
        Why 不在请求线程里算：整本 EPUB 解析 + 多批 cached-check 可能远超网关超时，
        页面只会永远停在「预览加载中」。后台算完落 `reading_word_detail_preview`，
        后续打开同一本书直接命中快照。
        How 覆盖率只走 moon-well 的 cached-check：`GET /vocabulary/detail/{word}` 在 miss
        时会现场生成并计费，用它探进度等于把「查进度」变成「下单」。
        """
        self._ensure_tables()
        # 这里只取书目与文件，不能为了拿指纹先解析一次整本 EPUB。
        book, path = self._book_file(book_id, book_format)
        fingerprint = self._fingerprint(path)
        normalized = (book_format or "epub").lower()
        with self._preview_lock:
            row = self._preview_row(book_id, normalized)
            if row and row.book_fingerprint == fingerprint:
                if row.status == "READY" and not force and self._preview_ready_is_fresh(row):
                    return self._preview_payload(row)
                if row.status == "FAILED" and not force and not self._preview_retry_is_due(row):
                    return self._preview_payload(row)
                if row.status == "RUNNING":
                    self._spawn_preview_worker(row.id, path, book.title, check)
                    ub.session.expire_all()
                    row = self._preview_row(book_id, normalized)
                    return self._preview_payload(row)

            if row is None:
                row = WordDetailPreview(id=uuid.uuid4().hex, book_id=int(book_id),
                                        book_format=normalized)
                ub.session.add(row)
            row.book_name = book.title or ""
            row.book_fingerprint = fingerprint
            row.status = "RUNNING"
            row.stage = "EXTRACTING"
            row.distinct_words = 0
            row.checked_words = 0
            row.cached_words = 0
            row.not_word_like = 0
            row.target_words = 0
            row.missing_json = None
            row.error_message = None
            row.computed_at = None
            row.updated_at = now_utc()
            _commit_with_retry(ub.session)
            preview_id = row.id
            self._spawn_preview_worker(preview_id, path, book.title, check)

        # 测试里会把 _spawn_preview_worker 换成同步执行；expire_all 保证这里能读到
        # 后台会话刚写回的 READY 或 FAILED，而不是请求线程的旧身份映射。
        ub.session.expire_all()
        row = self._preview_row(book_id, normalized)
        return self._preview_payload(row)

    def _preview_row(self, book_id, book_format):
        return (ub.session.query(WordDetailPreview)
                .filter(WordDetailPreview.book_id == int(book_id),
                        WordDetailPreview.book_format == book_format)
                .one_or_none())

    @staticmethod
    def _preview_ready_is_fresh(row, seconds=PREVIEW_READY_TTL_SECONDS):
        return bool(row.computed_at) and (
            now_utc() - as_utc(row.computed_at) <= timedelta(seconds=seconds))

    @staticmethod
    def _preview_retry_is_due(row, seconds=PREVIEW_RETRY_SECONDS):
        return now_utc() - as_utc(row.updated_at) >= timedelta(seconds=seconds)

    @staticmethod
    def _preview_payload(row):
        if row is None:
            raise ValueError("word detail preview is unavailable")
        missing = []
        if row.missing_json:
            try:
                missing = json.loads(row.missing_json) or []
            except (TypeError, ValueError):
                missing = []
        payload = {
            "status": row.status,
            "stage": row.stage,
            "bookId": row.book_id,
            "bookName": row.book_name,
            "distinctWords": row.distinct_words,
            "checkedWords": row.checked_words,
            "cachedWords": row.cached_words,
            "notWordLike": row.not_word_like,
            "targetWords": row.target_words,
            "estimatedTokens": row.target_words * ESTIMATED_TOKENS_PER_WORD,
            "missingSample": missing[:20],
            "computedAt": row.computed_at.isoformat() if row.computed_at else None,
        }
        if row.status == "FAILED":
            payload["message"] = row.error_message or "word detail preview failed"
        return payload

    def _fresh_preview_for_start(self, book_id, book_format, fingerprint):
        """预览刚算完时直接复用结果，避免「点开始」再解析/扫描一遍。"""
        row = self._preview_row(book_id, book_format)
        if (row is None or row.book_fingerprint != fingerprint or row.status != "READY"
                or not self._preview_ready_is_fresh(row) or row.missing_json is None):
            return None
        try:
            missing = json.loads(row.missing_json) or []
        except (TypeError, ValueError):
            return None
        return row, missing

    def _spawn_preview_worker(self, preview_id, path, book_name, check):
        return self._spawn_worker(
            preview_id,
            lambda job_id: self._preview_worker(job_id, path, book_name, check),
        )

    def _preview_worker(self, preview_id, path, book_name, check):
        """后台解析正文并分批探缓存，状态与阶段逐步落库。"""
        with _thread_db_session() as session:
            row = session.query(WordDetailPreview).filter_by(id=preview_id).one()
            # RUNNING 快照的每次轮询都会尝试补线程；线程刚好完成并注销花名册时，
            # 下一次补线程可能晚一步拿到 READY 行。这里二次判态，避免把已完成的预览重算一遍。
            if row.status != "RUNNING":
                return
            try:
                row.stage = "EXTRACTING"
                row.updated_at = now_utc()
                _commit_with_retry(session)

                paragraphs = extract_epub_paragraphs(path)
                words = self.distinct_words(paragraphs)
                if not words:
                    raise ValueError("no extractable words found")

                row.distinct_words = len(words)
                row.stage = "CHECKING"
                row.checked_words = 0
                row.updated_at = now_utc()
                _commit_with_retry(session)

                missing = []
                not_word_like = []
                seen = {"missing": set(), "notWordLike": set()}
                cached = 0
                for start in range(0, len(words), PROBE_CHUNK):
                    chunk = words[start:start + PROBE_CHUNK]
                    result = check(chunk) or {}
                    cached += int(result.get("cached") or 0)
                    for key in ("missing", "notWordLike"):
                        for word in result.get(key) or []:
                            if word not in seen[key]:
                                seen[key].add(word)
                                (missing if key == "missing" else not_word_like).append(word)
                    row.checked_words = min(start + len(chunk), len(words))
                    row.cached_words = cached
                    row.updated_at = now_utc()
                    _commit_with_retry(session)

                row.status = "READY"
                row.stage = "READY"
                row.cached_words = cached
                row.not_word_like = len(not_word_like)
                row.target_words = len(missing)
                row.missing_json = json.dumps(missing, ensure_ascii=False)
                row.error_message = None
                row.computed_at = now_utc()
                row.updated_at = row.computed_at
                _commit_with_retry(session)
                log.info("word-detail preview: ready book=%s name=%s distinct=%s cached=%s target=%s",
                         row.book_id, book_name, row.distinct_words, row.cached_words,
                         row.target_words)
            except Exception as error:
                row.status = "FAILED"
                row.stage = "FAILED"
                row.error_message = str(error)[:1000]
                row.updated_at = now_utc()
                _commit_with_retry(session)
                log.exception("word-detail preview: failed book=%s name=%s",
                              row.book_id, book_name)

    def _probe(self, check, words):
        """分批调 cached-check 并合并结果。

        Why 分批：服务端单次上限 2,000 词，超限直接拒（不静默截断）。
        How 合并时 missing/notWordLike 都去重：调用方传入的词表若含重复，
        跨批不能把同一个词数两遍——否则预览的「待生成数」会比真实值虚高。
        """
        merged = {"requested": 0, "cached": 0, "missing": [], "notWordLike": []}
        seen = {"missing": set(), "notWordLike": set()}
        for start in range(0, len(words), PROBE_CHUNK):
            chunk = words[start:start + PROBE_CHUNK]
            result = check(chunk) or {}
            merged["requested"] += int(result.get("requested") or 0)
            merged["cached"] += int(result.get("cached") or 0)
            for key in ("missing", "notWordLike"):
                for word in result.get(key) or []:
                    if word not in seen[key]:
                        seen[key].add(word)
                        merged[key].append(word)
        return merged

    # ------------------------------------------------------------------
    # ② 入队：建台账 + 后台分批发布
    # ------------------------------------------------------------------

    def start(self, book_id, book_format, force, publish, check):
        """建批次后立即返回，分批发布交给后台线程。

        Why 后台线程：一次 HTTP 请求里同步发完是跑不通的——moon-well 每个批次都要
        做一次索引扫描 + 数百次单事务插入，25 批串起来必然被公网网关 60s 掐断
        （整本翻译 R78 就是被同一件事教过：生产实测 3,160 段只发出 109 段）。
        Why 不做起动恢复线程：本链路的自愈是「同书再点一次」——已缓存跳过、在途跳过，
        重入零成本；僵尸批次由下面 30 分钟判定关闭。
        """
        self._ensure_tables()
        user_id = int(current_user.id)
        book, path = self._book_file(book_id, book_format)
        fingerprint = self._fingerprint(path)

        # 复用/僵尸判定放在抽词之前：重复点击不该白付一次 EPUB 解析 + 一轮索引扫描
        # （缓存探针服务端是 search_after 全索引翻页，一本书上万词时这是本链路最贵的一步）。
        if not force:
            existing = self._find_active_job(user_id, book_id, fingerprint)
            # 僵尸自愈（与整本翻译同形）：容器重启杀掉发布线程会让批次永远停在
            # RUNNING 且霸占复用通道；updated_at 停滞 30 分钟即判僵尸关闭，
            # 本次点击正常建新批次。真在跑的长尾最多损失一次重复入队——
            # moon-well 侧在途跳过兜底，不会二次计费。
            if existing and self._is_stale(existing):
                self._close_as_zombie(existing, book_id)
                existing = None
            if existing:
                log.info("word-detail batch: reuse active job %s (book=%s status=%s)",
                         existing.id, book_id, existing.status)
                return self.progress(existing)

        preview_snapshot = self._fresh_preview_for_start(
            book_id, (book_format or "epub").lower(), fingerprint)
        if preview_snapshot:
            preview_row, missing = preview_snapshot
            distinct_words = preview_row.distinct_words
            cached_words = preview_row.cached_words
            skipped_not_word_like = preview_row.not_word_like
        else:
            words = self.distinct_words(extract_epub_paragraphs(path))
            if not words:
                raise ValueError("no extractable words found")
            probe = self._probe(check, words)
            missing = probe.get("missing") or []
            distinct_words = len(words)
            cached_words = probe.get("cached", 0)
            skipped_not_word_like = len(probe.get("notWordLike") or [])
        if not missing:
            raise ValueError("这本书的正文词已全部有详解，无需补缺")

        job = WordDetailJob(id=uuid.uuid4().hex, user_id=user_id, book_id=int(book_id),
                            book_format=(book_format or "epub").upper(), book_name=book.title,
                            book_fingerprint=fingerprint, status="RUNNING",
                            distinct_words=distinct_words, cached_words=cached_words,
                            target_words=len(missing),
                            skipped_not_word_like=skipped_not_word_like)
        ub.session.add(job)
        for seq, offset in enumerate(range(0, len(missing), BATCH_SIZE)):
            batch = missing[offset:offset + BATCH_SIZE]
            ub.session.add(WordDetailJobItem(id=uuid.uuid4().hex, job_id=job.id, batch_seq=seq,
                                             words_json=json.dumps(batch, ensure_ascii=False),
                                             word_count=len(batch), status="PENDING"))
        _commit_with_retry(ub.session)

        # 受理观测点：与整本翻译同理由——「点了没反应」必须能区分前端没发请求与后端静默成功
        log.info("word-detail batch: job %s accepted (book=%s user=%s target=%s batches=%s force=%s)",
                 job.id, book_id, user_id, job.target_words,
                 (len(missing) + BATCH_SIZE - 1) // BATCH_SIZE, force)

        self._spawn_publish_worker(job.id, book.title, publish)
        return self.progress(job)

    def _spawn_publish_worker(self, job_id, book_title, publish):
        worker = threading.Thread(target=self._publish_worker, name="word-detail-publish-" + job_id[:8],
                                  args=(job_id, book_title, publish), daemon=True)
        worker.start()
        return worker

    def _publish_worker(self, job_id, book_title, publish):
        """后台逐批发布：单批失败只标该批 FAILED，不中断整本。"""
        with _thread_db_session() as session:
            try:
                job = session.query(WordDetailJob).filter_by(id=job_id).one()
                items = (session.query(WordDetailJobItem)
                         .filter_by(job_id=job.id, status="PENDING")
                         .order_by(WordDetailJobItem.batch_seq.asc()).all())
                for item in items:
                    # 逐批重读 job 状态：取消必须能在下一批前停下来。
                    # Why 不在入口判一次：一本书可几十批、每批一次 moon-well 调用，
                    # 只在入口判等于点「停止」后还要把整本发完才算停。
                    session.refresh(job)
                    if job.status == "CANCELED":
                        log.info("word-detail batch: job %s canceled, stop before batch %s",
                                 job.id, item.batch_seq)
                        break
                    words = json.loads(item.words_json or "[]")
                    try:
                        result = publish({"words": words, "bookName": book_title, "skipCached": True}) \
                            or {}
                        item.published_count = int(result.get("published") or 0)
                        item.skipped_cached = int(result.get("skippedCached") or 0)
                        item.skipped_in_flight = int(result.get("skippedInFlight") or 0)
                        item.skipped_invalid = int(result.get("skippedInvalid") or 0)
                        item.skipped_not_word_like = int(result.get("skippedNotWordLike") or 0)
                        # 发布回执里「已缓存」就是已覆盖——进度条从受理那一刻起就该动，
                        # 而不是等第一次轮询回来才跳一截
                        item.covered_count = item.skipped_cached
                        item.status = "PUBLISHED"
                        failed = result.get("failed") or []
                        if failed:
                            item.error_message = json.dumps(failed[:5], ensure_ascii=False)[:1000]
                    except Exception as error:
                        # 失败计数不在此处累加：_refresh_counts 按 item 状态汇总，
                        # 两处都写就会出现「页面上失败批次数比实际多一倍」
                        item.status = "FAILED"
                        item.error_message = str(error)[:1000]
                    item.updated_at = now_utc()
                    _commit_with_retry(session)
                self._refresh_counts(job, session)
                _commit_with_retry(session)
                log.info("word-detail batch: publish finished, job=%s target=%s published=%s "
                         "covered=%s failed_batches=%s status=%s",
                         job.id, job.target_words, job.published_words, job.covered_words,
                         job.failed_batches, job.status)
            except Exception:
                log.exception("word-detail batch publish thread crashed for job %s", job_id)

    # ------------------------------------------------------------------
    # ③ 进度：口径＝词覆盖率，不是任务状态
    # ------------------------------------------------------------------

    def get_progress(self, job_id, check):
        self._ensure_tables()
        job = self._own_job(job_id)
        # 懒回收：只盯还没覆盖满的批次。Why 不探已 DONE 的批次——词进了缓存不会退回，
        # 反复探它等于每轮白扫一遍索引；而 cached-check 服务端是一次索引级扫描
        # （search_after 翻页），所以页面轮询必须 30s 而不是整本翻译那种 4s，
        # 且一轮只发**一次**聚合探针而不是每批一次。
        open_items = (ub.session.query(WordDetailJobItem)
                      .filter(WordDetailJobItem.job_id == job.id,
                              ~WordDetailJobItem.status.in_(("DONE", "SKIPPED")))
                      .all())
        todo = []
        all_words = []
        seen_words = set()
        for item in open_items:
            words = json.loads(item.words_json or "[]")
            if item.covered_count >= self._item_target(item):
                continue
            todo.append((item, words))
            for word in words:
                if word not in seen_words:
                    seen_words.add(word)
                    all_words.append(word)
        if todo:
            probe = self._probe(check, all_words)
            # 覆盖 = 既不在 missing、也不在 notWordLike 的词。Why 要减 notWordLike：
            # 这些词（缩略形/连字符）永远不会被生成，按「批内词数 − 缺失数」反推会把它们
            # 算成已覆盖，进度条提前到 100% 而用户点进去还是没有详解——假完成。
            excluded = set(probe.get("missing") or []) | set(probe.get("notWordLike") or [])
            changed = False
            for item, words in todo:
                covered = sum(1 for word in words if word not in excluded)
                if covered > item.covered_count:
                    item.covered_count = covered
                    item.updated_at = now_utc()
                    if covered >= self._item_target(item):
                        item.status = "DONE"
                    changed = True
            if changed:
                self._refresh_counts(job, ub.session)
                ub.session.commit()
        elif job.status != "CANCELED":
            self._refresh_counts(job, ub.session)
            ub.session.commit()
        return self.progress(job)

    @staticmethod
    def _item_target(item):
        """批次里「真正该有详解」的词数 = 词数 − 服务端判定的非词形。

        Why 减：被词形过滤跳过的词永远不会生成详解，把它们留在分母里，
        覆盖率就永远到不了 100%，页面会一直显示「还差几个」的假故障。
        """
        return max(0, item.word_count - item.skipped_invalid - item.skipped_not_word_like)

    def _refresh_counts(self, job, session):
        items = session.query(WordDetailJobItem).filter_by(job_id=job.id).all()
        # published_words 只算**本批次真正发出去的**词：skippedCached/skippedInFlight
        # 是「别人已经发过/已在队列」，混进来会让页面把「一个新词都没发」显示成「发了 200 个」
        job.published_words = sum(item.published_count for item in items)
        job.covered_words = sum(item.covered_count for item in items)
        # 分母按 item 有效词数重算（减去服务端判定为非词形的词）：否则缩略形留在分母里，
        # 覆盖率永远到不了 100%，页面一直报「还差几个」的假故障
        job.target_words = sum(self._item_target(item) for item in items) or job.target_words
        job.failed_batches = sum(1 for item in items if item.status == "FAILED")
        if job.status != "CANCELED":
            if job.target_words and job.covered_words >= job.target_words:
                job.status = "COMPLETED"
            elif job.failed_batches:
                job.status = "PARTIAL_FAILED"
            else:
                job.status = "RUNNING"
        job.updated_at = now_utc()

    def progress(self, job):
        remaining = ub.session.query(WordDetailJobItem).filter(
            WordDetailJobItem.job_id == job.id,
            ~WordDetailJobItem.status.in_(("DONE", "FAILED", "SKIPPED"))).count()
        # Why 把最新一条批次错误带进进度：发布在后台线程跑，start 的 HTTP 响应先于失败发生，
        # 闸门文案（在途上限/单次词数上限）若只落台账，管理员在页面上永远看不到它，
        # 「message 不被吞」这条就成了一句空话。
        failed = (ub.session.query(WordDetailJobItem)
                  .filter(WordDetailJobItem.job_id == job.id,
                          WordDetailJobItem.status == "FAILED",
                          WordDetailJobItem.error_message.isnot(None))
                  .order_by(WordDetailJobItem.updated_at.desc()).first())
        return {"jobId": job.id, "bookId": job.book_id, "bookName": job.book_name,
                "status": job.status, "distinctWords": job.distinct_words,
                "targetWords": job.target_words, "coveredWords": job.covered_words,
                "publishedWords": job.published_words, "failedBatches": job.failed_batches,
                "openBatches": remaining, "lastError": failed.error_message if failed else None,
                "coverage": round(job.covered_words / job.target_words, 4) if job.target_words else 0.0,
                "updatedAt": job.updated_at.isoformat() if job.updated_at else None}

    def cancel(self, job_id):
        self._ensure_tables()
        job = self._own_job(job_id)
        job.status = "CANCELED"
        job.updated_at = now_utc()
        ub.session.query(WordDetailJobItem).filter(
            WordDetailJobItem.job_id == job.id,
            WordDetailJobItem.status.in_(("PENDING", "FAILED"))).update(
            {"status": "SKIPPED"}, synchronize_session=False)
        ub.session.commit()
        return self.progress(job)

    def latest_job(self, book_id):
        """详情页展示这本书最近一次批次（不区分状态），没有则返回 None。"""
        self._ensure_tables()
        return (ub.session.query(WordDetailJob)
                .filter(WordDetailJob.user_id == int(current_user.id),
                        WordDetailJob.book_id == int(book_id))
                .order_by(WordDetailJob.created_at.desc()).first())

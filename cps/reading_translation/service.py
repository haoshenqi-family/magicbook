import hashlib
import os
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from .. import calibre_db, config, logger, ub
from ..cw_login import current_user
from .models import TranslationJob, TranslationJobItem
from .parser import extract_epub_paragraphs, text_hash

log = logger.create()


ACTIVE_STATUSES = ("PENDING", "RUNNING", "PARTIAL_FAILED")

# 整书翻译单段提示词：与 moon-well PromptDefinitions.reading-paragraph-translate-plain
# 语义一致。Why: 发布时即填充为完整提示词（prompt 字段），任务记录自包含可审计，
# 执行器不再按模板键二次渲染；改提示词需改此处并重新部署 magicbook。
TRANSLATE_PROMPT = (
    "你是一位专业译者。将下面段落翻译成简洁、自然的中文："
    "人名、地名、专有名词的译法保持与全书一致。"
    "只返回一个 JSON 字符串数组：数组第 1 项是段落的中文翻译，"
    "不要解释，不要 markdown 代码块。\n段落：\n{paragraph}"
)


def build_paragraph_prompt(paragraph: str) -> str:
    return TRANSLATE_PROMPT.format(paragraph=paragraph)


def _now():
    return datetime.now(timezone.utc)


@contextmanager
def _thread_db_session():
    """后台线程专用 ub 会话（沿用 tasks/clean.py 的跨线程范式）。

    Why: ub.session 是 init_db 在主线程构造的普通 Session 实例——不可调用
    （按 scoped_session 语义调 ub.session() 直接抛 'Session' object is not
    callable，生产发布线程启动即崩溃），也不可跨线程共享。
    How: get_new_session_instance() 建独立 engine + 线程作用域会话，
    退出时 remove 归还，防线程会话泄漏。
    """
    factory = ub.get_new_session_instance()
    session = factory()
    try:
        yield session
    finally:
        factory.remove()


class WholeBookTranslationService:
    """Create and reconcile durable whole-book translation batches."""

    def _ensure_tables(self):
        bind = ub.session.get_bind()
        ub.Base.metadata.create_all(bind, tables=[TranslationJob.__table__, TranslationJobItem.__table__])

    def _book_file(self, book_id, book_format):
        book = calibre_db.get_filtered_book(book_id)
        if not book:
            raise ValueError("book is unavailable")
        normalized = (book_format or "").lower()
        if normalized not in ("epub", "kepub"):
            raise ValueError("only EPUB and KEPUB are supported")
        data = calibre_db.get_book_format(book_id, normalized.upper())
        if not data:
            raise ValueError("book format is unavailable")
        path = os.path.join(config.get_book_path(), book.path, data.name + "." + normalized)
        if not os.path.isfile(path):
            raise ValueError("book file is unavailable")
        return book, path

    @staticmethod
    def _fingerprint(path):
        stat = os.stat(path)
        return hashlib.sha256(f"{path}:{stat.st_size}:{stat.st_mtime_ns}".encode()).hexdigest()

    def start(self, book_id, book_format, force, publish, lookup=None):
        """创建批次后立即返回，发布任务交给后台线程。

        Why: 一本书数千段、每段一次 moon-well HTTP 发布，串行耗时数分钟，
        在请求线程里同步跑必然被公网网关超时断连杀死（生产实测 HP2 3160 段
        只发出 109 段，两次断连点 109/128 各不相同）。发布进度由 status
        接口轮询展示，HTTP 响应只承诺批次已受理。
        """
        self._ensure_tables()
        user_id = int(current_user.id)
        book, path = self._book_file(book_id, book_format)
        fingerprint = self._fingerprint(path)
        query = ub.session.query(TranslationJob).filter(
            TranslationJob.user_id == user_id,
            TranslationJob.book_id == book_id,
            TranslationJob.book_fingerprint == fingerprint,
            TranslationJob.status.in_(ACTIVE_STATUSES))
        if not force:
            existing = query.order_by(TranslationJob.created_at.desc()).first()
            # 僵尸批次自愈:任务记录清表、容器重启丢线程等历史事故会让旧批次永远停在
            # RUNNING/PARTIAL_FAILED 且无任何进展(线上实锤:book 44 卡 128 段的 9/15
            # 死批次霸占复用通道两天)。判定:updated_at 停滞超过 30 分钟即视为僵尸,
            # 标记 PARTIAL_FAILED 关闭之,让本次点击正常创建新批次;发布线程若其实还在
            # 跑(真长尾),它下次 commit 会把状态刷回,最多损失一次重复发布(幂等,缓存命中不重复计费)。
            if existing and _now() - existing.updated_at > timedelta(minutes=30):
                log.warning("whole-book translation: stale job %s (book=%s updated_at=%s) "
                            "closed as zombie; creating fresh batch",
                            existing.id, book_id, existing.updated_at)
                existing.status = "PARTIAL_FAILED"
                existing.updated_at = _now()
                ub.session.commit()
                existing = None
            if existing:
                # 复用是静默成功：无此日志时线上无从区分「没收到请求」与「命中幂等」
                log.info("whole-book translation: reuse active job %s (book=%s status=%s)",
                         existing.id, book_id, existing.status)
                return self.progress(existing)

        paragraphs = extract_epub_paragraphs(path)
        if not paragraphs:
            raise ValueError("no translatable paragraphs found")
        job = TranslationJob(id=uuid.uuid4().hex, user_id=user_id, book_id=book_id,
                             book_format=book_format.upper(), book_fingerprint=fingerprint,
                             book_name=book.title, status="RUNNING")
        ub.session.add(job)
        unique = {}
        for index, (chapter, text) in enumerate(paragraphs):
            digest = text_hash(text)
            if digest in unique:
                continue
            item = TranslationJobItem(id=uuid.uuid4().hex, job_id=job.id,
                                      paragraph_index=index, chapter=chapter, text=text,
                                      text_hash=digest, status="PENDING")
            unique[digest] = item
            ub.session.add(item)
        job.total_count = len(unique)
        ub.session.commit()

        # 受理观测点：整本翻译的 HTTP 成功路径此前零日志，「点击没反应」
        # 类问题无从区分前端没发请求还是后端静默成功，必须在此留痕。
        log.info("whole-book translation: job %s accepted (book=%s user=%s paragraphs=%s force=%s)",
                 job.id, book_id, user_id, job.total_count, force)

        # Why: scoped_session 绑定 greenlet/线程作用域，后台线程不能复用请求
        # 线程的 session；线程内自建会话操作，HTTP 响应无需等待发布完成。
        self._spawn_publish_worker(job.id, book.title, book_id, fingerprint, publish, lookup)
        return self.progress(job)

    def _spawn_publish_worker(self, job_id, book_title, book_id, fingerprint, publish, lookup=None):
        """拉起后台发布线程（start 与启动恢复共用同一入口）。"""
        worker = threading.Thread(
            target=self._publish_pending,
            args=(job_id, book_title, book_id, fingerprint, publish, lookup),
            name="whole-book-publish-" + str(job_id)[:8], daemon=True)
        worker.start()
        return worker

    def recover_active_jobs(self, publish, lookup=None):
        """应用启动恢复：为存在 PENDING 项的活动批次重新拉起发布线程。

        Why: 发布线程是 daemon，容器重启/更新会直接杀死它，剩余 PENDING
        段落既不会发布也不会失败，批次从此卡死（设计文档 §9 断点续作要求）。
        How: 由 web app 启动钩子调用一次；publish/lookup 闭包由调用方注入
        （无 Flask 请求上下文，需用内部身份头构造 moon-well 调用）。
        """
        self._ensure_tables()
        try:
            active = ub.session.query(TranslationJob).filter(
                TranslationJob.status.in_(ACTIVE_STATUSES)).all()
        except Exception:
            # 表可能尚未创建（首次部署），静默跳过
            return 0
        recovered = 0
        for job in active:
            pending = ub.session.query(TranslationJobItem.id).filter(
                TranslationJobItem.job_id == job.id,
                TranslationJobItem.status == "PENDING").count()
            if not pending:
                continue
            recovered += 1
            self._spawn_publish_worker(job.id, job.book_name, job.book_id,
                                       job.book_fingerprint, publish, lookup)
        if recovered:
            import logging
            logging.getLogger(__name__).info("whole-book translation: recovered %d active jobs", recovered)
        return recovered

    def _publish_pending(self, job_id, book_title, book_id, fingerprint, publish, lookup=None):
        """后台发布线程：缓存命中回收 + 未发布段落逐条发布。

        Why: 与请求线程解耦后，网关断连/客户端超时都不再影响发布进度；
        单段失败只标 FAILED 可重试，不中断整批。
        How: 会话走 _thread_db_session（独立 engine、线程作用域）；
        lookup 分批查询，避免一次性把全书文本塞进单次 HTTP。
        """
        with _thread_db_session() as session:
            try:
                job = session.query(TranslationJob).filter_by(id=job_id).one()
                items = session.query(TranslationJobItem).filter_by(job_id=job.id).all()
                # 缓存命中回收：分批查，命中直接标记 COMPLETED（译文冗余存本地）
                if lookup:
                    for batch in self._batches(items, 200):
                        try:
                            cached = lookup([item.text for item in batch]) or {}
                        except Exception:
                            session.rollback()
                            continue
                        for item in batch:
                            if cached.get(item.text):
                                item.status = "COMPLETED"
                                item.translation = cached[item.text]
                                job.cached_count += 1
                                job.completed_count += 1
                        session.commit()
                for item in items:
                    if item.status != "PENDING":
                        continue
                    # Why: 发布时即填充完整提示词(prompt),任务记录自包含可审计,
                    # 执行器直接使用;paragraph 裸原文供 moon-well 写缓存时作键。
                    payload = {"taskType": "TEXT", "caller": "magicbook-whole-book-translation",
                               "input": item.text,
                               "prompt": build_paragraph_prompt(item.text),
                               "parameters": {"jobId": job.id, "itemId": item.id, "bookId": book_id,
                                              "bookFingerprint": fingerprint, "paragraphIndex": item.paragraph_index,
                                              "textHash": item.text_hash, "bookName": book_title,
                                              "chapter": item.chapter, "paragraph": item.text}}
                    try:
                        response = publish(payload)
                        result = response.get("result", response) if isinstance(response, dict) else {}
                        task_id = result.get("taskId")
                        if not task_id:
                            raise ValueError("moon-well did not return taskId")
                        item.task_id = str(task_id)
                        item.status = "PUBLISHED"
                        item.attempt_count = 1
                        job.published_count += 1
                    except Exception as error:
                        item.status = "FAILED"
                        item.error_message = str(error)[:1000]
                        item.attempt_count = 1
                        job.failed_count += 1
                    item.updated_at = _now()
                    session.commit()
                self._refresh_counts_session(job, session)
                session.commit()
                log.info("whole-book translation: publish finished, job=%s total=%s cached=%s "
                         "published=%s failed=%s status=%s",
                         job.id, job.total_count, job.cached_count,
                         job.published_count, job.failed_count, job.status)
            except Exception:
                # 后台线程无 HTTP 上下文：异常只能落日志，批次状态由下次轮询/重试接管
                log.exception("whole-book publish thread crashed for job %s", job_id)

    @staticmethod
    def _batches(items, size):
        for start in range(0, len(items), size):
            yield items[start:start + size]

    def progress(self, job):
        pending = sum(1 for _ in ub.session.query(TranslationJobItem.id).filter(
            TranslationJobItem.job_id == job.id,
            ~TranslationJobItem.status.in_(("COMPLETED", "FAILED", "SKIPPED"))))
        # Why: 去回调化后 moon-well 完成任务自行写缓存，进度按缓存懒回收；
        # pendingCount 单独暴露，前端可区分「已发布未完成」与「彻底失败」。
        return {"jobId": job.id, "bookId": job.book_id, "status": job.status,
                "totalCount": job.total_count, "cachedCount": job.cached_count,
                "publishedCount": job.published_count, "completedCount": job.completed_count,
                "failedCount": job.failed_count, "pendingCount": pending}

    def get_progress(self, job_id, lookup=None):
        self._ensure_tables()
        job = ub.session.query(TranslationJob).filter_by(id=job_id, user_id=int(current_user.id)).one_or_none()
        if not job:
            raise ValueError("translation job is unavailable")
        # 去回调化后，本地未完成项仅由缓存命中回收：查询进度时懒刷新，避免引入常驻轮询进程。
        # moon-well 完成任务自行写入翻译缓存，magicbook 在此单向查缓存即可标记完成。
        if lookup:
            pending_items = ub.session.query(TranslationJobItem).filter(
                TranslationJobItem.job_id == job.id,
                ~TranslationJobItem.status.in_(("COMPLETED", "FAILED", "SKIPPED"))).all()
            # Why: 一本书数千段，一次性把全部原文塞进单次 find-translations
            # 会产生 MB 级请求体和长查询，20s 超时后整个 status 接口 503。
            # 分批回收（每批 200 段），单批失败不影响其余批次。
            changed = False
            for batch in self._batches(pending_items, 200):
                try:
                    cached = lookup([item.text for item in batch]) or {}
                except Exception:
                    continue
                for item in batch:
                    if cached.get(item.text):
                        item.status = "COMPLETED"
                        item.translation = cached[item.text]
                        item.error_message = None
                        item.updated_at = _now()
                        changed = True
            if changed:
                self._refresh_counts(job)
                ub.session.commit()
        return self.progress(job)

    def retry(self, job_id, publish):
        """重发布指定批次的 FAILED 段落。

        Why: 失败段可能上千，同步发布会被公网网关超时掐死且前端拿不到响应；
        改为后台线程重发布，HTTP 响应立即返回当前进度，进度继续走 status 轮询。
        """
        self._ensure_tables()
        job = ub.session.query(TranslationJob).filter_by(id=str(job_id), user_id=int(current_user.id)).one_or_none()
        if not job:
            raise ValueError("translation job is unavailable")
        items = ub.session.query(TranslationJobItem).filter_by(job_id=job.id, status="FAILED").all()
        if not items:
            return self.progress(job)
        threading.Thread(
            target=self._retry_failed,
            args=(job.id, [item.id for item in items], publish),
            name="whole-book-retry-" + job.id[:8], daemon=True).start()
        job.status = "RUNNING"
        ub.session.commit()
        return self.progress(job)

    def _retry_failed(self, job_id, item_ids, publish):
        """后台重发布线程：只处理传入的 item_id，用线程自建 session 操作。"""
        with _thread_db_session() as session:
            try:
                job = session.query(TranslationJob).filter_by(id=job_id).one()
                items = session.query(TranslationJobItem).filter(
                    TranslationJobItem.id.in_(item_ids)).all()
                for item in items:
                    try:
                        response = publish({"taskType": "TEXT", "caller": "magicbook-whole-book-translation",
                                            "input": item.text,
                                            "prompt": build_paragraph_prompt(item.text),
                                            "parameters": {"jobId": job.id, "itemId": item.id,
                                            "bookId": job.book_id, "bookFingerprint": job.book_fingerprint,
                                            "paragraphIndex": item.paragraph_index, "textHash": item.text_hash,
                                            "bookName": job.book_name,
                                            "chapter": item.chapter, "paragraph": item.text}})
                        result = response.get("result", response)
                        item.task_id = str(result["taskId"])
                        item.status = "PUBLISHED"
                        item.attempt_count += 1
                        item.error_message = None
                    except Exception as error:
                        item.attempt_count += 1
                        item.error_message = str(error)[:1000]
                    item.updated_at = _now()
                    session.commit()
                self._refresh_counts_session(job, session)
                session.commit()
                log.info("whole-book translation: retry finished, job=%s items=%s "
                         "published=%s failed=%s status=%s",
                         job.id, len(item_ids), job.published_count,
                         job.failed_count, job.status)
            except Exception:
                # 后台线程无 HTTP 上下文：异常只落日志，批次状态由下次轮询/重试接管
                log.exception("whole-book retry thread crashed for job %s", job_id)

    def cancel(self, job_id):
        self._ensure_tables()
        job = ub.session.query(TranslationJob).filter_by(id=str(job_id), user_id=int(current_user.id)).one_or_none()
        if not job:
            raise ValueError("translation job is unavailable")
        job.status = "CANCELED"
        ub.session.query(TranslationJobItem).filter(
            TranslationJobItem.job_id == job.id,
            TranslationJobItem.status.in_(("PENDING", "FAILED"))).update({"status": "SKIPPED"}, synchronize_session=False)
        ub.session.commit()
        return self.progress(job)

    @staticmethod
    def _refresh_counts(job):
        items = ub.session.query(TranslationJobItem).filter_by(job_id=job.id).all()
        job.completed_count = sum(item.status == "COMPLETED" for item in items)
        job.failed_count = sum(item.status == "FAILED" for item in items)
        job.published_count = sum(item.status in ("PUBLISHED", "ACCEPTED", "COMPLETED") for item in items)
        if job.status != "CANCELED":
            job.status = "COMPLETED" if job.completed_count == job.total_count else ("PARTIAL_FAILED" if job.failed_count else "RUNNING")
        job.updated_at = _now()

    @staticmethod
    def _refresh_counts_session(job, session):
        """后台发布线程专用：用线程自建 session 刷新统计（_refresh_counts 走全局 ub.session）。"""
        items = session.query(TranslationJobItem).filter_by(job_id=job.id).all()
        job.completed_count = sum(item.status == "COMPLETED" for item in items)
        job.failed_count = sum(item.status == "FAILED" for item in items)
        job.published_count = sum(item.status in ("PUBLISHED", "ACCEPTED", "COMPLETED") for item in items)
        if job.status != "CANCELED":
            job.status = "COMPLETED" if job.completed_count == job.total_count else ("PARTIAL_FAILED" if job.failed_count else "RUNNING")
        job.updated_at = _now()

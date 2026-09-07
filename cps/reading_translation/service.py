import hashlib
import os
import uuid
from datetime import datetime, timezone

from .. import calibre_db, config, ub
from ..cw_login import current_user
from .models import TranslationJob, TranslationJobItem
from .parser import extract_epub_paragraphs, text_hash


ACTIVE_STATUSES = ("PENDING", "RUNNING", "PARTIAL_FAILED")


def _now():
    return datetime.now(timezone.utc)


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
            if existing:
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
        cached = lookup([item.text for item in unique.values()]) if lookup else {}
        for item in unique.values():
            if cached.get(item.text):
                item.status = "COMPLETED"
                item.translation = cached[item.text]
                job.cached_count += 1
                job.completed_count += 1
                ub.session.commit()
                continue
            payload = {"taskType": "TEXT", "caller": "magicbook-whole-book-translation",
                       "input": item.text,
                       "parameters": {"jobId": job.id, "itemId": item.id, "bookId": book_id,
                                      "bookFingerprint": fingerprint, "paragraphIndex": item.paragraph_index,
                                      "textHash": item.text_hash, "bookName": book.title,
                                      "chapter": item.chapter}}
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
            ub.session.commit()
        self._refresh_counts(job)
        ub.session.commit()
        return self.progress(job)

    def progress(self, job):
        return {"jobId": job.id, "bookId": job.book_id, "status": job.status,
                "totalCount": job.total_count, "cachedCount": job.cached_count,
                "publishedCount": job.published_count, "completedCount": job.completed_count,
                "failedCount": job.failed_count}

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
            if pending_items:
                cached = lookup([item.text for item in pending_items])
                changed = False
                for item in pending_items:
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
        self._ensure_tables()
        job = ub.session.query(TranslationJob).filter_by(id=str(job_id), user_id=int(current_user.id)).one_or_none()
        if not job:
            raise ValueError("translation job is unavailable")
        items = ub.session.query(TranslationJobItem).filter_by(job_id=job.id, status="FAILED").all()
        for item in items:
            try:
                response = publish({"taskType": "TEXT", "caller": "magicbook-whole-book-translation",
                                    "input": item.text,
                                    "parameters": {"jobId": job.id, "itemId": item.id,
                                    "bookId": job.book_id, "bookFingerprint": job.book_fingerprint,
                                    "paragraphIndex": item.paragraph_index, "textHash": item.text_hash,
                                    "chapter": item.chapter}})
                result = response.get("result", response)
                item.task_id = str(result["taskId"])
                item.status = "PUBLISHED"
                item.attempt_count += 1
                item.error_message = None
            except Exception as error:
                item.attempt_count += 1
                item.error_message = str(error)[:1000]
            item.updated_at = _now()
        job.status = "RUNNING"
        self._refresh_counts(job)
        ub.session.commit()
        return self.progress(job)

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

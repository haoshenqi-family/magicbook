# -*- coding: utf-8 -*-

#  This file is part of the Magicbook (customized Calibre-Web).
#
#  R279 投稿服务层：提交（写 MinIO + 台账）、审核通过（后台线程入库）、
#  驳回（删对象 + 留痕）。
#
#  线程模型：入库在 daemon 线程跑（进程重启丢任务可接受——台账还在
#  APPROVED 状态，下次审核页点「通过」重跑即可，见 retry_ingest）。
#  不复用 WorkerThread：那个队列面向「任务列表 UI」，投稿入库是管理动作，
#  状态本身落在 book_submission 表，不必再混进全局任务列表。
#
#  会话纪律（R249 教训）：后台线程绝不能碰主线程的 ub.session /
#  calibre_db.session —— 一律走独立实例，逐次提交。台账用
#  get_new_session_instance()（app.db），calibre 侧用局部 CalibreDB 实例。

import hashlib
import os
import threading
import uuid

from .. import calibre_db, config, logger
from ..ub import get_new_session_instance
from . import models, storage
from .ingest import extract_meta, ingest_book_from_meta

log = logger.create()

_CHUNK = 1024 * 1024


def _submission_session():
    return get_new_session_instance()


def ensure_tables():
    """懒建 book_submission 表（book_insight 同款范式），幂等。"""
    from ..ub import Base
    factory = get_new_session_instance()
    session = factory()
    try:
        Base.metadata.create_all(session.get_bind(),
                                 tables=[models.BookSubmission.__table__])
    finally:
        factory.remove()


def get_submission(submission_id):
    ensure_tables()
    session = _submission_session()
    try:
        row = session.query(models.BookSubmission).get(int(submission_id))
        return _row_dict(row) if row is not None else None
    finally:
        session.remove()


class SubmissionError(Exception):
    def __init__(self, message, status=400):
        super(SubmissionError, self).__init__(message)
        self.message = message
        self.status = status


def _sha256_and_seek(stream):
    digest = hashlib.sha256()
    pos = stream.tell()
    while True:
        chunk = stream.read(_CHUNK)
        if not chunk:
            break
        digest.update(chunk)
    stream.seek(pos)
    return digest.hexdigest()


def create_submission(user_id, upload, ip_address=None):
    """校验并落一份投稿：扩展名白名单 + MIME 校验 + sha256 去重 + 配额。

    返回 (submission_dict, created)； SubmissionError 携带 4xx/5xx 状态码。
    Why 先全量读哈希再决定上传：同一用户重复传同一文件时直接复用旧记录，
    不再写 MinIO，防灌桶；跨用户不去重（避免把 A 的投稿状态泄漏给 B）。
    """
    ensure_tables()
    filename = upload.filename or ""
    if "." not in filename:
        raise SubmissionError("file must have an extension")
    extension = filename.rsplit(".", 1)[-1].lower()
    allowed = allowed_extensions()
    if extension not in allowed:
        raise SubmissionError("extension .{} is not allowed".format(extension))

    if not storage.configured():
        raise SubmissionError("submission storage is not configured", 503)

    stream = upload.stream
    sha256 = _sha256_and_seek(stream)
    size = stream.seek(0, os.SEEK_END)
    stream.seek(0)
    if size <= 0:
        raise SubmissionError("file is empty")
    if size > storage.max_submission_bytes():
        raise SubmissionError("file exceeds size limit", 413)

    # MIME 校验：复用 file_helper 的 libmagic 校验（与 /upload 同一面）。
    from ..file_helper import validate_mime_type
    if not validate_mime_type(upload, allowed):
        raise SubmissionError("file type is not allowed", 415)

    session = _submission_session()
    try:
        existing = session.query(models.BookSubmission).filter(
            models.BookSubmission.user_id == int(user_id),
            models.BookSubmission.sha256 == sha256).first()
        if existing is not None and existing.status != models.STATUS_FAILED:
            return _row_dict(existing), False

        pending_count = session.query(models.BookSubmission).filter(
            models.BookSubmission.user_id == int(user_id),
            models.BookSubmission.status.in_((models.STATUS_PENDING,
                                              models.STATUS_APPROVED))).count()
        if pending_count >= storage.max_pending_per_user():
            raise SubmissionError("too many pending submissions", 429)

        from ..reading_translation.timeutil import now_utc
        object_key = storage.object_key_for(user_id, uuid.uuid4().hex, extension)
        storage.put_object(object_key, stream, size,
                           content_type="application/octet-stream")

        row = models.BookSubmission(
            user_id=int(user_id),
            object_key=object_key,
            original_filename=filename[:500],
            size=int(size),
            sha256=sha256,
            status=models.STATUS_PENDING,
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        session.add(row)
        session.commit()
        return _row_dict(row), True
    finally:
        session.remove()


def allowed_extensions():
    """与 ingest.allowed_submission_extensions 同源（书类格式，去音视频）。"""
    from .ingest import allowed_submission_extensions
    return allowed_submission_extensions()


def _row_dict(row):
    return {
        "id": row.id,
        "userId": row.user_id,
        "originalFilename": row.original_filename,
        "size": row.size,
        "status": row.status,
        "note": row.note or "",
        "bookId": row.book_id,
        "errorMessage": row.error_message or "",
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def list_submissions(limit=200):
    ensure_tables()
    session = _submission_session()
    try:
        rows = (session.query(models.BookSubmission)
                .order_by(models.BookSubmission.id.desc())
                .limit(int(limit)).all())
        return [_row_dict(r) for r in rows]
    finally:
        session.remove()


def list_submissions_of_user(user_id):
    ensure_tables()
    session = _submission_session()
    try:
        rows = (session.query(models.BookSubmission)
                .filter(models.BookSubmission.user_id == int(user_id))
                .order_by(models.BookSubmission.id.desc()).all())
        return [_row_dict(r) for r in rows]
    finally:
        session.remove()


def review(submission_id, reviewer_id, approve, note=""):
    """审核动作：通过=置 APPROVED 并起后台入库线程；驳回=删对象置 REJECTED。

    状态迁移按当前值判定，重复点击是幂等 no-op。
    """
    ensure_tables()
    session = _submission_session()
    try:
        row = session.query(models.BookSubmission).get(int(submission_id))
        if row is None:
            raise SubmissionError("submission not found", 404)
        if row.status == models.STATUS_PENDING:
            from ..reading_translation.timeutil import now_utc
            if approve:
                row.status = models.STATUS_APPROVED
                row.reviewer_id = int(reviewer_id)
                row.reviewed_at = now_utc()
                row.note = (note or "")[:2000]
                row.error_message = ""
                session.commit()
                thread = threading.Thread(target=_ingest_worker,
                                          args=(int(submission_id), _flask_app()),
                                          name="book-submission-ingest",
                                          daemon=True)
                thread.start()
            else:
                row.status = models.STATUS_REJECTED
                row.reviewer_id = int(reviewer_id)
                row.reviewed_at = now_utc()
                row.note = (note or "")[:2000]
                session.commit()
                try:
                    storage.remove_object(row.object_key)
                except Exception as remove_error:  # noqa: BLE001
                    log.warning("submission %s: remove object failed: %s",
                                row.id, remove_error)
            return _row_dict(row)
        if row.status == models.STATUS_FAILED and approve:
            # 失败重试：重新排队入库
            from ..reading_translation.timeutil import now_utc
            row.status = models.STATUS_APPROVED
            row.error_message = ""
            row.updated_at = now_utc()
            session.commit()
            threading.Thread(target=_ingest_worker,
                             args=(int(submission_id), _flask_app()),
                             name="book-submission-ingest", daemon=True).start()
            return _row_dict(row)
        return _row_dict(row)
    finally:
        session.remove()


def _flask_app():
    """取真实 Flask app 实例：后台线程不能依赖 context-local 的 current_app。"""
    from flask import current_app
    try:
        return current_app._get_current_object()
    except RuntimeError:
        # 测试/非请求上下文（直接调用 review）时退回模块级单例
        from .. import app as module_app
        return module_app


def _ingest_worker(submission_id, app=None):
    """后台入库：下载对象 → 临时目录 → 解析 → 写书库 → 回写状态。

    Why 独立 CalibreDB 实例：R249 实锤主线程会话跨线程复用会崩；
    Why app.app_context()：uploader/cover 链路里有 gettext 与 config 读取。
    """
    app = app or _flask_app()
    with app.app_context():
        session = _submission_session()
        temp_path = None
        try:
            row = session.query(models.BookSubmission).get(int(submission_id))
            if row is None or row.status != models.STATUS_APPROVED:
                return
            # calibre_db.session 是 scoped_session（线程作用域）+ g.lib_sql 按
            # app context 隔离；本线程第一次访问时自建连接，与请求线程互不可见
            #（R249 纪律：绝不跨线程共享主线程会话）。
            temp_dir = os.path.join(config.get_book_path(), ".submissions-tmp")
            os.makedirs(temp_dir, exist_ok=True)
            ext = (row.original_filename or "book.epub").rsplit(".", 1)[-1]
            temp_path = os.path.join(temp_dir,
                                     "sub-{}.{}".format(submission_id, ext))
            resp = storage.get_object(row.object_key)
            try:
                with open(temp_path, "wb") as fh:
                    for chunk in resp.stream(_CHUNK):
                        fh.write(chunk)
            finally:
                resp.close()
                resp.release_conn()

            meta = extract_meta(temp_path, row.original_filename, ext)
            # ingest_book_from_meta 内部用 calibre_db 全局实例 —— scoped_session
            # 线程作用域保证后台线程拿到自己的会话；app_context 保证
            # config/gettext（flask.g）可用。
            db_book, error = ingest_book_from_meta(meta, temp_path)
            temp_path = None  # 成功路径文件已被搬走
            if error:
                raise RuntimeError(error)

            from ..reading_translation.timeutil import now_utc
            row = session.query(models.BookSubmission).get(int(submission_id))
            row.status = models.STATUS_INGESTED
            row.book_id = db_book.id
            row.updated_at = now_utc()
            session.commit()
            try:
                storage.remove_object(row.object_key)
            except Exception as remove_error:  # noqa: BLE001
                log.warning("submission %s: cleanup object failed: %s",
                            row.id, remove_error)
        except Exception as ingest_error:  # noqa: BLE001
            log.error("submission %s ingest failed: %s",
                          submission_id, ingest_error)
            try:
                from ..reading_translation.timeutil import now_utc
                row = session.query(models.BookSubmission).get(int(submission_id))
                if row is not None:
                    row.status = models.STATUS_FAILED
                    row.error_message = str(ingest_error)[:2000]
                    row.updated_at = now_utc()
                    session.commit()
            except Exception:
                session.rollback()
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            session.remove()


def preview_stream(submission_id):
    """审核预览：打开 MinIO 对象流（caller 负责关闭）。仅管理员调用。"""
    ensure_tables()
    session = _submission_session()
    try:
        row = session.query(models.BookSubmission).get(int(submission_id))
        if row is None:
            raise SubmissionError("submission not found", 404)
        return storage.get_object(row.object_key), row
    finally:
        session.remove()

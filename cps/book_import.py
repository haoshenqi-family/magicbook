# -*- coding: utf-8 -*-

#  This file is part of the Magicbook (customized Calibre-Web).
#
#  内部书籍导入 API（halo-book-connector 方案 A，R107）：
#  供内网连接器服务以共享密钥替换指定书目的 EPUB/封面，并可选触发整本翻译。
#  Why: 指南类图书以 Halo Markdown 为事实源，发布即出书；浏览器 session 鉴权
#  不适用于服务间调用，fork 内亦无现成入站密钥机制，故新建最小共享密钥通道。
#  设计文档：docs/feat/halo-book-connector/design/lld.md

import hmac
import os
import threading
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, jsonify, request, session as flask_session

from . import calibre_db, config, csrf, db, helper, logger, ub
from .cw_login import login_user
from .file_helper import validate_mime_type
from .reading_translation.service import WholeBookTranslationService, _commit_with_retry

bookimport = Blueprint("book_import", __name__)

log = logger.create()

# fail-closed：main.py 仅在 BOOK_IMPORT_KEY 配置时才注册本蓝图；
# 每次请求实时读 env，便于测试注入与运行期排错。
KEY_ENV = "BOOK_IMPORT_KEY"
USER_ID_ENV = "BOOK_IMPORT_USER_ID"
MAX_MB_ENV = "BOOK_IMPORT_MAX_MB"

_service = WholeBookTranslationService()

# per-book 导入锁：webhook 重放/并发触发时同一书目直接 409，
# 防止两个写线程交叉覆盖同一 EPUB 文件与 DB 行。
_locks = {}
_locks_guard = threading.Lock()


def _max_bytes():
    try:
        return int(os.environ.get(MAX_MB_ENV, "50")) * 1024 * 1024
    except ValueError:
        return 50 * 1024 * 1024


def _book_lock(book_id):
    with _locks_guard:
        lock = _locks.get(book_id)
        if lock is None:
            lock = _locks[book_id] = threading.Lock()
        return lock


def connector_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = os.environ.get(KEY_ENV, "")
        if not expected:
            # 蓝图未启用却仍有路由残留（如手工注册）：一律 404，不泄露存在性
            return jsonify({"error": "not_found"}), 404
        supplied = request.headers.get("X-Connector-Key", "")
        if not hmac.compare_digest(expected, supplied):
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def _system_closures():
    """整本翻译 publish/lookup 闭包（系统身份）。

    Why: 连接器请求没有 OIDC 会话，拿不到 moonwell_access_token；R145 全
    token 化后系统身份走 MOONWELL_SYSTEM_TOKEN 的 mk- API key（拦截器按
    user.token 查库校验），启动恢复（__init__.py _recover_whole_book_translation）
    同一范式。
    How: 延迟 import cps.web 规避循环依赖（同 __init__.py R78 注释）。
    """
    import json

    from . import web as web_module

    def publish(task_payload):
        response = web_module._moonwell_proxy("/llm/task/publish", task_payload, 20,
                                              "book-import translation",
                                              system_identity=True)
        if not isinstance(response, tuple) or response[1] < 200 or response[1] >= 300:
            raise ValueError("moon-well task publish failed")
        return json.loads(response[0])

    def lookup(paragraphs):
        response = web_module._moonwell_proxy("/reading/paragraph-cache/find-translations",
                                              {"paragraphs": paragraphs}, 20,
                                              "book-import translation cache",
                                              system_identity=True)
        if not isinstance(response, tuple) or response[1] < 200 or response[1] >= 300:
            return {}
        data = json.loads(response[0])
        return data.get("result", {}) if isinstance(data, dict) else {}

    return publish, lookup


@bookimport.route("/api/internal/book-import", methods=["POST"])
@csrf.exempt
@connector_required
def import_book():
    """替换已有书目的 EPUB（可选封面），并按需触发整本翻译。

    字段：book_id(必填) file(必填 EPUB) cover(可选 JPEG/PNG) trigger_translation
    (缺省 true) source_ref(可选溯源串)。V1 只更新已有书，不新建书目。
    格式硬编码仅 EPUB（较 LLD 的 config_upload_formats 白名单有意收紧，
    能力最小化：内部 API 不承担通用上传职责）。
    """
    try:
        book_id = int(request.form.get("book_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "book_id must be an integer"}), 400

    ebook = request.files.get("file")
    if ebook is None or ebook.filename == "":
        return jsonify({"error": "file (EPUB) is required"}), 400
    if not validate_mime_type(ebook, ["epub"]):
        return jsonify({"error": "only EPUB files are accepted"}), 415

    cover = request.files.get("cover")
    if cover is not None and cover.filename != "" and \
            not validate_mime_type(cover, ["jpg", "jpeg", "png"]):
        return jsonify({"error": "cover must be JPEG/PNG"}), 415

    book = calibre_db.get_book(book_id)
    if not book:
        return jsonify({"error": "book not found", "bookId": book_id}), 404

    lock = _book_lock(book_id)
    if not lock.acquire(blocking=False):
        return jsonify({"error": "import already in progress", "bookId": book_id}), 409
    try:
        return _do_import(book, book_id, ebook, cover)
    finally:
        lock.release()


def _do_import(book, book_id, ebook, cover):
    source_ref = (request.form.get("source_ref") or "").strip()
    trigger = (request.form.get("trigger_translation") or "true").strip().lower() \
        not in ("false", "0", "no")

    file_name = book.path.rsplit("/", 1)[-1]
    filepath = os.path.normpath(os.path.join(config.get_book_path(), book.path))
    saved_filename = os.path.join(filepath, file_name + ".epub")

    # 封面先落盘：失败即 415 返回，EPUB 不受影响（save_cover 原子写 cover.jpg）
    if cover is not None and cover.filename != "":
        try:
            ret, message = helper.save_cover(cover, book.path)
        except Exception as e:  # noqa: BLE001
            ret, message = False, str(e)
        if not ret:
            log.warning("book-import: cover rejected for book=%s: %s", book_id, message)
            return jsonify({"error": "cover rejected: " + str(message)}), 415
        helper.replace_cover_thumbnail_cache(book_id)

    # EPUB 写临时文件 + 精确校验 + os.replace 原子换入：
    # Why: 直接覆盖后再删会把新旧文件一并毁掉（评审实锤），任何失败必须保住上一版。
    if not os.path.exists(filepath):
        try:
            os.makedirs(filepath)
        except OSError:
            log.error("book-import: cannot create path %s", filepath)
            return jsonify({"error": "failed to create library path"}), 500
    tmp_filename = os.path.join(filepath, file_name + ".epub." + uuid.uuid4().hex + ".tmp")
    try:
        ebook.save(tmp_filename)
        file_size = os.path.getsize(tmp_filename)
        if file_size > _max_bytes():
            return jsonify({"error": "EPUB exceeds size limit"}), 413
        os.replace(tmp_filename, saved_filename)
    except OSError:
        log.error("book-import: failed to store file for book=%s", book_id)
        return jsonify({"error": "failed to store EPUB"}), 500
    finally:
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)

    try:
        if not calibre_db.get_book_format(book_id, "EPUB"):
            calibre_db.session.add(db.Data(book_id, "EPUB", file_size, file_name))
            _commit_with_retry(calibre_db.session)
            calibre_db.create_functions(config)

        book.last_modified = datetime.now(timezone.utc)
        calibre_db.session.merge(book)
        calibre_db.set_metadata_dirty(book.id)
        _commit_with_retry(calibre_db.session)
    except Exception as e:  # noqa: BLE001 文件已原子生效，DB 失败可重发导入修复
        calibre_db.session.rollback()
        log.error("book-import: database error for book=%s: %s", book_id, e)
        return jsonify({"error": "database error: " + str(e)}), 500

    fingerprint = _service._fingerprint(saved_filename)
    log.info("book-import: book=%s size=%s fingerprint=%s source=%s",
             book_id, file_size, fingerprint[:12], source_ref or "-")

    job_id = None
    translation_error = None
    if trigger:
        job_id, translation_error = _trigger_translation(book_id)

    if translation_error and job_id is None:
        # 文件已生效，翻译可独立补触发：502 让连接器按 §7 告警/重试
        return jsonify({"bookId": book_id, "format": "EPUB", "size": file_size,
                        "fingerprint": fingerprint, "translationJobId": None,
                        "translationError": translation_error}), 502

    return jsonify({"bookId": book_id, "format": "EPUB", "size": file_size,
                    "fingerprint": fingerprint, "translationJobId": job_id})


def _trigger_translation(book_id):
    """以配置的 admin 用户身份建整本翻译批次。

    Why: WholeBookTranslationService.start() 依赖 current_user.id 做批次归属
    与幂等复用；内部 API 无浏览器会话，按 BOOK_IMPORT_USER_ID（默认 1）登录
    系统管理员后复用既有 start() 全链路（含 fingerprint 幂等与僵尸自愈）。
    How: login_user 会把会话写进 SecureCookie session（响应带 admin cookie，
    评审实锤泄露面），调用结束立即弹出登录键，保证管理员会话不落调用方。
    """
    try:
        user_id = int(os.environ.get(USER_ID_ENV, "1"))
        user = ub.session.query(ub.User).filter(ub.User.id == user_id).first()
        if user is None or not user.role_admin():
            return None, "configured import user not found or not admin"
        login_user(user)
        try:
            publish, lookup = _system_closures()
            result = _service.start(book_id, "EPUB", False, publish, lookup)
            return result.get("jobId"), None
        finally:
            for key in ("_user_id", "_fresh", "_remember"):
                flask_session.pop(key, None)
    except Exception as e:  # noqa: BLE001 翻译失败不回滚文件（LLD §7）
        log.error("book-import: translation trigger failed for book=%s: %s", book_id, e)
        return None, str(e)

# -*- coding: utf-8 -*-

#  课级音频播放蓝图（R116③ LLD §4）：/nce/<book_id> 播放页、/lessons 课表、
#  /audio/<num> mp3 流（登录 + manifest 白名单 + Range 206）、/lyric/<num> 歌词。
#  fail-closed：main.py 仅在 MINIO_* 凭据齐备时注册本蓝图；对象名只出自
#  manifest（num 白名单），杜绝路径穿越与任意对象读取。

import logging
import re

from flask import Blueprint, Response, abort, jsonify, request, stream_with_context

from .. import calibre_db
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from . import store
from .series import resolve_nce_book_no

nce = Blueprint("nce", __name__, url_prefix="/nce")

log = logging.getLogger("cps.nce")

_CHUNK = 64 * 1024


def _book_no(book_id):
    book = calibre_db.get_book(book_id)
    if book is None:
        abort(404)
    book_no = resolve_nce_book_no(book)
    if book_no is None:
        abort(404)
    return book, book_no


def _manifest_or_503(book_no):
    try:
        return store.get_manifest(book_no)
    except Exception as e:
        log.error("nce-audio manifest book%s unavailable: %s", book_no, e)
        abort(503)


def _parse_range(header, total):
    """Return (start, end) | 'unsatisfiable' | None (serve full)."""
    if not header or total <= 0:
        return None
    m = re.match(r"^bytes=(\d*)-(\d*)$", header.strip())
    if not m or not (m.group(1) or m.group(2)):
        return None
    start_s, end_s = m.group(1), m.group(2)
    if not start_s:
        start = max(total - int(end_s), 0)
        end = total - 1
    else:
        start = int(start_s)
        if start >= total:
            return "unsatisfiable"
        end = min(int(end_s), total - 1) if end_s else total - 1
    if end < start:
        return None
    return start, end


def _stream_response(resp, mimetype, declared_length):
    def gen():
        try:
            for chunk in resp.stream(_CHUNK):
                yield chunk
        finally:
            resp.close()
            resp.release_conn()

    headers = {"Accept-Ranges": "bytes", "Content-Type": mimetype}
    if declared_length:
        headers["Content-Length"] = str(declared_length)
    return Response(stream_with_context(gen()), status=200, headers=headers)


@nce.route("/<int:book_id>")
@user_login_required
def player_page(book_id):
    book, book_no = _book_no(book_id)
    manifest = _manifest_or_503(book_no)
    return render_title_template("nce_player.html",
                                 title=book.title,
                                 book=book,
                                 book_no=book_no,
                                 lessons=manifest.get("lessons", []),
                                 page="nce")


@nce.route("/<int:book_id>/lessons")
@user_login_required
def lessons_json(book_id):
    _, book_no = _book_no(book_id)
    manifest = _manifest_or_503(book_no)
    return jsonify({"book": book_no, "lessons": manifest.get("lessons", [])})


@nce.route("/<int:book_id>/audio/<num>")
@user_login_required
def audio(book_id, num):
    _, book_no = _book_no(book_id)
    manifest = _manifest_or_503(book_no)
    lesson = store.find_lesson(manifest, num)
    if lesson is None or not lesson.get("audio"):
        abort(404)
    total = int(lesson.get("size") or 0)
    rng = _parse_range(request.headers.get("Range"), total)
    if rng == "unsatisfiable":
        return Response(status=416, headers={"Content-Range": "bytes */%d" % total,
                                             "Accept-Ranges": "bytes"})
    try:
        if rng:
            start, end = rng
            resp = store.get_object_range(book_no, lesson["audio"], start, end - start + 1)
            response = _stream_response(resp, "audio/mpeg", end - start + 1)
            response.status_code = 206
            response.headers["Content-Range"] = "bytes %d-%d/%d" % (start, end, total)
        else:
            resp = store.get_object_range(book_no, lesson["audio"])
            response = _stream_response(resp, "audio/mpeg", total)
    except Exception as e:
        log.error("nce-audio stream book%s/%s failed: %s", book_no, num, e)
        abort(503)
    return response


@nce.route("/<int:book_id>/lyric/<num>")
@user_login_required
def lyric(book_id, num):
    _, book_no = _book_no(book_id)
    manifest = _manifest_or_503(book_no)
    lesson = store.find_lesson(manifest, num)
    if lesson is None or not lesson.get("lyric"):
        abort(404)
    try:
        text = store.get_object_text(book_no, lesson["lyric"])
    except Exception as e:
        log.error("nce-audio lyric book%s/%s failed: %s", book_no, num, e)
        abort(503)
    return Response(text, mimetype="text/plain", content_type="text/plain; charset=utf-8")

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2018-2019 OzzieIsaacs, cervinko, jkrehm, bodybybuddha, ok11,
#                            andy29485, idalin, Kyosfonica, wuqi, Kennyl, lemmsh,
#                            falgh1, grunjol, csitko, ytils, xybydy, trasba, vrabe,
#                            ruben-herold, marblepebble, JackED42, SiphonSquirrel,
#                            apetresc, nanu-c, mutschler
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import json
import re
import threading
import uuid
import mimetypes
import chardet  # dependency of requests
import copy
import zipfile
import requests
from importlib.metadata import metadata
from urllib.parse import quote

from flask import Blueprint, jsonify, request, redirect, send_from_directory, make_response, flash, abort, url_for, current_app
from flask import session as flask_session
from flask_babel import gettext as _
from flask_babel import get_locale
from .cw_login import login_user, logout_user, current_user
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError
from sqlalchemy.sql.expression import text, func, false, not_, and_, or_
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.functions import coalesce
from werkzeug.datastructures import Headers
from werkzeug.security import generate_password_hash, check_password_hash

from . import constants, logger, isoLanguages, services, limiter
from . import db, ub, config, app, csrf
from . import calibre_db, kobo_sync_status
from .nce.series import resolve_nce_book_no
from .search import render_search_results, render_adv_search_results
from .gdriveutils import getFileFromEbooksFolder, do_gdrive_download
from .helper import check_valid_domain, check_email, check_username, \
    get_book_cover, get_series_cover_thumbnail, get_download_link, send_mail, generate_random_password, \
    send_registration_mail, check_send_to_ereader, check_read_formats, tags_filters, reset_password, valid_email, \
    edit_book_read_status, valid_password
from .pagination import Pagination
from .redirect import get_redirect_location
from .cw_babel import get_available_locale
from .usermanagement import login_required_if_no_ano
from .kobo_sync_status import remove_synced_book
from .render_template import render_title_template
from .kobo_sync_status import change_archived_books
from .services.worker import WorkerThread
from .tasks_status import render_task_status
from .usermanagement import user_login_required
from .string_helper import strip_whitespaces
from .reading_translation.service import WholeBookTranslationService
from .reading_tts.service import WholeBookTtsService
from .reading_word_detail.service import WordDetailBatchService
from .admin import admin_required


feature_support = {
    'ldap': bool(services.ldap),
    'goodreads': bool(services.goodreads_support),
    'kobo': bool(services.kobo)
}

try:
    from .oauth_bb import oauth_check, register_user_with_oauth, logout_oauth_user, get_oauth_status

    feature_support['oauth'] = True
except ImportError:
    feature_support['oauth'] = False
    oauth_check = {}
    register_user_with_oauth = logout_oauth_user = get_oauth_status = None

from functools import wraps

try:
    from natsort import natsorted as sort
except ImportError:
    sort = sorted  # Just use regular sort then, may cause issues with badly named pages in cbz/cbr files


sql_version = metadata("sqlalchemy")["Version"]
sqlalchemy_version2 = ([int(x) if x.isnumeric() else 0 for x in sql_version.split('.')[:3]] >= [2, 0, 0])


@app.before_request
def _begin_trace():
    """请求入口设置 trace-id（contextvar）。沿用上游 X-Trace-Id 保证全链路同一 ID。"""
    logger.trace_id_var.set(_moonwell_trace_id())


# MinIO 对外直链源清单（CSP 用；直链本身由 moon-well 按 minio.public-url 现拼，本站不代理二进制）。
# R210 过渡态：`minio.haoshenqi.top`（443 经 VPS 反代，新入口）与 `home.haoshenqi.top:9001`
# （旧入口）并列——先松 CSP、再翻 moon-well 的配置，否则翻转窗口内 TED 原声与伙伴头像会同时被拦。
# 待线上再无任何响应产出旧源（BuddyService/TedAudioService/LearningParagraphResolver 全部走新值），
# 删掉旧条目收窄，这必须是单独一笔，别夹在功能改动里。
MINIO_PUBLIC_ORIGINS = ("https://minio.haoshenqi.top", "https://home.haoshenqi.top:9001")


@app.after_request
def add_security_headers(resp):
    # trace-id 回写：报障时用户可直接提供此 ID，ES 中按 message 检索即可定位全链路日志
    resp.headers.setdefault("X-Trace-Id", _moonwell_trace_id())
    default_src = ([host.strip() for host in config.config_trustedhosts.split(',') if host] +
                   ["'self'", "'unsafe-inline'", "'unsafe-eval'"])
    csp = "default-src " + ' '.join(default_src)
    if request.endpoint == "web.read_book" and config.config_use_google_drive:
        csp +=" blob: "
    csp += "; font-src 'self' data:"
    if request.endpoint == "web.read_book":
        csp += " blob: "
        # 段落朗读经 URL.createObjectURL(blob) 生成 blob: 音频，Audio 播放走
        # media-src；CSP 未显式声明时回退 default-src（不含 blob:）导致播放被
        # 拦（控制台 "Loading media from 'blob:...' violates CSP"），必须显式放行。
        # 划词单词发音直连有道 dictvoice 词库 mp3（免费免 key），同样属 media
        # 加载，需一并放行该源（仅阅读页，其余页面不受影响）。
        # TED 类书的整段原声（R172「原声伴听」）由 moon-well 返回 MinIO 外网直链，
        # 由浏览器直连该源播放，同属 media 加载；未放行时阅读页报
        # "Loading media from '…/magicbook/ted-audio/….aac' violates … CSP directive:
        # media-src" 且静默无声（R181 复测现场），故一并放行。仅阅读页。
        # 源清单见 MINIO_PUBLIC_ORIGINS（R210：入口由 home:9001 迁到 minio.haoshenqi.top，
        # 后端同一份，过渡期两源并列）。
        csp += ("; media-src 'self' blob: https://dict.youdao.com"
                " " + " ".join(MINIO_PUBLIC_ORIGINS))
    csp += "; img-src 'self'"
    if request.path.startswith("/author/") and config.config_use_goodreads:
        csp += " images.gr-assets.com i.gr-assets.com s.gr-assets.com"
    csp += " data:"
    # 伙伴头像（R206）是 moon-well 下发的 MinIO 匿名直读直链，浏览器跨源取图；未放行时
    # <img> 被 img-src 拦，而 ai_chat.js 用 new Image() 预载探测——失败即静默保留「AI」
    # 文字兜底，故障在页面上不可见，故必须显式放行（同 R181 media-src 的踩坑口径）。
    # 沿用其窄面做法：只在悬浮按钮真正出现的阅读页与 /buddy 花名册页放行。
    if request.endpoint in ("web.read_book", "web.buddy_page"):
        csp += " " + " ".join(MINIO_PUBLIC_ORIGINS)
    if request.endpoint == "edit-book.show_edit_book" or config.config_use_google_drive:
        csp += " *"
    if request.endpoint == "web.read_book":
        csp += " blob: ; style-src-elem 'self' blob: 'unsafe-inline'"
    csp += "; object-src 'none';"
    resp.headers['Content-Security-Policy'] = csp
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
    resp.headers['X-XSS-Protection'] = '1; mode=block'
    resp.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return resp


web = Blueprint('web', __name__)

whole_book_translation_service = WholeBookTranslationService()

log = logger.create()


# ################################### Login logic and rights management ###############################################


def download_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if current_user.role_download():
            return f(*args, **kwargs)
        abort(403)

    return inner


def viewer_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if current_user.role_viewer():
            return f(*args, **kwargs)
        abort(403)

    return inner


# ################################### data provider functions #########################################################


@web.route("/ajax/emailstat")
@user_login_required
def get_email_status_json():
    tasks = WorkerThread.get_instance().tasks
    return jsonify(render_task_status(tasks))


@web.route("/ajax/bookmark/<int:book_id>/<book_format>", methods=['POST'])
@user_login_required
def set_bookmark(book_id, book_format):
    bookmark_key = request.form["bookmark"]
    ub.session.query(ub.Bookmark).filter(and_(ub.Bookmark.user_id == int(current_user.id),
                                              ub.Bookmark.book_id == book_id,
                                              ub.Bookmark.format == book_format)).delete()
    if not bookmark_key:
        ub.session_commit()
        return "", 204

    l_bookmark = ub.Bookmark(user_id=current_user.id,
                             book_id=book_id,
                             format=book_format,
                             bookmark_key=bookmark_key)
    ub.session.merge(l_bookmark)
    ub.session_commit("Bookmark for user {} in book {} created".format(current_user.id, book_id))
    return "", 201


@web.route("/ajax/toggleread/<int:book_id>", methods=['POST'])
@user_login_required
def toggle_read(book_id):
    message = edit_book_read_status(book_id)
    if message:
        return message, 400
    else:
        # 桥接 moon-well：置已读时触发 BOOKS_FINISHED 事件供成就判定（异步，失败不影响主链路）。
        # Why: 成就只消费 moon-well 自家 book 域事件，不桥接则读完 Calibre 书永远不解锁成就（R64）。
        try:
            read_now = ub.session.query(ub.ReadBook).filter(
                ub.ReadBook.user_id == int(current_user.id),
                ub.ReadBook.book_id == book_id).first()
            is_finished = bool(read_now and read_now.read_status == ub.ReadBook.STATUS_FINISHED)
        except Exception:
            is_finished = False
        if is_finished:
            _moonwell_book_finished_bridge(book_id, True)
        return message


@web.route("/ajax/togglearchived/<int:book_id>", methods=['POST'])
@user_login_required
def toggle_archived(book_id):
    change_archived_books(book_id, message="Book {} archive bit toggled".format(book_id))
    # Remove book from syncd books list to force resync (?)
    remove_synced_book(book_id)
    return ""


@web.route("/ajax/view", methods=["POST"])
@login_required_if_no_ano
def update_view():
    to_save = request.get_json()
    try:
        for element in to_save:
            for param in to_save[element]:
                current_user.set_view_property(element, param, to_save[element][param])
    except Exception as ex:
        log.error("Could not save view_settings: %r %r: %e", request, to_save, ex)
        return "Invalid request", 400
    return "1", 200












# ---------- R172 TED 原声伴听代理（TED/博客类书：整段原声，非逐段 TTS） ----------

def _ted_book_identity():
    """把前端传来的 Calibre 书号解析成 moon-well 认的「书名 + 作者」身份。

    Why（R200）：moon-well `/book/ted-audio` 的 bookId 是它自己 book 表的 id，
    与 Calibre 书号是两套自增序列（learning R139/R149 同款坑）——只有巧合对齐
    才命中；错位时上游返回 null，前端静默回落 TTS 机器音，用户只听到合成音。
    段落注册表本身按 title+author 索引，按书名查可彻底绕开 ID 空间不一致。

    How: 返回 (bookName, author, error)，error 为 None 表示成功；非数字 bookId
    仍在代理层挡成 400（脏串不往上游送），书不存在给 404。
    """
    payload = request.get_json(silent=True) or {}
    raw = str(payload.get("bookId", "")).strip()
    if not raw.isdigit():
        return None, None, ("bad_request", "bookId must be a number")
    book = calibre_db.get_book(int(raw))
    if not book:
        return None, None, ("not_found", "book not found")
    author = " & ".join(a.name for a in book.authors) if book.authors else ""
    return book.title or "", author, None








@web.route("/achievements", methods=["GET"])
@user_login_required
def achievements_page():
    """成就中心页：等级/XP/徽章墙，数据经 /ajax/achievements-* 异步加载。"""
    return render_title_template("achievements.html", title=_("Achievements"))






















# ---------- 积分充值（moon-well credit 模块代理） ----------
# Why: 订阅套餐暂时隐藏（R61），页面仅提供积分充值；subscription 代理保留以便随时恢复























# ---------- 词汇量测试代理（R116/US4）----------
#
# Why 薄透传、不在代理层翻译错误码：出题状态机、会话归属、超时判定全在 moon-well，
# 50301/50302/50303/50304 的语义只有它知道；代理复制一份判定等于把状态机搬错地方，
# 还会与后端演进脱节。代理只做参数域校验（挡住明显非法请求，省一次内网往返），
# 业务错误按原状态码与 Result 信封透传，前端按 Result.code 分支。


def _vt_positive_int(value):
    """取 JSON 里的正整数 id，非法返回 None。

    Why 显式排除 bool：Python 里 bool 是 int 的子类，客户端传 {"sessionId": true}
    会被 isinstance(x, int) 接受成 1，进而打到别人的会话上（归属校验会拒绝，但
    错误形态不该靠后端兜）。
    """
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value










# ---------- 每日学习代理（R132 / B3）----------
#
# Why 薄透传（同词汇量测试）：SRS 调度、四股配比、难度匹配全在 moon-well learning 模块，
# 50501-50506 的语义只有它知道；代理只做登录与参数域校验，业务错误按原状态码与
# Result 信封透传，前端按 Result.code 分支。



















# ---------- B1 输出训练代理（R152）。 ----------
# Why 薄透传（同 srs/answer）：写作/口语/复述的业务校验与 LLM 编排在 moon-well
# learning 模块，代理只挡「明显非法」——非 JSON 对象、字段类型/长度越界；业务
# 语义（场景枚举、评分、会话归属）归上游。LLM 密集端点超时给长（批改/出题/报告
# 实测 10-40s），纯指标端点给短。

_PROXY_LIMITS = {
    "taskId": 64, "sessionId": 64, "submissionId": 64, "retellId": 64,
    "scenario": 16, "scenarioLabel": 60, "coachStyle": 16, "mode": 16,
    "cefrLevel": 8, "bookId": 64, "bookTitle": 200, "chapter": 100,
    "prompt": 500, "text": 20000, "paragraphText": 20000, "transcript": 20000,
    "storyWords": 2000, "storyId": 64,
}


def _b1_payload(allowed, required=()):
    """校验并裁剪 B1 代理的 JSON 请求体：只留白名单字段，字符串限长、整数限幅。

    Why 白名单裁剪而非逐路由手写：B1 十二个端点的 payload 全是字符串/少量
    整数字段，语义校验在上游 @Valid + Service；代理统一的职责是防客户端把
    垃圾字段（超长文本/未知键/离谱数值）透传进 LLM 链路。返回 None 表示本地 400。
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None
    cleaned = {}
    for key in allowed:
        if key not in payload or payload[key] is None:
            continue
        value = payload[key]
        if key in ("durationMs", "round", "order"):
            # 整数字段：保类型透传（Jackson 语义一致），限幅防溢出
            if isinstance(value, bool) or not isinstance(value, int) \
                    or not 0 <= value <= 10 ** 9:
                return None
            cleaned[key] = value
            continue
        if key == "minutesPerRound":
            if not isinstance(value, list) or not value or len(value) > 5 or \
                    any(isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 30
                        for v in value):
                return None
            cleaned[key] = value
            continue
        if key == "addUnknown":
            if not isinstance(value, bool):
                return None
            cleaned[key] = value
            continue
        if isinstance(value, bool) or not isinstance(value, str):
            return None
        if not value or len(value) > _PROXY_LIMITS.get(key, 200):
            return None
        cleaned[key] = value
    for key in required:
        if key not in cleaned:
            return None
    return cleaned


def _b1_proxy(path, allowed, required=(), timeout=30):
    body = _b1_payload(allowed, required)
    if body is None:
        return jsonify({"success": False, "message": "invalid request body"}), 400
    return _moonwell_proxy(path, body, timeout, "learning b1: " + path)




























# ---------- B2/B3 输出扩展代理（R153：计时重读 + 听写；素材接口共用） ----------






























def _whole_book_closures():
    """构造整本翻译的 publish/lookup 闭包（start/retry/status 共用）。

    Why: 发布/重发布在 daemon 后台线程执行，线程内没有 Flask 请求上下文，
    闭包若在此时才解析身份（current_user / flask_session）会 RuntimeError，
    全部段落被标 FAILED。令牌必须在请求线程内先定格为纯数据快照，
    经 _moonwell_proxy 的 bearer_token 传入。
    status 接口的 lookup 虽在请求线程同步执行，复用同一闭包保持行为一致。
    """
    token = flask_session.get("moonwell_access_token")

    def publish(task_payload):
        if not token:
            raise ValueError("moon-well authorization is required")
        response = _moonwell_proxy("/llm/task/publish", task_payload, 20,
                                   "whole-book translation",
                                   bearer_token=token)
        if not isinstance(response, tuple) or len(response) < 2:
            raise ValueError("moon-well authorization is required")
        body, status = response[0], response[1]
        if status < 200 or status >= 300:
            raise ValueError("moon-well task publish failed")
        return json.loads(body)

    def lookup(paragraphs):
        if not token:
            return {}
        response = _moonwell_proxy("/reading/paragraph-cache/find-translations",
                                   {"paragraphs": paragraphs}, 20, "translation cache",
                                   bearer_token=token)
        if not isinstance(response, tuple) or response[1] < 200 or response[1] >= 300:
            return {}
        data = json.loads(response[0])
        return data.get("result", {}) if isinstance(data, dict) else {}

    return publish, lookup










# --------------------------------------------------------------------
# 批量整本翻译（R77）：一键翻译全部英文书——每本直接建批次立即执行
# （缓存回收 + 只发缺失段，与单本按钮同语义）；正在跑的书自动跳过。
# --------------------------------------------------------------------






# --------------------------------------------------------------------
# 整本朗读（TTS 预生成，magicbook R166）：批次受理/进度/重试/取消。
# Why admin 门禁与整本翻译一致：整本合成消耗大（发起者按字符计费）。
# 身份经 _whole_book_tts_closures 在请求线程定格（daemon 线程无 Flask 上下文）。
# --------------------------------------------------------------------

whole_book_tts_service = WholeBookTtsService(None)  # proxy 由 start/retry 注入（路由层闭包定格身份）


def _whole_book_tts_proxy_factory(token):
    """构造整本朗读专用的 moon-well 代理闭包（令牌在请求线程定格为快照）。"""

    def _proxy(path, payload, timeout, label, binary=False, method="POST", **kwargs):
        return _moonwell_proxy(path, payload, timeout, label, binary=binary,
                               method=method, bearer_token=token)
    return _proxy


def _whole_book_tts_closures():
    token = flask_session.get("moonwell_access_token")
    if not token:
        raise ValueError("moon-well authorization is required")
    return _whole_book_tts_proxy_factory(token)










@web.route("/translate-all", methods=["GET"])
@user_login_required
@admin_required
def translate_all_page():
    return render_title_template("translate_all.html", title=(_("Translate All English Books")),
                                 page="translate_all")


# --------------------------------------------------------------------
# 全文单词详解（R176，对端 moon-well R188）：给一本书把「查不到详解的词」
# 补进详解缓存。与整本翻译/整本朗读并列的第三个整本能力，但刻意是**两步式**
# （预览→入队）：详解是全仓最贵的调用且按发起者计费（R106 实测单次 21.6s），
# 而「这本书到底缺多少个词」在真书上没有实测样本（小说去重词 5k~15k），
# 必须先让管理员看到数字再点第二次（同 R118 US4「先预案后执行」）。
# 门禁沿用 _llm_task_admin_gate：真正的白名单在 moon-well 侧二检
# （ai.llm.task-manual-run.admin-user-ids），这里只挡 UI 入口，纵深防御同 R126。
# --------------------------------------------------------------------

word_detail_batch_service = WordDetailBatchService()

_WORD_DETAIL_PATHS = {
    "cachedCheck": "/vocabulary/detail/cached-check",
    "warmByWords": "/vocabulary/detail/warm-publish-by-words",
}


def _word_detail_unwrap(response, label):
    """解 moon-well 的 Result 包装并取出 result；任何失败都抛带原文案的 ValueError。

    Why 不静默返回空：接口故障若被降级成「缓存里没有」，页面就把故障显示成
    「这本书还缺 N 个词」，用户报回来的永远是错误结论（家族纪律：失败必须在界面上可见）。
    Why 透传 message：灌队闸门（在途上限、单次词数上限）都以 GlobalException 报业务文案，
    吞掉它用户只剩一个 500，无从判断是该分批还是该等资源。
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


def _word_detail_closures():
    """check/publish 两个闭包：令牌在请求线程定格成快照。

    Why 快照而不是线程内读 session：发布在 daemon 线程分批跑，线程里没有 Flask
    请求上下文，那时再解析 current_user/flask_session 会 RuntimeError，
    整批被标 FAILED（整本翻译 R78 生产事故同款）。
    """
    token = flask_session.get("moonwell_access_token")

    def check(words):
        if not token:
            raise ValueError("moon-well authorization is required")
        return _word_detail_unwrap(_moonwell_proxy(_WORD_DETAIL_PATHS["cachedCheck"],
                                                   {"words": list(words)}, 30,
                                                   "word detail cached check",
                                                   bearer_token=token), "cached-check")

    def publish(payload):
        if not token:
            raise ValueError("moon-well authorization is required")
        return _word_detail_unwrap(_moonwell_proxy(_WORD_DETAIL_PATHS["warmByWords"],
                                                   payload, 60,
                                                   "word detail warm publish",
                                                   bearer_token=token), "warm-publish-by-words")

    return check, publish


@web.route("/ajax/word-detail-preview", methods=["POST"])
@user_login_required
def reading_word_detail_preview():
    """只读预览：这本书的去重词数 / 已缓存 / 待生成 / 粗算 tokens。

    Why 只拿 check 闭包：预览路径**没有** publish 能力，把「不产生副作用」做成
    结构约束而不是靠约定（单测据此断言 warm-publish-by-words 一次都没被调）。
    """
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    try:
        book_id = int(payload.get("book_id"))
        book_format = str(payload.get("book_format") or "epub").lower()
        check, _ = _word_detail_closures()
        return jsonify(word_detail_batch_service.preview(book_id, book_format, check))
    except (TypeError, ValueError, OSError, zipfile.BadZipFile) as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/word-detail-start", methods=["POST"])
@user_login_required
def reading_word_detail_start():
    """建台账并后台分批入队；HTTP 立即返回批次快照。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    try:
        book_id = int(payload.get("book_id"))
        book_format = str(payload.get("book_format") or "epub").lower()
        force = bool(payload.get("force", False))
        check, publish = _word_detail_closures()
        return jsonify(word_detail_batch_service.start(book_id, book_format, force, publish, check))
    except (TypeError, ValueError, OSError, zipfile.BadZipFile) as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/word-detail-progress", methods=["POST"])
@user_login_required
def reading_word_detail_progress():
    """覆盖率进度（轮询）：顺带做一轮缓存懒回收。

    Why 进度口径是覆盖率而不是任务状态：详解的执行方是队列消费者，magicbook 既不是
    发起者也不是唯一消费者；把 COMPLETED 当完成还会踩 R188 记下的坑——
    872 条 COMPLETED 里约 202 条产出不合契约、缓存里根本没有。
    """
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    try:
        job_id = payload.get("job_id")
        if not job_id:
            book_id = int(payload.get("book_id"))
            job = word_detail_batch_service.latest_job(book_id)
            if not job:
                return jsonify({"status": "NONE"})
            job_id = job.id
        check, _ = _word_detail_closures()
        return jsonify(word_detail_batch_service.get_progress(str(job_id), check))
    except (TypeError, ValueError) as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/word-detail-cancel", methods=["POST"])
@user_login_required
def reading_word_detail_cancel():
    """停止本批次继续入队（已入队的任务仍由队列消费者生成，不归本接口管）。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(word_detail_batch_service.cancel(str(payload.get("job_id"))))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/word-detail-batch", methods=["GET"])
@user_login_required
@admin_required
def word_detail_batch_page():
    """按书补缺单词详解面板：打开即预览（只读），第二次点击才入队。"""
    book_id = request.args.get("book_id", "")
    # 与 learning_match_book 同款入参校验：非数字必须挡住，不能让 int() 在模板里炸成 500
    if not re.match(r"^\d+$", str(book_id)):
        abort(400)
    book_format = str(request.args.get("book_format") or "epub").lower()
    return render_title_template("word_detail_batch.html", title=(_("Whole-book Word Details")),
                                 page="word_detail_batch", book_id=int(book_id),
                                 book_format=book_format)


# --------------------------------------------------------------------
# LLM 任务手动执行面板（R126，对齐 moon-well R110 US3）：管理员选
# provider / model / 并发 / 本批上限，手动消费 moon-well 的 llm task 队列，
# 可查进度与停止。这里是薄代理——真正的门禁在 moon-well
# （ai.llm.task-manual-run.admin-user-ids 白名单二次校验），magicbook 的
# admin_required 只挡 UI 入口；与 /ajax/credit/admin-adjust 同一纵深防御形态。
# Why 不把 /llm/task/run* 加进 moon-well 的内网互信白名单：手跑会真实消耗
# 模型配额并把上万行改成 RUNNING，必须带着管理员本人的 token 才能归因。
# --------------------------------------------------------------------

_LLM_TASK_PATHS = {
    "options": "/llm/task/run/options",
    "run": "/llm/task/run",
    "status": "/llm/task/run/status",
    "stop": "/llm/task/run/stop",
    # R130（队列监控，对齐 moon-well R118）：读路径为主；republish 是唯一写路径，
    # 两步走（plan 不带 confirm 零写库 → 用户二次确认后才带 confirm）由前端驱动、
    # 服务端兜底——代理层不做字段改写，保持与 run 同款的「两侧 DTO 直接对齐」决策。
    "overview": "/llm/task/admin/overview",
    "failures": "/llm/task/admin/failures",
    "admin_page": "/llm/task/admin/page",
    "task_detail": "/llm/task/detail",
    "recovery_plan": "/llm/task/admin/recovery-plan",
    "republish": "/llm/task/admin/republish-failed",
}




def _llm_task_admin_gate():
    """JSON 入口的管理员门禁。

    Why 不用 @admin_required：它走 abort(403) 返回 HTML，前端 fetch 只能显示
    「HTTP 403」；面板需要可读文案，故与 /ajax/credit/admin-adjust 同一形态
    （handler 内判 role_admin 返回 JSON 403）。页面路由 /llm-tasks 仍用装饰器。
    """
    if not current_user.role_admin():
        return jsonify({"success": False, "message": _("admin only")}), 403
    return None










# ---- R178（架构评审 B1）：moon-well 防腐层本体已迁 cps/moonwell/client.py ----
# 以下薄委托保留原函数名：web.py 内 ~70 处调用点零改动，上游 merge 冲突面最小。
# 返回形态契约统一为三元组 (body, status, headers)，失败分支同样是三元组（手拼
# JSON，daemon 线程安全）——「失败二元组/成功三元组」的隐式契约（解包即
# ValueError→500）就此消灭。_moonwell_book_finished_bridge（业务编排 107 行）
# 属 B2 蓝图分域范围，暂留本文件。
from cps.moonwell.client import NO_PROXY, client as _moonwell_client

_MOONWELL_NO_PROXY = NO_PROXY


def _moonwell_base_url():
    return _moonwell_client.base_url()


def _moonwell_trace_id():
    return _moonwell_client.trace_id()


def _moonwell_system_token():
    return _moonwell_client.system_token()


def _moonwell_proxy(path, payload, timeout, label, binary=False, method="POST",
                    system_identity=False, bearer_token=None):
    return _moonwell_client.proxy(path, payload, timeout, label, binary=binary,
                                  method=method, system_identity=system_identity,
                                  bearer_token=bearer_token)


def _moonwell_refresh_session_token():
    return _moonwell_client.refresh_session_token()


def _moonwell_multipart(path, file_bytes, filename, timeout, label):
    return _moonwell_client.multipart(path, file_bytes, filename, timeout, label)



def _moonwell_settings_fetch():
    return _moonwell_client.settings_fetch()












# 划词标记的词形白名单：字母开头/结尾，中间仅字母/撇号/连字符。首尾
# 必须是字母——与 markVocabulary 分词正则的 \b 边界语义对齐（尾部带
# 撇号/连字符的 key 在页面标注中永远匹配不上，会存成脏数据）。词会
# 拼进 moon-well 的请求 path，必须严格防御注入。
_READING_WORD_RE = re.compile(r"^[A-Za-z](?:[A-Za-z'\u2019-]*[A-Za-z])?$")






def _moonwell_book_finished_bridge(book_id, read_status, title=None, authors=None):
    """已读状态变更后，向 moon-well 桥接同步（成就系统只认 moon-well 自家 book 域事件）。

    Why: Calibre 书库（本站）与 moon-well book 域是两套独立数据，成就是否解锁完全看
    moon-well 侧 BOOKS_FINISHED 事件（/book/update 置 FINISHED 或进度 100%）。不在
    toggleread 后桥接，用户读完 Calibre 里的任何书都不会触发成就（R64 根因）。

    策略：
    - 仅在置为已读（read_status=True）时同步：取消已读不回退成就（成就计数以 FINISHED
      状态收敛去重，反向操作无对应语义）；
    - 优先在用户 moon-well 书架按书名精确检索，命中则复用已有书籍 id；
    - 未命中则登记新书（附带 Calibre 书名/作者，书架页可识别来源）；
    - 重复置已读不重复解锁（moon-well 侧 justFinished 幂等，双保险）；
    - 全程失败只记日志，绝不影响本站已读状态变更主链路。
    """
    if not read_status:
        return

    # Why: worker 运行在后台线程，没有 Flask request 上下文——令牌必须在启动线程
    # （即 toggleread 请求处理线程，持有 flask_session）内取好快照再传入（R65 测试发现）。
    # R145 全 token 化：书架归属跟用户走，快照只带用户 token；无请求上下文或无 token
    # 一律跳过桥接（flask_session 在裸 app_context 下 get 会 RuntimeError）。
    try:
        token = flask_session.get("moonwell_access_token")
    except RuntimeError:
        token = None
    if not token:
        log.warning("moonwell book bridge: no moon-well token for book %s, skip", book_id)
        return

    def _worker(book_id=book_id, title=title, authors=authors, token=token):
        try:
            with app.app_context():

                # 书名/作者缺省时查本站书库补全
                if not title or not authors:
                    try:
                        entries = calibre_db.get_filtered_book(book_id)
                        if entries:
                            title = entries.title or title
                            authors = " & ".join(a.name for a in entries.authors) if entries.authors else authors
                    except Exception:
                        pass
                if not title:
                    log.warning("moonwell book bridge: book %s has no title, skip", book_id)
                    return

                # 1) 先按书名查用户 moon-well 书架，命中则复用已有书籍 id
                book_id_mw = None
                body, status, _h = _moonwell_proxy(
                    "/book/page", {"page": 1, "size": 100, "keyword": title}, 15,
                    "moonwell book bridge page", bearer_token=token)
                if 200 <= status < 300:
                    try:
                        data = json.loads(body)
                        if data.get("success") and data.get("result"):
                            records = data["result"].get("records") or data["result"].get("list") or []
                            for rec in records:
                                if (rec.get("title") or "").strip() == title.strip():
                                    book_id_mw = str(rec.get("id"))
                                    break
                    except (ValueError, TypeError):
                        pass

                # 2) 未命中则登记新书（readingStatus 默认 UNREAD）
                if not book_id_mw:
                    create_payload = {
                        "title": title[:255],
                        "author": (authors or "Unknown")[:255],
                    }
                    body, status, _h = _moonwell_proxy(
                        "/book/create", create_payload, 15, "moonwell book bridge create",
                        bearer_token=token)
                    if 200 <= status < 300:
                        try:
                            data = json.loads(body)
                            if data.get("success") and data.get("result"):
                                book_id_mw = str(data["result"].get("id"))
                        except (ValueError, TypeError):
                            pass
                    if not book_id_mw:
                        log.warning("moonwell book bridge: create failed for book %s (%s): HTTP %s %s",
                                    book_id, title, status, (body or "")[:200])
                        return

                # 3) 置 FINISHED 触发 BOOKS_FINISHED 事件（重复置已读由 justFinished 幂等兜底）
                update_payload = {
                    "id": book_id_mw,
                    "title": title[:255],
                    "author": (authors or "Unknown")[:255],
                    "readingStatus": "FINISHED",
                }
                body, status, _h = _moonwell_proxy(
                    "/book/update", update_payload, 15, "moonwell book bridge update",
                    bearer_token=token)
                if 200 <= status < 300:
                    log.info("moonwell book bridge: book %s -> moonwell book %s FINISHED ok",
                             book_id, book_id_mw)
                else:
                    log.warning("moonwell book bridge: update failed for book %s (%s): HTTP %s %s",
                                book_id, title, status, (body or "")[:200])
        except Exception:
            log.error_or_exception("moonwell book bridge unexpected error for book %s" % book_id)

    threading.Thread(target=_worker, name="moonwell-book-bridge", daemon=True).start()


@web.route("/ajax/getcomic/<int:book_id>/<book_format>/<int:page>")
@user_login_required
def get_comic_book(book_id, book_format, page):
    book = calibre_db.get_book(book_id)
    if not book:
        return "", 204
    else:
        for bookformat in book.data:
            if bookformat.format.lower() == book_format.lower():
                cbr_file = os.path.join(config.config_calibre_dir, book.path, bookformat.name) + "." + book_format
                if book_format in ("cbr", "rar"):
                    if feature_support['rar'] == True:
                        rarfile.UNRAR_TOOL = config.config_rarfile_location
                        try:
                            rf = rarfile.RarFile(cbr_file)
                            names = sort(rf.namelist())
                            extract = lambda page: rf.read(names[page])
                        except:
                            # rarfile not valid
                            log.error('Unrar binary not found, or unable to decompress file %s', cbr_file)
                            return "", 204
                    else:
                        log.info('Unrar is not supported please install python rarfile extension')
                        # no support means return nothing
                        return "", 204
                elif book_format in ("cbz", "zip"):
                    zf = zipfile.ZipFile(cbr_file)
                    names=sort(zf.namelist())
                    extract = lambda page: zf.read(names[page])
                elif book_format in ("cbt", "tar"):
                    tf = tarfile.TarFile(cbr_file)
                    names=sort(tf.getnames())
                    extract = lambda page: tf.extractfile(names[page]).read()
                else:
                    log.error('unsupported comic format')
                    return "", 204

                b64 = codecs.encode(extract(page), 'base64').decode()
                ext = names[page].rpartition('.')[-1]
                if ext not in ('png', 'gif', 'jpg', 'jpeg', 'webp'):
                    ext = 'png'
                extractedfile="data:image/" + ext + ";base64," + b64
                fileData={"name": names[page], "page":page, "last":len(names)-1, "content": extractedfile}
                return make_response(json.dumps(fileData))
        return "", 204


# ################################### Typeahead ##################################################################


@web.route("/get_authors_json", methods=['GET'])
@login_required_if_no_ano
def get_authors_json():
    return calibre_db.get_typeahead(db.Authors, request.args.get('q'), ('|', ','))


@web.route("/get_publishers_json", methods=['GET'])
@login_required_if_no_ano
def get_publishers_json():
    return calibre_db.get_typeahead(db.Publishers, request.args.get('q'), ('|', ','))


@web.route("/get_tags_json", methods=['GET'])
@login_required_if_no_ano
def get_tags_json():
    return calibre_db.get_typeahead(db.Tags, request.args.get('q'), tag_filter=tags_filters())


@web.route("/get_series_json", methods=['GET'])
@login_required_if_no_ano
def get_series_json():
    return calibre_db.get_typeahead(db.Series, request.args.get('q'))


@web.route("/get_languages_json", methods=['GET'])
@login_required_if_no_ano
def get_languages_json():
    query = (request.args.get('q') or '').lower()
    language_names = isoLanguages.get_language_names(get_locale())
    entries_start = [s for key, s in language_names.items() if s.lower().startswith(query.lower())]
    if len(entries_start) < 5:
        entries = [s for key, s in language_names.items() if query in s.lower()]
        entries_start.extend(entries[0:(5 - len(entries_start))])
        entries_start = list(set(entries_start))
    json_dumps = json.dumps([dict(name=r) for r in entries_start[0:5]])
    return json_dumps


@web.route("/get_matching_tags", methods=['GET'])
@login_required_if_no_ano
def get_matching_tags():
    tag_dict = {'tags': []}
    q = calibre_db.session.query(db.Books).filter(calibre_db.common_filters(True))
    calibre_db.create_functions()
    author_input = request.args.get('authors') or ''
    title_input = request.args.get('title') or ''
    include_tag_inputs = request.args.getlist('include_tag') or ''
    exclude_tag_inputs = request.args.getlist('exclude_tag') or ''
    q = q.filter(db.Books.authors.any(func.lower(db.Authors.name).ilike("%" + author_input + "%")),
                 func.lower(db.Books.title).ilike("%" + title_input + "%"))
    if len(include_tag_inputs) > 0:
        for tag in include_tag_inputs:
            q = q.filter(db.Books.tags.any(db.Tags.id == tag))
    if len(exclude_tag_inputs) > 0:
        for tag in exclude_tag_inputs:
            q = q.filter(not_(db.Books.tags.any(db.Tags.id == tag)))
    for book in q:
        for tag in book.tags:
            if tag.id not in tag_dict['tags']:
                tag_dict['tags'].append(tag.id)
    json_dumps = json.dumps(tag_dict)
    return json_dumps


def generate_char_list(entries): # data_colum, db_link):
    char_list = list()
    for entry in entries:
        upper_char = entry[0].name[0].upper()
        if upper_char not in char_list:
            char_list.append(upper_char)
    return char_list


def query_char_list(data_colum, db_link):
    results = (calibre_db.session.query(func.upper(func.substr(data_colum, 1, 1)).label('char'))
            .join(db_link).join(db.Books).filter(calibre_db.common_filters())
            .group_by(func.upper(func.substr(data_colum, 1, 1))).all())
    return results


def get_sort_function(sort_param, data):
    order = [db.Books.timestamp.desc()]
    if sort_param == 'stored':
        sort_param = current_user.get_view_property(data, 'stored')
    else:
        current_user.set_view_property(data, 'stored', sort_param)
    if sort_param == 'pubnew':
        order = [db.Books.pubdate.desc()]
    if sort_param == 'pubold':
        order = [db.Books.pubdate]
    if sort_param == 'abc':
        order = [db.Books.sort]
    if sort_param == 'zyx':
        order = [db.Books.sort.desc()]
    if sort_param == 'new':
        order = [db.Books.timestamp.desc()]
    if sort_param == 'old':
        order = [db.Books.timestamp]
    if sort_param == 'authaz':
        order = [db.Books.author_sort.asc(), db.Series.name, db.Books.series_index]
    if sort_param == 'authza':
        order = [db.Books.author_sort.desc(), db.Series.name.desc(), db.Books.series_index.desc()]
    if sort_param == 'seriesasc':
        order = [db.Books.series_index.asc()]
    if sort_param == 'seriesdesc':
        order = [db.Books.series_index.desc()]
    if sort_param == 'hotdesc':
        order = [func.count(ub.Downloads.book_id).desc()]
    if sort_param == 'hotasc':
        order = [func.count(ub.Downloads.book_id).asc()]
    if sort_param is None:
        sort_param = "new"
    return order, sort_param


def render_books_list(data, sort_param, book_id, page):
    order = get_sort_function(sort_param, data)
    if data == "rated":
        return render_rated_books(page, book_id, order=order)
    elif data == "discover":
        return render_discover_books(book_id)
    elif data == "unread":
        return render_read_books(page, False, order=order)
    elif data == "read":
        return render_read_books(page, True, order=order)
    elif data == "hot":
        return render_hot_books(page, order)
    elif data == "download":
        return render_downloaded_books(page, order, book_id)
    elif data == "author":
        return render_author_books(page, book_id, order)
    elif data == "publisher":
        return render_publisher_books(page, book_id, order)
    elif data == "series":
        return render_series_books(page, book_id, order)
    elif data == "ratings":
        return render_ratings_books(page, book_id, order)
    elif data == "formats":
        return render_formats_books(page, book_id, order)
    elif data == "category":
        return render_category_books(page, book_id, order)
    elif data == "language":
        return render_language_books(page, book_id, order)
    elif data == "archived":
        return render_archived_books(page, order)
    elif data == "search":
        term = request.args.get('query', None)
        offset = int(int(config.config_books_per_page) * (page - 1))
        return render_search_results(term, offset, order, config.config_books_per_page)
    elif data == "advsearch":
        term = json.loads(flask_session.get('query', '{}'))
        offset = int(int(config.config_books_per_page) * (page - 1))
        return render_adv_search_results(term, offset, order, config.config_books_per_page)
    else:
        website = data or "newest"
        entries, random, pagination = calibre_db.fill_indexpage(page, 0, db.Books, True, order[0],
                                                                True, config.config_read_column,
                                                                db.books_series_link,
                                                                db.Books.id == db.books_series_link.c.book,
                                                                db.Series)
        return render_title_template('index.html', random=random, entries=entries, pagination=pagination,
                                     title=_("Books"), page=website, order=order[1])


def render_rated_books(page, book_id, order):
    if current_user.check_visibility(constants.SIDEBAR_BEST_RATED):
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db.Books.ratings.any(db.Ratings.rating > 9),
                                                                order[0],
                                                                True, config.config_read_column,
                                                                db.books_series_link,
                                                                db.Books.id == db.books_series_link.c.book,
                                                                db.Series)

        return render_title_template('index.html', random=random, entries=entries, pagination=pagination,
                                     id=book_id, title=_("Top Rated Books"), page="rated", order=order[1])
    else:
        abort(404)


def render_discover_books(book_id):
    if current_user.check_visibility(constants.SIDEBAR_RANDOM):
        entries, __, ___ = calibre_db.fill_indexpage(1, 0, db.Books, True, [func.randomblob(2)],
                                                            join_archive_read=True,
                                                            config_read_column=config.config_read_column)
        pagination = Pagination(1, config.config_books_per_page, config.config_books_per_page)
        return render_title_template('index.html', random=false(), entries=entries, pagination=pagination, id=book_id,
                                     title=_("Discover (Random Books)"), page="discover")
    else:
        abort(404)


def render_hot_books(page, order):
    if current_user.check_visibility(constants.SIDEBAR_HOT):
        if order[1] not in ['hotasc', 'hotdesc']:
            # Unary expression comparison only working (for this expression) in sqlalchemy 1.4+
            # if not (order[0][0].compare(func.count(ub.Downloads.book_id).desc()) or
            #        order[0][0].compare(func.count(ub.Downloads.book_id).asc())):
            order = [func.count(ub.Downloads.book_id).desc()], 'hotdesc'
        if current_user.show_detail_random():
            random_query = calibre_db.generate_linked_query(config.config_read_column, db.Books)
            random = (random_query.filter(calibre_db.common_filters())
                     .order_by(func.random())
                     .limit(config.config_random_books).all())
        else:
            random = false()

        off = int(int(config.config_books_per_page) * (page - 1))
        all_books = ub.session.query(ub.Downloads, func.count(ub.Downloads.book_id)) \
            .order_by(*order[0]).group_by(ub.Downloads.book_id)
        hot_books = all_books.offset(off).limit(config.config_books_per_page)
        entries = list()
        for book in hot_books:
            query = calibre_db.generate_linked_query(config.config_read_column, db.Books)
            download_book = query.filter(calibre_db.common_filters()).filter(
                book.Downloads.book_id == db.Books.id).first()
            if download_book:
                entries.append(download_book)
            else:
                ub.delete_download(book.Downloads.book_id)
        num_books = entries.__len__()
        pagination = Pagination(page, config.config_books_per_page, num_books)
        return render_title_template('index.html', random=random, entries=entries, pagination=pagination,
                                     title=_("Hot Books (Most Downloaded)"), page="hot", order=order[1])
    else:
        abort(404)


def render_downloaded_books(page, order, user_id):
    if current_user.role_admin():
        user_id = int(user_id)
    else:
        user_id = current_user.id
    user = ub.session.query(ub.User).filter(ub.User.id == user_id).first()
    if current_user.check_visibility(constants.SIDEBAR_DOWNLOAD) and user:
        entries, random, pagination = calibre_db.fill_indexpage(page,
                                                            0,
                                                            db.Books,
                                                            ub.Downloads.user_id == user_id,
                                                            order[0],
                                                            True, config.config_read_column,
                                                            db.books_series_link,
                                                            db.Books.id == db.books_series_link.c.book,
                                                            db.Series,
                                                            ub.Downloads, db.Books.id == ub.Downloads.book_id)
        for book in entries:
            if not (calibre_db.session.query(db.Books).filter(calibre_db.common_filters())
                    .filter(db.Books.id == book.Books.id).first()):
                ub.delete_download(book.Books.id)
        return render_title_template('index.html',
                                     random=random,
                                     entries=entries,
                                     pagination=pagination,
                                     id=user_id,
                                     title=_("Downloaded books by %(user)s", user=user.name),
                                     page="download",
                                     order=order[1])
    else:
        abort(404)


def render_author_books(page, author_id, order):
    entries, __, pagination = calibre_db.fill_indexpage(page, 0,
                                                        db.Books,
                                                        db.Books.authors.any(db.Authors.id == author_id),
                                                        [order[0][0], db.Series.name, db.Books.series_index],
                                                        True, config.config_read_column,
                                                        db.books_series_link,
                                                        db.books_series_link.c.book == db.Books.id,
                                                        db.Series)
    if entries is None or not len(entries):
        flash(_("Oops! Selected book is unavailable. File does not exist or is not accessible"),
              category="error")
        return redirect(url_for("web.index"))
    if sqlalchemy_version2:
        author = calibre_db.session.get(db.Authors, author_id)
    else:
        author = calibre_db.session.query(db.Authors).get(author_id)
    author_name = author.name.replace('|', ',')

    author_info = None
    other_books = []
    if services.goodreads_support and config.config_use_goodreads:
        author_info = services.goodreads_support.get_author_info(author_name)
        book_entries = [entry.Books for entry in entries]
        other_books = services.goodreads_support.get_other_books(author_info, book_entries)
    return render_title_template('author.html', entries=entries, pagination=pagination, id=author_id,
                                 title=_("Author: %(name)s", name=author_name), author=author_info,
                                 other_books=other_books, page="author", order=order[1])


def render_publisher_books(page, book_id, order):
    if book_id == '-1':
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db.Publishers.name == None,
                                                                [db.Series.name, order[0][0], db.Books.series_index],
                                                                True, config.config_read_column,
                                                                db.books_publishers_link,
                                                                db.Books.id == db.books_publishers_link.c.book,
                                                                db.Publishers,
                                                                db.books_series_link,
                                                                db.Books.id == db.books_series_link.c.book,
                                                                db.Series)
        publisher = _("None")
    else:
        publisher = calibre_db.session.query(db.Publishers).filter(db.Publishers.id == book_id).first()
        if publisher:
            entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                    db.Books,
                                                                    db.Books.publishers.any(
                                                                        db.Publishers.id == book_id),
                                                                    [db.Series.name, order[0][0],
                                                                     db.Books.series_index],
                                                                    True, config.config_read_column,
                                                                    db.books_series_link,
                                                                    db.Books.id == db.books_series_link.c.book,
                                                                    db.Series)
            publisher = publisher.name
        else:
            abort(404)

    return render_title_template('index.html', random=random, entries=entries, pagination=pagination, id=book_id,
                                 title=_("Publisher: %(name)s", name=publisher),
                                 page="publisher",
                                 order=order[1])


def render_series_books(page, book_id, order):
    if book_id == '-1':
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db.Series.name == None,
                                                                [order[0][0]],
                                                                True, config.config_read_column,
                                                                db.books_series_link,
                                                                db.Books.id == db.books_series_link.c.book,
                                                                db.Series)
        series_name = _("None")
    else:
        series_name = calibre_db.session.query(db.Series).filter(db.Series.id == book_id).first()
        if series_name:
            entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                    db.Books,
                                                                    db.Books.series.any(db.Series.id == book_id),
                                                                    [order[0][0]],
                                                                    True, config.config_read_column)
            series_name = series_name.name
        else:
            abort(404)
    return render_title_template('index.html', random=random, pagination=pagination, entries=entries, id=book_id,
                                 title=_("Series: %(serie)s", serie=series_name), page="series", order=order[1])


def render_ratings_books(page, book_id, order):
    if book_id == '-1':
        db_filter = coalesce(db.Ratings.rating, 0) < 1
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db_filter,
                                                                [order[0][0]],
                                                                True, config.config_read_column,
                                                                db.books_ratings_link,
                                                                db.Books.id == db.books_ratings_link.c.book,
                                                                db.Ratings)
        title = _("Rating: None")
    else:
        name = calibre_db.session.query(db.Ratings).filter(db.Ratings.id == book_id).first()
        if name:
            entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                    db.Books,
                                                                    db.Books.ratings.any(db.Ratings.id == book_id),
                                                                    [order[0][0]],
                                                                    True, config.config_read_column)
            title = _("Rating: %(rating)s stars", rating=int(name.rating / 2))
        else:
            abort(404)
    return render_title_template('index.html', random=random, pagination=pagination, entries=entries, id=book_id,
                                 title=title, page="ratings", order=order[1])


def render_formats_books(page, book_id, order):
    if book_id == '-1':
        name = _("None")
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db.Data.format == None,
                                                                [order[0][0]],
                                                                True, config.config_read_column,
                                                                db.Data)

    else:
        name = calibre_db.session.query(db.Data).filter(db.Data.format == book_id.upper()).first()
        if name:
            name = name.format
            entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                    db.Books,
                                                                    db.Books.data.any(
                                                                        db.Data.format == book_id.upper()),
                                                                    [order[0][0]],
                                                                    True, config.config_read_column)
        else:
            abort(404)

    return render_title_template('index.html', random=random, pagination=pagination, entries=entries, id=book_id,
                                 title=_("File format: %(format)s", format=name),
                                 page="formats",
                                 order=order[1])


def render_category_books(page, book_id, order):
    if book_id == '-1':
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db.Tags.name == None,
                                                                [order[0][0], db.Series.name, db.Books.series_index],
                                                                True, config.config_read_column,
                                                                db.books_tags_link,
                                                                db.Books.id == db.books_tags_link.c.book,
                                                                db.Tags,
                                                                db.books_series_link,
                                                                db.Books.id == db.books_series_link.c.book,
                                                                db.Series)
        tagsname = _("None")
    else:
        tagsname = calibre_db.session.query(db.Tags).filter(db.Tags.id == book_id).first()
        if tagsname:
            entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                    db.Books,
                                                                    db.Books.tags.any(db.Tags.id == book_id),
                                                                    [order[0][0], db.Series.name,
                                                                     db.Books.series_index],
                                                                    True, config.config_read_column,
                                                                    db.books_series_link,
                                                                    db.Books.id == db.books_series_link.c.book,
                                                                    db.Series)
            tagsname = tagsname.name
        else:
            abort(404)
    return render_title_template('index.html', random=random, entries=entries, pagination=pagination, id=book_id,
                                 title=_("Category: %(name)s", name=tagsname), page="category", order=order[1])


def render_language_books(page, name, order):
    try:
        if name.lower() != "none":
            lang_name = isoLanguages.get_language_name(get_locale(), name)
            if lang_name == "Unknown":
                abort(404)
        else:
            lang_name = _("None")
    except KeyError:
        abort(404)
    if name.lower() == "none":
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db.Languages.lang_code == None,
                                                                [order[0][0]],
                                                                True, config.config_read_column,
                                                                db.books_languages_link,
                                                                db.Books.id == db.books_languages_link.c.book,
                                                                db.Languages)
    else:
        entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                                db.Books,
                                                                db.Books.languages.any(db.Languages.lang_code == name),
                                                                [order[0][0]],
                                                                True, config.config_read_column)
    return render_title_template('index.html', random=random, entries=entries, pagination=pagination, id=name,
                                 title=_("Language: %(name)s", name=lang_name), page="language", order=order[1])


def render_read_books(page, are_read, as_xml=False, order=None):
    sort_param = order[0] if order else []
    if not config.config_read_column:
        if are_read:
            db_filter = and_(ub.ReadBook.user_id == int(current_user.id),
                             ub.ReadBook.read_status == ub.ReadBook.STATUS_FINISHED)
        else:
            db_filter = coalesce(ub.ReadBook.read_status, 0) != ub.ReadBook.STATUS_FINISHED
    else:
        try:
            if are_read:
                db_filter = db.cc_classes[config.config_read_column].value == True
            else:
                db_filter = coalesce(db.cc_classes[config.config_read_column].value, False) != True
        except (KeyError, AttributeError, IndexError):
            log.error("Custom Column No.{} does not exist in calibre database".format(config.config_read_column))
            if not as_xml:
                flash(_("Custom Column No.%(column)d does not exist in calibre database",
                        column=config.config_read_column),
                      category="error")
                return redirect(url_for("web.index"))
            return []  # ToDo: Handle error Case for opds

    entries, random, pagination = calibre_db.fill_indexpage(page, 0,
                                                            db.Books,
                                                            db_filter,
                                                            sort_param,
                                                            True, config.config_read_column,
                                                            db.books_series_link,
                                                            db.Books.id == db.books_series_link.c.book,
                                                            db.Series)

    if as_xml:
        return entries, pagination
    else:
        if are_read:
            name = _('Read Books') + ' (' + str(pagination.total_count) + ')'
            page_name = "read"
        else:
            name = _('Unread Books') + ' (' + str(pagination.total_count) + ')'
            page_name = "unread"
        return render_title_template('index.html', random=random, entries=entries, pagination=pagination,
                                     title=name, page=page_name, order=order[1])


def render_archived_books(page, sort_param):
    order = sort_param[0] or []
    archived_books = (ub.session.query(ub.ArchivedBook)
                      .filter(ub.ArchivedBook.user_id == int(current_user.id))
                      .filter(ub.ArchivedBook.is_archived == True)
                      .all())
    archived_book_ids = [archived_book.book_id for archived_book in archived_books]

    archived_filter = db.Books.id.in_(archived_book_ids)

    entries, random, pagination = calibre_db.fill_indexpage_with_archived_books(page, db.Books,
                                                                                0,
                                                                                archived_filter,
                                                                                order,
                                                                                True,
                                                                                True, config.config_read_column)

    name = _('Archived Books') + ' (' + str(len(entries)) + ')'
    page_name = "archived"
    return render_title_template('index.html', random=random, entries=entries, pagination=pagination,
                                 title=name, page=page_name, order=sort_param[1])


# ################################### View Books list ##################################################################


@web.route("/", defaults={'page': 1})
@web.route('/page/<int:page>')
@login_required_if_no_ano
def index(page):
    sort_param = (request.args.get('sort') or 'stored').lower()
    return render_books_list("newest", sort_param, 1, page)


@login_required_if_no_ano
def books_list(data, sort_param, book_id, page):
    return render_books_list(data, sort_param, book_id, page)

# Limit number of routes to avoid redirects
data =["rated", "discover", "unread", "read", "hot", "download", "author", "publisher", "series", "ratings", "formats",
       "category", "language", "archived", "search", "advsearch", "newest"]
for d in data:
    web.add_url_rule('/{}/<sort_param>'.format(d), view_func=books_list, defaults={'page': 1, 'book_id': 1, "data": d})
    web.add_url_rule('/{}/<sort_param>/'.format(d), view_func=books_list, defaults={'page': 1, 'book_id': 1, "data": d})
    web.add_url_rule('/{}/<sort_param>/<book_id>'.format(d), view_func=books_list, defaults={'page': 1, "data": d})
    web.add_url_rule('/{}/<sort_param>/<book_id>/<int:page>'.format(d), defaults={"data": d}, view_func=books_list)


@web.route("/table")
@user_login_required
def books_table():
    visibility = current_user.view_settings.get('table', {})
    cc = calibre_db.get_cc_columns(config, filter_config_custom_read=True)
    return render_title_template('book_table.html', title=_("Books List"), cc=cc, page="book_table",
                                 visiblility=visibility)


@web.route("/ajax/listbooks")
@user_login_required
def list_books():
    off = int(request.args.get("offset") or 0)
    limit = int(request.args.get("limit") or config.config_books_per_page)
    search_param = request.args.get("search")
    sort_param = request.args.get("sort", "id")
    order = request.args.get("order", "").lower()
    state = None
    join = tuple()
    if not order in ["asc", "desc", ""]:
        order = "asc"
    if sort_param == "state":
        state = json.loads(request.args.get("state", "[]"))
    elif sort_param == "tags":
        order = [db.Tags.name.asc()] if order == "asc" else [db.Tags.name.desc()]
        join = db.books_tags_link, db.Books.id == db.books_tags_link.c.book, db.Tags
    elif sort_param == "series":
        order = [db.Series.name.asc()] if order == "asc" else [db.Series.name.desc()]
        join = db.books_series_link, db.Books.id == db.books_series_link.c.book, db.Series
    elif sort_param == "publishers":
        order = [db.Publishers.name.asc()] if order == "asc" else [db.Publishers.name.desc()]
        join = db.books_publishers_link, db.Books.id == db.books_publishers_link.c.book, db.Publishers
    elif sort_param == "authors":
        order = [db.Authors.name.asc(), db.Series.name, db.Books.series_index] if order == "asc" \
            else [db.Authors.name.desc(), db.Series.name.desc(), db.Books.series_index.desc()]
        join = db.books_authors_link, db.Books.id == db.books_authors_link.c.book, db.Authors, db.books_series_link, \
            db.Books.id == db.books_series_link.c.book, db.Series
    elif sort_param == "languages":
        order = [db.Languages.lang_code.asc()] if order == "asc" else [db.Languages.lang_code.desc()]
        join = db.books_languages_link, db.Books.id == db.books_languages_link.c.book, db.Languages
    elif order and sort_param in ["sort", "title", "authors_sort", "series_index"]:
        order = [text(sort_param + " " + order)]
    elif not state:
        order = [db.Books.timestamp.desc()]

    total_count = filtered_count = calibre_db.session.query(db.Books).filter(
        calibre_db.common_filters(allow_show_archived=True)).count()
    if state is not None:
        if search_param:
            books = calibre_db.search_query(search_param, config).all()
            filtered_count = len(books)
        else:
            query = calibre_db.generate_linked_query(config.config_read_column, db.Books)
            books = query.filter(calibre_db.common_filters(allow_show_archived=True)).all()
        entries = calibre_db.get_checkbox_sorted(books, state, off, limit, order, True)
    elif search_param:
        entries, filtered_count, __ = calibre_db.get_search_results(search_param,
                                                                    config,
                                                                    off,
                                                                    [order, ''],
                                                                    limit,
                                                                    *join)
    else:
        entries, __, __ = calibre_db.fill_indexpage_with_archived_books((int(off) / (int(limit)) + 1),
                                                                        db.Books,
                                                                        limit,
                                                                        True,
                                                                        order,
                                                                        True,
                                                                        True,
                                                                        config.config_read_column,
                                                                        *join)

    result = list()
    for entry in entries:
        val = entry[0]
        val.is_archived = entry[1] is True
        val.read_status = entry[2] == ub.ReadBook.STATUS_FINISHED
        for lang_index in range(0, len(val.languages)):
            val.languages[lang_index].language_name = isoLanguages.get_language_name(get_locale(), val.languages[
                lang_index].lang_code)
        result.append(val)

    table_entries = {'totalNotFiltered': total_count, 'total': filtered_count, "rows": result}
    js_list = json.dumps(table_entries, cls=db.AlchemyEncoder)

    response = make_response(js_list)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@web.route("/ajax/table_settings", methods=['POST'])
@user_login_required
def update_table_settings():
    current_user.view_settings['table'] = json.loads(request.data)
    try:
        try:
            flag_modified(current_user, "view_settings")
        except AttributeError:
            pass
        ub.session.commit()
    except (InvalidRequestError, OperationalError):
        log.error("Invalid request received: %r ", request, )
        return "Invalid request", 400
    return ""


@web.route("/author")
@login_required_if_no_ano
def author_list():
    if current_user.check_visibility(constants.SIDEBAR_AUTHOR):
        if current_user.get_view_property('author', 'dir') == 'desc':
            order = db.Authors.sort.desc()
            order_no = 0
        else:
            order = db.Authors.sort.asc()
            order_no = 1
        entries = calibre_db.session.query(db.Authors, func.count('books_authors_link.book').label('count')) \
            .join(db.books_authors_link).join(db.Books).filter(calibre_db.common_filters()) \
            .group_by(text('books_authors_link.author')).order_by(order).all()
        char_list = query_char_list(db.Authors.sort, db.books_authors_link)
        # If not creating a copy, readonly databases can not display authornames with "|" in it as changing the name
        # starts a change session
        author_copy = copy.deepcopy(entries)
        for entry in author_copy:
            entry.Authors.name = entry.Authors.name.replace('|', ',')
        return render_title_template('list.html', entries=author_copy, folder='web.books_list', charlist=char_list,
                                     title="Authors", page="authorlist", data='author', order=order_no)
    else:
        abort(404)


@web.route("/downloadlist")
@login_required_if_no_ano
def download_list():
    if current_user.get_view_property('download', 'dir') == 'desc':
        order = ub.User.name.desc()
        order_no = 0
    else:
        order = ub.User.name.asc()
        order_no = 1
    if current_user.check_visibility(constants.SIDEBAR_DOWNLOAD) and current_user.role_admin():
        entries = ub.session.query(ub.User, func.count(ub.Downloads.book_id).label('count')) \
            .join(ub.Downloads).group_by(ub.Downloads.user_id).order_by(order).all()
        char_list = ub.session.query(func.upper(func.substr(ub.User.name, 1, 1)).label('char')) \
            .filter(ub.User.role.op('&')(constants.ROLE_ANONYMOUS) != constants.ROLE_ANONYMOUS) \
            .group_by(func.upper(func.substr(ub.User.name, 1, 1))).all()
        return render_title_template('list.html', entries=entries, folder='web.books_list', charlist=char_list,
                                     title=_("Downloads"), page="downloadlist", data="download", order=order_no)
    else:
        abort(404)


@web.route("/publisher")
@login_required_if_no_ano
def publisher_list():
    if current_user.get_view_property('publisher', 'dir') == 'desc':
        order = db.Publishers.name.desc()
        order_no = 0
    else:
        order = db.Publishers.name.asc()
        order_no = 1
    if current_user.check_visibility(constants.SIDEBAR_PUBLISHER):
        entries = calibre_db.session.query(db.Publishers, func.count('books_publishers_link.book').label('count')) \
            .join(db.books_publishers_link).join(db.Books).filter(calibre_db.common_filters()) \
            .group_by(text('books_publishers_link.publisher')).order_by(order).all()
        no_publisher_count = (calibre_db.session.query(db.Books)
                           .outerjoin(db.books_publishers_link).outerjoin(db.Publishers)
                           .filter(db.Publishers.name == None)
                           .filter(calibre_db.common_filters())
                           .count())
        if no_publisher_count:
            entries.append([db.Category(_("None"), "-1"), no_publisher_count])
        entries = sorted(entries, key=lambda x: x[0].name.lower(), reverse=not order_no)
        char_list = generate_char_list(entries)
        return render_title_template('list.html', entries=entries, folder='web.books_list', charlist=char_list,
                                     title=_("Publishers"), page="publisherlist", data="publisher", order=order_no)
    else:
        abort(404)


@web.route("/series")
@login_required_if_no_ano
def series_list():
    if current_user.check_visibility(constants.SIDEBAR_SERIES):
        if current_user.get_view_property('series', 'dir') == 'desc':
            order = db.Series.sort.desc()
            order_no = 0
        else:
            order = db.Series.sort.asc()
            order_no = 1
        char_list = query_char_list(db.Series.sort, db.books_series_link)
        if current_user.get_view_property('series', 'series_view') == 'list':
            entries = calibre_db.session.query(db.Series, func.count('books_series_link.book').label('count')) \
                .join(db.books_series_link).join(db.Books).filter(calibre_db.common_filters()) \
                .group_by(text('books_series_link.series')).order_by(order).all()
            no_series_count = (calibre_db.session.query(db.Books)
                            .outerjoin(db.books_series_link).outerjoin(db.Series)
                            .filter(db.Series.name == None)
                            .filter(calibre_db.common_filters())
                            .count())
            if no_series_count:
                entries.append([db.Category(_("None"), "-1"), no_series_count])
            entries = sorted(entries, key=lambda x: (x[0].sort or x[0].name).lower(), reverse=not order_no)
            return render_title_template('list.html',
                                         entries=entries,
                                         folder='web.books_list',
                                         charlist=char_list,
                                         title=_("Series"),
                                         page="serieslist",
                                         data="series", order=order_no)
        else:
            entries = (calibre_db.session.query(db.Books, func.count('books_series_link').label('count'),
                                                func.max(db.Books.series_index), db.Books.id)
                       .join(db.books_series_link).join(db.Series).filter(calibre_db.common_filters())
                       .group_by(text('books_series_link.series'))
                       .having(or_(func.max(db.Books.series_index), db.Books.series_index==""))
                       .order_by(order)
                       .all())
            return render_title_template('grid.html', entries=entries, folder='web.books_list', charlist=char_list,
                                         title=_("Series"), page="serieslist", data="series", bodyClass="grid-view",
                                         order=order_no)
    else:
        abort(404)


@web.route("/ratings")
@login_required_if_no_ano
def ratings_list():
    if current_user.check_visibility(constants.SIDEBAR_RATING):
        if current_user.get_view_property('ratings', 'dir') == 'desc':
            order = db.Ratings.rating.desc()
            order_no = 0
        else:
            order = db.Ratings.rating.asc()
            order_no = 1
        entries = calibre_db.session.query(db.Ratings, func.count('books_ratings_link.book').label('count'),
                                           (db.Ratings.rating / 2).label('name')) \
            .join(db.books_ratings_link).join(db.Books).filter(calibre_db.common_filters()) \
            .filter(db.Ratings.rating > 0) \
            .group_by(text('books_ratings_link.rating')).order_by(order).all()
        no_rating_count = (calibre_db.session.query(db.Books)
                           .outerjoin(db.books_ratings_link).outerjoin(db.Ratings)
                           .filter(or_(db.Ratings.rating == None, db.Ratings.rating == 0))
                           .filter(calibre_db.common_filters())
                           .count())
        if no_rating_count:
            entries.append([db.Category(_("None"), "-1", -1), no_rating_count])
        entries = sorted(entries, key=lambda x: x[0].rating, reverse=not order_no)
        return render_title_template('list.html', entries=entries, folder='web.books_list', charlist=list(),
                                     title=_("Ratings list"), page="ratingslist", data="ratings", order=order_no)
    else:
        abort(404)


@web.route("/formats")
@login_required_if_no_ano
def formats_list():
    if current_user.check_visibility(constants.SIDEBAR_FORMAT):
        if current_user.get_view_property('formats', 'dir') == 'desc':
            order = db.Data.format.desc()
            order_no = 0
        else:
            order = db.Data.format.asc()
            order_no = 1
        entries = calibre_db.session.query(db.Data,
                                           func.count('data.book').label('count'),
                                           db.Data.format.label('format')) \
            .join(db.Books).filter(calibre_db.common_filters()) \
            .group_by(db.Data.format).order_by(order).all()
        no_format_count = (calibre_db.session.query(db.Books).outerjoin(db.Data)
                           .filter(db.Data.format == None)
                           .filter(calibre_db.common_filters())
                           .count())
        if no_format_count:
            entries.append([db.Category(_("None"), "-1"), no_format_count])
        return render_title_template('list.html', entries=entries, folder='web.books_list', charlist=list(),
                                     title=_("File formats list"), page="formatslist", data="formats", order=order_no)
    else:
        abort(404)


@web.route("/language")
@login_required_if_no_ano
def language_overview():
    if current_user.check_visibility(constants.SIDEBAR_LANGUAGE) and current_user.filter_language() == "all":
        order_no = 0 if current_user.get_view_property('language', 'dir') == 'desc' else 1
        languages = calibre_db.speaking_language(reverse_order=not order_no, with_count=True)
        char_list = generate_char_list(languages)
        return render_title_template('list.html', entries=languages, folder='web.books_list', charlist=char_list,
                                     title=_("Languages"), page="langlist", data="language", order=order_no)
    else:
        abort(404)


@web.route("/category")
@login_required_if_no_ano
def category_list():
    if current_user.check_visibility(constants.SIDEBAR_CATEGORY):
        if current_user.get_view_property('category', 'dir') == 'desc':
            order = db.Tags.name.desc()
            order_no = 0
        else:
            order = db.Tags.name.asc()
            order_no = 1
        entries = calibre_db.session.query(db.Tags, func.count('books_tags_link.book').label('count')) \
            .join(db.books_tags_link).join(db.Books).order_by(order).filter(calibre_db.common_filters()) \
            .group_by(db.Tags.id).all()
        no_tag_count = (calibre_db.session.query(db.Books)
                         .outerjoin(db.books_tags_link).outerjoin(db.Tags)
                        .filter(db.Tags.name == None)
                         .filter(calibre_db.common_filters())
                         .count())
        if no_tag_count:
            entries.append([db.Category(_("None"), "-1"), no_tag_count])
        entries = sorted(entries, key=lambda x: x[0].name.lower(), reverse=not order_no)
        char_list = generate_char_list(entries)
        return render_title_template('list.html', entries=entries, folder='web.books_list', charlist=char_list,
                                     title=_("Categories"), page="catlist", data="category", order=order_no)
    else:
        abort(404)




# ################################### Download/Send ##################################################################


@web.route("/cover/<int:book_id>")
@web.route("/cover/<int:book_id>/<string:resolution>")
@login_required_if_no_ano
def get_cover(book_id, resolution=None):
    resolutions = {
        'og': constants.COVER_THUMBNAIL_ORIGINAL,
        'sm': constants.COVER_THUMBNAIL_SMALL,
        'md': constants.COVER_THUMBNAIL_MEDIUM,
        'lg': constants.COVER_THUMBNAIL_LARGE,
    }
    cover_resolution = resolutions.get(resolution, None)
    return get_book_cover(book_id, cover_resolution)


@web.route("/series_cover/<int:series_id>")
@web.route("/series_cover/<int:series_id>/<string:resolution>")
@login_required_if_no_ano
def get_series_cover(series_id, resolution=None):
    resolutions = {
        'og': constants.COVER_THUMBNAIL_ORIGINAL,
        'sm': constants.COVER_THUMBNAIL_SMALL,
        'md': constants.COVER_THUMBNAIL_MEDIUM,
        'lg': constants.COVER_THUMBNAIL_LARGE,
    }
    cover_resolution = resolutions.get(resolution, None)
    return get_series_cover_thumbnail(series_id, cover_resolution)



@web.route("/robots.txt")
def get_robots():
    try:
        return send_from_directory(constants.STATIC_DIR, "robots.txt")
    except PermissionError:
        log.error("No permission to access robots.txt file.")
        abort(403)


@web.route("/show/<int:book_id>/<book_format>", defaults={'anyname': 'None'})
@web.route("/show/<int:book_id>/<book_format>/<anyname>")
@login_required_if_no_ano
@viewer_required
def serve_book(book_id, book_format, anyname):
    book_format = book_format.split(".")[0]
    book = calibre_db.get_filtered_book(book_id)
    if not book:
        return "File not in Database"
    data = calibre_db.get_book_format(book_id, book_format.upper())
    if not data:
        return "File not in Database"
    range_header = request.headers.get('Range', None)
    if not range_header:
        log.info('Serving book: \'%s\' to %s - %s', data.name, current_user.name,
                 request.headers.get('X-Forwarded-For', request.remote_addr))
    if config.config_use_google_drive:
        try:
            headers = Headers()
            headers["Content-Type"] = mimetypes.types_map.get('.' + book_format, "application/octet-stream")
            if not range_header:                
                headers['Accept-Ranges'] = 'bytes'
            df = getFileFromEbooksFolder(book.path, data.name + "." + book_format)
            return do_gdrive_download(df, headers, (book_format.upper() == 'TXT'))
        except AttributeError as ex:
            log.error_or_exception(ex)
            return "File Not Found"
    else:
        if book_format.upper() == 'TXT':
            try:
                rawdata = open(os.path.join(config.get_book_path(), book.path, data.name + "." + book_format),
                               "rb").read()
                result = chardet.detect(rawdata)
                try:
                    text_data = rawdata.decode(result['encoding']).encode('utf-8')
                except UnicodeDecodeError as e:
                    log.error("Encoding error in text file {}: {}".format(book.id, e))
                    if "surrogate" in e.reason:
                        text_data = rawdata.decode(result['encoding'], 'surrogatepass').encode('utf-8', 'surrogatepass')
                    else:
                        text_data = rawdata.decode(result['encoding'], 'ignore').encode('utf-8', 'ignore')
                return make_response(text_data)
            except FileNotFoundError:
                log.error("File Not Found")
                return "File Not Found"
        # enable byte range read of pdf
        response = make_response(
            send_from_directory(os.path.join(config.get_book_path(), book.path), data.name + "." + book_format))
        if not range_header:
            response.headers['Accept-Ranges'] = 'bytes'
        return response


@web.route("/download/<int:book_id>/<book_format>", defaults={'anyname': 'None'})
@web.route("/download/<int:book_id>/<book_format>/<anyname>")
@login_required_if_no_ano
@download_required
def download_link(book_id, book_format, anyname):
    if "kindle" in request.headers.get('User-Agent').lower():
        client = "kindle"
    elif "Kobo" in request.headers.get('User-Agent').lower():
        client = "kobo"
    else:
        client = ""
    return get_download_link(book_id, book_format, client)


@web.route('/send/<int:book_id>/<book_format>/<int:convert>', methods=["POST"])
@login_required_if_no_ano
@download_required
def send_to_ereader(book_id, book_format, convert):
    if not config.get_mail_server_configured():
        return make_response(jsonify(type="danger", message=_("Please configure the SMTP mail settings first...")))
    elif current_user.kindle_mail:
        result = send_mail(book_id, book_format, convert, current_user.kindle_mail, config.get_book_path(),
                           current_user.name)
        if result is None:
            ub.update_download(book_id, int(current_user.id))
            response = [{'type': "success", 'message': _("Success! Book queued for sending to %(eReadermail)s",
                                                       eReadermail=current_user.kindle_mail)}]
        else:
            response = [{'type': "danger", 'message': _("Oops! There was an error sending book: %(res)s", res=result)}]
    else:
        response = [{'type': "danger", 'message': _("Oops! Please update your profile with a valid eReader Email.")}]
    return make_response(jsonify(response))


# ################################### Login Logout ##################################################################

@web.route('/register', methods=['POST'])
@limiter.limit("40/day", key_func=get_remote_address)
@limiter.limit("3/minute", key_func=get_remote_address)
def register_post():
    if not config.config_public_reg:
        abort(404)
    to_save = request.form.to_dict()
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('web.index'))
    if not config.get_mail_server_configured():
        flash(_("Oops! Email server is not configured, please contact your administrator."), category="error")
        return render_title_template('register.html', title=_("Register"), page="register")
    nickname = strip_whitespaces(to_save.get("email", "")) if config.config_register_email else to_save.get('name')
    if not nickname or not to_save.get("email"):
        flash(_("Oops! Please complete all fields."), category="error")
        return render_title_template('register.html', title=_("Register"), page="register")
    try:
        nickname = check_username(nickname)
        email = check_email(to_save.get("email", ""))
    except Exception as ex:
        flash(str(ex), category="error")
        return render_title_template('register.html', title=_("Register"), page="register")

    content = ub.User()
    if check_valid_domain(email):
        content.name = nickname
        content.email = email
        password = generate_random_password(config.config_password_min_length)
        content.password = generate_password_hash(password)
        content.role = config.config_default_role
        content.locale = config.config_default_locale
        content.sidebar_view = config.config_default_show
        content.allowed_tags = config.config_allowed_tags
        content.denied_tags = config.config_denied_tags
        content.allowed_column_value = config.config_allowed_column_value
        content.denied_column_value = config.config_denied_column_value
        try:
            ub.session.add(content)
            ub.session.commit()
            if feature_support['oauth']:
                register_user_with_oauth(content)
            send_registration_mail(strip_whitespaces(to_save.get("email", "")), nickname, password)
        except Exception:
            ub.session.rollback()
            flash(_("Oops! An unknown error occurred. Please try again later."), category="error")
            return render_title_template('register.html', title=_("Register"), page="register")
    else:
        flash(_("Oops! Your Email is not allowed."), category="error")
        log.warning('Registering failed for user "{}" Email: {}'.format(nickname, to_save.get("email","")))
        return render_title_template('register.html', title=_("Register"), page="register")
    flash(_("Success! Confirmation Email has been sent."), category="success")
    return redirect(url_for('web.login'))


@web.route('/register', methods=['GET'])
def register():
    if not config.config_public_reg:
        abort(404)
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('web.index'))
    if not config.get_mail_server_configured():
        flash(_("Oops! Email server is not configured, please contact your administrator."), category="error")
        return render_title_template('register.html', title=_("Register"), page="register")
    if feature_support['oauth']:
        register_user_with_oauth()
    return render_title_template('register.html', config=config, title=_("Register"), page="register")


def handle_login_user(user, remember, message, category):
    login_user(user, remember=remember)
    flash(message, category=category)
    [limiter.limiter.clear(limit.limit, *limit.request_args) for limit in limiter.current_limits]
    return redirect(get_redirect_location(request.form.get('next', None), "web.index"))


def render_login(username="", password=""):
    next_url = request.args.get('next', default=url_for("web.index"), type=str)
    if url_for("web.logout") == next_url:
        next_url = url_for("web.index")
    oidc_enabled = current_app.config.get("AUTHENTIK_OIDC_ENABLED", False)
    # 邀请制注册入口：链接由 .env 的 AUTHENTIK_ENROLLMENT_INVITE_URL 注入（Authentik
    # 邀请默认 30 天过期，轮换时只改环境变量并重启，不动代码）；未配置则不渲染
    invite_url = (os.getenv("AUTHENTIK_ENROLLMENT_INVITE_URL") or "").strip()
    # R217：注册按钮改为指向 magicbook 侧的 /oidc/signup —— 它把「邀请注册」与
    # 「OIDC 授权」串成一条链，用户注册完自动回站且已是登录态（不再需要二次点击）。
    # 仍以 invite_url 是否配置为开关：未配置 → 不渲染注册入口（沿用 R103 语义）。
    signup_url = url_for("oidc.signup", next=next_url) if invite_url else ""
    return render_title_template('login.html',
                                 title=_("Login"),
                                 next_url=next_url,
                                 username=username,
                                 password=password,
                                 oauth_check=oauth_check,
                                 authentik_oidc_enabled=oidc_enabled,
                                 authentik_invite_url=invite_url,
                                 authentik_signup_url=signup_url,
                                 # 统一账户体系：Authentik 启用时隐藏本地密码表单，仅保留 OIDC 登录
                                 hide_local_login=oidc_enabled,
                                 mail=config.get_mail_server_configured(), page="login")


@web.route('/login', methods=['GET'])
def login():
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('web.index'))
    if config.config_login_type == constants.LOGIN_LDAP and not services.ldap:
        log.error(u"Cannot activate LDAP authentication")
        flash(_(u"Cannot activate LDAP authentication"), category="error")
    return render_login()


@web.route('/login', methods=['POST'])
@limiter.limit("40/day", key_func=lambda: strip_whitespaces(request.form.get('username', "")).lower())
@limiter.limit("3/minute", key_func=lambda: strip_whitespaces(request.form.get('username', "")).lower())
def login_post():
    form = request.form.to_dict()
    username = strip_whitespaces(form.get('username', "")).lower().replace("\n","").replace("\r","")
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('web.index'))
    if config.config_login_type == constants.LOGIN_LDAP and not services.ldap:
        log.error(u"Cannot activate LDAP authentication")
        flash(_(u"Cannot activate LDAP authentication"), category="error")
    # 统一账户体系：Authentik 启用后本地密码登录被禁用（含 forgot 找回），仅走 OIDC。
    # 关闭 OIDC 配置（AUTHENTIK_* 环境变量）即降级回本地登录，保留管理员恢复通道。
    if current_app.config.get("AUTHENTIK_OIDC_ENABLED", False):
        log.info('Local login disabled (Authentik OIDC enabled), redirecting user "%s" to OIDC', username)
        flash(_(u"Local password login is disabled; please log in with Authentik"), category="info")
        return redirect(url_for("oidc.login", next=request.form.get("next", "")))
    user = ub.session.query(ub.User).filter(func.lower(ub.User.name) == username).first()
    remember_me = bool(form.get('remember_me'))
    if config.config_login_type == constants.LOGIN_LDAP and services.ldap and user and form['password'] != "":
        login_result, error = services.ldap.bind_user(username, form['password'])
        if login_result:
            log.debug(u"You are now logged in as: '{}'".format(user.name))
            return handle_login_user(user,
                                     remember_me,
                                     _(u"you are now logged in as: '%(nickname)s'", nickname=user.name),
                                     "success")
        elif login_result is None and user and check_password_hash(str(user.password), form['password']) \
                and user.name != "Guest":
            log.info("Local Fallback Login as: '{}'".format(user.name))
            return handle_login_user(user,
                                     remember_me,
                                     _(u"Fallback Login as: '%(nickname)s', "
                                       u"LDAP Server not reachable, or user not known", nickname=user.name),
                                     "warning")
        elif login_result is None:
            log.info(error)
            flash(_(u"Could not login: %(message)s", message=error), category="error")
        else:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            log.warning('LDAP Login failed for user "%s" IP-address: %s', username, ip_address)
            flash(_(u"Wrong Username or Password"), category="error")
    else:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if form.get('forgot', "") == 'forgot':
            if user is not None and user.name != "Guest":
                ret, __ = reset_password(user.id)
                if ret == 1:
                    flash(_(u"New Password was sent to your email address"), category="info")
                    log.info('Password reset for user "%s" IP-address: %s', username, ip_address)
                else:
                    log.error(u"An unknown error occurred. Please try again later")
                    flash(_(u"An unknown error occurred. Please try again later."), category="error")
            else:
                flash(_(u"Please enter valid username to reset password"), category="error")
                log.warning('Username missing for password reset IP-address: %s', ip_address)
        else:
            if user and check_password_hash(str(user.password), form['password']) and user.name != "Guest":
                config.config_is_initial = False
                log.debug(u"You are now logged in as: '{}'".format(user.name))
                return handle_login_user(user,
                                         remember_me,
                                         _(u"You are now logged in as: '%(nickname)s'", nickname=user.name),
                                         "success")
            else:
                log.warning('Login failed for user "{}" IP-address: {}'.format(username, ip_address))
                flash(_(u"Wrong Username or Password"), category="error")
    return render_login(username, form.get("password", ""))


@web.route('/logout')
@user_login_required
def logout():
    if current_user is not None and current_user.is_authenticated:
        ub.delete_user_session(current_user.id, flask_session.get('_id', ""))
        logout_user()
        # R123: 会话已持久化（cookie 带 30 天滑动 Expires），登出必须整体清空——
        # 否则 moonwell_access_token / moonwell_refresh_token 滞留在被继续续期的
        # 永久 cookie 里，登出后仍可被重放。clear 置 modified，save_session 会对
        # 空会话下发 Set-Cookie 删除头，浏览器端 cookie 一并移除。
        flask_session.clear()
        if feature_support['oauth'] and (config.config_login_type == 2 or config.config_login_type == 3):
            logout_oauth_user()
    log.debug("User logged out")
    if config.config_anonbrowse:
        location = get_redirect_location(request.args.get('next', None), "web.login")
    else:
        location = None
    if location:
        return redirect(location)
    else:
        return redirect(url_for('web.login'))


# ################################### Users own configuration #########################################################
def change_profile(kobo_support, local_oauth_check, oauth_status, translations, languages):
    to_save = request.form.to_dict()
    current_user.random_books = 0
    try:
        if current_user.role_passwd() or current_user.role_admin():
            if to_save.get("password", "") != "":
                current_user.password = generate_password_hash(valid_password(to_save.get("password")))
        if to_save.get("kindle_mail", current_user.kindle_mail) != current_user.kindle_mail:
            current_user.kindle_mail = valid_email(to_save.get("kindle_mail"))
        new_email = valid_email(to_save.get("email", current_user.email))
        if not new_email:
            raise Exception(_("Email can't be empty and has to be a valid Email"))
        if new_email != current_user.email:
            current_user.email = check_email(new_email)
        if current_user.role_admin():
            if to_save.get("name", current_user.name) != current_user.name:
                # Query username, if not existing, change
                current_user.name = check_username(to_save.get("name"))
        current_user.random_books = 1 if to_save.get("show_random") == "on" else 0
        current_user.default_language = to_save.get("default_language", "all")
        current_user.locale = to_save.get("locale", "en")
        old_state = current_user.kobo_only_shelves_sync
        # 1 -> 0: nothing has to be done
        # 0 -> 1: all synced books have to be added to archived books, + currently synced shelfs which
        # don't have to be synced have to be removed (added to Shelf archive)
        current_user.kobo_only_shelves_sync = int(to_save.get("kobo_only_shelves_sync") == "on") or 0
        if old_state == 0 and current_user.kobo_only_shelves_sync == 1:
            kobo_sync_status.update_on_sync_shelfs(current_user.id)

    except Exception as ex:
        flash(str(ex), category="error")
        return render_title_template("user_edit.html",
                                     content=current_user,
                                     config=config,
                                     translations=translations,
                                     profile=1,
                                     languages=languages,
                                     title=_("%(name)s's Profile", name=current_user.name),
                                     page="me",
                                     kobo_support=kobo_support,
                                     registered_oauth=local_oauth_check,
                                     oauth_status=oauth_status)

    val = 0
    for key, __ in to_save.items():
        if key.startswith('show'):
            val += int(key[5:])
    current_user.sidebar_view = val
    if to_save.get("Show_detail_random"):
        current_user.sidebar_view += constants.DETAIL_RANDOM

    try:
        ub.session.commit()
        flash(_("Success! Profile Updated"), category="success")
        log.debug("Profile updated")
    except IntegrityError:
        ub.session.rollback()
        flash(_("Oops! An account already exists for this Email."), category="error")
        log.debug("Found an existing account for this Email")
    except OperationalError as e:
        ub.session.rollback()
        log.error("Database error: %s", e)
        flash(_("Oops! Database Error: %(error)s.", error=e), category="error")


@web.route("/me", methods=["GET", "POST"])
@user_login_required
def profile():
    languages = calibre_db.speaking_language()
    translations = get_available_locale()
    kobo_support = feature_support['kobo'] and config.config_kobo_sync
    if feature_support['oauth'] and config.config_login_type == 2:
        oauth_status = get_oauth_status()
        local_oauth_check = oauth_check
    else:
        oauth_status = None
        local_oauth_check = {}

    if request.method == "POST":
        change_profile(kobo_support, local_oauth_check, oauth_status, translations, languages)
    return render_title_template("user_edit.html",
                                 translations=translations,
                                 profile=1,
                                 languages=languages,
                                 content=current_user,
                                 config=config,
                                 kobo_support=kobo_support,
                                 title=_("%(name)s's Profile", name=current_user.name),
                                 page="me",
                                 registered_oauth=local_oauth_check,
                                 oauth_status=oauth_status)


# ###################################Show single book ##################################################################


def recent_reading(user_id, limit=6):
    """首页「继续阅读」取数（R213-B / MB-17）。

    Why 不直接 order_by 后 limit：`reading_progress` 里可能残留已读完的书与被
    删除的书，先截断再过滤会让列表出现空位。这里按 limit 的 3 倍取候选再过滤，
    过滤后不足 limit 就少显示几张卡，不补位。

    Why 返回 dict 而不是 ORM 行：模板要的是「书名 + 封面 + 37/125」，
    拼装放在这里，避免模板里再 join 书库。
    """
    if not user_id:
        return []
    try:
        rows = ub.session.query(ub.ReadingProgress).filter(
            ub.ReadingProgress.user_id == int(user_id)).order_by(
            ub.ReadingProgress.last_read_at.desc()).limit(max(limit, 1) * 3).all()
    except Exception as e:
        log.warning("recent_reading query failed: %s", e)
        return []
    if not rows:
        return []

    book_ids = [r.book_id for r in rows]
    # 一次查出已读完集合，避免逐本查 ReadBook
    finished = set()
    try:
        for read_book in ub.session.query(ub.ReadBook).filter(
                ub.ReadBook.user_id == int(user_id),
                ub.ReadBook.book_id.in_(book_ids),
                ub.ReadBook.read_status == ub.ReadBook.STATUS_FINISHED).all():
            finished.add(read_book.book_id)
    except Exception as e:
        log.warning("recent_reading read-status lookup failed: %s", e)

    entries = []
    for row in rows:
        if len(entries) >= limit:
            break
        if row.book_id in finished:
            continue
        try:
            book = calibre_db.get_filtered_book(row.book_id)
        except Exception:
            book = None
        # 书被删或当前用户无权看：静默跳过，不进列表也不报错
        if not book:
            continue
        entries.append({
            "book": book,
            "format": row.book_format,
            "position": row.position,
            "percent": row.progress_percent,
            "page_current": row.page_current,
            "page_total": row.page_total,
            "last_read_at": row.last_read_at,
        })
    return entries


@web.route("/read/<int:book_id>/<book_format>")
@login_required_if_no_ano
@viewer_required
def read_book(book_id, book_format):
    book = calibre_db.get_filtered_book(book_id)

    if not book:
        flash(_("Oops! Selected book is unavailable. File does not exist or is not accessible"),
              category="error")
        log.debug("Selected book is unavailable. File does not exist or is not accessible")
        return redirect(url_for("web.index"))

    book.ordered_authors = calibre_db.order_authors([book], False)

    # check if book has a bookmark
    bookmark = None
    if current_user.is_authenticated:
        bookmark = ub.session.query(ub.Bookmark).filter(and_(ub.Bookmark.user_id == int(current_user.id),
                                                             ub.Bookmark.book_id == book_id,
                                                             ub.Bookmark.format == book_format.upper())).first()
    # 账号级阅读位置（R213-B）：EPUB 恢复位置用；服务端优先于浏览器 localStorage
    reading_position = None
    if current_user.is_authenticated:
        progress = ub.session.query(ub.ReadingProgress).filter(
            ub.ReadingProgress.user_id == int(current_user.id),
            ub.ReadingProgress.book_id == book_id,
            ub.ReadingProgress.book_format == book_format.upper()).first()
        if progress:
            reading_position = {
                "position": progress.position,
                "percent": progress.progress_percent,
                "page_current": progress.page_current,
                "page_total": progress.page_total,
            }
    if book_format.lower() == "epub" or book_format.lower() == "kepub":
        log.debug("Start [k]epub reader for %d", book_id)
        return render_title_template('read.html', bookid=book_id, title=book.title, bookmark=bookmark,
                                     book_format=book_format, reading_position=reading_position)
    elif book_format.lower() == "pdf":
        log.debug("Start pdf reader for %d", book_id)
        return render_title_template('readpdf.html', pdffile=book_id, title=book.title,
                                     reading_position=reading_position)
    elif book_format.lower() == "txt":
        log.debug("Start txt reader for %d", book_id)
        return render_title_template('readtxt.html', txtfile=book_id, title=book.title,
                                     reading_position=reading_position)
    elif book_format.lower() in ["djvu", "djv"]:
        log.debug("Start djvu reader for %d", book_id)
        return render_title_template('readdjvu.html', djvufile=book_id, title=book.title,
                                     extension=book_format.lower())
    else:
        for fileExt in constants.EXTENSIONS_AUDIO:
            if book_format.lower() == fileExt:
                entries = calibre_db.get_filtered_book(book_id)
                log.debug("Start mp3 listening for %d", book_id)
                return render_title_template('listenmp3.html', mp3file=book_id, audioformat=book_format.lower(),
                                             entry=entries, bookmark=bookmark)
        for fileExt in ["cbr", "cbt", "cbz"]:
            if book_format.lower() == fileExt:
                all_name = str(book_id)
                title = book.title
                if len(book.series):
                    title = title + " - " + book.series[0].name
                    if book.series_index:
                        title = title + " #" + '{0:.2f}'.format(book.series_index).rstrip('0').rstrip('.')
                log.debug("Start comic reader for %d", book_id)
                return render_title_template('readcbr.html', comicfile=all_name, title=title,
                                             extension=fileExt, bookmark=bookmark)
        log.debug("Selected book is unavailable. File does not exist or is not accessible")
        flash(_("Oops! Selected book is unavailable. File does not exist or is not accessible"),
              category="error")
        return redirect(url_for("web.index"))


@web.route("/book/<int:book_id>")
@login_required_if_no_ano
def show_book(book_id):
    entries = calibre_db.get_book_read_archived(book_id, config.config_read_column, allow_show_archived=True)
    if entries:
        read_book = entries[1]
        archived_book = entries[2]
        entry = entries[0]
        entry.read_status = read_book == ub.ReadBook.STATUS_FINISHED
        entry.is_archived = archived_book
        for lang_index in range(0, len(entry.languages)):
            entry.languages[lang_index].language_name = isoLanguages.get_language_name(get_locale(), entry.languages[
                lang_index].lang_code)
        cc = calibre_db.get_cc_columns(config, filter_config_custom_read=True)
        book_in_shelves = []
        shelves = ub.session.query(ub.BookShelf).filter(ub.BookShelf.book_id == book_id).all()
        for sh in shelves:
            book_in_shelves.append(sh.shelf)

        entry.tags = sort(entry.tags, key=lambda tag: tag.name)

        entry.ordered_authors = calibre_db.order_authors([entry])

        entry.email_share_list = check_send_to_ereader(entry)
        entry.reader_list = check_read_formats(entry)

        entry.reader_list_sizes = dict()
        for data in entry.data:
            if data.format.lower() in entry.reader_list:
                entry.reader_list_sizes[data.format.lower()] = data.uncompressed_size

        entry.audio_entries = []
        for media_format in entry.data:
            if media_format.format.lower() in constants.EXTENSIONS_AUDIO:
                entry.audio_entries.append(media_format.format.lower())

        return render_title_template('detail.html',
                                     entry=entry,
                                     cc=cc,
                                     is_xhr=request.headers.get('X-Requested-With') == 'XMLHttpRequest',
                                     title=entry.title,
                                     books_shelfs=book_in_shelves,
                                     nce_book_no=resolve_nce_book_no(entry),
                                     page="book")
    else:
        log.debug("Selected book is unavailable. File does not exist or is not accessible")
        flash(_("Oops! Selected book is unavailable. File does not exist or is not accessible"),
              category="error")
        return redirect(url_for("web.index"))



# ---- R181（架构评审 B2）：定制路由按域分文件（cps/routes/）----
# 装饰注册沿用原 web blueprint（endpoint 名不变，url_for/模板/前端零改动）；
# 原版路由留在本文件（上游同款）。本 import 必须在全部辅助符号定义之后。
from cps.routes import register_domain_routes
register_domain_routes(web)
# cps/routes/home.py — 首页 `/home` 域路由（R213-C / MB-18，架构评审 B2 分域惯例）。
#
# 职责边界：
#   本文件只做「组装」——继续阅读取数复用 R213-B 的 `web.recent_reading`，
#   今日计划由前端异步拉既有代理端点，分级推荐是纯规则（不引入推荐算法）。
#   所有数据块各自 try，任一失败只降级该块，不整页 500（AC C3）。

import logging
import random
import re

from cps.web import recent_reading
from cps.web import web
from .. import calibre_db
from .. import config
from .. import db
from .. import ub
from ..cw_login import current_user
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from flask_babel import gettext as _
from sqlalchemy import func
from sqlalchemy import or_

log = logging.getLogger(__name__)

# 继续阅读与每阶推荐的本数（LLD §8 常量，不做成站点配置——这两个数没有
# 「按站点调」的需求，配置项越多越容易没人记得它在哪）。
HOME_RECENT_LIMIT = 6
HOME_LEVEL_PICKS = 6

# 分级书架命名解析（LLD §4.2）。刻意不锚定结尾：真实书架名常带副标题
# （「阶3 桥梁书」「分级阶2（2025）」），锚定结尾会把它们全判成未分级。
_LEVEL_RE = re.compile(r"^(?:分级)?阶\s*(\d+)")

UNLEVELED_LABEL = "未分级"


def level_of_shelf(name):
    """书架名 → 难度阶号；解析不出返回 None。

    Why 只认「阶N / 分级阶N」：本仓书架的难度信息只存在于名字里（shelf 表
    没有 kind/level 列，见 HLD §7.1 的拍板：本迭代不加列）。名字解析零 schema，
    但**判据必须窄**——「第一阶段」这类名字不该被算成阶 1。
    """
    match = _LEVEL_RE.match((name or "").strip())
    return int(match.group(1)) if match else None


def group_book_ids_by_level(shelf_rows):
    """[(shelf_id, name, book_id)] → ({level: set(book_id)}, {None: set(book_id)})。

    Why 单独成函数：这是唯一有分支的纯逻辑（同阶多书架合并、未分级归尾组），
    抽出来才能不碰数据库直接测（测试环境没有 calibre 库）。
    """
    grouped = {}
    for shelf_id, name, book_id in shelf_rows:
        if book_id is None:
            continue
        level = level_of_shelf(name)
        grouped.setdefault(level, set()).add(book_id)
    return grouped


def _finished_book_ids(user_id, book_ids):
    """已读完的书 id 集合——推荐里不该出现「读完了还推给你」。"""
    if not book_ids:
        return set()
    try:
        rows = ub.session.query(ub.ReadBook.book_id).filter(
            ub.ReadBook.user_id == int(user_id),
            ub.ReadBook.book_id.in_(list(book_ids)),
            ub.ReadBook.read_status == ub.ReadBook.STATUS_FINISHED).all()
    except Exception as exc:
        # 查不到就当没读过：推荐宁可多推一本，也不该整块消失
        log.warning("level picks: read-status lookup failed: %s", exc)
        return set()
    return {row[0] for row in rows}


def level_recommendations(user_id, per_level=None):
    """按难度阶分组的推荐书目（AC C4）。

    返回 `[{"level": 1|2|...|None, "label": "阶1"/"未分级", "books": [Books]}]`，
    阶号升序、未分级排最后。

    Why 不按书架名 ASCII 序排：`阶10` 会排在 `阶2` 前面（AC C4 点名要防的坑）。
    Why 先按 book_id 抽样、再逐本 `get_filtered_book`：一次把整阶几百本书的
    ORM 对象全查出来只为展示 6 本，代价不成比例；抽样后最多 6 次按主键查。
    """
    per_level = per_level or HOME_LEVEL_PICKS
    shelf_rows = []
    try:
        shelves = ub.session.query(ub.Shelf.id, ub.Shelf.name).filter(
            or_(ub.Shelf.is_public == 1, ub.Shelf.user_id == int(user_id))).all()
    except Exception as exc:
        log.warning("level picks: shelf lookup failed: %s", exc)
        return []
    shelf_names = {row[0]: row[1] for row in shelves}
    if not shelf_names:
        return []

    try:
        links = ub.session.query(ub.BookShelf.shelf, ub.BookShelf.book_id).filter(
            ub.BookShelf.shelf.in_(list(shelf_names.keys()))).all()
    except Exception as exc:
        log.warning("level picks: shelf book lookup failed: %s", exc)
        return []
    for shelf_id, book_id in links:
        shelf_rows.append((shelf_id, shelf_names.get(shelf_id), book_id))

    grouped = group_book_ids_by_level(shelf_rows)
    if not grouped:
        return []

    finished = _finished_book_ids(user_id, set().union(*grouped.values()))
    groups = []
    for level in sorted([k for k in grouped if k is not None]):
        groups.append((level, "阶{0}".format(level)))
    if None in grouped:
        groups.append((None, UNLEVELED_LABEL))

    result = []
    for level, label in groups:
        candidates = sorted(grouped.get(level, set()) - finished)
        if not candidates:
            continue
        picks = random.sample(candidates, min(per_level, len(candidates)))
        books = []
        for book_id in picks:
            try:
                book = calibre_db.get_filtered_book(book_id)
            except Exception:
                book = None
            # 书被删 / 当前用户无权看：跳过，不进推荐也不报错
            if book:
                books.append(book)
        if books:
            result.append({"level": level, "label": label, "books": books})
    return result


def random_discover_books(limit=None):
    """「随机发现」模块取数：原首页的随机书墙，原样搬进首页当一个模块。

    Why 不直接调 `fill_indexpage`：那套要同时算分页与主列表，首页只要随机墙；
    这里复用它的随机查询姿势（`generate_linked_query` + `common_filters`），
    保证与 `/` 的可见性过滤一致（受限书、归档书都不会漏出来）。
    """
    limit = limit or getattr(config, "config_random_books", 6) or 6
    try:
        query = calibre_db.generate_linked_query(config.config_read_column, db.Books)
        return query.filter(calibre_db.common_filters()).order_by(func.random()).limit(limit).all()
    except Exception as exc:
        log.warning("home: random discover failed: %s", exc)
        return []


@web.route("/home", methods=["GET"])
@user_login_required
def home():
    """新首页（R213-C）：继续阅读 / 今日计划 / 分级推荐 / 随机发现。

    Why 四块各自 try：这是登录落点，任何一块的上游抖动都不该让人「登录后
    看到 500」。今日计划的取数在前端（`home.js` 拉既有代理端点），服务端
    零上游调用——moon-well 慢不拖首屏，这是 R166 定下的同款姿势。
    """
    user_id = int(current_user.id)
    recent_books = recent_reading(user_id, HOME_RECENT_LIMIT)
    level_groups = level_recommendations(user_id, HOME_LEVEL_PICKS)
    discover_books = random_discover_books() if current_user.show_detail_random() else []
    return render_title_template("home.html", title=_("Home"), page="home",
                                 recent_books=recent_books,
                                 level_groups=level_groups,
                                 discover_books=discover_books)

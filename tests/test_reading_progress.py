"""R213-B / MB-17：账号级阅读位置（`reading_progress`）的守卫测试。

覆盖：
  1. 上报后落库，重复上报走 upsert（唯一约束生效，不新增行）。
  2. `last_read_at` 每次上报推进（同页反复开合也算「最近阅读」）。
  3. 入参防御：book_id / format 非法 → 400 且不落库；percent 越界被夹取；
     page_current > page_total 被夹取。
  4. `recent_reading` 排除已读完的书与被删除的书。
  5. 匿名上报被拒（登录门禁）。

Why 直接测 `recent_reading` 而不是走首页：/home 属 R213-C（MB-18），本单只交付
数据与取数函数；取数口径（排除已读/已删）必须在本单就钉住，否则 C 组装时才发现
口径不一致，会变成跨单返工。
"""

import pytest

from cps import ub


@pytest.fixture
def clean_progress(app):
    """每个用例前后清空 reading_progress，避免共享库相互污染。"""
    def _wipe():
        try:
            ub.session.query(ub.ReadingProgress).delete()
            ub.session.commit()
        except Exception:
            ub.session.rollback()
    _wipe()
    yield
    _wipe()


def _post(client, payload):
    return client.post("/ajax/reading-progress", json=payload)


def test_report_creates_and_upserts(admin_client, clean_progress):
    """同一 (user, book, format) 只一行，第二次上报改值不改行数。"""
    first = _post(admin_client, {"book_id": 1, "format": "EPUB",
                                 "position": "epubcfi(/6/4!/4/2/2)", "percent": 12.5,
                                 "page_current": 37, "page_total": 125})
    assert first.status_code == 200
    assert first.get_json()["success"] is True

    rows = ub.session.query(ub.ReadingProgress).all()
    assert len(rows) == 1
    assert rows[0].page_current == 37
    first_read_at = rows[0].last_read_at

    second = _post(admin_client, {"book_id": 1, "format": "EPUB",
                                  "position": "epubcfi(/6/8!/4/2/2)", "percent": 40,
                                  "page_current": 50, "page_total": 125})
    assert second.status_code == 200

    rows = ub.session.query(ub.ReadingProgress).all()
    assert len(rows) == 1, "唯一约束失效：同一本书同一格式被写成多行"
    assert rows[0].page_current == 50
    assert rows[0].progress_percent == 40
    assert rows[0].position == "epubcfi(/6/8!/4/2/2)"
    assert rows[0].last_read_at >= first_read_at, "最近阅读时间未推进"


def test_last_read_at_advances_on_same_position(admin_client, clean_progress):
    """位置没变（同页重开）也要刷新 last_read_at，否则首页排序会失真。"""
    payload = {"book_id": 2, "format": "EPUB", "position": "epubcfi(/6/2!/4/2)"}
    _post(admin_client, payload)
    first = ub.session.query(ub.ReadingProgress).one().last_read_at
    _post(admin_client, payload)
    second = ub.session.query(ub.ReadingProgress).one().last_read_at
    assert second >= first


@pytest.mark.parametrize("payload", [
    {"format": "EPUB"},                        # 缺 book_id
    {"book_id": 0, "format": "EPUB"},          # 非正数
    {"book_id": "abc", "format": "EPUB"},      # 非数字
    {"book_id": 1, "format": "DOCX"},          # 格式不在白名单
    {"book_id": 1},                            # 缺 format
])
def test_invalid_payload_rejected(admin_client, clean_progress, payload):
    resp = _post(admin_client, payload)
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False
    assert ub.session.query(ub.ReadingProgress).count() == 0


def test_percent_clamped(admin_client, clean_progress):
    """越界百分比夹到 0–100，而不是整条记录被拒。"""
    _post(admin_client, {"book_id": 3, "format": "EPUB", "percent": 150})
    assert ub.session.query(ub.ReadingProgress).one().progress_percent == 100.0

    _post(admin_client, {"book_id": 4, "format": "EPUB", "percent": -5})
    row = ub.session.query(ub.ReadingProgress).filter_by(book_id=4).one()
    assert row.progress_percent == 0.0


def test_page_current_clamped_to_total(admin_client, clean_progress):
    _post(admin_client, {"book_id": 5, "format": "EPUB",
                         "page_current": 200, "page_total": 125})
    row = ub.session.query(ub.ReadingProgress).one()
    assert row.page_current == 125


def test_anonymous_report_rejected(client, clean_progress):
    """登录门禁：匿名上报不得写库。"""
    resp = client.post("/ajax/reading-progress", json={"book_id": 6, "format": "EPUB"})
    assert resp.status_code in (302, 401, 403)
    assert ub.session.query(ub.ReadingProgress).count() == 0


class _FakeBook:
    def __init__(self, book_id, title):
        self.id = book_id
        self.title = title


class _FakeCalibreDb:
    """calibre 书库桩：测试环境没有 metadata.db，按 id 查表即可。"""

    def __init__(self, books):
        self._books = books

    def get_filtered_book(self, book_id):
        return self._books.get(book_id)


def test_recent_reading_skips_finished_and_missing(app, admin_client, clean_progress, monkeypatch):
    """已读完 / 书已删除的条目都不进「继续阅读」。"""
    import datetime as _dt
    from cps import web as web_mod

    user_id = int(ub.session.query(ub.User).filter(ub.User.name == "admin").one().id)
    now = _dt.datetime.now(_dt.timezone.utc)
    for offset, book_id in enumerate([101, 102, 103]):
        ub.session.add(ub.ReadingProgress(
            user_id=user_id, book_id=book_id, book_format="EPUB",
            position="epubcfi(/6/%d!/4/2)" % (offset + 2), progress_percent=10.0 * (offset + 1),
            page_current=10, page_total=100,
            last_read_at=now - _dt.timedelta(minutes=offset)))
    # 102 已读完；103 在书库里不存在（模拟书被删）
    ub.session.add(ub.ReadBook(user_id=user_id, book_id=102,
                               read_status=ub.ReadBook.STATUS_FINISHED))
    ub.session.commit()

    monkeypatch.setattr(web_mod, "calibre_db",
                        _FakeCalibreDb({101: _FakeBook(101, "继续读这本"),
                                        102: _FakeBook(102, "已读完")}))
    result = web_mod.recent_reading(user_id, limit=6)
    ids = [entry["book"].id for entry in result]
    assert ids == [101], f"期望只剩 101，实际 {ids}"


def test_recent_reading_empty_when_no_progress(app):
    from cps import web as web_mod
    assert web_mod.recent_reading(99999, limit=6) == []


# ---------------------------------------------------------------------------
# 阅读状态同步（2026-10-24 缺陷修复）
#
# 背景：网页阅读器此前只写位置不写状态，`book_read_link.read_status` 里
# `STATUS_IN_PROGRESS` 全库 0 行（只有 Kobo 同步会写），导致高级搜索的
# 「在读」返回空集。现在由进度上报端点负责把书标成在读。
# ---------------------------------------------------------------------------
@pytest.fixture
def clean_link(app):
    """只清理本组用例造出来的 book_read_link 行，不动其他用例的书。"""
    ids = (9001, 9002, 9003)

    def _wipe():
        try:
            ub.session.query(ub.ReadBook).filter(
                ub.ReadBook.book_id.in_(ids)).delete(synchronize_session=False)
            ub.session.commit()
        except Exception:
            ub.session.rollback()
    _wipe()
    yield
    _wipe()


def test_report_marks_book_in_progress(admin_client, clean_progress, clean_link):
    """打开即算在读：哪怕 percent=0、停在第 1 页也要落状态。"""
    resp = _post(admin_client, {"book_id": 9001, "format": "EPUB",
                                "percent": 0, "page_current": 1, "page_total": 125})
    assert resp.status_code == 200

    row = ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 9001).one()
    assert row.read_status == ub.ReadBook.STATUS_IN_PROGRESS, \
        "上报进度后书未被标成在读——搜索「在读」仍会是空集"


def test_report_upgrades_unread_to_in_progress(admin_client, clean_progress, clean_link):
    """已有 UNREAD(0) 记录的书，上报后升级为 IN_PROGRESS(2)。"""
    _post(admin_client, {"book_id": 9002, "format": "EPUB"})
    row = ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 9002).one()
    row.read_status = ub.ReadBook.STATUS_UNREAD
    ub.session.commit()

    _post(admin_client, {"book_id": 9002, "format": "EPUB", "page_current": 5})
    row = ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 9002).one()
    assert row.read_status == ub.ReadBook.STATUS_IN_PROGRESS


def test_report_does_not_downgrade_finished(admin_client, clean_progress, clean_link):
    """已读完的书回看，状态保持 FINISHED——完成标记是用户的显式决定。"""
    _post(admin_client, {"book_id": 9003, "format": "EPUB"})
    row = ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 9003).one()
    row.read_status = ub.ReadBook.STATUS_FINISHED
    ub.session.commit()

    _post(admin_client, {"book_id": 9003, "format": "EPUB", "percent": 3, "page_current": 2})
    row = ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 9003).one()
    assert row.read_status == ub.ReadBook.STATUS_FINISHED, \
        "已读完的书被网页阅读降级回在读了"


def test_report_does_not_touch_kobo_counters(admin_client, clean_progress, clean_link):
    """网页阅读不能污染 Kobo 的阅读统计字段。"""
    _post(admin_client, {"book_id": 9001, "format": "EPUB", "page_current": 3})
    _post(admin_client, {"book_id": 9001, "format": "EPUB", "page_current": 9})

    row = ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 9001).one()
    assert row.times_started_reading == 0, "网页阅读不该累加 Kobo 的「打开次数」"
    assert row.last_time_started_reading is None, "网页阅读不该写 Kobo 的「上次开始阅读时间」"

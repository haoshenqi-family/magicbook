"""R241：整本能力缓存齐备标识（readiness）单测 + 模板结构守卫。

Why 这套用例：标识的判定完全依赖三张批次表的「完成」字段与正文指纹一致性，
把任何一处口径写错都不会报错，只会静默给读者一个错的成本暗示（或者永远不亮）。
所以既要有纯逻辑用例钉住判定，也要有结构断言钉住模板真的把它渲染出来。
"""
import datetime
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cps import ub as ub_module
from cps.reading_insight import readiness
from cps.reading_translation.models import TranslationJob
from cps.reading_tts.models import ReadingTtsJob
from cps.reading_word_detail.models import WordDetailJob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DETAIL = os.path.join(ROOT, "cps", "templates", "detail.html")
PANEL = os.path.join(ROOT, "cps", "templates", "partials", "whole_book_panel.html")
WEB = os.path.join(ROOT, "cps", "web.py")

FINGERPRINT = "fp-current"
FORMAT = "epub"
# 现行三条 service 写台账都用 .upper()（translation:123 / tts:164 / word_detail:355），
# 夹具默认跟随生产形态：用大写入库才能钉住 readiness 的大小写兼容（SQL 侧 lower()）。
DB_FORMAT = "EPUB"


@pytest.fixture
def db(monkeypatch):
    """三张批次表的独立内存库；同时把抢眼的外部依赖（文件/指纹）换成纯函数。

    Why 不跑 create_app：本模块的判定是「查询 + 比较」，与 Flask 上下文无关；
    拉起整站只会把用例变慢并把无关失败混进来。
    """
    engine = create_engine("sqlite:///:memory:")
    ub_module.Base.metadata.create_all(
        engine, tables=[TranslationJob.__table__, ReadingTtsJob.__table__,
                        WordDetailJob.__table__])
    session = sessionmaker(bind=engine)()
    monkeypatch.setattr(ub_module, "session", session)
    monkeypatch.setattr(readiness, "_book_file", lambda book_id, book_format: (object(), "/tmp/x.epub"))
    monkeypatch.setattr(readiness, "_fingerprint", lambda path: FINGERPRINT)
    yield session
    session.close()


def _translate(total=10, completed=10, fingerprint=FINGERPRINT, fmt=DB_FORMAT, status="COMPLETED",
               created=None):
    return TranslationJob(id="t-{0}".format(created or 1), user_id=1, book_id=7, book_format=fmt,
                          book_fingerprint=fingerprint, status=status,
                          total_count=total, completed_count=completed,
                          created_at=created or datetime.datetime(2026, 10, 1))


def _tts(total=10, done=10, fingerprint=FINGERPRINT, fmt=DB_FORMAT, status="COMPLETED"):
    return ReadingTtsJob(id="a1", user_id=1, book_id=7, book_format=fmt,
                         book_fingerprint=fingerprint, status=status,
                         total_count=total, done_count=done)


def _word_detail(target=100, covered=100, fingerprint=FINGERPRINT, fmt=DB_FORMAT,
                 status="COMPLETED", distinct=1000):
    return WordDetailJob(id="w1", user_id=1, book_id=7, book_format=fmt,
                         book_fingerprint=fingerprint, status=status,
                         distinct_words=distinct, target_words=target, covered_words=covered)


def test_all_three_full_marks_book_ready(db):
    db.add_all([_translate(), _tts(), _word_detail()])
    db.commit()

    result = readiness.book_readiness(7, FORMAT)

    assert result["all"] is True
    assert result["translate"] == {"ready": True, "done": 10, "total": 10}
    assert result["tts"] == {"ready": True, "done": 10, "total": 10}
    # 详解带全书词数：分母是本次补缺词数，悬停要说清全书口径（reviewer C2）
    assert result["wordDetail"] == {"ready": True, "done": 100, "total": 100, "wholeWords": 1000}


def test_legacy_lowercase_format_row_still_matches(db):
    """存量行可能写成小写；SQL 侧 lower() 必须兜住（否则线上标识一枚都不亮）。"""
    db.add_all([_translate(fmt="epub"), _tts(fmt="epub"), _word_detail(fmt="epub")])
    db.commit()

    assert readiness.book_readiness(7, FORMAT)["all"] is True


def test_missing_one_chain_keeps_book_not_ready(db):
    """三项缺一项就不是「都能便宜学」——总标必须不亮，但已备齐的分项仍要亮。"""
    db.add_all([_translate(), _tts()])
    db.commit()

    result = readiness.book_readiness(7, FORMAT)

    assert result["all"] is False
    assert result["translate"]["ready"] is True
    assert result["tts"]["ready"] is True
    assert result["wordDetail"]["ready"] is False


def test_fingerprint_mismatch_invalidates_stale_batch(db):
    """书被替换/重排后，旧批次不再代表这一版正文的缓存。"""
    db.add_all([_translate(fingerprint="fp-old"), _tts(fingerprint="fp-old"),
                _word_detail(fingerprint="fp-old")])
    db.commit()

    result = readiness.book_readiness(7, FORMAT)

    assert result["all"] is False
    assert all(not result[kind]["ready"] for kind in readiness.KINDS)


def test_caller_supplied_fingerprint_skips_file_lookup(db, monkeypatch):
    """show_book 复用速览指纹时，不该再取一次书、stat 一次文件。"""

    def _boom(*_args, **_kwargs):
        raise AssertionError("fingerprint 已给出时不应再定位文件")

    monkeypatch.setattr(readiness, "_book_file", _boom)
    monkeypatch.setattr(readiness, "_fingerprint", _boom)
    db.add_all([_translate(), _tts(), _word_detail()])
    db.commit()

    assert readiness.book_readiness(7, FORMAT, fingerprint=FINGERPRINT)["all"] is True


def test_partial_coverage_is_not_ready(db):
    """COMPLETED 却 done<total 的存量脏行不能被当成跑满。"""
    db.add_all([_translate(total=10, completed=9), _tts(total=10, done=9),
                _word_detail(target=100, covered=99)])
    db.commit()

    result = readiness.book_readiness(7, FORMAT)

    assert result["all"] is False
    assert all(not result[kind]["ready"] for kind in readiness.KINDS)


def test_done_over_total_counts_as_full(db):
    """计数可能因缓存回收被多加（历史数据）；跑超了也算跑满，不该卡在 9/10 形态。"""
    db.add_all([_translate(total=10, completed=11), _tts(total=10, done=11),
                _word_detail(target=100, covered=101)])
    db.commit()

    assert readiness.book_readiness(7, FORMAT)["all"] is True


def test_format_mismatch_is_not_ready(db):
    """kepub 的批次不能给 epub 版本书背书。"""
    db.add_all([_translate(fmt="KEPUB"), _tts(fmt="KEPUB"), _word_detail(fmt="KEPUB")])
    db.commit()

    assert readiness.book_readiness(7, FORMAT)["all"] is False


def test_zero_total_is_not_ready(db):
    """total=0 只说明没跑成，不说明缓存有内容。"""
    db.add_all([_translate(total=0, completed=0), _tts(total=0, done=0),
                _word_detail(target=0, covered=0)])
    db.commit()

    assert readiness.book_readiness(7, FORMAT)["all"] is False


def test_non_completed_batch_is_ignored(db):
    db.add_all([_translate(status="PARTIAL_FAILED"), _tts(status="PARTIAL_FAILED"),
                _word_detail(status="PARTIAL_FAILED")])
    db.commit()

    assert readiness.book_readiness(7, FORMAT)["all"] is False


def test_published_but_not_converged_is_not_ready(db):
    """已知边界（LLD §3）：发布线程跑完但还没被进度轮询收敛的批次不算备齐。

    现行设计是「查询进度时懒刷新」——moon-well 写完缓存不会回调 magicbook，
    只有整本任务面板/批量进度页轮询过才会把状态推到 COMPLETED。这条用例把
    边界显式钉住：将来谁改了收敛机制，会在这里看到行为变化。
    """
    db.add_all([_translate(status="RUNNING", completed=0), _tts(status="RUNNING"),
                _word_detail(status="RUNNING", covered=0)])
    db.commit()

    assert readiness.book_readiness(7, FORMAT)["all"] is False


def test_older_full_batch_survives_later_partial_row(db):
    """更新的批次没跑满时，仍应回退到更早跑满的那一批（不被一票否决）。"""
    db.add_all([_translate(), _tts(), _word_detail()])
    db.commit()
    newer = _translate(total=20, completed=3, created=datetime.datetime(2026, 10, 20))
    db.add(newer)
    db.commit()

    assert readiness.book_readiness(7, FORMAT)["translate"]["ready"] is True


def test_query_failure_degrades_to_not_ready(db, monkeypatch):
    """台账查询炸了也只能少亮标识，不能让书页 500。"""

    class _Boom:
        def query(self, *args, **kwargs):
            raise RuntimeError("db is on fire")

    monkeypatch.setattr(ub_module, "session", _Boom())

    result = readiness.book_readiness(7, FORMAT)

    assert result["all"] is False
    assert all(not result[kind]["ready"] for kind in readiness.KINDS)


def test_unreadable_book_file_degrades_to_not_ready(db, monkeypatch):
    def _raise(book_id, book_format):
        raise ValueError("book file is unavailable")

    monkeypatch.setattr(readiness, "_book_file", _raise)

    result = readiness.book_readiness(7, FORMAT)

    assert result["all"] is False


# ---------------------------------------------------------------------------
# 结构守卫：标识必须真的出现在详情页与整本任务面板里
# ---------------------------------------------------------------------------

def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_detail_renders_all_three_cache_chips():
    src = _read(DETAIL)
    assert 'id="cache-ready-all"' in src
    for kind in ("translate", "tts", "wordDetail"):
        # 每个分项都有自己的小标；写死三份而不是循环，避免模板里再引一次 KINDS 常量
        assert 'data-kind="{0}"'.format(kind) in src, "缺少 {0} 的缓存小标".format(kind)
    # 条件取自 readiness 快照的三个 ready 字段（写错属性名时 grep 仍会过，故显式钉住）
    for kind in ("translate", "tts", "wordDetail"):
        assert "_cache.{0}.ready".format(kind) in src
    assert "_cache.all" in src
    assert "命中缓存按 1 积分/段计" in src


def test_panel_tabs_carry_cached_marker():
    src = _read(PANEL)
    assert src.count("wb-tab-cached") >= 3, "三个页签都应挂「已缓存」小标"
    for kind in ("translate", "tts", "wordDetail"):
        assert "_cache.{0}.ready".format(kind) in src


def _render_panel(cache_readiness):
    """真渲染整本面板：grep 只能证明字符串在，渲染才能证明 `_cache.<kind>.ready` 链是通的。

    Why 值得这份样板：Jinja 的 dict 属性访问出错时**不会报错**，只会渲染成空——
    「小标在该在的地方出现」这件事只有渲染结果说了算。面板的依赖只有 url_for /
    csrf_token / entry 三个，桩起来比整站 test client 便宜得多。
    """
    from types import SimpleNamespace

    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "cps", "templates")))
    for name in ("clean_string", "escapedlink", "formatdate", "formatfloat",
                 "last_modified", "yesno"):
        env.filters[name] = lambda value, *args, **kwargs: value
    env.globals["url_for"] = lambda *args, **kwargs: "/x"
    env.globals["csrf_token"] = lambda: "token"
    entry = SimpleNamespace(id=7, reader_list=["epub"], whole_book_active={},
                            cache_readiness=cache_readiness)
    return env.get_template("partials/whole_book_panel.html").render(entry=entry)


def test_panel_renders_marker_only_for_ready_kinds():
    ready = {"ready": True, "done": 10, "total": 10}
    not_ready = {"ready": False, "done": 0, "total": 0}

    out = _render_panel({"translate": ready, "tts": not_ready, "wordDetail": ready,
                         "all": False})
    assert out.count("wb-tab-cached") == 2

    out_all = _render_panel({"translate": ready, "tts": ready, "wordDetail": ready,
                             "all": True})
    assert out_all.count("wb-tab-cached") == 3

    out_none = _render_panel({"translate": not_ready, "tts": not_ready,
                              "wordDetail": not_ready, "all": False})
    assert "wb-tab-cached" not in out_none

    # 无快照（非 viewer / 取书失败）时面板照常渲染，不报 UndefinedError
    assert "wb-tab-cached" not in _render_panel(None)


def test_show_book_injects_readiness_for_viewers():
    """标识不受 admin 门禁限制：读者也要看得到（与三个整本入口的 admin 门禁区分）。"""
    src = _read(WEB)
    idx = src.find("book_readiness(")
    assert idx != -1, "show_book 未注入 cache_readiness"
    # 从赋值点往前找最近的「if entry.insight_format」判断块，避免固定窗口随注释行数漂移
    guard = src.rfind("if entry.insight_format", 0, idx)
    assert guard != -1, "cache_readiness 注入点前没有 insight_format 判断"
    window = src[guard:idx]
    assert "role_viewer" in window, "cache_readiness 的注入条件应含 role_viewer"
    assert "role_admin" not in window, "cache_readiness 不应被 admin 门禁包住"

"""R75 回归：整本翻译 offset-naive/offset-aware datetime 崩溃。

生产实锤：点击「整本译」报 can't subtract offset-naive and offset-aware
datetimes。TranslationJob.created_at/updated_at 是 naive DateTime 列，aware
值写入 DB 再读回 tzinfo=None（naive），service._now()（aware）与之相减即抛
TypeError；路由 except TypeError 把原文返回给前端 alert。

为什么单独建文件：既有 tests/test_reading_translation.py 中含有被写入护栏
拦截的占位令牌字面量（既有内容，非本次引入），对该文件的任何写入都会被
整体扫描拦下，故 R75 回归用例放在本文件，不动既有文件。
"""
import sys
import os
from datetime import datetime, timedelta, timezone

import pytest

_WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from cps.reading_translation import service as svc  # noqa: E402
from cps.reading_translation.models import TranslationJob, TranslationJobItem  # noqa: E402


def _write_epub(path):
    """与既有测试同构的最小 EPUB：1 个 xhtml、1 段可翻译文本。"""
    import zipfile
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    page = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Chapter One</title></head>"
            "<body><p>Fresh paragraph.</p></body></html>")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", page)


def _job_store():
    """真实 SQLite 往返的 TranslationJob 存取。

    Why: 内存对象直接持有 aware datetime 时旧测试全绿，但生产里值必须经
    DateTime 列往返、tzinfo 被丢成 naive；跳过 DB 往返的桩拦不住本缺陷。
    scoped_session 模拟生产的线程内同一会话语义（ub.session 形态）。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.pool import StaticPool
    from cps import ub as ub_module

    engine = create_engine("sqlite://", poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    ub_module.Base.metadata.create_all(
        engine, tables=[TranslationJob.__table__, TranslationJobItem.__table__])
    return scoped_session(sessionmaker(bind=engine))


def _patch_common(monkeypatch, tmp_path, book_title):
    """桩掉文件解析与身份，专注时间往返路径。"""
    _write_epub(tmp_path / "book.epub")
    monkeypatch.setattr(svc.WholeBookTranslationService, "_ensure_tables", lambda self: None)

    class _Book:
        title = book_title
        path = "."

    class _CalibreDB:
        @staticmethod
        def get_filtered_book(book_id):
            return _Book()

        @staticmethod
        def get_book_format(book_id, fmt):
            class _F:
                name = "book"
            return _F()

    class _Config:
        @staticmethod
        def get_book_path():
            return str(tmp_path)

    class _User:
        id = 1

    monkeypatch.setattr(svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(svc, "config", _Config)
    monkeypatch.setattr(svc, "current_user", _User, raising=False)

    spawned = []

    def _fake_spawn(self, job_id, book_title_, book_id, fingerprint, publish, lookup=None):
        spawned.append(job_id)

    monkeypatch.setattr(svc.WholeBookTranslationService, "_spawn_publish_worker", _fake_spawn)
    return spawned


def _seed_job(store, job_id, fingerprint, age, title):
    job = TranslationJob(id=job_id, user_id=1, book_id=1, book_format="EPUB",
                         book_fingerprint=fingerprint, book_name=title, status="RUNNING",
                         total_count=10, cached_count=0, published_count=0,
                         completed_count=0, failed_count=0,
                         created_at=datetime.now(timezone.utc) - age,
                         updated_at=datetime.now(timezone.utc) - age)
    store.add(job)
    store.commit()
    store.close()  # 过期全部实例：下次访问强制从 DB 重新加载（复现生产读回路径）


def _seed_fingerprint(tmp_path):
    """用 service 自身的 _book_file 拿到与生产完全一致的路径字符串再算指纹。"""
    service = svc.WholeBookTranslationService()
    _, file_path = service._book_file(1, "EPUB")
    return service._fingerprint(file_path)


def test_start_with_stale_job_survives_db_roundtrip(tmp_path, monkeypatch):
    """R75 回归（僵尸路径）：updated_at 停滞 >30 分钟的活动批次经真实 DB 往返
    读回 naive 值后，僵尸判定必须照常工作并新建批次，不得抛
    can't subtract offset-naive and offset-aware datetimes。"""
    spawned = _patch_common(monkeypatch, tmp_path, "Zombie Book")
    store = _job_store()
    monkeypatch.setattr(svc.ub, "session", store, raising=False)
    fingerprint = _seed_fingerprint(tmp_path)
    _seed_job(store, "zombie-db", fingerprint, timedelta(hours=3), "Zombie Book")

    def _publish(payload):
        raise AssertionError("spawn is stubbed; no publish expected")

    result = svc.WholeBookTranslationService().start(1, "EPUB", False, _publish, None)

    with store() as verify:
        closed = verify.query(TranslationJob).filter_by(id="zombie-db").one()
        assert closed.status == "PARTIAL_FAILED"
    assert len(spawned) == 1 and spawned[0] != "zombie-db"
    assert result["totalCount"] == 1
    assert result["jobId"] != "zombie-db"


def test_start_reuse_path_survives_db_roundtrip(tmp_path, monkeypatch):
    """R75 回归（复用路径）：活跃批次（<30 分钟）经 DB 往返读回 naive 值后，
    复用判断必须照常返回既有进度，不得抛 offset-naive/aware TypeError。
    修复前：epub.js 的「整本译」不传 force，已有活动批次时点击 100% 触发。"""
    spawned = _patch_common(monkeypatch, tmp_path, "Live Book")
    store = _job_store()
    monkeypatch.setattr(svc.ub, "session", store, raising=False)
    fingerprint = _seed_fingerprint(tmp_path)
    _seed_job(store, "live-db", fingerprint, timedelta(minutes=5), "Live Book")

    def _publish(payload):
        raise AssertionError("reuse path must not publish new segments")

    result = svc.WholeBookTranslationService().start(1, "EPUB", False, _publish, None)

    assert spawned == []
    assert result["jobId"] == "live-db"
    assert result["status"] == "RUNNING"

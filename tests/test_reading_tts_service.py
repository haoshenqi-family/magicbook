"""整本朗读批次服务测试（R166 设计 §3.1）。

姿势：真 app fixture（conftest 的 SQLite ub.session）+ 桩掉 Calibre 元数据/代理/
线程——daemon 用同步线程桩单进程驱动，验证批次生命周期、去重、幂等与计费通道标记。
"""

import zipfile

import pytest

from cps import ub
from cps.reading_tts import service as svc
from cps.reading_tts.models import ReadingTtsJob, ReadingTtsJobItem


def _write_epub(path):
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    one = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>C1</title></head>"
           "<body><p>Para one.</p><p>Para two.</p><p>Para one.</p></body></html>")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", one)


class _Book:
    id = 1
    title = "Test Book"
    language = "eng"
    comments = "<p>A girl who loves books.</p>"
    authors = []
    path = ""


@pytest.fixture
def env(app, tmp_path, monkeypatch):
    _write_epub(tmp_path / "book.EPUB")

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
        id = 7

    monkeypatch.setattr(svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(svc, "config", _Config)
    monkeypatch.setattr(svc, "current_user", _User)
    monkeypatch.setattr(svc.time, "sleep", lambda s: None)

    calls = []

    def proxy(path, payload, timeout, label, binary=False, method="POST", **kwargs):
        calls.append({"path": path, "payload": payload, "timeout": timeout, "binary": binary})
        return '{"voice":"Mia","style":"轻快清晰","reason":"儿童文学"}', 200

    return types_simple(calls=calls, proxy=proxy, original_proxy=proxy,
                        tmp_path=tmp_path, monkeypatch=monkeypatch)


def types_simple(**kwargs):
    import types
    return types.SimpleNamespace(**kwargs)


def _make_service(env, sync_worker=True):
    service = svc.WholeBookTtsService(env.proxy)
    if sync_worker:
        # daemon 线程替换为同步执行（单进程驱动，状态断言确定性）
        env.monkeypatch.setattr(service, "_spawn_synth_worker",
                                lambda job_id: service._synth_worker(job_id))
    return service


def _items(job_id):
    return (ub.session.query(ReadingTtsJobItem)
            .filter(ReadingTtsJobItem.job_id == job_id)
            .order_by(ReadingTtsJobItem.paragraph_index).all())


def test_start_creates_batch_dedupes_and_speaks_with_batch_source(env):
    service = _make_service(env)

    result = service.start(1, "EPUB")

    # 3 段提取、1 段重复 → 2 个 item（text_hash 去重）
    assert result["total"] == 2
    assert result["done"] == 2
    assert result["failed"] == 0
    assert result["status"] == "COMPLETED"
    # 整本选角先于合成，voice/style 回填批次
    assert env.calls[0]["path"] == svc.BOOK_VOICE_SELECT_PATH
    assert result["voice"] == "Mia"
    # 每次 speak 都带发起者计费通道标记（moon-well 按 source 分流计费）
    speak_calls = [c for c in env.calls if c["path"] == svc.SPEAK_PATH]
    assert len(speak_calls) == 2
    for call in speak_calls:
        assert call["payload"]["source"] == "book-tts-batch"
        assert call["binary"] is True
        assert call["timeout"] >= 200


def test_start_reuses_active_batch_for_same_book(env):
    service = _make_service(env)
    env.monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: None)

    first = service.start(1, "EPUB")
    calls_after_first = len(env.calls)
    second = service.start(1, "EPUB")

    assert first["jobId"] == second["jobId"]
    assert len(env.calls) == calls_after_first  # 复用不再选角/合成


def test_voice_select_failure_does_not_block_batch(env):
    def failing_proxy(path, payload, timeout, label, binary=False, method="POST", **kwargs):
        if path == svc.BOOK_VOICE_SELECT_PATH:
            raise RuntimeError("moon-well down")
        env.calls.append({"path": path, "payload": payload, "timeout": timeout, "binary": binary})
        return '{"ok":true}', 200

    service = svc.WholeBookTtsService(failing_proxy)
    env.monkeypatch.setattr(service, "_spawn_synth_worker",
                            lambda job_id: service._synth_worker(job_id))

    result = service.start(1, "EPUB")

    # 选角失败不阻断批次：voice/style 留空，段落照常合成
    assert result["status"] == "COMPLETED"
    assert result["voice"] is None


def test_synth_worker_marks_failed_after_retry_and_retry_requeues(env):
    service = _make_service(env)  # spawn=同步执行，retry 重跑在单进程内确定完成

    # 首轮：proxy 对 speak 持续 500 → 两段各重试 1 次后 FAILED
    def always_fail(path, payload, timeout, label, binary=False, method="POST", **kwargs):
        if path == svc.SPEAK_PATH:
            return "boom", 500
        return '{"ok":true}', 200

    service._proxy = always_fail
    result = service.start(1, "EPUB")
    job_id = result["jobId"]

    assert result["status"] == "PARTIAL_FAILED"
    assert all(i.status == "FAILED" and i.attempt_count == 2 for i in _items(job_id))

    # retry：FAILED → PENDING 并重跑（proxy 恢复成功；moon-well 缓存幂等，已完成段免费）
    service._proxy = env.original_proxy
    result2 = service.retry(job_id)

    assert result2["status"] == "COMPLETED"
    assert result2["failed"] == 0


def test_cancel_stops_batch(env):
    service = _make_service(env, sync_worker=False)
    env.monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: None)
    result = service.start(1, "EPUB")
    job_id = result["jobId"]

    cancelled = service.cancel(job_id)
    assert cancelled["status"] == "CANCELLED"

    # worker 见 CANCELLED 立即退出，不再合成
    env.calls.clear()
    service._synth_worker(job_id)
    assert not [c for c in env.calls if c["path"] == svc.SPEAK_PATH]

"""整本朗读批次服务测试（R166 设计 §3.1）。

姿势：真 app fixture（conftest 的 SQLite ub.session）+ 桩掉 Calibre 元数据/代理/
线程——daemon 用同步线程桩单进程驱动，验证批次生命周期、去重、幂等与计费通道标记。
"""

import threading
import zipfile

import pytest

from cps import ub
from cps.reading_job import service_base as base_svc
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


class _Lang:
    """真模型 Languages 行（cps/db.py:323，列名是 **lang_code**，db.py:327）。"""

    def __init__(self, lang_code):
        self.lang_code = lang_code


class _Comment:
    """真模型 Comments 行（cps/db.py:218：book.comments 是关系列表，正文在 .text）。"""

    def __init__(self, text):
        self.text = text


class _Book:
    """镜像本仓真实 `Books` 模型形状——**没有 language 标量列**，comments 也不是字符串。

    Why 逐字镜像：R169 生产崩溃（AttributeError: 'Books' object has no attribute
    'language'）之所以 21 例单测全绿，正是因为旧夹具替模型编了一个 `language = "eng"`，
    把真模型根本不存在的属性喂给了被测代码；评审复查又发现同型的 `comments="<p>…"`
    字符串假形状（真代码 re.sub 收到列表会 TypeError 并被吞成 summary 恒空）。
    夹具越像真模型，这类洞才越藏不住。
    """
    id = 1
    title = "Test Book"
    languages = [_Lang("eng")]
    comments = [_Comment("<p>A girl who loves books.</p>")]
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

    # B6 之后 `_book_file` 归一到 JobServiceBase：桩要打在骨架模块的符号上
    monkeypatch.setattr(base_svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(base_svc, "config", _Config)
    monkeypatch.setattr(svc, "current_user", _User)
    monkeypatch.setattr(svc.time, "sleep", lambda s: None)

    calls = []

    def proxy(path, payload, timeout, label, binary=False, method="POST", **kwargs):
        calls.append({"path": path, "payload": payload, "timeout": timeout, "binary": binary})
        # 真实 _moonwell_proxy 的返回形态：三元组 (body, status, headers)——R237 前
        # 桩只回二元组，service 的二元解包在单测里永远通过、一到生产就炸。
        return '{"voice":"Mia","style":"轻快清晰","reason":"儿童文学"}', 200, {}

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


def test_synth_worker_never_uses_request_session(env, monkeypatch):
    """生产事故回归：后台 worker 不得复用 ub.session。

    Why：生产 init_db 把普通 Session 实例赋给 ub.session；请求线程关闭事务后，
    worker 再查询就会抛 ``ResourceClosedError: This transaction is closed``，
    批次永久停在 RUNNING。这里把全局 session 换成任何访问都会报错的哨兵，
    worker 仍必须用独立线程会话把批次跑到 COMPLETED。
    """
    service = svc.WholeBookTtsService(env.proxy)
    monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: None)
    job_id = service.start(1, "EPUB")["jobId"]

    class _ClosedRequestSession:
        def __getattr__(self, name):
            raise AssertionError("worker touched request-scoped ub.session: %s" % name)

    monkeypatch.setattr(svc.ub, "session", _ClosedRequestSession(), raising=False)

    service._synth_worker(job_id)

    factory = ub.get_new_session_instance()
    session = factory()
    try:
        job = session.query(ReadingTtsJob).get(job_id)
        items = (session.query(ReadingTtsJobItem)
                 .filter(ReadingTtsJobItem.job_id == job_id).all())
    finally:
        factory.remove()
    assert job.status == "COMPLETED"
    assert job.done_count == 2
    assert {item.status for item in items} == {"DONE"}


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
        return '{"ok":true}', 200, {}

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
            return "boom", 500, {}
        return '{"ok":true}', 200, {}

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


# ---------- R169：元数据崩溃不得吃掉批次 + 线程存活自愈 ----------


def _book_meta_of(env):
    service = svc.WholeBookTtsService(env.proxy)
    return service._book_meta(_Book(), [("C1", "Para one."), ("C1", "Para two.")])


def test_book_meta_reads_languages_relation_not_scalar(env):
    """真模型只有 languages 关系：取到语言，且不因缺列抛错（R169 根因回归）。"""
    meta = _book_meta_of(env)

    assert meta["language"] == "eng"
    assert meta["bookName"] == "Test Book"


def test_book_meta_survives_book_without_languages_attr(env):
    """连 languages/comments 关系都取不到时逐项退化成空串——选角少一项输入，不是批次级失败。"""
    class _Bare:
        id, title = 2, "No Relations"

    service = svc.WholeBookTtsService(env.proxy)
    meta = service._book_meta(_Bare(), [("C1", "Para one.")])

    assert meta["language"] == ""
    assert meta["summary"] == ""
    assert meta["bookName"] == "No Relations"


def test_book_meta_reads_summary_from_comments_relation(env):
    """summary 必须真取到正文：旧实现把关系列表喂给 re.sub，异常被吞 ⇒ 生产恒空。"""
    meta = _book_meta_of(env)

    assert meta["summary"] == "A girl who loves books."


def test_spawn_worker_is_atomic_and_never_double_spawns(env, monkeypatch):
    """判活与登记同锁原子化：并发两次 spawn 只能起一条线程。

    Why 单独钉这条：Tornado 把视图跑在真线程池里，两个「点重试 / 点整本朗读」可能同时
    通过 `_needs_worker` 预检；`_synth_worker` 取段无 CAS，双线程 ⇒ 同段双合成、双扣字符。
    """
    service = svc.WholeBookTtsService(env.proxy)
    started = []

    class _FakeThread:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def start(self):
            started.append(self.kwargs["args"][0])

    # B6 之后线程在骨架里创建：直接桩 stdlib 的 Thread（模块单例，两处调用同一份）
    monkeypatch.setattr(threading, "Thread", _FakeThread)

    first = service._spawn_synth_worker("job-1")
    second = service._spawn_synth_worker("job-1")

    assert first is True and second is False
    assert started == ["job-1"]


def test_retry_on_cancelled_job_does_not_revive(env, monkeypatch):
    """cancel 是用户的显式停止意图：retry 不得把它拨回 RUNNING（旧实现有 FAILED 就复活）。"""
    service = svc.WholeBookTtsService(env.proxy)
    spawned = []
    monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: spawned.append(job_id))
    job_id = service.start(1, "EPUB")["jobId"]
    # 制造 FAILED + CANCELLED 的组合（旧代码正是这条路会复活批次）
    item = (ub.session.query(ReadingTtsJobItem)
            .filter(ReadingTtsJobItem.job_id == job_id).first())
    item.status = "FAILED"
    service.cancel(job_id)
    spawned.clear()

    result = service.retry(job_id)

    assert spawned == []
    assert result["status"] == "CANCELLED"


def test_start_still_spawns_worker_when_preselect_crashes(env, monkeypatch):
    """事故形态复现：_book_meta 抛异常也必须把 daemon 起起来。

    Why 这条是主闸门：R169 的台账之所以停在 RUNNING 0/307，就是异常落在
    「job 与全部 item 已 commit」与「_spawn_synth_worker」之间。
    """
    service = _make_service(env, sync_worker=False)
    spawned = []
    monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: spawned.append(job_id))
    monkeypatch.setattr(service, "_book_meta", lambda book, paragraphs: (_ for _ in ()).throw(
        AttributeError("'Books' object has no attribute 'language'")))

    result = service.start(1, "EPUB")

    assert spawned == [result["jobId"]]
    assert result["status"] == "RUNNING"
    assert result["total"] == 2 and result["done"] == 0
    assert result["voice"] is None  # 选角被跳过，退化成 provider 默认音色


def test_first_call_preselect_uses_this_request_proxy(env):
    """容器启动后的第一次点击：构造期 proxy 是 None，选角仍要用本次请求注入的代理。"""
    service = svc.WholeBookTtsService(None)  # web.py 的模块级单例就是这个形状
    env.monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: None)

    result = service.start(1, "EPUB", proxy=env.proxy)

    assert env.calls[0]["path"] == svc.BOOK_VOICE_SELECT_PATH
    assert result["voice"] == "Mia"


def test_retry_spawns_when_no_live_worker_and_pending(env, monkeypatch):
    """R169 现场：0 FAILED、全是 PENDING、线程从未起成——重试必须补线程。"""
    service = svc.WholeBookTtsService(env.proxy)
    spawned = []
    monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: spawned.append(job_id))
    job_id = service.start(1, "EPUB")["jobId"]
    spawned.clear()

    result = service.retry(job_id)

    assert spawned == [job_id]
    assert result["status"] == "RUNNING"


def test_retry_does_not_double_spawn_while_worker_is_live(env, monkeypatch):
    """活线程在跑时不得再起一条：_synth_worker 先查后写无 CAS，会抢同一段双合成双扣费。"""
    service = svc.WholeBookTtsService(env.proxy)
    spawned = []
    monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: spawned.append(job_id))
    job_id = service.start(1, "EPUB")["jobId"]
    spawned.clear()

    with service._workers_lock:
        service._live_workers.add(job_id)
    result = service.retry(job_id)

    assert spawned == []
    assert result["status"] == "RUNNING"


def test_progress_can_resume_only_when_pending_and_no_live_worker(env, monkeypatch):
    """R237 验收缺陷：页面要能区分「真在跑」与「容器重启后没人跑」。

    Why 由服务端给 canResume：DB 的 RUNNING 只能说明批次没终止，不能说明当前
    进程还有 daemon 线程。反向变异：去掉 _needs_worker 判定后，活线程在跑时
    也会显示「继续」。
    """
    service = _make_service(env, sync_worker=False)
    monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: None)
    result = service.start(1, "EPUB")
    job_id = result["jobId"]

    assert result["status"] == "RUNNING"
    assert result["canResume"] is True

    with service._workers_lock:
        service._live_workers.add(job_id)
    assert service.get_progress(job_id)["canResume"] is False

    with service._workers_lock:
        service._live_workers.discard(job_id)
    job = ub.session.query(ReadingTtsJob).get(job_id)
    job.status = "CANCELLED"
    ub.session.commit()
    assert service.get_progress(job_id)["canResume"] is False

    for item in _items(job_id):
        item.status = "DONE"
    job.status = "COMPLETED"
    ub.session.commit()
    assert service.get_progress(job_id)["canResume"] is False


def test_start_resumes_dead_batch_in_place_instead_of_new_ledger(env, monkeypatch):
    """再次点按钮：原地续跑旧台账，不换新的（断点台账不许因自愈而作废）。"""
    service = svc.WholeBookTtsService(env.proxy)
    spawned = []
    monkeypatch.setattr(service, "_spawn_synth_worker", lambda job_id: spawned.append(job_id))
    first = service.start(1, "EPUB")
    spawned.clear()
    jobs_before = ub.session.query(ReadingTtsJob).count()

    second = service.start(1, "EPUB")

    assert second["jobId"] == first["jobId"]
    assert spawned == [first["jobId"]]
    # 台账增量必须为 0（共享库夹具里绝对条数会含历史用例，只有增量可信）
    assert ub.session.query(ReadingTtsJob).count() == jobs_before


# ---- R237 守卫：moonwell proxy 返回契约恒为三元组 ------------------------------
def test_moonwell_proxy_contract_is_three_tuple():
    """reading_tts 全链路按 (body, status, headers) 三元组解包。

    Why 钉契约：R237 前事故＝service 按二元组解包 + 单测桩也回二元组——
    单测永远绿、生产每段必炸（每段重试两次后 FAILED，双倍合成白烧）。
    失败分支 _error_tuple 与成功分支 return 任何一边改形态，这里先报红。
    反向变异：把 proxy 成功分支改成二元组返回 → 本条报红。
    """
    import inspect
    from cps.moonwell.client import MoonWellClient, _error_tuple

    body, status, headers = _error_tuple(503, "x")
    assert status == 503 and isinstance(body, str) and isinstance(headers, dict)

    src = inspect.getsource(MoonWellClient.proxy)
    assert "return (body, response.status_code," in src, \
        "MoonWellClient.proxy 成功分支不再是三元组——reading_tts 解包会先炸"

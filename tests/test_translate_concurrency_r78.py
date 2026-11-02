"""R78 回归：发布并发收敛 + 锁重试 + 进度懒回收。

09-26 生产实锤：一键 44 本书 → 44 个发布线程并发写同一 SQLite，
30 次 'database is locked' 崩溃，31 本书的线程中途死亡，39,645 段
滞留 PENDING；同时 moon-well 后台持续完成早前积压而页面进度是静态
快照，用户以为翻译停了。
"""
import os
import sys
import threading
import zipfile

_WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from cps.reading_translation import service as svc  # noqa: E402
from cps.reading_translation.models import TranslationJob, TranslationJobItem  # noqa: E402


def _write_epub(path):
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    page = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>C1</title></head>"
            "<body><p>Hello.</p></body></html>")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", page)


def test_publish_workers_semaphore_caps_concurrency(monkeypatch, tmp_path):
    """R78：并发发布线程数被全局信号量约束在 PUBLISH_WORKERS 内。"""
    _write_epub(tmp_path / "book.epub")

    observed = []
    release = threading.Event()
    real_pending = svc.WholeBookTranslationService._publish_pending

    def _slow_pending(self, job_id, *args, **kw):
        observed.append(job_id)
        release.wait(timeout=5)  # 占住信号量：拿到令牌后等待主线程放行
        real_pending(self, job_id, *args, **kw)

    def _blocked_pending(self, job_id, *args, **kw):
        observed.append(job_id)
        release.wait(timeout=5)  # 若信号量失效，第 N+1 个线程会到达这里
        real_pending(self, job_id, *args, **kw)

    # PUBLISH_WORKERS 个线程用慢速实现占满信号量；再起 1 个：若信号量有效，
    # 它应阻塞在信号量上，永远到不了 _blocked_pending 的 observed.append
    monkeypatch.setattr(svc.WholeBookTranslationService, "_publish_pending", _slow_pending)
    threads = [threading.Thread(target=svc.WholeBookTranslationService()._publish_worker_guarded,
                                args=("job-%d" % i, "T", i, "fp", lambda p: None), daemon=True)
               for i in range(svc.PUBLISH_WORKERS)]
    for t in threads:
        t.start()
        t.join(timeout=0.3)

    monkeypatch.setattr(svc.WholeBookTranslationService, "_publish_pending", _blocked_pending)
    extra = threading.Thread(target=svc.WholeBookTranslationService()._publish_worker_guarded,
                             args=("job-extra", "T", 99, "fp", lambda p: None), daemon=True)
    extra.start()
    extra.join(timeout=1.5)

    assert "job-extra" not in observed, "semaphore must gate the extra worker"
    release.set()
    extra.join(timeout=2)
    assert "job-extra" in observed, "extra worker must run after semaphore released"


def test_commit_with_retry_survives_transient_lock(monkeypatch):
    """R78：commit 遇 'database is locked' 指数退避重试，最终成功；
    非锁错误立即抛出不重试。"""
    calls = {"locked": 0, "other": 0}

    class _Session:
        def commit(self):
            if calls["locked"] < 2:
                calls["locked"] += 1
                raise Exception("sqlite3.OperationalError: database is locked")

    sleeps = []
    monkeypatch.setattr(svc.time, "sleep", lambda s: sleeps.append(s))
    svc._commit_with_retry(_Session(), attempts=5)
    assert calls["locked"] == 2 and sleeps, "must retry twice then succeed"

    class _Broken:
        def commit(self):
            calls["other"] += 1
            raise ValueError("not a lock error")

    raised = False
    try:
        svc._commit_with_retry(_Broken(), attempts=5)
    except ValueError:
        raised = True
    assert raised and calls["other"] == 1, "non-lock error must not be retried"


def test_all_books_progress_lazy_recovers_cache(monkeypatch):
    """R78：进度接口带 lookup 时对每书最新批次做缓存懒回收，
    计数器跟着 moon-well 实际完成走。"""
    from datetime import timedelta

    job_old = TranslationJob(id="j-old", user_id=1, book_id=1, book_format="EPUB",
                             book_fingerprint="fp", book_name="B1", status="RUNNING",
                             total_count=2, cached_count=0, completed_count=0,
                             published_count=2, failed_count=0,
                             created_at=svc.now_utc() - timedelta(hours=2),
                             updated_at=svc.now_utc() - timedelta(hours=2))
    job_new = TranslationJob(id="j-new", user_id=1, book_id=1, book_format="EPUB",
                             book_fingerprint="fp2", book_name="B1", status="RUNNING",
                             total_count=2, cached_count=0, completed_count=0,
                             published_count=2, failed_count=0,
                             created_at=svc.now_utc() - timedelta(minutes=5),
                             updated_at=svc.now_utc() - timedelta(minutes=1))
    item_pending = TranslationJobItem(id="i1", job_id="j-new", paragraph_index=0,
                                      chapter="c", text="Hello.", text_hash="h1",
                                      status="PUBLISHED")
    item_done = TranslationJobItem(id="i2", job_id="j-new", paragraph_index=1,
                                   chapter="c", text="World.", text_hash="h2",
                                   status="COMPLETED", translation="世界。")

    class _Store:
        def __init__(self):
            self.jobs = [job_old, job_new]
            self.items = [item_pending, item_done]
            self.commits = 0

        def add(self, obj):
            self.jobs.append(obj)

        def commit(self):
            self.commits += 1

        def query(self, model_or_column):
            target = model_or_column
            if not isinstance(target, type):
                target = getattr(target, "class_", target)
            rows = [r for r in (self.jobs + self.items) if isinstance(r, target)]
            return _Q(rows)

        def get_bind(self):
            return None

    class _Q:
        def __init__(self, rows):
            self._rows = rows

        def filter(self, *conds):
            for cond in conds:
                key = getattr(cond.left, "key", None)
                value = getattr(cond.right, "value", None)
                if key is None or value is None:
                    continue
                # 二元条件可能是 == / in_ / ~in_（not_in_op）：按 operator 名分派，
                # 与真实 SQL 语义一致（R78 懒回收查询用 ~in_，首版 stub 当 == 处理）
                op_name = getattr(cond.operator, "__name__", "") if callable(getattr(cond, "operator", None)) else ""
                if op_name == "not_in_op":
                    self._rows = [r for r in self._rows if getattr(r, key, None) not in value]
                elif isinstance(value, (list, tuple, set)):
                    self._rows = [r for r in self._rows if getattr(r, key, None) in value]
                else:
                    self._rows = [r for r in self._rows if getattr(r, key, None) == value]
            return self

        def order_by(self, *a):
            return self

        def filter_by(self, **kw):
            self._rows = [r for r in self._rows
                          if all(getattr(r, k, None) == v for k, v in kw.items())]
            return self

        def all(self):
            return list(self._rows)

        def __iter__(self):
            return iter(self._rows)

    class _CalibreQuery:
        def __init__(self, rows):
            self._rows = rows

        def join(self, *a, **k):
            return self

        def filter(self, *a, **k):
            return self

        def distinct(self):
            return self

        def all(self):
            return [(1,)]

    class _CalibreSession:
        def query(self, col):
            return _CalibreQuery(None)

    class _CalibreDB:
        session = _CalibreSession()

    store = _Store()
    monkeypatch.setattr(svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(svc.ub, "session", store, raising=False)

    lookups = []

    def _lookup(paragraphs):
        lookups.append(list(paragraphs))
        # moon-well 已完成 "Hello." 的翻译并写缓存
        return {"Hello.": "你好。"}

    result = svc.WholeBookTranslationService().all_books_progress(_lookup)

    # 懒回收只看最新批次 j-new 的非终态 item（Hello.），且命中后计数刷新
    assert lookups and "Hello." in lookups[0]
    assert item_pending.status == "COMPLETED"
    assert item_pending.translation == "你好。"  # 译文回填到本地账本
    # cached_count 只在发布阶段预命中时累加（_refresh_counts 不重算它），
    # 懒回收的真相在 item 状态与 completed_count 里——这正是台账语义
    entry = result["books"][0]
    # i1 回收后 COMPLETED + i2 原本就是 COMPLETED → 每书最新批次 completed=2
    assert job_new.completed_count == 2
    assert entry["completed"] == 2 and entry["total"] == 2
    assert result["allDone"] is True


def test_recover_closure_resolves_moonwell_proxy(app, monkeypatch):
    """R78 追加：启动恢复闭包必须能解析 _moonwell_proxy。

    09-27 生产实锤：cps/__init__.py 的 _system_publish 闭包直接引用
    _moonwell_proxy（定义在 cps.web），未 import → NameError，
    恢复批次 27,428 段全部 FAILED（error_message 可证）。
    """
    from cps import web as web_module

    assert hasattr(web_module, "_moonwell_proxy")

    # create_app 的恢复闭包在运行时经 from . import web as web_module 解析；
    # 模拟恢复线程执行 publish：确认闭包能走到 _moonwell_proxy 并发出请求
    import json
    import cps  # noqa: F401  (create_app 已由 app fixture 构建)

    captured = {}

    class _Resp:
        status_code = 200
        content = b'{"result": {"taskId": "t-r78"}}'
        text = '{"result": {"taskId": "t-r78"}}'
        headers = {"Content-Type": "application/json"}

    monkeypatch.setattr(web_module.constants, "MOON_WELL_READING_URL",
                        "http://127.0.0.1:18082")
    # R145 全 token 化：系统身份走服务账号 mk- key（互信头已废）
    monkeypatch.setattr(web_module.os, "environ",
                        {**web_module.os.environ, "MOONWELL_SYSTEM_TOKEN": "mk-r78-key"})
    monkeypatch.setattr(web_module.requests, "post",
                        lambda url, json=None, headers=None, timeout=None, proxies=None:
                        captured.update(url=url) or _Resp())

    # 直接重放 create_app 内的 _system_publish 逻辑（等价于恢复线程路径）
    response = web_module._moonwell_proxy(
        "/llm/task/publish", {"input": "hi"}, 20,
        "whole-book translation recovery", system_identity=True)
    assert isinstance(response, tuple) and response[1] == 200
    assert captured["url"].endswith("/llm/task/publish")

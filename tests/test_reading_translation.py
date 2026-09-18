import zipfile

from cps.reading_translation.parser import extract_epub_paragraphs, split_long_text, text_hash


def _write_epub(path):
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
      <item id='two' href='two.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/><itemref idref='two'/></spine></package>"""
    one = "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Chapter One</title></head><body><div><p> First   paragraph. </p><p>Second.</p></div></body></html>"
    two = "<html xmlns='http://www.w3.org/1999/xhtml'><body><h1>Chapter Two</h1><p>Third.</p><script>ignore me</script></body></html>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", one)
        archive.writestr("OPS/two.xhtml", two)


def test_extracts_in_spine_order_and_skips_nested_or_script_nodes(tmp_path):
    path = tmp_path / "book.epub"
    _write_epub(path)

    assert extract_epub_paragraphs(path) == [
        ("Chapter One", "First paragraph."),
        ("Chapter One", "Second."),
        ("Chapter Two", "Third."),
    ]


def test_long_paragraph_prefers_sentence_boundaries_and_hash_is_trimmed():
    text = "A sentence. " * 300
    chunks = split_long_text(text)

    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 2000 for chunk in chunks)
    assert text_hash("  hello  ") == text_hash("hello")


def test_publish_payload_carries_prompt_template_and_progress_reports_pending(tmp_path, monkeypatch):
    """R46 整本翻译修复：发布任务必须带 promptTemplate（否则 moon-well 执行器
    拿裸英文去调 LLM，只会复述原文而非翻译）；progress 必须暴露 pendingCount。"""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cps.reading_translation import service as svc
    from cps.reading_translation.models import TranslationJob, TranslationJobItem

    path = tmp_path / "book.epub"
    _write_epub(path)

    # -- 不触发真实 DB：桩掉 _ensure_tables / calibre_db / current_user ------
    monkeypatch.setattr(svc.WholeBookTranslationService, "_ensure_tables", lambda self: None)
    monkeypatch.setattr(svc, "extract_epub_paragraphs", lambda p: [("Ch.1", "Hello paragraph.")])

    class _Book:
        title = "Test Book"

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

    class _BookPath(__import__("types").SimpleNamespace):
        pass

    monkeypatch.setattr(svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(svc, "config", _Config)

    class _User:
        id = 1

    monkeypatch.setattr(svc, "current_user", _User, raising=False)

    # 直接为 book 补齐 .path，_book_file 真正解析文件路径（已存在的 epub）
    real_book = _Book()
    real_book.path = "."
    monkeypatch.setattr(_CalibreDB, "get_filtered_book", staticmethod(lambda book_id: real_book))
    # 让 data.name + 扩展名正好命中刚才写入的 book.epub
    book, file_path = svc.WholeBookTranslationService()._book_file(1, "EPUB")

    published = []

    def _publish(payload):
        published.append(payload)
        return {"result": {"taskId": 42}}

    # Column default 只在真实 flush 时生效；stub session 下手动补默认值
    import types

    class _Session:
        def __init__(self):
            self.adds = []
            self.committed = 0

        def add(self, obj):
            self.adds.append(obj)
            # 模拟 flush 落 Column 默认值（default 只在真实 flush 生效）
            if isinstance(obj, TranslationJob):
                for field, default in (("total_count", 0), ("cached_count", 0),
                                       ("published_count", 0), ("completed_count", 0),
                                       ("failed_count", 0)):
                    if getattr(obj, field) is None:
                        setattr(obj, field, default)
            if isinstance(obj, TranslationJobItem) and obj.attempt_count is None:
                obj.attempt_count = 0

        def commit(self):
            self.committed += 1

        def query(self, model, *a, **k):
            state = self

            class _Q:
                def filter(self, *a, **k):
                    return self

                def order_by(self, *a, **k):
                    class _First:
                        def first(self):
                            return None
                    return _First()

                def filter_by(self, **kw):
                    self._kw = kw
                    return self

                def one(self):
                    # 后台发布线程：按模型区分——job 查询返回匹配的 job，
                    # item 查询返回该 job 的全部 item
                    jobs = [o for o in state.adds if isinstance(o, TranslationJob)]
                    job_id = getattr(self, "_kw", {}).get("id")
                    if job_id:
                        for job in jobs:
                            if job.id == job_id:
                                return job
                    return jobs[0] if jobs else None

                def all(self):
                    job_id = getattr(self, "_kw", {}).get("job_id")
                    if job_id:
                        return [o for o in state.adds
                                if isinstance(o, TranslationJobItem) and o.job_id == job_id]
                    return [o for o in state.adds if isinstance(o, TranslationJobItem)]

                def one_or_none(self):
                    return None

                def all(self):
                    job_id = getattr(self, "_kw", {}).get("job_id")
                    if job_id:
                        return [o for o in state.adds
                                if isinstance(o, TranslationJobItem) and o.job_id == job_id]
                    return []

                def __iter__(self):
                    return iter([])
            return _Q()

    # start() 现在把发布交给后台线程：测试里把 Thread 换成同步执行，便于断言
    class _SyncThread:
        def __init__(self, target=None, args=None, name=None, daemon=None):
            self._target = target
            self._args = args or ()

        def start(self):
            self._target(*self._args)

    monkeypatch.setattr(svc.threading, "Thread", _SyncThread)

    class _ScopedSession:
        """模拟 scoped_session：方法转发到共享 inner，调用返回同一会话，remove() 清理。"""
        def __init__(self, inner):
            self._inner = inner

        def __call__(self):
            return self._inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def remove(self):
            pass

    inner = _Session()
    monkeypatch.setattr(svc.ub, "session", _ScopedSession(inner), raising=False)
    # R51：后台线程改走 get_new_session_instance()（生产 ub.session 是普通
    # Session 实例、不可调用）；测试同样返回共享假会话，便于断言
    monkeypatch.setattr(svc.ub, "get_new_session_instance", lambda: _ScopedSession(inner))

    result = svc.WholeBookTranslationService().start(1, "EPUB", False, _publish, {})

    assert len(published) == 1
    # 核心断言 1：发布 payload 必须带翻译模板键
    assert published[0]["promptTemplate"] == "reading-paragraph-translate-plain"
    assert published[0]["parameters"]["bookName"] == "Test Book"
    # 核心断言 2：progress 返回 pendingCount（前端区分未完成与失败）
    assert "pendingCount" in result


def test_extract_is_deterministic_and_counts_all_paragraphs(tmp_path):
    """R47 回归：lxml 元素代理被 GC 后 id() 复用，曾导致同一本书三次抽取
    分别得到 759/78/78 段（生产 3177 个 <p> 只剩 128 段）。修复后必须：
    ① 抽取结果确定（多次运行一致）；② 所有顶层块级节点都被保留。"""
    body = "".join(f"<p>Paragraph {i} content.</p>" for i in range(300))
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    # h1 优先作为章节名（Calibre 转换书的 <title> 恒为书名，不能作为章节）
    page = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Book Title</title></head>"
            f"<body><h1>Chapter One</h1>{body}</body></html>")
    path = tmp_path / "big.epub"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", page)

    runs = [extract_epub_paragraphs(path) for _ in range(3)]
    counts = {len(r) for r in runs}
    assert len(counts) == 1, f"抽取结果不确定: {counts}"
    assert counts == {300}
    bad = sorted({chapter for chapter, _ in runs[0]})[:3]
    assert bad == ["Chapter One"], f"unexpected chapters: {bad}"
    assert runs[0][0][1] == "Paragraph 0 content."


def test_extract_skips_nested_blocks_and_empty_paragraphs(tmp_path):
    """blockquote 内的 p 不重复处理；全角空格空段不产出；script 内容不出现。"""
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    page = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>T</title></head><body>"
            "<blockquote><p>quoted line.</p></blockquote>"
            "<p>\u3000</p>"
            "<p>after empty.</p>"
            "<script>var x = 'nope';</script>"
            "</body></html>")
    path = tmp_path / "nested.epub"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", page)

    paragraphs = extract_epub_paragraphs(path)
    texts = [text for _, text in paragraphs]
    assert texts == ["quoted line.", "after empty."]


def test_publish_survives_single_segment_failure(tmp_path, monkeypatch):
    """R48 后台发布线程：单段发布失败只标 FAILED，不中断整批发布。"""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cps.reading_translation import service as svc
    from cps.reading_translation.models import TranslationJob, TranslationJobItem

    path = tmp_path / "book.epub"
    _write_epub(path)

    monkeypatch.setattr(svc.WholeBookTranslationService, "_ensure_tables", lambda self: None)
    monkeypatch.setattr(svc, "extract_epub_paragraphs",
                        lambda p: [("Ch.1", "first."), ("Ch.1", "second."), ("Ch.1", "third.")])

    class _Book:
        title = "Test Book"
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

    class _Session:
        def __init__(self):
            self.adds = []

        def add(self, obj):
            self.adds.append(obj)
            if isinstance(obj, TranslationJob):
                for f in ("total_count", "cached_count", "published_count",
                          "completed_count", "failed_count"):
                    if getattr(obj, f) is None:
                        setattr(obj, f, 0)
            if isinstance(obj, TranslationJobItem) and obj.attempt_count is None:
                obj.attempt_count = 0

        def commit(self):
            pass

        def query(self, model, *a, **k):
            state = self

            class _Q:
                def __init__(self):
                    self._kw = {}

                def filter(self, *a, **k):
                    return self

                def order_by(self, *a, **k):
                    class _First:
                        def first(self):
                            return None
                    return _First()

                def filter_by(self, **kw):
                    self._kw.update(kw)
                    return self

                def one(self):
                    jobs = [o for o in state.adds if isinstance(o, TranslationJob)]
                    job_id = self._kw.get("id")
                    for job in jobs:
                        if job.id == job_id:
                            return job
                    return jobs[0]

                def one_or_none(self):
                    return None

                def all(self):
                    job_id = self._kw.get("job_id")
                    if job_id:
                        return [o for o in state.adds
                                if isinstance(o, TranslationJobItem) and o.job_id == job_id]
                    return []

                def __iter__(self):
                    return iter([])
            return _Q()

    class _SyncThread:
        def __init__(self, target=None, args=None, name=None, daemon=None):
            self._target, self._args = target, args or ()

        def start(self):
            self._target(*self._args)

    class _ScopedSession:
        def __init__(self, inner):
            self._inner = inner

        def __call__(self):
            return self._inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def remove(self):
            pass

    monkeypatch.setattr(svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(svc, "config", _Config)
    monkeypatch.setattr(svc, "current_user", _User, raising=False)
    monkeypatch.setattr(svc.threading, "Thread", _SyncThread)
    inner = _Session()
    monkeypatch.setattr(svc.ub, "session", _ScopedSession(inner), raising=False)
    monkeypatch.setattr(svc.ub, "get_new_session_instance", lambda: _ScopedSession(inner))

    # 中间那次发布抛异常，前后两次成功
    published = []

    def _publish(payload):
        published.append(payload["parameters"]["paragraphIndex"])
        if len(published) == 2:
            raise ValueError("simulated publish failure")
        return {"result": {"taskId": 7}}

    result = svc.WholeBookTranslationService().start(1, "EPUB", False, _publish, {})

    assert sorted(published) == [0, 1, 2]          # 3 段全部尝试发布，失败不中断
    assert result["failedCount"] == 1              # 第 2 段失败
    assert result["publishedCount"] == 2           # 第 1、3 段发布成功


def test_publish_thread_uses_own_session_when_ub_session_is_plain_instance(monkeypatch, caplog):
    """R51 回归：生产 init_db 里 `session = Session()`，ub.session 是普通 Session
    实例（不可调用）。旧实现在线程里按 scoped_session 语义调 `ub.session()`，
    抛 'Session' object is not callable，发布线程启动即崩溃（异常被 except 吞掉
    只落日志，段落一个都没发布）。修复后线程必须经 get_new_session_instance()
    自建会话，与全局 ub.session 完全解耦。同时断言发布完成摘要日志——受理/完成
    观测点是「点击无反应」类问题的唯一判据。"""
    import logging
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    from cps import ub as ub_module
    from cps.reading_translation import service as svc
    from cps.reading_translation.models import TranslationJob, TranslationJobItem

    engine = create_engine("sqlite:///:memory:")
    ub_module.Base.metadata.create_all(
        engine, tables=[TranslationJob.__table__, TranslationJobItem.__table__])

    # 生产形态：全局 ub.session 是 sessionmaker 产出的普通 Session 实例
    plain = sessionmaker(bind=engine)()
    factory = scoped_session(sessionmaker(bind=engine))
    monkeypatch.setattr(ub_module, "session", plain)
    monkeypatch.setattr(ub_module, "get_new_session_instance", lambda: factory)

    job = TranslationJob(id="job-r51", user_id=1, book_id=1, book_format="EPUB",
                         book_fingerprint="fp", book_name="T", status="RUNNING", total_count=1)
    item = TranslationJobItem(id="item-r51", job_id="job-r51", paragraph_index=0,
                              chapter="c", text="Hello world.", text_hash="h", status="PENDING")
    plain.add_all([job, item])
    plain.commit()

    published = []

    def _publish(payload):
        published.append(payload)
        return {"result": {"taskId": "task-r51"}}

    with caplog.at_level(logging.INFO, logger="cps.reading_translation.service"):
        svc.WholeBookTranslationService()._publish_pending(
            "job-r51", "T", 1, "fp", _publish, lookup=None)

    # 旧代码在线程内调 ub.session() 抛 TypeError 后静默退出：published 必为空。
    assert len(published) == 1
    assert published[0]["promptTemplate"] == "reading-paragraph-translate-plain"
    # 观测点：发布完成必须留摘要日志（「点击无日志」问题的判定依据）
    assert "publish finished" in caplog.text
    assert "job-r51" in caplog.text
    with factory() as verify:
        row = verify.query(TranslationJobItem).filter_by(id="item-r51").one()
        assert row.task_id == "task-r51"
        assert row.status == "PUBLISHED"
        job_row = verify.query(TranslationJob).filter_by(id="job-r51").one()
        assert job_row.published_count == 1


def test_moonwell_proxy_snapshot_identity_works_without_flask_context(app, monkeypatch):
    """R51 回归：整本翻译发布在 daemon 线程执行，线程内没有 Flask 请求上下文。
    _moonwell_proxy 必须支持请求线程定格的身份快照（identity_headers +
    bearer_token）完成调用：任何对 current_user / flask_session 的触碰在本测试
    环境下都会抛 RuntimeError，正好构成断言。"""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 依赖 app fixture：cps.web 的导入链需要 cli_param 已初始化（gdrive 路径）
    from cps import web as web_module

    def _boom(*args, **kwargs):
        raise AssertionError("background thread must not resolve identity lazily")

    monkeypatch.setattr(web_module, "_moonwell_identity_headers", _boom)
    monkeypatch.setattr(web_module.constants, "MOON_WELL_READING_URL",
                        "http://127.0.0.1:18082")

    class _Resp:
        status_code = 200
        content = b'{"result": {"taskId": "t-snap"}}'
        text = '{"result": {"taskId": "t-snap"}}'
        headers = {"Content-Type": "application/json"}

    captured = {}

    def _post(url, json=None, headers=None, timeout=None, proxies=None):
        captured.update(url=url, json=json, headers=headers)
        return _Resp()

    monkeypatch.setattr(web_module.requests, "post", _post)

    body, status, _ = web_module._moonwell_proxy(
        "/llm/task/publish", {"input": "hi"}, 20, "whole-book translation",
        identity_headers={"X-User-Subject": "sub-r51"}, bearer_token="tok-r51")

    assert status == 200
    assert "t-snap" in body
    assert captured["url"].endswith("/llm/task/publish")
    assert captured["headers"]["X-User-Subject"] == "sub-r51"
    assert captured["headers"]["authorization"] == "Bearer tok-r51"


def test_moonwell_proxy_system_identity_works_without_flask_context(app, monkeypatch):
    """R52 回归：启动恢复线程以 system_identity 调用 _moonwell_proxy，线程内
    没有 Flask 请求上下文。旧实现无条件读 flask_session.get(...) 抛
    RuntimeError: Working outside of request context，被逐段 except 捕获后
    整批段落全部 FAILED（生产 job 57b763d：4477/4477 失败、pending=0）。"""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 依赖 app fixture：cps.web 的导入链需要 cli_param 已初始化（gdrive 路径）
    from cps import web as web_module

    def _boom(*args, **kwargs):
        raise AssertionError("system identity must not resolve user context lazily")

    monkeypatch.setattr(web_module, "_moonwell_identity_headers", _boom)
    monkeypatch.setattr(web_module.constants, "MOON_WELL_READING_URL",
                        "http://127.0.0.1:18082")

    class _Resp:
        status_code = 200
        content = b'{"result": {"taskId": "t-sys"}}'
        text = '{"result": {"taskId": "t-sys"}}'
        headers = {"Content-Type": "application/json"}

    captured = {}

    def _post(url, json=None, headers=None, timeout=None, proxies=None):
        captured.update(url=url, json=json, headers=headers)
        return _Resp()

    monkeypatch.setattr(web_module.requests, "post", _post)

    body, status, _ = web_module._moonwell_proxy(
        "/llm/task/publish", {"input": "hi"}, 20, "whole-book translation recovery",
        system_identity=True)

    assert status == 200
    assert "t-sys" in body
    # 系统身份头来自环境变量默认值，且不携带任何用户 Bearer 令牌
    assert captured["headers"]["X-User-Subject"] == "magicbook-system"
    assert "authorization" not in captured["headers"]

"""R76 回归：整本翻译任务队列（批量登记 + 逐本激活）。

覆盖：enqueue 幂等（重复调用只补新增）、eng+EPUB/KEPUB 筛选、
activate 调用 start(force=True) 的状态机、已 ACTIVATED 的幂等返回、
激活失败标 ERROR。
"""
import os
import sys
import zipfile

_WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from cps.reading_translation import service as svc  # noqa: E402
from cps.reading_translation.models import TranslationJob  # noqa: E402
from cps.reading_translation.queue import TranslationQueue  # noqa: E402


def _write_epub(path):
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    page = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>C1</title></head>"
            "<body><p>Hello paragraph.</p></body></html>")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", page)


class _Store:
    """最小内存 store：模拟 add/commit/query 语义，不碰真实 DB。"""

    def __init__(self):
        self.rows = []
        self._auto = 0

    def add(self, obj):
        if isinstance(obj, TranslationQueue) and obj.id is None:
            self._auto += 1
            obj.id = self._auto
        self.rows.append(obj)

    def commit(self):
        pass

    def query(self, model):
        return _Query([r for r in self.rows if isinstance(r, model)])

    def get_bind(self):
        return None


class _Query:
    def __init__(self, rows):
        self._rows = rows

    def order_by(self, *a):
        return self

    def filter_by(self, **kw):
        return _Query([r for r in self._rows
                       if all(getattr(r, k) == v for k, v in kw.items())])

    def all(self):
        return list(self._rows)

    def one_or_none(self):
        return self._rows[0] if self._rows else None


def _patch_common(monkeypatch, tmp_path, books):
    """books: [{id, format}]。桩掉 calibre_db 查询与文件解析。"""
    _write_epub(tmp_path / "book.epub")
    monkeypatch.setattr(svc.WholeBookTranslationService, "_ensure_tables", lambda self: None)

    class _Data:
        def __init__(self, fmt):
            self.format = fmt

    class _Lang:
        def __init__(self, code):
            self.lang_code = code

    class _Book:
        def __init__(self, bid, title, fmts):
            self.id = bid
            self.title = title
            self.data = [_Data(f) for f in fmts]
            self.languages = [_Lang("eng")]
            self.path = "."

    calibre_books = [_Book(b["id"], b.get("title", "Book %s" % b["id"]), b["formats"]) for b in books]

    class _CalibreQuery:
        """模拟 join+filter+distinct 链：只实现本服务用到的语义——
        eng 语言过滤与 EPUB/KEPUB 格式过滤在桩内按数据真实性判断。"""

        def __init__(self, rows):
            self._rows = rows

        def join(self, *a, **k):
            return self

        def filter(self, *a, **k):
            # 服务层用 Languages.lang_code=='eng' + upper(Data.format) in (EPUB,KEPUB)
            # 两个条件；桩无法回放 SQLAlchemy 表达式，改为语义等价的内存过滤
            self._rows = [b for b in self._rows
                          if any(l.lang_code == "eng" for l in b.languages)
                          and any(d.format.upper() in ("EPUB", "KEPUB") for d in b.data)]
            return self

        def distinct(self):
            return self

        def all(self):
            return self._rows

    class _CalibreDB:
        session = type("_S", (), {"query": staticmethod(lambda model: _CalibreQuery(calibre_books))})()

    class _Config:
        @staticmethod
        def get_book_path():
            return str(tmp_path)

    class _User:
        id = 1

    store = _Store()
    monkeypatch.setattr(svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(svc, "config", _Config)
    monkeypatch.setattr(svc, "current_user", _User, raising=False)
    monkeypatch.setattr(svc.ub, "session", store, raising=False)
    monkeypatch.setattr(svc.WholeBookTranslationService, "_ensure_queue_table", lambda self: None)
    return store


def test_enqueue_all_is_idempotent_and_filters_formats(tmp_path, monkeypatch):
    """R76：重复 enqueue 只补新增；非 eng/非 EPUB 的书不入队。"""
    store = _patch_common(monkeypatch, tmp_path, [
        {"id": 1, "title": "English EPUB", "formats": ["EPUB"]},
        {"id": 2, "title": "English KEPUB+EPUB", "formats": ["EPUB", "KEPUB"]},
        {"id": 3, "title": "English MOBI only", "formats": ["MOBI"]},
    ])
    service = svc.WholeBookTranslationService()

    first = service.enqueue_all_english_books()
    assert first["queued"] == 2, "MOBI-only book must not be queued"
    assert [r.book_format for r in store.rows] == ["EPUB", "KEPUB"]

    second = service.enqueue_all_english_books()
    assert second["queued"] == 0 and second["skipped"] == 2, "second run must be no-op"
    assert len(store.rows) == 2


def test_activate_materializes_batch_with_force_and_records_job(tmp_path, monkeypatch):
    """R76：激活必须调 start(force=True)（物化真实批次），并回填 job_id/ACTIVATED。"""
    store = _patch_common(monkeypatch, tmp_path, [{"id": 7, "title": "Queued Book", "formats": ["EPUB"]}])
    service = svc.WholeBookTranslationService()
    service.enqueue_all_english_books()

    captured = {}

    def _fake_start(self, book_id, book_format, force, publish, lookup=None):
        captured.update(book_id=book_id, fmt=book_format, force=force)
        return {"jobId": "job-act-1", "bookId": book_id, "status": "RUNNING"}

    monkeypatch.setattr(svc.WholeBookTranslationService, "start", _fake_start)
    monkeypatch.setattr(svc.WholeBookTranslationService, "get_progress",
                        lambda self, job_id, lookup=None: {"jobId": job_id})

    result = service.activate_queued(7, lambda p: None, None)

    assert captured == {"book_id": 7, "fmt": "EPUB", "force": True}
    assert result["jobId"] == "job-act-1"
    row = store.query(TranslationQueue).filter_by(book_id=7).one_or_none()
    assert row.status == "ACTIVATED" and row.job_id == "job-act-1"


def test_activate_is_idempotent_and_errors_mark_queue_row(tmp_path, monkeypatch):
    """R76：已 ACTIVATED 再次激活直接返回进度不重建；start 失败标 ERROR。"""
    store = _patch_common(monkeypatch, tmp_path, [{"id": 8, "title": "B8", "formats": ["EPUB"]}])
    service = svc.WholeBookTranslationService()
    service.enqueue_all_english_books()

    # 预置已激活批次：幂等返回进度
    row = store.query(TranslationQueue).filter_by(book_id=8).one_or_none()
    row.status = "ACTIVATED"
    row.job_id = "job-existing"
    store.rows.append(TranslationJob(id="job-existing", user_id=1, book_id=8,
                                     book_format="EPUB", book_fingerprint="fp",
                                     book_name="B8", status="RUNNING", total_count=3))

    calls = []

    def _boom_start(self, *a, **k):
        calls.append(a)
        raise AssertionError("start must not be called for ACTIVATED row")

    monkeypatch.setattr(svc.WholeBookTranslationService, "start", _boom_start)
    monkeypatch.setattr(svc.WholeBookTranslationService, "get_progress",
                        lambda self, job_id, lookup=None: {"jobId": job_id, "reused": True})

    result = service.activate_queued(8, None, None)
    assert result["reused"] is True and not calls

    # 新书激活失败 → ERROR + message
    store.add(TranslationQueue(book_id=9, book_format="EPUB", book_name="B9", status="QUEUED"))

    def _fail_start(self, book_id, fmt, force, publish, lookup=None):
        raise ValueError("book file is unavailable")

    monkeypatch.setattr(svc.WholeBookTranslationService, "start", _fail_start)
    raised = False
    try:
        service.activate_queued(9, None, None)
    except ValueError:
        raised = True
    assert raised
    err_row = store.query(TranslationQueue).filter_by(book_id=9).one_or_none()
    assert err_row.status == "ERROR" and "book file" in err_row.message

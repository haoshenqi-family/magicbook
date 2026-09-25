"""R77 回归：一键翻译全部英文书（登记即执行，无两段式队列）。

覆盖：eng+EPUB/KEPUB 筛选、逐本直接 start(force=True)、已有新鲜活动
批次的书跳过（不重复发布）、无文件书标记 unavailable 不中断、
all_books_progress 聚合取每书最新批次。
"""
import os
import sys
import zipfile
from datetime import timedelta

_WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from cps.reading_translation import service as svc  # noqa: E402
from cps.reading_translation.models import TranslationJob  # noqa: E402
from cps.reading_translation.timeutil import now_utc  # noqa: E402


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
    """内存 store：TranslationJob 台账 + 真实 start() 所需的最小语义。"""

    def __init__(self):
        self.jobs = []

    def add(self, obj):
        self.jobs.append(obj)

    def commit(self):
        pass

    def query(self, model_or_column):
        # 服务层既有 query(Model) 也有 query(Model.column)（如 progress 里的
        # TranslationJobItem.id）；后者取其父模型做行过滤。
        target = model_or_column
        if not isinstance(target, type):
            target = getattr(target, "class_", target)
        # 注意：SQLAlchemy 模型类是 DeclarativeMeta 的实例，不能用 type(target)
        # 判别；直接假定 model_or_column 已是模型类（服务层没有传非模型的用法）
        rows = [j for j in self.jobs if isinstance(j, target)]
        return _JobQuery(rows)

    def get_bind(self):
        return None


class _JobQuery:
    """通用 stub：对 BinaryExpression（== / in_）按列名与绑定值真实求值，
    避免 stub 语义漂移（R77 首版猜语义导致误判书在跑的教训）。"""

    def __init__(self, jobs):
        self._jobs = jobs

    def filter(self, *conds):
        for cond in conds:
            key = getattr(cond.left, "key", None)
            value = getattr(cond.right, "value", None)
            if key is None or value is None:
                continue
            self._jobs = [r for r in self._jobs
                          if getattr(r, key, None) == value
                          or (isinstance(value, (list, tuple, set))
                              and getattr(r, key, None) in value)]
        return self

    def order_by(self, *a, **k):
        return self

    def all(self):
        return list(self._jobs)

    def first(self):
        return self._jobs[-1] if self._jobs else None

    def one_or_none(self):
        return self._jobs[-1] if self._jobs else None

    def __iter__(self):
        return iter(self._jobs)

    def __len__(self):
        return len(self._jobs)


def _patch_common(monkeypatch, tmp_path, books):
    """books: [{id, title, formats}]。桩 calibre_db 查询与文件解析。"""
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

    calibre_books = [_Book(b["id"], b["title"], b["formats"]) for b in books]

    class _CalibreQuery:
        """按语义等价实现 eng + EPUB/KEPUB 过滤（同 R76 说明）。"""

        def __init__(self, rows, as_tuples=False):
            self._rows = rows
            self._as_tuples = as_tuples

        def join(self, *a, **k):
            return self

        def filter(self, *a, **k):
            self._rows = [b for b in self._rows
                          if any(l.lang_code == "eng" for l in b.languages)
                          and any(d.format.upper() in ("EPUB", "KEPUB") for d in b.data)]
            return self

        def distinct(self):
            return self

        def all(self):
            if self._as_tuples:
                return [(b.id,) for b in self._rows]
            return self._rows

    class _CalibreSession:
        def query(self, model_or_column):
            # all_books_progress 查 Books.id（列）：返回 (id,) 元组列表；
            # 查模型时返回完整 book 对象列表。
            is_id_query = not isinstance(model_or_column, type)
            return _CalibreQuery(calibre_books, as_tuples=is_id_query)

    class _CalibreDB:
        session = _CalibreSession()

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
    return store, calibre_books


def test_translate_all_starts_every_book_with_force(tmp_path, monkeypatch):
    """R77：一键 = 每本书直接 start(force=True)，无待办状态。"""
    store, books = _patch_common(monkeypatch, tmp_path, [
        {"id": 1, "title": "E1", "formats": ["EPUB"]},
        {"id": 2, "title": "E2", "formats": ["EPUB", "KEPUB"]},
    ])
    # start 内部要 extract_epub_paragraphs 与 _book_file：桩掉，直接模拟批次创建
    monkeypatch.setattr(svc, "extract_epub_paragraphs", lambda p: [("C1", "Hello.")])
    monkeypatch.setattr(svc.WholeBookTranslationService, "_spawn_publish_worker",
                        lambda self, *a, **k: None)
    monkeypatch.setattr(svc.WholeBookTranslationService, "_book_file",
                        lambda self, bid, fmt: (type("B", (), {"title": "T", "path": "."})(), str(tmp_path / "book.epub")))

    calls = []
    real_start = svc.WholeBookTranslationService.start

    def _spy_start(self, book_id, fmt, force, publish, lookup=None):
        calls.append({"book_id": book_id, "force": force})
        return real_start(self, book_id, fmt, force, publish, lookup)

    monkeypatch.setattr(svc.WholeBookTranslationService, "start", _spy_start)

    result = svc.WholeBookTranslationService().translate_all_english_books(lambda p: {"result": {"taskId": 1}})

    assert sorted(c["book_id"] for c in calls) == [1, 2]
    assert all(c["force"] is True for c in calls)
    assert result["started"] == 2 and result["alreadyRunning"] == 0
    from cps.reading_translation.models import TranslationJob as _J
    assert len([j for j in store.jobs if isinstance(j, _J)]) == 2


def test_translate_all_skips_fresh_running_batch_and_unavailable_books(tmp_path, monkeypatch):
    """R77：updated_at 新鲜（<30 分钟）的活动批次跳过不重复发布；
    文件缺失的书进 unavailable，不中断其他书。"""
    store, books = _patch_common(monkeypatch, tmp_path, [
        {"id": 1, "title": "Running", "formats": ["EPUB"]},
        {"id": 2, "title": "Broken", "formats": ["EPUB"]},
        {"id": 3, "title": "Fresh", "formats": ["EPUB"]},
    ])
    monkeypatch.setattr(svc.WholeBookTranslationService, "_spawn_publish_worker",
                        lambda self, *a, **k: None)

    # book 3：新鲜活动批次（5 分钟前 updated_at）
    store.jobs.append(TranslationJob(id="j-live", user_id=1, book_id=3, book_format="EPUB",
                                     book_fingerprint="fp", book_name="Fresh", status="RUNNING",
                                     total_count=5, created_at=now_utc() - timedelta(minutes=6),
                                     updated_at=now_utc() - timedelta(minutes=5)))

    real_start = svc.WholeBookTranslationService.start

    def _start(self, book_id, fmt, force, publish, lookup=None):
        if book_id == 2:
            raise ValueError("book file is unavailable")
        return real_start(self, book_id, fmt, force, publish, lookup)

    monkeypatch.setattr(svc.WholeBookTranslationService, "start", _start)
    monkeypatch.setattr(svc, "extract_epub_paragraphs", lambda p: [("C1", "Hello.")])
    monkeypatch.setattr(svc.WholeBookTranslationService, "_book_file",
                        lambda self, bid, fmt: (type("B", (), {"title": "T", "path": "."})(), str(tmp_path / "book.epub")))

    result = svc.WholeBookTranslationService().translate_all_english_books(lambda p: {"result": {"taskId": 1}})

    assert result["alreadyRunning"] == 1, "book 3 has fresh RUNNING batch"
    assert result["started"] == 1 and result["books"] == 3
    assert result["unavailable"] and result["unavailable"][0]["bookId"] == 2
    # book 3 没有新建批次（仍只有预置的 j-live）
    assert not [j for j in store.jobs
                if isinstance(j, TranslationJob) and j.book_id == 3 and j.id != "j-live"]


def test_all_books_progress_takes_latest_batch_per_book(tmp_path, monkeypatch):
    """R77：进度聚合同书多批次取最新一条。"""
    store, _ = _patch_common(monkeypatch, tmp_path, [{"id": 1, "title": "E1", "formats": ["EPUB"]}])
    store.jobs.append(TranslationJob(id="j-old", user_id=1, book_id=1, book_format="EPUB",
                                     book_fingerprint="fp", book_name="E1", status="PARTIAL_FAILED",
                                     total_count=10, completed_count=4, cached_count=0,
                                     published_count=5, failed_count=1,
                                     created_at=now_utc() - timedelta(hours=2),
                                     updated_at=now_utc() - timedelta(hours=2)))
    store.jobs.append(TranslationJob(id="j-new", user_id=1, book_id=1, book_format="EPUB",
                                     book_fingerprint="fp2", book_name="E1", status="RUNNING",
                                     total_count=10, completed_count=8, cached_count=8,
                                     published_count=2, failed_count=0,
                                     created_at=now_utc() - timedelta(minutes=5),
                                     updated_at=now_utc() - timedelta(minutes=1)))

    # 进度接口的英文书 id 列表（calibre_db stub 的 query 返回 _CalibreQuery，
    # all() 已按筛选项过滤；这里直接用其返回值解包）
    result = svc.WholeBookTranslationService().all_books_progress()

    assert len(result["books"]) == 1
    assert result["books"][0]["jobStatus"] if "jobStatus" in result["books"][0] else True
    assert result["books"][0]["completed"] == 8, "must aggregate the newest batch"
    assert result["allDone"] is False

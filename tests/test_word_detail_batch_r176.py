"""R176：全文单词详解（magicbook 侧台账与页面，对端 moon-well R188）。

设计要点里最容易被后续改动破坏的几条，都在这里钉住：
- **预览路径没有入队能力**：preview 只拿 check 闭包，断言 warm-publish-by-words 一次都没被打；
- **进度口径＝词覆盖率**，不是任务状态（执行方是队列消费者，COMPLETED 不等于缓存里有）；
- **缩略形/连字符词不算覆盖**：它们永远不会被生成，混进分子就是假完成（moon-well 因此把
  notWordLike 从数量改成清单，本文件按清单归属到批次）；
- 门禁返回 JSON 403 而不是 abort 的 HTML（面板靠 message 文案提示）；
- 上游业务文案不被吞（灌队闸门的提示必须原样到达浏览器）；
- 模板 i18n：新页面每个 _() msgid 在 zh_Hans_CN po 有非空译文，且 .mo 已重编译（R112/R124
  同型失效）；script 内无相邻同文行（R113 并行会话合并残留）。

不经网络：calibre 书库与 moon-well 全部打桩。
"""
import json
import os
import re
from types import SimpleNamespace

import pytest

from babel.messages.pofile import read_po

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE = os.path.join(_ROOT, "cps", "templates", "word_detail_batch.html")
_DETAIL = os.path.join(_ROOT, "cps", "templates", "detail.html")
_LAYOUT = os.path.join(_ROOT, "cps", "templates", "layout.html")
_PO = os.path.join(_ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.po")

CHECK_PATH = "/vocabulary/detail/cached-check"
PUBLISH_PATH = "/vocabulary/detail/warm-publish-by-words"

# 一本「小书」的正文：6 个去重词，其中 i'm / whole-hearted 归 moon-well 判非词形。
_BODY = "excruiciating runner i'm whole-hearted about running"
# 真词集合（去掉缩略形/连字符后的待生成面）
_TARGET_WORDS = {"excruiciating", "runner", "about", "running"}
_NOT_WORD_LIKE = {"i'm", "whole-hearted"}


@pytest.fixture(autouse=True)
def _clean_ledger(app):
    """每个用例前后清空两张台账表。

    Why 必须清：ub 的 SQLite 是 session 级共享的（conftest 只清 AI 表），而本链路
    「同书活动批次复用」正好按 book_id + fingerprint 查库——上一例留下的 RUNNING 批次
    会让下一例的 start 直接走复用通道，症状是「断言 400 结果拿到 200」。
    """
    from cps import ub

    from cps.reading_word_detail.models import WordDetailJob, WordDetailJobItem
    from cps.reading_word_detail.service import WordDetailBatchService

    WordDetailBatchService()._ensure_tables()
    ub.session.query(WordDetailJobItem).delete()
    ub.session.query(WordDetailJob).delete()
    ub.session.commit()
    yield


@pytest.fixture
def stubbed_book(monkeypatch):
    """把「书」换成内存桩：测试环境没有 metadata.db（见 conftest），calibre 一律打桩。"""
    from cps.reading_word_detail import service as wd_module
    from cps.reading_word_detail.service import WordDetailBatchService

    monkeypatch.setattr(WordDetailBatchService, "_book_file",
                        lambda self, book_id, book_format: (
                            SimpleNamespace(title="Sticky Book", id=int(book_id)), "/tmp/sticky.epub"))
    monkeypatch.setattr(WordDetailBatchService, "_fingerprint",
                        staticmethod(lambda path: "fp-v1"))
    monkeypatch.setattr(wd_module, "extract_epub_paragraphs", lambda path: [("Chapter 1", _BODY)])
    return wd_module


@pytest.fixture
def fake_moonwell(monkeypatch):
    """打桩 _moonwell_proxy：按真实返回形状回 (body, status, headers) 三元组。

    Why 三元组而不是 Response：真 _moonwell_proxy 上游分支就是手拼三元组（daemon 线程
    里 jsonify 会 RuntimeError），桩若返回 Response，闭包的解包分支就测不到。
    """
    from cps import web

    calls = []
    state = {"cached": set(), "notWordLike": set(), "publish_error": None}

    def _tuple(payload, status=200):
        return (json.dumps({"success": status < 400, "message": "", "result": payload}),
                status, {"Content-Type": "application/json"})

    def fake_proxy(path, payload, timeout, label, **kwargs):
        calls.append({"path": path, "payload": payload, "timeout": timeout, "kwargs": kwargs})
        if path == CHECK_PATH:
            words = payload["words"]
            not_word_like = [w for w in words if w in state["notWordLike"]]
            cached = [w for w in words if w in state["cached"]]
            missing = [w for w in words if w not in state["cached"] and w not in state["notWordLike"]]
            return _tuple({"requested": len(words) - len(not_word_like), "cached": len(cached),
                           "missing": missing, "notWordLike": not_word_like})
        if path == PUBLISH_PATH:
            if state["publish_error"] is not None:
                body, status = state["publish_error"]
                return (json.dumps(body), status, {"Content-Type": "application/json"})
            words = payload["words"]
            skipped_cached = len([w for w in words if w in state["cached"]])
            return _tuple({"scanned": len(words), "published": len(words) - skipped_cached,
                           "skippedCached": skipped_cached, "skippedInFlight": 0,
                           "skippedInvalid": 0, "skippedNotWordLike": len(
                               [w for w in words if w in state["notWordLike"]]),
                           "failed": [], "nextRankFrom": None})
        raise AssertionError("unexpected upstream path: " + path)

    monkeypatch.setattr(web, "_moonwell_proxy", fake_proxy)
    return SimpleNamespace(calls=calls, state=state)


@pytest.fixture
def synchronous_publish(monkeypatch):
    """让后台发布线程在请求线程里跑完：否则台账断言要等 daemon，测试必抖。"""
    from cps.reading_word_detail.service import WordDetailBatchService

    monkeypatch.setattr(WordDetailBatchService, "_spawn_publish_worker",
                        lambda self, job_id, book_title, publish:
                        self._publish_worker(job_id, book_title, publish))


@pytest.fixture
def no_publish(monkeypatch):
    """批次建好但不发布：给「取消」用例一个没有线程竞争的静态现场。"""
    from cps.reading_word_detail.service import WordDetailBatchService

    monkeypatch.setattr(WordDetailBatchService, "_spawn_publish_worker",
                        lambda self, job_id, book_title, publish: None)


def _sessions():
    """请求线程会话 + expire_all：后台/其它会话写入的计数要能读到最新值。"""
    from cps import ub

    ub.session.expire_all()
    return ub.session


def _models():
    from cps.reading_word_detail.models import WordDetailJob, WordDetailJobItem

    return WordDetailJob, WordDetailJobItem


def _login_plain(app):
    from cps import ub
    from werkzeug.security import generate_password_hash

    user = ub.session.query(ub.User).filter(ub.User.name == "wd-plain").first()
    if user is None:
        user = ub.User(name="wd-plain", email="wd@example.com",
                       password=generate_password_hash("wd-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()
    client = app.test_client()
    assert client.post("/login", data={"username": "wd-plain",
                                       "password": "wd-pass"}).status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


class TestPreviewIsReadOnly:
    def test_preview_never_touches_the_publish_endpoint(self, admin_client, stubbed_book,
                                                        fake_moonwell):
        rv = admin_client.post("/ajax/word-detail-preview",
                               json={"book_id": 7, "book_format": "epub"})

        assert rv.status_code == 200
        paths = {c["path"] for c in fake_moonwell.calls}
        assert paths == {CHECK_PATH}, \
            "预览只允许打 cached-check；打到 warm-publish-by-words 就是「查规模」变成「下单」"

    def test_preview_counts_come_from_upstream(self, admin_client, stubbed_book, fake_moonwell):
        fake_moonwell.state["cached"] = {"runner"}
        fake_moonwell.state["notWordLike"] = set(_NOT_WORD_LIKE)

        body = admin_client.post("/ajax/word-detail-preview", json={"book_id": 7}).get_json()

        assert body["distinctWords"] == 6
        assert body["cachedWords"] == 1
        assert body["notWordLike"] == 2
        assert body["targetWords"] == 3, "待生成 = 去重词 − 已缓存 − 非词形"
        assert body["estimatedTokens"] == 3 * 4000
        assert set(body["missingSample"]) == {"excruiciating", "about", "running"}

    def test_preview_probes_in_chunks_of_at_most_2000(self, admin_client, stubbed_book,
                                                      fake_moonwell, monkeypatch):
        from cps.reading_word_detail.service import WordDetailBatchService

        many = ["w%04d" % i for i in range(2500)]
        monkeypatch.setattr(WordDetailBatchService, "distinct_words",
                            staticmethod(lambda paragraphs: many))

        rv = admin_client.post("/ajax/word-detail-preview", json={"book_id": 7})

        assert rv.status_code == 200
        chunks = [c["payload"]["words"] for c in fake_moonwell.calls if c["path"] == CHECK_PATH]
        assert [len(chunk) for chunk in chunks] == [2000, 500], \
            "服务端单次上限 2000、超限直接拒；分批数与词数必须对齐"

    def test_missing_book_id_is_rejected_before_upstream(self, admin_client, stubbed_book,
                                                         fake_moonwell):
        rv = admin_client.post("/ajax/word-detail-preview", json={"book_id": ""})

        assert rv.status_code == 400
        assert not fake_moonwell.calls, "入参非法不该先花一趟上游调用"


class TestAdminGating:
    @pytest.mark.parametrize("url", ["/ajax/word-detail-preview", "/ajax/word-detail-start",
                                     "/ajax/word-detail-progress", "/ajax/word-detail-cancel"])
    def test_plain_user_gets_json_403_not_html(self, app, url):
        rv = _login_plain(app).post(url, json={"book_id": 7})

        assert rv.status_code == 403
        assert rv.get_json()["success"] is False, "面板读 message 文案，HTML 403 只会显示 HTTP 403"

    @pytest.mark.parametrize("url", ["/ajax/word-detail-preview", "/ajax/word-detail-start"])
    def test_gate_blocks_before_any_upstream_call(self, app, monkeypatch, url):
        from cps import web

        def spy(path, payload, timeout, label, **kwargs):
            raise AssertionError("非管理员不该打到 moon-well: " + path)

        monkeypatch.setattr(web, "_moonwell_proxy", spy)

        assert _login_plain(app).post(url, json={"book_id": 7}).status_code == 403

    def test_page_route_requires_admin(self, app):
        assert _login_plain(app).get("/word-detail-batch?book_id=7").status_code == 403

    def test_page_route_rejects_non_numeric_book_id(self, admin_client):
        assert admin_client.get("/word-detail-batch?book_id=abc").status_code == 400


class TestUpstreamErrorsAreVisible:
    def test_gate_message_reaches_the_browser_through_progress(self, admin_client, stubbed_book,
                                                               synchronous_publish, fake_moonwell):
        # moon-well 的灌队闸门是 GlobalException → HTTP 500 + Result.message
        fake_moonwell.state["publish_error"] = (
            {"success": False, "message": "该 caller 在途任务已达上限 12000，请等待队列消化",
             "result": None}, 500)

        started = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()

        # Why 断在 progress 而不是 start 的响应码：发布在后台线程，start 先返回「批次已受理」
        # 才是对的形制（同步发完整本必然被网关掐断，整本翻译 R78 实测过）；
        # 但闸门文案必须原样到达浏览器，否则管理员只剩一个涨不满的覆盖率。
        assert started["status"] == "RUNNING"
        progress = admin_client.post("/ajax/word-detail-progress",
                                     json={"job_id": started["jobId"]}).get_json()
        assert "在途任务已达上限" in progress["lastError"]
        assert progress["failedBatches"] == 1

    def test_unreadable_upstream_body_still_fails_loud(self, admin_client, stubbed_book,
                                                       monkeypatch):
        from cps import web

        monkeypatch.setattr(web, "_moonwell_proxy",
                            lambda path, payload, timeout, label, **kwargs:
                            ('<html>502</html>', 502, {"Content-Type": "text/html"}))

        rv = admin_client.post("/ajax/word-detail-preview", json={"book_id": 7})

        assert rv.status_code == 400
        assert "cached-check" in rv.get_json()["message"]


class TestStartLedger:
    def test_batches_are_200_words_and_payload_matches(self, admin_client, stubbed_book,
                                                        synchronous_publish, fake_moonwell,
                                                        monkeypatch):
        from cps.reading_word_detail.service import WordDetailBatchService

        many = ["w%04d" % i for i in range(450)]
        monkeypatch.setattr(WordDetailBatchService, "distinct_words",
                            staticmethod(lambda paragraphs: many))

        rv = admin_client.post("/ajax/word-detail-start", json={"book_id": 7})

        assert rv.status_code == 200
        publishes = [c["payload"] for c in fake_moonwell.calls if c["path"] == PUBLISH_PATH]
        assert [len(p["words"]) for p in publishes] == [200, 200, 50]
        assert all(p["bookName"] == "Sticky Book" and p["skipCached"] is True for p in publishes)
        assert sum(len(p["words"]) for p in publishes) == 450, "分批不能吞词也不能重复发"
        assert publishes[0]["words"] == many[:200]

        job_model, item_model = _models()
        session = _sessions()
        job = session.query(job_model).one()
        assert job.target_words == 450
        items = session.query(item_model).order_by(item_model.batch_seq).all()
        assert [item.batch_seq for item in items] == [0, 1, 2]
        assert [len(json.loads(item.words_json)) for item in items] == [200, 200, 50]

    def test_publish_receipt_counts_land_on_the_item(self, admin_client, stubbed_book,
                                                      synchronous_publish, fake_moonwell):
        fake_moonwell.state["cached"] = {"runner"}
        fake_moonwell.state["notWordLike"] = set(_NOT_WORD_LIKE)

        admin_client.post("/ajax/word-detail-start", json={"book_id": 7})

        _, item_model = _models()
        item = _sessions().query(item_model).one()
        assert item.published_count == 3
        assert item.skipped_cached == 0, "唯一的已缓存词不会进本批（预览已排除）"
        assert item.covered_count == item.skipped_cached, "受理即知的覆盖要落账，进度条不能从 0 起步"

    def test_start_skips_a_book_with_nothing_missing(self, admin_client, stubbed_book,
                                                      fake_moonwell):
        fake_moonwell.state["cached"] = set(_TARGET_WORDS)
        fake_moonwell.state["notWordLike"] = set(_NOT_WORD_LIKE)

        rv = admin_client.post("/ajax/word-detail-start", json={"book_id": 7})

        assert rv.status_code == 400
        assert "无需补缺" in rv.get_json()["message"]
        assert [c["path"] for c in fake_moonwell.calls] == [CHECK_PATH]

    def test_active_job_within_thirty_minutes_is_reused(self, admin_client, stubbed_book,
                                                        synchronous_publish, fake_moonwell):
        first = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()
        before = [c["path"] for c in fake_moonwell.calls].count(PUBLISH_PATH)
        fake_moonwell.state["cached"].add("excruiciating")

        second = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()

        assert second["jobId"] == first["jobId"], "同书活动批次必须复用，否则点两次就是双份队列"
        assert [c["path"] for c in fake_moonwell.calls].count(PUBLISH_PATH) == before
        assert [c["path"] for c in fake_moonwell.calls].count(CHECK_PATH) == 1, \
            "复用判定在抽词与探针之前：重复点击不该白付一趟索引扫描"

    def test_zombie_job_is_closed_and_a_fresh_batch_starts(self, admin_client, stubbed_book,
                                                            synchronous_publish, fake_moonwell):
        from datetime import timedelta

        from cps.reading_translation.timeutil import now_utc

        job_model, _ = _models()
        first = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()
        # 把批次打成僵尸：updated_at 拨回 31 分钟（容器重启杀掉发布线程的真实形态）
        session = _sessions()
        job = session.query(job_model).filter_by(id=first["jobId"]).one()
        job.updated_at = now_utc() - timedelta(minutes=31)
        session.commit()

        second = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()

        assert second["jobId"] != first["jobId"], "僵尸批次不能永远霸占复用通道"
        assert session.query(job_model).filter_by(id=first["jobId"]).one().status == "PARTIAL_FAILED"


class TestProgressIsCoverage:
    def test_coverage_comes_from_the_cache_probe_not_task_status(self, admin_client, stubbed_book,
                                                                  synchronous_publish, fake_moonwell):
        # 与生产同形：moon-well 的词形过滤先把缩略形/连字符挡在入队之前，
        # 台账的分母才等于「真该生成详解的词」
        fake_moonwell.state["notWordLike"] = set(_NOT_WORD_LIKE)
        started = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()
        assert started["coveredWords"] == 0

        # 队列消费者写回了 2 个词的详解——任务状态在这里看不见，只有缓存是真话
        fake_moonwell.state["cached"].update({"excruiciating", "runner"})

        progress = admin_client.post("/ajax/word-detail-progress",
                                     json={"job_id": started["jobId"]}).get_json()

        assert progress["targetWords"] == 4
        assert progress["coveredWords"] == 2
        assert progress["coverage"] == 0.5
        assert progress["status"] == "RUNNING", "还有词没覆盖就不能报完成"

    def test_words_the_server_calls_not_word_like_never_count_as_covered(
            self, admin_client, stubbed_book, synchronous_publish, fake_moonwell):
        """入队后才被判成非词形的词不能算进分子——那是「提前 100%」的假完成。"""
        started = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()
        fake_moonwell.state["cached"] = {"excruiciating", "runner", "running"}
        fake_moonwell.state["notWordLike"] = {"about"}

        progress = admin_client.post("/ajax/word-detail-progress",
                                     json={"job_id": started["jobId"]}).get_json()

        assert progress["coveredWords"] == 3
        assert progress["status"] == "RUNNING"
        assert progress["coverage"] < 1.0

    def test_progress_without_job_id_falls_back_to_latest_book_job(self, admin_client, stubbed_book,
                                                                    synchronous_publish, fake_moonwell):
        started = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()

        progress = admin_client.post("/ajax/word-detail-progress", json={"book_id": 7}).get_json()

        assert progress["jobId"] == started["jobId"]

    def test_progress_with_no_batch_says_none(self, admin_client, stubbed_book, fake_moonwell):
        rv = admin_client.post("/ajax/word-detail-progress", json={"book_id": 999})

        assert rv.get_json() == {"status": "NONE"}

    def test_completed_batches_are_not_probed_again(self, admin_client, stubbed_book,
                                                     synchronous_publish, fake_moonwell):
        fake_moonwell.state["notWordLike"] = set(_NOT_WORD_LIKE)
        started = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()
        fake_moonwell.state["cached"] = set(_TARGET_WORDS)
        probes = lambda: [c for c in fake_moonwell.calls if c["path"] == CHECK_PATH]
        admin_client.post("/ajax/word-detail-progress", json={"job_id": started["jobId"]})
        before = len(probes())

        done = admin_client.post("/ajax/word-detail-progress",
                                 json={"job_id": started["jobId"]}).get_json()

        assert done["status"] == "COMPLETED" and done["coverage"] == 1.0
        assert len(probes()) == before, \
            "批次已全部覆盖就不该再探——cached-check 服务端是一趟索引级扫描"

    def test_other_users_job_is_not_readable(self, app, admin_client, stubbed_book,
                                              synchronous_publish, fake_moonwell):
        started = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()

        rv = _login_plain(app).post("/ajax/word-detail-progress", json={"job_id": started["jobId"]})

        assert rv.status_code == 403


class TestCancel:
    def test_cancel_stops_remaining_batches(self, admin_client, stubbed_book, no_publish,
                                             fake_moonwell):
        job_model, item_model = _models()
        started = admin_client.post("/ajax/word-detail-start", json={"book_id": 7}).get_json()

        canceled = admin_client.post("/ajax/word-detail-cancel",
                                     json={"job_id": started["jobId"]}).get_json()

        assert canceled["status"] == "CANCELED"
        session = _sessions()
        assert session.query(job_model).filter_by(id=started["jobId"]).one().status == "CANCELED"
        assert [item.status for item in session.query(item_model).all()] == ["SKIPPED"], \
            "未发布的批次要落 SKIPPED，否则页面还在等一批永远不会发出去的词"

    def test_cancel_unknown_job_is_400(self, admin_client, stubbed_book, fake_moonwell):
        rv = admin_client.post("/ajax/word-detail-cancel", json={"job_id": "nope"})

        assert rv.status_code == 400


class TestTemplateContract:
    @staticmethod
    def _msgids(path):
        with open(path, encoding="utf-8") as handle:
            return set(re.findall(r"_\('([^']*)'\)", handle.read()))

    def test_every_msgid_has_chinese_translation(self):
        with open(_PO, "rb") as handle:
            catalog = read_po(handle)
        missing = [msgid for msgid in self._msgids(_TEMPLATE) | self._msgids(_LAYOUT)
                   if not (catalog.get(msgid) and catalog.get(msgid).string)]
        assert not missing, "缺 zh 译文会让 zh 用户静默看到英文（R112 同型失效）: {}".format(missing)

    def test_no_javascript_runtime_gettext_call(self):
        with open(_TEMPLATE, encoding="utf-8") as handle:
            script = re.search(r"<script>(.*?)</script>", handle.read(), re.S).group(1)
        rendered = re.sub(r"\{\{[_\s].*?\}\}", "X", script, flags=re.S)
        assert not re.search(r"(?<![\w.])_\(", rendered), "JS 里存在未被 Jinja 渲染的 _() 调用"

    def test_no_adjacent_duplicate_code_lines(self):
        """规则与 MIN_LEN 取自 test_no_duplicate_js_lines，范围换成本模板的 script。"""
        with open(_TEMPLATE, encoding="utf-8") as handle:
            script = re.search(r"<script>(.*?)</script>", handle.read(), re.S).group(1)
        lines = [line.strip() for line in script.splitlines()
                 if line.strip() and not line.strip().startswith("//")]
        duplicates = [(before, after) for before, after in zip(lines, lines[1:])
                      if len(before) >= 20 and before == after]
        assert not duplicates, "相邻同文行（合并残留嫌疑）: {}".format(duplicates[:3])

    def test_no_innerhtml_of_upstream_text(self):
        """书名/上游文案一律 textContent：拼进 innerHTML 等于把存储型 XSS 请进管理页。"""
        with open(_TEMPLATE, encoding="utf-8") as handle:
            script = re.search(r"<script>(.*?)</script>", handle.read(), re.S).group(1)

        # 只判**赋值**：注释里写「不拼进 innerHTML」是这条守卫的说明文字，不是违规
        assert not re.search(r"\.innerHTML\s*=", script)
        assert "document.createElement" in script

    def test_all_ajax_urls_point_at_registered_endpoint_names(self):
        from cps import web

        for name in ("reading_word_detail_preview", "reading_word_detail_start",
                     "reading_word_detail_progress", "reading_word_detail_cancel",
                     "word_detail_batch_page"):
            assert hasattr(web, name), "模板 url_for 依赖的视图函数缺失: " + name

    def test_page_anchors_render_and_poll_is_thirty_seconds(self, admin_client):
        page = admin_client.get("/word-detail-batch?book_id=7").data.decode("utf-8")

        for anchor in ("wd-csrf", "wd-book-id", "wd-book-format", "wd-preview", "wd-sample",
                       "wd-start", "wd-refresh", "wd-cancel", "wd-progress", "wd-fill",
                       "wd-bar-text", "wd-counters", "wd-note"):
            assert 'id="{0}"'.format(anchor) in page
        assert re.search(r'id="wd-start"[^>]*\bdisabled', page), "预览回来之前按钮必须是灰的"
        assert "var POLL_MS = 30000;" in page, \
            "覆盖率探针服务端是索引级扫描，轮询只能是 30s（整本翻译的 4s 源是本地行计数）"

    def test_start_button_is_not_a_one_click_purchase(self, admin_client):
        page = admin_client.get("/word-detail-batch?book_id=7").data.decode("utf-8")

        assert "window.confirm" in page and "preview.targetWords" in page, \
            "入队必须带一次复述数字的确认，否则最贵的调用藏在一次 click 里"

    def test_detail_page_has_the_third_whole_book_button(self):
        """详情页按钮位：三个整本入口经 R214-C 收进「整本任务」面板，位置与数量不变。

        Why 改形制（R214 子项 C）：三个并列按钮合并为单个入口 + 面板三 tab，一一对应；
        守卫跟着变成「入口一处 + 面板里三个 tab」，否则它会替旧形制挡住新需求。
        """
        with open(_DETAIL, encoding="utf-8") as handle:
            source = handle.read()

        assert source.count('id="whole-book-panel-open"') == 1
        assert "partials/whole_book_panel.html" in source
        assert 'id="whole-book-translate"' not in source

        panel = os.path.join(os.path.dirname(_DETAIL), "partials", "whole_book_panel.html")
        with open(panel, encoding="utf-8") as handle:
            panel_source = handle.read()
        assert panel_source.count("web.word_detail_batch_page") == 1
        assert "全文单词详解" in panel_source


class TestChineseRenderingIsLiveNotJustPo:
    """po 有词条 ≠ 用户看得到中文：.mo 没重编译时 zh 用户静默看英文，静态检查还全绿。"""

    @staticmethod
    def _as_zh_admin(app):
        from cps import config as cw_config
        from cps import ub

        admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
        previous = admin.locale
        admin.locale = "zh_Hans_CN"
        ub.session.commit()
        client = app.test_client()
        assert client.post("/login", data={"username": "admin",
                                           "password": "admin123"}).status_code == 302
        cw_config.db_configured = True
        return client, previous

    def test_page_body_renders_chinese_labels(self, app):
        client, previous = self._as_zh_admin(app)
        try:
            rv = client.get("/word-detail-batch?book_id=7")
            page = rv.data.decode("utf-8")

            assert rv.status_code == 200
            for label in ("全文单词详解", "开始补缺", "停止本批次", "本书去重词数", "待生成",
                          "粗算", "本批已入队", "失败批次", "预览加载中…"):
                assert label in page, "zh 页面缺文案：" + label
            assert "Start Backfill" not in page and "To generate" not in page, \
                "zh 页面混进英文即 .mo 未重编译"
        finally:
            from cps import ub

            admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
            admin.locale = previous
            ub.session.commit()

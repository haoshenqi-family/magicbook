"""R126：LLM 任务手动执行面板（magicbook 侧薄代理 + 管理页）。

对齐 moon-well R110 US3 的设计要点，全部在「不经网络」的前提下可验证：
- 四个 ajax 端点转发到正确的 moon-well 路径，请求体原样透传（不做 snake_case 映射，
  映射层会让两侧契约漂移无人发现，范围校验交给 moon-well 服务端夹取）；
- 门禁：admin_required 挡 UI，非管理员一律 403（moon-well 另有白名单二次校验）；
- 导航入口只在 admin 下渲染，普通用户不可见；
- 模板 i18n：新页面每个 _() msgid 必须在 zh_Hans_CN po 里有非空译文，
  否则 zh 用户静默看到英文（R112/R124 同型失效，这次一并锁住）；
- script 内无「相邻同文代码行」（R113 并行会话合并残留，规则取自
  test_no_duplicate_js_lines，只是范围换成本模板）。
"""
import os
import re

import pytest

from babel.messages.pofile import read_po

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE = os.path.join(_ROOT, "cps", "templates", "llm_tasks.html")
_LAYOUT = os.path.join(_ROOT, "cps", "templates", "layout.html")
_PO = os.path.join(_ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.po")


@pytest.fixture
def captured_proxy(monkeypatch):
    """接管 cps.web._moonwell_proxy，记录调用参数并返回一个可辨识的响应。"""
    calls = []

    def fake_proxy(path, payload, timeout, label, **kwargs):
        calls.append({"path": path, "payload": payload, "timeout": timeout,
                      "label": label, "kwargs": kwargs})
        from flask import jsonify
        return jsonify({"success": True, "message": "", "result": {"echo": path}})

    from cps import web
    monkeypatch.setattr(web, "_moonwell_proxy", fake_proxy)
    return calls


def _login_plain(app):
    from cps import ub
    from werkzeug.security import generate_password_hash

    user = ub.session.query(ub.User).filter(ub.User.name == "lr-plain").first()
    if user is None:
        user = ub.User(name="lr-plain", email="lr@example.com",
                       password=generate_password_hash("lr-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()
    client = app.test_client()
    assert client.post("/login", data={"username": "lr-plain", "password": "lr-pass"}).status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


class TestProxyForwarding:
    """四个端点必须打到 moon-well R110 的那四条路径上。"""

    @pytest.mark.parametrize("url,expected_path", [
        ("/ajax/llm-task/options", "/llm/task/run/options"),
        ("/ajax/llm-task/run", "/llm/task/run"),
        ("/ajax/llm-task/status", "/llm/task/run/status"),
        ("/ajax/llm-task/stop", "/llm/task/run/stop"),
    ])
    def test_forwards_to_expected_upstream_path(self, admin_client, captured_proxy, url, expected_path):
        rv = admin_client.post(url, json={})

        assert rv.status_code == 200
        assert captured_proxy[-1]["path"] == expected_path

    def test_run_payload_is_passed_through_unchanged(self, admin_client, captured_proxy):
        payload = {"provider": "zhipu", "model": "glm-4-flash-250414", "concurrency": 2,
                   "maxTasks": 50, "caller": "word-detail-warmup", "taskType": "TEXT",
                   "replayFailed": True}

        rv = admin_client.post("/ajax/llm-task/run", json=payload)

        assert rv.status_code == 200
        assert captured_proxy[-1]["payload"] == payload, "字段名与大小写必须逐字节透传给 moon-well"

    def test_missing_body_becomes_empty_object_not_crash(self, admin_client, captured_proxy):
        rv = admin_client.post("/ajax/llm-task/run", data="", content_type="application/json")

        assert rv.status_code == 200
        assert captured_proxy[-1]["payload"] == {}

    def test_options_sends_no_body_and_has_own_timeout(self, admin_client, captured_proxy):
        admin_client.post("/ajax/llm-task/options", json={})

        assert captured_proxy[-1]["payload"] == {}
        assert captured_proxy[-1]["timeout"] >= 10


class TestAdminGating:
    """非管理员必须被挡住，且 JSON 入口要返回可读 JSON（不是 abort 的 HTML 403）。"""

    def test_plain_user_cannot_open_page(self, app):
        assert _login_plain(app).get("/llm-tasks").status_code == 403

    @pytest.mark.parametrize("url,payload", [
        ("/ajax/llm-task/options", {}),
        ("/ajax/llm-task/run", {"provider": "zhipu"}),
        ("/ajax/llm-task/status", {"runId": "run-1"}),
        ("/ajax/llm-task/stop", {"runId": "run-1"}),
    ])
    def test_plain_user_gets_json_403_not_html(self, app, url, payload):
        rv = _login_plain(app).post(url, json=payload)

        assert rv.status_code == 403
        assert rv.get_json()["success"] is False, "面板靠 message 文案提示，HTML 403 只会显示 HTTP 403"

    def test_gate_blocks_before_any_upstream_call(self, app, monkeypatch):
        # 门禁必须在转发之前：否则非管理员也能借面板打到 moon-well
        hits = []

        def spy(path, payload, timeout, label, **kwargs):
            hits.append(path)
            raise AssertionError("不该被调用：" + path)

        from cps import web
        monkeypatch.setattr(web, "_moonwell_proxy", spy)

        assert _login_plain(app).post("/ajax/llm-task/run", json={"provider": "zhipu"}).status_code == 403
        assert not hits

    def test_admin_page_renders_the_controls(self, admin_client):
        page = admin_client.get("/llm-tasks").data.decode("utf-8")

        for anchor in ("lr-provider", "lr-model", "lr-concurrency", "lr-maxtasks",
                       "lr-caller", "lr-replay", "lr-start", "lr-stop", "lr-body"):
            assert 'id="{0}"'.format(anchor) in page

    def test_start_button_disabled_until_options_confirms_capability(self, admin_client):
        """上游不可达/未确认白名单时按钮必须是灰的，而不是点下去才收到一堆 4xx。"""
        page = admin_client.get("/llm-tasks").data.decode("utf-8")

        assert re.search(r'id="lr-start"[^>]*\bdisabled', page), "初始 state 应为禁用"
        assert "start.disabled = !capability.enabled || !capability.admin" in page, \
            "解禁只允许发生在 options 成功返回之后"

    def test_admin_reaches_the_proxy(self, admin_client, captured_proxy):
        admin_client.post("/ajax/llm-task/run", json={"provider": "zhipu"})

        assert captured_proxy[-1]["path"] == "/llm/task/run"

    def test_upstream_rejection_body_and_status_pass_through(self, admin_client, monkeypatch):
        # moon-well 的拒绝（非白名单 / 自动模式在跑 / 供应商未配置）必须原样到达浏览器：
        # 状态码 + Result.message 都不能被 magicbook 吞掉换成泛用文案，否则管理员无从处置
        import json

        from flask import Response
        from cps import web

        def rejecting(path, payload, timeout, label, **kwargs):
            body = json.dumps({"success": False, "message": "无权限手动执行 LLM 任务", "result": None})
            return Response(body, status=403, content_type="application/json")

        monkeypatch.setattr(web, "_moonwell_proxy", rejecting)

        rv = admin_client.post("/ajax/llm-task/run", json={"provider": "zhipu"})

        assert rv.status_code == 403
        assert rv.get_json()["message"] == "无权限手动执行 LLM 任务"


class TestNavigationEntry:
    def test_admin_dropdown_contains_entry(self, admin_client):
        page = admin_client.get("/reading/settings").data.decode("utf-8")

        assert 'id="top_llm_tasks"' in page
        assert 'href="/llm-tasks"' in page

    def test_plain_user_dropdown_hides_entry(self, app):
        page = _login_plain(app).get("/reading/settings").data.decode("utf-8")

        assert "top_llm_tasks" not in page

    def test_entry_id_appears_once(self, admin_client):
        page = admin_client.get("/reading/settings").data.decode("utf-8")

        assert page.count('id="top_llm_tasks"') == 1, "相邻重复即并行会话合并残留（R113）"


class TestChineseRenderingIsLiveNotJustPo:
    """po 里有词条 ≠ 用户看得到中文：.mo 没重编译时 zh 用户静默看英文，
    而只读 po 的静态检查全绿。这条用真实渲染把 .mo 一起验掉。"""

    @staticmethod
    def _as_zh_admin(app):
        from werkzeug.security import generate_password_hash
        from cps import ub, config as cw_config

        admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
        previous = admin.locale
        admin.locale = "zh_Hans_CN"
        ub.session.commit()
        client = app.test_client()
        assert client.post("/login", data={"username": "admin", "password": "admin123"}).status_code == 302
        cw_config.db_configured = True
        return client, previous

    def test_nav_label_switches_to_chinese(self, app):
        client, previous = self._as_zh_admin(app)
        try:
            page = client.get("/reading/settings").data.decode("utf-8")
            block = re.search(r'<li class="dropdown" id="top_mb_settings">.*?</ul>\s*</li>', page, re.S).group(0)

            assert "任务执行" in block
            assert "Task Runner" not in block, "zh 下拉框混进英文即 .mo 未重编译"
        finally:
            from cps import ub
            admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
            admin.locale = previous
            ub.session.commit()

    def test_page_body_renders_chinese_labels(self, app):
        client, previous = self._as_zh_admin(app)
        try:
            rv = client.get("/llm-tasks")
            page = rv.data.decode("utf-8")

            assert rv.status_code == 200
            for label in ("并发数", "开始执行", "停止执行", "供应商", "本批处理上限", "调用方筛选", "已认领"):
                assert label in page, "zh 页面缺文案：" + label
            # script 里的文案也必须被 Jinja 渲染成中文（T 表里的 'Batch started' → 批次已启动）
            assert "批次已启动" in page, "script 内文案未走 Jinja 渲染，浏览器会拿到英文或 ReferenceError"
        finally:
            from cps import ub
            admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
            admin.locale = previous
            ub.session.commit()


class TestCrossRepoContract:
    """把面板提交的 JSON 键与 moon-well DTO 字段名锁在一起。

    Why 跨仓库源码级断言：两侧不在同一构建里，字段名对不上不会有任何编译或测试信号，
    只会在线上表现为「provider 填了但服务端收到 null」。moon-well 与本仓同在
    haoshenqi-family 工作区，路径缺失时跳过（例如单独 clone magicbook）。
    """

    _JAVA_DTO = os.path.join(_ROOT, "..", "moon-well", "src", "main", "java", "top",
                             "haoshenqi", "magicbook", "system", "llm", "pojo", "dto",
                             "LlmTaskRunReqDTO.java")

    @pytest.mark.skipif(not os.path.exists(_JAVA_DTO), reason="moon-well 仓库不在同一工作区")
    @pytest.mark.parametrize("dto,expected", [
        ("LlmTaskRunReqDTO.java", None),
    ])
    def test_run_payload_keys_exist_on_the_java_dto(self, dto, expected):
        with open(self._JAVA_DTO, encoding="utf-8") as handle:
            source = handle.read()
        # 类型可能带嵌套泛型（Map<String, List<String>>），字符类必须容下 < > , 空格
        java_fields = set(re.findall(r"private\s+[\w<>, .]+\s+(\w+);", source))
        with open(_TEMPLATE, encoding="utf-8") as handle:
            script = re.search(r"<script>(.*?)</script>", handle.read(), re.S).group(1)
        body = re.search(r'llm_task_run"\) \}\}\', \{(.*?)\n {8}\}\)', script, re.S)
        assert body, "找不到 run 请求体字面量，模板结构变了"
        sent = set(re.findall(r"^\s{12}(\w+):", body.group(1), re.M))

        assert {"provider", "model", "caller", "concurrency", "maxTasks", "replayFailed"} <= sent
        unknown = sent - java_fields
        assert not unknown, "面板提交了 DTO 上不存在的键（服务端会静默丢字段）: {}".format(sorted(unknown))

    def test_frontend_reads_only_fields_moon_well_returns(self):
        # 前端读的字段名必须都在响应 DTO 里，否则拿到 undefined 显示成空白
        from pathlib import Path
        base = Path(_ROOT).parent / "moon-well" / "src" / "main" / "java" / "top" / \
            "haoshenqi" / "magicbook" / "system" / "llm" / "pojo" / "dto"
        if not base.exists():
            pytest.skip("moon-well 仓库不在同一工作区")
        fields = set()
        for name in ("LlmTaskRunOptionsRespDTO.java", "LlmTaskRunProgressRespDTO.java",
                     "LlmTaskRunRespDTO.java"):
            fields |= set(re.findall(r"private\s+[\w<>, .]+\s+(\w+);",
                                     (base / name).read_text(encoding="utf-8")))
        with open(_TEMPLATE, encoding="utf-8") as handle:
            script = re.search(r"<script>(.*?)</script>", handle.read(), re.S).group(1)
        read = set(re.findall(r"(?:data|result)\.(\w+)", script))

        missing = read - fields
        assert not missing, "前端读取了响应里不存在的字段: {}".format(sorted(missing))


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
        """script 里的 _( ) 必须由 Jinja 渲染；裸调用在浏览器是 ReferenceError。"""
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

    def test_all_ajax_urls_point_at_registered_endpoint_names(self):
        from cps import web

        for name in ("llm_task_options", "llm_task_run", "llm_task_status",
                     "llm_task_stop", "llm_task_runner_page"):
            assert hasattr(web, name), "模板 url_for 依赖的视图函数缺失: " + name

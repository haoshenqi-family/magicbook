"""R130：LLM 队列监控面板（四区块，对齐 moon-well R118）。

全部在「不经网络」的前提下可验证：
- 六个新 ajax 端点转发到 moon-well R118 的 admin 路径，请求体原样透传、
  超时按 LLD 表钉住（overview 10 / failures 15 / page 10 / detail 10 /
  recovery-plan 20 / republish 30）；
- 门禁：六个 JSON 入口非管理员一律 JSON 403（R126 同款 gate，先于任何上游调用）；
- 模板：四区块 + 模态框 id 齐全；keyword 必须搭配伴生过滤的前端闸门存在；
  AUTO_REQUEUE / FORBIDDEN 桶只读（不渲染动作按钮）；15s 轮询在页面不可见时暂停；
- 跨仓契约：前端读取的字段名必须存在于 moon-well 对应 DTO（漂移即红）；
  恢复分类下拉与状态下拉的取值 ⊆ moon-well 枚举；
- zh 渲染：新文案走 po→mo 链路（防「改了 po 忘 compile」的静默英文）。
"""
import os
import re

import pytest
from babel.messages.pofile import read_po

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE = os.path.join(_ROOT, "cps", "templates", "llm_tasks.html")
_PO = os.path.join(_ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.po")
_MOONWELL_DTO = os.path.join(_ROOT, "..", "moon-well", "src", "main", "java", "top",
                             "haoshenqi", "magicbook", "system", "llm", "pojo", "dto")
_MON_ENUM = os.path.join(_ROOT, "..", "moon-well", "src", "main", "java", "top",
                         "haoshenqi", "magicbook", "system", "llm", "pojo", "constant")


@pytest.fixture
def captured_proxy(monkeypatch):
    """接管 cps.web._moonwell_client.proxy，记录调用参数（R126 同款）。"""
    calls = []

    def fake_proxy(path, payload, timeout, label, **kwargs):
        calls.append({"path": path, "payload": payload, "timeout": timeout, "label": label})
        from flask import jsonify
        return jsonify({"success": True, "message": "", "result": {"echo": path}})

    from cps import web
    monkeypatch.setattr(web._moonwell_client, "proxy", fake_proxy)
    return calls


def _login_plain(app):
    from cps import ub
    from werkzeug.security import generate_password_hash

    user = ub.session.query(ub.User).filter(ub.User.name == "mon-plain").first()
    if user is None:
        user = ub.User(name="mon-plain", email="mon@example.com",
                       password=generate_password_hash("mon-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()
    client = app.test_client()
    assert client.post("/login", data={"username": "mon-plain", "password": "mon-pass"}).status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


def _monitor_script():
    """第二个 <script> 块（R130 监控脚本）。"""
    with open(_TEMPLATE, encoding="utf-8") as fh:
        src = fh.read()
    blocks = re.findall(r"<script>(.*?)</script>", src, re.S)
    assert len(blocks) >= 2, "R130 监控脚本块缺失"
    return blocks[-1]


class TestProxyForwarding:
    """六个端点必须打到 moon-well R118 的 admin 路径上，超时按 LLD §1 钉住。"""

    @pytest.mark.parametrize("url,expected_path,timeout", [
        ("/ajax/llm-task/admin-overview", "/llm/task/admin/overview", 10),
        ("/ajax/llm-task/admin-failures", "/llm/task/admin/failures", 15),
        ("/ajax/llm-task/admin-page", "/llm/task/admin/page", 10),
        ("/ajax/llm-task/detail", "/llm/task/detail", 10),
        ("/ajax/llm-task/admin-recovery-plan", "/llm/task/admin/recovery-plan", 20),
        ("/ajax/llm-task/admin-republish-failed", "/llm/task/admin/republish-failed", 30),
    ])
    def test_forwards_to_expected_upstream_path(self, admin_client, captured_proxy,
                                                url, expected_path, timeout):
        rv = admin_client.post(url, json={})

        assert rv.status_code == 200
        hit = captured_proxy[-1]
        assert hit["path"] == expected_path
        assert hit["timeout"] == timeout, "超时是 LLD 设计值，改动须同步设计文档"

    def test_payload_passes_through_unchanged(self, admin_client, captured_proxy):
        payload = {"caller": "word-detail-warmup", "errorCode": "E_TIMEOUT",
                   "category": "TIMEOUT", "limit": 500, "confirm": True,
                   "keyword": "book-91", "status": "FAILED", "pageNo": 2, "pageSize": 50}

        for url in ("/ajax/llm-task/admin-failures", "/ajax/llm-task/admin-page",
                    "/ajax/llm-task/admin-recovery-plan", "/ajax/llm-task/admin-republish-failed"):
            admin_client.post(url, json=payload)
            assert captured_proxy[-1]["payload"] == payload, \
                "字段名与大小写必须逐字节透传（R126 同款契约决策）"

    def test_overview_sends_empty_body(self, admin_client, captured_proxy):
        admin_client.post("/ajax/llm-task/admin-overview", json={})

        assert captured_proxy[-1]["payload"] == {}

    def test_confirm_reaches_upstream_verbatim(self, admin_client, captured_proxy):
        """confirm:true 必须原样到达 moon-well——服务端把它当写闸门，代理不许剥。"""
        admin_client.post("/ajax/llm-task/admin-republish-failed",
                          json={"caller": "word-detail-warmup", "limit": 100, "confirm": True})

        assert captured_proxy[-1]["payload"]["confirm"] is True


class TestAdminGating:
    """非管理员必须被挡在六个 JSON 入口外，且是可读 JSON、先于任何上游调用。"""

    URLS = ("/ajax/llm-task/admin-overview", "/ajax/llm-task/admin-failures",
            "/ajax/llm-task/admin-page", "/ajax/llm-task/detail",
            "/ajax/llm-task/admin-recovery-plan", "/ajax/llm-task/admin-republish-failed")

    @pytest.mark.parametrize("url", URLS)
    def test_plain_user_gets_json_403(self, app, url):
        rv = _login_plain(app).post(url, json={})

        assert rv.status_code == 403
        assert rv.get_json()["success"] is False

    def test_gate_blocks_before_any_upstream_call(self, app, monkeypatch):
        hits = []

        def spy(path, payload, timeout, label, **kwargs):
            hits.append(path)
            raise AssertionError("不该被调用：" + path)

        from cps import web
        monkeypatch.setattr(web._moonwell_client, "proxy", spy)

        for url in self.URLS:
            assert _login_plain(app).post(url, json={}).status_code == 403
        assert not hits


class TestTemplateContract:
    """四区块结构、前端闸门与渲染规则必须留在模板里。"""

    @pytest.fixture(autouse=True)
    def page(self, admin_client):
        return admin_client.get("/llm-tasks").data.decode("utf-8")

    def test_four_blocks_and_modal_exist(self, page):
        for anchor in ("lr-mon-overview", "lr-mon-failures", "lr-mon-tasks",
                       "lr-mon-recovery", "lr-mon-detail", "lr-mon-ov-bars"):
            assert 'id="{0}"'.format(anchor) in page, "监控区块缺失: " + anchor

    def test_top_level_tabs_run_and_monitor(self, page):
        # UI 改版二轮：页面顶层两大 Tab（任务执行 / 队列监控），R126 与 R130 各居其一
        assert 'id="lr-top-tabs"' in page
        for anchor_id in ("lr-pane-run", "lr-pane-monitor"):
            assert 'id="{0}"'.format(anchor_id) in page
        assert 'href="#lr-pane-run"' in page and 'href="#lr-pane-monitor"' in page

    def test_keyword_gate_is_enforced_client_side(self, page):
        # moon-well 强制 keyword 搭配伴生过滤；前端提前拦下（禁用按钮 + 变色提示）
        assert "var blocked = !!f.keyword && !f.companion" in page
        assert "document.getElementById('lr-mon-t-query').disabled = blocked" in page

    def test_readonly_recovery_buckets_render_no_button(self, page):
        # AUTO_REQUEUE / FORBIDDEN 桶只读：只有徽标、没有动作按钮（AC A2）
        assert "bucket.recovery === 'AUTO_REQUEUE' || bucket.recovery === 'FORBIDDEN'" in page
        assert "if (readOnly || bucket.recovery === 'MANUAL') { return badge; }" in page

    def test_plan_never_sends_confirm(self, page):
        # 两步语义：plan 请求体由 buildRecoveryBody(false) 构造（恒不带 confirm），
        # 只有确认按钮才拼 confirm:true —— 防止「看一眼预案就写库」
        assert "var body = buildRecoveryBody(false);" in page
        assert "Object.assign({}, recoveryBody, {confirm: true})" in page

    def test_republish_needs_window_confirm(self, page):
        assert "if (!window.confirm(text)) { return; }" in page
        assert "T.confirmRepublish.replace('{N}'" in page

    def test_polling_pauses_when_hidden(self, page):
        assert "if (!document.hidden) { loadOverview(); }" in page
        assert "}, 15000);" in page
        assert "document.addEventListener('visibilitychange'" in page

    def test_no_javascript_runtime_gettext_call(self):
        script = _monitor_script()
        rendered = re.sub(r"\{\{[_\s].*?\}\}", "X", script, flags=re.S)
        assert not re.search(r"(?<![\w.])_\(", rendered), "JS 里存在未被 Jinja 渲染的 _() 调用"

    def test_no_adjacent_duplicate_code_lines(self):
        script = _monitor_script()
        lines = [line.strip() for line in script.splitlines()
                 if line.strip() and not line.strip().startswith("//")]
        duplicates = [(before, after) for before, after in zip(lines, lines[1:])
                      if len(before) >= 20 and before == after]
        assert not duplicates, "相邻同文行（合并残留嫌疑）: {}".format(duplicates[:3])

    def test_all_monitor_urls_point_at_registered_endpoints(self, app):
        for name in ("llm_task_overview", "llm_task_failures", "llm_task_admin_page",
                     "llm_task_detail", "llm_task_recovery_plan", "llm_task_republish"):
            assert "web." + name in {r.endpoint for r in app.url_map.iter_rules()}, \
                "模板 url_for 依赖的 endpoint 未注册: " + name


class TestCrossRepoContract:
    """前端读取的字段必须存在于 moon-well DTO；下拉取值必须 ⊆ 枚举。

    Why 跨仓库源码级断言（R126 同款）：两侧不在同一构建里，字段名对不上没有任何
    编译/测试信号，只会在线上表现为 undefined 空白。moon-well 不在同一工作区时跳过。
    """

    # 每组 = (DTO 文件名, 模板 JS 里实际读取的字段清单)；清单同时在模板里回查存在性，
    # 防止测试清单与模板各自漂移
    FIELD_SETS = [
        ("LlmTaskOverviewRespDTO.java",
         ["pendingCount", "acceptedCount", "runningCount", "callers", "throughput",
          "oldestPendingCreatedAt", "lastFinishedAt", "ratePerHour", "stale", "reclaim"]),
        ("LlmTaskFailuresRespDTO.java",
         ["totalFailed", "unknownRatio", "buckets"]),
        ("LlmTaskAdminRowRespDTO.java",
         ["taskId", "caller", "status", "taskType", "provider", "model", "errorCode",
          "latencyMs", "totalTokens", "createdAt"]),
        ("LlmTaskDetailRespDTO.java",
         ["taskId", "requestId", "userId", "caller", "mode", "taskType", "priority",
          "provider", "model", "acceptedBy", "acceptedAt", "latencyMs", "errorCode",
          "errorMessage", "input", "parameters", "output", "status"]),
        ("LlmTaskRecoveryRespDTO.java",
         ["mode", "blocked", "blockReason", "byCategory", "totalFailed", "replayEligible",
          "republishEligible", "plannedLimit", "republished", "skippedDuplicate",
          "skippedForbiddenCategory", "failed"]),
        ("LlmTaskRecoveryReqDTO.java",
         ["caller", "errorCode", "category", "limit", "confirm"]),
    ]

    def test_frontend_reads_only_fields_moon_well_returns(self):
        if not os.path.isdir(_MOONWELL_DTO):
            pytest.skip("moon-well 仓库不在同一工作区")
        script = _monitor_script()
        for dto, fields in self.FIELD_SETS:
            with open(os.path.join(_MOONWELL_DTO, dto), encoding="utf-8") as fh:
                java_fields = set(re.findall(r"private\s+[\w<>, .]+\s+(\w+);", fh.read()))
            for field in fields:
                # 请求侧字段以对象字面量键出现（limit:、confirm:），响应侧以点访问出现，两种形态都认
                assert re.search(r"\." + field + r"\b|" + field + r"\s*:", script), \
                    "测试清单里的 {} 在模板 JS 中已不存在（清单与模板漂移）".format(field)
                # 嵌套类字段（CallerRow/Bucket/CategoryCount/FailedItem）也用 private 声明，一并命中
                assert field in java_fields, \
                    "{}: 前端读取了 DTO 上不存在的字段 {}".format(dto, field)

    def test_category_options_match_moon_well_enum(self):
        enum_path = os.path.join(_MON_ENUM, "LlmTaskFailureCategory.java")
        if not os.path.exists(enum_path):
            pytest.skip("moon-well 仓库不在同一工作区")
        with open(enum_path, encoding="utf-8") as fh:
            enum_values = set(re.findall(r"^\s+([A-Z_]+)\(Recovery\.", fh.read(), re.M))
        with open(_TEMPLATE, encoding="utf-8") as fh:
            block = re.search(r'id="lr-mon-r-category".*?</select>', fh.read(), re.S).group(0)
        options = set(re.findall(r"<option>([A-Z_]+)</option>", block))

        assert options == enum_values, "恢复分类下拉与 moon-well 枚举漂移: {} vs {}".format(
            sorted(options - enum_values), sorted(enum_values - options))

    def test_status_options_match_moon_well_enum(self):
        enum_path = os.path.join(_MON_ENUM, "LlmTaskStatusEnum.java")
        if not os.path.exists(enum_path):
            pytest.skip("moon-well 仓库不在同一工作区")
        with open(enum_path, encoding="utf-8") as fh:
            enum_values = set(re.findall(r"^\s+([A-Z_]+),?$", fh.read(), re.M))
        with open(_TEMPLATE, encoding="utf-8") as fh:
            block = re.search(r'id="lr-mon-t-status".*?</select>', fh.read(), re.S).group(0)
        options = set(re.findall(r"<option>([A-Z_]+)</option>", block))

        assert options <= enum_values, "状态下拉出现 moon-well 不存在的状态: {}".format(
            sorted(options - enum_values))

    def test_page_vo_shape(self):
        """分页响应消费（records/total）钉在 moon-well PageVO 上。"""
        vo_path = os.path.join(_ROOT, "..", "moon-well", "src", "main", "java", "top",
                               "haoshenqi", "magicbook", "system", "vo", "PageVO.java")
        if not os.path.exists(vo_path):
            pytest.skip("moon-well 仓库不在同一工作区")
        with open(vo_path, encoding="utf-8") as fh:
            fields = set(re.findall(r"private\s+[\w<>, .]+\s+(\w+);", fh.read()))
        assert {"records", "total"} <= fields
        script = _monitor_script()
        assert "data.records" in script and "data.total" in script


class TestChineseRenderingIsLiveNotJustPo:
    """zh 管理员真实渲染：静态区块文案 + script 内 T 表都要是中文（.mo 未编译即红）。"""

    def test_monitor_blocks_render_chinese(self, app):
        from cps import ub
        admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
        previous = admin.locale
        admin.locale = "zh_Hans_CN"
        ub.session.commit()
        try:
            client = app.test_client()
            assert client.post("/login", data={"username": "admin",
                                               "password": "admin123"}).status_code == 302
            from cps import config as cw_config
            cw_config.db_configured = True
            page = client.get("/llm-tasks").data.decode("utf-8")

            assert client.get("/llm-tasks").status_code == 200
            for label in ("队列监控", "队列总览", "失败分类", "任务查询", "生成恢复预案"):
                assert label in page, "zh 页面缺文案：" + label
            # script 内文案（T 表）也必须被 Jinja 渲染成中文
            assert "去恢复此类" in page, "监控脚本 T 表未走 Jinja 渲染"
            assert "确认重发" in page
        finally:
            admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
            admin.locale = previous
            ub.session.commit()

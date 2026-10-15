"""R177（架构评审 B5 / X1 本仓部分）：统一 API 公共层（common/api.js）的契约锁。

Why 纯静态断言：本仓无前端构建链，解包/CSRF 的「四份副本回潮」与「模板载入
顺序断裂」都不会让页面报错，只会让解包语义重新漂移（ai_chat 容错版 vs credits
严格版）、CSRF 某页静默取空——正是 R44/R173 类「接口故障被伪装成数据不存在」
的消费侧土壤。源码级锁住：

  (1) MBApi 公共成员齐全，且容错/严格两个解包口径都在（C1/C2）；
  (2) 四份历史副本不再各自定义解包与 CSRF 取值（C3 单点锁）；
  (3) 三处模板（layout/read/reading_settings）已载 api.js 且先于页面脚本（C4 顺序锁）；
  (4) 失败可见契约：unwrapResult 的失败分支抛 Error（message 上浮），不静默返 null（C5）。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_PATH = os.path.join(ROOT, "cps", "static", "js", "common", "api.js")
LAYOUT_PATH = os.path.join(ROOT, "cps", "templates", "layout.html")
READ_PATH = os.path.join(ROOT, "cps", "templates", "read.html")
SETTINGS_PATH = os.path.join(ROOT, "cps", "templates", "reading_settings.html")

CONSUMERS = ["ai_chat.js", "credits.js", "learning-common.js", "vocab-test.js"]


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def test_c1_api_exports_all_members():
    api = read("cps", "static", "js", "common", "api.js")
    for member in ["csrfToken", "httpJson", "getJson", "postJson",
                   "isBusinessError", "unwrapResult", "unwrapStrict"]:
        assert re.search(rf"{member}\s*:\s*{member}", api), f"MBApi 缺少成员 {member}"
    assert "window.MBApi" in api


def test_c2_csrf_chained_probe_covers_three_shapes():
    api = read("cps", "static", "js", "common", "api.js")
    # 三形态链式探测必须都在公共层（learning 系 / 积分页 / 阅读页隐藏域）
    assert "lh-csrf" in api
    assert "credit-csrf" in api
    assert re.search(r"input\[name=['\"]csrf_token['\"]\]", api)


def test_c3_consumers_no_longer_own_unwrap_or_csrf():
    # 解包迁移面 = 本次三份副本（ai_chat 容错 / credits 严格 / learning 信封判读）；
    # vocab-test 的 wrap.payload/codeOf 与 loadHistory 静默降级是页面状态机（AC-C1
    # 「测试卡片独立降级，弹错误反而打扰档位设置」，注释自证），不解包、不迁移。
    for name in ["ai_chat.js", "credits.js", "learning-common.js"]:
        js = read("cps", "static", "js", name)
        # 解包逻辑单点：消费方只允许一行委托，不允许自带完整实现体
        for banned in [
            r"success\s*!==\s*true",      # credits 原严格判读
            r"data\.success\s*===\s*false",  # ai_chat 原容错判读
            r"response\.data\.success",   # learning 原信封判读
        ]:
            assert not re.search(banned, js), f"{name} 仍自带解包判读（应委托 MBApi）：{banned}"
    for name in CONSUMERS:
        js = read("cps", "static", "js", name)
        # CSRF 取值单点：页面专属选择器的「取值调用」不得再出现（值探测收敛到
        # api.js；注释里的文字提及不算——只锁真实 DOM 访问形态）
        for banned in [
            r"\$\(\s*['\"]#lh-csrf['\"]\s*\)",
            r"getElementById\(\s*['\"]lh-csrf['\"]\s*\)",
            r"\$\(\s*['\"]#credit-csrf['\"]\s*\)",
            r"getElementById\(\s*['\"]credit-csrf['\"]\s*\)",
            r"querySelector\(\s*['\"]input\[name=['\"]csrf_token['\"]\]['\"]\s*\)",
        ]:
            assert not re.search(banned, js), f"{name} 仍直取 CSRF 元素（应委托 MBApi.csrfToken）：{banned}"
        assert "MBApi.csrfToken" in js, f"{name} 未迁移到 MBApi.csrfToken"


def test_c3b_learning_common_delegates_via_mbapi():
    js = read("cps", "static", "js", "learning-common.js")
    for fn in ["httpJson", "getJson", "postJson", "isBusinessError"]:
        assert f"window.MBApi.{fn}" in js, f"learning-common.{fn} 未委托 MBApi"
    # resultOf 走 strict 解包（learning 端点契约：非信封一律抛）
    assert "MBApi.unwrapStrict" in js


def test_c4_templates_load_api_before_page_scripts():
    layout = read("cps", "templates", "layout.html")
    assert "js/common/api.js" in layout, "layout.html 未全局载入 api.js"
    # layout 内：api.js 必须在 block js 之前（页面脚本先于公共层会 ReferenceError）
    assert layout.index("js/common/api.js") < layout.index("{% block js %}"), \
        "layout.html 的 api.js 载入晚于 block js"

    read_html = read("cps", "templates", "read.html")
    assert "js/common/api.js" in read_html
    assert read_html.index("js/common/api.js") < read_html.index("ai_chat_panel.html"), \
        "read.html 的 api.js 必须先于 ai_chat 面板"

    settings = read("cps", "templates", "reading_settings.html")
    assert settings.index("js/common/api.js") < settings.index("js/vocab-test.js"), \
        "reading_settings.html 的 api.js 必须先于 vocab-test.js"


def test_c5_failure_must_be_visible_not_silent():
    api = read("cps", "static", "js", "common", "api.js")
    # 容错口径：success===false 必须抛 Error（message 上浮给调用方呈现），
    # 禁止把业务失败静默吞成 null/原样（R44/R173 家族反模式）
    throw_block = re.search(
        r"unwrapResult[\s\S]{0,800}?success === false[\s\S]{0,200}?throw new Error", api)
    assert throw_block, "unwrapResult 的 success===false 分支必须 throw Error（失败可见）"
    # strict 口径：非信封（含 parse 失败 null）也必须抛
    strict_block = re.search(
        r"unwrapStrict[\s\S]{0,600}?throw new Error", api)
    assert strict_block, "unwrapStrict 的非信封分支必须 throw Error（失败可见）"

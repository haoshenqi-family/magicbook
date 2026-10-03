"""R109: 前端引导模式（onboarding tour）挂载点与状态契约。

Why: 引导模式刻意做成「零 Python 改动」——状态复用既有 POST /ajax/view 写进
     User.view_settings['onboarding']，读取直接在模板里取 current_user.view_settings。
     这两个都是间接依赖：上游一改，引导就静默失效（要么页面 500，要么永远邀请）。
     本测试锁住：挂载点存在且不重复、三种 view_settings 形态都能渲染、
     手动入口随角色显隐、以及 /ajax/view 这条写入通道对本用例确实可用。
"""
import json
import os
import re

import pytest
from werkzeug.security import generate_password_hash

from cps import ub

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cps", "templates")
JS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "cps", "static", "js", "onboarding.js")


@pytest.fixture
def settings_page(admin_client):
    """Why: /reading/settings 无需 calibre 书库，是测试环境里最稳的 layout 载体页
    （沿用 tests/test_nav_settings_dropdown.py 的姿势）。"""
    rv = admin_client.get("/reading/settings")
    assert rv.status_code == 200
    return rv.data.decode("utf-8")


@pytest.fixture
def tour_user(app):
    """独立账号，避免与并行用例争用同一 view_settings。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    if user is None:
        user = ub.User(name="tour-tester", email="tour@example.com",
                       password=generate_password_hash("tour-pass"))
        ub.session.add(user)
        ub.session.commit()
    user.view_settings = {}
    ub.session.commit()

    client = app.test_client()
    rv = client.post("/login", data={"username": "tour-tester", "password": "tour-pass"})
    assert rv.status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


def _dropdown_block(page):
    m = re.search(r'<li class="dropdown" id="top_mb_settings">.*?</ul>\s*</li>', page, re.S)
    assert m, "下拉框 #top_mb_settings 未渲染"
    return m.group(0)


def _mount_block(page):
    """圈定挂载点注入的配置块，避免 seen 断言被页面其他文本误满足。"""
    m = re.search(r"window\.MagicbookOnboarding = \{(.*?)\n  \};", page, re.S)
    assert m, "MagicbookOnboarding 配置块未渲染"
    return m.group(1)


def _seen_of(page):
    m = re.search(r"seen: (\{.*?\}),", _mount_block(page), re.S)
    assert m, "MagicbookOnboarding.seen 种子未渲染"
    return json.loads(m.group(1))


def test_mount_present_once(settings_page):
    assert settings_page.count('css/onboarding.css') == 1
    assert settings_page.count('js/onboarding.js') == 1
    assert "window.MagicbookOnboarding" in settings_page
    # 样式在 <head>、脚本在 jQuery 之后：两者顺序错了会分别导致无样式 / $ 未定义
    assert settings_page.index("<head>") < settings_page.index("css/onboarding.css")
    assert settings_page.index("js/libs/jquery.min.js") < settings_page.index("js/onboarding.js")


def test_csrf_wiring_present(settings_page):
    """挂载点自带 csrf_token 隐藏域，且前端确实带 X-CSRFToken 头。

    Why: 测试环境 conftest 关了 CSRF（WTF_CSRF_ENABLED=False），所以这里只能锁「接线」
         而不是端到端校验；真实 CSRF 行为由本地浏览器实跑覆盖（见 R109 设计稿 §8）。
         顺带修的既有问题：无上传权限的页面上原本没有任何 csrf_token 输入，
         main.js 的 $.ajaxSetup 取到空值，写 /ajax/view 会静默 400。
    """
    assert 'name="csrf_token"' in settings_page
    js = open(JS_PATH, encoding="utf-8").read()
    assert "X-CSRFToken" in js
    assert "/ajax/view" in js


def test_seen_seed_false_for_fresh_user(tour_user):
    rv = tour_user.get("/reading/settings")
    assert rv.status_code == 200
    assert _seen_of(rv.data.decode("utf-8")) == {}


def test_seen_seed_reflects_view_settings(tour_user):
    """服务端状态是权威：写入 onboarding.main 后种子必须带过来（跨设备记忆的前提）。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    user.view_settings = {"onboarding": {"main": True, "reader": False}}
    ub.session.commit()

    rv = tour_user.get("/reading/settings")
    seen = _seen_of(rv.data.decode("utf-8"))
    assert seen.get("main") is True
    assert seen.get("reader") is False


def test_null_view_settings_renders(tour_user):
    """view_settings 为 NULL（老账号/列空）不能抛 UndefinedError。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    user.view_settings = None
    ub.session.commit()

    rv = tour_user.get("/reading/settings")
    assert rv.status_code == 200
    assert _seen_of(rv.data.decode("utf-8")) == {}


def test_anonymous_seed_is_marked_and_page_ok(client):
    """匿名（current_user 无 view_settings 属性）：页面必须正常渲染，
    且 anonymous:true 让前端知道只能用 localStorage，不能写共享的匿名用户行。"""
    rv = client.get("/login")
    assert rv.status_code == 200
    page = rv.data.decode("utf-8")
    assert "anonymous: true" in page
    assert _seen_of(page) == {}


def test_manual_entry_bilingual_and_role_scoped(settings_page):
    block = _dropdown_block(settings_page)
    assert 'id="top_onboarding"' in block
    # R112：走 Babel gettext，admin（locale=en）只见英文 msgid，双写不得回流
    assert "Onboarding Tour" in block
    assert "使用引导" not in block
    assert settings_page.count('id="top_onboarding"') == 1


def test_manual_entry_hidden_for_anonymous(client):
    rv = client.get("/login")
    assert "top_onboarding" not in rv.data.decode("utf-8")


def test_state_write_reuses_ajax_view_channel(tour_user):
    """锁住外部契约：/ajax/view 必须能落 onboarding 命名空间，否则「零 Python 改动」
    的前提消失（引导会在每台设备每次访问都重弹邀请卡）。"""
    page = tour_user.get("/reading/settings").data.decode("utf-8")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)

    rv = tour_user.post("/ajax/view",
                       data=json.dumps({"onboarding": {"main": True, "reader": True}}),
                       content_type="application/json",
                       headers={"X-CSRFToken": token})
    assert rv.status_code == 200

    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    ub.session.expire(user)
    assert user.view_settings["onboarding"] == {"main": True, "reader": True}


def test_reader_page_mounts_tour():
    """read.html 独立于 layout，必须自带挂载点（先例：ai_chat_panel.html 的 include）。"""
    with open(os.path.join(TEMPLATE_DIR, "read.html"), encoding="utf-8") as fh:
        src = fh.read()
    assert "onboarding_mount.html" in src
    # 必须在 jQuery 之后
    assert src.index("js/libs/jquery.min.js") < src.index("onboarding_mount.html")


def test_reader_step_anchors_exist_in_template():
    """导览步骤表指向的阅读器控件不得改名失联（尤其 AI 伴读入口）。"""
    with open(os.path.join(TEMPLATE_DIR, "read.html"), encoding="utf-8") as fh:
        src = fh.read()
    for anchor in ('id="show-Toc"', 'id="next"', 'id="setting"',
                   'id="immersive-translate"', 'id="bookmark"', 'id="fullscreen"'):
        assert anchor in src, "{0} 已从阅读器模板消失，需同步 onboarding.js".format(anchor)

    with open(os.path.join(TEMPLATE_DIR, "ai_chat_panel.html"), encoding="utf-8") as fh:
        assert 'id="ai-companion-fab"' in fh.read()


def test_browse_step_anchors_exist_in_templates():
    with open(os.path.join(TEMPLATE_DIR, "layout.html"), encoding="utf-8") as fh:
        src = fh.read()
    for anchor in ('id="query"', 'id="advanced_search"', 'id="scnd-nav"'):
        assert anchor in src, "{0} 已从 layout 消失，需同步 onboarding.js".format(anchor)

    # index.html 同时服务首页（discover）与各浏览页；封面与排序条是导览锚点
    with open(os.path.join(TEMPLATE_DIR, "index.html"), encoding="utf-8") as fh:
        src = fh.read()
    for anchor in ('class="col-sm-3 col-lg-2 col-xs-6 book session', 'class="filterheader'):
        assert anchor in src

    with open(os.path.join(TEMPLATE_DIR, "detail.html"), encoding="utf-8") as fh:
        src = fh.read()
    # 注意：这些锚点多数带角色/数据门控（#readbtn 需 role_viewer+role_admin、
    # 单格式书渲染 #Download 而非 #btnGroupDrop1、#shelf-actions 需已有书架权限），
    # 源码级存在只能保证「导览不会指到不存在的东西」，缺锚点时的降级由引擎跳过负责。
    for anchor in ('id="detailcover"', 'id="btnGroupDrop1"', 'id="Download"',
                   'id="shelf-actions"', 'id="have_read_cb"',
                   'id="read-in-browser"', 'id="readbtn"'):
        assert anchor in src


def test_centered_card_is_displayed_after_append():
    """Why: 浏览器实跑发现「导览完成」卡一直挂在 DOM 里却完全不可见——
    jQuery 3 的 .show() 对未插入文档的元素不生效（isHiddenWithinTree 要在树内判定），
    而 #onb-bubble 默认 display:none。居中路径必须先 append 再显式给 display。"""
    with open(JS_PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert 'append(centered.show())' not in src
    assert re.search(r'\$\("body"\)\.append\(centered\);\s*\n(\s*//[^\n]*\n)*\s*centered\.css\("display", "block"\)', src), \
        "居中卡需在入树后显式设 display，否则完成卡/窄屏卡不可见"


def test_bubble_is_positioned_against_the_hole():
    """Why: 高于视口的目标（侧栏导航）原始 rect 的 top 是负值，拿它定位会把气泡推到
    屏幕外。定位基准必须是 drawMask 与视口求交后的「洞」，且超高元素改为顶对齐滚动。"""
    with open(JS_PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert not re.search(r'\n\s*position\(bubble, rect\);', src), \
        "必须按「洞」定位，不能用目标原始 rect"
    assert src.count("position(bubble, hole)") + src.count('position($("#onb-bubble"), hole)') == 2
    assert 'block: tall ? "start" : "center"' in src


def test_step_class_is_replaced_not_accumulated():
    """Why: 实跑发现换步时旧的 onb-step-* 没被摘掉。CSS 靠 body.onb-step-ai
    放行 z-index 高于蒙层的 AI 悬浮球，残留会让它在后续步骤上继续盖住导览卡片。"""
    with open(JS_PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert "function clearStepClass()" in src
    # 加新步类之前必须先清旧类
    assert re.search(r'clearStepClass\(\);\s*\n\s*\$\("body"\)\.addClass\("onb-step-', src)


def test_scroll_listener_uses_capture_phase():
    """Why: caliBlur 主题下真正滚动的是 .col-sm-10（overflow:auto），scroll 不冒泡，
    挂在 window 上的普通监听收不到内部容器滚动——实跑时高亮洞钉在原地与目标脱钩。
    必须用捕获阶段监听。"""
    with open(JS_PATH, encoding="utf-8") as fh:
        src = fh.read()
    assert 'window.addEventListener("scroll", onViewportEvent, true)' in src
    assert 'resize.onboarding scroll.onboarding' not in src


def _js_code(text):
    """去掉注释后的 JS 文本：Why 注释里会复述被禁止的旧写法（`$("#onb-help")`），
    全文匹配会把「已经修好」判成「仍有缺陷」。只对 showReaderHelp 这类小函数体用。"""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(^|\s)//[^\n]*", "", text, flags=re.M)


def _reader_help_fn():
    """圈出 showReaderHelp 函数体：入口契约只该由它自己的代码满足，全文件匹配会被
    teardown 的 remove 选择器、CSS 选择器等无关文本误满足。"""
    with open(JS_PATH, encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"function showReaderHelp\(\) \{.*?\n  \}", src, re.S)
    assert m, "showReaderHelp 不存在"
    return _js_code(m.group(0))


def test_reader_help_entry_appended_exactly_once():
    """R113 线上事故：阅读器左下角常驻「?」点了没反应，强制刷新也无效。
    Why: 提交 71d126cb（R111，当时 onboarding.js 正被 R112 会话同文件并发改写）里
         showReaderHelp 的 append 出现两行逐字符相同的代码 → 页面有两个同位置按钮；
         `$("#onb-help")` 走 getElementById 只返回第一个节点，监听只绑到它，
         而 DOM 靠后的那个盖在上层接收全部点击 → 入口永久是死按钮。localStorage 不随
         强刷清空，所以「刷新也没用」正是这个状态的指纹。
    锁：入口节点在函数体内只追加一次（字符串建一次、append 两遍同样要抓到）。"""
    body = _reader_help_fn()
    assert "applyChromePalette" in body, "函数体切片失效（没圈到 showReaderHelp 全文）"
    assert 'id="onb-help"' in body, "常驻「?」入口未渲染"
    assert body.count('$("body").append(') == 1, \
        "常驻「?」被追加了多次：两个同位置按钮会让点击落到没有监听的那个"


def test_reader_help_handler_bound_to_created_node():
    """锁 R113 的失效机制本身：监听必须绑在建好的节点上，去重守卫必须查 DOM。
    Why: 靠 `$("#onb-help").on(...)` 反查 + `$("#onb-help").length` 守卫这一对写法，
         在出现重复节点时既是失效原因（只绑第一个）又是失效帮凶（守卫数出 1 个，
         以为已经存在）。绑节点 + getElementById 让重复追加最多是「两个都能点」，
         而不是「两个都点不动」。"""
    body = _reader_help_fn()
    assert 'document.getElementById("onb-help")' in body, "去重守卫要查 DOM，别用 jQuery ID 选择器"
    assert '$("#onb-help")' not in body, "不要再按 #id 反查入口节点"
    assert re.search(r'help\.on\("click",.*?\n\s*\$\("body"\)\.append\(help\);', body, re.S), \
        "监听要在 append 之前绑到 help 节点本身"


def _mb_i18n(page):
    """解析 i18n_seed.html 注入的 MB_I18N 字典（tojson 会把中文转义，全文匹配不可靠）。"""
    m = re.search(r"window\.MB_I18N = (\{.*?\});\n\s*window\.mbT", page, re.S)
    assert m, "MB_I18N 种子未渲染"
    return json.loads(m.group(1))


def test_i18n_seed_mounted_once_and_localizes(app, admin_client):
    """R112 US2: layout 页注入 window.MB_I18N（只一次），en 账号取词回 msgid 本身。"""
    rv = admin_client.get("/reading/settings")
    page = rv.data.decode("utf-8")
    assert page.count("window.MB_I18N = ") == 1
    assert "window.mbT" in page
    d = _mb_i18n(page)
    assert d["Skip"] == "Skip"


def test_i18n_seed_renders_chinese_for_zh_user(app):
    """zh_Hans_CN 用户拿到的 MB_I18N 值是中文译文（po 链路生效），且不再双写。"""
    from werkzeug.security import generate_password_hash
    user = ub.session.query(ub.User).filter(ub.User.name == "zh-seed-tester").first()
    if user is None:
        user = ub.User(name="zh-seed-tester", email="zhseed@example.com",
                       password=generate_password_hash("zhseed-pass"))
        ub.session.add(user)
        ub.session.commit()
    user.locale = "zh_Hans_CN"
    ub.session.commit()

    client = app.test_client()
    rv = client.post("/login", data={"username": "zh-seed-tester", "password": "zhseed-pass"})
    assert rv.status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    page = client.get("/reading/settings").data.decode("utf-8")
    d = _mb_i18n(page)
    assert d["Skip"] == "跳过"
    assert d["Start Tour"] == "开始引导"
    assert d["Book wall"] == "书墙"
    # 尾点这条曾出现「字典 key 带句点、_() 实参不带」的不一致：值非空但是英文，
    # 遍历断言查不出来，故逐字比对（同缺陷类由 test_i18n_seed_contract 从源码侧锁死）
    assert d["Tap the “?” at the bottom-left any time to replay the tour."] == (
        "想重看随时点左下角的「?」。")
    # 含 \n / 引号转义的长词条走运行时比对（源码转义形态不可靠）
    for key, val in d.items():
        assert val, f"词条 {key!r} 翻译为空"
    assert d["Whole-book translation submitted\nTotal paragraphs: {total}\nCached: {cached}\n"
            "Newly published: {published}\n\nTranslations are generated in the background "
            "paragraph by paragraph and appear automatically while reading."] == (
        "整本翻译已提交\n总段落：{total}\n已缓存：{cached}\n新发布：{published}\n\n"
        "译文会在后台逐段生成，完成后阅读时自动显示。")
    assert d['(No long-term memories yet — say "remember…" in the chat or add one below)'] == (
        "（暂无长期记忆——对话里说「记住…」或在下方面板手动添加）")
    assert d["Delete this memory?"] == "删除这条记忆？"

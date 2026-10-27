"""R212 品牌一致性守卫：站内字样、图标资产与中文词条三者不许各走各的。

Why: 「把 Calibre-Web 收敛成 magicbook」这类改动有三个各自静默失效的面——
① 只改模板漏了 Python 侧的 `_(...)`（管理面板 flash、注册欢迎邮件都是用户可见）；
② 改了 msgid 忘了同步 .po，gettext 按 msgid 匹配，中文用户直接退回英文，看起来像
   「翻译丢了」而不是「字样没收敛」（本仓 R112/R141 同一坑位）；
③ 顶栏徽章与 favicon 换了引用却没换文件，页面静默 404 只剩 alt 空白。
三条都能编译通过、都能启动，只有形制断言钉得住。

不改的部分（有意保留，逐条注明）：
- 文件头许可证注释 `This file is part of the Calibre-Web (...)`：上游署名，不得改。
- `log.*` / `print` 里的 Calibre-Web：ES 按文本检索排障，改了会断链（`app-log-magicbook`）。
- `stats.html` 的 "powered by Calibre-Web"：这是真实的上游归属声明，抹掉等于谎报来源。
- `cps/cli.py` 的 `--help` 文案与 `debug_info.py` 的压缩包文件名：面向运维的 CLI/文件名，
  不属站内观感面，改动收益低且会牵连脚本使用者。
"""
import gettext
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CPS = os.path.join(ROOT, "cps")
TEMPLATES = os.path.join(CPS, "templates")
BRAND_DIR = os.path.join(CPS, "static", "img", "brand")

# 上游归属声明所在文件（允许出现 Calibre-Web 字样）
TEMPLATE_ALLOWLIST = {"stats.html"}

# 本仓已收敛、且 zh 目录里有译文的词条：必须解析出中文，不得原样回吐英文
RENAMED_WITH_ZH = [
    "magicbook Instance is unconfigured, please contact your administrator",
    "Show magicbook Log: ",
    "magicbook Log: ",
    "Download magicbook Log",
    "magicbook eBook Catalog",
    "magicbook configuration updated",
    "This Email has been sent via magicbook.",
    "magicbook Test Email",
    "Get Started with magicbook",
    "Error on search for custom columns, please restart magicbook",
]


def _walk(dirpath, suffixes):
    for cur, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in ("libs", "node_modules")]
        for name in files:
            if name.endswith(suffixes):
                yield os.path.join(cur, name)


def test_no_brand_string_in_templates():
    offenders = []
    for path in _walk(TEMPLATES, (".html", ".xml")):
        if os.path.basename(path) in TEMPLATE_ALLOWLIST:
            continue
        with open(path, encoding="utf-8") as fh:
            for no, line in enumerate(fh, 1):
                if "Calibre-Web" in line and not line.strip().startswith("{#"):
                    offenders.append("%s:%d" % (os.path.relpath(path, ROOT), no))
    assert not offenders, "模板里仍有 Calibre-Web 字样: " + ", ".join(offenders)


def test_no_gettext_call_carries_upstream_brand():
    offenders = []
    for path in _walk(CPS, (".py",)):
        with open(path, encoding="utf-8") as fh:
            for no, line in enumerate(fh, 1):
                if "Calibre-Web" in line and re.search(r"\bN?_\(", line):
                    offenders.append("%s:%d" % (os.path.relpath(path, ROOT), no))
    assert not offenders, (
        "用户可见文案仍带 Calibre-Web（日志行与许可证头不在此列）: " + ", ".join(offenders))


def test_renamed_msgids_resolve_to_chinese():
    catalog = gettext.translation(
        "messages", os.path.join(CPS, "translations"), languages=["zh_Hans_CN"])
    untranslated = [k for k in RENAMED_WITH_ZH if catalog.gettext(k) == k or "magicbook" not in catalog.gettext(k)]
    assert not untranslated, (
        "这些词条改了 msgid 却没同步 .po/未重编 .mo，中文界面会退回英文: %s" % untranslated)


def test_brand_assets_are_wired_via_same_origin_proxy():
    """R212-B：顶栏徽章与 favicon 走同源代理 /brand/<name>（真源 MinIO），不再引仓内静态。

    钉三件事：① layout 引代理路由而非 static img/brand（换了引用却留着旧文件/旧路径会静默 404）；
    ② layout 不出现 MinIO 字面源——一旦直链就同时推翻 img-src 守卫并 reintroduce 扩展裂图；
    ③ 代理白名单含 favicon.png 且顶栏 CSS 定位规则仍在。
    """
    layout = open(os.path.join(TEMPLATES, "layout.html"), encoding="utf-8").read()
    assert layout.count("url_for('web.brand_asset', name='favicon.png')") >= 2, (
        "favicon 与顶栏徽章都应引同源代理 web.brand_asset")
    assert "img/brand/" not in layout, "layout 仍引用已删除的仓内静态 img/brand/"
    assert "minio.haoshenqi.top" not in layout, "layout 不得直链 MinIO（CSP 守卫与扩展裂图）"
    assert not os.path.isfile(os.path.join(BRAND_DIR, "logo.png")), "仓内静态品牌图应已移除"
    brand = open(os.path.join(CPS, "routes", "brand.py"), encoding="utf-8").read()
    assert '"favicon.png"' in brand and "BRAND_OBJECTS" in brand, "代理白名单形态变了，本守卫需随之更新"
    style = open(os.path.join(CPS, "static", "css", "style.css"), encoding="utf-8").read()
    assert ".navbar-brand .brand-mark" in style, "顶栏徽章缺 CSS 定位规则（会掉成块级换行）"


def test_site_title_default_is_not_upstream_brand():
    config_sql = open(os.path.join(CPS, "config_sql.py"), encoding="utf-8").read()
    m = re.search(r"config_calibre_web_title = Column\(String, default='([^']*)'\)", config_sql)
    assert m, "config_calibre_web_title 默认值形态变了，本守卫需随之更新"
    assert m.group(1) == "magicbook", "新库首启顶栏仍会显示上游品牌: " + m.group(1)

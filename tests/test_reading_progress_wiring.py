"""R213-B：EPUB / PDF / TXT 接入账号级阅读位置的「接线面」守卫。

Why 用静态断言而不是端到端渲染：readpdf.html 是完整 pdf.js viewer 页面
（530+ 行 vendored 结构），走 Flask 路由渲染需要整库书桩 + 登录态 +
viewer 权限，性价比低；而这些接线点一旦回退（比如有人升级 viewer 模板时
顺手删掉内联脚本），端到端也难在 CI 发现——文本面守卫足够钉住「接没接」。
真正的行为契约由 test_reading_progress.py 的端点/取数用例钉住。

开关关闭时，上述接线必须随 reading_progress_enabled 一并消失：
  - EPUB 不加载 reader-progress.js、不注入服务端位置（本地 localStorage 仍在 epub.js）；
  - PDF 不拼 #page、不挂 pagechanging、不加载 reader-progress.js；
  - TXT 不注入位置、不加载 reader-progress.js，回到改造前行为。
"""

from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parent.parent / "cps" / "templates"
_JS = Path(__file__).resolve().parent.parent / "cps" / "static" / "js" / "reading"


def test_pdf_template_wires_progress_reporting():
    html = (_TEMPLATES / "readpdf.html").read_text(encoding="utf-8")
    assert "{% if reading_progress_enabled %}" in html
    assert "js/reading/reader-progress.js" in html, (
        "PDF 阅读器未加载 reader-progress.js：页码采集链路断"
    )
    assert "pagechanging" in html, (
        "PDF 阅读器未挂 eventBus 的 pagechanging：viewer.js 是 vendored 文件"
        "不能改，事件口是唯一的取页途径"
    )
    assert "app.page" in html, "取当前页代码缺失（app = window.PDFViewerApplication）"


def test_pdf_template_restores_via_page_fragment():
    html = (_TEMPLATES / "readpdf.html").read_text(encoding="utf-8")
    assert ("reading_progress_enabled and reading_position and "
            "reading_position.page_current") in html, (
        "defaultUrl 的 #page 片段未受总开关约束：关闭后仍会从服务端恢复页码"
    )
    assert "#page={{ reading_position.page_current }}" in html, (
        "defaultUrl 未拼 #page=N 片段：服务端记录的上次页码不会被恢复"
    )


def test_txt_template_injects_server_position():
    html = (_TEMPLATES / "readtxt.html").read_text(encoding="utf-8")
    assert "{% if current_user.is_authenticated and reading_progress_enabled %}" in html
    assert "js/reading/reader-progress.js" in html
    assert "readerPosition" in html, "TXT 阅读器未注入服务端位置，恢复无数据源"


def test_txt_reader_reports_position():
    js = (_JS / "txt_reader.js").read_text(encoding="utf-8")
    assert "ReaderProgress.update" in js, (
        "txt_reader.js 未上报位置：TXT 将退回到「没有任何进度记忆」的旧行为"
    )
    assert "goToPage" in js, "TXT 阅读器缺少按页恢复函数"


def test_epub_reader_still_wired():
    """回归守卫：EPUB 侧（本单首版已交付）的接线不被后续改动碰掉。"""
    js = (_JS / "epub.js").read_text(encoding="utf-8")
    assert "ReaderProgress.update" in js
    html = (_TEMPLATES / "read.html").read_text(encoding="utf-8")
    assert "{% if reading_progress_enabled %}" in html
    assert "js/reading/reader-progress.js" in html
    assert "readerPosition" in html


def test_progress_switch_guards_all_three_reader_templates():
    """B6：三个模板都必须由同一个 reading_progress_enabled 总开关控制。"""
    for name in ("read.html", "readtxt.html", "readpdf.html"):
        html = (_TEMPLATES / name).read_text(encoding="utf-8")
        assert "reading_progress_enabled" in html, "%s 未接总开关" % name

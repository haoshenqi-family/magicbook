"""R213-B：PDF / TXT 阅读器接入账号级阅读位置的「接线面」守卫。

Why 用静态断言而不是端到端渲染：readpdf.html 是完整 pdf.js viewer 页面
（530+ 行 vendored 结构），走 Flask 路由渲染需要整库书桩 + 登录态 +
viewer 权限，性价比低；而这些接线点一旦回退（比如有人升级 viewer 模板时
顺手删掉内联脚本），端到端也难在 CI 发现——文本面守卫足够钉住「接没接」。
真正的行为契约由 test_reading_progress.py 的端点/取数用例钉住。

PDF 侧的三个不可替代接线：
  1. reader-progress.js 被加载（采集/节流在那里面）
  2. `#page=N` 片段拼进 defaultUrl（viewer 原生恢复机制）
  3. `eventBus.on("pagechanging", ...)` 挂钩（vendored viewer.js 不能改，
     唯一合法的取页口就是这个事件）
TXT 侧的两个接线：
  1. reader-progress.js 被加载
  2. window.calibre.readerPosition 注入（txt_reader.js 的恢复数据源）
"""

from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parent.parent / "cps" / "templates"
_JS = Path(__file__).resolve().parent.parent / "cps" / "static" / "js" / "reading"


def test_pdf_template_wires_progress_reporting():
    html = (_TEMPLATES / "readpdf.html").read_text(encoding="utf-8")
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
    assert "#page={{ reading_position.page_current }}" in html, (
        "defaultUrl 未拼 #page=N 片段：服务端记录的上次页码不会被恢复"
    )


def test_txt_template_injects_server_position():
    html = (_TEMPLATES / "readtxt.html").read_text(encoding="utf-8")
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
    assert "js/reading/reader-progress.js" in html
    assert "readerPosition" in html

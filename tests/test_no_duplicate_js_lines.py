"""R113: 全仓自有静态 JS 的「相邻同文代码行」结构守卫。

Why: 线上「阅读器常驻 ? 点了没反应」的根因，是提交 71d126cb 里并排两行逐字符相同的
     `$("body").append('<button id="onb-help" ...>')`。这类并行会话的合并残留 `node --check`
     不报错、模板测试看不见、人眼 review 也容易漏（当时的去重守卫 `$("#onb-help").length`
     同样只数到 1，等于一起失效）。本项目这是常态风险——多个会话经常同改一批前端文件。
     tests/test_onboarding_tour.py 里的函数体断言只护得住 showReaderHelp 一个函数，
     这条护整个 cps/static/js。
范围只放 JS：模板与 CSS 里合法相邻重复太多（layout.html 的三行 `.icon-bar`、成对的
`{% endif %}`），白名单成本高于收益。
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_DIR = os.path.join(ROOT, "cps", "static", "js")
MIN_LEN = 20  # 短行（}); / break; / }）重复是正常代码形状，不是合并残留

# 上游 Calibre-Web 自带的既有重复，逐条注明为什么可以留
WHITELIST = {
    # 幂等：第二次 .remove() 选到的集合已空，等价于没执行；上游代码，不属我们的改动面
    ("cps/static/js/caliBlur.js", '$("#have_read_form").next("p").remove();'),
}


def _code_lines(path):
    """逐行取「有效代码行」，丢掉空行与纯注释行。

    Why: 合并残留常长成「代码 / 注释 / 同样的代码」——只比相邻的原始行会漏掉这一种，
    而带注释的形态恰恰是 Edit 工具在文件被并发改写后最容易产生的。
    """
    out = []
    with open(path, encoding="utf-8") as fh:
        for no, line in enumerate(fh, 1):
            text = line.strip()
            if not text or text.startswith("//") or text.startswith("/*") or text.startswith("*"):
                continue
            out.append((no, text))
    return out


def _own_js_files():
    for root, dirs, files in os.walk(JS_DIR):
        dirs[:] = [d for d in dirs if d != "libs"]  # 第三方库不在审查范围
        for name in sorted(files):
            if name.endswith(".js") and ".min." not in name:
                yield os.path.join(root, name)


def test_no_duplicated_adjacent_code_lines_in_own_js():
    offenders = []
    for path in sorted(_own_js_files()):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        lines = _code_lines(path)
        for i in range(1, len(lines)):
            text = lines[i][1]
            if len(text) < MIN_LEN or text != lines[i - 1][1]:
                continue
            if (rel, text) in WHITELIST:
                continue
            offenders.append("%s:%d-%d: %s" % (rel, lines[i - 1][0], lines[i][0], text[:90]))
    assert not offenders, (
        "出现逐字符相同的相邻代码行（并行会话合并残留的典型指纹）。"
        "确实是有意重复就把它加进 WHITELIST 并写明为什么无害：\n" + "\n".join(offenders)
    )

"""R263 朗读速度选项的静态契约锁。

Why 静态锁：三条播放链路（TED/博客类原声、整本 TTS 连播、单段朗读）各自在
「new Audio 之后」套 playbackRate，node --check 与「调用面 ⊆ 导出面」都看不见
「某一处漏套」——表现是用户切了 0.5x 某条链路仍是常速（静默不一致）。本锁把
「每个 new Audio 的链路都跟一句 applyTtsSpeed」钉在源码文本上。
"""

import re

from tests.reader_js_modules import reader_source


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_read_html_有语速按钮且跟随朗读组():
    html = _read("cps/templates/read.html")
    m = re.search(r'<a id="tts-speed"[^>]*>.*?</a>', html, re.S)
    assert m, "read.html 缺少 #tts-speed 语速按钮"
    assert 'Reading speed' in m.group(0), "按钮 title/label 必须走 i18n（msgid Reading speed）"
    # R263 修订：语速默认隐藏，起播才随「停止」一起出现（用户验收意见①）
    assert 'style="display:none"' in m.group(0), "语速按钮必须默认 display:none"
    # 位置钉在朗读组内（#tts-book-stop 之后、#bookmark 之前），窄屏折叠才不会把它孤立
    stop_pos = html.find('id="tts-book-stop"')
    speed_pos = html.find('id="tts-speed"')
    bookmark_pos = html.find('id="bookmark"')
    assert stop_pos < speed_pos < bookmark_pos
    # R263 修订（用户验收意见②）：朗读/停止/语速包进同一分组容器
    # 闭合标签锚定行首（懒匹配会被内层 tb-icon 的 </span> 截住）
    group = re.search(r'<span id="tts-group" class="tb-group">(.*?)\n\s*</span>', html, re.S)
    assert group, "朗读组容器 #tts-group 缺失"
    for anchor in ('id="tts-book"', 'id="tts-book-stop"', 'id="tts-speed"'):
        assert anchor in group.group(1), "{0} 必须在朗读分组容器内".format(anchor)


def test_语速按钮随播放态显隐():
    js = reader_source("reader-tts.js")
    # ttsButtonsRender 同时管两个播放器的按钮渲染，语速必须与停止同进退：
    # 无播放态（st 为空）隐藏、有播放态显示——TED 原声与整本连播两条链路共用本函数
    assert "if (speedBtn) speedBtn.style.display = 'none';" in js, "停止播放时语速必须收起"
    assert "if (speedBtn) speedBtn.style.display = '';" in js, "起播时语速必须出现"


def test_reader_core_档位与变速参数():
    js = reader_source("reader-core.js")
    assert 'TTS_SPEED_STEPS = [1, 0.75, 0.5]' in js, "三档 1.0/0.75/0.5 缺一不可"
    assert 'calibre.reader.ttsSpeed' in js, "localStorage 键与 TTS_ENGINE_KEY 命名族保持一致"
    assert 'audio.playbackRate = ttsSpeed()' in js
    # preservesPitch 显式钉住：变速不变调；Safari 旧版走 webkitPreservesPitch
    assert 'audio.preservesPitch = true' in js
    assert 'audio.webkitPreservesPitch = true' in js
    # 档位白名单校验：脏值（手改 localStorage）必须回落 1，不得把任意数值喂给 playbackRate
    assert 'TTS_SPEED_STEPS.indexOf(value) >= 0 ? value : 1' in js


def test_每条播放链路的new_Audio后都套速():
    tts = reader_source("reader-tts.js")
    ted = reader_source("reader-ted-audio.js")
    # 单段朗读（activeTts）、整本连播每块（startAudio）：两处 new Audio 都必须跟套速
    assert tts.count("new Audio(") == 2, "reader-tts.js 的 new Audio 形制变了，本锁需同步演进"
    assert "RC.applyTtsSpeed(audio); // R263" in tts, "单段朗读链路漏套速"
    assert "RC.applyTtsSpeed(audio); // R263 语速档位：每块新建" in tts, "整本连播块链路漏套速"
    # TED/博客类整段原声（用户点名的初学者主场景）
    assert "RC.applyTtsSpeed(audio); // R263 语速档位：TED/博客类" in ted
    # 浏览器兜底链路：utterance.rate 乘档位（SpeechSynthesisUtterance 无 playbackRate）
    assert "utterance.rate = 0.95 * RC.ttsSpeed()" in tts


def test_切档即时生效的接线完整():
    # 按钮点击 → cycleTtsSpeed → 推给两条在播链路；链路各自的 applyTtsSpeedToActive 必须存在且被导出
    ri = reader_source("reader-immersive.js")
    assert "RC.cycleTtsSpeed()" in ri
    assert "host.applyTtsSpeedToActive()" in ri
    epub = _read("cps/static/js/reading/epub.js")
    assert "RTTS.applyTtsSpeedToActive()" in epub and "RT.applyTtsSpeedToActive()" in epub, \
        "装配层必须把新档位同时推给 TTS 与 TED 原声两条链路"
    # 模块导出面（「调用面 ⊆ 导出面」锁只查已发生的调用，这里正向锁导出必须存在）
    assert "applyTtsSpeedToActive: applyTtsSpeedToActive" in reader_source("reader-tts.js")
    assert "applyTtsSpeedToActive: function () { RC.applyTtsSpeed(tedAudioPlayer" in reader_source("reader-ted-audio.js")


def test_无播放能力时语速按钮一并隐藏():
    ted = reader_source("reader-ted-audio.js")
    m = re.search(r"btn\.style\.display = 'none';\n(.*?)\n    \}", ted, re.S)
    assert m and "tts-speed" in m.group(1), \
        "原声与 TTS 回落都不可用时，#tts-speed 必须随 #tts-book 一并隐藏"


# ---------- R263 修订轮：顶栏收纳（用户验收意见②③） ----------

def test_书签与整本翻译常驻更多菜单():
    tb = _read("cps/static/js/reading/reader-toolbar.js")
    # 常驻菜单清单：书签（自动进度后冗余）与整本翻译（低频管理项）任何宽度不进顶栏
    assert 'MENU_ALWAYS = ["bookmark", "whole-book-translate"]' in tb
    assert 'MENU_NARROW_ONLY = ["setting", "fullscreen"]' in tb
    # 宽屏分支必须把常驻项放进菜单（不落于「只处理窄屏」的旧行为）
    assert "toBar(MENU_NARROW_ONLY);" in tb and "toMenu(MENU_ALWAYS);" in tb
    css = _read("cps/static/css/reader.css")
    # 「更多」按钮常显：宽屏也要有菜单入口（旧规则是窄屏才 display:inline-flex）
    assert ".reader-main #titlebar a.tb-more { display: inline-flex; min-width: 44px; }" in css


def test_朗读组分段样式存在():
    css = _read("cps/static/css/reader.css")
    assert ".reader-main #titlebar .tb-group" in css, "分组容器缺少样式"
    assert "a.tb-tool + a.tb-tool" in css, "分组内分隔线（相邻兄弟选择器）缺失"


def test_导览不再锚定书签():
    ob = _read("cps/static/js/onboarding.js")
    assert 'sel: "#bookmark"' not in ob, "书签已收进更多菜单，导览步骤须同步撤除"

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
    # 位置钉在朗读组内（#tts-book-stop 之后、#bookmark 之前），窄屏折叠才不会把它孤立
    stop_pos = html.find('id="tts-book-stop"')
    speed_pos = html.find('id="tts-speed"')
    bookmark_pos = html.find('id="bookmark"')
    assert stop_pos < speed_pos < bookmark_pos


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

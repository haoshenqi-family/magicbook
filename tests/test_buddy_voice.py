"""R227 Buddy 语音能力守卫：复用口语陪练的录音/转写链路 + 每条回复手动朗读。

为什么是源码断言而不是只跑页面：这一轮的三个失效模式都不会让页面报错——
(1) 麦克风没挂上（learning-voice.js 未随面板载入 / 仍硬依赖学习中枢）→ 用户只会觉得「点了没反应」；
(2) 朗读不走带 bookName 的端点 → 把 AI 回复永久写进「书籍段落」缓存并重复计费；
(3) 新文案走 t() 取词但词条没进种子/PO/MO → 中文用户拿到英文，且没有任何报错。
三者都只能在源码/词表层锁住。
"""
import gettext
import os
import re

from babel.messages.pofile import read_po

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, "cps", "templates", "ai_chat_panel.html")
CHAT_JS = os.path.join(ROOT, "cps", "static", "js", "ai_chat.js")
VOICE_JS = os.path.join(ROOT, "cps", "static", "js", "learning-voice.js")
SEED = os.path.join(ROOT, "cps", "templates", "i18n_seed.html")
PO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.po")
MO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.mo")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_panel_mounts_mic_and_voice_module(admin_client):
    """面板必须带麦克风与状态行，且 learning-voice.js 先于 ai_chat.js 载入。

    顺序是硬约束：ai_chat.js 在 init() 里读 window.MBLearningVoice，晚载入就是
    「按钮在、点了没反应」——这类静默失效只能靠顺序断言锁住。
    """
    body = admin_client.get("/buddy").data.decode("utf-8")
    assert 'id="ai-chat-mic"' in body
    assert 'class="sw-mic-label"' in body, "learning-voice 按 .sw-mic-label 读/复位文案"
    assert 'id="ai-chat-voice-status"' in body
    assert body.index("js/learning-voice.js") < body.index("js/ai_chat.js")


def test_voice_module_no_longer_requires_learning_hub():
    """录音模块已解耦：不再因缺 window.MBLearning 直接 return。

    Buddy 面板全站挂载（layout.html），那里没有 learning-common.js；保留旧
    `if (!MB) return;` 就等于「阅读页与站内页的麦克风静默失效」。
    """
    src = _read(VOICE_JS)
    assert "if (!MB) return" not in src.replace("if (!MB) return;", ""), \
        "learning-voice.js 不得再硬依赖 window.MBLearning"
    assert "window.MBLearning || {}" in src
    assert "window.MBApi.csrfToken" in src, "CSRF 必须回退到全站 common/api.js"
    assert "/ajax/learning/asr/transcribe" in src, "缺省转写地址要能独立成立"


def _function_body(src, name):
    """截取 `function <name>` 到下一个同级函数声明之间的源码（够做字面量断言）。"""
    start = src.index("function " + name)
    rest = src[start + 1:]
    nxt = re.search(r"\n  function ", rest)
    return src[start:] if not nxt else src[start:start + 1 + nxt.start()]


def test_voice_input_fills_textarea_instead_of_sending():
    """转写结果只填输入框（可编辑确认），不得自动发送——与口语陪练的「发送前检查」同口径。"""
    body = _function_body(_read(CHAT_JS), "initVoiceInput")
    assert "onRecording" in body
    assert "$input.val(" in body
    assert "sendMessage" not in body, "语音转写不得绕过用户确认直接发送"
    assert "/ajax/learning/asr/transcribe" in body


def test_read_aloud_uses_temporary_audio_without_book_context():
    """朗读必须走 /ajax/reading-tts 且不带 bookName/chapter。

    带上书籍上下文，moon-well 会把这段 AI 回复当「书籍段落」永久缓存；
    AI 回复是一次性的，落永久档既污染缓存也浪费空间（tts L2 的缓存分级口径）。
    """
    src = _read(CHAT_JS)
    body = _function_body(src, "fetchSpeechBytes")
    assert '"/ajax/reading-tts"' in src
    assert "/ajax/reading-tts-cached" not in body, "计费端点只用于「听=消费」，缓存回读另走一条"
    assert "bookName" not in body and "chapter" not in body
    assert "JSON.stringify({ text: text })" in body


def test_read_aloud_avoids_blob_media():
    """朗读不得用 URL.createObjectURL + <audio>：那需要 media-src blob: 全站放行。

    面板自 R220 起全站挂载，而 CSP 的 media-src 只在阅读页/口语页放行 blob:（窄面）。
    用 Web Audio 解字节（fetch 受 default-src 'self' 覆盖）才能在不动 CSP 的前提下全站可用。
    """
    src = _read(CHAT_JS)
    assert "createObjectURL" not in src
    assert "new Audio(" not in src
    assert "decodeAudioData" in src
    assert "AudioContext" in src


def test_speech_segments_stay_under_upstream_limit():
    """/tts/speak 单次 ≤2000 字（代理与 moon-well 双端校验），分段上限必须留余量。"""
    src = _read(CHAT_JS)
    m = re.search(r"SPEECH_SEGMENT_MAX\s*=\s*(\d+)", src)
    assert m, "分段上限常量缺失，长回复会撞 2000 字上限"
    assert 200 <= int(m.group(1)) < 2000


def test_new_voice_strings_are_seeded_and_translated():
    """t("…") 词条必须在种子 + PO + 编译后的 MO 里都有中文。

    Why 单独守 t()：ai_chat.js 的 mbT 在载入时被固定成恒等函数（i18n_seed 后置），
    本轮新增文案改走调用时取词 t()；生成器只扫 mbT 字面量，漏登记不会有任何报错。
    """
    src = _read(CHAT_JS)
    literals = set(re.findall(r"""(?<![\w.])t\(\s*(["'])((?:\\.|(?!\1).)*)\1""", src))
    literals = {raw for _, raw in literals}
    assert literals, "未抓到 t() 字面量，正则需同步更新"

    seed_src = _read(SEED)
    m = re.search(r"\{%\s*set\s+mb_i18n\s*=\s*(\{.*?\})\s*%\}", seed_src, re.S)
    assert m, "i18n_seed.html 的 mb_i18n 字典未找到"
    seeded = set(re.findall(r'"([^"\n]+)":\s*_\(', m.group(1)))

    missing = sorted(literals - seeded)
    assert not missing, "t() 词条不在 i18n_seed.html：%r" % missing

    with open(PO, "rb") as fh:
        catalog = read_po(fh)
    untranslated = sorted(msgid for msgid in literals
                          if not (catalog.get(msgid) and catalog.get(msgid).string))
    assert not untranslated, "t() 词条在 zh_Hans_CN po 里缺失或译文为空：%r" % untranslated

    with open(MO, "rb") as fh:
        mo = gettext.GNUTranslations(fh)
    still_english = sorted(msgid for msgid in literals if mo.gettext(msgid) == msgid)
    assert not still_english, "t() 词条在编译后的 .mo 里没有译文：%r" % still_english

"""cps/reading_tts — 整本朗读（TTS 预生成）批次模块（magicbook R166）。

书详情页一键为整本书预生成朗读音频：后台 daemon 串行逐段调 moon-well /tts/speak
（source=book-tts-batch 发起者计费通道）写永久缓存；完成后 R157 整本连播与单段
朗读全程毫秒级命中。段落提取口径 = 阅读器朗读口径（extractor，契约测试双锁）。
"""

from .service import WholeBookTtsService  # noqa: F401

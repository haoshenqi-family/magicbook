# reading 模块（阅读器）· 用户手册

## 能做什么

- **多格式阅读**：EPUB / PDF / TXT 在线阅读，进度记忆，回到上次位置。
- **划词查词（改由 MagicLens 扩展提供）**：2026-10-09 起阅读器不再内置划词翻译，选中单词或段落后的释义、发音、「认识 / 生词」标记、六板块单词详解（基本意思/词源/搭配·用法·习语/变体衍生/同反义词/俚语冷知识）统一在 [MagicLens 词镜](https://github.com/haoshenqi-family/magiclens) 浏览器扩展里完成，生词本与学习数据与本站互通。安装扩展后在本页正文里划词即可；未安装时阅读器不提供查词入口。
- **段落翻译**：鼠标移到段落上点「译」，译文直接显示在该段下方，再点一次收回。
- **段落 AI 批注**：段落旁「✨」生成背景/典故讲解。
- **朗读**：段落文字转语音朗读；同一段落重听零等待（音频按段落长期保留，不清理）。
- **整页 / 整本翻译**：当前页批量翻译；整本书翻译在书库发起，阅读器内查看进度。
- **新概念课级音频**：新概念英语书配套课级音频播放页（课文原文 + 音频同步）。

## 谁在用

站内读者的主要工作界面。

## 深入阅读

- L2 设计概要：[../reading/hld/hld.md](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/reading/hld/hld.md)（代理端点映射；后端契约权威在 moon-well）
- L3：[词汇测试前端与代理](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/vocab-size-test/design/) · [引导导览](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/onboarding-tour/design/) · [课级音频](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/nce-audio/design/) · [语言切换](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/language-i18n/design/)

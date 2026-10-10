# vocabulary 模块（词汇学习）· 用户手册

## 能做什么

- **生词自动判定**：阅读时按你的难度档位自动判断哪些词是你的生词；判定按屈折词族生效——标记任一词形即覆盖全族。波浪线由谁画是自动的：装了 MagicLens 且它的引擎在跑时由扩展画，否则阅读器自己画（两条同时出现的情况已被规避）。
- **认识 / 生词标记**：在划词气泡里一键标记（扩展的气泡或阅读器内置气泡都一样），标记立即生效并同步到生词本。
- **生词本**：自动收集阅读中遇到的生词，供学习与复习。
- **词汇量测试**：3-4 分钟自适应测试（词 + 纯英文例句，只答认识/不认识），给出词汇量估算、区间、各频段掌握度；结束后**推荐适合的阅读难度档位，一键应用**；历史成绩可回看。
- **难度档位**：0-9 十档（默认 CET4），影响生词判定密度，随时可改。

## 谁在用

「阅读设置」页的测试入口与档位设置在本站；划词查词、生词标记与网页上的生词高亮由 [MagicLens 词镜](https://github.com/haoshenqi-family/magiclens) 扩展承担（装了才接管，没装时阅读器自带同样的能力），两边共用同一份档位与生词本数据。

## 深入阅读

- L2 设计概要：[../vocabulary/hld/hld.md](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/vocabulary/hld/hld.md)
- L3：[词汇量测试（含前端与代理 US4）](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/vocab-size-test/design/vocab-size-test-lld.md)
- 后端契约权威：moon-well `docs/vocabulary/hld/hld.md`

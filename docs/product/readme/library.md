# library 模块（书库）· 用户手册

## 能做什么

- **书架**：浏览、搜索、按分类/标签筛选 Calibre 书库中的图书。
- **书籍详情**：元数据一览 + 内容速览——出版日期诚实标注（书目未标出版日时显示「导入于」）、语言按书目声明展示并标「双语」、难度阶标签（标签/书架/系列映射，未分级明示）；已加入的书架显示为可移除芯片；登录用户均可「在线阅读」（整本翻译/朗读/单词详解为管理员工具）。
- **上传与导入**：上传电子书入库（EPUB/PDF/TXT 等，自动解析）；Halo 站点的 Markdown 文章可经连接器一键成书（可同时触发整本翻译）。
- **下载与同步**：图书下载；OPDS 目录供电子书阅读器订阅；Kobo 设备同步。
- **元数据管理**：编辑书名、作者、封面、标签等元信息。
- **整本翻译**：对当前书一键发起整本翻译（按章节拆任务走后端队列，完成后阅读器内段落自动呈现译文；支持查看进度、取消、失败重试）。

## 谁在用

所有站内用户；OPDS/Kobo 面向外部阅读器设备。

## 深入阅读

- L2 接口说明：暂无（书库主体沿用 Calibre-Web 能力；整本翻译设计见历史归档）
- 历史设计（`docs/project/_legacy/feat/`）：[整本翻译设计](../../project/_legacy/feat/whole-book-translation/design/whole-book-translation-design.md) · [Halo 连接器](../../project/_legacy/feat/halo-book-connector/design/lld.md) · [fnOS 部署](../../project/_legacy/feat/magicbook-fnos/DEPLOY-FNOS.md)

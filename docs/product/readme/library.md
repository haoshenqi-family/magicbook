# library 模块（书库）· 用户手册

## 能做什么

- **书架**：浏览、搜索、按分类/标签筛选 Calibre 书库中的图书。
- **阅读难度入口**：书墙上方直接显示当前档位（如「3 - CET4」），点「修改」两步内进入偏好设置调整；档位决定阅读时哪些词被标为生词。
- **上传与导入**：上传电子书入库（EPUB/PDF/TXT 等，自动解析）；Halo 站点的 Markdown 文章可经连接器一键成书（可同时触发整本翻译）。
- **下载与同步**：图书下载；OPDS 目录供电子书阅读器订阅；Kobo 设备同步。
- **元数据管理**：编辑书名、作者、封面、标签等元信息。
- **整本翻译**：对当前书一键发起整本翻译（按章节拆任务走后端队列，完成后阅读器内段落自动呈现译文；支持查看进度、取消、失败重试）。

## 谁在用

所有站内用户；OPDS/Kobo 面向外部阅读器设备。

## 深入阅读

- L2 接口说明：暂无（书库主体沿用 Calibre-Web 能力；整本翻译设计见历史归档）
- 历史设计（`docs/project/_legacy/feat/`）：[整本翻译设计](../../project/_legacy/feat/whole-book-translation/design/whole-book-translation-design.md) · [Halo 连接器](../../project/_legacy/feat/halo-book-connector/design/lld.md) · [fnOS 部署](../../project/_legacy/feat/magicbook-fnos/DEPLOY-FNOS.md)

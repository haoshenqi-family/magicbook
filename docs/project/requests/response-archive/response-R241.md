## 2026-10-29（R241：整本能力缓存齐备标识——三项缓存都备齐时告诉读者「这本书学起来便宜」）

### R241（用户：「magicbook 增加一个功能，如果整本翻译，整本朗读，全文单词详解 都已经有缓存了，则每个都有一个特殊的标识，让用户知道这本书可以较为便宜的学习了。」）

- **任务定位**：需求（用户可见能力新增），单仓（magicbook）、moon-well 零改动、无新接口、无数据库迁移。
- **交付**：书籍详情页（含书卡点开的详情弹层）在难度标签之后给出缓存齐备信息——整本翻译 / 整本朗读 / 全文单词详解各一枚分项小标（哪项备齐亮哪项，悬停给出 `n/m` 与计费口径），三项齐备时追加「低成本学习」总标；整本任务面板的三个页签在对应缓存备齐时挂「已缓存」小标（同一份快照）。标识面向**普通读者**（`role_viewer()`），三个整本入口仍只给管理员（R214 拍板①不变）。
- **判定口径**：取本仓三条整本链路台账 `reading_translation_job` / `reading_tts_job` / `reading_word_detail_job`，要求 `status=COMPLETED` + 跑满（`completed_count/done_count/covered_words` 达到总量）+ `book_fingerprint` 与当前正文一致 + `book_format` 一致（SQL 侧 `lower()` 兜住大小写）；零上游调用、零 EPUB 解析。实现 `cps/reading_insight/readiness.py::book_readiness()`，`show_book` 注入 `entry.cache_readiness` 并复用速览 payload 已算好的指纹（不重复取书/stat）。
- **已知边界（已写入 LLD §3 / L3）**：① 不是实时探测，缓存被上游清掉会滞后；② 翻译与详解的 `COMPLETED` 依赖整本面板/批量进度页轮询时做缓存懒回收（R78 起不做常驻轮询），点完立刻关页面且之后不再打开的书会暂不亮标；③ 只认本仓发起过的整本批次；④ 归档书不亮标；⑤ 详解小标的计数是「本次补缺词数」，悬停改用全书去重词数表述。
- **测试**：新增 `tests/test_cache_readiness.py` **18 passed**（判定 15 条 + 面板真渲染 1 条 + 结构守卫 2 条）；定向回归 `test_book_detail_r214` / `r222` / `test_book_insight` / `test_i18n_seed_contract` / `test_job_service_base` / `test_reading_translation*` / `test_translate_all_r77` / `test_translate_concurrency_r78` / `test_word_detail_batch_r176` / `test_common_api_contract` 合计 **157 passed / 0 failed**。交叉审查（correctness reviewer）5 条发现已逐条处置：计数口径、归档书、重复取书/查询下推、大小写与未收敛边界补测。
- **文档**：LLD `docs/project/iterations/1.0/r241-cache-ready-badge/lld.md`（状态＝开发完成待验收）、L3 `docs/product/library/features/cache-ready-badge.md`（新建）、L1 `docs/product/readme/library.md`、需求基线 `docs/product/library/requirements.md` §R241、`docs/product/REQUIREMENTS.md` 变更记录、迭代 `plan.md`。
- **上线**：实现提交 `7d837dc8`，合并后 `f10d543d` 已推 `origin/develop`，fnOS 构建链自动部署（本次非纯文档 push）。**真机验收点**：找一本三项都跑满的书，详情页应出现「低成本学习」+ 三枚分项；只跑满一两项时只亮对应分项；普通读者账号可见、整本任务按钮仍仅管理员；从未跑过整本任务的书无标识且页面无报错。
- **worktree 驻留登记**：`../magicbook-r241-cache-ready-badge`（分支 `feat/r241-cache-ready-badge`，从 `origin/develop` 切出）按闸门保留待验收，验收通过后删除。
- **台账总结**：`requests.md` R241 已于开工时占号（`c16f1318`）；本条为 `response.md` 新增；同轮把最旧的 R230 一节原样搬入 `response-archive/response-R230.md` 维持 10 节窗口。

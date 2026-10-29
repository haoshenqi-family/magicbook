# R252 书籍详情展示整本朗读与翻译费用 · 验收标准

## A. 成本展示

- [x] **A1** 未缓存的书：详情页显示「完整翻译：约 N tokens · 全文生成原价 M 积分」
      与「完整朗读：约 N 字符（约 S 段） · 全文生成原价 M 积分」，不显示缓存成本。
- [x] **A2** 翻译已缓存：翻译行显示「缓存阅读 0 积分（全文生成原价 M 积分）」。
- [x] **A3** 朗读已缓存：朗读行显示「缓存收听 A 积分（全文生成原价 M 积分）」，
      `A = 已缓存段数 × 1`，并写明 TTS 不按 token 计费。
- [x] **A4** 翻译与朗读都已缓存：两行均按「缓存值（全文原价）」并列展示。
- [x] **A5** 费率不可得：仍显示 tokens / 字符 / 段数，积分写「费率暂不可得」，
      不显示 0 或猜测数字。
- [x] **A6** 旧速览快照没有去重字段时，页面正常回退，不报错。

## B. 可见性与性能

- [x] **B1** 已登录且有阅读权限的普通读者可见；三个整本入口仍仅管理员可见。
- [x] **B2** 完整详情页与书卡 XHR 详情弹层显示同一份成本摘要。
- [x] **B3** 打开详情页不触发整本翻译缓存查询、单词详解缓存检查或 TTS 逐段探针。
- [x] **B4** moon-well 费率端点故障时详情页仍在 2 秒级超时内正常渲染。
- [ ] **B5** 移动端两行摘要自然换行，不横向溢出。

## C. 回归

- [x] **C1** `/ajax/whole-book-estimate` 的翻译积分改为按实际 token 比例向上取整，
      与 R222 计费公式一致。
- [x] **C2** 整本翻译 / 朗读 / 详解的 start/status/retry/cancel 契约不变。
- [x] **C3** 缓存齐备标识、内容速览、归档书详情与进度条行为不回归。

## D. 本轮验证

- `tests/test_book_cost_summary.py`、`test_book_insight.py`、
  `test_whole_book_estimate.py`、`test_book_detail_r214.py`、
  `test_cache_readiness.py`、`test_reading_tts_service.py`：
  **118 passed / 0 failed**。
- 正式发布态全量：**1133 passed / 0 failed / 4 warnings**。
- `py_compile` 与 `git diff --check` 通过。

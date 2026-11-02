# 回应归档 · R130 节（正文实为 R190 回应）

> 2026-10-23 R209 写入触发轮转，原样搬移，正文未改写；节标题沿用原文件写法（标 R130，内容为 R190 的回复），不做更正。

## 2026-10-19（R130 LLM 队列监控面板：四区块实现）

### R190（用户：恢复历史写作任务、改完文稿后没有可点的「提交 AI」按钮，按钮显示「两稿已完成」）

- **根因（不是渲染缺陷）**：R168 的设计规则是「每任务初稿 + 修订稿两稿封顶」——moon-well 第三稿返回 `50513`，前端 `refreshSubmitButton` 在 `lastDraftNo >= 2` 时主动 `disabled`。用户恢复的正是已完成两稿的历史任务，所以编辑框能改、按钮不能点。用户拍板**放开两稿上限**（不是改成只读回看）。
- **前端改动**：`learning-writing.js` 删除 `done` 分支与 disable，交过稿后统一「提交修订稿」且始终可点（在途锁仍由 `busy()` 管）；提交后状态行统一为「第 N 稿已批改，可在上面改完再提交」；历史状态改为「已交第 N 稿 · 可继续修订」；一键续写固定指向最近一次写作并带稿状态（不再挑「<2 稿」）。模板按钮改「继续上次的写作」，批改面板提示补「修订次数不限」。
- **i18n**：`scripts/generate_i18n_seed.py` 追加 `Draft {{n}} reviewed · can keep revising`；`messages.po` 新增 3 条译文并 `pybabel compile` 重编 `.mo`。旧「两稿已完成」词条保留为未引用项（运行时不取）。
- **测试**：`pytest tests/test_learning_proxy.py tests/test_learning_pages_static.py tests/test_i18n_seed_contract.py` → **90 passed**；新增静态守卫 `test_writing_workshop_never_caps_draft_submissions`（禁止 `btn.disabled = done` / `lastDraftNo >= 2` / 「两稿已完成」回流）。
- **文档**：L1 `docs/product/readme/learning.md` 改为「修订次数不限」；LLD 落 `docs/project/iterations/2026-10-writing-unlimited/writing-unlimited/lld.md`（状态：开发中）。
- **收尾**：分支 `fix/r190-writing-unlimited`，merge 本地 `develop` **`67e8409e`**；合并并行 R130 后（merge `977636ee`）按用户指令 push `develop`，fnOS 构建 **END OK** + 部署 **SUCCESS**，容器 `Up (healthy)`；线上抽查 `https://magicbook.haoyuhang.top/static/js/learning-writing.js` 已无 `btn.disabled = done`、含 `can keep revising`（新状态机已生效）。worktree `../magicbook-r190-writing-unlimited` 留待验收后删除。跨仓依赖 moon-well R192（`revise` 稿号顺延）已于同一时段部署成功（`8dc8690`，active slot=blue）。
- **发布态全量闸门**：`pytest tests/` → **622 passed / 13 failed**。13 个失败全部在 `test_metadata_outbound.py`（`shutdown(cancel_futures)` 需 Python 3.9+，本机 3.8）与 `test_reading_tts_service.py`（`book file is unavailable` 缺本机书库 fixture），已在干净 `origin/develop` 基线（`d85ba8ba`）复现 **13 failed / 15 passed**，与本轮写作改动无关；本机无仓库要求的 `.venv`，故用系统 Python 3.8 跑，正式判据以 CI/容器环境为准。本轮改动的三个测试文件 **90 passed**。
- **总结**：requests.md 占号 R190；合并 origin/develop 时并行 R130 已轮转 R179，本条写入使窗口达 11，按「写入即检查」再搬最早一节 R180 至 `response-archive/response-R180.md` 并登记索引；冲突记录：与 R130 的 po/response 改动按并集合并，无撞号。
- **复测 503 说明（2026-10-21 15:40）**：用户提交修订稿收到 `learning b1: /learning/writing/revise service unavailable`。根因是回填文档的 push 触发第二次部署，moon-well 旧容器 graceful shutdown 中断了在途 revise（15:40:38），代理按连接异常返回 503。服务稳定后 moon-well 端已用系统身份端到端复验 generate → submit(1) → revise(2) → revise(3) 全部成功；前端无需改动，用户重试即可，历史草稿与批改均未丢失。该次确为部署停机窗口；**15:43 起的复发是另一因**——代理 90s 小于后端 LLM 150s 预算，见 R191。


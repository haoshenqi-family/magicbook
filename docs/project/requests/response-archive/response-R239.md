# 回应归档 · R239

> 2026-10-29 R250 / R252 合并后窗口达 11 节，原样搬移不改写。

## 2026-10-28（R239：全文单词详解预览屈折词覆盖漏算）

### R239（用户：「这个计算不对，完全没有考虑曲折变形。」）

- **结论先行**：用户判断正确。R238 的后台 worker 与页面轮询没有失败，错的是它读取的
  moon-well 覆盖率：`cachedLookupKeys()` 的 ES `_source` 只取 `forms.form`，把判定所需的
  `forms.type` 裁掉了，`books / children / going / beasts / witches / revolting` 等因此全部
  被列为缺失。扫描是全局词库视图，**所有含屈折形式的书都会高估待生成量**，不是 book 145 单书问题。
- **为什么详情面板是对的**：交互查词读完整文档，能按 `forms.type` 把 `books` 还原为 `book`；
  预览走全索引扫描，受另一条投影限制，两条链路口径分叉。详情面板显示“books 是 book 的三单”
  恰好证明缓存内容存在。
- **修复归属**：主责 moon-well R226，扫描同时投影 `forms.form` 与 `forms.type`。magicbook
  **零代码**：不复制屈折规则、不改 worker/快照/分批，也不新增生成调用。
- **快照边界**：READY 有 10 分钟 TTL；moon-well 部署后可能短暂显示旧数字。验收必须用
  `{book_id:145, book_format:"epub", force:true}` 强制刷新，再看 `missingSample` 与新计数。
  这不是再算错一次，而是既有快照尚未过期。
- **测试**：本仓无功能代码，保留预览链路定向回归
  `test_word_detail_batch_r176.py + test_job_service_base.py`：**56 passed / 0 failed**。
  上游修复的请求投影与七类屈折回归由 moon-well R226 的 54 例覆盖。
- **文档四问**：能力形态未变，L1 不改；契约补充 → L2 `vocabulary/interface.md` 的覆盖率权威；
  实现/边界 → L3 `vocabulary/features/word-detail-preview.md`；需求与本次实现 →
  `vocabulary/requirements.md` R239 与 `iterations/1.0/r239-word-detail-inflection/lld.md`。
  R238 LLD 只加“R226 后续修复”注记，不改写当时范围。
- **调用方经验沉淀**：L2 新增 §5.1“调用方使用清单”，L3 新增 §6“覆盖率消费规则”，
  明确本站只抽字面词且只信 `cached-check`；给出
  `原始去重词数 = cachedWords + targetWords + notWordLike` 的可复算关系，禁止用
  “原始词数 − cached”反推目标数，也禁止在前端复制屈折规则补救后端口径分叉。
- **驻留与闸门**：R239 占号 `463c2f4d`；worktree
  `../magicbook-r239-word-detail-inflection`（分支 `fix/r239-word-detail-inflection`）保留。
  R238 worktree `../magicbook-r238-word-detail-preview` 另待验收，未复用、未清理。
- **待验**：moon-well 上线后 force 刷新 book 145，确认六个代表词移出缺失样例，
  `cachedWords` 上升、`targetWords` 下降，预览仍不产生 token 费用。
- **冲突记录**：无撞号；与 moon-well R226 是同一缺陷的两仓记录，算法权威只在 moon-well。

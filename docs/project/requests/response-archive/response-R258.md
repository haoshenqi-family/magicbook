# 回应归档 · R258

## 2026-10-31（R258：设计方案五充值卡五段式 + 方案十已读三态口径）

### R258（用户拍板「方案五按照你的设计修改。方案十按你的设计开始」；方案二提问已答复）

- **方案五**：moon-well 套餐字段已结构化（credits/baseCredits/multiplier/price/promotionEndTimeEpochMs），renderPackages 纯前端重排五段式：价格大字→所得构成（内测 N 倍 = 基础额度，说人话）→活动倒计时→单一中文主按钮→单价辅助行（≈ 每万积分 ¥x，不足一万的测试档不显示）。formatCredits 口语化（≥1万→x 万积分）；pkg-name/pkg-base 独立行退场，R242 契约同步演进。
- **方案十（诊断+修正）**：生产 book_read_link 无脏数据（mbtester1031 零记录=「未读」口径成立；hsq/sunny 状态均为真实痕迹）——B4 确认系 R256 已修的 label 歧义，**无需数据修复**。诊断发现的真缺口：show_book 把三态压成布尔，「在读」（阅读器入口写 IN_PROGRESS，生产 10 本在状态）在详情页与未读无差别——修正为三态透出 + 「在读」label-info 标签；高级搜索三态同源不受影响；listenmp3 同款 checkbox 挂在无 read_status 的 entry 上属历史死状态，不夹带。
- **方案二（答复存档）**：专名判定四层过滤（形态统计/高频词表 top50k/Calibre 元数据强排除/LLM 批量复核兜底），不采用 spaCy NER 主路径；落点 R147 密度估算 tokenize（moon-well 侧），实施待拍板（LLD §3）。
- **测试**：新增 test_plan5_plan10_r258.py 9 用例；R242 契约演进 1 处。全量 **1237 passed / 0 failed**。
- **文档四问**：能力→credit L1 随验收回填；契约→无；实现/边界→`docs/project/iterations/1.0/r258-plan5-plan10/lld.md`。
- **状态与驻留**：**已 merge 待 push/待验收**。develop `d34c6968`；worktree `../magicbook-r258-plan5-plan10`（分支 `feat/r258-plan5-plan10`）保留；push 待用户拍板。
- **窗口与总结**：写入后 11 节，按「写入即检查」把最旧一节（R248）原样搬至 `response-archive/response-R248.md` 并登记索引，窗口恢复 10。冲突记录：无撞号。

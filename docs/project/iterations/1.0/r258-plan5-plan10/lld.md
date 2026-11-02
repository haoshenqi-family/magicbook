# LLD — R258 设计方案五（充值卡五段式）+ 方案十（已读三态口径）

> 状态：**开发中（待验收）**
> 工作项：R258 · 迭代 1.0
> 设计来源：[magicbook-产品设计方案-2026-10-30.md](../../../../../magicbook-产品设计方案-2026-10-30.md)（用户 2026-10-31 拍板方案五实施、方案十启动）

## 1. 方案五：充值卡五段式

**现状混乱**（体验报告 Q5）：「500万 积分内测 ×10 / 50万 积分 / ¥999.00 / Recharge Now」四层混排，倍率语义要读者自己算。

**数据前提**：moon-well `/credit/recharge/packages` 已透出结构化字段（`credits` 最终所得 / `baseCredits` 基础额度 / `multiplier` / `price` / `promotionEndTimeEpochMs`）——纯前端重排即可，无需后端改动。

**实现**（`credits.js renderPackages` 重排 + `credits.css` 层级）：

```
① 价格大字      ¥999.00                       （pkg-price 26px 加粗，提至卡首）
② 得到什么      500 万积分（内测 10 倍 = 50 万积分 基础额度）   （pkg-gain 加粗）
③ 活动说明      内测加赠，剩 62 天 23 小时       （pkg-promo，倒计时沿用）
④ 主按钮        立即充值                        （单一按钮，Recharge Now 词条已有）
⑤ 单价辅助行    ≈ 每万积分 ¥2.00               （pkg-unit-price 弱化灰字）
                （不足一万积分的测试档不显示单价）
```

- `formatCredits()`：≥1 万显示「x 万积分」（一位小数去尾零），否则千分位；积分数值口语化是旧卡可读性差的主因之一。
- `formatPricePerWan()`：自动算单价帮助比价；`credits < 10000` 的测试档跳过。
- 旧的 `pkg-name`（「500万 积分」标题行）与 `pkg-base`（划线行）不再渲染——标题信息已由「所得构成」完整承载；CSS 规则保留不删（R242 契约断言同步演进为「不再出现」）。
- i18n：新 msgid `Beta bonus ends in ` → 「内测加赠，剩 」进 seed（`t()` 字面量脚本扫不到，手动登记）+ po/mo。

## 2. 方案十：已读状态口径（诊断 + 修正）

**生产数据诊断结论（2026-10-31）**：
- `book_read_link` 无脏数据：新用户 mbtester1031（id=13）**零记录**（「未读=无记录」口径成立）；hsq 有 0/1/2 混合、sunny 2 条 IN_PROGRESS，均为真实操作痕迹。
- 写入路径健康：阅读器入口写 `STATUS_IN_PROGRESS`（reading.py:601）、toggle_read 写 FINISHED/UNREAD、Kobo 同步独立。
- **结论：体验报告 B4「所有书显示已读」确认系 label 歧义（R256 已修），状态数据与筛选口径本身健康，无需数据修复。**

**诊断发现的真缺口并修正**：「在读」被 UI 丢弃——`show_book` 把三态压成布尔（`read_book == STATUS_FINISHED`），阅读器写了 IN_PROGRESS 的书在详情页与未读无差别（生产 10 本书处于该状态）。

**实现**：
- `web.show_book`：`entry.read_status` 透出三态原值（0/1/2），另加 `read_status_finished` / `read_status_in_progress` 两个布尔供模板。
- `detail.html`：已读勾选；在读不勾选并显示「在读」标签（bootstrap `label-info` 现成类，UI 纪律不新造样式）；未读留空。
- `listenmp3.html` 的同款 checkbox 挂在无 read_status 的 entry 上（恒 false 的历史死状态），不在本次范围。
- 高级搜索三态筛选直接查表（search.py），与详情页同源，未受影响（守卫测试钉住）。

## 3. 方案二（专名判定）设计答复存档

四层过滤口径（用户 2026-10-31 已获答复，实施待拍板）：①形态统计（始终大写开头+出现≥2 次+句中位置）②高频词表 top50k ③Calibre 元数据强排除 ④LLM 批量复核兜底；不采用 spaCy NER 主路径（依赖重、首跑慢，且「排除专名出密度」不需 NER 精度）。落点在 R147 密度估算 tokenize 环节（moon-well 侧）。

## 4. 验证

- 新增 `tests/test_plan5_plan10_r258.py` 9 用例；契约演进 1 处（R242 `pkg-base` → 五段式构成行）。
- 全量 `pytest tests/`：**1237 passed / 0 failed**。

## 5. 文档四问

- 能力变了：充值卡信息层级重排、详情页「在读」可见——随验收回填 credit/readme L1。
- 契约变了：无对外 HTTP 契约变化。
- 实现/边界变了：本 LLD。
- 本次怎么实现：本文档；台账 R258。

# 整本费用预估（L3 实现说明）

> 建立：2026-10-29（R252）。读者是**要改书籍详情成本摘要的人**；
> 用户视角见 L1 [`product/readme/library.md`](../../readme/library.md)；
> 本次取舍见 LLD
> [`project/iterations/1.0/r252-book-cost-summary/lld.md`](../../../project/iterations/1.0/r252-book-cost-summary/lld.md)。

## 1. 它是什么

书籍详情页在「整本能力缓存齐备」标识之后显示两行固定摘要：

```text
完整翻译：约 N tokens · 缓存阅读 0 积分（全文生成原价约 M 积分）
完整朗读：约 N 字符（TTS 不按 token，约 S 段） · 缓存收听 A 积分（全文生成原价约 M 积分）
```

未缓存时省略「缓存…」片段，只显示全文生成原价。费率不可得时保留
tokens / 字符规模，积分写「费率暂不可得」。

## 2. 计费口径

| 链路 | 规模估算 | 全文生成原价 | 已缓存时 |
| --- | --- | --- | --- |
| 整本翻译 | `ceil(chars / 4)` tokens | `ceil(tokens × creditsPer1kToken / 1000)` | 缓存阅读 **0 积分**；同时保留全文原价 |
| 整本朗读 | 约 `chars` 字符，不按 token | `floor(chars / charsPerCredit)` | `已缓存段数 × 1 积分`；同时保留全文原价 |

`1 积分/段` 是 moon-well R213 的缓存收听规则，在本仓集中为
`cps/reading_insight/cost.py::TTS_CACHED_LISTEN_CREDITS`。token 与 TTS 费率
不镜像在 magicbook，统一读 moon-well `GET /credit/billing`：

- `creditsPer1kToken`
- `tts.enabled`
- `tts.charsPerCredit`

`tts.enabled=false` 是明确的免费状态，全文生成显示 0；响应缺少 `tts` 字段则是
费率不可得，必须显示未知，不能伪装成免费。

## 3. 数据流

1. `cps/reading_insight/parser.py::parse()` 在现有速览统计之外记录
   `billableParagraphCount` / `billableCharCount`。两者按规范化正文去重，
   与整本翻译/朗读台账的 `text_hash` 去重语义一致；不额外解析第二遍 EPUB。
2. `cps/web.py::show_book()` 复用 `entry.insight` 与 `entry.cache_readiness`，
   调用纯函数 `build_book_cost_summary()`；不调用 `find-translations`、
   `cached-check` 或 TTS 逐段缓存探针。
3. 费率沿用 `_credit_billing_rates()` 的 5 分钟进程缓存；详情页调用超时为
   2 秒，moon-well 故障只让积分暂缺，不拖垮详情页。
4. `cps/templates/detail.html` 在 `#book-cost-summary` 中渲染两行摘要；
   完整详情页与书卡 XHR 弹层消费同一个 `entry.book_cost_summary`。

旧 `book_insight` 快照没有去重字段时回退到 `charCount` / `paragraphCount`，
页面仍可显示，但重复段落可能让估算偏高；文件指纹变化触发速览重建后自动修正。

## 4. 缓存状态从哪来

缓存成本只认 `readiness.book_readiness()` 的三条本仓批次台账：

- 翻译：`translate.ready=true` → 缓存阅读 0 积分；
- 朗读：`tts.ready=true` → `tts.total × 1` 积分；
- `ready=false` 或查询失败 → 只显示全文生成原价，不声称“未缓存”。

这不是实时缓存探测。批次台账跑满但上游缓存后来被清掉时，摘要会滞后；
真正播放/翻译仍以 moon-well 缓存实况为准。逐段或逐词积累的缓存，只要没有
对应的整本完成批次，也不会被算成整本已缓存。

## 5. 边界

- **不是账单**：token 用字符数粗估，朗读字符量取内容速览的去重统计，
  与最终模型 token 或 TTS 精确分段可能有差异，所以页面使用「约」。
- **TTS 不按 token**：用户问“听完多少 token”时，页面必须明确改报字符量，
  不得复制翻译的 token 口径。
- **朗读缓存段数**：已缓存时使用 readiness 台账的精确 `total`；未缓存时
  只用于规模说明，不展示缓存收听费。
- **可见性**：已登录且有 `role_viewer()` 的读者可见；三个整本入口仍仅管理员。
- **失败降级**：费率接口异常、TTS 字段缺失、旧快照字段缺失都只降级对应片段，
  不得拦详情页，也不得把未知数字写成 0。
- **估算面板同步**：`/ajax/whole-book-estimate` 的翻译公式与这里一致，按
  R222 比例计费向上取整到 1 积分，不再“不足千按千”。

## 6. 修改时检查

1. 改 token 换算或 TTS 计费时，同时更新 `cost.py`、`service.py` 的估算公式与
   `tests/test_book_cost_summary.py`。
2. 新增缓存链路或改变 readiness 字段时，同步 `build_book_cost_summary()` 与
   本文件 §4，不要让页面猜缓存状态。
3. 改模板文案时保留「TTS 不按 token」与「缓存值（全文原价）」两个信息结构。
4. 任何新数据源都必须保持详情页零整本解析、零逐段缓存探针。

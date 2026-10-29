# LLD - R253 缓存翻译按 1 积分/缓存段计费

> 状态：**开发完成待验收**（2026-10-29；定向 57 passed / 0 failed）
> 工作项：R253 · 迭代 1.0 · 承接 R252 / moon-well R231
> 需求基线：[library requirements](../../../../product/library/requirements.md) · 验收：[acceptance.md](./ac/acceptance.md)

## 1. 目标

把书籍详情页成本摘要中的翻译缓存成本从 R252 的 `0` 改为：

```text
translate.cachedCredits = readiness.translate.total × 1
```

同时保持朗读缓存收听、全文生成原价、费率不可得降级与详情页零缓存探针边界不变。

## 2. 数据源与口径

| 字段 | 来源 | 口径 |
| --- | --- | --- |
| 翻译缓存段数 | `cache_readiness.translate.total` | 仅 `ready=true` 时计入 |
| 翻译缓存单价 | `TRANSLATION_CACHED_CREDITS_PER_SEGMENT` | 固定 1 积分/段，对应 moon-well R231 |
| 朗读缓存段数 | `cache_readiness.tts.total` | 仅 `ready=true` 时计入 |
| 朗读缓存单价 | `TTS_CACHED_LISTEN_CREDITS` | 固定 1 积分/段，对应 moon-well R213 |
| 全文翻译原价 | moon-well `/credit/billing` + `chars/4` | R222 token 公式，不与缓存费互相抵扣 |

翻译与朗读的段数分别取各自台账，不能用任一方的 `total` 代替另一方。

## 3. 实现

### 3.1 成本纯函数

`cps/reading_insight/cost.py::build_book_cost_summary()`：

```text
translate.cachedCredits = translate.total * 1  # ready=true
translate.cachedSegments = translate.total
translate.cachedPerSegment = 1

tts.cachedCredits = tts.total * 1              # ready=true
tts.cachedSegments = tts.total
tts.cachedPerSegment = 1
```

未缓存时对应 `cachedCredits = null`、`cachedSegments = 0`，页面只显示全文生成原价。

### 3.2 模板

详情页翻译行改为：

```text
完整翻译：约 N tokens · 缓存翻译 A 积分（全文生成原价约 M 积分）
```

整本翻译缓存标识的悬浮说明同步改为「命中缓存按 1 积分/段计」，避免同一页面出现两套口径。

### 3.3 不变项

- 不新增 HTTP 接口；
- 不实时调用 `find-translations`、`cached-check` 或 TTS 探针；
- 不改整本翻译任务的后台 token 计费；
- 不改 `readiness` 表结构或批次判定；
- 不改变全文生成原价公式与费率故障降级。

## 4. 边界

- **ready 才显示**：只有整本翻译批次跑满才展示缓存翻译费；逐段积累的缓存不被算作整本已缓存。
- **缓存不是账单**：页面展示 `total × 1` 是整本复用的估算，实际逐段交互以请求时缓存命中段数为准。
- **费率独立**：翻译缓存单价是产品固定规则，不依赖 moon-well `/credit/billing`；全文生成费率不可得时仍保留缓存翻译值。
- **段数隔离**：翻译通常按去重段落，朗读按 TTS 分段，数量可能不同；必须分别使用 `translate.total` 与 `tts.total`。
- **历史注记**：R252 LLD/AC 保留原文，只加 R253 取代注记。

## 5. 测试

`tests/test_book_cost_summary.py` 与 `tests/test_cache_readiness.py` 覆盖：

1. 翻译已缓存 = `translate.total × 1`；
2. 朗读已缓存 = `tts.total × 1`；
3. 翻译与朗读段数不同时各算各的；
4. 两者均缓存时并列展示缓存值与全文原价；
5. 费率不可得时仍显示缓存翻译值，全文生成显示暂不可得；
6. 详情页翻译缓存标识与成本行都写 1 积分/段。

## 6. 文档四问

- 能力变了：L1 `docs/product/readme/library.md` 改为缓存翻译 1 积分/段。
- 契约变了：无对外 HTTP 契约变化。
- 实现/边界变了：L3 `docs/product/library/features/book-cost-summary.md` 与 `cache-ready-badge.md`。
- 本次怎么实现：本 LLD 与同目录 AC。

# R252 书籍详情展示整本朗读与翻译费用 · LLD

> 状态：**开发完成待验收**
> 工作项：R252 · 迭代 1.0
> 用户原话：「书籍详情页写一下完整听完大概需要多少token，完整翻译完大概需要积分，如果已经缓存了就写缓存需要的积分加原始需要的积分，比如 【完整朗读预计花费1（100）积分】1是缓存 100是全文朗读预计。详情也写一下。」

## 1. 口径定案

用户同时提到了 token 与积分。两条整本链路的真实计费口径不同：

- 翻译按 token：moon-well 当前公式为 `ceil(tokens × creditsPer1kToken / 1000)`；
  本仓以 `chars / 4` 粗估 tokens。
- 朗读不按 token：全文生成按字符 `floor(chars / charsPerCredit)`；
  读者实际收听命中缓存时按 R213 口径 `1 积分/段`。

因此页面不把两者写成同一种“token 费用”，而是：

| 链路 | 长度 | 全文生成原价 | 已缓存时的当前成本 |
| --- | --- | --- | --- |
| 完整翻译 | 约 N tokens | M 积分 | 缓存阅读 0 积分 |
| 完整朗读 | N 字符（TTS 不按 token） | M 积分 | 缓存收听 1 积分/段 × 已缓存段数 |

展示格式为「缓存值（全文原价）」，与用户示例 `1（100）` 的信息结构一致，
但数字来自真实计费口径，不强行把整本朗读缓存总价写成 1。

## 2. 数据源

| 数据 | 来源 | 说明 |
| --- | --- | --- |
| 翻译 token 量 | `book_insight.payload_json` | 新增去重后 `billableCharCount`；旧快照缺失时回退 `charCount` |
| 朗读字符量 | 同上 | 详情页只做规模粗算，不重新解析 EPUB |
| 已缓存翻译段数 | `cache_readiness.translate` | 仅 `ready=true` 时展示缓存阅读成本 |
| 已缓存朗读段数 | `cache_readiness.tts` | 仅 `ready=true` 时展示缓存收听成本 |
| token/TTS 费率 | moon-well `/credit/billing` | 沿用 `_credit_billing_rates()` 的 5 分钟进程缓存 |
| TTS 缓存收听单价 | moon-well R213 固定规则 | `1 积分/段`；常量集中定义并注明来源 |

不调用 `find-translations`、`cached-check` 或逐段 TTS 探针。详情页不能因为展示成本而重新扫整本缓存。

## 3. 实现

### 3.1 内容速览补充去重规模

`cps/reading_insight/parser.py` 在现有统计之外增加：

- `billableParagraphCount`：按规范化正文去重后的段数；
- `billableCharCount`：去重后正文字符数。

旧 `book_insight` 快照没有这两个字段时，成本摘要回退到 `paragraphCount` / `charCount`，
不强制在详情页重建全部旧快照。

### 3.2 纯函数成本摘要

新增 `cps/reading_insight/cost.py::build_book_cost_summary(payload, readiness, rates)`：

```text
tokens = ceil(billableCharCount / 4)
translation.fullCredits = ceil(tokens * creditsPer1kToken / 1000)
translation.cachedCredits = 0                    # ready=true
tts.fullCredits = billableCharCount // charsPerCredit
tts.cachedCredits = tts.total * 1                # ready=true
```

返回字段：

```json
{
  "translate": {
    "tokens": 55324,
    "fullCredits": 553,
    "cachedCredits": 0,
    "cached": true
  },
  "tts": {
    "chars": 221296,
    "fullCredits": 4425,
    "cachedCredits": 1348,
    "cached": true,
    "segments": 1348
  }
}
```

费率不可得时保留 `tokens` / `chars` / `segments`，积分字段为 `null`，
模板显示「积分费率暂不可得」，不显示 0 或猜测值。TTS 关闭计费时全文生成显示 0，
但缓存收听仍按实际入口规则展示。

### 3.3 详情页注入

`cps/web.py::show_book` 在现有 `entry.insight` 与 `entry.cache_readiness` 之后调用成本摘要：

- 仅已登录、`role_viewer()` 且有 EPUB/KEPUB 速览数据时注入；
- 费率调用设置较短超时（2 秒），避免 moon-well 故障拖慢详情页；
- 任何异常只让成本摘要缺席并记 warning，不拦详情页；
- 因数据随 `entry` 下发，完整详情页与书卡 XHR 详情弹层使用同一份结果。

### 3.4 模板与样式

`detail.html` 在缓存齐备标识后渲染 `#book-cost-summary`：

- `完整翻译：约 N tokens · 缓存阅读 0 积分（全文生成原价 M 积分）`
- `完整朗读：约 N 字符（约 S 段） · 缓存收听 A 积分（全文生成原价 M 积分）`
- 未缓存时省略「缓存…」片段。

CSS 使用现有详情页排版语言，不新增图片或 JS，移动端允许自然换行。

### 3.5 整本任务面板公式同步

现有 `/ajax/whole-book-estimate` 的翻译公式仍是 R222 之前的“不足千按千”，
本轮回正为 `ceil(tokens × per1k / 1000)`，与积分流水一致。
面板字段、接口形制和 TTS 全 miss 上限逻辑不变。

## 4. 边界

- **不是实时缓存探测**：缓存成本只认本仓三条台账已跑满的状态；逐段/逐词积累的缓存不展示成本。
- **不是账单**：token 用 `chars / 4` 粗估，TTS 字符量来自速览去重口径，与最终流水可能有差异。
- **归档书**：沿用 R247/R241 的详情可见性；归档书能读取速览和台账时同样展示。
- **费率故障**：只隐藏积分数字，保留 token/字符规模；不得把费率不可得写成 0。
- **性能**：不解析第二遍 EPUB；成本摘要是纯函数；费率沿用 5 分钟缓存且 2 秒超时。

## 5. 测试

| 场景 | 断言 |
| --- | --- |
| 翻译未缓存 | 显示 token 与全文原价，不出现缓存阅读 |
| 翻译已缓存 | 显示缓存阅读 0 与全文原价 |
| 朗读未缓存 | 显示字符数与全文原价，不出现缓存收听 |
| 朗读已缓存 | 缓存收听 = 段数 × 1，并显示全文原价 |
| 翻译+朗读都已缓存 | 两行均采用「缓存值（全文原价）」 |
| 费率不可得 | 保留规模，积分显示不可得，不出现猜测 0 |
| TTS 关闭计费 | 全文生成 0，缓存收听仍按入口规则 |
| 旧速览快照 | 回退 `charCount` / `paragraphCount`，不报错 |
| 结构守卫 | 详情页包含两行摘要与缓存并列结构 |
| 回归 | 估算、readiness、详情、TTS 相关测试全绿 |

## 6. 文档四问

- 能力变了：L1 `docs/product/readme/library.md` 补详情页成本摘要。
- 契约变了：无对外 HTTP 契约变化。
- 实现/边界变了：新增 L3 `docs/product/library/features/book-cost-summary.md`。
- 本次怎么实现：本 LLD。

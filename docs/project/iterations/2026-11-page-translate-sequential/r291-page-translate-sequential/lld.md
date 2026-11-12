# R291 整页翻译排版修复 — LLD

状态：开发完成待验收（分支 `fix/r291-page-translate-sequential`，worktree `../magicbook-r291-page-translate-sequential`）

## 背景与实测证据（dev 环境，2026-11-11）

用户报障：点阅读器右上角「译」，排版出问题。Agent 以 `mbtester1030` 在 `dev-magicbook.haoshenqi.top/read/487/epub`（BBC: How are horses helping to heal humans?）实测复现：

| # | 现象 | 实测数据 |
| --- | --- | --- |
| 1 | 点后长时间无反馈 | 20 段请求（4 并发、单请求 10–18s），按钮转圈约 90s |
| 2 | 译文一次性插入后整章重排 | `body.scrollWidth` 2291 → 3215px，页边界整体后移，当前页从 6 段英文变成 3 段英文+译文 |
| 3 | 译文块被页边界切断 | 「I used to ride horses…」段译文 `getClientRects()` 分裂为 2 块：本页底（top 628–739）+ 下页顶（top 20–64） |
| 4 | 译文约 5s 自动消失、整章回弹 | `translationDisplaySecondsPer100` 默认 5（兼最小显示秒数）；插入约半分钟后仅剩 2 条错误块 |
| 5 | 关开关第三次重排 | 3677 → 2291 |

## 根因

1. **可见性判定拿错基准（主因）**：`isElementVisible` 用 `content.window.innerWidth` 当视口宽。epub.js default manager 把整章多栏排进一个 iframe——iframe 自身宽度=整章宽（实测 2310px），真正裁切是外层 `.epub-container`（462px）+ `.epub-view` 平移。判据恒真 → 全章 25 段全进队列、`< 20` 封顶截断章尾 5 段。
2. **译文块无 `break-inside: avoid`**：分栏流内普通 block，长译文被页边界碎片化。
3. **整页开关复用段落级 5s 自动隐藏**：与「开关开着就一直显示」语义冲突；顺序渲染下更糟（前段译文在后段翻出来之前就消失）。

## 拍板方案（2026-11-11 用户确认）

- **A 可见性**：新增 `visibleSliceFor(content)`——取 iframe 的 `frameElement.parentElement`（`.epub-view`）与 `frameEl.closest('.epub-container')` 的 `getBoundingClientRect()` 差值，得当前页在 iframe 坐标系里的水平区间；`isElementVisible` 改为与该区间求交。transform 与 scrollLeft 两种翻页机制下公式同形。区间拿不到时显式回退旧判据（宁退化旧行为、不静默翻零段）。段落清单在点击瞬间快照（现有遍历即文档序），含与视口相交的跨页段，不随插入后布局变化重算。**两段式**：扫描期零插入，缓存命中先收集、扫描完再统一落位——dev 验证轮实测：缓存命中若边扫边插，会把后面的段落推进当前页区间（末页一次点出 13 段、应 4 段），污染同一轮扫描的可见性判定；缓存命中与 `rendered` 回填也因此同样限定当前页（不再整章）。
- **渲染策略（取代 R226 的「全部返回后一次渲染」）**：严格按序逐段——`step()` 链式驱动，一段落位再发起下一段，**不并发**（用户明确不要二路并发）；结果到达即插入。理由：范围收窄到当前页（约 6 段）后，逐段小位移发生在阅读位置附近且随阅读节奏出现，优于 90s 空转后整章一次大跳；R226 当时的「二十次连续重排」正是整章范围下的产物。
- **C 整页常驻**：`insertTranslation` 增加 `persist` 形参；整页三来源（缓存命中、`rendered` 回填、按序落位）与整页错误块均 `persist=true`（`div._noHide` 标记，改配置重排计时时跳过）；关开关 `removeAllTranslations` 移除、换章随 DOM 重建消失。段落级「译」按钮路径不传 persist，5s 自动隐藏语义不变。
- **B 不跨页断裂**：`reader-core.js` 注入样式的 `.reading-translation` 规则追加 `break-inside:avoid;-webkit-column-break-inside:avoid`。超过整栏高的长译文浏览器忽略 avoid 照常断开，属可接受兜底。
- **脱附守卫**：按序落位前查 `finishedJob.el.isConnected`，换章/翻页导致脱附时只写缓存不插 DOM（旧批量路径此处 `el.parentNode.insertBefore` 直接 TypeError）。缓存每次落位重读重写（`loadTranslationCache` 取新对象），避免与划词气泡翻译的并发写互相覆盖。

## 改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/static/js/reading/reader-immersive.js` | 头注释补 R291 段；`insertTranslation` 加 persist；`rescheduleVisibleTranslations` 跳过 `_noHide`；新增 `visibleSliceFor`；`isElementVisible` 改签名吃 slice；`showTranslationError`/`translateSingleParagraph` 透传 persist；删 `runConcurrent`/`renderTranslationBatch`；`applyImmersiveTranslation` 重写为快照当前页（可见性前置 + 缓存命中收集后置的两段式）+ step 链按序落位；`restoreCachedTranslations` 改限当前页 + 两段式 |
| `cps/static/js/reading/reader-core.js` | `.reading-translation` 注入样式追加 `break-inside:avoid;-webkit-column-break-inside:avoid` |
| `tests/test_reader_r226_acceptance.py` | 「完成后一次渲染」断言按 R291 取代，收缩为「请求期不插占位 + 顶栏加载态」两条仍有效底线（文件头加取代标注） |
| `tests/test_reader_r291_page_translate.py` | 新增：可见性基准、按序无并发、常驻/段落级计时分界、break-inside 四组形制锁 |
| `docs/product/readme/reading.md`（L1） | 段落翻译/整页翻译两条描述改为「按序逐段显示 + 常驻」 |
| `docs/product/REQUIREMENTS.md` | 追加 R291 行 |

## 边界（不改的部分）

- 划词气泡翻译、段落级「译」按钮的 5s 自动隐藏语义不变；「整本译」走 `RS.startWholeBookTranslation`，不动。
- 不随翻页自动触发翻译（R226 拍板保留）：开关开着翻到新章不自动翻，需再点开关（关→开）。
- `rendered` 回填（`restoreCachedTranslations`）改限当前页：与「译文只随页出现」模型一致，也消除开书/翻章时整章回填的一次性大重排；时机仍挂 `rendered`+60ms，若初始定位尚未 settle，回填可能落在首页——错过不破坏排版，重开开关即正确。
- 翻页/换章后的在飞请求：脱附段只写缓存；若全部脱附，队列照常排空、加载态正常收尾。
- 后端 `reading-translate-batch` 接口契约不变（L2 无变化）；单段请求 10–18s 的网关时延不在本次范围。

## 验证

- 静态守卫：`pytest` 相关子集 42 passed（R291 新 4 例 + R226 收缩后 3 例 + R215/R183 模块面/R263/R287 既有锁）；`node --check` 两文件通过。
- 集成套件：`scan_magicbook_routes.py` 重扫无新路由；`guard.py` 三向对账全绿（magicbook 466 行、缺口 0）。
- 真机验证（dev 部署后）：见 response.md R291 条目。

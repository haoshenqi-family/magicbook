# US5 · 词汇量测试「细筛」前端：入口、前后对照与细档图（R154）

> 状态：开发完成，随 feat/r154-vocab-refine merge 进 develop（worktree 驻留待用户验收）
> 后端口径权威：moon-well `docs/feat/vocab-size-test/design/us4-refine-test.md`（R155）

## 1. 范围

纯前端 + 代理透传，后端 moon-well R155 同轮交付。三件事：

1. **入口**：卡片（有标准测试结果时）与结果页（标准测试完成后）各一个「细筛测试」按钮；
2. **代理**：`/ajax/vocab-test/start` 把 body 里的 `refine` 标志透传给 moon-well；
3. **结果展示**：细筛报告的前后对照行 + 按细档秩区间标注的掌握度图。

## 2. 交互口径

- **显隐**：`renderLast` 依最近报告的 `testType` 控制卡片按钮（标准=显示、细筛=隐藏、
  无历史=隐藏）；结果页按钮在细筛报告中隐藏——对细筛结果再筛等于重放同一窗口。
- **发起**：结果页处于 `result` 态也可直接开筛（浮层已开，答题视图就地切换），`state`
  放行 `idle|result`；三个开始类按钮统一禁用直至响应返回。
- **50305**（无可细筛基座）：回卡片态给一句「暂无可细筛的测试结果，请先完成一次标准测试」，
  不进浮层。
- **前后对照**：细筛报告携带 `previousEstimatedSize/previousCiLow/previousCiHigh`（父会话），
  结果页在区间行下方渲染「上次估算: ~4,033 (3,033–5,033)」。
- **细档图**：细筛报告的 `bandResults` 行序号只在会话档位表内有意义，标签一律按
  `bandRanges`（`[{band, lowRank, highRank}]`）的秩区间渲染（如 3,001–3,250）；
  标准报告的 `bandRanges` 是全表 8 档，与硬编码档名等价，标签通道统一。后端未升级
  （无 `bandRanges`）时退回硬编码档名（前端先行部署的降级态）。
- **i18n**：新词条 `Refine test` / `Previous estimate` / `Take a standard test first, then
  refine it.` 进 i18n_seed 字典 + zh_Hans_CN po/mo（契约测试 `test_i18n_seed_contract.py`
  守护）；按钮文案为模板 `_()` 通道，同键同译。

## 3. 代理契约

`vocab_test_start`（web.py）：body `{"refine": true}` 原样透传；**只认显式布尔 true**，
其余形态（缺省/false/字符串）一律按标准测试转发空体——代理不替用户解释字段，语义
分叉只在 moon-well 一处（测试 `test_start_forwards_refine_flag_only_when_explicit_true`）。

## 4. 测试

`tests/test_vocab_test_proxy.py` +1（透传矩阵：true→`{"refine": true}`、false/"yes"/缺省→
空体）；`tests/test_i18n_seed_contract.py` 对新词条自动生效；设置页渲染回归
`test_reading_settings.py` 全绿。全量 pytest 407 例通过。

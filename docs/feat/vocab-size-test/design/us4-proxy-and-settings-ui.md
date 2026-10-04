# US4 magicbook 代理层 + /reading/settings 测试 UI - 详细设计

> 上游：主 LLD（moon-well `vocab-size-test-lld.md`）§6 契约、本文档承接 magicbook LLD §2–§4。依赖后端 US1–US3 已部署方可联调，但代码可先行（入口按钮区合入时机见主 magicbook LLD §7）。

## 1. 代理层（`cps/web.py`）

四个路由，完全照 `reading_settings_get/update`（web.py:535-553）模式，薄透传零业务：

```python
@web.route("/ajax/vocab-test/start", methods=["POST"])            # → POST /vocabulary/test/start
@web.route("/ajax/vocab-test/answer", methods=["POST"])           # body 含 {"sessionId": id, "answer": 0|1}
@web.route("/ajax/vocab-test/finish", methods=["POST"])           # body 含 {"sessionId", "addUnknownToNotebook"}
@web.route("/ajax/vocab-test/history", methods=["GET"])           # → GET /vocabulary/test/history
```

- **sessionId 放 body/query 而非 URL path**：与 `_moonwell_proxy` 现有签名一致（path 是 moon-well 目标地址，代理层不做路径拼接转发），后端路径 `{sessionId}` 由前端 body 字段带入后拼目标 URL——实现时以 `_moonwell_proxy(f"/vocabulary/test/{sid}/answer", ...)` 构造目标即可。
- 校验：answer 仅校验 `answer ∈ {0,1}`、`sessionId` 为正整数，非法即 `jsonify({"success": False, ...}), 400`（对齐 web.py:549-551 风格）；其余透传。
- 超时：start/finish/history 10s；answer 5s（答题是内存态机 + 单行 insert，短超时快失败）。
- 首屏 history：`reading_settings()`（web.py:306）内新增 `_vocabtest_history_fetch()`——照 `_moonwell_settings_fetch()`（886-900）服务端同步拉取，失败静默 `vocabtest_history=None`，**不并入 load_error**（测试卡片独立于档位设置降级）。

## 2. 模板结构（`reading_settings.html`）

### 2.1 测试卡片（档位 panel 之后，同 `panel panel-default` 体系）

```
panel: Vocabulary Size Test
  p.text-muted: 一句话说明 + "~4 min, 40–50 words"
  [if last]  help-block: Last result: <b>~8,600</b> (7,200–10,000) · Oct 4, 2026
             [if capped] 显示 "25,000+"（无区间）
  checkbox#vt-add-unknown（默认勾选）: "Add unknown words to my notebook"
  button#vt-start .btn.btn-primary: "Start test"
  a#vt-toggle-history: "History" → 折叠 ul（日期 · 估算 · 题量，来自首屏 history；为 null 时整个 History 链接隐藏）
```

- 文案全部 `{{_()}}` 包裹、英文 msgid（页面现状单语纪律，见 magicbook LLD §2 视觉约束）；新增串需补 zh 翻译（`cps/translations`，参照 language-i18n 既有做法），未翻译前默认显示英文不阻塞。
- `#vt-add-unknown` 状态记忆：`localStorage["vtAddUnknown"]`，读不到默认 true。Why: 服务端 per-user 偏好需要新存储面，本期一人一设备场景 localStorage 足够。

### 2.2 答题浮层与结果视图（同模板内隐藏容器，modal 样式复用项目现有 overlay/modal 类）

- 浮层 DOM：进度条（`.vt-progress`）、`#vt-word`（超大字号）、`#vt-sentence`（灰）、两键 `#vt-known` / `#vt-unknown`、右上 `#vt-exit`、`#vt-error-line`。
- 结果 DOM：`#vt-size`（大字）、`#vt-range`、`#vt-capped-note`、条形图容器 `#vt-band-chart`（8 行 `.vt-bar`，`width:p%` 内联 + 秩区间标签，纯 CSS）、`#vt-notebook-line`（"N new words added to your notebook"，finish 响应 `addedToNotebook`）、`#vt-done`。
- 浮层跟随宿主主题：不自造配色，蒙层/文字/按钮全部继承现有 modal 与 `text-*`、`btn-*` 类。

### 2.3 JS 状态机（模板 `{% block js %}` 内，预估 >200 行则拆 `cps/static/js/vocab-test.js`——以拆分为默认选择，模板现 137 行不宜翻倍）

```
states: idle → asking(currentQuestion) → scoring → result | error(可重试)
```

- `start()`：POST start → 存 `{sessionId, question}` → asking；HTTP 401 走全局登录过期跳转（项目既有 fetch 约定），50301（词表未就绪）→ 卡片内 `setStatus` 提示，不进入浮层。
- `answer(known)`：**在途锁**（同一题未收到响应前忽略重复提交，含双击与键盘连击）→ POST answer →
  - `finished=true`：本地调 `finish()`；
  - 否则渲染下一题（服务端为准，前端**不预生成**任何题）。
  - 失败（非 401/50302 类网络/5xx）：`#vt-error-line` "Something went wrong — retry this word"，按钮重试**同一请求**（幂等靠后端 US2 §4 重发回放）；
  - 50302（归属/状态错）：直接关浮层回 idle（刷新卡片态）。
- `finish()`：POST finish（带 addUnknown）→ result 视图渲染 → 更新卡片 Last result 区（不整页刷新）。
- 键盘：`document.keydown`，仅 asking 态挂载处理；`e.isComposing === true` 或项目 R114 既有 IME 守卫工具函数（实现时优先复用现成守卫，如 header 搜索所用同一判定，不新写）一律忽略；`←/J`→known、`→/K`→unknown、`Esc`→exit。
- `exit()`：无请求（后端懒 abandoned），直接回 idle。Why 不发 abandon 请求：省一个端点，30 分钟超时语义已覆盖。
- CSRF：三处 POST 均带 `X-CSRFToken`，取法照模板 74-77 行 hidden input 惯例；失败自愈沿用 80-88 行模式（`vtCsrfReloaded` 独立标记键）。

## 3. 改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/web.py` | +4 代理路由 +`_vocabtest_history_fetch()`；`reading_settings()` 传 `vt_last`/`vt_history` |
| `cps/templates/reading_settings.html` | +卡片、+浮层/结果容器，`<script src=vocab-test.js>`；模板目标 ≤200 行 |
| `cps/static/js/vocab-test.js` | 新建，§2.3 状态机 |
| `cps/static/css/*`（以现有组织为准）或模板 `<style>` | `.vt-progress`/`.vt-bar` 少量样式（≤40 行） |
| `cps/translations/zh_*/LC_MESSAGES/messages.po` | 新增 msgid 翻译 |
| 测试 | `test_cps` 体系内新增代理路由用例（照 reading-settings 代理既有测试文件风格，另起文件防并行会话冲突——见项目共存纪律） |

## 4. 与后端联调核对单（= magicbook LLD §5 展开）

1. answer 响应题对象字段名 `{word, sentence}`；进度 `{answered}`（分母用文案 "~4–7 min" 弹性表述，不强依赖固定总数）。
2. `finished:true` 时不再带 question，前端即调 finish。
3. finish 重复调用回放同一报告（前端网络重试路径）。
4. `capped` / `ciLow/ciHigh`（后端驼峰）/ `bandResult[{band,questions,known}]` / `addedToNotebook`。
5. history 项 `{finishedAt, estimatedSize, ciLow, ciHigh, capped, questionCount}`，最近 10 条已排序。
6. 错误码 50301/50302/50303 透传行为逐一演练。

## 5. 验证方法

- 单元：代理路由参数校验与透传（mock `_moonwell_proxy`）。
- 本地端到端：moon-well 本地起 + 样本词表；浏览器完整跑通高/低词汇两个机器人用户。
- 视觉：无头 Chrome 截图浮层/结果/图表（docs/temp 夹具流程，遵守项目截图参数坑）；两套主题各一遍。
- 回归：档位设置卡片、IME 守卫无串扰、`load_error` 场景测试卡片仍可用。

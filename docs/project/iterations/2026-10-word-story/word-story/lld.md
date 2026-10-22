# 单词编故事（magicbook R205）· LLD

**状态**：开发中（2026-10-22 用户定稿：D1 不记遇见、D2 上 SSE、D3 storySeconds=120）
**同源**：moon-well R200（生成端点、落库、入账折算）；需求台账 magicbook R205 / moon-well R200

## 1. 交付形态

每日学习中枢加**第八张循环卡**「单词编故事」，点开是新子页面 `/learning/story`。卡片区自动把「今日欠账最多那股」排到最前，所以不需要手工调顺序；`data-strand="language"`（计入词汇学习股）。

页面三段式：词源选择（今天到期的词 / 我粘一批词）→ 生成按钮 + 状态行 → 故事正文（目标词加粗）+ 词表卡列表；下方是历史列表（点一行把故事装回页面）。

## 2. 路由与代理（`cps/routes/learning.py`，蓝图 `web`）

| 类型 | 路由 | 预算 |
| --- | --- | --- |
| 页面 | `@web.route("/learning/story")` + `user_login_required` → `learning_story.html` | — |
| 代理·SSE | `/ajax/learning/story/generate/stream` → `POST {moonwell}/learning/story/generate/stream`（`stream=True`、`X-Accel-Buffering: no`） | connect 10s / idle 300s |
| 代理·JSON 回退 | `/ajax/learning/story/generate` → `POST {moonwell}/learning/story/generate` | `_STORY_LLM_TIMEOUT = 120` |
| 代理 | `/ajax/learning/story/history` → `GET` | 15s |
| 代理 | `/ajax/learning/story/detail`（带 `id`）→ `GET` | 15s |

- JSON 回退走 `_moonwell_proxy`；SSE 走由写作代理泛化出的 `_llm_sse_proxy(path, label, payload_builder)`，请求体由 `_story_payload` 校验：`source` 枚举；due 的 `count` 为 1–8 的整数；manual 的 `words` 列表折叠成一个整段字符串（≤2000 字符），切分、去重与 8 词上限仍由 moon-well 判（一个口径）；`cefrLevel` 限 A2/B1/B2/C1。**不在服务端解 `Result` 包**（保持现有 passthrough 契约），解包在前端 `MBLearning.resultOf`。
- SSE 时长：每次生成通常 10–25s；`status` 建连即到，等待中每 5s 一条 `ping`，前端状态行显示已等待秒数。若 SSE 建连失败或**未收到任何事件**即断开，回退 JSON 端点一次；一旦收到 `status`/`ping`，断开后不再重试（故事可能已落库并入账）。
- 容器依赖：magicbook R204 已让 tornado `WSGIContainer` 对 `text/event-stream` 逐帧写出（`origin/develop` `a4b1a53b`），本功能直接受益，不重复改容器。
- 失败必须可见：`success:false` → `alert(message)`；无 `message` 时用本地「故事生成失败」，不得渲染成「今天没有故事」。

## 3. 前端

- 模板 `cps/templates/learning_story.html`：`extends layout.html`、`#lh-csrf`、返回链接、`{% include "learning_sub_css.html" %}`、注入 `window.learningUrls`（storyGenerate/storyGenerateStream/storyHistory/storyDetail/readingTts）。
- 脚本 `cps/static/js/learning-story.js`：沿用 `['id', …].forEach(els…)` 元素注册表范式，`var urls = window.learningUrls || {}`；**必须先载 `learning-common.js` 再载本模块**（守卫会查）。
- 状态机：按钮点击即 disabled，状态行按 SSE 事件走「连接中… → 正在写故事… Ns」；成功后渲染正文与词表卡；`missing=true` 的词卡标「未出现在故事中」，`uncached=true` 标「AI 释义」。
- 朗读：复用阅读器同一条 `/ajax/reading-tts`（下游 `/tts/speak`）与播放实现，不新造引擎。
- 手输词：一个 textarea，占位「最多粘贴 8 个英文单词，用逗号或换行分隔」；前端只做非空校验并把整段作为单元素 `words` 发出，切分/归一/去重/8 词上限全由 moon-well 负责（词形归一的权威在 moon-well，前端做会漂移）。「今天到期的词」按钮不预先拉队列，直接 `source:"due"` 一次调用——队列取词与素材装配都在后端，省一次往返也避免前后端取到不同批次。
- 历史：点行调 detail 把 `storyText`/`cards` 装回页面；不做删除（一期）。

## 4. 中枢卡片与守卫改动清单

1. `cps/templates/learning.html`：新增 `<a class="lh-card" data-key="story" data-strand="language" href="{{ url_for('web.learning_story_page') }}">`（标题/描述 ≥80 字符/插画 `<img>`）。
2. `cps/static/img/learning/story.webp`（<200 KB，守卫查存在与体积）。
3. `cps/routes/learning.py`：页面路由 + 4 条代理（JSON / SSE / history / detail）+ `_PROXY_LIMITS`。
4. `tests/test_learning_hub_cards.py` 的 `CARDS` 表增一行（顺序/标题/endpoint/strand 四列都要对，顺序断言按模板出现顺序）；`tests/test_learning_pages_static.py` 的 `PAIRS` 增一行（template/js/urls/id 注册与加载顺序守卫）。
5. i18n：卡片与页面 msgid 进 `zh_Hans_CN` po → `pybabel compile`；新增 `mbT("…")` 字面量后重跑 `scripts/generate_i18n_seed.py`（清单 `tests/i18n_js_files.json`）。
6. 导航无需改（`top_learning` 是唯一入口，中枢卡片不算导航项）。
7. `tests/test_no_duplicate_js_lines.py`：新模块整段复制阅读器代码会撞车，朗读部分要抽调用不抄实现。

## 5. 入账显示

时长不由前端上报：后端生成成功时记 `FLUENCY{activity:"story"}` 事件，`LearningStrandService` 折算进 LANGUAGE 股（moon-well R200 §5）。因此中枢「今日 x/10 分钟 · 词汇学习」与卡片徽章会自动带上编故事的花费，前端零改动。**若后端漏加 `case "story"`，这张卡的徽章会永远是空的**——这条要在联调时显式核。

## 6. 测试（开发态只跑改动相关）

- `tests/test_learning_story.py`：页面 200 且含卡片返回链；四条代理的 body 转发/超时预算/上游 5xx 与 `success:false` 的透传与界面可见错误；SSE 头、401 刷新与事件透传；`_story_payload` 对非枚举 source / 越界 count / 非法 cefr / 超长词表返 400。
- 复跑受影响的静态守卫：`test_learning_hub_cards.py`、`test_learning_pages_static.py`、`test_nav_settings_dropdown.py`、`test_no_duplicate_js_lines.py`。
- 命令：`../magicbook/.venv/bin/python -m pytest tests/test_learning_story.py tests/test_learning_pages_static.py tests/test_learning_hub_cards.py tests/test_learning_writing_sse.py tests/test_i18n_seed_contract.py`，读末行汇总（管道退出码不可信）。
- 2026-10-22 开发态实跑：`104 passed`。同日修 `generate_i18n_seed.py` 两处：mbT 双引号内含撇号（`Today's due words`）漏扫、回填时未转义——前者会让新增词条静默回退英文，后者会写坏 Jinja 字典。
- 真机验收：worktree 干净检出 + 复用主检出 `.venv`，浏览器走一遍「到期一键 → 生成 → 词表卡 → 朗读 → 历史回看 → 中枢徽章 +2min」。

## 7. AC（对齐 moon-well R200 §9 待定稿项后定稿）

1. 到期一键：有到期词时正文词表卡恰好使用请求的词；无到期词时界面显式提示「今天没有到期复习的词」。
2. 粘贴词：9 个词 → 报「一次最多 8 个词」且不静默截断；全是标点 → 报词表非法。
3. 未收录词照常出故事，词卡释义标「AI 释义」；漏词标「未出现在故事中」。
4. 每个目标词在正文里加粗且有一句原句回显；漏词标 `missing`。
5. 历史可回看、只看到自己的。
6. 朗读出音（非静音、非报错）。
7. 中枢词汇学习股今日分钟数按 `storySeconds` 增长，重复生成累加。
8. LLM 失败/欠费：错误文案来自后端 `message`，不伪装成空数据。
9. 守卫全绿：卡片表、页面对、形制断言、无重复 JS 行。

# Vocab-Size-Test 词汇量测试（magicbook 前端）- 低层设计文档 (LLD)

> 需求来源：`requests.md` R116（2026-10-04）；后端设计见 moon-well `docs/feat/vocab-size-test/design/vocab-size-test-lld.md`（两份须对齐评审）。
> 状态：**设计定稿待评审，未开发**。

## 1. 背景与范围

在 `https://magicbook.haoyuhang.top/reading/settings` 引入词汇量测试环节。magicbook 只做**代理 + 交互呈现**，出题状态机、估算、落库全部在 moon-well（后端 LLD D6/D7）。

现状锚点：

- 路由 `reading_settings()`：`cps/web.py:306-312`，`@user_login_required`，首屏经 `_moonwell_settings_fetch()`（web.py:886-900）同步拉设置，失败降级 `load_error`。
- 模板 `cps/templates/reading_settings.html`（137 行）：现仅「Vocabulary Difficulty Level」下拉 + Save（fetch 走 `/ajax/reading-settings/hard-level`）。
- 代理层 `_moonwell_proxy()`：web.py:1008-1082，内网信任 + `X-User-*` 身份头（web.py:700-725）+ Bearer 透传 + 401 refresh。**身份链零改动**。

## 2. UI 设计（遵循既有视觉纪律：轻蒙层、无实色描边、小卡片、单语英文文案、弹层跟随宿主主题）

### 2.1 设置页新增「Vocabulary Size Test」卡片

位置：难度档位卡片下方，同栏同宽。默认态（未测试/有历史）：

- 一句话说明 + 预计时长（~4 min）；
- 上次结果摘要：`~8,600 words (7,200–10,000) · Oct 4, 2026`，无历史则不显示该行；
- 按钮 `Start test`（主）与 `History`（次，折叠展开历次会话列表：日期/估算值/题量）。

### 2.2 答题浮层（全屏 modal）

- 结构自上而下：进度条（answered/预估 45，弱对比）、**单词**（超大字号，页面视觉唯一重音）、英文例句（灰色小字，**不出现任何中文/释义**，后端 LLD D4）、两键 `✓ I know it` / `✗ Not sure`。
- 键盘：`←`/`J` = 认识，`→`/`K` = 不认识；**必须带 IME 守卫**（R114 口径：composition 期间按键不触发）。浮层内无可聚焦输入框，守卫仅防宿主页面残留监听串扰，验收时确认。
- 提交即下一题，无「上一题」回退（测量学上不允许多次博弈同一词）；右上角 `Exit` 直接放弃会话（后端懒标 abandoned，不弹窗挽留）。
- 状态处理：请求失败重试本题（客户端持有当前题对象）；401 走既有全局登录过期跳转。

### 2.3 结果视图（替换浮层内容，非新页面）

- 大字估算值 + 区间；`capped=true` 时显示 `25,000+`（不显示区间）。
- 各频段掌握度：**纯 CSS 水平条形图**（8 行，band 秩区间为标签，认识率 0–100%），不引入图表库。
- 若 `addUnknownToNotebook` 生效：`N new words added to your notebook`，链接跳 moon-well 单词本入口（若无站内入口则仅文案提示）。
- 按钮：`Done`（回设置页，卡片刷新为上次结果态）。

### 2.4 结果页的选项开关

答题完成前无预告；**不认识词落生词本的开关放在何处**——定稿：设置页卡片内、`Start test` 按钮上方一个轻复选框 `Add unknown words to my notebook`（默认勾选）。理由：finish 请求一次成型，避免结果页再补一次写操作导致重复落本风险。

## 3. 代理端点（`cps/web.py`，全部薄封装 `_moonwell_proxy`，无业务逻辑）

| magicbook 路径 | 方法 | moon-well 目标 |
| --- | --- | --- |
| `/ajax/vocab-test/start` | POST | `POST /vocabulary/test/start` |
| `/ajax/vocab-test/<session_id>/answer` | POST | `POST /vocabulary/test/{id}/answer` |
| `/ajax/vocab-test/<session_id>/finish` | POST | `POST /vocabulary/test/{id}/finish` |
| `/ajax/vocab-test/history` | GET | `GET /vocabulary/test/history` |

- 均 `@user_login_required`；请求/响应体原样透传（含 `Result.code`），错误码翻译沿用前端现有约定。
- `reading_settings()` 首屏增加一次 history 拉取（服务端同步、失败静默降级为无历史态，与 `load_error` 同风格，不阻塞档位下拉渲染）。

## 4. 改动清单（magicbook，实现时逐项打钩）

| 文件 | 改动 |
| --- | --- |
| `cps/web.py` | +4 代理路由（照 `/ajax/reading-settings` 模式）；`reading_settings()` 首屏补 history |
| `cps/templates/reading_settings.html` | +测试卡片 + 浮层/结果视图容器 + JS（页面内 `<script>`，照现有 96-133 行风格；若超 ~250 行则拆 `cps/static/js/vocab-test.js`） |
| 样式 | 复用现有卡片/modal 类；仅进度条与条形图需少量新 CSS，写模板内 `<style>` 或现有 css 文件（以现有页面组织为准） |

## 5. 与后端契约的对齐点（评审时逐条核对）

1. start/answer 响应中的题对象字段名（`word`,`sentence`）与进度字段。
2. `finished` 信号语义（answer 返回 question=null）与前端切结果视图的触发。
3. finish 幂等回放（重复 finish 返回同一报告）——前端网络重试依赖此。
4. `capped`、`ci_low/ci_high`、`band_result` 数组结构。
5. history 列表项字段（默认最近 10 条，前端不翻页）。

## 6. 验收要点（AC 草案，正式 AC 验收阶段落 `ac/` 目录）

- Happy path：完整 40–50 题流程、结果图与后端报告一致；重进设置页显示上次结果。
- 边界：`capped=true` 文案；止损早停（~25 题）流程完整；70 题强制收尾由后端保证、前端无假设。
- 异常：moon-well 不可用时设置页正常渲染（load_error 风格）；答题中途断网重试本题成功；Exit 后会话不再可答。
- 回归：难度档位设置不受影响；IME 守卫不破坏其他页面监听；`/reading/settings` 两套主题渲染正常。
- 本地验证边界（项目既定约束）：本机无 calibre 书库不影响本页；视觉验证用 docs/temp 夹具 + 无头 Chrome 截图（注意既有截图参数坑）。

## 7. 发布顺序

依赖 moon-well 先上线（DDL+数据合并+后端接口，见后端 LLD §10），magicbook 前端为最后一步；前端先发也不会报错（history 拉取静默降级），但入口点击会 404，故 **卡片入口按钮区在后端就绪前不合入**。

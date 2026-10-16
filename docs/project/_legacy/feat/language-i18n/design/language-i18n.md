# Magicbook 语言模块修复（按 locale 单语切换）— LLD 设计稿

> 对应需求：`requests.md` R112 —「语言模块还是有问题。很多没有双语设置，很多直接把双语显示出来了，而不是根据选择的语言切换。」
> 形态决策已与用户确认：**英文 msgid + zh_Hans_CN po 译文**（沿用上游 Calibre-Web 约定），三个 User Story 全做。

## 1. 问题拆解（三个独立成因）

| 症状 | 根因 | 层次 |
| --- | --- | --- |
| 中文用户仍看到英文 | R102 刻意做的「中文为主 + 英文辅助」双写（`阅读设置 <small>Reading Settings</small>`）绕过了 Babel，无论 locale 为何都渲染两种语言 | 模板 |
| 中文用户看到英文 | magicbook 自有 `_()` msgid 从未进入 `zh_Hans_CN` po，`_()` 只能回退 msgid 本身 | po/mo |
| 阅读器/引导/AI 面板文案恒英文 | `epub.js`、`ai_chat.js`、`onboarding.js` 是静态 JS，拿不到 Jinja 的 `_()`，此前完全没有本地化通道 | JS |

## 2. User Story 划分与交付顺序

单线程开发，逐个验证后再进入下一个：

- **US1 模板层**：`layout.html` 设置下拉、`login.html` 登录/注册入口的双写改为 `{{ _('...') }}`；magicbook 自有 msgid 补入 `zh_Hans_CN` po 并 `pybabel compile`。
- **US2 JS 机制 + 引导**：新增 `cps/templates/i18n_seed.html`（种子通道）；`onboarding.js` 步骤表文案改为英文 msgid 经 `mbT()` 取词。
- **US3 阅读器文案收编**：`epub.js`（55 处）、`ai_chat.js`（21 处）中文字面量全部改走 `mbT()`，词条进种子 + po。

## 3. JS 层 i18n 通道（本设计唯一的新机制）

模板用 Babel 渲染「msgid → 当前 locale 译文」的字典，注入页面全局；JS 只按 msgid 取词。

```
cps/templates/i18n_seed.html
  {% set mb_i18n = { "Skip": _("Skip"), ... } %}
  window.MB_I18N = {{ mb_i18n | tojson }};
  window.mbT = id => hasOwnProperty(MB_I18N, id) ? MB_I18N[id] : id;
```

消费侧统一带降级：`var mbT = window.mbT || function (id) { return id; };`
——种子缺失（例如新脚本挂在未 include 的页面）时退化为英文，不会抛错。

四个设计约束，都是实现期实测踩到的：

1. **msgids 用英文**。与上游 Calibre-Web 的 po 约定一致，`pybabel extract` 的 jinja2 抽取器能扫到 `_()`；中文 msgid 会让上游词条与本项目词条混在同一文件里难以维护。
2. **种子必须早于消费脚本**。`read.html` 里 `i18n_seed.html` 的 include 放在 `reader.min.js`/`epub.js` 的 `<script>` 之前——`epub.js` 在顶层作用域取词，include 顺序错了就拿不到 `mbT`。`read.txt`/`readpdf` 走 `ai_chat_panel.html`，同样补了 include。
3. **占位符风格** `mbT('...{w}').replace('{w}', value)`；不引入模板引擎。`String.replace` 的第二参里 `$&`、`$1` 等序列会被特殊展开，因此**插入用户可控文本的三处**（生词 `Marked as unknown: {w}`、伴读角色名 `…“{r}”…`、会话名 `Delete conversation “{t}”?…`）走回调形式 `.replace('{w}', function () { return word; })`；其余占位符填的是服务端计数（`{d}/{t}/{f}/{total}/{cached}/{published}`），数字无 `$` 语义，保持字面写法。
4. **`tojson` 的安全性**：Flask 的 `tojson` 对非 ASCII 做 `\u` 转义并转义 `<>&'`，所以种子可以内联进 `<script>`；测试里不能用「中文原文」做全文匹配，必须解析 JSON 后比对。

模板写法限制（Jinja）：`{% set %}` 字典里既不能写 `//` 行注释，也不能写 `{# #}` 注释（`TemplateSyntaxError`），所以种子文件只在字典外留说明注释。

## 4. msgid 复用的坑：上游译文不合适

`Edit` / `Delete` 在上游 `zh_Hans_CN` po 里已分别译作「编辑书籍」「删除数据」（管理页语境）。AI 记忆面板复用这两个 msgid 会显示错误文案，因此改用独立 msgid：`Edit memory` / `Delete memory`。同理，运行时字符串与 po msgid 必须逐字符一致——`'Delete this memory?\\n'`（字面反斜杠）与真实换行拼接的形态不同，最终定为 msgid `Delete this memory?`，换行在 `mbT()` 之外拼接。

## 5. 一致性契约（测试锁死）

链路的失效模式都是**静默回退英文**，运行时不报错，所以用源码级断言（`tests/test_i18n_seed_contract.py`）：

| 契约 | 断言 | 对应历史缺陷 |
| --- | --- | --- |
| 1 | 种子字典 key 与 `_()` 实参逐字符相同 | 尾点差一个字符 → zh 用户拿到英文 |
| 2 | 三个 JS 里 `mbT('字面量')` 的词条都在种子里 | `Difficulty: ` 等 3 条收编时漏加 |
| 3 | 每个种子 msgid 在 `zh_Hans_CN` po 有非空译文 | msgid 没进 po |
| 4 | `onboarding.js` 步骤表 `title/body` 文案都在种子里 | 动态取词（`mbT(step.title)`）正则抓不到，正是尾点缺陷出处 |

渲染层断言在 `tests/test_onboarding_tour.py`（种子只注入一次、en 账号取回 msgid、zh 账号取回中文）与 `tests/test_nav_settings_dropdown.py`（en 账号无中文回流、zh 账号双写不回流）。

## 6. 改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/templates/i18n_seed.html` | 新增，144 词条种子 + `window.mbT` |
| `cps/templates/layout.html` | 设置下拉/引导入口双写 → `_()`；body 末 include 种子（早于 `onboarding_mount.html`） |
| `cps/templates/login.html` | `Sign in` / `Log in` / `Sign up` 走 `_()` |
| `cps/templates/read.html`、`readtxt.html`、`readpdf.html` | 消费脚本之前 include 种子 |
| `cps/static/js/onboarding.js` | 步骤表英文 msgid + `mbT()`，去掉 `.onb-title-en` 双写 |
| `cps/static/js/reading/epub.js` | 55 处中文字面量 → `mbT()`，含整本翻译/批注/TTS/生词本 |
| `cps/static/js/ai_chat.js` | 21 处 → `mbT()`，含会话、记忆面板、学情画像 |
| `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po|.mo` | +211 词条（base 876 → 1087），mo 重编译 |

## 7. 未采纳项与遗留

- 不做「同一控件中英双写」的展示形态（这正是用户投诉点），语言只由 `User.locale` 决定。
- `mbT()` 词条内嵌中文标点分隔符（`｜`、`、`、`：`）与 `＋/－` 按钮字形保留——它们是排版符号而非文案，本地化它们反而破坏等宽对齐。
- 种子内联约 9KB/页；未来词条继续膨胀时再改独立 JSON + fetch（当前量级不值得）。
- CSS `content` 里的 `Tr` 徽标依赖 `mbT('Tr')` 拼进样式串，改动需注意引号；上游若新增同名 msgid 需复核。
- `onboarding.js` 的 `esc()` 走 jQuery `text().html()`，转义 `& < >` 但**不转义引号**，用在 `title="…"` 这类属性值里理论上会被含 `"` 的译文截断。现有属性侧词条（`Onboarding Tour`、`Skip the cache…`）中文译文不含半角引号，本轮不扩大改动面；引导模块下次动 DOM 时一并收紧（改 `attr()` 赋值即可绕开）。

## 8. 事故记录（供后续脚本参考）

`write_po(f, cat, ...)` 之前用 `open(PO,"wb")` 打开目标文件——`write_po` 参数错误（`sort` 不被接受）抛异常时文件已被截断为 0 字节。恢复姿势：`git show HEAD:` 取 base po + 从已编译 `.mo`（`read_mo`）回灌 208 条译文，再补新增词条；`.mo` 与脚本里的翻译字典都在版本控制/备份之外，是这次能无损还原的原因。教训：**改 po 一律写临时文件再原子替换，且新增 msgid 的中文译文同时留在 `docs/temp/scripts/` 的字典里**。

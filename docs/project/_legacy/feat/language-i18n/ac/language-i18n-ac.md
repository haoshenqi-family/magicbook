# R112 语言模块修复 — 验收标准与验证结果

> 对应设计：`docs/feat/language-i18n/design/language-i18n.md`
> 验证环境：`magicbook/.venv`（Python 3.14 + Babel 2.18），`.venv/bin/pytest tests/ -q`

## US1 模板层：双写 → 按 locale 单语切换

| # | 验证点 | 手段 | 结果 |
| --- | --- | --- | --- |
| 1.1 | en 账号的设置下拉只出英文，中文双写不回流 | `tests/test_nav_settings_dropdown.py::test_labels_single_language_for_en_admin` | ✅ |
| 1.2 | `locale=zh_Hans_CN` 账号同一位置出「阅读设置 / 使用引导」，且不含 `Reading Settings` | `test_labels_switch_to_chinese_for_zh_user` | ✅ |
| 1.3 | 下拉入口 id（`top_mb_settings` 等）不变，且每个 id 全页只出现一次（DOM 契约不被改名破坏） | `test_old_flat_entries_and_dead_link_removed` | ✅ |
| 1.4 | 角色门控仍生效：普通用户看不到 admin 专属「整本翻译」入口 | `test_plain_user_sees_dropdown_without_admin_entries` | ✅ |
| 1.5 | 登录页 `Sign in / Log in / Sign up` 走 `_()`，注册入口不再中英双写 | `tests/test_login_invite_link.py` | ✅ |
| 1.6 | magicbook 自有 msgid 已进入 `zh_Hans_CN` po 且 mo 已重编译（mo mtime 不早于 po） | `docs/temp/scripts/r112_i18n_verify.py` B 段 | ✅ |

## US2 JS i18n 通道 + 引导本地化

| # | 验证点 | 手段 | 结果 |
| --- | --- | --- | --- |
| 2.1 | layout 页注入 `window.MB_I18N` 恰好一次，`window.mbT` 存在 | `tests/test_onboarding_tour.py::test_i18n_seed_mounted_once_and_localizes` | ✅ |
| 2.2 | zh 账号取词得到中文（`Skip`→跳过、`Start Tour`→开始引导、`Book wall`→书墙） | `test_i18n_seed_renders_chinese_for_zh_user` | ✅ |
| 2.3 | 全部种子词条渲染后非空（含带 `\n`、引号的长词条，走运行时 JSON 比对） | 同上，遍历断言 | ✅ |
| 2.4 | 种子字典 key 与 `_()` 实参逐字符相同（尾点类缺陷回归锁） | `tests/test_i18n_seed_contract.py::test_seed_key_equals_msgid` | ✅ |
| 2.5 | `onboarding.js` 步骤表 title/body 文案全部在种子里 | `test_onboarding_step_strings_are_seeded` | ✅ |
| 2.6 | 气泡不再渲染 `.onb-title-en` 英文副标题（双写形态清除） | `onboarding.js` 源码 + 2.2 渲染结果 | ✅ |

## US3 阅读器 / AI 面板文案收编

| # | 验证点 | 手段 | 结果 |
| --- | --- | --- | --- |
| 3.1 | `epub.js`、`ai_chat.js` 的 `mbT('字面量')` 词条都在种子里 | `tests/test_i18n_seed_contract.py::test_js_mbT_literals_are_seeded` | ✅ |
| 3.2 | 每个种子 msgid 在 po 有非空译文（不漏进 po 即静默英文） | `test_seed_msgids_have_zh_translation` | ✅ |
| 3.3 | 三个 JS 非注释区无遗留中文文案（只剩排版符号 `｜`、`、`、`＋/－`、`：`） | `r112_i18n_verify.py` C 段人工复核 7 处 | ✅ |
| 3.4 | 种子在 `read.html` 里早于 `epub.js` 加载；`readtxt.html`/`readpdf.html` 补 include（否则 AI 面板取词失败） | 模板 include 位置核对 | ✅ |
| 3.5 | 带占位符的重组句式可本地化（`Whole-book translation completed: {d}/{t}`、`Marked as unknown: {w}`、`Regenerating will overwrite the current “{r}” annotation. Continue?`） | 词条进种子+po，3.1/3.2 覆盖 | ✅ |
| 3.6 | 与上游 po 的 msgid 冲突已避让（记忆按钮改用 `Edit memory`/`Delete memory`，而非上游已占用的 `Edit`/`Delete`） | po 比对 | ✅ |
| 3.7 | 占位符填充用户可控文本走回调形式，`$&`/`$1` 不被 `String.replace` 展开（生词词文本、伴读角色名、会话名三处） | 源码核对 + node 复现：`'删除会话「{t}」'.replace('{t}', '$& 测试')` 旧写法吞掉占位符、回调写法原样输出；`node --check` 通过 | ✅ |

## 回归与完整性

| # | 验证点 | 结果 |
| --- | --- | --- |
| R.1 | 全量单元测试通过 | ✅ `275 passed`（含本次新增 4 条契约测试） |
| R.2 | 引导原有契约不受破坏（`view_settings` 三种形态、`/ajax/view` 写入通道、手动入口角色显隐） | ✅ `tests/test_onboarding_tour.py` 全绿 |
| R.3 | po 修复事故（`.po` 曾被 `write_po` 截断）已无损还原：base 876 条 msgid 零丢失、零译文倒退，新增 211 条 | ✅ 见设计稿 §8 |
| R.4 | XSS：种子经 Flask `tojson` 转义，不出现裸 JSON | ✅ `r112_i18n_verify.py` D 段 |

✅ 所有 AC 已覆盖验证

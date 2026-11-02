# 写作工坊续写（magicbook R168）· L3 设计

**状态**：已上线（2026-10-14 08:1x，develop `ffadd9fb`，同源 moon-well `1ef990f`）。

## 1. 问题与承接

R166 把写作工坊拆成子页面后，「写作历史」仍是一行行只读摘要。后端草稿正文一直存着
（`learning_writing_submission.text`）却从不出接口，所以中途停下就没法接着写。
本任务是 moon-well R172（`GET /learning/writing/task` + `lastDraftNo` + `tips` 落库）
的前端侧。

## 2. 关键取舍

**提交路径收敛为一个编辑区 + 一个状态驱动按钮。** 原页面有两个提交入口（初稿框 +
批改面板里的「修订框 + 提交修订按钮」），各自打 `/submit` 与 `/revise`。续写一旦把
第 1 稿装回来，两条路径就会同时可提交同一稿（且第二条会撞 50513）。因此撤掉面板内的
修订框与按钮，正文只在上层编辑区改，按钮文案与目标端点由 `writing.lastDraftNo` 决定：

| `lastDraftNo` | 按钮文案 | 目标端点 | 可点 |
| --- | --- | --- | --- |
| `null` | 提交批改 | `/ajax/learning/writing/submit` | 是 |
| `1` | 提交修订稿 | `/ajax/learning/writing/revise` | 是 |
| `2` | 两稿已完成 | — | 否（禁用，不让用户去撞 50513） |

## 3. 交互

- **历史行可点**：每行文案 = 题目 · 状态；`cursor:pointer` + `title` 提示，点击 `resume(taskId)`。
- **一键续写**：`armResumeBar(items)` 取列表里**第一条没写完的**（`lastDraftNo` 为 null 或 <2；
  列表本身按创建时间倒序）→ 顶部绿色按钮 + 旁边显示该题目前 40 字；全部写完则整条隐藏。
- **`applyTask(detail)` 铺回**：mode/cefrLevel/bookTitle 选择器、题目、要求、提示、
  最新稿正文进编辑区、该稿批改结果进批改面板（复用 `renderReview`），
  状态行说明「已恢复第 N 稿」，焦点给编辑区。
- 旧任务（R172 之前出的题）`tips` 为空列表——后端当时没存，属数据缺失，页面照常渲染。

## 4. 代理

`GET /ajax/learning/writing/task`：`taskId` 必须纯数字且 ≤64 字符，否则本地 400 不打上游
（防把任意串拼进转发路径）；合法时以 GET 转发 `/learning/writing/task?taskId=<id>`，
超时 20s（与同族 LLM 端点同档，避免上游冷启动时前端先超时）。业务语义（归属、50512）归上游。

## 5. 测试与验收

- `test_learning_proxy.py` +4 例：登录门禁、GET 透传与正文/批改字段不裁、
  非数字 taskId 本地 400 且不打上游、续写 UI 装配面（端点注入 + 按钮存在 +
  旧修订框已移除）。
- `test_learning_pages_static.py` 自动覆盖新 els 注册表（`sw-w-resume*` 三个 id 与模板双向锁）。
- `test_i18n_seed_contract.py`：10 条新 JS 词条进种子且 zh 译文非空；模板 3 条走 po
  （追加式补丁，diff 纯新增 30 行）。
- 开发态闸门 116 例绿；全量 **505 passed / 0 failed**。
- **交互态只能靠真浏览器判定**，静态断言看不见：`docs/temp/run_learning_hub_check.py`
  加 `probe=2` 交互探针 + 写作桩数据，无头 Chrome `--dump-dom` 读三步快照。
  **据此抓出并修掉四个真缺陷**：
  1. `armResumeBar` 的 `if (candidate || …)` 写成「命中后仍继续覆盖」→ 一键续写挑到的是
     **最后一条**（已写完的任务），不是第一条没写完的；
  2. `refreshSubmitButton` 在 `done` 分支把基准文案写回初稿文案 → 交满两稿后按钮仍是
     「提交批改」；
  3. `busy(btn,false)` 在 `.finally` 无条件解禁按钮，把「两稿已完成」的 disabled 冲掉 →
     解锁后必须再按草稿状态刷一遍；
  4. 二次提交后状态行停留在「已恢复第 1 稿」，用户不知道刚交的是哪一稿。
  修后快照：initial `提交批改/可点/正文 0` → after-resume `提交修订稿/可点/正文 174/批改面板已开`
  → after-second-submit `两稿已完成/禁用/正文 212`。

## 6. 未验

真实账号下的续写体验（旧任务 tips 为空的观感、两稿封顶后的回看）与生产数据下的
`lastDraftNo` 分布，需用户线上验收。

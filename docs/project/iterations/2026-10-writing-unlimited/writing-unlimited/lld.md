# 写作工坊放开修订次数（magicbook R190）· LLD

**状态**：已上线（2026-10-21，develop `977636ee`，fnOS 构建 END OK + 部署 SUCCESS，容器 healthy；线上 `learning-writing.js` 已含新状态机）

## 1. 问题与承接

用户报障：恢复历史写作任务、修改正文后，提交按钮不可点，文案「两稿已完成」。
排查确认不是渲染缺陷——R168 的设计规则是「每任务两稿封顶」（moon-well 50513），
前端 `refreshSubmitButton` 在 `lastDraftNo >= 2` 时主动 disable。

用户拍板**放开两稿上限**（同源 moon-well R192：`revise` 按已有最大稿号顺延，
第 3、4…稿均可批改并对比上一稿）。本轮 magicbook 侧只改状态机与文案。

## 2. 前端改动

`cps/static/js/learning-writing.js`

- `refreshSubmitButton`：删除 `done` 分支与 disable；只按「有没有交过稿」决定文案
  （0 稿＝提交批改，≥1 稿＝提交修订稿），按钮始终可点；在途锁仍由 `busy()` 负责。
- `submit` 回调：状态行统一为「第 N 稿已批改，可在上面改完再提交」，删除
  「两稿已完成——只能回看」分支。
- `statusLabel`：历史行状态改为「已交 N 稿 · 可继续修订」；未写过仍是「还没开始写」。
- `armResumeBar`：稿件没有「完成」终态，改为固定指向**最近一次写作**（列表第一条），
  标签显示「题目… · 稿状态」；无历史则隐藏。

`cps/templates/learning_writing.html`

- 一键续写按钮文案：`Continue your last unfinished draft` → `Continue your last writing`。
- 批改面板提示补一句「修订次数不限」。

## 3. i18n

- `scripts/generate_i18n_seed.py` 追加 JS 新词条 `Draft {{n}} reviewed · can keep revising`。
- `messages.po` 新增三条译文并 `pybabel compile` 重编 `.mo`：
  上述状态词、`Continue your last writing`、新的批改面板提示。
- 旧词条（`Both drafts finished` 等）保留为未引用词条，不影响运行时（生成器契约只查
  「JS 用到的必须在种子里」，不要求反向清理）。

## 4. 测试与验收

- `test_learning_proxy.py::test_writing_page_wires_the_resume_ui`：续写 UI 接线不回归。
- `test_learning_pages_static.py`：`sw-w-*` 元素注册表与模板双向锁不回归。
- `test_i18n_seed_contract.py`：新 mbT 词条进种子、po/mo 有中文译文。
- 开发态闸门：`pytest tests/test_learning_proxy.py tests/test_learning_pages_static.py tests/test_i18n_seed_contract.py`。
- 真机验收：恢复一个已交 2 稿的历史任务 → 按钮为「提交修订稿」且可点 → 改正文提交
  → 返回第 3 稿批改与进步确认；历史行状态变「已交 3 稿 · 可继续修订」。

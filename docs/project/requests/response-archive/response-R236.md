## 2026-10-28（R236：弹层恢复「整本任务」入口——跳完整详情页的普通链接）

### R236（用户：「弹层里恢复『整本任务』按钮。不要做其他的」）

- **结论先行**：已完成并上线待验收。范围严格限定为用户点名的这一件事：弹层里恢复入口；未动弹层书名链接、未做「面板进弹层」方案、未改门禁拍板。
- **定性**：R214 子项 C 的修复 `42ddfb19`（开面板按钮加 `not is_xhr` 门禁）引入的可达性回退——完整详情页在 UI 里没有普通左键可达路径（书卡封面/书名链接全部被 `data-toggle="modal"` 截去 `#bookDetailsModal`），管理员入口事实不可达。挂 R214 修复，不建独立 idea。
- **实现**（`detail.html`，最小 diff）：原开面板按钮行（`whole-book-panel-open`）原样不动；紧随其后新增 `{% if current_user.role_admin() and is_xhr %}` 分支渲染普通链接 `<a class="btn btn-default" id="whole-book-panel-link" href="{{ url_for('web.show_book', book_id=entry.id) }}">整本任务</a>`。同 URL 不带 `X-Requested-With` 头即渲染完整详情页，面板在完整页内照常打开；不挂 `data-toggle`/`data-target`（data-api 与 `#bookDetailsModal` 抢点击，`42ddfb19` 同款教训）。门禁不变：仍是管理员专属（R214 拍板①）。
- **守卫**：新增 `test_xhr_modal_entry_is_full_page_link`（链接指向 `web.show_book`、无 data-api、`role_admin` + `is_xhr` 双门禁，反向变异报红）；既有四条守卫（admin 门禁 / data-api 禁用 / XHR 隐藏开面板按钮 / 旧三按钮不复活）原样通过、语义未动。
- **测试**：定向回归 `test_book_detail_r214.py` + `test_whole_book_estimate.py` 50 passed；detail/show_book 相关全量 4 文件（含 `test_word_detail_batch_r176.py`、`test_onboarding_tour.py`、`test_auth_reader_covers_r225.py`）108 passed / 0 failed。
- **文档四问**：能力/契约未变（入口可达性恢复，L1/L2 无需动）；实现与边界 → LLD `iterations/1.0/r214-book-detail/lld.md` §15 + 状态行回填。
- **驻留与闸门**：worktree `../magicbook-r236-wholebook-modal-entry`（分支 `fix/r236-wholebook-modal-entry`，实现 `6180c6bc`，基线 origin/develop `ffc70a3e`）merge 后原样保留待验收；验收通过后 `git worktree remove` + `git branch -d`。真机验收项：管理员账号在书库列表点开任意 epub 书弹层 → 按钮行出现「整本任务」→ 点击落在完整详情页且页内「整本任务」按钮可开面板；普通账号弹层内不出现该入口。
- **窗口**：写入前 10 节已满，按「写入即检查」把最早 R225 整节原样搬至 `response-archive/response-R225.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 236 已从占位回填；本条为回应。冲突记录：无撞号（claim.sh 占号 `ffc70a3e`）；R235 为并行会话占号，未触碰。

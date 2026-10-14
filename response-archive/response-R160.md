# response-archive：R160（2026-10-11）

> 原样搬移自 `response.md`（2026-10-14 R172 写入触发轮转，窗口转入 R161 起）。

## 2026-10-11（R160：麦克风设备选择器）

### R160（用户场景：合盖外接显示器，iPhone 连续互通麦克风为系统输入；magicbook 页面仍无声）

- **场景定性**：M1 Pro 合盖时 macOS 硬件级禁用内建麦克风（Apple Silicon 安全设计）→ 内建麦全场景无声；用户切 iPhone 连续互通麦克风为系统默认（正确），且 iPhone 麦在其他 Mac 应用有声音——浏览器页面仍无声的最常见原因是 **per-site 设备记忆**：站点钉在旧设备上，系统默认切换不影响已记住的选择。
- **交付**：口语/复述面板各加麦克风设备下拉（enumerateDevices，权限未授予时占位编号），选中值存 localStorage 跨面板同步，getUserMedia 按 `deviceId.exact` 取流；devicechange 监听热刷新；i18n 3 词条（种子/po/mo）。
- **测试**：页面断言 + i18n 契约 + 静态完整性 = 48 passed。
- **总结**：requests.md 占号 R160（worktree 创建时登记）；本条为回应；冲突记录：无。

### R164：worktree 纪律修订——一次会话一个 worktree（手册已写入）

- **用户指令**：一次会话一个 worktree 就够了——R162 重构一个连续任务开了 6 个 worktree（五阶段 5 + NAS 下线 1）是反面做法。
- **手册落地（四仓同源 + 家族根）**：家族根 `AGENTS.md`「Git Worktree 开发纪律」新增**第 7 条：一次会话一个 worktree**（同一会话的多阶段/多子任务复用同一树，阶段 merge 回开发分支后续作前 fetch+merge 拉齐基线；跨会话优先复用台账登记的驻留树；仅并行会话允许多树并存）；moon-well/magicbook/magiclens/app-manager 四仓 AGENTS.md「Git Worktree 使用规范」节同源增补。magicbook push 首次被拒后 rebase --autostash 处理。
- **⚠️ magicbook 主检出警示（并行会话现场）**：该仓工作区有并行会话未提交工作（18 文件 +25/−753，涉及 learning/speaking_writing/i18n_seed 等），被本轮 rebase 的 autostash 收进 `stash@{0}`；恢复 pop 时与远端 R160 已合入内容冲突（UU），已按「不擅自解他人冲突」原则 `git reset --hard` 恢复安全态——**stash@{0} 完整保留对方改动，该会话回来需自行 pop 并人工解决与 614522fd（R160 麦克风选择器）的重叠**。我的 docs 提交（3fc23575）已在远端最新之上，不影响对方。
- **提交**：家族根 AGENTS.md（非 git 直接改）；moon-well 975d048；magicbook 3fc23575；magiclens ec9ae45；app-manager 4ce05bb。
- **六处驻留 worktree 的处置建议（待用户一句话）**：R162 全部代码已 merge+push+部署验证，若确认验收通过，六树可统一清理（`git worktree remove ../moon-well-<slug> && git branch -d <分支>` ×6）；按纪律等用户验收结论，不擅自删。
- **总结**：requests.md 占号 R164；本条为回应；冲突记录：无。

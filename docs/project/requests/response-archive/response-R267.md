# 回应归档 · R267

## R267 · 重写 GitHub README：核心功能与入门用法（2026-11-02）

### R267（用户：「修改一下 github magicbook 和magiclens的 readme。把核心功能 入门用法讲明白」）

- **做了什么**：仓库根 `README.md` 原样是上游 Calibre-Web 的 README（徽章/安装/排障全是上游内容），整体重写为本仓产品 README：一句话定位 + 在线站点与邀请制、项目三件套表（magicbook / moon-well 私有 / MagicLens）、核心功能按 书库/阅读器/词汇/每日学习/AI 伴读/积分账号 六组、快速上手七步（登录→引导→词汇量定档→分级选书→查词听书→每日复习→可选装扩展）、架构 mermaid（ES/MinIO 缓存、NAS 本地 Qwen3-TTS、LLM 网关）、本地开发四行命令、fork 致谢与 GPL-3.0 声明保留。内容口径以 L1（`docs/product/readme/`）与功能地图为准，未新增能力描述。
- **push 决策（用户拍板）**：本地 develop 有 10 个未 push 提交（R262/R264/R265，前序会话「push 即自动部署待验收」留置），用户选择**连同一起 push 上线**。push 前按正式发布态闸门跑全量单测。
- **闸门（全量 1270 passed / 0 failed）**：首跑 1 failed——`test_auth_reader_covers_r225.py::test_permission_hints_are_compiled_into_chinese_catalog`。定性：**预存破损**（origin/develop 同样失败，非本批 10 个提交引入）：R257 改权限提示文案后，同文件顶部 `R225_MSGIDS` 仍列 3 条已被移除的旧串（`.po` 中已是 `#~` 废弃条目），断言 `.mo` 含其译文必红。修复=把断言列表对齐 R257 现行 4 条文案（`detail.html` 实测 + `.po` 激活译文逐条核对），`31e87b6e`。
- **上线**：`711f6065..4454e9f2` push `origin/develop`（含 R262 计费修正 / R264 BBC 原声近似高亮 / R265 积分站内信渲染 + README + 闸门修复），fnOS 链构建部署（含代码，不属 docs-only 跳过）；R263 此前已在线。**GitHub 落地页 README 显示的是 `master`**，README 提交 `4454e9f2` 经临时 worktree cherry-pick 至 master（`a712694c..5b01c880`，只带 docs 提交，未做 792 提交的正式发布 merge——master 上另有 2026-09-08 两个旧提交，正式合并留作单独发布决策）。
- **台账顺手处置**：① 本次 merge origin/develop 时发现 requests.md 内嵌**上次 merge（6bd15ec7）提交时残留的冲突标记**（HEAD vs feat/r264 嵌套块），已在合并解决中清掉，264 完整条目去重为一次；② 发现 **258 编号重复**（占号条与完成条并存）为两边既有历史，按「不修改既有记录」纪律未动，留此存证。
- **magiclens 同题**：用户同指令改 magiclens README，见 magiclens 仓 response.md R58（随 r57 一起 push develop，未触发 Release）。
- **追加（同日用户指令「都 push 到 master」）**：执行正式发布合并——临时 worktree `../magicbook-r267-release-master` 内 `merge origin/develop` 成 `61deacf7` push `origin/master`（`5b01c880..61deacf7`），master 从落后 792 提交变为全量发布态。冲突裁决：`epub.js` 以 develop 为准（master 独有的 2026-09 `a712694c` 章节标题修复已被 develop `currentChapterTitle()` 取代，生产数月即跑此实现，复活旧补丁会双写且偏离已验证行为）；`docs/reading-vocabulary.md` 按 develop 删除（已迁 `docs/product/`）。README 两侧同内容自动归一。合并点全量单测 **1273 passed / 0 failed**（含并行 R268 新增 3 条）。同轮事实：magiclens 无 master 分支（landing=develop 已生效，遗留 main=init 骨架落后 94 提交未动）。

- **总结**：requests.md 条目 267 已回填；R254 回应整节搬至 `response-archive/response-R254.md` 并登记行内索引，本条写入后窗口 10。冲突记录：requests.md 与 origin/develop 台账冲突已按并集解决（本地完成条 + 远端 266/267 占号行）。

# 回应归档 · R260–R261

## 2026-10-31（R260：AI 了解我——用户自我介绍与系统提示词注入）

### R260（用户：「AI应该了解用户才能更好的跟他聊天，帮助他。AI伴读那里增加一个用户填写自我介绍的部分，并把这部分内容放到系统提示词里。」）

- **结论先行**：已在 AI 伴读记忆面板顶部增加「AI 了解我」，保存后由 moon-well 在书内与网页伴读的每次问答中注入系统提示词。用户主动声明的背景与 AI 自动抽取的长期记忆保持分层，互不覆盖；当前状态为**已上线待验收**。
- **后端（moon-well R234）**：新增 `ai_user_profile`，每用户一行、上限 2000 字符、清空即删行；`POST /ai/agent/profile` 读取、`POST /ai/agent/profile/save` 保存，身份只取 `UserContext`，统一返回显式 `Result` 包装。`/ai/agent/profile*` 整路径排除 HTTP 请求/响应日志。
- **提示词注入**：两套默认模板、Nacos 在线模板与渲染异常兜底路径均支持 `{{userProfile}}`。先补伙伴名、最后回填用户正文，防止正文中的伙伴名压掉名称段；用户正文中的 `{{memory}}` 等变量保持字面值，`& < >` 转义后放入 `<user_profile>`，并声明其不能改变角色、权限、工具或安全规则。空档案不留下空标题，旧在线模板缺段时安全补注一次。
- **前端（magicbook R260）**：记忆面板支持加载、编辑、实时 2000 字计数、保存、二次确认清空以及加载/保存/清空错误态；新增两条薄代理连接 moon-well。用户文本只用 `.val()` 渲染，不拼 HTML；固定提示不要填写密码、密钥、证件号等敏感信息。新文案已进入 i18n seed、中文 `.po` 与编译后的 `.mo`。
- **测试**：后端 5 类定向回归 **49 tests / 0 failures / 0 errors / 0 skipped / BUILD SUCCESS**（JDK 25.0.2），正式发布态全量 **1715 tests / 0 failures / 0 errors / 0 skipped / BUILD SUCCESS**；前端 `test_ai_agent_proxy.py` + `test_ai_user_profile_r260.py` **14 passed**，正式发布态全量 **1251 passed / 0 failed / 4 warnings**，`node --check cps/static/js/ai_chat.js` 通过。
- **测试环境**：按用户最终确认口径从 fnOS `/app/moon-well/.env` 取得依赖环境，MinIO 使用群晖 `http://192.168.31.10:9000`；本轮功能测试不实际读写 MinIO，该地址与现网 `.env` 和 `/ops` 一致。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → 新建 `docs/product/companion/features/user-profile.md`；本次实现 → `docs/project/iterations/1.0/r260-ai-user-profile/lld.md` 与迭代 `plan.md`。后续结构化档案与 AI 摘要方案记录在 LLD §8，不阻塞本轮首版。
- **上线**：已按 moon-well 代码 → magicbook 代码 → Nacos 提示词的顺序完成。moon-well `dd471fc8ad4234d49fd0a6acf0015a387f349dbf` 与 magicbook `7b96323e2f5ce04d7d06bbffb41b42e829b61862` 均已推 `origin/develop`；两仓 fnOS 构建均 `END OK`、部署 `SUCCESS`，moon-well 蓝绿切到 `moon-well-blue`、magicbook 容器 `running/healthy`。moon-well 镜像 `house.code-digest=5d04b43e275e5f44`，magicbook 镜像 `house.code-digest=92f502a325ca3318`。
- **Nacos / MinIO**：`agent-chat-system` 与 `agent-chat-system-web` 均从 `1.2.0` 发布到 `1.3.0`，逐字预检与回读 PASS，字符数分别为 917 / 943；Nacos 审批流水线返回 20002 时按脚本既定逻辑回落 `force-publish`。MinIO 保持群晖 `192.168.31.10:9000`，未改生产 `.env`；下一轮结构化档案 + AI 摘要优化本轮不做。
- **状态与驻留**：两仓均为**已上线待验收**。PingCode Ship 需求 `MB-237`、PJM 用户故事 `MB-22` 均为进行中，待验收通过后流转完成。moon-well worktree `../moon-well-r234-ai-user-profile`，分支 `feat/r234-ai-user-profile`；magicbook worktree `../magicbook-r260-ai-user-profile`，分支 `feat/r260-ai-user-profile`，按闸门保留。
- **窗口与总结**：写入前 `response.md` 为 11 节；按「写入即检查」把最早 R249、R250 两节原样搬至 `response-archive/response-R249-R250.md` 并登记索引，新增 R260 后恢复 10 节。requests.md 条目 260 已从占位回填；本条为回应，冲突记录已并入上面的 MinIO 环境项。

## R261 · Jinshu 借鉴三件套：行内生词释义/Book Fit 话术/复习小件（2026-11-01）

### R261（用户：Jinshu 调研后拍板「gloss 做成可选功能默认不启用；纠错上报不做我们有 AI；Book Fit 话术借鉴；复习 UX 小件做到学习模块默认不开启；墨水屏不做」）

- **结论先行**：三项全部实现并开发态全绿，待验收。A=阅读器行内小字释义（设置弹窗开关 localStorage 默认关，`markVocabulary` 双守卫挂 `data-gloss`，READER_TOOLS_STYLE 注入 iframe 的 `::after` attr 渲染不占文档流，切换 `ReaderVocabGloss.remark` 缓存重标零新请求；数据接 moon-well R236 analyze `gloss`）；B=选书页「~N 个重复出现的超纲词」行（`repeatedUnknownCount` null 容错隐藏）+ 样例词放宽 正合适/挑战读；C=学习抽屉「复习小件」两开关（复习卡来源书 chip 只亮书名 / 学习入口待复习角标镜像判关零请求）。
- **测试**：新增 `test_r261_jinshu_borrow.py` 8 条静态锁；开发态合计 230 passed（i18n 契约 5 + learning 五件 160 + reading_vocabulary/lens_handoff/learning_story 62），改动 JS `node --check` 全过。
- **i18n**：五步链全走，6 新词条（模板 4 + JS 2）入种子/zh po/mo；`generate_i18n_seed.py` 重跑（JS 清单 26 文件、msgid_count 494→517，顺带治愈 develop 漂移）。
- **文档四问**：能力→`readme/reading.md`（行内小字释义）+`readme/learning.md`（复习小件/Book Fit 话术/chip）；契约→`reading-vocabulary.md`（analyze 响应结构 R139 后再更新：+gloss）；实现/边界与本次实现→`project/iterations/2026-11-jinshu-borrow/lld.md`（状态：已开发待验收）。requirements 基线落 `learning/requirements.md`（含两项不做决策）。
- **PingCode**：idea `MB-238`（进行中）。后端 moon-well R236（LLD/SQL/基线权威在那边）。
- **状态与驻留**：开发完成待 merge/验收。worktree `../magicbook-r261-jinshu-borrow`（分支 `feat/r261-jinshu-borrow` @ 989a46d1）。冲突记录：无撞号。requests.md 条目 261 已回填。

# 回应归档 · R256–R257

## 2026-10-30（R256：黑盒体验报告四项缺陷——OIDC 建号侧栏位/空书架/已读歧义/实体解码）

### R256（用户全流程指令：黑盒测试 magicbook → 体验报告 → 设计方案 → 修复缺陷）

- **结论先行**：新用户临时账号（mbtester1030）全功能遍历产出体验报告（4 Bug+9 疑惑点+10 设计不合理）；本轮修复其中 4 项有代码级根因且可测的缺陷。
- **根因与修复**：B1 OIDC 建号漏设 sidebar_view（列默认值 1 只含 DETAIL_RANDOM 位），浏览路由 check_visibility 位缺失 abort(404)——修法=收拢 `oidc.create_oidc_user`（角色/语言/侧栏位一次取齐，侧栏位取 config_default_show 与本地注册同口径），生产实验已闭环验证因果（恢复 262143 后 /author 立即 200，2 分钟复查无改写者）。B2 create_edit_shelf 补空标题校验（flash+redirect）。B4 详情页阅读状态开关 label 弃用 msgid "Read" 改 Reading status（po/mo 同步「阅读状态」），msgid "Read" 原译保留给筛选器场景。B5 learning-common.js 新增 decodeHtmlEntities，loadMaterials 的 title/author 进 textContent 前解码（听写/复述/重读共用）。
- **修复范围裁决**：B3（删除书架 div 按钮无反应——main.js:787 绑定存在）/B6（听写载入段落无响应）在自动化环境无法证伪，报告存疑待真机复核，本轮不修。九项疑惑点的设计方案（专名误判黄金区、生词本入口、管理员文案分离等）在 `magicbook-产品设计方案-2026-10-30.md`，未夹带开发。
- **测试**：新增 `tests/test_newuser_sidebar404_r256.py` 10 用例（建号位组合/九浏览位覆盖/config 未初始化/helper 三项取齐/空标题参数化+正常对照/po+mo 双侧/JS 解码契约）；`TestCallbackContract` 2 用例随收拢结构演进（意图不变）。定向回归：oidc 全家+home/shell+detail+advsearch+i18n 契约+learning 三件套全绿（最后一批 33 passed）。
- **文档四问**：能力→无变化；契约→无变化；实现/边界→`docs/project/iterations/1.0/r256-newuser-sidebar404/lld.md`；本次实现→同 LLD。**存量数据修复 SQL 在 LLD §2.1**（上线后需在 fnOS 执行一次：sidebar_view=1 的存量 OIDC 用户回填 config_default_show）。
- **状态与驻留**：**已 merge 待 push/待验收**。主检出 develop `c3badf9e`（含占号 db3f445f）；worktree `../magicbook-r256-newuser-sidebar404`（分支 `fix/r256-newuser-sidebar404`）按闸门保留。push 触发 fnOS 自动部署+存量 SQL 待执行，本轮按「外向动作先确认」等用户拍板后再推。
- **窗口与总结**：写入前 10 节，新增后 11；按「写入即检查」把最旧一节（R246）原样搬至 `response-archive/response-R246.md` 并登记索引，窗口恢复 10。冲突记录：无撞号。

## 2026-10-31（R257：按产品设计方案实施七个可落地项）

### R257（用户拍板「按照设计方案修复」）

- **结论先行**：设计方案十个方案按文档自身 ⚡/🏗 标记与「不做什么」原则裁剪——本轮实施一/三/四/六/七/八/九，二/五/十（跨仓生词判定/充值卡重排/已读数据诊断）登记待拍板，未夹带。
- **实现要点**：①render_template 删除非管理员 Downloaded Books else 分支（books_list download 页双门槛必 404）；②review 空态改排程解释+测试结果旁直达复习队列（vt-notebook-link-row）；③detail 下载/阅读两处权限提示去「Users → Edit User」后台路径；④credits.js 三处 t() + buddy.js 稀有度字面量映射 + seed 脚本自动/手动补 7 词条 + po 8 条；语言菜单收敛（常用三项+当前语言直出、其余折叠、完整列表留 /me）；⑤index.html 移除难度横幅 include（模板保留）；⑥update_preferences 分场景 flash+next 白名单（防 openredirect）；⑦删除书架 div→button（form 内显式 type）+侧栏/详情页空名兜底「未命名书架」。
- **认知修正**：体验报告 B3「删除书架无反应」系自动化环境假阴性——main.js confirmDialog 确认流程原本存在；本轮仅做语义修复。
- **测试**：新增 test_design_plan_r257.py 20 用例；契约演进 4 处（横幅移除/权限文案 ×2/R212 locale 钉到 create_oidc_user——R212 文件系 R256 收尾漏跑，本轮全量暴露后一并钉住）。全量回归 **1228 passed / 0 failed**（跳过 test_ai_agent_proxy 网络依赖与 slow）。
- **文档四问**：能力→readme 随验收回填；契约→/me/preferences 新增可选 next 字段（站内白名单）；实现/边界→`docs/project/iterations/1.0/r257-design-plan-fixes/lld.md`。
- **状态与驻留**：**已 merge 待 push/待验收**。develop `5e03f189`；worktree `../magicbook-r257-design-plan-fixes`（分支 `feat/r257-design-plan-fixes`）按闸门保留；push 触发 fnOS 部署，等用户拍板。
- **窗口与总结**：写入后 11 节，按「写入即检查」把最旧一节（R247）原样搬至 `response-archive/response-R247.md` 并登记索引，窗口恢复 10。冲突记录：无撞号。

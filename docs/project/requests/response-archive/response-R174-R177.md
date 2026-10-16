# response-R174-R177.md — R174 / R176 / R177 归档

> 从 `response.md` 原样搬移（2026-10-16 R185 写入触发轮转，窗口回 10 条 request 内）；只搬移原文，不总结、不改写、不改编号。

## 2026-10-15（R174 架构评审任务拆分建档，只写文档）

### R174（家族根架构评审任务拆分建档：B1–B8 + DF1–DF8 落档，未做开发）

- **范围**：阅读家族根 `../docs/architecture-review-2026-10-14.md`，将其中本仓相关结论（§2.2 B1–B8、§3.2 严重度标记、§2.5 X1/X2 本仓部分、§5 冲突清单）拆分为待办任务落档。**零代码改动**（cps/ 与前端未触碰；纯文档任务不建 worktree）。
- **建档**：新建 `docs/feat/arch-review-2026-10/design/` 三份——
  - overview.md：任务总表（B5 波 1【X1】/ B1 波 2 / B2、B4 波 3 / B6、B7 波 4 / B3、B8 未排 + DF1–DF8）+ 跨仓协同表 + 执行纪律（web.py/epub.js 拆分以「上游 merge 冲突面下降」为第一判据）；
  - refactor-items.md：每项含现状问题、任务内容、验收判据；B1 消灭 `_moonwell_proxy` 二元组/三元组隐式契约；B4 验收含 R172/R173 已修缺陷不回退；
  - doc-fixes.md：DF1/DF2 S1/S2 状态滞留（product-review 自称已修但未落地的正面反面样本，回填前须核实 git 实况）、DF3 N2 端口 8085→8083、DF4 K1 旧域取代注记、DF5 悬空 feat + L1 计数 12→16 失实、DF6 L2 覆盖 2/7 口径明示、DF7 project-describe 空壳待用户决策、DF8 仓库卫生（删除前须用户确认）。
- **索引登记**：L1 `docs/readme/readme.md` 末尾加「开发者入口（非用户能力）」导航行指向新 overview。
- **跨仓**：四仓同源建档（moon-well R180 / magiclens R45 / app-manager R42）；X1（B5 与 moon-well M4 / magiclens L1 同窗口）与 X2（三组镜像向量）协同口径见家族根 `../docs/arch-review-2026-10-tasks-crossrepo.md`。
- **总结**：requests.md 占号 R174；response.md 本条（窗口 9 个 request，未触发轮转）；冲突记录：无。

### R176（发布固化：release/2026-10-15 分支 + ACR 镜像固定 tag；同源 moon-well R182）

- **分支**：`release/2026-10-15` 从 origin/develop 最新点 `9fe8fd20`（阅读页 CSP 放行 MinIO 外网源，R175）切出，已 push 远端。基线对应：当日 11:28 `build END OK (9fe8fd20)` —— 分支基线 = 线上运行代码，零漂移。
- **镜像固定 tag（ssh fnOS 执行）**：`magichouse/magicbook:release-2026-10-15` ← `:latest` 快照，经 `docker tag` + `docker push` 重打，**与 latest 字节级同 manifest digest `sha256:634de7e9...`**（同源 moon-well 侧为 image ID 一致、外层格式 schema2，见其 R182 记录）。部署引用未动（compose 仍 `:latest`），零上线风险。
- **回滚姿势（已写入 ops/apps/app-magicbook.md 部署表回滚点行）**：从 registry 拉 release tag 覆盖本地 latest 后 `up -d`；固定 tag 约定同 moon-well：大版本补打 `release-YYYY-MM-DD`，平时发版 `:latest` 原地更新，旧 release tag 永不被覆盖。
- **总结**：requests.md 占号 R176；response.md 本条；冲突记录：无（R175 为远端并行提交已占，按全史最大 +1 顺延）；fnOS 操作经 Tailscale SSH（方案经用户在线确认）。

### R177（架构评审波 1 · B5：统一 API 公共层 common/api.js，X1 本仓部分）

- **交付（commit `e750a739`，分支 `refactor/r177-unified-api-client`，已 merge 本地 develop）**：
  - 新增 `cps/static/js/common/api.js`（window.MBApi）：csrfToken 三形态链式探测、httpJson/getJson/postJson 基元、**unwrapResult 容错解包**（success===false 抛 message；success===true 含 result 字段解出；非信封 HTML/网关错误/裸数组原样返回不误判——与 moon-well M4 兑底后形态兼容）+ **unwrapStrict**（learning/credits 原口径保持）；
  - 四份副本收编：learning-common 四件套委托（MBLearning 导出名不变，九页零改动）、ai_chat（getCsrfToken/unwrap 委托）、credits（CSRF 快照改运行时探测、unwrap 迁 strict）、vocab-test（csrf 委托；wrap/codeOf/loadHistory 静默降级为页面状态机 **AC-C1 依据注释自证，保留不解包**）；
  - 模板：layout.html 全局 + read.html / reading_settings.html（独立骨架）各自引入，C4 契约锁载入顺序。
- **验证**：新增 `tests/test_common_api_contract.py` 6 例静态锁（C1 导出齐全 / C2 三形态 CSRF / C3+3b 迁移单点 / C4 模板顺序 / C5 失败必须可见）全绿；i18n 契约 JS_FILES 登记 api.js（兑底文案走 mbT）；**全量 545 passed 零回归**；node --check 五文件通过。
- **台账**：worktree `../magicbook-arch-b5`（分支 `refactor/r177-unified-api-client`，merge commit `e750a739`）驻留待验收，验收通过后 remove + branch -d。未 push（push 即上线，待用户指令）；真机验收点：阅读页 AI 抽屉会话/记忆面板、词汇量测试、积分页余额/套餐、每日学习各页。
- **X1 合围进度**：moon-well M4（兑底）+ magicbook B5（统一解包）已落地待验收，magiclens L1（rpc 门面）后补即三端合围验收。
- **总结**：requests.md 占号 R177；冲突记录：无。

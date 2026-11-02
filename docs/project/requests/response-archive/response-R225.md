# response 归档：R225（2026-10-25）

> 从 response.md 原样搬移（2026-10-28 R236 写入使窗口超 10 条，按「写入即检查」搬最早条目）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-25（R225：邀请注册跳转、普通账号阅读/下载 403、品牌封面占位）

### R225（用户：注册直接失败 + 普通账号阅读下载 403 + 无封面白字占位；「验证这些问题，如果确实存在修复他们」）

- **结论先行**：三项均真实存在，已修复并上线。分类为缺陷，挂既有 R219（邀请注册）/ R211（OIDC 角色）/ R214（详情与读者入口）；PingCode 工作项待建。
- **注册（已证伪「邀请过期」）**：`/oidc/signup` 原先把 `itoken` 与 `next` 组成内层 query，再整体塞进外层 `query`，实际跳转成 `?query=itoken%3D...%26next%3D...`。Authentik 2025.10.2 的 `FlowInterface` 又把浏览器原始 search 作为 executor API 的 `query` 入参，最终变成 `query=query%3D...`，无法解析邀请；顶层 `?itoken=...&next=...` 才能正常返回注册首步。修法：`cps/oidc.py::signup()` 与 `scripts/rotate_authentik_invite.py` 只生成顶层参数；`_invite_token()` 优先读顶层，仍兼容历史嵌套 env，避免部署瞬间关闭注册入口。
- **阅读与下载（分开定性和修复）**：生产 `config_default_role=0`，而 OIDC 新账号严格继承该值，导致不含 `ROLE_VIEWER=256`，`/read/...` 的 `@viewer_required` 一律 403。R225 起 `site_default_role()` 强制补 `ROLE_VIEWER`，继续剔除 `ROLE_ADMIN`；**不自动补 `ROLE_DOWNLOAD=2`**，因为下载是独立的整本文件权限，不能借“修阅读”顺手放开。详情页现在分别在账号被关阅读位/下载位时显示锁定提示，并写明到「用户 → 编辑用户」开通 View / Download，而不是让用户撞 403 后猜。
- **存量账号（未擅改生产库）**：新增 `scripts/reader_role_audit.py`，默认 dry-run 列缺阅读位账号；`--grant-viewer` 必须点名 `--ids` / `--emails`，只补 `ROLE_VIEWER`，写前备份 `.r225-bak-*`。只读核查时 `uxprobe2`（id=9）与 `uxprobe`（id=10）角色均为 0；建议验收时明确批准后执行 `python3 scripts/reader_role_audit.py --grant-viewer --ids 9,10`。同时修正 `oidc_admin_audit.py --demote` 的语义漂移：降级目标从“默认角色剔除管理员位”改为“默认角色补阅读位并剔除管理员位”，避免把存量超管降级后又变成读不了书的账号。
- **封面**：确认 `cps/static/generic_cover.jpg` 原本就是白底黑字的 `Cover not available`。替换为 564×800 深墨绿品牌封面，沿用 `get_cover_on_failure()` 单点回落，首页、详情、OPDS 等所有缺封面路径共用，不改 URL 与缓存语义；已目视检查。
- **测试**：定向回归 **90 passed / 0 failed**（`test_oidc_signup.py` / `test_oidc_admin_role.py` / `test_auth_reader_covers_r225.py` / `test_reader_role_audit_r225.py` / `test_book_detail_r214.py`），发布态全量 **961 passed / 0 failed**（4 个非阻断 warning）；另做反向变异：删除详情页 Download 提示后守卫报红，恢复后 27 passed。新增中文词条已进 `zh_Hans_CN` PO/MO，守卫从编译后 `.mo` 取词，防止“PO 正常、运行时英文”。
- **文档四问**：能力 → L1 `readme/library.md` 补无封面品牌占位，`readme/admin.md` 说明新账号阅读/下载边界；契约/边界 → L3 `admin/features/oidc-self-registration.md` 与 KB `oidc-login.md` 修正邀请链接形式、角色语义与两个修正 CLI；本次实现 → LLD `iterations/1.0/r225-auth-reader-covers/lld.md`（状态：已上线待验收）；`REQUIREMENTS.md` 与迭代 `plan.md` 同步。
- **上线实况**：修复提交 `53e2e662` 已 merge 到 `develop`（`b1f4d9e6`，最终 `890bc607`）并 push。GitHub webhook 对最终提交投递超时（500），fnOS 未自动接到构建；按脚本契约手动执行 `build-magicbook.sh refs/heads/develop 890bc607...` 补发成功。生产容器 `healthy`，`house.build-sha=890bc607...`；线上 `/oidc/signup` 已是顶层 `itoken` / `next` 且 Authentik 邀请页 200，品牌封面 81,048 字节并与仓库一致。
- **驻留与闸门**：worktree `../magicbook-r225-auth-reader-covers`（分支 `fix/r225-auth-reader-covers`）原样保留待验收，验收通过后 `git worktree remove` + `git branch -d`。真机验收项：干净浏览器从 `/login` 完成注册并回站登录；批准后给 `uxprobe2`/`uxprobe` 开 View 再打开 `/read/223/epub`；首页无封面书检查品牌图。下载权限若也要开放，须单独授 `ROLE_DOWNLOAD`，不与阅读权限捆绑。
- **窗口**：写入前已满 10 节，按「写入即检查」把最早 R217 整节原样搬至 `response-archive/response-R217.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 225 已从占位回填；本条为回应。冲突记录：无撞号；生产存量账号未改，需按点名清单另行批准；R225 与此前 R219 的“嵌套 query”结论相反，已在 L3 / KB 明确标为现网 2025.10.2 复核后的现行口径，历史 R219 记录保留不改写。

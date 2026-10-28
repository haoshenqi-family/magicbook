## 2026-10-25（R229：缺陷修复——/home 随机发现 linked Row 致生产登录落点 500，挂 R213）

### R229（博客截图会话中发现的生产缺陷）

- **任务定位**：缺陷修复（挂 R213 首页）。发现路径：为写产品功能博客做生产截图，打开 `/home` 直接 500（traceback 落在 `home.html` 随机发现块 `book_card(book)` 的 `url_for(book.id)`）；对所有开启「随机发现」的用户均复现，当晚 R227 镜像上线后被掩盖的窗口未知，属生产登录落点级故障。
- **根因**：`random_discover_books` 复用 `generate_linked_query`（返回 `(Books, is_archived, read_status)` 三元组）；旧 `index.html` 侧取 `entry.Books`，R213-C 的 `home.html` 把 Row 原样传给共享宏 `_book_card.html`（只认 Books 实体）。既有测试对 `random_discover_books` 全部打桩，真实返回形状从未被守卫——打桩护住了组装、漏了形状。
- **修复**：`cps/routes/home.py` 取 `row.Books`（Python 侧收敛形状，模板契约与其余两块一致）；新增回归测试 2 条：`test_random_discover_returns_books_entities`（仿 linked Row 断言必须返回 Books 实体）、`test_random_discover_swallows_upstream_failure`（上游抖动返回空列表，登录落点不许 500）。
- **验证**：`tests/test_home_route.py` 定向回归 **29 passed / 0 failed**（27 旧 + 2 新）。push `develop`（`c0a7311c`，经 `fix/r229-home-random-row` 分支直推 origin，未动被并行会话占用且处于 detached HEAD 的主检出）；fnOS 自动构建部署，生产实测 `/home` 四块完整渲染（继续阅读带 `186/1467` 进度、今日计划、阶推荐、随机发现）。
- **过程合规备注**：主检出当时为并行会话 detached HEAD（R228 本地未推 2 提交），merge 冲突后立即 `--abort` 并还原现场，改从 worktree 直推 origin/develop（与 `claim.sh` 同款姿势，fast-forward 无历史改写）；主检出已还原为 972b3830。
- **窗口**：写入前已有 10 节，按「写入即检查」把最早 R214 子项 C 整节原样搬至 `response-archive/response-R214.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 229 已回填；本条为回应。冲突记录：无撞号；与 R228 并行会话无 git 冲突（分支隔离 + 直推 fast-forward）。

# response 归档 · R180（B2 前置小修：getcomic 死块清除激活 + gdriveutils 守卫化）

> 从 response.md 窗口原样搬移（2026-10-21 R190 写入触发轮转）。前后两节（R179 撤销尝试 / R181 小步重做完成）见既有归档与窗口。

### R180（B2 前置小修两项：getcomic 死块清除激活 + gdriveutils 守卫化）

- **getcomic 死块清除**：删除 web.py 1828/1874 两个游离 ''' 行——getcomic 路由从死代码（R178 发现、评审遗留待确认项）变为注册可用；**激活语义如实说明**：若你实际有意下线漫画功能，告诉我可改为删除该路由段（而非激活）。真机验证点：`/ajax/getcomic/<id>/<fmt>/<page>` 漫画页（需书库内有 CBR/CBZ 格式书）。
- **gdriveutils.py 守卫化**：① 148 行 engine 创建——gd_path 为 None（测试环境/未初始化）时用内存 sqlite 兑底（顺带修掉原实现的潜在 bug：`create_engine('sqlite:///None')` 会在进程工作目录建出名为 None 的库文件）；② 179 行 create_all 加 gd_path 判空跳过（消除 os.path.exists(None) TypeError，即 B2 迁移暴露的 import 时序炸点）。配置就绪时行为逐字不变；gdrive 功能侧经既有 is_gdrive_ready() 自然降级，永不触达内存引擎。
- **验证**：全量 **549 passed 零回归**；pytest 环境内核验 getcomic 路由已在 app.url_map 注册 ✓；语法双文件 OK。
- **台账**：worktree `../magicbook-arch-b5` 新增 commit（r179 分支上第三 commit），merge 前驻留待验收；未 push。
- **总结**：requests.md 占号 R180；B2 两大前置已清，小步重做可启动（方案与坑清单见 R179）；冲突记录：无。

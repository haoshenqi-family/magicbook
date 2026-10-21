### R179（架构评审波 3 · B2 尝试：web.py 蓝图分域——本轮未完成，已撤销回基线）

- **做了什么**：盘点 139 路由（core 原版 42 留守 + 定制 97：reading 31/learning 38/credit 19/vocab 9，read/show_book 两条原版阅读入口留在 web.py 不迁）；脚本化迁移 94 段（AST 分析各域依赖生成显式 import）；中途修复段切割的装饰器链 bug（`node.lineno` 不含装饰器行，需用 min(decorator_list.lineno)）与相对导入层级（routes 子包内 web.py 的一级相对导入需升两级 `from ..X`）。
- **为什么撤销**：迁移后暴露四类连锁问题，剩余上下文不足以安全收尾——① **gdriveutils.py:179 模块级 `os.path.exists(cli_param.gd_path)` 依赖 config 就绪**，routes 的 import 时序使其在部分初始化路径下 TypeError；② 游离 ''' 死字符串块（B1 遗留待确认项）在行删除后**语义扩大**——get_sort_function 与大段原版路由被吞进字符串（863-2303 行），basic.py:32 反向 import 连锁失败；③ 63 处测试桩点全打在 cps.web，routes 迁移后需再迁移；④ 直接 create_app 出现挂起（未定位）。已 `git checkout` 恢复 web.py 并删除 cps/routes/，**全量 549 passed 回到基线绿**。
- **留存成果（下轮小步重做的完整清单）**：① 域分类清单与 94 段行号映射（本条上方盘点，可重跑盘点脚本再生成）；② 迁移模式定案：延迟注册（web.py 末尾 register_domain_routes(web)）+ endpoint 名不变 + routes 子包内相对导入升两级 + AST 生成显式 import；③ **前置修复清单**：gdriveutils:179 的模块级 config 依赖改为函数内守卫（U 级小修）、getcomic 死块的处置（用户确认）、游离 ''' 清理；④ 分步纪律：**每迁一域跑一次全量**（reading→credit→vocab→learning 顺序，learning 最大殿后）；⑤ 桩点迁移预案（同 L46 模式：迁至 client 实例属性或新桩面）。
- **台账**：worktree `../magicbook-arch-b5` 无新增 commit（B2 改动已撤销，r177/r178 两个 commit 保留）；web.py 3304 行（HEAD 状态）。未 push。
- **总结**：requests.md 占号 R179；冲突记录：无；**B2 状态回填 overview：尝试未完成，方案与坑清单已留存**。

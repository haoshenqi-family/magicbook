# 回应归档 · R259

## 2026-10-31（R259：设置页生词提示语对齐 moon-well R232 新口径——「该等级及以上」）

### R259（承接 moon-well R232；用户原话「判定逻辑改为大于等于，当前用户的难度等级+1……」）

- **结论先行**：moon-well R232 把生词判定兜底改为「词档 ≥ 用户档位」（档位=学习目标线）并做存量档位 +1 迁移。本仓零判定逻辑改动，只同步用户可见表述：设置页提示语从「高于该等级的词会被标记为生词」改为「该等级及以上的词会被标记为生词」，消除文案与行为的漂移（数值同源纪律）。
- **实现**：`cps/templates/reading_settings.html:46` msgid 改「Words at or above this level are marked as unknown while reading. Default: CET4.」；`cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po` 同步 msgid + msgstr「阅读时该等级及以上的词会被标记为生词。默认：CET4。」；`pybabel compile` 重建 messages.mo（运行时读 .mo，不编译则中文不生效）。其余 27 个 locale 无此条翻译，走英文源文回退（源文已正确表达新语义）。
- **文档**：L1 `docs/product/readme/vocabulary.md` 档位句补「档位代表你正在学的目标水平：该档及以上的词默认判为生词」；需求基线 `vocabulary/requirements.md` 变更记录加 R259 行。判定矩阵权威仍在 moon-well `docs/product/vocabulary/interface.md`（R232 已更新）。
- **测试**：定向 `test_nav_settings_dropdown.py + test_i18n_seed_contract.py + test_me_preferences.py + test_common_api_contract.py` 共 **28 passed**（i18n 种子契约与设置页回归均绿）；旧 msgid 全仓 grep 归零。
- **状态与驻留**：**已 merge 待验收**。worktree `../magicbook-r259-judge-tooltip`（分支 `feat/r259-judge-tooltip`）按闸门保留待验收；验收通过后删除。跨仓主线：moon-well R232（判定翻转 + 迁移 SQL，SQL 执行前线上行为与改前一致）。
- **窗口与总结**：写入前 10 节，写入后 11 节；按「写入即检查」把最旧一节（R248）原样搬至 `response-archive/response-R248.md` 并登记索引，窗口恢复 10。requests.md 条目 259 已从占位回填。冲突记录：无撞号。

# LLD — R149 神奇树屋合集拆分（as-run 记录 + 收尾步骤）

> 状态：收尾清单草案 v1（2026-10-18）；收尾执行完回填「已上线」。
> 上层设计：[hld.md](./hld.md)。

## 1. 已执行轮 as-run 记录（2026-10-10，素材源 `docs/temp/scripts/`）

| 环节 | 脚本 | 口径要点 |
| --- | --- | --- |
| 探测 | `probe_epub_149.py` / `probe_epub_149_bounds.py` / `tail_probe_149.py` | NCX depth-1 navPoint `"N: Title"` 恰 28 册；spine 起点单调；试读页标记 = "Special Preview of Magic Tree House #N+1…"（27 册）+ #12 直接下一册书名行 |
| 拆分 | `split_epub_149.py` | 书名 `title_case()`（SMALL 词表小写、连字符分段、`TYPO_FIX={"TN":"IN"}`）；标题 `Magic Tree House #NN: Title`、文件名 `Magic Tree House %02d - %s.epub`；OPF 写 `calibre:series` + `series_index` + cover meta；`drop_from` = 块内指向下一册 navPoint 的最小 spine 下标；`strip_dangling()` 悬空目录条目删除；NCX playOrder 重排连续；mimetype 首文件 ZIP_STORED |
| 验收 | `verify_split_149.py` / `final_check_149.py` / `cover_check_149.py` | manifest/spine/NCX 断链、站内悬空链接、封面、源字数差值、28 封面 md5 去重 |
| 入库 | `drylib_add_149.py` → `pre_add_check_149.py` → `add_to_library_149.py` → `post_add_verify_149.py` | 干跑库 `calibredb init /tmp/drylib`；只读 `metadata.db?mode=ro` 查重；正式 `calibredb --with-library=/calibre-library add <28 epub>`（timeout 1800）；终检预期 books 143=115+28 |
| 事故回滚 | `remove_bad_149.py` + `clean_orphans_149.py` | 首导书名缺 `#` → `calibredb remove --permanent` 28 条（守卫：不含 149、恰 28 条才执行）→ 孤儿目录 rmtree（严格正则 + 合集守卫目录不动）→ 修正重导 |

源与产出路径：合集 epub 在容器 `/calibre-library/Mary Pope Osborne/Magic Tree House Library Books 1-28 (149)`；产出 `/tmp/mth_split`。

## 2. 收尾步骤（待开放问题拍板后执行）

1. **只读核对**：容器内 `sqlite3 file:/calibre-library/metadata.db?mode=ro` 列 28 册 id 清单 + book 149 行，写 /tmp 留档。
2. **标签**：`calibredb --with-library=/calibre-library add_tag <id> 英文分级` + `阶2`（档位按拍板）；28 条循环，失败单条重试不中断。
3. **书架**：参照 `shelf_prep_bookworm.py` 探测 `/config/app.db` 的 `shelf`/`book_shelf` 表结构后 INSERT（先 `cp app.db app.db.bak-20261018`）；挂「英文分级」书架。
4. **合集处置**：拍板移除 → `calibredb remove 149`（非 --permanent，可从 calibre 垃圾桶恢复）+ 手工核对合集目录清理；拍板保留 → `add_tag 149 合集`。
5. **归档补写**：`response-archive/` 补 R148/R149 两节（素材 = 本文件 §1 + 本次实测数据 + requests 原文），response.md 窗口纪律照旧。

## 3. 验收判据

见 [ac/ac.md](./ac/ac.md)；核心 = 28 册标签/书架齐、合集处置有记录、归档可检索。

## 4. 文档四问预答

- L1：无能力变化（书库内容整理）；如挂新书架，`readme/library.md` 书架清单加一行。
- L2：无契约变化。
- L3：无（无代码）。
- LLD：本文件状态行 + 归档节即交付物。

# AC — R149 神奇树屋合集拆分收尾

> 验证环境 = fnOS 容器 magicbook（只读核对走 `mode=ro`，写操作先备份）。

- [ ] GIVEN metadata.db WHEN 只读查询 THEN 28 册 `Magic Tree House #1..#28` 在库且 series_index 连续 1–28（与 2026-10-18 基线一致）
- [ ] 28 册全部带 `英文分级` + 阶位标签（档位按拍板口径），无漏挂、无误挂他书
- [ ] 「英文分级」书架包含 28 册（若拍板挂书架）；app.db 已备份 `.bak-<日期>`
- [ ] 合集 book 149 处置与拍板一致（移除：calibre 列表不再出现、有操作记录；保留：带「合集」标签）
- [ ] R148/R149 response 归档两节已补写，含脚本清单互链与本次实测数据
- [ ] 抽 3 册（首/中/尾）EPUB 尾部无「Special Preview」试读页残留（复跑 `tail_probe_149.py` 口径）

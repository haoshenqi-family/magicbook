# response 归档：R140（2026-10-09）

> 从 response.md 原样搬移（2026-10-11 R153 写入触发轮转；R152 写入时搬走 R138 后窗口仍为 11，本条系复核后的补搬）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-09（R140 上传 7 本书 + 按分级建书架）

**回应**：
- **上传**：/Users/haoshenqi/Downloads/books 的 7 本 EPUB 全部入库（id 142–148，书库现 128 本）：Charlotte's Web（E. B. White，阶2）、Animal Farm（George Orwell，阶3）、Charlie and the Chocolate Factory / Matilda / Fantastic Mr Fox / The Magic Finger / Boy: Tales of Childhood（Roald Dahl ×5，阶2）。calibredb add 显式传 --title/--authors 覆盖 z-lib 文件名噪音，标签「英文分级,阶2/阶3」，格式行/权限验证通过；「Charlottes Web」标题已修正为「Charlotte's Web」。
- **书架**：app.db 新建 6 个公共书架（is_public=1，属主 hsq，id 4–9）：英文分级·阶1 (800–1500词) ～ 阶6 (9000+词)；按 metadata.db 的阶标签批量挂 book_shelf_link，共 44 本（阶1=2、阶2=9、阶3=5、阶4=12、阶5=12、阶6=4），与 37 本公版 + 7 本新书台账一致。
- **踩坑记录**：① Calibre metadata.db 的 books 表带 title_sort() 自定义函数触发器，裸 sqlite 改 title 需先 create_function 注册等效实现；② 跨库联查（app.db.book_shelf_link × metadata.db.books）必须 ATTACH，单条 SQL 不能跨两个文件。
- **总结**：requests.md 占号 R140 并以本条回应；冲突记录：无（R139 为并行会话 learning 修复，正常顺延）。

### R140：统计/计划/复习卡全部消失——R139 只修了一半（当天修复上线）

- **根因**：R139 的 show() 只设内联 `style.display`——「显示」时置空 display 并不会移除模板挂着的 `hidden` 属性，UA 的 `[hidden]{display:none}` 对**无作者 display 规则**的元素（.panel 统计/计划面板、#ln-card、#ln-empty）继续生效，全部显不出来；页面只剩动态创建的选书匹配列表。恰好与 R139 前的症状互为镜像：带 display:flex 的选项区当时"因祸得福"能用，纯属性元素全灭。
- **修复**（`17cf3b63`，16:21 部署 healthy）：show() 同时切换 `hidden` 属性（解 UA 规则）与内联 display（压作者规则），缺一不可；renderChoices 的选项按钮同款处理（.btn inline-block 下不足四选项时空按钮真隐藏）。22 用例绿，线上 JS 验收通过。
- **教训（修正 R139 条目）**：Bootstrap/带 display 规则的页面做显隐，**属性和内联必须一起动**——只动属性被作者样式顶回，只动内联在显示方向漏掉挂着的 hidden 属性。两个方向各坏一半，必须同时覆盖。
- **总结**：requests.md 占号 R140；本条为回应；冲突记录：无。


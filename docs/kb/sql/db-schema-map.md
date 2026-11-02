# 数据库 schema 归属与跨库查询规矩

> 2026-10-24 建立。起因：排查「高级搜索『在读』返回空集」时，手工查库撞上
> `no such table: books`——数据其实分在两个文件里，没有一张表说明这件事。
> 相关讨论与代价分析见
> [attached-db-join-options.md](../../project/iterations/1.0/r213-home-ia/attached-db-join-options.md)。

## 1. 一共有几个库

| 文件 | 内容 | 谁建表 | 谁读写 |
| --- | --- | --- | --- |
| `<calibre-library>/metadata.db` | calibre 书库：`books` / `authors` / `tags` / `series` / `publishers` / `data` / `comments` / `identifiers` / `languages` / `ratings` / `custom_columns` + 动态的 `custom_column_<id>` | calibre 自己的 schema | `calibre_db.session`（**calibre 桌面端也会写这个文件**） |
| `<config>/app.db` | 用户与阅读数据：`user` / `user_session` / `book_read_link` / `reading_progress` / `bookmark` / `shelf` / `book_shelf_link` / `archived_book` / `downloads` / `kobo_*` / `oauthProvider` / `registration` / `remote_auth_token` / `thumbnail` / `flask_settings` / `reading_translation_job*` | `ub.init_db()` 的 `Base.metadata.create_all` | `ub.session`（写）、`calibre_db.session`（读，见 §2） |
| `<config>/ai_companion.db` | AI 对话与记忆：`ai_config` / `ai_provider` / `ai_conversation` / `ai_message` / `ai_user_memory` | `cps/ai/database.py` 自己的 `AiBase` + 独立 engine | `cps.ai` 的 session |

两条容易搞错的归属：

- `reading_translation_job` / `reading_translation_job_item` **在 app.db**——它们继承 `ub.Base`（`cps/reading_translation/models.py:7,26`），不是独立库。
- `flask_settings` **在 app.db**（`cps/config_sql.py`）。
- 备注：生产 `app.db` 里也出现了 `ai_*` 表，与代码默认（独立 `ai_companion.db`）不一致，原因未核实；不影响本文三条规矩。

## 2. 跨库 join 是怎么实现的

`cps/db.py:697-705` 建了一个**内存 SQLite 连接**，把两个文件 ATTACH 上来：

```python
engine = create_engine('sqlite://', poolclass=StaticPool)   # 主库为空的内存库
with engine.begin() as connection:
    connection.execute(text("attach database '<calibre>/metadata.db' as calibre;"))
    connection.execute(text("attach database '<config>/app.db' as app_settings;"))
```

于是 `calibre_db.session` 上的查询可以同时用 `books` 和 `book_read_link`——
它们是同一个连接里两个 attached schema 的本地 join，不是分布式查询。

典型例子：`calibre_db.generate_linked_query()`（`db.py:819`）一次查出
`Books + ArchivedBook.is_archived + ReadBook.read_status` 三样，书库页、详情页、
高级搜索都靠它。

## 3. 三条规矩

### 规矩一：写 `app.db` 的表，一律走 `ub.session`

**不要**用 `calibre_db.session` 去改 ub 表。原因：那个 session 的
`commit()` 提交的是它范围内的**所有**改动，包含 ATTACH 进来的 `app_settings`。
一旦有人这么写，就会出现「我没动 app.db 啊，它怎么变了」这种极难定位的问题。

现状是干净的：`editbooks.py` 里所有 `calibre_db.session.add/delete` 都是 calibre
表，没有一处碰 ub 表。保持这个状态。

### 规矩二：跨库 join 只用于「读筛选」；展示能两段查就两段查

- **筛选**（搜索、书库过滤）必须在 SQL 里做，否则分页会错（先分页再过滤 → 每页
  条数不齐、总数不对）。这种场景继续用 `generate_linked_query` 的跨库 join。
- **纯展示**（列表上显示一个「已读」徽章）可以两段查：先拿书，再按 `book_id`
  批量查状态，Python 合并。少一次跨库。

### 规矩三：手工查库必须 ATTACH

直接 `sqlite3 /config/app.db` 然后 `select from books` 会报 `no such table: books`。
用这段（只读）：

```python
import sqlite3
conn = sqlite3.connect(':memory:')
conn.execute("ATTACH DATABASE '/calibre-library/metadata.db' AS calibre")
conn.execute("ATTACH DATABASE 'file:/config/app.db?mode=ro' AS app_settings")

conn.execute("""
    SELECT b.id, b.title, r.read_status
    FROM calibre.books b
    LEFT OUTER JOIN app_settings.book_read_link r
           ON r.user_id = ? AND r.book_id = b.id
    WHERE r.read_status = 2
    LIMIT 20
""", (3,)).fetchall()
```

容器内执行：

```bash
ssh ubuntu "ssh root@192.168.31.9 'docker exec magicbook python3 /tmp/query.py'"
```

## 4. 已知代价（不重要但要知道）

| 代价 | 说明 |
| --- | --- |
| calibre 侧查询串行 | `StaticPool` 单连接（`db.py:701`）。家庭规模无感，并发上来了会排队 |
| 两个连接同时碰 `app.db` | `ub.session`（QueuePool）与 `calibre_db.session`（ATTACH）各自持有连接，写要抢锁 |
| 备份要备两个文件 | 只恢复 `app.db` 或只恢复 `metadata.db` 都会丢数据 |

**为什么不改**：跨库只在读、没有跨库写；当前规模下单连接毫无压力；拆它等于重写
数据层并与上游 calibre-web 永久分叉。触发条件与备选方案见
[attached-db-join-options.md](../../project/iterations/1.0/r213-home-ia/attached-db-join-options.md)。

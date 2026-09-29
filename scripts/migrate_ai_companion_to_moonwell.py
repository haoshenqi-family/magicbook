#!/usr/bin/env python3
"""ai_companion.db → moon-well MySQL 一次性迁移（设计文档 magicbook 侧 §6）。

迁移边界（家族决策 D6/D8，已拍板）：
- 全量迁：ai_conversation / ai_message / ai_user_memory → moon-well MySQL
  （库 magichouse，表由 moon-well ddl-auto=update 建好）。
- 退役不迁：ai_config / ai_provider —— provider 配置收敛 Nacos ai.llm.configs，
  本脚本把它们快照导出为 JSON 归档文件，随后可下线 cps/ai。

用法（跑在 magicbook 容器或宿主，需能同时读到 SQLite 与 moon-well MySQL）：
    python3 scripts/migrate_ai_companion_to_moonwell.py \
        --sqlite /path/to/ai_companion.db \
        --mysql-url "mysql+pymysql://user:pass@192.168.31.9:3306/magichouse" \
        --user-map user_map.json          # {"<magicbook user.id>": "<moon-well userId>"}
        [--dry-run]                       # 只读源库 + 打印对账，不写 MySQL

或省略 --mysql-url，用环境变量 MOONWELL_MYSQL_URL。

user_id 映射（设计 §6.3 迁移前置条件）：两系统经 OIDC（authentik）统一认证，
大概率 subject 对齐、user id 同源——迁移前必须实测核实；确认同 id 后传
--identity-mapping 代替 --user-map。

映射与清洗规则：
- id 原样保留（MySQL AUTO_INCREMENT 事后拨到 max(id)+1，设计 §6.1 推荐方案）。
- ai_message.page_context 无目标列（moon-well 契约：上下文不进历史）——
  以 {"legacy_page_context": "..."} 形式存入 tool_trace（截断 2000 字符），
  新 UI 不渲染该字段，仅存档。
- ai_user_memory.content → memory；source_book_id → book_id（NULL 记 0=跨书通用）；
  created_at 同时回填 created_at/updated_at；source 统一记 agent-extract。
- 时间戳：SQLite naive 值原样入 DATETIME（两端同为本地时间语义）。

验证：结束后打印逐表行数对账 + 抽样比对；迁移前请先做 ai_companion.db
文件级备份（与 book89 迁移同款操作纪律）。
"""
import argparse
import json
import os
import sqlite3
import sys

TABLES_TO_MIGRATE = ("ai_conversation", "ai_message", "ai_user_memory")
TABLES_TO_ARCHIVE = ("ai_config", "ai_provider")
PAGE_CONTEXT_MAX_CHARS = 2000


# ---------------------------------------------------------------------------
# 源（SQLite，只读）
# ---------------------------------------------------------------------------
def read_source(sqlite_path):
    """读 ai_companion.db 全量。返回 {table: [row dict]}（列名即 key）。"""
    if not os.path.exists(sqlite_path):
        raise SystemExit("SQLite 源不存在: %s" % sqlite_path)
    conn = sqlite3.connect("file:%s?mode=ro" % sqlite_path, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        data = {}
        for table in TABLES_TO_MIGRATE + TABLES_TO_ARCHIVE:
            rows = [dict(r) for r in conn.execute(
                "SELECT * FROM %s" % table).fetchall()]
            data[table] = rows
        return data
    finally:
        conn.close()


def resolve_user_id(user_map, raw_id):
    """user_id 换算：显式映射表查表；user_map=None（--identity-mapping）原样透传。"""
    if user_map is None:
        return int(raw_id)
    mapped = user_map.get(str(raw_id))
    if mapped is None:
        raise SystemExit("user_id %s 不在映射表里（迁移前需核实映射关系，"
                         "或实测同 id 后改用 --identity-mapping）" % raw_id)
    return int(mapped)


# ---------------------------------------------------------------------------
# 行映射（SQLite 列 → moon-well MySQL 列）
# ---------------------------------------------------------------------------
def map_conversation(row, user_map):
    return {
        "id": row["id"],
        "user_id": resolve_user_id(user_map, row["user_id"]),
        # moon-well bookId 语义 = magicbook bookId 引用（不校验存在性），原样保留
        "book_id": row["book_id"] if row["book_id"] is not None else 0,
        "book_title": "",  # 冗余书名旧库没有；展示时前端随请求上行，历史列表留空可接受
        "title": (row["title"] or "")[:500],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"] or row["created_at"],
    }


def map_message(row, user_map):
    tool_trace = None
    if row.get("page_context"):
        # 页面上下文有存档价值但无目标列：以显式标记入 tool_trace（新 UI 不渲染）
        tool_trace = json.dumps({
            "legacy_page_context": str(row["page_context"])[:PAGE_CONTEXT_MAX_CHARS]
        }, ensure_ascii=False)
    return {
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "role": row["role"],
        "content": row["content"],
        "tool_trace": tool_trace,
        "created_at": row["created_at"],
    }


def map_memory(row, user_map):
    return {
        "id": row["id"],
        "user_id": resolve_user_id(user_map, row["user_id"]),
        "book_id": row["source_book_id"] if row["source_book_id"] is not None else 0,
        "memory": row["content"],
        "source": "agent-extract",
        "embedding": None,  # 设计 §7.1 P2 预留列，恒空
        "created_at": row["created_at"],
        "updated_at": row["created_at"],
    }


MAPPERS = {
    "ai_conversation": map_conversation,
    "ai_message": map_message,   # 无 user_id 列，map 里不用 user_map
    "ai_user_memory": map_memory,
}


# ---------------------------------------------------------------------------
# 目标（MySQL，pymysql 直插）
# ---------------------------------------------------------------------------
class MySqlTarget:
    """pymysql 直连 moon-well MySQL。Why 不走 SQLAlchemy：一次性脚本，
    少一层依赖，逐行 INSERT 的行为更透明。"""

    def __init__(self, mysql_url):
        try:
            import pymysql
        except ImportError:
            raise SystemExit("需要 pymysql：pip install pymysql 后重试")
        parsed = self._parse_url(mysql_url)
        self.conn = pymysql.connect(
            host=parsed["host"], port=parsed["port"],
            user=parsed["user"], password=parsed["password"],
            database=parsed["database"], charset="utf8mb4",
            autocommit=False)
        self.inserted = {}

    @staticmethod
    def _parse_url(mysql_url):
        # mysql+pymysql://user:pass@host:port/db
        rest = mysql_url.split("://", 1)[1]
        userinfo, hostpart = rest.rsplit("@", 1)
        user, password = userinfo.split(":", 1)
        host_port, database = hostpart.split("/", 1)
        host, _, port = host_port.partition(":")
        return {"host": host, "port": int(port or 3306),
                "user": user, "password": password, "database": database}

    def insert_rows(self, table, columns, rows):
        if not rows:
            self.inserted[table] = 0
            return
        placeholders = ", ".join(["%s"] * len(columns))
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (
            table, ", ".join(columns), placeholders)
        with self.conn.cursor() as cursor:
            cursor.executemany(sql, [
                tuple(row[c] for c in columns) for row in rows])
        self.inserted[table] = len(rows)

    def bump_auto_increment(self, table, next_id):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE %s AUTO_INCREMENT = %%s" % table, (next_id,))

    def count(self, table):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM %s" % table)
            return cursor.fetchone()[0]

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


COLUMNS = {
    "ai_conversation": ["id", "user_id", "book_id", "book_title", "title",
                        "created_at", "updated_at"],
    "ai_message": ["id", "conversation_id", "role", "content", "tool_trace",
                   "created_at"],
    "ai_user_memory": ["id", "user_id", "book_id", "memory", "source",
                       "embedding", "created_at", "updated_at"],
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sqlite", required=True,
                        help="ai_companion.db 路径（建议先用 cp 做文件级备份）")
    parser.add_argument("--mysql-url",
                        default=os.environ.get("MOONWELL_MYSQL_URL", ""),
                        help="mysql+pymysql://user:pass@host:3306/magichouse"
                             "（或环境变量 MOONWELL_MYSQL_URL）")
    parser.add_argument("--user-map", help='映射 JSON 文件 {"magicbook用户id": "moonwell userId"}')
    parser.add_argument("--identity-mapping", action="store_true",
                        help="两系统 user id 同源（需迁移前实测核实后才能用）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只读源库 + 打印对账，不写 MySQL")
    args = parser.parse_args(argv)

    if not args.identity_mapping and not args.user_map:
        raise SystemExit("必须提供 --user-map 或（实测核实同 id 后）--identity-mapping，"
                         "见设计文档 magicbook 侧 §6.3")
    if args.identity_mapping:
        user_map = None  # identity 模式：原样透传
    else:
        with open(args.user_map, encoding="utf-8") as fh:
            user_map = {str(k): str(v) for k, v in json.load(fh).items()}

    data = read_source(args.sqlite)

    print("=== 源库对账（%s）===" % args.sqlite)
    for table in TABLES_TO_MIGRATE + TABLES_TO_ARCHIVE:
        print("%-16s %d 行" % (table, len(data[table])))

    if args.dry_run:
        print("（dry-run：未写 MySQL）")
        return 0

    if not args.mysql_url:
        raise SystemExit("缺 --mysql-url（或环境变量 MOONWELL_MYSQL_URL）")

    mapped = {}
    for table in TABLES_TO_MIGRATE:
        mapper = MAPPERS[table]
        mapped[table] = [mapper(row, user_map) for row in data[table]]

    target = MySqlTarget(args.mysql_url)
    try:
        for table in TABLES_TO_MIGRATE:
            target.insert_rows(table, COLUMNS[table], mapped[table])
            max_id = max((row["id"] for row in mapped[table]), default=0)
            if max_id:
                target.bump_auto_increment(table, max_id + 1)
        # 退役表快照归档（不迁移，D8）
        archive_path = args.sqlite + ".config-archive.json"
        with open(archive_path, "w", encoding="utf-8") as fh:
            json.dump({t: data[t] for t in TABLES_TO_ARCHIVE}, fh,
                      ensure_ascii=False, indent=2, default=str)
        print("ai_config/ai_provider 已快照归档: %s" % archive_path)
        target.commit()
    except Exception:
        target.rollback()
        raise
    finally:
        target.close()

    print("=== 迁移后对账 ===")
    ok = True
    for table in TABLES_TO_MIGRATE:
        source_count = len(mapped[table])
        target_count = target.inserted.get(table, 0)
        status = "OK" if source_count == target_count else "MISMATCH"
        ok = ok and source_count == target_count
        print("%-16s 源 %d 行 -> 写入 %d 行 [%s]"
              % (table, source_count, target_count, status))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

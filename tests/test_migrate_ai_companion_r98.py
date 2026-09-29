"""Tests for scripts/migrate_ai_companion_to_moonwell.py (R98, P4).

Strategy: build a real SQLite source with the legacy ai_companion.db schema,
monkeypatch MySqlTarget with a recording fake, and assert the row mapping
(user_id 换算 / 列重命名 / page_context 存档 / AUTO_INCREMENT 拨号 / 对账退出码).
"""
import importlib.util
import json
import os
import sqlite3
import sys

import pytest

_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "scripts", "migrate_ai_companion_to_moonwell.py")

_spec = importlib.util.spec_from_file_location("migrate_ai_companion", _SCRIPT)
migrate = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("migrate_ai_companion", migrate)
_spec.loader.exec_module(migrate)


SCHEMA = """
CREATE TABLE ai_config (id INTEGER PRIMARY KEY, enabled BOOLEAN, default_provider VARCHAR(50),
    default_model VARCHAR(100), memory_enabled BOOLEAN, memory_extract_interval INTEGER,
    system_prompt_extra TEXT);
CREATE TABLE ai_provider (id INTEGER PRIMARY KEY, provider_name VARCHAR(100),
    display_name VARCHAR(100), api_base VARCHAR(500), api_key_encrypted VARCHAR(1000),
    models_json TEXT, active BOOLEAN);
CREATE TABLE ai_conversation (id INTEGER PRIMARY KEY, user_id INTEGER, book_id INTEGER,
    book_format VARCHAR(20), title VARCHAR(500), created_at DATETIME, updated_at DATETIME);
CREATE TABLE ai_message (id INTEGER PRIMARY KEY, conversation_id INTEGER, role VARCHAR(20),
    content TEXT, page_context TEXT, created_at DATETIME);
CREATE TABLE ai_user_memory (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT,
    source_book_id INTEGER, created_at DATETIME);
"""


class FakeTarget:
    """记录 INSERT 的假 MySQL 目标（不连库）。"""
    calls = None
    instances = None

    def __init__(self, url):
        self.inserted = {}
        self.bumped = {}
        self.committed = False
        FakeTarget.instances.append(self)

    def insert_rows(self, table, columns, rows):
        FakeTarget.calls.append((table, columns, rows))
        self.inserted[table] = len(rows)

    def bump_auto_increment(self, table, next_id):
        self.bumped[table] = next_id

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture
def fake_target(monkeypatch):
    FakeTarget.calls = []
    FakeTarget.instances = []
    monkeypatch.setattr(migrate, "MySqlTarget", FakeTarget)
    return FakeTarget


@pytest.fixture
def sqlite_source(tmp_path):
    """按旧 ai_companion.db 真实 schema 建源库并塞入跨表样例数据。"""
    db_path = tmp_path / "ai_companion.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO ai_conversation (id, user_id, book_id, book_format, title,"
                 " created_at, updated_at) VALUES (11, 1, 89, 'EPUB', '第一章问过 sidebars',"
                 " '2026-09-01 10:00:00', '2026-09-01 10:05:00')")
    conn.execute("INSERT INTO ai_message (id, conversation_id, role, content, page_context,"
                 " created_at) VALUES (21, 11, 'user', 'sidebars 是什么', 'The sidebars…',"
                 " '2026-09-01 10:00:01')")
    conn.execute("INSERT INTO ai_message (id, conversation_id, role, content, page_context,"
                 " created_at) VALUES (22, 11, 'assistant', '侧栏的意思', NULL,"
                 " '2026-09-01 10:00:02')")
    conn.execute("INSERT INTO ai_user_memory (id, user_id, content, source_book_id,"
                 " created_at) VALUES (31, 1, '偏好简洁解释', 89, '2026-09-01 10:00:03')")
    conn.execute("INSERT INTO ai_user_memory (id, user_id, content, source_book_id,"
                 " created_at) VALUES (32, 1, '词汇量约四级', NULL, '2026-09-01 10:00:04')")
    conn.execute("INSERT INTO ai_config (id, enabled) VALUES (1, 1)")
    conn.execute("INSERT INTO ai_provider (id, provider_name) VALUES (1, 'deepseek')")
    conn.commit()
    conn.close()
    return str(db_path)


@pytest.fixture
def user_map_file(tmp_path):
    path = tmp_path / "user_map.json"
    path.write_text(json.dumps({"1": "7"}), encoding="utf-8")
    return str(path)


def _argv(sqlite_source, user_map_file, extra=()):
    return ["--sqlite", sqlite_source, "--user-map", user_map_file,
            "--mysql-url", "mysql+pymysql://u:p@127.0.0.1:3306/magichouse", *extra]


def test_full_migration_maps_columns_and_ids(fake_target, sqlite_source, user_map_file, tmp_path):
    rc = migrate.main(_argv(sqlite_source, user_map_file))
    assert rc == 0

    tables = {t: rows for t, cols, rows in FakeTarget.calls}
    conv = tables["ai_conversation"][0]
    assert conv["user_id"] == 7                      # user_map 换算 1 → 7
    assert conv["book_id"] == 89                     # bookId 引用原样保留
    assert conv["book_title"] == ""

    msgs = tables["ai_message"]
    by_role = {m["role"]: m for m in msgs}
    # page_context 无目标列 → 存档进 tool_trace；NULL → tool_trace 为 NULL
    assert json.loads(by_role["user"]["tool_trace"])["legacy_page_context"] == "The sidebars…"
    assert by_role["assistant"]["tool_trace"] is None
    assert by_role["user"]["content"] == "sidebars 是什么"

    memories = {m["memory"]: m for m in tables["ai_user_memory"]}
    assert memories["偏好简洁解释"]["book_id"] == 89    # source_book_id → book_id
    assert memories["词汇量约四级"]["book_id"] == 0     # NULL → 跨书通用
    assert all(m["source"] == "agent-extract" for m in memories.values())
    assert all(m["user_id"] == 7 for m in memories.values())

    # id 原样保留 + AUTO_INCREMENT 拨到 max(id)+1（设计 §6.1 推荐方案）
    assert sorted(m["id"] for m in msgs) == [21, 22]
    assert FakeTarget.instances[0].bumped == {
        "ai_conversation": 12, "ai_message": 23, "ai_user_memory": 33}
    assert FakeTarget.instances[0].committed

    # 退役表快照归档落盘
    archive = json.loads(open(sqlite_source + ".config-archive.json", encoding="utf-8").read())
    assert archive["ai_config"][0]["id"] == 1
    assert archive["ai_provider"][0]["provider_name"] == "deepseek"


def test_identity_mapping_flag(fake_target, sqlite_source, tmp_path):
    rc = migrate.main(["--sqlite", sqlite_source, "--identity-mapping",
                       "--mysql-url", "mysql+pymysql://u:p@h/db"])
    assert rc == 0
    conv = [rows for t, c, rows in FakeTarget.calls if t == "ai_conversation"][0][0]
    assert conv["user_id"] == 1  # 原样透传


def test_missing_mapping_is_rejected(fake_target, sqlite_source):
    with pytest.raises(SystemExit, match="user-map"):
        migrate.main(["--sqlite", sqlite_source,
                      "--mysql-url", "mysql+pymysql://u:p@h/db"])


def test_unmapped_user_is_rejected(fake_target, sqlite_source, tmp_path):
    path = tmp_path / "bad_map.json"
    path.write_text(json.dumps({"2": "9"}), encoding="utf-8")
    with pytest.raises(SystemExit, match="user_id"):
        migrate.main(_argv(sqlite_source, str(path)))


def test_dry_run_writes_nothing(fake_target, sqlite_source, user_map_file):
    rc = migrate.main(_argv(sqlite_source, user_map_file, extra=["--dry-run"]))
    assert rc == 0
    assert FakeTarget.calls == []       # 未触碰 MySQL 目标
    assert not os.path.exists(sqlite_source + ".config-archive.json")

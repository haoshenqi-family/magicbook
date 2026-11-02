"""Tests for the legacy app.db -> independent AI store data migration.

The migration copies ai_* rows out of calibre-web's old SQLite app.db into the
new independent AI data store on first startup. These tests simulate the legacy
tables + rows and verify they land in the new store.
"""
from sqlalchemy import text

from cps.ai.models import AiConversation, AiMessage, AiProvider, AiUserMemory


class TestLegacyMigration:
    def test_migrates_rows_from_legacy_app_db(self, app, ai_session):
        """Rows present in legacy app.db ai_* tables are copied to the new store."""
        # Simulate a legacy ai_conversation table with one row inside the app.db
        # (this is what the pre-upgrade deployment looked like).
        from cps import ub
        legacy = ub.session.get_bind()
        with legacy.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ai_conversation"))
            conn.execute(text("DROP TABLE IF EXISTS ai_message"))
            conn.execute(text(
                "CREATE TABLE ai_conversation ("
                " id INTEGER PRIMARY KEY, user_id INTEGER, book_id INTEGER,"
                " book_format TEXT, title TEXT, created_at DATETIME, updated_at DATETIME)"
            ))
            conn.execute(text(
                "INSERT INTO ai_conversation (user_id, book_id, book_format, title)"
                " VALUES (1, 7, 'EPUB', 'legacy thread')"
            ))
            conn.execute(text(
                "CREATE TABLE ai_message ("
                " id INTEGER PRIMARY KEY, conversation_id INTEGER, role TEXT,"
                " content TEXT, page_context TEXT, created_at DATETIME)"
            ))
            conn.execute(text(
                "INSERT INTO ai_message (conversation_id, role, content)"
                " VALUES (1, 'user', 'legacy question')"
            ))
            conn.commit()

        # Now (re)initialize the AI data layer -> triggers _migrate_legacy_sqlite
        import cps.ai.database as aidb
        aidb._engine = None
        aidb._session_factory = None
        aidb._initialized = False
        aidb.init_ai_db()

        new_sess = aidb.get_session()
        convs = new_sess.query(AiConversation).all()
        assert len(convs) == 1
        assert convs[0].title == "legacy thread"
        assert convs[0].book_id == 7
        msgs = new_sess.query(AiMessage).all()
        assert len(msgs) == 1
        assert msgs[0].content == "legacy question"

    def test_does_not_migrate_when_new_store_has_data(self, app, ai_session):
        """If the new store already has conversations, migration is skipped."""
        from cps import ub
        legacy = ub.session.get_bind()
        with legacy.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ai_conversation"))
            conn.execute(text(
                "CREATE TABLE ai_conversation ("
                " id INTEGER PRIMARY KEY, user_id INTEGER, book_id INTEGER,"
                " book_format TEXT, title TEXT, created_at DATETIME, updated_at DATETIME)"
            ))
            conn.execute(text(
                "INSERT INTO ai_conversation (user_id, book_id, book_format, title)"
                " VALUES (1, 8, 'EPUB', 'legacy title')"
            ))
            conn.commit()

        # Seed the new store so it is "in use"
        ai_session.add(AiConversation(user_id=1, book_id=8, title="fresh"))
        ai_session.commit()

        import cps.ai.database as aidb
        aidb._engine = None
        aidb._session_factory = None
        aidb._initialized = False
        aidb.init_ai_db()

        new_sess = aidb.get_session()
        titles = [c.title for c in new_sess.query(AiConversation).all()]
        # The "fresh" row stays; the legacy row must NOT be copied in.
        assert "legacy title" not in titles
        assert "fresh" in titles

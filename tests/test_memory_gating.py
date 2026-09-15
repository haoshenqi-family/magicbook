"""Tests for memory gating, dedup/merge, and relevance-ordered injection."""
import pytest

from cps.ai.memory import (has_memory_signal, _memory_tokens, _similarity,
                           find_duplicate_memory, select_relevant_memories)


class TestHasMemorySignal:
    def test_preference_signal_triggers(self):
        msgs = [{"role": "user", "content": "我很喜欢这个作者的叙事风格"}]
        assert has_memory_signal(msgs) is True

    def test_english_signal_triggers(self):
        msgs = [{"role": "user", "content": "I really like epic fantasy novels"}]
        assert has_memory_signal(msgs) is True

    def test_learning_context_triggers(self):
        msgs = [{"role": "user", "content": "我正在学英语，读原版书练阅读"}]
        assert has_memory_signal(msgs) is True

    def test_pure_noise_streak_skips(self):
        msgs = [{"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！想聊什么？"},
                {"role": "user", "content": "谢谢"},
                {"role": "user", "content": "ok"}]
        assert has_memory_signal(msgs) is False

    def test_short_no_signal_message_skips(self):
        msgs = [{"role": "user", "content": "这一章讲了什么？"}]
        assert has_memory_signal(msgs) is False

    def test_no_user_messages_skips(self):
        assert has_memory_signal([{"role": "assistant", "content": "hi"}]) is False


class TestSimilarity:
    def test_paraphrase_scores_above_threshold(self):
        a = _memory_tokens("User enjoys epic worldbuilding")
        b = _memory_tokens("the user loves epic world-building")
        assert _similarity(a, b) >= 0.45

    def test_distinct_memories_score_below(self):
        a = _memory_tokens("User enjoys epic worldbuilding")
        b = _memory_tokens("User prefers reading on weekends only")
        assert _similarity(a, b) < 0.45


class TestFindDuplicateMemory:
    def _seed(self, ai_session, content, user_id=1):
        from cps.ai.models import AiUserMemory
        row = AiUserMemory()
        row.user_id = user_id
        row.content = content
        row.source_book_id = 42
        ai_session.add(row)
        ai_session.commit()

    def test_detects_paraphrase_duplicate(self, app, ai_session):
        self._seed(ai_session, "User enjoys epic worldbuilding")
        dup = find_duplicate_memory(1, "the user loves epic world-building")
        assert dup is not None
        assert dup.content == "User enjoys epic worldbuilding"

    def test_distinct_memory_not_flagged(self, app, ai_session):
        self._seed(ai_session, "User enjoys epic worldbuilding")
        assert find_duplicate_memory(1, "User prefers short chapters") is None


class TestSelectRelevantMemories:
    def _seed(self, ai_session, content, book_id, user_id=1):
        from cps.ai.models import AiUserMemory
        row = AiUserMemory()
        row.user_id = user_id
        row.content = content
        row.source_book_id = book_id
        ai_session.add(row)
        ai_session.commit()
        return row

    def test_current_book_memory_ranks_first(self, app, ai_session):
        self._seed(ai_session, "old memory from another book", book_id=99)
        self._seed(ai_session, "memory about this very book", book_id=7)

        result = select_relevant_memories(1, book_id=7, book_keywords=[], limit=10)

        assert result[0] == "memory about this very book"

    def test_keyword_mention_ranks_above_unrelated(self, app, ai_session):
        self._seed(ai_session, "random unrelated note", book_id=99)
        self._seed(ai_session, "enjoys frank herbert style sci-fi", book_id=2)

        result = select_relevant_memories(1, book_id=7,
                                          book_keywords=["Dune", "frank herbert"],
                                          limit=10)

        assert result[0] == "enjoys frank herbert style sci-fi"

    def test_window_cap_respected(self, app, ai_session):
        for i in range(15):
            self._seed(ai_session, "memory %d" % i, book_id=100 + i)

        result = select_relevant_memories(1, book_id=7, book_keywords=[], limit=10)

        assert len(result) == 10

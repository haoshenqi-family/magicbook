"""AI memory system: system-prompt construction + cross-book memory extraction.

Two responsibilities:
1. ``build_system_prompt()`` — assembles the system prompt sent to the LLM
   from book metadata, current page text, and the user's long-term memories.
2. ``extract_user_memory()`` — calls the LLM with recent conversation messages
   and asks it to produce a concise insight about the user; the result is
   stored in ``AiUserMemory`` for injection into future conversations.
"""
import re
from typing import List, Optional

from cps import logger

from .models import AiUserMemory
from .prompts import CHAT_SYSTEM, render_prompt

log = logger.create()


def _session():
    """Lazy access to the AI data session — read at call time, not import time,
    so this module can be imported before create_app() initializes the data layer."""
    from .database import get_session
    return get_session()

_MAX_PAGE_CHARS = 8000
_MAX_DESC_CHARS = 1000
_MAX_RECENT_MESSAGES = 12


def build_system_prompt(book_title: str,
                        book_authors: List[str],
                        book_description: str,
                        book_tags: List[str],
                        page_context: str,
                        user_memory: List[str],
                        extra_prompt: str = "",
                        chapter: str = "",
                        unfamiliar_words: Optional[List[str]] = None) -> str:
    """Build the system prompt for an AI chat about a book.

    The prompt instructs the AI to act as a reading companion, gives it the
    book's metadata, the current chapter, the current page text, the words the
    user has marked as unfamiliar on this page, and any long-term user memories
    so the AI has continuity across books. The text comes from the
    ``chat-system`` template (cps/ai/prompts.py) so it can be edited centrally.
    """
    authors_str = ", ".join(book_authors) if book_authors else "Unknown"
    tags_section = "\nTags: %s" % ", ".join(book_tags) if book_tags else ""
    description_section = ""
    if book_description:
        # Strip HTML from description (calibre stores it as HTML)
        desc = re.sub(r"<[^>]+>", "", book_description).strip()
        if len(desc) > _MAX_DESC_CHARS:
            desc = desc[:_MAX_DESC_CHARS] + "..."
        description_section = "\nDescription: %s" % desc
    memory_str = "\n".join("- %s" % m for m in user_memory) if user_memory else "(none yet)"
    unfamiliar_str = ("\n".join("- %s" % w for w in unfamiliar_words)
                      if unfamiliar_words else "（本页暂无）")

    # Truncate page context to avoid blowing the context window
    if len(page_context) > _MAX_PAGE_CHARS:
        page_context = page_context[:_MAX_PAGE_CHARS] + "\n...[truncated]"
    if not page_context:
        page_context = "(no page context provided)"

    return render_prompt(
        CHAT_SYSTEM,
        title=book_title,
        authors=authors_str,
        tags_section=tags_section,
        description_section=description_section,
        chapter=chapter or "(unknown)",
        page_context=page_context,
        unfamiliar_words=unfamiliar_str,
        memory=memory_str,
        extra_section="\n\n## Additional instructions\n%s" % extra_prompt if extra_prompt else "",
    )


def should_extract_memory(message_count: int, interval: int = 10) -> bool:
    """Return True if memory extraction should run after this many messages."""
    if interval <= 0:
        return False
    return message_count > 0 and message_count % interval == 0


# ---------------------------------------------------------------------------
# 信号门控（借鉴 Cheap Gate）：提取是 LLM 调用，先零成本判断最近对话里是否
# 出现值得记忆的信号，避免「每 N 条消息固定烧一次 token、大多数输出 NONE」。
# ---------------------------------------------------------------------------

#: 偏好/兴趣/纠正类信号：出现任一即值得让 LLM 判断是否提炼
# Why: 不绑定"我"前缀 —— "我很喜欢"/"I really like" 等修饰语会隔断短语匹配
_SIGNAL_PATTERNS = [
    re.compile(r"(喜欢|偏爱|爱看|不喜欢|讨厌|反感|更想|更喜欢|宁愿|以后都)", re.I),
    re.compile(r"(我在读|我在学|我正在读|我正在学|我在做|我的工作|我的专业|我是搞|我的职业|记住|别忘了|跟我提过)", re.I),
    re.compile(r"\b(i (?:really )?(?:like|love|hate|prefer|enjoy|admire)|i(?:'m| am) (?:reading|learning)|remember that)\b", re.I),
    re.compile(r"(太难了|太简单|看不懂|生词|阅读水平|词汇量)", re.I),
]

#: 明确的无信号快答：纯功能请求/问候不需要记忆
_NOISE_PATTERN = re.compile(r"^(你好|嗨|hi|hello|谢谢|多谢|thanks|ok|好的|继续)[!！.。\s]*$", re.I)


def has_memory_signal(recent_messages: list) -> bool:
    """Zero-cost gate: scan recent messages for preference/correction/context signals.

    Why: extraction is an LLM call; most intervals contain nothing worth
    remembering (the old unconditional trigger mostly produced NONE).
    Rules: any user message matching a signal pattern → True; a pure-noise
    streak (greetings/acknowledgements only) → False; default True when text
    is long enough that cheap regexes can't judge (don't miss real insights).
    """
    user_texts = [str(m.get("content") or "") for m in recent_messages
                  if m.get("role") == "user"]
    if not user_texts:
        return False
    noise_only = True
    for text in user_texts:
        stripped = text.strip()
        if not stripped:
            continue
        if _NOISE_PATTERN.match(stripped):
            continue
        noise_only = False
        for pattern in _SIGNAL_PATTERNS:
            if pattern.search(stripped):
                return True
    if noise_only:
        return False
    # 有实质内容但规则没命中: 消息足够长时宁可多提取一次(漏记代价 > 一次调用)
    return any(len(t) > 60 for t in user_texts)


# ---------------------------------------------------------------------------
# 写入前去重/合并（防堆积）：稳定偏好会被不同书反复提炼，无去重时重复行
# 会把多样记忆挤出「最新 10 条」注入窗口。
# ---------------------------------------------------------------------------

_STOPWORDS = set(("the a an of and or to in on for with my me i i'm it is was "
                  "user book this that these those 喜欢 讨厌 我 的 了 是 在 看 读 "
                  "一本 这个 那个 用户").split())


def _memory_tokens(text):
    """Normalize a memory into a comparable token set (lowercase, dedup stopwords).

    Hyphens are stripped before tokenizing so "world-building" and
    "worldbuilding" produce the same token."""
    normalized = re.sub(r"[-\u2010-\u2015]", "", (text or "").lower())
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", normalized)
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 1}


def _similarity(a_tokens, b_tokens):
    """Overlap coefficient (intersection over the smaller set), 0..1.

    Why not Jaccard: extraction phrasing varies in length; a short stable
    preference should still match its longer paraphrase. Overlap on the
    smaller set is robust to that asymmetry."""
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / min(len(a_tokens), len(b_tokens))


def find_duplicate_memory(user_id: int, content: str, threshold: float = 0.5):
    """Return an existing near-duplicate AiUserMemory row for this user, or None.

    Compares token-set Jaccard similarity against the user's existing entries;
    threshold 0.45 catches paraphrases ("User enjoys epic worldbuilding" vs
    "the user loves epic world-building") while keeping distinct memories.
    """
    new_tokens = _memory_tokens(content)
    if not new_tokens:
        return None
    try:
        ub_session = _session()
        existing = ub_session.query(AiUserMemory).filter_by(user_id=user_id)\
            .order_by(AiUserMemory.created_at.desc()).limit(50).all()
    except Exception as e:
        log.warning("duplicate check failed (storing anyway): %s", e)
        return None
    for row in existing:
        if _similarity(new_tokens, _memory_tokens(row.content)) >= threshold:
            return row
    return None


def extract_user_memory(provider, model: str, recent_messages: list,
                        user_id: int, book_id: int) -> Optional[str]:
    """Call the provider to extract a concise user-memory insight from recent messages.

    Stores the result in ``AiUserMemory`` and returns the extracted string
    (or None if nothing worth remembering was found).
    """
    extraction_prompt = (
        "You are a memory assistant. Read the following conversation between a user and an AI reading companion. "
        "Extract ONE concise sentence capturing a durable insight about this user — their reading preferences, "
        "interests, knowledge level, or what they care about. "
        "Output only the sentence, no preamble. If there is nothing worth remembering, output exactly: NONE"
    )
    messages = [{"role": "system", "content": extraction_prompt}]
    # Include up to the last N messages of context
    for m in recent_messages[-_MAX_RECENT_MESSAGES:]:
        messages.append({"role": m["role"], "content": m["content"]})

    try:
        result = provider.chat(messages, model=model, stream=False)
        result = (result or "").strip()
    except Exception as e:
        log.warning("memory extraction failed: %s", e)
        return None

    if not result or result.upper() == "NONE":
        return None

    try:
        ub_session = _session()
        # 去重/合并：与该用户现有记忆比对，近重复（换书重提炼的同一偏好）
        # 跳过写入，仅刷新原条目时间戳——防止重复行挤占注入窗口
        dup = find_duplicate_memory(user_id, result)
        if dup is not None:
            dup.created_at = __import__("datetime").datetime.utcnow()
            ub_session.commit()
            log.info("memory deduplicated (kept existing id=%s): %s", dup.id, result)
            return None

        mem = AiUserMemory()
        mem.user_id = user_id
        mem.content = result
        mem.source_book_id = book_id
        ub_session.add(mem)
        ub_session.commit()
    except Exception as e:
        log.warning("failed to store user memory: %s", e)
        try:
            ub_session.rollback()
        except Exception:
            pass

    return result


def select_relevant_memories(user_id: int, book_id=None,
                             book_keywords: Optional[List[str]] = None,
                             limit: int = 10) -> List[str]:
    """Return memories ordered by relevance to the current book, capped at limit.

    Relevance rules (no embeddings, cheap & explainable):
      1. memories extracted from the current book (source_book_id match) first;
      2. then memories whose text mentions the current book's keywords
         (title/author/tag words) — e.g. a genre preference recorded while
         reading another book by the same author;
      3. remaining recent memories fill the rest of the window.
    Duplicates the cap semantics of get_user_memory_strings but never lets
    off-topic rows crowd out on-topic ones.
    """
    try:
        ub_session = _session()
        rows = ub_session.query(AiUserMemory).filter_by(user_id=user_id)\
            .order_by(AiUserMemory.created_at.desc()).limit(50).all()
    except Exception as e:
        log.warning("failed to load user memory: %s", e)
        return []

    keywords = [k.lower() for k in (book_keywords or []) if k and len(str(k)) > 1]

    def relevance(row):
        if book_id is not None and row.source_book_id == book_id:
            return 0  # 本书记忆最相关
        text = (row.content or "").lower()
        if keywords and any(k in text for k in keywords):
            return 1  # 提到当前书关键词(作者/题材等)
        return 2      # 其他

    ordered = sorted(rows, key=relevance)
    return [row.content for row in ordered[:limit]]


def get_user_memory_strings(user_id: int, limit: int = 20) -> List[str]:
    """Return the user's long-term memory entries as a list of strings (newest first)."""
    try:
        ub_session = _session()
        mems = ub_session.query(AiUserMemory).filter_by(user_id=user_id)\
            .order_by(AiUserMemory.created_at.desc()).limit(limit).all()
        return [m.content for m in mems]
    except Exception as e:
        log.warning("failed to load user memory: %s", e)
        return []

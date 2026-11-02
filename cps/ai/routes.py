"""AI companion legacy blueprint — RETIRED chat path, read-only remnants.

Why conversations instead of one thread per book:
- A reader previously had exactly one chat thread per (user, book). Users now
  want multiple independent conversations per book ("+ 新建会话" + a dropdown
  to switch). The ``conversation_id`` is carried by the frontend on every chat
  request; ``/ai/conversations/<book_id>`` lists and creates threads.

Retirement (2026-09-29, agent backendization switch, magicbook-side design §6.2):
- The live companion chat moved to moon-well as a bounded agent loop; magicbook
  only keeps a thin proxy at ``cps/ai/proxy.py`` (/ai/agent/*). This module's
  WRITE endpoints permanently return 410 so ai_companion.db stops evolving —
  scripts/migrate_ai_companion_to_moonwell.py migrates the frozen data once.
- READ endpoints (conversation list / history / memory list) stay until the
  migration is verified in production, then the whole package goes away
  (design §4.3 retirement checklist).
- Provider/registry/crypto/memory helpers are no longer imported here; their
  files remain on disk only for the migration window and are deleted together
  with the SQLite archive.

Storage:
- All AI rows live in the independent AI data layer (``cps.ai.database``),
  NOT in calibre-web's ub.session. See cps/ai/database.py for why.

Authentication uses calibre-web's existing ``user_login_required`` decorator.
CSRF is handled by Flask-WTF (the frontend sends the X-CSRFToken header).
"""
from sqlalchemy import func

from flask import Blueprint, jsonify
from cps import logger
from cps.cw_login import current_user
from cps.usermanagement import user_login_required

from .models import AiConversation, AiMessage
from .database import get_session
from .memory import get_user_memory_strings

log = logger.create()

aichat = Blueprint("aichat", __name__)

# Default title shown in the conversation dropdown until the first real
# question gives the thread a meaningful name.
DEFAULT_CONV_TITLE = "新会话"


def _session():
    """Lazy access to the AI data session (read at call time, not import time)."""
    return get_session()


def _gone():
    """统一 410 响应：写路径已随 agent 后端化永久停写。"""
    return jsonify({
        "error": "AI 伴读已升级为 agent 模式（由 moon-well 承载），请刷新页面使用新版对话面板",
        "gone": True,
    }), 410


def _serialize_message(msg):
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "page_context": msg.page_context or "",
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


# ---------------------------------------------------------------------------
# Read-only remnants（迁移验证期内保留；新前端已走 /ai/agent/* 薄代理）
# ---------------------------------------------------------------------------

@aichat.route("/ai/conversations/<int:book_id>", methods=["GET"])
@user_login_required
def conversations(book_id):
    """Return all conversations of the current user for a book (newest first).

    ``message_count`` lets the frontend show how active each thread is.
    """
    sess = _session()
    convs = sess.query(AiConversation).filter_by(
        user_id=current_user.id, book_id=book_id)\
        .order_by(AiConversation.updated_at.desc()).all()
    if not convs:
        return jsonify({"conversations": []})
    # Batch-count messages once instead of one count() query per conversation.
    conv_ids = [c.id for c in convs]
    counts = dict(
        sess.query(AiMessage.conversation_id,
                   func.count(AiMessage.id))
        .filter(AiMessage.conversation_id.in_(conv_ids))
        .group_by(AiMessage.conversation_id).all())
    out = []
    for c in convs:
        out.append({
            "id": c.id,
            "title": c.title or DEFAULT_CONV_TITLE,
            "book_id": c.book_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "message_count": counts.get(c.id, 0),
        })
    return jsonify({"conversations": out})


@aichat.route("/ai/history/<int:conversation_id>", methods=["GET"])
@user_login_required
def history(conversation_id):
    """Return the message history of one conversation as JSON."""
    sess = _session()
    conv = sess.query(AiConversation).filter_by(
        id=conversation_id, user_id=current_user.id).first()
    if conv is None:
        return jsonify({"messages": [], "conversation": None})
    msgs = conv.messages.order_by(AiMessage.created_at.asc()).all()
    return jsonify({
        "conversation": {
            "id": conv.id,
            "title": conv.title or DEFAULT_CONV_TITLE,
            "book_id": conv.book_id,
        },
        "messages": [_serialize_message(m) for m in msgs],
    })


@aichat.route("/ai/memory", methods=["GET"])
@user_login_required
def get_memory():
    """Return the current user's long-term memory entries."""
    mems = get_user_memory_strings(current_user.id, limit=50)
    return jsonify({"memories": mems})


# ---------------------------------------------------------------------------
# Retired write endpoints（永久 410，停写 ai_companion.db）
# ---------------------------------------------------------------------------

@aichat.route("/ai/chat", methods=["POST"])
@user_login_required
def chat():
    """Retired：伴读对话已迁 moon-well agent（/ai/agent/chat 薄代理）。"""
    return _gone()


@aichat.route("/ai/conversations/<int:book_id>", methods=["POST"])
@user_login_required
def new_conversation(book_id):
    """Retired：会话由 moon-well 服务端在首问时创建（薄代理）。"""
    return _gone()


@aichat.route("/ai/conversations/<int:conversation_id>/rename", methods=["POST"])
@user_login_required
def rename_conversation(conversation_id):
    """Retired：走薄代理 /ai/agent/conversation/rename。"""
    return _gone()


@aichat.route("/ai/history/<int:conversation_id>", methods=["DELETE"])
@user_login_required
def clear_history(conversation_id):
    """Retired：走薄代理 /ai/agent/conversation/delete。"""
    return _gone()


@aichat.route("/ai/memory/clear", methods=["POST"])
@user_login_required
def clear_memory():
    """Retired：记忆管理走薄代理 /ai/agent/memory/*。"""
    return _gone()


@aichat.route("/ai/test_provider", methods=["POST"])
@user_login_required
def test_provider():
    """Retired：provider 管理随 agent 后端化退役（moon-well LlmGateway + Nacos 承接）。"""
    return _gone()


@aichat.route("/ai/admin", methods=["GET", "POST"])
@user_login_required
def admin():
    """Retired：provider/model 配置页下线（配置收敛 Nacos ai.llm.configs）。"""
    return _gone()

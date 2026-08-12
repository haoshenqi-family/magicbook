"""AI companion blueprint — chat API, conversations, history, memory, admin.

Why conversations instead of one thread per book:
- A reader previously had exactly one chat thread per (user, book). Users now
  want multiple independent conversations per book ("+ 新建会话" + a dropdown
  to switch). The ``conversation_id`` is carried by the frontend on every chat
  request; ``/ai/conversations/<book_id>`` lists and creates threads.

Storage:
- All AI rows live in the independent AI data layer (``cps.ai.database``),
  NOT in calibre-web's ub.session. See cps/ai/database.py for why.

Routes are mounted under ``/ai/``. Authentication uses calibre-web's existing
``user_login_required`` decorator. CSRF is handled by Flask-WTF (the frontend
sends the X-CSRFToken header).
"""
import json
import os

from sqlalchemy import func

from flask import (Blueprint, Response, request, jsonify, stream_with_context,
                   abort)
from flask_babel import gettext as _

from cps import logger, calibre_db
from cps.cw_login import current_user
from cps.usermanagement import user_login_required
from cps.render_template import render_title_template
from cps.config_sql import get_encryption_key

from .models import (AiConfig, AiProvider, AiConversation, AiMessage,
                     AiUserMemory)
from .registry import get_provider, list_providers
from .crypto import encrypt_value, decrypt_value
from .database import get_session
from .timezone import now as now_cn
from .memory import (build_system_prompt, extract_user_memory,
                     get_user_memory_strings, should_extract_memory)

log = logger.create()

aichat = Blueprint("aichat", __name__)

# Default title shown in the conversation dropdown until the first real
# question gives the thread a meaningful name.
DEFAULT_CONV_TITLE = "新会话"
_TITLE_MAX_LEN = 30


def _session():
    """Lazy access to the AI data session (read at call time, not import time)."""
    return get_session()


def _get_encryption_key():
    """Get the Fernet key calibre-web uses for config secrets.

    Returns the raw bytes key (or empty bytes if unavailable).
    """
    from cps import ub
    settings_path = os.path.dirname(ub.app_DB_path)
    key, _err = get_encryption_key(settings_path)
    return key or b""


def get_active_provider():
    """Instantiate the active provider from DB config.

    Returns ``(provider_instance, model_id)`` or raises ``RuntimeError`` if
    AI is disabled or no provider is configured.
    """
    sess = _session()
    cfg = sess.query(AiConfig).first()
    if cfg is None or not cfg.enabled:
        raise RuntimeError("AI companion is disabled")

    provider_name = cfg.default_provider
    prov_row = sess.query(AiProvider).filter_by(provider_name=provider_name).first()
    if prov_row is None:
        raise RuntimeError(f"provider '{provider_name}' not configured")

    key = _get_encryption_key()
    api_key = decrypt_value(prov_row.api_key_encrypted, key)

    provider = get_provider(provider_name, api_base=prov_row.api_base,
                            api_key=api_key)
    # Some providers (e.g. OpenAI-compatible local gateways) work without an
    # API key; only enforce a key when the provider class requires it.
    if not api_key and provider.requires_key:
        raise RuntimeError(f"provider '{provider_name}' has no API key set")
    return provider, cfg.default_model


def _serialize_message(msg):
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "page_context": msg.page_context or "",
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _get_or_create_conversation(user_id, book_id, book_format, title,
                                conversation_id=None):
    """Return an existing conversation (by id, if it belongs to the user+book)
    or create a fresh one.

    Ownership guard: a conversation_id that belongs to another user or another
    book returns None so the caller can reject the request (404) — we never
    fall through to creating/joining a thread the user shouldn't touch.

    New threads always start with the generic title; the first real question
    renames them (see chat()). We deliberately ignore ``title`` here so the
    auto-naming isn't defeated by book metadata titles.
    """
    sess = _session()
    if conversation_id is not None:
        conv = sess.query(AiConversation).filter_by(id=conversation_id).first()
        if conv is None or conv.user_id != user_id:
            return None
        if book_id and conv.book_id != book_id:
            return None
        return conv

    conv = AiConversation()
    conv.user_id = user_id
    conv.book_id = book_id
    conv.book_format = book_format or ""
    conv.title = DEFAULT_CONV_TITLE
    sess.add(conv)
    sess.commit()
    return conv


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


@aichat.route("/ai/conversations/<int:book_id>", methods=["POST"])
@user_login_required
def new_conversation(book_id):
    """Create a fresh empty conversation for the current user + book."""
    sess = _session()
    body = request.get_json(silent=True) or {}
    conv = AiConversation()
    conv.user_id = current_user.id
    conv.book_id = book_id
    conv.book_format = body.get("book_format", "")
    conv.title = DEFAULT_CONV_TITLE
    sess.add(conv)
    sess.commit()
    return jsonify({"conversation_id": conv.id, "title": conv.title})


@aichat.route("/ai/conversations/<int:conversation_id>/rename", methods=["POST"])
@user_login_required
def rename_conversation(conversation_id):
    """Rename a conversation owned by the current user.

    Request JSON: ``{title}``. Empty/whitespace titles are rejected so a
    thread never ends up with a blank label in the dropdown.
    """
    sess = _session()
    conv = sess.query(AiConversation).filter_by(
        id=conversation_id, user_id=current_user.id).first()
    if conv is None:
        return jsonify({"error": "conversation not found or not owned"}), 404

    body = request.get_json(silent=True) or {}
    raw = body.get("title")
    title = raw.strip() if isinstance(raw, str) else ""
    if not title:
        return jsonify({"error": "title is required"}), 400
    if len(title) > 500:
        return jsonify({"error": "title too long"}), 400

    conv.title = title
    sess.commit()
    return jsonify({"conversation_id": conv.id, "title": conv.title})


@aichat.route("/ai/chat", methods=["POST"])
@user_login_required
def chat():
    """Stream a chat completion response.

    Request JSON: ``{book_id, conversation_id?, book_format, message,
                     page_context, book_title?, book_authors?,
                     book_description?, book_tags?}``
    Response: ``text/event-stream`` of content deltas (``data: <chunk>\\n\\n``),
    terminated by ``data: [DONE]``.

    If ``conversation_id`` is omitted the server creates a new conversation.
    """
    sess = _session()
    data = request.get_json(silent=True) or {}
    book_id = data.get("book_id")
    message = (data.get("message") or "").strip()
    if not book_id or not message:
        return jsonify({"error": "book_id and message are required"}), 400

    # Try to fetch book metadata from calibre DB if not provided by frontend
    book_title = data.get("book_title", "")
    book_authors = data.get("book_authors", []) or []
    book_description = data.get("book_description", "")
    book_tags = data.get("book_tags", []) or []

    try:
        book = calibre_db.get_filtered_book(book_id)
        if book:
            if not book_title:
                book_title = book.title
            if not book_authors:
                book_authors = [a.name for a in book.authors]
            if not book_description and book.comments:
                book_description = book.comments[0].text or ""
            if not book_tags:
                book_tags = [t.name for t in book.tags]
    except Exception as e:
        log.warning("could not fetch book metadata for %s: %s", book_id, e)

    page_context = data.get("page_context", "")
    book_format = data.get("book_format", "")
    conversation_id = data.get("conversation_id")

    # Load config + memory
    cfg = sess.query(AiConfig).first()
    user_memory = []
    if cfg and cfg.memory_enabled:
        user_memory = get_user_memory_strings(current_user.id, limit=10)

    system_prompt = build_system_prompt(
        book_title=book_title or "Unknown",
        book_authors=book_authors,
        book_description=book_description,
        book_tags=book_tags,
        page_context=page_context,
        user_memory=user_memory,
        extra_prompt=cfg.system_prompt_extra if cfg else "",
    )

    # Get or create conversation + load history. title is intentionally empty:
    # new threads are auto-named from the first question (see _get_or_create_conversation).
    conv = _get_or_create_conversation(current_user.id, book_id, book_format,
                                       "", conversation_id)
    if conv is None:
        return jsonify({"error": "conversation not found or not owned"}), 404
    history_msgs = sess.query(AiMessage).filter_by(conversation_id=conv.id)\
        .order_by(AiMessage.created_at.asc()).all()

    messages = [{"role": "system", "content": system_prompt}]
    for hm in history_msgs:
        messages.append({"role": hm.role, "content": hm.content})
    messages.append({"role": "user", "content": message})

    # Save the user message; auto-name the thread from the first question.
    user_msg = AiMessage()
    user_msg.conversation_id = conv.id
    user_msg.role = "user"
    user_msg.content = message
    user_msg.page_context = (page_context or "")[:4000]
    sess.add(user_msg)
    if not conv.title or conv.title == DEFAULT_CONV_TITLE:
        conv.title = message.replace("\n", " ")[:_TITLE_MAX_LEN] or DEFAULT_CONV_TITLE
    conv.updated_at = now_cn()
    sess.commit()

    try:
        provider, model = get_active_provider()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    conv_id = conv.id
    user_id = current_user.id
    memory_enabled = bool(cfg and cfg.memory_enabled)
    extract_interval = cfg.memory_extract_interval if cfg else 10

    def generate():
        full_reply = []
        try:
            for delta in provider.chat(messages, model=model, stream=True):
                full_reply.append(delta)
                yield f"data: {json.dumps({'delta': delta})}\n\n"
        except Exception as e:
            log.error("chat streaming error: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # Save the assistant reply (persist every exchange to the DB).
        reply_text = "".join(full_reply)
        try:
            asst_msg = AiMessage()
            asst_msg.conversation_id = conv_id
            asst_msg.role = "assistant"
            asst_msg.content = reply_text
            sess.add(asst_msg)
            # Bump the thread's activity time so the conversation list orders
            # by "most recently active" rather than creation order.
            conv_row = sess.query(AiConversation).filter_by(id=conv_id).first()
            if conv_row is not None:
                conv_row.updated_at = now_cn()
            sess.commit()

            # Maybe extract memory
            if memory_enabled:
                msg_count = sess.query(AiMessage).filter_by(
                    conversation_id=conv_id).count()
                if should_extract_memory(msg_count, extract_interval):
                    all_msgs = [{"role": m.role, "content": m.content} for m in
                                sess.query(AiMessage).filter_by(
                                    conversation_id=conv_id).order_by(
                                    AiMessage.created_at.asc()).all()]
                    try:
                        extract_user_memory(provider, model, all_msgs,
                                            user_id, book_id)
                    except Exception as e:
                        log.warning("memory extraction failed: %s", e)
        except Exception as e:
            log.error("failed to save assistant message: %s", e)
            try:
                sess.rollback()
            except Exception:
                pass

        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


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


@aichat.route("/ai/history/<int:conversation_id>", methods=["DELETE"])
@user_login_required
def clear_history(conversation_id):
    """Delete one conversation (and all its messages)."""
    sess = _session()
    conv = sess.query(AiConversation).filter_by(
        id=conversation_id, user_id=current_user.id).first()
    if conv:
        sess.delete(conv)
        sess.commit()
    return jsonify({"status": "ok"})


@aichat.route("/ai/memory", methods=["GET"])
@user_login_required
def get_memory():
    """Return the current user's long-term memory entries."""
    mems = get_user_memory_strings(current_user.id, limit=50)
    return jsonify({"memories": mems})


@aichat.route("/ai/memory/clear", methods=["POST"])
@user_login_required
def clear_memory():
    """Delete all long-term memory entries for the current user."""
    sess = _session()
    sess.query(AiUserMemory).filter_by(user_id=current_user.id).delete()
    sess.commit()
    return jsonify({"status": "ok"})


@aichat.route("/ai/admin", methods=["GET", "POST"])
@user_login_required
def admin():
    """AI provider/model configuration page (admin only)."""
    if not current_user.role_admin():
        abort(403)
    sess = _session()

    if request.method == "POST":
        cfg = sess.query(AiConfig).first()
        if cfg is None:
            cfg = AiConfig()
            sess.add(cfg)
        cfg.enabled = request.form.get("enabled") == "on"
        cfg.default_provider = request.form.get("default_provider", "deepseek")
        cfg.default_model = request.form.get("default_model", "deepseek-chat")
        cfg.memory_enabled = request.form.get("memory_enabled") == "on"
        try:
            cfg.memory_extract_interval = int(request.form.get("memory_extract_interval", 10))
        except (ValueError, TypeError):
            cfg.memory_extract_interval = 10
        cfg.system_prompt_extra = request.form.get("system_prompt_extra", "")

        # Update provider configs
        key = _get_encryption_key()
        for prov in sess.query(AiProvider).all():
            field_prefix = f"provider_{prov.id}_"
            prov.api_base = request.form.get(field_prefix + "api_base", prov.api_base)
            new_key = request.form.get(field_prefix + "api_key", "")
            if new_key:
                prov.api_key_encrypted = encrypt_value(new_key, key)
            prov.active = request.form.get(field_prefix + "active") == "on"

            # For authentik, store client_secret in models_json; for AI providers
            # parse newline-separated "id|label" lines into JSON.
            if prov.provider_name == "authentik":
                new_secret = request.form.get(field_prefix + "client_secret", "")
                extra = {}
                try:
                    extra = json.loads(prov.models_json or "{}")
                    if not isinstance(extra, dict):
                        extra = {}
                except (ValueError, TypeError):
                    extra = {}
                if new_secret:
                    extra["client_secret_encrypted"] = encrypt_value(new_secret, key)
                prov.models_json = json.dumps(extra)
            else:
                models_text = request.form.get(field_prefix + "models", "")
                models_list = []
                for line in models_text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if "|" in line:
                        mid, mlabel = line.split("|", 1)
                    else:
                        mid, mlabel = line, line
                    models_list.append({"id": mid.strip(), "label": mlabel.strip()})
                prov.models_json = json.dumps(models_list)

        sess.commit()

    cfg = sess.query(AiConfig).first()
    if cfg is None:
        cfg = AiConfig()
        sess.add(cfg)
        sess.commit()
    providers = sess.query(AiProvider).all()
    available_provider_classes = list_providers()

    return render_title_template("ai_admin.html", title=_("AI Companion Settings"),
                                 config=cfg, providers=providers,
                                 available_providers=available_provider_classes,
                                 page="aiadmin")

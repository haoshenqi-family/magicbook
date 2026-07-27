"""AI companion blueprint — chat API, history, memory, and admin config routes.

All routes are mounted under ``/ai/``. The blueprint is registered in
``cps/main.py``. Authentication uses calibre-web's existing
``user_login_required`` decorator. CSRF is handled automatically by
Flask-WTF's CSRFProtect (the frontend sends the X-CSRFToken header).
"""
import json
import os

from flask import (Blueprint, Response, request, jsonify, stream_with_context,
                   abort)
from flask_babel import gettext as _

from cps import logger, calibre_db, ub
from cps.cw_login import current_user
from cps.usermanagement import user_login_required
from cps.render_template import render_title_template
from cps.config_sql import get_encryption_key

from .models import (AiConfig, AiProvider, AiConversation, AiMessage,
                     AiUserMemory)
from .registry import get_provider, list_providers
from .crypto import encrypt_value, decrypt_value
from .memory import (build_system_prompt, extract_user_memory,
                     get_user_memory_strings, should_extract_memory)

log = logger.create()

aichat = Blueprint("aichat", __name__)


def _session():
    """Lazy access to cps.ub.session (read at call time, not import time)."""
    return ub.session


def _get_encryption_key():
    """Get the Fernet key calibre-web uses for config secrets.

    Returns the raw bytes key (or empty bytes if unavailable).
    """
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
    if not api_key:
        raise RuntimeError(f"provider '{provider_name}' has no API key set")

    provider = get_provider(provider_name, api_base=prov_row.api_base,
                            api_key=api_key)
    return provider, cfg.default_model


def _serialize_message(msg):
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "page_context": msg.page_context or "",
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _get_or_create_conversation(user_id, book_id, book_format, title):
    sess = _session()
    conv = sess.query(AiConversation).filter_by(
        user_id=user_id, book_id=book_id
    ).first()
    if conv is None:
        conv = AiConversation()
        conv.user_id = user_id
        conv.book_id = book_id
        conv.book_format = book_format or ""
        conv.title = title or ""
        sess.add(conv)
        sess.commit()
    return conv


@aichat.route("/ai/chat", methods=["POST"])
@user_login_required
def chat():
    """Stream a chat completion response.

    Request JSON: ``{book_id, book_format, message, page_context,
                     book_title?, book_authors?, book_description?, book_tags?}``
    Response: ``text/event-stream`` of content deltas (``data: <chunk>\\n\\n``),
    terminated by ``data: [DONE]``.
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

    # Get or create conversation + load history
    conv = _get_or_create_conversation(current_user.id, book_id, book_format,
                                       book_title)
    history_msgs = sess.query(AiMessage).filter_by(conversation_id=conv.id)\
        .order_by(AiMessage.created_at.asc()).all()

    messages = [{"role": "system", "content": system_prompt}]
    for hm in history_msgs:
        messages.append({"role": hm.role, "content": hm.content})
    messages.append({"role": "user", "content": message})

    # Save the user message
    user_msg = AiMessage()
    user_msg.conversation_id = conv.id
    user_msg.role = "user"
    user_msg.content = message
    user_msg.page_context = (page_context or "")[:4000]
    sess.add(user_msg)
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

        # Save the assistant reply
        reply_text = "".join(full_reply)
        try:
            asst_msg = AiMessage()
            asst_msg.conversation_id = conv_id
            asst_msg.role = "assistant"
            asst_msg.content = reply_text
            sess.add(asst_msg)
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


@aichat.route("/ai/history/<int:book_id>", methods=["GET"])
@user_login_required
def history(book_id):
    """Return the conversation history for a book as JSON."""
    sess = _session()
    conv = sess.query(AiConversation).filter_by(
        user_id=current_user.id, book_id=book_id).first()
    if conv is None:
        return jsonify({"messages": []})
    msgs = conv.messages.order_by(AiMessage.created_at.asc()).all()
    return jsonify({"messages": [_serialize_message(m) for m in msgs]})


@aichat.route("/ai/history/<int:book_id>", methods=["DELETE"])
@user_login_required
def clear_history(book_id):
    """Delete the conversation (and all its messages) for a book."""
    sess = _session()
    conv = sess.query(AiConversation).filter_by(
        user_id=current_user.id, book_id=book_id).first()
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

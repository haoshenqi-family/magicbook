# cps/routes/reading.py — reading 域定制路由（R181，架构评审 B2 自 cps.web 迁出）。
# 装饰注册沿用原 web blueprint（endpoint 名不变）；依赖的辅助符号显式列于 import。
# moon-well 调用一律经 cps/moonwell/client.py（B1 防腐层），测试桩面稳定在 client。

from cps.web import (
    _READING_WORD_RE,
    _moonwell_proxy,
    _moonwell_settings_fetch,
    _ted_book_identity,
    _whole_book_closures,
    _whole_book_tts_closures,
    web,
    whole_book_translation_service,
    whole_book_tts_service,
)
from ..admin import admin_required
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from flask import jsonify
from flask import request
from flask_babel import gettext as _
from sqlalchemy.sql.expression import text
from urllib.parse import quote
import zipfile


@web.route("/ajax/reading-vocabulary", methods=["POST"])
@user_login_required
def reading_vocabulary():
    """Proxy the reader's word context using the caller's moon-well JWT."""
    # 15s 超时容忍 moon-well 重启后首次连接 ES 的临时慢响应
    return _moonwell_proxy("/vocabulary/reading/analyze",
                           request.get_json(silent=True) or {}, 15,
                           "reading vocabulary")


@web.route("/ajax/reading-translate", methods=["POST"])
@user_login_required
def reading_translate():
    """Proxy selected reader text using the caller's moon-well JWT."""
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text or len(text) > 2000:
        return jsonify({"success": False, "message": "selected text must be between 1 and 2000 characters"}), 400
    payload["text"] = text
    return _moonwell_proxy("/vocabulary/reading/translate", payload, 20,
                           "reading translation")


@web.route("/ajax/reading-translate-batch", methods=["POST"])
@user_login_required
def reading_translate_batch():
    """Proxy paragraph translation (one paragraph per request; the frontend
    fans a page out into concurrent single-paragraph calls)."""
    payload = request.get_json(silent=True) or {}
    paragraphs = payload.get("paragraphs")
    if not isinstance(paragraphs, list) or not 1 <= len(paragraphs) <= 20:
        return jsonify({"success": False,
                        "message": "paragraphs must contain 1 to 20 items"}), 400
    cleaned = []
    for item in paragraphs:
        text = str(item or "").strip()
        if not text or len(text) > 2000:
            return jsonify({"success": False,
                            "message": "each paragraph must be between 1 and 2000 characters"}), 400
        cleaned.append(text)
    payload["paragraphs"] = cleaned
    # 书籍上下文供 LLM 保持全书译法一致（moon-well 提示词模板变量）
    payload["bookName"] = str(payload.get("bookName") or "").strip()[:200]
    payload["chapter"] = str(payload.get("chapter") or "").strip()[:200]
    # 20s：现在是单段一次 LLM 调用（前端并发），不再需要整页批量的长超时
    return _moonwell_proxy("/vocabulary/reading/translate-batch", payload, 20,
                           "reading batch translation")


@web.route("/ajax/reading-tts", methods=["POST"])
@user_login_required
def reading_tts():
    """Proxy reader paragraph speech to moon-well (relays to Bailian TTS)."""
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text or len(text) > 2000:
        return jsonify({"success": False,
                        "message": "text must be between 1 and 2000 characters"}), 400
    payload["text"] = text
    # 书籍上下文决定 moon-well 侧音频缓存分级（有上下文=书籍段落，永久缓存；
    # 无上下文=AI 临时语音，7 天清理）。与翻译代理同口径清洗，避免超长字符串进 ES 文档
    payload["bookName"] = str(payload.get("bookName") or "").strip()[:200]
    payload["chapter"] = str(payload.get("chapter") or "").strip()[:200]
    # 65s：moon-well 调百炼合成并下载音频，比 JSON 接口慢
    return _moonwell_proxy("/tts/speak", payload, 65, "reading tts", binary=True)


@web.route("/ajax/reading-tts-cached", methods=["POST"])
@user_login_required
def reading_tts_cached():
    """回读已合成好的朗读音频（R170，伴读 agent 播放用），透传 moon-well 不计费端点。

    Why 不复用 /ajax/reading-tts：那条走 moon-well `/tts/speak`，语义是「听=消费」——
    每次请求（含缓存命中）都扣 1 积分。伴读工具 synthesize_tts 已在工具内合成并扣过分，
    前端再走 /speak 就是同一次朗读扣两遍，所以走 /tts/cached-audio（只读缓存、miss 404）。
    text 必须原样透传：moon-well 的缓存键是 trim 后原文的 SHA-256，这里再清洗一次反而会 miss。
    """
    payload = request.get_json(silent=True) or {}
    # `or ""` 而不是 get("text", "")：JSON null 会命中默认值失效的路径，str(None)=="None"
    # 会被当成合法文本送去合成（白扣一次积分、播一句「None」）
    text = str(payload.get("text") or "").strip()
    if not text or len(text) > 2000:
        return jsonify({"success": False,
                        "message": "text must be between 1 and 2000 characters"}), 400
    # 20s：只有一次 ES GET + 一次 MinIO 对象读取，远快于合成链路
    return _moonwell_proxy("/tts/cached-audio", {"text": text}, 20,
                           "reading tts cache", binary=True)


@web.route("/ajax/ted-audio", methods=["POST"])
@user_login_required
def reading_ted_audio():
    """Proxy TED talk original-audio cache lookup（整段原声地址/时长）。

    R172：TED/博客类书的内容本质是「一段连续原声」，阅读器伴听直接播整段，
    不走逐段 TTS 合成（逐段合成会把真人原声换成机器音且白烧算力/积分）。
    R200：改写为按 **书名+作者** 查——moon-well 的 bookId 是它自己 book 表的 id，
    与本仓 Calibre 书号是两套序列，按 id 透传只有巧合对齐才命中。
    未缓存 / 未建注册表时上游 result 为 null，前端据此回落 TTS 或隐藏按钮。
    """
    book_name, author, error = _ted_book_identity()
    if error:
        status = 404 if error[0] == "not_found" else 400
        return jsonify({"success": False, "message": error[1]}), status
    return _moonwell_proxy("/book/ted-audio",
                           {"bookName": book_name, "author": author}, 15, "ted audio")


@web.route("/ajax/ted-audio-paragraphs", methods=["POST"])
@user_login_required
def reading_ted_audio_paragraphs():
    """Proxy TED book paragraph registry（段落 order + 原声时间轴切片）。

    R172：时间轴驱动的高亮依赖段落级 tedAudioStart/End（该段在整段原声中的
    毫秒偏移），与 EPUB 段落 1:1；与 /ajax/ted-audio 同批并发拉取。
    R200：同样改按书名+作者查（`/book/paragraph/list` 本就支持该入参）。
    """
    book_name, author, error = _ted_book_identity()
    if error:
        status = 404 if error[0] == "not_found" else 400
        return jsonify({"success": False, "message": error[1]}), status
    return _moonwell_proxy("/book/paragraph/list",
                           {"bookName": book_name, "author": author}, 15,
                           "ted audio paragraphs")


@web.route("/reading/settings", methods=["GET"])
@user_login_required
def reading_settings():
    """阅读设置独立页：用户难度档位等 per-user 阅读偏好（后续配置统一挂这里）。"""
    settings, error = _moonwell_settings_fetch()
    # 词汇量测试卡片不在这里拉历史：服务端同步拉等于给首屏再加一次上游超时预算（最坏 10s×2），
    # 历史只是摘要，交给模板里的 vocab-test.js 异步取、失败静默降级（成就页 /ajax/achievements-* 同模式）
    return render_title_template("reading_settings.html", title=_("Reading Settings"),
                                 settings=settings, load_error=error)


@web.route("/ajax/reading-settings", methods=["GET"])
@user_login_required
def reading_settings_get():
    """Proxy the user's reading settings (currently hard level only)."""
    body, status, headers = _moonwell_proxy("/vocabulary/reading/settings", None, 10,
                                            "reading settings", method="GET")
    return body, status, headers


@web.route("/ajax/reading-settings/hard-level", methods=["POST"])
@user_login_required
def reading_settings_update_hard_level():
    """Proxy the hard level update; payload {"hardLevel": 0-9}."""
    payload = request.get_json(silent=True) or {}
    level = payload.get("hardLevel")
    if level is None:
        return jsonify({"success": False, "message": "hardLevel is required"}), 400
    return _moonwell_proxy("/vocabulary/reading/settings/hard-level", payload, 10,
                           "reading settings update")


@web.route("/ajax/reading-translate-book", methods=["POST"])
@user_login_required
@admin_required
def reading_translate_book():
    """Create a durable whole-book translation batch from an EPUB/Kepub."""
    payload = request.get_json(silent=True) or {}
    try:
        book_id = int(payload.get("book_id"))
        book_format = str(payload.get("book_format") or "epub").lower()
        force = bool(payload.get("force", False))

        publish, lookup = _whole_book_closures()
        return jsonify(whole_book_translation_service.start(book_id, book_format, force, publish, lookup))
    except (TypeError, ValueError, OSError, zipfile.BadZipFile) as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/reading-translate-book/status", methods=["POST"])
@user_login_required
@admin_required
def reading_translate_book_status():
    payload = request.get_json(silent=True) or {}
    try:
        # 去回调化：查询进度时对未完成项单向查 moon-well 缓存，懒回收完成状态。
        _, lookup = _whole_book_closures()
        return jsonify(whole_book_translation_service.get_progress(str(payload.get("job_id")), lookup))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404


@web.route("/ajax/reading-translate-book/retry", methods=["POST"])
@user_login_required
@admin_required
def reading_translate_book_retry():
    payload = request.get_json(silent=True) or {}
    try:
        publish, _ = _whole_book_closures()
        return jsonify(whole_book_translation_service.retry(str(payload.get("job_id")), publish))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/reading-translate-book/cancel", methods=["POST"])
@user_login_required
@admin_required
def reading_translate_book_cancel():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(whole_book_translation_service.cancel(str(payload.get("job_id"))))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/reading-translate-all", methods=["POST"])
@user_login_required
@admin_required
def reading_translate_all_books():
    """一键翻译全部英文书：逐本建批次并后台发布，正在跑的书跳过。"""
    publish, lookup = _whole_book_closures()
    return jsonify(whole_book_translation_service.translate_all_english_books(publish, lookup))


@web.route("/ajax/reading-translate-all/progress", methods=["POST"])
@user_login_required
@admin_required
def reading_translate_all_progress():
    # R78: 传入 lookup——进度页每次刷新顺带做缓存懒回收，数字跟着
    # moon-well 的实际完成走，不再是静态快照
    _, lookup = _whole_book_closures()
    return jsonify(whole_book_translation_service.all_books_progress(lookup))


@web.route("/ajax/reading-tts-book", methods=["POST"])
@user_login_required
@admin_required
def reading_tts_book_start():
    """受理整本朗读批次：立即返回进度快照，合成在后台 daemon 串行执行。"""
    payload = request.get_json(silent=True) or {}
    try:
        book_id = int(payload.get("book_id"))
        book_format = str(payload.get("book_format") or "epub").lower()
        proxy = _whole_book_tts_closures()
        return jsonify(whole_book_tts_service.start(book_id, book_format, proxy,
                                                    force_voice=bool(payload.get("force_voice", False))))
    except (TypeError, ValueError, zipfile.BadZipFile) as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/reading-tts-book/status", methods=["POST"])
@user_login_required
@admin_required
def reading_tts_book_status():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(whole_book_tts_service.get_progress(str(payload.get("job_id"))))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 404


@web.route("/ajax/reading-tts-book/retry", methods=["POST"])
@user_login_required
@admin_required
def reading_tts_book_retry():
    payload = request.get_json(silent=True) or {}
    try:
        proxy = _whole_book_tts_closures()
        return jsonify(whole_book_tts_service.retry(str(payload.get("job_id")), proxy))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/reading-tts-book/cancel", methods=["POST"])
@user_login_required
@admin_required
def reading_tts_book_cancel():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(whole_book_tts_service.cancel(str(payload.get("job_id"))))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/reading-annotation-create", methods=["POST"])
@user_login_required
def reading_annotation_create():
    """Proxy paragraph annotation creation to moon-well.

    批注与段落缓存（翻译/音频）落在 moon-well 同一 ES 文档；paragraph
    必须与翻译/朗读链路相同的归一化文本（trim + 压缩空白，≤2000），
    才能命中同一段落文档。署名与时间由 moon-well 凭 OIDC 身份头取，客户端不可传。
    """
    payload = request.get_json(silent=True) or {}
    paragraph_value = payload.get("paragraph")
    content_value = payload.get("content")
    # JSON null 不能被 str() 静默转换成 "None"，否则会写入错误的段落文档。
    if not isinstance(paragraph_value, str) or not isinstance(content_value, str):
        return jsonify({"success": False,
                        "message": "paragraph and content must be strings"}), 400
    paragraph = paragraph_value.strip()
    content = content_value.strip()
    if not paragraph or len(paragraph) > 2000 or not content or len(content) > 2000:
        return jsonify({"success": False,
                        "message": "paragraph and content must be between 1 and 2000 characters"}), 400
    payload["paragraph"] = paragraph
    payload["content"] = content
    payload["bookName"] = str(payload.get("bookName") or "").strip()[:200]
    payload["chapter"] = str(payload.get("chapter") or "").strip()[:200]
    # 15s：与阅读生词/翻译同量级的 JSON 接口
    return _moonwell_proxy("/reading/annotation/create", payload, 15,
                           "reading annotation")


@web.route("/ajax/reading-annotation-list-by-paragraph", methods=["POST"])
@user_login_required
def reading_annotation_list_by_paragraph():
    """Proxy per-paragraph annotation listing to moon-well."""
    payload = request.get_json(silent=True) or {}
    paragraph_value = payload.get("paragraph")
    if not isinstance(paragraph_value, str):
        return jsonify({"success": False, "message": "paragraph must be a string"}), 400
    paragraph = paragraph_value.strip()
    if not paragraph or len(paragraph) > 2000:
        return jsonify({"success": False,
                        "message": "paragraph must be between 1 and 2000 characters"}), 400
    payload["paragraph"] = paragraph
    return _moonwell_proxy("/reading/annotation/list-by-paragraph", payload, 15,
                           "reading annotation")


@web.route("/ajax/reading-annotation-list-by-book", methods=["POST"])
@user_login_required
def reading_annotation_list_by_book():
    """Proxy book-level annotation listing to moon-well (ES search, slower)."""
    payload = request.get_json(silent=True) or {}
    book_name = str(payload.get("bookName") or "").strip()
    if not book_name or len(book_name) > 200:
        return jsonify({"success": False,
                        "message": "bookName must be between 1 and 200 characters"}), 400
    payload["bookName"] = book_name
    payload["chapter"] = str(payload.get("chapter") or "").strip()[:200]
    # 20s：moon-well 侧为 ES exists+term 检索，容忍冷启动慢响应
    return _moonwell_proxy("/reading/annotation/list-by-book", payload, 20,
                           "reading annotation")


@web.route("/ajax/reading-companion-roles", methods=["POST"])
@user_login_required
def reading_companion_roles():
    """Proxy the fixed reading-companion role list to moon-well.

    角色清单固定在 moon-well 代码（本期不可添加）；前端页面级缓存一次即可。
    """
    return _moonwell_proxy("/reading/companion/roles", {}, 10, "reading companion")


@web.route("/ajax/reading-companion-annotate", methods=["POST"])
@user_login_required
def reading_companion_annotate():
    """Proxy AI companion annotation (role-based paragraph annotation) to moon-well.

    AI 批注缓存在 moon-well 段落文档 aiAnnotations 字段（key=roleId），paragraph
    必须与翻译/批注链路相同的归一化文本（trim，≤2000）才能命中同一段落文档；
    force=true 跳过缓存强制重新生成并覆盖。roleId 仅接受 LLM_ANNOTATION 类角色
    （moon-well 侧校验），翻译/朗读仍走各自既有通道。
    """
    payload = request.get_json(silent=True) or {}
    paragraph_value = payload.get("paragraph")
    role_value = payload.get("roleId")
    # JSON null 不能被 str() 静默转换成 "None"（与批注路由同因）
    if not isinstance(paragraph_value, str) or not isinstance(role_value, str):
        return jsonify({"success": False,
                        "message": "paragraph and roleId must be strings"}), 400
    paragraph = paragraph_value.strip()
    role_id = role_value.strip()
    if not paragraph or len(paragraph) > 2000 or not role_id or len(role_id) > 50:
        return jsonify({"success": False,
                        "message": "paragraph must be 1-2000 chars and roleId required"}), 400
    payload["paragraph"] = paragraph
    payload["roleId"] = role_id
    payload["bookName"] = str(payload.get("bookName") or "").strip()[:200]
    payload["chapter"] = str(payload.get("chapter") or "").strip()[:200]
    payload["force"] = bool(payload.get("force"))
    # 60s：单段一次同步 LLM 调用（参考段落朗读 65s 的先例）
    return _moonwell_proxy("/reading/companion/annotate", payload, 60,
                           "reading companion")


@web.route("/ajax/reading-companion-list-by-paragraph", methods=["POST"])
@user_login_required
def reading_companion_list_by_paragraph():
    """Proxy per-paragraph AI companion annotation listing to moon-well."""
    payload = request.get_json(silent=True) or {}
    paragraph_value = payload.get("paragraph")
    if not isinstance(paragraph_value, str):
        return jsonify({"success": False, "message": "paragraph must be a string"}), 400
    paragraph = paragraph_value.strip()
    if not paragraph or len(paragraph) > 2000:
        return jsonify({"success": False,
                        "message": "paragraph must be between 1 and 2000 characters"}), 400
    payload["paragraph"] = paragraph
    return _moonwell_proxy("/reading/companion/list-by-paragraph", payload, 15,
                           "reading companion")


@web.route("/ajax/reading-word-mark", methods=["POST"])
@user_login_required
def reading_word_mark():
    """Mark a selected word as unknown (+) or known (-) via moon-well.

    划词气泡的 ＋/－ 按钮调用。词形先归一化为小写 + 直撇号（与
    markVocabulary 及 moon-well ES 索引的词 key 一致），再转发到
    moon-well 的 GET /vocabulary/unknown|known/{word}。
    """
    payload = request.get_json(silent=True) or {}
    # word 必须是字符串（null 会被 str() 转成 "None" 通过校验，存成脏词）
    word = payload.get("word")
    if not isinstance(word, str):
        return jsonify({"success": False, "message": "invalid word"}), 400
    # unknown 必须是 JSON boolean（"false" 字符串经 bool() 恒为真，易误标）
    unknown = payload.get("unknown")
    if not isinstance(unknown, bool):
        return jsonify({"success": False, "message": "invalid unknown flag"}), 400
    # 弯撇号归一化为直撇号、小写：与前端 vocabularyRecords 的 key 保持一致
    word = word.strip().replace("\u2019", "'").lower()
    if not _READING_WORD_RE.match(word) or len(word) > 64:
        return jsonify({"success": False, "message": "invalid word"}), 400
    path = ("/vocabulary/unknown/" if unknown else "/vocabulary/known/") + quote(word, safe="")
    # 标记是即时小操作，8s 足够
    return _moonwell_proxy(path, None, 8, "reading word mark", method="GET")


@web.route("/ajax/reading-word-detail", methods=["POST"])
@user_login_required
def reading_word_detail():
    """单词详解（R123，与 magiclens v0.4.0 同源）：六板块结构化内容。

    划词气泡的「详」按钮调用；口径与 word_mark 一致（POST+JSON+CSRF，
    词形归一化后转发 moon-well 的 GET /vocabulary/detail/{word}）。
    变体词（ran/running）由 moon-well 的 LLM 还原词目并针对词目讲解，
    缓存按词目落档（magicbook-vocabulary 索引），重复查询不再计费。
    """
    payload = request.get_json(silent=True) or {}
    # word 必须是字符串（null 会被 str() 转成 "None" 拼进上游 path）
    word = payload.get("word")
    if not isinstance(word, str):
        return jsonify({"success": False, "message": "invalid word"}), 400
    # 弯撇号归一化为直撇号、小写：与 word_mark 及 moon-well 缓存词目口径一致
    word = word.strip().replace("\u2019", "'").lower()
    if not _READING_WORD_RE.match(word) or len(word) > 64:
        return jsonify({"success": False, "message": "invalid word"}), 400
    # 缓存 miss 时 moon-well 现场生成（一次 LLM 调用），30s 覆盖慢响应
    return _moonwell_proxy("/vocabulary/detail/" + quote(word, safe=""), None, 30,
                           "reading word detail", method="GET")

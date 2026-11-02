"""halo-book-connector：Halo 发布事件 → Markdown → EPUB → magicbook 内部导入。

单进程同步处理（V1 无并发诉求），per-slug 锁防同一书重入。
鉴权：入站 X-Hook-Token 共享密钥（CONNECTOR_HOOK_TOKEN 未配置则一律 401，
fail-closed）；出站 X-Connector-Key 调 magicbook /api/internal/book-import。
"""
import glob
import hashlib
import hmac
import json
import logging
import os
import threading
import time

from flask import Flask, jsonify, request

from builder import EpubBuilder
from halo_client import HaloClient, HaloError
from magicbook_client import MagicbookClient, MagicbookError
from mapping import Mapping
from notify import notify

log = logging.getLogger("connector")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")

DATA_DIR = os.environ.get("CONNECTOR_DATA_DIR",
                          os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
STATE_PATH = os.path.join(DATA_DIR, "state.json")
OUT_DIR = os.path.join(DATA_DIR, "out")
MAPPING_FILE = os.environ.get(
    "CONNECTOR_MAPPING",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "mapping.yaml"))

HALO_BASE = os.environ.get("HALO_BASE_URL", "https://note.haoshenqi.top")
MAGICBOOK_BASE = os.environ.get("MAGICBOOK_BASE_URL", "http://192.168.31.9:8083")
BOOK_IMPORT_KEY = os.environ.get("BOOK_IMPORT_KEY", "")
HOOK_TOKEN = os.environ.get("CONNECTOR_HOOK_TOKEN", "")
BARK_KEY = os.environ.get("BARK_KEY", "")

DEFAULT_EVENTS = "NEW_POST,UPDATE_POST"

app = Flask(__name__)
mapping = Mapping(MAPPING_FILE)
_state_lock = threading.Lock()
_slug_locks = {}
_slug_locks_guard = threading.Lock()


def _slug_lock(slug):
    with _slug_locks_guard:
        return _slug_locks.setdefault(slug, threading.Lock())


def _load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def _save_state(state):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


# R195：state.json 是整份读-改-写，而线上是 gunicorn --threads 4。
# 只有 per-slug 锁时，两本书并发会各读一份旧 state、后写者覆盖前者 ——
# 丢掉的 last_sha 会让下次发布被当成新版本重导，并因 EPUB mtime 变化
# 触发整本重译（白烧积分）。故所有读改写一律走 _state_lock 临界区。
def _state_entry(slug):
    with _state_lock:
        return _load_state().get(slug) or {}


def _state_update(slug, remove=(), **fields):
    with _state_lock:
        state = _load_state()
        entry = state.get(slug) or {}
        entry.update(fields)
        for key in remove:
            entry.pop(key, None)
        state[slug] = entry
        _save_state(state)
        return entry


def _allowed_events():
    """R196：Halo 事件白名单。

    Why: 原实现硬编码只认 NEW_POST，文章修订后重新发布（Halo 对已发布文章的
    更新通常发 UPDATE_POST 类事件）会被直接 ignored —— 而本链路的事实源语义
    是「Halo 最新发布版为准，事件只作触发器」，修订版同样要进书。
    How: 环境变量 CONNECTOR_EVENTS 可覆盖；默认 NEW_POST,UPDATE_POST。
    刻意不放宽到 DELETE 类事件：删除语义没有对应动作（不删书）。
    """
    raw = os.environ.get("CONNECTOR_EVENTS", DEFAULT_EVENTS)
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


def _prune_out(book_dir, keep=20):
    files = sorted(glob.glob(os.path.join(book_dir, "*.epub")),
                   key=os.path.getmtime)
    for path in files[:-keep] if keep else files:
        try:
            os.remove(path)
        except OSError:
            pass


def _process_slug(slug, cfg):
    halo = HaloClient(HALO_BASE)
    post = halo.find_post(slug)
    md = halo.get_markdown(post["name"])
    sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    entry = _state_entry(slug)
    if entry.get("last_sha") == sha:
        log.info("slug=%s unchanged sha=%s, no-op", slug, sha[:8])
        return {"result": "no-op", "sha": sha[:8]}

    today = time.strftime("%Y-%m-%d")
    meta = {
        "title": cfg["title"] or post["title"],
        "creator": cfg["creator"],
        "lang": cfg["lang"],
        "identifier": cfg["identifier"],
        "date": today,
        "modified": today + "T00:00:00Z",
        "slug": slug,
    }
    book_dir = os.path.join(OUT_DIR, str(cfg["book_id"]))
    out_path = os.path.join(book_dir, sha[:8] + ".epub")
    source_ref = f"halo:{slug}@sha256:{sha}"
    EpubBuilder(meta).build(md, out_path, halo, source_ref=source_ref)
    _prune_out(book_dir)

    cover_bytes = None
    if cfg.get("cover_slug") and post.get("cover"):
        try:
            cover_bytes = halo.download(post["cover"])
        except HaloError as exc:
            log.warning("cover download failed slug=%s: %s", slug, exc)

    mb = MagicbookClient(MAGICBOOK_BASE, BOOK_IMPORT_KEY)
    try:
        result = mb.import_book(cfg["book_id"], out_path,
                                 cover_bytes=cover_bytes,
                                 trigger_translation=cfg["trigger_translation"],
                                 source_ref=source_ref)
    except MagicbookError as exc:
        if exc.status == 502:
            # 文件已生效，仅翻译触发失败：记录版本并降级告警，不重试
            _state_update(slug,
                          last_sha=sha, last_book_id=cfg["book_id"],
                          last_job_id=None,
                          last_time=time.strftime("%Y-%m-%dT%H:%M:%S"),
                          translation_error=str(exc)[:200])
            notify(f"book{cfg['book_id']} 已更新，翻译触发失败",
                   str(exc)[:200], BARK_KEY)
            return {"result": "imported-translation-failed", "detail": str(exc)[:200]}
        notify(f"book{cfg['book_id']} 导入失败", str(exc)[:200], BARK_KEY)
        raise

    job_id = result.get("translationJobId")
    _state_update(slug, remove=("translation_error",),
                  last_sha=sha, last_book_id=cfg["book_id"],
                  last_job_id=job_id,
                  last_time=time.strftime("%Y-%m-%dT%H:%M:%S"))
    notify(f"📖 book{cfg['book_id']} 已更新",
           "翻译中" if job_id else "内容无新段落" , BARK_KEY)
    return {"result": "imported", "jobId": job_id, "sha": sha[:8]}


@app.post("/hooks/halo")
def hook():
    candidate = request.headers.get("X-Hook-Token", "")
    if not HOOK_TOKEN or not hmac.compare_digest(candidate, HOOK_TOKEN):
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    event = payload.get("eventType")
    if (event or "").upper() not in _allowed_events():
        return jsonify({"result": "ignored", "eventType": event}), 200
    slug = (payload.get("data") or {}).get("slug")
    if not slug:
        return jsonify({"error": "missing slug"}), 400
    cfg = mapping.get(slug)
    if not cfg:
        return jsonify({"result": "no-mapping", "slug": slug}), 200
    with _slug_lock(slug):
        try:
            result = _process_slug(slug, cfg)
        except (HaloError, MagicbookError, OSError) as exc:
            log.exception("process failed slug=%s", slug)
            return jsonify({"error": str(exc)[:500]}), 502
        except Exception as exc:
            log.exception("build failed slug=%s", slug)
            notify(f"book{cfg['book_id']} 构建失败", str(exc)[:200], BARK_KEY)
            return jsonify({"error": str(exc)[:500]}), 500
        return jsonify(result), 200


@app.post("/resync")
def resync():
    """手动补账：把映射表里的书按 Halo 当前发布版重新对账一次。

    Why（R197）：webhook 是「事件驱动、无补投」的——连接器停机或网络抖动期间
    丢掉的发布事件，此前只能去 Halo 手动重发布一次；书的过期是静默的。
    How：沿用 X-Hook-Token 鉴权；body 可带 {"slugs": [...]}，缺省=映射表全量；
    逐条复用 _process_slug（sha 未变自动 no-op，天然幂等）；单条失败只记入
    results 并继续，不中断整批。
    """
    candidate = request.headers.get("X-Hook-Token", "")
    if not HOOK_TOKEN or not hmac.compare_digest(candidate, HOOK_TOKEN):
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    requested = payload.get("slugs")
    slugs = [s for s in requested if isinstance(s, str)] if isinstance(requested, list) \
        else list(mapping.books)
    if not slugs:
        return jsonify({"error": "no slugs to resync"}), 400

    results, imported, failed = [], 0, 0
    for slug in slugs:
        cfg = mapping.get(slug)
        if not cfg:
            results.append({"slug": slug, "result": "no-mapping"})
            continue
        with _slug_lock(slug):
            try:
                item = _process_slug(slug, cfg)
            except Exception as exc:  # noqa: BLE001 单条失败不阻断整批
                log.exception("resync failed slug=%s", slug)
                failed += 1
                results.append({"slug": slug, "error": str(exc)[:300]})
                continue
        if str(item.get("result", "")).startswith("imported"):
            imported += 1
        results.append({"slug": slug, **item})
    log.info("resync done: total=%s imported=%s failed=%s",
             len(results), imported, failed)
    return jsonify({"total": len(results), "imported": imported,
                    "failed": failed, "results": results})


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True,
                    "mapping_hooks": HOOK_TOKEN != "",
                    "import_hooks": BOOK_IMPORT_KEY != ""})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("CONNECTOR_PORT", "9878")))

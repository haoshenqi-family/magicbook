"""整本朗读（TTS 预生成）批次服务（R166 设计 §3.1，镜像 WholeBookTranslationService 骨架）。

执行链路（拍板 D1 方案 A）：daemon 串行逐段 POST moon-well /tts/speak，payload 带
``source: "book-tts-batch"``（发起者计费通道：miss 按 floor(字符/1000) 扣、命中 0 扣），
音频落 moon-well 永久缓存；魔法全在缓存幂等——retry/重跑对已完成段免费快返。
批次表即断点台账（R142 done.jsonl 的产品化）。
"""

import hashlib
import os
import threading
import time

from .. import calibre_db, config, ub, logger
from ..cw_login import current_user
from ..reading_translation.timeutil import as_utc, now_utc
from ..reading_translation.models import TranslationJob  # noqa: F401  (表注册顺序依赖)
from .extractor import extract_epub_paragraphs
from .models import ACTIVE_STATUSES, ReadingTtsJob, ReadingTtsJobItem

log = logger.create()

# 与 moon-well /tts/speak 的 source 标记逐字对应（ReadingTtsService.SOURCE_BOOK_TTS_BATCH）
SOURCE_BOOK_TTS_BATCH = "book-tts-batch"
# 整本选角端点（moon-well R166 P1）
BOOK_VOICE_SELECT_PATH = "/tts/book-voice/select"
SPEAK_PATH = "/tts/speak"

# 僵尸批次判定：updated_at 停滞超过该分钟数即视为丢失执行线程（翻译同款 30min）
ZOMBIE_MINUTES = 30
# daemon 段间隔（秒）：≈75 RPM < MiMo 100 RPM，留余量给阅读器即时朗读；命中段也 sleep
#（daemon 不识别命中，简单且安全——R142 补跑参数）
SYNTH_INTERVAL_SECONDS = 0.8
# daemon HTTP 超时：服务端 local 环 180s（生产 Nacos 现值）+ 余量；R142 实测最长段 78.6s
SYNTH_TIMEOUT_SECONDS = 200
# 选角正文样本：前 N 段拼接，≤1500 字符（moon-well BookVoiceService SAMPLE_MAX_CHARS 同口径）
VOICE_SAMPLE_MAX_CHARS = 1500
VOICE_SAMPLE_PARAGRAPHS = 3


def text_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class WholeBookTtsService:
    """Create and reconcile durable whole-book TTS batches."""

    def __init__(self, moonwell_proxy):
        # Why 注入代理而非直接 import：daemon 线程需要「请求线程定格的令牌快照」
        # （R51/R145 教训：线程内读 flask_session 会 RuntimeError），闭包由路由层构造
        self._proxy = moonwell_proxy

    def _ensure_tables(self):
        bind = ub.session.get_bind()
        ub.Base.metadata.create_all(bind, tables=[ReadingTtsJob.__table__, ReadingTtsJobItem.__table__])

    def _book_file(self, book_id, book_format):
        book = calibre_db.get_filtered_book(book_id)
        if not book:
            raise ValueError("book is unavailable")
        normalized = (book_format or "").lower()
        if normalized not in ("epub", "kepub"):
            raise ValueError("only EPUB and KEPUB are supported")
        data = calibre_db.get_book_format(book_id, normalized.upper())
        if not data:
            raise ValueError("book format is unavailable")
        path = os.path.join(config.get_book_path(), book.path, data.name + "." + normalized)
        if not os.path.isfile(path):
            raise ValueError("book file is unavailable")
        return book, path

    @staticmethod
    def _fingerprint(path):
        stat = os.stat(path)
        return hashlib.sha256(f"{path}:{stat.st_size}:{stat.st_mtime_ns}".encode()).hexdigest()

    # ---------- 选角 ----------

    def _book_meta(self, book, paragraphs):
        """从 Calibre 元数据取选角输入（设计 §5：这些列只在 magicbook 的 metadata.db）。"""
        author = ""
        try:
            author = ", ".join(a.name for a in (book.authors or []))[:300]
        except Exception:
            log.warning("whole-book tts: read authors failed (book=%s)", book.id)
        summary = ""
        try:
            comments = book.comments or ""
            # 简介是 HTML，剥标签后归一（comments 里 HTML 是常态）
            import re
            text = re.sub(r"<[^>]+>", " ", comments)
            summary = re.sub(r"\s+", " ", text).strip()[:2000]
        except Exception:
            log.warning("whole-book tts: read comments failed (book=%s)", book.id)
        sample = " ".join(p[1] for p in paragraphs[:VOICE_SAMPLE_PARAGRAPHS])[:VOICE_SAMPLE_MAX_CHARS]
        return {
            "bookName": (book.title or "").strip()[:200],
            "author": author,
            "summary": summary,
            "language": (book.language or "").strip()[:20],
            "sampleText": sample,
        }

    def _select_voice(self, meta, force):
        """整本预选角；失败不阻断批次（选角是增强而非依赖），返回 (voice, style) 或 (None, None)。"""
        try:
            payload = dict(meta)
            payload["force"] = bool(force)
            body, status = self._proxy(BOOK_VOICE_SELECT_PATH, payload, 60, "whole-book tts voice select")
            if 200 <= status < 300:
                import json
                data = json.loads(body)
                voice = (data.get("voice") or "").strip() or None
                style = (data.get("style") or "").strip() or None
                return voice, style
            log.warning("whole-book tts: voice select non-2xx (%s) — fallback to provider default", status)
        except Exception as error:
            log.warning("whole-book tts: voice select failed (%s) — fallback to provider default", error)
        return None, None

    # ---------- 批次生命周期 ----------

    def start(self, book_id, book_format, proxy=None, force_voice=False, force_new_batch=False):
        """创建批次后立即返回，合成交给后台线程（翻译 HP2 实测教训：请求线程必被网关超时杀死）。"""
        self._ensure_tables()
        user_id = int(current_user.id)
        book, path = self._book_file(book_id, book_format)
        fingerprint = self._fingerprint(path)
        query = ub.session.query(ReadingTtsJob).filter(
            ReadingTtsJob.user_id == user_id,
            ReadingTtsJob.book_id == book_id,
            ReadingTtsJob.book_fingerprint == fingerprint,
            ReadingTtsJob.status.in_(ACTIVE_STATUSES))
        existing = query.order_by(ReadingTtsJob.created_at.desc()).first()
        if existing and now_utc() - as_utc(existing.updated_at) > __import__("datetime").timedelta(minutes=ZOMBIE_MINUTES):
            # 僵尸批次自愈（翻译同款）：任务记录清表/容器重启丢线程等历史事故会让旧批次
            # 永远停在 RUNNING 且无进展；判定 30 分钟无 updated_at 进展即关闭
            log.warning("whole-book tts: stale job %s (book=%s updated_at=%s) closed as zombie",
                        existing.id, book_id, existing.updated_at)
            existing.status = "PARTIAL_FAILED"
            existing.updated_at = now_utc()
            ub.session.commit()
            existing = None
        if existing and not force_new_batch:
            # 复用是静默成功：无此日志无从区分「没收到请求」与「命中幂等」
            log.info("whole-book tts: reuse active job %s (book=%s status=%s)",
                     existing.id, book_id, existing.status)
            return self.progress(existing)

        paragraphs = extract_epub_paragraphs(path)
        if not paragraphs:
            raise ValueError("no speakable paragraphs found")
        job = ReadingTtsJob(user_id=user_id, book_id=book_id, book_format=book_format.upper(),
                            book_name=book.title or "", book_fingerprint=fingerprint, status="RUNNING")
        ub.session.add(job)
        ub.session.flush()
        unique = {}
        for index, (chapter, text) in enumerate(paragraphs):
            digest = text_hash(text)
            if digest in unique:
                continue
            item = ReadingTtsJobItem(job_id=job.id, paragraph_index=index, chapter=chapter,
                                     text=text, text_hash=digest, status="PENDING")
            unique[digest] = item
            ub.session.add(item)
        job.total_count = len(unique)
        ub.session.commit()

        # 受理观测点（翻译同款）：HTTP 成功路径零日志时「点击没反应」无从排查
        log.info("whole-book tts: job %s accepted (book=%s user=%s paragraphs=%s force_voice=%s)",
                 job.id, book_id, user_id, job.total_count, force_voice)

        meta = self._book_meta(book, paragraphs)
        voice, style = self._select_voice(meta, force_voice)
        if voice:
            job.voice = voice
            job.style = style
            ub.session.commit()

        self._proxy = proxy or self._proxy
        self._spawn_synth_worker(job.id)
        return self.progress(job)

    def _spawn_synth_worker(self, job_id):
        worker = threading.Thread(
            target=self._synth_worker_guarded,
            args=(job_id,),
            name=f"whole-book-tts-{job_id[:8]}", daemon=True)
        worker.start()

    def _synth_worker_guarded(self, job_id):
        try:
            self._synth_worker(job_id)
        except Exception:
            log.exception("whole-book tts: synth worker crashed (job=%s)", job_id)

    def _synth_worker(self, job_id):
        # Why 自建查询而非闭包 session：scoped_session 绑定线程作用域，后台线程不能复用
        # 请求线程的 session；线程内自建会话操作（翻译同款）。鉴权由路由层注入的 proxy
        # 闭包封装（请求线程定格的令牌快照），service 不接触任何凭据概念。
        proxy = self._proxy
        while True:
            job = ub.session.query(ReadingTtsJob).get(job_id)
            if job is None or job.status == "CANCELLED":
                return
            item = (ub.session.query(ReadingTtsJobItem)
                    .filter(ReadingTtsJobItem.job_id == job_id,
                            ReadingTtsJobItem.status == "PENDING")
                    .order_by(ReadingTtsJobItem.paragraph_index)
                    .first())
            if item is None:
                self._refresh_counts(job)
                pending = (ub.session.query(ReadingTtsJobItem)
                           .filter(ReadingTtsJobItem.job_id == job_id,
                                   ReadingTtsJobItem.status == "PENDING").count())
                if pending == 0:
                    failed = (ub.session.query(ReadingTtsJobItem)
                              .filter(ReadingTtsJobItem.job_id == job_id,
                                      ReadingTtsJobItem.status == "FAILED").count())
                    job.status = "PARTIAL_FAILED" if failed else "COMPLETED"
                    ub.session.commit()
                    log.info("whole-book tts: job %s finished (done=%s failed=%s)",
                             job.id, job.done_count, job.failed_count)
                return
            ok = False
            error = None
            for attempt in (1, 2):
                try:
                    body, status = proxy(SPEAK_PATH,
                                         {"text": item.text, "bookName": job.book_name,
                                          "chapter": item.chapter, "source": SOURCE_BOOK_TTS_BATCH},
                                         SYNTH_TIMEOUT_SECONDS, "whole-book tts synth",
                                         binary=True)
                    if 200 <= status < 300:
                        ok = True
                        break
                    error = "moon-well /tts/speak HTTP %s" % status
                except Exception as exc:  # 网络抖动/moon-well 重启：重试一次后 FAILED
                    error = str(exc)
                time.sleep(1)
            item.attempt_count = attempt
            item.status = "DONE" if ok else "FAILED"
            item.error_message = None if ok else (error or "unknown")[:500]
            if not ok:
                job.failed_count = (ub.session.query(ReadingTtsJobItem)
                                    .filter(ReadingTtsJobItem.job_id == job_id,
                                            ReadingTtsJobItem.status == "FAILED").count())
            job.done_count = (ub.session.query(ReadingTtsJobItem)
                              .filter(ReadingTtsJobItem.job_id == job_id,
                                      ReadingTtsJobItem.status == "DONE").count())
            job.updated_at = now_utc()
            ub.session.commit()
            time.sleep(SYNTH_INTERVAL_SECONDS)

    def _refresh_counts(self, job):
        job.done_count = (ub.session.query(ReadingTtsJobItem)
                          .filter(ReadingTtsJobItem.job_id == job.id,
                                  ReadingTtsJobItem.status == "DONE").count())
        job.failed_count = (ub.session.query(ReadingTtsJobItem)
                            .filter(ReadingTtsJobItem.job_id == job.id,
                                    ReadingTtsJobItem.status == "FAILED").count())

    def progress(self, job):
        self._refresh_counts(job)
        ub.session.commit()
        done = job.done_count
        failed = job.failed_count
        return {
            "jobId": job.id,
            "bookId": job.book_id,
            "bookName": job.book_name,
            "status": job.status,
            "total": job.total_count,
            "done": done,
            "failed": failed,
            "voice": job.voice,
            "style": job.style,
        }

    def get_progress(self, job_id):
        self._ensure_tables()
        job = ub.session.query(ReadingTtsJob).get(job_id)
        if job is None:
            raise ValueError("job not found")
        return self.progress(job)

    def retry(self, job_id, proxy=None):
        self._ensure_tables()
        job = ub.session.query(ReadingTtsJob).get(job_id)
        if job is None:
            raise ValueError("job not found")
        failed = (ub.session.query(ReadingTtsJobItem)
                  .filter(ReadingTtsJobItem.job_id == job_id,
                          ReadingTtsJobItem.status == "FAILED").all())
        for item in failed:
            item.status = "PENDING"
            item.error_message = None
        if failed:
            job.status = "RUNNING"
            ub.session.commit()
            log.info("whole-book tts: retry job %s (%s items re-queued)", job_id, len(failed))
            if proxy:
                self._proxy = proxy
            self._spawn_synth_worker(job_id)
        return self.progress(job)

    def cancel(self, job_id):
        self._ensure_tables()
        job = ub.session.query(ReadingTtsJob).get(job_id)
        if job is None:
            raise ValueError("job not found")
        job.status = "CANCELLED"
        job.updated_at = now_utc()
        ub.session.commit()
        log.info("whole-book tts: job %s cancelled by user", job_id)
        return self.progress(job)

"""整本朗读（TTS 预生成）批次服务（R166 设计 §3.1，镜像 WholeBookTranslationService 骨架）。

执行链路（拍板 D1 方案 A）：daemon 串行逐段 POST moon-well /tts/speak，payload 带
``source: "book-tts-batch"``（发起者计费通道：miss 按 floor(字符/1000) 扣、命中 0 扣），
音频落 moon-well 永久缓存；魔法全在缓存幂等——retry/重跑对已完成段免费快返。
批次表即断点台账（R142 done.jsonl 的产品化）。
"""

import hashlib
import os
import re
import threading
import time
from datetime import timedelta

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
        # 本进程内的合成线程花名册（job_id）。Why 需要它：`_synth_worker` 取 PENDING 段是
        # 先查后写、没有 CAS，两条线程同跑会抢同一段 ⇒ 双合成、双扣字符；而「updated_at
        # 是否停滞」只能证明至少 30 分钟没进展，救不了「台账已建、线程从未起成」这种当下就
        # 坏的形态（R169 生产事故）。magicbook 单进程起服务（entrypoint.sh 末行
        # `exec python /app/cps.py`），进程内字典因此是权威判据；跨进程重启后花名册清空，
        # 「没有线程 + 还有 PENDING」正是该补线程的信号。判活与登记同锁原子化见
        # `_spawn_synth_worker`。
        self._live_workers = set()
        self._workers_lock = threading.Lock()

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
            # 真模型 `book.comments` 是 Comments 关系**列表**（cps/db.py:218，本仓惯用法
            # `book.comments[0].text`），不是字符串。旧代码把列表直接喂给 re.sub，TypeError
            # 被自家 except 吞掉 ⇒ 选角输入里的 summary 在生产恒空（R169 评审补上的同型洞）。
            comments = book.comments or []
            raw = comments[0].text if len(comments) else ""
            # 简介是 HTML，剥标签后归一（comments 里 HTML 是常态）
            text = re.sub(r"<[^>]+>", " ", raw or "")
            summary = re.sub(r"\s+", " ", text).strip()[:2000]
        except Exception:
            log.warning("whole-book tts: read comments failed (book=%s)", book.id)
        language = ""
        try:
            # Why 走 languages 关系而不是 book.language：本仓 Books 没有 language 标量列
            # （语言是多对多 cps/db.py:428 `languages = relationship(Languages, ...)`，
            # 列名是 `Languages.lang_code`，db.py:327），裸取 book.language 会 AttributeError
            # ——R169 生产事故正是这一行让整批朗读台账停在 RUNNING 0/307（异常发生在 job 已
            # commit、daemon 尚未 spawn 之间）。
            language = ", ".join((l.lang_code or "").strip() for l in (book.languages or [])
                                 if l.lang_code)[:20]
        except Exception:
            log.warning("whole-book tts: read languages failed (book=%s)", book.id)
        sample = " ".join(p[1] for p in paragraphs[:VOICE_SAMPLE_PARAGRAPHS])[:VOICE_SAMPLE_MAX_CHARS]
        return {
            "bookName": (book.title or "").strip()[:200],
            "author": author,
            "summary": summary,
            "language": language,
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
        if existing and not force_new_batch:
            if self._needs_worker(existing):
                # 自愈主路：台账在、本进程却没有活线程（从未起成 / 容器重启 / 线程崩），
                # 且还有 PENDING 段 ⇒ 原地补线程续跑。不另起新台账——批次表就是断点台账
                # （设计 §3.1），换台账会让已合成的段白走一遍 HTTP 且进度条回 0。
                log.warning("whole-book tts: job %s (book=%s status=%s updated_at=%s) has no live "
                            "worker — resuming with %s pending items",
                            existing.id, book_id, existing.status, existing.updated_at,
                            self._pending_count(existing.id))
                self._revive_running(existing)
                self._proxy = proxy or self._proxy
                self._spawn_synth_worker(existing.id)
                return self.progress(existing)
            if self._is_stalled(existing) and self._pending_count(existing.id) == 0:
                # 停滞且无待跑段＝线程在「完成最后一段」与「收尾定终态」之间没了
                # （容器重启的典型落点）：按僵尸关闭，落回下面新建批次
                log.warning("whole-book tts: stale job %s (book=%s updated_at=%s) closed as zombie "
                            "(no pending left)", existing.id, book_id, existing.updated_at)
                existing.status = "PARTIAL_FAILED"
                existing.updated_at = now_utc()
                ub.session.commit()
                existing = None
            else:
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

        # Why 先把本次请求的代理定下来再做选角：_select_voice 走的是 self._proxy，而本类是
        # 模块级单例——原顺序下容器启动后的第一次点按钮，self._proxy 仍是构造期传入的 None，
        # 选角必然抛「'NoneType' object is not callable」并被吞成默认音色（单测从构造函数注入
        # proxy，所以看不见这个洞）。
        self._proxy = proxy or self._proxy

        # Why 元数据与选角整段包异常：这两步是「音色增强」而非执行依赖，绝不能决定批次能否
        # 起跑。R169 生产事故形态＝job 与全部 item 已 commit、_book_meta 抛 AttributeError
        # ⇒ daemon 从未 spawn ⇒ 台账永久停在 RUNNING 0/N。
        try:
            meta = self._book_meta(book, paragraphs)
            voice, style = self._select_voice(meta, force_voice)
        except Exception:
            log.exception("whole-book tts: preselect crashed (job=%s) — "
                          "continuing with provider default voice", job.id)
            voice = style = None
        if voice:
            job.voice = voice
            job.style = style
            ub.session.commit()

        self._spawn_synth_worker(job.id)
        return self.progress(job)

    def _spawn_synth_worker(self, job_id):
        """为该批次起一条合成线程；已有活线程时静默跳过（返回 False）。

        Why 判活与登记必须在同一把锁里：Tornado 把视图跑在真线程池里
        （`cps/server.py:251` 的 `HTTPServer(MyWSGIContainer(...))`），两个「点整本朗读 /
        点重试」的请求可能同时判定「没有活线程」，各自起一条 ⇒ 抢同一段、双合成双扣字符。
        先查后登记的那个 TOCTOU 窗口只能靠把两步合成一个原子操作闭掉，调用方的预检
        （`_needs_worker`）只用来决定要不要记日志。
        """
        with self._workers_lock:
            if job_id in self._live_workers:
                return False
            # Why 先登记再 start：线程可能在 start() 返回的瞬间就跑完，后加会漏判活
            self._live_workers.add(job_id)
        worker = threading.Thread(
            target=self._synth_worker_guarded,
            args=(job_id,),
            name=f"whole-book-tts-{job_id[:8]}", daemon=True)
        try:
            worker.start()
        except Exception:
            # 起线程失败（资源耗尽等）必须当场注销，否则该批次被花名册永久判定「有人在跑」
            with self._workers_lock:
                self._live_workers.discard(job_id)
            raise
        return True

    def _synth_worker_guarded(self, job_id):
        try:
            self._synth_worker(job_id)
        except Exception:
            log.exception("whole-book tts: synth worker crashed (job=%s)", job_id)
        finally:
            with self._workers_lock:
                self._live_workers.discard(job_id)

    def _needs_worker(self, job):
        """该批次现在该不该补一条合成线程：本进程无活线程 且 仍有 PENDING 段。"""
        if job is None or job.status == "CANCELLED":
            return False
        with self._workers_lock:
            live = job.id in self._live_workers
        return not live and self._pending_count(job.id) > 0

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

    @staticmethod
    def _is_stalled(job):
        """停滞判定：``updated_at`` 超过 ZOMBIE_MINUTES 无进展。

        Why 它不再是「补线程」的判据（那是 `_needs_worker` 的花名册）：停滞只能证明「至少
        30 分钟没进展」，证明不了当下有没有线程。现在只留一个用途——判死「停滞且已无 PENDING」
        的旧批次（线程崩在完成最后一段与收尾定终态之间），让它落回新建流程。
        """
        return now_utc() - as_utc(job.updated_at) > timedelta(minutes=ZOMBIE_MINUTES)

    @staticmethod
    def _pending_count(job_id):
        return (ub.session.query(ReadingTtsJobItem)
                .filter(ReadingTtsJobItem.job_id == job_id,
                        ReadingTtsJobItem.status == "PENDING").count())

    def _revive_running(self, job):
        """把停滞批次拨回 RUNNING 并推进时钟——顺带挡住 30 分钟窗口内的重复补线程。"""
        job.status = "RUNNING"
        job.updated_at = now_utc()
        ub.session.commit()

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
        if job.status == "CANCELLED":
            # Why 直接拒绝而不是回收 FAILED：cancel 是用户的显式停止意图，旧实现里
            # 「有 FAILED 就把 status 拨回 RUNNING」会让一个已取消的批次被重试悄悄复活
            # （纯 PENDING 的却不复活——两条路口径相反）。要重新开跑请点「整本朗读」
            # （start 的幂等/续跑分支），不是 retry。
            log.info("whole-book tts: retry ignored, job %s is cancelled", job_id)
            return self.progress(job)
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
        # Why 补线程的判据不看 FAILED 而是「本进程无活线程 + 仍有 PENDING」：R169 的现场批次
        # 307 段全是 PENDING、0 FAILED（daemon 从未起成），旧条件（只在回收了 FAILED 时才
        # spawn）下一条线程都不会补，点重试等于空转。判活也不能省——活线程还在跑时再起一条
        # 会抢同一段（先查后写无 CAS ⇒ 双合成、双扣字符）。
        if self._needs_worker(job):
            log.warning("whole-book tts: retry job %s has no live worker — spawning for %s pending items",
                        job_id, self._pending_count(job_id))
            self._revive_running(job)
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

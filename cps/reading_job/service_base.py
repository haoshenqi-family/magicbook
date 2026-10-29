"""整本批次服务的公共骨架（架构评审 B6：三条链路的台账原语归一）。

三条链路（整本翻译 R75/R78、整本朗读 R166/R169、全文单词详解 R176）都是同一形制的
「job/item 台账 + 请求线程定格身份 + 后台线程执行 + 页面轮询进度」。抽之前逐字比对过：
`_book_file`/`_fingerprint` 三份完全相同，`_ensure_tables` 只差两张表名，
「按 (用户, 书, 正文指纹) 取最新未终态批次」的复用查询、30 分钟僵尸判定与关闭各三份，
`ACTIVE_STATUSES` 两份相同（整本朗读按设计只认 RUNNING/PARTIAL_FAILED）。
同构双改的风险不是推测——R169 的整本朗读批次事故就是「双胞胎侧改一处漏一处」的形态。

边界（与 L3 `docs/project/_legacy/feat/arch-review-2026-10/design/refactor-items.md` B6 同源）：
- **只搬证明相同的**：进度字典口径、item 状态机、worker 循环内容三家各异，留在各自 service。
- **花名册自愈（R169 的「无活线程 + 还有待跑项 ⇒ 补线程」）在此实现一份**，
  由整本朗读使用；整本翻译/详解的发布线程靠「幂等复用通道 + 新鲜度拦截」防重复，
  套上花名册会改变「连点两次」的现有语义，属行为变更，不在去重重构里顺手做。
"""

import hashlib
import os
import threading
from datetime import timedelta

from .. import calibre_db, config, logger, ub
from ..cw_login import current_user
from ..reading_translation.timeutil import as_utc, now_utc

log = logger.create()

# 台账的「未终态」集合：整本翻译与全文详解共用（PENDING 是历史遗留的建号前状态，
# 保留以兼容存量行）。整本朗读刻意不含 PENDING——它的批次一建就是 RUNNING。
ACTIVE_STATUSES = ("PENDING", "RUNNING", "PARTIAL_FAILED")

# 僵尸批次判定阈值：三条链路原本各自硬编码 30 分钟（两处常量 + 四处内联表达式），
# 归一为单一事实源。停滞只能证明「至少这么久没进展」，证明不了当下有没有线程。
ZOMBIE_MINUTES = 30


class JobServiceBase:
    """Durable whole-book job ledgers — primitives shared by the three batch services.

    子类必须填 `job_model` / `item_model`；`active_statuses`、`missing_job_error`、
    `worker_name_prefix`、`log_prefix` 按各自链路现值覆写，**日志与报错文案保持原样**，
    ES 里的关键字与前端 toast 不因重构而漂移。
    """

    job_model = None
    item_model = None
    # 子类可声明随台账一起懒建的附加表。R238 的预览快照即一本书一条，
    # 与 job/item 同生命周期入口创建；建表原语仍只保留在这一处。
    extra_tables = ()
    active_statuses = ACTIVE_STATUSES
    # 查无批次时的报错文案（三家不同且已上线，逐字保留）
    missing_job_error = "job is unavailable"
    # 「用户显式取消」的状态值：朗读写 CANCELLED，整本翻译与详解写 CANCELED——
    # 这个拼写分叉是历史造成的，现只有朗读侧启用花名册自愈；另两家若要启用必须覆写本值
    cancelled_status = "CANCELLED"
    # 骨架内部日志的前缀与线程名：整本朗读用 "whole-book tts:" / "whole-book-tts"
    log_prefix = "reading job:"
    worker_name_prefix = "reading-job"
    # 骨架日志归到调用方自己的 logger 名下（评审 M6 的教训：logger 名塌到基类会让
    # 按 logger 过滤的检索习惯失效），子类把自己模块的 log 赋进来
    job_log = log

    def __init__(self):
        # 本进程内的后台线程花名册（job_id）。Why 需要它：worker 取「待跑项」是先查后写、
        # 没有 CAS，两条线程同跑同一个批次会抢同一段 ⇒ 双执行、双扣费；而「updated_at
        # 是否停滞」只能证明至少 30 分钟没进展，救不了「台账已建、线程从未起成」这种当下
        # 就坏的形态（R169 生产事故：307 段全 PENDING、批次永久停在 RUNNING 0/307）。
        # magicbook 单进程起服务（entrypoint.sh 末行 `exec python /app/cps.py`），进程内
        # 字典因此是权威判据；跨进程重启后花名册清空，「没有线程 + 还有待跑项」正是该补
        # 线程的信号。判活与登记同锁原子化见 `_spawn_worker`。
        self._live_workers = set()
        self._workers_lock = threading.Lock()

    # ---------- 台账表与正文定位 ----------

    def _ensure_tables(self):
        bind = ub.session.get_bind()
        tables = [self.job_model.__table__, self.item_model.__table__]
        tables.extend(model.__table__ for model in self.extra_tables)
        ub.Base.metadata.create_all(bind, tables=tables)

    def _book_file(self, book_id, book_format, allow_show_archived=False):
        # 整本任务默认沿用归档过滤；内容速览与详情页共用“归档书仍可查看”的可见性，
        # 因此由调用方显式放宽。不要把默认值改宽，否则会改变三条整本任务的取书语义。
        if allow_show_archived:
            book = calibre_db.get_filtered_book(book_id, allow_show_archived=True)
        else:
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

    # ---------- 幂等复用与僵尸判定 ----------

    def _find_active_job(self, user_id, book_id, fingerprint):
        """按 (用户, 书, 正文指纹) 取最新的未终态批次——三家共用的幂等复用通道。"""
        return (ub.session.query(self.job_model)
                .filter(self.job_model.user_id == user_id,
                        self.job_model.book_id == int(book_id),
                        self.job_model.book_fingerprint == fingerprint,
                        self.job_model.status.in_(self.active_statuses))
                .order_by(self.job_model.created_at.desc()).first())

    @staticmethod
    def _is_stale(job, minutes=ZOMBIE_MINUTES):
        """停滞判定：`updated_at` 超过 `minutes` 无进展。

        Why 它不是「补线程」的判据（那是 `_needs_worker` 的花名册）：停滞只能证明「至少
        这么久没进展」，证明不了当下有没有线程。它只留一个用途——判死「停滞且已无待跑项」
        的旧批次（线程崩在完成最后一项与收尾定终态之间），让它落回新建流程。

        DB 读回的值可能是 naive（DATETIME 列丢弃 tzinfo），必须先经 `as_utc` 归一，
        否则抛 offset-naive/offset-aware TypeError（R75 的实踩形态）。
        """
        return now_utc() - as_utc(job.updated_at) > timedelta(minutes=minutes)

    @staticmethod
    def _is_fresh(job, minutes=ZOMBIE_MINUTES):
        """「还活着」判据：``updated_at`` 严格晚于 ``now - minutes``。

        Why 与 `_is_stale` 并存而不是写成取反：原实现的两处比较就不是互补的——僵尸判定用
        ``now - updated_at > 30min``，一键译全库的「在跑就跳过」用 ``updated_at > now - 30min``
        （严格大于）。恰好停在 30 分整那条记录，旧行为是「判僵尸、开新批次」，取反后会变成
        「算在跑」。边界值不可测（时钟精度），但重构不许顺手改判据，两个谓词原样保留。
        """
        return as_utc(job.updated_at) > now_utc() - timedelta(minutes=minutes)

    def _close_as_zombie(self, job, book_id):
        """把停滞且无待跑项的旧批次按僵尸关闭，让本次点击落回新建流程。"""
        self.job_log.warning("%s stale job %s (book=%s updated_at=%s) closed as zombie",
                             self.log_prefix, job.id, book_id, job.updated_at)
        job.status = "PARTIAL_FAILED"
        job.updated_at = now_utc()
        ub.session.commit()

    def _own_job(self, job_id):
        """按 id 取当前用户的批次；查不到即抛各自链路的既有文案（路由按 ValueError 映射状态码）。"""
        job = (ub.session.query(self.job_model)
               .filter_by(id=str(job_id), user_id=int(current_user.id)).one_or_none())
        if not job:
            raise ValueError(self.missing_job_error)
        return job

    # ---------- 后台线程骨架（R169 自愈机制的单一实现） ----------

    def _pending_count(self, job_id):
        """台账里「还没开始跑」的项数（item.status == 'PENDING'）。

        Why 只认 PENDING 而不写成「未完成」：三条链路的 item 状态机不同——整本翻译与详解
        的「未完成」口径是 ``~in_(COMPLETED, FAILED, SKIPPED)``，其中 PUBLISHED 段
        **已经发出去了**，把它算进「该补线程的理由」会让自愈对着一条正在被 moon-well 消费的
        批次再起一线。补线程判据要的是「一段活儿没人认领」。
        """
        return (ub.session.query(self.item_model)
                .filter(self.item_model.job_id == job_id,
                        self.item_model.status == "PENDING").count())

    def _needs_worker(self, job):
        """该批次现在该不该补一条后台线程：未被用户显式取消 且 本进程无活线程 且 仍有待跑项。

        Why 只排除「已取消」而**不收紧成「必须在 active_statuses 里」**（评审后修正）：调用方
        `retry` 是按 id 直取批次的，终态行也会走到这里；旧实现（R169 落地版）对「已 COMPLETED
        却还留着 PENDING 段」的矛盾台账是**照补线程**的——那是当时唯一能把这种台账拉回正轨的路。
        用状态集合当闸门会把这条静默成 no-op。「已取消不复活」的判据归 `retry` 自己管
        （朗读侧 `retry` 对 CANCELLED 早退并写日志）。
        """
        if job is None or job.status == self.cancelled_status:
            return False
        with self._workers_lock:
            live = job.id in self._live_workers
        return not live and self._pending_count(job.id) > 0

    def _revive_running(self, job):
        """把停滞批次拨回 RUNNING 并推进时钟——顺带挡住 30 分钟窗口内的重复补线程。"""
        job.status = "RUNNING"
        job.updated_at = now_utc()
        ub.session.commit()

    def _spawn_worker(self, job_id, run):
        """为该批次起一条后台线程；花名册已有活线程时静默跳过（返回 False）。

        Why 判活与登记必须在同一把锁里：Tornado 把视图跑在真线程池里
        （`cps/server.py:251` 的 `HTTPServer(MyWSGIContainer(...))`），两个「点整本 / 点重试」
        的请求可能同时判定「没有活线程」，各自起一条 ⇒ 抢同一段、双执行双扣费。
        先查后登记的那个 TOCTOU 窗口只能靠把两步合成一个原子操作闭掉，调用方的预检
        （`_needs_worker`）只用来决定要不要记日志。
        """
        with self._workers_lock:
            if job_id in self._live_workers:
                return False
            # Why 先登记再 start：线程可能在 start() 返回的瞬间就跑完，后加会漏判活
            self._live_workers.add(job_id)
        worker = threading.Thread(
            target=self._worker_guarded,
            args=(job_id, run),
            name="%s-%s" % (self.worker_name_prefix, str(job_id)[:8]), daemon=True)
        try:
            worker.start()
        except Exception:
            # 起线程失败（资源耗尽等）必须当场注销，否则该批次被花名册永久判定「有人在跑」
            with self._workers_lock:
                self._live_workers.discard(job_id)
            raise
        return True

    def _worker_guarded(self, job_id, run):
        """线程体的异常兜底与花名册注销（`finally` 保证崩溃也要从花名册摘掉）。"""
        try:
            run(job_id)
        except Exception:
            self.job_log.exception("%s worker crashed (job=%s)", self.log_prefix, job_id)
        finally:
            with self._workers_lock:
                self._live_workers.discard(job_id)

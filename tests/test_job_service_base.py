"""整本批次骨架的结构守卫（架构评审 B6）。

守卫的是「别再长回三份」：三个 service 若重新定义 `_book_file` / `_fingerprint` /
`_is_stale` 这类已归一的原语，骨架就被复制了一遍，30 分钟僵尸口径会重新各说各话——
R169 的「双胞胎侧改一处漏一处」正是这么来的。
"""

import inspect

import pytest

from cps.reading_job import service_base
from cps.reading_job.service_base import ACTIVE_STATUSES, JobServiceBase
from cps.reading_translation.service import WholeBookTranslationService
from cps.reading_tts.service import WholeBookTtsService
from cps.reading_word_detail.service import WordDetailBatchService

SERVICES = [WholeBookTranslationService, WholeBookTtsService, WordDetailBatchService]
IDS = ["translation", "tts", "word_detail"]

# 已归一到骨架、不得再出现在子类 __dict__ 里的原语
RELOCATED = ("_ensure_tables", "_book_file", "_fingerprint", "_find_active_job",
             "_is_stale", "_is_fresh", "_close_as_zombie", "_own_job", "_pending_count",
             "_needs_worker", "_revive_running", "_spawn_worker", "_worker_guarded")


@pytest.mark.parametrize("cls", SERVICES, ids=IDS)
def test_骨架原语不得在子类里长回第二份(cls):
    assert issubclass(cls, JobServiceBase), cls.__name__
    doubled = sorted(name for name in RELOCATED if name in cls.__dict__)
    assert doubled == [], f"{cls.__name__} 重新定义了骨架方法：{doubled}"


def test_同一原语三家只有一份实现():
    for name in ("_book_file", "_fingerprint", "_ensure_tables", "_is_stale", "_is_fresh",
                 "_own_job"):
        impls = {getattr(cls, name) for cls in SERVICES}
        assert len(impls) == 1, f"{name} 在三个服务之间又分叉了"


@pytest.mark.parametrize("cls", SERVICES, ids=IDS)
def test_骨架依赖的类属性必须显式填(cls):
    # 空 job_model 会让 _ensure_tables 在建表时才炸，宁可在这里就红
    for attr in ("job_model", "item_model", "log_prefix", "job_log", "missing_job_error"):
        assert attr in cls.__dict__, f"{cls.__name__} 未声明 {attr}"
    assert "RUNNING" in cls.active_statuses


def test_僵尸阈值只有单一事实源():
    assert service_base.ZOMBIE_MINUTES == 30
    for cls in SERVICES:
        module = inspect.getmodule(cls)
        assert not hasattr(module, "ZOMBIE_MINUTES"), \
            f"{module.__name__} 又自定义了僵尸阈值"


def test_查无批次的文案逐字保持():
    # 文案是前端 toast 与路由状态码的一部分，重构不许顺手改词
    assert WholeBookTranslationService.missing_job_error == "translation job is unavailable"
    assert WordDetailBatchService.missing_job_error == "word detail job is unavailable"
    assert WholeBookTtsService.missing_job_error == "job not found"


def test_own_job_只认当前用户名下的批次(app, monkeypatch):
    """`_own_job` 的属主过滤是鉴权边界，归一到骨架后必须仍可测。

    Why 单独钉：评审复查发现三家唯一的按属主取批次路径（翻译 / 详解的 progress/retry/cancel）
    在 B6 后一次都没被跑到——桩打在原子类模块的 `current_user` 上已够不着骨架。这里把桩
    打到骨架模块，并用「别人的批次取不到」把这条边界钉住（朗读侧 loader 不筛属主，
    属另一条待决事实，见 b6-job-service-base.md §4）。
    """
    from cps import ub
    from cps.reading_job import service_base as base_svc
    from cps.reading_translation.models import TranslationJob
    from cps.reading_translation.timeutil import now_utc

    class _User:
        id = 7

    monkeypatch.setattr(base_svc, "current_user", _User)
    service = WholeBookTranslationService()
    service._ensure_tables()
    mine = TranslationJob(id="job-mine", user_id=7, book_id=1, book_format="EPUB",
                          book_name="Mine", book_fingerprint="fp", status="RUNNING",
                          total_count=1)
    theirs = TranslationJob(id="job-theirs", user_id=8, book_id=2, book_format="EPUB",
                            book_name="Theirs", book_fingerprint="fp", status="RUNNING",
                            total_count=1)
    for job in (mine, theirs):
        job.updated_at = job.created_at = now_utc()
        ub.session.add(job)
    ub.session.commit()

    assert service.get_progress("job-mine")["jobId"] == "job-mine"
    for missing in ("job-theirs", "job-none"):
        with pytest.raises(ValueError) as error:
            service.get_progress(missing)
        assert str(error.value) == "translation job is unavailable"


def test_台账活跃状态集合保持各家现值():
    # 归一常量不等于归一口径：整本朗读刻意不含 PENDING（批次一建就是 RUNNING）
    assert ACTIVE_STATUSES == ("PENDING", "RUNNING", "PARTIAL_FAILED")
    assert WholeBookTtsService.active_statuses == ("RUNNING", "PARTIAL_FAILED")
    assert WholeBookTtsService.active_statuses is not ACTIVE_STATUSES
    assert WholeBookTranslationService.active_statuses == ACTIVE_STATUSES
    assert WordDetailBatchService.active_statuses == ACTIVE_STATUSES


def test_补线程判据_只排除已取消_有活线程不补(monkeypatch):
    """R169 自愈判据的三条边界，归一到骨架后仍要成立。

    Why 把 COMPLETED 也判「该补」并写进守卫：这是评审揪出的一次静默行为变更——骨架初版把
    否决条件从「status == CANCELLED」改成「status not in active_statuses」，于是「台账已
    COMPLETED 却还留着 PENDING 段」的矛盾批次点重试会变成 no-op（旧实现照补线程）。
    终态要不要自愈由调用方决定（朗读的 retry 只管「已取消不复活」），骨架不越权。
    """
    class _Job:
        id = "j-1"

    service = WholeBookTtsService(None)
    monkeypatch.setattr(service, "_pending_count", lambda job_id: 3)
    for status in ("RUNNING", "PARTIAL_FAILED", "COMPLETED"):
        job = _Job()
        job.status = status
        assert service._needs_worker(job) is True, status
    job = _Job()
    job.status = service.cancelled_status
    assert service._needs_worker(job) is False
    job = _Job()
    job.status = "RUNNING"
    service._live_workers.add("j-1")
    assert service._needs_worker(job) is False

def test_边界值上新鲜与停滞不是取反关系(monkeypatch):
    """`_is_stale` 与 `_is_fresh` 并存的原因（评审修正 #2）。

    旧实现两处比较本就不是互补的：僵尸判定用 ``now - updated_at > 30min``，一键译全库的
    「在跑就跳过」用 ``updated_at > now - 30min``。恰好停在 30 分整时两者**都是 False**——
    若把后者写成 ``not _is_stale(...)``，同一条记录就从「开新批次」变成「算在跑」。
    时间钉住之后这条判据是可测的，不是修辞。
    """
    from datetime import datetime, timedelta, timezone

    from cps.reading_job import service_base as base_svc

    frozen = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(base_svc, "now_utc", lambda: frozen)

    class _Job:
        pass

    job = _Job()
    job.updated_at = frozen - timedelta(minutes=30)
    assert base_svc.JobServiceBase._is_stale(job) is False
    assert base_svc.JobServiceBase._is_fresh(job) is False

    job.updated_at = frozen - timedelta(minutes=30, seconds=1)
    assert base_svc.JobServiceBase._is_stale(job) is True
    assert base_svc.JobServiceBase._is_fresh(job) is False


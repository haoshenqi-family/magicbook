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
             "_is_stale", "_close_as_zombie", "_own_job", "_pending_count",
             "_needs_worker", "_revive_running", "_spawn_worker", "_worker_guarded")


@pytest.mark.parametrize("cls", SERVICES, ids=IDS)
def test_骨架原语不得在子类里长回第二份(cls):
    assert issubclass(cls, JobServiceBase), cls.__name__
    doubled = sorted(name for name in RELOCATED if name in cls.__dict__)
    assert doubled == [], f"{cls.__name__} 重新定义了骨架方法：{doubled}"


def test_同一原语三家只有一份实现():
    for name in ("_book_file", "_fingerprint", "_ensure_tables", "_is_stale", "_own_job"):
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


def test_台账活跃状态集合保持各家现值():
    # 归一常量不等于归一口径：整本朗读刻意不含 PENDING（批次一建就是 RUNNING）
    assert ACTIVE_STATUSES == ("PENDING", "RUNNING", "PARTIAL_FAILED")
    assert WholeBookTtsService.active_statuses == ("RUNNING", "PARTIAL_FAILED")
    assert WholeBookTtsService.active_statuses is not ACTIVE_STATUSES
    assert WholeBookTranslationService.active_statuses == ACTIVE_STATUSES
    assert WordDetailBatchService.active_statuses == ACTIVE_STATUSES


def test_补线程判据_终态不补_有活线程不补(monkeypatch):
    """R169 自愈判据的三条边界，归一到骨架后仍要成立。"""
    class _Job:
        id = "j-1"

    service = WholeBookTtsService(None)
    monkeypatch.setattr(service, "_pending_count", lambda job_id: 3)
    for status in ("CANCELLED", "COMPLETED", "RUNNING"):
        job = _Job()
        job.status = status
        assert service._needs_worker(job) is (status == "RUNNING"), status
    service._live_workers.add("j-1")
    job = _Job()
    job.status = "RUNNING"
    assert service._needs_worker(job) is False

"""R277 请求失败必须可诊断。

现象：开发者工具里一切正常，体验版/真机全部「网络请求失败，请检查网络」。
根因几乎总是 wx.request 的 fail —— 而 fail 里唯一有价值的 `errMsg`
（形如 `request:fail url not in domain list`）被我们自己抹掉了，
于是「域名白名单没配」被显示成「网络有问题」，排查方向整体跑偏。

本锁保证三件事不被改回去：
1. fail 回调必须接收 err 并把 errMsg 带进日志；
2. 「不在白名单」要单独识别，并直接给出后台的配置路径；
3. 兜底也要原样带出 errMsg，而不是一句空话。
"""

import os

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def test_fail_callback_keeps_err_msg():
    api = _read("utils/api.js")
    assert "fail: (err) =>" in api, "fail 回调必须接收 err，否则拿不到 errMsg"
    assert "err.errMsg" in api, "errMsg 必须被读取"
    assert "console.error" in api, "原始 errMsg 要留痕，体验版调试面板才看得到"


def test_domain_whitelist_is_recognized():
    api = _read("utils/api.js")
    assert "not in domain list" in api, "白名单错误要单独识别"
    assert "服务器域名" in api, "提示里要给出后台配置路径，而不是让用户「检查网络」"
    assert "CONFIG.baseUrl" in api, "提示里带上实际要配的域名，省一次来回"


def test_unknown_failure_still_shows_raw_reason():
    api = _read("utils/api.js")
    fallback = "return raw ? '网络请求失败：' + raw : '网络请求失败：请检查网络';"
    assert fallback in api, "认不出的失败也要原样带出 errMsg"


def test_old_misleading_message_is_gone():
    api = _read("utils/api.js")
    assert "请检查网络，或在开发者工具中关闭「域名校验」" not in api, \
        "旧文案把真机问题说成开发者工具设置问题，会误导排查"

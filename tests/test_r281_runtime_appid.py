"""R281 报错里必须带出运行时 AppID。

真实困境：白名单是按 AppID 存的，而「代码里的 appid」不等于「这个包上传时用的 appid」。
改了 project.config.json 却没重新上传、或开发者工具里项目 AppID 还是旧号，
都会让人对着后台反复确认「我明明配好了」。把运行时 appid 写进报错和日志，
一次就能排除这类猜测。
"""

import os

ROOT = "miniprogram"


def _api():
    with open(os.path.join(ROOT, "utils/api.js"), encoding="utf-8") as handle:
        return handle.read()


def test_runtime_appid_is_read_from_account_info():
    api = _api()
    assert "wx.getAccountInfoSync" in api, "运行时 AppID 只能从 getAccountInfoSync 取"
    assert "miniProgram.appId" in api
    # 基础库差异下该接口可能不存在，必须容错，不能因为拿不到 appid 就把请求逻辑搞崩
    assert "function runtimeAppId()" in api
    assert "catch (e)" in api


def test_whitelist_error_mentions_runtime_appid():
    api = _api()
    assert "当前 AppID" in api, "白名单报错要直接写清是哪个 AppID 在跑"
    assert "为这个 AppID 添加" in api, "提示要绑定到「这个 AppID」，而不是一个抽象的域名"


def test_console_log_carries_appid():
    api = _api()
    assert "appid=' + runtimeAppId()" in api, "console 日志同样要带 appid，便于体验版 vConsole 核对"

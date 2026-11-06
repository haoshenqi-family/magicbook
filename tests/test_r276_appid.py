"""R276 小程序 AppID 必须是正式号。

起因：开发者工具里点「预览 / 真机调试」弹「测试号 AppId 无法使用当前功能」。
测试号除了不能真机，还有一个更隐蔽的问题——它的 openid 与正式号不同域，
换号后所有微信绑定都会「查无此人」，用户看到的是一个空账号。

锁两件事：
1. appid 就是正式号（不是 touristappid，也不是过渡期用过的测试号）；
2. 格式合法（wx + 16 位十六进制），防止手抄漏字符。

第三件事（后端默认值必须与此处一致）没法在这里断言：它依赖兄弟仓路径，
CI 里只检出 magicbook 时必然假失败。改由 moon-well 的
`WechatAppIdConfigTest` 锁住自己那一侧，两边的改动在同一张需求单上评审。
"""

import json
import os
import re

ROOT = "miniprogram"
PRODUCTION_APPID = "wx7b31b435be6beae3"
# 过渡期用过的测试号，不得再回到配置里
RETIRED_TEST_APPID = "wxd511f98508dc9cee"


def _config():
    with open(os.path.join(ROOT, "project.config.json"), encoding="utf-8") as handle:
        return json.load(handle)


def test_appid_is_production():
    appid = _config().get("appid", "")
    assert appid == PRODUCTION_APPID, "必须是正式 AppID，当前为 %r" % appid
    assert appid != RETIRED_TEST_APPID
    assert "tourist" not in appid


def test_appid_format():
    appid = _config()["appid"]
    assert re.fullmatch(r"wx[0-9a-f]{16}", appid), "AppID 应为 wx + 16 位十六进制: %r" % appid

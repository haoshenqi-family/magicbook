# cps/landing.py — 登录 / 回站后的默认落点（R213-C / MB-18）。
#
# Why 单独一个模块而不是塞进 web.py：落点判据被三处消费——web.py 的登录页与
#     登录提交、oidc.py 的授权回调。oidc.py 在 web.py 导入期就被注册，若把
#     判据写在 web.py，oidc.py 只能用函数内 import 绕环形依赖；独立小模块让
#     三处都能在模块顶部正常 import。
# How 判据只有一条：站点配置 `config_home_landing` 为真则落 `web.home`，
#     否则回退 `web.index`（原 `/` 发现页）——回退不需要发版，见 config_sql.py
#     里该列的注释。

import logging

from . import config

log = logging.getLogger(__name__)

HOME_ENDPOINT = "web.home"
FALLBACK_ENDPOINT = "web.index"


def landing_endpoint():
    """返回登录 / 回站后应落到的 endpoint 名。

    读配置失败一律回退 `web.index`：落点判断不该成为登录链路的故障点——
    宁可回旧首页，也不能让「登录成功但 500」。
    """
    try:
        if config.config_home_landing:
            return HOME_ENDPOINT
    except Exception as exc:  # 老库缺列 / 配置未初始化
        log.warning("home landing flag unavailable, falling back to index: %s", exc)
    return FALLBACK_ENDPOINT

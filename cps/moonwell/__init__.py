# cps/moonwell — moon-well 防腐层包（R178，架构评审 B1）。
#
# 本包是 magicbook 访问 moon-well 的唯一出口：URL、trace-id、令牌（用户 JWT /
# 系统服务账号 mk- key）、代理禁用、401 刷新、统一三元组响应形态都收敛在
# client.MoonWellClient。业务模块（web.py 路由、ai/proxy、book_import、
# __init__ 恢复闭包、oidc 回调）一律经本包，不再 import cps.web 的防腐层。
from cps.moonwell.client import MoonWellClient, client

__all__ = ["MoonWellClient", "client"]

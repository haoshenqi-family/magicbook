# cps/routes — 定制路由按域分文件（R181，架构评审 B2）。

def register_domain_routes(web):
    """web.py 末尾调用：import 即完成各域装饰注册。"""
    from cps.routes import reading, credit, vocab, learning, buddy, preferences, book_detail, home  # noqa: F401

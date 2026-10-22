"""R206 伙伴页服务端渲染冒烟：只验模板能出页面，不验 JS 行为。

Why: /buddy 由前端异步拉 catalog，既有全量用例一个都不覆盖它；本仓 layout.html 的
     渲染错误会让所有 extends layout 的页面一起 500，必须有断言站住这条路。
"""


def test_buddy_page_renders(admin_client):
    rv = admin_client.get("/buddy")
    assert rv.status_code == 200
    body = rv.data.decode("utf-8")
    assert 'id="buddy-roster"' in body
    assert 'id="buddy-csrf"' in body


def test_buddy_nav_entry_present_once(admin_client):
    body = admin_client.get("/buddy").data.decode("utf-8")
    assert body.count('id="top_buddy"') == 1

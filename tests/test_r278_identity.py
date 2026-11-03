"""R278 账号 ID 不得出现在界面上，身份只用邮箱表达。

背景：账号页原本显示「账号 ID 123 · 邮箱 x@y」，副标题还回显自动生成的 username
（`wx_xxx` 一类内部标识）。对用户没有可用性，截图分享时还等于把内部标识发出去。

锁三件事：
1. 模板里不得出现 `user.userId` / `user.username`；
2. 「账号 ID」这句话不得回来；
3. 「我」页的身份计算只允许用昵称与邮箱，username 只能存在于存储层，不能参与展示。
"""

import glob
import os

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _templates():
    for path in glob.glob(os.path.join(ROOT, "pages", "*", "*.wxml")):
        yield os.path.relpath(path, ROOT), open(path, encoding="utf-8").read()


def test_templates_never_render_account_identifiers():
    for name, content in _templates():
        assert "user.userId" not in content, "%s 不应渲染 userId" % name
        assert "user.username" not in content, "%s 不应渲染自动生成的 username" % name


def test_account_id_label_is_gone():
    assert "账号 ID" not in _read("pages/account/account.wxml")


def test_identity_is_expressed_with_email():
    account = _read("pages/account/account.wxml")
    stats = _read("pages/stats/stats.wxml")
    assert "user.email" in account, "账号页要用邮箱表达身份"
    assert "user.email" in stats, "「我」页要用邮箱表达身份"


def test_identity_helpers_ignore_username():
    stats_js = _read("pages/stats/stats.js")
    assert "user.username" not in stats_js, "username 只能留在存储层，不得参与展示计算"
    assert "user.nickname || user.email" in stats_js, "头像首字取昵称或邮箱"

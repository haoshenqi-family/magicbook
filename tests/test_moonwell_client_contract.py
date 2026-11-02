"""R178（架构评审 B1）：moon-well 防腐层包（cps/moonwell/）的契约锁。

Why 纯静态断言：防腐层的关键失效模式都不是运行时报错——
  (1) 失败分支形态回潮（有人在新分支里 return jsonify(...) 恢复二元组）→
      消费方解包即 ValueError→500 白页（报告 §3.2 🔴 的原始事故形态）；
  (2) 反向 import web 回潮（新代码图方便 from cps.web import _moonwell_proxy）→
      web.py 三重身份回归，上游 merge 冲突面重新增长；
  (3) exchange 直连回潮（新回调页绕过 client 自连）→ URL/禁代理/双键名解析
      口径再次散落。
源码级锁住这三种回潮。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_PATH = os.path.join(ROOT, "cps", "moonwell", "client.py")
WEB_PATH = os.path.join(ROOT, "cps", "web.py")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def test_c1_client_is_single_exit_and_tuple_only():
    client = read("cps", "moonwell", "client.py")
    assert "class MoonWellClient" in client
    assert "client = MoonWellClient()" in client
    for method in ["def base_url", "def trace_id", "def system_token",
                   "def proxy", "def refresh_session_token", "def multipart",
                   "def settings_fetch", "def exchange_id_token"]:
        assert method in client, f"client 缺少 {method}"
    # 统一三元组：client 里禁止 jsonify「调用」（失败分支一律手拼 JSON 三元组，
    # daemon 线程无 Flask 上下文也安全）；模块头注释解释 Why 的文字提及不算
    assert not re.search(r"(?<![-—\w])jsonify\s*\(", client), \
        "client.py 出现 jsonify 调用——统一三元组契约被破坏"


def test_c2_web_py_delegates_not_owning():
    web = read("cps", "web.py")
    for fn in ["_moonwell_base_url", "_moonwell_trace_id", "_moonwell_system_token",
               "_moonwell_proxy", "_moonwell_refresh_session_token",
               "_moonwell_multipart", "_moonwell_settings_fetch"]:
        assert f"def {fn}" in web, f"web.py 缺薄委托 {fn}"
    # 本体特征不再出现在 web.py：requests 直连与 refresh 实现必须已迁出
    assert not re.search(r"requests\.(post|get)\(\s*base \+", web), \
        "web.py 仍有 moon-well 直连实现（应委托 cps/moonwell/client）"
    assert "from cps.moonwell.client import NO_PROXY, client as _moonwell_client" in web
    assert "_MOONWELL_NO_PROXY = NO_PROXY" in web
    # bridge（业务编排 107 行）按计划留守 web.py，B2 蓝图分域时迁出
    assert "def _moonwell_book_finished_bridge" in web


def test_c3_no_reverse_import_web_for_moonwell():
    ai_proxy = read("cps", "ai", "proxy.py")
    assert "from cps.web import" not in ai_proxy, \
        "ai/proxy.py 反向 import web 回潮（应引 cps/moonwell/client）"
    assert "cps.moonwell" in ai_proxy

    init = read("cps", "__init__.py")
    assert "web_module._moonwell_proxy" not in init, \
        "__init__.py 仍经 web_module 取防腐层（应直引 client）"
    assert "from cps.moonwell.client import client" in init

    book_import = read("cps", "book_import.py")
    assert "web_module._moonwell_proxy" not in book_import
    assert "from cps.moonwell.client import client" in book_import

    oidc = read("cps", "oidc.py")
    assert "/auth/oidc/exchange" not in oidc, \
        "oidc.py 仍直连 exchange（应收编 client.exchange_id_token）"
    assert "exchange_id_token" in oidc


def test_c3b_editbooks_bridge_import_still_valid():
    # bridge 留守 web.py（B2 范围），editbooks 的既有 import 保持有效
    editbooks = read("cps", "editbooks.py")
    assert "from .web import _moonwell_book_finished_bridge" in editbooks
    web = read("cps", "web.py")
    assert "def _moonwell_book_finished_bridge" in web

"""R282 报错必须说出「实际请求的完整 URL」。

现象：后台白名单、开发者工具「项目配置 → 域名信息」、工具本地缓存三处都显示
`https://moon-well.haoshenqi.top` 已在 request 合法域名里，运行时 AppID 也确实是
正式号，可请求仍然报 `url not in domain list`。

排查之所以绕了几轮，是因为我们自己给的提示只打印 `CONFIG.baseUrl`——
**它永远显示那个「本该正确」的域名**。路径拼接错误、baseUrl 带隐藏字符、
或者请求根本发往了别处时，提示依然看起来完全正常，于是人被引去反复确认后台。

本锁要求：一旦失败，屏幕与日志都要能回答「到底请求了哪个地址」。
"""

import json
import os
import subprocess

ROOT = "miniprogram"
API = os.path.join(ROOT, "utils", "api.js")


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _node(script):
    result = subprocess.run(
        ["node", "-e", script],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_request_url_is_computed_once_and_reused():
    api = _read("utils/api.js")
    assert "const url = CONFIG.baseUrl + options.path;" in api, \
        "完整 URL 要先算出来，wx.request 与报错共用同一个值"
    # wx.request 传的必须是那个变量，而不是再拼一次（拼两次迟早有一处漏改）
    assert "      url,\n" in api, "wx.request 必须直接使用算好的 url 变量"


def test_failure_log_prints_full_url_not_just_path():
    api = _read("utils/api.js")
    assert "console.error('[api] 请求失败', url," in api, \
        "日志要打完整 URL：只打 path 看不出主机名是否拼错"
    assert "console.error('[api] 请求失败', options.path," not in api, \
        "旧的「只打 path」写法要消失"


def test_whitelist_message_exposes_real_url_and_raw_reason():
    api = _read("utils/api.js")
    assert "实际请求" in api, "提示里要带真实请求地址"
    assert "微信原文" in api, "提示里要带 errMsg 原文，避免我们的分类器盖掉真相"
    assert "hostOf(url)" in api, "被拦域名要从真实 URL 取，不能从 baseUrl 取"


def test_both_call_sites_pass_url():
    api = _read("utils/api.js")
    assert "describeNetworkError(err, url)" in api, "普通请求要把 url 传进分类器"
    assert "describeNetworkError(err, chatUrl)" in api, "SSE 请求同样要传 url"


def test_host_of_strips_scheme_path_and_keeps_port():
    script = (
        "const api=require('./miniprogram/utils/api.js');"
        "console.log(JSON.stringify(["
        "api.hostOf('https://moon-well.haoshenqi.top/auth/wx/login'),"
        "api.hostOf('https://a.b:8443/x?y=1'),"
        "api.hostOf(''),api.hostOf(null)]));"
    )
    assert json.loads(_node(script)) == [
        "moon-well.haoshenqi.top",
        "a.b:8443",
        "",
        "",
    ], "hostOf 只保留主机（去协议/路径/查询串），端口要保留以便暴露带端口的配置错误"


def test_comment_does_not_pretend_to_be_the_message():
    """提示文案里不能再只有 baseUrl 那一种说法。

    R277/R281 的锁盯着「服务器域名」「为这个 AppID 添加」这类措辞，
    本锁只补一条：凡是告诉用户「去加这个域名」，都必须同时给出真实 URL。
    """
    api = _read("utils/api.js")
    start = api.index("function describeNetworkError")
    end = api.index("function unwrap")
    body = api[start:end]
    assert "实际请求" in body and "url" in body

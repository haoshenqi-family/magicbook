# cps/routes/brand.py — 品牌资产同源代理（R212-B）。
# MinIO `brand/` 为唯一真源：发布对象即 magicbook 与 authentik 一起换标，无需重新构建/推送。
# Why 同源代理而非 HTML 直链 MinIO：① 顶栏徽章与 favicon 在每一页，直链要把 img-src 全站
# 放宽到 MinIO，推翻 R181/R220 有意收紧的守卫（tests/test_csp_media.py）；② R220 实测个别
# 拦截类扩展对跨站图片子资源 ERR_BLOCKED_BY_CLIENT，直链会让带扩展的用户全站裂图。
# 代理把两者都避开：HTML 只引同源路径，CSP 不动、扩展不拦、真源仍是 MinIO。
# 防滥用（SSRF/开放代理）：对象名固定白名单 + GET-only + 只拼本站 MinIO 入口，不接受任意 src。
import logging
import mimetypes
import time

from cps.web import web
from flask import Response
import requests as http_requests

log = logging.getLogger(__name__)

# 只代理顶栏/favicon 实际引用的 emblem 章；lockup（brand/logo.png）仅 authentik 直链，不经本站。
BRAND_OBJECTS = ("favicon.png",)
_MINIO_ORIGIN = "https://minio.haoshenqi.top"
_BUCKET_PATH = "/magicbook/brand/"
_TTL = 300  # 进程内缓存与 Cache-Control 同步：发布 MinIO 后最长 5 分钟全站生效

_cache = {}


@web.route("/brand/<name>", methods=["GET"])
def brand_asset(name):
    """同源吐出 MinIO brand/ 对象；免登录（登录页顶栏与 favicon 匿名就要能加载）。"""
    if name not in BRAND_OBJECTS:
        return Response("unknown brand asset", status=404)
    entry = _cache.get(name)
    if not entry or entry[0] <= time.time():
        url = _MINIO_ORIGIN + _BUCKET_PATH + name
        try:
            upstream = http_requests.get(url, timeout=10)
        except http_requests.RequestException:
            log.warning("brand upstream unreachable: %s", url)
            return Response("brand upstream unreachable", status=502)
        if upstream.status_code != 200:
            log.warning("brand upstream error %s: %s", upstream.status_code, url)
            return Response("brand upstream error", status=upstream.status_code)
        ctype = (upstream.headers.get("Content-Type")
                 or mimetypes.guess_type(name)[0] or "application/octet-stream")
        entry = (time.time() + _TTL, upstream.content, ctype)
        _cache[name] = entry
    resp = Response(entry[1], mimetype=entry[2])
    resp.headers["Cache-Control"] = "public, max-age=%d" % _TTL
    return resp

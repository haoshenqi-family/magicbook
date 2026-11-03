"""R271 微信小程序的静态契约锁。

Why 静态锁：小程序不在容器里跑，`pytest` 与 `node --check` 都只能看见单个文件是否合法，
看不见「app.json 引用的页面是否存在」「tabBar 指向的页面是否在 pages 里」「config 里
baseUrl 是否还是生产域名」这类**跨文件一致性**。这些错误在开发者工具里表现为白屏或
tab 点不动，而本机没有开发者工具，只能在源码层钉住。

锁的四件事：
1. 每个页面四件套齐全（.js/.json/.wxml/.wxss），app.json 的 pages 都能落地；
2. tabBar 的 pagePath 必须都在 pages 里（否则这个 tab 点了就白）；
3. 生产域名仍是 moon-well（换域名必须改这里，避免改漏 config 却以为切了环境）；
4. 小程序目录不进容器镜像（`Dockerfile` 不 COPY 它，`cps/` 不引用它）——
   否则一次 push 会把小程序源码塞进网页镜像，构建体积与语义都错。
"""

import json
import os

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _json(relative):
    return json.loads(_read(relative))


def test_pages_have_all_four_parts():
    pages = _json("app.json")["pages"]
    assert pages, "app.json 未声明页面"
    for page in pages:
        for suffix in (".js", ".json", ".wxml", ".wxss"):
            path = os.path.join(ROOT, page + suffix)
            assert os.path.isfile(path), "页面文件缺失: %s" % path


def test_tabbar_points_to_declared_pages():
    app = _json("app.json")
    pages = set(app["pages"])
    for item in app["tabBar"]["list"]:
        assert item["pagePath"] in pages, "tabBar 指向未声明页面: %s" % item["pagePath"]
        assert item.get("text"), "tabBar 项必须有文字（本项目用纯文字 tab，不带图标资源）"


def test_base_url_is_production_backend():
    config = _read("config.js")
    assert "https://moon-well.haoshenqi.top" in config, "baseUrl 必须指向生产后端"
    assert "http://" not in config, "小程序只允许 HTTPS 请求"


def test_miniprogram_stays_out_of_image():
    with open("Dockerfile", encoding="utf-8") as handle:
        dockerfile = handle.read()
    assert "miniprogram" not in dockerfile, "小程序源码不得进容器镜像"


def test_frontend_does_not_import_miniprogram():
    """cps/ 侧不应引用小程序：两边唯一的耦合是 HTTP 契约，不是代码。"""
    for dirpath, _dirnames, filenames in os.walk("cps"):
        for name in filenames:
            if not name.endswith((".py", ".html", ".js")):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8", errors="ignore") as handle:
                if "miniprogram" in handle.read():
                    raise AssertionError("cps/ 侧出现 miniprogram 引用: %s" % path)


def test_appid_is_declared():
    config = _json("project.config.json")
    assert config.get("appid", "").startswith("wx"), "project.config.json 缺少正式 AppID"
    assert "touristappid" not in config["appid"], "不得把游客 AppID 提交上去"

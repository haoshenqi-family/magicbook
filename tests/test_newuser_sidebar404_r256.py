"""R256：黑盒体验报告四项缺陷的回归守卫。

Why：R256 黑盒体验报告（新用户视角）暴露四项缺陷——
    B1 新 OIDC 用户九个侧栏浏览入口全 404（建号漏设 sidebar_view）；
    B2 空标题书架可创建且无界面入口可清理；
    B4 详情页阅读状态开关的固定 label 复用 msgid "Read"（po 译「已读」），
       未读书籍也显示「已读」字样，状态语义失真；
    B5 听写/复述/重读素材下拉直接展示元数据里未解码的 HTML 实体。
每项用例钉住「不能再次退化」的那条硬约束，根因说明见各用例 docstring。
"""
import os

import pytest

from cps import config, constants, oidc
from cps import ub

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 线上实测（R256 体验报告）：这九个入口在位缺失时统一 abort(404)。
BROWSE_ENDPOINTS = [
    ("category", constants.SIDEBAR_CATEGORY),
    ("series", constants.SIDEBAR_SERIES),
    ("author", constants.SIDEBAR_AUTHOR),
    ("publisher", constants.SIDEBAR_PUBLISHER),
    ("language", constants.SIDEBAR_LANGUAGE),
    ("ratings", constants.SIDEBAR_RATING),
    ("formats", constants.SIDEBAR_FORMAT),
    ("rated", constants.SIDEBAR_BEST_RATED),
    ("downloadlist", constants.SIDEBAR_DOWNLOAD),
]


class TestOidcNewUserSidebarView:
    """B1：OIDC 建号必须显式取站点默认侧栏位，位缺失=浏览路由 404。"""

    def test_建号侧栏位取站点默认值(self, monkeypatch):
        monkeypatch.setattr(config, "config_default_show", 262143, raising=False)
        assert oidc.new_user_sidebar_view() == 262143

    def test_站点默认位覆盖九个浏览入口的可见性位(self, monkeypatch):
        """262143（现网 config_default_show 实测值）必须同时含九个浏览位。

        新增浏览路由时把 (endpoint, 位) 追加进 BROWSE_ENDPOINTS——漏位的直接
        症状就是新用户侧栏入口 404。
        """
        monkeypatch.setattr(config, "config_default_show", 262143, raising=False)
        value = oidc.new_user_sidebar_view()
        for endpoint, bit in BROWSE_ENDPOINTS:
            assert constants.has_flag(value, bit), \
                "站点默认位缺 {0}（SIDEBAR 位 {1}），新用户该入口将 404".format(endpoint, bit)

    def test_配置未初始化时回退0而不抛异常(self, monkeypatch):
        """config 单例可能尚未初始化（None）——回退 0 交管理员后台补，不猜位组合。"""
        monkeypatch.setattr(config, "config_default_show", None, raising=False)
        assert oidc.new_user_sidebar_view() == 0

    def test_create_oidc_user_三项默认值一次取齐(self, app, monkeypatch):
        """R211（角色）/R256（侧栏位）踩的是同一个调用点——helper 必须三项都带。"""
        monkeypatch.setattr(config, "config_default_role", 0, raising=False)
        monkeypatch.setattr(config, "config_default_show", 262143, raising=False)
        # new_user_locale 在无 claim 时读 Accept-Language——真实回调永远发生在
        # 请求内，这里用请求上下文还原同一前提。
        with app.test_request_context("/", headers={"Accept-Language": "zh-CN"}):
            user = oidc.create_oidc_user("oidc-tester", "tester@example.com", {})
        assert user.name == "oidc-tester"
        assert user.email == "tester@example.com"
        assert constants.has_flag(user.role, constants.ROLE_VIEWER)
        assert user.sidebar_view == 262143
        # locale 落到 Accept-Language 归一结果或站点默认，只约束非空；
        # 归一细节由 new_user_locale 自身用例覆盖。
        assert user.locale


class TestShelfTitleRequired:
    """B2：空标题书架在创建入口拒绝——事后无界面可清理。"""

    @pytest.mark.parametrize("title", ["", "   "])
    def test_空标题创建被拒且不落库(self, admin_client, title):
        before = ub.session.query(ub.Shelf).count()
        rv = admin_client.post("/shelf/create", data={"title": title})
        assert rv.status_code == 302
        assert ub.session.query(ub.Shelf).count() == before

    def test_正常标题仍可创建(self, admin_client):
        rv = admin_client.post("/shelf/create", data={"title": "R256 回归书架"})
        assert rv.status_code == 302
        shelf = ub.session.query(ub.Shelf).filter(
            ub.Shelf.name == "R256 回归书架").first()
        assert shelf is not None
        # 清理，避免污染其他用例的书架计数守卫
        ub.session.delete(shelf)
        ub.session.commit()


class TestDetailReadStatusLabel:
    """B4：阅读状态开关的 label 不许复用 msgid "Read"。"""

    def test_详情页label改用Reading_status(self):
        with open(os.path.join(_BASE, "cps/templates/detail.html"),
                  encoding="utf-8") as fh:
            src = fh.read()
        # have_read_form 块内的 span 不再用 _('Read') 作 label
        marker = "have_read_form"
        idx = src.index(marker)
        block = src[idx:src.index("</form>", idx)]
        assert "_('Reading status')" in block
        assert "{{ _('Read') }}" not in block

    def test_中文词条已入库且已编译(self):
        """po 是源、mo 是运行时读取物——只查 po 不够，漏编译=线上仍旧英文。"""
        po_path = os.path.join(
            _BASE, "cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po")
        with open(po_path, encoding="utf-8") as fh:
            po = fh.read()
        entry = 'msgid "Reading status"\nmsgstr "阅读状态"'
        assert entry in po

        mo_path = os.path.join(
            _BASE, "cps/translations/zh_Hans_CN/LC_MESSAGES/messages.mo")
        with open(mo_path, "rb") as fh:
            mo = fh.read()
        assert "阅读状态".encode("utf-8") in mo


class TestDictationEntityDecode:
    """B5：素材下拉标题必须先解码 HTML 实体再进 textContent。"""

    def test_loadMaterials_经decode函数(self):
        path = os.path.join(_BASE, "cps/static/js/learning-common.js")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        assert "function decodeHtmlEntities" in src
        load_idx = src.index("function loadMaterials")
        block = src[load_idx:src.index("}", src.index("opt.textContent", load_idx))]
        assert "decodeHtmlEntities(m.title" in block

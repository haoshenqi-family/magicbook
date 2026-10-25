"""R225：注册跳转、普通账号阅读权限与品牌封面的行为守卫。

Why 单独成文件：这三条分别落在 OIDC / 权限 / 静态资产，回归时最容易只修一条
而把另外两条重新破坏。这里只钉可执行行为，不依赖生产账号或真实 Authentik。
"""
import gettext
import os
import importlib.util

from PIL import Image

from cps import constants


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZH_MO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN",
                     "LC_MESSAGES", "messages.mo")
R225_MSGIDS = (
    "Reading access is not enabled for this account",
    "Ask an administrator to enable “View” in Users → Edit User for your account.",
    "Download access is not enabled for this account",
    "Ask an administrator to enable “Download” in Users → Edit User for your account.",
    "Self-registered accounts always receive View. Administrators can still adjust it per account. Download is a separate permission.",
)


def test_generic_cover_is_brand_asset_not_white_text_placeholder():
    path = os.path.join(ROOT, "cps", "static", "generic_cover.jpg")
    with Image.open(path) as image:
        assert image.format == "JPEG"
        assert image.size == (564, 800)
        # 四角与中心都必须落在深墨绿底上；旧版白底黑字图会在这里报红。
        for point in ((4, 4), (559, 4), (4, 795), (559, 795), (282, 400)):
            red, green, blue = image.convert("RGB").getpixel(point)
            assert green > red + 15 and blue > red + 10, (point, (red, green, blue))


def test_all_missing_covers_use_the_same_brand_asset():
    helper = open(os.path.join(ROOT, "cps", "helper.py"), encoding="utf-8").read()
    assert helper.count('send_from_directory(_STATIC_DIR, "generic_cover.jpg")') == 1
    for marker in ("get_book_cover_internal", "get_cover_on_failure"):
        assert marker in helper


def test_detail_page_explains_missing_reading_permission():
    path = os.path.join(ROOT, "cps", "templates", "detail.html")
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    assert 'id="read-permission-hint"' in source
    assert "Reading access is not enabled for this account" in source
    assert "enable “View”" in source


def test_detail_page_explains_download_is_a_separate_permission():
    path = os.path.join(ROOT, "cps", "templates", "detail.html")
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    assert 'id="download-permission-hint"' in source
    assert "Download access is not enabled for this account" in source
    assert "enable “Download”" in source


def test_permission_hints_are_compiled_into_chinese_catalog():
    with open(ZH_MO, "rb") as fh:
        catalog = gettext.GNUTranslations(fh)
    untranslated = [msgid for msgid in R225_MSGIDS if catalog.gettext(msgid) == msgid]
    assert not untranslated, "R225 中文译文未进入 .mo：%r" % untranslated


def test_default_role_grants_reading_not_download():
    from cps import oidc

    role = oidc.resolve_new_user_role()
    assert constants.has_flag(role, constants.ROLE_VIEWER)
    assert not constants.has_flag(role, constants.ROLE_DOWNLOAD)
    assert not constants.has_flag(role, constants.ROLE_ADMIN)


def test_reader_route_is_guarded_by_viewer():
    web = open(os.path.join(ROOT, "cps", "web.py"), encoding="utf-8").read()
    route = web[web.index('@web.route("/read/<int:book_id>/<book_format>")'):]
    route = route[:route.index("def read_book")]
    assert "@viewer_required" in route


def test_signup_never_double_encodes_invite_query():
    oidc = open(os.path.join(ROOT, "cps", "oidc.py"), encoding="utf-8").read()
    source = oidc[oidc.index("def signup():"):]
    source = source[:source.index("def callback():")]
    assert 'urlencode({"itoken": invite_token, "next": target})' in source
    assert 'urlencode({"query": nested_query})' not in source


def test_invite_rotation_tool_builds_top_level_query():
    path = os.path.join(ROOT, "scripts", "rotate_authentik_invite.py")
    spec = importlib.util.spec_from_file_location("rotate_authentik_invite_r225", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    url = module.build_invite_url("https://account.example", "invite-token")
    assert url == "https://account.example/if/flow/invitation-enrollment/?itoken=invite-token"

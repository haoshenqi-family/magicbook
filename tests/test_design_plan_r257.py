"""R257：按产品设计方案实施的守卫测试。

方案一（普通用户不再渲染必 404 的「已下载书籍」入口）、方案三（复习队列空态
解释 + 词汇测试结果交叉引用）、方案四（下载权限提示改为用户视角）、方案六
（积分页/伙伴页英文残留补词条）、方案七（书库首页移除难度横幅）、方案八
（切语言原地停留 + 准确反馈）、方案九（删除书架真按钮 + 空标题兜底）。
模板/JS 源码断言沿用 R214/R251 的契约风格；HTTP 用例走 update_preferences。
"""
import os

import pytest

from cps import ub

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MO = 'cps/translations/zh_Hans_CN/LC_MESSAGES/messages.mo'


def _read(rel):
    with open(os.path.join(_BASE, rel), encoding='utf-8') as fh:
        return fh.read()


def _mo():
    from babel.messages.mofile import read_mo
    with open(os.path.join(_BASE, MO), 'rb') as fh:
        return read_mo(fh)


class TestPlan1SidebarEntrance:
    """方案一：侧栏只承诺真实可达的入口。"""

    def test_普通用户分支不再渲染已下载入口(self):
        src = _read('cps/render_template.py')
        # else 分支（web.books_list 的 download 页对普通用户 role_admin 门槛必 404）已删除：
        # 「Downloaded Books」元素只允许指向管理员专属的 web.download_list。
        assert src.count('"text": _(\'Downloaded Books\')') == 1
        assert "'web.download_list'" in src
        # 普通用户 else 分支（指向普通用户必 404 的 books_list download 页）已删除
        assert '"id": "download", "visibility": constants.SIDEBAR_DOWNLOAD, \'public\': (not current_user.is_anonymous),\n                        "page": "download", "show_text": _(\'Show Downloaded Books\'),\n                        "config_show": content})' not in src


class TestPlan3ReviewQueue:
    """方案三：空态解释去向，测试结果 ≤1 跳到复习队列。"""

    def test_测试结果旁有直达复习队列链接(self):
        tpl = _read('cps/templates/reading_settings.html')
        assert 'id="vt-notebook-link-row"' in tpl
        assert "url_for('web.learning_review_page')" in tpl

    def test_落本发生时JS显示链接(self):
        js = _read('cps/static/js/vocab-test.js')
        assert "show(els['vt-notebook-link-row'], true)" in js

    def test_空态解释排程语义(self):
        tpl = _read('cps/templates/learning_review.html')
        assert 'forgetting curve' in tpl
        # 旧的安慰性空态文案（无信息量）已替换
        assert 'Keep reading — new words will find their way here.' not in tpl


class TestPlan4DownloadCopy:
    """方案四：界面只说用户能做的事。"""

    def test_后台路径与角色名不再出现在下载提示(self):
        tpl = _read('cps/templates/detail.html')
        assert "Users → Edit User" not in tpl
        assert 'online reading is unaffected' in tpl
        # R225 加的「阅读权限」提示同口径修改
        assert 'Ask an administrator' not in tpl
        assert 'contact the site administrator' in tpl

    def test_新词条已编译(self):
        mo = _mo()
        for msgid in ("Download is not available; online reading is unaffected.",
                      "If you need download access, please contact the site administrator."):
            entry = mo.get(msgid)
            assert entry and entry.string, msgid


class TestPlan6I18nResidues:
    """方案六：积分页/伙伴页英文残留收口。"""

    def test_积分与稀有度词条已编译(self):
        mo = _mo()
        for msgid, want in [
            ("Recharge Now", "立即充值"),
            ("Credits Spent", "累计消耗"),
            ("AI Calls", "AI 调用次数"),
            ("COMMON", "普通"),
            ("RARE", "稀有"),
            ("EPIC", "史诗"),
            ("LEGENDARY", "传说"),
        ]:
            entry = mo.get(msgid)
            assert entry and entry.string == want, msgid

    def test_js文案经mbT(self):
        credits = _read('cps/static/js/credits.js')
        assert "t('Recharge Now')" in credits
        assert "t('Credits Spent')" in credits
        buddy = _read('cps/static/js/buddy.js')
        assert 'mbT("LEGENDARY")' in buddy

    def test_seed登记完整(self):
        seed = _read('cps/templates/i18n_seed.html')
        for key in ('"COMMON"', '"RARE"', '"EPIC"', '"LEGENDARY"',
                    '"Recharge Now"', '"Credits Spent"', '"AI Calls"'):
            assert key + ': _(' in seed, key


class TestPlan7DifficultyBanner:
    """方案七：书库首页不再常驻难度横幅。"""

    def test_index不再include横幅(self):
        tpl = _read('cps/templates/index.html')
        assert "difficulty_entry.html" not in tpl
        # 模板本体保留（阅读器/设置页仍可复用）
        assert os.path.exists(os.path.join(_BASE, 'cps/templates/difficulty_entry.html'))


class TestPlan8LanguageSwitch:
    """方案八：切语言原地停留 + 反馈准确。"""

    @pytest.fixture(autouse=True)
    def _restore_admin_locale(self, admin_client):
        """切语言用例会改共享 admin 会话的 locale——用后还原，避免顺序依赖。"""
        yield
        admin_client.post("/me/preferences", data={"locale": "en"})

    def test_切语言表单只在账号域且白名单仍生效(self):
        """R269 取代 R257 方案八的「顶栏原地停留」。

        顶栏语言下拉已整体撤掉，切语言的唯一表单在 /me；`next` 白名单守卫
        与「界面语言已更新」反馈仍然保留——它们是防开放重定向与反馈分流的
        契约，不随入口位置变化。
        """
        tpl = _read('cps/templates/layout.html')
        assert 'id="top_language"' not in tpl, "顶栏不应再有语言下拉（R269）"
        me = _read('cps/templates/me.html')
        assert 'id="me-language"' in me
        assert "url_for('web.update_preferences')" in me
        src = _read('cps/web.py')
        assert 'startswith("/") and not next_target.startswith("//")' in src

    def test_切语言反馈与资料保存反馈分离(self):
        src = _read('cps/web.py')
        assert 'Interface language updated' in src

    def test_http_切语言停留当前页(self, admin_client):
        rv = admin_client.post("/me/preferences",
                               data={"locale": "zh_Hans_CN", "next": "/learning"})
        assert rv.status_code == 302
        assert rv.headers["Location"].endswith("/learning")

    def test_http_openredirect被拒(self, admin_client):
        rv = admin_client.post("/me/preferences",
                               data={"locale": "zh_Hans_CN", "next": "//evil.example"})
        assert rv.status_code == 302
        assert "evil.example" not in rv.headers["Location"]


class TestPlan6bLanguageMenu:
    """方案六的折叠菜单已被 R269 取代：语言整体迁入账号域，改用全量 select。

    保留本类是为了把「为什么不再有顶栏折叠菜单」钉在测试里——方案六解决的
    是「顶栏 29 项铺开」；入口一旦搬进 /me 的下拉框，铺开问题自然消失，
    再留一套折叠 + 手风琴开关就是双份实现。
    """

    def test_语言入口只在账号域(self):
        tpl = _read('cps/templates/layout.html')
        for gone in ('mb_lang_priority', 'mb-lang-more-item', 'mb-lang-more-toggle'):
            assert gone not in tpl, "{0} 应随 R269 一起撤出顶栏".format(gone)
        me = _read('cps/templates/me.html')
        assert 'id="me-language"' in me
        assert 'name="locale"' in me

    def test_折叠开关已随入口下线(self):
        js = _read('cps/static/js/main.js')
        assert '#mb-lang-more-toggle' not in js, "元素已不存在，开关是死代码"
        assert '#top_language' not in js


class TestPlan9Shelf:
    """方案九：删除真按钮 + 空标题兜底。"""

    def test_删除书架是真按钮且防表单提交(self):
        tpl = _read('cps/templates/shelf.html')
        assert '<button type="button" class="btn btn-danger" data-action=' in tpl
        assert 'id="delete_shelf"' in tpl
        # 旧 div 形态不得残留
        assert '<div class="btn btn-danger" data-action=' not in tpl

    def test_空标题书架三处兜底(self):
        layout = _read('cps/templates/layout.html')
        assert layout.count("(shelf.name or _('Untitled Shelf'))") == 3
        shelf_py = _read('cps/shelf.py')
        assert 'name=shelf.name or _("Untitled Shelf")' in shelf_py

    def test_未命名书架词条已编译(self):
        entry = _mo().get("Untitled Shelf")
        assert entry and entry.string == "未命名书架"

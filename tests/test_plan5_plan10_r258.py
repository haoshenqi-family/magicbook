"""R258：设计方案五（充值卡五段式）与方案十（已读状态三态口径）守卫。

方案五验收口径（设计文档）：新用户看任意一张卡 3 秒内答对「花多少/得多少/
截止何时」；单一中文主按钮；单价辅助行自动算好。
方案十验收口径：新注册用户所有书显示未读；三态（未读/在读/已读）在详情页
可区分，不再被布尔化丢弃「在读」。生产数据诊断结论（2026-10-31，LLD）：
book_read_link 无脏数据，新用户零记录，B4 确系 R256 已修的 label 歧义。
"""
import os

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_BASE, rel), encoding='utf-8') as fh:
        return fh.read()


def _mo():
    from babel.messages.mofile import read_mo
    with open(os.path.join(_BASE, 'cps/translations/zh_Hans_CN/LC_MESSAGES/messages.mo'), 'rb') as fh:
        return read_mo(fh)


class TestPlan5PackageCard:
    """方案五：充值卡五段式。"""

    def test_五段式结构与顺序(self):
        js = _read('cps/static/js/credits.js')
        idx_price = js.index('① 价格大字')
        idx_gain = js.index('② 得到什么')
        idx_promo = js.index('③ 活动说明')
        idx_btn = js.index('④ 主按钮')
        idx_unit = js.index('⑤ 单价辅助行')
        assert idx_price < idx_gain < idx_promo < idx_btn < idx_unit

    def test_所得构成说人话(self):
        """旧卡「500万 积分内测 ×10 / 50万 积分 / ¥999.00」三层混排是硬伤——
        新卡把倍率翻译成「内测 N 倍 = 基础额度」。"""
        js = _read('cps/static/js/credits.js')
        assert '内测 ' in js and '基础额度' in js
        assert "pkg.baseCredits" in js

    def test_单价辅助行与口语化格式(self):
        js = _read('cps/static/js/credits.js')
        assert 'function formatCredits' in js
        assert '每万积分' in js
        # 不足一万积分的测试档不算单价（0.01 元 ÷ 0.01 万无意义）
        assert 'c < 10000' in js

    def test_倒计时文案词条齐备(self):
        mo = _mo()
        entry = mo.get('Beta bonus ends in ')
        assert entry and entry.string == '内测加赠，剩 '
        seed = _read('cps/templates/i18n_seed.html')
        assert '"Beta bonus ends in "' in seed

    def test_css层级齐备(self):
        css = _read('cps/static/css/credits.css')
        assert '.pkg-gain' in css and '.pkg-unit-price' in css


class TestPlan10ReadTriState:
    """方案十：详情页三态口径。"""

    def test_show_book透出三态(self):
        src = _read('cps/web.py')
        assert 'entry.read_status_finished' in src
        assert 'entry.read_status_in_progress' in src
        # 旧布尔化必须已移除
        assert 'entry.read_status = read_book == ub.ReadBook.STATUS_FINISHED' not in src

    def test_detail三态渲染(self):
        tpl = _read('cps/templates/detail.html')
        assert 'entry.read_status_finished %}checked' in tpl
        assert 'read-in-progress-badge' in tpl
        assert "{{_('Reading now')}}" in tpl

    def test_在读词条已编译(self):
        entry = _mo().get('Reading now')
        assert entry and entry.string == '在读'

    def test_高级搜索三态口径未受影响(self):
        """筛选直接查表三态，与详情页展示同源（设计口径一致性）。"""
        src = _read('cps/search.py')
        for state in ('STATUS_FINISHED', 'STATUS_IN_PROGRESS'):
            assert state in src

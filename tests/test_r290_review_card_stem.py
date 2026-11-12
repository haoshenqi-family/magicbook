"""R290 小程序每日复习页空题面死卡（用户截图）。

现象：截图里第 1/20 张卡只有一行「看下面的提示，回想这个词」+「揭示答案」，
**没有任何题面**；用户没有可看的内容，只能盲点，揭示后也不知道该回想什么。

根因（两层，都在 `pages/review`）：
1. 题干只挂在「四选一 / 拼写」两个分支上——`mode === 'CHOOSE' || mode === 'SPELL'`
   才渲染 `card.meaning`；而 `pickMode` 对 `RECALL`（后端默认档位、也是自适应策略
   最常给出的题型）返回 `SELF`，落进 `wx:else` 的提示语分支。于是**每一张回忆卡都
   没有题面**：后端下发的 `meaning` 就在手里，前端却没渲染它。
2. 释义缺失（后端契约：详解缓存未命中 `meaning=null`）时更彻底——提示语、释义、
   词面三者都不出现，卡片是一块白板；`contextClozeSentence` 也没被当成题干用过。

修法：
- 呈现态判定抽成纯函数 `utils/review-card.js#presentCard`，与网页端
  `learning-review.js` 同口径：CHOOSE/DISCRIMINATE 需释义 + ≥2 选项、SPELL 需释义、
  CONTEXT_CLOZE 用挖空句当题干、**其余有释义的一律 RECALL 且释义即题干**、
  都没有才退到 SELF（直接亮词面自评，不出空卡）。
- WXML 改为渲染统一的 `stem`，词面/语境按「已揭示 or SELF」控制显隐；揭示按钮
  对 RECALL 与 SPELL 都给（拼写卡也不能卡死在输入框上）。

本锁钉住三件事：纯函数在各种队列项下的判定、WXML 不再出现无题干分支、
以及 Node 里跑真代码验证（不是人眼看模板）。
"""

import os
import subprocess

import pytest

ROOT = "miniprogram"
CARD = os.path.join(ROOT, "utils", "review-card.js")
WXML = os.path.join(ROOT, "pages", "review", "review.wxml")
JS = os.path.join(ROOT, "pages", "review", "review.js")


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=os.getcwd(), capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


@pytest.mark.skipif(
    __import__("shutil").which("node") is None, reason="node is required")
def test_present_card_matrix():
    """各种队列项 → 呈现态与题干，逐项在 Node 里跑真代码。"""
    script = r"""
const { presentCard } = require(process.cwd() + '/miniprogram/utils/review-card.js');
const cases = [
  // RECALL + 释义：R290 的核心回归——题干必须是释义，不能是空串
  [{ questionType: 'RECALL', word: 'abandon', meaning: '放弃' }, 'RECALL', '放弃', false],
  // CHOOSE 有释义有选项：题干是释义，走四选一
  [{ questionType: 'CHOOSE', word: 'abandon', meaning: '放弃', choices: ['a','b','c','d'] }, 'CHOOSE', '放弃', false],
  // CHOOSE 选项不足：降级回忆，题干仍是释义（旧实现降级后连题干一起丢了）
  [{ questionType: 'CHOOSE', word: 'abandon', meaning: '放弃', choices: ['a'] }, 'RECALL', '放弃', false],
  // CHOOSE 缺释义：退到自评，不出空题
  [{ questionType: 'CHOOSE', word: 'abandon', choices: ['a','b','c','d'] }, 'SELF', '', false],
  // SPELL 有释义：题干是释义
  [{ questionType: 'SPELL', word: 'abandon', meaning: '放弃' }, 'SPELL', '放弃', false],
  // SPELL 缺释义：退到自评
  [{ questionType: 'SPELL', word: 'abandon' }, 'SELF', '', false],
  // CONTEXT_CLOZE：挖空句当题干，走挖空样式
  [{ questionType: 'CONTEXT_CLOZE', word: 'abandon', contextClozeSentence: 'He _____ the plan.' }, 'RECALL', 'He _____ the plan.', true],
  // CONTEXT_CLOZE 缺挖空句但有释义：题干回落释义
  [{ questionType: 'CONTEXT_CLOZE', word: 'abandon', meaning: '放弃' }, 'RECALL', '放弃', false],
  // 未知题型有释义：按回忆出题（不出死卡）
  [{ questionType: 'SOMETHING_NEW', word: 'abandon', meaning: '放弃' }, 'RECALL', '放弃', false],
  // 什么都没有：自评，题干为空但词面会亮
  [{ word: 'abandon' }, 'SELF', '', false],
  // 空白字符串的释义按缺失处理
  [{ questionType: 'RECALL', word: 'abandon', meaning: '   ' }, 'SELF', '', false],
];
const out = [];
for (const [card, mode, stem, cloze] of cases) {
  const got = presentCard(card);
  out.push({ input: card, got, expect: { mode, stem, cloze } });
}
const bad = out.filter(x => x.got.mode !== x.expect.mode || x.got.stem !== x.expect.stem || x.got.cloze !== x.expect.cloze);
if (bad.length) { console.error('MISMATCH', JSON.stringify(bad)); process.exit(1); }
if (!presentCard({ questionType: 'RECALL', meaning: '放弃' }).label) { console.error('NO_LABEL'); process.exit(2); }
process.stdout.write('MATRIX_OK');
"""
    assert "MATRIX_OK" in _node(script)


@pytest.mark.skipif(
    __import__("shutil").which("node") is None, reason="node is required")
def test_no_card_can_render_without_a_stem_or_the_word():
    """任何队列项都必须至少露出「题干」或「词面」之一，不许出现白板卡。"""
    script = r"""
const { presentCard } = require(process.cwd() + '/miniprogram/utils/review-card.js');
const cards = [
  { questionType: 'RECALL', word: 'w1', meaning: '释义' },
  { questionType: 'CHOOSE', word: 'w2', meaning: '释义', choices: ['a','b'] },
  { questionType: 'SPELL', word: 'w3', meaning: '释义' },
  { questionType: 'CONTEXT_CLOZE', word: 'w4', contextClozeSentence: 'x ___ y' },
  { questionType: 'RECALL', word: 'w5' },
  { word: 'w6' },
];
const bad = [];
for (const card of cards) {
  const p = presentCard(card);
  const wordVisibleAtStart = p.mode === 'SELF';
  if (!p.stem && !wordVisibleAtStart) bad.push({ card, p });
}
if (bad.length) { console.error('BLANK_CARD', JSON.stringify(bad)); process.exit(1); }
process.stdout.write('NO_BLANK');
"""
    assert "NO_BLANK" in _node(script)


def test_wxml_renders_stem_instead_of_a_hint_only_branch():
    wxml = _read(WXML)
    # 旧实现的「看下面的提示，回想这个词」是空题干的遮羞布，必须消失
    assert "看下面的提示" not in wxml
    # 题干只从 stem 渲染，且挖空句走 cloze 样式
    assert "{{stem}}" in wxml
    assert "stemCloze" in wxml
    # 题型标签取纯函数给的 label，不再写三元嵌套
    assert "{{modeLabel}}" in wxml
    # 揭示按钮对回忆与拼写都可用
    assert "mode === 'RECALL' || mode === 'SPELL'" in wxml
    # 词面与语境不得在揭示前泄题
    assert "mode === 'SELF' || revealed" in wxml


def test_page_uses_the_pure_presenter():
    js = _read(JS)
    assert "require('../../utils/review-card')" in js
    assert "reviewCard.presentCard(raw)" in js
    assert "function pickMode" not in js, "呈现态判定必须只在 utils/review-card.js 一处"
    assert "card.meaning" not in js, "题干渲染不得再散落在页面里"

/* global $, calibre */

/**
 * R183（架构评审 B4 批次 2）：单词详解面板（R123，与 magiclens v0.4.0 同构）独立模块。
 *
 * 六板块：基本意思 → 词源 → 搭配·用法·习语 → 变体衍生 → 同/反义词 → 俚语冷知识。
 * Why textContent 组装：内容来自 LLM，绝不进 innerHTML，杜绝注入。
 *
 * Why 单拆这一域：它是「划词气泡」下游最重的一块（217 行、面板生命周期与请求守卫都在
 * 这里），而气泡自身（B 节）与词形归一（C 节）还在 epub.js 里。两侧不能互相 import
 * IIFE 私有函数，所以由宿主在载入时注入三个回调（见 setHost）——面板对气泡的影响
 * （挂起 5s 自动隐藏、关闭后恢复倒计时）全部走这三个回调，模块不持有 DOM 之外的气泡状态。
 *
 * 载入顺序：i18n_seed → api.js → reader-core.js → 本文件 → epub.js（见 cps/templates/read.html）
 */
(function () {
    "use strict";

    var RC = window.ReaderCore;
    // R112: i18n 取词（种子缺失时回退 msgid 本身）
    var mbT = window.mbT || function (id) { return id; };

    // 宿主回调（epub.js 载入末尾注入）：词形归一口径与气泡自动隐藏的挂起/恢复
    var host = {
        normalizedWord: function (text) { return String(text || '').trim().toLowerCase(); },
        schedulePopoverHide: function () { },
        cancelAutoHide: function () { }
    };

    var wordDetailRequest = 0;
    var wordDetailPanel = null;

    function wdEl(tag, cls, text) {
        var el = document.createElement(tag);
        if (cls) el.className = cls;
        if (text !== undefined && text !== null) el.textContent = text;
        return el;
    }

    function wdSection(title) {
        var sec = wdEl('div', 'wd-sec');
        sec.appendChild(wdEl('h4', null, title));
        var ul = wdEl('ul');
        sec.appendChild(ul);
        return {sec: sec, ul: ul};
    }

    function closeWordDetailPanel() {
        wordDetailRequest++; // 在途响应作废，旧词慢响应不得覆盖新面板
        if (wordDetailPanel) {
            wordDetailPanel.remove();
            wordDetailPanel = null;
        }
        document.removeEventListener('keydown', closeWordDetailPanelOnEsc, true);
        // 面板存活期间气泡自动隐藏被挂起：关闭面板后恢复倒计时
        //（气泡已不在时宿主 schedulePopoverHide 内部会直接跳过，不会形成循环）
        host.schedulePopoverHide();
    }

    // R125：不再有点外关闭——面板是独立浮层，用户阅读/复制/点正文都不应误杀
    // 一趟 15~30s 的生成；关闭路径只有 ✕ 按钮与 Esc（捕获先于分层退出链）

    function closeWordDetailPanelOnEsc(ev) {
        if (ev.key === 'Escape') {
            // 捕获先于分层退出链：面板是最表层，本次 Esc 只关面板，
            // 阻断后续监听才不会连带收走划词气泡（一次 Esc 只关一层）
            ev.stopImmediatePropagation();
            closeWordDetailPanel();
        }
    }

    function appendWordDetailButton(popover, text) {
        var btn = wdEl('span', 'translation-detail', '详');
        btn.title = mbT('Word detail (etymology, phrases, forms…)');
        btn.addEventListener('click', function (ev) {
            ev.stopPropagation();
            openWordDetailPanel(host.normalizedWord(text), popover);
        });
        popover.appendChild(btn);
    }

    function openWordDetailPanel(word, anchor) {
        // Why 先清理再取序号：closeWordDetailPanel 会自增序号作废旧响应，
        // 若先取 seq 再清理，本请求的响应会被自己的守卫丢弃（审查 P0）
        closeWordDetailPanel();
        var seq = ++wordDetailRequest;
        var panel = wdEl('div', 'reading-word-detail');
        panel._anchor = anchor;
        var head = wdEl('div', 'wd-head');
        var wordEl = wdEl('span', 'wd-word', word);
        var tag = wdEl('span', 'wd-tag', mbT('variant'));
        tag.hidden = true;
        var closeBtn = wdEl('span', 'wd-close', '✕');
        closeBtn.title = mbT('Close');
        closeBtn.addEventListener('click', function (ev) {
            ev.stopPropagation();
            closeWordDetailPanel();
        });
        head.appendChild(wordEl);
        head.appendChild(tag);
        head.appendChild(closeBtn);
        var variantLine = wdEl('p', 'wd-variant');
        variantLine.hidden = true;
        var body = wdEl('div', 'wd-body');
        body.appendChild(wdEl('div', 'wd-msg',
            mbT('AI is generating… (first lookup takes 15-30s, the panel stays open and shows the result automatically)')));
        panel.appendChild(head);
        panel.appendChild(variantLine);
        panel.appendChild(body);
        document.body.appendChild(panel);
        wordDetailPanel = panel;
        positionWordDetailPanel();
        // 面板存活期间挂起气泡自动隐藏（30s 级生成与阅读不被 5s 倒计时收走）
        host.cancelAutoHide();
        // R125：仅 Esc 关闭（点外/新选区/翻页不再误关面板，关闭路径只有 ✕ 与 Esc）
        document.addEventListener('keydown', closeWordDetailPanelOnEsc, true);
        $.ajax({
            url: calibre.readingWordDetailUrl, method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': RC.csrfToken()},
            data: JSON.stringify({word: word})
        }).done(function (response) {
            if (seq !== wordDetailRequest || !wordDetailPanel) return;
            renderWordDetail(response.result || response.data || {}, word);
        }).fail(function (xhr) {
            // CSRF 过期/会话重建：刷新页面拿新 token，避免误导性报错
            if (RC.reloadIfCsrfBlocked(xhr)) return;
            if (seq !== wordDetailRequest || !wordDetailPanel) return;
            body.innerHTML = '';
            var errMsg = wdEl('div', 'wd-msg is-err', mbT('Failed to load detail, please retry later'));
            // R19/R125：非鉴权失败给点击重试（后端已缓存部分结果或下次命中）
            errMsg.style.cursor = 'pointer';
            errMsg.addEventListener('click', function () {
                openWordDetailPanel(word, anchor);
            });
            body.appendChild(errMsg);
        });
    }

    function positionWordDetailPanel() {
        if (!wordDetailPanel || !wordDetailPanel._anchor) return;
        var r = wordDetailPanel._anchor.getBoundingClientRect();
        var b = wordDetailPanel.getBoundingClientRect();
        var top = r.bottom + 8, left = r.left;
        if (top + b.height > window.innerHeight) top = Math.max(8, r.top - b.height - 8);
        left = Math.min(Math.max(8, left), window.innerWidth - b.width - 8);
        wordDetailPanel.style.top = top + 'px';
        wordDetailPanel.style.left = left + 'px';
    }

    function renderWordDetail(d, queriedWord) {
        if (!wordDetailPanel) return;
        var body = wordDetailPanel.querySelector('.wd-body');
        var tag = wordDetailPanel.querySelector('.wd-tag');
        var variantLine = wordDetailPanel.querySelector('.wd-variant');
        body.innerHTML = '';
        // 标题展示词目（lemma）：划的是变体（ran）时讲解主体是词目（run）
        wordDetailPanel.querySelector('.wd-word').textContent = d.lemma || d.word || queriedWord;
        if (d.isVariant) {
            tag.hidden = false;
            variantLine.hidden = !d.variantNote;
            variantLine.textContent = d.variantNote || '';
        }
        var arr = function (v) { return Array.isArray(v) ? v : []; };

        // 1 基本意思
        if (arr(d.meaning).length) {
            var ms = wdSection(mbT('Meaning'));
            arr(d.meaning).forEach(function (m) {
                var li = wdEl('li');
                if (m.pos) li.appendChild(wdEl('span', 'wd-pos', '【' + m.pos + '】'));
                li.appendChild(wdEl('span', 'wd-en', m.sense || ''));
                if (m.example) li.appendChild(wdEl('span', 'wd-note', '　' + m.example));
                ms.ul.appendChild(li);
            });
            body.appendChild(ms.sec);
        }
        // 2 词源（重点板块）
        if (d.etymology) {
            var es = wdSection(mbT('Etymology'));
            es.ul.appendChild(wdEl('li', null, d.etymology));
            body.appendChild(es.sec);
        }
        // 3 固定搭配 / 常见用法 / 习语
        if (arr(d.phrases).length) {
            var ps = wdSection(mbT('Phrases · Usage · Idioms'));
            arr(d.phrases).forEach(function (p) {
                var li = wdEl('li');
                if (p.kind) li.appendChild(wdEl('span', 'wd-pos', '【' + p.kind + '】'));
                li.appendChild(wdEl('span', 'wd-en', p.phrase || ''));
                if (p.meaning) li.appendChild(wdEl('span', 'wd-note', '　' + p.meaning));
                if (p.example) li.appendChild(wdEl('span', 'wd-note', '　' + p.example));
                ps.ul.appendChild(li);
            });
            body.appendChild(ps.sec);
        }
        // 4 变体与衍生词（不规则变化金色高亮）
        if (arr(d.forms).length) {
            var fs = wdSection(mbT('Forms & Derivatives'));
            var chips = wdEl('li');
            arr(d.forms).forEach(function (f) {
                var chip = wdEl('span', 'wd-chip' + (f.irregular ? ' is-irregular' : ''));
                chip.appendChild(wdEl('b', null, f.form || ''));
                if (f.type) chip.appendChild(document.createTextNode(' ' + f.type));
                chips.appendChild(chip);
            });
            fs.ul.appendChild(chips);
            body.appendChild(fs.sec);
        }
        // 5 同义词 / 反义词
        var wordList = function (title, list) {
            var s = wdSection(title);
            arr(list).forEach(function (w) {
                var li = wdEl('li');
                li.appendChild(wdEl('span', 'wd-en', w.word || ''));
                if (w.note) li.appendChild(wdEl('span', 'wd-note', '　' + w.note));
                s.ul.appendChild(li);
            });
            body.appendChild(s.sec);
        };
        if (arr(d.synonyms).length) wordList(mbT('Synonyms'), d.synonyms);
        if (arr(d.antonyms).length) wordList(mbT('Antonyms'), d.antonyms);
        // 6 俚语 / 冷知识
        if (arr(d.slang).length) {
            var sl = wdSection(mbT('Slang & Informal'));
            arr(d.slang).forEach(function (it) {
                var li = wdEl('li');
                li.appendChild(wdEl('span', 'wd-en', it.meaning || ''));
                if (it.example) li.appendChild(wdEl('span', 'wd-note', '　' + it.example));
                sl.ul.appendChild(li);
            });
            body.appendChild(sl.sec);
        }
        if (arr(d.funFacts).length) {
            var ff = wdSection(mbT('Fun Facts'));
            arr(d.funFacts).forEach(function (t) { ff.ul.appendChild(wdEl('li', null, t)); });
            body.appendChild(ff.sec);
        }
        if (!body.childElementCount) {
            body.appendChild(wdEl('div', 'wd-msg', mbT('No detail available')));
        }
        positionWordDetailPanel(); // 内容撑开面板后重新定位
    }

    window.ReaderWordDetail = {
        /** 宿主（epub.js）注入回调；未注入时走上面的安全兜底 */
        setHost: function (next) {
            if (next.normalizedWord) host.normalizedWord = next.normalizedWord;
            if (next.schedulePopoverHide) host.schedulePopoverHide = next.schedulePopoverHide;
            if (next.cancelAutoHide) host.cancelAutoHide = next.cancelAutoHide;
        },
        appendButton: appendWordDetailButton,
        open: openWordDetailPanel,
        close: closeWordDetailPanel,
        closeOnEsc: closeWordDetailPanelOnEsc,
        position: positionWordDetailPanel,
        render: renderWordDetail,
        isOpen: function () { return !!wordDetailPanel; },
        containsNode: function (node) { return !!(wordDetailPanel && node && wordDetailPanel.contains(node)); }
    };
})();

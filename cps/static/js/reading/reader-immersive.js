/* global $, calibre, reader */

/**
 * R183（架构评审 B4 批次 5）：沉浸式翻译。
 * R215（MB-14）：译文从「正文流内逐段插入」改为「右侧译文栏」——分页列布局下
 * 任何流内高度变化都会触发 epub.js 重分页，插占位只能减少次数、不能消除抖动；
 * 右栏在 iframe 外，翻译到达零重排。交互同步改为「开关即翻译模式，点正文段落选中」。
 *
 * 载入顺序：i18n_seed → api.js → reader-core.js → reader-word-detail.js →
 * reader-annotations.js → reader-selection.js → 本文件 → epub.js
 */
(function () {
    "use strict";

    var RC = window.ReaderCore;
    var RS = window.ReaderSelection;
    var mbT = window.mbT || function (id) { return id; };

    // R215：新键与旧「整页批量翻译」语义区分；旧键只清理、不读取
    var RAIL_MODE_KEY = "calibre.reader.translationRailMode";
    var LEGACY_TRANSLATE_KEY = "calibre.reader.immersiveTranslate";
    var TRANSLATION_CACHE_MAX = 500;

    // 宿主回调：本域与两种「整段音频播放」互斥（翻译段落时先停播放并刷新它们的按钮），
    // 且需要章标题做译文缓存键；这些都由 epub.js 在 setHost 时注入。
    var host = {
        bookPlayerStop: function () { },
        bookPlayerUpdateButtons: function () { },
        tedAudioStop: function () { },
        tedAudioUpdateButtons: function () { },
        tedAudioEnsureLoaded: function () { return Promise.resolve(); },
        tedAudioActive: function () { return false; },
        bookListenToggle: function () { },
        isTedBook: function () { return false; },
        currentChapterTitle: function () { return ''; }
    };

    // core / selection 同名别名：正文与 epub.js 时代逐字一致，静态锁继续成立
    var readerCsrfToken = function () { return RC.csrfToken(); };
    var reloadIfCsrfBlocked = function (x) { return RC.reloadIfCsrfBlocked(x); };
    var paragraphSpeechText = function (el) { return RC.paragraphSpeechText(el); };
    var readerToast = function (m) { RC.toast(m); };

    // --- 状态 ---
    var railMode = false;
    var selectedEl = null;
    var selectedText = '';
    var railRequestSeq = 0;

    function railModeEnabled() {
        try { return localStorage.getItem(RAIL_MODE_KEY) === 'true'; } catch (e) { return false; }
    }

    function translationCacheKey() {
        return 'calibre.reader.translation.' + reader.book.key();
    }

    function loadTranslationCache() {
        try {
            return JSON.parse(localStorage.getItem(translationCacheKey()) || '{}') || {};
        } catch (e) { return {}; }
    }

    function saveTranslationCache(cache) {
        try {
            var keys = Object.keys(cache);
            // 超限时淘汰最早写入的条目（对象键序即插入序）
            for (var i = 0; i < keys.length - TRANSLATION_CACHE_MAX; i++) delete cache[keys[i]];
            localStorage.setItem(translationCacheKey(), JSON.stringify(cache));
        } catch (e) {}
    }

    function paragraphHash(text) {
        var hash = 5381;
        for (var i = 0; i < text.length; i++) {
            hash = ((hash << 5) + hash) + text.charCodeAt(i);
            hash = hash & 0x7fffffff;
        }
        return hash.toString(36);
    }

    // --- 译文栏 DOM 与面板互斥 ---
    function railParts() {
        return {
            rail: document.getElementById('translation-rail'),
            source: document.getElementById('translation-rail-source'),
            body: document.getElementById('translation-rail-body')
        };
    }

    function requestRepagination() {
        // 宽度落定后再让 epub.js 重分页一次：它监听 window resize
        window.requestAnimationFrame(function () {
            setTimeout(function () {
                window.dispatchEvent(new Event('resize'));
            }, 0);
        });
    }

    function setRailBody(text, state) {
        var parts = railParts();
        if (!parts.body) return;
        parts.body.className = 'translation-rail-body' + (state ? ' is-' + state : '');
        parts.body.textContent = text || '';
    }

    function setRailSource(text) {
        var parts = railParts();
        if (!parts.source) return;
        parts.source.textContent = text || '';
        parts.source.title = text || '';
    }

    function openRail() {
        var parts = railParts();
        if (!parts.rail) return;
        // 已开着就只更新内容：每次选段都重设 dataset + resize 会让 epub.js
        // 重分页，正文在选段时跳动，正好违背本单的验收口径。
        var alreadyOpen = !parts.rail.hidden
            && document.body.getAttribute('data-side-panel') === 'translation';
        parts.rail.hidden = false;
        parts.rail.setAttribute('aria-hidden', 'false');
        if (!parts.body.textContent) {
            setRailBody(mbT('Click a paragraph to see its translation'), 'empty');
        }
        if (alreadyOpen) return;
        document.body.setAttribute('data-side-panel', 'translation');
        document.dispatchEvent(new CustomEvent('reader:panel-open', {detail: {kind: 'translation'}}));
        requestRepagination();
    }

    // 只收起栏面，保留翻译模式（AI 面板抢占右侧时使用；不派发 close，避免回环）
    function hideRailOnly() {
        var parts = railParts();
        if (!parts.rail) return;
        var wasOpen = !parts.rail.hidden;
        var cleared = document.body.getAttribute('data-side-panel') === 'translation';
        parts.rail.hidden = true;
        parts.rail.setAttribute('aria-hidden', 'true');
        if (cleared) document.body.removeAttribute('data-side-panel');
        // 若 AI 已先把 dataset 改成 ai，宽度变化由 AI 自己触发一次重分页，这里不重复
        if (wasOpen && cleared) requestRepagination();
    }

    function closeRail() {
        hideRailOnly();
        document.dispatchEvent(new CustomEvent('reader:panel-close', {detail: {kind: 'translation'}}));
    }

    function clearSelection() {
        if (selectedEl) selectedEl.classList.remove('reading-para-selected');
        selectedEl = null;
        selectedText = '';
        railRequestSeq++;
        setRailSource('');
    }

    function updateTranslateToggle() {
        var toggle = document.getElementById('immersive-translate');
        if (!toggle) return;
        toggle.classList.toggle('active', railMode);
        toggle.setAttribute('aria-pressed', railMode ? 'true' : 'false');
        var label = toggle.querySelector('.tb-label');
        if (label) label.textContent = railMode ? mbT('Translation mode') : mbT('Translation');
    }

    function setRailMode(on) {
        railMode = !!on;
        try { localStorage.setItem(RAIL_MODE_KEY, String(railMode)); } catch (e) {}
        updateTranslateToggle();
        if (railMode) {
            openRail();
            readerToast(mbT('Translation mode enabled: click a paragraph to see its translation'));
        } else {
            clearSelection();
            closeRail();
            setRailBody('', '');
            readerToast(mbT('Translation mode disabled'));
        }
    }

    // --- 译文请求 ---
    function upstreamErrorText(xhr) {
        try {
            var data = JSON.parse(xhr && xhr.responseText || "");
            return (data && (data.message || data.error)) || ("HTTP " + (xhr && xhr.status));
        } catch (e) {
            return "HTTP " + (xhr && xhr.status);
        }
    }

    function renderRetry(text) {
        var parts = railParts();
        if (!parts.body) return;
        parts.body.className = 'translation-rail-body is-error';
        parts.body.textContent = text + ' ';
        var retry = document.createElement('button');
        retry.type = 'button';
        retry.className = 'translation-rail-retry';
        retry.textContent = mbT('Retry');
        retry.addEventListener('click', function () {
            if (selectedEl ? selectedEl.isConnected : false) {
                requestTranslation(selectedEl, selectedText);
            } else {
                setRailBody(mbT('The selected paragraph is no longer on this page'), 'error');
            }
        });
        parts.body.appendChild(retry);
    }

    function requestTranslation(el, text) {
        var seq = ++railRequestSeq;
        setRailBody(mbT('Translating…'), 'loading');
        if (!calibre.readingTranslateBatchUrl) {
            renderRetry(mbT('Translation is unavailable for this book'));
            return;
        }
        $.ajax({
            url: calibre.readingTranslateBatchUrl,
            method: 'POST',
            contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({
                paragraphs: [text],
                bookName: calibre.bookName || '',
                chapter: host.currentChapterTitle()
            })
        }).done(function (response) {
            var translation = ((response.result || response.data || [])[0] || '').trim();
            if (seq !== railRequestSeq || el !== selectedEl) return;
            if (!translation) {
                renderRetry(mbT('Translation failed, click to retry'));
                return;
            }
            var cache = loadTranslationCache();
            cache[paragraphHash(text)] = translation;
            saveTranslationCache(cache);
            if (el.isConnected) {
                setRailBody(translation, '');
            } else {
                setRailBody(translation + '\n\n' + mbT('The selected paragraph is no longer on this page'), '');
            }
        }).fail(function (xhr) {
            if (seq !== railRequestSeq || el !== selectedEl) return;
            if (reloadIfCsrfBlocked(xhr)) return;
            // B5：必须把上游错误原文露出来，不能静默降级成通用文案
            renderRetry(mbT('Translation failed, retry later') + "：" + upstreamErrorText(xhr));
        });
    }

    function selectParagraph(el) {
        var text = paragraphSpeechText(el);
        if (!text) return;
        if (!railMode) {
            // 段尾「译」在模式外也能用：先进入模式，但不要在这里重复 openRail
            railMode = true;
            try { localStorage.setItem(RAIL_MODE_KEY, 'true'); } catch (e) {}
            updateTranslateToggle();
        }

        if (selectedEl) selectedEl.classList.remove('reading-para-selected');
        selectedEl = el;
        selectedText = text;
        el.classList.add('reading-para-selected');
        setRailSource(text.length > 40 ? text.slice(0, 40) + '…' : text);
        openRail();

        var cached = loadTranslationCache()[paragraphHash(text)];
        if (typeof cached === 'string' && cached) {
            railRequestSeq++;
            setRailBody(cached, '');
            return;
        }
        requestTranslation(el, text);
    }

    // 兼容既有调用面：段落「译」按钮与触屏菜单都走这里；不再在正文内插任何节点
    function translateParagraph(el, btn) {
        if (!el || !el.isConnected) return;
        if (btn) btn.classList.remove('is-loading');
        selectParagraph(el);
    }

    // epub.js 在每个 rendered 的 iframe 上调用：翻译模式下单击段落即选中
    function bindContent(content) {
        var doc = content && content.document;
        if (!doc || !doc.body) return;
        if (doc.__r215TranslateBound) return;
        doc.__r215TranslateBound = true;
        doc.addEventListener('click', function (event) {
            if (!railMode) return;
            var win = content.window || doc.defaultView;
            var selection = win && win.getSelection ? win.getSelection() : null;
            if (selection && String(selection.toString() || '').trim()) return;
            var target = event.target;
            if (!target || !target.closest) return;
            // 链接、工具按钮、译文节点都不触发段落翻译
            if (target.closest('a, button, .reading-para-tools, .reading-para-btn, .reading-para-menu-btn, .reading-translation')) return;
            var el = target.closest(RC.PARAGRAPH_SELECTOR);
            if (!el) return;
            // div 只取无块级子元素的叶子段落（与 ReaderCore.collectParagraphs 同口径）
            if (el.tagName === 'DIV' && el.querySelector(RC.BLOCK_CHILD_SELECTOR)) return;
            if (!(el.textContent || '').trim()) return;
            selectParagraph(el);
        });
    }

    // 工具栏「翻译」开关：开 = 打开右栏并进入点段翻译模式；关 = 收起右栏并清除选中
    function bindToolbar() {
        var translateToggle = document.getElementById('immersive-translate');
        if (translateToggle) {
            translateToggle.addEventListener('click', function () {
                setRailMode(!railMode);
            });
        }
        var railClose = document.getElementById('translation-rail-close');
        if (railClose) {
            railClose.addEventListener('click', function () {
                if (railMode) setRailMode(false);
                else closeRail();
            });
        }
        var wholeBookToggle = document.getElementById('whole-book-translate');
        if (wholeBookToggle) wholeBookToggle.addEventListener('click', RS.startWholeBookTranslation);

        // ESC 只关译文栏（AI 抽屉有自己的分层 ESC；两者互斥，不会同开）
        document.addEventListener('keydown', function (event) {
            if (event.key !== 'Escape' || !railMode) return;
            if (document.body.getAttribute('data-side-panel') !== 'translation') return;
            setRailMode(false);
        });

        // 面板互斥：AI 打开 → 只收起栏面（保留模式）；AI 关闭 → 恢复栏面
        document.addEventListener('reader:panel-open', function (event) {
            if (event.detail && event.detail.kind === 'ai') hideRailOnly();
        });
        document.addEventListener('reader:panel-close', function (event) {
            if (event.detail && event.detail.kind === 'ai' && railMode) openRail();
        });
    }

    // R157 整本连播按钮：■ 停止（绑定与宿主状态无关，点击时才读 host）
    var ttsBookStopBtn = document.getElementById('tts-book-stop');
    if (ttsBookStopBtn) {
        ttsBookStopBtn.addEventListener('click', function () {
            if (host.tedAudioActive()) host.tedAudioStop();
            else host.bookPlayerStop(false);
        });
    }

    // 原 epub.js 里本域末尾的载入期副作用（探测 TED 原声、刷新两种播放器的按钮语义）。
    // Why 不在模块 IIFE 里直接跑：那一刻宿主回调还没注入（setHost 发生在 epub.js 执行时），
    // 直接跑会变成静默的空操作——起播零等待的原声探测悄悄不做了，界面上只是「第一次播有点慢」。
    // 必须由 epub.js 在 setHost 之后显式 init()。
    function init() {
        try { localStorage.removeItem(LEGACY_TRANSLATE_KEY); } catch (e) {}
        bindToolbar();

        var ttsBookBtn = document.getElementById('tts-book');
        // #tts-book 的分流判据来自运行时探测（R172/R173），处理函数是 J 节的 bookListenToggle；
        // 绑定必须发生在 setHost 之后，否则永久绑成宿主默认空函数——按钮变成点了没反应
        if (ttsBookBtn) ttsBookBtn.addEventListener('click', host.bookListenToggle);
        host.bookPlayerUpdateButtons();
        host.tedAudioEnsureLoaded().then(function () {
            if (host.isTedBook()) host.tedAudioUpdateButtons();
        }).catch(function () {});

        // 恢复上次的翻译模式（只开栏，不自动翻任何段落）
        if (railModeEnabled()) {
            railMode = true;
            updateTranslateToggle();
            openRail();
        } else {
            updateTranslateToggle();
        }
    }

    window.ReaderImmersive = {
        setHost: function (next) {
            Object.keys(next).forEach(function (k) { if (next[k]) host[k] = next[k]; });
        },
        init: init,
        enabled: railModeEnabled,
        translateParagraph: translateParagraph,
        bindContent: bindContent
    };
})();

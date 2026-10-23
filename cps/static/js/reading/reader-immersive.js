/* global $, calibre */

/**
 * R183（架构评审 B4 批次 5）：沉浸式翻译（整本/逐段译文插入、缓存、显隐与重试）。
 *
 * R215 验收回滚（2026-10-23）：右侧译文栏方案被用户否决，恢复「译文直接插入
 * 段落下方」的形态；用户明确接受由此带来的 epub.js 重分页抖动。本文件回到
 * R183 实现，不再包含右栏/点段选中逻辑。
 *
 * 载入顺序：i18n_seed → api.js → reader-core.js → reader-word-detail.js →
 * reader-annotations.js → reader-selection.js → 本文件 → epub.js
 */
(function () {
    "use strict";

    var RC = window.ReaderCore;
    var RS = window.ReaderSelection;
    var mbT = window.mbT || function (id) { return id; };

    var TRANSLATE_ENABLED_KEY = "calibre.reader.immersiveTranslate";
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
    var collectParagraphElements = function (doc) { return RC.collectParagraphs(doc); };
    var translationDisplaySecondsFor = function (t) { return RC.translationDisplaySecondsFor(t); };
    var readerToast = function (m) { RC.toast(m); };
    // --- 沉浸式翻译 ---
    var translationInFlight = false;
    var translationRetryPending = false;

    function translationEnabled() {
        try { return localStorage.getItem(TRANSLATE_ENABLED_KEY) === 'true'; } catch (e) { return false; }
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
            hash = ((hash << 5) + hash + text.charCodeAt(i)) & 0x7fffffff;
        }
        return hash.toString(36);
    }

    function translationSibling(el) {
        var next = el.nextElementSibling;
        return (next && next.classList && next.classList.contains('reading-translation')) ? next : null;
    }

    function insertTranslation(el, text, extraClass) {
        var existing = translationSibling(el);
        if (existing) existing.remove();
        var doc = el.ownerDocument;
        var div = doc.createElement('div');
        div.className = 'reading-translation' + (extraClass ? ' ' + extraClass : '');
        div.textContent = text;
        el.parentNode.insertBefore(div, el.nextSibling);
        // 仅对最终译文计时自动隐藏；loading/error 中间态会被替换或需点击重试，不计时
        if (extraClass !== 'is-loading' && extraClass !== 'is-error') scheduleTranslationHide(div, el);
        return div;
    }

    // 译文块自动消失：显示时长按所在段落原文的词数折算，到点移除并复位段落
    // 「译」按钮（可再点重出，命中缓存即时显示）。定时器挂在块自身，配置修改
    // 时可清除重排；块已被动删除（手动取消/被替换）时触发为 no-op。
    function scheduleTranslationHide(div, el) {
        if (div._hideTimer) { clearTimeout(div._hideTimer); div._hideTimer = null; }
        var seconds = el ? translationDisplaySecondsFor(paragraphSpeechText(el)) : 0;
        if (!seconds) return;
        div._hideTimer = setTimeout(function () {
            div._hideTimer = null;
            if (!div.isConnected) return;
            div.remove();
            if (el) setParagraphTranslated(el, false);
        }, seconds * 1000);
    }

    // 配置修改后：已显示的译文（含划词气泡）立即按新时长重新计时
    function rescheduleVisibleTranslations() {
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            Array.prototype.slice.call(doc.querySelectorAll('.reading-translation'))
                .forEach(function (div) {
                    if (div.classList.contains('is-loading') || div.classList.contains('is-error')) return;
                    scheduleTranslationHide(div, div.previousElementSibling);
                });
        });
        if (RS.isPopoverOpen()) RS.scheduleHide();
    }

    function removeAllTranslations() {
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            Array.prototype.slice.call(doc.querySelectorAll('.reading-translation'))
                .forEach(function (el) { el.remove(); });
            Array.prototype.slice.call(doc.querySelectorAll('.reading-translate-btn.is-done'))
                .forEach(function (el) { el.classList.remove('is-done'); });
        });
    }

    function setParagraphTranslated(el, on) {
        var btn = el.querySelector(':scope > .reading-translate-btn');
        if (btn) btn.classList.toggle('is-done', !!on);
    }

    // iframe 内容是 CSS 分栏：与 iframe 视口相交的段落即当前可见页
    function isElementVisible(el, win) {
        try {
            var rect = el.getBoundingClientRect();
            return rect.bottom > 0 && rect.top < win.innerHeight &&
                   rect.right > 0 && rect.left < win.innerWidth;
        } catch (e) { return false; }
    }

    function showTranslationError(el, text) {
        setParagraphTranslated(el, false);
        var div = insertTranslation(el, mbT('Translation failed, click to retry'), 'is-error');
        div.addEventListener('click', function () {
            div.remove();
            translateSingleParagraph(el, text);
        });
    }

    function translateSingleParagraph(el, text) {
        var btn = el.querySelector(':scope > .reading-translate-btn');
        if (btn) btn.classList.add('is-loading');
        insertTranslation(el, mbT('Translating…'), 'is-loading');
        $.ajax({
            url: calibre.readingTranslateBatchUrl,
            method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({paragraphs: [text], bookName: calibre.bookName || '',
                chapter: host.currentChapterTitle()})
        }).done(function (response) {
            var translation = ((response.result || response.data || [])[0] || '').trim();
            if (translation) {
                insertTranslation(el, translation);
                setParagraphTranslated(el, true);
                var cache = loadTranslationCache();
                cache[paragraphHash(text)] = translation;
                saveTranslationCache(cache);
            } else {
                showTranslationError(el, text);
            }
}).fail(function (xhr) {
            if (reloadIfCsrfBlocked(xhr)) return;
            showTranslationError(el, text);
        }).always(function () {
            if (btn) btn.classList.remove('is-loading');
        });
    }

    // 段落级「译」按钮：单击翻译本段（优先命中缓存），已有译文时再点一次取消
    function translateParagraph(el, btn) {
        if (btn.classList.contains('is-loading')) return;
        var sibling = translationSibling(el);
        if (sibling && !sibling.classList.contains('is-loading')) {
            sibling.remove();
            setParagraphTranslated(el, false);
            return;
        }
        if (sibling) return;
        var text = paragraphSpeechText(el);
        if (!text) return;
        var cached = loadTranslationCache()[paragraphHash(text)];
        if (typeof cached === 'string' && cached) {
            insertTranslation(el, cached);
            setParagraphTranslated(el, true);
            return;
        }
        translateSingleParagraph(el, text);
    }

    // 翻页/新章节渲染后仅回填已缓存的译文（不发 LLM 请求）；
    // 翻译由段落按钮或工具栏「译」手动触发，避免整页批量请求卡顿
    function restoreCachedTranslations() {
        var cache = loadTranslationCache();
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            collectParagraphElements(doc).forEach(function (el) {
                if (translationSibling(el)) return;
                var text = paragraphSpeechText(el);
                if (!text) return;
                var cached = cache[paragraphHash(text)];
                if (typeof cached === 'string' && cached) {
                    insertTranslation(el, cached);
                    setParagraphTranslated(el, true);
                }
            });
        });
    }

    // 并发池：同一时刻最多 limit 个任务飞行，每个任务完成后立即启动下一个
    function runConcurrent(items, limit, worker) {
        var index = 0;
        function launch() {
            if (index >= items.length) return;
            var item = items[index++];
            worker(item, launch);
        }
        for (var i = 0; i < Math.min(limit, items.length); i++) launch();
    }

    // 整页翻译的单段任务（复用批量接口，段落数为 1）：带书籍上下文，
    // 响应到达即渲染并写缓存，失败仅影响该段
    function translateParagraphJob(job, cache, chapter, onDone) {
        $.ajax({
            url: calibre.readingTranslateBatchUrl,
            method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({paragraphs: [job.text], bookName: calibre.bookName || '',
                chapter: chapter})
        }).done(function (response) {
            var translation = ((response.result || response.data || [])[0] || '').trim();
            if (translation) {
                cache[job.hash] = translation;
                saveTranslationCache(cache);
                insertTranslation(job.el, translation);
                setParagraphTranslated(job.el, true);
            } else {
                showTranslationError(job.el, job.text);
            }
        }).fail(function (xhr) {
            if (!reloadIfCsrfBlocked(xhr)) showTranslationError(job.el, job.text);
        }).always(onDone);
    }

    function applyImmersiveTranslation() {
        if (!translationEnabled() || !calibre.readingTranslateBatchUrl) return;
        if (translationInFlight) { translationRetryPending = true; return; }
        var cache = loadTranslationCache();
        var jobs = [];
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            var win = content.window || doc.defaultView;
            collectParagraphElements(doc).forEach(function (el) {
                if (translationSibling(el)) return;
                var text = paragraphSpeechText(el);
                if (!text) return;
                var cached = cache[paragraphHash(text)];
                if (typeof cached === 'string' && cached) {
                    insertTranslation(el, cached);
                    setParagraphTranslated(el, true);
                    return;
                }
                if (isElementVisible(el, win) && jobs.length < 20) {
                    jobs.push({el: el, text: text, hash: paragraphHash(text)});
                }
            });
        });
        if (!jobs.length) return;

        translationInFlight = true;
        var chapter = host.currentChapterTitle();
        var remaining = jobs.length;
        jobs.forEach(function (job) { insertTranslation(job.el, mbT('Translating…'), 'is-loading'); });
        // 逐段并发（限 4）：每段一个请求，翻译到达即显示，避免整页单请求的长时间卡顿
        runConcurrent(jobs, 4, function (job, done) {
            translateParagraphJob(job, cache, chapter, function () {
                done();
                remaining--;
                if (remaining) return;
                translationInFlight = false;
                if (translationRetryPending) {
                    translationRetryPending = false;
                    setTimeout(applyImmersiveTranslation, 50);
                }
            });
        });
    }

    // 工具栏「译」：开启 = 批量翻译当前可见页（全部翻译），关闭 = 移除所有译文。
    // 不再随翻页自动触发，避免整页 LLM 请求卡顿。
    var translateToggle = document.getElementById('immersive-translate');
    function updateTranslateToggle() {
        if (translateToggle) translateToggle.classList.toggle('active', translationEnabled());
    }
    if (translateToggle) {
        translateToggle.addEventListener('click', function () {
            var enabled = !translationEnabled();
            try { localStorage.setItem(TRANSLATE_ENABLED_KEY, String(enabled)); } catch (e) {}
            updateTranslateToggle();
            if (enabled) applyImmersiveTranslation();
            else removeAllTranslations();
        });
        updateTranslateToggle();
        // 打开阅读器时若开关已开启：只回填已缓存的译文
        if (translationEnabled()) setTimeout(restoreCachedTranslations, 200);
    }
    var wholeBookToggle = document.getElementById('whole-book-translate');
    if (wholeBookToggle) wholeBookToggle.addEventListener('click', RS.startWholeBookTranslation);

    // R157 整本连播按钮：▶/❚❚ 起播暂停切换，■ 停止；依赖 moon-well TTS 代理，
    // 未配置（readingTtsUrl 缺失）时隐藏（单段朗读有浏览器兜底，连播没有）。
    // R172：同一个按钮在「探测到整段原声」的书上改接原声伴听（TED/博客类），不再走 TTS
    // 逐段合成——TED 是整段真人原声，逐段合成会把原声换成机器音。分流判据只能运行时探测
    // （calibre.bookFormat 是 Calibre 文件格式，见 TED_BOOK 定义处），故点击统一走 bookListenToggle。
    var ttsBookBtn = document.getElementById('tts-book');
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
        // #tts-book 的分流判据来自运行时探测（R172/R173），处理函数是 J 节的 bookListenToggle；
        // 绑定必须发生在 setHost 之后，否则永久绑成宿主默认空函数——按钮变成点了没反应
        if (ttsBookBtn) ttsBookBtn.addEventListener('click', host.bookListenToggle);
        host.bookPlayerUpdateButtons();
        host.tedAudioEnsureLoaded().then(function () {
            if (host.isTedBook()) host.tedAudioUpdateButtons();
        }).catch(function () {});
    }

    window.ReaderImmersive = {
        setHost: function (next) {
            Object.keys(next).forEach(function (k) { if (next[k]) host[k] = next[k]; });
        },
        init: init,
        enabled: translationEnabled,
        translateParagraph: translateParagraph,
        rescheduleVisibleTranslations: rescheduleVisibleTranslations,
        restoreCachedTranslations: restoreCachedTranslations,
        removeAllTranslations: removeAllTranslations
    };
})();

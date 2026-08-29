/* global $, calibre, EPUBJS, ePubReader */

var reader;

(function () {
    "use strict";

    EPUBJS.filePath = calibre.filePath;
    EPUBJS.cssPath = calibre.cssPath;

    reader = ePubReader(calibre.bookUrl, {
        restore: true,
        bookmarks: calibre.bookmark ? [calibre.bookmark] : [],
    });

    Object.keys(themes).forEach(function (theme) {
        reader.rendition.themes.register(theme, themes[theme].css_path);
    });

    if (calibre.useBookmarks) {
        reader.on("reader:bookmarked", updateBookmark.bind(reader, "add"));
        reader.on("reader:unbookmarked", updateBookmark.bind(reader, "remove"));
    } else {
        $("#bookmark, #show-Bookmarks").remove();
    }

    // Enable swipe support
    // I have no idea why swiperRight/swiperLeft from plugins is not working, events just don't get fired
    var touchStart = 0;
    var touchEnd = 0;

    reader.rendition.on('touchstart', function(event) {
        touchStart = event.changedTouches[0].screenX;
    });
    reader.rendition.on('touchend', function(event) {
      touchEnd = event.changedTouches[0].screenX;
        if (touchStart < touchEnd) {
            if(reader.book.package.metadata.direction === "rtl") {
    			reader.rendition.next();
    		} else {
    			reader.rendition.prev();
    		}
            // Swiped Right
        }
        if (touchStart > touchEnd) {
            if(reader.book.package.metadata.direction === "rtl") {
    			reader.rendition.prev();
    		} else {
                reader.rendition.next();
    		}
            // Swiped Left
        }
    });

    // Update progress percentage
    let progressDiv = document.getElementById("progress");
    // Pages counter (virtual pages via EPUB locations)
    let pagesDiv = document.getElementById("pages-count");
    // Honor saved visibility preference for pages counter
    (function () {
        try {
            var pref = localStorage.getItem("calibre.reader.showPages");
            var show = pref === null ? true : pref === "true";
            if (pagesDiv)
                pagesDiv.style.visibility = show ? "visible" : "hidden";
        } catch (e) {}
    })();

    reader.book.ready.then(() => {
        let locations_key = reader.book.key() + "-locations";
        // Key to persist last-read position for this book in localStorage
        let position_key = "calibre.reader.position." + reader.book.key();
        let stored_locations = localStorage.getItem(locations_key);
        let make_locations, save_locations;
        if (stored_locations) {
            make_locations = Promise.resolve(
                reader.book.locations.load(stored_locations)
            );
            // No-op because locations are already saved
            save_locations = () => {};
        } else {
            make_locations = reader.book.locations.generate();
            save_locations = () => {
                localStorage.setItem(
                    locations_key,
                    reader.book.locations.save()
                );
            };
        }
        make_locations
            .then(() => {
                // Try to restore last position (CFI) from localStorage if present
                try {
                    var _savedPos = localStorage.getItem(position_key);
                    if (_savedPos) {
                        try {
                            var _posObj = JSON.parse(_savedPos);
                            if (_posObj && _posObj.cfi) {
                                // Display the saved CFI location
                                try {
                                    reader.rendition.display(_posObj.cfi);
                                } catch (e) {}
                            }
                        } catch (e) {}
                    }
                } catch (e) {}

                reader.rendition.on("relocated", (location) => {
                    let percentage = Math.round(location.end.percentage * 100);
                    progressDiv.textContent = percentage + "%";

                    // Pages based on generated EPUB locations (CFI positions)
                    const cfi = location.start.cfi;
                    const current =
                        reader.book.locations.locationFromCfi(cfi) || 0; // 1-based index typically
                    const total = reader.book.locations.length() || 0;

                    if (total > 0) {
                        pagesDiv.textContent = current + "/" + total;
                        pagesDiv.style.visibility = "visible";
                    } else {
                        pagesDiv.textContent = "";
                        pagesDiv.style.visibility = "hidden";
                    }

                    // Persist last position (CFI + percentage) to localStorage so reader can restore on next open
                    try {
                        var posObj = {
                            cfi: location.start.cfi,
                            percentage: location.start.percentage,
                        };
                        localStorage.setItem(
                            position_key,
                            JSON.stringify(posObj)
                        );
                    } catch (e) {}
                });
                reader.rendition.reportLocation();
                progressDiv.style.visibility = "visible";
            })
            .then(save_locations);
    });

    // Mark unfamiliar words in the currently visible EPUB document and show their history.
    var vocabularyInFlight = false;
// 翻页时若上一请求仍在飞行，标记待重检；请求完成后重新检查当前页，
    // 避免新页面因 inFlight 短路而漏标生词。
    var vocabularyRetryPending = false;
    // word -> latest record returned by moon-well, kept across page turns so that
    // re-rendered pages (going back to a previously read page) can be re-marked.
    var vocabularyRecords = {};
    // 最近一次已成功提交的页面文本签名；翻回已读页（文本相同）时直接复用
    // 缓存 records 标注，不再重复请求 moon-well。
    var lastPageTextSignature = null;

    // 从导航目录中按 href 文件名递归匹配章节标题。
    function findTocLabel(items, href) {
        var target = (href || '').split('/').pop();
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            if ((item.href || '').split('/').pop() === target) return item.label;
            if (item.subitems && item.subitems.length) {
                var label = findTocLabel(item.subitems, href);
                if (label) return label;
            }
        }
        return '';
    }

    // 划词翻译：选中文本弹出翻译气泡（来自 master 分支功能）。
    var translationRequest = 0;
    var translationPopover;

    function closeTranslationPopover() {
        if (translationPopover) {
            translationPopover.remove();
            translationPopover = null;
        }
    }

    function showTranslationPopover(text, rect, loading) {
        closeTranslationPopover();
        translationPopover = document.createElement('div');
        translationPopover.className = 'reading-translation-popover' + (loading ? ' is-loading' : '');
        translationPopover.textContent = loading ? '翻译中…' : text;
        document.body.appendChild(translationPopover);
        var top = rect.bottom + 8, left = rect.left;
        var bounds = translationPopover.getBoundingClientRect();
        if (top + bounds.height > window.innerHeight) top = Math.max(8, rect.top - bounds.height - 8);
        left = Math.min(Math.max(8, left), window.innerWidth - bounds.width - 8);
        translationPopover.style.top = top + 'px';
        translationPopover.style.left = left + 'px';
        return translationPopover;
    }

    function translateSelection(content) {
        if (!calibre.readingVocabularyEnabled || !calibre.readingTranslationUrl) return;
        var selection = content.window.getSelection();
        var text = selection && selection.toString().replace(/\s+/g, ' ').trim();
        if (!text || text.length > 2000) return;
        var range = selection.getRangeAt(0), rect = range.getBoundingClientRect();
        if (!rect.width && !rect.height) return;
        var frame = content.window.frameElement;
        if (frame) {
            var frameRect = frame.getBoundingClientRect();
            rect = {top: rect.top + frameRect.top, bottom: rect.bottom + frameRect.top,
                left: rect.left + frameRect.left, width: rect.width, height: rect.height};
        }
        var requestId = ++translationRequest;
        var popover = showTranslationPopover('', rect, true);
        var context = range.commonAncestorContainer.parentElement &&
            range.commonAncestorContainer.parentElement.textContent || text;
        $.ajax({
            url: calibre.readingTranslationUrl, method: 'POST', contentType: 'application/json',
            data: JSON.stringify({text: text, context: context.slice(0, 2000)})
        }).done(function (response) {
            if (requestId !== translationRequest || !translationPopover) return;
            var result = response.result || response.data || {};
            popover.classList.remove('is-loading');
            popover.textContent = result.translation || '暂无翻译';
            if (result.source) {
                var source = document.createElement('div');
                source.className = 'translation-source';
                source.textContent = result.source === 'dictionary' ? '词典' : 'AI 翻译';
                popover.appendChild(source);
            }
        }).fail(function () {
            if (requestId === translationRequest && translationPopover) {
                popover.classList.remove('is-loading');
                popover.textContent = '翻译失败，请稍后重试';
            }
        });
    }

    function bindSelectionTranslation(content) {
        content.document.addEventListener('mouseup', function () {
            setTimeout(function () { translateSelection(content); }, 0);
        });
        content.document.addEventListener('touchend', function () {
            setTimeout(function () { translateSelection(content); }, 80);
        });
    }

    // ===== 段落朗读（TTS）+ 沉浸式翻译 =====

    var TRANSLATE_ENABLED_KEY = "calibre.reader.immersiveTranslate";
    var TTS_ENGINE_KEY = "calibre.reader.ttsEngine";
    var TRANSLATION_CACHE_MAX = 500;

    function readerCsrfToken() {
        return $("input[name='csrf_token']").val() || "";
    }

    // 注入 iframe 的按钮/译文样式：用 currentColor 跟随阅读主题
    var READER_TOOLS_STYLE = [
        '.reading-tts-btn{display:inline-block;margin-left:6px;padding:0 2px;font-size:.8em;line-height:1;opacity:0;cursor:pointer;user-select:none;-webkit-user-select:none;color:inherit}',
        '.reading-tts-btn::before{content:"▶"}',
        '.reading-tts-btn.is-loading::before{content:"⟳"}',
        '.reading-tts-btn.is-playing::before{content:"■"}',
        '.reading-tts-btn.is-loading,.reading-tts-btn.is-playing{opacity:.85}',
        'p:hover>.reading-tts-btn,li:hover>.reading-tts-btn,blockquote:hover>.reading-tts-btn,h1:hover>.reading-tts-btn,h2:hover>.reading-tts-btn,h3:hover>.reading-tts-btn,h4:hover>.reading-tts-btn,h5:hover>.reading-tts-btn,h6:hover>.reading-tts-btn,div:hover>.reading-tts-btn{opacity:.5}',
        '.reading-tts-btn:hover{opacity:1}',
        '@media (hover:none){.reading-tts-btn{opacity:.35}}',
        '.reading-translation{margin:6px 0 14px;font-size:.92em;line-height:1.5;color:inherit;opacity:.72;border-left:2px solid currentColor;padding-left:10px}',
        '.reading-translation.is-loading{opacity:.4;font-style:italic}',
        '.reading-translation.is-error{cursor:pointer;color:#c0392b;opacity:.9;font-style:italic;border-left-color:#c0392b}'
    ].join('');

    function injectReaderToolsStyle(doc) {
        if (doc.getElementById('reading-tools-style')) return;
        var style = doc.createElement('style');
        style.id = 'reading-tools-style';
        style.textContent = READER_TOOLS_STYLE;
        (doc.head || doc.documentElement).appendChild(style);
    }

    // 段落选择：常见块级元素；div 只取无块级子元素的"叶子段落"（部分 EPUB 用 div 当自然段）
    var PARAGRAPH_SELECTOR = 'p, li, blockquote, h1, h2, h3, h4, h5, h6, div';
    var BLOCK_CHILD_SELECTOR = 'p, li, div, blockquote, section, article, table, ul, ol, h1, h2, h3, h4, h5, h6';

    function collectParagraphElements(doc) {
        var els = Array.prototype.slice.call(doc.querySelectorAll(PARAGRAPH_SELECTOR));
        return els.filter(function (el) {
            if (el.tagName === 'DIV' && el.querySelector(BLOCK_CHILD_SELECTOR)) return false;
            return (el.textContent || '').trim().length > 0;
        });
    }

    function paragraphSpeechText(el) {
        var text = (el.textContent || '').replace(/\s+/g, ' ').trim();
        // 与后端 /ai/tts 校验一致的上限；超长段落截断朗读
        return text.length > 2000 ? text.slice(0, 2000) : text;
    }

    // --- 朗读按钮注入 ---
    function injectParagraphTools(content) {
        var doc = content.document;
        if (!doc || !doc.body) return;
        injectReaderToolsStyle(doc);
        collectParagraphElements(doc).forEach(function (el) {
            var existing = el.querySelector(':scope > .reading-tts-btn');
            if (existing) return;
            var btn = doc.createElement('span');
            btn.className = 'reading-tts-btn';
            btn.title = '朗读本段';
            btn.addEventListener('click', function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                speakParagraph(el, btn);
            });
            el.appendChild(btn);
        });
    }

    // --- 朗读状态机：全局单例，一次只播一段 ---
    var activeTts = null;
    var ttsRequestSeq = 0;

    function getTtsEngine() {
        var saved = null;
        try { saved = localStorage.getItem(TTS_ENGINE_KEY); } catch (e) {}
        if (saved === 'ai' || saved === 'browser') return saved;
        return calibre.ttsConfigured ? 'ai' : 'browser';
    }

    function stopTts() {
        ttsRequestSeq++;
        if (!activeTts) return;
        if (activeTts.btn) activeTts.btn.classList.remove('is-playing', 'is-loading');
        if (activeTts.audio) {
            activeTts.audio.pause();
            if (activeTts.url) URL.revokeObjectURL(activeTts.url);
        } else if (activeTts.utterance) {
            try { window.speechSynthesis.cancel(); } catch (e) {}
        }
        activeTts = null;
    }

    function speakParagraph(el, btn) {
        if (btn.classList.contains('is-playing')) { stopTts(); return; }
        stopTts();
        var text = paragraphSpeechText(el);
        if (!text) return;
        if (getTtsEngine() === 'ai' && calibre.readingTtsUrl) speakWithAi(btn, text);
        else speakWithBrowser(btn, text);
    }

    function speakWithAi(btn, text) {
        var seq = ++ttsRequestSeq;
        btn.classList.add('is-loading');
        fetch(calibre.readingTtsUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': readerCsrfToken()},
            body: JSON.stringify({text: text})
        }).then(function (resp) {
            var type = resp.headers.get('Content-Type') || '';
            if (resp.ok && type.indexOf('audio') >= 0) return resp.blob();
            return resp.json().then(function (data) {
                throw new Error(data.error || ('HTTP ' + resp.status));
            });
        }).then(function (blob) {
            if (seq !== ttsRequestSeq) return;
            btn.classList.remove('is-loading');
            btn.classList.add('is-playing');
            var url = URL.createObjectURL(blob);
            var audio = new Audio(url);
            activeTts = {audio: audio, url: url, btn: btn};
            audio.onended = function () { if (activeTts && activeTts.audio === audio) stopTts(); };
            audio.onerror = function () {
                if (activeTts && activeTts.audio === audio) { stopTts(); readerToast('音频播放失败'); }
            };
            audio.play().catch(function () { stopTts(); readerToast('音频播放失败'); });
        }).catch(function (err) {
            if (seq !== ttsRequestSeq) return;
            btn.classList.remove('is-loading');
            readerToast('AI 朗读失败，改用本地语音' + (err && err.message ? '：' + err.message : ''));
            speakWithBrowser(btn, text);
        });
    }

    function speechLang(text) {
        var cjk = (text.match(/[\u4e00-\u9fff]/g) || []).length;
        return cjk * 4 >= text.length ? 'zh-CN' : 'en-US';
    }

    function speakWithBrowser(btn, text) {
        if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
            readerToast('当前浏览器不支持语音合成');
            return;
        }
        var lang = speechLang(text);
        var utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = 0.95;
        var voices = window.speechSynthesis.getVoices() || [];
        for (var i = 0; i < voices.length; i++) {
            if (voices[i].lang && voices[i].lang.toLowerCase().indexOf(lang.slice(0, 2).toLowerCase()) === 0) {
                utterance.voice = voices[i];
                break;
            }
        }
        btn.classList.add('is-playing');
        activeTts = {utterance: utterance, btn: btn};
        utterance.onend = function () { if (activeTts && activeTts.utterance === utterance) stopTts(); };
        utterance.onerror = function () {
            if (activeTts && activeTts.utterance === utterance) { stopTts(); readerToast('语音合成失败'); }
        };
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }

    // Chrome 的 getVoices() 首次调用常为空，触发一次加载即可
    if (window.speechSynthesis) {
        try {
            window.speechSynthesis.getVoices();
            window.speechSynthesis.onvoiceschanged = function () { window.speechSynthesis.getVoices(); };
        } catch (e) {}
    }

    var readerToastTimer = null;
    function readerToast(message) {
        var el = document.getElementById('reader-toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'reader-toast';
            document.body.appendChild(el);
        }
        el.textContent = message;
        el.classList.add('is-visible');
        if (readerToastTimer) clearTimeout(readerToastTimer);
        readerToastTimer = setTimeout(function () { el.classList.remove('is-visible'); }, 2600);
    }

    // --- 朗读引擎设置 ---
    var ttsEngineSelect = document.getElementById('ttsEngine');
    if (ttsEngineSelect) {
        ttsEngineSelect.value = getTtsEngine();
        ttsEngineSelect.addEventListener('change', function () {
            stopTts();
            try { localStorage.setItem(TTS_ENGINE_KEY, ttsEngineSelect.value); } catch (e) {}
        });
    }

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
        return div;
    }

    function removeAllTranslations() {
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            Array.prototype.slice.call(doc.querySelectorAll('.reading-translation'))
                .forEach(function (el) { el.remove(); });
        });
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
        var div = insertTranslation(el, '翻译失败，点击重试', 'is-error');
        div.addEventListener('click', function () {
            div.remove();
            retryParagraphTranslation(el, text);
        });
    }

    function retryParagraphTranslation(el, text) {
        insertTranslation(el, '翻译中…', 'is-loading');
        $.ajax({
            url: calibre.readingTranslateBatchUrl,
            method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({paragraphs: [text]})
        }).done(function (response) {
            var translation = ((response.result || response.data || [])[0] || '').trim();
            if (translation) {
                insertTranslation(el, translation);
                var cache = loadTranslationCache();
                cache[paragraphHash(text)] = translation;
                saveTranslationCache(cache);
            } else {
                showTranslationError(el, text);
            }
        }).fail(function () { showTranslationError(el, text); });
    }

    function applyImmersiveTranslation() {
        if (!translationEnabled() || !calibre.readingTranslateBatchUrl) return;
        if (translationInFlight) { translationRetryPending = true; return; }
        var cache = loadTranslationCache();
        var jobs = [];
        var cacheChanged = false;
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
                    cacheChanged = true;
                    return;
                }
                if (isElementVisible(el, win) && jobs.length < 20) {
                    jobs.push({el: el, text: text, hash: paragraphHash(text)});
                }
            });
        });
        if (cacheChanged) saveTranslationCache(cache);
        if (!jobs.length) return;

        translationInFlight = true;
        jobs.forEach(function (job) { insertTranslation(job.el, '翻译中…', 'is-loading'); });
        $.ajax({
            url: calibre.readingTranslateBatchUrl,
            method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({paragraphs: jobs.map(function (job) { return job.text; })})
        }).done(function (response) {
            var translations = response.result || response.data || [];
            jobs.forEach(function (job, index) {
                var translation = (translations[index] || '').trim();
                if (translation) {
                    cache[job.hash] = translation;
                    insertTranslation(job.el, translation);
                } else {
                    showTranslationError(job.el, job.text);
                }
            });
            saveTranslationCache(cache);
        }).fail(function () {
            jobs.forEach(function (job) { showTranslationError(job.el, job.text); });
        }).always(function () {
            translationInFlight = false;
            if (translationRetryPending) {
                translationRetryPending = false;
                setTimeout(applyImmersiveTranslation, 50);
            }
        });
    }

    // 工具栏翻译开关
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
        // 打开阅读器时若开关已开启，当前页自动翻译
        if (translationEnabled()) setTimeout(applyImmersiveTranslation, 200);
    }

    reader.rendition.on('rendered', function (section, view) {
        var content = view && view.contents;
        if (content && content.document) {
            bindSelectionTranslation(content);
            injectParagraphTools(content);
        }
        // 沉浸式翻译：新章节渲染后先回填缓存，再请求当前页缺失译文
        if (translationEnabled()) setTimeout(applyImmersiveTranslation, 60);
    });

    document.addEventListener('mousedown', function (event) {
        if (!translationPopover || translationPopover.contains(event.target)) return;
        closeTranslationPopover();
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') closeTranslationPopover();
    });

    // 获取当前章节的真实标题。旧实现读取 #chapter-title，但该元素被
    // reader.min.js 的 MetaController 填充为书籍作者而非章节名，
    // 导致上报给 moon-well 的 chapter 字段错误。
    function currentChapterTitle() {
        var label = '';
        try {
            var location = reader.currentLocation && reader.currentLocation();
            var cfi = location && location.start && location.start.cfi;
            var nav = reader.book.navigation;
            if (cfi && nav && nav.toc) {
                var spineItem = reader.book.spine.get(cfi);
                if (spineItem) {
                    if (nav.toc[spineItem.index] && nav.toc[spineItem.index].label) {
                        label = nav.toc[spineItem.index].label;
                    }
                    if (!label && spineItem.href) {
                        label = findTocLabel(nav.toc, spineItem.href);
                    }
                }
            }
        } catch (e) {}
        // 兜底：取当前渲染文档的 <title>
        if (!label) {
            try {
                var contents = reader.rendition.getContents();
                if (contents && contents.length && contents[0].document &&
                    contents[0].document.title) {
                    label = contents[0].document.title;
                }
            } catch (e) {}
        }
        return label;
    }

    // 收集当前可见「页」的文本（异步回调）。
    // EPUB.js 的 getContents() 返回整个 section 文档（iframe 内整章内容经 CSS 分栏
    // 分页），直接取 body.innerText 会把整章文本都上报（可达数十 KB）。首选用
    // currentLocation() 的 start/end CFI 经 book.getRange() 精确取「当前页」文本；
    // 若 CFI 定位失败或结果为空，退回整 section 文本，保证一定有内容可上报。
    function currentPageText(done) {
        var fallback = function () {
            var parts = [];
            try {
                reader.rendition.getContents().forEach(function (content) {
                    var doc = content.document;
                    if (!doc || !doc.body) return;
                    var text = doc.body.innerText || doc.body.textContent || '';
                    if (text) parts.push(text.trim());
                });
            } catch (e) {}
            done(parts.join('\n\n').trim());
        };
        var startCfi = null, endCfi = null;
        try {
            var location = reader.currentLocation && reader.currentLocation();
            startCfi = location && location.start && location.start.cfi;
            endCfi = location && location.end && location.end.cfi;
        } catch (e) {}
        if (!startCfi || !endCfi) { fallback(); return; }
        try {
            Promise.all([reader.book.getRange(startCfi), reader.book.getRange(endCfi)]).then(function (ranges) {
                var sr = ranges && ranges[0], er = ranges && ranges[1];
                if (!sr || !er || !sr.startContainer || !er.startContainer) { fallback(); return; }
                var doc = sr.startContainer.ownerDocument;
                if (!doc || !doc.createRange) { fallback(); return; }
                var range = doc.createRange();
                range.setStart(sr.startContainer, sr.startOffset);
                range.setEnd(er.endContainer, er.endOffset);
                var text = (range.toString() || '').trim();
                if (text) done(text); else fallback();
            }).catch(fallback);
        } catch (e) { fallback(); }
    }

    function markVocabulary(records) {
        var byWord = {};
        (records || []).forEach(function (record) {
            if (record && record.word) byWord[record.word] = record;
        });
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            var walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
            var textNodes = [], node;
            while ((node = walker.nextNode())) textNodes.push(node);
            textNodes.forEach(function (textNode) {
                // 已包过 span 的文本节点跳过，防止重复标注产生嵌套 span
                var parent = textNode.parentElement;
                if (parent && parent.classList &&
                    parent.classList.contains('reading-vocabulary-unknown')) return;
                var fragment = doc.createDocumentFragment(), text = textNode.textContent, last = 0;
                var regex = /\b[A-Za-z][A-Za-z'’-]*\b/g, match;
                while ((match = regex.exec(text))) {
                    var word = match[0].toLowerCase().replace(/[’']/g, "'");
                    var record = byWord[word];
                    if (!record || !record.unknown) continue;
                    fragment.appendChild(doc.createTextNode(text.slice(last, match.index)));
                    var span = doc.createElement('span');
                    span.className = 'reading-vocabulary-unknown';
                    span.textContent = match[0];
                    span.title = (record.translation || '点击查看学习记录') +
                        (record.lastBookName ? '\n上次：' + record.lastBookName + ' · ' + (record.lastChapter || '') : '');
                    span.dataset.word = word;
                    span.addEventListener('click', function () {
                        alert(this.title);
                    });
                    fragment.appendChild(span); last = regex.lastIndex;
                }
                if (last > 0) {
                    fragment.appendChild(doc.createTextNode(text.slice(last)));
                    textNode.parentNode.replaceChild(fragment, textNode);
                }
            });
        });
    }

    function inspectVocabulary() {
        if (!calibre.readingVocabularyEnabled) return;
        // 上一请求（含异步取文）仍在飞行：标记待重检并跳过本次，避免漏标新页面的生词
        if (vocabularyInFlight) {
            vocabularyRetryPending = true;
            return;
        }

        vocabularyInFlight = true;
        currentPageText(function (pageText) {
            if (!pageText) {
                finishVocabularyFlight();
                return;
            }

            // 页面文本与上次已上传的完全一致（翻回已读页/同一渲染重触发）：
            // 直接用缓存 records 重新标注，不重复请求 moon-well
            var sign = pageText.slice(0, 64) + '#' + pageText.length;
            if (sign === lastPageTextSignature) {
                if (Object.keys(vocabularyRecords).length) markVocabulary(Object.keys(vocabularyRecords)
                    .map(function (w) { return vocabularyRecords[w]; }));
                finishVocabularyFlight();
                return;
            }

            var location = reader.currentLocation && reader.currentLocation();
            $.ajax({
                url: calibre.readingVocabularyUrl, method: 'POST', contentType: 'application/json',
                // EPUB 阅读器不加载 main.js，不会自动附带 CSRF 头；而服务端全局启用
                // CSRF，缺 token 会返回 400 导致生词标注静默失效，故在此显式补充。
                headers: { "X-CSRFToken": $("input[name='csrf_token']").val() || "" },
                data: JSON.stringify({bookId: calibre.bookId, bookName: calibre.bookName,
                    chapter: currentChapterTitle(),
                    page: document.getElementById('pages-count').textContent,
                    cfi: location && location.start && location.start.cfi || '',
                    pageText: pageText})
            }).done(function (response) {
                var records = response.result || response.data || [];
                (records || []).forEach(function (record) {
                    if (record && record.word) vocabularyRecords[record.word] = record;
                });
                lastPageTextSignature = sign;
                markVocabulary(records);
            }).always(function () {
                finishVocabularyFlight();
            });
        });
    }

    // 请求（含异步取文）结束：清飞行标记；期间若有过翻页则重检当前页
    function finishVocabularyFlight() {
        vocabularyInFlight = false;
        if (vocabularyRetryPending) {
            vocabularyRetryPending = false;
            setTimeout(inspectVocabulary, 50);
        }
    }
    reader.rendition.on('relocated', function () { setTimeout(inspectVocabulary, 120); });

    /**
     * @param {string} action - Add or remove bookmark
     * @param {string|int} location - Location or zero
     */
    function updateBookmark(action, location) {
        // Remove other bookmarks (there can only be one)
        if (action === "add") {
            this.settings.bookmarks
                .filter(function (bookmark) {
                    return bookmark && bookmark !== location;
                })
                .map(
                    function (bookmark) {
                        this.removeBookmark(bookmark);
                    }.bind(this)
                );
        }

        var csrftoken = $("input[name='csrf_token']").val();

        // Save to database
        $.ajax(calibre.bookmarkUrl, {
            method: "post",
            data: { bookmark: location || "" },
            headers: { "X-CSRFToken": csrftoken },
        }).fail(function (xhr, status, error) {
            alert(error);
        });
    }

    // Default settings load
    const theme = localStorage.getItem("calibre.reader.theme") ?? "lightTheme";
    selectTheme(theme);

    // Restore saved font and font size after reader is ready
    reader.book.ready.then(() => {
        const savedFontSize = localStorage.getItem("calibre.reader.fontSize");
        if (savedFontSize) {
            reader.rendition.themes.fontSize(`${savedFontSize}%`);
        }

        const savedFont = localStorage.getItem("calibre.reader.font");
        if (savedFont && window.selectFont) {
            window.selectFont(savedFont);
        }
    });
})();

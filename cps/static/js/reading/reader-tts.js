/* global $, calibre */

/**
 * R183（架构评审 B4 批次 7）：段落朗读与整本连播——逐段 TTS（服务端合成 + 浏览器兜底）、
 * 段落与页内按钮注入、朗读状态机、整本连播（听书）状态机与翻章续播。
 *
 * 载入顺序：… reader-immersive.js → reader-ted-audio.js → 本文件 → epub.js
 * 宿主回调只剩两个：章标题与阅读位置（都依赖 rendition/toc，只有装配层持有）。
 * 对 TED 的互斥调用走 window.ReaderTedAudio 直调（它在前面载入，可安全引用）；
 * TED 侧要停本模块，由 TED 自己的宿主回调接走，不构成反向 import。
 */
(function () {
    "use strict";

    var RC = window.ReaderCore;
    // R203：这几个跨模块别名同样是拆分时漏带的——原先是 epub.js 的**函数作用域**变量，
    // 搬进本文件后没有重新声明，运行时 `ReferenceError`，界面表现全是「点了没反应」：
    //   RI.translateParagraph → 段落「译」按钮；AN.openPopover → 批注 / AI 批注按钮；
    //   RT.isActive/stop → 单段朗读与整本连播的「TED 原声让位」（线上报障即此处：
    //   `ReferenceError: RT is not defined at bookPlayerStart`）。
    // 静态锁此前两把都漏：拼接 blob 上下文里 epub.js 的 `var RT` 能对上号；「闭包符号」
    // 那把只扫小写开头 ≥5 字符的标识符。新锁见 tests/test_reader_module_surface.py
    // 的 test_跨模块别名必须在所属文件内声明（按单文件粒度查）。
    var RI = window.ReaderImmersive;
    var AN = window.ReaderAnnotations;
    // RT 用空实现兜底、RI/AN 不兜底，是刻意的区分：RT 只做「另一路播放器让位」，
    // 模块缺失时空转比让朗读整条链崩掉更好；而翻译/批注是用户动作，空转就是本类
    // 事故本身（点了没反应且无任何提示），宁可让 epub.js 的模块缺失检查把话说明白。
    var RT = window.ReaderTedAudio || {
        isActive: function () { return false; },
        stop: function () { }
    };
    var mbT = window.mbT || function (id) { return id; };

    var TTS_ENGINE_KEY = "calibre.reader.ttsEngine";

    var host = {
        currentChapterTitle: function () { return ''; },
        renditionLocation: function () { return null; }
    };
    // ===== 段落朗读（TTS）+ 沉浸式翻译 =====

    // 翻译内容自动隐藏时长：按原文词数动态折算——配置值是「每 100 词显示的
    // 秒数」，段落/选区越长显示越久，供「看一眼译文继续读原文」的使用方式；
    // 0 = 一直显示（关闭自动隐藏）。新 key 与旧的固定秒数语义区分，
    // 旧值不会被误读为每 100 词秒数。键名与默认值出自 reader-core.js（单一真相，
    // 设置面板与折算实现必须读同一个 key，R183）
    var TRANSLATION_DISPLAY_KEY = RC.TRANSLATION_DISPLAY_KEY;
    var TRANSLATION_DISPLAY_DEFAULT = RC.TRANSLATION_DISPLAY_DEFAULT;
    // 配置值同时是最小显示秒数：折算不足时按配置值整秒显示，避免单词/短句一闪而过

    // core 原语在本模块内的同名别名（批次 1 下沉 reader-core.js），
    // 正文与拆分前逐字一致，既有静态锁（X-CSRFToken 计数、CSRF 自愈引用次数）因此继续成立
    var readerToast = function (m) { RC.toast(m); };
    var readerCsrfToken = function () { return RC.csrfToken(); };
    var reloadIfCsrfBlocked = function (x) { return RC.reloadIfCsrfBlocked(x); };
    var translationDisplaySecondsPer100 = function () { return RC.translationDisplaySecondsPer100(); };
    var translationDisplaySecondsFor = function (t) { return RC.translationDisplaySecondsFor(t); };
    var countWords = function (t) { return RC.countWords(t); };
    var collectParagraphElements = function (doc) { return RC.collectParagraphs(doc); };
    var paragraphSpeechText = function (el) { return RC.paragraphSpeechText(el); };
    var injectReaderToolsStyle = function (doc) { RC.injectToolsStyle(doc); };

    // --- R215：触屏段尾菜单 ---
    // Why 用外层 document.body 承载菜单：iframe 内节点会被分页列裁切，且触屏菜单
    // 需要脱离正文流；坐标换算沿用批注弹层（reader-annotations.js）的 iframe 偏移做法。
    var paragraphMenu = null;

    function closeParagraphMenu() {
        if (!paragraphMenu) return;
        paragraphMenu.remove();
        paragraphMenu = null;
        document.removeEventListener('mousedown', onParagraphMenuOutside, true);
        document.removeEventListener('keydown', onParagraphMenuKeydown, true);
    }

    function onParagraphMenuOutside(event) {
        if (paragraphMenu && !paragraphMenu.contains(event.target)) closeParagraphMenu();
    }

    function onParagraphMenuKeydown(event) {
        if (event.key === 'Escape') closeParagraphMenu();
    }

    function openParagraphMenu(el, menuBtn) {
        closeParagraphMenu();
        var rect = menuBtn.getBoundingClientRect();
        var frame = menuBtn.ownerDocument.defaultView && menuBtn.ownerDocument.defaultView.frameElement;
        if (frame) {
            var frameRect = frame.getBoundingClientRect();
            rect = {top: rect.top + frameRect.top, bottom: rect.bottom + frameRect.top,
                left: rect.left + frameRect.left, width: rect.width, height: rect.height};
        }
        var menu = document.createElement('div');
        menu.className = 'reading-para-menu';
        [
            {label: mbT('Read this paragraph aloud'), target: '.reading-para-toolbar .reading-tts-btn'},
            {label: mbT('Translate this paragraph (click again to undo)'), target: '.reading-para-toolbar .reading-translate-btn'},
            {label: mbT('Annotate this paragraph'), target: '.reading-para-toolbar .reading-annotation-btn'},
            {label: mbT('AI companion annotation'), target: '.reading-para-toolbar .reading-companion-btn'}
        ].forEach(function (action) {
            var target = el.querySelector(action.target);
            if (!target) return;
            var item = document.createElement('button');
            item.type = 'button';
            item.textContent = action.label;
            item.addEventListener('click', function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                closeParagraphMenu();
                // 直接触发隐藏的 span：朗读/翻译/批注/AI 的实现与桌面完全同源
                target.click();
            });
            menu.appendChild(item);
        });
        document.body.appendChild(menu);
        var bounds = menu.getBoundingClientRect();
        var top = rect.bottom + 8;
        var left = rect.left;
        if (top + bounds.height > window.innerHeight) top = Math.max(8, rect.top - bounds.height - 8);
        left = Math.min(Math.max(8, left), window.innerWidth - bounds.width - 8);
        menu.style.top = top + 'px';
        menu.style.left = left + 'px';
        paragraphMenu = menu;
        document.addEventListener('mousedown', onParagraphMenuOutside, true);
        document.addEventListener('keydown', onParagraphMenuKeydown, true);
    }

    // --- 朗读/翻译按钮注入 ---
    function createParaButton(doc, className, title, onActivate) {
        var btn = doc.createElement('span');
        btn.className = 'reading-para-btn ' + className;
        btn.title = title;
        btn.setAttribute('aria-label', title);
        btn.addEventListener('click', function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            onActivate(btn);
        });
        return btn;
    }

    function injectParagraphTools(content) {
        var doc = content.document;
        if (!doc || !doc.body) return;
        injectReaderToolsStyle(doc);
        collectParagraphElements(doc).forEach(function (el) {
            if (el.querySelector(':scope > .reading-para-tools')) return;

            // R215：四个 24px 图标保持在段落尾部行内；不采用绝对定位浮层
            // （用户验收反馈：浮层压字太丑）。触屏由行内 44px「⋯」承接。
            var tools = doc.createElement('span');
            tools.className = 'reading-para-tools';
            var bar = doc.createElement('span');
            bar.className = 'reading-para-toolbar';

            bar.appendChild(createParaButton(doc, 'reading-tts-btn',
                mbT('Read this paragraph aloud'), function (btn) { speakParagraph(el, btn); }));
            // 段落「译」按钮**不受 R141/R143 下线影响**：magiclens 的「段落整页翻译」
            // 至今仍是规划 P1（其 README 当前状态表），没有等价实现，属「未重复」项，
            // 因此保留在阅读器内提供——R141 初版把它一起收掉是边界划错，R143 恢复。
            bar.appendChild(createParaButton(doc, 'reading-translate-btn',
                mbT('Translate this paragraph (click again to undo)'), function (btn) { RI.translateParagraph(el, btn); }));
            bar.appendChild(createParaButton(doc, 'reading-annotation-btn',
                mbT('Annotate this paragraph'), function (btn) { AN.openPopover(el, btn); }));
            bar.appendChild(createParaButton(doc, 'reading-companion-btn',
                mbT('AI companion annotation'), function (btn) { AN.openPopover(el, btn); }));
            tools.appendChild(bar);

            // 触屏只露一个 44px「⋯」，菜单里再展开四个动作
            var menuBtn = doc.createElement('span');
            menuBtn.className = 'reading-para-menu-btn';
            menuBtn.setAttribute('role', 'button');
            menuBtn.setAttribute('tabindex', '0');
            menuBtn.setAttribute('aria-label', mbT('Paragraph tools'));
            menuBtn.title = mbT('Paragraph tools');
            // 字形走 CSS ::after：textContent 会混进 paragraphSpeechText，
            // 污染翻译/TTS 的段落缓存键
            menuBtn.addEventListener('click', function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                openParagraphMenu(el, menuBtn);
            });
            tools.appendChild(menuBtn);
            el.appendChild(tools);
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
        // 整本连播 / TED 原声伴听让位单段朗读：同一扬声器互斥，避免两路音频叠播
        if (bookPlayer && bookPlayer.active) bookPlayerStop(false);
        if (RT.isActive()) RT.stop();  // TED 原声让位（状态归 reader-ted-audio.js）
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
            // 带书籍上下文：moon-well 据此把音频判为「书籍段落」永久缓存，
            // 只发 text 会被当临时语音 7 天清理（重听又要重新合成）
            body: JSON.stringify({text: text, bookName: calibre.bookName || '',
                chapter: host.currentChapterTitle()})
        }).then(function (resp) {
            var type = resp.headers.get('Content-Type') || '';
            if (resp.ok && type.indexOf('audio') >= 0) return resp.blob();
            // CSRF 等非 JSON 错误体先用 text 捕获（json() 解析会吞掉原因）
            return resp.text().then(function (body) {
                var message = body || ('HTTP ' + resp.status);
                try {
                    var data = JSON.parse(body);
                    message = (data && (data.error || data.message || data.msg)) || message;
                } catch (e) {}
                throw new Error(message);
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
                if (activeTts && activeTts.audio === audio) { stopTts(); readerToast(mbT('Audio playback failed')); }
            };
            audio.play().catch(function () { stopTts(); readerToast(mbT('Audio playback failed')); });
        }).catch(function (err) {
            if (seq !== ttsRequestSeq) return;
            btn.classList.remove('is-loading');
            // CSRF 过期/会话重建：刷新页面拿新 token（AI 朗读才能恢复）
            if (reloadIfCsrfBlocked(err && err.message)) return;
            readerToast(mbT('AI speech failed, falling back to local voice') + (err && err.message ? '：' + err.message : ''));
            speakWithBrowser(btn, text);
        });
    }

    function speechLang(text) {
        var cjk = (text.match(/[\u4e00-\u9fff]/g) || []).length;
        return cjk * 4 >= text.length ? 'zh-CN' : 'en-US';
    }

    function buildSpeechUtterance(text) {
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
        return utterance;
    }

    function speakWithBrowser(btn, text) {
        if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
            readerToast(mbT('Speech synthesis is not supported in this browser'));
            return;
        }
        var utterance = buildSpeechUtterance(text);
        btn.classList.add('is-playing');
        activeTts = {utterance: utterance, btn: btn};
        utterance.onend = function () { if (activeTts && activeTts.utterance === utterance) stopTts(); };
        utterance.onerror = function () {
            if (activeTts && activeTts.utterance === utterance) { stopTts(); readerToast(mbT('Speech synthesis failed')); }
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

    // R183（B4 批次 1）：toast 实现下沉 reader-core.js，此处保留同名薄委托（27 处调用不动）
    function readerToast(message) {
        RC.toast(message);
    }

    // --- 整本连播（听书）状态机（R157）---
    // Why: 单段朗读播完即停（activeTts 单例），听整本书需要顺序推进的播放队列：
    // 逐段请求 /ajax/reading-tts（moon-well 按 SHA-256(段落原文) 永久缓存，重听毫秒级），
    // 播完自动接下一段；本章耗尽后 rendition.next() 翻章重建队列，全书末尾自动停。
    // 暂停=段内保留进度（audio.pause / 已就位的 blob 不开播），继续从原位续听。
    // 预取保持 ≤1 个在途合成：NAS 本地 TTS 是 CPU 算子瓶颈、MiMo 有 100 RPM 上限，
    // 顺序播放天然串行合规；当前块开播后才预取下一块。
    var bookPlayer = null;
    var BOOK_TTS_MAX = 2000;      // 与 /ajax/reading-tts 前后端一致的单请求上限
    var BOOK_TTS_CHUNK_GAP = 260; // 段落间自然停顿（毫秒，暂停期间冻结）

    // #tts-book（▶/❚❚）与 #tts-book-stop（■）是整本 TTS 连播与 TED 原声伴听**共用**的
    // 同一对按钮：两种播放状态机互斥（任一时刻只有一个非空），故渲染逻辑共用，
    // 只把状态对象作为参数传入（R172 复用 R157 的按钮与文案，避免重造一套 UI）。
    // R215：顶栏工具改成「图标 + 文字标签」后，状态只能写内层 .tb-icon；
    // 直接写 btn.textContent 会把「朗读」标签一并抹掉。
    function setToolIcon(btn, text) {
        var icon = btn && btn.querySelector('.tb-icon');
        if (icon) icon.textContent = text;
        else if (btn) btn.textContent = text;
    }

    function ttsButtonsRender(st) {
        var btn = document.getElementById('tts-book');
        var stopBtn = document.getElementById('tts-book-stop');
        if (!btn) return;
        if (!st) {
            setToolIcon(btn, '▶');
            btn.title = mbT('Listen to this book');
            btn.classList.remove('active');
            if (stopBtn) stopBtn.style.display = 'none';
            return;
        }
        btn.classList.add('active');
        setToolIcon(btn, st.paused ? '▶' : '❚❚');
        btn.title = mbT(st.paused ? 'Resume reading aloud' : 'Pause reading aloud');
        if (stopBtn) {
            stopBtn.style.display = '';
            setToolIcon(stopBtn, '■');
            stopBtn.title = mbT('Stop reading aloud');
        }
    }

    function bookPlayerUpdateButtons() { ttsButtonsRender(bookPlayer); }

    // 超长段落切分为 ≤2000 字符的朗读块：优先在后 1/3 窗口找句读断句，找不到硬切。
    // Why: 单段朗读把 2000 字符以外直接截断（paragraphSpeechText），听书模式不能
    // 静默丢内容，必须切块连读；块的缓存键=切块原文，moon-well 侧按哈希自然去重。
    function bookPlayerChunkTexts(text) {
        var chunks = [];
        var pos = 0;
        while (pos < text.length) {
            if (text.length - pos <= BOOK_TTS_MAX) {
                chunks.push(text.slice(pos));
                break;
            }
            var slice = text.slice(pos, pos + BOOK_TTS_MAX);
            var cut = -1;
            for (var j = slice.length - 1; j >= Math.floor(BOOK_TTS_MAX * 2 / 3); j--) {
                var ch = slice.charAt(j);
                if ('。！？；…'.indexOf(ch) >= 0) { cut = j + 1; break; }
                if ('.!?'.indexOf(ch) >= 0) {
                    var after = slice.charAt(j + 1);
                    if (after === '' || after === ' ') { cut = j + 1; break; }
                }
            }
            if (cut < 0) cut = BOOK_TTS_MAX;
            chunks.push(text.slice(pos, pos + cut));
            pos += cut;
        }
        return chunks;
    }

    // 收集当前章节朗读队列：与段落按钮同一份段落选择口径（collectParagraphElements），
    // 长段切块共用同一 DOM 元素。mode：
    //   page-start      从当前页顶部的段落开始（起播 / 手动翻章跟随）
    //   resume-current  从上次开播的块继续（同章重渲染：字号/主题切换不打断进度）
    function bookPlayerBuildQueue(section, doc, mode) {
        var st = bookPlayer;
        if (!st || !doc || !doc.body) return false;
        var els = collectParagraphElements(doc);
        var items = [];
        els.forEach(function (el, elIndex) {
            var full = (el.textContent || '').replace(/\s+/g, ' ').trim();
            if (!full) return;
            var pieces = bookPlayerChunkTexts(full);
            pieces.forEach(function (piece, pieceIndex) {
                items.push({el: el, elIndex: elIndex, text: piece,
                    pieceIndex: pieceIndex, pieceCount: pieces.length});
            });
        });
        st.items = items;
        st.idx = 0;
        if (mode === 'page-start') {
            st.idx = bookPlayerIndexOfPageStart(section, els, items);
        } else if (mode === 'resume-current' && st.lastStartedText) {
            for (var i = 0; i < items.length; i++) {
                if (items[i].text === st.lastStartedText) { st.idx = i; break; }
            }
        }
        return items.length > 0;
    }

    // 用 epub.js locations 把页首 CFI 与段落 CFI 折算成全书位置序号后比较，
    // 取「页首所在的段落」（起点含该段）。locations 未生成/CFI 失败回退本章第一段。
    function bookPlayerIndexOfPageStart(section, els, items) {
        try {
            var location = host.renditionLocation();
            var startCfi = location && location.start && location.start.cfi;
            if (!startCfi || !section || typeof section.cfiFromElement !== 'function') return 0;
            var locations = reader.book.locations;
            if (!locations || !locations.length()) return 0;
            var target = locations.locationFromCfi(startCfi);
            if (target == null) return 0;
            var bestEl = 0, bestLoc = -1;
            for (var i = 0; i < els.length; i++) {
                var paraCfi = null;
                try { paraCfi = section.cfiFromElement(els[i]); } catch (eCfi) { continue; }
                if (!paraCfi) continue;
                var li = locations.locationFromCfi(paraCfi);
                if (li == null) continue;
                if (li <= target && li >= bestLoc) { bestLoc = li; bestEl = i; }
            }
            for (var k = 0; k < items.length; k++) {
                if (items[k].elIndex === bestEl) return k;
            }
        } catch (e) {}
        return 0;
    }

    function bookPlayerHighlight(el) {
        var st = bookPlayer;
        if (!st) return;
        bookPlayerClearHighlight();
        if (!el || !el.classList) return;
        el.classList.add('reading-tts-speaking');
        st.highlightEl = el;
        bookPlayerFollowPage(el);
    }

    function bookPlayerClearHighlight() {
        var st = bookPlayer;
        if (st && st.highlightEl && st.highlightEl.classList) {
            st.highlightEl.classList.remove('reading-tts-speaking');
        }
        if (st) st.highlightEl = null;
    }

    // 视图跟随朗读进度：仅当当前段落不在可见页内才 display 跳页（听一段闪一下
    // 很难受）。跳页用段落元素当下实时算出的 CFI，不存在旧 CFI 越界毒化显示
    // 队列的风险（IndexSizeError 事故只发生在恢复历史保存位置的场景）。
    // 章节由调用方给出（TTS 连播用 bookPlayer.section，TED 原声用 tedAudioPlayer.section）。
    function followPageInSection(section, el) {
        try {
            if (!section || typeof section.cfiFromElement !== 'function') return;
            var paraCfi = section.cfiFromElement(el);
            if (!paraCfi) return;
            var locations = reader.book.locations;
            var location = host.renditionLocation();
            var startCfi = location && location.start && location.start.cfi;
            var endCfi = location && location.end && location.end.cfi;
            if (!locations || !locations.length() || !startCfi || !endCfi) return;
            var li = locations.locationFromCfi(paraCfi);
            var lo = locations.locationFromCfi(startCfi);
            var hi = locations.locationFromCfi(endCfi);
            if (li == null || lo == null || hi == null) return;
            if (li < lo || li > hi) {
                var p = reader.rendition.display(paraCfi);
                if (p && typeof p.catch === 'function') p.catch(function () {});
            }
        } catch (e) {}
    }

    function bookPlayerFollowPage(el) {
        var st = bookPlayer;
        if (!st) return;
        followPageInSection(st.section, el);
    }

    function bookPlayerFetchAudio(text) {
        return fetch(calibre.readingTtsUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': readerCsrfToken()},
            // 带书籍上下文：moon-well 据此把音频判为书籍段落永久缓存（同单段朗读）
            body: JSON.stringify({text: text, bookName: calibre.bookName || '',
                chapter: host.currentChapterTitle()})
        }).then(function (resp) {
            var type = resp.headers.get('Content-Type') || '';
            if (resp.ok && type.indexOf('audio') >= 0) return resp.blob();
            return resp.text().then(function (body) {
                var message = body || ('HTTP ' + resp.status);
                try {
                    var data = JSON.parse(body);
                    message = (data && (data.error || data.message || data.msg)) || message;
                } catch (eParse) {}
                throw new Error(message);
            });
        });
    }

    // 可暂停的间隙等待：暂停期间冻结计时，停止/换块返回 false
    function bookPlayerGap(ms) {
        return new Promise(function (resolve) {
            var waited = 0;
            var timer = setInterval(function () {
                var st = bookPlayer;
                if (!st || !st.active) { clearInterval(timer); resolve(false); return; }
                if (st.paused) return;
                waited += 50;
                if (waited >= ms) { clearInterval(timer); resolve(true); }
            }, 50);
        });
    }

    // 预取下一块：当前块开播后才发起，且全程 ≤1 个在途合成。结果按文本挂
    // nextReady，进块时命中复用；换章/手动跳转 miss 即 revoke（服务端永久
    // 缓存不受影响，预取的合成不白做）。
    function bookPlayerMaybePrefetch() {
        var st = bookPlayer;
        if (!st || !st.active || st.paused || st.nextReady || st.prefetching) return;
        var next = st.items && st.items[st.idx + 1];
        if (!next) return;
        st.prefetching = true;
        bookPlayerFetchAudio(next.text).then(function (blob) {
            st.prefetching = false;
            if (!bookPlayer || !bookPlayer.active) return;
            st.nextReady = {text: next.text, url: URL.createObjectURL(blob)};
        }).catch(function () { st.prefetching = false; });
    }

    function bookPlayerPlayChunk(chunk) {
        var st = bookPlayer;
        if (!st) return Promise.reject(new Error('stopped'));
        var seq = ++st.chunkSeq;
        st.lastStartedText = chunk.text;
        return new Promise(function (resolve, reject) {
            function cleanup() {
                if (st.audio) {
                    st.audio.onended = null; st.audio.onerror = null; st.audio.onplay = null;
                    try { st.audio.pause(); } catch (ePause) {}
                    st.audio = null;
                }
                if (st.url) {
                    try { URL.revokeObjectURL(st.url); } catch (eUrl) {}
                    st.url = null;
                }
            }
            function finish() {
                if (seq !== st.chunkSeq) return;
                cleanup();
                resolve();
            }
            function fail(err) {
                if (seq !== st.chunkSeq) return;
                cleanup();
                reject(err || new Error('tts failed'));
            }
            function startAudio(url) {
                st.url = url;
                var audio = new Audio(url);
                st.audio = audio;
                audio.onplay = function () { if (seq === st.chunkSeq) bookPlayerMaybePrefetch(); };
                audio.onended = function () {
                    if (seq !== st.chunkSeq) return;
                    // 先记账再停顿：idx 前移后，暂停→继续直接从下一块开始
                    st.lastPlayedText = chunk.text;
                    st.idx++;
                    bookPlayerGap(BOOK_TTS_CHUNK_GAP).then(function (alive) {
                        if (alive) finish(); else fail(new Error('stopped'));
                    });
                };
                audio.onerror = function () { fail(new Error('audio error')); };
                if (st.paused) return; // 拉取期间用户已暂停：音频就位待继续
                audio.play().catch(function () {
                    if (seq !== st.chunkSeq) return;
                    // 浏览器拦截自动播放：转暂停态，用户点一下即恢复（点击即新手势）
                    st.paused = true;
                    bookPlayerUpdateButtons();
                    readerToast(mbT('Autoplay was blocked, tap to continue'));
                });
            }
            var ready = st.nextReady;
            if (ready && ready.text === chunk.text) {
                st.nextReady = null;
                startAudio(ready.url);
            } else {
                if (ready) {
                    try { URL.revokeObjectURL(ready.url); } catch (eReady) {}
                    st.nextReady = null;
                }
                bookPlayerFetchAudio(chunk.text).then(function (blob) {
                    // 已换块/已停止：音频已在服务端按原文落永久缓存，blob 直接丢弃
                    if (seq !== st.chunkSeq) return;
                    startAudio(URL.createObjectURL(blob));
                }).catch(fail);
            }
        });
    }

    function bookPlayerTick() {
        var st = bookPlayer;
        if (!st || !st.active || st.paused) return;
        if (!st.items || st.idx >= st.items.length) {
            if (st.switching) return; // 翻章已在途，rendered 后自动续播
            st.switching = true;
            bookPlayerNextChapter().then(function (advanced) {
                st.switching = false;
                var cur = bookPlayer;
                if (!cur || !cur.active) return;
                if (advanced) { if (!cur.paused) bookPlayerTick(); }
                else bookPlayerStop(true);
            });
            return;
        }
        var chunk = st.items[st.idx];
        bookPlayerHighlight(chunk.el);
        bookPlayerPlayChunk(chunk).then(function () {
            if (!bookPlayer || !bookPlayer.active) return;
            bookPlayerTick();
        }).catch(function (err) {
            var cur = bookPlayer;
            if (!cur || !cur.active) return;
            if (reloadIfCsrfBlocked(err && err.message)) return;
            // 单块失败不中断整本：提示后跳到下一块
            readerToast(mbT('AI speech failed, skipped to next paragraph')
                + (err && err.message ? '：' + err.message : ''));
            cur.idx++;
            bookPlayerTick();
        });
    }

    // 唤醒 NextChapter 的等待链（内部翻章结束/失败时）
    function bookPlayerFireWaiters(st, ok) {
        var waiters = st.renderedWaiters;
        st.renderedWaiters = [];
        waiters.forEach(function (fn) { try { fn(ok); } catch (eWait) {} });
    }

    // 本章队列耗尽 → 翻到下一章：等 rendered 后由 bookPlayerOnRendered 重建
    // 队列并回 resolve(true)；已是最后一章或 20s 未渲染完成则 resolve(false)。
    function bookPlayerNextChapter() {
        var st = bookPlayer;
        if (!st) return Promise.resolve(false);
        var location = host.renditionLocation();
        var startIndex = location && typeof location.start.index === 'number'
            ? location.start.index : null;
        var spineItems = reader.book.spine && reader.book.spine.spineItems;
        if (startIndex === null || !spineItems || !spineItems[startIndex + 1]) {
            return Promise.resolve(false);
        }
        bookPlayerClearHighlight();
        st.emptySkips = 0;
        if (st.audio) { try { st.audio.pause(); } catch (ePause) {} st.audio = null; }
        if (st.url) { try { URL.revokeObjectURL(st.url); } catch (eUrl) {} st.url = null; }
        if (st.nextReady) {
            try { URL.revokeObjectURL(st.nextReady.url); } catch (eNext) {}
            st.nextReady = null;
        }
        st.items = [];
        st.lastStartedText = null;
        st.lastPlayedText = null;
        st.internalNav = true;
        return new Promise(function (resolve) {
            var settled = false;
            var done = function (ok) {
                if (settled) return;
                settled = true;
                clearTimeout(timer);
                resolve(!!ok);
            };
            var timer = setTimeout(function () { done(false); }, 20000);
            st.renderedWaiters.push(done);
            try {
                var p = reader.rendition.next();
                if (p && typeof p.catch === 'function') p.catch(function () { done(false); });
            } catch (eNext) { done(false); }
        });
    }

    // rendered 钩子（reader.rendition.on('rendered') 里调用）：
    //   internalNav = 播放器自身发起的翻章 → 重建队列并唤醒等待链（tick 续播）
    //   其余        = 手动翻章/字号主题等重渲染 → 掐掉当前块，重建队列跟随继续
    function bookPlayerOnRendered(section, view) {
        var st = bookPlayer;
        if (!st || !st.active) return;
        var content = view && view.contents;
        var doc = content && content.document;
        if (!doc) return;
        var prevSection = st.section;
        st.section = section;
        if (st.internalNav) {
            st.internalNav = false;
            if (!bookPlayerBuildQueue(section, doc, 'page-start') && ++st.emptySkips <= 10) {
                // 空文字章节（纯图片封面页等）：跳过继续翻章，别把整场连播判停；
                // 上限 10 章防止 spine 异常时的死循环（超限由 NextChapter 超时兜底）
                st.internalNav = true;
                try {
                    var pNext = reader.rendition.next();
                    if (pNext && typeof pNext.catch === 'function') {
                        pNext.catch(function () { bookPlayerFireWaiters(st, false); });
                    }
                } catch (eSkip) { bookPlayerFireWaiters(st, false); }
                return;
            }
            bookPlayerFireWaiters(st, !!st.items.length);
            return;
        }
        bookPlayerClearHighlight();
        if (st.audio) { try { st.audio.pause(); } catch (ePause) {} st.audio = null; }
        if (st.url) { try { URL.revokeObjectURL(st.url); } catch (eUrl) {} st.url = null; }
        if (st.nextReady) {
            try { URL.revokeObjectURL(st.nextReady.url); } catch (eReady) {}
            st.nextReady = null;
        }
        st.chunkSeq++;
        // 同章重渲染（字号/主题/分栏）继续听原块；真的换了章则从新页顶部起播
        var mode = (section && prevSection && section.index === prevSection.index)
            ? 'resume-current' : 'page-start';
        if (!bookPlayerBuildQueue(section, doc, mode)) {
            bookPlayerStop(false);
            readerToast(mbT('No readable paragraphs in this chapter'));
            return;
        }
        if (!st.paused) bookPlayerTick();
    }

    function bookPlayerStart() {
        if (!calibre.readingTtsUrl) return;
        stopTts(); // 单段朗读让位
        if (RT.isActive()) RT.stop();  // TED 原声让位（状态归 reader-ted-audio.js）
        var content = null;
        try {
            var contents = reader.rendition.getContents();
            content = contents && contents.length ? contents[0] : null;
        } catch (eContents) {}
        var doc = content && content.document;
        var section = null;
        try {
            var location = host.renditionLocation();
            var cfi = location && location.start && location.start.cfi;
            if (cfi) section = reader.book.spine.get(cfi);
        } catch (eSpine) {}
        bookPlayer = {
            active: true, paused: false, items: [], idx: 0, emptySkips: 0,
            audio: null, url: null, nextReady: null, prefetching: false,
            internalNav: false, switching: false, chunkSeq: 0,
            renderedWaiters: [], section: section, highlightEl: null,
            lastStartedText: null, lastPlayedText: null
        };
        if (!doc || !bookPlayerBuildQueue(section, doc, 'page-start')) {
            bookPlayer = null;
            readerToast(mbT('No readable paragraphs in this chapter'));
            return;
        }
        bookPlayerUpdateButtons();
        bookPlayerTick();
    }

    function bookPlayerToggle() {
        var st = bookPlayer;
        if (!st) { bookPlayerStart(); return; }
        if (!st.paused) {
            st.paused = true;
            bookPlayerUpdateButtons();
            if (st.audio) { try { st.audio.pause(); } catch (ePause) {} }
            return;
        }
        st.paused = false;
        bookPlayerUpdateButtons();
        if (st.audio && !st.audio.ended) {
            st.audio.play().catch(function () {
                readerToast(mbT('Audio playback failed'));
            });
        } else {
            bookPlayerTick();
        }
    }

    function bookPlayerStop(reachedEnd) {
        var st = bookPlayer;
        bookPlayer = null;
        if (!st) return;
        st.active = false;
        st.chunkSeq++;
        st.renderedWaiters = [];
        if (st.audio) { try { st.audio.pause(); } catch (ePause) {} st.audio = null; }
        if (st.url) { try { URL.revokeObjectURL(st.url); } catch (eUrl) {} st.url = null; }
        if (st.nextReady) {
            try { URL.revokeObjectURL(st.nextReady.url); } catch (eReady) {}
            st.nextReady = null;
        }
        if (st.highlightEl && st.highlightEl.classList) {
            st.highlightEl.classList.remove('reading-tts-speaking');
        }
        bookPlayerUpdateButtons();
        if (reachedEnd) readerToast(mbT('Reached the end of the book'));
    }



    window.ReaderTts = {
        TTS_ENGINE_KEY: TTS_ENGINE_KEY,
        /** 宿主（epub.js）注入章标题与阅读位置 */
        setHost: function (next) {
            Object.keys(next).forEach(function (k) { if (next[k]) host[k] = next[k]; });
        },
        injectParagraphTools: injectParagraphTools,
        speakParagraph: speakParagraph,
        stopTts: stopTts,
        getTtsEngine: getTtsEngine,
        buildSpeechUtterance: buildSpeechUtterance,
        ttsButtonsRender: ttsButtonsRender,
        followPageInSection: followPageInSection,
        bookPlayerToggle: bookPlayerToggle,
        bookPlayerStop: bookPlayerStop,
        bookPlayerUpdateButtons: bookPlayerUpdateButtons,
        bookPlayerOnRendered: bookPlayerOnRendered,
        bookPlayerActive: function () { return !!(bookPlayer && bookPlayer.active); }
    };
})();

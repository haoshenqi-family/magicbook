/* global $, calibre */

/**
 * R183（架构评审 B4 批次 4）：划词簇——翻译气泡（B）+ 划词发音与生词标记（C）+ 右键快捷菜单（E）。
 *
 * Why 三个小节合成一个模块：它们不是三个功能，而是一件事的三段——一次划词先探测 MagicLens
 * 是否接管，再决定弹不弹气泡，气泡上同时挂「＋/－」生词标记、「详」详解与朗读；
 * translationPopover / popoverHideTimer / selectionMenu 三份状态只在彼此之间流转，拆成三个
 * 模块只会把内部耦合升格成 API 表面。批次 2 的详解面板正是靠这里的 normalizedWord 与自动
 * 隐藏定时器接线的，气泡状态归一后那条注入才有着落（见本文件末尾的导出与 epub.js 的 RS.setHost）。
 *
 * 对宿主只反向依赖两件事：生词标记台账 markVocabulary（装配层持有 vocabularyRecords）
 * 与浏览器朗读的 utterance 组装 buildSpeechUtterance（H 节朗读状态机持有）。
 *
 * 载入顺序：i18n_seed → api.js → reader-core.js → reader-word-detail.js →
 * reader-annotations.js → 本文件 → epub.js（见 cps/templates/read.html）
 */
(function () {
    "use strict";

    var RC = window.ReaderCore;
    var RD = window.ReaderWordDetail;
    var AN = window.ReaderAnnotations;
    var mbT = window.mbT || function (id) { return id; };

    // core 原语的同名别名：正文与 epub.js 时代逐字一致，既有静态锁（CSRF 自愈引用次数、
    // X-CSRFToken 计数）因此继续成立
    var readerToast = function (m) { RC.toast(m); };
    var readerCsrfToken = function () { return RC.csrfToken(); };
    var reloadIfCsrfBlocked = function (x) { return RC.reloadIfCsrfBlocked(x); };
    var translationDisplaySecondsFor = function (t) { return RC.translationDisplaySecondsFor(t); };

    // 宿主回调：生词台账（vocabularyRecords）与 utterance 组装、整本翻译进度轮询
    // 都在装配层/H/I 节，模块只经这三个口请求，不持有第二份台账
    var host = {
        markVocabulary: function () { },
        buildSpeechUtterance: function () { return null; },
        applyWordRecord: function () { return []; },
        getWordRecord: function () { return null; },
        startWholeBookProgressPolling: function () { }
    };
    // ===== MagicLens 接管探测（R141 静态下线 → R143 收窄边界 → R146 改运行时探测）=====
    // 口径不变：只让位 magiclens 真正接管的部分，不重复、不打架；但不再写死——
    // 「装了扩展」不等于「这条能力在此处通」。v0.8.5 之前 iframe 拖选根本不通，而写死
    // 下线让装了扩展的用户在阅读器里划词凭空消失，就是这个写法的代价。
    // 改为读扩展自己在 DOM 上留的接管标记（magiclens v0.8.6 / 其 R37）：
    //   · data-magiclens-selection：由 selection-relay.js 写在**它所在的那个文档**上，
    //     语义是「本帧的拖选划词确实在被扩展处理」，所以逐文档判定；
    //   · data-magiclens-highlight：由 highlight.js 写在**顶层文档**上，语义是「高亮引擎
    //     正在跑」（它跨文档标注本页所有 frame），会随 Alt+U / 域名禁用 / 登出被清除。
    // 读不到标记就保留内置实现：未装扩展、扩展版本过旧（<0.8.6 没有标记）、该 frame
    // 注入失败、用户关了高亮——这四种情况下功能都不因「让位」而缺失。标记的值就是扩展
    // 版本号，出问题时在 DevTools 里看一眼 DOM 属性即可分辨是上面哪一种。
    // 不在让位范围内的：段落「译」按钮、整页/整本翻译、朗读、批注、AI 伴读、右键快捷
    // 菜单，以及 inspectVocabulary 的每页文本上送（喂 moon-well 阅读事件流与伴读生词）。

    // 本帧的拖选划词是否已被扩展接管（contentDoc 即 epub.js 渲染正文的那个同源 iframe）
    function lensOwnsSelection(contentDoc) {
        return Boolean(contentDoc.documentElement.dataset.magiclensSelection);
    }

    // 生词高亮是否已被扩展接管（其引擎在顶层文档统一标注，故看顶层文档的标记）
    function lensOwnsHighlight() {
        return Boolean(document.documentElement.dataset.magiclensHighlight);
    }

    // 划词翻译：选中文本弹出翻译气泡（来自 master 分支功能）。
    var translationRequest = 0;
    var translationPopover;
    var popoverHideTimer = null;
    var popoverHideText = '';

    function startWholeBookTranslation() {
        if (!calibre.wholeBookTranslationUrl || !window.confirm(mbT('Start/resume whole-book translation?\n\nParagraphs that already have translations only hit the cache and are not billed again; only missing paragraphs are actually translated.'))) return;
        var button = document.getElementById('whole-book-translate');
        if (button) { button.classList.add('active'); button.textContent = mbT('Submitting…'); }
        $.ajax({url: calibre.wholeBookTranslationUrl, method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            // R75 后续：恒带 force。历史批次可能停在 PUBLISHED 缺口（已发布但译文
            // 未落缓存），retry 只重发 FAILED 段够不着；force 每次新建批次，已译段
            // 经缓存命中回收（幂等不重复计费），只真正发布缺失段。
            data: JSON.stringify({book_id: calibre.bookId, book_format: calibre.bookFormat, force: true})
        }).done(function (result) {
            // 译文不是同步返回：任务由 moon-well 后台逐段执行并写入段落缓存，
            // R215 起不再自动插进正文，点段翻译模式下命中缓存即时显示。
            try { localStorage.setItem('calibre.reader.translation.job.' + calibre.bookId, result.jobId); } catch (e) {}
            alert(mbT('Whole-book translation submitted\nTotal paragraphs: {total}\nCached: {cached}\nNewly published: {published}\n\nTranslations are generated in the background paragraph by paragraph; turn on Translation mode and click a paragraph to read them.')
                .replace('{total}', result.totalCount || 0)
                .replace('{cached}', result.cachedCount || 0)
                .replace('{published}', result.publishedCount || 0));
            host.startWholeBookProgressPolling();
        }).fail(function (xhr) {
            if (reloadIfCsrfBlocked(xhr)) return;
            alert((xhr.responseJSON && xhr.responseJSON.message) || mbT('Failed to submit whole-book translation'));
        }).always(function () {
            if (button) { button.classList.remove('active'); button.textContent = mbT('Whole-book'); }
        });
    }

    function closeTranslationPopover() {
        if (popoverHideTimer) { clearTimeout(popoverHideTimer); popoverHideTimer = null; }
        popoverHideText = '';
        // R125：详解面板与气泡生命周期解耦——收气泡不再收面板。
        // 生成要 15~30s，翻页/新选区误关一次用户就白等一趟；面板仅由 ✕/Esc 关闭
        if (translationPopover) {
            translationPopover.remove();
            translationPopover = null;
        }
    }

    // 划词气泡的自动隐藏：时长按选中原文的词数折算（与段落译文共用
    // 「每 100 词秒数」配置）；气泡内点击（发音/标记按钮）会重新调度，
    // 避免操作中途被收走
    function schedulePopoverHide(text) {
        if (text !== undefined) popoverHideText = text;
        // Why 挂起：详解面板存活期间气泡不自动隐藏（单词译文默认仅 5 秒，
        // 而面板要承载 30s 级的现场生成与阅读）；面板关闭时由其负责重挂计时
        if (RD.isOpen()) return; // R183：面板态归模块持有
        // 气泡已被收走（如翻页联动）时无需再计时
        if (!translationPopover) return;
        // 译文结果未到达（loading 态点击）：没有可计时的内容
        if (!popoverHideText) return;
        if (popoverHideTimer) { clearTimeout(popoverHideTimer); popoverHideTimer = null; }
        var seconds = translationDisplaySecondsFor(popoverHideText);
        if (!seconds) return;
        popoverHideTimer = setTimeout(function () {
            popoverHideTimer = null;
            closeTranslationPopover();
        }, seconds * 1000);
    }

    function showTranslationPopover(text, rect, loading) {
        closeTranslationPopover();
        translationPopover = document.createElement('div');
        translationPopover.className = 'reading-translation-popover' + (loading ? ' is-loading' : '');
        translationPopover.textContent = loading ? mbT('Translating…') : text;
        // 气泡内任何点击（朗读/生词标记等）都视为正在使用：重置自动隐藏计时。
        // 用捕获阶段监听——按钮自身的 click 处理器会 stopPropagation，
        // 冒泡阶段的监听收不到，捕获先于目标处理器执行不受影响。
        translationPopover.addEventListener('click', function () { schedulePopoverHide(); }, true);
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
        // 扩展正在接管本帧的拖选时不出内置气泡，避免同页双气泡、两套 Esc 互相抢占
        if (lensOwnsSelection(content.document)) return;
        if (!calibre.readingVocabularyEnabled || !calibre.readingTranslationUrl) return;
        var selection = content.window.getSelection();
        var text = selection && selection.toString().replace(/\s+/g, ' ').trim();
        // 任何「不再弹出气泡」的路径都必须关掉旧气泡：单击正文清除选区后
        // 旧实现直接 return，导致气泡常驻不消失（划词翻译不自动关闭的根因之一）
        if (!text || text.length > 2000) { closeTranslationPopover(); return; }
        var range = selection.getRangeAt(0), rect = range.getBoundingClientRect();
        if (!rect.width && !rect.height) { closeTranslationPopover(); return; }
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
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({text: text, context: context.slice(0, 2000)})
        }).done(function (response) {
            if (requestId !== translationRequest || !translationPopover) return;
            var result = response.result || response.data || {};
            popover.classList.remove('is-loading');
            popover.textContent = result.translation || mbT('No translation yet');
            if (result.source) {
                var source = document.createElement('div');
                source.className = 'translation-source';
                source.textContent = result.source === 'dictionary' ? mbT('Dictionary') : mbT('AI translation');
                popover.appendChild(source);
            }
            // 划词发音：单词走有道词库真人音频，短语/句子走浏览器合成（speakSelection）
            if ((window.speechSynthesis && window.SpeechSynthesisUtterance) ||
                SINGLE_WORD_RE.test(text)) {
                var speakBtn = document.createElement('span');
                speakBtn.className = 'translation-speak';
                speakBtn.textContent = '🔊';
                speakBtn.title = mbT('Read original aloud');
                speakBtn.addEventListener('click', function (ev) {
                    ev.stopPropagation();
                    speakSelection(text);
                });
                popover.appendChild(speakBtn);
            }
            // 划词标记：仅对单个英文单词显示 ＋（不认识）/ －（已认识）
            if (calibre.readingWordMarkUrl && SINGLE_WORD_RE.test(text)) {
                appendWordMarkButtons(popover, text);
            }
            // 单词详解：与生词标记同口径，仅单个英文单词显示「详」
            if (calibre.readingWordDetailUrl && SINGLE_WORD_RE.test(text)) {
                RD.appendButton(popover, text);
            }
            // 译文渲染完成才开始计时（loading 中间态不占显示时长）；
            // 词数以选中原文为基数
            schedulePopoverHide(text);
        }).fail(function (xhr) {
            // CSRF 过期/会话重建：刷新页面拿新 token，避免"翻译失败"误导
            if (reloadIfCsrfBlocked(xhr)) return;
            if (requestId === translationRequest && translationPopover) {
                popover.classList.remove('is-loading');
                popover.textContent = mbT('Translation failed, please retry later');
            }
        });
    }

    // 单个英文单词：首尾必须是字母（与 markVocabulary 分词的 \b 边界
    // 语义对齐——尾部带撇号/连字符的选区不会匹配任何页面词形）；
    // 句子/短语不显示标记按钮
    var SINGLE_WORD_RE = /^\s*[A-Za-z](?:[A-Za-z'\u2019-]*[A-Za-z])?\s*$/;

    // 词形归一化：小写 + 弯撇号转直撇号，与 vocabularyRecords 的 key 保持一致
    function normalizedWord(text) {
        return text.trim().toLowerCase().replace(/[\u2019']/g, "'");
    }

    // ===== 划词发音 =====
    // 单个英文单词用有道 dictvoice 词库音频（免费、无需 key、真人音色），
    // 替代 speechSynthesis「取第一个匹配语言的系统音色」的机械声（金山词典
    // 释义无音频字段，此前单词也只能用合成音）；短语/句子仍走浏览器合成。
    // type=2 美式发音（1 为英式）
    var YOUDAO_DICT_VOICE = 'https://dict.youdao.com/dictvoice?type=2&audio=';
    // 正在播放的词库音频：再次发音前先停掉上一段，避免重叠
    var selectionAudio = null;

    function speakSelection(text) {
        if (selectionAudio) {
            selectionAudio.pause();
            selectionAudio = null;
        }
        try { window.speechSynthesis.cancel(); } catch (e) {}
        if (!SINGLE_WORD_RE.test(text)) {
            try { window.speechSynthesis.speak(host.buildSpeechUtterance(text)); } catch (e) {}
            return;
        }
        var audio = new Audio(YOUDAO_DICT_VOICE + encodeURIComponent(text.trim()));
        selectionAudio = audio;
        // 外链音频加载/播放失败（断网、词库无该词）回退浏览器合成，发音始终可用；
        // onerror 与 play() 拒绝可能都触发，靠 selectionAudio 引用判重只回退一次
        var fallback = function () {
            if (selectionAudio !== audio) return;
            selectionAudio = null;
            try { window.speechSynthesis.speak(host.buildSpeechUtterance(text)); } catch (e) {}
        };
        audio.onerror = fallback;
        audio.play().catch(fallback);
    }

    // 标记生效：更新会话内记录并同步页面标注
    // （＋补波浪线；－移除该词全部波浪线 span，即时可见）
    function applyWordUnknown(word, unknown) {
        // 台账更新走宿主（返回全量记录）：vocabularyRecords 归装配层独占，
        // 翻回已读页与 inspectVocabulary 都读它，模块里留副本必然漂移
        var records = host.applyWordRecord(word, unknown);
        if (unknown) {
            host.markVocabulary(records);
        } else {
            unwrapWordSpans(word);
        }
    }

    // 移除某词的全部生词标注 span（解包为纯文本，波浪线即时消失）
    function unwrapWordSpans(word) {
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            Array.prototype.slice.call(
                doc.querySelectorAll('span.reading-vocabulary-unknown')
            ).forEach(function (span) {
                if ((span.dataset.word || '') !== word) return;
                span.parentNode.replaceChild(doc.createTextNode(span.textContent), span);
            });
        });
    }

    // 构建划词气泡的 ＋/－ 标记按钮：互斥高亮当前状态，点击即调 moon-well
    function appendWordMarkButtons(popover, text) {
        var word = normalizedWord(text);
        var plusBtn = document.createElement('span');
        plusBtn.className = 'translation-mark translation-mark-plus';
        plusBtn.textContent = '＋';
        plusBtn.title = mbT('Mark as unknown');
        var minusBtn = document.createElement('span');
        minusBtn.className = 'translation-mark translation-mark-minus';
        minusBtn.textContent = '－';
        minusBtn.title = mbT('Mark as known');

        function refreshState() {
            // ＋/－ 的当前态也读宿主台账：按钮态必须与波浪线依据同一份记录
            var record = host.getWordRecord(word);
            var unknown = !!(record && record.unknown);
            plusBtn.classList.toggle('is-marked', unknown);
            // 从未记录过的词两个按钮都保持常态（既非已知也非未知）
            minusBtn.classList.toggle('is-marked', !!record && !unknown);
        }

        function mark(unknown, btn) {
            if (btn.classList.contains('is-loading')) return;
            btn.classList.add('is-loading');
            $.ajax({
                url: calibre.readingWordMarkUrl, method: 'POST', contentType: 'application/json',
                headers: {'X-CSRFToken': readerCsrfToken()},
                data: JSON.stringify({word: word, unknown: unknown})
            }).done(function () {
                applyWordUnknown(word, unknown);
                refreshState();
                // 插入的是用户选中的原文，用回调形式：String.replace 的第二参里 $&/$1 有特殊含义
                readerToast(unknown ? mbT('Marked as unknown: {w}').replace('{w}', function () { return word; })
                                    : mbT('Marked as known: {w}').replace('{w}', function () { return word; }));
            }).fail(function (xhr) {
                // CSRF 过期/会话重建：刷新页面拿新 token，避免「标记失败」误导
                if (reloadIfCsrfBlocked(xhr)) return;
                readerToast(mbT('Failed to mark, please retry later'));
            }).always(function () {
                btn.classList.remove('is-loading');
            });
        }

        plusBtn.addEventListener('click', function (ev) {
            ev.stopPropagation();
            mark(true, plusBtn);
        });
        minusBtn.addEventListener('click', function (ev) {
            ev.stopPropagation();
            mark(false, minusBtn);
        });
        refreshState();
        popover.appendChild(plusBtn);
        popover.appendChild(minusBtn);
    }

    // ===== 划词右键快捷菜单：引用选中内容到 AI 伴读输入框 =====
    // 有选区时右键用自定义菜单替换原生菜单（原生菜单被拦截后「复制」入口
    // 没了，作为第二个菜单项补回）；无选区时放行原生菜单。
    var SELECTION_QUOTE_MAX = 2000;
    var selectionMenu = null;

    function closeSelectionMenu() {
        if (selectionMenu) {
            selectionMenu.remove();
            selectionMenu = null;
        }
    }

    function currentSelectionText(content) {
        var selection = content.window.getSelection();
        return selection ? String(selection.toString()).replace(/\s+/g, ' ').trim() : '';
    }

    function copySelectionText(content, text) {
        var done = function () { readerToast(mbT('Copied')); };
        var legacy = function () {
            try { content.document.execCommand('copy'); done(); } catch (e) {}
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(done, legacy);
        } else {
            legacy();
        }
    }

    // 引用到 AI 伴读：只填入输入框不发送，用户接着补提示词自己发；
    // 超长选区截断，与段落翻译/批注的 2000 字符上限保持一致
    function quoteSelectionToAi(text) {
        var trimmed = text.length > SELECTION_QUOTE_MAX ? text.slice(0, SELECTION_QUOTE_MAX) + '…' : text;
        if (window.AICompanion && typeof window.AICompanion.insertIntoInput === 'function' &&
            window.AICompanion.insertIntoInput(trimmed)) {
            readerToast(mbT('Quoted into the AI companion — add a prompt and send'));
        }
    }

    function showSelectionMenu(content, event) {
        closeSelectionMenu();
        var text = currentSelectionText(content);
        if (!text) return;
        selectionMenu = document.createElement('div');
        selectionMenu.className = 'reading-selection-menu';

        function addItem(label, action) {
            var item = document.createElement('div');
            item.className = 'selection-menu-item';
            item.textContent = label;
            item.addEventListener('click', function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                closeSelectionMenu();
                action();
            });
            selectionMenu.appendChild(item);
        }

        if (window.AICompanion && typeof window.AICompanion.insertIntoInput === 'function') {
            addItem(mbT('Quote to AI companion'), function () { quoteSelectionToAi(text); });
        }
        addItem(mbT('Copy'), function () { copySelectionText(content, text); });

        document.body.appendChild(selectionMenu);

        // contextmenu 坐标是 iframe 内坐标，换算到主视口（与划词气泡一致）
        var x = event.clientX, y = event.clientY;
        var frame = content.window.frameElement;
        if (frame) {
            var frameRect = frame.getBoundingClientRect();
            x += frameRect.left;
            y += frameRect.top;
        }
        var bounds = selectionMenu.getBoundingClientRect();
        x = Math.min(Math.max(8, x), window.innerWidth - bounds.width - 8);
        y = Math.min(Math.max(8, y), window.innerHeight - bounds.height - 8);
        selectionMenu.style.left = x + 'px';
        selectionMenu.style.top = y + 'px';
    }

    function bindSelectionTranslation(content) {
        // iframe 内事件不冒泡到主文档：正文区的按下/ESC 必须在 iframe
        // document 上处理，否则气泡无法自动消失（双击查词后点击正文
        // 气泡常驻的根因）。气泡挂在主文档 body 上，iframe 内的任何
        // mousedown 都意味着用户点击了正文 → 关闭。批注弹层同理。
        content.document.addEventListener('mousedown', function () {
            closeTranslationPopover();
            AN.closePopover();
            closeSelectionMenu();
        });
        content.document.addEventListener('mouseup', function () {
            setTimeout(function () { translateSelection(content); }, 0);
        });
        content.document.addEventListener('touchend', function () {
            setTimeout(function () { translateSelection(content); }, 80);
        });
        // iframe 内按 ESC 同样关闭划词气泡与右键菜单
        content.document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                closeTranslationPopover();
                closeSelectionMenu();
            }
        });
        // 有选区的右键替换为快捷菜单（引用到 AI 伴读/复制）；无选区放行原生菜单
        content.document.addEventListener('contextmenu', function (event) {
            if (!currentSelectionText(content)) return;
            event.preventDefault();
            showSelectionMenu(content, event);
        });
    }

    window.ReaderSelection = {
        /** 宿主（epub.js）注入生词台账与 utterance 组装 */
        setHost: function (next) {
            if (next.markVocabulary) host.markVocabulary = next.markVocabulary;
            if (next.buildSpeechUtterance) host.buildSpeechUtterance = next.buildSpeechUtterance;
        },
        bindFrame: bindSelectionTranslation,
        startWholeBookTranslation: startWholeBookTranslation,
        lensOwnsSelection: lensOwnsSelection,
        lensOwnsHighlight: lensOwnsHighlight,
        normalizedWord: normalizedWord,
        /* 划词气泡：状态归本模块，外部只做判定与关闭 */
        isPopoverOpen: function () { return !!translationPopover; },
        popoverContainsNode: function (node) { return !!(translationPopover && node && translationPopover.contains(node)); },
        closePopover: closeTranslationPopover,
        scheduleHide: schedulePopoverHide,
        cancelAutoHide: function () {
            if (popoverHideTimer) { clearTimeout(popoverHideTimer); popoverHideTimer = null; }
        },
        /* 右键菜单 */
        isMenuOpen: function () { return !!selectionMenu; },
        menuContainsNode: function (node) { return !!(selectionMenu && node && selectionMenu.contains(node)); },
        closeMenu: closeSelectionMenu
    };
})();

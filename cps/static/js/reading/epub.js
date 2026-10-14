/* global $, calibre, EPUBJS, ePubReader */

var reader;

(function () {
    "use strict";
  // R112: i18n 取词（种子缺失时回退 msgid 本身）
  var mbT = window.mbT || function (id) { return id; };

    EPUBJS.filePath = calibre.filePath;
    EPUBJS.cssPath = calibre.cssPath;

    // epub.js 显示队列毒化兜底：display(CFI) 内部 toRange 抛 IndexSizeError 时
    // （书内容更新导致旧保存的 CFI 越界），rejection 被 epub.js 内部 promise 链吞掉，
    // 显示队列永久卡死、整本书无法翻页，且调用方 catch 不到。此处全局捕获该类
    // 未捕获错误，清掉坏位置后刷新页面重建渲染；sessionStorage 标记防止
    // 「位置再次保存 → 再崩 → 再刷」死循环。
    window.addEventListener("error", function (ev) {
        if (!ev || !/IndexSizeError/.test(String(ev.message || ""))) return;
        if (!/epub\.min\.js/.test(String(ev.filename || ""))) return;
        try {
            var crashKey = "calibre.reader.cfiCrashReload";
            if (sessionStorage.getItem(crashKey)) {
                sessionStorage.removeItem(crashKey);
                return;
            }
            sessionStorage.setItem(crashKey, "1");
            if (window.reader && reader && reader.book) {
                localStorage.removeItem(
                    "calibre.reader.position." + reader.book.key()
                );
            }
        } catch (e) {}
        setTimeout(function () {
            location.reload();
        }, 50);
    });

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

    // Why: epub.js 的 display(CFI) 对「越界字符 offset」的 CFI 会在内部 toRange 抛
    // IndexSizeError 并毒死显示队列（无法翻页），且异常对调用方不可见。恢复保存的
    // 位置前必须用此轻量校验拦住可疑 CFI：解析 CFI 末段的元素 id 断言与字符 offset，
    // 在当前渲染文档里累计该元素下的文本总长，offset 超界即判为不安全。
    // 校验器自身不认识的 CFI 形态一律放行，交给 window error 兜底刷新处理。
    function cfiSafeForCurrentDocument(readerInst, cfi) {
        try {
            var contents = readerInst.rendition.getContents();
            if (!contents || !contents.length || !contents[0].document) return true;
            var doc = contents[0].document;
            var offMatch = String(cfi).match(/\/1:(\d+)\)?\s*$/);
            if (!offMatch) return true;
            var offset = parseInt(offMatch[1], 10);
            var idMatches = String(cfi).match(/\[([^\]]+)\]/g);
            if (!idMatches || !idMatches.length) return true;
            var target = doc.getElementById(
                idMatches[idMatches.length - 1].slice(1, -1)
            );
            if (!target) return true;
            var total = 0;
            var walker = doc.createTreeWalker(target, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                total += (walker.currentNode.textContent || "").length;
            }
            return offset <= total;
        } catch (e) {
            return true;
        }
    }

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
                // Try to restore last position from localStorage if present.
                // Why: 直接 display(保存的 CFI) 在「书内容更新导致旧 CFI 越界」时会在
                // epub.js 内部 toRange 抛 IndexSizeError，且该 rejection 被内部 promise
                // 链吞掉——调用方 catch 不到、返回 promise 永远 pending，显示队列从此
                // 卡死，整本书无法翻页（BOOK-20260913，哈利波特 EPUB 复现）。
                // 因此恢复必须两级：先按 spine 序号 display（整数路径不走 CFI Range，
                // 无此雷）安全落位，再用 cfiSafeForCurrentDocument 校验通过的 CFI 做
                // 章内精调；校验不过则丢弃保存的位置，绝不让可疑 CFI 进入显示队列。
                try {
                    var _savedPos = localStorage.getItem(position_key);
                    if (_savedPos) {
                        try {
                            var _posObj = JSON.parse(_savedPos);
                            if (_posObj && _posObj.cfi) {
                                var _section = null;
                                try { _section = reader.book.spine.get(_posObj.cfi); } catch (eS) {}
                                var _startIndex = _section && typeof _section.index === "number"
                                    ? _section.index : null;
                                if (_startIndex !== null) {
                                    var _p = reader.rendition.display(_startIndex);
                                    if (_p && typeof _p.then === "function") {
                                        _p.then(function () {
                                            if (cfiSafeForCurrentDocument(reader, _posObj.cfi)) {
                                                try {
                                                    var _p2 = reader.rendition.display(_posObj.cfi);
                                                    if (_p2 && typeof _p2.catch === "function") _p2.catch(function () {});
                                                } catch (e2) {}
                                            } else {
                                                try { localStorage.removeItem(position_key); } catch (e3) {}
                                            }
                                        });
                                    }
                                } else {
                                    // CFI 连 spine 都定位不到（书结构大改/损坏）：丢弃
                                    try { localStorage.removeItem(position_key); } catch (e4) {}
                                }
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
                    // index 为 spine 序号：恢复时先按它安全落位（见上方恢复逻辑），
                    // 避免书更新后旧 CFI 越界毒化 epub.js 显示队列。
                    try {
                        var posObj = {
                            cfi: location.start.cfi,
                            percentage: location.start.percentage,
                            index: typeof location.start.index === "number" ? location.start.index : undefined,
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
            .then(save_locations)
            .then(() => {
                // 阅读器成功初始化后重置崩溃兜底标记：本次会话若再遇坏 CFI 崩溃
                // （其他 display(CFI) 调用点），仍可再触发一次兜底刷新
                try { sessionStorage.removeItem("calibre.reader.cfiCrashReload"); } catch (e) {}
            });
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

    // 整书翻译进度轮询：提交后每 30s 查一次批次进度（懒回收：moon-well 完成
    // 任务即写缓存，进度接口查缓存回收完成数），全部完成后提示一次并停止轮询。
    var wholeBookPollTimer = null;
    function startWholeBookProgressPolling() {
        if (wholeBookPollTimer || !calibre.wholeBookTranslationStatusUrl) return;
        wholeBookPollTimer = setInterval(function () {
            var jobId = null;
            try { jobId = localStorage.getItem('calibre.reader.translation.job.' + calibre.bookId); } catch (e) {}
            if (!jobId) return;
            $.ajax({url: calibre.wholeBookTranslationStatusUrl, method: 'POST',
                contentType: 'application/json', headers: {'X-CSRFToken': readerCsrfToken()},
                data: JSON.stringify({job_id: jobId})
            }).done(function (result) {
                if (result && (result.status === 'COMPLETED' || result.status === 'PARTIAL_FAILED')) {
                    clearInterval(wholeBookPollTimer);
                    wholeBookPollTimer = null;
                    readerToast(result.status === 'COMPLETED'
                        ? mbT('Whole-book translation completed: {d}/{t}').replace('{d}', result.completedCount).replace('{t}', result.totalCount)
                        : mbT('Whole-book translation finished, {f} paragraphs failed: {d}/{t}').replace('{f}', result.failedCount).replace('{d}', result.completedCount).replace('{t}', result.totalCount));
                }
            }).fail(function () {
                // 查询失败静默：下次轮询继续；会话过期时后端返回 401，轮询仍无害
            });
        }, 30000);
    }

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
            // 译文不是同步返回：任务由 moon-well 后台逐段执行并写入缓存，
            // 完成后本阅读器翻页时经 restoreCachedTranslations 自动回填。
            try { localStorage.setItem('calibre.reader.translation.job.' + calibre.bookId, result.jobId); } catch (e) {}
            alert(mbT('Whole-book translation submitted\nTotal paragraphs: {total}\nCached: {cached}\nNewly published: {published}\n\nTranslations are generated in the background paragraph by paragraph and appear automatically while reading.')
                .replace('{total}', result.totalCount || 0)
                .replace('{cached}', result.cachedCount || 0)
                .replace('{published}', result.publishedCount || 0));
            startWholeBookProgressPolling();
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
        if (wordDetailPanel) return;
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
                appendWordDetailButton(popover, text);
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
            try { window.speechSynthesis.speak(buildSpeechUtterance(text)); } catch (e) {}
            return;
        }
        var audio = new Audio(YOUDAO_DICT_VOICE + encodeURIComponent(text.trim()));
        selectionAudio = audio;
        // 外链音频加载/播放失败（断网、词库无该词）回退浏览器合成，发音始终可用；
        // onerror 与 play() 拒绝可能都触发，靠 selectionAudio 引用判重只回退一次
        var fallback = function () {
            if (selectionAudio !== audio) return;
            selectionAudio = null;
            try { window.speechSynthesis.speak(buildSpeechUtterance(text)); } catch (e) {}
        };
        audio.onerror = fallback;
        audio.play().catch(fallback);
    }

    // 标记生效：更新会话内记录并同步页面标注
    // （＋补波浪线；－移除该词全部波浪线 span，即时可见）
    function applyWordUnknown(word, unknown) {
        var record = vocabularyRecords[word];
        if (record) {
            record.unknown = unknown;
        } else {
            vocabularyRecords[word] = {word: word, unknown: unknown};
        }
        if (unknown) {
            markVocabulary(Object.keys(vocabularyRecords)
                .map(function (w) { return vocabularyRecords[w]; }));
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
            var record = vocabularyRecords[word];
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

    // ===== 单词详解面板（R123，与 magiclens v0.4.0 同构）=====
    // 六板块：基本意思 → 词源 → 搭配·用法·习语 → 变体衍生 → 同/反义词 → 俚语冷知识。
    // Why textContent 组装：内容来自 LLM，绝不进 innerHTML，杜绝注入。
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
        //（气泡已不在时 schedulePopoverHide 内部会直接跳过，不会形成循环）
        schedulePopoverHide();
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
            openWordDetailPanel(normalizedWord(text), popover);
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
        if (popoverHideTimer) { clearTimeout(popoverHideTimer); popoverHideTimer = null; }
        // R125：仅 Esc 关闭（点外/新选区/翻页不再误关面板，关闭路径只有 ✕ 与 Esc）
        document.addEventListener('keydown', closeWordDetailPanelOnEsc, true);
        $.ajax({
            url: calibre.readingWordDetailUrl, method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({word: word})
        }).done(function (response) {
            if (seq !== wordDetailRequest || !wordDetailPanel) return;
            renderWordDetail(response.result || response.data || {}, word);
        }).fail(function (xhr) {
            // CSRF 过期/会话重建：刷新页面拿新 token，避免误导性报错
            if (reloadIfCsrfBlocked(xhr)) return;
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
            closeAnnotationPopover();
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

    // ===== 段落朗读（TTS）+ 沉浸式翻译 =====

    var TRANSLATE_ENABLED_KEY = "calibre.reader.immersiveTranslate";
    var TTS_ENGINE_KEY = "calibre.reader.ttsEngine";
    var TRANSLATION_CACHE_MAX = 500;

    // 翻译内容自动隐藏时长：按原文词数动态折算——配置值是「每 100 词显示的
    // 秒数」，段落/选区越长显示越久，供「看一眼译文继续读原文」的使用方式；
    // 0 = 一直显示（关闭自动隐藏）。新 key 与旧的固定秒数语义区分，
    // 旧值不会被误读为每 100 词秒数。
    var TRANSLATION_DISPLAY_KEY = 'calibre.reader.translationDisplaySecondsPer100';
    var TRANSLATION_DISPLAY_DEFAULT = 5;
    // 配置值同时是最小显示秒数：折算不足时按配置值整秒显示，避免单词/短句一闪而过

    function translationDisplaySecondsPer100() {
        var raw = null;
        try { raw = localStorage.getItem(TRANSLATION_DISPLAY_KEY); } catch (e) {}
        var value = parseInt(raw, 10);
        return (isNaN(value) || value < 0) ? TRANSLATION_DISPLAY_DEFAULT : value;
    }

    // 词数统计：中文每字算一词，连续拉丁字母/数字串算一词（英文段落按单词
    // 计、中文段落按字计），作为显示时长的折算基数
    function countWords(text) {
        var normalized = String(text || '').replace(/\s+/g, ' ').trim();
        if (!normalized) return 0;
        var cjk = (normalized.match(/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/g) || []).length;
        var latin = (normalized.match(/[A-Za-z0-9]+(?:['\u2019-][A-Za-z0-9]+)*/g) || []).length;
        return cjk + latin;
    }

    // 显示秒数 = max(配置值, 词数 * 配置值 / 100)，四舍五入到整秒：
    // 配置值即最小显示时长：单词/短句按配置值整秒显示、不会一闪而过；长段落按词数折算显示更久
    function translationDisplaySecondsFor(sourceText) {
        var per100 = translationDisplaySecondsPer100();
        if (!per100) return 0;
        var scaled = Math.round(countWords(sourceText) * per100 / 100);
        return Math.max(per100, scaled);
    }

    function readerCsrfToken() {
        return $("input[name='csrf_token']").val() || "";
    }

    // CSRF 失败自愈：页面长期打开（token 过期/会话重建后旧 token 与
    // session 不匹配）时，服务端会以 400 拒绝而阅读器内多数请求是静默
    // 失败。检测到 CSRF 类错误即刷新页面——epub.js 会从 localStorage
    // 恢复原阅读位置，仅一次轻微闪断。sessionStorage 标记防死循环刷新。
    function reloadIfCsrfBlocked(xhrOrText) {
        var text = typeof xhrOrText === 'string' ? xhrOrText
            : (xhrOrText && (xhrOrText.responseText || '')) || '';
        if (!/csrf/i.test(text)) return false;
        var key = 'calibre.reader.csrfReloaded';
        var seen = false;
        try { seen = sessionStorage.getItem(key) === '1'; } catch (e) {}
        if (seen) return true;
        try { sessionStorage.setItem(key, '1'); } catch (e) {}
        location.reload();
        return true;
    }

    // 注入 iframe 的按钮/译文样式：用 currentColor 跟随阅读主题
    var READER_TOOLS_STYLE = [
        '.reading-para-btn{display:inline-block;margin-left:6px;padding:0 2px;font-size:.8em;line-height:1;opacity:0;cursor:pointer;user-select:none;-webkit-user-select:none;color:inherit}',
        '.reading-para-btn:hover{opacity:1}',
        '.reading-para-btn.is-loading,.reading-para-btn.is-playing{opacity:.85}',
        'p:hover>.reading-para-btn,li:hover>.reading-para-btn,blockquote:hover>.reading-para-btn,h1:hover>.reading-para-btn,h2:hover>.reading-para-btn,h3:hover>.reading-para-btn,h4:hover>.reading-para-btn,h5:hover>.reading-para-btn,h6:hover>.reading-para-btn,div:hover>.reading-para-btn{opacity:.5}',
        '@media (hover:none){.reading-para-btn{opacity:.35}}',
        '.reading-tts-btn::before{content:"▶"}',
        '.reading-tts-btn.is-loading::before{content:"⟳"}',
        '.reading-tts-btn.is-playing::before{content:"■"}',
        '.reading-translate-btn::before{content:"' + mbT('Tr') + '"}',
        '.reading-translate-btn.is-loading::before{content:"⟳"}',
        '.reading-translate-btn.is-done{opacity:.5}',
        '.reading-annotation-btn::before{content:"✎"}',
        '.reading-companion-btn::before{content:"✨"}',
        '.reading-companion-btn.is-loading::before{content:"⟳"}',
        '.reading-translation{margin:6px 0 14px;font-size:.92em;line-height:1.5;color:inherit;opacity:.72;border-left:2px solid currentColor;padding-left:10px}',
        '.reading-translation.is-loading{opacity:.4;font-style:italic}',
        '.reading-translation.is-error{cursor:pointer;color:#c0392b;opacity:.9;font-style:italic;border-left-color:#c0392b}',
        '.reading-tts-speaking{background:rgba(255,193,7,.24);box-shadow:inset 3px 0 0 rgba(255,152,0,.85)}'
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
        // 与后端 /ajax/reading-tts 校验一致的上限；超长段落截断朗读
        return text.length > 2000 ? text.slice(0, 2000) : text;
    }

    // --- 朗读/翻译按钮注入 ---
    function injectParagraphTools(content) {
        var doc = content.document;
        if (!doc || !doc.body) return;
        injectReaderToolsStyle(doc);
        collectParagraphElements(doc).forEach(function (el) {
            if (!el.querySelector(':scope > .reading-tts-btn')) {
                var ttsBtn = doc.createElement('span');
                ttsBtn.className = 'reading-para-btn reading-tts-btn';
                ttsBtn.title = mbT('Read this paragraph aloud');
                ttsBtn.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    speakParagraph(el, ttsBtn);
                });
                el.appendChild(ttsBtn);
            }
            // 段落「译」按钮**不受 R141/R143 下线影响**：magiclens 的「段落整页翻译」
            // 至今仍是规划 P1（其 README 当前状态表），没有等价实现，属「未重复」项，
            // 因此保留在阅读器内提供——R141 初版把它一起收掉是边界划错，R143 恢复。
            if (!el.querySelector(':scope > .reading-translate-btn')) {
                var trBtn = doc.createElement('span');
                trBtn.className = 'reading-para-btn reading-translate-btn';
                trBtn.title = mbT('Translate this paragraph (click again to undo)');
                trBtn.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    translateParagraph(el, trBtn);
                });
                el.appendChild(trBtn);
            }
            if (!el.querySelector(':scope > .reading-annotation-btn')) {
                var noteBtn = doc.createElement('span');
                noteBtn.className = 'reading-para-btn reading-annotation-btn';
                noteBtn.title = mbT('Annotate this paragraph');
                noteBtn.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    openAnnotationPopover(el, noteBtn);
                });
                el.appendChild(noteBtn);
            }
            if (!el.querySelector(':scope > .reading-companion-btn')) {
                var aiBtn = doc.createElement('span');
                aiBtn.className = 'reading-para-btn reading-companion-btn';
                aiBtn.title = mbT('AI companion annotation');
                aiBtn.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    openAnnotationPopover(el, aiBtn);
                });
                el.appendChild(aiBtn);
            }
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
        if (tedAudioPlayer && tedAudioPlayer.active) tedAudioStop();
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
                chapter: currentChapterTitle()})
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
    function ttsButtonsRender(st) {
        var btn = document.getElementById('tts-book');
        var stopBtn = document.getElementById('tts-book-stop');
        if (!btn) return;
        if (!st) {
            btn.textContent = '▶';
            btn.title = mbT('Listen to this book');
            btn.classList.remove('active');
            if (stopBtn) stopBtn.style.display = 'none';
            return;
        }
        btn.classList.add('active');
        btn.textContent = st.paused ? '▶' : '❚❚';
        btn.title = mbT(st.paused ? 'Resume reading aloud' : 'Pause reading aloud');
        if (stopBtn) {
            stopBtn.style.display = '';
            stopBtn.textContent = '■';
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
            var location = renditionLocation();
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
            var location = renditionLocation();
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
                chapter: currentChapterTitle()})
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
        var location = renditionLocation();
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
        if (tedAudioPlayer && tedAudioPlayer.active) tedAudioStop(); // TED 原声让位
        var content = null;
        try {
            var contents = reader.rendition.getContents();
            content = contents && contents.length ? contents[0] : null;
        } catch (eContents) {}
        var doc = content && content.document;
        var section = null;
        try {
            var location = renditionLocation();
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

    // ===== R172 TED 原声伴听：整段原声 + 时间轴高亮（与 bookPlayer 互斥） =====
    // Why 与整本 TTS 连播分设两个状态机：TED/博客类书的内容本质是「一段连续原声」，
    // 文本段落只是这段录音上的时间轴切片；对 TED 走逐段 TTS 会把真人原声换成机器音
    // （语义错），且一场演讲数万字白烧算力/积分。普通小说书没有原声，仍走 bookPlayer。
    // 分流判据 = calibre.bookFormat === 'TED'，与 moon-well BookFormatEnum.TED 对齐。
    var TED_BOOK = calibre.bookFormat === 'TED';
    var tedAudioPlayer = null;  // 播放态；与 bookPlayer 互斥（任一时刻至多一个非空）
    var tedAudioData = null;    // 预取结果：{audioUrl, segments:[], byChapter:{}}
    var tedAudioLoad = null;    // 预取 Promise（进阅读页即发起，起播不等待）
    var tedAudioMetaOk = null;  // 原声是否可用；false → 隐藏伴听按钮
    var tedAudioAbsenceNotified = false;

    // 段落记录 → 时间轴索引：片段时间升序 + 按 chapterTitle 分组（TED 章节标题唯一）
    function tedAudioIndex(paragraphs) {
        var segments = [];
        var byChapter = {};
        (paragraphs || []).forEach(function (p) {
            if (!p || p.tedAudioStart == null || p.tedAudioEnd == null) return;
            var seg = {
                order: p.order,
                chapterTitle: p.chapterTitle || '',
                chapterOrder: p.chapterOrder == null ? null : Number(p.chapterOrder),
                startMs: Number(p.tedAudioStart),
                endMs: Number(p.tedAudioEnd),
                text: (p.text || '').replace(/\s+/g, ' ').trim()
            };
            segments.push(seg);
            (byChapter[seg.chapterTitle] || (byChapter[seg.chapterTitle] = [])).push(seg);
        });
        segments.sort(function (a, b) { return a.startMs - b.startMs; });
        Object.keys(byChapter).forEach(function (key) {
            byChapter[key].sort(function (a, b) { return (a.order || 0) - (b.order || 0); });
        });
        return {segments: segments, byChapter: byChapter};
    }

    function tedAudioFetch(url) {
        return fetch(url, {
            method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': readerCsrfToken()},
            body: JSON.stringify({bookId: calibre.bookId})
        }).then(function (resp) {
            return resp.text().then(function (body) {
                var data = null;
                try { data = JSON.parse(body); } catch (e) {}
                if (resp.ok && data && data.success) return data.result;
                throw new Error((data && (data.message || data.msg)) || ('HTTP ' + resp.status));
            });
        });
    }

    // 原声不可用（未缓存 / 未建注册表）：隐藏伴听按钮并一次性提示（不静默失败）
    function tedAudioApplyAvailability() {
        if (!TED_BOOK || tedAudioMetaOk) return;
        var btn = document.getElementById('tts-book');
        if (btn) btn.style.display = 'none';
        if (!tedAudioAbsenceNotified) {
            tedAudioAbsenceNotified = true;
            readerToast(mbT('Original audio is not available yet'));
        }
    }

    function tedAudioEnsureLoaded() {
        if (tedAudioLoad) return tedAudioLoad;
        tedAudioLoad = Promise.all([
            tedAudioFetch(calibre.tedAudioUrl),
            tedAudioFetch(calibre.tedAudioParagraphsUrl)
        ]).then(function (res) {
            var meta = res[0] || null;
            var list = res[1] || {};
            var index = tedAudioIndex(list.paragraphs);
            tedAudioData = {
                audioUrl: meta && meta.audioUrl ? meta.audioUrl : '',
                segments: index.segments, byChapter: index.byChapter
            };
            tedAudioMetaOk = !!tedAudioData.audioUrl;
            tedAudioApplyAvailability();
            return tedAudioData;
        }).catch(function (err) {
            tedAudioMetaOk = false;
            tedAudioApplyAvailability();
            throw err;
        });
        return tedAudioLoad;
    }

    function tedAudioUpdateButtons() { ttsButtonsRender(tedAudioPlayer); }

    // 当前渲染章节的真实标题（与 currentChapterTitle 同源：优先 toc.ncx label）
    function tedChapterTitle(section) {
        try {
            var nav = reader.book.navigation;
            if (!nav || !nav.toc) return '';
            if (section) {
                if (nav.toc[section.index] && nav.toc[section.index].label) {
                    return nav.toc[section.index].label;
                }
                if (section.href) {
                    var label = findTocLabel(nav.toc, section.href);
                    if (label) return label;
                }
            }
        } catch (e) {}
        return '';
    }

    function tedAudioChapterOrder(title) {
        var st = tedAudioPlayer;
        var group = (st && title && st.byChapter[title]) || null;
        return group && group.length && group[0].chapterOrder != null
            ? group[0].chapterOrder : null;
    }

    function tedAudioSegmentByOrder(st, order) {
        var segs = st && st.segments;
        if (!segs) return null;
        for (var i = 0; i < segs.length; i++) {
            if (segs[i].order === order) return segs[i];
        }
        return null;
    }

    function tedAudioSegmentAt(st, ms) {
        var segs = st.segments;
        if (!segs || !segs.length) return null;
        if (ms < segs[0].startMs) return segs[0];
        var lo = 0, hi = segs.length - 1, found = 0;
        while (lo <= hi) {
            var mid = (lo + hi) >> 1;
            if (segs[mid].startMs <= ms) { found = mid; lo = mid + 1; }
            else hi = mid - 1;
        }
        return segs[found];
    }

    // 段落元素 ↔ 注册表段落记录对齐。主：chapterTitle 分组 + 段内序（EpubBuilder
    // 保证「一章 xhtml = 该章全部段落、一段一 <p>」，且注册表 chapterTitle 与
    // toc.ncx label 同源，故两端数量相符即可按位对齐）。兜底：归一化文本匹配
    // （两侧文本同源；重复文本按出现序一一消费）。
    function tedAudioAlignChapter(st, section, doc) {
        if (!st || !doc) return null;
        var els = collectParagraphElements(doc);
        if (!els.length) return null;
        var title = tedChapterTitle(section);
        var segs = (title && st.byChapter[title]) || null;
        var map = {};
        if (segs && segs.length && segs.length === els.length) {
            segs.forEach(function (seg, i) { map[seg.order] = els[i]; });
            return {map: map, matched: els.length, total: els.length};
        }
        var pool = segs || st.segments;
        var buckets = {};
        pool.forEach(function (seg) {
            (buckets[seg.text] || (buckets[seg.text] = [])).push(seg);
        });
        var matched = 0;
        els.forEach(function (el) {
            var text = (el.textContent || '').replace(/\s+/g, ' ').trim();
            var bucket = text && buckets[text];
            if (!bucket || !bucket.length) return;
            map[bucket.shift().order] = el;
            matched++;
        });
        return {map: map, matched: matched, total: els.length};
    }

    // 对齐结果入状态；失败段落占比 > 20% → 该章降级「仅整段播放、不高亮/不切播」
    // 并 console.warn（不静默失败，与设计 §4.4 一致）。
    function tedAudioSetAligned(st, section, doc) {
        st.section = section;
        var aligned = tedAudioAlignChapter(st, section, doc);
        if (aligned && aligned.total &&
                (aligned.matched / aligned.total) < 0.8) {
            try {
                console.warn('[ted-audio] paragraph alignment degraded: '
                    + aligned.matched + '/' + aligned.total
                    + ' @ ' + (tedChapterTitle(section) || '?'));
            } catch (eW) {}
            aligned = null;
        }
        st.aligned = aligned;
        if (aligned) {
            // data-ted-order 供段落点击切播时向上查找所属段落（不依赖闭包内映射）
            Object.keys(aligned.map).forEach(function (order) {
                var el = aligned.map[order];
                if (el && el.setAttribute) el.setAttribute('data-ted-order', order);
            });
        }
        return aligned;
    }

    function tedAudioHighlight(el) {
        var st = tedAudioPlayer;
        if (!st) return;
        if (st.highlightEl && st.highlightEl.classList) {
            st.highlightEl.classList.remove('reading-tts-speaking');
        }
        st.highlightEl = null;
        if (!el || !el.classList) return;
        el.classList.add('reading-tts-speaking');
        st.highlightEl = el;
        followPageInSection(st.section, el);
    }

    function tedAudioClearHighlight() {
        var st = tedAudioPlayer;
        if (st && st.highlightEl && st.highlightEl.classList) {
            st.highlightEl.classList.remove('reading-tts-speaking');
        }
        if (st) st.highlightEl = null;
    }

    // 当前段落在别的章节且在其之后：整段原声是全书连续时间轴，播放会跨章——前向
    // 翻章跟随。翻章由 rendered 钩子复位 navigating 并重建对齐，避免递归等待链。
    function tedAudioNavForward(st) {
        if (st.navigating) return;
        st.navigating = true;
        setTimeout(function () {
            if (tedAudioPlayer === st) st.navigating = false;
        }, 20000);
        try {
            var p = reader.rendition.next();
            if (p && typeof p.catch === 'function') {
                p.catch(function () { if (tedAudioPlayer === st) st.navigating = false; });
            }
        } catch (e) { st.navigating = false; }
    }

    function tedAudioFollowSegment(seg) {
        var st = tedAudioPlayer;
        if (!st) return;
        var el = st.aligned && st.aligned.map[seg.order];
        if (el) { tedAudioHighlight(el); return; }
        // 段在本章但未对齐：静默跳过（降级章）；段在别的章：仅当在其之后才前向翻章
        var curTitle = tedChapterTitle(st.section);
        if (curTitle && seg.chapterTitle === curTitle) return;
        var curOrder = tedAudioChapterOrder(curTitle);
        if (seg.chapterOrder != null && (curOrder == null || seg.chapterOrder > curOrder)) {
            st.pendingSegOrder = seg.order;
            tedAudioNavForward(st);
        }
    }

    // timeupdate 节流（≤4 次/秒）后按 currentTime 命中当前段并高亮/跟随
    function tedAudioOnTimeUpdate() {
        var st = tedAudioPlayer;
        if (!st || !st.active || st.paused || !st.audio) return;
        var now = Date.now();
        if (now - st.lastTick < 250) return;
        st.lastTick = now;
        var seg = tedAudioSegmentAt(st, st.audio.currentTime * 1000);
        if (!seg || seg.order === st.segIdx) return;
        st.segIdx = seg.order;
        tedAudioFollowSegment(seg);
    }

    // rendered 钩子（阅读器 rendered 事件里调用）：重建对齐，并按播放位置续高亮
    function tedAudioOnRendered(section, view) {
        var st = tedAudioPlayer;
        if (!st || !st.active) return;
        st.navigating = false;
        var doc = view && view.contents && view.contents.document;
        if (!doc) return;
        tedAudioSetAligned(st, section, doc);
        var seg = st.pendingSegOrder != null
            ? tedAudioSegmentByOrder(st, st.pendingSegOrder) : null;
        if (seg && st.aligned && st.aligned.map[seg.order]) {
            st.pendingSegOrder = null;
            tedAudioHighlight(st.aligned.map[seg.order]);
            return;
        }
        if (st.segIdx >= 0) {
            var cur = tedAudioSegmentByOrder(st, st.segIdx);
            var curEl = cur && st.aligned && st.aligned.map[cur.order];
            if (curEl) tedAudioHighlight(curEl);
        }
    }

    // 段落点击切播：跳到该段原声起点并高亮（不打断播放）。有文字选择（划词）时让位。
    function tedAudioBindSeek(doc) {
        if (!doc || doc.__tedAudioSeekBound) return;
        doc.__tedAudioSeekBound = true;
        doc.addEventListener('click', function (ev) {
            var st = tedAudioPlayer;
            if (!st || !st.active || !st.audio || !st.aligned) return;
            try {
                var sel = doc.getSelection ? doc.getSelection() : null;
                if (sel && sel.toString && sel.toString().trim()) return;
            } catch (eSel) {}
            var el = ev.target;
            var hit = null;
            while (el && el !== doc.body && el.parentNode) {
                if (el.getAttribute && el.getAttribute('data-ted-order') != null) { hit = el; break; }
                el = el.parentNode;
            }
            if (!hit) return;
            var order = parseInt(hit.getAttribute('data-ted-order'), 10);
            var seg = tedAudioSegmentByOrder(st, order);
            if (!seg) return;
            try { st.audio.currentTime = seg.startMs / 1000; } catch (eSeek) {}
            st.segIdx = order;
            tedAudioHighlight(hit);
        });
    }

    function tedAudioStart() {
        stopTts();
        if (bookPlayer && bookPlayer.active) bookPlayerStop(false); // 两模式互斥
        tedAudioPlayer = {
            active: true, paused: false, audio: null, segments: [], byChapter: {},
            section: null, aligned: null, highlightEl: null, segIdx: -1,
            pendingSegOrder: null, navigating: false, lastTick: 0, warned: false
        };
        tedAudioUpdateButtons();
        tedAudioEnsureLoaded().then(function (data) {
            var st = tedAudioPlayer;
            if (!st || !st.active) return;
            if (!data.audioUrl) { tedAudioStop(); return; }
            st.segments = data.segments;
            st.byChapter = data.byChapter;
            var view = tedAudioCurrentView();
            tedAudioSetAligned(st, view.section, view.doc);
            var audio = new Audio(data.audioUrl);
            st.audio = audio;
            audio.addEventListener('ended', function () {
                if (tedAudioPlayer === st) tedAudioStop();
            });
            audio.addEventListener('error', function () {
                if (tedAudioPlayer !== st) return;
                tedAudioStop();
                readerToast(mbT('Audio playback failed'));
            });
            audio.addEventListener('timeupdate', tedAudioOnTimeUpdate);
            var p = audio.play();
            if (p && typeof p.catch === 'function') {
                p.catch(function () {
                    if (tedAudioPlayer !== st) return;
                    // 浏览器拦截自动播放：转暂停态，用户点一下即恢复（点击即新手势）
                    st.paused = true;
                    tedAudioUpdateButtons();
                    readerToast(mbT('Autoplay was blocked, tap to continue'));
                });
            }
        }).catch(function (err) {
            if (!tedAudioPlayer || !tedAudioPlayer.active) return;
            tedAudioStop();
            if (reloadIfCsrfBlocked(err && err.message)) return;
            readerToast(mbT('Original audio is not available yet'));
        });
    }

    function tedAudioCurrentView() {
        var doc = null, section = null;
        try {
            var contents = reader.rendition.getContents();
            var content = contents && contents.length ? contents[0] : null;
            doc = content && content.document;
        } catch (e) {}
        try {
            var loc = renditionLocation();
            var cfi = loc && loc.start && loc.start.cfi;
            if (cfi) section = reader.book.spine.get(cfi);
        } catch (e2) {}
        return {section: section, doc: doc};
    }

    function tedAudioToggle() {
        var st = tedAudioPlayer;
        if (!st) { tedAudioStart(); return; }
        if (!st.audio) return; // 原声仍在加载
        if (!st.paused) {
            st.paused = true;
            tedAudioUpdateButtons();
            try { st.audio.pause(); } catch (ePause) {}
            return;
        }
        st.paused = false;
        tedAudioUpdateButtons();
        if (st.audio.ended) { try { st.audio.currentTime = 0; } catch (eSeek) {} }
        st.audio.play().catch(function () { readerToast(mbT('Audio playback failed')); });
    }

    function tedAudioStop() {
        var st = tedAudioPlayer;
        tedAudioPlayer = null;
        if (!st) return;
        st.active = false;
        if (st.audio) {
            try { st.audio.pause(); } catch (ePause) {}
            try { st.audio.removeEventListener('timeupdate', tedAudioOnTimeUpdate); } catch (eOff) {}
            try { st.audio.src = ''; } catch (eSrc) {}
            st.audio = null;
        }
        if (st.highlightEl && st.highlightEl.classList) {
            st.highlightEl.classList.remove('reading-tts-speaking');
        }
        tedAudioUpdateButtons();
    }

    // 离开阅读页 / 换书：释放整段原声
    window.addEventListener('pagehide', function () {
        if (tedAudioPlayer) tedAudioStop();
    });

    // --- 朗读引擎设置 ---
    var ttsEngineSelect = document.getElementById('ttsEngine');
    if (ttsEngineSelect) {
        ttsEngineSelect.value = getTtsEngine();
        ttsEngineSelect.addEventListener('change', function () {
            // 整本连播固定走 AI 语音：切换引擎时直接结束连播，状态可预期
            if (bookPlayer && bookPlayer.active) bookPlayerStop(false);
            stopTts();
            try { localStorage.setItem(TTS_ENGINE_KEY, ttsEngineSelect.value); } catch (e) {}
        });
    }

    // --- 翻译显示时长设置（每 100 词秒数，同时是最小显示秒数）：改动即时保存，已显示的译文重新计时 ---
    var translationDisplayInput = document.getElementById('translationDisplaySecondsPer100');
    if (translationDisplayInput) {
        translationDisplayInput.value = String(translationDisplaySecondsPer100());
        translationDisplayInput.addEventListener('change', function () {
            var value = parseInt(translationDisplayInput.value, 10);
            if (isNaN(value) || value < 0) value = TRANSLATION_DISPLAY_DEFAULT;
            translationDisplayInput.value = String(value);
            try { localStorage.setItem(TRANSLATION_DISPLAY_KEY, String(value)); } catch (e) {}
            rescheduleVisibleTranslations();
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
        if (translationPopover) schedulePopoverHide();
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
                chapter: currentChapterTitle()})
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
        var chapter = currentChapterTitle();
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
    if (wholeBookToggle) wholeBookToggle.addEventListener('click', startWholeBookTranslation);

    // R157 整本连播按钮：▶/❚❚ 起播暂停切换，■ 停止；依赖 moon-well TTS 代理，
    // 未配置（readingTtsUrl 缺失）时隐藏（单段朗读有浏览器兜底，连播没有）。
    // R172：TED/博客类书同一个按钮改接「原声伴听」（calibre.bookFormat === 'TED'），
    // 不再走 TTS 逐段合成——TED 是整段真人原声，逐段合成会把原声换成机器音。
    var ttsBookBtn = document.getElementById('tts-book');
    var ttsBookStopBtn = document.getElementById('tts-book-stop');
    if (ttsBookBtn) {
        if (TED_BOOK) {
            ttsBookBtn.addEventListener('click', tedAudioToggle);
        } else {
            if (!calibre.readingTtsUrl) ttsBookBtn.style.display = 'none';
            ttsBookBtn.addEventListener('click', bookPlayerToggle);
        }
    }
    if (ttsBookStopBtn) {
        ttsBookStopBtn.addEventListener('click', function () {
            if (TED_BOOK) tedAudioStop();
            else bookPlayerStop(false);
        });
    }
    if (TED_BOOK) {
        // 进阅读页即预取原声元数据 + 段落清单：起播无等待；不可用则隐藏按钮并提示一次
        tedAudioUpdateButtons();
        tedAudioEnsureLoaded().catch(function () {});
    } else {
        bookPlayerUpdateButtons();
    }

    // ===== 段落批注（与翻译/朗读缓存同 ES 文档） =====
    // 段落文本用与翻译/朗读一致的 paragraphSpeechText 归一化，moon-well 按
    // SHA-256(段落) 定位同一份文档：批注自动挂在翻译/音频缓存所在段落上，
    // 批注署名与时间由 moon-well 从登录用户取，前端不传也不能传。

    var annotationPopover = null;
    var annotationPanel = null;
    var annotationRequestSeq = 0;

    // --- AI 伴读批注状态（与批注弹层同生命周期：弹层单例，模块级状态即可） ---
    var companionRoles = null;         // 角色清单缓存（仅 LLM_ANNOTATION 角色）
    var companionRolesPromise = null;  // 防并发重复拉取
    var companionRequestSeq = 0;       // 飞行中弹层关闭/换段时丢弃过期响应
    var companionParagraph = '';       // 当前弹层段落（生成/再生成请求体用）
    var companionChipsEl = null;       // 当前弹层的角色 chips 容器
    var companionListEl = null;        // 当前弹层的 AI 批注列表容器
    var companionEntries = {};         // 当前段落的 AI 批注（roleId → 条目）

    function closeAnnotationPopover() {
        if (annotationPopover) {
            annotationPopover.remove();
            annotationPopover = null;
        }
        companionChipsEl = null;
        companionListEl = null;
        companionEntries = {};
        companionParagraph = '';
    }

    function closeAnnotationPanel() {
        if (annotationPanel) {
            annotationPanel.remove();
            annotationPanel = null;
            if (annotationPanelToggle) annotationPanelToggle.classList.remove('active');
        }
    }

    // ISO 时间 → 可读短格式（2026-09-02T21:30:45 → 2026-09-02 21:30）
    function formatAnnotationTime(value) {
        return String(value || '').replace('T', ' ').slice(0, 16);
    }

    function annotationItem(item) {
        var el = document.createElement('div');
        el.className = 'annotation-item';
        var meta = document.createElement('div');
        meta.className = 'annotation-meta';
        meta.textContent = (item.nickName || mbT('Anonymous')) + ' · ' + formatAnnotationTime(item.annotatedAt);
        var content = document.createElement('div');
        content.className = 'annotation-content';
        content.textContent = item.content || '';
        el.appendChild(meta);
        el.appendChild(content);
        return el;
    }

    function renderAnnotationList(container, items, emptyText) {
        container.textContent = '';
        if (!items || !items.length) {
            var empty = document.createElement('div');
            empty.className = 'annotation-empty';
            empty.textContent = emptyText || mbT('No annotations yet');
            container.appendChild(empty);
            return;
        }
        items.forEach(function (item) {
            container.appendChild(annotationItem(item));
        });
    }

    function loadParagraphAnnotations(paragraph, listEl) {
        var seq = ++annotationRequestSeq;
        renderAnnotationList(listEl, null, mbT('Loading annotations…'));
        $.ajax({
            url: calibre.readingAnnotationListUrl, method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({paragraph: paragraph})
        }).done(function (response) {
            // 请求飞行期间弹层被关闭/换段：丢弃过期响应
            if (seq !== annotationRequestSeq || !annotationPopover) return;
            renderAnnotationList(listEl, response.result || response.data || []);
        }).fail(function (xhr) {
            if (reloadIfCsrfBlocked(xhr)) return;
            if (seq !== annotationRequestSeq || !annotationPopover) return;
            renderAnnotationList(listEl, null, mbT('Failed to load annotations, please retry later'));
        });
    }

    // --- AI 伴读批注：角色清单（页面级缓存一次）、按角色生成、条目渲染 ---

    function loadCompanionRoles() {
        if (companionRoles) return Promise.resolve(companionRoles);
        if (!calibre.readingCompanionRolesUrl) return Promise.reject(new Error('companion roles unavailable'));
        if (!companionRolesPromise) {
            companionRolesPromise = $.ajax({
                url: calibre.readingCompanionRolesUrl, method: 'POST', contentType: 'application/json',
                headers: {'X-CSRFToken': readerCsrfToken()},
                data: JSON.stringify({})
            }).then(function (response) {
                // 只保留 LLM 生成类角色作 chips；翻译/朗读（TRANSLATION/TTS）
                // 走既有 ▶/译 按钮，不并入 AI 批注区
                companionRoles = ((response && (response.result || response.data)) || []).filter(function (role) {
                    return role && role.kind === 'LLM_ANNOTATION';
                });
                return companionRoles;
            }).catch(function (error) {
                // 失败允许下次弹层重试
                companionRolesPromise = null;
                throw error;
            });
        }
        return companionRolesPromise;
    }

    function companionRoleOf(roleId) {
        var match = (companionRoles || []).filter(function (role) {
            return role.roleId === roleId;
        })[0];
        return match || null;
    }

    function companionEmpty(text) {
        var el = document.createElement('div');
        el.className = 'annotation-empty';
        el.textContent = text;
        return el;
    }

    function renderCompanionList() {
        if (!companionListEl) return;
        companionListEl.textContent = '';
        var roleIds = Object.keys(companionEntries);
        if (!roleIds.length) {
            companionListEl.appendChild(companionEmpty(mbT('Pick a role above to let AI generate a companion note for this paragraph')));
            return;
        }
        roleIds.forEach(function (roleId) {
            var entry = companionEntries[roleId];
            var el = document.createElement('div');
            el.className = 'annotation-item ai-annotation-item';
            var meta = document.createElement('div');
            meta.className = 'annotation-meta';
            meta.textContent = '🤖 ' + (entry.roleName || roleId) + ' · ' + formatAnnotationTime(entry.createdAt);
            var regen = document.createElement('span');
            regen.className = 'ai-annotation-regen';
            regen.textContent = mbT('Regenerate');
            regen.title = mbT('Skip the cache and regenerate this annotation (overwrites the old one)');
            regen.addEventListener('click', function () {
                if (regen.classList.contains('is-loading')) return;
                var role = companionRoleOf(roleId) || {roleId: roleId, name: entry.roleName || roleId};
                if (!window.confirm(mbT('Regenerating will overwrite the current “{r}” annotation. Continue?')
                    .replace('{r}', function () { return entry.roleName || roleId; }))) return;
                generateAiAnnotation(role, regen, true);
            });
            meta.appendChild(regen);
            var content = document.createElement('div');
            content.className = 'annotation-content';
            content.textContent = entry.content || '';
            el.appendChild(meta);
            el.appendChild(content);
            companionListEl.appendChild(el);
        });
    }

    // 生成/重新生成：请求期间在触发元素上加 loading 态；成功刷新列表与 chips 完成态。
    // 段落取 companionParagraph（弹层打开时定格）——再生成入口在列表渲染闭包里，
    // 与其逐层传参不如统一读模块状态（弹层单例，状态唯一）。
    function generateAiAnnotation(role, trigger, force) {
        trigger.classList.add('is-loading');
        $.ajax({
            url: calibre.readingCompanionAnnotateUrl, method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({paragraph: companionParagraph, roleId: role.roleId,
                bookName: calibre.bookName || '', chapter: currentChapterTitle(), force: !!force})
        }).done(function (response) {
            var entry = (response && (response.result || response.data)) || null;
            if (!annotationPopover || !entry || !entry.content) {
                readerToast(mbT('AI annotation failed, please retry later'));
                return;
            }
            companionEntries[entry.roleId || role.roleId] = entry;
            renderCompanionList();
            Array.prototype.forEach.call(document.querySelectorAll('.ai-annotation-chip'), function (chip) {
                if (chip.dataset.roleId === (entry.roleId || role.roleId)) chip.classList.add('is-done');
            });
            readerToast(force ? mbT('AI annotation updated') : mbT('AI annotation generated'));
        }).fail(function (xhr) {
            if (reloadIfCsrfBlocked(xhr)) return;
            var message = mbT('AI annotation failed, please retry later');
            try {
                var data = JSON.parse(xhr.responseText);
                if (data && data.message) message = data.message;
            } catch (e) {}
            readerToast(message);
        }).always(function () {
            trigger.classList.remove('is-loading');
        });
    }

    function renderCompanionChips() {
        if (!companionChipsEl) return;
        companionChipsEl.textContent = '';
        loadCompanionRoles().then(function (roles) {
            if (!companionChipsEl || !annotationPopover) return;
            if (!roles.length) {
                companionChipsEl.appendChild(companionEmpty(mbT('No companion roles available')));
                return;
            }
            roles.forEach(function (role) {
                var chip = document.createElement('span');
                chip.className = 'ai-annotation-chip';
                chip.dataset.roleId = role.roleId;
                chip.textContent = role.name;
                chip.title = role.description || role.name;
                if (companionEntries[role.roleId]) chip.classList.add('is-done');
                chip.addEventListener('click', function () {
                    if (chip.classList.contains('is-loading')) return;
                    if (companionEntries[role.roleId]) {
                        readerToast(mbT('This role already has an annotation; use Regenerate on the item to update it'));
                        return;
                    }
                    generateAiAnnotation(role, chip, false);
                });
                companionChipsEl.appendChild(chip);
            });
        }).catch(function () {
            if (!companionChipsEl || !annotationPopover) return;
            companionChipsEl.textContent = '';
            companionChipsEl.appendChild(companionEmpty(mbT('Failed to load roles, please reopen the panel later')));
        });
    }

    function loadCompanionAnnotations(paragraph) {
        if (!calibre.readingCompanionListUrl) return;
        var seq = ++companionRequestSeq;
        // AI 批注是派生缓存：加载失败静默按空处理，不打扰用户批注区
        $.ajax({
            url: calibre.readingCompanionListUrl, method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({paragraph: paragraph})
        }).done(function (response) {
            if (seq !== companionRequestSeq || !annotationPopover) return;
            companionEntries = (response && (response.result || response.data)) || {};
            renderCompanionList();
        }).fail(function () {
            if (seq !== companionRequestSeq || !annotationPopover) return;
            // 静默按空处理；但不清空已有条目（快速生成成功后列表响应才失败的场景）
            if (!Object.keys(companionEntries).length) renderCompanionList();
        });
    }

    // 段落批注弹层：挂在主文档 body（与划词气泡同模式），段落按钮在 iframe
    // 内，坐标需加 iframe 偏移换算到主视口
    function openAnnotationPopover(el, btn) {
        closeAnnotationPopover();
        var paragraph = paragraphSpeechText(el);
        if (!paragraph) return;

        var rect = btn.getBoundingClientRect();
        var frame = btn.ownerDocument.defaultView && btn.ownerDocument.defaultView.frameElement;
        if (frame) {
            var frameRect = frame.getBoundingClientRect();
            rect = {top: rect.top + frameRect.top, bottom: rect.bottom + frameRect.top,
                left: rect.left + frameRect.left, width: rect.width, height: rect.height};
        }

        var popover = document.createElement('div');
        popover.className = 'reading-annotation-popover';

        var header = document.createElement('div');
        header.className = 'annotation-header';
        var title = document.createElement('span');
        title.className = 'annotation-title';
        title.textContent = mbT('Paragraph annotation');
        var closeBtn = document.createElement('span');
        closeBtn.className = 'annotation-close';
        closeBtn.textContent = '×';
        closeBtn.title = mbT('Close (Esc)');
        closeBtn.addEventListener('click', function () { closeAnnotationPopover(); });
        header.appendChild(title);
        header.appendChild(closeBtn);

        var excerpt = document.createElement('div');
        excerpt.className = 'annotation-excerpt';
        excerpt.textContent = paragraph.length > 80 ? paragraph.slice(0, 80) + '…' : paragraph;
        excerpt.title = paragraph;

        // AI 伴读区：角色 chips + 已生成的 AI 批注，位于用户批注列表之上
        var aiSection = document.createElement('div');
        aiSection.className = 'ai-annotation-section';
        var aiTitle = document.createElement('div');
        aiTitle.className = 'ai-annotation-title';
        aiTitle.textContent = mbT('AI Companion');
        var chips = document.createElement('div');
        chips.className = 'ai-annotation-chips';
        var aiList = document.createElement('div');
        aiList.className = 'ai-annotation-list';
        aiList.appendChild(companionEmpty(mbT('Loading AI annotation…')));
        aiSection.appendChild(aiTitle);
        aiSection.appendChild(chips);
        aiSection.appendChild(aiList);

        var list = document.createElement('div');
        list.className = 'annotation-list';

        var input = document.createElement('textarea');
        input.className = 'annotation-input';
        input.placeholder = mbT('Write your annotation for this paragraph… (Ctrl+Enter to submit)');
        input.maxLength = 2000;

        var actions = document.createElement('div');
        actions.className = 'annotation-actions';
        var submit = document.createElement('span');
        submit.className = 'annotation-submit';
        submit.textContent = mbT('Submit annotation');
        var hint = document.createElement('span');
        hint.className = 'annotation-hint';
        hint.textContent = mbT('Esc to close');
        actions.appendChild(submit);
        actions.appendChild(hint);

        popover.appendChild(header);
        popover.appendChild(excerpt);
        popover.appendChild(aiSection);
        popover.appendChild(list);
        popover.appendChild(input);
        popover.appendChild(actions);
        document.body.appendChild(popover);

        // 定位：优先按钮下方，越界翻上方；左右夹紧视口（与划词气泡一致）
        var top = rect.bottom + 8, left = rect.left;
        var bounds = popover.getBoundingClientRect();
        if (top + bounds.height > window.innerHeight) top = Math.max(8, rect.top - bounds.height - 8);
        left = Math.min(Math.max(8, left), window.innerWidth - bounds.width - 8);
        popover.style.top = top + 'px';
        popover.style.left = left + 'px';

        annotationPopover = popover;
        // AI 伴读区状态定格后并行拉角色与已生成批注（与用户批注加载互不阻塞）
        companionParagraph = paragraph;
        companionChipsEl = chips;
        companionListEl = aiList;
        renderCompanionChips();
        loadCompanionAnnotations(paragraph);
        loadParagraphAnnotations(paragraph, list);
        setTimeout(function () { input.focus(); }, 0);

        function submitAnnotation() {
            var content = input.value.trim();
            if (!content) { input.focus(); return; }
            if (submit.classList.contains('is-loading')) return;
            submit.classList.add('is-loading');
            $.ajax({
                url: calibre.readingAnnotationCreateUrl, method: 'POST', contentType: 'application/json',
                headers: {'X-CSRFToken': readerCsrfToken()},
                data: JSON.stringify({paragraph: paragraph, content: content,
                    bookName: calibre.bookName || '', chapter: currentChapterTitle()})
            }).done(function (response) {
                // 头部插入服务端返回的批注（含署名与时间），不整列表重拉
                var item = (response && (response.result || response.data)) ||
                    {nickName: mbT('Me'), content: content};
                var empty = list.querySelector('.annotation-empty');
                if (empty) empty.remove();
                list.insertBefore(annotationItem(item), list.firstChild);
                input.value = '';
                readerToast(mbT('Annotation saved'));
            }).fail(function (xhr) {
                // CSRF 过期/会话重建：刷新页面拿新 token
                if (reloadIfCsrfBlocked(xhr)) return;
                var message = mbT('Failed to save annotation, please retry later');
                try {
                    var data = JSON.parse(xhr.responseText);
                    if (data && data.message) message = data.message;
                } catch (e) {}
                readerToast(message);
            }).always(function () {
                submit.classList.remove('is-loading');
            });
        }

        submit.addEventListener('click', submitAnnotation);
        // Ctrl/Cmd+Enter 提交，Enter 留给多行批注换行
        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                submitAnnotation();
            }
        });
    }

    // --- 本书批注面板（工具栏「批」）---
    var annotationPanelToggle = document.getElementById('reading-annotations');

    function annotationPanelCard(item) {
        var card = document.createElement('div');
        card.className = 'annotation-card';
        var meta = document.createElement('div');
        meta.className = 'annotation-card-meta';
        meta.textContent = item.chapter || mbT('Unknown chapter');
        var excerpt = document.createElement('div');
        excerpt.className = 'annotation-card-excerpt';
        var text = item.paragraph || '';
        excerpt.textContent = text.length > 120 ? text.slice(0, 120) + '…' : text;
        excerpt.title = text;
        var list = document.createElement('div');
        list.className = 'annotation-card-list';
        (item.annotations || []).forEach(function (entry) {
            list.appendChild(annotationItem(entry));
        });
        card.appendChild(meta);
        card.appendChild(excerpt);
        card.appendChild(list);
        return card;
    }

    function openAnnotationPanel() {
        closeAnnotationPanel();
        var overlay = document.createElement('div');
        overlay.className = 'reading-annotation-panel';
        var panel = document.createElement('div');
        panel.className = 'annotation-panel-card';

        var header = document.createElement('div');
        header.className = 'annotation-header';
        var title = document.createElement('span');
        title.className = 'annotation-title';
        title.textContent = mbT('Book annotations');
        var closeBtn = document.createElement('span');
        closeBtn.className = 'annotation-close';
        closeBtn.textContent = '×';
        closeBtn.title = mbT('Close (Esc)');
        closeBtn.addEventListener('click', closeAnnotationPanel);
        header.appendChild(title);
        header.appendChild(closeBtn);

        var list = document.createElement('div');
        list.className = 'annotation-panel-list';
        panel.appendChild(header);
        panel.appendChild(list);
        overlay.appendChild(panel);
        document.body.appendChild(overlay);
        annotationPanel = overlay;
        if (annotationPanelToggle) annotationPanelToggle.classList.add('active');

        // 点击半透明背景关闭（面板内部点击不关）
        overlay.addEventListener('mousedown', function (ev) {
            if (ev.target === overlay) closeAnnotationPanel();
        });

        renderAnnotationList(list, null, mbT('Loading annotations…'));
        $.ajax({
            url: calibre.readingAnnotationBookUrl, method: 'POST', contentType: 'application/json',
            headers: {'X-CSRFToken': readerCsrfToken()},
            data: JSON.stringify({bookName: calibre.bookName || ''})
        }).done(function (response) {
            var paragraphs = response.result || response.data || [];
            list.textContent = '';
            if (!paragraphs.length) {
                renderAnnotationList(list, null, mbT('No annotations in this book yet — click ✎ next to a paragraph to add one'));
                return;
            }
            paragraphs.forEach(function (item) {
                list.appendChild(annotationPanelCard(item));
            });
        }).fail(function (xhr) {
            if (reloadIfCsrfBlocked(xhr)) return;
            renderAnnotationList(list, null, mbT('Failed to load annotations, please retry later'));
        });
    }

    if (annotationPanelToggle) {
        annotationPanelToggle.addEventListener('click', function () {
            if (annotationPanel) closeAnnotationPanel();
            else openAnnotationPanel();
        });
    }

    reader.rendition.on('rendered', function (section, view) {
        var content = view && view.contents;
        if (content && content.document) {
            bindSelectionTranslation(content);
            injectParagraphTools(content);
            // R172 TED 原声伴听：段落点击切播（跳到该段原声位置）
            if (tedAudioPlayer && tedAudioPlayer.active) {
                tedAudioBindSeek(content.document);
            }
        }
        // 新章节渲染后仅回填缓存译文，翻译由段落按钮/工具栏手动触发
        if (translationEnabled()) setTimeout(restoreCachedTranslations, 60);
        // R157 整本连播：翻章/重渲染时重建播放队列（播放器自身翻章走 internalNav 分支）
        if (bookPlayer && bookPlayer.active) bookPlayerOnRendered(section, view);
        // R172 TED 原声伴听：翻章/重渲染后重建段落↔时间轴对齐并续高亮
        if (tedAudioPlayer && tedAudioPlayer.active) tedAudioOnRendered(section, view);
    });

    document.addEventListener('mousedown', function (event) {
        // 点击浮层外部一律关闭（划词气泡 / 右键菜单 / 段落批注弹层 / 书批注面板）；
        // 菜单项自身不能在 mousedown 被关掉，否则 click 到不了菜单项
        if (selectionMenu && !selectionMenu.contains(event.target)) {
            closeSelectionMenu();
        }
        if (translationPopover && !translationPopover.contains(event.target)
            && !(wordDetailPanel && wordDetailPanel.contains(event.target))) {
            // 详解面板是气泡的兄弟节点：面板内点击不算「点气泡外」，
            // 否则会在面板里按鼠标时把气泡和面板一起收走（审查 P0）
            closeTranslationPopover();
        }
        if (annotationPopover && !annotationPopover.contains(event.target)) {
            closeAnnotationPopover();
        }
        // 工具栏切换按钮不属于面板，但点击它应由 click handler 负责关闭，
        // 不能被这里的 mousedown 先关后又在 click 中重新打开。
        var clickedAnnotationToggle = annotationPanelToggle &&
            (event.target === annotationPanelToggle || annotationPanelToggle.contains(event.target));
        if (annotationPanel && !annotationPanel.contains(event.target) && !clickedAnnotationToggle) {
            closeAnnotationPanel();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Escape') return;
        // 分层退出：划词右键菜单（最表层）→ 书批注面板 → 段落批注弹层 →
        // 划词气泡，一次 Esc 只关一层并阻断后续监听（本 handler 先于
        // ai_chat.js 注册，stopImmediatePropagation 可阻断其 jQuery 委托监听），
        // 多层面板同开时逐层退出；全部关闭时不阻断，ai_chat.js 正常关抽屉。
        if (selectionMenu) {
            closeSelectionMenu();
            event.stopImmediatePropagation();
            return;
        }
        if (annotationPanel) {
            closeAnnotationPanel();
            event.stopImmediatePropagation();
            return;
        }
        if (annotationPopover) {
            closeAnnotationPopover();
            event.stopImmediatePropagation();
            return;
        }
        if (!translationPopover) return;
        closeTranslationPopover();
        event.stopImmediatePropagation();
    });

    // 供 ai_chat.js 的 ESC 分层关闭：划词气泡打开时 ESC 只关气泡，
    // 不连带关闭 AI 抽屉（两个面板同时打开时逐层退出）
    window.ReaderTranslation = {
        isOpen: function () { return !!translationPopover; }
    };

    // 取当前渲染位置（含当前页 start/end CFI）。ePubReader 包装器上没有
    // currentLocation 方法，入口在 rendition 上；本 bundle 的
    // rendition.currentLocation() 同步返回 location 对象。
    // 旧代码误用 reader.currentLocation（undefined），导致 CFI 永远为空，
    // currentPageText 取不到当前页文本。
    function renditionLocation() {
        try {
            var fn = reader.rendition && reader.rendition.currentLocation;
            if (typeof fn !== "function") return null;
            var location = fn.call(reader.rendition);
            if (location && typeof location.then === "function") return null;
            return location && location.start ? location : null;
        } catch (e) {
            return null;
        }
    }

    // 获取当前章节的真实标题。旧实现读取 #chapter-title，但该元素被
    // reader.min.js 的 MetaController 填充为书籍作者而非章节名，
    // 导致上报给 moon-well 的 chapter 字段错误。
    function currentChapterTitle() {
        var label = '';
        try {
            var location = renditionLocation();
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

    // AI 伴读桥接：聊天面板经 window.AICompanion 读取当前章节与当前页生词
    // （注入 /ai/chat 的 system prompt），与 ai_page_extract.js 的桥接模式一致
    window.AICompanion = window.AICompanion || {};
    window.AICompanion.getChapter = function () { return currentChapterTitle() || ''; };
    window.AICompanion.getUnfamiliarWords = function () {
        return Object.keys(vocabularyRecords).filter(function (word) {
            var record = vocabularyRecords[word];
            return record && record.unknown;
        }).slice(0, 30);
    };

    // 收集当前可见「页」的文本（异步回调）。
    // EPUB.js 的 getContents() 返回整个 section 文档（iframe 内整章内容经 CSS 分栏
    // 分页），直接取 body.innerText 会把整章文本都上报（可达数十 KB）。
    // 仅使用 currentLocation() 的 start/end CFI 经 book.getRange() 精确取
    // 「当前页」文本；CFI 定位失败时返回空串（本轮不上报），绝不退回整章文本。
    function currentPageText(done) {
        var startCfi = null, endCfi = null;
        try {
            var location = renditionLocation();
            startCfi = location && location.start && location.start.cfi;
            endCfi = location && location.end && location.end.cfi;
        } catch (e) {}
        if (!startCfi || !endCfi) { done(''); return; }
        try {
            Promise.all([reader.book.getRange(startCfi), reader.book.getRange(endCfi)]).then(function (ranges) {
                var sr = ranges && ranges[0], er = ranges && ranges[1];
                if (!sr || !er || !sr.startContainer || !er.startContainer) { done(''); return; }
                var doc = sr.startContainer.ownerDocument;
                if (!doc || !doc.createRange) { done(''); return; }
                var range = doc.createRange();
                range.setStart(sr.startContainer, sr.startOffset);
                range.setEnd(er.endContainer, er.endOffset);
                done((range.toString() || '').trim());
            }).catch(function () { done(''); });
        } catch (e) { done(''); }
    }

    function markVocabulary(records) {
        // 扩展高亮引擎在跑时不画内置波浪线（它经 contentDocument 跨文档标注，同页并存
        // 就是一个词两条线）；引擎关了 / 未登录 / 站点被禁用时它会自己清掉标记，内置随即
        // 回来。这里只停 DOM 标注，不停 inspectVocabulary 的请求：那份上报同时是
        // moon-well 阅读事件流（学情、成就解锁）和 AI 伴读「当前页生词」上下文的数据来源。
        if (lensOwnsHighlight()) return;
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
                    // Why: 暂时下线生词信息的两种展示（悬停 tooltip / 点击 alert）——
                    // 「释义 + 上次：书 · 章节」文本太长干扰阅读，仅保留波浪线标注；
                    // 恢复时连同取消注释即可（moon-well analyze 也已暂停返回 translation）。
                    // span.title = (record.translation || '点击查看学习记录') +
                    //     (record.lastBookName ? '\n上次：' + record.lastBookName + ' · ' + (record.lastChapter || '') : '');
                    span.dataset.word = word;
                    // span.addEventListener('click', function () {
                    //     alert(this.title);
                    // });
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

            var location = renditionLocation();
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
            }).fail(function (xhr) {
                // CSRF 过期/会话重建：刷新页面拿新 token，恢复生词标注
                reloadIfCsrfBlocked(xhr);
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
    reader.rendition.on('relocated', function () {
        // 翻页后旧气泡/批注弹层/右键菜单的坐标基于已换下的页面，必须关闭
        closeTranslationPopover();
        closeAnnotationPopover();
        closeSelectionMenu();
        setTimeout(inspectVocabulary, 120);
    });

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
            // CSRF 过期/会话重建：刷新页面拿新 token，不要弹「error」误导
            if (reloadIfCsrfBlocked(xhr)) return;
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

/* global $, calibre, EPUBJS, ePubReader */

var reader;

(function () {
    "use strict";
  // R112: i18n 取词（种子缺失时回退 msgid 本身）
  var mbT = window.mbT || function (id) { return id; };
  // R183（B4 批次 1）：横切原语单点（toast / CSRF 自愈 / 段落口径），实现见 reader-core.js
  var RC = window.ReaderCore;
  // R183（B4 批次 2）：单词详解面板（R123）实现见 reader-word-detail.js
  var RD = window.ReaderWordDetail;
  // R183（B4 批次 3）：段落批注 / AI 伴读批注 / 本书批注面板实现见 reader-annotations.js
  var AN = window.ReaderAnnotations;
  // R183（B4 批次 4）：划词簇实现见 reader-selection.js
  var RS = window.ReaderSelection;
  // R183（B4 批次 5）：沉浸式翻译实现见 reader-immersive.js
  var RI = window.ReaderImmersive;
  // R183（B4 批次 6）：TED 原声伴听实现见 reader-ted-audio.js
  var RT = window.ReaderTedAudio;
  if (!RD || !AN || !RS || !RI || !RT) {
      // Why 显式报错而不是静默跳过：详解与批注面板会整块失效，静默降级在界面上的表现是
      // 「详按钮/批注按钮点了没反应」，用户报障永远指不到载入顺序这一步
      console.error('[reader] reader 模块未载入（word-detail / annotations / selection / immersive / ted-audio），划词·详解·批注·整本译文·原声伴听能力不可用');
  }

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

    // ===== 划词簇（气泡 / 发音 / 生词标记 / 右键菜单）——实现已迁出 reader-selection.js（R183 B4 批次 4）=====
    // 三份浮层状态（translationPopover / popoverHideTimer / selectionMenu）随之归模块，本文件
    // 只在装配处以 RS.* 使用它，并把两张「只有装配层才有」的依赖注入回去：生词台账与
    // 浏览器朗读的 utterance 组装（function 声明提升，此处引用在载入期即有效）。
    RS.setHost({
        markVocabulary: markVocabulary,
        buildSpeechUtterance: buildSpeechUtterance,
        startWholeBookProgressPolling: startWholeBookProgressPolling,
        getWordRecord: function (word) { return vocabularyRecords[word]; },
        applyWordRecord: function (word, unknown) {
            var record = vocabularyRecords[word];
            if (record) {
                record.unknown = unknown;
            } else {
                vocabularyRecords[word] = {word: word, unknown: unknown};
            }
            return Object.keys(vocabularyRecords).map(function (w) { return vocabularyRecords[w]; });
        }
    });
    // ===== 单词详解面板（R123）——实现已迁出 reader-word-detail.js（R183 B4 批次 2）=====
    // 面板 DOM/请求守卫/六板块渲染都在模块内；这里只留气泡调用点需要的薄委托与宿主回调。
    function appendWordDetailButton(popover, text) {
        RD.appendButton(popover, text);
    }

    // Why 注入回调而不是让模块反向 import：词形归一与气泡自动隐藏定时器归 reader-selection.js
    // 持有（批次 4），详解面板只经这三个回调请求「取词口径 / 挂起 / 恢复倒计时」，
    // 不碰气泡内部状态——R125「面板存活期间挂起气泡 5s 倒计时」的语义因此仍只有一份真相
    RD.setHost({
        normalizedWord: RS.normalizedWord,
        schedulePopoverHide: RS.scheduleHide,
        cancelAutoHide: RS.cancelAutoHide
    });


    // ===== 段落朗读（TTS）+ 沉浸式翻译 =====

    var TTS_ENGINE_KEY = "calibre.reader.ttsEngine";

    // 翻译内容自动隐藏时长：按原文词数动态折算——配置值是「每 100 词显示的
    // 秒数」，段落/选区越长显示越久，供「看一眼译文继续读原文」的使用方式；
    // 0 = 一直显示（关闭自动隐藏）。新 key 与旧的固定秒数语义区分，
    // 旧值不会被误读为每 100 词秒数。键名与默认值出自 reader-core.js（单一真相，
    // 设置面板与折算实现必须读同一个 key，R183）
    var TRANSLATION_DISPLAY_KEY = RC.TRANSLATION_DISPLAY_KEY;
    var TRANSLATION_DISPLAY_DEFAULT = RC.TRANSLATION_DISPLAY_DEFAULT;
    // 配置值同时是最小显示秒数：折算不足时按配置值整秒显示，避免单词/短句一闪而过

    // R183（B4 批次 1）：以下三组实现已下沉 reader-core.js（window.ReaderCore），
    // 这里保留同名薄委托——调用点与静态锁的计数口径都不变，一个过渡期后再逐步改直调。
    function translationDisplaySecondsPer100() {
        return RC.translationDisplaySecondsPer100();
    }

    function countWords(text) {
        return RC.countWords(text);
    }

    function translationDisplaySecondsFor(sourceText) {
        return RC.translationDisplaySecondsFor(sourceText);
    }

    function readerCsrfToken() {
        return RC.csrfToken();
    }

    function reloadIfCsrfBlocked(xhrOrText) {
        return RC.reloadIfCsrfBlocked(xhrOrText);
    }

    function injectReaderToolsStyle(doc) {
        RC.injectToolsStyle(doc);
    }

    function collectParagraphElements(doc) {
        return RC.collectParagraphs(doc);
    }

    function paragraphSpeechText(el) {
        return RC.paragraphSpeechText(el);
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
                    RI.translateParagraph(el, trBtn);
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
                    AN.openPopover(el, noteBtn);
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
                    AN.openPopover(el, aiBtn);
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
        if (RT.isActive()) RT.stop();  // TED 原声让位（状态归 reader-ted-audio.js） // TED 原声让位
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

    // ===== R172 TED 原声伴听——实现已迁出 reader-ted-audio.js（R183 B4 批次 6）=====
    // 探测/时间轴/点段切播/与整本连播的互斥都在模块内；本文件注入互斥动作与翻页口径，
    // 并把 RT.* 交给 reader-immersive.js 的宿主回调（L 域翻译时要先停原声）。
    RT.setHost({
        bookPlayerStop: bookPlayerStop,
        bookPlayerToggle: bookPlayerToggle,
        stopTts: stopTts,
        ttsButtonsRender: ttsButtonsRender,
        findTocLabel: findTocLabel,
        followPageInSection: followPageInSection,
        renditionLocation: renditionLocation,
        bookPlayerActive: function () { return !!(bookPlayer && bookPlayer.active); }
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
            RI.rescheduleVisibleTranslations();
        });
    }

    // ===== 沉浸式翻译——实现已迁出 reader-immersive.js（R183 B4 批次 5）=====
    // 译文插入/缓存/显隐/重试都在模块内；它要与两种整段播放器互斥并取章标题做译文缓存键，
    // 这些状态只有本文件（I/J 节与装配层）持有，故注入回调 + 显式 init（模块载入期不能跑，
    // 那一刻宿主还没注入，跑起来是静默空操作）。I/J 拆出去后这六个回调应收敛成一个播放仲裁器。
    RI.setHost({
        bookPlayerStop: bookPlayerStop,
        bookPlayerUpdateButtons: bookPlayerUpdateButtons,
        tedAudioStop: RT.stop,
        tedAudioUpdateButtons: RT.updateButtons,
        tedAudioEnsureLoaded: RT.ensureLoaded,
        tedAudioActive: RT.isActive,
        bookListenToggle: RT.listenToggle,
        isTedBook: RT.isTedBook,
        currentChapterTitle: currentChapterTitle
    });
    RI.init();

    // ===== 段落批注 / AI 伴读批注 / 本书批注面板 ——实现已迁出 reader-annotations.js（R183 B4 批次 3）=====
    // 弹层/面板/角色 chips/请求序号守卫都在模块内；本文件只在五个入口处以 AN.* 调用它，
    // 并把章标题口径注入回去（装配层才持有 rendition/toc，模块不得反向 import 本文件私有函数）。
    AN.setHost({ currentChapterTitle: currentChapterTitle });
    reader.rendition.on('rendered', function (section, view) {
        var content = view && view.contents;
        if (content && content.document) {
            RS.bindFrame(content);
            injectParagraphTools(content);
            // R172 TED 原声伴听：段落点击切播（跳到该段原声位置）
            if (RT.isActive()) {
                RT.bindSeek(content.document);
            }
        }
        // 新章节渲染后仅回填缓存译文，翻译由段落按钮/工具栏手动触发
        if (RI.enabled()) setTimeout(RI.restoreCachedTranslations, 60);
        // R157 整本连播：翻章/重渲染时重建播放队列（播放器自身翻章走 internalNav 分支）
        if (bookPlayer && bookPlayer.active) bookPlayerOnRendered(section, view);
        // R172 TED 原声伴听：翻章/重渲染后重建段落↔时间轴对齐并续高亮
        if (RT.isActive()) RT.onRendered(section, view);
    });

    document.addEventListener('mousedown', function (event) {
        // 点击浮层外部一律关闭（划词气泡 / 右键菜单 / 段落批注弹层 / 书批注面板）；
        // 菜单项自身不能在 mousedown 被关掉，否则 click 到不了菜单项
        if (RS.isMenuOpen() && !RS.menuContainsNode(event.target)) {
            RS.closeMenu();
        }
        if (RS.isPopoverOpen() && !RS.popoverContainsNode(event.target)
            && !RD.containsNode(event.target)) {
            // 详解面板是气泡的兄弟节点：面板内点击不算「点气泡外」，
            // 否则会在面板里按鼠标时把气泡和面板一起收走（审查 P0）
            RS.closePopover();
        }
        if (AN.isPopoverOpen() && !AN.containsNode(event.target)) {
            AN.closePopover();
        }
        // 工具栏切换按钮不属于面板，但点击它应由 click handler 负责关闭，
        // 不能被这里的 mousedown 先关后又在 click 中重新打开。
        if (AN.isPanelOpen() && !AN.panelContainsNode(event.target) && !AN.isToggleClick(event.target)) {
            AN.closePanel();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Escape') return;
        // 分层退出：划词右键菜单（最表层）→ 书批注面板 → 段落批注弹层 →
        // 划词气泡，一次 Esc 只关一层并阻断后续监听（本 handler 先于
        // ai_chat.js 注册，stopImmediatePropagation 可阻断其 jQuery 委托监听），
        // 多层面板同开时逐层退出；全部关闭时不阻断，ai_chat.js 正常关抽屉。
        if (RS.isMenuOpen()) {
            RS.closeMenu();
            event.stopImmediatePropagation();
            return;
        }
        if (AN.isPanelOpen()) {
            AN.closePanel();
            event.stopImmediatePropagation();
            return;
        }
        if (AN.isPopoverOpen()) {
            AN.closePopover();
            event.stopImmediatePropagation();
            return;
        }
        if (!RS.isPopoverOpen()) return;
        RS.closePopover();
        event.stopImmediatePropagation();
    });

    // 供 ai_chat.js 的 ESC 分层关闭：划词气泡打开时 ESC 只关气泡，
    // 不连带关闭 AI 抽屉（两个面板同时打开时逐层退出）
    window.ReaderTranslation = {
        isOpen: RS.isPopoverOpen
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
        if (RS.lensOwnsHighlight()) return;
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
        RS.closePopover();
        AN.closePopover();
        RS.closeMenu();
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

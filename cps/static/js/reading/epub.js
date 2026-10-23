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
  // R183（B4 批次 7）：段落朗读与整本连播实现见 reader-tts.js
  var RTTS = window.ReaderTts;
  if (!RD || !AN || !RS || !RI || !RT || !RTTS) {
      // Why 显式报错而不是静默跳过：详解与批注面板会整块失效，静默降级在界面上的表现是
      // 「详按钮/批注按钮点了没反应」，用户报障永远指不到载入顺序这一步
      console.error('[reader] reader 模块未载入（见 read.html 的 js/reading/* 顺序），划词·详解·批注·译文·原声·朗读能力不可用');
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
                // R213-B：位置来源优先级 = 服务端（账号级、跨设备）> localStorage（本机兜底）。
                // Why 不是简单二选一：老账号在服务端还没有记录，第一次进阅读器时服务端为空，
                // 此时仍要用本地位置，并由 relocated 的首次上报自然完成回填（不写迁移脚本）。
                var _savedPos = null;
                try {
                    var _srv = (window.calibre && window.calibre.readerPosition) || {};
                    if (_srv && _srv.position) {
                        _savedPos = JSON.stringify({
                            cfi: _srv.position,
                            percentage: typeof _srv.percent === "number" ? _srv.percent / 100 : undefined,
                        });
                    }
                } catch (eSrv) {}
                if (!_savedPos) {
                    _savedPos = localStorage.getItem(position_key);
                }
                try {
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

                    // R213-B：同时上报账号级位置（跨设备可见）。节流与卸载补发在
                    // reader-progress.js 内，这里只负责把「当前真实位置」交出去。
                    // 页码口径直接复用上面 locations 的 current/total —— 与阅读器顶部
                    // 显示的 37/125 必须同源，否则首页卡片与阅读器会显示两个页码。
                    try {
                        if (window.ReaderProgress) {
                            window.ReaderProgress.update({
                                position: cfi,
                                percent: percentage,
                                page: total > 0 ? current : undefined,
                                total: total > 0 ? total : undefined,
                            });
                        }
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
                contentType: 'application/json', headers: {'X-CSRFToken': RC.csrfToken()},
                data: JSON.stringify({job_id: jobId})
            }).done(function (result) {
                if (result && (result.status === 'COMPLETED' || result.status === 'PARTIAL_FAILED')) {
                    clearInterval(wholeBookPollTimer);
                    wholeBookPollTimer = null;
                    RC.toast(result.status === 'COMPLETED'
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
        buildSpeechUtterance: RTTS.buildSpeechUtterance,
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


    // ===== 段落朗读与整本连播（TTS）——实现已迁出 reader-tts.js（R183 B4 批次 7）=====
    // 逐段合成/浏览器兜底、按钮注入、连播状态机与翻章续播都在模块内；宿主只注入章标题
    // 与阅读位置两件装配层才有的事。
    RTTS.setHost({
        currentChapterTitle: currentChapterTitle,
        renditionLocation: renditionLocation
    });
    // ===== R172 TED 原声伴听——实现已迁出 reader-ted-audio.js（R183 B4 批次 6）=====
    // 探测/时间轴/点段切播/与整本连播的互斥都在模块内；本文件注入互斥动作与翻页口径，
    // 并把 RT.* 交给 reader-immersive.js 的宿主回调（L 域翻译时要先停原声）。
    RT.setHost({
        bookPlayerStop: RTTS.bookPlayerStop,
        bookPlayerToggle: RTTS.bookPlayerToggle,
        stopTts: RTTS.stopTts,
        ttsButtonsRender: RTTS.ttsButtonsRender,
        findTocLabel: findTocLabel,
        followPageInSection: RTTS.followPageInSection,
        renditionLocation: renditionLocation,
        bookPlayerActive: RTTS.bookPlayerActive
    });
    // --- 朗读引擎设置 ---
    var ttsEngineSelect = document.getElementById('ttsEngine');
    if (ttsEngineSelect) {
        ttsEngineSelect.value = RTTS.getTtsEngine();
        ttsEngineSelect.addEventListener('change', function () {
            // 整本连播固定走 AI 语音：切换引擎时直接结束连播，状态可预期
            if (RTTS.bookPlayerActive()) RTTS.bookPlayerStop(false);
            RTTS.stopTts();
            try { localStorage.setItem(RTTS.TTS_ENGINE_KEY, ttsEngineSelect.value); } catch (e) {}
        });
    }

    // --- 翻译显示时长设置（每 100 词秒数，同时是最小显示秒数）：改动即时保存，已显示的译文重新计时 ---
    var translationDisplayInput = document.getElementById('translationDisplaySecondsPer100');
    if (translationDisplayInput) {
        translationDisplayInput.value = String(RC.translationDisplaySecondsPer100());
        translationDisplayInput.addEventListener('change', function () {
            var value = parseInt(translationDisplayInput.value, 10);
            if (isNaN(value) || value < 0) value = RC.TRANSLATION_DISPLAY_DEFAULT;
            translationDisplayInput.value = String(value);
            try { localStorage.setItem(RC.TRANSLATION_DISPLAY_KEY, String(value)); } catch (e) {}
            // R215：段落译文不再自动隐藏；该设置只剩划词气泡仍在用，改动后重排气泡计时
            if (RS.isPopoverOpen()) RS.scheduleHide();
        });
    }

    // ===== 沉浸式翻译——实现已迁出 reader-immersive.js（R183 B4 批次 5）=====
    // 译文插入/缓存/显隐/重试都在模块内；它要与两种整段播放器互斥并取章标题做译文缓存键，
    // 这些状态只有本文件（I/J 节与装配层）持有，故注入回调 + 显式 init（模块载入期不能跑，
    // 那一刻宿主还没注入，跑起来是静默空操作）。I/J 拆出去后这六个回调应收敛成一个播放仲裁器。
    RI.setHost({
        bookPlayerStop: RTTS.bookPlayerStop,
        bookPlayerUpdateButtons: RTTS.bookPlayerUpdateButtons,
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
            RTTS.injectParagraphTools(content);
            // R215：翻译模式下单击段落 → 选中并在右栏显示译文（不再向正文插节点）
            RI.bindContent(content);
            // R172 TED 原声伴听：段落点击切播（跳到该段原声位置）
            if (RT.isActive()) {
                RT.bindSeek(content.document);
            }
        }
        // R157 整本连播：翻章/重渲染时重建播放队列（播放器自身翻章走 internalNav 分支）
        if (RTTS.bookPlayerActive()) RTTS.bookPlayerOnRendered(section, view);
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
                RC.reloadIfCsrfBlocked(xhr);
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
            if (RC.reloadIfCsrfBlocked(xhr)) return;
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

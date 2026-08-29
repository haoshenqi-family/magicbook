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

    reader.rendition.on('rendered', function (section, view) {
        var content = view && view.contents;
        if (content && content.document) bindSelectionTranslation(content);
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

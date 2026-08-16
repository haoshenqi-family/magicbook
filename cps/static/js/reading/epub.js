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
    // Words that have already been sent to moon-well this session, to avoid re-requesting.
    var vocabularySeen = {};
    // word -> latest record returned by moon-well, kept across page turns so that
    // re-rendered pages (going back to a previously read page) can be re-marked.
    var vocabularyRecords = {};

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

    function visibleWords() {
        var words = {};
        reader.rendition.getContents().forEach(function (content) {
            var doc = content.document;
            if (!doc || !doc.body) return;
            var walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
            var node;
            while ((node = walker.nextNode())) {
                var sentence = (node.parentElement && node.parentElement.textContent || node.textContent || '').trim();
                (node.textContent.match(/\b[A-Za-z][A-Za-z'’-]*\b/g) || []).forEach(function (raw) {
                    var word = raw.toLowerCase().replace(/[’']/g, "'");
                    // 收集所有可见词（不做 seen 过滤），以便翻回已读页时用缓存重新标注
                    if (word.length > 1) words[word] = sentence.slice(0, 500);
                });
            }
        });
        return words;
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
        // 上一请求仍在飞行：标记待重检并跳过本次，避免漏标新页面的生词
        if (vocabularyInFlight) {
            vocabularyRetryPending = true;
            return;
        }
        var words = visibleWords(), list = Object.keys(words);
        if (!list.length) return;

        // 已缓存 records 的词直接用缓存重新标注（翻页/翻回时 DOM 重建），
        // 仅对从未请求过的词发起网络请求。
        var cachedRecords = [], fresh = [];
        list.forEach(function (word) {
            if (vocabularyRecords[word]) {
                cachedRecords.push(vocabularyRecords[word]);
            } else if (!vocabularySeen[word]) {
                fresh.push(word);
            }
        });
        if (cachedRecords.length) markVocabulary(cachedRecords);

        if (!fresh.length) return;
        vocabularyInFlight = true;
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
                words: fresh.map(function (word) { return {word: word, sentence: words[word]}; })})
        }).done(function (response) {
            var records = response.result || response.data || [];
            fresh.forEach(function (word) { vocabularySeen[word] = true; });
            (records || []).forEach(function (record) {
                if (record && record.word) vocabularyRecords[record.word] = record;
            });
            markVocabulary(records);
        }).always(function () {
            vocabularyInFlight = false;
            // 飞行期间有过翻页（pending 被置位）：请求完成后重检当前页，
            // 保证翻页过快时生词也能被标注
            if (vocabularyRetryPending) {
                vocabularyRetryPending = false;
                setTimeout(inspectVocabulary, 50);
            }
        });
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

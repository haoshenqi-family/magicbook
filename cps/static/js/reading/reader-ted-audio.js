/* global $, calibre */

/**
 * R183（架构评审 B4 批次 6）：R172 TED / 博客类整段原声伴听——元数据与段落清单探测、
 * 时间轴高亮、点段切播，与 R157 整本 TTS 连播互斥。
 *
 * 载入顺序：… → reader-selection.js → reader-immersive.js → 本文件 → epub.js
 * （本文件被 reader-immersive.js 的宿主回调用到，故注入方向是 epub.js 把 RT.* 交给 RI，
 * 不存在反向 import。）
 *
 * 宿主回调七个：两种播放器的互斥要靠彼此（stopTts / bookPlayerStop / bookPlayerToggle /
 * ttsButtonsRender 在 H、I 节），翻页与章标题口径只有装配层持有（renditionLocation /
 * followPageInSection / findTocLabel）。I 节拆出后这组回调应连同 immersive 的八个一起
 * 收敛成播放仲裁器。
 */
(function () {
    "use strict";

    var RC = window.ReaderCore;
    var mbT = window.mbT || function (id) { return id; };

    var host = {
        bookPlayerStop: function () { },
        bookPlayerToggle: function () { },
        stopTts: function () { },
        ttsButtonsRender: function () { },
        findTocLabel: function () { return ''; },
        followPageInSection: function () { return Promise.resolve(); },
        renditionLocation: function () { return null; },
        bookPlayerActive: function () { return false; }
    };

    // core 同名别名：正文与 epub.js 时代逐字一致，静态锁继续成立
    var readerToast = function (m) { RC.toast(m); };
    var readerCsrfToken = function () { return RC.csrfToken(); };
    var reloadIfCsrfBlocked = function (x) { return RC.reloadIfCsrfBlocked(x); };
    var collectParagraphElements = function (doc) { return RC.collectParagraphs(doc); };
    // ===== R172 TED 原声伴听：整段原声 + 时间轴高亮（与 bookPlayer 互斥） =====
    // Why 与整本 TTS 连播分设两个状态机：TED/博客类书的内容本质是「一段连续原声」，
    // 文本段落只是这段录音上的时间轴切片；对 TED 走逐段 TTS 会把真人原声换成机器音
    // （语义错），且一场演讲数万字白烧算力/积分。普通小说书没有原声，仍走 bookPlayer。
    // 分流判据：**不能**用 calibre.bookFormat —— 那是 Calibre 文件格式（epub/pdf/txt，
    // read.html 里来自 URL 的 book_format 段），与 moon-well BookFormatEnum.TED 同名不同义；
    // 而 TED 书在 Calibre 里同样是 epub ⇒ `=== 'TED'` 恒 false（R172 首版因此从未生效）。
    // 改为运行时探测 moon-well /book/ted-audio：有 audioUrl（整段原声）就用原声伴听，
    // 否则回落 R157 整本 TTS 连播（普通书与「TED 但未缓存原声」都走这条，探测无法区分两者）。
    var TED_BOOK = false;  // 由 tedAudioEnsureLoaded() 的探测结果置位
    var tedAudioPlayer = null;  // 播放态；与 bookPlayer 互斥（任一时刻至多一个非空）
    var tedAudioData = null;    // 预取结果：{audioUrl, segments:[], byChapter:{}}
    var tedAudioLoad = null;    // 预取 Promise（进阅读页即发起，起播不等待）
    var tedAudioMetaOk = null;  // 原声是否可用（null=探测中，false=无原声）

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

    // 探测完成后的按钮可用性：有原声 → 保持可见（接原声伴听）；无原声 → 看 TTS 端点
    // （有 readingTtsUrl 则回落整本连播、保留按钮；两者都没有才隐藏）。
    // 不再提示「原声未缓存」：探测区分不了「普通书」与「TED 但未缓存原声」，提示会误伤普通书。
    function tedAudioApplyAvailability() {
        var btn = document.getElementById('tts-book');
        if (!btn) return;
        if (tedAudioMetaOk) return;
        if (calibre.readingTtsUrl) return;
        btn.style.display = 'none';
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
            TED_BOOK = tedAudioMetaOk;  // 有整段原声 → 本页按原声伴听分流
            tedAudioApplyAvailability();
            return tedAudioData;
        }).catch(function (err) {
            tedAudioMetaOk = false;
            TED_BOOK = false;
            tedAudioApplyAvailability();
            throw err;
        });
        return tedAudioLoad;
    }

    function tedAudioUpdateButtons() { host.ttsButtonsRender(tedAudioPlayer); }

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
                    var label = host.findTocLabel(nav.toc, section.href);
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
        host.followPageInSection(st.section, el);
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
        host.stopTts();
        if (host.bookPlayerActive()) host.bookPlayerStop(false); // 两模式互斥（bookPlayer 归 I 节）
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
            var loc = host.renditionLocation();
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

    // 整本朗读按钮的统一入口：先确保原声探测完成（首次点击可能仍在途，复用同一 Promise），
    // 再决定走原声伴听还是 R157 整本 TTS 连播。TED 判据只能由探测给出（见 TED_BOOK 定义处）。
    function bookListenToggle() {
        if (host.bookPlayerActive()) { host.bookPlayerToggle(); return; }   // 正在 TTS 连播：切换暂停
        if (TED_BOOK || (tedAudioPlayer && tedAudioPlayer.active)) { tedAudioToggle(); return; }
        tedAudioEnsureLoaded().then(function (data) {
            if (data && data.audioUrl) { TED_BOOK = true; tedAudioToggle(); return; }
            if (calibre.readingTtsUrl) host.bookPlayerToggle();
        }).catch(function () {
            if (calibre.readingTtsUrl) host.bookPlayerToggle();
        });
    }

    // 离开阅读页 / 换书：释放整段原声
    window.addEventListener('pagehide', function () {
        if (tedAudioPlayer) tedAudioStop();
    });


    window.ReaderTedAudio = {
        /** 宿主（epub.js）注入两种播放器的互斥动作与翻页/章标题口径 */
        setHost: function (next) {
            Object.keys(next).forEach(function (k) { if (next[k]) host[k] = next[k]; });
        },
        ensureLoaded: tedAudioEnsureLoaded,
        bindSeek: tedAudioBindSeek,
        onRendered: tedAudioOnRendered,
        stop: tedAudioStop,
        updateButtons: tedAudioUpdateButtons,
        listenToggle: bookListenToggle,
        isActive: function () { return !!(tedAudioPlayer && tedAudioPlayer.active); },
        isTedBook: function () { return !!TED_BOOK; }
    };
})();

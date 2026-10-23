/* global $ */

/**
 * R183（架构评审 B4 批次 1）：阅读器横切原语单点。
 *
 * Why 单拆这一层：toast / CSRF 自愈 / 段落口径三组能力被 epub.js 的 8 个功能域共用
 * （27 / 17+16 / 7 处调用），留在 epub.js 里等于「装配层」还要兼任实现；
 * 其中 paragraphSpeechText 与 PARAGRAPH_SELECTOR 是后端 ES 缓存键的同源口径
 * （cps/reading_tts/extractor.py 按同一归一化落 SHA-256），复制或改写即缓存全失效，
 * 所以它们必须先有一个唯一出处，后续按域拆分时不再各处出现第二份真相。
 *
 * Why 用 IIFE + window 命名空间（仓内形制，同 js/common/api.js 的 window.MBApi）：
 * 本仓无构建链，脚本以 <script src> 同步顺序加载，epub.js 顶层就读 ReaderCore。
 *
 * 载入顺序：必须在 i18n_seed.html 之后（顶层样式里的按钮角标 mbT('Tr') 即时求值），
 * 并在 epub.js 之前（见 cps/templates/read.html）。
 */
(function () {
    "use strict";

    // R112: i18n 取词（种子缺失时回退 msgid 本身）
    var mbT = window.mbT || function (id) { return id; };

    var TRANSLATION_DISPLAY_KEY = 'calibre.reader.translationDisplaySecondsPer100';
    var TRANSLATION_DISPLAY_DEFAULT = 5;
    // 配置值同时是最小显示秒数：折算不足时按配置值整秒显示，避免单词/短句一闪而过

    var readerToastTimer = null;

    // 段落选择：常见块级元素；div 只取无块级子元素的"叶子段落"（部分 EPUB 用 div 当自然段）
    var PARAGRAPH_SELECTOR = 'p, li, blockquote, h1, h2, h3, h4, h5, h6, div';
    var BLOCK_CHILD_SELECTOR = 'p, li, div, blockquote, section, article, table, ul, ol, h1, h2, h3, h4, h5, h6';

    // 注入 iframe 的按钮/译文样式：用 currentColor 跟随阅读主题
    var READER_TOOLS_STYLE = [
        // R215：桌面图标提到 24px（1.5em 跟随字号），工具条保持在段落尾部行内——
        // 绝对定位浮层会压字（用户验收否决），这里只做行内放大。
        '.reading-para-tools{display:inline-flex;align-items:center;vertical-align:middle;margin-left:6px;line-height:1;white-space:nowrap}',
        '.reading-para-toolbar{display:inline-flex;align-items:center;gap:2px;opacity:0;pointer-events:none;transition:opacity .15s}',
        'p:hover>.reading-para-tools>.reading-para-toolbar,li:hover>.reading-para-tools>.reading-para-toolbar,blockquote:hover>.reading-para-tools>.reading-para-toolbar,h1:hover>.reading-para-tools>.reading-para-toolbar,h2:hover>.reading-para-tools>.reading-para-toolbar,h3:hover>.reading-para-tools>.reading-para-toolbar,h4:hover>.reading-para-tools>.reading-para-toolbar,h5:hover>.reading-para-tools>.reading-para-toolbar,h6:hover>.reading-para-tools>.reading-para-toolbar,div:hover>.reading-para-tools>.reading-para-toolbar{opacity:.95;pointer-events:auto}',
        '.reading-para-btn{display:inline-flex;align-items:center;justify-content:center;min-width:24px;height:24px;padding:0;font-size:1.5em;line-height:1;opacity:1;cursor:pointer;user-select:none;-webkit-user-select:none;color:inherit}',
        '.reading-para-btn:hover{opacity:1}',
        '.reading-para-btn.is-loading,.reading-para-btn.is-playing{opacity:.85}',
        '.reading-para-menu-btn{display:none;width:44px;height:44px;margin:-10px 0;align-items:center;justify-content:center;font-size:22px;line-height:1;opacity:.62;cursor:pointer;user-select:none;-webkit-user-select:none;color:inherit}',
        '.reading-para-menu-btn::after{content:"⋯"}',
        '.reading-para-selected{outline:2px solid rgba(74,144,217,.55);outline-offset:2px;background:rgba(74,144,217,.06);border-radius:2px}',
        '@media (hover:none){.reading-para-toolbar{display:none}.reading-para-menu-btn{display:inline-flex}}',
        '.reading-tts-btn::before{content:"▶"}',
        '.reading-tts-btn.is-loading::before{content:"⟳"}',
        '.reading-tts-btn.is-playing::before{content:"■"}',
        '.reading-translate-btn::before{content:"' + mbT('Tr') + '"}',
        '.reading-translate-btn.is-loading::before{content:"⟳"}',
        '.reading-translate-btn.is-done{opacity:.5}',
        '.reading-annotation-btn::before{content:"✎"}',
        '.reading-companion-btn::before{content:"✨"}',
        '.reading-companion-btn.is-loading::before{content:"⟳"}',
        '.reading-tts-speaking{background:rgba(255,193,7,.24);box-shadow:inset 3px 0 0 rgba(255,152,0,.85)}'
    ].join('');

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

    function csrfToken() {
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

    function toast(message) {
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

    function injectReaderToolsStyle(doc) {
        if (doc.getElementById('reading-tools-style')) return;
        var style = doc.createElement('style');
        style.id = 'reading-tools-style';
        style.textContent = READER_TOOLS_STYLE;
        (doc.head || doc.documentElement).appendChild(style);
    }

    function collectParagraphElements(doc) {
        var els = Array.prototype.slice.call(doc.querySelectorAll(PARAGRAPH_SELECTOR));
        return els.filter(function (el) {
            if (el.tagName === 'DIV' && el.querySelector(BLOCK_CHILD_SELECTOR)) return false;
            return (el.textContent || '').trim().length > 0;
        });
    }

    // 段落文本归一化口径：moon-well 的翻译/TTS/批注 ES 文档都以它的 SHA-256 为键，
    // 改这一行 = 全库缓存失效，任何调用方都不得自行重写
    function paragraphSpeechText(el) {
        var text = (el.textContent || '').replace(/\s+/g, ' ').trim();
        // 与后端 /ajax/reading-tts 校验一致的上限；超长段落截断朗读
        return text.length > 2000 ? text.slice(0, 2000) : text;
    }

    window.ReaderCore = {
        PARAGRAPH_SELECTOR: PARAGRAPH_SELECTOR,
        BLOCK_CHILD_SELECTOR: BLOCK_CHILD_SELECTOR,
        TRANSLATION_DISPLAY_KEY: TRANSLATION_DISPLAY_KEY,
        TRANSLATION_DISPLAY_DEFAULT: TRANSLATION_DISPLAY_DEFAULT,
        translationDisplaySecondsPer100: translationDisplaySecondsPer100,
        countWords: countWords,
        translationDisplaySecondsFor: translationDisplaySecondsFor,
        csrfToken: csrfToken,
        reloadIfCsrfBlocked: reloadIfCsrfBlocked,
        toast: toast,
        injectToolsStyle: injectReaderToolsStyle,
        collectParagraphs: collectParagraphElements,
        paragraphSpeechText: paragraphSpeechText
    };
})();

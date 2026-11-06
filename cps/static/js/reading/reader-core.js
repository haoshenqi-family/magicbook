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
        // R215：桌面图标保持 24px 触达盒，但字形按各自 em 宽度微调——
        // 「译」「▶」是满幅字形，1.5em 会明显大于 ✎/✨（用户验收嫌不和谐）。
        '.reading-para-tools{display:inline-flex;align-items:center;vertical-align:middle;margin-left:6px;line-height:1;white-space:nowrap}',
        '.reading-para-toolbar{display:inline-flex;align-items:center;gap:2px;opacity:0;pointer-events:none;transition:opacity .15s}',
        'p:hover>.reading-para-tools>.reading-para-toolbar,li:hover>.reading-para-tools>.reading-para-toolbar,blockquote:hover>.reading-para-tools>.reading-para-toolbar,h1:hover>.reading-para-tools>.reading-para-toolbar,h2:hover>.reading-para-tools>.reading-para-toolbar,h3:hover>.reading-para-tools>.reading-para-toolbar,h4:hover>.reading-para-tools>.reading-para-toolbar,h5:hover>.reading-para-tools>.reading-para-toolbar,h6:hover>.reading-para-tools>.reading-para-toolbar,div:hover>.reading-para-tools>.reading-para-toolbar{opacity:.95;pointer-events:auto}',
        '.reading-para-btn{display:inline-flex;align-items:center;justify-content:center;min-width:24px;height:24px;padding:0;font-size:1em;line-height:1;opacity:1;cursor:pointer;user-select:none;-webkit-user-select:none;color:inherit}',
        '.reading-tts-btn{font-size:.95em}',
        '.reading-translate-btn{font-size:.9em;font-weight:600}',
        '.reading-annotation-btn{font-size:1.15em}',
        '.reading-companion-btn{font-size:1.05em}',
        '.reading-para-btn:hover{opacity:1}',
        '.reading-para-btn.is-loading,.reading-para-btn.is-playing{opacity:.85}',
        '.reading-para-menu-btn{display:none;width:44px;height:44px;margin:-10px 0;align-items:center;justify-content:center;font-size:22px;line-height:1;opacity:.62;cursor:pointer;user-select:none;-webkit-user-select:none;color:inherit}',
        '.reading-para-menu-btn::after{content:"⋯"}',
        '.reading-translation{margin:6px 0 14px;font-size:.92em;line-height:1.5;color:inherit;opacity:.72;border-left:2px solid currentColor;padding-left:10px}',
        '.reading-translation.is-loading{opacity:.4;font-style:italic}',
        '.reading-translation.is-error{cursor:pointer;color:#c0392b;opacity:.9;font-style:italic;border-left-color:#c0392b}',
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
        '.reading-tts-speaking{background:rgba(255,193,7,.24);box-shadow:inset 3px 0 0 rgba(255,152,0,.85)}',
        // R268 生词波浪线样式必须注入 iframe：EPUB 正文渲染在本文件的同源 iframe 内，
        // 而 reader.css 只加载在父页，父页 CSS 不会跨文档作用到 iframe。此前只有
        // reader.css 定义 .reading-vocabulary-unknown，markVocabulary 已插入 span 但
        // iframe 内无此规则，表现为「analyze 正常返回生词、页面却看不到下划线」，
        // 手动刷新也无法恢复（刷新同样不注入）。这里随段落工具样式一起注入 iframe，
        // 与 R261 gloss 的 ::after 规则同源，确保标注即渲染。
        // R284 验收修复：问号光标下线——hover 反馈改由父页即时释义卡承载
        '.reading-vocabulary-unknown{text-decoration:underline wavy #d98b00 1px;text-decoration-skip-ink:none;cursor:pointer}',
        '.reading-vocabulary-unknown:hover{background:rgba(217,139,0,.16)}',
        // R261 行内小字释义（Word Wise 式，可选功能默认关）：小字浮在词头顶上一行，
        // 不占文档流（gloss 挂 data-gloss 属性，::after 取 attr 渲染）——占流会推动
        // 分栏重排、翻页时全文抖动。opacity 压到 .78 弱于正文，颜色随主题 currentColor
        '.reading-vocabulary-unknown[data-gloss]{position:relative}',
        '.reading-vocabulary-unknown[data-gloss]::after{content:attr(data-gloss);position:absolute;left:0;bottom:calc(100% + 1px);font-size:10px;line-height:1.1;white-space:nowrap;opacity:.78;pointer-events:none;font-style:normal;text-transform:none;letter-spacing:0}'
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

    // ===== R263 朗读速度（1.0 / 0.75 / 0.5 三档循环）=====
    // Why 客户端 playbackRate 而非服务端 TTS 变速：音频缓存键=SHA-256(段落原文)，
    // 变速落服务端要么同文双份缓存要么击穿永久缓存设计；浏览器 playbackRate 配合
    // preservesPitch 变速不变调，TED/博客类真人原声与整本 TTS 连播都适用，切换即时零成本。
    // 初学者场景：TED/博客类是真人常速演讲，0.75/0.5 是听得清的最小集合。
    var TTS_SPEED_KEY = "calibre.reader.ttsSpeed";
    var TTS_SPEED_STEPS = [1, 0.75, 0.5]; // 循环顺序：常速 → 慢 → 更慢 → 回常速
    function ttsSpeed() {
        var saved = null;
        try { saved = localStorage.getItem(TTS_SPEED_KEY); } catch (e) {}
        var value = parseFloat(saved);
        return TTS_SPEED_STEPS.indexOf(value) >= 0 ? value : 1;
    }
    function ttsSpeedLabel() {
        var value = ttsSpeed();
        return value === 1 ? '1.0x' : value + 'x'; // 0.75x / 0.5x
    }
    function cycleTtsSpeed() {
        var next = TTS_SPEED_STEPS[(TTS_SPEED_STEPS.indexOf(ttsSpeed()) + 1) % TTS_SPEED_STEPS.length];
        try { localStorage.setItem(TTS_SPEED_KEY, String(next)); } catch (e) {}
        return ttsSpeedLabel();
    }
    // 对任一在播 <audio> 套当前档位；preservesPitch 显式钉住（Safari 旧名 webkitPreservesPitch）
    function applyTtsSpeed(audio) {
        if (!audio) return;
        try {
            audio.playbackRate = ttsSpeed();
            audio.preservesPitch = true;
            audio.webkitPreservesPitch = true;
        } catch (e) {}
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
        paragraphSpeechText: paragraphSpeechText,
        TTS_SPEED_KEY: TTS_SPEED_KEY,
        TTS_SPEED_STEPS: TTS_SPEED_STEPS,
        ttsSpeed: ttsSpeed,
        ttsSpeedLabel: ttsSpeedLabel,
        cycleTtsSpeed: cycleTtsSpeed,
        applyTtsSpeed: applyTtsSpeed
    };
})();

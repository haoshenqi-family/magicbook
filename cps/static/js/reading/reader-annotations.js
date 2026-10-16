/* global $, calibre */

/**
 * R183（架构评审 B4 批次 3）：段落批注 / AI 伴读批注 / 本书批注面板（477 行）独立模块。
 *
 * 段落文本用与翻译/朗读一致的 paragraphSpeechText 归一化，moon-well 按 SHA-256(段落)
 * 定位同一份文档：批注自动挂在翻译/音频缓存所在段落上；批注署名与时间由 moon-well
 * 从登录用户取，前端不传也不能传。
 *
 * Why 现在拆得动：本域是 epub.js 里的「叶子」——对外只依赖宿主一处章标题
 * （currentChapterTitle，装配层持有 rendition/toc），其余全是 core 原语；反向只需五个
 * 入口（G 节两个按钮、E 节关闭、装配层的 mousedown/Esc/relocated）。TTS 簇不是叶子，
 * 所以批次排在它前面。
 *
 * 载入顺序：i18n_seed → api.js → reader-core.js → reader-word-detail.js → 本文件 → epub.js
 */
(function () {
    "use strict";

    var RC = window.ReaderCore;
    var mbT = window.mbT || function (id) { return id; };

    // 宿主回调：章标题口径由装配层独占（它才持有 rendition/toc）
    var host = { currentChapterTitle: function () { return ''; } };

    // core 原语在本模块内的同名别名——保持下面正文与 epub.js 时代逐字一致，
    // 也让既有静态锁（X-CSRFToken 计数、paragraphSpeechText 归一化契约）继续成立
    var readerCsrfToken = function () { return RC.csrfToken(); };
    var reloadIfCsrfBlocked = function (x) { return RC.reloadIfCsrfBlocked(x); };
    var readerToast = function (m) { RC.toast(m); };
    var paragraphSpeechText = function (el) { return RC.paragraphSpeechText(el); };
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
                bookName: calibre.bookName || '', chapter: host.currentChapterTitle(), force: !!force})
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
                    bookName: calibre.bookName || '', chapter: host.currentChapterTitle()})
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


    window.ReaderAnnotations = {
        /** 宿主（epub.js）注入章标题口径 */
        setHost: function (next) {
            if (next.currentChapterTitle) host.currentChapterTitle = next.currentChapterTitle;
        },
        openPopover: openAnnotationPopover,
        closePopover: closeAnnotationPopover,
        isPopoverOpen: function () { return !!annotationPopover; },
        containsNode: function (node) { return !!(annotationPopover && node && annotationPopover.contains(node)); },
        openPanel: openAnnotationPanel,
        closePanel: closeAnnotationPanel,
        isPanelOpen: function () { return !!annotationPanel; },
        panelContainsNode: function (node) { return !!(annotationPanel && node && annotationPanel.contains(node)); },
        isToggleClick: function (node) {
            return !!(annotationPanelToggle && node &&
                (node === annotationPanelToggle || annotationPanelToggle.contains(node)));
        }
    };
})();

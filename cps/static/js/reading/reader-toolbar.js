/* global window, document */
/**
 * R215：阅读器顶栏的窄屏折叠。
 *
 * Why：顶栏要同时满足「桌面 24px 图标 + 文字标签」与「触屏 44px 触达」。
 * 390px 宽度塞不下六个带标签的控件，必须把次要项收进「更多」菜单；
 * 菜单里必须是**原节点**而不是克隆品——克隆会复制 ID、丢失已绑定的监听，
 * 表现就是「更多」里的设置/书签点了没反应。
 *
 * How：≤767px 时把次要项 append 进 #title-more-menu，回到宽屏时按原顺序
 * 插回 #title-more 之前；节点搬家因此不影响各自的事件处理。本文件不导出
 * window 命名空间、不声明 init：载入即绑定，避免触发「声明 init 必须显式调用」守卫。
 */
(function () {
    "use strict";

    var more = document.getElementById("title-more");
    var menu = document.getElementById("title-more-menu");
    if (!more || !menu) return;

    // 顺序即视觉顺序；whole-book-translate 仅管理员存在
    var ITEM_IDS = ["bookmark", "setting", "fullscreen", "whole-book-translate"];
    var narrowQuery = window.matchMedia("(max-width: 767px)");
    var moved = [];
    var menuOpen = false;

    more.setAttribute("aria-haspopup", "true");

    function collect() {
        return ITEM_IDS.map(function (id) {
            return document.getElementById(id);
        }).filter(Boolean);
    }

    function closeMenu() {
        if (!menuOpen) return;
        menuOpen = false;
        menu.hidden = true;
        more.setAttribute("aria-expanded", "false");
    }

    function openMenu() {
        if (menuOpen) return;
        menuOpen = true;
        menu.hidden = false;
        more.setAttribute("aria-expanded", "true");
    }

    function syncLayout() {
        if (narrowQuery.matches) {
            if (moved.length) return;
            moved = collect();
            moved.forEach(function (el) { menu.appendChild(el); });
            return;
        }
        // 宽屏：按原顺序插回 #title-more 之前。逐个 insertBefore 后，
        // 已插入项自然排在 more 前面，顺序与 ITEM_IDS 一致。
        moved.forEach(function (el) {
            if (el.parentNode === menu) menu.removeChild(el);
            more.parentNode.insertBefore(el, more);
        });
        moved = [];
        closeMenu();
    }

    more.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (menuOpen) closeMenu();
        else openMenu();
    });

    // 点击菜单项后收起菜单；不要抢在原监听之前（同一元素上的 click
    // 监听先执行，本监听在冒泡阶段收尾）
    menu.addEventListener("click", function (event) {
        if (event.target && event.target.closest && event.target.closest("a")) {
            closeMenu();
        }
    });

    document.addEventListener("mousedown", function (event) {
        if (!menuOpen) return;
        if (event.target === more || menu.contains(event.target)) return;
        closeMenu();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") closeMenu();
    });

    var resizeTick = null;
    window.addEventListener("resize", function () {
        if (resizeTick) return;
        resizeTick = window.requestAnimationFrame(function () {
            resizeTick = null;
            syncLayout();
        });
    });

    if (narrowQuery.addEventListener) {
        narrowQuery.addEventListener("change", syncLayout);
    } else if (narrowQuery.addListener) {
        narrowQuery.addListener(syncLayout);
    }

    syncLayout();
})();

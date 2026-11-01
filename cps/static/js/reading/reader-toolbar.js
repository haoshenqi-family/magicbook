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
 *
 * R263 修订：书签（自动记录阅读进度后冗余）与整本翻译（低频管理项）**常驻菜单**、
 * 任何宽度都不进顶栏；设置/全屏仍宽屏直达、仅窄屏折叠。「更多」按钮因此常显。
 */
(function () {
    "use strict";

    var more = document.getElementById("title-more");
    var menu = document.getElementById("title-more-menu");
    if (!more || !menu) return;

    // 常驻菜单项：任何宽度都在「更多」里（宽屏菜单顺序 = 本清单顺序）
    var MENU_ALWAYS = ["bookmark", "whole-book-translate"];
    // 仅窄屏折叠项：宽屏插回 #title-more 之前（保持本清单相对顺序）
    var MENU_NARROW_ONLY = ["setting", "fullscreen"];
    // 窄屏菜单顺序：与 R215 时代顶栏顺序一致（书签/设置/全屏/整本翻译）
    var MENU_NARROW_ALL = ["bookmark", "setting", "fullscreen", "whole-book-translate"];
    var narrowQuery = window.matchMedia("(max-width: 767px)");
    var menuOpen = false;

    more.setAttribute("aria-haspopup", "true");

    function collect(ids) {
        return ids.map(function (id) {
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

    function toMenu(ids) {
        collect(ids).forEach(function (el) {
            if (el.parentNode !== menu) menu.appendChild(el);
        });
    }

    function toBar(ids) {
        collect(ids).forEach(function (el) {
            if (el.parentNode === menu) menu.removeChild(el);
            // insertBefore 对「已在 more 之前」的节点是原位 no-op
            more.parentNode.insertBefore(el, more);
        });
    }

    function syncLayout() {
        if (narrowQuery.matches) {
            toMenu(MENU_NARROW_ALL);
            return;
        }
        // 宽屏：窄屏折叠项插回顶栏，常驻项留菜单（已在菜单则原地不动）
        toBar(MENU_NARROW_ONLY);
        toMenu(MENU_ALWAYS);
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

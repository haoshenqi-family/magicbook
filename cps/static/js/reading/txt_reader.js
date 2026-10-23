/* This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
 *    Copyright (C) 2021 Ozzieisaacs
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * 判定是否为「预排版」硬换行文本（如 Project Gutenberg 电子书）。
 * Why: 这类 TXT 保留纸质书排版（行尾硬换行 + 不规则缩进），阅读器按 pre-wrap + 双栏分页渲染时
 *      行被任意切入不同栏，产生左右交错、断行错乱的排版。
 * How: 流式 TXT（现代导出）绝大多数非空行超过 72 字符；预排版文本行普遍短于该值，
 *      长行占比低于 30% 且行数足够多时判定为预排版，需要重排。
 */
function isHardWrappedText(textStr) {
    var lines = textStr.split(/\r?\n/).filter(function(line) {
        return line.trim().length > 0;
    });
    if (lines.length < 20) {
        return false;
    }
    var longLines = 0;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].trim().length > 72) {
            longLines++;
        }
    }
    return longLines / lines.length < 0.3;
}

/**
 * 将预排版文本重排为流式段落。
 * How: 空行为段落边界；段内各行合并为一段——行尾连字符视为断词直接拼接（保留连字符，
 *      如 tea- + kettle → tea-kettle）；CJK 字符之间不插空格，避免中文句子被拆出空格；
 *      其余行以单空格连接并压缩连续空格。诗歌等行式内容会被并入段落，换取整体可读性。
 */
function reflowHardWrappedText(textStr) {
    var CJK = /[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]/;
    return textStr.split(/\r?\n[ \t]*\r?\n/).map(function(block) {
        return block.split(/\r?\n/).reduce(function(acc, line) {
            line = line.trim();
            if (!line) {
                return acc;
            }
            if (!acc) {
                return line;
            }
            if (/-$/.test(acc)) {
                return acc + line;
            }
            var joiner = (CJK.test(acc.slice(-1)) || CJK.test(line.charAt(0))) ? '' : ' ';
            return acc + joiner + line;
        }, '').replace(/ {2,}/g, ' ').trim();
    }).filter(function(paragraph) {
        return paragraph.length > 0;
    }).join('\n\n');
}

$(document).ready(function() {
    //to int
    $("#area").width($("#area").width());
    $("#content").width($("#content").width());
    //bind text
    $("#content").load($("#readmain").data('load'), function(textStr) {
        $(this).height($(this).parent().height()*0.95);
        $(this).text(isHardWrappedText(textStr) ? reflowHardWrappedText(textStr) : textStr);
        // R213-B：文本进入 DOM 后 scrollWidth 才有效，分页与恢复都必须在这一步之后
        homeLeft = $(this).offset().left;
        pageCount = Math.max(1, Math.ceil(this.scrollWidth / pageWidth));
        var _srv = (window.calibre && window.calibre.readerPosition) || {};
        if (_srv.page_current) {
            goToPage(_srv.page_current);
        }
        reportProgress(); // 首屏位置（恢复页）入库
    });
    //keybind
    $(document).keydown(function(event){
        if(event.keyCode == 37){
            prevPage();
        }
        if(event.keyCode == 39){
            nextPage();
        }
    });
    //click
    $( "#left" ).click(function() {
        prevPage();
    });
    $( "#right" ).click(function() {
        nextPage();
    });
    $("#readmain").swipe( {
        swipeRight:function() {
            prevPage();
        },
        swipeLeft:function() {
            nextPage();
        },
    });

    //bind mouse
    $(window).bind('DOMMouseScroll mousewheel', function(event) {
        var delta = 0;
        if (event.originalEvent.wheelDelta) {
            delta = event.originalEvent.wheelDelta;
        } else if (event.originalEvent.detail) {
            delta = event.originalEvent.detail*-1;
        }
        if (delta >= 0) {
            prevPage();
        } else {
            nextPage();
        }
    });

    //page animate
    var origwidth = $("#content")[0].getBoundingClientRect().width;
    var gap = 20;
    // R213-B：账号级阅读位置。TXT 此前没有进度记忆，本次为首次接入——
    // 页码口径 = 内容相对初始位置的偏移 / 每页位移，与服务端 page_current 同单位。
    var pageWidth = origwidth + gap;
    var homeLeft = null; // 第 1 页时 content 的文档坐标（不一定是 0）
    var pageCount = 1;
    function currentPage() {
        var left = $("#content").offset().left;
        if (homeLeft === null) homeLeft = left;
        var idx = Math.round((homeLeft - left) / pageWidth);
        return Math.max(1, Math.min(pageCount, idx + 1));
    }
    function reportProgress() {
        if (!window.ReaderProgress) return;
        window.ReaderProgress.update({
            page: currentPage(),
            total: pageCount,
            percent: pageCount > 1 ? Math.round(currentPage() / pageCount * 10000) / 100 : null,
        });
    }
    function goToPage(page) {
        if (page < 1 || page > pageCount) return;
        if (homeLeft === null) homeLeft = $("#content").offset().left;
        $("#content").offset({left: homeLeft - (page - 1) * pageWidth});
    }
    function prevPage() {
        var page = currentPage();
        if (page <= 1) {
            return;
        }
        goToPage(page - 1);
        reportProgress();
    }
    function nextPage() {
        var page = currentPage();
        if (page >= pageCount) {
            return;
        }
        goToPage(page + 1);
        reportProgress();
    }
});

/*
 * Credits page: balance + recharge packages -> Alipay face-to-face QR checkout -> poll order status.
 * R242 also adds transferable credit cards: buy a card (settles to a key, not buyer credits),
 * redeem any valid key, copy purchased keys, and admin batch issue/export/void.
 * All calls go through magicbook backend proxies (/ajax/credit-*) which forward
 * to moon-well with the session-bound JWT (see _moonwell_proxy in web.py).
 * moon-well grants credits immediately when the payment settles (notify or poll compensation).
 * adminOnly packages (test tier) are hidden for non-admin users.
 */
(function ($) {
    'use strict';

    var CSRF = window.MBApi.csrfToken();  // R177：CSRF 单点迁 common/api.js（#credit-csrf 为链式第 2 形态，值等价）
    var IS_ADMIN = $('#credit-page').attr('data-is-admin') === '1';
    var POLL_INTERVAL_MS = 3000;
    var MAX_CONSECUTIVE_ERRORS = 5;
    var CSRF_RELOAD_FLAG = 'creditCsrfReloaded';

    var pollTimer = null;
    var countdownTimer = null;
    var promoCountdownTimer = null;
    var consecutiveErrors = 0;
    var currentOrder = null; // precreate 成功前不赋值，避免失败后残留半初始化订单
    var currentBatchId = null;
    var PENDING_CARD_KEY = 'creditCardPendingRedeem';

    function revealElement(element) {
        if (element && typeof element.scrollIntoView === 'function') {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    function showError(message, reveal) {
        var alertBox = $('#credit-alert');
        alertBox.removeClass('alert-success').addClass('alert-danger')
            .text(message).show();
        if (reveal) {
            revealElement(alertBox[0]);
        }
    }

    function showSuccess(message) {
        var alertBox = $('#credit-alert');
        alertBox.removeClass('alert-danger').addClass('alert-success')
            .text(message).show();
    }

    function hideMessages() {
        $('#credit-alert').hide();
    }

    // R177（架构评审 B5）：解包迁 common/api.js 的 strict 口径（与原实现等价：
    // 非信封/parse 失败一律抛，告警框呈现，null 不漏到渲染层）。
    function unwrap(response) {
        return window.MBApi.unwrapStrict(response);
    }

    // Why: CSRFProtect 校验失败返回非 JSON 的 400；自动 reload 一次取新 token 自愈，
    // sessionStorage 标记防止 token 真失效时陷入 reload 死循环
    function allowCsrfReload() {
        if (sessionStorage.getItem(CSRF_RELOAD_FLAG)) {
            return false;
        }
        sessionStorage.setItem(CSRF_RELOAD_FLAG, '1');
        return true;
    }

    function ajax(url, method, payload) {
        var options = { method: method || 'GET', headers: {} };
        if (method === 'POST') {
            options.headers['Content-Type'] = 'application/json';
            options.headers['X-CSRFToken'] = CSRF;
            options.body = JSON.stringify(payload || {});
        }
        return fetch(url, options).then(function (resp) {
            // moon-well 侧业务异常以 Result JSON 返回（HTTP 4xx/5xx），统一按 JSON 解析
            return resp.json().catch(function () {
                if (resp.status === 400 && allowCsrfReload()) {
                    window.location.reload();
                    throw new Error('session expired, reloading...');
                }
                throw new Error('HTTP ' + resp.status);
            });
        });
    }

    // Why separate from ajax(): export returns text/plain, not the Result JSON envelope.
    function ajaxBlob(url, method, payload) {
        var options = {
            method: method || 'POST',
            headers: { 'X-CSRFToken': CSRF }
        };
        if (options.method === 'POST') {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(payload || {});
        }
        return fetch(url, options).then(function (resp) {
            if (!resp.ok) {
                return resp.text().then(function (text) {
                    var message = 'HTTP ' + resp.status;
                    try {
                        message = JSON.parse(text).message || message;
                    } catch (e) { /* non-JSON error */ }
                    throw new Error(message);
                });
            }
            return resp.blob();
        });
    }

    function formatMoney(value) {
        return '¥' + parseFloat(value).toFixed(2);
    }

    function renderBalance(account) {
        var balance = account ? account.balance : null;
        if (balance === null || balance === undefined) {
            $('#credit-balance').text('0');
            return;
        }
        $('#credit-balance').text(String(balance));
    }

    function loadBalance() {
        ajax('/ajax/credit/account', 'POST').then(function (response) {
            renderBalance(unwrap(response));
        }).catch(function (error) {
            $('#credit-balance').text('-');
            showError('Failed to load balance: ' + error.message);
        });
    }

    // ---------- R205：活动角标 / 划线原价 / 倒计时 ----------
    // Why 一律用服务端给的 promotionEndTimeEpochMs 而不是解析时间字符串:
    // 浏览器按本地时区解析「2026-12-31 23:59:59」会换算出偏差，非东八区用户会看到「活动已结束」而实际仍在进行。
    function formatPromotionRemain(ms) {
        if (ms <= 0) { return '活动已结束'; }
        var totalMinutes = Math.floor(ms / 60000);
        var days = Math.floor(totalMinutes / 1440);
        var hours = Math.floor((totalMinutes % 1440) / 60);
        var minutes = totalMinutes % 60;
        if (days > 0) { return '活动剩 ' + days + ' 天 ' + hours + ' 小时'; }
        if (hours > 0) { return '活动剩 ' + hours + ' 小时 ' + minutes + ' 分'; }
        return '活动剩 ' + minutes + ' 分';
    }

    function refreshPromotionCountdown() {
        $('.pkg-promo').each(function () {
            var endMs = parseInt($(this).attr('data-promo-end'), 10);
            if (isNaN(endMs)) { return; }
            $(this).text(formatPromotionRemain(endMs - Date.now()));
        });
    }

    // 每 60 秒刷新一次即可：文案粒度到「分」，秒级刷新只是白烧 CPU
    function startPromotionCountdown() {
        refreshPromotionCountdown();
        if (promoCountdownTimer) { clearInterval(promoCountdownTimer); }
        promoCountdownTimer = setInterval(refreshPromotionCountdown, 60000);
    }

    function renderPackages(packages) {
        // Why: adminOnly 测试档仅管理员可见（moon-well 无角色概念，前端过滤 + 入口隐藏）
        var visible = packages.filter(function (pkg) {
            return !pkg.adminOnly || IS_ADMIN;
        });
        var container = $('#credit-packages').empty();
        if (!visible.length) {
            container.html('<p class="text-muted">No recharge packages available.</p>');
            return;
        }
        visible.forEach(function (pkg) {
            var onPromotion = pkg.multiplier > 1;
            var card = $('<div>').addClass('credit-package-card');
            var nameRow = $('<div>').addClass('pkg-name').text(pkg.title);
            if (onPromotion) {
                nameRow.append($('<span>').addClass('pkg-badge').text('内测 ×' + pkg.multiplier));
            }
            card.append(nameRow);
            if (onPromotion && pkg.baseTitle) {
                card.append($('<div>').addClass('pkg-base').text(pkg.baseTitle));
            }
            card.append($('<div>').addClass('pkg-price').text(formatMoney(pkg.price)));
            card.append($('<div>').addClass('pkg-desc').text(pkg.description || ''));
            if (onPromotion && pkg.promotionEndTimeEpochMs) {
                card.append($('<div>').addClass('pkg-promo')
                    .attr('data-promo-end', String(pkg.promotionEndTimeEpochMs))
                    .text(formatPromotionRemain(pkg.promotionEndTimeEpochMs - Date.now())));
            }
            card.append($('<button>').addClass('btn btn-primary btn-sm pkg-buy-btn')
                .attr('data-package-id', pkg.id)
                .text('Recharge Now'));
            container.append(card);
        });
        startPromotionCountdown();
    }

    function loadPackages() {
        return ajax('/ajax/credit/packages').then(function (response) {
            var packages = unwrap(response) || [];
            renderPackages(packages);
        }).catch(function (error) {
            $('#credit-packages').empty()
                .append($('<p>').addClass('text-danger').text('Failed to load packages: ' + error.message));
        });
    }

    // ---------- R242: credit cards ----------
    function copyText(text, button, successText, errorText) {
        function done() {
            var original = button.text();
            button.text(successText || '已复制');
            setTimeout(function () { button.text(original); }, 1500);
        }
        function fallback() {
            var area = document.createElement('textarea');
            area.value = text;
            area.setAttribute('readonly', '');
            area.style.position = 'fixed';
            area.style.opacity = '0';
            document.body.appendChild(area);
            area.select();
            try {
                // execCommand 返回 false 表示浏览器拒绝复制，不能伪装成成功。
                if (document.execCommand('copy')) {
                    done();
                } else {
                    showError(errorText || '复制失败，请手动选择内容复制。');
                }
            } catch (e) {
                showError(errorText || '复制失败，请手动选择内容复制。');
            }
            document.body.removeChild(area);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(done).catch(fallback);
        } else {
            fallback();
        }
    }

    function cardShareUrl(card) {
        var base = $('#credit-page').attr('data-card-share-url') ||
            (window.location.origin + '/credit-card/share');
        var params = new URLSearchParams();
        params.set('key', card.key);
        if (card.credits !== null && card.credits !== undefined) {
            params.set('credits', String(card.credits));
        }
        // Why fragment: bearer key must not reach Flask, proxies or access logs.
        return base.split('#')[0] + '#' + params.toString();
    }

    function consumeSharedCardKey() {
        var key = '';
        var credits = '';
        try {
            var hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));
            key = (hashParams.get('redeem') || '').trim();
        } catch (e) {
            key = '';
        }
        if (!key) {
            try {
                var pending = JSON.parse(sessionStorage.getItem(PENDING_CARD_KEY) || 'null');
                if (pending && Date.now() - Number(pending.savedAt || 0) <= 60 * 60 * 1000) {
                    key = String(pending.key || '').trim();
                    credits = String(pending.credits || '').trim();
                }
            } catch (e) {
                key = '';
            }
        }
        sessionStorage.removeItem(PENDING_CARD_KEY);
        if (!key) { return; }

        $('#credit-card-redeem-key').val(key);
        $('#credit-card-redeem-result')
            .removeClass('text-danger text-success').addClass('text-muted')
            .text((credits ? credits + ' 积分卡密' : '卡密') +
                '已从分享链接填入，请确认后点击「兑换」。');
        revealElement($('#credit-card-redeem')[0]);
        if (window.history && window.history.replaceState) {
            // Remove the bearer key from the visible URL after moving it to the form.
            window.history.replaceState(null, '', window.location.pathname + window.location.search);
        }
    }

    function renderCardPackages(packages) {
        var container = $('#credit-card-packages').empty();
        if (!packages || !packages.length) {
            container.append($('<p>').addClass('text-muted').text('暂无可购买的积分卡。'));
            return;
        }
        packages.forEach(function (pkg) {
            var card = $('<div>').addClass('credit-package-card');
            card.append($('<div>').addClass('pkg-name').text(pkg.title + ' 积分卡'));
            card.append($('<div>').addClass('pkg-price').text(formatMoney(pkg.price)));
            card.append($('<div>').addClass('pkg-desc')
                .text('支付后生成一张可转赠的卡密，购买者积分不变。'));
            card.append($('<button>').addClass('btn btn-primary btn-sm credit-card-buy-btn')
                .attr('data-package-id', pkg.id)
                .text('购买并赠送'));
            container.append(card);
        });
    }

    function loadCardPackages() {
        ajax('/ajax/credit/card/packages').then(function (response) {
            renderCardPackages(unwrap(response) || []);
        }).catch(function (error) {
            $('#credit-card-packages').empty()
                .append($('<p>').addClass('text-danger').text('积分卡档位加载失败：' + error.message));
        });
    }

    function cardRow(card, options) {
        var row = $('<tr>').addClass('credit-card-row');
        row.append($('<td>').addClass('credit-card-key').text(card.key || '-'));
        row.append($('<td>').text(card.credits == null ? '-' : card.credits));
        row.append($('<td>').text(card.statusText || card.status || '-'));
        row.append($('<td>').text(card.expiresAt || '长期有效'));
        var actions = $('<td>');
        if (card.key) {
            var copyButton = $('<button>').addClass('btn btn-default btn-xs').text('复制卡密')
                .on('click', function () {
                    copyText(card.key, copyButton, '卡密已复制', '复制失败，请手动选择卡密复制。');
                });
            var shareButton = $('<button>').addClass('btn btn-primary btn-xs')
                .css('margin-left', '5px').text('复制并分享')
                .on('click', function () {
                    copyText(cardShareUrl(card), shareButton, '分享链接已复制',
                        '复制分享链接失败，请手动复制。');
                });
            actions.append(copyButton);
            actions.append(shareButton);
        }
        if (options && options.voidable && card.status === 'ACTIVE') {
            var voidButton = $('<button>').addClass('btn btn-danger btn-xs')
                .css('margin-left', '5px').text('作废')
                .on('click', function () { voidCard(card, options.reload); });
            actions.append(voidButton);
        }
        row.append(actions);
        return row;
    }

    function renderPurchasedCards(cards, highlightOrderNo) {
        var tbody = $('#credit-card-purchased-rows').empty();
        if (!cards || !cards.length) {
            tbody.html('<tr><td colspan="5" class="text-muted">还没有购买过积分卡。</td></tr>');
            return;
        }
        cards.forEach(function (card) {
            var row = cardRow(card);
            if (highlightOrderNo && card.purchaseOrderNo === highlightOrderNo) {
                row.addClass('success');
            }
            tbody.append(row);
        });
    }

    function loadPurchasedCards(highlightOrderNo) {
        return ajax('/ajax/credit/card/purchase-list', 'POST', {}).then(function (response) {
            renderPurchasedCards(unwrap(response) || [], highlightOrderNo);
            return true;
        }).catch(function (error) {
            $('#credit-card-purchased-rows').html(
                '<tr><td colspan="5" class="text-danger">卡密列表加载失败：' +
                $('<span>').text(error.message).html() + '</td></tr>');
            return false;
        });
    }

    function redeemCard() {
        var input = $('#credit-card-redeem-key');
        var key = $.trim(input.val());
        var result = $('#credit-card-redeem-result');
        if (!key) {
            result.removeClass('text-success').addClass('text-danger').text('请输入卡密。');
            return;
        }
        var button = $('#credit-card-redeem-form button[type=submit]').prop('disabled', true);
        result.removeClass('text-success text-danger').addClass('text-muted').text('兑换中...');
        ajax('/ajax/credit/card/redeem', 'POST', { key: key }).then(function (response) {
            var redeemed = unwrap(response);
            input.val('');
            result.removeClass('text-muted text-danger').addClass('text-success')
                .text('兑换成功：+' + redeemed.credits + ' 积分，当前余额 ' + redeemed.balanceAfter + '。');
            loadBalance();
            loadConsumeDetail();
            loadPurchasedCards();
        }).catch(function (error) {
            result.removeClass('text-muted text-success').addClass('text-danger')
                .text(error.message || '兑换失败。');
        }).finally(function () {
            button.prop('disabled', false);
        });
    }

    function issueCardBatch() {
        var longTerm = $('#credit-card-admin-long-term').is(':checked');
        var payload = {
            credits: parseInt($('#credit-card-admin-credits').val(), 10),
            count: parseInt($('#credit-card-admin-count').val(), 10),
            validityDays: longTerm ? null : parseInt($('#credit-card-admin-validity').val(), 10),
            longTerm: longTerm,
            reason: $.trim($('#credit-card-admin-reason').val())
        };
        if (!payload.reason) {
            window.alert('发卡原因必填。');
            return;
        }
        if (!longTerm && (!payload.validityDays || payload.validityDays < 1)) {
            window.alert('有效期天数必须在 1-3650 之间，或勾选长期有效。');
            return;
        }
        if (!window.confirm('确认发放 ' + payload.count + ' 张 ' + payload.credits + ' 积分卡？')) {
            return;
        }
        ajax('/ajax/credit/card/admin-issue', 'POST', payload).then(function (response) {
            var batch = unwrap(response);
            window.alert('已生成批次 ' + batch.id + '，共 ' + batch.totalCount + ' 张。');
            $('#credit-card-admin-issue-form')[0].reset();
            $('#credit-card-admin-long-term').prop('checked', false);
            $('#credit-card-admin-validity').prop('disabled', false).val('30');
            loadAdminBatches();
            loadAdminCards(batch.id);
        }).catch(function (error) {
            window.alert('发卡失败：' + error.message);
        });
    }

    function renderAdminBatches(batches) {
        var tbody = $('#credit-card-admin-batches-rows').empty();
        if (!batches || !batches.length) {
            tbody.html('<tr><td colspan="7" class="text-muted">暂无发卡批次。</td></tr>');
            return;
        }
        batches.forEach(function (batch) {
            var row = $('<tr>');
            row.append($('<td>').text(batch.id));
            row.append($('<td>').text(batch.credits));
            row.append($('<td>').text(batch.totalCount));
            row.append($('<td>').text(batch.longTerm ? '长期有效' : (batch.validityDays + ' 天')));
            row.append($('<td>').text(batch.source === 'PURCHASE' ? '购卡' : '管理员'));
            row.append($('<td>').text(batch.createdAt || '-'));
            var actions = $('<td>');
            actions.append($('<button>').addClass('btn btn-default btn-xs').text('查看')
                .on('click', function () { loadAdminCards(batch.id); }));
            actions.append($('<button>').addClass('btn btn-default btn-xs')
                .css('margin-left', '5px').text('导出')
                .on('click', function () { exportBatch(batch.id); }));
            row.append(actions);
            tbody.append(row);
        });
    }

    function loadAdminBatches() {
        if (!IS_ADMIN) { return; }
        ajax('/ajax/credit/card/admin-batches', 'POST', {}).then(function (response) {
            renderAdminBatches(unwrap(response) || []);
        }).catch(function (error) {
            $('#credit-card-admin-batches-rows').html(
                '<tr><td colspan="7" class="text-danger">批次加载失败：' +
                $('<span>').text(error.message).html() + '</td></tr>');
        });
    }

    function renderAdminCards(cards, batchId) {
        var tbody = $('#credit-card-admin-cards-rows').empty();
        if (!cards || !cards.length) {
            tbody.html('<tr><td colspan="5" class="text-muted">该批次没有卡密。</td></tr>');
        } else {
            cards.forEach(function (card) {
                tbody.append(cardRow(card, {
                    voidable: true,
                    reload: function () { loadAdminCards(batchId); }
                }));
            });
        }
        $('#credit-card-admin-cards').show();
    }

    function loadAdminCards(batchId) {
        if (!IS_ADMIN || !batchId) { return; }
        currentBatchId = batchId;
        ajax('/ajax/credit/card/admin-cards', 'POST', { batchId: batchId }).then(function (response) {
            renderAdminCards(unwrap(response) || [], batchId);
        }).catch(function (error) {
            $('#credit-card-admin-cards').show();
            $('#credit-card-admin-cards-rows').html(
                '<tr><td colspan="5" class="text-danger">卡密加载失败：' +
                $('<span>').text(error.message).html() + '</td></tr>');
        });
    }

    function voidCard(card, reload) {
        var reason = window.prompt('作废原因（必填）：', '');
        if (reason === null) { return; }
        reason = $.trim(reason);
        if (!reason) {
            window.alert('作废原因必填。');
            return;
        }
        ajax('/ajax/credit/card/admin-void', 'POST', { cardId: card.id, reason: reason })
            .then(function () {
                window.alert('卡密已作废。');
                if (reload) { reload(); }
                loadAdminBatches();
                loadPurchasedCards();
            }).catch(function (error) {
                window.alert('作废失败：' + error.message);
            });
    }

    function exportBatch(batchId) {
        ajaxBlob('/ajax/credit/card/admin-export', 'POST', { batchId: batchId })
            .then(function (blob) {
                var url = URL.createObjectURL(blob);
                var link = document.createElement('a');
                link.href = url;
                link.download = 'credit-cards-batch-' + batchId + '.txt';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }).catch(function (error) {
                window.alert('导出失败：' + error.message);
            });
    }

    function stopPolling() {
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    }

    function stopCountdown() {
        if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
    }

    function stopAllTimers() {
        stopPolling();
        stopCountdown();
    }

    function markPaid() {
        stopAllTimers();
        // Why: 支付完成后二维码即失效，收起收银台并给出明确的到账结果与新余额，
        // 避免页面停留在"扫码中"的观感（用户感知为"没有正确跳转"）
        $('#credit-checkout').modal('hide');
        var grantedCredits = currentOrder ? currentOrder.credits : null;
        var isCard = currentOrder && currentOrder.kind === 'CARD';
        var accountRequest = ajax('/ajax/credit/account', 'POST').then(function (response) {
            renderBalance(unwrap(response));
        });
        if (isCard) {
            // Why 两条刷新互不依赖: 卡已由支付回调生成，余额接口抖动不应让买家看不到新卡密。
            accountRequest.catch(function () { /* 卡密列表仍继续刷新 */ });
            loadPurchasedCards(currentOrder.orderNo).then(function (loaded) {
                showSuccess(loaded
                    ? '支付成功，积分卡已生成，请复制卡密。'
                    : '支付成功，积分卡已生成；卡密列表刷新失败，请刷新页面后复制。');
            });
            return;
        }
        accountRequest.then(function () {
            showSuccess('充值成功：' + (grantedCredits ? grantedCredits + ' 积分已到账，' : '积分已到账，') +
                '当前余额 ' + ($('#credit-balance').text() || '-') + '。');
        }).catch(function () {
            showSuccess('充值成功，积分已到账（余额刷新失败，可刷新页面查看）。');
        });
    }

    function markExpired() {
        stopAllTimers();
        $('#credit-status').text('Order expired.').removeClass().addClass('text-danger');
        $('#credit-countdown').text('');
        $('#credit-regenerate').show();
    }

    function renderCheckout(order, qrCode) {
        $('#credit-checkout-title').text(
            order.kind === 'CARD' ? '购买积分卡 · 支付宝扫码支付' : '积分充值 · 支付宝扫码支付');
        $('#credit-checkout-info').html('Pay <strong>' + formatMoney(order.amount) +
            '</strong> for ' + $('<span>').text(order.credits).html() +
            (order.kind === 'CARD' ? ' credit card' : ' credits'));
        $('#credit-checkout-help').text(order.kind === 'CARD'
            ? '支付成功后会生成一张可转赠的卡密，不会增加你的积分。请复制卡密后发给对方。'
            : '支付成功后积分会自动到账。');
        $('#credit-status').text('Waiting for payment...').removeClass().addClass('text-muted');
        $('#credit-regenerate').hide();
        var qrTarget = $('#credit-qr').empty()[0];
        // eslint-disable-next-line no-new
        new QRCode(qrTarget, {
            text: qrCode,
            width: 200,
            height: 200,
            correctLevel: QRCode.CorrectLevel.M
        });
        // Why: 收银台在长页面下方时会被用户完全忽略，创建订单后必须用弹窗明确反馈。
        $('#credit-checkout').modal('show');
    }

    function startCountdown() {
        function tick() {
            var expireMs = new Date(currentOrder.expireTime).getTime();
            var remainSeconds;
            if (isNaN(expireMs)) {
                // 充值单缺 expireTime 时按建单默认 30 分钟兜底倒计时
                remainSeconds = Math.max(0, 30 * 60 -
                    Math.floor((Date.now() - currentOrder.createdAtMs) / 1000));
            } else {
                remainSeconds = Math.max(0, Math.floor((expireMs - Date.now()) / 1000));
            }
            var minutes = String(Math.floor(remainSeconds / 60)).padStart(2, '0');
            var seconds = String(remainSeconds % 60).padStart(2, '0');
            $('#credit-countdown').text('QR valid for ' + minutes + ':' + seconds);
            if (remainSeconds <= 0) {
                // Why: 归零先做一次服务端确认（轮询间隙/时钟偏差内仍可能已付款并发放），
                // 确认 status=0 才判过期，避免用户重复付款
                ajax('/ajax/credit/recharge-status', 'POST',
                     { orderNo: currentOrder.orderNo }).then(function (response) {
                    var order = unwrap(response);
                    if (order.status === 1) { markPaid(); }
                    else { markExpired(); }
                }).catch(markExpired);
            }
        }
        tick();
        countdownTimer = setInterval(tick, 1000);
    }

    function handlePollFailure(error) {
        consecutiveErrors += 1;
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
            stopPolling();
            $('#credit-status').text('Status check failed: ' + error.message)
                .removeClass().addClass('text-danger');
            $('#credit-regenerate').show();
        }
    }

    function pollOrderStatus() {
        ajax('/ajax/credit/recharge-status', 'POST',
             { orderNo: currentOrder.orderNo }).then(function (response) {
            consecutiveErrors = 0;
            var order = unwrap(response);
            currentOrder.status = order.status;
            if (order.status === 1) {
                markPaid();
            } else if (order.status === 2) {
                markExpired();
            } else if (order.status !== 0) {
                // 未知终态兜底停轮询，避免无限等待
                stopPolling();
                $('#credit-status').text('Order status: ' + order.status)
                    .removeClass().addClass('text-warning');
                $('#credit-regenerate').show();
            }
            // status 0（待支付）继续轮询
        }).catch(handlePollFailure);
    }

    function startPolling() {
        stopPolling(); // 只清轮询定时器，不动倒计时
        consecutiveErrors = 0;
        pollTimer = setInterval(pollOrderStatus, POLL_INTERVAL_MS);
    }

    function buy(packageId, kind, orderUrl, trigger) {
        hideMessages();
        stopAllTimers(); // 入口统一清场：旧订单的轮询/倒计时不再存活
        var buyButtons = $('.pkg-buy-btn, .credit-card-buy-btn').prop('disabled', true);
        var triggerButton = trigger ? $(trigger) : null;
        var triggerText = triggerButton ? triggerButton.text() : '';
        if (triggerButton) {
            triggerButton.text('正在创建订单...');
        }
        var createdOrder = null;
        ajax(orderUrl || '/ajax/credit/recharge-order', 'POST', { packageId: packageId }).then(function (response) {
            createdOrder = unwrap(response);
            return ajax('/ajax/credit/recharge-pay', 'POST', { orderNo: createdOrder.orderNo });
        }).then(function (response) {
            var precreate = unwrap(response);
            // Why: precreate 成功才整体覆盖全局订单，失败时旧收银台状态不被破坏
            currentOrder = {
                orderNo: createdOrder.orderNo,
                packageId: createdOrder.packageId,
                credits: createdOrder.credits,
                amount: createdOrder.amount,
                expireTime: createdOrder.expireTime,
                qrCode: precreate.qrCode,
                createdAtMs: Date.now(),
                kind: kind || 'CREDIT'
            };
            renderCheckout(currentOrder, currentOrder.qrCode);
            startCountdown();
            startPolling();
        }).catch(function (error) {
            showError('创建支付订单失败：' + error.message, true);
        }).finally(function () {
            buyButtons.prop('disabled', false);
            if (triggerButton) {
                triggerButton.text(triggerText);
            }
        });
    }

    // ---------- 消耗明细（R64；R49 扩展为获取+消耗统一明细） ----------
    var CONSUME_PAGE_SIZE = 10;
    var consumePageNo = 1;
    var consumeTotal = 0;
    var consumeType = ''; // ''-全部 / INCOME-获取 / CONSUME-消耗

    var TYPE_LABELS = {
        GRANT: '获取', RECHARGE: '充值', CARD_REDEEM: '积分卡兑换', CONSUME: '消耗'
    };

    function consumeFilters() {
        return {
            type: consumeType || undefined,
            caller: $('#credit-consume-caller').val() || undefined,
            startDate: $('#credit-consume-start').val() || undefined,
            endDate: $('#credit-consume-end').val() || undefined
        };
    }

    function buildConsumePayload() {
        return $.extend({ pageNo: consumePageNo, pageSize: CONSUME_PAGE_SIZE }, consumeFilters());
    }

    function formatTime(iso) {
        if (!iso) { return '-'; }
        return String(iso).replace('T', ' ').slice(0, 19);
    }

    function renderConsumeGroups(groups) {
        var container = $('#credit-consume-groups').empty();
        if (!groups || !groups.length) { return; }
        var max = groups[0].amount || 1;
        groups.forEach(function (g) {
            var row = $('<div>').addClass('credit-consume-group');
            row.append($('<span>').addClass('label').attr('title', g.name).text(g.name));
            row.append($('<span>').addClass('bar').css('width', Math.max(2, Math.round((g.amount / max) * 260)) + 'px'));
            row.append($('<span>').addClass('value')
                .text(g.amount + ' ' + 'credits · ' + (g.count || 0) + ' times · ' + (g.percent || 0) + '%'));
            container.append(row);
        });
    }

    function renderConsumeSummary(summary) {
        var box = $('#credit-consume-summary').empty();
        if (!summary) {
            box.append($('<p>').addClass('text-muted').text('No consumption data.'));
            return;
        }
        // R50：Total Tokens 不再展示（后端仍随流水记录，随时可恢复展示）
        var stats = [
            { strong: summary.totalAmount || 0, span: 'Credits Spent' },
            { strong: summary.totalCount || 0, span: 'AI Calls' }
        ];
        stats.forEach(function (st) {
            var item = $('<div>').addClass('stat');
            item.append($('<strong>').text(st.strong));
            item.append($('<span>').text(st.span));
            box.append(item);
        });
        renderConsumeGroups(summary.byCaller);
        // 用汇总结果填充功能过滤下拉（保留当前选择）；R52：模型筛选下线（model 只记录不展示）
        (function () {
            var select = $('#credit-consume-caller');
            var current = select.val();
            select.find('option:not(:first)').remove();
            (summary.byCaller || []).forEach(function (g) {
                select.append($('<option>').val(g.key).text(g.name));
            });
            if (current) { select.val(current); }
        })();
    }

    function renderConsumeRows(records) {
        var tbody = $('#credit-consume-rows').empty();
        if (!records || !records.length) {
            tbody.html('<tr><td colspan="5" class="text-muted">No records in this range.</td></tr>');
            return;
        }
        records.forEach(function (r) {
            var isIncome = r.direction === 'INCOME';
            var row = $('<tr>');
            row.append($('<td>').text(formatTime(r.createdAt)));
            // 类型徽标：获取（绿色）/ 消耗（黄色）；充值行附「更多」入口看订单详情（R51）
            var badge = $('<span>').addClass('credit-type-badge ' + (isIncome ? 'income' : 'consume'))
                .text(TYPE_LABELS[r.type] || (isIncome ? '获取' : '消耗'));
            var typeCell = $('<td>').append(badge);
            if (isIncome && r.type === 'RECHARGE' && r.detail) {
                typeCell.append(' ').append($('<a>').attr('href', 'javascript:void(0)').text('更多')
                    .on('click', function () { showRechargeDetail(r.detail); }));
            }
            row.append(typeCell);
            // R51：原因列——消耗为功能名，获取为充值单号/赠送说明
            row.append($('<td>').attr('title', r.reason || '').text(r.reason || '-'));
            // R52：model 只随流水记录，不在明细展示（后端 summary 仍按模型聚合）
            row.append($('<td>').text(isIncome ? '-' : (r.callerName || r.caller || '未知来源')));
            var credits = isIncome ? '+' + (r.amount || 0) : '-' + (r.amount || 0);
            row.append($('<td>').addClass('text-right').css('color', isIncome ? '#3c763d' : '#8a6d3b').text(credits));
            tbody.append(row);
        });
    }

    // R51：充值详情弹窗——订单号/账单号（支付宝交易号）/档位/支付金额/支付方式/支付时间
    var RECHARGE_DETAIL_FIELDS = [
        ['orderNo', '订单号'], ['transactionId', '账单号'], ['packageTitle', '充值档位'],
        ['credits', '积分'], ['multiplier', '倍率'], ['amount', '支付金额（元）'],
        ['payType', '支付方式'], ['payTime', '支付时间']
    ];
    function showRechargeDetail(detailJson) {
        var data;
        try { data = JSON.parse(detailJson); } catch (e) { data = null; }
        if (!data) { return; }
        var rows = RECHARGE_DETAIL_FIELDS.filter(function (f) {
            return data[f[0]] !== null && data[f[0]] !== undefined && data[f[0]] !== '';
        }).map(function (f) {
            return '<tr><td style="color:#777;padding:4px 12px 4px 0;white-space:nowrap">' + f[1] +
                   '</td><td style="padding:4px 0">' + $('<span>').text(String(data[f[0]])).html() + '</td></tr>';
        }).join('');
        var html = '<table style="width:100%;font-size:13px">' + rows + '</table>';
        bootstrapModal('充值详情', html);
    }
    function bootstrapModal(title, bodyHtml) {
        var modal = $(
            '<div class="modal fade" tabindex="-1" role="dialog">' +
            '<div class="modal-dialog modal-sm" role="document"><div class="modal-content">' +
            '<div class="modal-header"><button type="button" class="close" data-dismiss="modal">&times;</button>' +
            '<h4 class="modal-title"></h4></div>' +
            '<div class="modal-body"></div>' +
            '</div></div></div>');
        modal.find('.modal-title').text(title);
        modal.find('.modal-body').html(bodyHtml);
        modal.on('hidden.bs.modal', function () { modal.remove(); });
        modal.modal('show');
    }

    function renderConsumePager() {
        var pager = $('#credit-consume-pager').empty();
        var totalPages = Math.max(1, Math.ceil(consumeTotal / CONSUME_PAGE_SIZE));
        if (totalPages <= 1) { return; }
        var prev = $('<button>').addClass('btn btn-default btn-sm').attr('aria-label', 'Previous page')
            .text('< Prev').prop('disabled', consumePageNo <= 1);
        var next = $('<button>').addClass('btn btn-default btn-sm').attr('aria-label', 'Next page')
            .text('Next >').prop('disabled', consumePageNo >= totalPages);
        var info = $('<span>').addClass('text-muted').css('margin', '0 10px')
            .text(consumePageNo + ' / ' + totalPages + ' · ' + consumeTotal + ' 条');
        prev.on('click', function () { consumePageNo -= 1; loadConsumeDetail(); });
        next.on('click', function () { consumePageNo += 1; loadConsumeDetail(); });
        pager.append(prev, info, next);
    }

    function loadConsumeDetail() {
        var payload = buildConsumePayload();
        ajax('/ajax/credit/consume-summary', 'POST', payload).then(function (response) {
            renderConsumeSummary(unwrap(response));
        }).catch(function (error) {
            $('#credit-consume-summary').html('<p class="text-danger" style="margin:0">Failed to load summary: ' +
                $('<span>').text(error.message).html() + '</p>');
        });
        ajax('/ajax/credit/consume-page', 'POST', payload).then(function (response) {
            var page = unwrap(response);
            consumeTotal = page.total || 0;
            renderConsumeRows(page.records);
            renderConsumePager();
        }).catch(function (error) {
            $('#credit-consume-rows').html('<tr><td colspan="5" class="text-danger">Failed to load records: ' +
                $('<span>').text(error.message).html() + '</td></tr>');
        });
    }

    // ---------- R205：管理员发布倍率活动 ----------
    // Why 表单值直接原样提交（不做时区换算）: 管理员填的就是东八区墙上时间，
    // moon-well 用显式 Asia/Shanghai 的 Clock 解释它；前端一旦按浏览器时区换算，
    // 一个在 UTC 时区办公的管理员发布的「10-24 00:00」会提前 8 小时生效。
    var PROMOTION_DEFAULT_END = '2026-12-31T23:59:59';

    function pad2(value) {
        return String(value).padStart(2, '0');
    }

    function localInputValue(date) {
        return date.getFullYear() + '-' + pad2(date.getMonth() + 1) + '-' + pad2(date.getDate()) +
            'T' + pad2(date.getHours()) + ':' + pad2(date.getMinutes()) + ':' + pad2(date.getSeconds());
    }

    function fillPromotionDefaults() {
        if (!$('#credit-promo-start').val()) {
            var today = new Date();
            today.setHours(0, 0, 0, 0);
            $('#credit-promo-start').val(localInputValue(today));
        }
        if (!$('#credit-promo-end').val()) {
            $('#credit-promo-end').val(PROMOTION_DEFAULT_END);
        }
    }

    function renderPromotions(list) {
        var tbody = $('#credit-promo-rows').empty();
        if (!list || !list.length) {
            tbody.html('<tr><td colspan="4" class="text-muted">暂无活动记录。</td></tr>');
            return;
        }
        list.forEach(function (p) {
            var row = $('<tr>');
            // 服务端已按东八区格式化，直接展示；不要在浏览器里再 new Date() 一遍
            row.append($('<td>').text(p.startTime || '-'));
            row.append($('<td>').text(p.endTime || '-'));
            row.append($('<td>').text('×' + p.multiplier));
            row.append($('<td>').text(p.statusText || '-'));
            tbody.append(row);
        });
    }

    function loadPromotions() {
        if (!IS_ADMIN) { return; }
        ajax('/ajax/credit/admin-promotion-list', 'POST', {}).then(function (response) {
            renderPromotions(unwrap(response) || []);
        }).catch(function (error) {
            $('#credit-promo-rows').html('<tr><td colspan="4" class="text-danger">活动列表加载失败：' +
                $('<span>').text(error.message).html() + '</td></tr>');
        });
    }

    // R205 验收微调：目标用户改成下拉选择。userId 与 magicbook 本地账号不同源，
    // 手填极易打到别人头上；选项直接取 moon-well /credit/admin/users 同源数据。
    function renderAdminUserOptions(users) {
        var select = $('#credit-admin-user').empty();
        select.append($('<option>').attr('value', '').text('Select user...'));
        (users || []).forEach(function (user) {
            var label = '#' + user.userId + ' ' + (user.nickname || user.username || '') +
                (user.email ? ' (' + user.email + ')' : '');
            select.append($('<option>').attr('value', String(user.userId)).text(label));
        });
    }

    function loadAdminUserOptions() {
        if (!IS_ADMIN) { return; }
        ajax('/ajax/credit/admin-users', 'POST', {}).then(function (response) {
            renderAdminUserOptions(unwrap(response) || []);
        }).catch(function (error) {
            // 下拉加载失败必须可见：静默退化成手填会重新打开打错人的口子
            window.alert('用户列表加载失败：' + error.message + '。请刷新页面重试，不要手填用户ID。');
        });
    }

    function submitPromotion() {
        var start = $('#credit-promo-start').val();
        var end = $('#credit-promo-end').val();
        var multiplier = parseInt($('#credit-promo-multiplier').val(), 10);
        if (!start || !end || !multiplier) { return; }
        // Why 二次确认：活动发布后不可编辑/撤销（用户拍板），配错只能改库
        var summary = '倍率 ×' + multiplier + '，' + start.replace('T', ' ') + ' ~ ' +
            end.replace('T', ' ') + '（东八区）';
        if (!window.confirm('发布后不可修改或撤销，确认发布活动？\n' + summary)) {
            return;
        }
        $.ajax({
            url: '/ajax/credit/admin-promotion-create', method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ startTime: start, endTime: end, multiplier: multiplier })
        }).done(function () {
            window.alert('活动已发布。');
            loadPromotions();
            // 活动即刻影响档位展示与下单倍率，必须刷新卡片，否则管理员会以为没生效
            loadPackages();
        }).fail(function (xhr) {
            var msg = '发布失败';
            try { msg = (JSON.parse(xhr.responseText).message) || msg; } catch (err) { /* ignore */ }
            window.alert(msg);
        });
    }

    function resetConsumePage() {
        consumePageNo = 1;
        consumeTotal = 0;
    }

    $(function () {
        sessionStorage.removeItem(CSRF_RELOAD_FLAG);
        loadBalance();
        loadPackages();
        loadCardPackages();
        loadPurchasedCards();
        loadConsumeDetail();

        $('#credit-card-redeem-form').on('submit', function (e) {
            e.preventDefault();
            redeemCard();
        });
        $(document).on('click', '.credit-card-buy-btn', function () {
            buy($(this).attr('data-package-id'), 'CARD',
                '/ajax/credit/card/purchase-order', this);
        });
        $('#credit-consume-apply').on('click', resetConsumePage);
        $('#credit-consume-apply').on('click', loadConsumeDetail);
        // R205：管理员活动发布（入口仅管理员可见；moon-well 白名单二次校验）
        if (IS_ADMIN) {
            fillPromotionDefaults();
            loadPromotions();
            loadAdminUserOptions();
            loadAdminBatches();
            $('#credit-card-admin-issue-form').on('submit', function (e) {
                e.preventDefault();
                issueCardBatch();
            });
            $('#credit-card-admin-long-term').on('change', function () {
                var longTerm = $(this).is(':checked');
                $('#credit-card-admin-validity').prop('disabled', longTerm);
                if (longTerm) {
                    $('#credit-card-admin-validity').val('');
                } else if (!$('#credit-card-admin-validity').val()) {
                    $('#credit-card-admin-validity').val('30');
                }
            });
            $('#credit-promo-form').on('submit', function (e) {
                e.preventDefault();
                submitPromotion();
            });
        }
        // R54：管理员积分调整（入口仅管理员可见；moon-well 白名单二次校验）
        $('#credit-admin-adjust-form').on('submit', function (e) {
            e.preventDefault();
            var userId = parseInt($('#credit-admin-user').val(), 10);
            var amount = parseInt($('#credit-admin-amount').val(), 10);
            var reason = $.trim($('#credit-admin-reason').val());
            if (!userId || !amount || !reason) { return; }
            if (!window.confirm('确认调整用户 ' + userId + ' 的积分 ' + (amount > 0 ? '+' : '') + amount + '？此操作将记入流水审计。')) {
                return;
            }
            $.ajax({
                url: '/ajax/credit/admin-adjust', method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ userId: userId, amount: amount, reason: reason })
            }).done(function (resp) {
                var data = resp && resp.result ? resp.result : resp;
                var balance = data && data.balance !== undefined ? data.balance : '?';
                window.alert('调整成功，用户 ' + userId + ' 当前余额：' + balance);
                $('#credit-admin-adjust-form')[0].reset();
                loadConsumeDetail();
            }).fail(function (xhr) {
                var msg = '调整失败';
                try { msg = (JSON.parse(xhr.responseText).message) || msg; } catch (err) { /* ignore */ }
                window.alert(msg);
            });
        });

        // R49：获取/消耗方向切换——重置分页并立即重查
        $('.credit-type-btn').on('click', function () {
            $('.credit-type-btn').removeClass('btn-primary active').addClass('btn-default');
            $(this).addClass('btn-primary active').removeClass('btn-default');
            consumeType = $(this).attr('data-type') || '';
            resetConsumePage();
            loadConsumeDetail();
        });
        $('#credit-consume-reset').on('click', function () {
            $('#credit-consume-caller').val('');
            $('#credit-consume-start').val('');
            $('#credit-consume-end').val('');
            resetConsumePage();
            loadConsumeDetail();
        });

        $(document).on('click', '.pkg-buy-btn', function () {
            buy($(this).attr('data-package-id'), 'CREDIT',
                '/ajax/credit/recharge-order', this);
        });
        $('#credit-regenerate').on('click', function () {
            if (currentOrder && currentOrder.packageId) {
                buy(currentOrder.packageId, currentOrder.kind,
                    currentOrder.kind === 'CARD'
                        ? '/ajax/credit/card/purchase-order'
                        : '/ajax/credit/recharge-order');
            }
        });
        consumeSharedCardKey();
    });
}(jQuery));

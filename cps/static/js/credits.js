/*
 * Credits page: balance + recharge packages -> Alipay face-to-face QR checkout -> poll order status.
 * All calls go through magicbook backend proxies (/ajax/credit-*) which forward
 * to moon-well with the session-bound JWT (see _moonwell_proxy in web.py).
 * moon-well grants credits immediately when the payment settles (notify or poll compensation).
 * adminOnly packages (test tier) are hidden for non-admin users.
 */
(function ($) {
    'use strict';

    var CSRF = $('#credit-csrf').val();
    var IS_ADMIN = $('#credit-page').attr('data-is-admin') === '1';
    var POLL_INTERVAL_MS = 3000;
    var MAX_CONSECUTIVE_ERRORS = 5;
    var CSRF_RELOAD_FLAG = 'creditCsrfReloaded';

    var pollTimer = null;
    var countdownTimer = null;
    var consecutiveErrors = 0;
    var currentOrder = null; // precreate 成功前不赋值，避免失败后残留半初始化订单

    function showError(message) {
        var alertBox = $('#credit-alert');
        alertBox.removeClass('alert-success').addClass('alert-danger')
            .text(message).show();
    }

    function showSuccess(message) {
        var alertBox = $('#credit-alert');
        alertBox.removeClass('alert-danger').addClass('alert-success')
            .text(message).show();
    }

    function hideMessages() {
        $('#credit-alert').hide();
    }

    function unwrap(response) {
        if (!response || response.success !== true) {
            throw new Error(response && response.message ? response.message : 'request failed');
        }
        return response.result;
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
            var card = $('<div>').addClass('credit-package-card');
            card.append($('<div>').addClass('pkg-name').text(pkg.title));
            card.append($('<div>').addClass('pkg-price').text(formatMoney(pkg.price)));
            card.append($('<div>').addClass('pkg-desc').text(pkg.description || ''));
            card.append($('<button>').addClass('btn btn-primary btn-sm pkg-buy-btn')
                .attr('data-package-id', pkg.id)
                .text('Recharge Now'));
            container.append(card);
        });
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
        $('#credit-checkout').hide();
        var grantedCredits = currentOrder ? currentOrder.credits : null;
        ajax('/ajax/credit/account', 'POST').then(function (response) {
            var account = unwrap(response);
            renderBalance(account);
            showSuccess('充值成功：' + (grantedCredits ? grantedCredits + ' 积分已到账，' : '积分已到账，') +
                '当前余额 ' + (account && account.balance !== undefined ? account.balance : '-') + '。');
        }).catch(function () {
            // 余额刷新失败不掩盖到账事实
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
        $('#credit-checkout').show();
        $('#credit-checkout-info').html('Pay <strong>' + formatMoney(order.amount) +
            '</strong> for ' + $('<span>').text(order.credits).html() + ' credits');
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

    function buy(packageId) {
        hideMessages();
        stopAllTimers(); // 入口统一清场：旧订单的轮询/倒计时不再存活
        var buyButtons = $('.pkg-buy-btn').prop('disabled', true);
        var createdOrder = null;
        ajax('/ajax/credit/recharge-order', 'POST', { packageId: packageId }).then(function (response) {
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
                createdAtMs: Date.now()
            };
            renderCheckout(currentOrder, currentOrder.qrCode);
            startCountdown();
            startPolling();
        }).catch(function (error) {
            showError('Failed to create payment: ' + error.message);
        }).finally(function () {
            buyButtons.prop('disabled', false);
        });
    }

    $(function () {
        sessionStorage.removeItem(CSRF_RELOAD_FLAG);
        loadBalance();
        loadPackages();

        $(document).on('click', '.pkg-buy-btn', function () {
            buy($(this).attr('data-package-id'));
        });
        $('#credit-regenerate').on('click', function () {
            if (currentOrder && currentOrder.packageId) {
                buy(currentOrder.packageId);
            }
        });
    });
}(jQuery));

/*
 * Subscription page: plan list -> Alipay face-to-face QR checkout -> poll order status.
 * All calls go through magicbook backend proxies (/ajax/subscription-*) which forward
 * to moon-well with the session-bound JWT (see _moonwell_proxy in web.py).
 * Polling terminal states: 1=paid (refresh current subscription), 2=cancelled/expired;
 * any other non-zero status (e.g. 3=refunded) is treated as terminal as well.
 */
(function ($) {
    'use strict';

    var CSRF = $('#subscription-csrf').val();
    var POLL_INTERVAL_MS = 3000;
    var MAX_CONSECUTIVE_ERRORS = 5;
    var CSRF_RELOAD_FLAG = 'subscriptionCsrfReloaded';

    var pollTimer = null;
    var countdownTimer = null;
    var consecutiveErrors = 0;
    var currentOrder = null; // precreate 成功前不赋值，避免失败后残留半初始化订单

    function showError(message) {
        var alertBox = $('#sub-alert');
        alertBox.text(message).show();
    }

    function hideError() {
        $('#sub-alert').hide();
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

    // Why: 上游 LocalDateTime 序列化为无时区 ISO 串，直接截取日期部分，
    // 避免 Date 往返在东八区把 00:00–07:59 的日期偏移成前一天
    function formatDate(isoString) {
        return (typeof isoString === 'string' && isoString.length >= 10)
            ? isoString.slice(0, 10) : (isoString || '-');
    }

    function renderFeatureList(features) {
        try {
            var items = typeof features === 'string' ? JSON.parse(features) : features;
            if (Array.isArray(items) && items.length) {
                return '<ul class="sub-plan-features">' + items.map(function (item) {
                    return '<li>' + $('<span>').text(item).html() + '</li>';
                }).join('') + '</ul>';
            }
        } catch (error) { /* features 非法时静默跳过 */ }
        return '';
    }

    function loadCurrent() {
        ajax('/ajax/subscription/current').then(function (response) {
            var subscription = unwrap(response);
            if (!subscription || subscription.status !== 1) {
                $('#sub-current-info').text('No active subscription');
                return;
            }
            var planName = 'Plan #' + subscription.planId;
            var plans = window.__subPlansCache || [];
            for (var i = 0; i < plans.length; i++) {
                if (plans[i].id === subscription.planId) {
                    planName = plans[i].name;
                    break;
                }
            }
            $('#sub-current-info')
                .removeClass('text-muted')
                .text(planName + ' · ' + formatDate(subscription.endDate));
        }).catch(function () {
            // 未订阅/接口失败均按无订阅展示，不打断套餐浏览
            $('#sub-current-info').text('No active subscription');
        });
    }

    function renderPlans(plans) {
        // 价格为 0 的套餐（如 FREE）不走支付宝收银台，直接过滤
        var purchasable = plans.filter(function (plan) {
            return parseFloat(plan.price) > 0;
        });
        var container = $('#sub-plans').empty();
        if (!purchasable.length) {
            container.html('<p class="text-muted">No purchasable plans available.</p>');
            return;
        }
        purchasable.forEach(function (plan) {
            var card = $('<div>').addClass('sub-plan-card');
            card.append($('<div>').addClass('sub-plan-name').text(plan.name));
            card.append($('<div>').addClass('sub-plan-price').text(formatMoney(plan.price)));
            card.append($('<div>').addClass('sub-plan-desc').text(plan.description || ''));
            card.append(renderFeatureList(plan.features));
            card.append($('<div>').addClass('text-muted').text(
                plan.durationDays + ' days'));
            card.append($('<button>').addClass('btn btn-primary btn-sm sub-buy-btn')
                .attr('data-plan-id', plan.id)
                .text('Buy Now'));
            container.append(card);
        });
    }

    function loadPlans() {
        return ajax('/ajax/subscription/plans').then(function (response) {
            var plans = unwrap(response) || [];
            window.__subPlansCache = plans;
            renderPlans(plans);
        }).catch(function (error) {
            $('#sub-plans').empty()
                .append($('<p>').addClass('text-danger').text('Failed to load plans: ' + error.message));
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
        $('#sub-status').text('Payment received! Subscription is active.')
            .removeClass().addClass('text-success');
        $('#sub-countdown').text('');
        loadCurrent();
    }

    function markExpired() {
        stopAllTimers();
        $('#sub-status').text('Order expired.').removeClass().addClass('text-danger');
        $('#sub-countdown').text('');
        $('#sub-regenerate').show();
    }

    function renderCheckout(order, qrCode, planName) {
        $('#sub-checkout').show();
        $('#sub-checkout-info').html('Pay for <strong>' + $('<span>').text(planName).html() +
            '</strong> — ' + formatMoney(order.amount));
        $('#sub-status').text('Waiting for payment...').removeClass().addClass('text-muted');
        $('#sub-regenerate').hide();
        var qrTarget = $('#sub-qr').empty()[0];
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
                // 订单体缺 expireTime 时按建单默认 30 分钟兜底倒计时
                remainSeconds = Math.max(0, 30 * 60 -
                    Math.floor((Date.now() - currentOrder.createdAtMs) / 1000));
            } else {
                remainSeconds = Math.max(0, Math.floor((expireMs - Date.now()) / 1000));
            }
            var minutes = String(Math.floor(remainSeconds / 60)).padStart(2, '0');
            var seconds = String(remainSeconds % 60).padStart(2, '0');
            $('#sub-countdown').text('QR valid for ' + minutes + ':' + seconds);
            if (remainSeconds <= 0) {
                // Why: 归零先做一次服务端确认（轮询间隙/时钟偏差内仍可能已付款并落账），
                // 确认 status=0 才判过期，避免用户重复购买
                ajax('/ajax/subscription/order-status', 'POST',
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
            $('#sub-status').text('Status check failed: ' + error.message)
                .removeClass().addClass('text-danger');
            $('#sub-regenerate').show();
        }
    }

    function pollOrderStatus() {
        ajax('/ajax/subscription/order-status', 'POST',
             { orderNo: currentOrder.orderNo }).then(function (response) {
            consecutiveErrors = 0;
            var order = unwrap(response);
            currentOrder.status = order.status;
            if (order.status === 1) {
                markPaid();
            } else if (order.status === 2) {
                markExpired();
            } else if (order.status !== 0) {
                // 未知终态（如 3=已退款）兜底停轮询，避免无限等待
                stopPolling();
                $('#sub-status').text('Order status: ' + order.status)
                    .removeClass().addClass('text-warning');
                $('#sub-regenerate').show();
            }
            // status 0（待支付）继续轮询
        }).catch(handlePollFailure);
    }

    function startPolling() {
        stopPolling(); // 只清轮询定时器，不动倒计时
        consecutiveErrors = 0;
        pollTimer = setInterval(pollOrderStatus, POLL_INTERVAL_MS);
    }

    function buy(planId) {
        hideError();
        stopAllTimers(); // 入口统一清场：旧订单的轮询/倒计时不再存活
        var buyButtons = $('.sub-buy-btn').prop('disabled', true);
        var createdOrder = null;
        ajax('/ajax/subscription/order', 'POST', { planId: planId }).then(function (response) {
            createdOrder = unwrap(response);
            return ajax('/ajax/subscription/pay', 'POST', { orderNo: createdOrder.orderNo });
        }).then(function (response) {
            var precreate = unwrap(response);
            // Why: precreate 成功才整体覆盖全局订单，失败时旧收银台状态不被破坏
            currentOrder = {
                orderNo: createdOrder.orderNo,
                planId: createdOrder.planId,
                amount: createdOrder.amount,
                expireTime: createdOrder.expireTime,
                qrCode: precreate.qrCode,
                createdAtMs: Date.now()
            };
            var planName = 'Plan #' + currentOrder.planId;
            (window.__subPlansCache || []).forEach(function (plan) {
                if (plan.id === currentOrder.planId) { planName = plan.name; }
            });
            renderCheckout(currentOrder, currentOrder.qrCode, planName);
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
        // Why: 先加载套餐再查当前订阅，planId→套餐名映射才可用（loadPlans 内部已兜底不 reject）
        loadPlans().then(loadCurrent);

        $(document).on('click', '.sub-buy-btn', function () {
            buy(parseInt($(this).attr('data-plan-id'), 10));
        });
        $('#sub-regenerate').on('click', function () {
            if (currentOrder && currentOrder.planId) {
                buy(currentOrder.planId);
            }
        });
    });
}(jQuery));

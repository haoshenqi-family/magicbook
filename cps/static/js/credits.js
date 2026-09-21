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

    // ---------- 消耗明细（R64；R49 扩展为获取+消耗统一明细） ----------
    var CONSUME_PAGE_SIZE = 10;
    var consumePageNo = 1;
    var consumeTotal = 0;
    var consumeType = ''; // ''-全部 / INCOME-获取 / CONSUME-消耗

    var TYPE_LABELS = {
        GRANT: '获取', RECHARGE: '充值', CONSUME: '消耗'
    };

    function consumeFilters() {
        return {
            type: consumeType || undefined,
            caller: $('#credit-consume-caller').val() || undefined,
            model: $('#credit-consume-model').val() || undefined,
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
        // 用汇总结果填充功能/模型过滤下拉（保留当前选择）
        ['caller', 'model'].forEach(function (key) {
            var select = $('#credit-consume-' + key);
            var current = select.val();
            var list = key === 'caller' ? summary.byCaller : summary.byModel;
            select.find('option:not(:first)').remove();
            (list || []).forEach(function (g) {
                select.append($('<option>').val(g.key).text(g.name));
            });
            if (current) { select.val(current); }
        });
    }

    function renderConsumeRows(records) {
        var tbody = $('#credit-consume-rows').empty();
        if (!records || !records.length) {
            tbody.html('<tr><td colspan="6" class="text-muted">No records in this range.</td></tr>');
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
            row.append($('<td>').text(isIncome ? '-' : (r.callerName || r.caller || '未知来源')));
            row.append($('<td>').text(isIncome ? '-' : (r.model || '-')));
            var credits = isIncome ? '+' + (r.amount || 0) : '-' + (r.amount || 0);
            row.append($('<td>').addClass('text-right').css('color', isIncome ? '#3c763d' : '#8a6d3b').text(credits));
            tbody.append(row);
        });
    }

    // R51：充值详情弹窗——订单号/账单号（支付宝交易号）/档位/支付金额/支付方式/支付时间
    var RECHARGE_DETAIL_FIELDS = [
        ['orderNo', '订单号'], ['transactionId', '账单号'], ['packageTitle', '充值档位'],
        ['credits', '积分'], ['amount', '支付金额（元）'], ['payType', '支付方式'],
        ['payTime', '支付时间']
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

    function resetConsumePage() {
        consumePageNo = 1;
        consumeTotal = 0;
    }

    $(function () {
        sessionStorage.removeItem(CSRF_RELOAD_FLAG);
        loadBalance();
        loadPackages();
        loadConsumeDetail();

        $('#credit-consume-apply').on('click', resetConsumePage);
        $('#credit-consume-apply').on('click', loadConsumeDetail);
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
            $('#credit-consume-model').val('');
            $('#credit-consume-start').val('');
            $('#credit-consume-end').val('');
            resetConsumePage();
            loadConsumeDetail();
        });

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

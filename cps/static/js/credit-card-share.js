/*
 * Credit-card share landing page.
 * The bearer key deliberately travels in the URL fragment only, so it is never
 * sent to Flask, reverse proxies or access logs. This page explains the flow;
 * it never redeems automatically because link previews and accidental opens
 * must not consume a one-time card.
 */
(function () {
    'use strict';

    var PENDING_KEY = 'creditCardPendingRedeem';
    var root = document.getElementById('credit-card-share');
    if (!root) { return; }

    var keyElement = document.getElementById('credit-share-key');
    var summaryElement = document.getElementById('credit-share-summary');
    var alertElement = document.getElementById('credit-share-alert');
    var copyButton = document.getElementById('credit-share-copy-key');
    var loginLink = document.getElementById('credit-share-login');
    var redeemLink = document.getElementById('credit-share-redeem');
    var authenticated = root.getAttribute('data-authenticated') === '1';
    var params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    var key = (params.get('key') || '').trim();
    var credits = (params.get('credits') || '').trim();

    function showAlert(message, kind) {
        alertElement.textContent = message;
        alertElement.className = 'alert credit-share-alert alert-' + (kind || 'danger');
        alertElement.style.display = 'block';
    }

    function copyFallback(text) {
        var area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', '');
        area.style.position = 'fixed';
        area.style.opacity = '0';
        document.body.appendChild(area);
        area.select();
        try {
            return document.execCommand('copy');
        } catch (error) {
            return false;
        } finally {
            document.body.removeChild(area);
        }
    }

    function copyKey() {
        function done() {
            showAlert('卡密已复制。登录后到积分页粘贴兑换即可。', 'success');
        }
        function fallback() {
            if (copyFallback(key)) {
                done();
            } else {
                showAlert('复制失败，请手动选择卡密复制。', 'danger');
            }
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(key).then(done).catch(fallback);
        } else {
            fallback();
        }
    }

    if (!key) {
        summaryElement.textContent = '分享链接不完整，无法读取卡密。';
        copyButton.disabled = true;
        redeemLink.style.display = 'none';
        loginLink.style.display = 'none';
        showAlert('请让分享者重新发送完整链接。', 'danger');
        return;
    }

    keyElement.textContent = key;
    summaryElement.textContent = credits
        ? '这是一张 ' + credits + ' 积分的积分卡，兑换后会立即计入你的账户。'
        : '兑换后会立即计入你的账户。';

    var redeemTarget = '/credits#redeem=' + encodeURIComponent(key);
    redeemLink.href = redeemTarget;
    redeemLink.style.display = authenticated ? 'inline-block' : 'none';
    loginLink.style.display = authenticated ? 'none' : 'inline-block';

    copyButton.addEventListener('click', copyKey);
    loginLink.addEventListener('click', function () {
        // OIDC/login redirects cannot carry the fragment back, so persist it for
        // the credits page in this same tab before leaving for authentication.
        sessionStorage.setItem(PENDING_KEY, JSON.stringify({
            key: key,
            credits: credits,
            savedAt: Date.now()
        }));
    });
}());

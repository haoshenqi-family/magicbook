// me_submission.js — R279 「账号 → 建议一本书」投稿面板。
//
// Why 独立文件：me.html 原本零 JS，投稿是唯一需要 fetch 的交互；
// 复用 MBApi（R177 全站公共层：CSRF + 解包口径），不另起一套。
(function () {
  'use strict';

  var fileInput, filenameSpan, declaration, submitButton, alertBox, historyBox;

  function t(id) {
    return typeof window.mbT === 'function' ? window.mbT(id) : id;
  }

  function setStatus(text, isError) {
    alertBox.textContent = text;
    alertBox.style.display = 'block';
    alertBox.classList.toggle('alert-danger', !!isError);
    alertBox.classList.toggle('alert-success', !isError);
  }

  function statusLabel(status) {
    var map = {
      PENDING: 'Pending review',
      APPROVED: 'Approved',
      REJECTED: 'Rejected',
      INGESTED: 'In library',
      FAILED: 'Ingest failed',
    };
    return t(map[status] || status);
  }

  function loadHistory() {
    if (!window.MBApi) return;
    window.MBApi.getJson('/ajax/library/submissions/mine').then(function (response) {
      if (!response.ok || !response.data || response.data.success !== true) return;
      var rows = response.data.result || [];
      if (!rows.length) {
        historyBox.textContent = '';
        return;
      }
      historyBox.innerHTML = rows.slice(0, 5).map(function (row) {
        return '<div>#' + row.id + ' ' + t('Submission') + ' ' +
          escapeHtml(row.originalFilename) + ' — ' + statusLabel(row.status) + '</div>';
      }).join('');
    });
  }

  function escapeHtml(value) {
    var div = document.createElement('div');
    div.textContent = value === null || value === undefined ? '' : String(value);
    return div.innerHTML;
  }

  function submit() {
    var file = fileInput.files && fileInput.files[0];
    if (!file) {
      setStatus(t('Choose a file first'), true);
      return;
    }
    if (!declaration.checked) {
      setStatus(t('You must confirm you have the right to share this file.'), true);
      return;
    }
    var form = new FormData();
    form.append('file', file);
    form.append('declaration', '1');
    submitButton.disabled = true;
    fetch('/ajax/library/submit', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': window.MBApi.csrfToken() },
      body: form,
    }).then(function (response) {
      return response.json().then(function (data) {
        return { ok: response.ok, data: data };
      });
    }).then(function (result) {
      submitButton.disabled = false;
      if (result.ok && result.data && result.data.success === true) {
        setStatus(t('Submitted; an admin will review it'), false);
        fileInput.value = '';
        filenameSpan.textContent = '';
        refreshSubmitState();
        loadHistory();
      } else {
        setStatus((result.data && result.data.message) || t('Something went wrong'), true);
      }
    }).catch(function () {
      submitButton.disabled = false;
      setStatus(t('Something went wrong'), true);
    });
  }

  function refreshSubmitState() {
    var file = fileInput.files && fileInput.files[0];
    submitButton.disabled = !(file && declaration.checked);
  }

  document.addEventListener('DOMContentLoaded', function () {
    fileInput = document.getElementById('submission-file');
    filenameSpan = document.getElementById('submission-filename');
    declaration = document.getElementById('submission-declaration');
    submitButton = document.getElementById('submission-submit');
    alertBox = document.getElementById('submission-alert');
    historyBox = document.getElementById('submission-history');
    if (!fileInput) return;
    fileInput.addEventListener('change', function () {
      var file = fileInput.files && fileInput.files[0];
      filenameSpan.textContent = file ? file.name : '';
      refreshSubmitState();
    });
    declaration.addEventListener('change', refreshSubmitState);
    submitButton.addEventListener('click', submit);
    loadHistory();
  });
})();

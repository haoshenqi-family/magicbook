// admin_submissions.js — R279 书籍投稿审核页。
//
// Why 独立文件：审核动作要直接操作台账（通过/驳回/失败重试），与积分治理、
// 运营邮件的领域不同；共用面只有 MBApi（CSRF + httpJson），按 R177 纪律
// 全局层已由 layout.html 提供。
(function () {
  'use strict';

  var tbody = null;
  var alertBox = null;

  function t(id) {
    return typeof window.mbT === "function" ? window.mbT(id) : id;
  }

  function httpJson(url, options) {
    if (!window.MBApi || typeof window.MBApi.httpJson !== "function") {
      // 全局层缺失时直接报错而不是静默假成功（R44/R173 家族纪律）。
      throw new Error("MBApi unavailable");
    }
    return window.MBApi.httpJson(url, options || { credentials: "same-origin" });
  }

  function postJson(url, body) {
    if (!window.MBApi || typeof window.MBApi.postJson !== "function") {
      throw new Error("MBApi unavailable");
    }
    return window.MBApi.postJson(url, body);
  }

  function setStatus(text, isError) {
    alertBox.textContent = text;
    alertBox.style.display = 'block';
    alertBox.classList.toggle('alert-danger', !!isError);
    alertBox.classList.toggle('alert-success', !isError);
  }

  function escapeHtml(value) {
    var div = document.createElement('div');
    div.textContent = value === null || value === undefined ? '' : String(value);
    return div.innerHTML;
  }

  function statusBadge(status) {
    var map = {
      PENDING: ['label-warning', 'Pending review'],
      APPROVED: ['label-info', 'Approved'],
      REJECTED: ['label-default', 'Rejected'],
      INGESTED: ['label-success', 'In library'],
      FAILED: ['label-danger', 'Ingest failed'],
    };
    var entry = map[status] || ['label-default', status];
    return '<span class="label ' + entry[0] + '">' + t(entry[1]) + '</span>';
  }

  function formatSize(bytes) {
    var n = Number(bytes) || 0;
    if (n >= 1024 * 1024) return (n / (1024 * 1024)).toFixed(1) + ' MB';
    if (n >= 1024) return (n / 1024).toFixed(0) + ' KB';
    return n + ' B';
  }

  function actionButtons(row) {
    var buttons = '';
    var preview = '<a class="btn btn-xs btn-default" href="/ajax/admin/submissions/' +
      row.id + '/preview">' + t('Preview') + '</a> ';
    if (row.status === 'PENDING' || row.status === 'FAILED') {
      buttons += preview;
      buttons += '<button class="btn btn-xs btn-success" data-act="approve" data-id="' +
        row.id + '">' + t('Approve & ingest') + '</button> ';
      if (row.status === 'PENDING') {
        buttons += '<button class="btn btn-xs btn-danger" data-act="reject" data-id="' +
          row.id + '">' + t('Reject') + '</button>';
      }
    } else if (row.status === 'INGESTED' && row.bookId) {
      buttons += preview + '<a class="btn btn-xs btn-default" href="/book/' +
        row.bookId + '">' + t('Open book') + '</a>';
    } else {
      buttons += preview;
    }
    return buttons;
  }

  function renderRows(rows) {
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted">' +
        t('No submissions yet') + '</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (row) {
      return '<tr data-id="' + row.id + '">' +
        '<td>' + row.id + '</td>' +
        '<td>' + escapeHtml(row.originalFilename) + '</td>' +
        '<td>' + formatSize(row.size) + '</td>' +
        '<td>' + statusBadge(row.status) + (row.errorMessage ?
          '<div class="text-danger small">' + escapeHtml(row.errorMessage) + '</div>' : '') +
        '</td>' +
        '<td>' + escapeHtml(row.note || '') + '</td>' +
        '<td>' + actionButtons(row) + '</td>' +
        '</tr>';
    }).join('');
  }

  function load() {
    httpJson('/ajax/admin/submissions').then(function (response) {
      var data = response.data;
      if (!response.ok || !data || data.success !== true) {
        setStatus(t('Failed to load submissions'), true);
        return;
      }
      renderRows(data.result || []);
    }).catch(function () {
      setStatus(t('Failed to load submissions'), true);
    });
  }

  function review(id, approve) {
    var note = '';
    if (!approve) {
      note = window.prompt(t('Rejection note (optional)')) || '';
    }
    postJson('/ajax/admin/submissions/' + id + '/review', {
      approve: approve, note: note,
    }).then(function (response) {
      var data = response.data;
      if (response.ok && data && data.success === true) {
        setStatus(approve ? t('Approved; ingest started') : t('Rejected'), false);
        load();
      } else {
        setStatus((data && data.message) || t('Review action failed'), true);
      }
    }).catch(function () {
      setStatus(t('Review action failed'), true);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    tbody = document.getElementById('submissions-body');
    alertBox = document.getElementById('submissions-alert');
    if (!tbody) return;
    tbody.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-act]');
      if (!button) return;
      review(parseInt(button.getAttribute('data-id'), 10),
        button.getAttribute('data-act') === 'approve');
    });
    load();
  });
})();

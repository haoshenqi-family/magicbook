// Why: 中文输入法用回车确认候选词时，浏览器可能同时触发原生表单提交或 JS 的 Enter 处理
//      （header 搜索、高级搜索、typeahead 下拉、AI 聊天发送等），导致搜索条件未写完就被误提交。
// How: 在 document 捕获阶段拦截输入框/文本域的回车 keydown，若处于组合输入
//      （isComposing / composition 标记）则 preventDefault + stopPropagation，
//      同时挡住原生提交和 typeahead 等元素级监听；对不设置 isComposing、只给 keyCode 229
//      的浏览器直接拦截该 keydown；compositionend 后保留 100ms 宽限，
//      兼容部分 IME"候选先上屏、再补发不带标记的 Enter"的时序。
(function () {
  var composing = false;
  var clearTimer = null;

  document.addEventListener('compositionstart', function () {
    if (clearTimer) {
      clearTimeout(clearTimer);
      clearTimer = null;
    }
    composing = true;
  }, true);

  document.addEventListener('compositionend', function () {
    if (clearTimer) clearTimeout(clearTimer);
    clearTimer = setTimeout(function () {
      composing = false;
      clearTimer = null;
    }, 100);
  }, true);

  document.addEventListener('keydown', function (e) {
    var t = e.target;
    if (!t || (t.tagName !== 'INPUT' && t.tagName !== 'TEXTAREA')) return;
    if (e.keyCode === 229) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    var isEnter = e.key === 'Enter' || e.keyCode === 13;
    if (!isEnter || e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
    if (e.isComposing || composing) {
      e.preventDefault();
      e.stopPropagation();
    }
  }, true);
})();

/* Detects which reader is active (epub/pdf/txt) and extracts the current page text.
   Exposes window.AICompanion.getPageContext() -> string (sync)
   and window.AICompanion.getPageContextAsync() -> Promise<string> (for PDF).
   Loaded by ai_chat_panel.html (included in each reader template). */
(function () {
  "use strict";
  window.AICompanion = window.AICompanion || {};

  function truncate(text, max) {
    max = max || 8000;
    if (!text) return "";
    text = text.replace(/\s+/g, " ").trim();
    return text.length > max ? text.slice(0, max) + "..." : text;
  }

  function extractEpub() {
    try {
      if (typeof reader === "undefined" || !reader || !reader.rendition) return "";
      var contents = reader.rendition.getContents();
      if (!contents || !contents.length) return "";
      var texts = [];
      for (var i = 0; i < contents.length; i++) {
        var doc = contents[i].document || (contents[i].contentDocument || contents[i]);
        if (doc && doc.body) {
          texts.push(doc.body.innerText || doc.body.textContent || "");
        }
      }
      return truncate(texts.join("\n\n"));
    } catch (e) {
      console.warn("AICompanion epub extract failed:", e);
      return "";
    }
  }

  function extractTxt() {
    try {
      var el = document.getElementById("content");
      if (el) return truncate(el.innerText || el.textContent);
      return "";
    } catch (e) {
      return "";
    }
  }

  function detectFormat() {
    if (typeof reader !== "undefined" && reader && reader.rendition) return "epub";
    if (typeof PDFViewerApplication !== "undefined") return "pdf";
    if (document.getElementById("content") && document.getElementById("readmain")) return "txt";
    return "unknown";
  }

  // Synchronous extractor (best-effort; PDF returns "" here and uses async)
  window.AICompanion.getPageContext = function () {
    var fmt = detectFormat();
    if (fmt === "epub") return extractEpub();
    if (fmt === "txt") return extractTxt();
    return "";
  };

  // Async extractor (PDF needs getTextContent which is async)
  window.AICompanion.getPageContextAsync = function () {
    var fmt = detectFormat();
    if (fmt === "pdf" && typeof PDFViewerApplication !== "undefined" && PDFViewerApplication.pdfDocument) {
      var pageNum = PDFViewerApplication.page || 1;
      return PDFViewerApplication.pdfDocument.getPage(pageNum).then(function (page) {
        return page.getTextContent();
      }).then(function (tc) {
        var text = (tc.items || []).map(function (it) { return it.str; }).join(" ");
        return truncate(text);
      }).catch(function () { return ""; });
    }
    return Promise.resolve(window.AICompanion.getPageContext());
  };

  window.AICompanion.detectFormat = detectFormat;
})();

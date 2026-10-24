/* Detects which reader is active (epub/pdf/txt) and extracts the current page text.
   Exposes window.AICompanion.getPageContext() -> string (sync)
   and window.AICompanion.getPageContextAsync() -> Promise<string> (for PDF).
   On regular pages it extracts the rendered body as the site assistant's context.
   Loaded by ai_chat_panel.html (site layout and reader templates). */
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
    return "site";
  }

  function extractSitePage() {
    try {
      var clone = document.body.cloneNode(true);
      ["script", "style", "noscript", "nav", "header", "footer", "iframe", "#ai-companion-root"]
        .forEach(function (selector) {
          clone.querySelectorAll(selector).forEach(function (el) { el.remove(); });
        });
      var heading = clone.querySelector("h1") || clone.querySelector("h2");
      var headingText = heading ? (heading.innerText || heading.textContent || "").trim() : "";
      var text = (clone.innerText || clone.textContent || "").replace(/\s+/g, " ").trim();
      var title = document.title || "";
      var prefix = "Page title: " + title;
      if (headingText && headingText !== title) prefix += " | Page heading: " + headingText;
      return truncate(prefix + "\n" + text);
    } catch (e) {
      return "";
    }
  }

  // Synchronous extractor (best-effort; PDF returns "" here and uses async)
  window.AICompanion.getPageContext = function () {
    var fmt = detectFormat();
    if (fmt === "epub") return extractEpub();
    if (fmt === "txt") return extractTxt();
    if (fmt === "site") return extractSitePage();
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
    if (fmt === "site") return Promise.resolve(extractSitePage());
    return Promise.resolve(window.AICompanion.getPageContext());
  };

  window.AICompanion.detectFormat = detectFormat;
})();

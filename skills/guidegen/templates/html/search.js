// GuideGen manual: client-side search over an embedded index, click-to-zoom, mobile sidebar, active section.
(function () {
  "use strict";
  var index = JSON.parse(document.getElementById("search-index").textContent || "[]");
  var q = document.getElementById("q");
  var results = document.getElementById("results");
  var active = -1;

  function norm(s) { return (s || "").toLowerCase(); }
  function score(entry, terms) {
    var t = norm(entry.t), x = norm(entry.x), s = 0;
    for (var i = 0; i < terms.length; i++) {
      var term = terms[i];
      if (t.indexOf(term) >= 0) s += 10; else if (x.indexOf(term) >= 0) s += 2; else return 0;
    }
    return s;
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function close() {
    results.hidden = true; q.setAttribute("aria-expanded", "false"); q.removeAttribute("aria-activedescendant"); active = -1;
  }
  function select(i) {
    var items = results.querySelectorAll("li");
    items.forEach(function (li, j) { li.setAttribute("aria-selected", j === i ? "true" : "false"); });
    active = i;
    // screen readers announce the highlighted result; keep it visible in a long list
    if (items[i]) { q.setAttribute("aria-activedescendant", items[i].id); items[i].scrollIntoView({ block: "nearest" }); }
  }
  function search() {
    var terms = norm(q.value).split(/\s+/).filter(Boolean);
    if (!terms.length) { close(); return; }
    var hits = index.map(function (e) { return { e: e, s: score(e, terms) }; })
      .filter(function (h) { return h.s > 0; }).sort(function (a, b) { return b.s - a.s; }).slice(0, 12);
    results.innerHTML = hits.length ? hits.map(function (h, i) {
      return '<li role="option" id="r' + i + '" aria-selected="false"><a href="' + h.e.u + '">' + esc(h.e.t) + "<small>" + esc(h.e.s) + "</small></a></li>";
    }).join("") : '<li role="option" aria-disabled="true"><a>No results</a></li>';
    results.hidden = false;
    q.setAttribute("aria-expanded", "true");
    q.removeAttribute("aria-activedescendant");
    active = -1;
  }
  q.addEventListener("input", search);
  q.addEventListener("keydown", function (ev) {
    var items = results.querySelectorAll("li a[href]");
    if (ev.key === "ArrowDown" && items.length) { ev.preventDefault(); select(Math.min(active + 1, items.length - 1)); }
    else if (ev.key === "ArrowUp" && items.length) { ev.preventDefault(); select(Math.max(active - 1, 0)); }
    else if (ev.key === "Enter" && items.length) { ev.preventDefault(); (items[active >= 0 ? active : 0]).click(); close(); }
    else if (ev.key === "Escape") { close(); }
  });
  results.addEventListener("click", function () { close(); });
  document.addEventListener("click", function (ev) { if (!ev.target.closest(".search")) close(); });

  // click-to-zoom
  var dlg = document.getElementById("zoom");
  document.querySelectorAll(".zoomable").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var img = btn.querySelector("img");
      var big = dlg.querySelector("img");
      big.src = img.src; big.alt = img.alt;
      if (dlg.showModal) dlg.showModal(); else window.open(img.src);
    });
  });
  dlg.addEventListener("click", function (ev) { if (ev.target === dlg) dlg.close(); });

  // mobile sidebar
  var toggle = document.querySelector(".menu-toggle");
  var sidebar = document.getElementById("sidebar");
  toggle.addEventListener("click", function () {
    var open = sidebar.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
  sidebar.addEventListener("click", function (ev) {
    if (ev.target.tagName === "A" && window.matchMedia("(max-width: 900px)").matches) {
      sidebar.classList.remove("open"); toggle.setAttribute("aria-expanded", "false");
    }
  });

  // highlight the current section in the sidebar
  if ("IntersectionObserver" in window) {
    var links = {};
    sidebar.querySelectorAll("a[href^='#']").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && links[en.target.id]) {
          Object.keys(links).forEach(function (k) { links[k].removeAttribute("aria-current"); });
          links[en.target.id].setAttribute("aria-current", "true");
        }
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    document.querySelectorAll("article[id], section[id]").forEach(function (el) { obs.observe(el); });
  }
})();

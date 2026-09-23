/* Tender Radar front end. Matching rules mirror radar/match.py. */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var REGIONS = { anywhere: null, ontario: ["Ontario", "National Capital Region", "Ottawa"], ncr: ["National Capital Region", "Ottawa"] };
  var IDEAS = ["cleaning", "printing", "software", "furniture", "training", "snow", "catering", "security"];
  var PAGE = 20;
  var data = [], words = [], shown = PAGE, loaded = false;

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  // ---------- matching (same rules as radar/match.py) ----------
  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  function specific(regions) { return (regions || []).filter(function (r) { return ["Canada", "World", "Foreign"].indexOf(r) < 0; }); }
  function inRegion(t, region) {
    var wanted = REGIONS[region]; if (!wanted) return true;
    var named = specific(t.regions); if (!named.length) return true;
    return named.some(function (r) { return wanted.some(function (w) { return r.indexOf(w) > -1; }); });
  }
  function isLocal(t, region) {
    var wanted = REGIONS[region], named = specific(t.regions);
    return !!(wanted && named.length && named.some(function (r) { return wanted.some(function (w) { return r.indexOf(w) > -1; }); }));
  }
  function match(region) {
    var pats = words.map(function (w) { return { w: w, re: new RegExp("\\b" + esc(w)) }; });
    if (!pats.length) return [];
    var out = [];
    data.forEach(function (t) {
      if (!inRegion(t, region)) return;
      var hits = pats.filter(function (p) { return p.re.test(t.text); }).map(function (p) { return p.w; });
      if (!hits.length) return;
      var title = t.title.toLowerCase();
      out.push({ t: t, hits: hits, local: isLocal(t, region), inTitle: pats.some(function (p) { return p.re.test(title); }) });
    });
    // Local work first, then tenders whose title mentions the word, then soonest deadline
    var rank = function (b) { return b ? 0 : 1; };
    out.sort(function (a, b) {
      return rank(a.local) - rank(b.local) || rank(a.inTitle) - rank(b.inTitle) || (a.t.closes < b.t.closes ? -1 : a.t.closes > b.t.closes ? 1 : 0);
    });
    return out;
  }

  // ---------- helpers ----------
  function daysLeft(iso) {
    var d = new Date(iso.slice(0, 10) + "T00:00:00"), now = new Date(); now.setHours(0, 0, 0, 0);
    return Math.round((d - now) / 86400000);
  }
  function niceDate(iso) { return new Date(iso.slice(0, 10) + "T12:00:00").toLocaleDateString("en-CA", { month: "long", day: "numeric", year: "numeric" }); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  // ---------- steps ----------
  function show(id) {
    ["p1", "p2", "p3"].forEach(function (p) { $(p).hidden = p !== id; });
    document.querySelectorAll(".step").forEach(function (b) { b.setAttribute("aria-selected", b.dataset.p === id ? "true" : "false"); });
    if (id === "p2") { shown = PAGE; renderList(); }
    if (id === "p3") renderKeep();
    save();
    window.scrollTo(0, 0);
  }
  document.querySelectorAll(".step").forEach(function (b) { b.addEventListener("click", function () { show(b.dataset.p); }); });
  $("to2").addEventListener("click", function () { show("p2"); });

  // ---------- words ----------
  function renderChips() {
    var c = $("chips"); c.textContent = "";
    words.forEach(function (w, i) {
      var b = el("button", "chip"); b.type = "button"; b.setAttribute("aria-label", "Remove " + w);
      b.appendChild(document.createTextNode(w));
      var x = el("span", null, "×"); x.setAttribute("aria-hidden", "true"); b.appendChild(x);
      b.addEventListener("click", function () { words.splice(i, 1); renderChips(); save(); });
      c.appendChild(b);
    });
    $("chipHint").hidden = !words.length;
  }
  function addWord(v) {
    v = (v || "").trim().toLowerCase().replace(/[^a-z0-9\- ]/g, "");
    if (v.length < 3) { $("wordErr").textContent = "Use a word with at least 3 letters, like “paint”."; $("wordErr").hidden = false; return; }
    $("wordErr").hidden = true;
    if (words.indexOf(v) < 0 && words.length < 10) words.push(v);
    renderChips(); save();
  }
  $("addForm").addEventListener("submit", function (e) { e.preventDefault(); addWord($("word").value); $("word").value = ""; });
  $("word").addEventListener("input", function () { $("wordErr").hidden = true; });
  IDEAS.forEach(function (w) {
    var b = el("button", "idea", w); b.type = "button";
    b.addEventListener("click", function () { addWord(w); });
    $("ideas").appendChild(b);
  });
  $("where").addEventListener("change", save);

  // ---------- matches ----------
  function renderList() {
    var box = $("list"); box.textContent = ""; $("more").hidden = true;
    if (!loaded) { $("mh").textContent = "Still loading…"; $("mhint").textContent = ""; return; }
    if (!words.length) { $("mh").textContent = "Add a word first"; $("mhint").textContent = "Go back to step 1 and tell us what you sell."; return; }
    var m = match($("where").value);
    $("mh").textContent = m.length ? m.length + (m.length === 1 ? " open tender for you" : " open tenders for you") : "No matches today";
    $("mhint").textContent = m.length ? "Work in your area comes first. Tenders with your word in the title come before ones that only mention it in the details." : "";
    if (!m.length) {
      box.appendChild(el("p", null, "Nothing mentions " + words.join(", ") + " right now. Try a shorter word (“clean” finds cleaning and cleaners), or check again tomorrow. New tenders are added every day."));
      return;
    }
    m.slice(0, shown).forEach(function (o) {
      var t = o.t, d = daysLeft(t.closes), card = el("article", "tender");
      card.appendChild(el("h3", null, t.title));
      var f = el("div", "facts");
      f.appendChild(el("span", "fact" + (d <= 7 ? " soon" : ""), d <= 0 ? "Closes today" : "Closes in " + d + (d === 1 ? " day" : " days")));
      f.appendChild(el("span", "fact", t.category));
      f.appendChild(el("span", "fact", "Where: " + t.where));
      card.appendChild(f);
      card.appendChild(el("p", null, t.summary));
      card.appendChild(el("p", "meta", "Buyer: " + t.buyer + (t.place ? " (" + t.place + ")" : "") + " · Deadline " + niceDate(t.closes) + " · Matched: " + o.hits.join(", ")));
      var a = el("a", "open", t.exactLink ? "Open the official notice ↗" : "Search CanadaBuys ↗");
      a.href = t.url; a.target = "_blank"; a.rel = "noopener";
      card.appendChild(a);
      if (!t.exactLink) card.appendChild(el("p", "meta", "No direct link was published. Reference number: " + t.id + (t.contact ? ". Buyer contact: " + t.contact : "")));
      box.appendChild(card);
    });
    if (m.length > shown) { $("more").hidden = false; $("more").textContent = "Show more (" + (m.length - shown) + " left)"; }
  }
  $("more").addEventListener("click", function () { shown += PAGE; renderList(); });

  // ---------- keep ----------
  function shareUrl() {
    var u = location.origin + location.pathname;
    return words.length ? u + "?words=" + encodeURIComponent(words.join(",")) + "&where=" + $("where").value : u;
  }
  function renderKeep() {
    $("share").value = shareUrl();
    var m = loaded ? match($("where").value) : [];
    var lines = [m.length + " open tender" + (m.length === 1 ? "" : "s") + " for " + (words.join(", ") || "your work") + ":", ""];
    m.slice(0, 15).forEach(function (o) { lines.push("- " + o.t.title + " (closes " + niceDate(o.t.closes) + ")"); lines.push("  " + o.t.url); });
    if (m.length > 15) lines.push("", "…and " + (m.length - 15) + " more at " + shareUrl());
    $("digest").value = lines.join("\n");
  }
  function copy(field, msg) {
    var done = function () { $("copied").textContent = msg; };
    var fallback = function () { $(field).select(); $("copied").textContent = "Selected. Press Ctrl+C (or ⌘+C) to copy."; };
    if (navigator.clipboard) navigator.clipboard.writeText($(field).value).then(done, fallback); else fallback();
  }
  $("copyLink").addEventListener("click", function () { copy("share", "Link copied."); });
  $("copyDigest").addEventListener("click", function () { copy("digest", "List copied."); });

  // ---------- state ----------
  function save() { store("tr-words", words.join(",")); store("tr-where", $("where").value); }
  function restore() {
    var q = new URLSearchParams(location.search);
    var w = q.get("words") || store("tr-words") || "cleaning,printing";
    words = w.split(",").map(function (s) { return s.trim(); }).filter(Boolean).slice(0, 10);
    var where = q.get("where") || store("tr-where");
    if (where && REGIONS.hasOwnProperty(where)) $("where").value = where;
  }
  restore(); renderChips();

  fetch("data/tenders.json", { cache: "no-cache" }).then(function (r) {
    if (!r.ok) throw new Error(r.status); return r.json();
  }).then(function (j) {
    data = j.tenders || []; loaded = true;
    $("fresh").textContent = j.count + " open tenders, updated " + new Date(j.updated).toLocaleString("en-CA", { dateStyle: "long", timeStyle: "short" }).replace(/\.$/, "") + ".";
    if (!$("p2").hidden) renderList();
  }).catch(function () {
    $("fresh").textContent = "Today's tenders couldn't load. Refresh the page, or try again in a few minutes.";
  });
})();

/* ---------------------------------------------------------------
   Language switcher. Translates the whole site - navigation, headings,
   buttons, the sixteen itineraries and the legal pages. Page strings come
   from assets/i18n/<page>.js, built by tools/i18n_build.py; anything not
   translated yet falls back to English per string, never per page.
   --------------------------------------------------------------- */
(function (win, doc) {
  'use strict';
  var LANGS = win.JV_I18N || {}, S = win.JV_STRINGS || {};
  var KEY = 'jeevo_lang';

  function pick() {
    try { var sv = win.localStorage.getItem(KEY); if (sv && LANGS[sv]) return sv; } catch (e) {}
    /* fall back to the browser's own preference before defaulting to English */
    var navLangs = win.navigator.languages || [win.navigator.language || 'en'];
    for (var i = 0; i < navLangs.length; i++) {
      var base = String(navLangs[i]).toLowerCase().split('-')[0];
      if (LANGS[base]) return base;
    }
    return 'en';
  }

  var active = 'en';

  /* translate one subtree - used for anything injected after first paint */
  function paint(root, lang) {
    /* alt / title / aria-label / meta description are attributes, so
       textContent never reaches them - images and page titles would stay
       English in every language without this */
    var ats = root.querySelectorAll ? root.querySelectorAll('[data-i18n-attr]') : [];
    for (var a = 0; a < ats.length; a++) {
      var spec = ats[a].getAttribute('data-i18n-attr').split(';');
      for (var t = 0; t < spec.length; t++) {
        var bits = spec[t].split(':'), arow = S[bits[1]];
        if (bits.length === 2 && arow) ats[a].setAttribute(bits[0], arow[lang] || arow.en);
      }
    }
    var phs = root.querySelectorAll ? root.querySelectorAll('[data-i18n-ph]') : [];
    for (var p = 0; p < phs.length; p++) {
      var pk = phs[p].getAttribute('data-i18n-ph'), prow = S[pk];
      if (prow) phs[p].setAttribute('placeholder', prow[lang] || prow.en);
    }
    var nodes = root.querySelectorAll ? root.querySelectorAll('[data-i18n]') : [];
    for (var i = 0; i < nodes.length; i++) {
      var k = nodes[i].getAttribute('data-i18n'), row = S[k];
      if (!row) continue;
      var val = row[lang] || row.en;
      if (nodes[i].textContent !== val) nodes[i].textContent = val;
    }
    if (root.getAttribute && root.getAttribute('data-i18n')) {
      var rk = root.getAttribute('data-i18n'), rr = S[rk];
      if (rr) {
        var rv = rr[lang] || rr.en;
        if (root.textContent !== rv) root.textContent = rv;
      }
    }
  }

  function apply(lang) {
    if (!LANGS[lang]) lang = 'en';
    active = lang;
    var nodes = doc.querySelectorAll('[data-i18n]');
    for (var i = 0; i < nodes.length; i++) {
      var k = nodes[i].getAttribute('data-i18n');
      var row = S[k];
      if (!row) continue;
      nodes[i].textContent = row[lang] || row.en;
    }
    /* placeholders and aria-labels are attributes, so textContent never reaches
       them - a form would stay English in every language without this */
    /* alt / title / aria-label / meta description are attributes, so
       textContent never reaches them - images and page titles would stay
       English in every language without this */
    var ats = doc.querySelectorAll('[data-i18n-attr]');
    for (var a = 0; a < ats.length; a++) {
      var spec = ats[a].getAttribute('data-i18n-attr').split(';');
      for (var t = 0; t < spec.length; t++) {
        var bits = spec[t].split(':'), arow = S[bits[1]];
        if (bits.length === 2 && arow) ats[a].setAttribute(bits[0], arow[lang] || arow.en);
      }
    }
    var phs = doc.querySelectorAll('[data-i18n-ph]');
    for (var p = 0; p < phs.length; p++) {
      var pk = phs[p].getAttribute('data-i18n-ph'), prow = S[pk];
      if (prow) phs[p].setAttribute('placeholder', prow[lang] || prow.en);
    }
    doc.documentElement.setAttribute('lang', lang);
    doc.documentElement.setAttribute('dir', LANGS[lang].dir);
    /* right-to-left needs the page mirrored, but never the logo or the photos */
    doc.documentElement.classList.toggle('jv-rtl', LANGS[lang].dir === 'rtl');
    try { win.localStorage.setItem(KEY, lang); } catch (e) {}
    var note = doc.querySelector('.jv-lang-note');
    if (note && S['i18n.note']) note.textContent = lang === 'en' ? '' : (S['i18n.note'][lang] || '');
    var cur = doc.querySelector('.jv-lang-current');
    if (cur) cur.textContent = LANGS[lang].name;
    /* scripts that write textContent themselves cannot use data-i18n, so they
       look strings up with jvT() and re-run on this event */
    try { doc.dispatchEvent(new CustomEvent('jv:lang', { detail: lang })); } catch (e) {}
  }

  /* which language is showing - for scripts and for the chat backend */
  win.jvLang = function () { return active; };

  /* string lookup for scripts that build their own text */
  win.jvT = function (key, fallback) {
    var row = S[key];
    return row ? (row[active] || row.en) : (fallback || '');
  };

  function build() {
    var host = doc.querySelector('.nav-container');
    if (!host || doc.querySelector('.jv-lang')) return;

    var wrap = doc.createElement('div');
    wrap.className = 'jv-lang';
    var opts = '';
    for (var code in LANGS) {
      opts += '<option value="' + code + '">' + LANGS[code].name + '</option>';
    }
    wrap.innerHTML =
      '<label class="jv-sr-only" for="jv-lang-select" data-i18n="i18n.label">' +
        'Language</label>' +
      '<span class="jv-lang-globe" aria-hidden="true">&#127760;</span>' +
      '<select id="jv-lang-select" class="jv-lang-select">' + opts + '</select>' +
      '<span class="jv-lang-current" aria-hidden="true"></span>';

    var toggle = host.querySelector('.nav-toggle');
    if (toggle) host.insertBefore(wrap, toggle); else host.appendChild(wrap);

    var sel = wrap.querySelector('select');
    sel.addEventListener('change', function () { apply(sel.value); });
    return sel;
  }

  function init() {
    var sel = build();
    var lang = pick();
    if (sel) sel.value = lang;
    apply(lang);
  }

  /* The nav drawer and some widgets are built by their own scripts after this
     one has already run, so their labels would stay English. Re-translate
     anything that appears later. */
  function watch() {
    if (!win.MutationObserver || !doc.body) return;
    new win.MutationObserver(function (muts) {
      if (active === 'en') return;
      for (var i = 0; i < muts.length; i++) {
        var added = muts[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          if (added[j].nodeType === 1) paint(added[j], active);
        }
      }
    }).observe(doc.body, { childList: true, subtree: true });
  }

  function boot() { init(); watch(); }

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', boot);
  else boot();
})(window, document);

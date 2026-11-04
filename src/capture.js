/*! Broad Eye Solutions · Signals and Attribution Blueprint · capture.js · MIT License
 *   https://github.com/BroadEyeSolutions/power-law-signals
 *
 * Load on every page of the site (in <head>). It keeps where the visitor came from for the whole visit, then
 * writes it into any lead form as hidden fields at the moment the form is sent.
 *
 *   last touch   the tracking parameters of the arrival that started this visit (sessionStorage)
 *   first touch  the very first arrival this browser recorded (localStorage, written once)
 *   session id   one id per visit, so behavior in your analytics can be joined to the lead
 *
 * Only the parameters listed in KEYS are read. Anything else in the address (a name, an email, a form answer) is
 * never stored, so nothing personal ends up in the lead's tracking fields.
 *
 * The capture URL. Every submission also carries the page it was sent from, with that page's own tracking
 * parameters (the KEYS only). A visitor who opted out of tracking isn't followed from page to page, and their wish is
 * kept. But the page they submit from is part of what they submit, under the form's consent checkbox, and on the
 * page an ad sent them to it still carries the ad's parameters. That's why web leads can be attributed far more
 * completely than most teams expect, from the capture URL and the user agent alone.
 *
 * Optional settings, set before this file loads:
 *   window.PLS_CONFIG = {
 *     keys: [...],              replace the parameter list
 *     fieldPrefix: 'pls_',      hidden-field name prefix
 *     storeFirstTouch: false    skip localStorage (for example until the visitor consents)
 *     persist: false            keep nothing between pages: the form still gets the tags and capture URL of the
 *                               page it's on
 *     optedOut: true            the visitor opted out of tracking (set it from your consent tool). Implies
 *                               persist: false, and marks the submission so the server sends nothing about this
 *                               lead to the ad platforms. Your own attribution still works from the capture URL
 *   }
 *
 * Every lead form carries three attributes, read at submit:
 *   data-pls-form-id="WF-0007"     its id in the form map (maps/MAP_FORM.csv)
 *   data-pls-capture="web_form"    the capture method (web_form unless the form says otherwise)
 *   data-pls-brand="EX"            the brand the form belongs to (maps/MAP_BRAND.csv)
 *
 * API: PLS.fill(form, eventId) writes the hidden fields and returns them. PLS.newEventId() makes the one id each
 * submission carries everywhere: the lead record, the browser conversion and the server conversion.
 */
(function (w, d) {
  'use strict';
  var cfg = w.PLS_CONFIG || {};
  var KEYS = cfg.keys || [
    // the names, in the traditional fields: source, medium, campaign, term (keyword, or the ad set's name), content (the ad's name)
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    // the platform's own IDs, each in a field of its own, so every report joins the platform's one to one
    'utm_campaignid', 'utm_adgroupid', 'utm_adid',
    'placement', 'network', 'device', 'matchtype',
    // click ids the platforms add to the address
    'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid', 'ttclid', 'li_fat_id'
  ];
  var PREFIX = cfg.fieldPrefix || 'pls_';
  var LAST = 'pls_last', FIRST = 'pls_first', SID = 'pls_session';

  function read(store, k) { try { return JSON.parse(store.getItem(k) || 'null'); } catch (e) { return null; } }
  function write(store, k, v) { try { store.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked: keep going */ } }
  function newEventId() {
    try { if (w.crypto && w.crypto.randomUUID) return w.crypto.randomUUID(); } catch (e) { /* fall through */ }
    return 'pls-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 12);
  }
  function cleanUrl(href) { try { var u = new URL(href); return u.origin + u.pathname; } catch (e) { return ''; } }
  // The capture URL: the page address with only its allow-listed tracking parameters kept
  function captureUrl(href) {
    try {
      var u = new URL(href), q = new URLSearchParams();
      KEYS.forEach(function (k) { var v = u.searchParams.get(k); if (v) q.set(k, String(v).slice(0, 200)); });
      var qs = q.toString();
      return u.origin + u.pathname + (qs ? '?' + qs : '');
    } catch (e) { return ''; }
  }
  // The full referral URL: where the visitor was before this page. Browsers usually send only another site's origin.
  function refOf(ref) { return ref ? String(ref).slice(0, 500) : ''; }
  function cookie(name) {
    var m = d.cookie.match(new RegExp('(?:^|; )' + name.replace(/[.$?*|{}()[\]\\/+^]/g, '\\$&') + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  var ss = null, ls = null;
  var keep = cfg.persist !== false && cfg.optedOut !== true;
  try { ss = keep ? w.sessionStorage : null; } catch (e) { ss = null; }
  try { ls = keep && cfg.storeFirstTouch !== false ? w.localStorage : null; } catch (e) { ls = null; }

  var params = new URLSearchParams(w.location.search);
  var found = {};
  var tagged = false;
  KEYS.forEach(function (k) {
    var v = params.get(k);
    if (v) { found[k] = String(v).slice(0, 200); tagged = true; }
  });

  var now = new Date().toISOString();
  var last = ss ? read(ss, LAST) : null;
  // A tagged arrival replaces the visit's touch. Moving between pages without tags keeps it.
  if (tagged || !last) {
    last = { params: found, landing_page: cleanUrl(w.location.href), referral_url: refOf(d.referrer), at: now };
    if (ss) write(ss, LAST, last);
  }
  var first = ls ? read(ls, FIRST) : null;
  if (!first) { first = last; if (ls) write(ls, FIRST, first); }
  var sid = ss ? read(ss, SID) : null;
  if (!sid) { sid = newEventId(); if (ss) write(ss, SID, sid); }

  function fields(eventId) {
    var out = {};
    KEYS.forEach(function (k) { out[k] = (last.params && last.params[k]) || ''; });
    out.landing_page = last.landing_page || '';
    out.referral_url = last.referral_url || '';
    out.arrived_at = last.at || '';
    out.first_utm_source = (first.params && first.params.utm_source) || '';
    out.first_utm_medium = (first.params && first.params.utm_medium) || '';
    out.first_utm_campaign = (first.params && first.params.utm_campaign) || '';
    out.first_landing_page = first.landing_page || '';
    out.first_referral_url = first.referral_url || '';
    out.first_seen_at = first.at || '';
    out.form_page = captureUrl(w.location.href);   // the capture URL, with the page's own tracking parameters
    out.session_id = sid;
    out.tracking = cfg.optedOut === true ? 'opted_out' : 'allowed';
    out.event_id = eventId || '';
    // Meta's browser cookies, if its pixel is on the page. They let the server-side conversion match the click.
    out.fbp = cookie('_fbp');
    out.fbc = cookie('_fbc');
    return out;
  }

  function fill(form, eventId) {
    var f = fields(eventId);
    // Which form, how the lead was captured and which brand. Every form carries its own id from the form map
    // (maps/MAP_FORM.csv), so the CRM can tell forms apart and attribution can use what each form was built for.
    f.form_id = form.getAttribute('data-pls-form-id') || '';
    f.capture_method = form.getAttribute('data-pls-capture') || 'web_form';
    f.brand = form.getAttribute('data-pls-brand') || '';
    Object.keys(f).forEach(function (k) {
      var name = PREFIX + k;
      var el = form.querySelector('input[name="' + name + '"]');
      if (!el) {
        el = d.createElement('input');
        el.type = 'hidden';
        el.name = name;
        form.appendChild(el);
      }
      el.value = f[k];
    });
    return f;
  }

  w.PLS = w.PLS || {};
  w.PLS.keys = KEYS.slice();
  w.PLS.sessionId = sid;
  w.PLS.fields = fields;
  w.PLS.fill = fill;
  w.PLS.newEventId = newEventId;
  w.PLS.cleanUrl = cleanUrl;
  w.PLS.captureUrl = captureUrl;
})(window, document);

/*! Broad Eye Solutions · Signals and Attribution Blueprint · submit.js · MIT License
 *   https://github.com/BroadEyeSolutions/power-law-signals
 *
 * Sends a lead form in the right order:
 *   1. one event id for this submission, written into the hidden fields with everything capture.js kept
 *   2. the server saves the lead and answers (it decides qualified, from src/signal-rules.json)
 *   3. only then: the move to the thank-you page the server's answer picks. A qualified lead goes to
 *      /thank-you/next-steps/, every other lead to /thank-you/. The pages are for the visitor, so their addresses are
 *      neutral: nothing in an address decides anything, and no answer or code is ever in one
 *   4. the thank-you page pushes the data layer events, once. The events carry the conversion, never the page
 *
 * The record is saved before anything else happens. A save fired from the browser as the page is leaving can lose
 * that race, and the lead is never saved. The events wait for the next page for the same reason: a tag fired as a page
 * unloads can lose the race too.
 *
 * Usage (after capture.js):
 *   <form action="/lead" method="post" data-pls-next="/thank-you/" data-pls-next-qualified="/thank-you/next-steps/"> ... </form>
 *   <script>PLS.wire(document.querySelector('form'))</script>
 * and on both thank-you pages:
 *   <script src="/src/submit.js"></script><script>PLS.thankYou()</script>
 *
 * Data layer events, pushed by the thank-you page (the tag manager routes them to the ad platforms):
 *   lead_submitted         every saved lead, on either page. Meta's custom Inquiry, Google's observation-only action and
 *                          analytics fire on it. Never the bidding goal.
 *   qualified_conversion   only for a lead the server said qualified. The tag manager fires the platforms' conversion
 *                          on this event, never on the page address: on financial-services pixels Meta's Core Setup
 *                          can strip everything after the domain, so a rule on the address may never fire (gtm/README.md).
 *                          The one conversion the platforms bid on.
 * Both carry event_id (also the lead id), so a browser conversion and a server conversion of the same lead count once.
 * The page pushes them once: the hand-off from the form is read and removed, so a reload or a direct visit to either
 * thank-you page pushes nothing. Neither event carries the answers or their codes: every tag in the container can read
 * the data layer. A team that keeps the threshold in the tag manager instead can turn the codes on with
 * PLS.wire(form, { pushCodes: true }) (see gtm/README.md for the trade-off).
 * Visitors who opted out of tracking (PLS_CONFIG.optedOut) get the right page and no hand-off, so nothing is pushed.
 */
(function (w, d) {
  'use strict';

  var KEY = 'pls_submitted';

  function optedOut() { return !!(w.PLS_CONFIG && w.PLS_CONFIG.optedOut === true); }

  function wire(form, opts) {
    opts = opts || {};
    var button = form.querySelector('[type="submit"]');
    var status = form.querySelector('[data-pls-status]');
    var next = opts.next || form.getAttribute('data-pls-next') || '/thank-you/';
    var nextQualified = opts.nextQualified || form.getAttribute('data-pls-next-qualified') || '/thank-you/next-steps/';
    var busy = false;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (busy) return;
      if (form.reportValidity && !form.reportValidity()) return;
      busy = true;
      if (button) button.disabled = true;
      if (status) status.textContent = '';

      var eventId = w.PLS.newEventId();
      w.PLS.fill(form, eventId);

      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { accept: 'application/json' } })
        .then(function (r) {
          return r.json().catch(function () { return {}; }).then(function (j) {
            if (!r.ok || !j.ok) throw new Error(j.error || ('HTTP ' + r.status));
            return j;
          });
        })
        .then(function (res) {
          var hand = { event_id: res.lead_id, lead_id: res.lead_id, qualified: !!res.qualified,
            form_id: form.getAttribute('data-pls-form-id') || '', capture_method: form.getAttribute('data-pls-capture') || 'web_form' };
          if (res.qualified && res.value !== null && res.value !== undefined) { hand.value = res.value; hand.currency = res.currency; }
          if (opts.pushCodes) hand.codes = res.codes || {};
          if (!optedOut()) {
            try { w.sessionStorage.setItem(KEY, JSON.stringify(hand)); } catch (err) { /* private mode: the page still moves on */ }
          }
          w.location.assign(res.qualified ? nextQualified : next);
        })
        .catch(function () {
          busy = false;
          if (button) button.disabled = false;
          if (status) status.textContent = opts.errorText || 'That didn’t go through. Please try again.';
        });
    });
  }

  // On both thank-you pages: push the events for the lead that was just saved, once.
  function thankYou() {
    var hand = null;
    try {
      hand = JSON.parse(w.sessionStorage.getItem(KEY) || 'null');
      w.sessionStorage.removeItem(KEY);
    } catch (err) { hand = null; }
    if (!hand || !hand.event_id) return null;            // a reload, a bookmark or a direct visit: nothing to count
    w.dataLayer = w.dataLayer || [];
    var base = { event_id: hand.event_id, lead_id: hand.lead_id, form_id: hand.form_id, capture_method: hand.capture_method };
    Object.keys(hand.codes || {}).forEach(function (k) { base['code_' + k] = hand.codes[k] || ''; });
    var lead = { event: 'lead_submitted' };
    Object.keys(base).forEach(function (k) { lead[k] = base[k]; });
    w.dataLayer.push(lead);
    if (hand.qualified) {
      var q = { event: 'qualified_conversion' };
      Object.keys(base).forEach(function (k) { q[k] = base[k]; });
      if (hand.value !== undefined) { q.value = hand.value; q.currency = hand.currency; }
      w.dataLayer.push(q);
    }
    return hand;
  }

  w.PLS = w.PLS || {};
  w.PLS.wire = wire;
  w.PLS.thankYou = thankYou;
})(window, document);

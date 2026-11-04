/*! Broad Eye Solutions · Signals and Attribution Blueprint · signal.js · MIT License
 *   https://github.com/BroadEyeSolutions/power-law-signals
 *
 * Turns form answers into ordered codes and decides whether a lead is qualified, from one rules file
 * (src/signal-rules.json). Runs in the browser (window.PLSSignal) and on the server (require / import).
 *
 *   evaluate(rules, answers) -> { codes, unknown, qualified }
 *     answers  { monthly_sales: '30k_to_100k', years_in_business: '1_to_3' }   (the option values from the form)
 *     codes    { monthly_sales: '1100', years_in_business: '1000' }           (null when an answer is missing or unknown)
 *     unknown  ['monthly_sales=30-100k']                                       (answers that matched no code: log these)
 *
 * Match on option values, never on the visible label. A label edited for wording (a changed dash, a new currency
 * symbol) then can't silently break the rule.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.PLSSignal = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function encode(rules, answers) {
    var codes = {};
    var unknown = [];
    var questions = rules.questions || {};
    Object.keys(questions).forEach(function (q) {
      var raw = answers ? answers[q] : undefined;
      if (raw === undefined || raw === null || String(raw).trim() === '') { codes[q] = null; return; }
      var v = String(raw).trim();
      var map = questions[q].codes || {};
      if (Object.prototype.hasOwnProperty.call(map, v)) codes[q] = map[v];
      else { codes[q] = null; unknown.push(q + '=' + v); }
    });
    return { codes: codes, unknown: unknown };
  }

  function passes(cond, codes) {
    var c = codes[cond.question];
    if (typeof c !== 'string') return false;
    if (typeof cond.starts_with === 'string') return c.indexOf(cond.starts_with) === 0;
    if (Array.isArray(cond.in)) return cond.in.indexOf(c) !== -1;
    return false;
  }

  function qualifies(rules, codes) {
    var q = rules.qualified || {};
    if (Array.isArray(q.all) && q.all.length) return q.all.every(function (c) { return passes(c, codes); });
    if (Array.isArray(q.any) && q.any.length) return q.any.some(function (c) { return passes(c, codes); });
    return false;
  }

  function evaluate(rules, answers) {
    var e = encode(rules, answers);
    return { codes: e.codes, unknown: e.unknown, qualified: qualifies(rules, e.codes) };
  }

  return { encode: encode, qualifies: qualifies, evaluate: evaluate };
});

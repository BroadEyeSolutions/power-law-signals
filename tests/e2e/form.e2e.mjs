// End-to-end check of the example form in a real browser (Playwright's Chromium).
//   node tests/e2e/form.e2e.mjs
// The page, the scripts and POST /lead are all served in-process: /lead runs the real handler from server/.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createLeadHandler } from '../../server/lead-endpoint.mjs';

// Playwright is resolved the CommonJS way, so a global install works too.
const { chromium } = createRequire(import.meta.url)('playwright');

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const rules = JSON.parse(readFileSync(path.join(root, 'src/signal-rules.json'), 'utf8'));
const saved = [];
const sent = [];
const handle = createLeadHandler({ rules, save: async (l) => { saved.push(l); }, send: [async (l) => { sent.push(l.lead_id); }] });

const ORIGIN = 'https://pls.test';
const browser = await chromium.launch();
const page = await browser.newPage();
await page.route(ORIGIN + '/**', async (route) => {
  const req = route.request();
  const url = new URL(req.url());
  if (url.pathname === '/lead') {
    const res = await handle(new Request(url, { method: req.method(), headers: req.headers(), body: req.postDataBuffer() }));
    return route.fulfill({ status: res.status, headers: { 'content-type': 'application/json' }, body: await res.text() });
  }
  if (url.pathname === '/thank-you/') return route.fulfill({ status: 200, contentType: 'text/html', body: readFileSync(path.join(root, 'examples/thank-you.html')) });
  if (url.pathname === '/thank-you/next-steps/') return route.fulfill({ status: 200, contentType: 'text/html', body: readFileSync(path.join(root, 'examples/thank-you-next-steps.html')) });
  if (url.pathname === '/other.html') return route.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><script src="/src/capture.js"></script><a id="go" href="/examples/form.html">apply</a>' });
  const file = path.join(root, url.pathname);
  const type = file.endsWith('.html') ? 'text/html' : file.endsWith('.js') ? 'text/javascript' : 'application/octet-stream';
  try { return route.fulfill({ status: 200, contentType: type, body: readFileSync(file) }); } catch { return route.fulfill({ status: 404, body: '' }); }
});

// Arrive on another page with tags, then move to the form with none: the visit keeps its touch.
await page.goto(ORIGIN + '/other.html?utm_source=meta&utm_medium=fb&utm_campaign=lead-gen-2611&utm_campaignid=2385&utm_adgroupid=2386&utm_adid=2387&fbclid=IwAR-xyz&email=leak@example.com');
await page.click('#go');
await page.waitForURL('**/examples/form.html');
await page.evaluate(() => { window.dataLayer = []; });

await page.fill('#first_name', 'Ana');
await page.fill('#last_name', 'Ruiz');
await page.fill('#email', 'ana@example.com');
await page.fill('#phone', '5550102030');
await page.fill('#company', 'Ruiz Supply');
await page.selectOption('#monthly_sales', '30k_to_100k');
await page.selectOption('#years_in_business', '1_to_3');
await page.check('input[name="consent"]');

const formLayer = () => page.evaluate(() => (window.dataLayer || []).filter((e) => e.event).map((e) => e.event));
assert.deepEqual(await formLayer(), [], 'the form page pushes nothing before the save');
const navigated = page.waitForURL('**/thank-you/next-steps/');
await page.click('button[type="submit"]');
await navigated;
await page.waitForFunction(() => (window.dataLayer || []).length > 0);
// the events come from the thank-you page the server picked, once, for the lead it just saved
const layer = await page.evaluate(() => JSON.parse(JSON.stringify(window.dataLayer)));

assert.equal(saved.length, 1, 'one lead saved');
const lead = saved[0];
assert.equal(lead.tracking.utm_source, 'meta');
assert.equal(lead.tracking.utm_campaign, 'lead-gen-2611');
assert.equal(lead.tracking.utm_adid, '2387', 'the ad id survives the move between pages');
assert.equal(lead.tracking.fbclid, 'IwAR-xyz');
assert.equal(lead.tracking.landing_page, ORIGIN + '/other.html', 'landing page kept, without its query string');
assert.ok(!JSON.stringify(lead.tracking).includes('leak@example.com'), 'parameters outside the list are never stored');
assert.equal(lead.qualified, true);
assert.equal(lead.form_id, 'WF-0001', 'the form id reaches the record');
assert.equal(lead.capture_method, 'web_form');
assert.equal(lead.brand, 'EX', 'the hard-coded brand reaches the record');
assert.equal(lead.capture_url, ORIGIN + '/examples/form.html', 'the capture URL is the page the form was sent from');
assert.equal(lead.lead_id, lead.tracking.event_id, 'the event id is the lead id');
assert.deepEqual(sent, [lead.lead_id], 'the server-side conversion went out once, for this lead');

const names = layer.map((e) => e.event);
assert.deepEqual(names, ['lead_submitted', 'qualified_conversion']);
assert.ok(layer.every((e) => e.event_id === lead.lead_id), 'browser events carry the same id');
assert.ok(!JSON.stringify(layer).includes('30k_to_100k'), 'the answer never enters the data layer');
assert.ok(!JSON.stringify(layer).includes('code_'), 'nor its code, unless a team turns pushCodes on');
assert.ok(!page.url().includes('30k') && !page.url().includes('?'), 'the thank-you page address carries nothing');

// A reload of the thank-you page pushes nothing: the hand-off from the form was read once and removed.
await page.reload();
assert.deepEqual(await page.evaluate(() => (window.dataLayer || []).filter((e) => e.event).length), 0, 'a reload counts nothing');

// A visitor who opted out of tracking lands straight on the form from an ad. Nothing is kept between pages, and the
// capture URL still carries the ad's tags (only the allow-listed ones), so the lead is still attributed.
const page2 = await browser.newPage();
await page2.route(ORIGIN + '/**', async (route) => {
  const url = new URL(route.request().url());
  if (url.pathname === '/lead') {
    const req = route.request();
    const res = await handle(new Request(url, { method: req.method(), headers: req.headers(), body: req.postDataBuffer() }));
    return route.fulfill({ status: res.status, headers: { 'content-type': 'application/json' }, body: await res.text() });
  }
  if (url.pathname === '/thank-you/') return route.fulfill({ status: 200, contentType: 'text/html', body: readFileSync(path.join(root, 'examples/thank-you.html')) });
  if (url.pathname === '/thank-you/next-steps/') return route.fulfill({ status: 200, contentType: 'text/html', body: readFileSync(path.join(root, 'examples/thank-you-next-steps.html')) });
  const file = path.join(root, url.pathname);
  const type = file.endsWith('.html') ? 'text/html' : 'text/javascript';
  try { return route.fulfill({ status: 200, contentType: type, body: readFileSync(file) }); } catch { return route.fulfill({ status: 404, body: '' }); }
});
await page2.addInitScript(() => { window.PLS_CONFIG = { optedOut: true }; });
await page2.goto(ORIGIN + '/examples/form.html?utm_source=meta&utm_medium=ig&utm_campaignid=120200000000101&utm_adid=901&email=leak@example.com');
await page2.fill('#first_name', 'Bo');
await page2.fill('#last_name', 'Lee');
await page2.fill('#email', 'bo@example.com');
await page2.fill('#phone', '5550104040');
await page2.fill('#company', 'Lee Tools');
await page2.selectOption('#monthly_sales', '10k_to_30k');
await page2.selectOption('#years_in_business', '3_to_5');
await page2.check('input[name="consent"]');
const nav2 = page2.waitForURL('**/thank-you/');
await page2.click('button[type="submit"]');
await nav2;
const lead2 = saved[1];
assert.equal(await page2.evaluate(() => sessionStorage.length), 0, 'nothing kept between pages for an opted-out visitor');
assert.equal(lead2.tracking_choice, 'opted_out');
assert.equal(lead2.capture_url, ORIGIN + '/examples/form.html?utm_source=meta&utm_medium=ig&utm_campaignid=120200000000101&utm_adid=901', 'the capture URL keeps the ad\'s tags');
assert.ok(!lead2.capture_url.includes('leak'), 'and nothing outside the allow-list');
assert.equal(lead2.qualified, false);
assert.ok(page2.url().endsWith('/thank-you/'), 'a lead that doesn\'t qualify lands on the other page');
assert.deepEqual(await page2.evaluate(() => (window.dataLayer || []).filter((e) => e.event).length), 0, 'and an opted-out visitor\'s page pushes nothing');

console.log('e2e ok: saved', lead.lead_id, '| events on the next-steps page', names.join(', '), '| a reload pushed nothing | opted-out lead attributed from its capture URL');
await browser.close();

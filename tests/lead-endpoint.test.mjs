import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createLeadHandler, metaConversions, normalizePhone, webhookSave, inAppBrowser } from '../server/lead-endpoint.mjs';

const rules = JSON.parse(readFileSync(new URL('../src/signal-rules.json', import.meta.url), 'utf8'));
const sha = (s) => createHash('sha256').update(s).digest('hex');

function post(fields, headers = {}) {
  const body = new URLSearchParams(fields);
  return new Request('https://example.test/lead', { method: 'POST', body, headers: { 'user-agent': 'test-agent', 'cf-connecting-ip': '203.0.113.9', ...headers } });
}
const base = {
  first_name: 'Ana', last_name: 'Ruiz', email: ' Ana@Example.COM ', phone: '(555) 010-2030', company: 'Ruiz Supply',
  monthly_sales: '30k_to_100k', years_in_business: '3_to_5', consent: 'yes',
  pls_event_id: 'evt-123', pls_utm_source: 'meta', pls_utm_adid: '120200000000001', pls_fbclid: 'IwAR-abc',
  pls_form_page: 'https://example.test/apply/?utm_source=meta&utm_medium=ig&utm_campaignid=120200000000101', pls_arrived_at: '2026-10-01T12:00:00.000Z', pls_form_id: 'WF-0001', pls_capture_method: 'web_form', pls_brand: 'EX'
};

test('a lead that clears the line is saved first, then sent to Meta once, with the same id', async () => {
  const order = [];
  const saved = [];
  const sent = [];
  const fakeFetch = async (url, init) => { order.push('meta'); sent.push({ url, body: JSON.parse(init.body) }); return new Response('{}', { status: 200 }); };
  const handle = createLeadHandler({
    rules,
    save: async (lead) => { order.push('save'); saved.push(lead); },
    send: [metaConversions({ pixelId: '123', accessToken: 'tok', apiVersion: 'vX', fetchImpl: fakeFetch, value: 250, currency: 'USD' })],
    now: () => Date.parse('2026-10-01T12:05:00Z')
  });
  const res = await handle(post(base));
  const out = await res.json();
  assert.equal(res.status, 200);
  assert.deepEqual(order, ['save', 'meta']);
  assert.equal(out.lead_id, 'evt-123');
  assert.equal(out.qualified, true);
  assert.deepEqual(out.codes, { monthly_sales: '1100', years_in_business: '1100' });
  assert.equal(saved[0].email, 'ana@example.com');
  assert.equal(saved[0].tracking.utm_adid, '120200000000001');
  assert.equal(saved[0].form_id, 'WF-0001');
  assert.equal(saved[0].capture_url, 'https://example.test/apply/?utm_source=meta&utm_medium=ig&utm_campaignid=120200000000101', 'the capture URL keeps its tracking parameters');
  assert.equal(saved[0].capture_method, 'web_form');
  assert.equal(saved[0].brand, 'EX');
  assert.deepEqual(saved[0].said, { monthly_sales: 'SA-0001', years_in_business: 'SA-0002' }, 'each answer keeps its question\'s SAID');
  assert.equal(saved[0].consent, true);
  assert.equal(saved[0].consent_at, saved[0].received_at, 'consent is stamped when it was given');
  const ev = sent[0].body.data[0];
  assert.equal(ev.event_name, 'Lead');
  assert.equal(ev.event_id, 'evt-123', 'event_id matches the lead id, so the browser pixel event deduplicates');
  assert.equal(ev.user_data.em[0], sha('ana@example.com'));
  assert.equal(ev.user_data.ph[0], sha('15550102030'));
  assert.equal(ev.user_data.fbc, 'fb.1.' + Date.parse('2026-10-01T12:00:00.000Z') + '.IwAR-abc');
  assert.equal(ev.event_source_url, 'https://example.test/apply/', 'the platform gets the page without its query string');
  assert.deepEqual(ev.custom_data, { value: 250, currency: 'USD' });
  assert.ok(!sent[0].url.includes('access_token'), 'the token never goes in the address');
  assert.equal(sent[0].body.access_token, 'tok', 'the token goes in the body');
  assert.ok(!JSON.stringify(sent[0].body).includes('30k_to_100k'), 'the answer never reaches the platform');
  assert.ok(!JSON.stringify(sent[0].body).includes('1100'), 'nor its code');
});

test('a lead that clears the line, from a visitor who opted out of tracking is saved, attributed and never sent', async () => {
  let sends = 0;
  const saved = [];
  const handle = createLeadHandler({ rules, save: async (l) => { saved.push(l); }, send: [async () => { sends++; }] });
  const out = await (await handle(post({ ...base, pls_tracking: 'opted_out' }))).json();
  assert.equal(out.qualified, true);
  assert.equal(sends, 0, 'nothing about the lead reaches the ad platforms');
  assert.equal(saved[0].tracking_choice, 'opted_out');
  assert.ok(saved[0].capture_url.includes('utm_source=meta'), 'the capture URL still carries the attribution');
});

test('a lead below the line is saved and never sent', async () => {
  let sends = 0;
  const handle = createLeadHandler({ rules, save: async () => {}, send: [async () => { sends++; }] });
  const out = await (await handle(post({ ...base, monthly_sales: '10k_to_30k' }))).json();
  assert.equal(out.qualified, false);
  assert.equal(out.value, null);
  assert.equal(sends, 0);
});

test('every saved lead is forwarded to the CRM after the save, and a failed forward still answers ok', async () => {
  const order = [];
  const handle = createLeadHandler({
    rules,
    save: async () => { order.push('store'); },
    forward: [async () => { order.push('crm'); throw new Error('CRM down'); }]
  });
  const res = await handle(post({ ...base, monthly_sales: 'under_10k' }));
  assert.equal(res.status, 200, 'the store has the submission, so the visitor sees a success');
  assert.deepEqual(order, ['store', 'crm'], 'below the line too: every lead goes to the CRM, after the store');
});

test('if the save fails, the visitor gets an error and nothing is forwarded or sent', async () => {
  let sends = 0;
  const handle = createLeadHandler({ rules, save: async () => { throw new Error('down'); }, forward: [async () => { sends++; }], send: [async () => { sends++; }] });
  const res = await handle(post(base));
  assert.equal(res.status, 502);
  assert.equal(sends, 0);
});

test('bots that fill the honeypot get a quiet success and nothing is saved', async () => {
  let saves = 0;
  const handle = createLeadHandler({ rules, save: async () => { saves++; } });
  const out = await (await handle(post({ ...base, company_website: 'http://spam.example' }))).json();
  assert.equal(out.ok, true);
  assert.equal(saves, 0);
});

test('a bad email is refused', async () => {
  const handle = createLeadHandler({ rules, save: async () => {} });
  const res = await handle(post({ ...base, email: 'not-an-email' }));
  assert.equal(res.status, 400);
});

test('phone numbers become digits with the country code', () => {
  assert.equal(normalizePhone('(555) 010-2030'), '15550102030');
  assert.equal(normalizePhone('+44 20 7946 0000'), '442079460000');
  assert.equal(normalizePhone(''), '');
});

test('webhookSave throws when the webhook does not confirm the write', async () => {
  const save = webhookSave({ url: 'https://hook.test', fetchImpl: async () => new Response('', { status: 500 }) });
  await assert.rejects(save({ lead_id: 'x' }));
});

test('in-app browsers are recognized from the user agent', () => {
  assert.equal(inAppBrowser('Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 330.0.0.40.92'), 'instagram');
  assert.equal(inAppBrowser('Mozilla/5.0 (iPhone) Mobile/15E148 [FBAN/FBIOS;FBAV/470.0.0.40.98]'), 'facebook');
  assert.equal(inAppBrowser('Mozilla/5.0 (iPhone) Mobile/15E148 [FBAN/MessengerForiOS;FBAV/470.0]'), 'messenger');
  assert.equal(inAppBrowser('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.5 Safari/605.1.15'), '');
});

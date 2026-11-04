// Broad Eye Solutions · Signals and Attribution Blueprint · server/lead-endpoint.mjs · MIT License
//   https://github.com/BroadEyeSolutions/power-law-signals
//
// The server half of a lead form, written as plain fetch-API code so it runs as a Cloudflare Pages Function,
// a Worker, or in Node 20+ (see functions/lead.js for the Cloudflare wiring).
//
// Order of work, on purpose:
//   1. validate the submission, and drop bots quietly (honeypot)
//   2. score the answers with the same rules file the page uses (src/signal-rules.json)
//   3. SAVE THE SUBMISSION to the submission store (a Google Sheet or a web-connected database) and wait for the save.
//      If the save fails, the visitor sees an error and can send again.
//   4. FORWARD every saved lead to the CRM, on one path. If the CRM is down, the store still has the lead, and the
//      weekly tie-out of the store against the CRM shows the gap (docs/08-qa-checklist.md)
//   5. only when the answers clear the line: send the server-side conversion (Meta Conversions API), with the lead's event id,
//      so it deduplicates against the browser pixel's event
//   6. answer the page with { ok, lead_id, codes, qualified, value, currency }
//
// The ad platform never receives the answers or the codes. It hears that a qualified conversion happened, and nothing more.

import signal from '../src/signal.js';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Social apps open links in their own built-in browser and name themselves in the user agent. That's a hint about
// where the click happened when the tracking parameters are missing. Hints only: the strings change, so check them
// against your own leads now and then. Raw user agent is kept as well.
const IN_APP = [
  ['instagram', /Instagram/i],
  ['messenger', /FBAN\/Messenger|MessengerForiOS|\bOrca-Android/i],
  ['facebook', /FBAN|FBAV|FB_IAB|FBIOS/i],
  ['linkedin', /LinkedInApp/i],
  ['tiktok', /musical_ly|Bytedance|TikTok/i],
  ['snapchat', /Snapchat/i],
  ['pinterest', /Pinterest/i]
];
export function inAppBrowser(ua) {
  for (const [name, re] of IN_APP) if (re.test(ua || '')) return name;
  return '';
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });
}

async function readBody(request) {
  const type = request.headers.get('content-type') || '';
  if (type.includes('application/json')) return await request.json();
  const fd = await request.formData();
  const out = {};
  for (const [k, v] of fd.entries()) if (typeof v === 'string') out[k] = v;
  return out;
}

const clip = (v, n = 300) => String(v ?? '').trim().slice(0, n);
// The page without its query string, for anything sent to an ad platform. The full capture URL stays on the lead.
export function pageOnly(href) { try { const u = new URL(href); return u.origin + u.pathname; } catch { return ''; } }

export function createLeadHandler({ rules, save, forward = [], send = [], fieldPrefix = 'pls_', honeypot = 'company_website', now = () => Date.now() }) {
  if (!rules || !rules.questions) throw new Error('createLeadHandler: rules are required');
  if (typeof save !== 'function') throw new Error('createLeadHandler: save is required');

  return async function handleLead(request, ctx = {}) {
    if (request.method !== 'POST') return json({ ok: false, error: 'method' }, 405);
    let body;
    try { body = await readBody(request); } catch { return json({ ok: false, error: 'body' }, 400); }

    // A filled honeypot is a bot. Answer like a success so it moves on, and save nothing.
    if (clip(body[honeypot])) return json({ ok: true, lead_id: null, codes: {}, qualified: false, value: null, currency: null });

    const email = clip(body.email, 254).toLowerCase();
    if (!EMAIL.test(email)) return json({ ok: false, error: 'email' }, 400);

    const leadId = clip(body[fieldPrefix + 'event_id'], 64) || crypto.randomUUID();
    const answers = {};
    for (const q of Object.keys(rules.questions)) answers[q] = clip(body[q], 80);
    const scored = signal.evaluate(rules, answers);

    const tracking = {};
    for (const [k, v] of Object.entries(body)) if (k.startsWith(fieldPrefix)) tracking[k.slice(fieldPrefix.length)] = clip(v);

    const value = rules.value && rules.value.qualified_conversion != null ? Number(rules.value.qualified_conversion) : null;
    const lead = {
      lead_id: leadId,
      received_at: new Date(now()).toISOString(),
      email,
      phone: clip(body.phone, 40),
      first_name: clip(body.first_name, 80),
      last_name: clip(body.last_name, 80),
      company: clip(body.company, 160),
      answers,
      // Each question's SAID (self-assessment ID) from the rules file, beside its answer and code. A question asked
      // differently gets a new SAID, and maps/MAP_SAID.csv translates every SAID into the field it fills.
      said: Object.fromEntries(Object.keys(rules.questions).map((q) => [q, rules.questions[q].said || null])),
      codes: scored.codes,
      qualified: scored.qualified,
      unknown_answers: scored.unknown,
      // The page the form was sent from. Every web and chat submission carries one, so a lead without it didn't come
      // from the site: that absence is what lets PRO set its Capture Group to Web or Non-Web.
      // The capture URL keeps the page's allow-listed tracking parameters: on the page an ad sent the visitor to,
      // they're there even when the visitor opted out of tracking, and PRO reads them (analysis/resolve_sources.py).
      capture_url: clip(body[fieldPrefix + 'form_page'], 600),
      form_id: clip(body[fieldPrefix + 'form_id'], 40),
      capture_method: clip(body[fieldPrefix + 'capture_method'], 40) || 'web_form',
      brand: clip(body[fieldPrefix + 'brand'], 40),
      consent: clip(body.consent, 10) === 'yes',
      consent_text: clip(body.consent_text, 600),
      consent_at: clip(body.consent, 10) === 'yes' ? new Date(now()).toISOString() : null,
      // 'opted_out' when the visitor opted out of tracking (capture.js, PLS_CONFIG.optedOut). Nothing about the lead
      // goes to the ad platforms then. It's still saved, and still attributed in your own reports.
      tracking_choice: clip(body[fieldPrefix + 'tracking'], 20) || 'allowed',
      tracking,
      client: {
        ip_address: request.headers.get('cf-connecting-ip') || (request.headers.get('x-forwarded-for') || '').split(',')[0].trim(),
        user_agent: request.headers.get('user-agent') || '',
        in_app_browser: inAppBrowser(request.headers.get('user-agent') || ''),
        country: request.headers.get('cf-ipcountry') || ''
      }
    };

    try {
      await save(lead);
    } catch {
      return json({ ok: false, error: 'save' }, 502);
    }

    // Every saved lead goes on to the CRM. The submission is already in the store, so a failed forward loses nothing.
    for (const f of forward) {
      const p = Promise.resolve().then(() => f(lead)).catch(() => { /* the store has it; the tie-out shows the gap */ });
      if (ctx.waitUntil) ctx.waitUntil(p); else await p;
    }

    if (lead.qualified && send.length && lead.tracking_choice !== 'opted_out') {
      for (const s of send) {
        const p = Promise.resolve().then(() => s(lead)).catch(() => { /* the record is saved; a failed send is logged by the sender */ });
        if (ctx.waitUntil) ctx.waitUntil(p); else await p;
      }
    }

    return json({
      ok: true,
      lead_id: leadId,
      codes: scored.codes,
      qualified: scored.qualified,
      value: lead.qualified ? value : null,
      currency: lead.qualified && value != null ? (rules.value.currency || 'USD') : null
    });
  };
}

// ---------- savers ----------

// POST the lead as JSON to a webhook you own. As the save: the submission store (a Google Apps Script web app writing
// to a sheet, or a web-connected database or form system). As a forward: your CRM's intake endpoint.
// The webhook must answer 2xx only once the row is written.
export function webhookSave({ url, secret, fetchImpl = fetch }) {
  if (!url) throw new Error('webhookSave: url is required');
  return async (lead) => {
    const r = await fetchImpl(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json', ...(secret ? { 'x-pls-secret': secret } : {}) },
      body: JSON.stringify(lead)
    });
    if (!r.ok) throw new Error('save failed: ' + r.status);
  };
}

// ---------- senders ----------

async function sha256(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

// Meta wants the phone as digits with the country code. Ten digits are read as a US number.
export function normalizePhone(p, defaultCountry = '1') {
  const digits = String(p || '').replace(/\D/g, '');
  if (!digits) return '';
  return digits.length === 10 ? defaultCountry + digits : digits;
}

// Meta Conversions API: one "Lead" event per qualified conversion, deduplicated against the browser pixel's Lead event by
// event_id (the pixel must send eventID = the same lead id) and event_name. Set apiVersion to the current Graph API
// version from Meta's documentation. Use testEventCode while you check events in Events Manager.
export function metaConversions({ pixelId, accessToken, apiVersion, testEventCode, eventName = 'Lead', value = null, currency = 'USD', fetchImpl = fetch, log = () => {} }) {
  if (!pixelId || !accessToken || !apiVersion) throw new Error('metaConversions: pixelId, accessToken and apiVersion are required');
  return async (lead) => {
    const t = lead.tracking || {};
    const userData = { em: [await sha256(lead.email)] };
    const phone = normalizePhone(lead.phone);
    if (phone) userData.ph = [await sha256(phone)];
    if (lead.client && lead.client.ip_address) userData.client_ip_address = lead.client.ip_address;
    if (lead.client && lead.client.user_agent) userData.client_user_agent = lead.client.user_agent;
    if (t.fbp) userData.fbp = t.fbp;
    const clickTime = Date.parse(t.arrived_at || lead.received_at) || Date.now();
    if (t.fbc) userData.fbc = t.fbc;
    else if (t.fbclid) userData.fbc = `fb.1.${clickTime}.${t.fbclid}`;

    const event = {
      event_name: eventName,
      event_time: Math.floor(Date.parse(lead.received_at) / 1000),
      event_id: lead.lead_id,
      action_source: 'website',
      user_data: userData
    };
    if (t.form_page) event.event_source_url = pageOnly(t.form_page);   // the page address without its query string
    if (value != null) event.custom_data = { value: Number(value), currency };
    // The token goes in the request body, never in the address, so it stays out of any log that records URLs.
    const body = { data: [event], access_token: accessToken };
    if (testEventCode) body.test_event_code = testEventCode;

    const url = `https://graph.facebook.com/${apiVersion}/${encodeURIComponent(pixelId)}/events`;
    const r = await fetchImpl(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) {
      log('meta conversions api ' + r.status);
      throw new Error('meta ' + r.status);
    }
  };
}

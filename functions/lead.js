// Broad Eye Solutions · Signals and Attribution Blueprint · functions/lead.js · MIT License
// Cloudflare Pages Function: POST /lead. Copy this file and the server/ and src/ folders into your Pages project, and keep
// src/signal-rules.json out of the site's public output folder, so your line is never served.
//
// Settings (Pages project → Settings → Variables and secrets):
//   SAVE_WEBHOOK         the submission store, where every submission is saved first (your sheet's Apps Script web app,
//                        or a web-connected database). Required.
//   SAVE_SECRET          shared secret the webhook checks (encrypted)
//   CRM_WEBHOOK          optional: your CRM's intake, where every saved lead is forwarded. Leave it out when the CRM
//                        reads the leads from the store instead. One path into the CRM, never both
//   CRM_SECRET           shared secret for the CRM intake (encrypted)
//   META_PIXEL_ID        optional: turns on the server-side Lead for qualified conversions
//   META_ACCESS_TOKEN    Conversions API token (encrypted)
//   META_API_VERSION     the current Graph API version, for example from Meta's Conversions API docs
//   META_TEST_EVENT_CODE optional, while testing in Events Manager

import rules from '../src/signal-rules.json';
import { createLeadHandler, webhookSave, metaConversions } from '../server/lead-endpoint.mjs';

export async function onRequestPost(context) {
  const { env } = context;
  const send = [];
  if (env.META_PIXEL_ID && env.META_ACCESS_TOKEN && env.META_API_VERSION) {
    send.push(metaConversions({
      pixelId: env.META_PIXEL_ID,
      accessToken: env.META_ACCESS_TOKEN,
      apiVersion: env.META_API_VERSION,
      testEventCode: env.META_TEST_EVENT_CODE,
      value: rules.value ? rules.value.qualified_conversion : null,
      currency: rules.value ? rules.value.currency : 'USD',
      log: (m) => console.log(m)
    }));
  }
  const forward = env.CRM_WEBHOOK ? [webhookSave({ url: env.CRM_WEBHOOK, secret: env.CRM_SECRET })] : [];
  const handle = createLeadHandler({ rules, save: webhookSave({ url: env.SAVE_WEBHOOK, secret: env.SAVE_SECRET }), forward, send });
  return handle(context.request, { waitUntil: (p) => context.waitUntil(p) });
}

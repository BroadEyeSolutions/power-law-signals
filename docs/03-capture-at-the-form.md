# 3 · Capture at the form

The form is where an anonymous click becomes a lead. Everything the visit carried has to land on the lead record here, with the form's own ID, before the page moves on.

## Every form gets an ID

Each form, instant form, tracking number and partner feed has a row in the form map (`maps/MAP_FORM.csv`) and an ID that's never reused.

| Field | What it's for |
|---|---|
| `form_id` | The web form's ID, the WFID, for example `WF-0007`. On the page as `data-pls-form-id="WF-0007"` |
| `brand` | The brand the form belongs to, hard-coded. On the page as `data-pls-brand="EX"` |
| `capture_method` | Hard-coded on the form: `web_form` here, `chat` on the chat, `api`, `phone_call` and so on for the other doors ([section 1](01-the-chain.md)) |
| `built_for_source`, `built_for_medium`, `built_for_category` | The traffic the form was built to receive. A form that only runs in Meta ads says `meta`. PRO uses this when a lead arrives with its tags missing ([section 6](06-raw-source-and-pro-source.md)) |
| `offer`, `owner`, `status`, `created` | What it offers, who owns it, whether it's live |

A new form gets its row before it goes live. A form whose purpose changes gets a new ID, so old leads keep the meaning they arrived with.

## The hidden fields

`src/capture.js` keeps where the visitor came from and writes it into the form at submit, as hidden fields with the `pls_` prefix:

| Field | What it holds |
|---|---|
| `pls_utm_source`, `pls_utm_medium`, `pls_utm_campaign`, `pls_utm_term`, `pls_utm_content` | The names, in the traditional fields, from the arrival that started this visit |
| `pls_utm_campaignid`, `pls_utm_adgroupid`, `pls_utm_adid` | The platform's own IDs for the campaign, the ad set or ad group, and the ad |
| `pls_placement`, `pls_network`, `pls_device`, `pls_matchtype` | Platform detail, where it exists |
| `pls_gclid`, `pls_gbraid`, `pls_wbraid`, `pls_fbclid`, `pls_msclkid`, `pls_ttclid`, `pls_li_fat_id` | Click IDs |
| `pls_landing_page`, `pls_referral_url`, `pls_arrived_at` | Where the visit began (the landing page without its query string, and the full referral URL) |
| `pls_first_utm_source`, `pls_first_utm_medium`, `pls_first_utm_campaign`, `pls_first_landing_page`, `pls_first_referral_url`, `pls_first_seen_at` | The first arrival this browser recorded |
| `pls_form_page`, `pls_form_id`, `pls_capture_method`, `pls_brand` | The capture URL (the page the lead was sent from, with that page's own tracking parameters), the form, the capture method and the brand |
| `pls_session_id`, `pls_event_id` | The visit, and this submission. The event ID becomes the lead ID |
| `pls_fbp`, `pls_fbc` | Meta's browser cookies, if its pixel is on the page |
| `pls_tracking` | `allowed` or `opted_out`, from `PLS_CONFIG.optedOut`. The endpoint stores it as `tracking_choice`, and an opted-out lead sends nothing to the ad platforms |

Store them on the lead exactly as they arrive. Resolution happens later, beside them ([section 6](06-raw-source-and-pro-source.md)).

**The capture URL is required on every web and chat lead.** The endpoint stores the form page as `capture_url`. Once every web submission carries one, a lead without it didn't come from the website, and PRO's Capture Group can split Web from Non-Web ([section 6](06-raw-source-and-pro-source.md)). **The must-haves.** A few fields make a web lead provably a web lead and carry most of its attribution: the capture URL, the full referral URL, the IP address, the user agent and the click IDs, with the WFID beside them. A lead missing all of them came in some other way. Two of them, the capture URL and the user agent, carry attribution on their own. After the must-haves come the traditional UTM fields and the platform's IDs, and then the extras worth keeping. `templates/capture_fields.csv` is the full list, each field marked must-have, standard, recommended or optional, with where it comes from.

**Opted out of tracking.** When your consent tool says a visitor opted out, set `PLS_CONFIG.optedOut = true` for them before `capture.js` loads. Nothing is kept from page to page, and the submission is marked so the server sends nothing about that lead to the ad platforms. The form still writes the capture URL and the tags of the page it's on, because they're part of what the visitor submits, under the consent checkbox. On the page an ad sent them to, that's the ad's tags, so the lead is still attributed in your own reports ([section 6](06-raw-source-and-pro-source.md)).

**The visit keeps its tags.** A visitor who lands on a blog post from an ad and fills in the form three pages later still carries the ad's tags. A new tagged arrival replaces them. Only the parameters in the list are read, so a name or email that ends up in an address is never stored.

## Save first, then everything else

`src/submit.js` and `server/lead-endpoint.mjs` send a lead in this order:

1. The page creates the event ID and fills the hidden fields.
2. The form posts to your own endpoint, which scores the answers ([section 4](04-the-signal.md)), so the record is saved with its codes, then saves the submission to the **submission store** and **waits for the save** before it answers.
3. If the save failed, the visitor sees an error and can send again. Nothing else fires.
4. The endpoint forwards the lead to the CRM. If the CRM is down, the store still has it.
5. When the answers clear the line, the endpoint sends the server-side conversion ([section 5](05-tell-the-platforms.md)).
6. The page moves on to the thank-you page the server's answer picked: one for leads that clear the line (`/thank-you/next-steps/` in the example), one for the rest (`/thank-you/`). The pages are for the visitor, so their addresses are neutral and carry nothing.
7. That page pushes the events to the tag manager, once, for the lead the form just saved. A reload or a direct visit pushes nothing. The tag manager fires on the events, never on the page address.

The order matters. A save fired from the browser as the page is leaving races the redirect, and when the redirect wins, the lead is never saved. It happens on slow phones and busy networks, so the leads it loses aren't random. The events wait for the next page for the same reason: a tag fired as a page unloads can lose that race too.

**The submission store.** A Google Sheet, or a web-connected database or form system, that keeps every web submission exactly as it arrived, with its event ID, form ID, capture URL, tracking fields, answers, codes and tracking choice. Nothing edits it and nothing works leads from it. It's there so no lead is lost when the CRM connection fails, and so the count of distinct web submissions can be checked against the leads in the CRM and the conversions each platform logged ([section 1](01-the-chain.md)).

**One path into the CRM.** The CRM gets each lead once: forwarded by the endpoint (`CRM_WEBHOOK` in `functions/lead.js`), or read from the store by one integration. Two systems that each create the lead (a workflow tool and a direct integration, say) create duplicates, or each fails on its own.

## Multi-step forms

Two orders work. Either way, one event ID runs from the first step to the last, and the lead is created once.

- **Contact first.** Step one creates the lead. Step two updates the same lead, found by its lead ID. Step two isn't a new lead. Count it as the next step of the same lead (`form_step_completed`, step 2), never as a second lead.
- **Answers first** (the sorting questions before the contact details). Step one posts its answers with the event ID, the form ID and the capture URL, and nothing that identifies the person. The record becomes a lead at the step that adds the contact details and the consent, and only then do `lead_submitted` and `qualified_conversion` fire. A record that stops before that step never goes to sales, and its answers show which bands the contact step lost.
- Carry the lead ID between steps, never the name, email or phone in the address. An address with personal details ends up in browser history, server logs and every analytics tool on the next page. Keeping every step on one page avoids the problem, and the reload that drops the tags.
- Fire `form_step_completed` with the `form_id` and the `step` at every step, to product analytics only ([section 9](09-tracking-plan.md)). The ad platforms never see the steps.
- Give each version of a form its own form ID, so a test between a one-step and a two-step version reads by conversion point.

## Consent

If sales will call or text, the form asks with a checkbox, and the lead record keeps the exact wording the visitor saw, the answer and the time. Paragraph text under a button isn't a checkbox. The wording also covers what the form sends with the answers: the page it was sent from and the browser it was sent with. Have counsel approve the wording for your business.

## The browser

Store the raw user agent on the lead. Social apps open links in their own built-in browser and name themselves in it, so the endpoint also records an `in_app_browser` hint (`instagram`, `facebook`, `messenger`, `linkedin`, `tiktok`). When the tags are missing, that hint helps resolve the source and medium. The strings change, so treat it as a hint and check it against your own leads now and then.

## Product analytics

Analytics shows the path. The CRM keeps the record. Join them with the lead ID:

```js
// after the endpoint confirms the save
posthog.identify(res.lead_id);
posthog.capture('lead_submitted', { form_id: 'WF-0007', capture_method: 'web_form', qualified: res.qualified });
```

- Mask the form in session replay (PostHog: `ph-no-capture` on the form, `maskAllInputs: true`), so no answers or contact details are recorded.
- In GA4, send `generate_lead` from the tag manager on `lead_submitted`, and mark it as a key event.

## Privacy, in short

- No personal details or answers in any address.
- Ad pixels and the server-side conversion get the page address without its query string ([section 5](05-tell-the-platforms.md)).
- The capture URL on the lead keeps only the allow-listed tracking parameters, never anything else in the address.
- Email and phone are normalized and hashed before they go to an ad platform.
- A honeypot field stops most bots without a puzzle for people.

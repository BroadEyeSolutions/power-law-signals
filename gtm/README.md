# Google Tag Manager recipe

The thank-you page the server picked pushes two events to the data layer (`src/submit.js`, `PLS.thankYou()`), once per saved lead. The tag manager routes them. The rule for which leads qualify lives in `src/signal-rules.json` and the server decides it, so nothing in the container decides who qualifies. Build every trigger on the events, never on a page address: on financial-services pixels Meta's Core Setup can strip everything after the domain, so a trigger or custom conversion on the address may never fire on Meta's side ([section 5](../docs/05-tell-the-platforms.md)).

## Variables

| Name | Type | Setting |
|---|---|---|
| `DLV - event_id` | Data Layer Variable | `event_id` |
| `DLV - lead_id` | Data Layer Variable | `lead_id` |
| `DLV - value` | Data Layer Variable | `value` |
| `DLV - currency` | Data Layer Variable | `currency` |

## Triggers

| Name | Type | Fires on |
|---|---|---|
| `CE - lead_submitted` | Custom Event | Event name `lead_submitted` |
| `CE - qualified_conversion` | Custom Event | Event name `qualified_conversion` |

## Tags

| Tag | Type | Trigger | Settings |
|---|---|---|---|
| Meta Pixel - Base | Meta Pixel template, or Custom HTML | All Pages (Initialization) | Pixel ID. Load it once, here only |
| Meta - Inquiry (every lead) | Custom HTML | `CE - lead_submitted` | `fbq('trackCustom', 'Inquiry', {}, {eventID: {{DLV - event_id}}});` A custom event, so no ad set can optimize for it by default. Never set it as an ad set's goal |
| Meta - Lead (qualified) | Custom HTML | `CE - qualified_conversion` | `fbq('track', 'Lead', {value: {{DLV - value}}, currency: {{DLV - currency}}}, {eventID: {{DLV - event_id}}});` (drop value and currency if you don't send one) |
| Meta - Customer survey (optional) | Custom HTML | Custom Event `customer_survey_completed`, pushed by the survey page | `fbq('trackCustom', 'CustomerSurveyCompleted');` For audiences only. Never an ad set's goal, and never `Lead` |
| Google Ads - Conversion Linker | Conversion Linker | All Pages | Defaults |
| Google Ads - Qualified conversion | Google Ads Conversion Tracking | `CE - qualified_conversion` | The qualified conversion action's ID and label. Transaction ID `{{DLV - event_id}}`. Value and currency from the data layer. Enhanced conversions on |
| Google Ads - Every lead (observe) | Google Ads Conversion Tracking | `CE - lead_submitted` | The every-lead action's ID and label. Transaction ID `{{DLV - event_id}}`. Set as Secondary in Google Ads |
| GA4 - generate_lead | GA4 Event | `CE - lead_submitted` | Event `generate_lead`, parameters `lead_id`, `form_id`. Mark as a key event in GA4 |

Meta hears about every lead, as a custom `Inquiry`, and bids on one: the qualified `Lead`. That's the starve. Every lead is counted on Meta's side too, so its totals tie out against yours.

The server sends the same qualified `Lead` through the Conversions API with the same event ID, and Meta keeps one. `Inquiry` goes from the browser only.

## In Google Ads

| Action | Goal setting | Count |
|---|---|---|
| Qualified conversion | Primary, in the account-default goal | One |
| Every lead | Secondary (observe only) | One |

Demote any imported analytics form-submit action to secondary.

## Test in Preview

| Submit with | `lead_submitted` | `qualified_conversion` | Meta Inquiry | Meta Lead | Google qualified |
|---|---|---|---|---|---|
| 30k_to_100k, 1_to_3 | fires | fires | fires once | fires once | fires once |
| over_100k, under_1 | fires | no | fires once | no | no |
| 10k_to_30k, over_5 | fires | no | fires once | no | no |

Reload each thank-you page and visit it directly: nothing fires. Then check Meta Events Manager's Test Events (set `META_TEST_EVENT_CODE` on the endpoint) for one deduplicated `Lead`, and Google Tag Assistant for the conversion with its transaction ID. Publish only when every row matches.

## Codes in the data layer (opt-in)

The server decides who qualifies, from `src/signal-rules.json`, and the container only routes the events. A team that wants the codes in analytics can turn them on with `PLS.wire(form, { pushCodes: true })`, which pushes `code_monthly_sales` and so on with both events. Never build a trigger on them: `qualified_conversion` is the only qualified trigger. Once the codes are in the data layer, every tag in the container can read them, so keep the container's tags to the ones you've checked.

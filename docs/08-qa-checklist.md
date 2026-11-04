# 8 · Check it before it spends, and every week after

## Before launch

- [ ] **One test click per campaign.** Every parameter from [section 2](02-tag-every-link.md) arrives filled in on the landing page.
- [ ] **The visit keeps its tags.** Land tagged, move two pages without tags, send the form: the lead carries the first page's tags.
- [ ] **Every answer combination.** Send the form once per band of each question. Each one gets the right code, and only the combinations over the line come back `qualified: true`.

  | monthly_sales | years_in_business | qualified |
  |---|---|---|
  | under_10k | over_5 | no |
  | 10k_to_30k | over_5 | no |
  | 30k_to_100k | under_1 | no |
  | 30k_to_100k | 1_to_3 | yes |
  | over_100k | 3_to_5 | yes |

- [ ] **One record per submission,** with the form ID, capture method, event ID and every tracking field.
- [ ] **The store, then the CRM.** Every test submission lands in the submission store, and once in the CRM. Point the CRM forward at a broken address and send one: the visitor sees a success, and the store has it.
- [ ] **A failed save shows an error** (point the endpoint at a broken webhook and try it) and fires nothing.
- [ ] **Call tracking.** Every tracking number has a row in the form map, and a test call shows in the call tracking system with its number and its length.
- [ ] **Tag manager preview:** `lead_submitted` on every submission, `qualified_conversion` only on qualified ones, and each ad platform tag fires once.
- [ ] **Meta Events Manager, Test Events:** one `Lead` per qualified submission, received from the browser and the server, shown as deduplicated.
- [ ] **Google Ads:** the qualified-conversion action is primary, in the goal, counted One. The every-lead action is secondary. Tag Assistant shows the transaction ID.
- [ ] **No answers or personal details** in any address, data layer event or platform call, and no codes in any platform call.
- [ ] **Consent** is a checkbox, and the record stores its wording and time.

## The breaks that show up most

These come up again and again in audits of real lead funnels:

| The break | What it does | The fix |
|---|---|---|
| Qualified and unqualified leads fire the same conversion action, with different values | The bidding counts every lead, including the zero-value ones | Separate actions. Only the qualified one is primary |
| An imported analytics "form submit", counted Every, is what the bidding optimizes toward | The bidding optimizes toward the biggest, noisiest number | Demote it to secondary. Leads count One |
| The conversion fires when the thank-you page loads, or on its address | Reloads and direct visits count as leads, and on a Core Setup pixel Meta may never see the address | Fire on the server's answer (`qualified_conversion`), deduplicate with the event ID |
| Two copies of the same pixel on one page | Every event fires twice | One pixel, loaded once, through the tag manager |
| Event code pasted twice into a page | The funnel's steps double-count | One tracking spec, the same on every page |
| The CRM save fires from the browser as the page redirects | Leads go missing, mostly on slow phones | Save on the server first, and wait for it |
| Two systems each create the lead | Duplicates, or one path fails without anyone noticing | One path creates the record |
| Leads go only to the CRM | When the connection fails, the leads are gone, and nobody can say how many | A submission store first, tied out against the CRM every week |
| Calls are never logged as leads | Inbound calls look weaker than they are, and their source never gets the credit | Tie the longer calls to the call leads every week |
| The rule matches the label text ("1 – 3 Years") | A changed dash quietly stops every lead from qualifying | Match option values, log unknown answers |
| Name, email and phone passed to step two in the address | Personal details in logs, history and every tag on the next page | Pass the lead ID only |
| Every landing page tracks differently | Reports can't compare pages, and some leads miss fields | One spec, one script, on every page |
| Consent as paragraph text | No record that the visitor agreed | A checkbox, with the wording stored |

## Every week: tie the counts out

Export last week from each system: each platform's daily spend export, product analytics' visits by source, the submission store, the CRM and the call tracking system. Count each tie-out in [section 1](01-the-chain.md) for the week, Saturday to Friday, and set its ratio beside the weeks before.

Mark a week only when its ratio moves well past its usual level, by more than its weekly noise and by at least three records, so one stray conversion on a small count doesn't raise an alarm. The breaks that show up most look like this:

| Tie-out | Usual | The week it broke | What broke |
|---|---|---|---|
| Meta conversions logged to qualified submissions | 1.02 | 0.00 | A site update removed the Meta tags for four days |
| CRM web leads to web submissions in the store | 0.98 | 0.57 | The CRM connection failed for three days |
| Google visits to clicks | 0.90 | 0.34 | A redirect on the search landing page stripped the tags |
| Call leads to calls of 60 seconds or more | 0.70 | 0.19 | Calls went on, and nobody created the call leads |

`templates/tie_outs.csv` lists what a gap usually means for each one. ABPRO_ runs these counts every week and flags the weeks that moved.

## Every week: field coverage by source

For each PRO Source and Medium, the share of last week's leads with each tracking field filled in:

| Field | Healthy |
|---|---|
| `utm_source`, `utm_medium`, `utm_campaign` | Near 100% on ad traffic |
| `utm_adid` (the ad ID) and `utm_campaignid` | Near 100% on ad traffic |
| Click ID | Near 100% on search ads with auto-tagging |
| `form_id`, `capture_method`, `brand`, `event_id` | 100% everywhere |
| `user_agent` | 100% on every web and chat lead |
| `capture_url` | 100% on every web form and chat, with the page's tracking parameters. A gap turns web leads into Non-Web |
| The signal questions | 100% on every form that asks them |

A field that drops on one channel means a template broke, an app is stripping the address, or a page went live without the script. The `_basis` columns show the same thing from the other side: more of a channel resolving from the form default or the in-app browser means its tags are going missing.

## Every week: the maps

Run `analysis/update_maps.py` on last week's raw leads. Every value it lists is a source, medium, campaign, form or capture method nobody has mapped yet: review it, fill in its value and mark it verified. Then check:

| Check | Healthy |
|---|---|
| Leads whose Capture Group basis is `capture_method_no_url` | Zero. Each one is a web form or chat that didn't write its capture URL |
| Leads with `brand_unmapped` | Zero. A new site or brand code gets its row in `MAP_BRAND.csv` |
| Leads with any `*_unmapped` basis | Falling, week on week |
| Share of leads resolved through verified map rows, per map | Agree a floor and hold it |
| Forms in the leads with no row in `MAP_FORM.csv` (status `unregistered`) | Zero. A form gets its row before it goes live |

Fix what the checks find in the maps or at the form. Never edit the CRM to make a check pass ([section 10](10-maps-keys-and-audits.md)).

# 1 · The chain: one ID across every system

A lead can only be judged by what it became if its record in each system, from the ad platform to the revenue, can be tied to the next. Break one link and the revenue can't be traced back to the ad, the form or the answer that brought it in.

The systems don't share an ID, and they won't. "CRM" below means whatever holds the records: one system, such as HubSpot on its own, or several linked together, such as Pardot for marketing, Salesforce for sales and a third system for customers. The chain rests on the IDs each system keeps, not on one vendor's objects. The data starts with third parties, in systems that aren't yours: the ad platforms have their campaign, ad and click IDs, product analytics its sessions, the submission store its event IDs, call tracking its call IDs, the CRM its record IDs and billing its account IDs. PRO assigns one ID of its own, the **lead ID**, and ties each system's IDs to it. Where two systems hold a record of the same lead, PRO joins them on an ID they share. Where they don't, the date does: each system's counts, by day, source and campaign, are laid side by side.

## Every stage, its system and its own IDs

| Stage | System | The record | Its own IDs | How PRO ties it in |
|---|---|---|---|---|
| Third party | Not yours: the ad platforms and other outside sources, wherever they keep it | Impressions, clicks, spend, and the conversions they logged, by day, campaign, ad set and ad, read from their exports | Campaign, ad set or ad group, and ad IDs. A click ID for each click (`gclid`, `fbclid` and others) | By date, source and campaign. The tags carry the campaign and ad IDs and the click ID onto the lead |
| Visit | Product analytics (PostHog or GA4), on your site | The session, its pages and its events | Session ID, the analytics user ID | By date, source and campaign. The session ID is written on the submission, and `identify(lead_id)` ties the session to the lead |
| Conversion point | The submission store for forms, call tracking for calls | The submission. The call | Event ID. Call ID and the tracking number | The submission's event ID becomes the lead ID. Calls are counted by date against the leads sales created from them |
| CRM: Contacts | The CRM | The contact: a prospect until it raises its hand, a lead from then on | The CRM's own contact ID | The lead ID is saved on the record, beside the CRM's ID |
| CRM: Opportunity | The CRM, owned by sales | Opened when the rep converts the lead, at the SQL | Opportunity ID | The lead ID is handed on from the contact, and the opportunity is linked to it inside the CRM |
| Decision | Underwriting, approval, onboarding, where the business has them | The decision and its reason, on the opportunity or in underwriting's own system | Application or decision ID | The ID it was sent with, or the email and date, kept in the ID map |
| CRM: Accounts | The CRM, billing or the core system | The customer | Account ID | The lead ID is handed on, or the ID map ties the account ID to it |
| CRM: Company | The CRM | The business: one company across its contacts, opportunities and accounts | Company ID | Each contact, opportunity and account is linked to it |
| Revenue | Statements, invoices | Each period's revenue | Account ID and period | By account ID and month |

PRO's **ID map** is a keyed table like the maps in [section 10](10-maps-keys-and-audits.md): one row per lead ID, each system's own ID beside it, and how each match was made. The lead ID is the event ID of the submission that created the lead. ABPRO_ calls it the Performance ID.

## The rules

1. **One lead ID per record, created where it enters.** The web form's event ID becomes the lead ID. A record from a call, a chat, a partner or an import gets an ID made the same way every time (a stable hash of its email and date works), so it never changes on a rebuild, and a prospect keeps its ID when it becomes a lead.
2. **Carry the ID into every system that will take it.** Save it on the CRM record, send it with the application to underwriting, and write it on the account where billing has a field for it. Each system that holds it is one join PRO doesn't have to make. Where a system won't take it, PRO matches the records and keeps the match, and how it was made, in the ID map. A link nobody records leaves the revenue orphaned.
3. **Keep the lead and the opportunity separate.** The contact's funnel runs from the prospect to the SQL and answers the questions before the commitment: did they raise a hand, meet the criteria, get reached and get qualified. At the SQL the rep converts the lead to an opportunity, and the opportunity is sales' record from there through to funded or lost. One object holding both works at low volume, then blocks forecasting, win and loss analysis, and repeat business.
4. **A prospect isn't a lead.** A name on a purchased list, a contact who never raised a hand, or a conversion your systems hold before it's accepted as a lead is a prospect. A hand raise makes the lead: a form sent, a call made, a reply, a meeting booked, a request to be contacted. Keep them apart, so a lead count and a lead source each mean one thing.
5. **One email can have many leads.** Give each submission its own ID, and tie it to the lead it created or joined. Joining on email alone can match an account to the wrong submission, and to the wrong source.
6. **Tie every contact, opportunity and account to its company.** A business can send in several people, and win, lose and come back. The company record keeps them on one line, so revenue is counted once per business and a second contact isn't mistaken for a new customer.
7. **Every contact records its conversion point.** It's required, a hard-coded field written by the form or the integration, never typed by a person. A contact without one is a gap to fix.
8. **Every web and chat lead records its capture URL.** Then the leads without one are known to be off the website ([section 6](06-raw-source-and-pro-source.md)).
9. **Every web submission is kept twice.** The submission store keeps it exactly as it arrived, and the CRM gets the lead on one path ([section 3](03-capture-at-the-form.md)).

## Every system keeps its own count

Each system in the chain counts the same people at its own step, so each count can be checked against the next one's. No two match exactly, but each pair keeps a steady ratio. A ratio that moves means something broke between the two systems, and checking every week finds it the week it happened, not the quarter after.

**Keep every web submission outside the CRM too.** The endpoint saves each submission to a **submission store** first: a Google Sheet, or a web-connected database or form system. The CRM then gets the lead on one path. If the connection to the CRM fails, no lead is lost, and the gap between the two counts shows it.

| Tie-out | Count | Against | What to expect | A gap usually means |
|---|---|---|---|---|
| Clicks to visits | Each platform's clicks, from its spend export | The visits product analytics counted with that platform's tags | A steady share, a little under all of them | The landing page is down or slow, a redirect strips the tags, or a campaign went live without them |
| Submissions to the platforms | The qualified submissions in the store that a platform should have logged, from visitors who didn't opt out of tracking: for Google, those whose PRO source is Google, and for Meta, all of them (Meta receives every source's qualified conversion) | The conversions that platform logged | Very close to all of them, if not exactly | The tag or the Conversions API stopped sending, or the event fires on a page load or twice |
| Submissions to the CRM | The web submissions in the store | The web leads in the CRM | Close to all of them, short only by the CRM's duplicate and spam rules | The connection failed, a form isn't wired to the CRM, or a rule is catching real leads |
| Calls to call leads | Inbound calls to the tracking numbers that lasted a set time or more, from the call tracking system | The leads sales created from calls | A steady share | Calls answered and never logged as leads, or a number missing from the form map |

`templates/tie_outs.csv` lists the four. Run them every week, and flag the week a ratio moves ([section 8](08-qa-checklist.md)). The submissions-to-CRM ratio is also the funnel's first step on the web track, from conversion to lead.

## The date joins what IDs can't

The ad platform never sees a lead's ID, and the CRM never sees a click's. Their records can't be joined one to one, and they don't need to be. Count each system's records by date, and by PRO source and campaign where it has them, and lay the counts side by side. The tie-outs above are those counts, read as ratios. ABPRO_ builds the full view from each system's export, from the impression through the funnel, and runs the tie-outs on it every week.

## Conversion points and capture method

The **conversion point** is the door the contact came through, and every contact has one. It has a type, a capture method and an ID of its own. The four types:

| Conversion point | Capture methods under it | Capture Group |
|---|---|---|
| Online | Web Form, Live Chat | Web |
| API / Third Party Direct | Third Party API (an integration delivers it straight into the CRM: an ad platform's own lead form, such as Meta's instant form, or a partner's feed) | Non-Web |
| Manual Entry | Inbound Call, Referral, Manual Entry (a rep keyed it in: an event, a business card, a walk-in) | Non-Web |
| List | List (a list loaded into the CRM: bought, rented, a trade show's scans) | Non-Web |

Each door has its own ID in the form map (`maps/MAP_FORM.csv`). A web form's is its web form ID, the **WFID** (some builds call the hidden field the conversion ID). Two IDs are required on every online conversion: the WFID, and the **SAID** of each self-assessment question the form asks, the sorting question's own ID ([section 4](04-the-signal.md)).

The **capture method** says what kind of door it was, and so how the lead got into the CRM. That's one of the earliest predictors of what a lead is worth, whatever its source, so it's on every lead, hard-coded by the form or the integration, never typed by a person:

| Raw `capture_method` (hard-coded) | PRO Capture Method | PRO Capture Group | What it must carry |
|---|---|---|---|
| `web_form` | Web Form | Web | Form ID, capture URL, session ID, event ID, the tracking fields, user agent and IP |
| `chat` | Live Chat | Web | Capture URL (the page the chat was opened on), the conversation ID |
| `phone_call` | Inbound Call | Non-Web | The tracking number dialled, the call ID |
| `referral` | Referral | Non-Web | The partner or referrer ID |
| `api` | Third Party API | Non-Web | The sender (the platform or the partner) and its own lead ID, plus the form ID for a platform's lead form. An ad platform's own form is online, but it isn't your website |
| `import` | List | Non-Web | The import batch |
| `manual` | Manual Entry | Non-Web | The rep, and why (an event, a business card, a walk-in) |

PRO reads the raw value through the capture map (`maps/MAP_CAPTURE.csv`), so a CRM that already says "Inbound Phone" or "Zapier/API" maps into the same vocabulary without anyone editing a record.

**Capture Group** has two values, Web and Non-Web, and the capture URL decides it, not the label. Every web and chat lead writes the page it was sent from. Once that's true without exception, a lead with no capture URL didn't come from the website, whatever else it says ([section 6](06-raw-source-and-pro-source.md)).

**Brand** is hard-coded the same way. Every form writes the brand it belongs to, so leads from a sub-brand's site, a second brand or a company the business bought can be cut apart from the main brand's before anything else is read.

## A minimal data model

```
id_map         performance_id · crm_record_id · opportunity_id · decision_id · account_id · company_id · matched_by
platform_daily date · source · campaign_id · adset_id · ad_id · impressions · clicks · spend · conversions
               (each ad platform's export)
visits_daily   date · source · campaign_id · visits (product analytics, by the visit's tags)
submissions    event_id · received_at · brand · form_id · capture_url · the tracking fields · answers · qualified ·
               tracking_choice (the submission store: every web submission, saved before the CRM gets it)
calls          call_id · started_at · tracking_number · conversion_point · duration_sec (the call tracking system)
leads          lead_id · received_at · brand · capture_method · form_id · capture_url · email · phone · company
               answers (raw) · codes · qualified · consent · consent_text
               tracking: utm_source · utm_medium · utm_campaign · utm_term · utm_content (the names) ·
               utm_campaignid · utm_adgroupid · utm_adid (the IDs) · click ids · landing_page · referral_url · session_id
               client: ip_address · user_agent · in_app_browser · country
               entered_as (conversion, prospect or lead) · stage (the furthest stage reached) ·
               <stage>_first_at and <stage>_last_at for every
               funnel stage · first_attempt_at · contacted_at · lead_status · lead_track (active or passive) ·
               owner · lost_at · lost_reason · nonqualified_type (permanent or reviewable) · company_id
opportunities  opportunity_id · lead_id · company_id · created_at · stage · amount · decision · decision_reason
accounts       account_id · lead_id · opportunity_id · company_id · started_at
companies      company_id · name · the contacts, opportunities and accounts linked to it
revenue        account_id · period · revenue
```

## The funnel stages

Every record moves through the same named stages, from the point it entered your systems to the revenue its account produces. Name them once, write down what moves a lead into each one, and use the same names in the CRM, the reports and every meeting. The list is in `templates/funnel_stages.csv`.

| Stage | Code | What it means | Set by |
|---|---|---|---|
| Conversion | `conversion` | An online conversion: a form or chat sent on the site, with its event ID, saved in the submission store | The endpoint |
| Prospect | `prospect` | A record in your systems that isn't a lead yet. Where the systems hold conversions as prospects first, every conversion passes through it. Names that never converted enter here too: a bought list, a trade show's scans, contacts sent in through an API, names the team has cultivated. Greyed out where conversions become leads directly | The import, the API, the marketing system or the CRM |
| Lead | `lead` | Someone who has raised a hand, on any track: an online conversion, an inbound call, a referral, a prospect who replied or booked a call. One record and the lead ID. A duplicate or a test is a conversion, never a new lead | The endpoint for web leads, the CRM for every other track |
| MQL, interest signaled | `mql` | The subset of leads that meet the organization's qualifying criteria, whatever track they came in on | The qualifying rules, applied to what the lead told you, on a form or on a call |
| SAL, interest confirmed | `sal` | Sales reached the lead, and the conversation confirmed the interest. Sales accepts it as worth working | The rep, from a logged conversation |
| SQL, sales qualified | `sql` | The rep has qualified it against what the offer needs, the size, the need and the timing, and converts the lead to an opportunity. The contact's funnel ends here | The rep, by converting the lead |
| SQO, sales qualified opportunity | `sqo` | The opportunity reaches a real commitment, such as a signed application or an accepted proposal | Sales, when the commitment arrives |
| RQO, risk qualified opportunity | `rqo` | Underwriting or the risk review approved it. Only business models with underwriting have this stage | Underwriting |
| Closed won | `cw` | Signed, funded, or the first payment received | Sales operations or finance |
| Activation | `activation` | The account is live: the first transaction, the first invoice | The core system |
| Revenue | `revenue` | Each month the account bills, by account ID | Billing |

Every record enters the funnel at a named stage, depending on the track it came in on, and keeps it in `entered_as`:

| Track | Capture method | Enters as |
|---|---|---|
| A form or chat on the website | Web Form, Live Chat | `conversion` |
| A bought list, a trade show's scans, a data feed, names the team cultivated | List, Third Party API, Manual Entry | `prospect` |
| An inbound call, a referral, an ad platform's lead form, a partner or a rep entering someone who asked to be contacted | Inbound Call, Referral, Third Party API, Manual Entry | `lead` |

Then every track is measured on the same steps: the website from conversion to lead (through prospect, where the systems have that step), a list from prospect to lead, and every track from the lead onward. Below the lead the rates are standardized, so a trade show, a bought list and an ad campaign compare on one funnel. A prospect becomes a lead on a hand raise (it replies, books a call or sends a form), and keeps its `entered_as`.

They group into four parts of the business: acquisition (conversion, prospect and lead to MQL), nurture (SAL to SQO), risk (RQO) and revenue (closed won onward).

- **The prospect step is optional.** Many systems turn a conversion straight into a lead. That's fine. Grey the prospect stage out for those records, the way risk is greyed out without underwriting, and read the website from conversion to lead.
- **The risk section is optional.** It belongs to business models with an underwriting or risk review. Without one, grey it out in reports, leave `rqo` out of the stage list, and a lead goes from SQO straight to closed won.
- **The qualified conversion isn't a stage.** It's an advertising signal: the subset of conversions whose answers clear a line, sent to the ad platforms as the one conversion they bid on ([section 5](05-tell-the-platforms.md)). Firing it for fewer than all the conversions points the bidding at more value in the conversion pool instead of more conversions. It never enters the funnel. The MQL is the organization's own bar, a CRM stage any lead can reach from any track. It often takes in every lead that cleared the qualified conversion's line, plus other leads that meet a higher standard the organization sets. An inbound call is never an online conversion, but it's a lead, and it can be an MQL. So the qualified conversions and the MQLs are different counts, and the MQLs include leads the platforms never saw.

## Inside the lead: assign, engage, advance

From the prospect to the SQL, the record lives on the contact, and a status says where it is. The SAL and the SQL are reached by working the lead, so the statuses describe that work. The list is in `templates/lead_statuses.csv`.

Every lead gets the same three moves, whatever status it's in:

- **Assign.** An owner, by rule, the moment it arrives, so no lead waits for someone to notice it.
- **Engage.** The cadence set for its status. Each status has its own: the calls, emails and texts for a new lead aren't the ones for a lead that's already confirmed.
- **Advance.** Confirm the data (the contact details are real) and the audience (the business is one the offer is for), set the next step (a follow-up booked, or the application sent), or convert it.

| Status | What it means | The stage it marks |
|---|---|---|
| New lead | Assigned, not reached yet | `lead`, and `mql` where it meets the criteria |
| Unconfirmed | Being worked, the data and the audience not confirmed yet | `lead` |
| Confirmed | The rep confirmed the data and the audience: a real business the offer is for | `sal` |
| Application sent | The next step is out: the application, the proposal or the demo | `sal`, on the way to `sql` |
| Converted | The rep converted the lead to an opportunity | `sql` |

**Active and passive.** Every status has an active and a passive version, kept in `lead_track`. A lead that stops answering has its hand raise set to off and moves to the passive track with the status it reached, and gets a lighter cadence, mostly email, instead of a rep's calls. A new hand raise moves it back to the active track at the same status.

**Non-qualified is permanent or reviewable.** A passive lead is either still qualified, and worth the nurture, or non-qualified, with a reason from a fixed list. Non-qualified is **permanent** (a business that closed, never a fit) or **reviewable** (too small today, the wrong time), kept in `nonqualified_type`, and a reviewable lead is checked again on a schedule.

If your CRM calls these statuses something else, such as attempting or connected, map its statuses to these the same way the source values are mapped, and keep the CRM's own names as they are. The status says where a lead is now. The stage timestamps say when it got there.

## Two timestamps for every stage

A status field says where a lead is now, and it's overwritten every time the lead moves. So each stage also gets two timestamps of its own:

- **`<stage>_first_at`**: the first time the lead reached the stage. Set once and never changed. Funnel reports count it, cohorts are built on it, and time-to-stage is measured from it.
- **`<stage>_last_at`**: the most recent time the lead reached the stage. Updated every time it gets there again: a lead recycled to nurture that comes back, an application resubmitted after a decline, an account reactivated. The gap between the two shows the recycling.

Rules:

1. **Set them from the event that moved the lead,** by the system wherever possible: the endpoint for web conversions and web leads, the import, the API or the marketing system for prospects, the CRM for leads from every other track, the qualifying rules for MQL, the phone system's logged conversation for SAL, the conversion to an opportunity for SQL, the commitment on the opportunity for SQO, the decision record for RQO, the funding or payment for closed won.
2. **Never edit a first timestamp.** A correction goes in the overrides table ([section 6](06-raw-source-and-pro-source.md)), applied on top at every rebuild.
3. **A stage the lead never passed through stays blank.** A web lead whose systems skip the prospect step has no prospect timestamp, and a lead from an inbound call has no conversion timestamp, because a call is never an online conversion. The funnel report counts every lead from the lead stage on, at every stage up to the furthest one it reached, and a question about MQLs themselves reads `mql_first_at` directly.
4. **Lost keeps what it earned.** A lead that's disqualified or lost keeps every timestamp it reached, and gets `lost_at` and a `lost_reason` from a fixed list.
5. **The bidding reads the same fields.** A qualified lead's later stages, and its value-line result, go back to the ad platforms as later conversions, dated from these fields ([section 5](05-tell-the-platforms.md)), so the platforms' counts can be checked against yours.

Most CRMs record when a record enters a stage, and some overwrite that date when the record comes back. Check which yours does. Either way, keep your own pair of date-time fields per stage, set by a workflow on the stage change: the first written once and never overwritten, the last written every time.

## Contact, inside SAL

`first_attempt_at` and `contacted_at` sit beside the stages: the first call or message, and the first two-way conversation.

`contacted_at` is the first two-way conversation with the person who sent the lead (a connected call or a written reply), not the first attempt. SAL follows when that conversation confirms the interest. Log every attempt from the phone system, with its time and an outcome (connected, no answer, voicemail, wrong number, disconnected, wrong person, asked not to be contacted), and keep `first_attempt_at` beside it. Then contact rate reads the same way every month, by form, source and answer band, and wrong numbers show up as a form problem rather than a sales one. Pick the contact window (seven days, say) once and keep it.

Raw capture is never edited, and no report reads it directly. The PRO fields (Brand, Capture Group, Capture Method, Conversion Point, Class, Category, Source, Medium, Campaign) are resolved beside it from all of each lead's evidence, through the map files, and they're what every report reads. See [6 · Report on PRO, never on raw data](06-raw-source-and-pro-source.md) and [10 · Maps, keys and audits](10-maps-keys-and-audits.md).

## Later results go back to the platforms

When a lead that qualified on the form reaches a later stage, or its account's first full month of revenue lands above the value line, that's a later conversion. With the click ID and the lead ID on the record, it can be sent back to the platform that bought the click. See [5 · Tell the platforms](05-tell-the-platforms.md).

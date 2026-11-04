# 5 · Tell the platforms

Automated bidding on the major algorithmic advertising platforms optimizes toward whatever conversion it's handed. Hand it every form fill and it finds as many form fills as it can, from wherever they come cheapest, which in a power-law book is where the accounts are worth the least. Hand it only the qualified conversion, the subset of conversions whose answers clear a line, and it goes looking for more value in the conversion pool instead of more conversions. Starve it of everything else.

## Two events, one conversion to bid on

| Data layer event | Fires when | Sent to the platforms as | Used for bidding |
|---|---|---|---|
| `lead_submitted` | Every saved lead | A custom `Inquiry` event on Meta, never optimized for. An observation-only conversion on Google | **Never** |
| `qualified_conversion` | The server says the answers cleared the line | The lead conversion, from the browser and from the server, with one event ID | **Yes, the only one** |

Both events carry `event_id`, which is the lead ID. That's what lets the platforms count a browser event and a server event for the same lead once. Neither carries the answers or their codes.

**Visitors who opted out of tracking.** The server sends nothing about their leads to the ad platforms (`tracking_choice = opted_out`, set by `capture.js`). Keep the browser tags off for them too, through your consent tool. Their leads are still saved and attributed in your own reports.

## Meta

**In the browser, through the tag manager:**
- The standard `Lead` event fires on `qualified_conversion` only, with `eventID` set to the event ID.
- `lead_submitted` sends Meta a custom event, `Inquiry` (`fbq('trackCustom', 'Inquiry', {}, {eventID})`), for every lead. Meta's own reports then count every lead beside the qualified ones, and the two counts tie out. It's a custom event, not a standard one such as `Lead`, and no ad set optimizes for it.
- Ad sets optimize for the `Lead` event.
- Page addresses stay clean at the source. No personal details, answers or codes ever go in a URL, so there's nothing in the address for a pixel to pick up ([section 3](03-capture-at-the-form.md)).

**From the server, through the Conversions API** (`server/lead-endpoint.mjs`). This blueprint sends the server-side copy to Meta only. Google gets the browser tag, with the event ID as its transaction ID.
- One `Lead` event per qualified conversion, and nothing else: `Inquiry` goes from the browser only. The Conversions API shares what you choose and no more. Each `Lead` has `event_id` set to the lead ID, hashed email and phone, the visitor's IP and browser, and the `_fbp` and `_fbc` cookies (or an `fbc` built from the `fbclid`).
- Meta deduplicates a pixel event and a server event when the event ID and the event name match, if they arrive within 48 hours of each other. Meta recommends sending both.

**Names:** keep event and conversion names plain ("Lead"). Meta blocks custom conversions that suggest financial status or a health condition, and a conversion named after an answer can read like one.

## Google Ads

| Conversion action | Fires on | Goal setting | Count | Value |
|---|---|---|---|---|
| Qualified conversion | `qualified_conversion` | **Primary**, in the account-default goal (or the campaign's own goal) | One | What a qualified conversion is worth to you, or none |
| Every lead | `lead_submitted` | **Secondary (observe only)** | One | None |

- Google's automated bidding optimizes toward the primary conversions in the goals it's given. A conversion that isn't included is reported, and never bid for.
- Leads count **One** per click. **Every** counts a repeat submission twice, and the bidding learns from the duplicate.
- Set the conversion tag's transaction ID to the event ID, so a reload can't count the same lead again.
- Turn on enhanced conversions in Google Ads, and set the conversion tag to send the lead's email and phone (Google hashes them before they leave the browser).
- Don't keep an imported analytics "form submit" as a primary conversion beside the qualified conversion. Bidding will optimize toward the bigger number.
- Never fire one conversion action with a value of zero for leads that don't qualify. A zero-value conversion is still a conversion, and it's counted.

## Later results

The best signal is the result itself: how far a lead gets through the funnel, and what its account turns out to be worth. Those arrive weeks after the click, so they go back to the platforms as later conversions, for the leads that cleared the line on the form and only those. Send each one as it's reached, not in a monthly batch: Meta's Conversions API turns away an event more than 7 days after it happened.

Report as far into the funnel as you can, for the qualified leads only. Meta's guidance for its CRM integration is to send every stage as it's reached, the raw lead included, and let the bidding put more and more weight on closed won. The blueprint holds back on purpose, because closed won isn't the goal. Left to itself, with volume bias pulling the other way, the bidding optimizes for the small closed-won accounts, because there will always be more of them. So every later conversion is limited to the leads that cleared the line when they came in. Each stage one of them reaches (MQL, SQL, SQO, closed won) goes back as its own conversion, whether or not it goes on to the next. A lead that didn't qualify on the form sends nothing later, even when it advances. The deepest result is the value line: the first full month of revenue above the median, read early enough to land inside the platforms' windows. Google takes a click ID up to 90 days old and hashed details up to 63 days after the click, so a line read on a full first quarter arrives too late to teach the bidding anything. Tiering and reporting keep the full quarter ([section 7](07-close-the-loop.md)):

- **Google:** enhanced conversions for leads matches a later result to the click from the hashed email captured on the form, alongside the GCLID. From June 15, 2026, these uploads go through Google's Data Manager API instead of the Google Ads API, so check the current method before building it.
- **Meta:** send each later stage, and the value-line result, through the Conversions API with the same hashed details and the lead's event ID, each in its own event, for the qualified leads only. Name the events the way the send log does (`templates/crm_fields.csv`): `mql`, `sql`, `sqo`, `cw` and `above_line`.
- **Which one to bid on:** the one that happens soon enough and often enough for the bidding to learn from. Platforms only credit results inside their lookback windows. Keep the later stages as secondary conversions, and move the bidding later in the funnel as the volume allows. The stage timestamps make that switch a setting, not a rebuild.

## Every source reaches the same events

Landing pages can differ by source, and so can the thank-you pages' copy. The container and the events can't. A lead from Google fires Meta's `Inquiry`, and its `Lead` when it qualifies, the same as a lead from Meta. That isn't credit. PRO decides the source, and Meta's Ads Manager is a separate count: by default it credits Meta with any conversion from someone who clicked a Meta ad in the last 7 days or saw or engaged with one in the last day, so a Google lead can show up there as Meta's too. Events Manager counts every Lead event, whatever the source. What matters for the bidding is that Meta's guidance says "you can use only matched events for ads attribution and ad delivery optimization," so what lets an event teach the bidding is a match to a person, not a click on a Meta ad. The same holds the other way for Google's tag.

## Show the platforms who your best customers are

Never send existing customers to the qualified thank-you page (from a survey email or a newsletter, say) to show the platforms more of the people you know are worth having. Each visit would fire a conversion that didn't happen: the platform's counts and value rise, an ad a customer happened to see gets credit, and the bidding learns from people already won. With the events fired on the server's answer, such a visit fires nothing anyway. Instead:

- **Send back the qualified leads' later stages and value-line result** (above). The platform learns how far its qualified leads got and which turned out valuable, matched to the click that brought them.
- **Give customer visits their own event.** A survey page or a customer area fires a custom event of its own, `customer_survey_completed` for example, never `Lead`. Build audiences from it, and keep it out of every ad set's goal.
- **Upload the customer list and every existing lead** to keep them out of prospecting, whatever each lead answered, refreshed weekly, and, outside the Special Ad Categories, the customers as a seed for the platform's audience suggestions. Never upload only the leads below the line. That list would tell the platform the answer ([section 4](04-the-signal.md)). In a Special Ad Category, custom-audience exclusion still works.

In a Special Ad Category, lookalike audiences aren't available, because a model built on existing customers can reproduce protected traits. Seeding the bidding with customers is the same model by another route: a question for counsel first.

## Enough to learn from

Starving the algorithm means fewer conversions. Set the line at the middle-high bands, not the very top. The working minimum is 30 qualified conversions per campaign in 30 days. Plan for no fewer than 45, so a slow stretch doesn't take a campaign under it, and aim for 60 a month, double the minimum. Meta's learning phase looks for about 50 optimization events per ad set in a week, so a campaign at these levels can stay in learning longer, and run this way, campaigns have held up in practice. On Google, target ROAS on Search typically needs at least 15 conversions in the past 30 days. If `qualified_conversion` fires too rarely for that, consolidate first, into fewer campaigns and ad sets that each clear the minimum, then move the line down one band, or move to an earlier signal. Don't go back to every form fill.

## Tie the platforms' counts to yours

Every week, the conversions each platform logged should tie very closely, if not exactly, to the qualified submissions in the submission store that should have reached it: the ones whose PRO source is that platform, from visitors who didn't opt out of tracking ([section 8](08-qa-checklist.md)). A difference of one or two comes from attribution windows and people who clicked on one device and sent the form on another. A week that falls well short means the tag or the Conversions API stopped sending.

Two totals tie exactly. Meta's Events Manager should receive one `Lead` for every qualified submission from a visitor who didn't opt out, from any source, because the Pixel and the Conversions API send them all, and one `Inquiry` for every submission from a visitor who didn't opt out. GA4's `generate_lead` should count every submission from a visitor who didn't opt out.

## The thank-you pages are for the visitor

The server decides who qualifies, and the events carry the conversion. The two thank-you pages, one for leads that clear the line and one for the rest, are there for what the visitor reads next, so give them neutral addresses and never build a conversion on one:

- **Meta may never see the address.** On financial-services pixels (banking, lending, financial services, insurance), Meta's Core Setup can restrict "custom parameters and parts of URLs after the domain." A custom conversion on a code in the address, or on the qualified page's path, then matches an address Meta never receives. A data layer event fired on the server's answer works the same either way.
- **Meta flags custom conversions that suggest financial status.** Since September 2025, a flagged custom conversion can't be used in new campaigns and stops receiving data. A rule built on an answer band invites it. The standard `Lead` event needs no custom conversion at all.
- **Google receives the full page address,** so anything in it goes to Google with every tag, and a page-load conversion has no transaction ID to deduplicate with.
- **A page load isn't a lead.** Reloads, the back button and a direct visit to the qualified page all load it. The events fire once, for a saved lead, with its event ID.

So `submit.js` sends the visitor to the page the server picked, and that page pushes `lead_submitted` and, for a qualified lead, `qualified_conversion`, once. The tag manager fires on those events ([gtm/README.md](../gtm/README.md)).

**Special Ad Categories.** On Meta, US ads for credit, employment, housing and financial products and services run in a Special Ad Category, and the financial category covers credit cards, financing, bank accounts, investment and insurance services and related financial offers, so ads for personal and business loans fall in it and ads for payment services can too. It's decided per campaign by what the ad promotes, not by the event the campaign optimizes for, so no event name keeps a campaign out of it. Check Meta's current definitions before launch.

## The tag manager

[`gtm/README.md`](../gtm/README.md) lists the variables, triggers and tags for Google Tag Manager, with the test cases.

*Platform settings checked October 28, 2026, against Google Ads Help ("About account-default conversion goals", "About conversion counting options", "About enhanced conversions for leads") and Meta for Developers ("Handling Duplicate Pixel and Conversions API Events"). Platforms change these pages, so check them when you build.*

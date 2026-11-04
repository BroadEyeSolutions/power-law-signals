# 6 · Report on PRO, never on raw data

No report runs on raw data. The CRM's lead source field, the tags on a form and a platform's own count were each captured by a different system for its own purpose, each one is missing or wrong on some share of the leads, and a report built on any one of them is only as accurate as that field. Reports read a separate layer, built to make attribution accurate and actionable: the PRO fields (PRO is Performance Revenue Optimization). It's the layer ABPRO_ builds every client's reporting on.

- **Raw data is the evidence:** the tracking tags, click IDs, capture URL, user agent, referrer, the fields hard-coded on the form and the CRM's own fields, exactly as captured. It's never edited, and no report reads it directly.
- **The PRO fields are what reports read.** Each one is mapped to a value in the reporting vocabulary, and each one is resolved from all of the lead's evidence, not from a single field, through the map files and ordered rules. Every value can be corrected, and its `_basis` column names the evidence that decided it.
- **`zNAA`** (no attribution available) fills a PRO field only where the evidence runs out, at the level where the trail stops. Everything the evidence does settle keeps its value. A web lead with no tags, no click ID and no referrer still has its form and its site, so its source is `website` and its medium is `zNAA`.

A PRO value is almost never a CRM field read as it stands: the CRM field is evidence, and a map turns it into a value you can report on ([section 10](10-maps-keys-and-audits.md)).

## Cookieless by design

Two fields arrive with every web submission, whatever the visitor's tracking choices: the page it was sent from (the **capture URL**) and the browser that sent it (the **user agent**). With those two alone, most teams can get web attribution working better than any third-party tool manages.

- **The capture URL carries the ad's tags.** On the page an ad sent the visitor to, the address still holds the ad's parameters. A visitor who opted out of tracking isn't followed from page to page, and that wish is kept. But the page they submit from is part of what they submit, under the form's consent checkbox, and its parameters arrive with it. That makes the lead attributable in your own reports. Nothing about it goes to the ad platforms ([section 5](05-tell-the-platforms.md)).
- **The user agent names the in-app browser.** Instagram's, Facebook's and Messenger's built-in browsers say so, which gives the source and medium when the tags are gone.
- **The form ID and the hard-coded fields** (capture method, brand) say which door the lead came through and what that door was built for.

Tags carried in cookies or browser storage are the backup, for the visitors who browsed to another page before they submitted. When they're there, PRO reads them first, because they came from the arrival itself. The model doesn't depend on them.

## The PRO fields

| Field | The question it answers | Values | Decided by |
|---|---|---|---|
| **PRO Brand** | Which brand did the lead engage with? | Brand (the main brand), Non-Brand (sub-brands, and other brands and sites the business launched or bought) | `MAP_BRAND`: the brand hard-coded on the form, then the capture URL's domain |
| **PRO Capture Group** | Did it come from the website? | Web, Non-Web | The capture URL, then `MAP_CAPTURE` |
| **PRO Capture Method** | How did it get into the CRM? | Web Form, Live Chat, Inbound Call, Referral, Third Party API, List, Manual Entry | `MAP_CAPTURE`, from the hard-coded capture method on the record or the form's row |
| **PRO Conversion Point** | Through which door, exactly? | The form ID (`WF-0001`), tracking number, chat or partner, named in the form map | `MAP_FORM` |
| **PRO Class** | Did an investment bring it? | Investments (what you pay or partner for: ads, sponsorships, trade shows, referral partners), Inbound (what arrived with none), `zNAA` | The category, through `category_class` in the rules file, so a business can move one |
| **PRO Category** | What kind of investment brought it? | Advertising, Affiliate, Organic, Direct Sales, Legacy, `zNAA` | Rules on the fields around it |
| **PRO Source** | Which platform or channel? | `meta`, `google`, `microsoft`, `linkedin`, `newsletter` … | `MAP_SOURCE` |
| **PRO Medium** | The first cut of that platform's spend, in the exact value its own spend report uses | Meta (Platform): `facebook`, `instagram`, `messenger`, `audience_network` · Google (Campaign type): `Search`, `Display`, `Video`, `Performance Max`, `Demand Gen`, `Shopping` · LinkedIn (campaign type): `SPONSORED_UPDATES`, `SPONSORED_INMAILS`, `TEXT_AD`, `DYNAMIC` · `content` (your own posts that aren't ads), `organic` (a visit with no tags, sourced from its referrer: set by PRO, never a tag), `email` | `MAP_MEDIUM`, keyed on the source and the raw medium |
| **PRO Campaign** | Which campaign? | The campaign's reporting name, with its `campaign_key` | `MAP_CAMPAIGN`, by ID first, then by name |

**Capture Method** is the most underused field in most CRMs. How a lead got into the CRM is one of the earliest predictors of what it's worth, whatever its source: a call and a rep-entered referral convert differently from a form fill, and a list import differently again. Every door writes it, hard-coded, and nobody types it. It rolls up to the **Capture Group**: Web Form and Live Chat are Web, and everything else is Non-Web, including an ad platform's own lead form, which is online but isn't your website.

**Leads a rep created** (Manual Entry) get their own category, Direct Sales. They convert differently from anything marketing bought, and mixed in with the rest they flatter whichever channel they land in.

## Cut the data in this order

1. **Label what isn't in scope.** Tests, spam, duplicates and out-of-scope leads (job seekers, existing customers asking for support) get a label, never a delete. Every performance number leaves them out, and the raw data keeps them.
2. **Brand against Non-Brand.** Most businesses have more than one brand by the time they look at attribution: a sub-brand launched later, a second site, a company bought with its own forms. Mixed together, each one's numbers hide the others'. Cut them apart first.
3. **Web against Non-Web, then Capture Method.** The website's leads and everyone else's convert differently, and the capture method says how each one got in.
4. **Class, Category, Source, Medium, Campaign.** Each level is a subcategory of the one before it, read in the same vocabulary everywhere. Investments › Advertising › meta › instagram › a campaign is the same path in every report, every month.

At each level, aim for three to five groups, keep "other" and `zNAA` together under about a fifth of the leads, and split any group that's big enough to matter. The best layer to report on isn't the most detailed one. It's the one whose groups differ the most from each other.

## The order of evidence

Each PRO field reads all of the lead's evidence, strongest first, and takes the first piece that settles it. Every tracking value is read from the lead's own stored field first, then from the capture URL.

**PRO Source:**
1. `utm_source`, through the source map ("Facebook" and "fb" become `meta`)
2. A click ID (`gclid`, `gbraid` or `wbraid` means `google`, `fbclid` means `meta`, `msclkid` means `microsoft`)
3. The form's built-for source, from the form map
4. The in-app browser (Instagram's, Facebook's or Messenger's built-in browser means `meta`)
5. The referrer (`google.com` means `google`, `facebook.com` means `meta`), with the medium set to `organic`
6. A web lead with none of these: `website`, or your site's own domain (`website_source` in the rules), grouped by its form ID
7. Nothing settles it: `zNAA`, short for no attribution available. The z sorts it to the bottom of every list

**PRO Medium**, read in the source's own vocabulary:
1. `utm_medium`, through the medium map ("ig" becomes `instagram`, "cpc" on Google becomes `Search`)
2. The in-app browser (Instagram's browser means `instagram`)
3. The form's built-for medium
4. `organic`, when the source came from the referrer
5. `zNAA`

**PRO Campaign:** the campaign ID through the campaign map, then the campaign name, then the raw ID, then `zNAA`.

**An example.** A lead arrives with no tracking tags in its fields, and a capture URL with none either. Something between the ad and the page dropped them. It came in on form `WF-0001`, which only runs in Meta ads, and the browser is Instagram's built-in one. PRO resolves it to Brand › Web › Web Form › Advertising › `meta` › `instagram`. The source basis reads `form_default:WF-0001` and the medium basis reads `in_app:instagram`, so anyone checking can see exactly why. The campaign stays `zNAA`, because only the tags carry it.

## What's missing is evidence too

Attribution isn't only what landed in the source, medium and campaign fields. It's everything known about a lead, and everything known to be missing.

The capture URL is the clearest case. If every web form and chat submission writes the page it was sent from into the CRM, without exception, then a lead with no capture URL didn't come from the website. It came from a call, a referral, a rep, a list or an ad platform's own form. That's the **Capture Group**:

| Capture Group | Rule | Basis |
|---|---|---|
| Web | The lead has a capture URL | `capture_url` |
| Web, with a gap | No capture URL, but the hard-coded capture method says web form or chat. A capture gap to fix at the form | `capture_method_no_url` |
| Non-Web | No capture URL, and nothing says web | `no_capture_url` |

Web and Non-Web then become two cohorts to read through every funnel stage, from the lead through MQL, SAL, SQL and SQO to closed won ([section 1](01-the-chain.md)). Non-Web leads stop hiding inside "unknown", and their own stage rates show up beside the website's. Split them by Capture Method next, and the calls, referrals and rep-entered leads each get their own line. The fields are on every lead, so any reporting tool can read the funnel by them. ABPRO_ reads it by cohort.

The rule only holds if the capture is diligent. One web form that skips the capture URL turns its leads into Non-Web by mistake, so the weekly checks ([section 8](08-qa-checklist.md)) watch the capture URL on every web form, and the `capture_method_no_url` count should stay at zero.

## Confidence falls level by level

The form ID and the capture URL keep the top levels solid. A worked example, with illustrative numbers:

- 30% of visitors opt out of tracking. Nothing follows them from page to page.
- 10% of form fills happen on a page other than the one the ad sent them to.
- The 90% who fill in the form on the Meta landing page resolve to `meta` from the form ID alone, tags or no tags. Their capture URL carries the campaign, ad set and ad IDs too, opted out or not.
- Of the 10% on another page, the 70% who allowed tracking still carry the tags from the landing page, from browser storage. The 30% who opted out arrive with a capture URL from a page the ad never pointed to.
- PRO Source: 90% + 7% = **97% of Meta's leads attributed to Meta.**

| Level | What it needs | Resolved in the example |
|---|---|---|
| Source | The form ID, or the tags (stored, or in the capture URL), or a click ID | 97% |
| Medium | The tags, or the in-app browser | 97% |
| Campaign | The tags, and a campaign ID that maps | 97% |
| Ad set | The tags, and an ad ID that maps to its ad set | 97% |
| Ad | The tags, and an ad ID that maps to a name | 97% |

Without the capture URL and its tags, everything below the source would rest on the visitors who allowed tracking: 70% in this example, which is where most teams stop. (These are your own reports. For a visitor who opted out, nothing is sent to the ad platforms.) So where does the confidence go, even with it? Three places.

1. **Tags that never reach the page.** Some apps, redirects and link shorteners strip the parameters before the page loads. The form ID still gives the source. The campaign, ad set and ad are gone.
2. **IDs that don't map.** An ad ID that arrived truncated, a campaign that was never tagged with its ID, a spend export missing a rename: each one costs a level below the source and nothing above it.
3. **Thinner slices.** A platform with 1,000 leads a month, 5 campaigns, 20 ad sets and 60 ads has 970 traced leads behind the platform question, 194 behind each campaign, 49 behind each ad set and 16 behind each ad. One lucky account moves an ad's numbers. It barely moves the platform's.

Read attribution from the top down. Settle whether a platform works, by the above-average accounts and revenue its leads produce, before arguing about which ad does. The first question has a near-complete answer and a lot of leads behind it. The last one rests on a smaller, less certain slice.

`resolve_sources.py` prints how many leads each level resolved, and the `_basis` counts show how much of it came from the capture URL, so you can see where your own confidence drops.

## Every value shows its basis

Each PRO field has a `_basis` column beside it: `utm_source`, `capture_url:utm_source`, `click_id:gclid`, `form_default:WF-0001`, `in_app:instagram`, `referrer:google.`, `campaign_map:utm_campaignid`, `capture_url:domain`, `form_map:PH-0001`, `none`. A report can then show how much of a channel's volume was resolved from evidence weaker than its own tags. When a share of Meta's leads starts resolving from the form default instead of `utm_source`, something is stripping the tags, and the basis column is where it shows up first.

## Don't guess

- A value the maps don't know is kept and flagged (`utm_source_unmapped`, `brand_unmapped`), and `analysis/update_maps.py` appends it to its map as an unverified row for someone to review. It's never silently filed under something else.
- With nothing to go on, the answer is `zNAA`. It's a real finding, and its own line in every report. Some reports roll it into brand demand, on the reasoning that demand nobody can trace is demand the brand created. If yours does, keep `zNAA` visible underneath, so the gap stays a gap.
- Tests, spam, duplicates and out-of-scope leads are labeled, never deleted. They stay in the raw data, and every performance number leaves them out.

## Overlay, never overwrite

The PRO fields sit beside the raw capture. A correction goes in a map, or in an overrides table for a single lead (lead ID, field, new value, who, why), applied on top at every rebuild. Nothing writes back into the CRM's raw fields or the form data, and an audit never "cleans" the system of record. See [10 · Maps, keys and audits](10-maps-keys-and-audits.md).

## IDs to names

Campaign, ad set and ad names come from each platform's spend export, joined on the IDs the tags carried, and they live in the campaign map. Each campaign gets one `campaign_key`, so a report groups on the key and a renamed campaign stays one line. Read IDs as text. Spreadsheets round long numbers, and a rounded ID quietly matches the wrong ad.

## The starter

`analysis/resolve_sources.py` resolves a CSV of leads through the map files in `maps/` and the starter rules in `analysis/rules/pro_rules.example.json`, and writes the PRO fields and their bases beside the raw columns. `analysis/update_maps.py` lists the raw values the maps don't know yet:

```
python3 analysis/sample/generate_sample.py
python3 analysis/resolve_sources.py analysis/sample/leads.csv --out analysis/sample/leads_resolved.csv
python3 analysis/update_maps.py analysis/sample/leads.csv
```

## What ABPRO_ adds

This repository resolves one file of leads through its starter maps. ABPRO_ runs PRO across a client's CRM, every web form and each ad platform's spend export: one lead ID tied to every system's own IDs, the systems' counts stacked by date, campaign, ad set and ad names resolved from their IDs, campaign groups and cohorts, managed advertising separated from boosted posts, the account and revenue maps that tie each lead to what it became, an editable map workbook that every report reads from, and every source and signal read by the share of above-average accounts it produces and the revenue they return, month by month. That's the done-for-you version.

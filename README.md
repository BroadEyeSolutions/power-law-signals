# Signals and Attribution Blueprint

**Broad Eye Solutions** · How to build attribution and value signals into a lead funnel, from the ad click to the revenue it produced.

In most revenue books, a minority of accounts carries most of the revenue. A funnel that counts every lead the same can't see that, and neither can the automated bidding it feeds: it finds as many leads as it can, from wherever they come cheapest, and that's where the accounts are worth the least.

This blueprint fixes both halves:

- **Attribution:** each system keeps its own IDs. Every lead gets one ID, made once where it enters, and every system's own IDs are tied to it, from the form through the CRM, the decision and the account to the revenue. Where systems share no ID, such as the ad platform and the CRM, the date joins them: their counts are stacked side by side by date, source and campaign, and tied out every week. Each lead's source is resolved beside the raw data, through map files and rules you can read and correct.
- **Signals:** one question on the form, about the business, predicts which leads become above-average accounts. Only those leads are reported to the ad platforms as conversions, so the bidding goes looking for more of them.

It's how Broad Eye Solutions builds it for clients, as PRO (Performance Revenue Optimization). The docs, code and templates here are open source, under the MIT License.

## The build

| | Part | What it covers |
|---|---|---|
| 1 | [The chain](docs/01-the-chain.md) | One ID across every system: each system's own IDs, tied to one lead ID, and the date as the join where no ID carries across. Each system's own count, and the weekly tie-outs between them. Conversion points, capture method, brand. Leads, opportunities, accounts. The funnel stages, from conversion to prospect to lead and on to revenue (prospect greyed out where conversions become leads directly, risk where there's no underwriting), each with a first and a last timestamp |
| 2 | [Tag every link](docs/02-tag-every-link.md) | One parameter set and one vocabulary. Meta, Google and LinkedIn templates. The medium as the value each platform's own spend report uses |
| 3 | [Capture at the form](docs/03-capture-at-the-form.md) | Form IDs, hidden fields, saving to the submission store first and one path into the CRM, multi-step forms, consent, analytics |
| 4 | [The signal](docs/04-the-signal.md) | Choosing the question, ordered answer codes, one rules file, what's off-limits |
| 5 | [Tell the platforms](docs/05-tell-the-platforms.md) | Two events, one conversion to bid on. Meta Pixel and Conversions API. Google Ads goals and counting. Later results. Tying the platforms' counts to yours |
| 6 | [Report on PRO, never on raw data](docs/06-raw-source-and-pro-source.md) | Why reports read the PRO fields and never the raw data. Cookieless attribution from the capture URL and user agent. The PRO fields, the order to cut them, what's missing as evidence (Web and Non-Web), confidence by level |
| 7 | [Close the loop](docs/07-close-the-loop.md) | Joining leads to revenue, reading campaigns on value, the signal register, and where ABPRO_ takes over |
| 8 | [QA](docs/08-qa-checklist.md) | Launch checks, the breaks that show up most, the weekly tie-outs, field coverage and maps |
| 9 | [The tracking plan](docs/09-tracking-plan.md) | Event names, and which system does what |
| 10 | [Maps, keys and audits](docs/10-maps-keys-and-audits.md) | Raw, maps and PRO. How map files are keyed and kept. Why audits never write back to the CRM |
| 11 | [What your CRM needs](docs/11-what-your-crm-needs.md) | One record per lead, its ID carried through conversion. Every submission kept, the first never overwritten. The fields by object and what writes each, a first and a last timestamp on every stage, picklists matched on values. What the return path needs for a qualified lead's later stages and value-line result, the read-only extracts, PRO kept out of the CRM, and the CRM's own QA |

## What's here

```
src/capture.js            on every page: keeps the visit's tracking tags, fills the form's hidden fields
src/submit.js             sends a lead form in the right order: save first, move to the thank-you page the server picked,
                          and push the events there, once
src/signal.js             answers to ordered codes, and qualified or not, from the rules file
src/signal-rules.json     the one place the line is set
server/lead-endpoint.mjs  scores the lead, saves it to the submission store, forwards it to the CRM, and sends the
                          qualified conversion to Meta's Conversions API
functions/lead.js         the same endpoint as a Cloudflare Pages Function
gtm/README.md             the Google Tag Manager variables, triggers, tags and test cases
examples/                 a complete example form, and its two thank-you pages
maps/                     the map files: brand, capture method, form, source, medium, campaign and self-assessment question (SAID), keyed on raw values
analysis/                 resolve_sources.py (PRO fields, through the maps), update_maps.py (new raw values, for review),
                          and a generator for a synthetic lead book
templates/                capture fields, UTM vocabulary, tracking plan, funnel stages, lead statuses, signal register,
                          tie-outs, CRM fields
tests/                    unit tests, and an end-to-end test of the example form in a real browser
```

## Get it

```
git clone https://github.com/BroadEyeSolutions/power-law-signals.git
cd power-law-signals
```

Or download it as a ZIP from the green **Code** button on GitHub. Start with [the chain](docs/01-the-chain.md), then work through the build in order. Each part says which files in this repository it uses.

## Try it

```
npm test                                     # unit tests (Node 20+ and Python 3.9+, no installs)
npm run test:e2e                             # the example form in Chromium (first: npm i --no-save playwright && npx playwright install chromium)

python3 analysis/sample/generate_sample.py   # a synthetic lead book
python3 analysis/resolve_sources.py analysis/sample/leads.csv --out analysis/sample/leads_resolved.csv
python3 analysis/update_maps.py analysis/sample/leads.csv      # raw values the maps don't know yet
```

The sample is synthetic. No real company, lead or account is in it. It isn't kept in the repository: the generator makes the same book every time.

## Deploy the endpoint

`functions/lead.js` is a Cloudflare Pages Function for `POST /lead`. Copy it, with the `server/` and `src/` folders, into your Pages project, keep `src/signal-rules.json` out of the site's public output folder so your line is never served, and set the variables listed at the top of `functions/lead.js`. The endpoint saves every lead to your submission store first (`SAVE_WEBHOOK`, such as a Google Sheet's Apps Script web app or a web-connected database), so that store is yours to set up. `server/lead-endpoint.mjs` also runs as a Worker or in Node 20+.

## The principles

1. One ID per lead, made once where it enters and tied to every system's own IDs. Where no ID joins two systems, the date does.
2. Every form, number and partner has its own ID, and every lead a hard-coded capture method.
3. Raw capture is never edited, and audits never write back to the CRM. Attribution is resolved beside it, through map files, from everything known and everything known to be missing, and every value shows how it was decided.
4. The signal is about the business, never the person, and it's checked against revenue before anyone bids on it.
5. The ad platforms hear that a qualified conversion happened. They never see the answers.
6. The lead is saved before anything else fires, in a submission store as well as the CRM, and every system's count is tied out every week.
7. Every lead is still worked. The signal decides the order and who calls, not who gets a call.
8. Expect cost per lead to go up. Judge it by revenue per lead.

## Where the blueprint stops

This blueprint gets the data into the right systems, with the IDs that join them, and sends the platforms the conversion worth bidding on. Reading that data is what ABPRO_ does, on your own book:

- **The joined data, read by value.** Tiers, signal checks, the funnel by cohort, the revenue each cohort returns per $1 at 1, 3, 12 and 60 months, and forecasts, from your statements, CRM and spend.
- **The rules that set the numbers.** How accounts of different ages are tiered, what counts as invested in each cohort, how the baseline is drawn, and when a signal has earned its place in the bidding.
- **Maps built with you.** One account across every system's IDs, your reps and partners in every spelling, campaigns and pricing, kept current as your sources change.
- **One universe across every view,** so the accounts that carry the book are in every report.
- **Every figure traced to its column,** with tests on every refresh.
- **A refresh every statement cycle,** and a monthly review.

[abovebaselinepro.com](https://abovebaselinepro.com)

## The full PRO build

This repository is the method and a working starter. Broad Eye Solutions runs the full build for clients: the tracking and form work across every site, the CRM pipeline and its fields, the platform setup, and PRO attribution across the CRM, every web form and each ad platform's spend, reported in ABPRO_ with every source and signal read by the above-average accounts it produces and the revenue they return.

[broadeyesolutions.com](https://broadeyesolutions.com)

---

Platform settings checked October 28, 2026. Meta and Google change their settings and help pages, so check them when you build.

MIT License · © 2026 Broad Eye Solutions LLC

# 7 · Close the loop

Attribution and signals pay off when each lead is read by what it became. That takes the chain from [section 1](01-the-chain.md), every lead joined to its outcome, and a register of every signal.

## Join each lead to what it became

- Join each opportunity, decision and account to its lead through the ID map: on the lead ID where the system holds it, and on the system's own IDs where the map ties them to it ([section 1](01-the-chain.md)).
- Older records without a lead ID need a documented match, recorded with its basis so it can be told apart from a clean join. ABPRO_ builds those account and contact maps for its clients ([section 10](10-maps-keys-and-audits.md)).
- Keep the leads that never became accounts. They're half of every rate below.

## What happens to the joined data

With every lead joined to what it became, the book can be read by value: the accounts tiered by what they're worth over time, each signal checked against the above-average accounts it found, and each cohort read through the funnel stage by stage. That reading is ABPRO_'s job. This blueprint makes sure the data it reads is there, in the right systems, with the IDs that join them.

Whether a signal has earned its place in the bidding is checked on your own book, cohort after cohort, against the above-average accounts its leads became. ABPRO_ runs that check.

## Read campaigns on value

- Judge each source, campaign and form by above-average accounts per 100 leads and by revenue per lead, read by cohort at one, three and twelve months.
- Cost per lead tells you what each lead cost. It says nothing about what it's worth.
- Expect cost per lead to go up when the bidding moves to the qualified conversion. The test is whether revenue per lead rises faster.

## Keep a signal register

`templates/signal_register.csv` holds every signal, live or retired: its rule, where it's captured, when it's known, where it's installed (bidding, scoring, routing), who owns it and when it was last checked, with its lift, coverage and sample filled in from the latest check. `ab_per_100_leads` counts tier A and B accounts, the above-average ones, per 100 leads.

| Status | Meaning |
|---|---|
| proposed | Lift found, not yet installed |
| testing | Installed on part of the traffic, with a comparison group |
| live | Installed everywhere it applies |
| retired | Stopped predicting, or replaced |

A change to the line is a row too: the signal, the old line, the new one, the month it took effect and the 30-day counts behind it ([section 4](04-the-signal.md)).

**A score is a signal.** When one question stops being enough, what a lead does in its first days can sort leads too. ABPRO_ builds and runs that score for its clients, and it gets its own row here like any other signal. First-party behavior only: nothing about a person's finances, no trait the law protects, nothing from a data broker.

## The rhythm

| How often | What |
|---|---|
| Weekly | The tie-outs between the platforms, analytics, the submission store, call tracking and the CRM, and field coverage by source ([section 8](08-qa-checklist.md)). The share of each channel's leads resolved from evidence weaker than its own tags |
| Monthly | Re-tier the book and re-check every signal on the newest cohorts (ABPRO_) |
| Each new cohort | Confirm every live signal still holds its lift. Retire the ones that don't |

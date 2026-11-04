# 4 · The signal

Attribution says where a lead came from. A signal says what it's likely to be worth, early enough to act on. In a power-law book, a minority of accounts carries most of the revenue, so the earliest trait that predicts those accounts is worth more than any other field on the form.

## What makes a good signal

- **It's about the business, never the person.**
- **It's known at the first form,** while it can still steer bidding, scoring and routing.
- **It predicts value in your own book.** You check that before you act on it ([section 7](07-close-the-loop.md)).
- **It costs the wrong lead more to give.** A declared monthly sales band takes seconds for anyone, but a booked call or a document upload takes effort a tire-kicker won't spend.
- **The platforms allow it and the law permits it** (below).

## Candidates to test

| Trait | Example question or field |
|---|---|
| Size | Average monthly sales, in bands. Number of locations. Number of employees |
| Age | Time in business, in bands |
| Presence | Do you have a website already? |
| Intent | The amount or plan asked for. When they want to start |
| Channel | Called or filled in a form. Booked a meeting or didn't |
| Effort | Finished the second step. Uploaded documents |

## Where the signal sits decides what it can change

A signal can only change the stages from the point where it's found onward ([section 1](01-the-chain.md) has the funnel), and an optimization built on it works at the stage where it's applied.

| Where the signal is found | What it can change | What it can't |
|---|---|---|
| On the form (conversion, MQL) | The bidding, the lead score, routing and speed to lead, and every stage after | Nothing before the click |
| On the first call (SAL, SQL) | Routing, qualification, the offer, underwriting | The ads that already bought the lead |
| In underwriting (RQO, where there is one) | Approval, pricing, terms | Who was acquired, or which rep worked them |
| In the revenue (closed won onward) | Retention, pricing, service | Everything before the sale, unless it goes back to the platforms as a later conversion ([section 5](05-tell-the-platforms.md)) |

- **Earlier reaches more of the funnel.** A signal on the first form can steer the bidding, which decides who arrives at all. The same answer collected on the second call can only steer what happens after it.
- **Later predicts better, and arrives later and rarer.** A funded account is the truest signal, weeks after the click and at a fraction of the volume. Where to add a signal, and which stage to bid on, trade reach against accuracy. Move the bidding later as the volume allows.
- **Read an optimization from the stage where it's applied to revenue.** Above that stage it shows only its cost: a step that sorts at the form lowers the form's conversion rate, and the gain shows up below it.

## Store each answer as an ordered code

Give each answer band a code that sorts in order. Each band adds one more `1`:

| Average monthly sales | Option value on the form | Code |
|---|---|---|
| Under $10,000 | `under_10k` | `0000` |
| $10,000 to $30,000 | `10k_to_30k` | `1000` |
| $30,000 to $100,000 | `30k_to_100k` | `1100` |
| Over $100,000 | `over_100k` | `1110` |

Then the line is one rule. "Starts with `11`" means $30,000 a month and up. Moving the line to $10,000 is a change from `11` to `1`, in one file, with nothing else touched. The raw answer stays on the lead in the CRM, and the code travels with it.

**Move the line by rule, once a month.** Every lead keeps its code, so you can count what each line would have produced over the last 30 days. Once the campaigns are consolidated, set the line once a month at the highest band that keeps every campaign at 45 or more qualified conversions in 30 days (the floor is 30, the aim is 60). Log every change as a row in the signal register ([section 7](07-close-the-loop.md)): the old line, the new one, the month it took effect and the counts behind it. A line that moves every week changes what the platform learns from every week.

The rule lives in one place, `src/signal-rules.json`, read by the server, which decides. The page only moves on to the thank-you page the server picked:

```json
"qualified": {
  "all": [
    { "question": "monthly_sales", "starts_with": "11" },
    { "question": "years_in_business", "starts_with": "1" }
  ]
}
```

Each question in the rules file has an ID of its own, its **SAID** (self-assessment ID), the way each form has its WFID. The endpoint saves each answer's SAID on the lead, beside the answer and its code. When the question is asked differently, it gets a new SAID with its own codes, and the SAID map (`maps/MAP_SAID.csv`) translates both into the same field. The WFID and the SAID are the two IDs every online conversion carries.

## Match on option values, never on labels

The code is looked up from the option's `value`, not the words the visitor sees. A label edited for wording (a different dash, a currency symbol) can't break the rule, and an answer that matches no code is reported as unknown instead of quietly failing to qualify.

## Off-limits

Some traits would predict value and still can't be used, by platform rule and, for protected traits, by law. Leave out:

- personal financial details: credit score, income, debt, net worth
- health, including conditions and treatments
- race or ethnicity, religion, sexual orientation, political views, union membership, criminal history
- anything that stands in for a protected trait, however well it predicts.

Meta blocks custom conversions that suggest financial status or a health condition. Google doesn't allow conversion uploads about sensitive categories, including negative financial status. In credit, housing and employment advertising, the platforms add their own limits, and counsel reviews the question before it goes live.

Business size is a fact about the business, not the person. Even so, check how the platform classifies your account before you rely on any signal, and re-check the rules when a platform updates them.

## The answer never leaves your systems

The platforms never see the answers or the codes. No answers, no codes and no thresholds go in the conversion, the page address or the server call, and the data layer events carry neither (every tag in the container can read the data layer). The only conversion the platforms bid on is the qualified conversion. The endpoint's tests and the end-to-end test check this ([`tests/`](../tests/)).

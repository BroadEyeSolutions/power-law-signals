# 10 · Maps, keys and audits

The numbers in a PRO report are almost never a CRM field read as it stands. The CRM field is evidence. A map turns it into a value you can report on, the same way every month, and anyone can follow the value back to the raw data that produced it.

## Three layers

```
  RAW                         MAPS                               PRO                          REPORTS
  the CRM, the forms,   ──►   keyed tables that translate   ──►  resolved fields, each   ──►  read PRO only
  the spend exports           raw values into one vocabulary     with the evidence behind it
  never edited                edited by people, reviewed         rebuilt from raw + maps
                              and versioned                      on every run
```

- **Raw** is the system of record and the exports pulled from it. It stays exactly as it arrived.
- **Maps** are small tables, kept as files, with one row per raw value (or per combination of raw values) and the reporting value it stands for. This is where people make decisions: what "fb" means, which campaign belongs to which group, which form was built for which channel.
- **PRO** is computed, never typed. Every run rebuilds it from the raw data and the current maps, so a change to a map applies to every past and future lead at once.

## Why the field itself isn't the answer

A CRM's lead source field holds whatever anyone, or any integration, ever put in it: "Facebook", "facebook", "FB", "Meta Ads", a partner's name, a rep's guess. Reporting on it directly gives a different answer each time someone types differently. Fixing it in place makes it worse: the history changes, nobody can tell what it said before, and the next import brings the old spellings back.

A map holds the decision instead. "facebook" means `meta` because a row in `MAP_SOURCE` says so, with who decided and when. The raw value is still there, and the report still matches.

## What a map row looks like

| Column | What it holds |
|---|---|
| The key | The raw value, or the raw values that together identify one thing (`pro_source` + `raw_value` in the medium map, and `platform` + `campaign_id` in the campaign map) |
| The mapped value | What the key means in the reporting vocabulary (`pro_source`, `pro_medium`, `pro_campaign` …) |
| `override` | A person's correction. When it's filled in, it wins |
| `status` | `verified`, `unverified` (added by a script, waiting for a person) or `retired` |
| `first_seen` | When the key first turned up |
| `notes` | Why. Anything someone will want to know in a year |

The value a report uses is the override if there is one, otherwise the mapped value. A blank means not mapped yet, and the resolver says so (`*_unmapped`) instead of guessing.

The starter maps in `maps/`:

| Map | Key | Gives |
|---|---|---|
| `MAP_BRAND.csv` | A brand code hard-coded on the form, or a site's domain | The brand's name, and PRO Brand: Brand or Non-Brand |
| `MAP_SOURCE.csv` | raw `utm_source` | PRO Source |
| `MAP_MEDIUM.csv` | PRO Source + raw `utm_medium` | PRO Medium, in that platform's own vocabulary |
| `MAP_CAPTURE.csv` | raw `capture_method` | PRO Capture Method, and its Capture Group (Web or Non-Web) |
| `MAP_FORM.csv` | `form_id` | The conversion point: what each form, number or feed is, its brand, and the traffic it was built for |
| `MAP_CAMPAIGN.csv` | `platform` + `campaign_id` (or the name, when there's no ID) | `campaign_key`, the reporting name |
| `MAP_SAID.csv` | `said`, the self-assessment question's ID | The field its answers fill, the question as it was asked, the forms that ask it |

## Keys

- **Key on IDs, not names.** A campaign gets renamed. Its ID doesn't. Look up by ID first and by name only when there's no ID.
- **One thing, one key.** When the natural key takes more than one column (platform and campaign ID, because two platforms can issue the same number), give the row a short surrogate key of its own (`campaign_key` `C00001`). Reports group on that key, so a renamed campaign stays one line and two platforms never collide.
- **Keys are minted once and never reused.** A retired campaign keeps its key. A new one gets the next number.
- **IDs are text.** Spreadsheets round long numbers to trailing zeros, and a rounded ID matches the wrong ad. Store IDs as text, and drop any ID that arrived truncated rather than map it.
- **Two systems, two columns.** When the CRM and the ad platform both hold a campaign name and they disagree, keep both, named for where they came from (`campaign_name_crm`, `campaign_name_platform`). Don't silently pick one.

## New values are appended, never guessed

New raw values arrive every month: a new campaign, a new spelling, a form that went live without a row. `analysis/update_maps.py` reads the raw leads, finds every value with no row, and appends it to its map as `unverified` with the mapped value blank. Someone who knows the accounts fills it in and marks it `verified`. Until then the resolver keeps the raw value and flags it, so the gap shows up in the report instead of hiding in the wrong line.

```
python3 analysis/update_maps.py leads.csv            # show what's new
python3 analysis/update_maps.py leads.csv --write    # back up the maps, then append
```

It never changes an existing row. Edits to existing rows are made by a person, and every edit is backed up and can be compared with the version before.

## Audits read. They never write back.

An attribution audit pulls the raw data out (the CRM export, the form submissions, each platform's spend export), runs it through the maps, and reports what it finds: missing capture URLs, forms without a row, sources nobody can name, leads in the CRM that never reached the platforms and conversions on the platforms with no lead behind them.

It doesn't fix any of it in the CRM, the form tool or any other system of record. That's deliberate:

- **The system of record is the evidence.** Once it's been "cleaned", nobody can tell what it said, and nothing can be reconciled against the platforms any more.
- **A fix in a map is reviewable and reversible,** and it applies to every past and future lead. A fix typed into the CRM applies to the rows someone happened to touch, and the next import undoes it.
- **The CRM belongs to the team that runs it.** Sales works in it every day. An audit that rewrites their records breaks their trust in it and their reports.

What an audit finds goes one of three places:

| Finding | Where the fix goes |
|---|---|
| A raw value means something the maps don't know yet | A map row |
| One lead is resolved wrongly and no rule would catch it | An override for that lead: lead ID, field, new value, who, why |
| The capture itself is broken (a form not writing its capture URL, a tag stripped) | The form or the tag, so new leads arrive right. History stays as it was, and the maps and the `_basis` columns account for it |

## Coverage

The source, capture, form and campaign maps each get a coverage number: the share of leads whose raw value has a verified row (`update_maps.py` prints it on every run). A falling number means new raw values are arriving faster than they're being reviewed, and it's the first sign that a new campaign, form or integration went live without anyone telling the people who keep the maps.

## Checklist for every map

- [ ] The key is stated in the file's first lines or the docs, and it's unique.
- [ ] Every value has a status. Nothing unmapped is blank without a flag.
- [ ] IDs are stored as text, at full length.
- [ ] Existing rows change only through a person's edit, with a backup.
- [ ] Coverage is measured on every run.
- [ ] No personal details in any map. Review every row `update_maps.py` appends before the map is committed: a value that looks like a name, email, phone number or address is deleted from the map, never kept as a vocabulary entry.

## What ABPRO_ adds

This repository has its starter maps and the scripts to keep them. ABPRO_ builds and keeps the full set for a client: account and contact maps that tie each lead to the account it became, partner and rep identity across every system's spelling, campaign groups and cohorts from the spend exports, effective-dated rules, and an editable map workbook that every report reads from, reviewed with the client's own people each month. That's the done-for-you version.

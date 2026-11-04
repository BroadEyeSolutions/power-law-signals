# 11 · What your CRM needs

Most of this blueprint runs through the CRM. The endpoint forwards each lead into it, sales works the stages in it, the records that turn out valuable go back to the platforms from what it holds, and the reports read it. This part lists what any CRM has to hold and do for the chain to work, whichever one you run. It's the spec, not the build. Field names, screens and automation differ from one CRM to the next, and from one edition of the same CRM to the next, so none of them are here.

"CRM" means whatever holds the records, as in [section 1](01-the-chain.md): one system, or several linked together.

## The work, at a glance

| What | The CRM has to | The size of it |
|---|---|---|
| Records | Keep one record per lead and one per submission, with the opportunity, the account and the company, all tied by the lead ID | Five objects, and a log of what went back to the platforms |
| Fields | Hold the raw capture, the signal, the contact details, the working fields and the stage timestamps. The PRO fields stay out of the CRM | More than 100 fields, most of them on the lead. [`templates/crm_fields.csv`](../templates/crm_fields.csv) lists them |
| Tracks | Create the lead the same way from every door | Eight capture methods, each with its own way in |
| Stage timestamps | Stamp a first and a last on every stage, by automation | 22 date-time fields across the lead, the opportunity and the account |
| The return path | Hold what Meta and Google match on, so a qualified lead's later stages and value-line result can go back inside their windows | A later conversion for each stage a qualified lead reaches, and for the value line, for each platform |
| The extracts | Write a lead file and an accounts file, read-only, on a schedule | Two files |

All of it has to be right on every record from the first lead. A capture field that was written over is gone, and a stage nobody stamped can only be guessed at later.

## One record per lead

- **One lead, one record.** The lead record is whichever object your CRM keeps a lead on, such as a lead, a contact or a person. Every track creates it once, the same way.
- **A lead ID that never changes, created on arrival.** For a web lead it's the event ID of the submission that created it. Every other track makes one the same way every time, such as a stable hash of the email and the date, so it never changes on a rebuild ([section 1](01-the-chain.md)). A prospect gets its ID when it enters and keeps it when it becomes a lead. The ID is unique, stored as text, and nobody can edit it.
- **Carried through conversion.** When the rep converts the lead at the SQL, automation writes the lead ID and the company onto the opportunity. When the opportunity closes won, automation writes the lead ID, the opportunity ID and the company onto the account. Nobody types an ID.
- **The CRM's own IDs stay beside it.** The record ID, the opportunity ID and the account ID are the CRM's own. The ID map ties each one to the lead ID ([section 1](01-the-chain.md)).
- **Every record links to its company,** so a business with several contacts, or one that comes back, is counted once.

Where the account lives in billing or a core system, write the lead ID onto it there if the system has a field for it. If it doesn't, the ID map ties the account ID to the lead ID.

## Every submission is a record

The first submission creates the lead. Every later one is added to it, as a record of its own with its own event ID. In most CRMs that can be a form submission record, an activity or an object of its own. Whichever it is, it needs fields that can be counted and extracted. A note won't do.

- **The first is never overwritten.** A later visit, a second form, or the same form sent twice adds a submission with its own form ID, capture URL, tracking fields and answers. The lead's capture fields keep what the first submission wrote.
- **A duplicate is a conversion, never a new lead.** It moves `conversion_last_at` and leaves `conversion_first_at` alone. It adds nothing to the lead count. A passive lead that sends a form again has raised its hand again, and moves back to the active track ([section 1](01-the-chain.md)).
- **Each submission says how it was matched.** It created the lead, it carried the lead ID, the CRM matched it (usually on email), it came over in a merge, or a person linked it. That's `matched_by`, a basis column like the ones in [section 6](06-raw-source-and-pro-source.md).
- **Where the team merges records, the merge works the same way.** The surviving record keeps the earliest lead ID and the capture fields that came with it, and the other record's submissions move onto it. Each submission keeps its own event ID, so the merged lead's ID is still on the submission that created it.
- **A duplicate record that isn't merged** (an import that missed the match, a mistyped email) is never deleted. It's labeled `duplicate`, points to the lead it repeats in `duplicate_of`, and every performance number leaves it out ([section 6](06-raw-source-and-pro-source.md)).

## The fields, by object

[`templates/crm_fields.csv`](../templates/crm_fields.csv) lists every field: its object, its type, what writes it, how often, whether it's required and the blueprint's name for it. Call the fields whatever your CRM likes. The extract writes them out under the blueprint's names, so every file means the same thing whichever CRM it came from.

Required means the field has to exist. Whether it's filled depends on the track: a call has no capture URL, and that blank is evidence ([section 6](06-raw-source-and-pro-source.md)).

| Object | Fields | Written by | How often |
|---|---|---|---|
| Lead or contact: IDs | `lead_id`, `crm_record_id`, `company_id`, `received_at`, `entered_as` | The endpoint for web leads, automation for every other track, the CRM for its own ID | Once |
| Lead: raw capture | `brand`, `capture_method`, `form_id`, `capture_url`, `referral_url`, the tracking fields and click IDs, `ip_address`, `user_agent`, consent, `tracking_choice` | The endpoint, or the track's integration. Hard-coded by the door, never typed | Once, by the first submission |
| Lead: the signal | Each answer as its option value, its code, `qualified` | The endpoint, from `src/signal-rules.json` | Once |
| Lead: contact details | Name, email, phone, company name | The form, the integration or the team | When they change |
| Lead: working it | `lead_status`, `lead_track`, `owner`, `first_attempt_at`, `contacted_at`, `lost_at`, `lost_reason`, `nonqualified_type` | Automation for the owner, the track and the times. The team for statuses and reasons | On every change |
| Lead: stages | `stage`, and a first and a last timestamp for conversion, prospect, lead, MQL, SAL and SQL | Automation, on the event that moved the lead | First once, last every time |
| Submission | `event_id`, `lead_id`, `received_at`, `matched_by`, and the capture fields and answers as that submission sent them | The endpoint or the track's integration | Once |
| Opportunity or deal | `opportunity_id`, `lead_id`, `company_id`, `created_at`, `stage`, `amount`, `lost_reason`, and the timestamps for SQO, RQO and closed won | Automation for the IDs and the timestamps. The team for the stage, the amount and the reason | IDs once, the rest on change |
| Opportunity: the decision | `decision`, `decision_reason`, `decision_id`, where there's underwriting | Underwriting or the risk review | On change |
| Account | `account_id`, `lead_id`, `opportunity_id`, `company_id`, `started_at`, and the activation timestamps | Automation at closed won, or the core system's integration | Once, and activation's last on reactivation |
| Company | `company_id`, the name, and the records linked to it | The CRM, automation or the team | On change |

Three rules hold across all of it:

- **Raw capture is written once, by the system that captured it.** Lock those fields so the team can read them and can't edit them. A wrong value is fixed in a map or the overrides table, never on the record ([section 10](10-maps-keys-and-audits.md)).
- **The door sets the capture method.** `capture_method`, `form_id` and `brand` come from the form, the integration or the entry screen that created the record. A rep doesn't pick `manual` or `referral` from a list. Each door the team enters leads through has its own screen or form, and that sets it.
- **The PRO fields stay out of the CRM.** They're resolved beside the raw data, from the extract and the maps ([section 6](06-raw-source-and-pro-source.md)), and the reports that judge sources read them there. Nothing writes them into the CRM, so the extract stays the only connection to it, and it only reads.

## Timestamps, statuses and reasons

**A first and a last timestamp on every funnel stage,** `<stage>_first_at` and `<stage>_last_at`, as [section 1](01-the-chain.md) defines them. The lead holds conversion through SQL, the opportunity holds SQO, RQO and closed won, and the account holds activation and revenue. `templates/funnel_stages.csv` names both fields for every stage.

- **Set by automation, never typed.** A rule on the event that moved the record writes them: the first only when it's blank, the last every time the stage is reached. The team can read them and can't edit them. A correction goes in the overrides table ([section 6](06-raw-source-and-pro-source.md)).
- **Stored in UTC.** Every timestamp is stored in UTC, the way the lead endpoint writes it, and turned into the business's own time zone only in reports. A mix of local and UTC times moves records across day and week lines, and the tie-outs drift.
- **The CRM's own stage dates aren't enough.** Many CRMs record when a record entered a stage, and some write over it when the record comes back. Keep the blueprint's pair anyway.
- **A stage the record skipped stays blank.** The automation stamps what happened, never the steps in between ([section 1](01-the-chain.md)).
- **Lost keeps what it earned.** A lost lead or opportunity keeps every timestamp it reached, and gets `lost_at` and a `lost_reason`.

**Statuses and reasons are picklists.** Lead status, lead track, stage, lost reason, non-qualified type, decision and decision reason each have a fixed list of values. Nothing that gets counted is typed.

- **Match on values, never labels.** Rules, reports, the return path and the extract read the stored value (`application_sent`), never the label a rep sees. A label can be reworded without breaking a count, the same as the form's answers ([section 4](04-the-signal.md)).
- **The values come from the templates.** Lead statuses from `templates/lead_statuses.csv`, stages from `templates/funnel_stages.csv`. Map your CRM's own stage and status values to them, by value. The statuses include `duplicate`, `test`, `spam` and `out_of_scope`, the values the rules file reads to leave those records out of every performance number (`analysis/rules/pro_rules.example.json`).
- **A new reason is a new value,** added by the admin. A retired value stays retired, never reused for something else.

## The return path

The qualified leads' later results go back to the platforms as later conversions. [Section 5](05-tell-the-platforms.md) sets which ones: each stage a lead that qualified on the form reaches, and the value line. The value line is drawn from revenue, so that send often runs beside the CRM, from the lead file and the accounts it became. Wherever it runs, the CRM has to hold what it needs:

- **Only the leads that qualified on the form.** Each later stage one of them reaches goes back once, when it's first reached, and so does its value-line result: the account's first full month of revenue above the median, say, read in time to land inside the platforms' windows ([section 5](05-tell-the-platforms.md)). A lead that didn't qualify sends nothing later, even when it advances. Never every closed won.
- **Inside the window.** A rule or a scheduled job sends each one soon after it happens, never in a monthly batch. A result sent after the window is turned away or never credited.
- **With what the match needs.** The lead ID, the click IDs, the email and phone hashed before they leave, and Meta's `fbp` and `fbc` where the lead has them. All of it was written at capture, which is one more reason the capture fields are never written over.
- **Nothing for a visitor who opted out.** A lead with `tracking_choice` set to `opted_out` sends nothing, ever ([section 5](05-tell-the-platforms.md)).
- **Never the answers or the codes.** A later conversion says the lead reached a stage or cleared the value line, and nothing about why ([section 4](04-the-signal.md)).
- **Every send is logged.** One row per lead, platform and event: when it happened, when it was sent and what came back. Then the platforms' counts of later conversions tie out against yours, the way the qualified conversions do ([section 5](05-tell-the-platforms.md)).

## The extracts

The reporting layer reads the CRM through an extract.

- **One row per lead,** in the blueprint's lead-file shape: the IDs, the raw capture fields as they were written, the answers, `lead_status`, `entered_as`, `stage`, and `<stage>_first_at` and `<stage>_last_at` for every stage. The stages held on the opportunity and the account are joined onto the lead's row by the lead ID. Where a lead has more than one opportunity, each stage takes the earliest first timestamp and the latest last timestamp across them.
- **An accounts file beside it,** one row per account: the account ID, the lead ID, the opportunity ID and the company ID. Revenue by period comes from billing, joined on the account ID.
- **The blueprint's column names, every time,** whatever the CRM calls the fields. `analysis/resolve_sources.py` and `analysis/update_maps.py` read the lead file as it comes, and `analysis/sample/generate_sample.py` writes a synthetic one in the same shape.
- **No names, emails or phone numbers.** The IDs carry every join, and the owner goes out as the CRM's user ID.
- **Raw, never cleaned.** The extract pulls what the CRM holds, with IDs as text at full length ([section 10](10-maps-keys-and-audits.md)). Fixes happen beside it, in the maps.
- **Read-only access.** The extract runs as its own user or key, which can read the fields it pulls and can't create, edit, merge or delete anything. An extract that can't write can't damage the records it's there to read.
- **On a schedule,** at least weekly for the tie-outs ([section 8](08-qa-checklist.md)), with nothing edited by hand between the CRM and the file.

## Reports and audits

- **The CRM's own reports run the team:** each rep's queue, the cadence, speed to lead, contact rate, the pipeline by stage and owner. They belong in the CRM, where the team works.
- **The reports that judge sources, campaigns and signals read the PRO fields,** never the CRM's lead source field or the raw tags. A lead source field holds whatever anyone or any integration ever put in it. It's evidence, and a map turns it into a value ([section 10](10-maps-keys-and-audits.md)). They run in the reporting layer, where the PRO fields are ([section 6](06-raw-source-and-pro-source.md)).
- **Audits read. They never write back.** An audit pulls the extract, runs it through the maps and reports what it finds. It never cleans, merges or rewrites a record. Its fixes go in a map, an override, or the capture itself ([section 10](10-maps-keys-and-audits.md)).

## QA for the CRM

The launch checks and weekly tie-outs in [section 8](08-qa-checklist.md) cover the CRM too. Add these.

**Before launch:**

- [ ] **One test record per track.** A web form, a chat, a call, a referral, a Third Party API feed (a platform's lead form and a partner's feed), an import and a manual entry each create one record, with a lead ID, the capture method its door sets and its capture fields filled in.
- [ ] **The same form, sent twice.** One lead, two submissions. The capture fields still hold the first one's values. `conversion_first_at` hasn't moved and `conversion_last_at` has.
- [ ] **Convert and close a test lead.** The opportunity and the account carry the lead ID and the company, written by automation.
- [ ] **Walk a test record through every stage, and back.** Each first timestamp is set once. Each last timestamp moves when a stage is reached again. A skipped stage stays blank.
- [ ] **Edit a capture field or a timestamp as a rep.** The CRM refuses.
- [ ] **Reword a picklist label.** Every rule, report and extract counts the same.
- [ ] **Move a qualified test lead to a later stage, and an unqualified one.** The qualified lead's stage goes once, inside the window, with the lead ID, and it's logged. The unqualified lead sends nothing, and neither does an opted-out one.
- [ ] **Run the extract.** One row per lead, the lead file's columns, no names, emails or phone numbers, IDs at full length. Its user can't write.

**Every week:**

| Check | Healthy |
|---|---|
| Leads, opportunities and accounts with no lead ID | Zero, or tied in the ID map |
| A lead ID on more than one lead record | Zero |
| A record at a stage with no first timestamp for it | Zero |
| A last timestamp earlier than its first | Zero |
| A capture field or first timestamp changed after it was written | Zero, from the CRM's change history |
| Web submissions in the CRM against the submission store | Very close to the same count, if not exactly. Web leads run below it by the duplicates ([section 1](01-the-chain.md)) |
| Later conversions sent back, against the qualified leads that reached each stage or cleared the value line | All of them, inside the window |

Fix what the checks find at the form, the integration or the automation. Never edit a record to make a check pass ([section 10](10-maps-keys-and-audits.md)).

## What ABPRO_ adds

This part is the spec. ABPRO_ does the build, CRM by CRM, for the CRM a client runs, with the client's own admin: the pipeline stages mapped to the blueprint's, the field list in that CRM's own terms, the automation that writes the lead ID, carries it through conversion and stamps every timestamp, the return path to Meta and Google inside their windows, and the extractors that pull the lead file and the accounts file read-only on a schedule. That's the done-for-you version.

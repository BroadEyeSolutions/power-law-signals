# 9 · The tracking plan

One list of every event and property, kept in `templates/tracking_plan.csv`. A new event goes in the plan before it goes in the code.

## Naming

- **Events** are `object_verb`, lowercase with underscores, in the past tense: `lead_submitted`, `form_started`, `application_submitted`, `booking_link_clicked`. `qualified_conversion` is the one exception: it's named for the qualified conversion it sends, the one conversion the platforms bid on, and it isn't a funnel stage.
- **Allowed verbs:** `viewed`, `clicked`, `started`, `submitted`, `completed`, `failed`, `selected`. Don't add synonyms.
- **Properties** are lowercase with underscores. Booleans start `is_` or `has_`. Times end `_at`. First-touch values start `first_`.
- **One property, many values.** `landing_page_variant = b`, never a property per variant.

## The core events

| Event | When | Key properties | Where it goes |
|---|---|---|---|
| `form_started` | First field focused | `form_id` | Product analytics |
| `form_step_completed` | Each step of a multi-step form | `form_id`, `step` | Product analytics |
| `lead_submitted` | The server confirmed the save | `event_id`, `lead_id`, `form_id`, `capture_method` (never the answers or their codes) | Product analytics, observation-only conversions. The record itself is already in the submission store |
| `qualified_conversion` | The server said the answers cleared the line | `event_id`, `lead_id`, `value` | The conversion every ad platform bids on |
| `application_submitted` | The full application saved, the commitment that opens the SQO on most funnels. Not a form step: each step of a multi-step form fires `form_step_completed`, and in an answers-first form the step that adds the contact details is the lead | `lead_id` | Product analytics. For a lead that qualified on the form, a later conversion, secondary until it has the volume to bid on ([section 5](05-tell-the-platforms.md)) |
| `booking_link_clicked` | A meeting link clicked | `booking`, `location` | Product analytics |

## Which tool does what

| Tool | Its job | Never its job |
|---|---|---|
| The CRM | The record of every lead and opportunity, with the lead ID saved beside its own record IDs | Deciding where a lead came from on its own |
| The submission store (a Google Sheet, or a web-connected database or form system) | Every web submission exactly as it arrived, saved before the CRM gets it, so none is lost and the CRM's count can be checked | Working the leads |
| Call tracking | Every inbound call to the tracking numbers, with the number and the call's length | Deciding which calls are leads (sales does) |
| The tag manager | Routing data layer events to the ad platforms and analytics, with the platform settings in one place | Deciding which leads qualify (the rules file does) |
| Product analytics (PostHog, GA4) | The visits, which pair with the platforms' clicks, and the path: pages, steps, drop-off, experiments, joined to the lead by `identify(lead_id)` | Being the system of record for leads |
| The ad platforms | Their own count of impressions, clicks, spend and the conversions they logged, and learning from the one conversion they're told to bid on | Seeing answers, codes or personal details |
| The reporting layer (PRO) | Tying every system's IDs to one lead ID, laying the systems' counts side by side by date, resolving attribution, tiering the book, reading every source by value | Editing the raw capture |

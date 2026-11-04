# 2 · Tag every link the same way

Every ad's link carries the same parameter names, filled in by the platform's own dynamic values, from one shared vocabulary. Then "meta / instagram" means the same thing in every report, and the platform fills in every name it can. Google can't fill in a campaign's name, so it's typed once per campaign, and the campaign ID never goes stale.

## The parameter set

| Parameter | What it holds | Examples |
|---|---|---|
| `utm_source` | The platform, from the vocabulary | `meta`, `google`, `microsoft`, `linkedin`, `newsletter` |
| `utm_medium` | The first cut of the platform's spend | Meta: `fb`, `ig`, `msg`, `an` (from `{{site_source_name}}`) · Google: `search`, `display`, `video`, `performance_max`, `demand_gen`, `shopping` · LinkedIn: `sponsored_updates`, `sponsored_inmails`, `text_ad`, `dynamic` |
| `utm_campaign` | The campaign name | `lead-gen-revenue-2611` |
| `utm_term` | The keyword on search, the ad set or ad group name elsewhere | |
| `utm_content` | The ad name | |
| `utm_campaignid` | The campaign ID | `120200000000001` |
| `utm_adgroupid` | The ad set or ad group ID | |
| `utm_adid` | The ad ID | |
| `placement`, `network`, `device`, `matchtype` | Platform detail, where it exists | |

The click IDs (`gclid`, `gbraid`, `wbraid`, `fbclid`, `msclkid`, `ttclid`, `li_fat_id`) are added by the platforms themselves. Leave auto-tagging on.

**Names go in the traditional fields, and every ID gets a field of its own.** `utm_campaign`, `utm_term` and `utm_content` hold the names, the way every analytics tool expects. `utm_campaignid`, `utm_adgroupid` and `utm_adid` hold the platform's own IDs, so your reports join to the platform's reports and spend exports one to one. Names get edited, and a campaign renamed in March splits into two lines in any report that groups on the name. IDs don't change. With the ad ID on every lead, a lead resolves to its ad, ad set and campaign even after someone renames all three.

## One vocabulary

`templates/utm_vocabulary.csv` holds every allowed source and medium. A new value goes in the vocabulary before the first link that uses it. The PRO resolver folds old spellings into it ("Facebook" and "fb" become `meta`, "ig" becomes `instagram`, "cpc" on Google becomes `Search`), but the cleanest data is the data that never needed folding.

The medium is the first cut under the source, the first layer you break a channel's spend into when you dig into it. So it has to be a cut the platform's own spend report makes too, and PRO Medium takes the exact value that report uses, so leads join to spend with no translation. On Meta that's where the ad was seen, the Platform column in its report: `facebook`, `instagram`, `messenger`, `audience_network`. On Google it's the Campaign type column: `Search`, `Display`, `Video` (YouTube), `Performance Max`, `Demand Gen`, `Shopping`. On LinkedIn it's the campaign type: `SPONSORED_UPDATES` (Sponsored Content), `SPONSORED_INMAILS` (Message and Conversation Ads), `TEXT_AD`, `DYNAMIC`. The tags on the links stay short and lowercase, and the medium map (`maps/MAP_MEDIUM.csv`) turns each one into its report value. Your own posts on a platform that aren't ads get `content` (a post on Meta that isn't an ad is `meta` / `content`), and email gets `email`. Nothing is ever tagged `organic`. A visit with no tags takes its source from the referrer, and PRO sets its medium to `organic` ([section 6](06-raw-source-and-pro-source.md)). One cost to know: GA4's default channel groups count a medium as paid only when it says cpc, ppc or paid, so Meta, LinkedIn and TikTok ad traffic tagged this way lands outside GA4's paid groups. If your team reads GA4, give it a custom channel group built from the vocabulary, instead of adding "paid" to the tags.

## Meta

Put this in each ad's URL parameters (Ads Manager, the ad's Tracking section):

```
utm_source=meta&utm_medium={{site_source_name}}&utm_campaign={{campaign.name}}&utm_term={{adset.name}}&utm_content={{ad.name}}&utm_campaignid={{campaign.id}}&utm_adgroupid={{adset.id}}&utm_adid={{ad.id}}&placement={{placement}}
```

`{{site_source_name}}` is filled in with where the ad was seen, as `fb`, `ig`, `msg` or `an`, so Meta's subcategories land in `utm_medium` without anyone typing them. The medium map turns them into the Platform values in Meta's spend report: `facebook`, `instagram`, `messenger`, `audience_network`. If Meta adds a placement, add its value to the vocabulary once you've seen it arrive. Check each dynamic parameter's name against the URL parameter builder in Ads Manager before the ads go live, and run one test click (section 8).

## Google Ads

Set this as the account's final URL suffix, so every campaign inherits it:

```
utm_source=google&utm_medium={_channel}&utm_campaign={_campaign}&utm_term={keyword}&utm_campaignid={campaignid}&utm_adgroupid={adgroupid}&utm_adid={creative}&matchtype={matchtype}&network={network}&device={device}&placement={placement}
```

`{campaignid}`, `{adgroupid}`, `{creative}`, `{keyword}`, `{matchtype}`, `{network}`, `{device}` and `{placement}` are ValueTrack parameters, filled in by Google at the click. There's no ValueTrack parameter for the campaign type or the campaign's name, so each campaign gets two custom parameters, named `channel` and `campaign`. In the suffix they're written with an underscore, as `{_channel}` and `{_campaign}`:

| Custom parameter | Set to |
|---|---|
| `channel` | `search`, `display`, `video`, `performance_max`, `demand_gen` or `shopping`. The medium map turns each into the Campaign type value in Google's report (`Search`, `Performance Max` …) |
| `campaign` | The campaign's name in your naming convention |

Parameters that don't apply to a campaign type arrive empty (a Performance Max click has no keyword). That's expected. Google's ads have no names to carry, so `utm_content` stays empty on Google, and the ad's ID arrives in `utm_adid`.

## LinkedIn

LinkedIn's reporting splits spend by campaign type, so that's its medium, in the value LinkedIn's reporting uses:

| Campaign | Where it's seen | `utm_medium` | PRO Medium |
|---|---|---|---|
| Sponsored Content: single image, video, carousel, document, event and thought leader ads | The feed, and the Audience Network when it's on | `sponsored_updates` | `SPONSORED_UPDATES` |
| Message Ads and Conversation Ads | The LinkedIn inbox | `sponsored_inmails` | `SPONSORED_INMAILS` |
| Text Ads | The right rail and top of the page, on desktop | `text_ad` | `TEXT_AD` |
| Dynamic Ads | The right rail, on desktop | `dynamic` | `DYNAMIC` |

These are the campaign types in LinkedIn's reporting API. When the first Campaign Manager export arrives, check its wording, and if it differs, change the PRO Medium column in the medium map to match it.

LinkedIn has no dynamic value for the campaign type, so set `utm_source=linkedin` and the medium as static values in each ad set's URL tracking parameters (Campaign Manager), from the table above. Fill the rest with LinkedIn's dynamic values, in the same places as on the other platforms: the campaign's name and ID in `utm_campaign` and `utm_campaignid`, the ad set's name and ID in `utm_term` and `utm_adgroupid`, and the ad's ID in `utm_adid`. Since LinkedIn's late-2025 rename, its campaign (formerly the campaign group) is the level other platforms call the campaign, and its ad set (formerly the campaign) is the level they call the ad set or ad group.

Two things to set up front:

- **Give the Audience Network its own campaigns,** or leave it off. A Sponsored Content campaign with it on serves in the feed and off LinkedIn at once. LinkedIn's reporting can split that campaign's spend by serving location (on LinkedIn or off it), but its links can't say where each click came from, so its leads can't be split the same way.
- **Message Ads and Conversation Ads don't take LinkedIn's dynamic values,** so their links carry static values, typed in once per campaign.

## Other platforms

Microsoft Advertising, TikTok and the rest use the same parameter names, filled with each platform's own dynamic values. The medium is the platform's own first cut of spend under the source, in the value its report uses. Add the platform's source and medium values to the vocabulary before its first ad runs.

## Links you place yourself

| Link | Tags |
|---|---|
| Newsletter | `utm_source=newsletter&utm_medium=email&utm_campaign=<issue>` |
| Your own post on a platform, not an ad | `utm_source=<platform>&utm_medium=content&utm_campaign=<post or theme>` |
| Partner | `utm_source=partner&utm_medium=<partner id>&utm_campaign=<offer>` |
| QR code, print | `utm_source=<where it's printed>&utm_medium=offline&utm_campaign=<piece>` |

## The rules

- Lowercase, with hyphens or underscores. Never spaces.
- Values from the vocabulary only.
- Nothing personal and no form answers in any address. Not in an ad's link, not in a redirect, not in the thank-you page's address.
- Every new campaign gets one test click before it spends, to check every parameter arrives filled in (section 8).

*Platform settings checked October 28, 2026. Platforms rename things, so check their current help pages when you build.*

#!/usr/bin/env python3
"""Make a synthetic lead book to try the analysis on.  Broad Eye Solutions · Signals and Attribution Blueprint · MIT License

SYNTHETIC DATA. No real company, lead or account is in it. It's built so the tools have something realistic to chew
on: messy tracking (missing parameters, in-app browsers, old spellings), a mix of forms and conversion points (web forms,
chat, an ad platform's lead form through its integration, calls, rep-entered leads, a list), a sub-brand with its own site, and a planted signal (businesses with higher monthly sales become bigger accounts more often).

    python3 analysis/sample/generate_sample.py      writes analysis/sample/leads.csv and accounts.csv

Each record carries `entered_as` (prospect, conversion or lead) and the funnel stages from templates/funnel_stages.csv
(conversion through closed won) as a pair of timestamps, <stage>_first_at and <stage>_last_at, and `stage` is the furthest one it reached. A few leads recycle: they
went quiet after SAL, went back to nurture and came back months later, so their last SAL timestamp is later than the first.
"""
import csv
import math
import os
import random
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(7)
rng_t = random.Random(11)   # stage timestamps only, so adding them leaves the rest of the sample unchanged

UA_IG = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 330.0.0.40.92'
UA_FB = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/470.0.0.40.98]'
UA_SAFARI = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
UA_DESK = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36'

BANDS = ['under_10k', '10k_to_30k', '30k_to_100k', 'over_100k']
YEARS = ['under_1', '1_to_3', '3_to_5', 'over_5']
# chance a lead becomes an account, and the scale of its yearly revenue, by monthly-sales band (the planted signal)
CONVERT = {'under_10k': 0.18, '10k_to_30k': 0.22, '30k_to_100k': 0.27, 'over_100k': 0.30}
SCALE = {'under_10k': 1500, '10k_to_30k': 3500, '30k_to_100k': 11000, 'over_100k': 26000}
# campaign ids are fixed per campaign, the way the platforms issue them; each campaign runs a handful of ads.
# lead-gen-lal-2612 and pmax-all have no row in maps/MAP_CAMPAIGN.csv, so update_maps.py has something to find.
CAMPAIGN_IDS = {'lead-gen-revenue-2611': '120200000000101', 'lead-gen-broad-2611': '120200000000102',
                'lead-gen-lal-2612': '120200000000103', 'search-brand': '21000000001', 'search-funding': '21000000002',
                'pmax-all': '21000000003'}
ADS = {c: [i[:-3] + f'{k:03d}' for k in range(1, 5)] for c, i in CAMPAIGN_IDS.items()}
AD_NAME = lambda ad_id: 'ad-' + ad_id[-3:]   # the ad's name, as the platform fills it into utm_content


def pick(weights):
    r, acc = rng.random(), 0.0
    for k, w in weights:
        acc += w
        if r <= acc:
            return k
    return weights[-1][0]


def lead(i, when):
    kind = pick([('meta', .33), ('google', .30), ('organic', .08), ('newsletter', .04), ('phone', .05), ('chat', .03),
                 ('instant', .04), ('rep', .02), ('import', .02), ('sub', .06), ('test', .01), ('unmapped', .02)])
    r = dict(lead_id=f'L{i:05d}', received_at=when.isoformat(timespec='seconds'), cohort=when.strftime('%Y-%m'),
             brand='EX', form_id='', capture_method='web_form', utm_source='', utm_medium='', utm_campaign='', utm_content='',
             utm_campaignid='', utm_adid='', gclid='', fbclid='', referral_url='', user_agent=UA_DESK, lead_status='new_lead', capture_url='')
    # the channel shapes the mix of businesses it brings in
    if kind == 'meta':
        sales = pick([('under_10k', .42), ('10k_to_30k', .30), ('30k_to_100k', .20), ('over_100k', .08)])
    elif kind == 'google':
        sales = pick([('under_10k', .25), ('10k_to_30k', .30), ('30k_to_100k', .30), ('over_100k', .15)])
    else:
        sales = pick([('under_10k', .30), ('10k_to_30k', .30), ('30k_to_100k', .25), ('over_100k', .15)])
    r['monthly_sales'] = sales
    r['years_in_business'] = pick([('under_1', .2), ('1_to_3', .35), ('3_to_5', .25), ('over_5', .2)])

    if kind == 'meta':
        r['form_id'] = 'WF-0001'
        medium = pick([('fb', .55), ('ig', .38), ('msg', .03), ('an', .04)])
        r['user_agent'] = UA_IG if medium == 'ig' else (UA_FB if medium in ('fb', 'msg') else UA_SAFARI)
        if rng.random() < 0.18:
            pass  # parameters lost on the way (an app or a redirect stripped them): only the form and browser are left
        else:
            r['utm_source'] = pick([('meta', .8), ('facebook', .12), ('fb', .08)])
            r['utm_medium'] = medium if rng.random() < .9 else {'fb': 'Facebook', 'ig': 'Instagram'}.get(medium, medium)
            r['utm_campaign'] = pick([('lead-gen-revenue-2611', .5), ('lead-gen-broad-2611', .35), ('lead-gen-lal-2612', .15)])
            r['utm_campaignid'] = CAMPAIGN_IDS[r['utm_campaign']]
            r['utm_adid'] = rng.choice(ADS[r['utm_campaign']])
            r['utm_content'] = AD_NAME(r['utm_adid'])
            r['fbclid'] = 'IwAR' + ''.join(rng.choice('abcdefXYZ0123') for _ in range(12))
    elif kind == 'google':
        r['form_id'] = 'WF-0002'
        r['gclid'] = 'Cj0K' + ''.join(rng.choice('abcdefXYZ0123') for _ in range(14))
        if rng.random() < 0.9:
            r['utm_source'] = 'google'
            r['utm_medium'] = pick([('search', .6), ('pmax', .3), ('cpc', .1)])
            r['utm_campaign'] = pick([('search-brand', .3), ('search-funding', .5), ('pmax-all', .2)])
            r['utm_campaignid'] = CAMPAIGN_IDS[r['utm_campaign']]
            r['utm_adid'] = rng.choice(ADS[r['utm_campaign']])
            r['utm_content'] = AD_NAME(r['utm_adid'])
    elif kind == 'organic':
        r['form_id'] = 'WF-0003'
        r['referral_url'] = pick([('https://www.google.com/', .6), ('', .3), ('https://www.linkedin.com/', .1)])
    elif kind == 'newsletter':
        r['form_id'] = 'WF-0004'
        r['utm_source'], r['utm_medium'], r['utm_campaign'] = 'newsletter', 'email', 'issue-2611'
    elif kind == 'phone':
        r['form_id'], r['capture_method'] = 'PH-0001', 'phone_call'
    elif kind == 'chat':
        r['form_id'], r['capture_method'] = 'CH-0001', 'chat'
        r['referral_url'] = pick([('https://www.google.com/', .5), ('', .5)])
    elif kind == 'instant':
        r['form_id'], r['capture_method'] = 'LA-0001', 'api'
        r['user_agent'] = UA_IG if rng.random() < .4 else UA_FB
    elif kind == 'rep':
        r['form_id'], r['capture_method'] = '', 'manual'
    elif kind == 'import':
        r['form_id'], r['capture_method'], r['utm_campaign'] = '', 'import', 'legacy-crm'
    elif kind == 'sub':
        # a sub-brand with its own site and form: the first cut, Brand against Non-Brand, keeps it apart
        r['brand'], r['form_id'] = 'SB', 'WF-0101'
        if rng.random() < 0.6:
            r['utm_source'], r['utm_medium'], r['utm_campaign'] = 'google', 'search', 'sub-brand-search'
            r['gclid'] = 'Cj0K' + ''.join(rng.choice('abcdefXYZ0123') for _ in range(14))
        else:
            r['referral_url'] = 'https://www.google.com/'
    elif kind == 'test':
        r['form_id'], r['utm_source'], r['utm_campaign'] = 'WF-0003', 'test', 'test'
    else:
        r['form_id'], r['utm_source'], r['utm_medium'] = 'WF-0003', 'partnerx', 'referral'
    if r['capture_method'] in ('web_form', 'chat'):
        page = {'WF-0001': '/apply/', 'WF-0002': '/get-started/', 'WF-0003': '/contact/', 'WF-0004': '/newsletter/'}.get(r['form_id'], '/pricing/')
        site = 'https://example-sister.com' if r['brand'] == 'SB' else 'https://example.com'
        page = '/quote/' if r['form_id'] == 'WF-0101' else page
        # the capture URL keeps the page's own tracking parameters (the ad's, on the page the ad sent them to)
        tags = '&'.join(f'{k}={r[k]}' for k in ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_campaignid', 'utm_adid', 'gclid', 'fbclid') if r.get(k))
        # a small share of web leads lose the capture URL on the way into the CRM, the gap QA is there to catch
        if rng.random() > 0.015:
            r['capture_url'] = site + page + ('?' + tags if tags else '')
            # some forms store only the page address: the tag fields arrive empty, and PRO reads the capture URL
            if tags and rng.random() < 0.25:
                for k in ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_campaignid', 'utm_adid', 'gclid', 'fbclid'):
                    r[k] = ''
    if rng.random() < 0.02:
        r['lead_status'] = 'duplicate'
    elif rng.random() < 0.01:
        r['lead_status'] = 'out_of_scope'     # a job seeker or an existing customer: labeled, never deleted
    return r


def is_test(r):
    """A test record, read the way the resolver reads it: by its tag field, or by the tag in the capture URL when the
    form stored only the page address."""
    return r['utm_source'] == 'test' or 'utm_source=test' in r.get('capture_url', '')


STAGES = ['conversion', 'prospect', 'lead', 'mql', 'sal', 'sql', 'sqo', 'rqo', 'cw']
MQL_BANDS = ('10k_to_30k', '30k_to_100k', 'over_100k')   # the sample's MQL rule: monthly sales of $10,000 and up


def stage_times(r):
    """The funnel stages as first/last timestamps, from how far the lead got (the old coarse stage: lead, contacted,
    application, funded). A skipped stage stays blank, as docs/01 says."""
    t0 = datetime.fromisoformat(r['received_at'])
    # every record enters at a named stage (docs/01): a list import as a prospect, the website as a conversion, and a call,
    # a rep's entry or a platform's lead form through its integration straight as a lead. None of those is a web conversion.
    cm = r['capture_method']
    entered = 'prospect' if cm == 'import' else 'conversion' if cm in ('web_form', 'chat') else 'lead'
    r['entered_as'] = entered
    got = {entered: t0} if entered != 'lead' else {}
    reached = r['stage']
    excluded = r['lead_status'] in ('duplicate', 'out_of_scope') or is_test(r)
    worked = reached in ('contacted', 'application', 'funded')
    if not excluded and (entered != 'prospect' or worked):   # a prospect becomes a lead only when it shows interest
        t_lead = t0 + timedelta(days=rng_t.uniform(1, 40)) if entered == 'prospect' else t0
        got['lead'] = t_lead
        if r['monthly_sales'] in MQL_BANDS:
            got['mql'] = t_lead                               # set by the qualifying rules; below them, a lead can still
                                                              # reach sales (a call, a chat) and skips MQL
        if worked:
            got['sal'] = t_lead + timedelta(hours=rng_t.uniform(0.2, 30))
            if reached in ('application', 'funded') or rng_t.random() < 0.35:
                got['sql'] = got['sal'] + timedelta(days=rng_t.uniform(0, 6))
            if reached in ('application', 'funded'):
                got['sqo'] = got['sql'] + timedelta(days=rng_t.uniform(1, 10))
            if reached == 'funded':
                got['rqo'] = got['sqo'] + timedelta(days=rng_t.uniform(1, 7))
                got['cw'] = got['rqo'] + timedelta(days=rng_t.uniform(0, 4))
    last = dict(got)
    if 'sal' in got and 'sqo' not in got and rng_t.random() < 0.12:   # recycled to nurture, back months later
        last['sal'] = got['sal'] + timedelta(days=rng_t.uniform(30, 120))
    for k in STAGES:
        r[f'{k}_first_at'] = got[k].isoformat(timespec='seconds') if k in got else ''
        r[f'{k}_last_at'] = last[k].isoformat(timespec='seconds') if k in last else ''
    r['stage'] = [k for k in STAGES if k in got][-1] if got else ''


def main():
    start = datetime(2026, 1, 1)
    leads, accounts = [], []
    for i in range(1, 3601):
        when = start + timedelta(minutes=rng.randint(0, 60 * 24 * 300))
        r = lead(i, when)
        leads.append(r)
        if r['lead_status'] in ('duplicate', 'out_of_scope') or is_test(r):
            r['stage'] = 'lead'
            continue
        band = r['monthly_sales']
        p = CONVERT[band] * (0.7 if r['years_in_business'] == 'under_1' else 1.0)
        # how far each lead got: contacted, application, funded (an account). Calls and referrals reach a person more often.
        reach = {'phone_call': 0.75, 'manual': 0.85, 'chat': 0.65, 'api': 0.40}.get(r['capture_method'], 0.55)
        r['stage'] = 'lead'
        if rng.random() < reach:
            r['stage'] = 'contacted'
            if rng.random() < 0.5:
                r['stage'] = 'application'
        if rng.random() < p and r['stage'] == 'application' or rng.random() < p * 0.6:
            r['stage'] = 'funded'
            rev = SCALE[band] * math.exp(rng.gauss(0, 1.1))
            accounts.append(dict(account_id='A' + r['lead_id'][1:], lead_id=r['lead_id'], revenue=round(rev, 2)))
    for r in leads:
        stage_times(r)
    leads.sort(key=lambda r: r['received_at'])
    with open(os.path.join(HERE, 'leads.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(leads[0].keys()))
        w.writeheader()
        w.writerows(leads)
    with open(os.path.join(HERE, 'accounts.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['account_id', 'lead_id', 'revenue'])
        w.writeheader()
        w.writerows(accounts)
    print(f'synthetic sample: {len(leads)} leads, {len(accounts)} accounts -> {HERE}')


if __name__ == '__main__':
    main()

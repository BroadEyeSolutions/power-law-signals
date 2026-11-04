#!/usr/bin/env python3
"""Resolve each lead's PRO fields from its raw capture.  Broad Eye Solutions · Signals and Attribution Blueprint · MIT License

Three layers, and only the last one is reported:

    raw     what arrived, exactly as the CRM and the form stored it. Never edited, by this or by anything else.
    maps    keyed tables in maps/ that translate raw values into the reporting vocabulary (MAP_BRAND, MAP_CAPTURE,
            MAP_FORM, MAP_SOURCE, MAP_MEDIUM, MAP_CAMPAIGN). People review and edit the maps, never the raw data.
    PRO     the fields below, written beside the raw columns, each with a *_basis column naming the evidence that
            decided it. A report reads PRO. Anyone checking a number can follow it back to the raw value.

    pro_brand             the first cut        Brand (the main brand) or Non-Brand (sub-brands, other brands and sites
                                               the business launched or bought), from the brand hard-coded on the form,
                                               then the capture URL's domain (MAP_BRAND)
    pro_capture_group     Web or Non-Web       a capture URL means the website. If every web and chat submission writes
                                               one, a lead without it didn't come from the site
    pro_capture_method    how it got into      Web Form, Live Chat, Inbound Call, Referral, Third Party API,
                          the CRM              List, Manual Entry (MAP_CAPTURE, from the record or the form's row)
    pro_conversion_point  which door           the form ID (or tracking number, chat, partner): the specific conversion
                                               point, named in MAP_FORM
    pro_class             did an investment    Investments (ads, sponsorships, trade shows, referral partners), Inbound
                          bring it             (what arrived with none), zNAA, from the category (rules: category_class)
    pro_category          kind of investment   Advertising, Affiliate, Organic, Direct Sales, Legacy, zNAA
    pro_source            platform or channel  meta, google, microsoft ... (MAP_SOURCE)
    pro_medium            where on it          the platform's own report value: meta facebook, instagram ...  ·  google Search, Performance Max ... (MAP_MEDIUM)
    pro_campaign          the campaign         by its id, then its name (MAP_CAMPAIGN), with campaign_key

Read them in that order: tests, spam, duplicates and out-of-scope leads are labeled first, then Brand, then the capture
group and method, then class, category, source, medium and campaign.

Source, in order: utm_source (through MAP_SOURCE) -> click id -> the form's built-for source (MAP_FORM)
                  -> in-app browser -> referrer -> zNAA
Medium, in order: utm_medium (through MAP_MEDIUM, for that source) -> in-app browser -> the form's built-for medium
                  -> referrer -> zNAA
Cookieless by design. Every web submission carries its capture URL and user agent, whatever the visitor's tracking
choices, and on the page an ad sent them to the capture URL still holds the ad's parameters. Tags carried by cookies or
browser storage are the backup, for visitors who browsed to another page first. Each tracking value is read from the
lead's own (stored) field first, because it's there when tracking was allowed, then from the capture URL's query
string. A value found in the capture URL gets a basis starting capture_url:.

A raw value the maps don't know is kept as it arrived and flagged (*_unmapped), never guessed. update_maps.py lists
those values and appends them to the maps as unverified rows for someone to review.

This is a starter. It runs on one CSV of leads. The full version (ABPRO_) runs the same idea across the CRM, the web
forms and the ad platforms' spend exports, with the account and revenue maps that tie a lead to what it became.

Usage:
    python3 analysis/resolve_sources.py leads.csv --out leads_resolved.csv [--maps maps] \
        [--rules analysis/rules/pro_rules.example.json]
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from urllib.parse import urlsplit, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NA = 'zNAA'

IN_APP = [
    ('instagram', re.compile(r'Instagram', re.I)),
    ('messenger', re.compile(r'FBAN/Messenger|MessengerForiOS|\bOrca-Android', re.I)),
    ('facebook', re.compile(r'FBAN|FBAV|FB_IAB|FBIOS', re.I)),
    ('linkedin', re.compile(r'LinkedInApp', re.I)),
    ('tiktok', re.compile(r'musical_ly|Bytedance|TikTok', re.I)),
    ('snapchat', re.compile(r'Snapchat', re.I)),
    ('pinterest', re.compile(r'Pinterest', re.I)),
]

PRO_COLS = ['pro_brand', 'pro_capture_group', 'pro_capture_method', 'pro_conversion_point', 'pro_class', 'pro_category',
            'pro_source', 'pro_medium', 'pro_campaign', 'campaign_key',
            'brand_basis', 'capture_group_basis', 'capture_method_basis', 'conversion_point_basis', 'class_basis', 'category_basis',
            'source_basis', 'medium_basis', 'campaign_basis']


TAG_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_campaignid', 'utm_adgroupid', 'utm_adid',
            'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid', 'ttclid', 'li_fat_id']


def url_tags(url):
    """The tracking parameters in a capture URL. On the page an ad sent the visitor to, they're there even when the
    visitor opted out of tracking, and many forms store only the page address, so this is evidence in its own right."""
    try:
        q = parse_qs(urlsplit((url or '').strip()).query)
    except ValueError:
        return {}
    return {k: q[k][0].strip() for k in TAG_KEYS if q.get(k) and q[k][0].strip()}


DEFAULT_CLASS = {'Advertising': 'Investments', 'Affiliate': 'Investments', 'Organic': 'Inbound', 'Direct Sales': 'Inbound',
                 'Legacy': 'Inbound'}


def host_of(url):
    try:
        return urlsplit((url or '').strip()).hostname or ''
    except ValueError:
        return ''


def norm(v):
    return re.sub(r'[\s\-]+', '_', (v or '').strip().lower())


def in_app_browser(ua):
    for name, rx in IN_APP:
        if rx.search(ua or ''):
            return name
    return ''


def _read(path):
    if not path or not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def effective(row, field, override='override'):
    """A map row's value: the override if someone set one, else the mapped value. Blank means not mapped yet."""
    return ((row.get(override) or '').strip() or (row.get(field) or '').strip()) or None


def load_maps(folder=os.path.join(ROOT, 'maps')):
    """Read the map files into lookups keyed the way the resolver asks for them."""
    m = {'brand': {}, 'source': {}, 'medium': {}, 'capture': {}, 'form': {}, 'campaign': {}, 'campaign_name': {}}
    for r in _read(os.path.join(folder, 'MAP_BRAND.csv')):
        m['brand'][(norm(r['key_type']), norm(r['raw_value']))] = (effective(r, 'pro_brand'), (r.get('brand_name') or '').strip())
    for r in _read(os.path.join(folder, 'MAP_SOURCE.csv')):
        m['source'][norm(r['raw_value'])] = effective(r, 'pro_source')
    for r in _read(os.path.join(folder, 'MAP_MEDIUM.csv')):
        m['medium'][(norm(r['pro_source']), norm(r['raw_value']))] = effective(r, 'pro_medium')
    for r in _read(os.path.join(folder, 'MAP_CAPTURE.csv')):
        m['capture'][norm(r['raw_value'])] = (effective(r, 'pro_capture_method'), (r.get('capture_group') or '').strip())
    for r in _read(os.path.join(folder, 'MAP_FORM.csv')):
        if r.get('form_id'):
            m['form'][r['form_id'].strip().upper()] = r
    for r in _read(os.path.join(folder, 'MAP_CAMPAIGN.csv')):
        plat = norm(r.get('platform'))
        if (r.get('campaign_id') or '').strip():
            m['campaign'][(plat, r['campaign_id'].strip())] = r
        if (r.get('campaign_name') or '').strip():
            m['campaign_name'][(plat, norm(r['campaign_name']))] = r
    return m


def resolve(row, rules, maps):
    """Return the PRO fields and their bases for one lead (a dict of raw columns). The row itself isn't changed."""
    url_t = url_tags(row.get('capture_url') or row.get('form_page'))
    for ex in rules.get('exclude', []):
        if norm(row.get(ex['field']) or url_t.get(ex['field'])) == ex['equals']:
            lab = ex['label']
            out = {k: lab for k in PRO_COLS if k.startswith('pro_')}
            out.update({k: 'exclude:' + ex['field'] for k in PRO_COLS if k.endswith('_basis')})
            out['campaign_key'] = ''
            return out

    out = {}
    form = maps['form'].get((row.get('form_id') or '').strip().upper())
    from_url = url_tags(row.get('capture_url') or row.get('form_page'))

    def tag(k):
        """A tracking value and where it came from: the lead's own field first, then the capture URL."""
        v = (row.get(k) or '').strip()
        if v:
            return v, k
        if from_url.get(k):
            return from_url[k], 'capture_url:' + k
        return '', ''

    # brand, the first cut: the brand hard-coded on the form, then the capture URL's domain, then the form's row
    host = ''
    try:
        host = (urlsplit((row.get('capture_url') or row.get('form_page') or '').strip()).hostname or '').lower()
        host = host[4:] if host.startswith('www.') else host
    except ValueError:
        pass
    raw_brand = norm(row.get('brand'))
    hit_brand, bb = None, 'none'
    if raw_brand:
        hit_brand, bb = maps['brand'].get(('brand_code', raw_brand)), 'brand'
    if not hit_brand and host:
        hit_brand, bb = maps['brand'].get(('domain', norm(host))), 'capture_url:domain'
    if not hit_brand and form and form.get('brand'):
        hit_brand, bb = maps['brand'].get(('brand_code', norm(form['brand']))), 'form_map:' + form['form_id']
    if hit_brand and hit_brand[0]:
        out['pro_brand'], out['brand_basis'] = hit_brand[0], bb
    elif raw_brand or host:
        out['pro_brand'], out['brand_basis'] = NA, 'brand_unmapped'
    else:
        out['pro_brand'], out['brand_basis'] = NA, 'none'

    # capture method: the record's own (hard-coded) capture method, else the form's row, through MAP_CAPTURE
    raw_cm, cb = norm(row.get('capture_method')), 'capture_method'
    if not raw_cm and form:
        raw_cm, cb = norm(form.get('capture_method')), 'form_map:' + form['form_id']
    method, group = maps['capture'].get(raw_cm, (None, '')) if raw_cm else (None, '')
    if method:
        out['pro_capture_method'], out['capture_method_basis'] = method, cb
    elif raw_cm:
        out['pro_capture_method'], out['capture_method_basis'] = raw_cm, 'capture_method_unmapped'
    else:
        out['pro_capture_method'], out['capture_method_basis'] = NA, 'none'

    # capture group, Web or Non-Web: what's missing is evidence too
    url = (row.get('capture_url') or row.get('form_page') or '').strip()
    if url:
        out['pro_capture_group'], out['capture_group_basis'] = 'Web', 'capture_url'
    elif group == 'Web':
        # the record says web form or chat, but the URL is missing: a capture gap to fix at the form
        out['pro_capture_group'], out['capture_group_basis'] = 'Web', 'capture_method_no_url'
    else:
        out['pro_capture_group'], out['capture_group_basis'] = 'Non-Web', 'no_capture_url'

    # conversion point: the specific door, by its ID in the form map
    fid = (row.get('form_id') or '').strip().upper()
    if form:
        out['pro_conversion_point'], out['conversion_point_basis'] = form['form_id'], 'form_id'
    elif fid:
        out['pro_conversion_point'], out['conversion_point_basis'] = fid, 'form_id_unmapped'
    else:
        out['pro_conversion_point'], out['conversion_point_basis'] = NA, 'none'

    app = norm(row.get('in_app_browser')) or in_app_browser(row.get('user_agent'))
    app_rule = rules.get('in_app_browsers', {}).get(app) if app else None
    ref_host = (row.get('referrer_host') or host_of(row.get('referral_url'))).lower()   # the full referral URL, or an older host-only column
    ref_rule = next((r for r in rules.get('referrers', []) if r['host_contains'] in ref_host), None) if ref_host else None

    # source
    src, sb = None, 'none'
    v, where = tag('utm_source')
    raw_src = norm(v)
    if raw_src:
        src = maps['source'].get(raw_src)
        sb = where if src else 'utm_source_unmapped'
        src = src or raw_src
    if not src:
        for key, platform in rules.get('click_ids', {}).items():
            v, where = tag(key)
            if v:
                src, sb = platform, ('click_id:' if where == key else 'capture_url:click_id:') + key
                break
    if not src and form and form.get('built_for_source'):
        src, sb = norm(form['built_for_source']), 'form_default:' + form['form_id']
    if not src and app_rule:
        src, sb = app_rule['source'], 'in_app:' + app
    if not src and ref_rule:
        src, sb = ref_rule['source'], 'referrer:' + ref_rule['host_contains']
    if not src and out.get('pro_capture_group') == 'Web':
        # a web lead with no tags, no click ID, no form default, no browser hint and no referrer: the website itself is
        # the source (or the site's own domain, set in the rules), grouped by its form ID. The medium stays zNAA.
        src, sb = rules.get('website_source', 'website'), 'website:' + (out.get('pro_conversion_point') or NA)
    out['pro_source'] = src or NA
    out['source_basis'] = sb

    # medium, read in the source's own vocabulary so every platform's subcategories stay consistent
    med, mb = None, 'none'
    v, where = tag('utm_medium')
    raw_med = norm(v)
    if raw_med and src:
        med = maps['medium'].get((src, raw_med))
        if med:
            mb = where
    if not med and app_rule and app_rule.get('medium') and app_rule['source'] == src:
        med, mb = app_rule['medium'], 'in_app:' + app
    if not med and form and form.get('built_for_medium') and norm(form.get('built_for_source')) == src:
        bfm = form['built_for_medium'].strip()      # read through the medium map, so it lands in the platform's report wording
        med, mb = maps['medium'].get((src, norm(bfm))) or bfm, 'form_default:' + form['form_id']
    if not med and ref_rule and ref_rule['source'] == src:
        med, mb = ref_rule['medium'], 'referrer:' + ref_rule['host_contains']
    if not med and raw_med:
        med, mb = raw_med, 'utm_medium_unmapped'
    out['pro_medium'] = med or NA
    out['medium_basis'] = mb

    # category
    ad_sources = set(rules.get('advertising_sources', []))
    method = out['pro_capture_method']
    if method == 'List':
        cat, catb = 'Legacy', 'capture_method'
    elif method == 'Manual Entry':
        cat, catb = 'Direct Sales', 'capture_method'      # a rep created it: kept apart, because it converts differently
    elif src == 'partner' or method == 'Referral':
        cat, catb = 'Affiliate', 'source' if src == 'partner' else 'capture_method'
    elif sb.startswith(('utm_source', 'click_id', 'capture_url')) and src in ad_sources and med not in ('organic', 'content'):
        cat, catb = 'Advertising', 'source'
    elif src == 'newsletter' or (med in ('organic', 'content') and sb.startswith(('utm_source', 'capture_url'))):
        cat, catb = 'Organic', 'source' if src == 'newsletter' else 'medium'
    elif sb.startswith(('form_default', 'in_app')) and form and form.get('built_for_category'):
        cat, catb = form['built_for_category'], 'form_default:' + form['form_id']
    elif sb.startswith('referrer'):
        cat, catb = 'Organic', 'referrer'
    else:
        cat, catb = NA, 'none'
    out['pro_category'] = cat
    out['category_basis'] = catb
    # class: did an investment bring it? From the category, through the rules file, so a business can move one
    classes = rules.get('category_class', {})
    out['pro_class'] = classes.get(cat, cat if cat == NA or cat not in DEFAULT_CLASS else DEFAULT_CLASS[cat])
    out['class_basis'] = 'category:' + cat

    # campaign: the id first (names get edited, ids don't), then the name, through MAP_CAMPAIGN
    cid, cid_from = tag('utm_campaignid')
    name, name_from = tag('utm_campaign')
    pre = lambda where: 'capture_url:' if where.startswith('capture_url') else ''
    hit, how = None, ''
    if cid:
        hit, how = maps['campaign'].get((src or '', cid)), pre(cid_from) + 'campaign_map:utm_campaignid'
    if not hit and name:
        hit, how = maps['campaign_name'].get((src or '', norm(name))), pre(name_from) + 'campaign_map:utm_campaign'
    if hit:
        out['pro_campaign'] = effective(hit, 'pro_campaign') or hit.get('campaign_name') or cid
        out['campaign_key'], out['campaign_basis'] = hit['campaign_key'], how
    elif name:
        out['pro_campaign'], out['campaign_key'], out['campaign_basis'] = name, '', 'utm_campaign_unmapped'
    elif cid:
        out['pro_campaign'], out['campaign_key'], out['campaign_basis'] = cid, '', 'utm_campaignid_unmapped'
    else:
        out['pro_campaign'], out['campaign_key'], out['campaign_basis'] = NA, '', 'none'
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('leads')
    ap.add_argument('--out', required=True)
    ap.add_argument('--maps', default=os.path.join(ROOT, 'maps'))
    ap.add_argument('--rules', default=os.path.join(HERE, 'rules', 'pro_rules.example.json'))
    a = ap.parse_args(argv)
    rules = json.load(open(a.rules, encoding='utf-8'))
    maps = load_maps(a.maps)
    with open(a.leads, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit('no leads in ' + a.leads)
    clash = [c for c in PRO_COLS if c in rows[0]]
    if clash:
        sys.exit('the leads file already has PRO columns (%s). Resolve from the raw export, not a resolved file.' % ', '.join(clash))
    cols = list(rows[0].keys()) + PRO_COLS
    bases, groups, unmapped = Counter(), Counter(), Counter()
    resolved = []
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            p = resolve(r, rules, maps)
            w.writerow({**r, **p})
            resolved.append(p)
            bases[p['source_basis'].split(':')[0]] += 1
            groups[(p['pro_category'], p['pro_source'], p['pro_medium'])] += 1
            for k in ('brand_basis', 'capture_method_basis', 'conversion_point_basis', 'source_basis', 'medium_basis', 'campaign_basis'):
                if p[k].endswith('_unmapped'):
                    unmapped[p[k]] += 1
    print(f'{len(rows)} leads resolved -> {a.out}')
    labels = {ex['label'] for ex in rules.get('exclude', [])}
    live = [(r, p) for r, p in zip(rows, resolved) if p['pro_category'] not in labels]
    if live:
        print('resolved at each level (tests, spam, duplicates and out-of-scope leads left out):')
        for lab, key in (('source', 'pro_source'), ('medium', 'pro_medium'), ('campaign', 'pro_campaign')):
            n = sum(1 for _, p in live if p[key] not in (NA, ''))
            print(f'  {lab:9s} {n / len(live):6.1%}')
        n = sum(1 for r, _ in live if (r.get('utm_adid') or '').strip() or url_tags(r.get('capture_url')).get('utm_adid'))
        print(f'  {"ad id":9s} {n / len(live):6.1%}   (utm_adid carries the ad ID, in its field or the capture URL)')
        web = Counter((p['pro_capture_group'], p['capture_group_basis']) for _, p in live)
        print('capture group:', ', '.join(f'{k[0]} ({k[1]}) {v}' for k, v in web.most_common()))
        print('brand:', ', '.join(f'{k} {v}' for k, v in Counter(p['pro_brand'] for _, p in live).most_common()))
    print('source decided by:', ', '.join(f'{k} {v}' for k, v in bases.most_common()))
    if unmapped:
        print('values the maps don\'t know yet (run update_maps.py):', ', '.join(f'{k} {v}' for k, v in unmapped.most_common()))
    for (c, s, m), n in sorted(groups.items(), key=lambda kv: -kv[1])[:15]:
        print(f'  {n:6d}  {c} / {s} / {m}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Find raw values the maps don't know yet, and append them for review.  Broad Eye Solutions · Signals and Attribution Blueprint · MIT License

New raw values arrive every month: a new campaign, a new spelling of a source, a form that went live without a row.
This script reads the raw leads, finds every value with no row in its map, and appends one row per value with
status "unverified" and the mapped value left blank. Someone who knows the accounts fills in the value and sets the
status to "verified". Until then the resolver keeps the raw value and flags it (*_unmapped), so nothing is guessed.

Rules it keeps:
    - It only appends. Existing rows, values, overrides and notes are never changed or reordered.
    - Keys are minted once and never reused (campaign_key C00001, C00002 ...).
    - It reads the raw export. It never writes to the CRM, the form data or any system of record.
    - With --write it copies the current maps to maps/_backup/<time>/ first, and prints what it added.

Usage:
    python3 analysis/update_maps.py leads.csv [--maps maps]            # show what would be added
    python3 analysis/update_maps.py leads.csv [--maps maps] --write    # back up, then append
Tests, spam, duplicates and out-of-scope leads (the exclude list in the rules file) are skipped.
"""
import argparse
import csv
import json
import os
import shutil
import sys
from collections import Counter, OrderedDict
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from analysis.resolve_sources import load_maps, norm, url_tags, TAG_KEYS  # noqa: E402
from urllib.parse import urlsplit  # noqa: E402

FILES = ['MAP_BRAND.csv', 'MAP_SOURCE.csv', 'MAP_MEDIUM.csv', 'MAP_CAPTURE.csv', 'MAP_FORM.csv', 'MAP_CAMPAIGN.csv']


def _header(path):
    with open(path, newline='', encoding='utf-8') as f:
        return next(csv.reader(f))


def _keys(path, col):
    with open(path, newline='', encoding='utf-8') as f:
        return [r[col] for r in csv.DictReader(f)]


def find_new(rows, maps, folder, today=None, rules=None):
    """Return {map file: [new rows]} for every raw value with no row yet. Counts how often each was seen.
    Rows the rules exclude (tests, spam, duplicates, out of scope) are skipped: their values don't belong in the vocabulary."""
    today = today or date.today().isoformat()
    excl = (rules or {}).get('exclude', [])
    seen = {f: OrderedDict() for f in FILES}
    count = {f: Counter() for f in FILES}

    def add(f, key, row):
        if key not in seen[f]:
            seen[f][key] = row
        count[f][key] += 1

    for r in rows:
        u = url_tags(r.get('capture_url') or r.get('form_page'))
        if any(norm(r.get(ex['field']) or u.get(ex['field'])) == ex['equals'] for ex in excl):
            continue
        # the lead's own tracking fields, filled in from the capture URL where they're empty
        url = r.get('capture_url') or r.get('form_page') or ''
        r = {**url_tags(url), **{k: v for k, v in r.items() if v}}
        b = norm(r.get('brand'))
        if b and ('brand_code', b) not in maps['brand']:
            add('MAP_BRAND.csv', ('brand_code', b), {'key_type': 'brand_code', 'raw_value': b})
        try:
            host = (urlsplit(url.strip()).hostname or '').lower()
        except ValueError:
            host = ''
        host = host[4:] if host.startswith('www.') else host
        if host and ('domain', norm(host)) not in maps['brand']:
            add('MAP_BRAND.csv', ('domain', norm(host)), {'key_type': 'domain', 'raw_value': host})
        src_raw = norm(r.get('utm_source'))
        src = maps['source'].get(src_raw) if src_raw else None
        if src_raw and src_raw not in maps['source']:
            add('MAP_SOURCE.csv', src_raw, {'raw_value': src_raw})
        med_raw = norm(r.get('utm_medium'))
        if med_raw and src and (src, med_raw) not in maps['medium']:
            add('MAP_MEDIUM.csv', (src, med_raw), {'pro_source': src, 'raw_value': med_raw})
        cm = norm(r.get('capture_method'))
        if cm and cm not in maps['capture']:
            add('MAP_CAPTURE.csv', cm, {'raw_value': cm})
        fid = (r.get('form_id') or '').strip().upper()
        if fid and fid not in maps['form']:
            add('MAP_FORM.csv', fid, {'form_id': fid, 'capture_method': cm, 'status': 'unregistered'})
        cid, name = (r.get('utm_campaignid') or '').strip(), (r.get('utm_campaign') or '').strip()
        if src and (cid or name):
            known = (cid and (src, cid) in maps['campaign']) or (not cid and (src, norm(name)) in maps['campaign_name'])
            if not known:
                key = (src, cid) if cid else (src, '', norm(name))
                add('MAP_CAMPAIGN.csv', key, {'platform': src, 'campaign_id': cid, 'campaign_name': name})

    out = {}
    for f in FILES:
        if not seen[f]:
            continue
        new = []
        for key, row in seen[f].items():
            row = dict(row)
            row.setdefault('status', 'unverified')
            row['first_seen'] = today
            row['notes'] = f'Seen on {count[f][key]} lead(s). Added by update_maps.py for review'
            new.append(row)
        if f == 'MAP_CAMPAIGN.csv':
            path = os.path.join(folder, f)
            taken = [k for k in _keys(path, 'campaign_key') if k[1:].isdigit()] if os.path.exists(path) else []
            nxt = max([int(k[1:]) for k in taken] or [0]) + 1
            for row in new:
                row['campaign_key'] = f'C{nxt:05d}'
                nxt += 1
        out[f] = new
    return out


def coverage(rows, folder, rules=None):
    """Share of leads whose raw value has a verified row in each map. A falling number means new values are
    arriving faster than anyone is reviewing them."""
    def verified(f, *cols, ok=('verified',)):
        path = os.path.join(folder, f)
        if not os.path.exists(path):
            return set()
        with open(path, newline='', encoding='utf-8') as fh:
            return {tuple(norm(r[c]) for c in cols) for r in csv.DictReader(fh) if (r.get('status') or '').strip() in ok}
    src_ok = verified('MAP_SOURCE.csv', 'raw_value')
    cap_ok = verified('MAP_CAPTURE.csv', 'raw_value')
    form_ok = verified('MAP_FORM.csv', 'form_id', ok=('live', 'verified', 'retired'))   # the form map's statuses
    camp_ok = verified('MAP_CAMPAIGN.csv', 'platform', 'campaign_id')
    src_map = load_maps(folder)['source']
    excl = (rules or {}).get('exclude', [])
    hit, seen = Counter(), Counter()
    for r in rows:
        u = url_tags(r.get('capture_url') or r.get('form_page'))
        if any(norm(r.get(ex['field']) or u.get(ex['field'])) == ex['equals'] for ex in excl):
            continue
        t = {**u, **{k: v for k, v in r.items() if v}}
        s = norm(t.get('utm_source'))
        if s:
            seen['source'] += 1; hit['source'] += (s,) in src_ok
        cm = norm(t.get('capture_method'))
        if cm:
            seen['capture'] += 1; hit['capture'] += (cm,) in cap_ok
        fid = norm(t.get('form_id'))
        if fid:
            seen['form'] += 1; hit['form'] += (fid,) in form_ok
        cid = (t.get('utm_campaignid') or '').strip()
        if cid and s:
            seen['campaign'] += 1; hit['campaign'] += (norm(src_map.get(s) or s), norm(cid)) in camp_ok
    return {k: (hit[k], seen[k]) for k in seen}


def append(folder, new):
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = os.path.join(folder, '_backup', stamp)
    os.makedirs(backup, exist_ok=True)
    for f in FILES:
        if os.path.exists(os.path.join(folder, f)):
            shutil.copy2(os.path.join(folder, f), os.path.join(backup, f))
    for f, rows in new.items():
        path = os.path.join(folder, f)
        cols = _header(path)
        with open(path, 'a', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
            for r in rows:
                w.writerow({c: r.get(c, '') for c in cols})
    return backup


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('leads')
    ap.add_argument('--maps', default=os.path.join(ROOT, 'maps'))
    ap.add_argument('--rules', default=os.path.join(HERE, 'rules', 'pro_rules.example.json'))
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    with open(a.leads, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    rules = json.load(open(a.rules, encoding='utf-8'))
    cov = coverage(rows, a.maps, rules)
    print('coverage (leads whose raw value has a verified row):', ', '.join(f'{k} {h / n:.1%}' for k, (h, n) in cov.items() if n))
    new = find_new(rows, load_maps(a.maps), a.maps, rules=rules)
    if not new:
        print('every raw value already has a row in its map')
        return
    for f, rs in new.items():
        print(f'{f}: {len(rs)} new value(s)')
        for r in rs[:12]:
            print('   ', ', '.join(f'{k}={v}' for k, v in r.items() if k not in ('notes', 'first_seen', 'status') and v))
        if len(rs) > 12:
            print(f'    ... and {len(rs) - 12} more')
    if a.write:
        backup = append(a.maps, new)
        print(f'appended as unverified. The maps before this run are in {backup}')
    else:
        print('nothing written. Run again with --write to back up the maps and append these rows.')


if __name__ == '__main__':
    main()

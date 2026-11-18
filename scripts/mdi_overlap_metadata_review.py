"""Read-only review audit of saved overlap metadata; no selection, network or maps.

Outputs counts only. This does not certify whole-footprint mu or link any patch
with a full-disk source by nominal time. QUALITY x INTERVAL is full-disk only.
Run with explicit --repo and --out; refuse an existing output folder.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

from mdi_overlap_kernels import parse_quality32


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(p):
    with (gzip.open(p, 'rt', newline='') if p.suffix == '.gz' else p.open(newline='')) as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def interval_class(raw):
    try:
        v = Decimal(raw)
    except (InvalidOperation, TypeError):
        return 'missing' if raw in ('', 'MISSING', 'NaN', 'nan', None) else 'other'
    if not v.is_finite():
        return 'missing'
    return {Decimal(30): '30', Decimal(60): '60', Decimal(300): '300'}.get(v, 'other')


def finite(raw):
    try:
        v = float(raw)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def write_csv(p, fields, data):
    with p.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit('Refusing to overwrite the output folder')
    root = args.repo.resolve()
    base = root/'data/sharp/metadata_inventory_mdi/schema_20261116_http_ac06138'
    analysis = root/'results/MDI_SMARP_INVENTORY/schema_20261116_http_ac06138/overlap_only/198785bb3002'
    registry = base.parent/'INVENTORY_REGISTRY.json'
    original_registry = sha(registry)
    started = time.monotonic()
    source_meta = json.loads((analysis/'META.json').read_text())
    inputs = {}
    saved = {}
    for profile in ('smarp_overlap','hmi_overlap','fd_min'):
        name = 'RECORDS_'+profile+'.csv.gz'
        p = base/name
        assert sha(p) == source_meta['source_sha256'][name], 'Saved source changed: '+name
        inputs[name] = sha(p)
        header, allrows = rows(p)
        kept = [x for x in allrows if x['edge']=='0']
        saved[profile] = (header, kept)
    assert [len(saved[p][1]) for p in ('smarp_overlap','hmi_overlap','fd_min')] == [11387,103709,4515]
    table = Counter()
    for x in saved['fd_min'][1]:
        q = parse_quality32(x['QUALITY'])
        t = x['T_REC']
        interval = interval_class(x['INTERVAL'])
        table[('fd_2010_acquired',q,interval)] += 1
        if '2010.05.01' <= t < '2010.10.29':
            table[('fd_overlap_window',q,interval)] += 1
    # Include explicit zero cells for the requested four interval categories.
    table_rows = []
    for scope, q in sorted({(scope,q) for scope,q,_ in table}):
        for inter in ('60','300','30','missing','other'):
            table_rows.append(dict(scope=scope,quality_hex=f'0x{q:08X}',interval_class=inter,
                                   count=table[scope,q,inter]))
    assert sum(x['count'] for x in table_rows if x['scope']=='fd_2010_acquired') == 4515
    dimensions = ('LAT_MIN','LAT_MAX','LON_MIN','LON_MAX','NAXIS1','NAXIS2','DSUN_OBS','RSUN_REF')
    availability = []
    for profile in ('smarp_overlap','hmi_overlap'):
        schema_name = 'SCHEMA_'+('mdi.smarp_cea_96m' if profile.startswith('smarp') else 'hmi.sharp_cea_720s')+'.json'
        schema = json.loads((base/schema_name).read_text())
        inputs[schema_name] = sha(base/schema_name)
        keywords = {x['name']: x for x in schema['keywords']}
        header, data = saved[profile]
        for key in dimensions:
            availability.append(dict(profile=profile,field=key,in_schema=int(key in keywords),
                        acquired=int(key in header),finite_values=sum(finite(x.get(key)) is not None for x in data),
                        total=len(data),note=keywords.get(key,{}).get('note','not a schema keyword')))
    ph = analysis/'OVERLAP_CANDIDATES.csv.gz'
    inputs['OVERLAP_CANDIDATES.csv.gz'] = sha(ph)
    _, candidates = rows(ph)
    sm = {x['TARPNUM']+'|'+x['T_REC']:x for x in saved['smarp_overlap'][1]}
    hm = {x['HARPNUM']+'|'+x['T_REC']:x for x in saved['hmi_overlap'][1]}
    counts = Counter()
    pairs = defaultdict(set)
    warnings = Counter()
    for p in candidates:
        if p['unique_in_G5']!='1' or p['unique_in_G10']!='1': continue
        s,h = sm[p['smarp_id']],hm[p['hmi_id']]
        if parse_quality32(s['QUALITY']) not in (0,512) or parse_quality32(h['QUALITY'])!=0: continue
        dt = finite(p['dt_obs_s'])
        if dt is None or abs(dt)>360: continue
        slat,hlat = finite(s['CRVAL2']),finite(h['CRVAL2'])
        hlon,obs = finite(h['CRVAL1']),finite(h['CRLN_OBS'])
        if any(v is None for v in (slat,hlat,hlon,obs)): continue
        if slat*hlat<=0 or max(abs(slat),abs(hlat))>30: continue
        lon = (hlon-obs+180)%360-180
        if abs(lon)>30: continue
        st = ('N' if hlat>0 else 'S')+('_central' if abs(lon)<=15 else '_lateral')
        counts[st] += 1; pairs[st].add((p['TARPNUM'],p['HARPNUM']))
        # Center-only diagnostic in the parallel-ray limit; neither an eligibility
        # certificate nor a rejection of a magnetic footprint not containing the center.
        b0 = finite(h['CRLT_OBS'])
        if b0 is not None:
            l,b,L = map(math.radians,(hlat,b0,lon))
            cospsi = math.sin(l)*math.sin(b)+math.cos(l)*math.cos(b)*math.cos(L)
            warnings[st] += int(cospsi<.8)
    pool = [dict(stratum=st,record_arcs_available_conditions=counts[st],distinct_patch_pairs=len(pairs[st]),
                 hmi_center_parallel_cospsi_below_08=warnings[st],
                 full_footprint_mu_not_assessable=counts[st])
            for st in ('N_central','S_central','N_lateral','S_lateral')]
    # Verify persistent copies against recorded hashes. Do not rely on volatile /tmp.
    docdir = base.parent/'documentation_20261118'
    rec = json.loads((docdir/'DOCUMENTATION_HTTP_RECEIPT.json').read_text())
    docchecks = {x['name']:sha(docdir/x['name'])==x['sha256'] for x in rec['files']}
    prep = json.loads((docdir/'PREPARATION_RECEIPT.json').read_text())
    for name, value in prep['sources_and_staged_files_sha256'].items():
        if name.startswith('sources/'):
            docchecks[name] = sha(docdir/Path(name).name)==value
    assert docchecks and all(docchecks.values())
    assert sha(registry)==original_registry
    summary = dict(scope='review_diagnostics_only_no_selection',input_sha256=inputs,
                   geometry=availability,pool=pool,quality_interval=table_rows,
                   persistent_source_checks=docchecks,registry_unchanged_sha256=original_registry,
                   duration_s=time.monotonic()-started,
                   limitations=['No whole-footprint eligibility or expected loss rate can be estimated from these saved fields',
                       'Center diagnostic does not certify or reject the magnetic footprint',
                       'Full-disk table does not assign INTERVAL or source to any SMARP patch'])
    args.out.mkdir(parents=True)
    write_csv(args.out/'QUALITY_INTERVAL.csv',('scope','quality_hex','interval_class','count'),table_rows)
    write_csv(args.out/'GEOMETRY_FIELDS.csv',('profile','field','in_schema','acquired','finite_values','total','note'),availability)
    write_csv(args.out/'STRATA_DIAGNOSTIC.csv',tuple(pool[0]),pool)
    (args.out/'REVIEW_AUDIT.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'pool':pool,'quality_interval': [x for x in table_rows if x['count']],
                      'persistent_sources_verified':len(docchecks),'output':str(args.out)},indent=2))


if __name__=='__main__': main()

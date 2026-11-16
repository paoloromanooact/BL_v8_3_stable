"""Offline preview of the acquired overlap under the frozen metadata-inventory plan.

No history acquisition, export, map download or new matching rule. It imports the reviewed collector's
registered geometry and matching routines, checks the nearest-time joins and both graphs separately,
and explicitly labels the whole inventory incomplete. The cumulative registry counts analysis time.

    .venv/bin/python -B scripts/mdi_smarp_overlap_analysis.py --selftest
    .venv/bin/python -B scripts/mdi_smarp_overlap_analysis.py --run-id schema_20261116_http_ac06138
"""
from __future__ import annotations
import argparse
import bisect
import csv
import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mdi_smarp_inventory as I


def verify_matches(smarp, hmi, pairs, states, components):
    """Independent by-HARPNUM nearest-time search, haversine distance, degrees and patch components."""
    groups = defaultdict(list)
    for h in hmi:
        groups[h['HARPNUM']].append(h)
    times = {}
    for key, g in groups.items():
        g.sort(key=lambda x: x['_t']); times[key] = [x['_t'] for x in g]
    expected = set()
    for s in smarp:
        for key, g in groups.items():
            j = bisect.bisect_left(times[key], s['_t'])
            candidates = [g[k] for k in (j-1, j) if 0 <= k < len(g)]
            if candidates:
                h = min(candidates, key=lambda x: (abs((x['_t']-s['_t']).total_seconds()), x['_t']))
                if abs((h['_t']-s['_t']).total_seconds()) <= 360:
                    expected.add((s['_id'], h['_id']))
    observed = {(p['smarp_id'], p['hmi_id']) for p in pairs}
    checks = {'nearest_time_pairs': observed == expected and len(observed) == len(pairs),
              'one_state_per_smarp': len(states) == len(smarp) and {x['smarp_id'] for x in states} == {x['_id'] for x in smarp}}
    sm = {x['_id']: x for x in smarp}; hm = {x['_id']: x for x in hmi}
    distance_ok = True
    for p in pairs:
        a, b = sm[p['smarp_id']], hm[p['hmi_id']]
        if a['_geom']['status'] != 'ok' or b['_geom']['status'] != 'ok':
            distance_ok &= p['dist_deg'] is None
            continue
        ga, gb = a['_geom'], b['_geom']
        lat1, lat2 = math.radians(ga['lat']), math.radians(gb['lat'])
        dlon = math.radians(gb['lon']-ga['lon'])
        q = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        dist = math.degrees(2*math.asin(math.sqrt(min(1., max(0., q)))))
        distance_ok &= abs(dist-p['dist_deg']) <= 1e-9
    checks['independent_haversine_distances'] = bool(distance_ok)
    for radius in (5., 10.):
        rr = int(radius)
        arcs = [p for p in pairs if p['dist_deg'] is not None and p['dist_deg'] <= radius]
        ds = Counter(p['smarp_id'] for p in arcs); dh = Counter(p['hmi_id'] for p in arcs)
        checks[f'G{rr}_degrees_and_uniqueness'] = all(
            p[f'in_G{rr}'] == int(p['dist_deg'] is not None and p['dist_deg'] <= radius)
            and p[f'unique_in_G{rr}'] == int(ds[p['smarp_id']] == dh[p['hmi_id']] == 1
                                           and p['dist_deg'] is not None and p['dist_deg'] <= radius)
            for p in pairs)
        adjacent = defaultdict(set)
        for p in arcs:
            a, b = ('T',p['TARPNUM']), ('H',p['HARPNUM'])
            adjacent[a].add(b); adjacent[b].add(a)
        seen=set(); nc=0
        for node in adjacent:
            if node in seen: continue
            nc+=1; stack=[node];seen.add(node)
            while stack:
                for nxt in adjacent[stack.pop()]:
                    if nxt not in seen: seen.add(nxt);stack.append(nxt)
        checks[f'G{rr}_patch_components'] = nc == components[radius]
        checks[f'G{rr}_record_partition'] = all(x[f'state_G{rr}'] in I.STATES for x in states)
    return checks


def summarize(smarp, hmi, pairs, states, components):
    summary = dict(scope='overlap_only', inventory_complete=False,
                   smarp_records=len(smarp), smarp_patches=len({x['TARPNUM'] for x in smarp}),
                   hmi_records_with_margins=len(hmi), hmi_patches=len({x['HARPNUM'] for x in hmi}),
                   temporal_pairs=len(pairs), components={f'G{int(k)}':v for k,v in components.items()})
    for radius in (5,10):
        arcs = [p for p in pairs if p[f'in_G{radius}']]
        unique = [p for p in arcs if p[f'unique_in_G{radius}']]
        summary[f'G{radius}'] = dict(record_arcs=len(arcs), unique_record_arcs=len(unique),
             patch_pairs=len({(p['TARPNUM'],p['HARPNUM']) for p in arcs}),
             patch_pairs_with_a_unique_record_arc=len({(p['TARPNUM'],p['HARPNUM']) for p in unique}),
             record_states=dict(Counter(x[f'state_G{radius}'] for x in states)))
    summary['ambiguous_on_widening_records'] = sum(p['ambiguous_on_widening'] for p in pairs)
    summary['smarp_records_with_incomplete_competitor_geometry'] = sum(not x['geometry_complete_competitors'] for x in states)
    summary['smarp_records_with_incomplete_temporal_search'] = sum(not x['search_complete'] for x in states)
    summary['envelope_not_assessable_pairs'] = sum(not p['envelope_assessable'] for p in pairs)
    summary['nominal_time_offsets_s'] = dict(Counter(str(p['dt_s']) for p in pairs))
    obs = [p['dt_obs_s'] for p in pairs if p['dt_obs_s'] is not None]
    summary['observation_time_offsets_s'] = dict(available=len(obs), min=min(obs) if obs else None, max=max(obs) if obs else None)
    summary['noaa_concordance'] = dict(Counter(p['noaa_concordance'] for p in pairs))
    summary['geometry_status'] = {name:dict(Counter(x['_geom']['status'] for x in recs)) for name,recs in [('smarp',smarp),('hmi',hmi)]}
    summary['quality_values'] = {name:dict(Counter(I.parse_quality(x.get('QUALITY'))[1] for x in recs))
                                 for name,recs in [('smarp',smarp),('hmi_with_margins',hmi)]}
    patch = {}
    for p in pairs:
        if not p['in_G10']: continue
        key = (p['TARPNUM'],p['HARPNUM'])
        r = patch.setdefault(key, dict(TARPNUM=key[0],HARPNUM=key[1],n_G5=0,n_G10=0,n_unique_G5=0,n_unique_G10=0,
                                      min_dist_deg=p['dist_deg'],max_dist_deg=p['dist_deg']))
        for k in (5,10):
            r[f'n_G{k}'] += p[f'in_G{k}'];r[f'n_unique_G{k}'] += p[f'unique_in_G{k}']
        r['min_dist_deg']=min(r['min_dist_deg'],p['dist_deg']);r['max_dist_deg']=max(r['max_dist_deg'],p['dist_deg'])
    return summary, sorted(patch.values(),key=lambda x:(int(x['TARPNUM']),int(x['HARPNUM'])))


def analyze(run):
    if I.git('status','--porcelain','--untracked-files=no'):
        raise I.TechnicalError('tracked tree must be clean')
    rel=str(Path(__file__).resolve().relative_to(I.ROOT))
    if I.git('ls-files','--error-unmatch',rel)!=rel:
        raise I.TechnicalError('analysis driver must be committed')
    I.check_plan()
    commit=I.git('rev-parse','HEAD');out=run.res/'overlap_only'/commit[:12]
    if out.exists():raise I.TechnicalError('output already exists; refusing overwrite')
    meta=dict(scope='overlap_only',outcome='non riuscito',start_utc=I.now_utc(),**I.provenance())
    meta['collector_sha256']=meta.pop('script_sha256');meta['script_sha256']=I.sha_file(__file__)
    with I.lock(run):
        if not run.registry_path.exists():raise I.TechnicalError('inventory registry missing')
        reg=I.Registry(run.registry_path,run_id=run.id)
        before={k:reg.d[k] for k in ('attempts','bytes','rows')}
        try:
            def tick(*a):reg.check('offline overlap analysis')
            tick();fmap,rules=I.registered_map(run)
            if not I.leaf_status(run)['overlap']['complete']:
                raise I.TechnicalError('overlap acquisition incomplete')
            receipts=[json.loads(x) for x in run.p('LIST_RECEIPTS.jsonl').read_text().splitlines()]
            reconciliation=I.reconcile_derived(run,receipts,tick,fmap,rules)
            if not reconciliation['ok']:raise I.TechnicalError(reconciliation['msg'])
            for line in run.p('raw/QUERY_LOG.jsonl').read_text().splitlines():
                e=json.loads(line)
                if I.sha_file(run.p('raw')/e['file'])!=e['sha256']:raise I.TechnicalError('raw response hash differs')
                tick()
            sm=[x for x in I.load_records(run,'smarp_overlap',fmap) if x['edge']=='0' and x['_t'] is not None and I.OV0<=x['_t']<I.OV1]
            hm=[x for x in I.load_records(run,'hmi_overlap',fmap) if x['edge']=='0' and x['_t'] is not None]
            for prof,recs in [('smarp_overlap',sm),('hmi_overlap',hm)]:
                tn=I.role_name(fmap,prof,'time_obs')
                for j,x in enumerate(recs):
                    x['_geom']=I.geom_of(x,fmap,prof);x['_tobs']=x.get(tn)
                    if j%500==0:tick()
            pairs,states,components=I.match_overlap(sm,hm,fmap,incomplete=I.incomplete_hmi_intervals(run),tick=tick)
            checks=verify_matches(sm,hm,pairs,states,components)
            checks['originals_reconciled']=reconciliation['ok']
            checks['no_network_or_new_rows'] = before=={k:reg.d[k] for k in before}
            if not all(checks.values()):raise I.TechnicalError('independent matching checks failed: '+str(checks))
            summary,patch=summarize(sm,hm,pairs,states,components)
            tick();out.mkdir(parents=True)
            with gzip.open(out/'OVERLAP_CANDIDATES.csv.gz','wt',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(pairs[0]) if pairs else ['smarp_id'],lineterminator='\n');w.writeheader();w.writerows(pairs)
            I.write_csv(out/'RECORD_STATES.csv',states,list(states[0]) if states else ['smarp_id'])
            I.write_csv(out/'PATCH_PAIRS.csv',patch,list(patch[0]) if patch else ['TARPNUM','HARPNUM'])
            I.write_json(out/'SUMMARY.json',summary);I.write_json(out/'CHECKS.json',checks)
            meta.update(outcome='complete_for_overlap_only',inventory_complete=False,
                        source_sha256={n:I.sha_file(run.p(n)) for n in ['FIELD_MAP.csv','PRODUCT_RULES.json','FIELD_MAP_REVIEW.json','FIELD_MAP_REGISTRATION.json','LIST_RECEIPTS.jsonl']+[f'RECORDS_{p}.csv.gz' for p in ('smarp_overlap','hmi_overlap','fd_min')]},
                        checks=checks,limitations=['No physical-region identity is certified by the candidate graphs',
                        'No image or magnetic measurement has been compared', 'Envelopes are not assessable without dimensions',
                        'History is not acquired; this is not the final inventory analysis'])
            tick()
        except Exception as exc:
            meta.update(outcome='non riuscito',exception_type=type(exc).__name__,reason=str(exc));raise
        finally:
            reg.close('analyze_overlap_only',meta['outcome'])
            meta.update(end_utc=I.now_utc(),registry={k:reg.d[k] for k in ('attempts','bytes','rows','wall_s_completed')})
            out.mkdir(parents=True,exist_ok=True);I.write_json(out/'META.json',meta)
    print(json.dumps(summary,indent=2));print('output:',out)


def selftest():
    from datetime import datetime,timedelta
    t=datetime(2010,6,1)
    def record(ident,kind,delta,lon,lat=0):
        return dict(_id=ident,_t=t+timedelta(seconds=delta),_tobs=None,_geom=dict(status='ok',lon=lon,lat=lat,env=None,method='synthetic'),**{kind:ident[0]})
    s=record('1s','TARPNUM',0,359.0)
    h=[record('1a','HARPNUM',-360,1.0),record('1b','HARPNUM',360,1.0),record('2a','HARPNUM',0,6.0)]
    pairs,states,comps=I.match_overlap([s],h,[])
    checks=verify_matches([s],h,pairs,states,comps)
    assert all(checks.values()) and pairs[0]['hmi_id']=='1a'
    assert len(pairs)==2 and sum(p['in_G5'] for p in pairs)==1 and sum(p['in_G10'] for p in pairs)==2
    assert pairs[0]['ambiguous_on_widening']==1
    h[1]['_geom']=dict(status='not_assessable')
    pairs,states,comps=I.match_overlap([s],h,[])
    assert all(verify_matches([s],h,pairs,states,comps).values())
    print('offline driver selftest passed')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run-id');ap.add_argument('--selftest',action='store_true');args=ap.parse_args()
    if args.selftest:selftest()
    elif args.run_id:analyze(I.Run(args.run_id))
    else:ap.error('--run-id or --selftest is required')

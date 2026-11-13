"""Confronto e tabelle del protocollo morfologico HMI, A1/A2.

Solo letture gia bloccate e misure numeriche gia distribuite. Non classifica
immagini, non ricostruisce misure dai FITS e non modifica letture originali.
    .venv/bin/python python/sharpbl/morphology_compare.py --selftest
    .venv/bin/python python/sharpbl/morphology_compare.py --run
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'results/MORPHOLOGY'
OUT = BASE / 'ANALYSIS'
INPUT_LIST = ROOT / 'docs/MORPHOLOGY_COMPARISON_INPUTS_SHA256.csv'
PRIMARY = ['A', 'B', 'D', 'U']
CATS_C = ['si', 'no', 'non_valutabile']
NEW_GROUPS = ['24N', '24S', '25N']
COMMITMENTS = ['CALIBRATION_READER1_COMMITMENT.csv', 'CALIBRATION_READER2_COMMITMENT.csv',
               'READING_READER1_COMMITMENT.csv', 'PRIMARY_READER2_COMMITMENT.csv',
               'CENTROIDS_READER1_COMMITMENT.csv', 'CENTROIDS_READER2_COMMITMENT.csv',
               'CODE_MAP_COMMITMENT.csv']
CHECKS = []

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()

def load(rel):
    return pd.read_csv(ROOT / rel, keep_default_na=False)

def check(name, ok, detail=''):
    CHECKS.append(dict(check=name, passed=bool(ok), detail=str(detail)))
    if not ok:
        raise ValueError(name + ': ' + str(detail))

def ratio(a, b):
    return float(a / b) if b != 0 else np.nan

def sums(values):
    values = list(values)
    return math.fsum(values), math.fsum(abs(x) for x in values)

def matrix(a, b, cats):
    ct = Counter(zip(a, b))
    return pd.DataFrame([dict(reader1=x, reader2=y, n=ct[x, y]) for x in cats for y in cats])

def normalize_c(values):
    return values.astype(str).str.strip().str.lower().replace({'sì': 'si', 'non valutabile': 'non_valutabile'})

def selftest():
    a, b = ['A', 'B', 'D', 'U'], ['A', 'A', 'D', 'B']
    m = matrix(a, b, PRIMARY)
    assert len(m) == 16 and m.n.sum() == 4
    assert m.loc[m.reader1 == m.reader2, 'n'].sum() == 2
    c = matrix(['si', 'no', 'non_valutabile'], ['si', 'non_valutabile', 'non_valutabile'], CATS_C)
    assert len(c) == 9 and c.n.sum() == 3
    assert c.loc[c.reader1 == c.reader2, 'n'].sum() == 2
    assert normalize_c(pd.Series(['sì', 'non valutabile', 'no'])).tolist() == CATS_C[0:1] + CATS_C[2:3] + CATS_C[1:2]
    assert sums([10., -9.]) == (1., 19.)
    assert math.isnan(ratio(1., 0.))
    assert [x for x in ['B', 'B', 'U'] if x == 'B'] == ['B', 'B']
    return 8

def historical_rows(doc):
    rows, section = [], None
    for line in doc.splitlines():
        if line.startswith('## 1.'):
            section = 'dominante'
        elif line.startswith('## 2.'):
            section = 'controllo'
        elif line.startswith('## 3.'):
            section = None
        if section and line.startswith('|'):
            cells = [x.strip() for x in re.split(r'(?<!\\)\|', line)[1:-1]]
            j = 1 if section == 'dominante' else 0
            if len(cells) > j + 1 and cells[j].isdigit():
                label = cells[3 if section == 'dominante' else 1].replace('**', '').strip()
                match = re.match(r'^[ABCDE](?:/[ABCDE])?', label)
                assert match, label
                rows.append(dict(HARPNUM=int(cells[j]), historical_class=match.group(),
                                 historical_class_original=label, historical_kind=section))
    return pd.DataFrame(rows)

def snapshot_checks():
    locks, verified = {}, []
    for name in COMMITMENTS:
        rows = load('results/MORPHOLOGY/' + name)
        for row in rows.to_dict('records'):
            fname = row['file']
            check('safe_filename_' + fname, Path(fname).name == fname)
            path = BASE / fname if fname == 'CODE_MAP.csv' else BASE / 'LOCKED_READINGS' / fname
            check('locked_hash_' + fname, sha(path) == row['sha256'])
            private = BASE / 'private' / fname
            if fname != 'CODE_MAP.csv' and private.exists():
                check('private_original_unchanged_' + fname, sha(private) == row['sha256'])
            if 'locked_utc' in row:
                locks[fname] = row['locked_utc']
            verified.append(dict(commitment=name, file=fname, sha256=row['sha256'], verified=1))
    check('both_primary_before_both_centroid_locks',
          max(locks['READING_READER1.csv'], locks['PRIMARY_READER2.csv']) <
          min(locks['CENTROIDS_READER1.csv'], locks['CENTROIDS_READER2.csv']))
    return pd.DataFrame(verified)

def reading_tables():
    prefix = 'results/MORPHOLOGY/LOCKED_READINGS/'
    p1, p2 = load(prefix + 'READING_READER1.csv'), load(prefix + 'PRIMARY_READER2.csv')
    c1, c2 = load(prefix + 'CENTROIDS_READER1.csv'), load(prefix + 'CENTROIDS_READER2.csv')
    o1 = load('results/MORPHOLOGY/READING_ORDER_READER1.csv')
    o2 = load('results/MORPHOLOGY/READING_ORDER_READER2.csv')
    for name, df, order in [('p1', p1, o1), ('p2', p2, o2), ('c1', c1, o1), ('c2', c2, o2)]:
        check(name + '_exact_order_and_codes',
              list(zip(df.order, df.code)) == list(zip(order.order, order.code)) and not df.code.duplicated().any())
    check('fixed_reader_counts', len(p1) == len(c1) == 90 and len(p2) == len(c2) == 30)
    check('primary1_categories', set(p1['class']) <= set(PRIMARY))
    check('primary2_categories', set(p2.primary_class) <= set(PRIMARY))
    c1['C'] = normalize_c(c1['C']); c2['indicator_c'] = normalize_c(c2.indicator_c)
    check('centroid1_categories', set(c1.C) <= set(CATS_C))
    check('centroid2_categories', set(c2.indicator_c) <= set(CATS_C))
    p1 = p1[['code', 'class', 'alternatives', 'reason']].rename(columns={'class':'class_r1', 'alternatives':'alternatives_r1', 'reason':'reason_primary_r1'})
    p2 = p2[['code', 'primary_class', 'alternatives', 'visual_reason']].rename(columns={'primary_class':'class_r2', 'alternatives':'alternatives_r2', 'visual_reason':'reason_primary_r2'})
    c1 = c1[['code', 'C', 'C_polarity', 'C_reason', 'border_contact', 'border_note']].rename(columns={'C':'C_r1', 'C_polarity':'C_polarity_r1', 'C_reason':'C_reason_r1', 'border_contact':'border_r1', 'border_note':'border_note_r1'})
    c2 = c2[['code', 'indicator_c', 'affected_polarity', 'visual_reason', 'mask_image_border_contact', 'border_note']].rename(columns={'indicator_c':'C_r2', 'affected_polarity':'C_polarity_r2', 'visual_reason':'C_reason_r2', 'mask_image_border_contact':'border_r2', 'border_note':'border_note_r2'})
    one = p1.merge(c1, on='code', validate='one_to_one')
    two = p2.merge(c2, on='code', validate='one_to_one')
    common = o2[['order','code']].merge(one, on='code', validate='one_to_one').merge(two, on='code', validate='one_to_one')
    check('common_30', len(common) == 30)
    common['primary_equal'] = (common.class_r1 == common.class_r2).astype(int)
    common['C_equal'] = (common.C_r1 == common.C_r2).astype(int)
    common['C_both_evaluable'] = ((common.C_r1 != 'non_valutabile') & (common.C_r2 != 'non_valutabile')).astype(int)
    return one.merge(two, how='left', on='code', validate='one_to_one').fillna(''), common

def registry(new):
    cmap = load('results/MORPHOLOGY/CODE_MAP.csv')
    selection = load('results/DOMINANT/DOMINANT_HARP_SELECTION.csv')
    checks = load('results/DOMINANT/DOMINANT_HARP_CHECKS.csv')
    cat = load('results/P1/P1_SBL_CATALOG_BY_HARP.csv')
    hist = historical_rows((ROOT / 'docs/DOMINANT_HARP_VISUAL_25S.md').read_text())
    check('historical_30', len(hist) == 30 and hist.HARPNUM.nunique() == 30)
    check('selection_120', len(selection) == 120 and selection.HARPNUM.nunique() == 120)
    check('mapping_101', len(cmap) == 101 and cmap.code.nunique() == 101 and cmap.HARPNUM.nunique() == 101)
    mapped = cmap[cmap.role == 'nuova'].copy()
    if len(mapped) != 90:
        mapped = cmap[cmap.code.str.startswith('M')].copy()
    check('mapping_new90_codes', len(mapped) == 90 and set(mapped.code) == set(new.code))
    for role in ['group', 'kind', 'T_REC']:
        j = cmap.merge(selection[['HARPNUM', role]], on='HARPNUM', suffixes=('', '_selection'), validate='one_to_one')
        check('mapping_selection_' + role, (j[role] == j[role + '_selection']).all())
    check('all_202_image_hashes', all(sha(ROOT / f"figures/MORPHOLOGY/{v}_{r.code}.png") == getattr(r, 'sha256_' + v + '_png') for r in cmap.itertuples() for v in ['map','cen']))
    cols = ['HARPNUM','T_REC','group','kind','rank','in_S','s_bl_P1','abs_sbl','share_abs',
            'group_n','group_sum_abs','group_sum_net','NOAA_NUM','NOAA_ARS','phi_P1_cat']
    reg = selection[cols].copy()
    rmap = mapped[['HARPNUM','code']].merge(new, on='code', validate='one_to_one')
    reg = reg.merge(rmap, on='HARPNUM', how='left', validate='one_to_one').merge(hist, on='HARPNUM', how='left', validate='one_to_one')
    reg['cohort'] = np.where(reg.group == '25S','historical_25S','new_A2')
    reg = reg.fillna('')
    for variant in ['bmap1','uniform']:
        reg = reg.merge(checks[['HARPNUM',variant+'_possible',variant+'_s_bl']], on='HARPNUM', validate='one_to_one')
        ok = reg[variant+'_possible'].astype(int) == 1
        vals = pd.to_numeric(reg.loc[ok,variant+'_s_bl'],errors='raise')
        check(variant + '_possible_are_finite', np.isfinite(vals).all())
    cycle_numeric = pd.to_numeric(cat.cycle, errors='coerce')
    valid = cat[(cat.role != 'control') & (cat.valid_bl.astype(int) == 1) & cycle_numeric.isin([24,25])].copy()
    valid['cycle'] = cycle_numeric.loc[valid.index].astype(int)
    valid['group'] = valid.cycle.astype(int).astype(str) + np.where(valid.lat_mean_deg.astype(float) >= 0,'N','S')
    check('full_base_4189',len(valid) == 4189)
    for group, part in valid.groupby('group'):
        sr = reg[reg.group == group]
        total, absolute = sums(part.s_bl.astype(float))
        check('base_denominators_' + group,
              len(part) == int(sr.group_n.iloc[0]) and
              math.isclose(total,float(sr.group_sum_net.iloc[0]),rel_tol=1e-12) and
              math.isclose(absolute,float(sr.group_sum_abs.iloc[0]),rel_tol=1e-12))
    selected = valid.merge(reg[['HARPNUM','s_bl_P1','T_REC']], on='HARPNUM', validate='one_to_one',suffixes=('','_selected'))
    check('selection_matches_P1_records',len(selected)==120 and (selected.T_REC == selected.T_REC_selected).all() and
          np.allclose(selected.s_bl.astype(float),selected.s_bl_P1.astype(float),rtol=1e-12,atol=0))
    check('historical_cohort_separate',len(reg[reg.cohort=='historical_25S'])==30 and (reg.loc[reg.cohort=='historical_25S','class_r1']=='').all())
    return reg, hist

def agreement_tables(common):
    m1 = matrix(common.class_r1, common.class_r2, PRIMARY)
    m2 = matrix(common.C_r1, common.C_r2, CATS_C)
    both = common.C_both_evaluable == 1
    rows = []
    for name, num, den in [
        ('primary_exact_all30', common.primary_equal.sum(), 30),
        ('reader1_U_all30', (common.class_r1=='U').sum(),30),
        ('reader2_U_all30', (common.class_r2=='U').sum(),30),
        ('C_exact_all30_including_NV', common.C_equal.sum(),30),
        ('C_exact_both_evaluable', common.loc[both,'C_equal'].sum(),both.sum()),
        ('C_reader1_NV_all30',(common.C_r1=='non_valutabile').sum(),30),
        ('C_reader2_NV_all30',(common.C_r2=='non_valutabile').sum(),30),
        ('C_at_least_one_NV_all30',(~both).sum(),30),
        ('border_exact_all30',(common.border_r1==common.border_r2).sum(),30)]:
        rows.append(dict(metric=name,numerator=int(num),denominator=int(den),fraction=ratio(num,den)))
    check('primary_matrix_recounts',m1.n.sum()==30 and m1.loc[m1.reader1==m1.reader2,'n'].sum()==common.primary_equal.sum())
    check('C_matrix_recounts',m2.n.sum()==30 and m2.loc[m2.reader1==m2.reader2,'n'].sum()==common.C_equal.sum())
    return m1,m2,pd.DataFrame(rows)

def distributions(reg):
    sources, sensitivity = [], []
    cohorts = [('new_reader1',reg[reg.cohort=='new_A2'],'class_r1','C_r1'),
               ('new_reader2_common',reg[reg.class_r2!=''],'class_r2','C_r2'),
               ('historical_25S',reg[reg.cohort=='historical_25S'],'historical_class',None)]
    for cohort, frame, pcol, ccol in cohorts:
        for group, g in frame.groupby('group'):
            totalabs,totalnet = float(g.group_sum_abs.iloc[0]),float(g.group_sum_net.iloc[0])
            cats = PRIMARY if cohort != 'historical_25S' else sorted(g[pcol].unique())
            for grouping, column, categories in [('primary_class',pcol,cats)] + ([('indicator_C',ccol,CATS_C)] if ccol else []):
                for label in categories:
                    for kind in ['all','dominante','controllo']:
                        scope = g if kind=='all' else g[g.kind==kind]
                        part = scope[scope[column]==label]
                        net,absolute = sums(part.s_bl_P1.astype(float))
                        row = dict(cohort=cohort,group=group,grouping=grouping,label=label,kind=kind,
                                   n=len(part),n_in_S=int(part.in_S.astype(int).sum()),
                                   n_examined_scope=len(scope),n_full_P1_group=int(g.group_n.iloc[0]),
                                   sum_net=net,sum_abs=absolute,group_sum_net=totalnet,group_sum_abs=totalabs,
                                   share_abs_full_P1_group=ratio(absolute,totalabs),
                                   share_abs_examined_scope=ratio(absolute,math.fsum(scope.abs_sbl.astype(float))),
                                   net_rel_full_P1_net=ratio(net,totalnet))
                        sources.append(row)
                        if kind != 'all':
                            continue
                        for variant in ['bmap1','uniform']:
                            ok = part[part[variant+'_possible'].astype(int)==1]
                            diff = pd.to_numeric(ok[variant+'_s_bl'],errors='raise') - ok.s_bl_P1.astype(float)
                            dnet,dabs = sums(diff)
                            if not len(ok):
                                dnet=dabs=np.nan
                            sensitivity.append(dict(cohort=cohort,group=group,grouping=grouping,label=label,variant=variant,
                                n_examined=len(part),n_comparable=len(ok),n_missing=len(part)-len(ok),
                                comparable_original_sum_abs=math.fsum(ok.abs_sbl.astype(float)),
                                comparable_share_full_P1_abs=ratio(math.fsum(ok.abs_sbl.astype(float)),totalabs),
                                delta_sum=dnet,sum_abs_delta=dabs,delta_rel_full_P1_abs=ratio(dnet,totalabs),
                                abs_delta_rel_full_P1_abs=ratio(dabs,totalabs),delta_rel_full_P1_net=ratio(dnet,totalnet)))
            for label in cats:
                part = g[g[pcol]==label]
                check(f'class_independent_fsum_{cohort}_{group}_{label}',
                      math.isclose(float(part.s_bl_P1.astype(float).sum()),math.fsum(part.s_bl_P1.astype(float)),rel_tol=1e-12,abs_tol=1e-12*totalabs))
    return pd.DataFrame(sources),pd.DataFrame(sensitivity)

def priority(reg, agreement):
    gnew=reg[reg.cohort=='new_A2']
    rows=[]
    for group in NEW_GROUPS:
        g=gnew[gnew.group==group]
        first=g.class_r1=='B'
        shared=g.class_r2!=''
        conservative=first & (~shared | (g.class_r2=='B'))
        denom=float(g.group_sum_abs.iloc[0])
        one=math.fsum(g.loc[first,'abs_sbl'].astype(float))/denom
        two=math.fsum(g.loc[conservative,'abs_sbl'].astype(float))/denom
        rows.append(dict(group=group,reader1_B_n=int(first.sum()),conservative_B_n=int(conservative.sum()),
                         n_common=int(shared.sum()),reader1_B_share_full_P1_abs=one,
                         conservative_B_share_full_P1_abs=two,reader1_reaches_10pct=int(one>=.1),
                         conservative_reaches_10pct=int(two>=.1),group_threshold_changed=int((one>=.1)!=(two>=.1))))
    table=pd.DataFrame(rows)
    a=agreement.set_index('metric').numerator
    first_ok=int(table.reader1_reaches_10pct.sum())>=2
    conservative_ok=int(table.conservative_reaches_10pct.sum())>=2
    result=dict(reader1_groups_at_10pct=int(table.reader1_reaches_10pct.sum()),
                conservative_groups_at_10pct=int(table.conservative_reaches_10pct.sum()),
                source_condition_reader1=first_ok,source_condition_conservative=conservative_ok,
                primary_agreement_at_least_24=bool(a['primary_exact_all30']>=24),
                reader1_U_at_most_3=bool(a['reader1_U_all30']<=3),reader2_U_at_most_3=bool(a['reader2_U_all30']<=3),
                reader_changes_source_condition=first_ok!=conservative_ok)
    result['all_operational_conditions_met']=bool(first_ok and conservative_ok and
        result['primary_agreement_at_least_24'] and result['reader1_U_at_most_3'] and result['reader2_U_at_most_3'])
    result['status']='propose_separate_representative_S_design_only' if result['all_operational_conditions_met'] else (
        'inconclusive_reader_dependent_source_condition' if result['reader_changes_source_condition'] else 'complete_report_and_stop_under_current_rule')
    return table,result

def run():
    check('hand_built_selftests',selftest()==8)
    check('output_directory_new',not OUT.exists())
    check('tracked_clean_before_run',not git('status','--porcelain','--untracked-files=no'))
    head=git('rev-parse','HEAD')
    expected=load(str(INPUT_LIST.relative_to(ROOT)))
    for r in expected.itertuples():
        check('input_hash_'+r.file,sha(ROOT/r.file)==r.sha256)
    verified=snapshot_checks()
    new,common=reading_tables()
    reg,hist=registry(new)
    common=common.merge(reg[['code','HARPNUM','group','kind','in_S','share_abs']],on='code',validate='one_to_one')
    check('composition_7dominants_3controls_each_group',all(len(common[(common.group==g)&(common.kind==k)])==n for g in NEW_GROUPS for k,n in [('dominante',7),('controllo',3)]))
    m1,m2,agreement=agreement_tables(common)
    source,sensitivity=distributions(reg)
    pri,decision=priority(reg,agreement)
    composition=common.groupby(['group','kind'],sort=True).agg(n=('code','size'),n_in_S=('in_S','sum'),share_abs_full_P1_group=('share_abs','sum')).reset_index()
    for row in source[source.grouping=='primary_class'].groupby(['cohort','group','kind']):
        _,g=row
        check('class_counts_partition_'+'_'.join(map(str,row[0])),int(g.n.sum())==int(g.n_examined_scope.iloc[0]))
    for v in ['bmap1','uniform']:
        ss=sensitivity[(sensitivity.grouping=='primary_class')&(sensitivity.variant==v)]
        for (cohort,group),g in ss.groupby(['cohort','group']):
            check('sensitivity_partition_'+cohort+'_'+group+'_'+v,int((g.n_comparable+g.n_missing).sum())==int(g.n_examined.sum()))
    check('fixed_register_120_unique',len(reg)==120 and reg.HARPNUM.nunique()==120)
    check('no_consensus_labels_created',not any('consensus' in c for c in reg.columns))
    stamp=dict(git_commit_comparison=head,git_dirty_comparison=0,
               sha256_morphology=sha(ROOT/'docs/PROTOCOL_HMI_MORPHOLOGY.md'),
               sha256_morphology_A1=sha(ROOT/'docs/PROTOCOL_HMI_MORPHOLOGY_A1.md'),
               sha256_morphology_A2=sha(ROOT/'docs/PROTOCOL_HMI_MORPHOLOGY_A2.md'))
    tables={'LOCK_VERIFICATION':verified,'COMPARISON':common,'CONFUSION_PRIMARY':m1,'CONFUSION_C':m2,
            'AGREEMENT':agreement,'COMPARISON_COMPOSITION':composition,'REGISTER':reg,
            'HISTORICAL_25S_FROM_DOCUMENT':hist,'CLASS_SOURCE':source,'SENSITIVITY_BY_CLASS':sensitivity,
            'PRIORITY_GROUPS':pri,'PRIORITY_DECISION':pd.DataFrame([decision])}
    OUT.mkdir()
    for name,df in tables.items():
        df.assign(**stamp).to_csv(OUT/(name+'.csv'),index=False)
    saved=pd.read_csv(OUT/'COMPARISON.csv',keep_default_na=False)
    independent_primary=Counter(zip(saved.class_r1,saved.class_r2))
    independent_c=Counter(zip(saved.C_r1,saved.C_r2))
    check('serialized_primary_counts_independent',all(int(r.n)==independent_primary[r.reader1,r.reader2] for r in m1.itertuples()))
    check('serialized_C_counts_independent',all(int(r.n)==independent_c[r.reader1,r.reader2] for r in m2.itertuples()))
    # Recount class memberships and signed/absolute sums from serialized rows
    # with csv + Decimal, separately from pandas grouping and float reduction.
    from decimal import Decimal
    with (OUT/'REGISTER.csv').open() as f:
        plain_reg = list(csv.DictReader(f))
    for row in source[(source.grouping=='primary_class') & (source.kind=='all')].itertuples():
        column = {'new_reader1':'class_r1','new_reader2_common':'class_r2','historical_25S':'historical_class'}[row.cohort]
        part = [x for x in plain_reg if x['group']==row.group and x[column]==row.label and
                (x['cohort']=='historical_25S' if row.cohort=='historical_25S' else x['cohort']=='new_A2')]
        dn = sum((Decimal(x['s_bl_P1']) for x in part), Decimal(0))
        da = sum((abs(Decimal(x['s_bl_P1'])) for x in part), Decimal(0))
        tolerance = 1e-12*row.group_sum_abs
        check('serialized_source_recount_'+row.cohort+'_'+row.group+'_'+row.label,
              len(part)==row.n and abs(float(dn)-row.sum_net)<=tolerance and abs(float(da)-row.sum_abs)<=tolerance)
    for r in expected.itertuples():
        check('input_unchanged_'+r.file,sha(ROOT/r.file)==r.sha256)
    for r in verified.itertuples():
        private=BASE/'private'/r.file
        if r.file!='CODE_MAP.csv' and private.exists():
            check('private_still_unchanged_'+r.file,sha(private)==r.sha256)
    check('HEAD_unchanged',git('rev-parse','HEAD')==head)
    pd.DataFrame(CHECKS).assign(**stamp).to_csv(OUT/'CHECKS.csv',index=False)
    meta=dict(**stamp,status='complete_descriptive_comparison_no_consensus',
              run_utc=datetime.now(timezone.utc).isoformat(),input_manifest_sha256=sha(INPUT_LIST),
              code_sha256=sha(Path(__file__)),checks_passed=len(CHECKS),
              inputs=expected.to_dict('records'),operational_rule=decision,
              output_hashes={p.name:sha(p) for p in sorted(OUT.glob('*.csv'))},
              versions=dict(numpy=np.__version__,pandas=pd.__version__),
              limits=['Shared calibration and known project; independent of new labels before locks.',
                      'Historical 25S categories kept separate; no conversion to A2.',
                      'Selection is not representative of all P1 or S; no quenching test.',
                      'C agreement all30 includes matching NV; both-evaluable denominator separately reported.',
                      'Border judgement ancillary and visual, not a pixel-count audit.'])
    (OUT/'META.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='complete',checks_passed=len(CHECKS),rows_common=len(common),rows_register=len(reg)),indent=2))

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--selftest',action='store_true');g.add_argument('--run',action='store_true')
    args=ap.parse_args()
    if args.selftest:
        print('hand-built checks:',selftest())
    else:
        try:
            run()
        except Exception:
            if OUT.exists():
                pd.DataFrame(CHECKS).to_csv(OUT/'CHECKS_FAILED.csv',index=False)
            raise

if __name__=='__main__':
    main()

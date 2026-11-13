"""Internal post hoc morphology audit; separate stdlib implementation, same author.
Reads locked public sources, no image classification, FITS, fitting or simulation.
Writes only to the explicitly requested new --out directory.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal, getcontext
import hashlib
import json
from pathlib import Path
import subprocess

getcontext().prec = 50
parser=argparse.ArgumentParser()
parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
parser.add_argument('--out',required=True)
args=parser.parse_args();ROOT=Path(args.root);OUT=Path(args.out)
if (OUT/'REVIEW_CHECKS.csv').exists() or (OUT/'META.json').exists():
    raise SystemExit('Review artifacts already exist: choose a new output directory.')
BASE=ROOT/'results/MORPHOLOGY';A=BASE/'ANALYSIS'
checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
    inputs[str(p.relative_to(ROOT))]=sha(p)
    with p.open() as f:return list(csv.DictReader(f))
def check(name,condition):
    checks.append(dict(check=name,passed=bool(condition)))
    if not condition:raise AssertionError(name)
def dec(x):return Decimal(str(x))
def same(a,b,scale=None):
    if a in ('','nan','NaN') or b is None:return a in ('','nan','NaN') and b is None
    x,y=dec(a),dec(b)
    if not(x.is_finite() and y.is_finite()):return x==y
    sc=max(abs(x),abs(y),abs(dec(scale)) if scale is not None else Decimal(0),Decimal('1e-100'))
    return abs(x-y)<=Decimal('1e-11')*sc
def total(rows,key):return sum((dec(x[key]) for x in rows),Decimal(0))
def frac(n,d):return n/d if d else None
def key(rows,field):
    result={x[field]:x for x in rows};check('unique_'+field+'_'+str(len(rows)),len(result)==len(rows));return result
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT).decode().strip()

head=git('rev-parse','HEAD')
commitments=['CALIBRATION_READER1','CALIBRATION_READER2','READING_READER1','PRIMARY_READER2','CENTROIDS_READER1','CENTROIDS_READER2','CODE_MAP']
locks={}
for name in commitments:
    for item in load(BASE/(name+'_COMMITMENT.csv')):
        file=item['file'];path=BASE/file if name=='CODE_MAP' else BASE/'LOCKED_READINGS'/file
        check('public_lock_'+file,sha(path)==item['sha256'])
        inputs[str(path.relative_to(ROOT))]=sha(path)
        private=BASE/'private'/file
        if private.exists():check('private_lock_'+file,sha(private)==item['sha256'])
        if item.get('locked_utc'):locks[file]=item['locked_utc']
check('primary_before_secondary',max(locks['READING_READER1.csv'],locks['PRIMARY_READER2.csv']) < min(locks['CENTROIDS_READER1.csv'],locks['CENTROIDS_READER2.csv']))
for commit,file in [('21dfe6d','PROTOCOL_HMI_MORPHOLOGY.md'),('67f5e1a','PROTOCOL_HMI_MORPHOLOGY_A1.md'),('9a4c4cd','PROTOCOL_HMI_MORPHOLOGY_A2.md')]:
    rel='docs/'+file
    raw=subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT)
    check('frozen_'+file,hashlib.sha256(raw).hexdigest()==sha(ROOT/rel))
    inputs[rel]=sha(ROOT/rel)

raw1=load(BASE/'LOCKED_READINGS/READING_READER1.csv');raw2=load(BASE/'LOCKED_READINGS/PRIMARY_READER2.csv')
craw1=load(BASE/'LOCKED_READINGS/CENTROIDS_READER1.csv');craw2=load(BASE/'LOCKED_READINGS/CENTROIDS_READER2.csv')
order1=load(BASE/'READING_ORDER_READER1.csv');order2=load(BASE/'READING_ORDER_READER2.csv')
for label,rows,order in [('r1',raw1,order1),('r2',raw2,order2),('c1',craw1,order1),('c2',craw2,order2)]:
    check('order_'+label,[(x['order'],x['code']) for x in rows]==[(x['order'],x['code']) for x in order])
p1=key(raw1,'code');p2=key(raw2,'code');c1=key(craw1,'code');c2=key(craw2,'code')
check('90_30_90_30',list(map(len,[p1,p2,c1,c2]))==[90,30,90,30])
codes=[x['code'] for x in order2]
primary=Counter((p1[c]['class'],p2[c]['primary_class']) for c in codes)
cm=Counter((c1[c]['C'],c2[c]['indicator_c']) for c in codes)
for name,want in [('CONFUSION_PRIMARY',primary),('CONFUSION_C',cm)]:
    rows=load(A/(name+'.csv'))
    got={(x['reader1'],x['reader2']):int(x['n']) for x in rows}
    check(name+'_from_original_labels',sum(got.values())==30 and all(v==want[k] for k,v in got.items()))
metrics={
 'primary_exact_all30':(sum(v for (x,y),v in primary.items() if x==y),30),
 'reader1_U_all30':(sum(p1[c]['class']=='U' for c in codes),30),
 'reader2_U_all30':(sum(p2[c]['primary_class']=='U' for c in codes),30),
 'C_exact_all30_including_NV':(sum(v for (x,y),v in cm.items() if x==y),30),
 'C_exact_both_evaluable':(sum(c1[c]['C']==c2[c]['indicator_c'] for c in codes if c1[c]['C']!='non_valutabile' and c2[c]['indicator_c']!='non_valutabile'),sum(c1[c]['C']!='non_valutabile' and c2[c]['indicator_c']!='non_valutabile' for c in codes)),
 'C_reader1_NV_all30':(sum(c1[c]['C']=='non_valutabile' for c in codes),30),
 'C_reader2_NV_all30':(sum(c2[c]['indicator_c']=='non_valutabile' for c in codes),30),
 'C_at_least_one_NV_all30':(sum(c1[c]['C']=='non_valutabile' or c2[c]['indicator_c']=='non_valutabile' for c in codes),30),
 'border_exact_all30':(sum(c1[c]['border_contact']==c2[c]['mask_image_border_contact'] for c in codes),30)}
for row in load(A/'AGREEMENT.csv'):
    n,d=metrics[row['metric']]
    check('agreement_'+row['metric'],n==int(row['numerator']) and d==int(row['denominator']) and same(row['fraction'],Decimal(n)/d))

mapping=key(load(BASE/'CODE_MAP.csv'),'code')
selection=key(load(ROOT/'results/DOMINANT/DOMINANT_HARP_SELECTION.csv'),'HARPNUM')
variants=key(load(ROOT/'results/DOMINANT/DOMINANT_HARP_CHECKS.csv'),'HARPNUM')
register=load(A/'REGISTER.csv')
check('register_120_unique',len(register)==120 and len({x['HARPNUM'] for x in register})==120)
reg=key(register,'HARPNUM')
for x in register:
    s=selection[x['HARPNUM']]
    check('register_original_measure_'+x['HARPNUM'],x['T_REC']==s['T_REC'] and x['group']==s['group'] and x['kind']==s['kind'] and x['in_S']==s['in_S'] and same(x['s_bl_P1'],s['s_bl_P1']) and same(x['abs_sbl'],s['abs_sbl']))
    c=x['code']
    if c:
        check('labels_preserved_'+c,x['class_r1']==p1[c]['class'] and x['C_r1']==c1[c]['C'] and x['HARPNUM']==mapping[c]['HARPNUM'] and (x['class_r2']==p2[c]['primary_class'] and x['C_r2']==c2[c]['indicator_c'] if c in p2 else not x['class_r2'] and not x['C_r2']))
    else:
        check('historical_kept_separate_'+x['HARPNUM'],x['group']=='25S' and x['historical_class'] and not x['class_r1'] and not x['C_r1'])
check('common_composition_7_3',all(sum(mapping[c]['group']==g and mapping[c]['kind']==k for c in codes)==n for g in ['24N','24S','25N'] for k,n in [('dominante',7),('controllo',3)]))

catalogue=load(ROOT/'results/P1/P1_SBL_CATALOG_BY_HARP.csv');den={};base_n=0
for row in catalogue:
    if row['role']=='control' or row['valid_bl']!='1' or row['cycle'] not in ('24','25','24.0','25.0'):continue
    group=str(int(dec(row['cycle'])))+('N' if dec(row['lat_mean_deg'])>=0 else 'S')
    v=dec(row['s_bl']);d=den.setdefault(group,dict(net=Decimal(0),absolute=Decimal(0),n=0))
    d['net']+=v;d['absolute']+=abs(v);d['n']+=1;base_n+=1
check('full_base_size',base_n==4189)
for group,d in den.items():
    one=next(x for x in register if x['group']==group)
    check('full_base_'+group,int(one['group_n'])==d['n'] and same(one['group_sum_abs'],d['absolute']) and same(one['group_sum_net'],d['net']))

def chosen(cohort,group,grouping,label,kind='all'):
    col={'new_reader1':'class_r1','new_reader2_common':'class_r2','historical_25S':'historical_class'}[cohort]
    if grouping=='indicator_C':col='C_r1' if cohort=='new_reader1' else 'C_r2'
    candidates=[x for x in register if x['group']==group and (x['cohort']=='historical_25S' if cohort=='historical_25S' else x['cohort']=='new_A2') and (cohort!='new_reader2_common' or x['class_r2']) and (kind=='all' or x['kind']==kind)]
    return candidates,[x for x in candidates if x[col]==label]

for row in load(A/'CLASS_SOURCE.csv'):
    scope,part=chosen(row['cohort'],row['group'],row['grouping'],row['label'],row['kind'])
    net=total(part,'s_bl_P1');absolute=total(part,'abs_sbl');g=den[row['group']]
    check('class_source_'+row['cohort']+'_'+row['group']+'_'+row['grouping']+'_'+row['label']+'_'+row['kind'],
       int(row['n'])==len(part) and int(row['n_in_S'])==sum(int(x['in_S']) for x in part) and int(row['n_examined_scope'])==len(scope) and same(row['sum_net'],net) and same(row['sum_abs'],absolute) and same(row['share_abs_full_P1_group'],frac(absolute,g['absolute'])) and same(row['share_abs_examined_scope'],frac(absolute,total(scope,'abs_sbl'))))
sens=load(A/'SENSITIVITY_BY_CLASS.csv')
for row in sens:
    _,part=chosen(row['cohort'],row['group'],row['grouping'],row['label'])
    v=row['variant'];usable=[x for x in part if variants[x['HARPNUM']][v+'_possible']=='1']
    delta=[dec(variants[x['HARPNUM']][v+'_s_bl'])-dec(x['s_bl_P1']) for x in usable]
    net=sum(delta,Decimal(0)) if usable else None
    absolute=sum(map(abs,delta),Decimal(0)) if usable else None
    scale=sum((abs(dec(x['s_bl_P1'])) for x in usable),Decimal(0))
    check('sensitivity_'+row['cohort']+'_'+row['group']+'_'+row['grouping']+'_'+row['label']+'_'+v,
       int(row['n_examined'])==len(part) and int(row['n_comparable'])==len(usable) and int(row['n_missing'])==len(part)-len(usable) and same(row['delta_sum'],net,scale) and same(row['sum_abs_delta'],absolute,scale) and same(row['delta_rel_full_P1_abs'],None if net is None else net/den[row['group']]['absolute']) and same(row['abs_delta_rel_full_P1_abs'],None if absolute is None else absolute/den[row['group']]['absolute']))
# A decomposition by classes must retain the old aggregate totals, including cancellation.
for row in load(ROOT/'results/DOMINANT/DOMINANT_HARP_VARIANTS.csv'):
    if row['variant'] not in ('bmap1','uniform'):continue
    cohort='historical_25S' if row['group']=='25S' else 'new_reader1'
    selected=[x for x in sens if x['cohort']==cohort and x['group']==row['group'] and x['grouping']=='primary_class' and x['variant']==row['variant']]
    net=sum((dec(x['delta_sum']) for x in selected if x['delta_sum']),Decimal(0))
    check('existing_variant_total_'+row['group']+'_'+row['variant'],sum(int(x['n_comparable']) for x in selected)==int(row['n_comparable']) and same(net,row['delta_sum'],den[row['group']]['absolute']))

priority=load(A/'PRIORITY_GROUPS.csv');counts=[]
for row in priority:
    group=row['group'];b=[c for c,x in p1.items() if x['class']=='B' and mapping[c]['group']==group]
    conservative=[c for c in b if c not in p2 or p2[c]['primary_class']=='B']
    def share(cc):return sum((abs(dec(selection[mapping[c]['HARPNUM']]['s_bl_P1'])) for c in cc),Decimal(0))/den[group]['absolute']
    first,second=share(b),share(conservative);one=first>=Decimal('.1');two=second>=Decimal('.1')
    counts.append((one,two))
    check('priority_'+group,len(b)==int(row['reader1_B_n']) and len(conservative)==int(row['conservative_B_n']) and same(row['reader1_B_share_full_P1_abs'],first) and same(row['conservative_B_share_full_P1_abs'],second) and one==bool(int(row['reader1_reaches_10pct'])) and two==bool(int(row['conservative_reaches_10pct'])))
d=load(A/'PRIORITY_DECISION.csv')[0]
decision=sum(x for x,y in counts)>=2 and sum(y for x,y in counts)>=2 and metrics['primary_exact_all30'][0]>=24 and metrics['reader1_U_all30'][0]<=3 and metrics['reader2_U_all30'][0]<=3
check('operational_decision',d['all_operational_conditions_met']==str(decision) and d['status']=='propose_separate_representative_S_design_only')
check('no_input_changed',all(sha(ROOT/f)==h for f,h in inputs.items()))
check('HEAD_unchanged',git('rev-parse','HEAD')==head)
OUT.mkdir(parents=True,exist_ok=True)
with (OUT/'REVIEW_CHECKS.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['check','passed'],lineterminator='\n');w.writeheader();w.writerows(checks)
metadata=dict(review_type='internal_post_hoc_same_author_not_external',git_reference=head,
    created_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(Path(__file__)),
    reviewed_report_sha256=sha(ROOT/'docs/MORPHOLOGY_RESULTS.md'),
    inputs=inputs,checks_passed=len(checks),review_checks_sha256=sha(OUT/'REVIEW_CHECKS.csv'),
    scope='independent implementation using csv/Decimal, same author; no relabelling or new scientific analysis',
    formatting_findings=['Unescaped literal pipes in two Markdown table headers.','Tiny nonzero percentages rendered as 0.000% need an explicit rounding note.'])
(OUT/'META.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'reference':head,'operational_conditions_met':decision},indent=2))

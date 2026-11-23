"""Audit preserved S2 diagnostic products and parser precision; no SEALED or T3 re-estimate.
The two S2 fits reuse the common M implementation and are a numerical reproduction check.
"""
from pathlib import Path
import importlib.util,csv,hashlib,json
import numpy as np,pandas as pd
root=Path(__file__).resolve().parents[1]
def module(name,filename):
 s=importlib.util.spec_from_file_location(name,root/'scripts'/filename);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=module('diag','t3_mwo_s2_diagnosis.py');R=module('recount','t3_mwo_s2_diagnosis_recount.py')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=root/'results/T3_MWO_S2_DIAGNOSIS_R4';meta=json.loads((out/'META.json').read_text());receipt=json.loads((root/'results/T3_MWO_S2_DIAGNOSIS_R4_RECOUNT/RECEIPT.json').read_text())
assert receipt['passed']==receipt['total']==19 and receipt['partial'] is False and all(c['ok'] is True for c in receipt['checks'])
assert receipt['diagnosis_meta_sha256']==h(out/'META.json')
assert set(meta['inputs_sha256'])==R.EXPECTED_INPUTS
for n,v in meta['inputs_sha256'].items():assert h(root/n)==v,n
for n,v in meta['products_sha256'].items():assert h(out/n)==v,n
assert not D.chain_problems()
parser={}
for path,cols in [(D.STAB/'WL_TILTS.csv',['gamma_wl','d_wl']),(D.REL/'MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv',['joy_gamma_deg','separation_deg'])]:
 with path.open() as f:raw=list(csv.DictReader(f))
 rt=pd.read_csv(path,float_precision='round_trip');default=pd.read_csv(path)
 for col in cols:
  ref=np.array([float(row[col]) if row[col] else np.nan for row in raw]);actual=rt[col].to_numpy(float)
  assert np.array_equal(ref,actual,equal_nan=True)
  parser[path.name+':'+col]=float(np.nanmax(np.abs(actual-default[col].to_numpy(float))))
sub=D.load_subset();own=R.own_subset();assert len(sub)==len(own)==4694
assert list(zip(sub.noaa,sub.day))==list(zip(own.noaa,own.day))
g=R.own_g(own);gm=own.gamma_mwo.to_numpy(float);gw=own.gamma_wl.to_numpy(float);wrap=R.axial(gm-gw)-(gm-gw)
dec=json.loads((out/'DECOMPOSITION.json').read_text())
for k,v in {'g_d':g@own.d_wl,'g_gamma_mwo':g@gm,'g_gamma_wl':g@gw,'g_r':g@wrap}.items():assert abs(dec[k]-v)<1e-9
assert (wrap<-1e-9).sum()==72 and (wrap>1e-9).sum()==108
F=pd.read_csv(out/'FITS.csv',float_precision='round_trip');groups,_=R.own_groups(own,R.own_sources());expected={'S2 complete':np.ones(len(own),bool),**{k:groups[k] for k in groups if k not in ['all','N','S','source missing or non-alphabetic']},'without |d_WL| > 45':np.abs(own.d_wl)<=45}
assert len(F)==len(expected)==19
maxdiff=0.
for row in F.itertuples():
 ss=own[expected[row.label]].reset_index(drop=True);gg=R.own_g(ss);assert row.n==len(ss)
 e=abs(row.beta-gg@ss.d_wl);maxdiff=max(maxdiff,float(e));assert e<1e-8
boundary=int((F.phi_at_bound|F.kappa_at_bound).sum());assert boundary==13
assert list(F.loc[(F.lo>0)|(F.hi<0),'label'])==['dpd_area tercile 3']
reference=json.loads((D.STAB/'STABILITY.json').read_text())['S2']
rtfit=D.A.s2_fit(sub)
old=sub.copy();wl=pd.read_csv(D.STAB/'WL_TILTS.csv',dtype={'noaa':str});old['d_wl']=wl.loc[wl.wl_status=='ok','d_wl'].to_numpy()
oldfit=D.A.s2_fit(old)
fields=['beta','se','lo','hi','var_a','var_b','phi','kappa','sigma_x2']
rt_delta={k:float(rtfit[k]-reference[k]) for k in fields};old_delta={k:float(oldfit[k]-reference[k]) for k in fields}
assert all(v==0. for v in rt_delta.values())
result={'receipt':'19/19 complete and bound','all_input_product_hashes_verified':True,'python_float_and_round_trip_equal':True,'max_parser_differences':parser,'round_trip_fit_minus_saved':rt_delta,'default_fit_minus_saved':old_delta,'independent_point_estimates':19,'max_abs_point_difference':maxdiff,'wraps_minus180_plus180':[72,108],'fit_boundary_count':boundary,'sealed_read':False,'original_T3_not_reestimated':True}
print(json.dumps(result,indent=2))

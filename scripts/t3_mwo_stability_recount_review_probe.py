"""Full stability recount on synthetic data; no real sealed response is read."""
from pathlib import Path
import hashlib,importlib.util,json,math,sys,tempfile
from types import SimpleNamespace
import numpy as np,pandas as pd
root=Path(__file__).resolve().parents[1]
def load(n):
 s=importlib.util.spec_from_file_location(n,root/'scripts'/f'{n}.py');m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
A=load('t3_mwo_analysis');EX=load('t3_mwo_stability_extras');R=load('t3_mwo_stability_recount');RC=R.RC
print('RECOUNT SHA256',hashlib.sha256((root/'scripts/t3_mwo_stability_recount.py').read_bytes()).hexdigest())

def row_line(kind,day,noaa,lat,lon,area):
 s=list(' '*96)
 for at,txt in ((0,f'{kind} {day:%Y %m %d} 12 00 00'),(22,f'{noaa:>6}'),(53,f'{area:5d}'),(59,f'{lat:6.2f}'),(66,f'{lon:6.2f}'),(73,f'{0.:6.2f}')):
  s[at:at+len(txt)]=txt
 return ''.join(s)

with tempfile.TemporaryDirectory() as td:
 td=Path(td);cat=td/'cat';chk=td/'check';val=td/'val';stab=td/'stab';data=td/'dpd'
 for p in (cat,chk,val,stab,data):p.mkdir()
 rows=[];groups=[];spots=[];daily=[]
 for i in range(124):
  day=pd.Timestamp('2011-01-01')+pd.Timedelta(days=i)
  hem='N' if i%2==0 else 'S';lat=(1 if hem=='N' else -1)*(10+i%7);sg=1 if hem=='N' else -1
  noaa=str(10000+i)
  groups.append(row_line('g',day,noaa,lat,100.,200))
  spots.extend([row_line('s',day,noaa,lat-sg*.5,103.,100),row_line('s',day,noaa,lat+sg*.5,97.,100)])
  daily.append(f'd {day:%Y %m %d} 12 00 00 GYUL 1 2 3 4 0 0 0')
  rows.append(dict(record_set='all',noaa=noaa,day=day.strftime('%Y-%m-%d'),cycle=24,epoch='E8',hemisphere=hem,
   CR=2106+i//10,A_main=.5+(i//10)/6,sinlat=math.sin(math.radians(abs(lat))),phi_mwo=1e21*(1+(i%5)/10),
   isolated=i<120,n_neighbours=0 if i<120 else 1,rank=1,abs_lcm=4.))
 al=pd.DataFrame(rows);iso=al.iloc[:120].copy().assign(record_set='isolated').reset_index(drop=True)
 d=pd.concat([iso,al],ignore_index=True);d.to_csv(cat/'DESIGN.csv',index=False)
 (cat/'COVERAGE.json').write_text(json.dumps({'outcome':'informativo'}))
 for y in range(1974,2013):(data/f'gDPD{y}.txt').write_text('\n'.join(groups) if y==2011 else '')
 (data/'sDPD2011.txt').write_text('\n'.join(spots));(data/'dailyDPD1974_2016.txt').write_text('\n'.join(daily))
 wl=A.wl_for_records
 A.wl_for_records=lambda frame:wl(frame,gdpd=data,sdpd=data)
 ident,kept,X,w=RC.matrix(iso);g=RC.projection(X,w)
 C=.5*abs(RC.ramp_true(iso,g,.2))
 (chk/'IDENTIFIABILITY.json').write_text(json.dumps({'joy':{'identifiable':bool(ident)}}))
 (chk/'TARGETS.json').write_text(json.dumps({'C':C,'delta_beta_20':-2*C}))
 (val/'ACCEPTANCE.json').write_text(json.dumps({'accepted_15deg':True}))
 gamma_wl,st=A.wl_for_records(iso);gamall,stall=A.wl_for_records(al)
 beta=2*C
 iso['gamma_mwo']=gamma_wl+beta*(iso.A_main-1)*iso.sinlat
 iso['gamma_wl']=gamma_wl;iso['wl_status']=st;iso['d_wl']=A.axial(iso.gamma_mwo-iso.gamma_wl)
 al['gamma_mwo']=gamall+beta*(al.A_main-1)*al.sinlat
 sealed=pd.DataFrame([dict(record_set=label,noaa=r.noaa,gamma_deg=r.gamma_mwo,leading_sign=1,hale_expected=1)
  for label,fr in [('isolated',iso),('all',al)] for r in fr.itertuples()])
 sealed.to_csv(cat/'SEALED.csv.gz',index=False)
 pars=dict(var_a=math.log(.0001),var_b=0.,phi=.5,kappa=.1,sigma_x2=.0001)
 key=pd.MultiIndex.from_arrays([iso.CR,iso.hemisphere]);codes,u=pd.factorize(key);cr=np.array([c for c,_ in u]);hh=np.array([h for _,h in u]);lp=np.log(w)
 se=RC.se_from_saved(SimpleNamespace(**pars),iso,g,codes,cr-cr.min(),hh,lp-lp.mean())
 beta=float(g@iso.d_wl.to_numpy());lo,hi=beta-RC.Z*se,beta+RC.Z*se
 status,nonzero=A.s2_outcome(lo,hi,C)
 by_hem={}
 for hem in 'NS':
  sh=iso[iso.hemisphere==hem].reset_index(drop=True)
  _,_,xh,wh=RC.matrix(sh);gh=RC.projection(xh,wh)
  bh=float(gh@sh.d_wl.to_numpy())
  kh=pd.MultiIndex.from_arrays([sh.CR,sh.hemisphere]);ch,uh=pd.factorize(kh)
  crh=np.array([x for x,_ in uh]);hh2=np.array([h for _,h in uh]);lph=np.log(wh)
  seh=RC.se_from_saved(SimpleNamespace(**pars),sh,gh,ch,crh-crh.min(),hh2,lph-lph.mean())
  lh,hh3=bh-RC.Z*seh,bh+RC.Z*seh
  by_hem[hem]=dict(state='stimato',n=len(sh),beta=bh,se=seh,lo=lh,hi=hh3,
    verdict='supportato' if hh3<0 else 'opposto' if lh>0 else 'non deciso',covered=int(lh<=0<=hh3),lo_above=int(lh>0),hi_below=int(hh3<0),**pars)
 s2=dict(state='stimato',n=len(iso),beta=beta,se=se,lo=lo,hi=hi,status=status,distinguishable_from_zero=nonzero,C=C,by_hemisphere=by_hem,
   verdict='supportato' if hi<0 else 'opposto' if lo>0 else 'non deciso',covered=int(lo<=0<=hi),lo_above=int(lo>0),hi_below=int(hi<0),**pars)
 vr=A.epoch_verifiable(iso);s1,t1=A.s1(iso,vr,reps=2000)
 unver=0.;rule=A.final_rule(s1['status'],status,unver,True,True,True)
 result=dict(S1=s1,S2=s2,unverifiable_share=unver,verifiable=sorted(f'{e}{h}' for (e,h),v in vr.items() if v),
  subset={'n':len(iso),'share':1.},rule={'outcome':rule[0],'reasons':rule[1]})
 # One reference gives an explicitly non-identifiable descriptive P1 fit, without a fit of M.
 EX.daily_sources=lambda path:dict(zip(al.day,['GYUL']*len(al)))
 EX.p1_records=lambda:pd.DataFrame({'noaa':[iso.noaa.iloc[0]],'day':[iso.day.iloc[0]],'gamma':[iso.gamma_mwo.iloc[0]-.3]})
 extras=EX.extras(A,iso,sealed,al)
 frames={'STABILITY.json':result,'S1_TABLE.csv':t1,'S3_HALE.csv':iso.assign(agree=True).groupby(['epoch','hemisphere']).agree.agg(['size','mean']).reset_index(),
  'S4.csv':A.s4_table(iso),'WL_TILTS.csv':iso[['noaa','day','epoch','hemisphere','wl_status','gamma_wl','d_wl']],**extras}
 def save_all():
  for name,obj in frames.items():
   if isinstance(obj,pd.DataFrame):obj.to_csv(stab/name,index=False)
   else:(stab/name).write_text(json.dumps(obj,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
  hashes={p.name:R.h256(p) for p in stab.iterdir() if p.name!='META.json'}
  (stab/'META.json').write_text(json.dumps({'products_sha256':hashes}))
 save_all()
 kwargs=dict(cat=cat,check_dir=chk,val=val,stab=stab,gdpd=data,sdpd=data,require_git=False)
 print('BASELINE C, beta, S1, rule:',C,beta,s1['status'],rule)
 baseline=R.check(out=td/'baseline_receipt',write=True,**kwargs)
 print('BASELINE RESULT',baseline)
 assert baseline,'Fixture must pass before probing mutations'
 # Reuse S1 only in mutation tests: the input table is unchanged in every case.
 original_s1=R.s1_own
 cached=original_s1(iso,vr,reps=2000)
 R.s1_own=lambda *args,**kw:cached
 records={}
 def mutation(label,mutate,restore):
  mutate();save_all()
  records[label]=R.check(out=td/label,write=True,**kwargs)
  print('MUTATION',label,'ACCEPTED',records[label])
  restore();save_all()
 old=json.loads(json.dumps(result,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
 def wrong_C():
  result['S2']['C']=100*C;result['S2']['status']='scarto contenuto';result['rule']['outcome']='verdetto';result['rule']['reasons']=''
 def restore_C():
  result.clear();result.update(json.loads(json.dumps(old)))
 mutation('wrong_C_creates_verdict',wrong_C,restore_C)
 oldlo,oldhi=result['S2']['lo'],result['S2']['hi']
 mutation('wrong_S2_bounds',lambda:result['S2'].update(lo=999.,hi=1000.),lambda:result['S2'].update(lo=oldlo,hi=oldhi))
 oldhem=json.loads(json.dumps(result['S2']['by_hemisphere']))
 mutation('wrong_S2_hemisphere',lambda:result['S2']['by_hemisphere']['N'].update(beta=999.),lambda:result['S2'].__setitem__('by_hemisphere',oldhem))
 p1=extras['S2_P1.json'];oldp=json.loads(json.dumps(p1))
 mutation('wrong_P1_result',lambda:p1.update(n_matched=999,median_d=999.),lambda:(p1.clear(),p1.update(oldp)))
 t=frames['S4_DWL_ALL.csv'];orig=t.copy()
 mutation('wrong_S4_medians',lambda:t.__setitem__('median',999.),lambda:(t.__setitem__('median',orig['median'])))
 table=frames['S3_HALE.csv'];ep=table.epoch.copy()
 mutation('wrong_S3_labels',lambda:table.__setitem__('epoch','E1'),lambda:table.__setitem__('epoch',ep))
 flags=frames['S1_TABLE.csv'].flag.copy()
 mutation('wrong_S1_flags',lambda:frames['S1_TABLE.csv'].__setitem__('flag',True),lambda:frames['S1_TABLE.csv'].__setitem__('flag',flags))
 print('SUMMARY',json.dumps(records))
 sys.exit(1 if any(records.values()) else 0)

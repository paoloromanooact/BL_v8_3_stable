"""Exercise the proposed wiring in a temporary copy, on synthetic inputs only."""
from pathlib import Path
import importlib.util,json,sys,tempfile,subprocess,shutil,hashlib
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np,pandas as pd
root=Path(__file__).resolve().parents[1]
_scratch=tempfile.TemporaryDirectory(prefix='bl_stability_wiring_')
tree=Path(_scratch.name)
(tree/'scripts').mkdir()
names=('scripts/t3_mwo_analysis.py','scripts/t3_mwo_stability_extras.py')
before={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
for n in names:shutil.copyfile(root/n,tree/n)
if 'IMPLEMENTED = False' in (tree/names[1]).read_text():
 subprocess.run(['git','apply','--directory='+str(tree),'--unsafe-paths',str(root/'patches/T3_MWO_STABILITY_WIRING.patch')],cwd=root,check=True)
sys.path.insert(0,str(root/'python'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
 sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
A=load('wire_review',tree/'scripts/t3_mwo_analysis.py')
EX=load('wire_extras',tree/'scripts/t3_mwo_stability_extras.py')
assert EX.selftest()
d=pd.DataFrame(dict(noaa=['1','2','3','4'],day=['2011-01-01','2011-01-02','2011-01-03','2011-01-04'],
 epoch=['E8']*4,hemisphere=['N','N','S','S'],CR=[2100,2100,2101,2101],A_main=[.5,1.,1.5,2.],
 sinlat=[.2]*4,phi_mwo=[1e21]*4,rank=[1]*4,abs_lcm=[4.]*4,n_neighbours=[0,1,0,1],isolated=[True,False,True,False]))
iso=d.iloc[[0,2]].reset_index(drop=True)
sealed=pd.DataFrame([dict(record_set=s,noaa=r.noaa,gamma_deg=2.,leading_sign=1,hale_expected=1)
                     for s,frame in [('all',d),('isolated',iso)] for r in frame.itertuples()])
EX.daily_sources=lambda path:dict(zip(d.day,['GYUL']*4))
EX.p1_records=lambda:pd.DataFrame(dict(noaa=['1','3'],day=['2011-01-01','2011-01-03'],gamma=[1.,1.]))
with tempfile.TemporaryDirectory() as td:
 td=Path(td)
 for k in ('cat','check','val','reading'):(td/k).mkdir()
 A.CAT=td/'cat';A.OUT_CHECK=td/'check';A.OUT_VAL=td/'val';A.OUT_STAB=td/'stability'
 A.VAL_READ=td/'reading'
 for folder in (A.CAT,A.OUT_CHECK,A.OUT_VAL):(folder/'META.json').write_text('{}')
 (A.VAL_READ/'READ.json').write_text('{}')
 (A.CAT/'COVERAGE.json').write_text(json.dumps({'outcome':'informativo'}))
 (A.OUT_CHECK/'TARGETS.json').write_text(json.dumps({'C':.5}))
 (A.OUT_CHECK/'IDENTIFIABILITY.json').write_text(json.dumps({'joy':{'identifiable':True}}))
 (A.OUT_VAL/'ACCEPTANCE.json').write_text(json.dumps({'accepted_15deg':False}))
 calls=[];saved={}
 A.gate_problem=lambda *args:None
 A.read_sealed=lambda:(calls.append('sealed') or sealed.copy())
 A.load_design=lambda set_name='isolated':iso.copy() if set_name=='isolated' else d.copy()
 A.wl_for_records=lambda frame:(frame.gamma_mwo.to_numpy()-.5,np.array(['ok']*len(frame)))
 A.s1=lambda *args:({'status':'stabile fra epoche'},pd.DataFrame())
 A.s2_fit=lambda frame:{'state':'stimato','lo':-.1,'hi':.1,'beta':0.,'se':.1,'n':len(frame)}
 A.write_out=lambda out,frames,meta:saved.update(frames=frames,meta=meta)
 fake_spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda mod:None))
 with patch('importlib.util.spec_from_file_location',return_value=fake_spec),patch('importlib.util.module_from_spec',return_value=EX):
  assert A.stability('protocol','amendment')==0
  wanted={'S1_DPD_SOURCES.csv','S2_P1.json','S2_P1_MATCHED.csv','S4_ISOLATION.csv','S4_DWL_ALL.csv'}
  assert wanted<=set(saved['frames'])
  assert saved['frames']['S2_P1.json']['n_matched']==2
  assert saved['frames']['S4_ISOLATION.csv'].n_groups.sum()==4
  assert saved['meta']['extras_sha256']==A.sha(tree/'scripts/t3_mwo_stability_extras.py')
  assert calls==['sealed']
  print('PASS: patched stability writes all five extra products and the helper SHA on synthetic inputs')
  EX.IMPLEMENTED=False
  try:A.stability('protocol','amendment')
  except SystemExit as exc:assert 'not implemented' in str(exc)
  else:raise AssertionError('False implementation flag did not block stability')
  assert calls==['sealed']
  print('PASS: implementation flag blocks stability before reading the synthetic seal')
print('No real MWO sealed input or real P1 tilt read; active files unchanged')

assert before=={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
# The extended patch must gate beta3 on a complete, bound stability receipt.
with tempfile.TemporaryDirectory() as td:
 ds={k:Path(td)/k for k in ('cat','cat_recount','check','check_recount','val','val_recount','val_read','stab','stab_recount')}
 for p in ds.values():p.mkdir()
 def put(k,n,obj):(ds[k]/n).write_text(json.dumps(obj))
 def receipt(k,key,meta):put(k,'RECEIPT.json',{'passed':1,'total':1,'partial':False,'checks':[{'ok':True}],key:A.sha(meta)})
 put('cat','META.json',{});put('cat','COVERAGE.json',{'outcome':'informativo'})
 receipt('cat_recount','catalogue_meta_sha256',ds['cat']/'META.json')
 put('check','META.json',{'catalogue_meta_sha256':A.sha(ds['cat']/'META.json')})
 put('check','IDENTIFIABILITY.json',{'joy':{'identifiable':True}})
 receipt('check_recount','design_check_meta_sha256',ds['check']/'META.json')
 put('val','META.json',{'design_check_meta_sha256':A.sha(ds['check']/'META.json')})
 put('val','ACCEPTANCE.json',{'accepted_15deg':False,'problems':[]})
 receipt('val_recount','validation_meta_sha256',ds['val']/'META.json')
 put('val_read','READ.json',{'acceptance_sha256':A.sha(ds['val']/'ACCEPTANCE.json'),'recount_receipt_sha256':A.sha(ds['val_recount']/'RECEIPT.json')})
 put('stab','META.json',{})
 with patch.object(A,'committed',return_value=True):
  assert A.chain_problem('estimate',ds) is not None
  receipt('stab_recount','stability_meta_sha256',ds['stab']/'META.json')
  assert A.chain_problem('estimate',ds) is None
  rec=json.loads((ds['stab_recount']/'RECEIPT.json').read_text())
  rec['partial']=True;put('stab_recount','RECEIPT.json',rec)
  assert A.chain_problem('estimate',ds) is not None
  rec['partial']=False;rec['stability_meta_sha256']='0'*64;put('stab_recount','RECEIPT.json',rec)
  assert A.chain_problem('estimate',ds) is not None
 print('PASS: estimate requires a complete stability receipt bound to the current META')

_scratch.cleanup()

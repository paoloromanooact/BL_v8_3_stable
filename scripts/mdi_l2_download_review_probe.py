"""Synthetic interruption/transport probes and read-only plan provenance test. No network/FITS from JSOC."""
import contextlib,importlib.util,io,json,shutil,sys,tempfile,types
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def load(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/'scripts'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=load('fd_interruption','mdi_fd_fetch.py');R=load('plan_provenance','mdi_l2_replan_a1_recount.py')
out={}
with tempfile.TemporaryDirectory() as td:
 td=Path(td);fx=D.fixture(td/'fx',['/SUM/interrupt']);calls=[]
 def interrupt(target,dest,*args):
  calls.append(target);Path(dest).write_bytes(b'partial');raise KeyboardInterrupt('synthetic interruption')
 kw=dict(dest=td/'dest',state=td/'state',transport=interrupt,ledger=td/'ledger',**fx)
 for k in range(3):
  try:
   with contextlib.redirect_stdout(io.StringIO()):D.run(**kw)
  except KeyboardInterrupt:pass
 out['interrupted_file_transport_calls']=len(calls)
 out['open_attempts']=D.LG.totals(td/'ledger')['open_attempts']

 class TE(Exception):
  kind='http_500'
 def fail(target,dest,*args):
  dest.with_suffix('.transport.json').write_text(json.dumps(dict(requests=1,final_url='http://jsoc.stanford.edu'+target)))
  raise TE('synthetic worker failure')
 fake=types.SimpleNamespace(transfer_a1=fail,TransportError=TE)
 old=sys.modules.get('mdi_hmi_patch_download');sys.modules['mdi_hmi_patch_download']=fake
 try:
  try:D.real_transport('/SUM/one',td/'one.part',100,None,1)
  except TE as e:out['error_requests_forwarded_from_sidecar']=getattr(e,'requests',None)
 finally:
  if old is None:sys.modules.pop('mdi_hmi_patch_download',None)
  else:sys.modules['mdi_hmi_patch_download']=old

 # The real metadata plan is already preserved and read; this checks only its selected-coordinate integrity.
 sel=td/'sel';shutil.copytree(ROOT/'results/MDI_PILOT_SELECTION',sel)
 s=pd.read_csv(sel/'SAMPLE.csv',dtype={'noaa':str},float_precision='round_trip');s.loc[0,'lat']+=1
 s.to_csv(sel/'SAMPLE.csv',index=False)
 old_sel=R.SEL;R.SEL=sel
 try:
  with contextlib.redirect_stdout(io.StringIO()):out['modified_selection_with_unchanged_meta_accepted']=R.check(write=False)
 finally:R.SEL=old_sel
print(json.dumps(out,indent=2))

assert out['interrupted_file_transport_calls'] == 2
assert out['open_attempts'] == 2
assert out['error_requests_forwarded_from_sidecar'] == 1
assert out['modified_selection_with_unchanged_meta_accepted'] is False

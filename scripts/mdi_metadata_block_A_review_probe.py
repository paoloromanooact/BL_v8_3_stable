"""Offline probes of metadata collection and recount. No sockets or real science outputs."""
from pathlib import Path
import contextlib,copy,hashlib,importlib.util,io,json,tempfile
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('m_A','mdi_fd_metadata.py');R=load('r_A','mdi_fd_metadata_recount.py')
out={}
empty={'status':0,'count':0,'keywords':[{'name':n,'values':[]} for n in ['T_REC','T_OBS','QUALITY','INTERVAL']],'segments':[{'name':'data','values':[]}]}
try:
    out['empty_answer_status']=M.choose(M.records_from_answer(empty),'2000-06-01 10:00:00')[0]['status']
except Exception as exc:out['empty_answer_status']=type(exc).__name__+': '+str(exc)

class Response:
    status=200
    def __init__(self): self.body=io.BytesIO(b'x'*(M.LG.METADATA_CAP_BYTES+100000))
    def read1(self,n):return self.body.read(n)
class Connection:
    def __init__(self,*a,**k):pass
    def request(self,*a,**k):pass
    def getresponse(self):return Response()
    def close(self):pass
old=M.http.client.HTTPConnection;M.http.client.HTTPConnection=Connection
try:
    M.http_json({})
except M.TransportFailure as exc:out['oversized_body_bytes_read']=exc.nbytes;out['metadata_body_cap']=M.LG.METADATA_CAP_BYTES
finally:M.http.client.HTTPConnection=old

with tempfile.TemporaryDirectory() as td:
    td=Path(td);fx=M.fixture(td,n=2)
    rows=[M.rec('2000.06.01_10:00:00_TAI','2000.06.01_10:00:32_TAI',path='/SUM1/a'),M.rec('2000.06.01_11:36:00_TAI','2000.06.01_11:36:32_TAI',path='/SUM1/b')]
    def transport(*a,**k):return M.answer(rows),900,1
    with contextlib.redirect_stdout(io.StringIO()):M.fetch(td/'out',transport,td/'ledger',**fx)
    d=td/'out';original={p.name:p.read_bytes() for p in d.iterdir()}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    def check():
        with contextlib.redirect_stdout(io.StringIO()):return R.check(d,fx['sel'],write=False,real=False)
    out['recount_base_accepted']=check()
    changes={
      'plan_size':('DOWNLOAD_PLAN.csv',lambda t:t.assign(size=1)),
      'choice_path':('CHOICES.csv',lambda t:t.assign(A_path='/SUMevil/wrong')),
      'choice_dt':('CHOICES.csv',lambda t:t.assign(A_dt_h=100)),
    }
    for name,(file,fn) in changes.items():
        for f,b in original.items():(d/f).write_bytes(b)
        fn(pd.read_csv(d/file,dtype={'noaa':str})).to_csv(d/file,index=False)
        meta=json.loads((d/'META.json').read_text());meta['products_sha256'][file]=sha(d/file);(d/'META.json').write_text(json.dumps(meta))
        out['mutated_'+name+'_accepted']=check()
    for f,b in original.items():(d/f).write_bytes(b)
    meta=json.loads((d/'META.json').read_text());meta['completeness']='incomplete';meta['requests_ok']=0
    (d/'META.json').write_text(json.dumps(meta));out['mutated_completeness_accepted']=check()
print(json.dumps(out,indent=2))

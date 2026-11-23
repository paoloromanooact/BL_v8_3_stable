"""Synthetic query-window regression for the metadata recount. No network."""
import contextlib,hashlib,importlib.util,io,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,p):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('meta_qprobe','mdi_fd_metadata.py');R=load('recount_qprobe','mdi_fd_metadata_recount.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as td:
    td=Path(td);fx=M.fixture(td,n=1);led=td/'ledger.jsonl';out=td/'out'
    def fake(q):return M.answer([M.rec('r0','2000.06.01_10:00:32_TAI')]),100,1
    with contextlib.redirect_stdout(io.StringIO()):M.fetch(out,fake,led,**fx)
    kw=dict(sel=fx['sel'],sel_rec=fx['sel_rec'],ledger=led,protocol=fx['protocol'],freeze=fx['freeze'],write=False,synthetic=True)
    with contextlib.redirect_stdout(io.StringIO()):base=R.check(out,**kw)
    a=json.loads((out/'ANSWERS.jsonl').read_text());wrong='mdi.fd_M_96m_lev182[1999.01.01_00:00:00_TAI-1999.01.01_01:00:00_TAI]';a['ds']=wrong
    (out/'ANSWERS.jsonl').write_text(json.dumps(a)+'\n')
    entries=[json.loads(x) for x in led.read_text().splitlines()]
    for e in entries:
        if e['phase']=='start':e['target']=wrong
    led.write_text(''.join(json.dumps(e)+'\n' for e in entries))
    meta=json.loads((out/'META.json').read_text());meta['products_sha256']['ANSWERS.jsonl']=sha(out/'ANSWERS.jsonl');(out/'META.json').write_text(json.dumps(meta))
    with contextlib.redirect_stdout(io.StringIO()):changed=R.check(out,**kw)
    assert base and not changed
    print(json.dumps(dict(base_accepted=base,wrong_query_and_ledger_accepted=changed),indent=2))

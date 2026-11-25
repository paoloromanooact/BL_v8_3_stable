"""Read-only audit of the committed Q4 recount receipt and its hashes; no scientific CSV is parsed."""
from pathlib import Path
import hashlib,json,subprocess
import argparse
_ap=argparse.ArgumentParser(description=__doc__);_ap.add_argument('--out',required=True,type=Path);args=_ap.parse_args()
if args.out.exists():raise SystemExit('refusing to overwrite an existing audit')
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
blob=lambda rev,rel:subprocess.check_output(['git','show',f'{rev}:{rel}'],cwd=ROOT)
receipt_rel='results/MDI_Q4_PROSPECTIVE_RECOUNT/RECEIPT.json';rp=ROOT/receipt_rel
r=json.loads(rp.read_text());nfrel='docs/MDI_PILOT_Q4_NOTE_FREEZE.json';nf=json.loads((ROOT/nfrel).read_text())
checks=[]
def ok(name,value):checks.append({'name':name,'ok':bool(value)})
ok('receipt identical to preserved 8924285 blob',rp.read_bytes()==blob('8924285',receipt_rel))
ok('strict complete receipt 21/21 with unique checks',type(r.get('passed')) is int and type(r.get('total')) is int and r['passed']==r['total']==21 and len(r.get('checks',[]))==21 and len({c['name'] for c in r['checks']})==21 and all(type(c.get('ok')) is bool and c['ok'] for c in r['checks']) and r.get('partial') is False)
expected={'CELL_COUNTS.csv','CRITERIA.csv','DESIGNS.csv','META.json','MF_POOLS.csv','NOT_COMPUTABLE.csv','PROOFS.csv','RAW.csv.gz','RUN.exit','RUN.log','SUMMARY.csv','YIELD_EFFECTS.csv'}
out=ROOT/'results/MDI_Q4_PROSPECTIVE'
ok('exact output set and all current hashes',set(r['outputs_sha256'])==expected=={p.name for p in out.iterdir()} and all(sha(out/n)==h for n,h in r['outputs_sha256'].items()))
ok('all outputs match preserved pre-reading dab5a33 blobs',all(hashlib.sha256(blob('dab5a33','results/MDI_Q4_PROSPECTIVE/'+n)).hexdigest()==h for n,h in r['outputs_sha256'].items()))
code='scripts/mdi_q4_recount.py';approved='a6c0a72d227c26d15f5ca584f22bdf12e63c3222028ffe4eaab3f33aa0233398'
ok('recount code exact approved d303c3a source',r['recount_sha256']==approved==sha(ROOT/code)==hashlib.sha256(blob('d303c3a',code)).hexdigest())
ok('note receipt fixed to reviewed fingerprint',sha(ROOT/nfrel)=='0f9b3acc01e6a58a182685259350f71a8caf82edc2381c209f210d89b5b2410d')
extras={nfrel,'docs/MDI_PILOT_Q4_NOTE.md','docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2.md','docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2_FREEZE.json','docs/PROTOCOL_MDI_TILT_PILOT.md','docs/MDI_Q4_PREP_COUNTS_RULES.md'}
inputs=set(nf['inputs_sha256'])|set(nf['reused_code_sha256'])|extras
ok('exact recorded input set and all current hashes',set(r['inputs_sha256'])==inputs and all(sha(ROOT/n)==h for n,h in r['inputs_sha256'].items()))
ok('input and reused-code hashes equal frozen note values',all(r['inputs_sha256'][n]==h for key in ['inputs_sha256','reused_code_sha256'] for n,h in nf[key].items()))
ok('preservation precedes recount commit',subprocess.run(['git','merge-base','--is-ancestor','dab5a33','8924285'],cwd=ROOT).returncode==0)
report={'passed':sum(x['ok'] for x in checks),'total':len(checks),'checks':checks,'receipt_sha256':sha(rp),'receipt_commit':'8924285','recount_commit':'d303c3a','scope':'Integrity/provenance review only; no scientific result tables parsed; not a new numerical recount.'}
print(json.dumps(report,indent=2));args.out.write_text(json.dumps(report,indent=2)+'\n');assert all(c['ok'] for c in checks)

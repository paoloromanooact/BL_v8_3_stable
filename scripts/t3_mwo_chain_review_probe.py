"""Synthetic counterexample for the review of f12d093. No real tilt is read.

Run from the BL repository; the output shows whether the reviewed guard accepts
these cases. This probe is separate from the method's scientific validation.
"""
from pathlib import Path
import importlib.util,json,tempfile
from unittest.mock import patch
root=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('a',root/'scripts/t3_mwo_analysis.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
with tempfile.TemporaryDirectory() as td:
 dirs={k:Path(td)/k for k in ('cat','cat_recount','check','val','val_recount','val_read','stab')}
 for p in dirs.values():p.mkdir()
 def put(k,f,x): (dirs[k]/f).write_text(json.dumps(x))
 put('cat','META.json',{'revision':1});put('cat','COVERAGE.json',{'outcome':'informativo'})
 put('cat_recount','RECEIPT.json',{'passed':5,'total':5,'catalogue_meta_sha256':a.sha(dirs['cat']/'META.json')})
 put('check','META.json',{'catalogue_meta_sha256':a.sha(dirs['cat']/'META.json'),'revision':1})
 put('check','IDENTIFIABILITY.json',{'joy':{'identifiable':True}})
 put('val','META.json',{'design_check_meta_sha256':a.sha(dirs['check']/'META.json')})
 put('val','ACCEPTANCE.json',{'accepted_15deg':False,'problems':[]})
 put('val_recount','RECEIPT.json',{'passed':5,'total':5,'validation_meta_sha256':a.sha(dirs['val']/'META.json')})
 put('val_read','READ.json',{'acceptance_sha256':a.sha(dirs['val']/'ACCEPTANCE.json'),'recount_receipt_sha256':a.sha(dirs['val_recount']/'RECEIPT.json')})
 with patch.object(a,'committed',return_value=True):
  print('initial stability chain:',a.chain_problem('stability',dirs))
  put('check','META.json',{'catalogue_meta_sha256':a.sha(dirs['cat']/'META.json'),'revision':2})
  print('old validation after changed design META:',a.chain_problem('stability',dirs))
  print('validation before any design-recount receipt:',a.chain_problem('validate',dirs))
  put('cat_recount','RECEIPT.json',{'catalogue_meta_sha256':a.sha(dirs['cat']/'META.json')})
  print('catalogue receipt with no passed/total:',a.chain_problem('design-check',dirs))

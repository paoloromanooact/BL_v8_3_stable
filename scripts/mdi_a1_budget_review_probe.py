"""Synthetic sequential ledger test: reservation is not cumulative consumption. No network/FITS."""
import importlib.util,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('ledger_under_review',ROOT/'scripts/mdi_l2_ledger.py')
L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'ledger.jsonl'
    for j in range(90):
        i,why=L.reserve('metadata',str(j),L.METADATA_CAP_BYTES,p);assert i is not None,why
        L.finish(i,'metadata',1,3879+int(j<44),'ok',path=p)
    for j in range(161):
        i,why=L.reserve('fits',str(j),L.FILE_CAP_BYTES,p);assert i is not None,(j,why)
        L.finish(i,'fits',2,1_600_000,'ok',path=p)
    t=L.totals(p)
    assert t==dict(requests=412,bytes=257949154,files=161,open_attempts=0)
    print(json.dumps(dict(reservation_bytes=L.FILE_CAP_BYTES,completed_files=161,totals=t,all_reserved_32MiB_sequential_files_admitted=True),indent=2))

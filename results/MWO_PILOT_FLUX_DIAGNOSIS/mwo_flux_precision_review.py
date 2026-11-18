import sys, json, tarfile, hashlib, math
from pathlib import Path
import numpy as np
import pandas as pd
root=Path('/home/gianluca/BL_v8_3_stable')
sys.path.insert(0,str(root/'scripts'))
import mwo_pilot_tilt as runner
import mwo_pilot_recount as recount
rows=pd.read_csv(root/'results/MWO_PILOT/ROWS.csv')
ev=rows[rows.status=='ok']
checks=[]
for year,g in ev.groupby(ev.member.str.slice(0,4)):
    wanted=set(g.member)
    with tarfile.open(runner.MWO_DATA/f'MWO_{year}.tar.gz') as archive:
        blobs={m.name:archive.extractfile(m).read() for m in archive.getmembers() if m.name in wanted}
    for r in g.itertuples():
        data=blobs[r.member]
        h,field64=recount.read_fits(data)
        pos=0
        while True:
            block=data[pos:pos+2880]
            if len(block)!=2880:raise ValueError('truncated header')
            pos+=2880
            if any(block[i:i+80].startswith(b'END     ') for i in range(0,2880,80)):break
        typ={16:'>i2',32:'>i4',-32:'>f4',-64:'>f8'}[int(h['BITPIX'])]
        count=int(h['NAXIS1']*h['NAXIS2'])
        # Independent reader, with float32 applied BEFORE the FITS scaling operations.
        field32=np.frombuffer(data,offset=pos,count=count,dtype=typ).astype(np.float32).reshape(int(h['NAXIS2']),int(h['NAXIS1']))
        field32=field32*float(h.get('BSCALE',1.))+float(h.get('BZERO',0.))
        a=recount.measure(h,field64,r.dpd_lat,r.dpd_lon)
        b=recount.measure(h,field32,r.dpd_lat,r.dpd_lon)
        if a is None or b is None:raise ValueError('record became unavailable')
        saved=r.mwo_flux_pos_mx+r.mwo_flux_neg_mx
        tilt,lead=recount.p1_tilt_convention(b['cp'],b['cn'])
        checks.append(dict(HARPNUM=r.HARPNUM,old_rel=a['flux']/saved-1,matched_rel=b['flux']/saved-1,
             tilt_error=abs((tilt-r.mwo_tilt_deg+180)%360-180),leading_equal=lead==r.mwo_leading_sign,
             bscale=h.get('BSCALE',1.),bzero=h.get('BZERO',0.),bitpix=h['BITPIX']))
    print('checked year',year,len(checks),flush=True)
x=pd.DataFrame(checks)
summ=dict(diagnostic='post-run diagnosis of FITS reader precision, original receipt and tolerance preserved',n=len(x),
  old_rel_min=float(x.old_rel.min()),old_rel_median=float(x.old_rel.median()),old_rel_max=float(x.old_rel.max()),
  max_matched_rel=float(x.matched_rel.abs().max()),max_tilt_error=float(x.tilt_error.max()),all_leading_equal=bool(x.leading_equal.all()),
  bitpix=sorted(x.bitpix.unique().tolist()),bscale=sorted(x.bscale.unique().tolist()),
  product_hashes_ok=all(hashlib.sha256((root/'results/MWO_PILOT'/n).read_bytes()).hexdigest()==h for n,h in json.loads((root/'results/MWO_PILOT/META.json').read_text())['products_sha256'].items()))
Path('/tmp/mwo_flux_precision_review.json').write_text(json.dumps(summ,indent=2)+'\n')
print(json.dumps(summ,indent=2))
print('saved statistics',recount.verdict_of(ev))
print('selection causes',rows.status.value_counts().to_dict())

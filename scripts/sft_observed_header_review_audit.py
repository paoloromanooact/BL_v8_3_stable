from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from astropy.io import fits
import argparse
_ap=argparse.ArgumentParser(description=__doc__);_ap.add_argument('--out',required=True,type=Path);args=_ap.parse_args()
if args.out.exists():raise SystemExit('refusing to overwrite an existing audit')
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'results/P1/P1_SBL_CATALOG_BY_HARP.csv'
c=pd.read_csv(path,usecols=['HARPNUM','T_REC','role','family_rank','valid_bl'])
c['t']=pd.to_datetime(c.T_REC.str.removesuffix('_TAI'),format='%Y.%m.%d_%H:%M:%S')
p=c[c.role=='primary'].set_index('HARPNUM');k=c[c.role=='control'].set_index('HARPNUM');j=p.join(k,lsuffix='_p',rsuffix='_c');g=(j.t_c-j.t_p).dt.total_seconds()/86400.
j=j[(g>=1)&(g<=4.5)&(j.valid_bl_p==1)&(j.family_rank_p==0)]
mismatch=[];wrap=[];n=0
for h,r in j.iterrows():
 keys=[]
 for side in ['p','c']:
  tr=r['T_REC_'+side];st=tr[:4]+tr[5:7]+tr[8:10]+'_'+tr[11:13]+tr[14:16]+tr[17:19]+'_TAI';stem=f'hmi.sharp_cea_720s.{h}.{st}';f=ROOT/'data/sharp/fits'/tr[:4]/(stem+'.Br.fits');kp=f.with_name(stem+'.keys.json');kk=json.loads(kp.read_text());keys.append(kk)
  with fits.open(f,memmap=True,lazy_load_hdus=True,do_not_scale_image_data=True) as hd:
   hdr=hd[-1].header;shape=(int(hdr['NAXIS1']),int(hdr['NAXIS2']))
  guessed=(int(round(2*kk['CRPIX1']-1)),int(round(2*kk['CRPIX2']-1)));n+=1
  if shape!=guessed:mismatch.append({'harp':int(h),'role':side,'actual_nx_ny':shape,'guessed_nx_ny':guessed,'crpix':[kk['CRPIX1'],kk['CRPIX2']]})
 if abs(float(keys[0]['CRVAL1'])-float(keys[1]['CRVAL1']))>180:wrap.append(int(h))
out={'different_branch_count':len(wrap),'pairs':len(j),'headers_read':n,'fits_pixels_read':False,'metadata_columns_read':['HARPNUM','T_REC','role','family_rank','valid_bl'],'dimensions_mismatch_count':len(mismatch),'dimensions_mismatch_examples':mismatch[:8],'different_CRVAL1_branch_pairs':wrap,'catalogue_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
args.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

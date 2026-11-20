"""Independent reconstruction of six metadata-only MWO R4 coverage tables. No tilt read."""
from pathlib import Path
import hashlib,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
 o=ROOT/'results/T3_MWO_COVERAGE_R4';c=ROOT/'results/T3_MWO_CATALOGUE_R4'
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 m=json.loads((o/'META.json').read_text());assert m['catalogue_meta_sha256']==sha(c/'META.json')
 assert all(sha(o/n)==h for n,h in m['products_sha256'].items())
 cm=json.loads((c/'META.json').read_text())
 for n in ['DESIGN.csv','ATTEMPTS.csv.gz','LOSSES.csv','MAGNETOGRAMS.csv.gz']:assert sha(c/n)==cm['products_sha256'][n]
 d=pd.read_csv(c/'DESIGN.csv');a=pd.read_csv(c/'ATTEMPTS.csv.gz',low_memory=False)
 loss=pd.read_csv(c/'LOSSES.csv');g=pd.read_csv(c/'MAGNETOGRAMS.csv.gz',low_memory=False)
 def same(own,name):
  saved=pd.read_csv(o/name);own=own.copy()
  if 'value' in own:own['value']=own.value.astype(str);saved['value']=saved.value.astype(str)
  pd.testing.assert_frame_equal(own,saved,check_dtype=False,check_names=False)
 for dim,name in [('cycle','RECORDS_BY_CYCLE_HEMISPHERE.csv'),('epoch','RECORDS_BY_EPOCH_HEMISPHERE.csv')]:
  same(d.groupby(['record_set',dim,'hemisphere']).size().unstack(fill_value=0).reset_index(),name)
 same(d[d.record_set=='isolated'].groupby(['epoch','res_class']).size().unstack(fill_value=0).reset_index(),'RESOLUTION_BY_EPOCH.csv')
 same(a.assign(epoch=a.epoch.fillna('(none)')).groupby(['epoch','status']).size().unstack(fill_value=0).reset_index(),'ATTEMPT_STATUS_BY_EPOCH.csv')
 sel=loss[loss.dimension=='A_tercile'].copy();sel['groups']=sel[['record','all_attempts_failed','no_candidate_day']].sum(axis=1)
 sel['fraction_with_record']=sel.record/sel.groups;same(sel.reset_index(drop=True),'SELECTION_BY_ACTIVITY.csv')
 saved=pd.read_csv(o/'MAGNETOGRAM_STATUS.csv').set_index('status').n.sort_index()
 pd.testing.assert_series_equal(g.groupby('status').size().sort_index(),saved,check_names=False)
 print('PASS: six coverage tables independently reconstructed; source and product hashes match; no sealed data read')
if __name__=='__main__':main()

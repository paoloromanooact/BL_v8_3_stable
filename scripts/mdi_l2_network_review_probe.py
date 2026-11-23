"""Offline review probes: synthetic responses/FITS only, no sockets or real MDI pixels."""
from pathlib import Path
import importlib.util,json,tempfile,contextlib,io
import numpy as np
import pandas as pd
from astropy.io import fits
ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('md_review','mdi_fd_metadata.py');L=load('led_review','mdi_l2_ledger.py')
D=load('dl_review','mdi_fd_fetch.py');A=load('ad_review','mdi_fd_adapter.py')
out={}
rows=[M.rec('r0','2000.06.01_10:00:32_TAI'),M.rec('r1','2000.06.01_11:36:32_TAI',q='MISSING')]
t=M.records_from_answer(M.answer(rows))
t=t.assign(dt_h=[0,1.6],year='2000',act_class=1,hemisphere='N',area_class=1,cohort='M1')
try:
    M.composition(t);out['composition_missing_quality']='accepted'
except Exception as exc: out['composition_missing_quality']=type(exc).__name__+': '+str(exc)
rows=[M.rec('r0','2000.06.01_10:00:32_TAI',interval='MISSING'),M.rec('r1','2000.06.01_11:36:32_TAI',interval='300')]
c,_=M.choose(M.records_from_answer(M.answer(rows)),pd.Timestamp('2000-06-01 10:00:00'))
out['mixed_missing_interval_pair_status']=c['pair_status']
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    # An interrupted metadata read could have consumed its body cap.
    L.start('metadata','synthetic',td/'interrupted.jsonl')
    out['interrupted_metadata_bytes']=L.totals(td/'interrupted.jsonl')['bytes']
    i=L.start('metadata','previous',td/'nearcap.jsonl')
    L.finish(i,'metadata',1,L.CAP_BYTES-1,'ok',path=td/'nearcap.jsonl')
    out['metadata_allowed_with_one_byte_left']=L.can_start('metadata',0,td/'nearcap.jsonl')[0]
    # No selection receipt or valid selection META: fake transport still gets invoked.
    sel=td/'sel';sel.mkdir()
    pd.DataFrame(dict(noaa=['1','2'],day=['2000-06-01']*2,t_dpd=['2000-06-01 10:00:00']*2,level2=[True]*2,
                      act_class=[1]*2,hemisphere=['N']*2,area_class=[1]*2,cohort=['M1']*2)).to_csv(sel/'SAMPLE.csv',index=False)
    (sel/'META.json').write_text('{}')
    old=M.SEL;M.SEL=sel;calls=[]
    class PartialError(ConnectionError): bytes_received=1234
    def fake(query):
        calls.append(query)
        if len(calls)==1: raise PartialError('partial body then error')
        return M.answer([M.rec('r0','2000.06.01_10:00:32_TAI',q='0x200')]),800,1
    try:
        with contextlib.redirect_stdout(io.StringIO()): M.fetch(td/'metadata',transport=fake,ledger=td/'fetch.jsonl')
    finally: M.SEL=old
    out['requests_without_selection_receipt']=len(calls)
    out['recorded_metadata_bytes']=L.totals(td/'fetch.jsonl')['bytes']
    out['received_metadata_bytes_in_fixture']=1234+800
    alt=pd.read_csv(td/'metadata/ADMISSIBLE_ALTERNATIVES.csv')
    out['alternative_count_groups']=int(alt.n_groups.sum())
    out['selected_groups_in_fixture']=2
    # Fits resume: same-size different pixels accepted without a recorded prior digest.
    md=td/'fits_meta';md.mkdir();dest=td/'fits';dest.mkdir()
    target=dest/D.file_name('r0')
    fits.PrimaryHDU(np.zeros((1024,1024),dtype=np.int16)).writeto(target)
    before=D.sha(target)
    with fits.open(target,mode='update') as hd: hd[0].data[:]=123
    after=D.sha(target)
    pd.DataFrame([dict(T_REC='r0',path='/SUM1/S0/data.fits',size=target.stat().st_size)]).to_csv(md/'DOWNLOAD_PLAN.csv',index=False)
    (md/'META.json').write_text('{}')
    def never(*args): raise AssertionError('must not make requests')
    with contextlib.redirect_stdout(io.StringIO()): D.run(md,dest,td/'fits_out',never,td/'fits.jsonl',verify_upstream=False)
    out['resume_modified_file_status']=pd.read_csv(td/'fits_out/MANIFEST.csv').status.iloc[0]
    out['resume_modified_digest_changed']=before!=after
    # Shared adapter contract with synthetic pixel coordinates.
    k=dict(CDELT1=2.,CDELT2=3.,RSUN_OBS=1000.)
    mu=np.ones((2,10));lat=np.zeros((2,10));lon=np.repeat([[1.],[359.]],10,axis=1)
    b=np.repeat([[100.],[-100.]],10,axis=1)
    out['adapter_missing_quality_status']=A.measure(b,k,0.,0.,50.,geom=(lat,lon,mu))['status']
    try:
        A.measure(b,dict(k,QUALITY='0x00000000'),0.,0.,50.,geom=(lat,lon,mu))
        out['adapter_hex_quality']='accepted'
    except Exception as exc: out['adapter_hex_quality']=type(exc).__name__
    expected=abs(k['CDELT1']*k['CDELT2'])*(A.RSUN_CM/k['RSUN_OBS'])**2
    out['non_square_pixel_area_ratio']=float(A.pixel_area_cm2(k,1.)/expected)
print(json.dumps(out,indent=2))

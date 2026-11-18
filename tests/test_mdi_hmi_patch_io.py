"""Offline regression checks for the native patch acquisition and CEA adapter."""
import json
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pytest
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import mdi_hmi_patch_io as io
import mdi_hmi_patch_download as download

T = "2010.07.01_00:00:00_TAI"
REC = "123|"+T


def fixture(series):
    schema = {"keywords": [dict(name=k, type="double", units="m") for k in io.NUMERIC],
              "segments": [dict(name=k, units="Enumerated" if k=="bitmap" else "Gauss") for k in io.SEGMENTS[series]]}
    kw = dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="degree", CUNIT2="deg",
              CRPIX1=2, CRPIX2=1.5, CRVAL1=60., CRVAL2=-10., CROTA2=0.,
              CDELT1=.12, CDELT2=.12, CRLT_OBS=-10., CRLN_OBS=60.,
              DSUN_OBS=1.5e11, RSUN_REF=6.96e8, T_OBS=T, T_REC=T, QUALITY=0,
              TELESCOP="SOHO" if series==io.MDI else "SDO/HMI", INSTRUME="MDI" if series==io.MDI else "HMI")
    kw[io.ID[series]] = "123"
    files = {s:dict(path=f"/SUM1/D2/S00000/{s}.fits",dims="3x2") for s in io.SEGMENTS[series]}
    return kw, files, schema


def response(series):
    kw,files,_ = fixture(series)
    return dict(count=1,status=0,keywords=[dict(name=k,values=[v]) for k,v in kw.items()],
                segments=[dict(name=k,values=[v["path"]],dims=[v["dims"]]) for k,v in files.items()])


@pytest.mark.parametrize("series", [io.MDI, io.HMI])
def test_native_compressed_record_and_scaling(tmp_path,series):
    kw,files,schema = fixture(series)
    kw = io.metadata(response(series),series,REC,files)
    name = "magnetogram"
    maskcode=37 if series==io.MDI else 33
    paths={}
    for s,values in [(name, [[-2,0,3],[-1,1,2]]),("bitmap", [[maskcode]*3,[0]*3])]:
        path=tmp_path/(s+".fits")
        h=fits.CompImageHDU(np.array(values,dtype=np.int16))
        if s==name:
            h.header["BSCALE"]=4
        fits.HDUList([fits.PrimaryHDU(),h]).writeto(path)
        paths[s]=path,io.sha(path)
    hdr=io.physical_header(kw,series,0,(2,3),schema)
    lon,lat=io.geometry.lonlat_maps(hdr,(2,3))
    view=io.viewing_geometry(lon,lat,observer_lon_deg=60,observer_lat_deg=-10,distance_m=1.5e11,radius_m=6.96e8)
    cert=dict(state="certified",dims="3x2",min_mu=view["mu"].min())
    r=io.adapt_record(series,REC,files,paths,kw,0,cert,schema)
    np.testing.assert_equal(r["arrays"][name][0],[-8,0,12])
    assert r["footprint"].sum()==3
    assert r["area_cm2"]==pytest.approx((6.96e10*np.deg2rad(.12))**2)
    with pytest.raises(ValueError,match="minimum"):
        io.adapt_record(series,REC,files,paths,kw,0,dict(cert,min_mu=.9),schema)


@pytest.mark.parametrize("wrong",["quality","spacecraft","dimensions","unit","identity","path"])
def test_wrong_reference_rejected(wrong):
    kw,files,schema=fixture(io.MDI)
    doc=response(io.MDI)
    if wrong=="quality":kw["QUALITY"]=512
    if wrong=="spacecraft":kw["TELESCOP"]="SDO"
    if wrong=="dimensions":kw["CRPIX1"]=3
    if wrong=="unit":kw["CUNIT1"]="arcsec"
    if wrong=="identity":doc["keywords"][-1]["values"]=["999"]
    if wrong=="path":doc["segments"][0]["values"]=["/other.fits"]
    with pytest.raises(ValueError):
        io.metadata(doc,io.MDI,REC,files)
        io.physical_header(kw,io.MDI,0,(2,3),schema)


def test_ledger_restart_and_corruption(tmp_path):
    ledger=dict(events=[],prior_attempts=41,prior_seconds=550.)
    def fake(target,path,limit,expected,timeout):
        path.write_bytes(b"hello")
    def fetch():
        return download.acquire(tmp_path,ledger,"example","/test",100,(),lambda p:None, fake)
    path,digest=fetch()
    assert fetch()==(path,digest) and len(ledger["events"])==1
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA-256"):
        fetch()
    assert json.loads((tmp_path/"LEDGER.json").read_text())["events"][0]["bytes"]==5


@pytest.mark.parametrize("case", ["attempts","time","volume","interrupted_twice"])
def test_budget_refusals(tmp_path,case):
    e=dict(key="a",state="pending",fits=True,seconds=1,bytes=20)
    st=dict(events=[e],prior_attempts=41,prior_seconds=550.)
    if case=="attempts": st["prior_attempts"]=download.REQUEST_LIMIT-1
    if case=="time":st["prior_seconds"]=download.SECONDS_LIMIT-1
    if case=="volume":e["bytes"]=download.TOTAL_LIMIT-1
    if case=="interrupted_twice":st["events"].append(e.copy())
    with pytest.raises((ValueError, download.Unavailable)):
        download.acquire(tmp_path,st,"a","/test",20,(20,),lambda p:None,lambda *args:pytest.fail())


@pytest.mark.parametrize("status,length,accept", [(200,4,True),(302,4,False),(200,8,False),(200,None,False)])
def test_local_transport(tmp_path,status,length,accept):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            if length:self.send_header("Content-Length",str(length))
            self.end_headers()
            self.wfile.write(b"test")
        def log_message(self,*args): pass
    with HTTPServer(("127.0.0.1",0),Handler) as server:
        server.timeout=5
        thread=threading.Thread(target=server.handle_request)
        thread.start()
        path=tmp_path/"file"
        proc=download.get_context("spawn").Process(target=download.receive,args=(
            "127.0.0.1","/",path,4,(4,),4,server.server_port))
        proc.start();proc.join(8);thread.join(6)
        assert (proc.exitcode==0)==accept
        if accept: assert path.read_bytes()==b"test"

def test_acquire_partial_resume_and_br_only_adapter(tmp_path,monkeypatch):
    # Exercise record metadata, file identity, the ledger, a failure, a retry and R0-only loading.
    import io as stream
    from urllib.parse import parse_qs, urlsplit
    root=tmp_path/"patch_download"
    pair=dict(slot="1", smarp_series=io.MDI, hmi_series=io.HMI, smarp_record=REC,
              hmi_record=REC,quality_mdi="0",quality_hmi="0",dt_obs_s="0")
    records={}; docs={}; blobs={}; cert={}; schemas={}
    for series,side in [(io.MDI,"smarp"),(io.HMI,"hmi")]:
        kw,files,sch=fixture(series)
        schemas[series]=sch
        doc=response(series)
        for sg in doc["segments"]:
            name=sg["name"]
            hdu=fits.PrimaryHDU(np.array([[33,33,0],[33,0,0]] if name=="bitmap" else [[250,-200,0],[0,0,0]],dtype="int16"))
            buf=stream.BytesIO()
            hdu.writeto(buf)
            path=f"/SUM1/D{1 if side=='hmi' else 2}/S00000/{name}.fits"
            sg["values"]=[path]
            blobs[path]=buf.getvalue()
            files[name].update(slot="1",path=path,reported_bytes=str(len(blobs[path])-1))
        docs[series]=doc
        hdr=io.physical_header(kw,series,0,(2,3),sch)
        lon,lat=io.geometry.lonlat_maps(hdr,(2,3))
        view=io.viewing_geometry(lon,lat,observer_lon_deg=60,observer_lat_deg=-10,distance_m=1.5e11,radius_m=6.96e8)
        cert[side,REC]=dict(state="certified",dims="3x2",min_mu=view["mu"].min())
        records[series,REC]=files
    data=([pair],records,cert,schemas,41,550, sum(map(len,blobs.values())))
    calls=[]
    def fake(target,path,limit,expected,timeout):
        calls.append(target)
        if expected:
            if target=="/SUM1/D1/S00000/Bp.fits" and calls.count(target)==1:
                raise OSError("temporary unavailability")
            path.write_bytes(blobs[target])
        else:
            series=parse_qs(urlsplit(target).query)["ds"][0].split("[")[0]
            path.write_text(json.dumps(docs[series]))
    download.run(root,data,fake)
    assert io.readjson(root/"MANIFEST.json")["status"]=="partial"
    download.run(root,data,fake)
    assert io.readjson(root/"MANIFEST.json")["status"]=="complete"
    assert len(calls)==10   # 2 metadata + 7 FITS + 1 failed attempt
    monkeypatch.setattr(io,"plan",lambda:([pair],records))
    monkeypatch.setattr(io,"reference_inputs",lambda:(cert,schemas))
    monkeypatch.setattr(io,"BASE",tmp_path)
    patch=io.load_selected(1,io.HMI,["Br","bitmap"])
    assert set(patch["arrays"])=={"Br","bitmap"}
    assert patch["arrays"]["Br"][0,0]==250

"""Independent synthetic oracles for the MDI full-disk adapter. No network or real FITS.

--selftest validates the reference construction. --check-adapter compares production code with it;
an exit code 1 reports discrepancies, not permission to change the production code.
The geometry is the orthographic model of the frozen pilot, not a validation of instrument metadata.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
R_CM = 6.96e10


def frame(b0, l0):
    b, l = np.radians([b0, l0])
    observer = np.array([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)])
    west = np.array([-np.sin(l), np.cos(l), 0.0])
    north = np.cross(observer, west)
    return observer, west, north


def sphere(lat, lon):
    b, l = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)], axis=-1)


def rotated_image_matrix(k):
    a = np.radians(k['CROTA2'])
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]) @ np.diag([k['CDELT1'], k['CDELT2']])


def locate(lat, lon, b0=5., l0=359., roll=27., scales=(2., 2.), pixel=(15., 15.)):
    """Forward-project a known surface point and put it at a chosen zero-based image pixel."""
    o, w, n = frame(b0, l0)
    v = sphere(lat, lon)
    k = dict(QUALITY=0, CRLT_OBS=b0, CRLN_OBS=l0, CROTA2=roll, CDELT1=scales[0], CDELT2=scales[1], RSUN_OBS=1000.)
    projected = k['RSUN_OBS'] * np.array([v @ w, v @ n])
    offset = np.linalg.solve(rotated_image_matrix(k), projected)
    k['CRPIX1'], k['CRPIX2'] = pixel[0]+1-offset[0], pixel[1]+1-offset[1]
    return k, float(v @ o)


def image_vectors(k, x, y):
    """Own ray/sphere construction in the observer basis; x/y are zero-based pixel positions."""
    x, y = np.broadcast_arrays(x, y)
    offsets = np.stack([x+1-k['CRPIX1'], y+1-k['CRPIX2']], axis=-1)
    xy = np.einsum('ij,...j->...i', rotated_image_matrix(k), offsets) / k['RSUN_OBS']
    mu = np.sqrt(1. - np.sum(xy**2, axis=-1))
    o, w, n = frame(k['CRLT_OBS'], k['CRLN_OBS'])
    return mu[..., None]*o + xy[..., :1]*w + xy[..., 1:]*n, mu


def lonlat(v):
    return np.degrees(np.arcsin(v[..., 2])), np.degrees(np.arctan2(v[..., 1], v[..., 0])) % 360.


def area_jacobian(k, x, y, h=1e-3):
    dx = (image_vectors(k, x+h, y)[0]-image_vectors(k, x-h, y)[0])/(2*h)
    dy = (image_vectors(k, x, y+h)[0]-image_vectors(k, x, y-h)[0])/(2*h)
    return np.linalg.norm(np.cross(dx, dy), axis=-1) * R_CM**2


def expected_area(k, mu):
    return abs(k['CDELT1']*k['CDELT2'])*(R_CM/k['RSUN_OBS'])**2/mu


def angle(a, b):
    mid = (a+b)/np.linalg.norm(a+b)
    west = np.cross([0., 0., 1.], mid)
    west /= np.linalg.norm(west)
    north = np.cross(mid, west)
    return float(np.degrees(np.arctan2((b-a) @ north, (b-a) @ west)))


def bipole(lat0=15., cmd=25., b0=5., roll=27.):
    lon0 = (359.+cmd) % 360.
    k, _ = locate(lat0, lon0, b0=b0, roll=roll)
    yy, xx = np.mgrid[:31, :31]
    v, mu = image_vectors(k, xx, yy)
    lat, lon = lonlat(v)
    assert np.max(np.abs(lat-lat0)) < 6 and np.max(np.abs((lon-lon0+180)%360-180)) < 8
    br = np.zeros(mu.shape)
    br[3:10, 3:15] = 120.
    br[20:27, 17:29] = -240.
    return k, lat0, lon0, v, mu, br


def reference_measure(v, mu, br, k):
    area = expected_area(k, mu)
    result = {}
    cent = {}
    for label, mask in [('pos', br >= 50), ('neg', br <= -50)]:
        weights = np.abs(br[mask])*area[mask]
        c = np.sum(v[mask]*weights[:, None], axis=0)
        cent[label] = c/np.linalg.norm(c)
        result['n'+label] = int(mask.sum())
        result['flux_'+label+'_mx'] = float(weights.sum())
    positive_leading = abs(angle(cent['neg'], cent['pos'])) < 90.
    lead, follow = (cent['pos'], cent['neg']) if positive_leading else (cent['neg'], cent['pos'])
    result['leading_sign'] = 1 if positive_leading else -1
    result['tilt_deg'] = angle(lead, follow)
    return result


def run(adapter=False):
    checks = []
    def ok(name, passed, **details):
        checks.append(dict(name=name, ok=bool(passed), **details))
    max_geometric_error = 0.
    max_mu_error = 0.
    configurations = 0
    for b0 in (-7.25, 0., 7.25):
        for roll in (-31., 0., 27., 180.):
            for scale in ((2., 2.), (-2., 2.), (2., 3.)):
                for lat in (-25., 0., 25.):
                    for cmd in (-25., 0., 25.):
                        lon = (359.+cmd) % 360
                        k, target_mu = locate(lat, lon, b0=b0, roll=roll, scales=scale, pixel=(0., 0.))
                        v, m = image_vectors(k, 0., 0.)
                        a, l = lonlat(v)
                        e = max(abs(a-lat), abs((l-lon+180)%360-180))
                        max_mu_error = max(max_mu_error, float(abs(m-target_mu)))
                        max_geometric_error = max(max_geometric_error, float(e));configurations += 1
    ok('independent forward/ray roundtrip across observer latitude, roll, scales and longitude seam', max_geometric_error < 1e-10 and max_mu_error < 1e-12,
       configurations=configurations, max_angle_error_deg=max_geometric_error, max_mu_error=max_mu_error)
    area_errors = []
    for scales in ((2., 2.), (2., 3.), (-2., 3.)):
        k, mu = locate(15., 24., scales=scales)
        area_errors.append(abs(area_jacobian(k, 15., 15.)/expected_area(k, mu)-1))
    ok('spherical pixel area independently checked by numerical Jacobian', max(area_errors) < 1e-7, max_relative_error=float(max(area_errors)))
    k, la, lo, v, mu, br = bipole()
    ref = reference_measure(v, mu, br, k)
    ok('synthetic bipole is inside the full mu domain and has both polarities', mu.min() > .8 and ref['npos'] == ref['nneg'] == 84)
    omitted = reference_measure(v, mu, br*mu, k)
    doubled = reference_measure(v, mu, br/mu, k)
    ratio_omitted = omitted['flux_pos_mx']/ref['flux_pos_mx']
    ratio_doubled = doubled['flux_pos_mx']/ref['flux_pos_mx']
    ok('reference distinguishes omitted and doubled LOS/mu correction', ratio_omitted < .95 and ratio_doubled > 1.05,
       flux_ratio_without_correction=float(ratio_omitted), flux_ratio_double_correction=float(ratio_doubled))
    if adapter:
        spec = importlib.util.spec_from_file_location('mdi_fd_adapter_under_review', ROOT/'scripts/mdi_fd_adapter.py')
        A = importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
        errors, mu_errors = [], []
        for b0 in (-7.25, 0., 7.25):
            for roll in (-31., 0., 27., 180.):
                for scales in ((2., 2.), (-2., 2.), (2., 3.)):
                    for lat in (-25., 0., 25.):
                        for cmd in (-25., 0., 25.):
                            lon = (359.+cmd)%360
                            kk, target_mu = locate(lat, lon, b0, roll=roll, scales=scales, pixel=(0., 0.))
                            la2, lo2, mu2 = A.geometry(kk, (1, 1))
                            errors.append(max(abs(float(la2[0, 0])-lat), abs((float(lo2[0, 0])-lon+180)%360-180)))
                            mu_errors.append(abs(float(mu2[0, 0])-target_mu))
        ok('adapter registration against independent forward-projected surface points', max(errors) < 1e-10 and max(mu_errors) < 1e-12,
           configurations=len(errors), max_angle_error_deg=float(max(errors)), max_mu_error=float(max(mu_errors)))
        for name, scales in [('square', (2., 2.)), ('rectangular', (2., 3.))]:
            kk, m = locate(15., 24., scales=scales)
            ratio = A.pixel_area_cm2(kk, m)/area_jacobian(kk, 15., 15.)
            ok('adapter area '+name, abs(ratio-1) < 1e-7, ratio=float(ratio))
        for name, params in [('north', {}), ('south', dict(lat0=-20., cmd=-20., b0=-6., roll=-31.))]:
            kk, la, lo, vv, mm, radial = bipole(**params)
            observed = radial*mm
            expected = reference_measure(vv, mm, radial, kk)
            measured = A.measure(observed, kk, la, lo, 50.)
            flux_error = max(abs(measured.get(c, np.nan)/expected[c]-1) for c in ('flux_pos_mx', 'flux_neg_mx'))
            tilt_error = abs((measured.get('tilt_deg', np.nan)-expected['tilt_deg']+180)%360-180)
            ok('LOS/mu recovery, polarity, flux and tilt '+name, measured.get('status') == 'ok' and flux_error < 1e-9
               and tilt_error < 1e-8 and measured.get('leading_sign') == expected['leading_sign'],
               flux_relative_error=float(flux_error), tilt_error_deg=float(tilt_error))
            flipped = A.measure(-observed, kk, la, lo, 50.)
            ok('field reversal preserves geometry and reverses polarity '+name, flipped.get('leading_sign') == -measured.get('leading_sign')
               and abs(flipped.get('tilt_deg', np.nan)-measured.get('tilt_deg', np.nan)) < 1e-8)
        k, la, lo, v, mu, br = bipole()
        for count, status in [(20, 'ok'), (60, 'window_missing')]:
            observed = br*mu
            observed.flat[np.flatnonzero(br == 0)[:count]] = np.nan
            result = A.measure(observed, k, la, lo, 50.)
            ok('missing pixels '+str(count), result.get('status') == status and result.get('n_missing_win') == count)
        kk, _ = locate(0., np.degrees(np.arccos(.8)), b0=0., l0=0., roll=0.)
        result = A.measure(np.ones((31,31))*100, kk, 0., np.degrees(np.arccos(.8)), 50.)
        ok('full window mu guard rejects a window straddling mu=0.8', result.get('status') == 'window_outside_mu_domain')
        no_quality = dict(k);no_quality.pop('QUALITY')
        ok('missing QUALITY rejected', A.measure(br*mu, no_quality, la, lo, 50.).get('status') != 'ok')
        try:
            result = A.measure(br*mu, dict(k, QUALITY='0x00000000'), la, lo, 50.)
            ok('explicit hexadecimal QUALITY zero accepted', result.get('status') == 'ok')
        except (ValueError, TypeError) as exc:
            ok('explicit hexadecimal QUALITY zero accepted', False, error=type(exc).__name__)
        ok('QUALITY 0x200 rejected under the original rule', A.measure(br*mu, dict(k, QUALITY=512), la, lo, 50.).get('status') == 'quality_not_zero')
        with tempfile.TemporaryDirectory() as td:
            raw = np.array([[10,-20,-32768],[100,-100,0]],dtype=np.int16)
            hdu = fits.PrimaryHDU(raw)
            hdu.header['BSCALE'],hdu.header['BZERO'],hdu.header['BLANK'] = .1,3.5,-32768
            p=Path(td)/'synthetic_scaled_blank.fits';hdu.writeto(p)
            read = A.read_data(p)
            expected = raw.astype(float)*.1+3.5;expected[raw==-32768]=np.nan
            ok('FITS scaling and BLANK on a synthetic int16 file', np.allclose(read, expected, atol=1e-6, rtol=0, equal_nan=True))
    report=dict(mode='adapter comparison' if adapter else 'independent reference selftest', passed=sum(c['ok'] for c in checks),
                total=len(checks), checks=checks, real_data_read=False, network_used=False)
    print(json.dumps(report, indent=2))
    return report['passed'] == report['total']


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--selftest',action='store_true');g.add_argument('--check-adapter',action='store_true')
    args=p.parse_args();raise SystemExit(0 if run(args.check_adapter) else 1)

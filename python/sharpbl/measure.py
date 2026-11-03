"""Misura della sorgente BL per una singola mappa SHARP CEA.

Due metodi:
- "legacy": riproduce la v8.3 IDL di Paolo Romano (centroidi e distanze in
  pixel con scala unica, latitudine da sin(CRVAL2) + (j - CRPIX2) dmu, bitmap
  >= 1, ciclo dalla sola data). Serve solo per il confronto.
- "v84": geometria sferica dalla WCS completa, ciclo dal modulo cycle,
  soglia 100 G, bitmap configurabile.

In entrambi S_BL = hale_sign * Phi * d * cos(lambda) * sin(alpha).
Il metodo v84 calcola anche il contributo al dipolo assiale,
D = 3 / (4 pi R^2) * sum(Br sin(lambda) dA), che non richiede segno Hale ne'
assegnazione del ciclo.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np

from . import cycle as cyc
from . import geometry as geo

THRESHOLD_G = 100.0
MAX_ABS_BR_G = 10000.0
TILT_WARN_DEG = 60.0
RSUN_CM_LEGACY = 6.957e10


def parse_trec(t_rec: str) -> datetime:
    s = t_rec.replace("_TAI", "").replace("_", " ")
    for fmt in ("%Y.%m.%d %H:%M:%S.%f", "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"T_REC non riconosciuto: {t_rec}")


def base_mask(br, bitmap, bmap_min, max_abs_br):
    m = np.isfinite(br) & (np.abs(br) <= max_abs_br)
    if bitmap is not None:
        m &= np.isfinite(bitmap) & (bitmap >= bmap_min)
    return m


def quality(nmask, npos, nneg, values):
    """Stessi codici di sharp_bl_quality_flag della v8.3."""
    if nmask <= 0:
        return 4, "EMPTY_MASK"
    if npos <= 0 and nneg <= 0:
        return 3, "NO_POLARITIES"
    if npos <= 0:
        return 1, "NO_POSITIVE"
    if nneg <= 0:
        return 2, "NO_NEGATIVE"
    if not np.isfinite(values["phi_mx"]):
        return 5, "BAD_FLUX"
    if not all(np.isfinite(values[k]) for k in ("d_cm", "lat_mean_deg", "coslat", "sintilt", "s_bl")):
        return 6, "BAD_GEOMETRY"
    return 0, "OK"


def finish(out, nmask, npos, nneg, tilt_warn_deg=TILT_WARN_DEG):
    q, qs = quality(nmask, npos, nneg, out)
    out.update(nmask=int(nmask), npos=int(npos), nneg=int(nneg), quality_flag=q,
               quality_string=qs, valid_bl=int(q == 0))
    reason = qs if q else "NONE"
    if q == 0:
        reasons = []
        if out["hale_sign"] == -1:
            reasons.append("ANTI_HALE")
        if abs(out["tilt_reduced_deg"]) > tilt_warn_deg:
            reasons.append("LARGE_TILT")
        reason = "+".join(reasons) if reasons else "NONE"
    out["diagnostic_reason"] = reason
    out["suspicious_flag"] = int(reason != "NONE")
    return out


def empty_geometry():
    return dict(d_cm=np.nan, lat_mean_deg=np.nan, coslat=np.nan, tilt_deg=np.nan,
                tilt_reduced_deg=np.nan, sintilt=np.nan, s_bl=np.nan, leading_sign=0,
                expected_leading_sign=0, hale_sign=0)


def measure_legacy(br, bitmap, header, threshold=THRESHOLD_G, max_abs_br=MAX_ABS_BR_G, bmap_min=1,
                   cycle_mode="date", boundary=None):
    """Riproduzione della v8.3 IDL (process_sharp_day con LEADING_SIDE='XMAX').

    cycle_mode="date" (predefinito, v8.3) o "p1c" (regola del ciclo di P1/P1c, solo per il
    fattoriale esplorativo; usa la latitudine media di questa geometria).
    """
    ny, nx = br.shape
    m = base_mask(br, bitmap, bmap_min, max_abs_br)
    nmask = int(m.sum())
    d1 = np.radians(abs(float(header["CDELT1"])))
    d2 = np.radians(abs(float(header["CDELT2"])))
    area = RSUN_CM_LEGACY ** 2 * d1 * d2
    pixscale = RSUN_CM_LEGACY * np.sqrt(d1 * d2)
    strong = m & (np.abs(br) >= threshold)
    phi = float(np.abs(br[strong]).sum() * area) if strong.any() else 0.0
    pos = m & (br >= threshold)
    neg = m & (br <= -threshold)
    npos, nneg = int(pos.sum()), int(neg.sum())
    t = parse_trec(header["T_REC"])
    out = dict(method="legacy", phi_mx=phi, cycle=cyc.cycle_by_date(t), cycle_state="DATE",
               p_new=np.nan, **empty_geometry())
    if npos and nneg:
        yy, xx = np.mgrid[0:ny, 0:nx]
        wp, wn = br[pos], np.abs(br[neg])
        cp = np.array([(xx[pos] * wp).sum(), (yy[pos] * wp).sum()]) / wp.sum()
        cn = np.array([(xx[neg] * wn).sum(), (yy[neg] * wn).sum()]) / wn.sum()
        d = float(np.hypot(*(cp - cn)) * pixscale)
        j = np.arange(1, ny + 1, dtype=float)
        s = np.sin(np.radians(float(header["CRVAL2"]))) + (j - float(header["CRPIX2"])) * d2
        lat_rows = np.degrees(np.arcsin(np.clip(s, -1, 1)))
        lat_map = np.broadcast_to(lat_rows[:, None], br.shape)
        w = np.abs(br[strong])
        lat_mean = float((lat_map[strong] * w).sum() / w.sum())
        leading = 1 if cp[0] > cn[0] else -1
        if cycle_mode == "p1c":
            c_, p_, st_ = cyc.assign_cycle(t, lat_mean, boundary)
            out.update(cycle=c_, p_new=p_, cycle_state=st_)
        exp_lead = cyc.expected_leading_sign(out["cycle"], lat_mean)
        hale = 1 if leading == exp_lead else -1
        lead, follow = (cp, cn) if leading == 1 else (cn, cp)
        dx, dy = follow - lead
        norm = np.hypot(dx, dy)
        tilt = float(np.degrees(np.arctan2(dy, dx))) if norm > 0 else np.nan
        sintilt = float(dy / norm) if norm > 0 else np.nan
        coslat = float(np.cos(np.radians(lat_mean)))
        out.update(d_cm=d, lat_mean_deg=lat_mean, coslat=coslat, tilt_deg=tilt,
                   tilt_reduced_deg=geo.reduce_tilt_deg(tilt), sintilt=sintilt,
                   s_bl=hale * phi * d * coslat * sintilt, leading_sign=leading,
                   expected_leading_sign=exp_lead, hale_sign=hale)
    return finish(out, nmask, npos, nneg)


def measure_v84(br, bitmap, header, threshold=THRESHOLD_G, max_abs_br=MAX_ABS_BR_G,
                bmap_min=33, boundary=None, cycle_mode="p1c"):
    """Metodo corretto: geometria sferica, ciclo per latitudine nelle sovrapposizioni."""
    m = base_mask(br, bitmap, bmap_min, max_abs_br)
    nmask = int(m.sum())
    r = geo.rsun_cm(header)
    area = geo.pixel_area_cm2(header)
    lon, lat = geo.lonlat_maps(header, br.shape)
    strong = m & (np.abs(br) >= threshold) & np.isfinite(lon) & np.isfinite(lat)
    pos = strong & (br >= threshold)
    neg = strong & (br <= -threshold)
    npos, nneg = int(pos.sum()), int(neg.sum())
    phi_pos = float(br[pos].sum() * area)
    phi_neg = float(-br[neg].sum() * area)
    phi = phi_pos + phi_neg
    t = parse_trec(header["T_REC"])
    out = dict(method="v84", phi_mx=phi, phi_pos_mx=phi_pos, phi_neg_mx=phi_neg,
               cycle=np.nan, cycle_state="", p_new=np.nan,
               lon_pos=np.nan, lat_pos=np.nan, lon_neg=np.nan, lat_neg=np.nan,
               lon_mean_stony=np.nan, d_axial_g=np.nan, d_axial_bal_g=np.nan,
               **empty_geometry())
    if strong.any():
        w = np.abs(br[strong])
        lon_m, lat_m = geo.weighted_centroid(lon[strong], lat[strong], w)
        out["lat_mean_deg"] = lat_m
        out["coslat"] = float(np.cos(np.radians(lat_m)))
        crln = header.get("CRLN_OBS")
        if crln is not None:
            out["lon_mean_stony"] = float((lon_m - float(crln) + 180.0) % 360.0 - 180.0)
        if cycle_mode == "date":  # solo per il fattoriale esplorativo
            c, p, state = cyc.cycle_by_date(t), np.nan, "DATE"
        else:
            c, p, state = cyc.assign_cycle(t, lat_m, boundary)
        out.update(cycle=c, p_new=p, cycle_state=state)
        sinlat = np.sin(np.radians(lat[strong]))
        k = 3.0 / (4.0 * np.pi * r * r)
        out["d_axial_g"] = float(k * (br[strong] * sinlat * area).sum())
    if npos and nneg:
        lp = geo.weighted_centroid(lon[pos], lat[pos], br[pos])
        ln = geo.weighted_centroid(lon[neg], lat[neg], -br[neg])
        out.update(lon_pos=lp[0], lat_pos=lp[1], lon_neg=ln[0], lat_neg=ln[1])
        d = geo.great_circle_deg(*lp, *ln)
        d_cm = float(np.radians(d) * r)
        # leading = polarita' piu' a ovest (longitudine di Carrington maggiore):
        # tilt del vettore negativa -> positiva, |angolo| < 90 se la positiva e' a ovest
        t_np = geo.tilt_deg(ln, lp)
        leading = 1 if abs(t_np) < 90.0 else -1
        lead, follow = (lp, ln) if leading == 1 else (ln, lp)
        tilt = geo.tilt_deg(lead, follow)
        sintilt = float(np.sin(np.radians(tilt)))
        exp_lead = cyc.expected_leading_sign(int(out["cycle"]), out["lat_mean_deg"])
        hale = 1 if leading == exp_lead else -1
        phibar = 0.5 * (phi_pos + phi_neg)
        k = 3.0 / (4.0 * np.pi * r * r)
        mean_sin_pos = float((br[pos] * np.sin(np.radians(lat[pos]))).sum() / br[pos].sum())
        mean_sin_neg = float((br[neg] * np.sin(np.radians(lat[neg]))).sum() / br[neg].sum())
        out.update(d_cm=d_cm, tilt_deg=tilt, tilt_reduced_deg=geo.reduce_tilt_deg(tilt),
                   sintilt=sintilt, s_bl=hale * phi * d_cm * out["coslat"] * sintilt,
                   leading_sign=leading, expected_leading_sign=exp_lead, hale_sign=hale,
                   d_axial_bal_g=float(k * phibar * (mean_sin_pos - mean_sin_neg)))
    return finish(out, nmask, npos, nneg)

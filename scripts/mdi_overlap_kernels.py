"""Draft pure-array kernels for a future MDI/HMI comparison.

No FITS reader, network, sample selection or real-data runner is provided.
Coordinates and observer longitude must use the same Carrington frame;
LOS is positive towards the observer, Btheta towards south, Bphi west.
Area is supplied explicitly in cm^2: neither WCS nor resolution is inferred.
Existing P1 geometry is reused; these helpers do not update P1 or T3/T5.
"""
from __future__ import annotations

import numpy as np
import re
from sharpbl import geometry as geo


def _maps(*arrays):
    values = [np.asarray(a, dtype=float) for a in arrays]
    if not values or values[0].ndim != 2 or any(a.shape != values[0].shape for a in values):
        raise ValueError("Expected equally shaped 2D maps")
    return values


def _mask(mask, shape):
    value = np.asarray(mask)
    if value.dtype != bool or value.shape != shape:
        raise ValueError("Footprint must be an explicit Boolean map of the same shape")
    return value


def parse_quality32(value):
    """Preserve the same 32-bit pattern for signed and unsigned integer notation.

    Decimal input may be in [-2**31, 2**32-1]; hex is unsigned (0x prefix).
    Missing values, booleans, floats and out-of-range integers are errors.
    This normalizes representation only; it does not apply an eligibility rule.
    """
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (str, int, np.integer)):
        raise ValueError("QUALITY requires an integer or an exact integer string")
    s = str(value).strip()
    if re.fullmatch(r"0[xX][0-9a-fA-F]{1,8}", s):
        return int(s, 16)
    if not re.fullmatch(r"[+-]?[0-9]+", s):
        raise ValueError("Invalid QUALITY notation")
    q = int(s, 10)
    if not -(1 << 31) <= q < (1 << 32):
        raise ValueError("QUALITY outside signed/unsigned 32-bit range")
    return q & 0xffffffff


def patch_membership(bitmap, *, instrument):
    """Decode membership only, without magnetic/intensity or QUALITY filtering.

    HMI documented values: 0,1,2,33,34. MDI documented values:
    0,5,6,9,10,17,18,37,38,41,42,49,50. Unknown codes are errors.
    MDI 37 (quiet continuum + weak field + membership) remains inside.
    """
    b = np.asarray(bitmap, dtype=float)
    if b.ndim != 2 or not np.isfinite(b).all() or not np.equal(b, np.floor(b)).all():
        raise ValueError("Bitmap must contain finite integer codes in a 2D map")
    codes = {"HMI": {0, 1, 2, 33, 34}, "MDI": {0, 5, 6, 9, 10, 17, 18, 37, 38, 41, 42, 49, 50}}
    if instrument not in codes or not set(np.unique(b)).issubset(codes[instrument]):
        raise ValueError("Unknown instrument or bitmap code; inspect the product definition")
    return (b.astype(np.int64) & 32) != 0


def viewing_geometry(lon_deg, lat_deg, *, observer_lon_deg, observer_lat_deg,
                     distance_m, radius_m):
    """Finite-distance LOS coefficients on the photospheric sphere, per pixel.

    Observer and surface coordinates must be in the same frame and epoch.
    Inputs are geometric, without an additional light-time correction.
    u = (D * e_observer - R * e_r) / |D * e_observer - R * e_r|.
    mu = e_r dot u; visibility requires mu > 0 (no limb clipping).
    """
    lon, lat = _maps(lon_deg, lat_deg)
    scalars = np.array([observer_lon_deg, observer_lat_deg, distance_m, radius_m], float)
    if not np.isfinite(scalars).all() or not (-90 <= observer_lat_deg <= 90):
        raise ValueError("Observer metadata missing or outside its domain")
    if radius_m <= 0 or distance_m <= radius_m:
        raise ValueError("Require D > R > 0 in metres")
    if not np.isfinite(lon).all() or not np.isfinite(lat).all() or (np.abs(lat) > 90).any():
        raise ValueError("Invalid surface coordinates")
    phi, lam = np.deg2rad(lon), np.deg2rad(lat)
    er = geo.unit_vectors(lon, lat)
    # e_theta increases towards south; e_phi towards increasing longitude.
    etheta = np.stack([np.sin(lam)*np.cos(phi), np.sin(lam)*np.sin(phi), -np.cos(lam)], axis=-1)
    ephi = np.stack([-np.sin(phi), np.cos(phi), np.zeros_like(phi)], axis=-1)
    eo = geo.unit_vectors(float(observer_lon_deg), float(observer_lat_deg))
    ray = distance_m * eo - radius_m * er
    ray /= np.linalg.norm(ray, axis=-1)[..., None]
    return {"mu": np.clip(np.sum(er * ray, axis=-1), -1., 1.),
            "theta": np.sum(etheta * ray, axis=-1),
            "phi": np.sum(ephi * ray, axis=-1)}


def vector_to_los(br, bt, bp, geometry):
    """Project vector components; this is distinct from measured magnetogram LOS."""
    br, bt, bp, mu, ct, cp = _maps(br, bt, bp, geometry["mu"], geometry["theta"], geometry["phi"])
    return br * mu + bt * ct + bp * cp


def radial_proxy(los, mu, footprint, *, mu_min):
    """Reject the entire comparison if a footprint pixel is invalid/out of domain.

    No division at mu <= 0 and no silent trimming of a patch at the chosen bound.
    Outside the footprint, the returned proxy is NaN even if inputs are finite.
    mu_min must be decided in the future protocol, not estimated by this helper.
    """
    los, mu = _maps(los, mu)
    footprint = _mask(footprint, los.shape)
    if not np.isfinite(mu_min) or not 0 < mu_min <= 1:
        raise ValueError("Require 0 < mu_min <= 1")
    bad = footprint & (~np.isfinite(los) | ~np.isfinite(mu) | (mu < mu_min) | (mu > 1))
    proxy = np.full(los.shape, np.nan)
    if not footprint.any():
        status = "empty_footprint"
    elif bad.any():
        status = "invalid_or_outside_mu_domain"
    else:
        np.divide(los, mu, out=proxy, where=footprint)
        status = "ok"
    return {"status": status, "field_g": proxy, "n_footprint": int(footprint.sum()),
            "n_bad": int(bad.sum())}


def measure_field(field_g, footprint, lon_deg, lat_deg, area_cm2, *, radius_cm,
                  threshold_g=100., max_abs_g=10000.):
    """Cycle-free flux, spherical centroids and axial dipole on an explicit grid.

    No S_BL, D*, efficiency or quenching verdict: cycle/Hale adapter is pending.
    Field cut and threshold follow P1, but nonfinite footprint pixels reject
    this strict comparison kernel. R0 must call frozen measure_v84 unchanged:
    a kernel rejection is distinct from a failure to reproduce the P1 reference.
    Scalar or per-pixel surface area is supported (G * cm^2 gives Mx).
    """
    field, lon, lat = _maps(field_g, lon_deg, lat_deg)
    footprint = _mask(footprint, field.shape)
    scalars = np.array([radius_cm, threshold_g, max_abs_g], float)
    if not np.isfinite(scalars).all() or radius_cm <= 0 or not 0 < threshold_g <= max_abs_g:
        raise ValueError("Invalid radius or field cuts")
    area = np.asarray(area_cm2, dtype=float)
    if area.ndim == 0:
        area = np.full(field.shape, float(area))
    if area.shape != field.shape:
        raise ValueError("Area must be scalar or match the map")
    invalid = footprint & (~np.isfinite(field) | ~np.isfinite(lon) | ~np.isfinite(lat)
                           | (np.abs(lat) > 90) | ~np.isfinite(area) | (area <= 0))
    if invalid.any():
        return {"status": "invalid_input", "n_bad": int(invalid.sum())}
    eligible = footprint & (np.abs(field) <= max_abs_g)
    pos = eligible & (field >= threshold_g)
    neg = eligible & (field <= -threshold_g)
    strong = pos | neg
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            wp, wn = field[pos] * area[pos], -field[neg] * area[neg]
            pp, pn = float(wp.sum()), float(wn.sum())
            flux = pp + pn
            k = 3 / (4 * np.pi * np.square(np.float64(radius_cm)))
            dipole = float(k * np.sum(field[strong] * np.sin(np.deg2rad(lat[strong])) * area[strong]))
            if not np.isfinite([pp, pn, flux, k, dipole]).all() or k == 0:
                return {"status": "numeric_failure"}
    except FloatingPointError:
        return {"status": "numeric_failure"}
    out = {"status": "ok", "phi_mx": flux, "phi_pos_mx": pp, "phi_neg_mx": pn,
           "d_axial_g": dipole, "npos": int(pos.sum()), "nneg": int(neg.sum()),
           "n_over_max": int((footprint & ~eligible).sum()),
           "d_axial_bal_g": np.nan, "tilt_deg": np.nan, "d_cm": np.nan}
    if not footprint.any():
        out["status"] = "empty_footprint"
    elif not pos.any() or not neg.any():
        out["status"] = "no_positive" if not pos.any() else "no_negative"
        if not strong.any():
            out["status"] = "no_polarities"
    else:
        cp = geo.weighted_centroid(lon[pos], lat[pos], wp)
        cn = geo.weighted_centroid(lon[neg], lat[neg], wn)
        cm = geo.weighted_centroid(lon[strong], lat[strong], np.abs(field[strong]) * area[strong])
        distance = geo.great_circle_deg(*cp, *cn)
        if not np.isfinite(distance) or not 0 < distance < 180:
            out["status"] = "degenerate_geometry"
            return out
        t_np = geo.tilt_deg(cn, cp)
        leading = 1 if abs(t_np) < 90 else -1
        lead, follow = (cp, cn) if leading == 1 else (cn, cp)
        tilt = geo.tilt_deg(lead, follow)
        if not np.isfinite(tilt) or not np.isfinite(cm).all():
            out["status"] = "degenerate_geometry"
            return out
        means = (np.sum(wp * np.sin(np.deg2rad(lat[pos]))) / pp
                 - np.sum(wn * np.sin(np.deg2rad(lat[neg]))) / pn)
        out.update(lon_pos=cp[0], lat_pos=cp[1], lon_neg=cn[0], lat_neg=cn[1],
                   lat_mean_deg=cm[1], lon_mean_deg=cm[0], leading_sign=leading,
                   tilt_deg=tilt, d_cm=float(np.deg2rad(distance) * radius_cm),
                   d_axial_bal_g=float(k * flux / 2 * means))
    return out


def paired_differences(reference, candidate):
    """Signed differences, relative flux if nonzero, and axial tilt modulo 180°.

    Valid only for comparable declared footprints/quantities; no regridding here.
    An invalid record is kept as unavailable, never imputed with zero.
    """
    if reference.get("status") != "ok" or candidate.get("status") != "ok":
        return {"status": "not_comparable"}
    keys = ("phi_mx", "phi_pos_mx", "phi_neg_mx", "d_axial_g", "d_axial_bal_g",
            "tilt_deg", "d_cm", "lat_pos", "lat_neg", "lat_mean_deg")
    lon_keys = ("lon_pos", "lon_neg", "lon_mean_deg")
    if not all(np.isfinite(obj.get(k, np.nan))
               for obj in (reference, candidate) for k in keys + lon_keys):
        return {"status": "not_comparable"}
    delta = {"status": "ok"}
    for key in keys:
        delta["delta_" + key] = candidate[key] - reference[key]
    for key in lon_keys:
        delta["delta_" + key] = (candidate[key] - reference[key] + 180) % 360 - 180
    delta["delta_tilt_axial_deg"] = (candidate["tilt_deg"] - reference["tilt_deg"] + 90) % 180 - 90
    for suffix, lon_key, lat_key in (("pos", "lon_pos", "lat_pos"),
                                    ("neg", "lon_neg", "lat_neg"),
                                    ("mean", "lon_mean_deg", "lat_mean_deg")):
        delta["centroid_" + suffix + "_sep_deg"] = geo.great_circle_deg(
            reference[lon_key], reference[lat_key], candidate[lon_key], candidate[lat_key])
    for key, value in list(delta.items()):
        if key.startswith("delta_"):
            delta["abs_" + key] = abs(value)
    delta["relative_flux"] = ((candidate["phi_mx"] - reference["phi_mx"]) / reference["phi_mx"]
                               if reference["phi_mx"] != 0 else np.nan)
    return delta

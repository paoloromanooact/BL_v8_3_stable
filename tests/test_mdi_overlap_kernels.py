"""Synthetic-only checks for draft geometry. No FITS or saved response is read."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
# Same import arrangement as the existing standalone repository tests.
sys.path.insert(0, str(ROOT / "python"))
spec = importlib.util.spec_from_file_location("mdi_overlap_kernels", ROOT / "scripts/mdi_overlap_kernels.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def geom(lon_map, lat_map, **kw):
    return core.viewing_geometry(lon_map, lat_map, observer_lon_deg=kw.get("lon", 0.),
                                 observer_lat_deg=kw.get("lat", 0.),
                                 distance_m=kw.get("distance", 100.), radius_m=1.)


def test_finite_distance_not_parallel_rays():
    lon, lat = np.array([[0., 60.]]), np.zeros((1, 2))
    g = geom(lon, lat, distance=10.)
    np.testing.assert_allclose(g["mu"], [[1., 4/np.sqrt(91)]], rtol=1e-14, atol=0.)
    assert g["mu"][0, 1] != .5


def test_projection_basis_and_theta_sign():
    g = geom(np.array([[0.]]), np.array([[0.]]), lat=30.)
    assert g["theta"][0, 0] < 0  # southward field points away from a northern observer
    los = core.vector_to_los([[0]], [[100]], [[0]], g)
    assert los[0, 0] < 0
    np.testing.assert_allclose(g["mu"]**2 + g["theta"]**2 + g["phi"]**2, 1., rtol=1e-14)


def test_radial_field_round_trip():
    g = geom(np.array([[0., 10.]]), np.array([[5., 10.]]))
    br = np.array([[200., -400.]])
    los = core.vector_to_los(br, np.zeros_like(br), np.zeros_like(br), g)
    out = core.radial_proxy(los, g["mu"], np.ones(br.shape, bool), mu_min=.8)
    assert out["status"] == "ok"
    np.testing.assert_allclose(out["field_g"], br, rtol=1e-14, atol=0.)


def test_radial_approximation_does_not_remove_horizontal_field():
    g = geom([[0]], [[0]], lat=30.)
    los = core.vector_to_los([[200]], [[100]], [[0]], g)
    out = core.radial_proxy(los, g["mu"], np.ones((1, 1), bool), mu_min=.8)
    assert out["field_g"][0, 0] < 200


def test_zero_mu_rejects_whole_record_without_division():
    with np.errstate(divide="raise", invalid="raise"):
        out = core.radial_proxy([[100., -100.]], [[1., 0.]], np.ones((1, 2), bool), mu_min=.8)
    assert out["status"] != "ok" and out["n_bad"] == 1
    assert np.isnan(out["field_g"]).all()


def test_unusable_pixel_outside_footprint_does_not_trim_inside():
    out = core.radial_proxy([[100., np.nan]], [[1., np.nan]], np.array([[True, False]]), mu_min=.8)
    assert out["status"] == "ok" and out["field_g"][0, 0] == 100
    assert np.isnan(out["field_g"][0, 1])


@pytest.mark.parametrize("mu_min", [0., -1., 1.1, np.nan])
def test_explicit_mu_domain_required(mu_min):
    with pytest.raises(ValueError):
        core.radial_proxy([[1]], [[1]], np.ones((1, 1), bool), mu_min=mu_min)


def test_footprint_is_not_implicitly_boolean():
    with pytest.raises(ValueError):
        core.radial_proxy([[1]], [[1]], [[np.nan]], mu_min=.8)


def test_bitmap_membership_is_instrument_specific():
    b = np.array([[5, 6, 37, 38, 41, 49, 50]])
    assert core.patch_membership(b, instrument="MDI").tolist() == [[False, False, True, True, True, True, True]]
    assert core.patch_membership([[0, 1, 2, 33, 34]], instrument="HMI").tolist() == [[False, False, False, True, True]]
    with pytest.raises(ValueError):
        core.patch_membership(b, instrument="HMI")
    with pytest.raises(ValueError):
        core.patch_membership([[36]], instrument="MDI")


def test_two_pixel_bipole_with_known_dipole_and_flux():
    radius = 10.
    m = core.measure_field([[100, -100]], np.ones((1, 2), bool), [[0, 0]], [[30, -30]],
                           2., radius_cm=radius)
    assert m["status"] == "ok" and m["phi_mx"] == 400
    k = 3/(4*np.pi*radius**2)
    np.testing.assert_allclose(m["d_axial_g"], k*200, rtol=1e-14)
    np.testing.assert_allclose(m["d_axial_bal_g"], k*200, rtol=1e-14)
    np.testing.assert_allclose(m["d_cm"], np.pi*radius/3, rtol=1e-14)


def test_area_weights_centroids_and_polarity_flux():
    m = core.measure_field([[200, 200, -200]], np.ones((1, 3), bool), [[0, 10, 20]], [[0, 0, 1]],
                           [[1, 2, 1]], radius_cm=1.)
    assert m["phi_pos_mx"] == 600 and m["phi_neg_mx"] == 200
    assert 6 < m["lon_pos"] < 7


def test_no_polarity_is_unavailable_not_zero_geometry():
    m = core.measure_field([[200, 50]], np.ones((1, 2), bool), [[0, 1]], [[0, 1]], 1., radius_cm=1.)
    assert m["status"] == "no_negative" and m["phi_mx"] == 200
    assert np.isnan(m["tilt_deg"]) and np.isnan(m["d_axial_bal_g"])
    assert core.paired_differences(m, m)["status"] == "not_comparable"


def test_nonfinite_field_inside_footprint_rejects_measurement():
    m = core.measure_field([[200, np.nan]], np.ones((1, 2), bool), [[0, 1]], [[0, 1]], 1., radius_cm=1.)
    assert m["status"] == "invalid_input"


def test_bad_area_and_map_shape_are_detected():
    m = core.measure_field([[200, -200]], np.ones((1, 2), bool), [[0, 1]], [[0, 1]], -1., radius_cm=1.)
    assert m["status"] == "invalid_input"
    with pytest.raises(ValueError):
        geom([[0]], [[0, 1]])
    with pytest.raises(ValueError):
        geom([[0]], [[0]], distance=.5)


def test_axial_wrap_and_zero_reference_denominator():
    a = dict(status="ok", phi_mx=0., d_axial_g=0., d_axial_bal_g=0., d_cm=1., tilt_deg=89.)
    b = dict(a, tilt_deg=-89., phi_mx=1.)
    d = core.paired_differences(a, b)
    assert d["delta_tilt_deg"] == -178 and d["delta_tilt_axial_deg"] == 2
    assert np.isnan(d["relative_flux"])


def test_longitude_wrap_does_not_move_centroid_to_180():
    m = core.measure_field([[200, 200, -200]], np.ones((1, 3), bool), [[359, 1, 10]], [[0, 0, 1]],
                           1., radius_cm=1.)
    assert abs(m["lon_pos"]) < 1e-12


def test_arrays_are_not_modified():
    field = np.array([[200., -200.]])
    original = field.copy()
    core.radial_proxy(field, np.ones_like(field), np.ones(field.shape, bool), mu_min=.8)
    core.measure_field(field, np.ones(field.shape, bool), [[0, 1]], [[0, 1]], 1., radius_cm=1.)
    np.testing.assert_array_equal(field, original)


def test_longitude_projection_sign():
    g = geom([[30]], [[0]])
    assert g["phi"][0, 0] < 0
    assert core.vector_to_los([[0]], [[0]], [[100]], g)[0, 0] < 0


def test_coincident_centroids_do_not_produce_a_valid_tilt():
    m = core.measure_field([[200, -200]], np.ones((1, 2), bool), [[0, 0]], [[0, 0]], 1., radius_cm=1.)
    assert m["status"] == "degenerate_geometry"


def test_empty_footprint_and_nonfinite_pair_stay_unavailable():
    m = core.measure_field([[200, -200]], np.zeros((1, 2), bool), [[0, 1]], [[0, 1]], 1., radius_cm=1.)
    assert m["status"] == "empty_footprint"
    a = dict(status="ok", phi_mx=1., d_axial_g=np.nan, d_axial_bal_g=0., d_cm=1., tilt_deg=0.)
    assert core.paired_differences(a, a)["status"] == "not_comparable"


def test_nonphysical_observer_and_coordinate_are_rejected():
    with pytest.raises(ValueError):
        geom([[0]], [[91]])
    with pytest.raises(ValueError):
        geom([[0]], [[0]], lat=np.nan)


def test_numeric_overflow_is_not_a_valid_measurement():
    with np.errstate(over="raise", invalid="raise"):
        m = core.measure_field([[200, -200]], np.ones((1, 2), bool), [[0, 1]], [[0, 1]],
                               1e308, radius_cm=1.)
    assert m["status"] == "numeric_failure"


def test_threshold_and_maximum_field_edges():
    m = core.measure_field([[100, -100, 10001, -99]], np.ones((1, 4), bool), [[0, 1, 2, 3]],
                           [[0, 1, 2, 3]], 1., radius_cm=1.)
    assert m["status"] == "ok" and m["phi_mx"] == 200 and m["n_over_max"] == 1


def test_uniform_area_matches_frozen_p1_measure_on_synthetic_map():
    from sharpbl import geometry, measure
    field = np.array([[200., -200.], [300., -150.]])
    hdr = dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CRVAL1=359.9, CRVAL2=15.,
               CDELT1=.03, CDELT2=.03, CRPIX1=1.5, CRPIX2=1.5,
               CUNIT1="deg", CUNIT2="deg", T_REC="2024.06.01_00:00:00_TAI", RSUN_REF=6.96e8)
    lon, lat = geometry.lonlat_maps(hdr, field.shape)
    a = core.measure_field(field, np.ones(field.shape, bool), lon, lat, geometry.pixel_area_cm2(hdr),
                           radius_cm=geometry.rsun_cm(hdr))
    b = measure.measure_v84(field, np.full(field.shape, 33), hdr)
    for key in ("phi_mx", "d_axial_g", "d_axial_bal_g", "d_cm", "tilt_deg", "lat_mean_deg"):
        np.testing.assert_allclose(a[key], b[key], rtol=1e-12, atol=0., err_msg=key)

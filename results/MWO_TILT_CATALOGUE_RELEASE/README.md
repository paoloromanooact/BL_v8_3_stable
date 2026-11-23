# Mount Wilson magnetic tilt catalogue 1974-2012

Built for test T3 of the SHARP BL project (docs/PROTOCOL_T3_MWO.md, amendments A1-A3).

Population. DPD groups (corrected whole-spot area >= 1 millionth, |latitude| <= 45 deg), 1974-01-01 to
2012-12-31 UTC, measured on Mount Wilson Fe I 5250 A full-disc magnetograms of the same UTC day (ephemeris checks,
amendments A2 and A3 exclusions applied before the choice; finest resolution class, then closest to the DPD time).
A record exists when the window |lat - lat_DPD| <= 6 deg, |L - L_DPD| <= 8 deg lies entirely at mu >= 0.8 and both
polarities have pixels with 50 <= |B_r| <= 4000 G (B_r = B_LOS / mu, BLANK pixels excluded, amendment A1). The
isolated table keeps, per group, the first candidate day in |LCM| order on which the group is isolated (no other DPD
group centre in the window) and the measurement succeeds; the all table drops the isolation condition, so the same
group can have a different day in the two tables. This is the population of isolated (or all) MEASURABLE regions at the
selected instant: large regions are measurable more often, and measurability depends on activity (see LOSSES.csv of the
catalogue). Known limits: observing resolution ~10-20 arcsec; saturation and zero-point corrections in the native
FITS are not documented; instrumental epochs before 1996 are known only from the headers; the GV=0.03 and the
anomalous-distribution magnetograms are excluded (EXCLUDED_MAGNETOGRAMS.csv).

Tables: isolated 5223 regions, all 5942 regions.

## Columns

- `noaa`: DPD group number (string, letters kept)
- `day_utc`: UTC day of the DPD row and of the MWO scan
- `mwo_time_utc`: UTC instant of the MWO magnetogram (session date + TAVG-UT)
- `mwo_file`: FITS member of the MWO archive
- `epoch`: instrumental epoch E1-E8 (protocol §4)
- `resolution_class`: R1 ~9.5x13 arcsec, R2 ~13x20, R3 ~14x17, R0 other
- `carrington_rotation`: Carrington rotation of the MWO instant
- `cycle`: solar cycle by date (minima 1976-03, 1986-09, 1996-08, 2008-12)
- `hemisphere`: N or S, sign of lat_flux_weighted
- `lat_flux_weighted_deg`: flux-weighted latitude of the measured pixels, deg
- `dpd_lat_deg`: latitude of the DPD group, deg
- `dpd_carrington_lon_deg`: Carrington longitude of the DPD group, deg
- `dpd_lcm_deg`: longitude from the central meridian of the DPD group, deg
- `dpd_area_msh`: corrected whole-spot area of the DPD group, millionths of the hemisphere
- `flux_window_mx`: unsigned flux of the pixels with 50 <= |B_r| <= 4000 G in the window, Mx
- `tilt_deg`: tilt in the P1 convention (leading = westernmost polarity), deg
- `joy_gamma_deg`: Joy variable sign(lat) asin(sin tilt), positive for leading closer to the equator
- `leading_polarity_sign`: sign of the leading (west) polarity
- `hale_expected_sign`: leading sign expected from Hale's law for the cycle and hemisphere
- `lon_pos_deg`: Carrington longitude of the positive-polarity centroid, deg
- `lat_pos_deg`: latitude of the positive-polarity centroid, deg
- `lon_neg_deg`: Carrington longitude of the negative-polarity centroid, deg
- `lat_neg_deg`: latitude of the negative-polarity centroid, deg
- `separation_deg`: great-circle distance of the two centroids, deg
- `isolated_day`: no other DPD group centre inside the window on that day
- `n_neighbours`: other DPD group centres inside the window
- `candidate_rank`: position of the chosen day in the |LCM| order of the candidate days
- `n_candidate_days`: candidate days of the group
- `n_blank_window`: BLANK pixels in the window (amendment A1)
- `activity_dpd_norm`: monthly hemispheric DPD activity, normalised to the 1974-2012 mean

## Joy's law per cycle (descriptive, no test)

k in gamma = k sin|lat| per cycle and hemisphere, through the origin; flux-weighted and unweighted; percentile bootstrap over blocks of 6 CR (2000 replicates, seed 69 500 001). Cycles 20 and 24 are only partly covered.

 cycle hemisphere  weighted  n_regions  n_cr  n_blocks  k_deg      lo     hi  invalid_replicates  partial_cycle
    20          N      True         53    19         4  0.092  -9.002 64.564                   0           True
    20          S      True         78    24         5 23.233  16.442 67.299                   0           True
    21          N      True        595   100        21 27.150  11.446 40.540                   0          False
    21          S      True        657   100        21 22.201   8.799 36.219                   0          False
    22          N      True        779   122        23 24.210  16.898 30.839                   0          False
    22          S      True        901   119        22 26.631  18.543 36.253                   0          False
    23          N      True        839   101        22 16.457   9.339 25.207                   0          False
    23          S      True        934   117        24 22.512  13.679 31.447                   0          False
    24          N      True        229    39         9 17.507   3.554 43.168                   0           True
    24          S      True        158    38         7  8.826  -5.565 28.808                   0           True
    20          N     False         53    19         4 -1.500 -28.655 80.037                   0           True
    20          S     False         78    24         5  0.940  -5.532 31.678                   0           True
    21          N     False        595   100        21 23.681  13.545 33.020                   0          False
    21          S     False        657   100        21 17.045   7.905 27.016                   0          False
    22          N     False        779   122        23 23.721  17.286 28.448                   0          False
    22          S     False        901   119        22 16.274  10.037 23.878                   0          False
    23          N     False        839   101        22 14.988   8.606 21.604                   0          False
    23          S     False        934   117        24 15.932   9.938 22.703                   0          False
    24          N     False        229    39         9 15.637   2.434 34.980                   0           True
    24          S     False        158    38         7  8.669  -0.824 18.005                   0           True

## Comparisons

COMPARISONS/ holds the stability outputs: white-light DPD tilts by epoch (S1), the comparison with SDO/HMI (P1) in 2010-2012 (S2_P1), Hale agreement by epoch (S3) and the d_WL of the all-records set.

## Provenance

```
{
  "catalogue_meta_sha256": "77db727e40b061cd1b7251e7e81387c22cb36a2cb5853ed4341911b175cbb3e4",
  "stability_meta_sha256": "b6789830d48dced0d0f8e9d3a5a95e617ee5e53edaff4147ecd0d2aa4984d04e",
  "estimate_meta_sha256": "8bad8c81dc47453c4d58b3ce0254d25fc4949be6bd9aba667369c7cab7589d81",
  "estimate_recount_receipt_sha256": "95b7fc18815aa38dd6971294236d3115afbb257400acb4d076718ac8ccf74445",
  "script_sha256": "8c840f9cc09823f6a7bfa13f9a63bdf7a2d8702adcbdf889b59e12f7d4fbe3dd"
}
```

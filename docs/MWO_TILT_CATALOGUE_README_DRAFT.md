# Mount Wilson magnetic tilt catalogue of sunspot groups, 1974–2012 — README (draft)

**Draft, 20 November 2026. Written before the tilts are unsealed: it describes definitions, selection and provenance
only. Sections marked [after the estimate] are filled from the reviewed release products.** Numbers below come from
catalogue R4 (`results/T3_MWO_CATALOGUE_R4`, independent recount 18/18) and its metadata-only coverage
(`results/T3_MWO_COVERAGE_R4`).

## 1. What the catalogue is

Magnetic tilt angles of sunspot groups measured on the Mount Wilson Observatory (MWO) 150-ft tower full-disc
line-of-sight magnetograms (Fe I 525.02 nm), at the positions of the Debrecen Photoheliographic Data (DPD) groups, from
1974-01-01 to 2012-12-31 UTC. One row per DPD group. Each row has the tilt of the axis joining the flux-weighted centroids
of the two polarities, with the polarity of the leading part, the flux in the measurement window, and quality and
provenance fields.

The catalogue was built to test whether the Joy's-law coefficient depends on hemispheric activity within the cycle
(test T3 of the SHARP BL project; protocol `docs/PROTOCOL_T3_MWO.md`, amendments A1–A3, all frozen before measurement).
It is released as a data product with the same rules.

**Prior work.** Li & Ulrich (2012, ApJ 758, 115) measured magnetic tilt angles of about 30 600 sunspots on the MWO
daily averaged magnetograms 1974–2012 and on MDI 1996–2010; Wang et al. (2014, ApJ 796, 1) compared MWO magnetic and
DPD white-light tilts in cycles 21–23. This catalogue is not the first MWO magnetic tilt catalogue. It differs in:
- positions from the DPD groups, with one record per group under a frozen rule;
- the isolation condition;
- documented quality control: BLANK pixels, the 18 GV = 0.03 scans, 8 anomalous field distributions, UTC-day grouping;
- an independent recount of every record;
- a reproducible release with code and SHA-256 of every input.

Two tables:

| Table | Regions | Rule for the day of each group |
|---|---|---|
| `MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv` | 5223 | first day, in increasing \|LCM\| order, on which the group is isolated and the measurement succeeds |
| `MWO_TILT_CATALOGUE_ALL_1974_2012.csv` | 5942 | same, without the isolation condition |

The same group can appear in both tables on different days.

## 2. Population — read before using the catalogue

The catalogue contains **measurable** regions, not all sunspot groups.

1. **DPD groups:** corrected whole-spot area ≥ 1 millionth of the hemisphere, |latitude| ≤ 45°.
2. **Same UTC day MWO Fe I magnetogram.** The magnetogram must pass the ephemeris checks of the frozen MWO pipeline
   (|ΔCENLON| ≤ 18°, |ΔB0| ≤ 0.5°) and must not be in the exclusion lists A2 and A3 (§6). Among the remaining scans of
   the day, the choice is the finest resolution class, then the closest time to the DPD row, then the lowest TAVG-UT.
3. **Window:** |λ − λ_DPD| ≤ 6° and |L − L_DPD| ≤ 8° around the DPD centre, entirely at μ ≥ 0.8.
4. **Field:** B_r = B_LOS/μ, pixels with 50 ≤ |B_r| ≤ 4000 G, BLANK pixels excluded (A1). A window with more than 5 %
   BLANK pixels fails.
5. **Both polarities present** in the window above threshold.
6. **Isolated table:** no other DPD group centre inside the window on that day.

Consequences:
- **Selection depends on activity.** The fraction of eligible DPD groups that obtain an isolated record grows from 24 %
  (lowest activity tercile) to 32 % (highest); for the all table, from 27 % to 38 % (`SELECTION_BY_ACTIVITY.csv`).
  Large regions are measured more often.
- **Losses** are dominated by windows outside μ ≥ 0.8 and by days without a valid MWO magnetogram (`LOSSES.csv`,
  `ATTEMPTS.csv.gz`).
- **Coverage gaps:** 1979–1980 (no usable archives), 1997 (no Fe I scans), sparse scans in 2005, 2008 and the 2008–2010
  minimum. Cycles 20 (from 1974) and 24 (up to 2012) are covered only in part.

## 3. Measurement and conventions

- **Geometry:** the frozen MWO pipeline mapping (ξ = (x+1−X0)/R0, η = (y+1−Y0)/R0; heliographic latitude and Carrington
  longitude from B0 and CENLON), with the pipeline reader (float32 before BSCALE/BZERO).
- **Centroids:** flux-weighted (|B_r|/μ) unit-vector centroids on the sphere, separately for the positive and the
  negative pixels.
- **Tilt (`tilt_deg`):** P1 convention. The leading part is the westernmost polarity; the tilt is the angle of the vector
  from the leading to the following centroid in the local tangent plane at their midpoint, with x towards increasing
  Carrington longitude (west) and y towards north: tilt = atan2(Δy, Δx), in (−180°, 180°].
- **Joy variable (`joy_gamma_deg`):** γ = sign(λ̄)·asin(sin tilt), in [−90°, 90°], positive when the leading part is
  closer to the equator than the following part (Joy's sense) in both hemispheres. It does not use the polarity: it is
  defined for Hale and anti-Hale regions alike.
- **Polarity:** `leading_polarity_sign` is the sign of the leading part; `hale_expected_sign` is the sign expected from
  Hale's law for the cycle (by date) and the hemisphere. Their agreement is reported by epoch in the comparisons.
- **Flux (`flux_window_mx`):** Σ|B_r|·(R☉/R0)²/μ over the above-threshold pixels, R☉ = 6.96·10¹⁰ cm. It is the flux
  seen at MWO resolution above 50 G, not the total flux of the region. In the pilot comparison with SDO/HMI SHARP
  (211 regions, 2010-05 to 2013-01) it was a median 16 % of the SHARP flux; this ratio is a pilot result, not a
  property of the whole catalogue.
- **Latitude (`lat_flux_weighted_deg`):** flux-weighted mean latitude of the above-threshold pixels; the hemisphere
  follows its sign.
- **Cycle:** by date, with minima 1976-03, 1986-09, 1996-08 and 2008-12; no latitude-based separation in the overlaps.
- **Carrington rotation:** of the full UTC instant of the MWO scan.

## 4. Instrumental epochs and resolution

The epochs come from the FITS headers (hardware keyword MRKMOD, file family, port separation PSEPMA). Before 1996 they
are documented only by the headers.

| Epoch | Indicator | From | To | Isolated records | Resolution classes of the records |
|---|---|---|---|---|---|
| E1 datex | MRKMOD 0 | 1974-01 | 1974-07 | 38 | R3 |
| E2 ael | MRKMOD 256 | 1974-07 | 1981-12 | 693 | mostly R1 |
| E3 fm-0 | MRKMOD 1280 | 1982-01 | 1984-09 | 566 | R1 |
| E4 fm-1 | MRKMOD 1281 | 1984-09 | 1989-04 | 371 | R1 (+R2) |
| E5 fm-2 | MRKMOD 1282 | 1989-04 | 1993-09 | 1208 | R1 (+R2) |
| E6 fm-3 | MRKMOD 1283 | 1993-09 | 1994-12 | 135 | R1 (+R2) |
| E7 modern, before the PSEPMA change | `*fe1*`, PSEPMA ~66–69 | 1995-03 | 1996-04 | 45 | R1 |
| E8 modern, after | `*fe1*`, PSEPMA ~77–78 | 1996-04 | 2012-12 | 2167 | R1 (+R2) |

Ulrich et al. (2002, §2) date the new 24-channel system only to 1996; the E7/E8 boundary is the PSEPMA change seen in
the headers.

Resolution classes, from the observing pixel sizes DXB_OBS/DYB_OBS: R1 ≈ 9.5″×13″, R2 ≈ 13″×20″, R3 ≈ 14″×17″,
R0 other or missing. The finest class available on the day is chosen.

## 5. Columns

The column dictionary is in `COLUMNS.csv` of the release (name, source column, definition). Main groups:
- identification: `noaa`, `day_utc`, `mwo_time_utc`, `mwo_file`, `epoch`, `resolution_class`, `carrington_rotation`,
  `cycle`;
- position: `hemisphere`, `lat_flux_weighted_deg`, `dpd_lat_deg`, `dpd_carrington_lon_deg`, `dpd_lcm_deg`,
  `dpd_area_msh`;
- measurement: `flux_window_mx`, `tilt_deg`, `joy_gamma_deg`, `leading_polarity_sign`, `hale_expected_sign`,
  `lon_pos_deg`, `lat_pos_deg`, `lon_neg_deg`, `lat_neg_deg`, `separation_deg`;
- quality: `isolated_day`, `n_neighbours`, `candidate_rank`, `n_candidate_days`, `n_blank_window`;
- activity: `activity_dpd_norm` (monthly hemispheric DPD area, normalised to the 1974–2012 mean).

## 6. Exclusions and quality control

- **A1:** BLANK pixels (−32768) are excluded; the frozen reader did not handle them.
- **A2:** 18 magnetograms with header GV = 0.03 (1988-10-21; 1989-09-03/05) have the field scaled by about 100 and
  saturated at 32767·BSCALE. They are the same 18 files excluded by the frozen QC of the MWO polar-flux project.
- **A3:** 8 magnetograms whose central-disc median |B| exceeds 3 times the median of all Fe I scans of the 7 surrounding
  UTC days (1974-07-16, 1975-09-29, four of 1986, 1989-09-10, 2000-08-06). The rule was written after a pixel audit
  of all 30 952 Fe I magnetograms, blind to the tilts.
- Two 2013 files are unreadable. 33 scans have no usable central-disc pixels and are not certified as sound; none
  produces a selected record.
- Saturation alone is not a criterion: 1999-09-23 has 8.5 % saturated central pixels with a normal median and is never
  selected.

`EXCLUDED_MAGNETOGRAMS.csv` lists, with SHA-256, the 26 instrumental exclusions of A2 and A3 only. The two unreadable
files, the scans failing the ephemeris checks and every failed measurement attempt are recorded in the catalogue
products MAGNETOGRAMS, ATTEMPTS and LOSSES, not in that list.

## 7. Comparisons with other instruments [after the estimate]

- SDO/HMI SHARP (P1), same NOAA region and UTC day:
  - **pilot** (separate frozen protocol; P1 candidates 2010-05 to 2013-12, evaluable records 2010-05-04 to 2013-01-14,
    211 regions): leading polarity agrees in 95.7 %, median d_γ −0.69°, median |d_ax| 4.40°;
  - **catalogue-level comparison S2-P1** (isolated records of this catalogue, 2010-05-01 to 2012-12-31): [after the
    estimate].
- DPD white-light tilts (same group and day), by epoch and hemisphere (S1) and against activity (S2): [after the
  estimate].
- Hale agreement by epoch and hemisphere (S3): [after the estimate].
- MDI (1996–2010): planned extension, not in the first release.

## 8. Joy's law per cycle (descriptive) [after the estimate]

k in γ = k·sin|λ̄| per cycle and hemisphere, least squares through the origin, flux-weighted and unweighted; percentile
bootstrap over blocks of 6 Carrington rotations (2000 replicates, seed 69 500 001). Descriptive only: no test.
**k (degrees, in γ = k sin|λ|) is not numerically the same quantity as a tilt-latitude slope in degrees per degree**
(e.g. 0.26 in Dasi-Espuig et al. 2010): any comparison with published values must state the functional form,
population, weights and tilt convention of each, and stays descriptive.

## 9. Known limits

- Observing resolution about 10″–20″: compact regions are measured less reliably, and the tilt dispersion per region is
  larger than with SDO/HMI.
- The saturation and zero-point corrections in the native MWO FITS are not documented. No correction is applied: a
  uniform factor leaves the centroids unchanged only if the selected pixels stay the same.
- Selection depends on activity and size (§2).
- The epochs before 1996 are known only from the headers.
- The white-light comparison is relative: magnetic and photographic tilts differ physically and observationally.

## 10. Provenance, credits and licence [to complete]

- **Data:** MWO 150-ft tower synoptic magnetograms (UCLA/Mount Wilson Observatory; archive of the MWO polar-flux
  project); Debrecen Photoheliographic Data (Debrecen Heliophysical Observatory; gDPD, sDPD and daily files with
  SHA-256); SDO/HMI SHARP via JSOC (comparison only). Exact acknowledgement texts to be taken from the providers.
- **Code:** `scripts/t3_mwo_catalogue.py` (measurement), `scripts/t3_mwo_catalogue_recount.py` (independent recount),
  `scripts/t3_mwo_catalogue_release.py` (export). The commit and SHA-256 of every input are in `META.json`.
- **Licence, authors and deposit** (e.g. Zenodo DOI): to be agreed.

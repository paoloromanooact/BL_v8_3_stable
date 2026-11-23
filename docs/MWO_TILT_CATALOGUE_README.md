# Mount Wilson magnetic tilt catalogue of sunspot groups, 1974–2012

**README for deposit — version prepared 23 November 2026. NOT yet published.** Licence, authors and repository (for
example Zenodo with a DOI) are still to be agreed. This text describes the verified local release
`results/MWO_TILT_CATALOGUE_RELEASE` (release META SHA-256 `b5879cd3…`, independent check 115/115,
`results/MWO_TILT_CATALOGUE_RELEASE_RECOUNT`). The README generated inside the release folder is the short
machine-written version; this file replaces it in the deposit package.

## 1. What the catalogue is

Magnetic tilt angles of sunspot groups measured on the Mount Wilson Observatory (MWO) 150-ft tower full-disc
line-of-sight magnetograms (Fe I 525.02 nm). Positions come from the Debrecen Photoheliographic Data (DPD) groups.
Period: 1974-01-01 to 2012-12-31 UTC.

Each row is one DPD group and gives:
- the tilt of the axis joining the flux-weighted centroids of the two polarities;
- the polarity of the leading part;
- the flux in the measurement window;
- quality and provenance fields.

| File | Rows | Rule for the day of each group |
|---|---|---|
| `MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv` | 5223 | first day, in increasing \|LCM\| order, on which the group is isolated and the measurement succeeds |
| `MWO_TILT_CATALOGUE_ALL_1974_2012.csv` | 5942 | same, without the isolation condition |
| `COLUMNS.csv` | 30 | column name, source column, definition |
| `EXCLUDED_MAGNETOGRAMS.csv` | 26 | magnetograms excluded by amendments A2 and A3, with reason and SHA-256 |
| `JOY_BY_CYCLE.csv` | 20 | descriptive Joy coefficient per cycle and hemisphere (§8) |
| `COMPARISONS/` | — | white-light DPD and SDO/HMI comparisons, Hale agreement (§7) |
| `META.json` | — | package metadata: SHA-256 of every file, link to the verified release and its check |
| `RELEASE_META.json` | — | metadata of the verified release (SHA-256 of its products and of the upstream products) |
| `README_RELEASE_SHORT.md` | — | the short README generated with the release, kept unchanged |
| `SHA256SUMS.txt` | — | SHA-256 of every file of the package (`sha256sum -c SHA256SUMS.txt`) |

The same group can appear in both tables, on different days.

**Purpose and rules.** The catalogue was built to test whether the Joy's-law coefficient depends on hemispheric
activity within the cycle (test T3 of the SHARP BL project). The measurement rules were frozen before any tilt was
read: protocol `docs/PROTOCOL_T3_MWO.md` and amendments A1–A3. The tilts stayed sealed until the statistical
validation had been run, recounted and reviewed.

**Prior work.** This is not the first MWO magnetic tilt catalogue.
- Li & Ulrich (2012, ApJ 758, 115) measured tilt angles of about 30 600 sunspots on the MWO daily averaged
  magnetograms 1974–2012 and on MDI 1996–2010.
- Wang et al. (2014, ApJ 796, 1) compared MWO magnetic and DPD white-light tilts in cycles 21–23.

This catalogue differs in:
- positions from the DPD groups, with one record per group under a frozen rule;
- an isolation condition;
- documented quality control (§6);
- an independent recount of every record and of every downstream product;
- a release with code and SHA-256 of every input.

As of 23 November 2026 we found no public machine-readable version of the Li & Ulrich measurements (§11). No
record-by-record comparison with them has been made.

## 2. Population — read before using the catalogue

The catalogue contains **measurable** regions, not all sunspot groups. Selection steps:
1. **DPD groups:** corrected whole-spot area ≥ 1 millionth of the hemisphere, |latitude| ≤ 45°.
2. **Same-UTC-day MWO Fe I magnetogram** that passes the ephemeris checks of the frozen MWO pipeline (|ΔCENLON| ≤ 18°,
   |ΔB0| ≤ 0.5°) and is not in the exclusion lists A2 and A3 (§6).
   - Among the remaining scans of the day, the order of preference is: finest resolution class, then closest time to
     the DPD row, then lowest TAVG-UT.
3. **Window:** |λ − λ_DPD| ≤ 6° and |L − L_DPD| ≤ 8°, entirely at μ ≥ 0.8.
4. **Field:** B_r = B_LOS/μ, pixels with 50 ≤ |B_r| ≤ 4000 G, BLANK pixels excluded (A1). A window with more than 5 %
   BLANK pixels fails.
5. **Both polarities present** above the threshold.
6. **Isolated table only:** no other DPD group centre inside the window on that day.

Consequences:
- **Selection depends on activity and size.** The fraction of eligible DPD groups that obtain an isolated record grows
  from 24 % in the lowest activity tercile to 32 % in the highest; for the all table, from 27 % to 38 %. Large regions
  are measured more often.
- The share of groups excluded for non-isolation grows with activity: 10 %, 12 % and 14 % by tercile.
- **Coverage gaps:**
  - 1979–1980: no usable archives;
  - 1997: no Fe I scans;
  - sparse scans in 2005, 2008 and the 2008–2010 minimum.
- Cycles 20 (from 1974) and 24 (up to 2012) are only partly covered.

## 3. Measurement and conventions

- **Geometry:** the frozen MWO pipeline mapping, with ξ = (x+1−X0)/R0 and η = (y+1−Y0)/R0.
  - Heliographic latitude and Carrington longitude follow from B0 and CENLON.
  - The pipeline reader converts the data to float32 before applying BSCALE and BZERO.
- **Centroids:** unit-vector centroids on the sphere, weighted by |B_r|/μ, computed separately for the positive and
  the negative pixels.
- **Tilt (`tilt_deg`):** P1 convention.
  - The leading part is the westernmost polarity.
  - The tilt is the angle of the vector from the leading to the following centroid, in the local tangent plane at
    their midpoint.
  - Axes: x towards increasing Carrington longitude (west), y towards north. tilt = atan2(Δy, Δx), in (−180°, 180°].
- **Joy variable (`joy_gamma_deg`):** γ = sign(λ̄)·asin(sin tilt), in [−90°, 90°].
  - It is positive when the leading part is closer to the equator, in both hemispheres.
  - It does not use the polarity, so it is defined for Hale and anti-Hale regions alike.
- **Polarity:**
  - `leading_polarity_sign`: sign of the leading part;
  - `hale_expected_sign`: sign expected from Hale's law for the cycle (by date) and the hemisphere.
- **Flux (`flux_window_mx`):** Σ|B_r|·(R☉/R0)²/μ over the above-threshold pixels, with R☉ = 6.96·10¹⁰ cm.
  - It is the flux seen at MWO resolution above 50 G, not the total flux of the region.
  - In the pilot comparison with SDO/HMI SHARP (211 regions, 2010–2013) it was a median 16 % of the SHARP flux.
- **Latitude (`lat_flux_weighted_deg`):** flux-weighted mean latitude; the hemisphere follows its sign.
- **Cycle:** assigned by date, with minima 1976-03, 1986-09, 1996-08 and 2008-12.
- **Carrington rotation:** computed from the full UTC instant of the MWO scan.
- **No individual uncertainty** is given for the tilts: none has been estimated and verified.

## 4. Instrumental epochs and resolution

The epochs come from the FITS headers: hardware keyword MRKMOD, file family and port separation PSEPMA. Before 1996
they are documented only by these headers.

| Epoch | Indicator | From | To | Isolated records |
|---|---|---|---|---|
| E1 datex | MRKMOD 0 | 1974-01 | 1974-07 | 38 |
| E2 ael | MRKMOD 256 | 1974-07 | 1981-12 | 693 |
| E3 fm-0 | MRKMOD 1280 | 1982-01 | 1984-09 | 566 |
| E4 fm-1 | MRKMOD 1281 | 1984-09 | 1989-04 | 371 |
| E5 fm-2 | MRKMOD 1282 | 1989-04 | 1993-09 | 1208 |
| E6 fm-3 | MRKMOD 1283 | 1993-09 | 1994-12 | 135 |
| E7 modern, PSEPMA ~66–69 | `*fe1*` | 1995-03 | 1996-04 | 45 |
| E8 modern, PSEPMA ~77–78 | `*fe1*` | 1996-04 | 2012-12 | 2167 |

Resolution classes, from the observing pixel sizes DXB_OBS/DYB_OBS:
- R1 ≈ 9.5″×13″;
- R2 ≈ 13″×20″;
- R3 ≈ 14″×17″;
- R0: other or missing.

## 5. Columns

See `COLUMNS.csv`. Groups of columns:
- **identification:** `noaa`, `day_utc`, `mwo_time_utc`, `mwo_file`, `epoch`, `resolution_class`,
  `carrington_rotation`, `cycle`;
- **position:** `hemisphere`, `lat_flux_weighted_deg`, `dpd_lat_deg`, `dpd_carrington_lon_deg`, `dpd_lcm_deg`,
  `dpd_area_msh`;
- **measurement:** `flux_window_mx`, `tilt_deg`, `joy_gamma_deg`, `leading_polarity_sign`, `hale_expected_sign`,
  `lon_pos_deg`, `lat_pos_deg`, `lon_neg_deg`, `lat_neg_deg`, `separation_deg`;
- **quality:** `isolated_day`, `n_neighbours`, `candidate_rank`, `n_candidate_days`, `n_blank_window`;
- **activity:** `activity_dpd_norm`, the monthly hemispheric DPD area normalised to the 1974–2012 mean.

## 6. Exclusions and quality control

- **A1:** BLANK pixels (−32768) are excluded.
- **A2:** 18 magnetograms with header GV = 0.03 (1988-10-21; 1989-09-03/05). Their field is scaled by about 100 and
  saturated.
- **A3:** 8 magnetograms whose central-disc median |B| exceeds 3 times the median of the Fe I scans of the 7
  surrounding UTC days. The rule was written after a pixel audit of all 30 952 Fe I magnetograms, without looking at
  the tilts.
- Two 2013 files are unreadable. 33 scans have no usable central-disc pixels; none of them produces a selected record.
- `EXCLUDED_MAGNETOGRAMS.csv` lists only the 26 exclusions of A2 and A3. Every failed attempt is recorded in the
  catalogue products MAGNETOGRAMS, ATTEMPTS and LOSSES.
- Every record and every column of the release was recomputed by independent code:
  - catalogue recount 18/18;
  - release check 115/115.

## 7. Comparisons with other instruments (descriptive)

**SDO/HMI SHARP (P1), same region and UTC day.**
- Pilot comparison, 211 regions (2010–2013): the leading polarity agrees in 95.7 % of regions; median d_γ −0.69°;
  median |d_ax| 4.40°.
- Catalogue comparison (`COMPARISONS/S2_P1*`), 153 isolated records in 2010-05 to 2012-12:
  - median γ_MWO − γ_HMI: +0.71°;
  - the slope of the difference against activity has an interval that contains zero;
  - the variance fit sits at the boundary of its domain.

**DPD white-light tilts, same group and day.** 4694 of the 5223 isolated records (89.9 %) have one.
- By epoch and hemisphere (`COMPARISONS/S1_TABLE.csv`):
  - the bootstrap check was not determined, because two small epoch–hemisphere cells (E1N, E7S) make 28.7 % of the
    replicates singular;
  - among the non-singular replicates, only E4N differs by more than the 2.4° threshold with an interval that
    excludes zero.
- Against activity: the slope of the MWO − white-light difference is −3.18, nominal 97.5 % interval [−8.77, +2.40].
  - The interval is not contained in the equivalence margin ±0.53, and it includes zero: the check could not show
    stability against activity, and it does not show a dependence on activity either.
  - Magnetic and white-light tilts differ for physical and observational reasons (Wang et al. 2014).
- DPD sources by epoch: `COMPARISONS/S1_DPD_SOURCES.csv`.

**Hale agreement** (`COMPARISONS/S3_HALE.csv`): 0.79–0.90 in epoch–hemisphere cells with at least 45 records.

## 8. Joy's law per cycle (descriptive, no test)

Model: k in γ = k·sin|λ̄|, per cycle and hemisphere, least squares through the origin. Intervals are percentile
bootstrap over blocks of 6 Carrington rotations (2000 replicates, seed 69 500 001).

Flux-weighted k, in degrees:

| Cycle | N | S |
|---|---|---|
| 20 (partial) | 0.1 [−9.0, 64.6] | 23.2 [16.4, 67.3] |
| 21 | 27.1 [11.4, 40.5] | 22.2 [8.8, 36.2] |
| 22 | 24.2 [16.9, 30.8] | 26.6 [18.5, 36.3] |
| 23 | 16.5 [9.3, 25.2] | 22.5 [13.7, 31.4] |
| 24 (partial) | 17.5 [3.6, 43.2] | 8.8 [−5.6, 28.8] |

Unweighted values are in `JOY_BY_CYCLE.csv`. k (degrees, in γ = k sin|λ|) is not the same quantity as a
tilt–latitude slope in degrees per degree. Any comparison with published values must state functional form,
population, weights and tilt convention, and stays descriptive.

## 9. Status of the test T3 (for context; not a property of the data)

The pre-registered analysis gives a slope of the Joy coefficient with activity of β₃ = −4.93, nominal 97.5 % interval
[−10.21, +0.34].
- It is **descriptive, with no verdict on the presence or absence of tilt quenching**. The frozen stability rule
  requires it because both checks were inconclusive: the epoch comparison was not determined and the
  white-light/activity check could not show stability.
- The interval contains zero and also the values projected for a 10–20 % quenching ramp.
- No quenching percentage should be derived from it.
- Reports: `docs/T3_MWO_STABILITY_R4_RESULTS.md`, `docs/T3_MWO_FINAL_RESULTS.md`.

## 10. Known limits

- **Resolution:** the observing resolution is about 10″–20″. Compact regions are measured less reliably than with
  SDO/HMI.
- **Native corrections:** the saturation and zero-point corrections in the native MWO FITS are not documented, and no
  correction is applied.
- **Selection:** it depends on activity and size (§2).
- **Epochs:** before 1996 they are known only from the headers. Their relative stability is not established (§7).
- **Drifts:** slow changes within an epoch are not checked.
- **White-light comparison:** it is relative; it is not an absolute calibration.

## 11. Provenance, reproduction, credits

**Data:**
- MWO 150-ft tower synoptic magnetograms (UCLA / Mount Wilson Observatory; Ulrich et al. 2002, 2024);
- Debrecen Photoheliographic Data (Baranyi et al. 2016; Győri et al. 2017);
- SDO/HMI SHARP (Bobra et al. 2014), for the comparison only;
- WDC-SILSO, Royal Observatory of Belgium, for activity sensitivities.

The exact acknowledgement texts are to be taken from the providers.

**Code** (repository SHARP BL, branch `v8.4-python-gianluca`):

| Step | Script |
|---|---|
| Measurement | `scripts/t3_mwo_catalogue.py` |
| Recount | `scripts/t3_mwo_catalogue_recount.py` |
| Export | `scripts/t3_mwo_catalogue_release.py` |
| Release check | `scripts/t3_mwo_release_recount.py` |
| Comparisons | `scripts/t3_mwo_analysis.py --stability`, `scripts/t3_mwo_stability_extras.py` |

**Commits:** catalogue R4 `823d29e`; release `93f3eb7`; release check `3c88ca5`.

**Li & Ulrich (2012) availability, checked 23 November 2026:**
- the paper (arXiv:1209.1642) has no data availability statement and gives only aggregated tables;
- the authors' page (www2.ess.ucla.edu/~jingli/ApJ201210/) does not respond. Its archived copy of 2026-07-20 shows
  text and figures only;
- VizieR did not respond during the check, so its availability is not determined.

**Licence, authors, deposit:** to be agreed.

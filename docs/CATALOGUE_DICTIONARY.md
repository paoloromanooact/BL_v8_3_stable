# Dizionario del catalogo `results/P1/P1_SBL_CATALOG_BY_HARP.csv`

Una riga per **record** SHARP misurato (record primario e record di controllo
di ogni HARP; un solo record con `role = both` se coincidono). 14195 righe,
7133 HARP, 2010-05-01 → 2026-09-29. Protocolli: P1, P1b, P1c, P1d, P1e.
Valori mancanti: celle vuote (NaN); per i segni, 0 = non definito.

## Identificazione e selezione

| Colonna | Unità / valori | Significato |
|---|---|---|
| `HARPNUM` | intero | numero HARP di JSOC |
| `T_REC` | `AAAA.MM.GG_hh:mm:ss_TAI` | istante del record (TAI) |
| `role` | primary / control / both | P1 §4: primario = più vicino al meridiano centrale (\|LON_FWT\| ≤ 30°); controllo = flusso USFLUX massimo entro ±60° |
| `QUALITY`, `qual_0x80` | intero; 0/1 | keyword QUALITY; 1 se QUALITY = 0x80 (P1b) |
| `LON_FWT`, `LAT_FWT` | gradi (Stonyhurst, ovest > 0) | posizione pesata col flusso (JSOC) |
| `USFLUX` | Mx | flusso unsigned di JSOC (altra maschera e soglia) |
| `NOAA_NUM`, `NOAA_AR`, `NOAA_ARS` | intero; testo | numero e identificativi delle regioni NOAA nella HARP |
| `CRPIX1`, `CRPIX2` | pixel | centro della mappa (dimensione ≈ 2·CRPIX) |
| `CR` | intero | rotazione di Carrington del record (parte intera di CAR_ROT) |
| `hemisphere` | N / S | dal segno di `lat_mean_deg` (v8.4) |

## Misura v8.4 (P1 §3; maschera bitmap ≥ 33, \|Br\| ≥ 100 G, \|Br\| ≤ 10⁴ G)

| Colonna | Unità | Significato |
|---|---|---|
| `phi_mx`, `phi_pos_mx`, `phi_neg_mx` | Mx | flusso unsigned totale, positivo, negativo sopra soglia |
| `d_cm` | cm | distanza di cerchio massimo tra i centroidi di polarità (R = RSUN_REF) |
| `lat_mean_deg`, `coslat` | gradi; — | latitudine del centroide sferico pesato con \|Br\|; suo coseno |
| `lon_mean_stony` | gradi | longitudine di Stonyhurst del centroide |
| `lon_pos`, `lat_pos`, `lon_neg`, `lat_neg` | gradi (Carrington) | centroidi delle due polarità |
| `tilt_deg`, `tilt_reduced_deg` | gradi | angolo leading→following nel piano tangente (x ovest, y nord); ridotto in (−90°, 90°] |
| `sintilt` | — | sin α > 0 se la following è a nord della leading |
| `leading_sign` | ±1 | polarità più a ovest |
| `expected_leading_sign` | ±1 | polarità leading attesa (Hale) dato ciclo ed emisfero |
| `hale_sign` | ±1 (0 non definito) | +1 se leading osservata = attesa |
| `cycle`, `cycle_state`, `p_new` | intero; testo; — | ciclo assegnato; DATE / DATE_IN_WINDOW / LATITUDE / AMBIGUOUS; probabilità del ciclo nuovo (P1c) |
| `s_bl` | Mx·cm | S_BL = hale_sign · Φ · d · cos λ · sin α |
| `d_axial_g`, `d_axial_bal_g` | G | contributo al dipolo assiale iniziale: 3/(4πR²) Σ Br sin λ dA; versione bilanciata |
| `nmask`, `npos`, `nneg` | pixel | pixel della maschera; sopra soglia positivi e negativi |
| `quality_flag`, `quality_string`, `valid_bl` | intero; testo; 0/1 | codici di qualità come v8.3; 1 = misura valida |
| `diagnostic_reason`, `suspicious_flag` | testo; 0/1 | ANTI_HALE, LARGE_TILT (> 60°) o motivo di non validità |

## Misura v8.3 (`leg_*`, metodo legacy; maschera bitmap ≥ 1)

`leg_phi_mx`, `leg_d_cm`, `leg_lat_mean_deg`, `leg_tilt_deg`, `leg_tilt_reduced_deg`,
`leg_sintilt`, `leg_leading_sign`, `leg_hale_sign`, `leg_cycle`, `leg_s_bl`,
`leg_valid_bl`, `leg_quality_string`, `leg_diagnostic_reason`, `leg_hemisphere`:
stesso significato delle colonne v8.4, calcolate come nella v8.3 IDL (pixel,
latitudine da sin(CRVAL2) + (j − CRPIX2)Δμ, R = 6,957·10¹⁰ cm, ciclo dalla data).

## Keyword JSOC del record (`key_*`)

`key_CAR_ROT`, `key_CRLN_OBS` (gradi), `key_LAT_FWTPOS`, `key_LON_FWTPOS`,
`key_LAT_FWTNEG`, `key_LON_FWTNEG` (gradi, Stonyhurst per le longitudini),
`key_USFLUX` (Mx): dai file `.keys.json` scaricati con i FITS.

## Ricomparse candidate (P1e)

| Colonna | Significato |
|---|---|
| `recurrence_of` | HARP precedente di cui questa è candidata ricomparsa (vuoto se nessuna) |
| `family_id`, `family_rank` | famiglia di candidate ricomparse; 0 = prima HARP |
| `first_seen_on_disk` | 1 se il primo record ha LON_FWT > −60° |
| `p1d_family_rank` | regola P1d (sostituita), solo per confronto |

## Provenienza e stato

| Colonna | Significato |
|---|---|
| `sha256_P1` … `sha256_P1e` | SHA-256 dei protocolli applicati |
| `git_commit`, `git_dirty` | commit del codice che ha prodotto il file; 1 se c'erano modifiche non committate |
| `complete_series`, `validation_passed` | 1 se tutti i record sono presenti / i controlli obbligatori sono superati |

## Riproduzione

```bash
python3 -m virtualenv .venv && .venv/bin/pip install -r requirements-v84.txt
.venv/bin/python python/sharpbl/fetch_metadata.py          # metadati (senza email)
.venv/bin/python python/sharpbl/select_records.py          # P1 §4, P1b
.venv/bin/python python/sharpbl/cycle_boundary.py          # P1 §5, P1c
.venv/bin/python python/sharpbl/download_records.py        # FITS (as-is) + keys.json, ~5,7 GB
.venv/bin/python python/sharpbl/run_p1.py                  # catalogo, somme, confronto, controlli
.venv/bin/python python/sharpbl/figures_p1.py              # figure P1
.venv/bin/python python/sharpbl/run_p3.py                  # P3 (BARD)
.venv/bin/python python/sharpbl/run_p2.py                  # P2 (descrittivo, dopo P2E_ACCEPTANCE)
OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2d.py --validate --estimator p2e   # validazione P2e
```
I metadati di JSOC possono cambiare nel tempo (nuovi mesi, riprocessamenti):
la riproduzione esatta richiede le copie su disco dei metadati e dei FITS.

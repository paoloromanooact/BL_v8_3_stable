# Indice di figure e tabelle: dati, script, commit

Ogni CSV di risultato contiene anche le colonne `git_commit` (codice che l'ha
prodotto), `git_dirty` e gli SHA-256 dei protocolli; quelli esplorativi anche
`status` e gli SHA-256 dei file di input. "Commit" qui è quello che ha
aggiunto o aggiornato il file nel repository.

| Elemento | File | Dati tracciati / input | Script | Commit | Stato |
|---|---|---|---|---|---|
| Fig. diagramma a farfalla | `figures/P1/fig1_butterfly.png` | `figures/P1/data/fig1_butterfly.csv` ← catalogo P1 | `figures_p1.py` | `120f852` | protocollo P1–P1e |
| Fig. serie per CR e dipolo cumulato | `figures/P1/fig2_series_by_cr.png` | `figures/P1/data/fig2_*.csv` ← `P1_SBL_BY_CR_HEMISPHERE.csv` | `figures_p1.py` | `120f852` | protocollo |
| Fig. v8.3 contro v8.4 | `figures/P1/fig3_legacy_vs_v84.png` | `figures/P1/data/fig3*.csv` ← `P1_LEGACY_VS_V84.csv` | `figures_p1.py` | `120f852` | protocollo |
| Fig. casi di Hale cambiato | `figures/EXPLORATORY/hale_transition_cases.png` | `figures/EXPLORATORY/data/hale_transition_cases.csv` ← FITS | `hale_case_figures.py` | `6439f5d` | esplorativo |
| Catalogo per record | `results/P1/P1_SBL_CATALOG_BY_HARP.csv` | FITS + `P1_RECORD_SELECTION.csv` + `CYCLE_BOUNDARY_FITS.csv` + metadati | `run_p1.py` | `120f852` (codice `3947ee8`) | protocollo |
| Somme per CR ed emisfero | `results/P1/P1_SBL_BY_CR_HEMISPHERE.csv` | catalogo | `run_p1.py` | `120f852` | protocollo |
| Controlli della serie | `results/P1/P1_CHECKS.csv` | catalogo, caso di prova, test | `run_p1.py` | `120f852` | protocollo |
| Validazione con BARD | `results/P3/P3_BARD_*.csv`, `P3_RANDOM_CONTROL.csv` | BARD v3.0, metadati, FITS contemporanei, catalogo | `run_p3.py` | `c41fa4c` | protocollo P3–P3c |
| Test del quenching (descrittivi) | `results/P2/P2_*.csv`, `P2B_*.csv`, `P2D_TESTS.csv` | catalogo, SILSO emisferico | `run_p2.py` | `c41fa4c` | protocollo, solo descrittivo |
| Validazione della procedura P2d/P2e | `results/P2/P2E_VALIDATION*.csv`, `P2E_ACCEPTANCE.csv` | cataloghi sintetici | `p2d.py --validate` | `3da29da` (codice `3fcd702`) | protocollo P2d/P2e |
| Calibrazione P2b | `results/P2/P2B_CALIBRATION_RUN1_N40.*`, `..._RUN2_N100.*` | cataloghi sintetici | `run_p2.py` | `fb3e8ae` e successivi | protocollo P2b |
| Fattoriale e analisi esplorative | `results/EXPLORATORY/*.csv` | `FACTORIAL_BY_RECORD.csv.gz` ← FITS; catalogo; coppie BARD | `factorial.py`, `exploratory.py` | `6439f5d` | **esplorativo** |
| Diagnosi di P2d/P2e e quadro delle sensibilità | `results/DIAGNOSTIC/DIAG_*.csv`, `SENS_*.csv` | validazione P2e, test P2, catalogo, somme P1 | `diag_summary.py` | 2026-11-09 | **diagnostico/descrittivo** (`docs/DIAGNOSTIC_P2E.md`, `docs/SENSITIVITY_SUMMARY.md`) |
| Controllo diagnostico A (varianza nulla contro vera) | `results/DIAGNOSTIC/A_*.csv*` | cataloghi sintetici della validazione P2e (semi 40000 + k) | `diag_a_variance.py` | 2026-11-09 (codice `5315103`) | **diagnostico** (`docs/DIAGNOSTIC_A_PLAN.md`, `docs/DIAGNOSTIC_A_RESULTS.md`) |
| Controllo diagnostico B (oracolo, parametri temporali veri) | `results/DIAGNOSTIC/B_*.csv*` | cataloghi sintetici V1–V4 della validazione P2e, stessi semi | `diag_b_oracle.py` | 2026-11-09 (codice `d171cee`) | **diagnostico** (`docs/DIAGNOSTIC_B_PLAN.md`, `docs/DIAGNOSTIC_B_RESULTS.md`) |
| Controllo diagnostico C (componente individuale e leva) | `results/DIAGNOSTIC/C_*_RUN1.*` (C2-T3 non valido), `C2_A1_*` | cataloghi sintetici V1–V4 della validazione P2e | `diag_c_individual.py`, `diag_c2_a1.py` | 2026-11-09 (codice `c56779f`, `555c973`) | **diagnostico** (`docs/DIAGNOSTIC_C_PLAN.md`, `..._A1.md`, `docs/DIAGNOSTIC_C_RESULTS.md`) |
| Verifica di coerenza di C1 (post hoc) | `results/DIAGNOSTIC/AUDIT_C1_*.csv` | `A_BY_CATALOGUE.csv.gz`, `C_RAW_RUN1.csv.gz` | `diag_c1_audit.py` | 2026-11-09 | **verifica post hoc** (`docs/DIAGNOSTIC_C1_AUDIT.md`) |
| Controlli diretti su C1 (finitezza, trasformazione di T3) | `results/DIAGNOSTIC/C1_CHECKS_DIRECT.csv`, `C1_INPUTS_RESIM_BY_CATALOGUE.csv.gz`, `C1_T3_TRANSFORM*.csv*`, `C1_T3_UNITS.csv` | cataloghi di sviluppo, `C_RAW_RUN1.csv.gz`, `A_BY_CATALOGUE.csv.gz` | `diag_c1_checks.py`, `diag_c1_t3_units.py` | 2026-11-09 | **verifica post hoc** (`docs/DIAGNOSTIC_C1_AUDIT.md` §4) |
| Controllo diagnostico D (livello di C1 su cataloghi nuovi) | `results/DIAGNOSTIC/D_*` | cataloghi sintetici nuovi (semi 1 000 000 + 100 000·s + k) | `diag_d_new_seeds.py` | 2026-11-09 (codice `b1f8eaf`) | **diagnostico** (`docs/DIAGNOSTIC_D_PLAN.md`, `..._A1.md`, `docs/DIAGNOSTIC_D_RESULTS.md`) |

Riproduzione: comandi in `docs/CATALOGUE_DICTIONARY.md`; analisi esplorative:
`.venv/bin/python python/sharpbl/factorial.py` poi `exploratory.py` e
`hale_case_figures.py`.

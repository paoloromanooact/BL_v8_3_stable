# Indice di figure e tabelle: dati, script, commit

Le esecuzioni recenti registrano `git_commit`, `git_dirty` e gli SHA-256 dei protocolli;
alcune tabelle derivate ereditano la provenienza dagli input, e alcuni file storici non la
registrano. Le eccezioni sono nella tabella finale. "Commit" nell'indice è quello che ha
aggiunto o aggiornato il file nel repository, distinto dal commit del codice eseguito.

La bozza `docs/REPRO_GIT_REFERENCES_DRAFT.csv` separa per ogni tabella il commit/blob
del riferimento distribuito, i commit registrati nei dati e l'eventuale codice effettivo
dichiarato con evidenza (JSON storici P2b). È una ricognizione, non una certificazione
dell'identità del produttore o della riproduzione numerica. Regole e scale proposte:
`docs/REPRO_COMPARISON_RULES.md` e le due tabelle di chiavi e scale associate.

Revisione di queste regole: `docs/REPRO_REVIEW_21E7210.md`. La prima verifica è
congelata in `docs/REPRO_PHASE1_PLAN.md` e comprende soltanto cinque CSV delle figure P1:
non è ancora stata eseguita. `docs/MDI_SMARP_FEASIBILITY.md` è uno studio documentale,
non un risultato di calibrazione o un'estensione della serie.

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
| Pilota di sviluppo P2f: test preliminari | `results/P2F_PILOT/PRELIM_TESTS.csv`, `PRELIM_T1_REML.csv`, `PRELIM_T2_VARFUN.csv` (esecuzione 1 fallita: `PRELIM_*_RUN1.csv`) | disegno reale senza risposte (catalogo P1, SILSO), serie sintetiche (semi 5 000 000 + k), `A_BY_CATALOGUE.csv.gz` | `p2f_pilot.py --selftest` | 2026-11-11 (codice `67058f6`; esecuzione 1 `e98b3bf`) | **sviluppo** (`docs/P2F_PILOT_PLAN.md`, `..._A1.md`, `..._A2.md`) |
| Pilota di sviluppo P2f: conteggi del disegno congelato | `results/P2F_PILOT/DESIGN_CHECKS.csv` | catalogo P1 senza risposte, SILSO (seme sintetico 5 000 950 solo per costruire le unità) | `p2f_checks.py design` | `211b3ed` | **sviluppo** (`docs/P2F_PILOT_IMPLEMENTATION_NOTE.md`) |
| Pilota di sviluppo P2f: esecuzione unica | `results/P2F_PILOT/PILOT_RAW.csv.gz`, `PILOT_FALSE_VERDICTS.csv`, `PILOT_POWER.csv`, `PILOT_CHOICE.csv` | disegno reale senza risposte, risposte sintetiche (semi 3 000 000 + 100 000·s + k, potenza 3 900 000 + …, bootstrap 4 000 000 + …) | `p2f_pilot.py` | `bea7de8` (codice `67058f6`) | **sviluppo, nessun verdetto** (`docs/P2F_PILOT_RESULTS.md`) |
| Pilota P2f: controllo indipendente e diagnostica | `results/P2F_PILOT/POST_CHECKS*.csv`, `PILOT_DIAGNOSTICS_M.csv`, `PILOT_ERRORS.csv` | `PILOT_RAW.csv.gz` e tabelle del pilota | `p2f_checks.py raw`, `diag` | `bea7de8` (codice `c9258fe`, `bea7de8`) | **verifica** (`docs/P2F_PILOT_IMPLEMENTATION_NOTE.md` §3) |
| Validazione P2f (procedura M) | `results/P2F/VALIDATION_RAW.csv.gz`, `VALIDATION_FALSE_VERDICTS.csv`, `VALIDATION_COVERAGE_POWER.csv`, `VALIDATION_DECISION.csv`, `PRELIM_*.csv` (e `_ed90e15`) | disegno reale senza risposte, risposte sintetiche (semi 6 000 000 + …, 7 500 000 + …, test 20 000 000 + k) | `p2f_validation.py` | `11b71f4` (codice `ed90e15`, provenienza `5c3b664`) | **validazione**: T3 validato, T5 no (`docs/P2F_VALIDATION_RESULTS.md`) |
| Validazione P2f: controllo indipendente | `results/P2F/POST_CHECKS*.csv` (colonna `status` con etichetta «pilota» ereditata, dichiarata) | output della validazione | `p2f_checks.py vraw` | `11b71f4` (codice `a518115`) | **verifica** |
| P2f, applicazione di T3 ai dati reali | `results/P2F/REAL_T3.csv`, `REAL_T3_SENSITIVITY.csv` | catalogo P1, selezione, SILSO; decisione e controlli della validazione | `p2f_apply.py --test T3 --real` | `8ad8e61` (codice ed esecuzione `42fcd01`) | **test validato, esito «non deciso»**; sensibilità non validate (`docs/P2F_RESULTS.md`) |
| Controllo delle HARP dominanti | `results/DOMINANT/*.csv`, `figures/DOMINANT/*.png` | catalogo P1, `PRIMARY_VS_CONTROL_BY_HARP.csv`, 240 FITS (SHA-256 in `DOMINANT_HARP_FITS_SHA256.csv`) | `dominant_harp_check.py` | `36676a9` (esecuzione `1a22e09`) | **descrittivo** (`docs/DOMINANT_HARP_PLAN.md`, `docs/DOMINANT_HARP_RESULTS.md`) |

## File storici, rinominati o senza produttore nel codice attuale

| File | Origine (primo commit) | Come è stato prodotto | Stato |
|---|---|---|---|
| `results/P1/P1E_METADATA_VERIFICATION_BY_YEAR.csv` | `6ffa258` (2026-11-03) | verifica sui metadati citata in `docs/PROTOCOL_P1E_CANDIDATE_RECURRENCES.md` (riga 83), senza script nel repository | storico, conservato; produttore da documentare |
| `results/P3/P3_C1_DISCORDANT_DESCRIPTIVE.csv`, `P3_C1_DISCORDANT_SUMMARY.csv` | `37acdf0` (2026-11-03) | analisi descrittiva citata in `docs/P3_RESULTS_C1.md` §(righe 48–49), senza script nel repository | storico, conservato; produttore da documentare |
| `results/P3/P3_BARD_CONVENTIONS_ATTEMPT1_STOPPED.csv` | `9824ac4` (2026-11-03) | primo tentativo di `run_p3.py` interrotto, rinominato a mano (ha `git_commit`) | esecuzione conservata agli atti |
| `results/P2/P2E_DEVELOPMENT_ESTIMATORS.csv` | `3fcd702` (2026-11-03) | sviluppo degli stimatori di P2e citato in `docs/PROTOCOL_P2E_ATTENUATION_CORRECTION.md`, senza script nel repository | storico (sviluppo), conservato |
| `results/P2/P2B_CALIBRATION_RUN1_N40.*`, `P2B_CALIBRATION_RUN2_N100.*` | `05355e2`, `fb3e8ae` (2026-11-03) | `run_p2.py` (calibrazione P2b), output `P2B_CALIBRATION.*` rinominati a mano per esecuzione (hanno `git_commit`) | esecuzioni conservate |
| `results/P2/P2E_VALIDATION_RAW.csv.gz` | `3da29da` | `p2d.py --validate` scrive il `.csv` non compresso; compresso a mano (il `.csv` non tracciato resta sul disco) | tracciato compresso |
| `results/DIAGNOSTIC/C_*_RUN1.*` | `c092068` (2026-11-09) | `diag_c_individual.py`, rinominati a mano (esecuzione 1, C2-T3 non valido) | esecuzione conservata |
| `results/P2F_PILOT/PRELIM_*_RUN1.csv` | `0eb7bd6` | `p2f_pilot.py --selftest` su `e98b3bf`, test 2 fallito, rinominati a mano | esecuzione conservata |
| `results/P2F/PRELIM_*_ed90e15.csv` | (da committare con la validazione) | `p2f_validation.py --selftest` su `ed90e15`, rinominati a mano prima della riesecuzione su `5c3b664` | esecuzione conservata |
| `results/DOMINANT_TRIAL_2HARP/*` | `9b762f5` | `dominant_harp_check.py --limit 2 --out <scratchpad>` su `a41c451` non pulito, copiati | prova tecnica, non il controllo |

Riproduzione: comandi in `docs/CATALOGUE_DICTIONARY.md`; analisi esplorative:
`.venv/bin/python python/sharpbl/factorial.py` poi `exploratory.py` e
`hale_case_figures.py`.

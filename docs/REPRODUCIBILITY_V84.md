# Riproducibilità della v8.4 — inventario (2026-11-11)

Inventario di sola lettura di comandi, dipendenze, input e output del branch `v8.4-python-gianluca`
(HEAD `a518115` al momento della ricognizione). **Non è una verifica eseguita**: nessuno script è
stato rilanciato per questo documento (la validazione P2f occupava la macchina). Distingue ciò che
si rigenera dal solo repository (o dallo ZIP) da ciò che richiede i dati esterni non tracciati.
Le verifiche effettive (rilancio e confronto byte per byte) sono elencate in §7 come lavoro
da fare.

## 1. Ambiente

- Python 3.10 (`.venv/pyvenv.cfg`: CPython 3.10.12, virtualenv 21.14.12, senza pacchetti di
  sistema). Creazione: `python3 -m virtualenv .venv && .venv/bin/pip install -r requirements-v84.txt`.
- `requirements-v84.txt`, versioni bloccate: numpy 2.2.6, scipy 1.15.3, astropy 6.1.7,
  pandas 2.3.3, matplotlib 3.8.4, drms 0.9.0, pytest 9.2.0. (`requirements.txt` è quello della
  v8.3, senza versioni; IDL/SolarSoft servono solo alla pipeline v8.3 in `idl/` e `scripts/`.)
- Esecuzioni numeriche con `OMP_NUM_THREADS=1` dove indicato (p2d, pilota, validazione).
- Controlli offline: `bash scripts/check_repo.sh` (sintassi Bash, `ast.parse` di `python/` e
  `tests/`, help del launcher, pytest) e `git diff --check`. Test: `.venv/bin/python -m pytest -q tests`
  (40 funzioni di test in 4 file, tutte su dati sintetici o file tracciati; il «20 test» di
  `README_V84.md` è superato e va corretto).

## 2. Input non tracciati (fuori dallo ZIP)

| Percorso | Dimensione | Contenuto | Serve a |
|---|---|---|---|
| `data/sharp` → `/storage/shared/gianluca/SHARP_BL` (link) | | | |
| `data/sharp/metadata/sharp_meta_*.csv` | 245 MB | keyword JSOC `hmi.sharp_cea_720s`, orarie, 2010-05 → 2026-09 | `select_records.py`, `run_p1.py`, `run_p3.py` |
| `data/sharp/fits/<anno>/*.Br.fits`, `*.bitmap.fits`, `*.keys.json` | 5,5 GB | 14 195 record selezionati | `run_p1.py`, `factorial.py`, `hale_case_figures.py` |
| `data/sharp/fits_p3/` | 846 MB | record per il confronto BARD (C1) | `run_p3.py` |
| `data/sharp/external/BARD/` | 6 MB | cataloghi BARD MDI/HMI, `PROVENANCE.txt`, `SHA256.txt` | `run_p3.py` |
| `data/sharp/test_20240508/` | 13 MB | caso di prova v8.3 (26 FITS) | `compare_test_case.py`, controllo legacy in `run_p1.py` |

Tracciati e sufficienti per tutto il resto: `ancillary/SILSO_HEMI/` (con `SHA256.txt` e
`PROVENANCE.json`), `results/`, `figures/`, `docs/`. Esclusi da Git anche `output/`, `logs/`,
`.venv/`, `results/P2F_PILOT/_design.pkl`, `results/P2F/_design.pkl` (rigenerati dagli script).

I metadati JSOC possono cambiare nel tempo (`docs/CATALOGUE_DICTIONARY.md` §Riproduzione): una
riesecuzione esatta richiede le copie su disco di metadati e FITS, non un nuovo download.

## 3. Catena e dipendenza dai dati esterni

Legenda: **ZIP** = solo file tracciati; **meta** = metadati JSOC; **FITS** = FITS in `data/sharp`;
**rete** = scarica da JSOC.

| # | Script (`python/sharpbl/`) | Input principali | Output | Richiede |
|---|---|---|---|---|
| 1 | `fetch_metadata.py` | JSOC | `data/sharp/metadata/*.csv` | rete |
| 2 | `select_records.py` | metadati | `results/P1/P1_RECORD_SELECTION.csv`, `P1_NO_CM_RECORD.csv` | meta |
| 3 | `cycle_boundary.py` | `P1_RECORD_SELECTION.csv` | `results/P1/CYCLE_BOUNDARY_FITS.csv` | ZIP |
| 4 | `download_records.py` | selezione, JSOC SUMS | `data/sharp/fits/` | rete |
| 5 | `run_p1.py` | selezione, confini, FITS, metadati, caso di prova; esegue pytest | `results/P1/P1_SBL_CATALOG_BY_HARP.csv`, `P1_SBL_BY_CR_HEMISPHERE.csv`, `P1_LEGACY_VS_V84.csv`, `P1_CHECKS.csv` | FITS + meta |
| 6 | `figures_p1.py` | output di 5 | `figures/P1/*.png`, `figures/P1/data/*.csv` | ZIP |
| 7 | `run_p3.py` | BARD, metadati, `fits_p3` (o download), catalogo | `results/P3/P3_BARD_*.csv`, `P3_RANDOM_CONTROL.csv` | FITS + meta + BARD (o rete) |
| 8 | `p2d.py --validate --estimator p2e` | cataloghi sintetici, SILSO | `results/P2/P2E_VALIDATION*.csv`, `P2E_ACCEPTANCE.csv` | ZIP |
| 9 | `run_p2.py` | catalogo (con controllo degli SHA P1–P1e e dei flag), `P1_CHECKS.csv`, selezione, `P2E_ACCEPTANCE.csv`, SILSO | `results/P2/P2_*.csv`, `P2B_*.csv`, `P2D_TESTS.csv` | ZIP |
| 10 | `diag_summary.py`, `diag_a_variance.py`, `diag_b_oracle.py`, `diag_c_individual.py`, `diag_c2_a1.py`, `diag_c1_audit.py`, `diag_c1_checks.py`, `diag_c1_t3_units.py`, `diag_d_new_seeds.py` | output di 8–9, SILSO, cataloghi sintetici, output dei passi precedenti della diagnosi | `results/DIAGNOSTIC/*` | ZIP |
| 11 | `p2f_pilot.py --selftest`, poi `p2f_pilot.py`; `p2f_checks.py design|raw|diag` | catalogo (solo disegno), SILSO, `A_BY_CATALOGUE.csv.gz` | `results/P2F_PILOT/*` | ZIP |
| 12 | `p2f_validation.py --selftest`, poi `p2f_validation.py`; `p2f_checks.py vraw` | come 11, protocollo P2f | `results/P2F/*` | ZIP |
| 13 | `p2f_apply.py --test T3|T5 --real` (solo test validati, dopo 12 e il controllo) | catalogo, selezione, SILSO, decisione e controlli di 12 | `results/P2F/REAL_*.csv` | ZIP |
| E | `factorial.py` → `exploratory.py` → `hale_case_figures.py` | FITS, catalogo, `P3_BARD_MATCHES.csv` | `results/EXPLORATORY/*`, `figures/EXPLORATORY/*` | FITS (E1, E3); ZIP (E2) |

Ordine documentato in `docs/CATALOGUE_DICTIONARY.md` §Riproduzione (passi 1–9) e in
`docs/RESULTS_INDEX.md` (script e commit per ogni file). Le porte di esecuzione sono nel
codice: `run_p2` non parte senza `complete_series` = `validation_passed` = 1 e SHA dei
protocolli coincidenti; `p2d --validate` rifiuta un albero sporco; pilota e validazione P2f
richiedono i test preliminari sullo stesso commit pulito; `p2f_apply` richiede decisione,
controllo indipendente superato e SHA-256 coincidenti dei quattro output e del protocollo.

**Dal solo ZIP si rigenerano**: passi 3, 6, 8–13 ed E2, cioè tutte le tabelle statistiche
(P2, P2d/P2e, diagnosi A–D, pilota e validazione P2f), le figure P1 e le analisi esplorative
derivate. **Richiedono i dati esterni**: il catalogo P1 (passo 5, FITS + metadati), la
selezione (passo 2, metadati), il confronto BARD (passo 7), il fattoriale e le figure dei casi
Hale (E1, E3).

## 4. Provenienza

- Ogni CSV di risultato porta `git_commit`, `git_dirty` (da `git status --porcelain
  --untracked-files=no`; −1 se git manca) e gli SHA-256 dei protocolli richiesti
  (`python/sharpbl/provenance.py`, mappa P1–P3c). I piani diagnostici e P2f aggiungono le
  proprie colonne (`sha256_DIAGNOSTIC_*_PLAN*`, `sha256_P2F_PILOT_PLAN*`,
  `sha256_PROTOCOL_P2F`); P2f non è nella mappa di `provenance.py` ed è gestito dagli script.
- `MANIFEST.txt` è l'elenco dei file tracciati (`git ls-files`), senza hash. Non esiste un
  manifesto di hash dei file tracciati: per un confronto byte per byte serve il repository Git
  o un manifesto da aggiungere (§7).
- Somme di controllo esterne: `ancillary/SILSO_HEMI/SHA256.txt`,
  `data/sharp/external/BARD/SHA256.txt` (non tracciato).

## 5. Incongruenze trovate (da correggere o dichiarare)

1. **`P2E_VALIDATION_RAW`**: `p2d.py` scrive `results/P2/P2E_VALIDATION_RAW.csv` non compresso;
   i consumatori (`diag_summary.py`, `diag_a_variance.py`, `diag_b_oracle.py`) leggono
   `P2E_VALIDATION_RAW.csv.gz`, che è il file tracciato. La compressione è stata un passo
   manuale; il `.csv` non tracciato (14 MB, 2026-11-03) è ancora sul disco e va preservato.
2. **File rinominati a mano**, senza uno script che produca quei nomi:
   `results/DIAGNOSTIC/C_*_RUN1.*`, `results/P2F_PILOT/PRELIM_*_RUN1.csv`,
   `results/P2F/PRELIM_*_ed90e15.csv`. Sono esecuzioni conservate agli atti; il nome va
   documentato nell'indice.
3. **File tracciati senza produttore trovato** tra gli script attuali:
   `results/P1/P1E_METADATA_VERIFICATION_BY_YEAR.csv`; `results/P3/P3_C1_DISCORDANT_DESCRIPTIVE.csv`,
   `P3_C1_DISCORDANT_SUMMARY.csv`, `P3_BARD_CONVENTIONS_ATTEMPT1_STOPPED.csv`;
   `results/P2/P2E_DEVELOPMENT_ESTIMATORS.csv`, `P2B_CALIBRATION_RUN1_N40.*`,
   `P2B_CALIBRATION_RUN2_N100.*`. Vanno ricondotti al commit e allo script (o al passo manuale)
   che li ha generati, oppure dichiarati storici.
4. `README_V84.md` indica «20 test»; le funzioni di test sono 40.
5. `docs/CATALOGUE_DICTIONARY.md` §Riproduzione si ferma a `p2d.py --validate`: mancano la
   diagnosi A–D, il pilota e la validazione P2f (ordine in `docs/RESULTS_INDEX.md` e
   `docs/HANDOFF.md`).

## 6. Che cosa è verificabile da chi ha solo lo ZIP

- Che ogni CSV tracciato dichiari commit, albero pulito e SHA dei protocolli uguali ai file
  `docs/PROTOCOL_*.md` dello ZIP (controllo di coerenza, senza ricalcolo).
- Che i passi 3, 6, 8–13 ed E2 rigenerino i file tracciati (ricalcolo; i tempi: p2d circa
  ore, diagnosi A–D ore, pilota 1,8 h, validazione P2f stimata 15–20 h su 12 processi).
- Che i test passino.
- **Non** verificabile senza i dati esterni: catalogo P1, selezione, BARD, fattoriale.

## 7. Lavoro da fare (nessuno eseguito qui)

1. Rilancio dei passi rigenerabili dal solo ZIP in una copia pulita, confronto byte per byte
   (o numerico, dove gli output contengono date) con i file tracciati; registrare quali
   coincidono. Da fare a macchina libera.
2. Aggiungere un manifesto con SHA-256 dei file tracciati (come nel repository MWO) e il suo
   controllo.
3. Correggere le incongruenze di §5 (compressione di `P2E_VALIDATION_RAW` nello script o nel
   documento; produttori dei file orfani; conteggio dei test; ordine completo in
   `CATALOGUE_DICTIONARY.md`).
4. Separare nel README la riproduzione «dal solo ZIP» da quella «con i dati esterni», con la
   tabella di §3.

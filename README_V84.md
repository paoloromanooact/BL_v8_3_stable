# SHARP BL — v8.4 (Python), branch `v8.4-python-gianluca`

Questo branch porta in Python la pipeline SHARP BL v8.3 di Paolo Romano,
corregge geometria, maschera e assegnazione del ciclo, e la estende da un
singolo istante a una **serie di tutta l'era HMI (2010–2026), con una misura
per HARP**.

**Obiettivo scientifico.** Costruire una serie osservativa della sorgente
Babcock–Leighton (S_BL) e verificare come tilt, latitudine ed
efficienza della sorgente variano rispetto all'attività.

Note sulle definizioni:
- *Una misura per HARP* non equivale necessariamente a una misura per regione
  fisica: una regione può ricomparire con una nuova HARP (ricomparse candidate,
  protocollo P1e) e una HARP può essere complessa o contenere più regioni NOAA.
- *S_BL* è un proxy della sorgente BL **misurato all'istante del record
  selezionato** (il primario è il più vicino al meridiano centrale, non
  necessariamente all'emersione). Non misura
  direttamente quanto campo polare resterà al ciclo successivo: in mezzo
  intervengono evoluzione, cancellazione e trasporto superficiale. Lo stesso
  vale per il contributo al dipolo assiale D e D_bal.

Il codice IDL v8.3 (`idl/`, `scripts/`) non è modificato e resta come
riferimento; `main` non è toccato da questo branch.

## Cosa cambia rispetto alla v8.3

| | v8.3 (IDL) | v8.4 (Python) |
|---|---|---|
| Coordinate | latitudine da sin(CRVAL2) + (j − CRPIX2)·Δμ, distanze in pixel con scala unica | longitudine e latitudine dalla WCS completa (le mappe SHARP CEA sono **oblique**, centrate sulla patch); centroidi, d e tilt **sulla sfera** |
| Maschera | bitmap ≥ 1 (include pixel **esterni** alla HARP) | **bitmap ≥ 33** (solo pixel interni) |
| Soglia | 1000 G nella routine, 100 G nel launcher | **100 G** ovunque |
| Ciclo | dalla sola data (ciclo 25 da 2019-12) | dalla data, ma **dalla latitudine** nelle finestre di sovrapposizione 2010–2011 e 2017–2021 (mistura di gaussiane, mai dalle polarità) |
| Campione | tutte le HARP di un istante | **un record per HARP**, il più vicino al meridiano centrale (\|lon\| ≤ 30°, QUALITY = 0) |
| Grandezze | S_BL = hale_sign · Φ · d · cos λ · sin α | la stessa S_BL, più il contributo al dipolo assiale D e D_bal (indipendenti da Hale e ciclo) |

Effetto sul caso di prova 2024-05-08 03:12 TAI (tabella `output/test_20240508_compare.csv`,
fuori da Git, rigenerata da `python/sharpbl/compare_test_case.py`):
la geometria cambia d di circa il 2% e la latitudine fino a ~2°; la bitmap ha
l'effetto grande. 11150 e 11192 non hanno pixel interni in quell'istante
(USFLUX = 0) e il loro S_BL "anti-Hale" veniva da altre regioni; 11152 passa
da tilt +74,9° (anti-Hale) a −18,4° (Hale normale). Il metodo `legacy`
riproduce esattamente i risultati v8.3 di Paolo.

## Protocolli (congelati prima di guardare la serie)

- [`docs/PROTOCOL_P1_SBL_SERIES.md`](docs/PROTOCOL_P1_SBL_SERIES.md) — misura,
  selezione dei record, regola del ciclo, somme per rotazione di Carrington ed
  emisfero, e la stessa serie con il metodo v8.3 per confronto (§7b).
- [`docs/PROTOCOL_P1B_QUALITY_0x80.md`](docs/PROTOCOL_P1B_QUALITY_0x80.md) — emendamento
  di P1: accetta anche QUALITY = 0x80 (difetto di calibrazione noto, 2016-04 →
  2017-03), con flag e varianti senza quei record.
- [`docs/PROTOCOL_P1C_CYCLE_RULE.md`](docs/PROTOCOL_P1C_CYCLE_RULE.md) — emendamento
  di P1 §5 (non cieco, solo latitudini): due cicli in un gruppo solo se media vecchia
  ≤ 12°, nuova ≥ 18°, distanza ≥ 8°.
- [`docs/PROTOCOL_P2_QUENCHING.md`](docs/PROTOCOL_P2_QUENCHING.md) — test del
  quenching del tilt, in latitudine e dell'efficienza della sorgente; due test
  principali (T3, T5) con intervalli al 97,5%; attività emisferica da SILSO.

Una regola nuova o cambiata richiede un nuovo protocollo, scritto prima di
eseguirlo; gli script registrano lo SHA-256 dei protocolli negli output.

## Installazione

```bash
python3 -m virtualenv .venv
.venv/bin/pip install -r requirements-v84.txt   # numpy 2.2.6, scipy 1.15.3, astropy 6.1.7, pandas 2.3.3, drms 0.9.0
.venv/bin/python -m pytest -q tests             # 60 casi raccolti da pytest (40 funzioni, alcune parametrizzate; test/ invariati dal commit 55cd7f4, conteggio del 2026-11-11): bipoli sintetici, P2, P2d/P2e, P3 su dati sintetici o costruiti
```

Non servono IDL né SolarSoft. `bash scripts/check_repo.sh` controlla la sintassi di tutti i
file Python e Bash e, se pytest è installato (è in `requirements-v84.txt`), esegue i test;
senza pytest lo dice esplicitamente.

`run_p1.py` scrive due flag in ogni output: `complete_series` (tutti i record presenti) e
`validation_passed` (controlli obbligatori superati: il legacy riproduce il caso di prova,
i test passano). Se un controllo obbligatorio fallisce esce con codice 2, e `run_p2.py`
non parte senza entrambi i flag a 1.

## Dati

I dati non sono in Git. `data/sharp` può essere un link a un disco capiente
(qui `/storage/shared/gianluca/SHARP_BL`):

- `data/sharp/metadata/` — keyword SHARP orarie di tutte le HARP, un CSV per
  mese (~150–250 MB in tutto), senza email:
  `.venv/bin/python python/sharpbl/fetch_metadata.py`
- `data/sharp/test_20240508/` — caso di prova (26 FITS, 13 MB):
  `.venv/bin/python python/download_sharp_day.py 2024-05-08 --email <email JSOC> --times 03:12 --out data/sharp/test_20240508`
- `data/sharp/fits/` — `Br` e `bitmap` dei record selezionati da P1
  (export JSOC, email registrata richiesta).

## Codice (`python/sharpbl/`)

| File | Contenuto |
|---|---|
| `geometry.py` | lettura FITS, WCS, area del pixel, centroidi sferici, distanza, tilt |
| `cycle.py` | ciclo per data e per latitudine, polarità leading attesa |
| `measure.py` | `measure_v84` (corretto) e `measure_legacy` (riproduzione v8.3) |
| `fetch_metadata.py` | scaricamento dei metadati, riprendibile |
| `select_records.py` | record primario e di controllo per HARP (P1 §4, P1b) |
| `download_records.py` | download diretto (as-is) di Br e bitmap, keyword in `.keys.json`, riprendibile |
| `cycle_boundary.py` | regola del ciclo nelle sovrapposizioni (P1 §5, P1c) |
| `provenance.py` | SHA-256 dei protocolli e commit negli output |
| `run_p1.py` | serie P1: catalogo per HARP (v84 e legacy), somme per CR ed emisfero, confronto, controlli |
| `figures_p1.py` | figure della serie (farfalla, somme per CR, confronto v8.3/v8.4) con i valori in `figures/P1/data/` |
| `run_p2.py` | test P2 (T0–T5), bootstrap a blocchi sulle CR; parte solo con la serie P1 completa |
| `compare_test_case.py` | confronto v8.3/v8.4 sul caso di prova |

## Stato

- [x] Porting, correzioni e test sintetici; legacy verificato sul caso di prova.
- [x] Protocolli P1, P1b–e, P2, P2b–e, P3, P3b–c congelati.
- [x] Metadati di tutte le HARP: 8296 HARP, 2010-05 → 2026-09; 7133 con record primario.
- [x] Selezione dei record e scaricamento dei FITS: 14195/14195 record (~4,5 GB).
- [x] Elaborazione completa dei record selezionati (14195 record, 7133 HARP) e
  controlli interni obbligatori superati (`complete_series` = `validation_passed` = 1); figure.
- [x] Confronto esterno P3 C1 con BARD: accordo su geometria e convenzioni
  magnetiche (tilt, polarità leading, separazione, latitudine) nel campione
  confrontato (999 regioni, circa il 69% di BARD) (`docs/P3_RESULTS_C1.md`); C2 riportato.
- [ ] L'**ampiezza** della sorgente (Φ, S_BL, D) non ha ancora una validazione
  esterna equivalente: il rapporto dei flussi nostro/BARD è 1,67 in C1.
- [x] Validazione della procedura P2d/P2e: criterio **non** soddisfatto; T3 e T5 solo descrittivi
  (`docs/P2_DECISION_DESCRIPTIVE_FALLBACK.md`). Le cause del mancato superamento
  non sono ancora state diagnosticate.
- [x] P2 descrittivo sui dati reali (`docs/P2_RESULTS_DESCRIPTIVE.md`): legge di Joy presente;
  T3 e T5 senza verdetto. Una pendenza negativa non dimostra il quenching; una
  pendenza vicina a zero non dimostra un'efficienza costante.
- [ ] Discussione con Paolo.
- [ ] Prossimi controlli: `docs/HANDOFF.md`, "Prossimi passi".

## Ancillari

- `ancillary/SILSO_HEMI/` — numero di macchie emisferico SILSO V2.0
  (WDC-SILSO, Royal Observatory of Belgium), con provenienza e SHA-256.

# Riproducibilità, fase 1 — valori delle figure P1: risultati

Stato: **eseguita il 2026-11-13** secondo il piano congelato `docs/REPRO_PHASE1_PLAN.md`
(`0f51e61`, SHA-256 `638c308e…`), dopo la fine della validazione P2f e del suo controllo. Esito:
**fase 1 superata** per i cinque CSV, con due correzioni del comparatore prima dei confronti successivi
(dichiarate in §3; tre confronti conservati). Attesta i valori delle figure P1 **condizionatamente agli input P1 distribuiti**:
non ricostruisce P1 dai FITS, non valida P2/P2f, non verifica BARD e non certifica l'intero progetto.

## 1. Preparazione

- Comparatore `scripts/repro_compare.py` scritto e committato prima del rilancio (`06eedec`), con
  16 prove sintetiche (chiavi mancanti, duplicate e vuote, righe permutate, NaN e infiniti, schema,
  valori minuscoli T5, conteggi, provenienza e `status` alterati): tutte con l'esito atteso.
- Clone locale isolato e pulito (`git clone --no-local`, nessun file non tracciato copiato) al commit
  `120f852510f2b4ecb7c54fbbb8bad9ee21ac3be2`; verificati SHA-256 e blob Git dei 3 moduli di codice,
  dei 3 input e dei 5 riferimenti elencati in `docs/REPRO_PHASE1_FILES.csv`: tutti coincidenti.
- Ambiente separato (non quello del processo P2f): Python 3.10.12, numpy 2.2.6, scipy 1.15.3,
  pandas 2.3.3, matplotlib 3.8.4, astropy 6.1.7 da `requirements-v84.txt` di `0f51e61`; piattaforma
  Linux 6.8.0-138-generic x86_64, glibc 2.35. Elenco completo in `results/REPRO_PHASE1/run/`. Sono le
  versioni prescritte per il rilancio, non prova dell'ambiente originale delle figure.

## 2. Rilancio

Dalla radice del clone, un processo:
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg timeout 600s python python/sharpbl/figures_p1.py`
— 2026-11-13 08:42:18–08:42:19 UTC, codice di uscita 0, ben dentro il limite di 10 minuti. Il clone
era pulito prima e **è rimasto pulito dopo** (`git status` vuoto): i 5 CSV e anche i 3 PNG accessori
rigenerati sono byte-identici ai file tracciati in `120f852`. Hash in
`results/REPRO_PHASE1/run/regenerated_sha256_and_clean_after.txt`. I PNG non entrano
nell'accettazione (piano).

## 3. Confronto

**Prima esecuzione del confronto (conservata come `results/REPRO_PHASE1/*_RUN1.*`):** 4 file su 5
superati; `fig3a_s_bl_by_cr.csv` respinto per «chiave mancante» nel riferimento e nel rilancio. La
causa è nel comparatore: le regole congelate (§2) ammettono componenti di chiave mancanti per
schema con un marcatore esplicito, e in quel file tutte le 424 righe sono righe per CR × emisfero
con `HARPNUM` e `T_REC` vuoti per costruzione (con il marcatore la chiave è unica). Il comparatore
è stato corretto per applicare la regola, con due prove sintetiche aggiunte (18 su 18 con l'esito
atteso), e committato (`a92e34d`) **prima** del secondo confronto sugli stessi output rigenerati.
Correzione **non cieca**: l'identità byte per byte era già stata osservata.

**Confronto finale** (`results/REPRO_PHASE1/PHASE1_FILES_REPORT.csv`, `PHASE1_COLUMNS_REPORT.csv`,
`PHASE1_META.json` con gli SHA-256 di piano, regole, tabelle e comparatore):

| File | Righe | Chiave | Byte-identico | Valori |
|---|---|---|---|---|
| `fig1_butterfly.csv` | 4189 | HARPNUM | sì | uguali |
| `fig2_cumulative_d_bal.csv` | 220 | CR | sì | uguali |
| `fig2_series_by_cr.csv` | 424 | variant, CR, hemisphere | sì | uguali |
| `fig3a_s_bl_by_cr.csv` | 424 | HARPNUM, T_REC, CR, hemisphere (marcatore) | sì | uguali |
| `fig3b_tilt_difference.csv` | 4189 | HARPNUM | sì | uguali |

- Schema, cardinalità e insieme delle chiavi identici in tutti i file.
- 59 colonne confrontate: tutte le colonne esatte senza differenze; le 25 colonne continue
  **identiche** in tutti i valori (scarto massimo assoluto e normalizzato 0, nessuna fuori
  tolleranza); colonne di provenienza ereditate dagli input (`git_commit`, `git_dirty`, SHA P1–P1e)
  uguali.
- Riferimenti letti da Git (`git show 120f852:<file>`) con SHA-256 uguale a quello fissato.

**Terzo confronto, dopo la revisione esterna di `ceb5d38`** (il secondo è conservato come
`results/REPRO_PHASE1/*_RUN2.*`). Il revisore ha confermato identità dei CSV, hash congelati, assenza di
sostituzioni dei riferimenti e legame del rapporto agli hash, e ha trovato due difetti del comparatore,
riproducibili su input sintetici e senza effetto su questi cinque file byte-identici:
(1) pandas legge un campo che inizia con un byte NUL come vuoto, quindi un testo con NUL (o il
marcatore interno scritto nel file) poteva essere accettato come chiave mancante; (2) nelle colonne
esatte la conversione numerica passava per float64, e grandi interi diversi (9007199254740992 e
…993) risultavano uguali. Correzioni (`d757255`, prima del terzo confronto): i byte NUL si rifiutano
prima del parsing; le colonne esatte e di provenienza si confrontano senza perdita (testo, oppure
`Decimal` per i numeri senza zeri iniziali, così 5 = 5.0 = 5e0 ma 007 ≠ 7); 10 prove END-TO-END da byte
CSV aggiunte (28 su 28 con l'esito atteso). Il terzo confronto sugli **stessi output rigenerati
conservati** (clone ancora pulito, nessun rilancio) dà lo stesso esito: 5 file byte-identici, 59
colonne uguali (comparatore SHA-256 `43fbd46b…` in `PHASE1_META.json`). Correzione non cieca.

## 4. Che cosa attesta

I valori dei cinque CSV delle figure P1 si rigenerano identici dal codice `120f852` e dagli input P1
distribuiti, nell'ambiente prescritto. Non dice nulla sulla ricostruzione del catalogo P1 dai FITS
(richiede i dati esterni), né sulle altre 107 tabelle, che richiedono fasi proprie con comandi,
riferimenti e budget fissati prima.

# Protocollo P1 — Serie S_BL per regione e per rotazione di Carrington (v8.4)

Stato: **congelato il 2026-11-03**, prima della selezione dei record, dello
scaricamento dei FITS e di qualunque calcolo della serie. Dopo il congelamento
questo file non si modifica: ogni cambiamento di regola richiede un nuovo
protocollo (P1b, P2, …). Lo script che esegue P1 registra lo SHA-256 di questo
file in ogni output.

## 0. Cosa è già stato visto (protocollo non del tutto cieco)

- Il caso di prova di Paolo Romano (2024-05-08 03:12 TAI, 13 HARP), con il
  metodo v8.3 e con quello v8.4: tabella in `output/test_20240508_compare.csv`.
  Su questo caso è stata scelta la bitmap ≥ 33 (§3).
- I metadati SHARP (keyword) di tutte le HARP 2010-05 → 2014-01: posizioni,
  flusso, QUALITY, numero di regioni NOAA. **Nessuna polarità, nessun tilt,
  nessun S_BL** della serie è stato calcolato o guardato.

## 1. Scopo

Produrre, per l'era HMI (2010-05 → ultimo mese disponibile su JSOC):
1. un catalogo con **una misura per HARP** della sorgente Babcock–Leighton;
2. le somme per rotazione di Carrington (CR) e per emisfero.

P1 produce solo la serie. I test del quenching sono in un protocollo
successivo (P2), scritto e congelato prima di guardare la serie.

## 2. Dati

- Serie definitiva `hmi.sharp_cea_720s`, segmenti `Br` e `bitmap`.
- Metadati: le keyword elencate in `python/sharpbl/fetch_metadata.py`, a
  cadenza oraria, per tutte le HARP.
- Raggio solare: `RSUN_REF` dell'header (6,96·10¹⁰ cm).

## 3. Misura su una mappa (metodo `v84`, `python/sharpbl/measure.py`)

- Maschera: `Br` finito, |Br| ≤ 10 000 G, **bitmap ≥ 33** (solo pixel
  interni alla HARP; i codici 1 e 2 sono pixel esterni).
- Soglia: **|Br| ≥ 100 G** per flusso, centroidi e latitudine media.
- Coordinate: longitudine di Carrington e latitudine di ogni pixel dalla WCS
  completa (proiezione CEA obliqua centrata sulla patch).
- Area del pixel: R²·Δφ·Δμ con CDELT in radianti (costante in CEA).
- Φ = Σ|Br| dA sopra soglia; Φ₊ e Φ₋ separati.
- Centroidi delle polarità: media dei vettori unitari pesata con |Br|,
  rinormalizzata.
- Latitudine media λ: centroide sferico di tutti i pixel sopra soglia, pesato
  con |Br|.
- d: distanza di cerchio massimo tra i centroidi, per R.
- Leading: la polarità più a ovest (longitudine di Carrington maggiore).
- Tilt: angolo del vettore leading→following nel piano tangente al punto
  medio, con x verso ovest e y verso nord (convenzione v8.3); sin α > 0 se la
  following è a nord della leading. Tilt ridotto in (−90°, 90°] come nella v8.3.
- Ciclo: vedi §5. Polarità leading attesa (Hale): cicli dispari leading
  positiva a nord, pari negativa a nord. `hale_sign` = +1 se la leading
  osservata coincide con quella attesa, −1 altrimenti.
- **S_BL = hale_sign · Φ · d · cos λ · sin α** (Mx·cm).
- Contributo al dipolo assiale, indipendente da Hale e dal ciclo:
  - D = 3/(4πR²) · Σ Br sin λ dA, su tutti i pixel sopra soglia (G);
  - D_bal = 3/(4πR²) · Φ̄ · (⟨sin λ⟩₊ − ⟨sin λ⟩₋), con Φ̄ = (Φ₊+Φ₋)/2 e medie
    pesate con |Br| (elimina il termine di monopolo dovuto allo sbilancio).
- Codici di qualità e motivi diagnostici come nella v8.3 (`quality_flag`,
  `diagnostic_reason`: ANTI_HALE, LARGE_TILT > 60°).

## 4. Selezione di un record per HARP

Dai metadati orari:
- candidati: `QUALITY == 0` e `USFLUX > 0`;
- **record primario**: il candidato con |LON_FWT| minimo, purché
  |LON_FWT| ≤ 30°; a parità, il più antico;
- **record di controllo**: il candidato con USFLUX massimo tra quelli con
  |LON_FWT| ≤ 60°;
- HARP senza record primario: elencate come `NO_CM_RECORD`, nessun download,
  escluse dalla serie;
- si scaricano `Br` e `bitmap` dei record primario e di controllo (un solo
  record se coincidono).

## 5. Assegnazione del ciclo

- Fuori dalle finestre di sovrapposizione decide la data: ciclo 24 da
  2008-12, ciclo 25 da 2019-12.
- Finestre: **2010-01 → 2011-12** (cicli 23/24) e **2017-01 → 2021-12**
  (cicli 24/25).
- Dentro una finestra decide la **latitudine**, con una regola che non usa
  mai le polarità:
  1. si usano le |LAT_FWT| dei record primari di tutte le HARP della finestra
     (dai metadati);
  2. si divide la finestra in semestri di calendario (gennaio–giugno, luglio–dicembre); un semestre con meno di 15
     HARP viene unito al semestre adiacente con meno HARP, finché ogni gruppo
     ne ha almeno 15;
  3. in ogni gruppo si adatta una mistura di due gaussiane su |lat| (EM,
     partenza: medie 10° e 25°, σ 5°; la componente con media maggiore è il
     ciclo nuovo);
  4. se una componente ha peso < 0,05, o le medie distano meno di 5°, il
     gruppo è considerato di un solo ciclo e si usa la data (stato
     `DATE_IN_WINDOW`);
  5. altrimenti p_new = probabilità a posteriori della componente nuova alla
     |λ| della regione; ciclo nuovo se p_new ≥ 0,5. Stato `AMBIGUOUS` se
     0,2 < p_new < 0,8, `LATITUDE` altrimenti.
- I parametri adattati di ogni gruppo si salvano in
  `CYCLE_BOUNDARY_FITS.csv`.

## 6. Flag per regione (nessuna esclusione automatica oltre §4)

- `valid_bl` (quality_flag = 0);
- `noaa_num` (0 = HARP senza regione NOAA; > 1 = HARP con più regioni NOAA);
- `cycle_state` (DATE, DATE_IN_WINDOW, LATITUDE, AMBIGUOUS);
- |LON_FWT| del record, differenza tra centroidi v84 e LAT/LON_FWTPOS/NEG di
  JSOC (solo controllo, vedi §8).

## 7. Somme per CR ed emisfero

- CR dalla data T_REC del record primario; emisfero dal segno di λ.
- Per ogni CR ed emisfero: numero di regioni, Σ S_BL, Σ D, Σ D_bal, Σ Φ.
- Varianti, tutte riportate:
  - **A**: tutte le regioni con `valid_bl` = 1 (serie principale);
  - **B**: come A, senza le regioni con `cycle_state` = AMBIGUOUS;
  - **C**: come A, solo HARP con esattamente una regione NOAA.
- Incertezza: bootstrap sulle regioni di ogni CR ed emisfero, 2000
  ricampionamenti, seme 20261103; si riportano i percentili 16 e 84.

## 7b. Serie con il metodo di Paolo (v8.3), per confronto

Sugli **stessi record** del §4 si calcola anche il metodo `legacy`
(`measure_legacy`), che riproduce la v8.3 IDL: centroidi e distanze in pixel
con scala unica, latitudine da sin(CRVAL2) + (j − CRPIX2)·Δμ, bitmap ≥ 1,
soglia 100 G, ciclo dalla sola data, R = 6,957·10¹⁰ cm. Si producono le
stesse somme del §7 (variante **L**, analoga ad A) e una tabella di confronto
per regione e per CR: differenza di S_BL, di tilt, di λ, cambi di
`hale_sign` e di validità tra v8.3 e v8.4. La variante L non sostituisce A:
serve a quantificare l'effetto delle correzioni.

## 8. Controlli (si riportano; nessuna regola viene adattata ai risultati)

1. Il metodo `legacy` riproduce il caso di prova di Paolo: 3 anti-Hale
   (11150, 11152, 11192), 4 non valide (11182, 11186, 11187, 11189),
   tilt ridotto di 11152 pari a 74,9° ± 0,1°.
2. Test sintetici (`tests/`) superati.
3. Mediana e 95° percentile di |λ₊ − LAT_FWTPOS|, |λ₋ − LAT_FWTNEG| e delle
   differenze di longitudine. JSOC usa una maschera e pesi diversi, quindi non
   c'è una soglia di accettazione.
4. Rapporto Φ / USFLUX (USFLUX usa pixel e soglie diversi): mediana e
   dispersione.
5. Frazione di HARP con record primario, frazione `valid_bl`, numero di
   regioni per stato di ciclo.

## 9. Output (`results/P1/`)

- `P1_RECORD_SELECTION.csv` — record primario e di controllo di ogni HARP.
- `P1_SBL_CATALOG_BY_HARP.csv` — misure v84 e legacy di ogni record scaricato.
- `P1_LEGACY_VS_V84.csv` — confronto per regione e per CR (§7b).
- `P1_SBL_BY_CR_HEMISPHERE.csv` — somme per CR, emisfero e variante.
- `CYCLE_BOUNDARY_FITS.csv` — parametri della regola di ciclo.
- `P1_CHECKS.csv` — controlli del §8.
- Ogni file riporta la versione del codice (commit git) e lo SHA-256 di
  questo protocollo.

# Pilota MDI — piano del codice e delle prove (BOZZA)

23 novembre 2026 (Claude).
- Accompagna la bozza rev. 3 del protocollo (`docs/PROTOCOL_MDI_TILT_PILOT_DRAFT.md`, `4385692`), limitata a Q1–Q3.
- **Nessun codice scritto, nessun congelamento, nessuna misura, nessuna rete.** Prima viene il controllo finale di
  protocollo e piano.

## 1. Ordine di lavoro e cancelli

| Fase | Cosa | Cancello per passare alla fase successiva |
|---|---|---|
| 0 | Congelamento del protocollo (SHA + record) | revisione finale di Codex |
| 1 | Modulo di misura condiviso + identità con MWO | selftest e prova di identità superati; revisione del codice |
| 2 | Selezione del campione (solo metadati DPD/MWO) | selezione conservata in Git, riconteggio indipendente della selezione |
| 3 | Adattatore sinottico + misura del livello 1 | selftest; revisione del codice; misura; conservazione prima della lettura; riconteggio |
| 4 | Metadati full-disk e acquisizione del livello 2 | **autorizzazione esplicita dell'utente** per rete e budget |
| 5 | Adattatore full-disk + misura del livello 2 | selftest; revisione; misura; conservazione; riconteggio |
| 6 | Analisi descrittive Q1–Q3 + rapporto | riconteggio delle analisi; revisione |

Ogni fase ha:
- uscite in una cartella nuova, scritta in modo atomico e senza sovrascrivere;
- un META con gli SHA di protocollo, script, moduli e input;
- un riconteggio indipendente con ricevuta stretta: conteggi interi non booleani, totale > 0, ogni controllo con
  `ok is True`, partial false solo sul percorso reale, legame al META.

## 2. Moduli e script

### 2.1 `python/sharpbl/tilt_window.py` — modulo di misura condiviso (nuovo)

- `measure_window(lat, lon, br, area, lat_c, lon_c, *, dlat=6, dlon=8, bmin, bmax, min_pix_per_pol=None,
  missing_frac_max=0.05)`.
  - Input: array di pixel già in coordinate eliografiche e campo radiale, con area per pixel.
  - Output: stato, centroidi delle polarità, tilt (P1), polarità leading, separazione, flusso, conteggi e aree per
    polarità, pixel mancanti.
- Funzioni condivise: `sph_centroid`, `tilt_p1` (eventualmente riusando `sharpbl.geometry.tilt_deg`), `joy_gamma`,
  `diff_raw/dir/ax`, `d_gamma(lat_ref)`.
- Non tocca `scripts/t3_mwo_catalogue.py` né la pipeline MWO.

**Prove**
- Dipolo sintetico con tilt noto, in entrambi gli emisferi, per polarità positiva o negativa in testa.
- Finestra a cavallo di L = 0/360.
- Soglie inferiore e superiore; pixel mancanti oltre e sotto il 5 %; polarità sotto il minimo di pixel.
- Differenze angolari: tagli ±90° e ±180°, coppie a cavallo, λ_ref = 0 (d_γ non definito), |λ_ref| < 2°.

**Identità con MWO**, script `scripts/mdi_pilot_mwo_identity.py`:
- ricalcola con il modulo, usando lettore, geometria, soglie (50/4000 G), area e precisione di lettura di MWO:
  - i record del pilota MWO;
  - il sottoinsieme deterministico di R4 (due per epoca × emisfero, NOAA più basso, più tre con `n_blank_window > 0`);
- confronta tilt e γ entro 1e-6°, flusso entro 1e-9 relativo, conteggi esatti;
- legge i FITS MWO già sul disco senza modificarli; ricevuta propria.

### 2.2 `scripts/mdi_pilot_select.py` — selezione (fase 2)

- Popolazione eleggibile dalla lettura DPD di MWO:
  - gruppi 1996-05-01 → 2010-10-31, area ≥ 1, |λ| ≤ 45°, almeno un giorno isolato;
  - giorno con |LCM| minimo fra gli isolati, spareggio sul giorno più precoce; t_DPD;
  - A_main e area; terzili e classi; coorti M1/U ed etichette M0/M2 dal rilascio MWO.
- Estrazione:
  - 18 celle nell'ordine del protocollo, coorte M1 poi U;
  - un solo `default_rng(71 000 001)`; una permutazione per cella × coorte;
  - livello 1: le prime n1; livello 2: le prime n2 della stessa permutazione.
- Uscite:
  - `POPULATION.csv` (con classi, coorte, etichetta);
  - `SAMPLE.csv` (livello, ordine nella permutazione, π₁, π₂, peso);
  - `CELLS.csv` (N_g, n1_g, n2_g, disavanzi, coorti vuote);
  - META.
- Nessun tilt letto: dal rilascio MWO si usano solo le chiavi (NOAA, giorno).

**Prove:** ordine canonico e riproducibilità; coorte vuota; N_g < n; nessun trasferimento; livello 2 ⊂ livello 1 e
indipendente dal successo; π corretti; confini con valori uguali; seme confrontato con gli elenchi effettivi.

**Riconteggio:** `scripts/mdi_pilot_select_recount.py`, con lettura DPD e regole proprie.

### 2.3 `scripts/mdi_synoptic_adapter.py` — adattatore sinottico (fase 3)

- `load_map(cr)`: verifica lo SHA contro l'audit e restituisce dati, header e griglia.
- `pixel_coords(header)`: CT, L e sin λ, con CRVAL2.
- `ct_of_time(t)` = 360·R(t) − 360, con `carrington_continuous_from_date` della pipeline MWO congelata.
- `ct_group(t_dpd, L_dpd)`: N che minimizza la distanza, spareggio sul minore.
- `extract(ct_g, lat_c)`: cucitura CR e CR ± 1, stato «mappa mancante», controllo della banda polar-fill (LAT0).
- Area dei pixel costante; nessuna divisione per μ.

**Prove**
- Sui metadati reali (sola lettura degli header, non tilt): a T_ROT di ogni mappa, |CT(T_ROT) − CARRTIME| entro una
  tolleranza dichiarata.
- LON_FRST/LON_LAST coerenti con la formula.
- Continuità dei bordi: le ultime colonne di CR e le prime di CR+1 hanno CT contigui.
- Mappa sintetica con dipolo a coordinate note, anche a cavallo del bordo.
- CR mancante (1938–1940) e mappa con pixel mancanti.

### 2.4 `scripts/mdi_pilot_measure_l1.py` — misura del livello 1

- Per ogni gruppo di `SAMPLE.csv` (livello 1): estrazione, `measure_window` con 50 G e, come sensibilità, 100 G, minimo
  10 pixel per polarità.
- Registra mappe, IMG_NUM, T_START/T_STOP, T_ROT, CT_g, aree, separazione in pixel e finestre di quiete.
- **Finestre di quiete:** L_DPD ± 30°, esclusione dei gruppi DPD entro ±1 giorno dal passaggio, almeno 50 % di pixel
  finiti, MAD scalata.
- Uscite: `L1_RECORDS.csv`, `L1_QUIET.csv`, META.
- Le uscite si conservano in Git prima di qualsiasi lettura.

**Riconteggio** `scripts/mdi_pilot_l1_recount.py`: coordinate, estrazione e misura con codice proprio
(implementazione indipendente dei centroidi e del tilt), stati e cause, finestre di quiete.

### 2.5 Fase 4 — metadati e acquisizione full-disk (solo dopo autorizzazione)

- `scripts/mdi_fd_metadata.py`: metadati per record dei giorni del livello 2 via HTTP (T_REC, T_OBS, QUALITY, INTERVAL,
  MISSVALS, geometria).
  - Scelta di A e B dai soli metadati, con le regole del protocollo.
  - Elenco deduplicato dei file e piano dei byte.
- `scripts/mdi_fd_fetch.py`: trasporto A1 esistente, con registro di richieste, redirect, tentativi falliti, riprese
  e byte; tetto ≤ 220 file, ≤ 1,5 GB, ≤ 600 richieste; SHA di ogni file; nessuna sovrascrittura.
- **Prove:** su risposte registrate e sintetiche, senza rete. Casi:
  - INTERVAL mancante o diverso;
  - QUALITY ≠ 0;
  - nessun record entro ±6 h;
  - B prima e dopo A;
  - spareggi;
  - deduplicazione;
  - superamento del tetto.

### 2.6 `scripts/mdi_fd_adapter.py` e `scripts/mdi_pilot_measure_l2.py` (fase 5)

- Geometria del full-disk da CRPIX, CDELT, RSUN_OBS, CRLT_OBS, CRLN_OBS e CROTA2.
- B_r = B_LOS/μ, μ ≥ 0,8 su tutta la finestra; pixel mancanti; QUALITY = 0.
- Misura di A e B. Finestre di quiete dello stesso giorno.

**Prove:** full-disk sintetico con geometria nota (B0 ≠ 0, CROTA2 ≠ 0), dipolo noto, finestra al limite di μ;
confronto della geometria con i valori di header reali di uno dei file MDI 2010 già sul disco.

**Riconteggio:** codice proprio di geometria e misura.

### 2.7 `scripts/mdi_pilot_analysis.py` — Q1–Q3 (fase 6)

- Q1:
  - resa per cella × coorte e resa proiettata con 1/π;
  - dispersione osservata;
  - ripetibilità A − B;
  - fit esplorativo di M (procedura comune, dichiarata come dipendenza), con copertura, celle, parametri e bordi.
- Q2 (sinottica − fd(A)) e Q3 (MDI − MWO, solo M1): d_raw, d_dir, d_ax, d_γ, polarità; rapporti di flusso, pixel e
  aree; Δt reale.
- Classi di separazione dai terzili del livello 1 riuscito. Bootstrap a blocchi di 6 CR, 2000 repliche, seme
  71 100 001, con le regole per meno di 10 coppie e meno di 3 blocchi.
- BARD-MDI sulle regioni comuni.

**Riconteggio** indipendente delle statistiche e del bootstrap, ripetendo le stesse estrazioni.

## 3. Prove trasversali

- Tutte le prove sono sintetiche o su soli metadati e header, salvo l'identità con MWO, che rilegge FITS MWO già
  misurati.
- Nessuna prova legge tilt MDI reali prima della misura prevista.
- Ogni script rifiuta di sovrascrivere, verifica lo SHA del protocollo congelato e scrive in modo atomico.
- La suite pytest esistente deve continuare a passare (146 test).

## 4. Stima del lavoro

- Fasi 1–3 (senza rete): modulo, identità, selezione, adattatore sinottico, misura L1 e riconteggi. È la parte più
  consistente, con calcolo di pochi minuti.
- Fasi 4–5: dopo l'autorizzazione; lo scaricamento è stimato in decine di minuti.
- Fase 6: analisi e rapporto.

## 5. Punti per il controllo finale

1. Se il modulo condiviso debba vivere in `python/sharpbl/`, come qui proposto, o in `scripts/`.
2. Implementazione indipendente nei riconteggi: proposta di centroidi e tilt riscritti da zero, non importati dal
   modulo.
3. Tolleranza per la verifica del tempo di Carrington sui metadati reali: proposta 0,05° (mezzo pixel di
   longitudine).

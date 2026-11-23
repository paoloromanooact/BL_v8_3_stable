# Pilota di un catalogo di tilt magnetici MDI 1996–2010 — inventario (sola lettura)

23 novembre 2026 (Claude). Lettura di file locali, nessuna richiesta di rete. Scopo: dire cosa abbiamo, cosa manca e
quali dati servono per progettare il pilota.

Obiettivi del pilota (utente e Codex):
- costruire e verificare un catalogo MDI;
- stimare resa, rumore, copertura e correlazione temporale per un disegno prospettico del catalogo completo;
- confrontare MDI e MWO sugli stessi gruppi e giorni, per attività, dimensione e geometria, come scarto relativo;
- valutare se MDI può sostenere un **nuovo T3**, senza promettere un verdetto.

## 1. Dati disponibili

**Magnetogrammi MDI**
- **Patch SMARP CEA**: solo del 2010, dai due piccoli confronti MDI–HMI.
  - `data/sharp/metadata_inventory_mdi/small_comparison_6d6fd12/` (84 FITS, 12 coppie);
  - `.../second_sample_bbd719c/` (140 FITS, 20 coppie).
  - **Nessun magnetogramma MDI del 1996–2009 è sul disco.**
- **Full-disk `mdi.fd_M_96m_lev182`**:
  - nel progetto SHARP BL solo metadati (schema, conteggi, `RECORDS_fd_min.csv.gz` per gennaio–ottobre 2010);
  - 42 FITS 2010–2011 nel progetto del flusso polare (`/storage/shared/gianluca/MWO_project/…/MDI_HMI_POLAR_FLUX/`),
    fuori dal periodo del pilota.

**Metadati SMARP**
- Per il 1996–2010 esistono solo **conteggi** (`COUNT_LEAVES.csv`): 640 289 record `mdi.smarp_cea_96m`, massimo nel
  2000–2002 (circa 100 000 l'anno), minimo nel 2008–2009 (circa 4 000–5 000). `fd_M`: 81 240 record.
- Tabelle per record (NOAA, posizione, NPIX, USFLUXL, QUALITY) solo per la sovrapposizione del 2010.
  - Il profilo storico congelato prevede solo chiavi minime: per il pilota servirebbe una specifica nuova.

**Cataloghi esterni e posizioni**
- DPD: gDPD 1974–2016, sDPD 1974–2012 (`data/sharp/external_*DPD_20261118`), già usati per MWO.
- **BARD-MDI** (Muñoz-Jaramillo et al. 2021, doi:10.7910/DVN/QEMSZ2):
  - `data/sharp/external/BARD/BARD_1996-2010_MDI_tilts.csv`, 2471 regioni;
  - un catalogo di tilt MDI 1996–2010 **già pubblicato**;
  - non è cieco per questo progetto: il confronto P3 con HMI lo ha già usato.
- **Precedenti:** anche Li & Ulrich (2012) hanno misurato tilt MDI 1996–2010. Un nostro catalogo MDI sarebbe nuovo
  per metodo e controlli, non come primo catalogo di tilt MDI.

**Catalogo MWO nell'epoca MDI** (solo metadati di R4, nessun tilt letto):
- 1822 record isolati (2032 in tutto) fra il 1996-05 e il 2010, tutti in E8, 1773 nel ciclo 23; N 867, S 955.
- Per anno:

  | 1996 | 1997 | 1998 | 1999 | 2000 | 2001 | 2002 | 2003 | 2004 | 2005 | 2006 | 2007 | 2008 | 2009 | 2010 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | 17 | 0 | 67 | 230 | 336 | 343 | 337 | 199 | 141 | 21 | 58 | 31 | 0 | 7 | 35 |

  - Il 1997 e il 2008 sono vuoti; 2005 e 2009 quasi.
  - Il confronto MDI–MWO è quindi possibile soprattutto nel 1999–2004.
  - La bassa attività è poco rappresentata lato MWO (1996, 2006–2007, 2010).
- Terzili di A_main nell'epoca MDI: 1,20 e 2,22. Area DPD mediana: 41 milionesimi (10° percentile 3, 90° 494).

## 2. Accesso a JSOC (stato al 18 novembre, non riverificato oggi)

- **HTTPS diretto a jsoc.stanford.edu:** fallisce con le impostazioni predefinite (`SSLV3_ALERT_HANDSHAKE_FAILURE`;
  diagnosi in `results/MDI_SMARP_ACCESS_DIAGNOSIS`).
- **HTTP semplice:** funziona per i metadati.
- **FITS:** scaricati con un solo redirect verso https://jsoc1 a certificato verificato (emendamento A1).
  - Primo campione: 84/84 file in 135 s. Secondo campione: 140/140 file in 362 s.
- Budget scritti nel codice:
  - inventario: 1000 tentativi e 1 GiB, di cui usati 272 tentativi e 46 MB;
  - downloader: tetti per file e totali.
- **Da riverificare prima di qualsiasi scaricamento**, con un'autorizzazione esplicita.

## 3. Codice riutilizzabile

**Indipendente dallo strumento** (da `scripts/t3_mwo_catalogue.py`, `mwo_pilot_tilt.py`):
- lettura DPD, filtri (area ≥ 1, |λ| ≤ 45°), isolamento;
- ordine dei giorni candidati per |LCM| con il primo successo;
- corpo della misura: finestra ±6°/±8° attorno alla posizione DPD, B_r = B/μ, centroidi pesati sulla sfera, tilt
  nella convenzione di P1, variabile di Joy γ;
- attività e ciclo;
- schema dei riconteggi indipendenti e delle ricevute.

**Specifico di MWO, da sostituire:**
- geometria dagli header (X0/Y0/R0/B0/CENLON) e controlli delle effemeridi;
- lettura degli archivi tar;
- epoche e classi di risoluzione;
- BLANK ed esclusioni A2/A3;
- soglie 50/4000 G, scelte per la risoluzione MWO.

**Codice MDI esistente** (`scripts/mdi_*`, `mdi_overlap_kernels.py`, test in `tests/`):
- costruito per patch SMARP CEA con bitmap, non per finestre su posizioni DPD;
- riutilizzabili:
  - geometria di vista e μ;
  - proxy radiale LOS/μ;
  - lettura FITS con verifica degli hash;
  - trasporto A1 con budget;
  - selezione con riconteggio indipendente.

## 4. Risultati già noti (MDI–HMI, 2010, vicino al minimo)

- **Secondo campione:** 16 coppie su 20 valutabili; mediana d_γ −0,13°, |d_ax| 1,76°.
- **Unione dei due campioni:** n = 20, mediana −0,21°, quattro strati coperti, nessun allarme.
- **Rapporto di flusso MDI/HMI:** mediana 1,26.
- **Due scarti grandi** (+49,6°, +19,5°) in regioni deboli, dove MDI ha 2–9 pixel sopra 100 G. Va fissata prima una
  soglia di flusso o di pixel per polarità.
- **Parametri strumentali noti** (`docs/MDI_SMARP_FEASIBILITY.md`):
  - scala MDI ≈ 1,3–1,4 × HMI;
  - rumore MDI 16–26 Mx cm⁻² contro 6 di HMI;
  - risoluzione circa 4″;
  - cadenza 96 min;
  - buco di SOHO giugno–ottobre 1998 (e periodi successivi nel 1998–1999);
  - prodotto 1 min / 5 min non sempre identificabile (INTERVAL).
- **Limite del confronto del 2010:** è vicino al minimo, quindi non controlla scarti che dipendono dall'attività.

## 5. Cosa manca per il pilota

1. **Scelta del metodo** (da fissare nel protocollo):
   - **(a) finestre su posizioni DPD in magnetogrammi full-disk `fd_M_96m_lev182`.** È lo stesso disegno di MWO:
     popolazione, giorno e misura confrontabili record per record con lo stesso codice.
   - **(b) patch SMARP.** Usano le maschere native, ma la popolazione e la geometria sono diverse da MWO.

   **Proposta: (a)**, con (b) al più come controllo descrittivo.
2. **Dati:** magnetogrammi full-disk MDI dei giorni scelti per il pilota.
   - Ordine di grandezza: qualche centinaio di file, circa 1 GB. Da stimare dai metadati prima di scaricare.
   - Servono i metadati per record di `fd_M` (T_REC, QUALITY, INTERVAL, MISSVALS, geometria) per i giorni candidati.
   - Entrambi richiedono rete e un budget autorizzato.
3. **Lettore MDI full-disk:**
   - geometria da CRPIX/CDELT/RSUN_OBS/CRLT_OBS/CRLN_OBS;
   - pixel mancanti;
   - regola QUALITY;
   - scelta del prodotto (1 min / 5 min).
4. **Soglie MDI fissate prima:**
   - campo minimo: 100 G per il rumore MDI, oppure un valore scalato;
   - tetto;
   - pixel minimi per polarità;
   - flusso minimo.
5. **Chiave di confronto con MWO:** stesso gruppo DPD e stesso giorno UTC, con la differenza di orario dichiarata
   (MDI ogni 96 min; MWO una sessione al giorno).
6. **Disegno del pilota:**
   - strati per anno o fase (bassa e alta attività, entro il ciclo 23), emisfero e terzile di area;
   - numerosità che bilanci il costo dello scaricamento con la stima di resa, rumore, copertura e correlazione
     temporale per il disegno prospettico.
7. **Posizione su BARD-MDI:** confronto solo descrittivo, dichiarato non cieco.
8. **Limite noto:** la bassa attività è scarsa nella sovrapposizione con MWO. Il pilota MDI può coprirla, ma il
   confronto con MWO in quelle fasi avrà pochi record.

## Prossimo passo

Bozza del protocollo del pilota, con il metodo (a) e i punti 3–7, da rivedere con Codex. Nessuna richiesta di rete
prima dell'approvazione e di un'autorizzazione esplicita del budget.

# Pilota del catalogo di tilt magnetici MDI 1996–2010 — protocollo CONGELATO (Q1–Q3)

**CONGELATO il 23 novembre 2026** dopo le revisioni di Codex della rev. 1, della rev. 2 (`020cbda`) e del piano del
codice, con le due correzioni finali recepite: tempo di Carrington (la funzione a periodo medio sceglie solo N;
controllo diagnostico entro 3°; verifica indipendente di N con l'effemeride) e sottoinsieme R4 («fino a tre» record con
BLANK, assenti in R4).
- Testo della bozza rev. 3, conservata in `docs/PROTOCOL_MDI_TILT_PILOT_DRAFT.md`.
- SHA-256 e commit in `docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json`.
- Da questo commit il file non si modifica: ogni cambiamento è un emendamento registrato prima dell'uso.
- Al congelamento nessun tilt MDI è stato misurato e nessun magnetogramma acquisito.
- **Il congelamento non autorizza la rete:** l'acquisizione del livello 2 richiede l'autorizzazione esplicita
  dell'utente. Il codice passa in revisione prima delle misure MDI.
- Il piano del codice è in `docs/MDI_TILT_PILOT_CODE_PLAN.md`.

## 0. Scopo e limiti

Il pilota è **descrittivo e preparatorio**.
- **Q1. Resa, copertura e dispersione osservata,** per strato e coorte MWO, più un fit esplorativo della covarianza
  temporale.
  - Servono a una successiva nota prospettica (Q4); non sono la precisione del catalogo completo.
  - Il §5 elenca ciò che il pilota non può stimare.
- **Q2. Differenza fra prodotti:** tilt da mappe sinottiche contro tilt da magnetogrammi istantanei full-disk, sullo
  stesso gruppo.
  - La differenza comprende composizione temporale, rimappatura, risoluzione ed evoluzione reale; non isola la sola
    composizione sinottica.
  - **Q2 precede la scelta del metodo del catalogo completo.**
- **Q3. Scarto relativo MDI–MWO** sugli stessi gruppi e giorno, per attività, dimensione e geometria.
  - Nessuno dei due strumenti è assunto corretto.
  - Un accordo non dimostrerebbe l'assenza di distorsioni né validerebbe T3.

**Non fa:** non stima β₃, non produce verdetti, non costruisce il catalogo completo, non riapre T3 su MWO.

**Precedenti** da esaminare per metodo e disponibilità dei parametri, senza assumere che popolazione e definizioni
coincidano con quelle DPD:
- **ARISE:**
  - Wang, R., Jiang, J. & Luo, Y. (2023), «Toward a Live Homogeneous Database of Solar Active Regions Based on SOHO/MDI
    and SDO/HMI Synoptic Magnetograms. I. Automatic Detection and Calibration», ApJS 268, 55,
    https://doi.org/10.3847/1538-4365/acef1b;
  - (2024) «II. Parameters for Solar Cycle Variability», ApJ 971, 110, https://doi.org/10.3847/1538-4357/ad5b5f;
  - codice e database: https://github.com/Wang-Ruihui/A-live-homogeneous-database-of-solar-active-regions.
- **BARD-MDI** (Muñoz-Jaramillo et al. 2021): non cieco; confronto solo descrittivo.
- **Li & Ulrich (2012):** tilt MDI 1996–2010.

## 1. Dati

**Livello 1, sinottico (sul disco, senza rete)**
- `mdi.synoptic_Mr_polfil_96m`, 193 mappe, CR 1909–2104; SHA-256 in `results/MDI_SYNOPTIC_AUDIT/FILES.csv`.
- Licenza CC0. Griglia CEA 3600×1440, 0,1° in longitudine di Carrington, passo uniforme in sin λ. Campo radiale in
  Mx cm⁻².
- **Costruzione.**
  - Gli header danno IMG_NUM (numero **globale** di immagini della mappa, 10–447), EQPOINTS 20, W_WEIGHT 'Even',
    HWNWIDTH 20, METHOD 'TEMP_SPAT', T_START/T_STOP, una sola data di costruzione (2018-08-13).
  - Il numero di contributi per pixel non è nei file.
  - Il codice pubblico JSOC `mdisynop.c`, secondo la verifica di Codex, descrive EQPOINTS come contributi equivalenti,
    distingue i modi di esposizione e usa HWNWIDTH come semilarghezza angolare. Non è dimostrato che sia la versione
    che ha prodotto questi file. Le fonti NASA/HMI non descrivono questa serie MDI.
  - **La finestra temporale effettiva per pixel resta indeterminata;** il confronto fra prodotti (Q2) non la richiede.
  - Si conservano riferimento, URL e versione (o hash) delle fonti consultate.
- **Lacune:** mancano le CR 1938–1940; 17 mappe hanno pixel mancanti.
- **Polar filling** (LAT0 60°, LATFIL 75°, LATFIL1 62°): una finestra con |λ| massima ≥ LAT0 della sua mappa fallisce
  («banda polar-fill»). Il controllo si fa per record.

**Livello 2, full-disk** (`mdi.fd_M_96m_lev182`): rete solo dopo autorizzazione esplicita, regole al §4.

**Posizioni e attività**
- gDPD e sDPD come per MWO: stessi file, SHA e lettura, comprese le correzioni dei secondi = 60.
- A_main con lo stesso codice del DESIGN MWO.

**MWO:** tabella isolata del rilascio verificato. È già aperta, quindi Q3 non è cieco rispetto a MWO.

## 2. Popolazione, giorno, classi, coorti

**Popolazione eleggibile:** gruppi DPD 1996-05-01 → 2010-10-31, area corretta ≥ 1 milionesimo, |λ| ≤ 45°, con almeno
un giorno isolato (regola di isolamento MWO).

**Giorno scelto**
- Fra i giorni isolati, quello con |LCM| minimo; spareggio, il giorno UTC più precoce.
- Si sceglie dai soli dati DPD e non cambia se la misura fallisce: il fallimento conta nella resa.
- L'istante DPD di quel giorno è t_DPD (UTC).

**Classi, sulla popolazione eleggibile prima dell'estrazione**
- Terzili di A_main e terzili di area DPD, un valore per gruppo al giorno scelto.
- Quantili lineari NumPy non pesati; classe = `searchsorted(confini, x, side="right") + 1`; confini registrati.

**Coorti MWO per l'allocazione**
- **M1:** record MWO isolato nello stesso giorno scelto.
- **U = M0 ∪ M2:** gli altri gruppi.
- M2 (gruppo in MWO, ma in un altro giorno) e M0 (assente da MWO) restano **etichette informative**. Il confronto MWO
  in giorni diversi è rinviato e non fa parte di questo pilota.

## 3. Campione

**Celle**
- 18 celle, nell'ordine attività 1→3, emisfero N→S, area 1→3. In ogni cella, prima la coorte M1, poi U.
- In ogni cella × coorte le unità sono ordinate per (NOAA, giorno).

**Estrazione**
- Un unico generatore `numpy.random.default_rng(71 000 001)`. Per ogni cella × coorte, nell'ordine sopra, una
  permutazione delle unità.
- **Livello 1:** le prime n1 della permutazione; obiettivo n1 = 15 per M1 e 15 per U.
- **Livello 2:** le prime n2 della stessa permutazione, quindi un sottoinsieme del livello 1 scelto **senza usare il
  successo del livello 1**; obiettivo n2 = 3 per M1 e 2 per U.
- Senza reinserimento.
- Con N_g < n: si prendono tutte le N_g unità e il disavanzo si dichiara. Una coorte vuota ha n = 0 e
  probabilità non definita.
- Nessun trasferimento fra celle o coorti e nessuna sostituzione dopo la misura.

**Probabilità e pesi campionari**
- Per cella × coorte g, con N_g unità:
  - π₁ = n1_g/N_g;
  - π₂ = (n1_g/N_g)·(n2_g/n1_g) = n2_g/N_g.
- Il peso campionario è 1/π del livello pertinente. È distinto dai pesi di flusso della misura.
- Le stime riferite alla popolazione eleggibile (per esempio la resa proiettata) usano questi pesi.
- Le mediane non pesate descrivono il campione bilanciato, non la popolazione.
- Si registrano N_g, n1_g, n2_g, π₁, π₂ e i denominatori di ogni statistica.

## 4. Misura

**Corpo comune: modulo nuovo e condiviso; la catena MWO conservata non si modifica.**
- Finestra |λ − λ_DPD| ≤ 6°, |L − L_DPD| ≤ 8°.
- Centroidi delle due polarità pesati con |B_r| sulla sfera.
- Tilt nella convenzione di P1, in (−180°, 180°]; polarità leading; separazione; flusso; segno di Hale atteso.

**Identità con MWO, prima di qualsiasi misura MDI**
- Il modulo, con le soglie, i criteri sui pixel, la precisione di lettura e l'area originali di MWO (non con il filtro
  MDI di 10 pixel), deve riprodurre:
  - i record del pilota MWO già misurato;
  - un sottoinsieme deterministico di R4: per ogni epoca × emisfero presente, i due record con NOAA più basso, più
    **fino a tre** record con NOAA più basso fra quelli con `n_blank_window > 0`, se presenti.
    - In R4 non ce ne sono: 0 su 11 165 righe del DESIGN. L'assenza si dichiara.
    - Restano obbligatorie le prove sintetiche con pixel mancanti sotto e sopra il 5 %.
- Tolleranze fissate ora: tilt e γ entro 1e-6°, flusso entro 1e-9 relativo, conteggi esatti.
- Nessuna sorgente o prodotto conservato viene modificato.

**Adattatore sinottico (livello 1)**
- **Coordinate:**
  - CT = CRVAL1 + (i + 1 − CRPIX1)·CDELT1;
  - L = (360·CR − CT) mod 360;
  - sin λ = CRVAL2 + (j + 1 − CRPIX2)·CDELT2.
- **Rotazione del gruppo (solo l'intero N).** CT_g = 360·N − L_DPD.
  - **Scelta di N:** R(t) è il numero di rotazione frazionario di `carrington_continuous_from_date` della pipeline MWO
    congelata, una funzione a periodo medio; CT(t) = 360·R(t) − 360. N è l'intero che minimizza |CT_g − CT(t_DPD)|;
    spareggio, N minore.
    - La funzione serve **solo a scegliere N**: l'errore della funzione a periodo medio (fino a 2,66° sugli header)
      non entra nelle coordinate né nei tilt, che dipendono da L_DPD e dalla griglia.
  - **Controllo diagnostico** sui metadati reali: |CT(T_ROT) − CARRTIME| ≤ 3° per ogni mappa.
  - **Verifica indipendente di N tramite effemeridi:** N deve coincidere con `cr_of` (effemeride con termini
    periodici, usata dal catalogo MWO per la rotazione) dell'istante di passaggio al meridiano centrale stimato,
    t_cm = t_DPD + Δ, con Δ = −LCM/13,2° al giorno. Il segno di LCM si verifica nel selftest.
    - In caso di disaccordo la misura non si esegue («N ambiguo») e il caso si conta.
- **Bordi:** estrazione in CT cucendo le mappe CR e CR ± 1. Una parte in una CR mancante fa fallire la misura («mappa
  mancante»).
- **Test indipendente** su passaggi e bordi con mappe adiacenti e metadati reali, oltre a un dipolo sintetico. È un
  controllo di coordinate, non un calcolo di tilt.
- **Campo già radiale:** nessuna divisione per μ.
- **Area dei pixel:** costante, Δlon(rad)·Δ(sin λ)·R☉².
- **Pixel mancanti:** oltre il 5 % della finestra la misura fallisce; altrimenti si escludono.
- Si registrano la mappa o le mappe, IMG_NUM, T_START/T_STOP e T_ROT.

**Adattatore full-disk (livello 2)**
- Geometria da CRPIX1/2, CDELT1/2, RSUN_OBS, CRLT_OBS, CRLN_OBS, CROTA2.
- B_r = B_LOS/μ, con μ ≥ 0,8 su tutta la finestra.
- **Metadati ammissibili:** QUALITY = 0. È un filtro operativo conservativo, non una prova di omogeneità o accuratezza.
  - Le perdite si riportano per anno e per INTERVAL.
  - I valori ammessi non si allargano dopo aver visto i tilt.
- **Immagine A** (riferimento di Q2 e Q3):
  - fra i record ammissibili per i metadati, quello con T_OBS (UTC) più vicino a t_DPD entro ±6 h; spareggio, il più
    precoce;
  - si registrano i record scartati e la causa;
  - se la misura su A fallisce, non si cerca un'altra immagine.
- **Immagine B** (ripetibilità):
  - il primo record ammissibile successivo ad A con INTERVAL **numerico e uguale** a quello di A, entro 4 h;
  - altrimenti il primo precedente con le stesse condizioni;
  - altrimenti «nessuna coppia».
  - INTERVAL mancante non è un modo uguale: A con modo ignoto entra in Q2, con il modo riportato come ignoto, ma non
    forma una coppia di ripetibilità.
- Si riportano Δt reale da T_OBS e INTERVAL di A e B. I limiti di ±6 h e 4 h non garantiscono la contemporaneità con
  MWO o con i contributi della sinottica.
- Ogni full-disk si scarica una sola volta, anche se serve a più gruppi.

**Soglie esplorative, fissate ora**
- Campo: 50 ≤ |B_r| ≤ 4000 G nella principale, 100 G come sensibilità.
  - «Come MWO» non implica equivalenza di rumore o di selezione.
  - I pixel oltre 4000 G si escludono da centroidi e conteggi.
- Almeno **10 pixel per polarità** (solo MDI): filtro minimo di stabilità dei centroidi, non una validazione.
  - Si registrano l'area per polarità (milionesimi di emisfero) e la separazione in unità di pixel della griglia.

## 5. Analisi descrittive

**Differenze angolari (definite ora)**
- d_raw = t₁ − t₂, in (−360°, 360°).
- d_dir = (d_raw + 180) mod 360 − 180: differenza orientata.
- d_ax = (d_raw + 90) mod 180 − 90: differenza assiale.
- Ordine:
  - Q2: sinottica − fd(A);
  - Q3: MDI − MWO (sinottica − MWO e fd(A) − MWO);
  - ripetibilità: A − B.
- **Joy comune:** d_γ = sign(λ_DPD)·d_ax. Se λ_DPD = 0, d_γ non è definito: si riportano d_ax e l'accordo della
  polarità leading, non uno zero.
- I tilt individuali sono conservati invariati.
- Selftest: casi al taglio ±90° e ±180°, coppie a cavallo del taglio, λ_DPD = 0 e |λ_DPD| < 2°.

**Q1**
- **Resa** per cella × coorte, con le cause di fallimento; **resa proiettata** sulla popolazione eleggibile con i pesi
  1/π.
- **Dispersione osservata del campo.**
  - Per ogni misura, due finestre di quiete della stessa forma della finestra di misura, centrate in L_DPD ± 30° alla
    stessa latitudine.
  - Una finestra di quiete si scarta se:
    - contiene, nel suo riquadro allargato di ±6° in latitudine e ±8° in longitudine, il centro di un qualunque gruppo
      DPD:
      - per la sinottica: di qualunque giorno in cui quella longitudine è entro ±1 giorno dal passaggio al meridiano;
      - per il full-disk: dello stesso giorno;
    - oppure, per il full-disk, viola μ ≥ 0,8;
    - oppure ha meno del 50 % di pixel finiti.
  - Statistica: MAD scalata, 1,4826·mediana(|B_r − mediana(B_r)|), sui pixel finiti.
  - Per la misura si riporta la media delle finestre valide, o «non disponibile».
  - È dispersione osservata (campo solare, rumore e processamento), non rumore strumentale.
- **Ripetibilità** (livello 2): d_ax(A − B) con Δt. Comprende evoluzione reale ed errori eventualmente correlati; il
  pilota non li separa.
- **Fit esplorativo di M** (REML AR(1), cella CR × emisfero) sui residui di γ dal modello di Joy per ciclo ed
  emisfero, livello 1.
  - Si riportano copertura temporale, celle, parametri e bordi.
  - È poco informativo per costruzione e non è una misura della correlazione fra rotazioni.
- **Il pilota non stima:** la correlazione temporale con precisione; la separazione fra rumore ed evoluzione; la
  dispersione per pixel delle immagini istantanee a partire dai compositi.

**Q2 e Q3**
- Per ogni confronto: n coppie, mediane di d_ax e d_γ, accordo della polarità leading, rapporti di flusso, pixel e
  aree.
- Q3 riporta anche la distanza temporale reale: T_AVG della sessione MWO contro t_DPD o T_OBS(A); per la sinottica,
  T_ROT e CT_g, perché l'istante per pixel è indeterminato.
- **Classi**, fissate prima di leggere gli scarti:
  - attività e area dal §2;
  - separazione: terzili delle separazioni misurate nel livello 1 sinottico (misure riuscite), applicati identici a
    tutti i confronti.
- **Bootstrap:**
  - blocchi floor((CR − CR_min)/6) sull'insieme delle coppie del confronto, con estrazioni comuni ai due emisferi;
  - 2000 repliche, seme **71 100 001**;
  - percentili al 95 % solo con almeno 1900 repliche valide;
  - si riportano n coppie e n blocchi per gruppo.
  - Con meno di 10 coppie: solo n e mediana. Con meno di 3 blocchi distinti: n e mediana, intervallo «non valutabile».
- **BARD-MDI:** sulle regioni comuni, descrittivo e non cieco.

## 6. Codice, prove, rete, conservazione

**Script previsti:** selezione, adattatore sinottico, adattatore full-disk, modulo di misura condiviso, misura,
riconteggio indipendente.
- I selftest coprono:
  - i casi dei §2–5;
  - l'identità con MWO;
  - coordinate, segni e associazione temporale verificati in modo indipendente.
- La selezione si conserva in Git prima di misurare; gli output prima della lettura; segue il riconteggio con
  ricevuta stretta.

**Rete (solo livello 2, solo dopo autorizzazione)**
- Prima i metadati per record dei giorni candidati, poi i FITS.
- Tetto tecnico proposto: ≤ 220 file, ≤ 1,5 GB, ≤ 600 richieste. Conta metadati, redirect, tentativi falliti, riprese
  e byte ricevuti.
- Il congelamento di questo protocollo **non autorizza** l'acquisizione.

## 7. Q4 rinviato

La precisione prospettica di un nuovo T3 su MDI sarà una **nota separata**, scritta dopo la lettura del pilota e prima
di qualsiasi calcolo prospettico. Dichiarerà quali informazioni del pilota sono già note.

La nota dovrà fissare almeno:
- i livelli numerici di σ²ₓ e κ e la definizione di σ_e;
- la propagazione dell'incertezza sulla resa e il trattamento degli strati senza dati;
- l'assegnazione dei flussi che conservi la relazione con area, latitudine e attività;
- la resa e la disponibilità dei periodi full-disk non inventariati;
- le condizioni di non calcolabilità.

Il congelamento di questo protocollo non autorizza Q4.

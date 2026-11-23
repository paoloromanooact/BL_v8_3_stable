# Pilota del catalogo di tilt magnetici MDI 1996–2010 — protocollo (BOZZA)

**BOZZA rev. 2, 23 novembre 2026 (Claude). Non congelata.**
- Recepisce la revisione di Codex della rev. 1 (`4506cb4`), punti 1–6, semi, budget e ARISE.
- Nessun tilt MDI misurato e nessuna acquisizione di magnetogrammi. Revisione di Codex prima del congelamento e della
  misura.
- Base:
  - inventario `docs/MDI_TILT_PILOT_INVENTORY.md`;
  - audit delle mappe sinottiche `results/MDI_SYNOPTIC_AUDIT` (`511f2dc`).

## 0. Scopo e limiti

Il pilota è **descrittivo e preparatorio**. Le domande:
- **Q1. Resa, copertura e dispersione osservata**, per strato e disponibilità MWO, più un fit esplorativo della
  covarianza temporale.
  - Servono al disegno prospettico del catalogo completo; non ne sono la precisione.
  - Il §5 elenca le componenti che il pilota non può stimare.
- **Q2. Differenza fra prodotti:** tilt da mappe sinottiche contro tilt da magnetogrammi istantanei full-disk, sullo
  stesso gruppo.
  - La differenza comprende composizione temporale, rimappatura, risoluzione ed evoluzione reale. Non isola la sola
    composizione sinottica.
  - **Q2 precede la scelta del metodo del catalogo completo.**
- **Q3. Scarto relativo MDI–MWO** sugli stessi gruppi, per attività, dimensione, geometria e distanza temporale.
  - Nessuno dei due strumenti è assunto corretto.
  - Un accordo non dimostrerebbe l'assenza di distorsioni né validerebbe T3.
- **Q4. Precisione prospettica di un nuovo T3 su MDI da solo**, su un disegno prospettico esplicito (§6).
  - È condizionata a ipotesi e scenari; non è una validazione né una stima di β₃.
  - Sinottico e full-disk sono distinti.

**Non fa:** non stima β₃, non produce verdetti, non costruisce il catalogo completo.

**Precedenti da citare ed esaminare per metodo e disponibilità dei parametri,** senza assumere che popolazione e
definizioni coincidano con quelle DPD:
- **ARISE:** Wang, Jiang & Luo (2023), «Toward a Live Homogeneous Database of Solar Active Regions Based on SOHO/MDI and
  SDO/HMI Synoptic Magnetograms. I. Automatic Detection and Calibration», ApJS 268, 55; e (2024) «II. Parameters for
  Solar Cycle Variability», ApJ 971, 110. Database e codice degli autori. DOI da registrare dalla fonte.
- **BARD-MDI** (Muñoz-Jaramillo et al. 2021): sul disco e non cieco; solo confronto descrittivo dichiarato.
- **Li & Ulrich (2012):** tilt MDI 1996–2010.

## 1. Dati

**Livello 1, sinottico (sul disco, senza rete)**
- `mdi.synoptic_Mr_polfil_96m`, 193 mappe, CR 1909–2104; SHA-256 in `results/MDI_SYNOPTIC_AUDIT/FILES.csv`.
- Licenza CC0. Griglia CEA 3600×1440, 0,1° in longitudine di Carrington, passo uniforme in sin λ. Campo radiale in
  Mx cm⁻².
- **Costruzione: cosa è verificabile e cosa no.**
  - Negli header ci sono IMG_NUM (10–447), EQPOINTS 20, W_WEIGHT 'Even', HWNWIDTH 20, METHOD 'TEMP_SPAT',
    T_START/T_STOP e una sola data di costruzione (2018-08-13).
  - **IMG_NUM è il numero globale di immagini della mappa, non il numero di contributi per pixel.** Quest'ultimo non è
    nei file.
  - Nel codice pubblico JSOC `mdisynop.c`, secondo la verifica di Codex:
    - EQPOINTS riguarda contributi equivalenti;
    - la selezione distingue i modi di esposizione;
    - HWNWIDTH è una semilarghezza angolare.
  - **Non è dimostrato** che quella versione del codice sia quella che ha prodotto i nostri file.
  - La pagina NASA sulle sinottiche descrive HMI a 720 s, non questa serie MDI.
  - **La finestra temporale effettiva per pixel resta indeterminata.** Non si assume «20 immagini × 96 min».
  - Si conservano nel pacchetto del pilota riferimento, URL e versione (o hash) delle fonti consultate.
- **Lacune:** mancano le CR 1938–1940; 17 mappe hanno pixel mancanti.
- **Polar filling:** gli header indicano LAT0 60°, LATFIL 75°, LATFIL1 62°. Una finestra con |λ| massima ≥ LAT0 della
  sua mappa fallisce («banda polar-fill»). Con |λ_DPD| ≤ 45° e ±6° non dovrebbe accadere; lo si verifica per record.

**Livello 2, full-disk** (`mdi.fd_M_96m_lev182`, rete solo dopo autorizzazione esplicita): §3–4.

**Posizioni e attività**
- gDPD e sDPD come per MWO (stessi file e SHA, stessa lettura, comprese le correzioni dei secondi = 60).
- Attività emisferica mensile A_main con lo stesso codice del DESIGN di MWO.

**MWO**
- Tabella isolata del rilascio verificato. È già aperta e nel pacchetto locale, quindi Q3 non è cieco rispetto a MWO e
  lo si dichiara.

## 2. Popolazione, giorno, classi

**Popolazione eleggibile:** gruppi DPD 1996-05-01 → 2010-10-31, area corretta ≥ 1 milionesimo, |λ| ≤ 45°, con almeno
un giorno isolato (regola di isolamento di MWO).

**Giorno scelto (univoco, senza riguardo al tilt).**
- Fra i giorni isolati del gruppo, quello con |LCM| minimo. Spareggio: il giorno UTC più precoce.
- Il giorno si sceglie dai soli dati DPD e **non cambia** se la misura in quel giorno fallisce: il fallimento conta
  nella resa. Non c'è ricerca di un giorno alternativo.
- L'istante DPD del giorno scelto è t_DPD (UTC).

**Classi fissate prima dell'estrazione,** sulla popolazione eleggibile, un valore per gruppo al giorno scelto:
- attività: terzili di A_main;
- area DPD: terzili.

Regole:
- quantili lineari NumPy non pesati;
- classe = `searchsorted(confini, x, side="right") + 1`;
- confini registrati.
- I confini 1,20 e 2,22 della rev. 1 venivano dal campione MWO e sono sostituiti da questi.

**Disponibilità MWO,** tre stati distinti e registrati:
- **M1:** record MWO isolato nello **stesso giorno scelto**;
- **M2:** gruppo presente nel catalogo MWO isolato, ma in un altro giorno;
- **M0:** gruppo assente dal catalogo MWO isolato.

## 3. Campione

**Strati:** attività (3) × emisfero (2) × area (3), 18 in tutto. In ogni strato le unità sono ordinate canonicamente
per (NOAA, giorno).

**Estrazione**
- Per strato e disponibilità: permutazione con `numpy.random.default_rng(71 000 001)` in un ordine fisso degli strati.
  Codex ha verificato il seme: nessuna collisione con la griglia MWO, con USED, con S1, Joy e la diagnosi S2.
- Si prendono i primi k **senza reinserimento**.
- Disponibilità insufficiente: si prendono tutte le unità disponibili e il disavanzo si dichiara. **Nessun
  trasferimento** fra strati o classi e **nessuna sostituzione** dopo la misura.

**Livello 1: obiettivo 30 per strato** (540), esplorativo e senza garanzia di precisione.
- 15 dalla classe M1, 15 da M0 ∪ M2.
- Un gruppo in una CR mancante resta nel campione e fallisce come «mappa mancante».

**Livello 2: obiettivo 5 per strato** (90).
- Estratti dal campione del livello 1 dello stesso strato: 3 dalla classe M1 e 2 da M0 ∪ M2.
- Così Q2 non dipende soltanto dagli anni con MWO (1999–2004).

**Registrazioni per strato × disponibilità:**
- popolazione N;
- estratti n;
- probabilità di selezione n/N, per livello;
- denominatori;
- cause di fallimento.

**Proiezioni:**
- Le stime di resa per la popolazione completa pesano ogni gruppo con N/n del suo strato e della sua disponibilità.
  Questo corregge il sovracampionamento di M1.
- Q3 usa solo M1 (stesso giorno); M2 dà un confronto secondario con la distanza temporale riportata.

## 4. Misura

**Corpo comune**
- Finestra |λ − λ_DPD| ≤ 6°, |L − L_DPD| ≤ 8°.
- Centroidi delle due polarità pesati con |B_r| sulla sfera.
- Tilt nella convenzione di P1, in (−180°, 180°]; polarità leading; separazione; flusso; segno di Hale atteso.
- È un **modulo nuovo e condiviso**. La catena MWO conservata non si modifica.
- L'identità con il calcolo MWO si dimostra su dati già disponibili: si ricalcolano con il nuovo modulo i record del
  pilota MWO e un sottoinsieme di R4 dai FITS MWO, e si confrontano con i valori conservati entro tolleranze dichiarate.

**Adattatore sinottico (livello 1)**
- **Coordinate.**
  - CT = CRVAL1 + (i + 1 − CRPIX1)·CDELT1 (tempo di Carrington), L = (360·CR − CT) mod 360;
  - sin λ = (j + 1 − CRPIX2)·CDELT2.
  - Segni verificati nel selftest con LON_FRST/LON_LAST e con una mappa sintetica a dipolo noto.
- **Tempo di Carrington del gruppo:** CT_g = 360·N − L_DPD, con N intero tale che CT_g sia il più vicino al tempo di
  Carrington di t_DPD.
- **Bordi:** la finestra si estrae in CT cucendo le mappe CR e CR ± 1. Se una parte cade in una CR mancante, la misura
  fallisce («mappa mancante»).
- **Campo già radiale:** nessuna divisione per μ, nessuna soglia μ.
- **Area dei pixel:** costante, Δlon(rad)·Δ(sin λ)·R☉².
- **Pixel mancanti:** oltre il 5 % della finestra la misura fallisce; altrimenti i pixel mancanti si escludono.
- Si registrano la mappa o le mappe usate, IMG_NUM e T_START/T_STOP.

**Adattatore full-disk (livello 2)**
- Geometria da CRPIX1/2, CDELT1/2, RSUN_OBS, CRLT_OBS, CRLN_OBS, CROTA2.
- B_r = B_LOS/μ, con μ ≥ 0,8 su tutta la finestra.
- **QUALITY ammesso: solo 0.** Qualsiasi altro valore fallisce («qualità») e il valore si registra.
- Pixel mancanti: la stessa regola del 5 %.
- **Immagine di riferimento A** (per Q2 e Q3):
  - il record con T_OBS (UTC) più vicino a t_DPD, entro ±6 h;
  - spareggio: il più precoce;
  - nessun record entro ±6 h: «nessun magnetogramma», senza ricerca in altri giorni.
- **Immagine B** (ripetibilità):
  - il primo record successivo ad A con QUALITY 0 e **lo stesso INTERVAL** (modo di esposizione) di A, entro 4 h;
  - altrimenti il primo precedente con le stesse condizioni;
  - altrimenti «nessuna coppia».
  - Si riportano Δt effettivo da T_OBS e INTERVAL di entrambe.
  - Due record consecutivi non garantiscono 96 minuti.
- I modi di esposizione non si mescolano nella coppia. In Q2 la classe di INTERVAL di A è riportata.

**Soglie esplorative (fissate ora)**
- **Campo:** 50 ≤ |B_r| ≤ 4000 G nella principale; 100 G come sensibilità.
  - «Come MWO» non implica equivalenza di rumore o di selezione, e lo si dichiara.
  - I pixel oltre 4000 G si escludono da centroidi e conteggi.
- **Almeno 10 pixel per polarità.**
  - È un filtro minimo di stabilità dei centroidi, non una validazione del tilt.
  - Non rappresenta la stessa area né lo stesso numero di elementi indipendenti nelle due griglie: si registrano anche
    l'area per polarità (in milionesimi di emisfero) e la separazione in unità di pixel di ciascuna griglia.

**Differenze angolari (Q2, Q3), definite ora**
- Si conservano per ogni coppia:
  - **differenza grezza** dei tilt t₁ − t₂ in (−180°, 180°];
  - **differenza assiale** d_ax = axial(t₁ − t₂) in [−90°, 90°);
  - **accordo della polarità leading.**
- **Convenzione di Joy comune:** latitudine di riferimento λ_ref = λ_DPD per entrambe le misure.
  - γᵢ = sign(λ_ref)·asin(sin tᵢ);
  - d_γ = sign(λ_ref)·d_ax.
  - Non si sottraggono γ calcolate con latitudini diverse.
- **Selftest:** casi al taglio ±90°, coppie a cavallo del taglio, regioni con |λ_ref| < 2°.

## 5. Analisi descrittive

**Q1**
- **Resa** per strato × disponibilità, con cause di fallimento, e resa proiettata con pesi N/n.
- **Dispersione osservata del campo** in finestre di quiete a bassa latitudine.
  - Comprende campo solare, rumore e processamento: non è identificata con il rumore strumentale.
- **Ripetibilità** (livello 2): differenza assiale fra A e B, con Δt.
  - Comprende evoluzione reale ed errori eventualmente correlati; il pilota non li separa.
- **Fit esplorativo di M** (REML AR(1), cella CR × emisfero) sui residui di γ dal modello di Joy per ciclo ed
  emisfero, livello 1.
  - Si riportano copertura temporale, numero di celle, parametri e bordi del dominio.
  - **Non è una misura affidabile della correlazione fra rotazioni,** e la sola stima puntuale di φ non si usa in Q4.
- **Il pilota non può stimare:**
  - la correlazione temporale con precisione;
  - la separazione fra rumore ed evoluzione;
  - la dispersione per pixel delle immagini istantanee a partire dai compositi.

  Q4 tratta queste componenti con scenari.

**Q2** (livello 2): d_ax, d_γ e polarità per A contro sinottica.
- Mediana con intervallo bootstrap a blocchi di 6 CR, complessiva e per classe di attività, area, separazione e
  disponibilità MWO.
- Rapporti di flusso, pixel e aree.

**Q3:** syn − MWO (livello 1, M1) e fd(A) − MWO (livello 2, M1).
- Le stesse statistiche, più la distanza temporale reale fra le misure. Per MWO: T_AVG della sessione; per la
  sinottica: T_ROT e il CT del gruppo, perché l'istante effettivo per pixel è indeterminato.
- M2: secondario, per classi di distanza temporale.

**BARD-MDI:** sulle regioni comuni, descrittivo e non cieco.

**Bootstrap:** blocchi floor((CR − CR_min)/6) sul campione, 2000 repliche, seme **71 100 001** (da verificare come gli
altri). Percentili solo con almeno 1900 repliche valide; gruppi con meno di 10 coppie solo con n e mediana.

## 6. Q4 — disegno prospettico

Per ciascun metodo (sinottico e full-disk, separati), si costruisce il disegno prospettico del catalogo completo sulla
**popolazione eleggibile reale** del 1996–2010. Si conservano:
- distribuzione per CR ed emisfero;
- attività A, latitudine, area;
- lacune: CR mancanti per il sinottico; per il full-disk la disponibilità non è nota senza metadati e si tratta come
  scenario.

**Resa.** Ogni gruppo eleggibile riceve la probabilità di successo del suo strato × disponibilità stimata dal pilota.
- Si generano **R = 1000 disegni** con estrazioni di Bernoulli (seme **71 200 001**).
- Gli strati con meno di 5 tentativi usano la resa del livello di attività, con flag. La regola è fissata ora.

**Pesi.** Per i record simulati, i pesi Φ si estraggono dalla distribuzione dei flussi misurati nel pilota per
strato. Le alternative a pesi uguali e ad area DPD sono sensibilità.

**Matrice.** La stessa del protocollo T3: cicli × emisferi, eventuali termini di epoca (nessuno per MDI salvo
decisione contraria), riduzione a rango pieno.
- I bersagli delle rampe del 10 % e del 20 % (Δβ = g·Δγ) si proiettano sulla matrice MDI prevista, non si copiano da
  MWO.
- Un disegno non identificabile si conta e si riporta.

**Covarianza: scenari, non stime.**
- Griglia: φ ∈ {0; 0,5; 0,9; 0,98}, σ²ₓ ∈ tre livelli, σ_e da Q1 (dispersione residua) ± 50 %.
- I parametri del fit esplorativo di Q1 sono un punto della griglia, non il riferimento.

**Uscita:** SE prospettico di β₃ e potenza nominale per le rampe, in distribuzione sui disegni e per scenario.
- La precisione del catalogo sinottico non determina quella del full-disk.
- Nessun β₃ osservato.

## 7. Codice, prove, rete, conservazione

**Script previsti:** selezione, adattatore sinottico, adattatore full-disk, modulo di misura condiviso, misura,
riconteggio indipendente, Q4.
- I selftest coprono i casi dei §2–6, l'identità con MWO e la verifica indipendente di coordinate, segni e
  associazione temporale.
- La selezione si conserva in Git prima di misurare; gli output prima della lettura; segue il riconteggio con
  ricevuta stretta.

**Rete (solo livello 2, solo dopo autorizzazione)**
- Prima i metadati per record dei giorni candidati, poi i FITS.
- Il budget preliminare (≤ 220 file, ≤ 1,5 GB, ≤ 600 richieste) conta:
  - richieste di metadati, redirect, tentativi falliti, riprese;
  - byte effettivamente ricevuti.
- I full-disk condivisi da più gruppi si scaricano una volta sola.
- **Questa bozza non autorizza alcuna acquisizione.**

## 8. Questioni per la revisione

1. Le ripartizioni 15/15 e 3/2 fra M1 e le altre classi.
2. La finestra ±6 h e i 4 h per la coppia full-disk.
3. La griglia di scenari di Q4 e il numero di disegni R.
4. I semi 71 100 001 e 71 200 001.
5. Se il confronto di identità con MWO debba usare anche un sottoinsieme di R4 ricalcolato dai FITS: richiede la
   lettura degli archivi MWO, già sul disco.

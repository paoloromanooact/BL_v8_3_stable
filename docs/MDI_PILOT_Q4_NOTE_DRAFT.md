# Pilota MDI — nota prospettica Q4: precisione attesa di T3 con un catalogo MDI 1996–2010

**BOZZA, revisione 3.1, 24 novembre 2026 (Claude). Non congelata, da rivedere con Codex.** È la nota prevista dal
protocollo congelato del pilota (`docs/PROTOCOL_MDI_TILT_PILOT.md` §7): si scrive dopo la lettura del pilota e
**prima di qualsiasi calcolo prospettico**. Per scriverla:
- nessun calcolo prospettico;
- nessuna simulazione;
- nessun dato nuovo.

La revisione 2 ha recepito la revisione di Codex della revisione 1 e il suo riscontro al piano di correzione
(`MDI_Q4_NOTA_BOZZA_REVISIONE_CODEX.txt`, `MDI_Q4_NOTA_RISPOSTA_REVISIONE_CODEX.txt`). La revisione 3 recepisce la
revisione della revisione 2 (`MDI_Q4_NOTA_REVISIONE2_REVISIONE_CODEX.txt`). Le modifiche sono elencate al §12.
Usa i **conteggi preparatori** non ciechi del §1.3, con regole fissate prima di contare. I numeri citati sono
risultati già conservati. Il congelamento di questa nota non autorizza i calcoli: l'avvio resta una decisione
dell'utente.

## 0. Obiettivo servito e decisione

- **Obiettivo servito:** il secondo del progetto, il quenching del tilt con l'attività (T3).
- **Decisione che informa:**
  - se costruire il catalogo MDI completo 1996–2010 per T3;
  - con quale prodotto (sinottico o full-disk).
- **Cosa aggiunge rispetto alla fase A del piano prospettico** (`docs/PROSPECTIVE_PHASE_A_RESULTS.md`). Lì MDI (E2)
  era un disegno sintetico: celle HMI ricampionate con l'attività del 1996–2010, resa f e rumore k come griglie
  esplorative. Qui il disegno è quello reale:
  - i gruppi DPD eleggibili del pilota, con i filtri del §3.1;
  - con le rese misurate per prodotto, ricostruite nelle celle della selezione;
  - con i flussi MDI misurati;
  - con scenari di errore di misura scelti come scale, non come stime.
- Il full-disk (MF) è in tutta la nota una **proiezione indicativa**: la sua resa viene da 90 gruppi, 2 o 3 per cella.
- **Non serve all'obiettivo 1** (sorgente BL). La differenza di scala del flusso con MWO resta aperta e richiede una
  specifica propria. Q4 usa i flussi MDI solo come pesi della regressione T3.

## 1. Informazioni già note (nota non cieca)

### 1.1 Risultati e studi prospettici

**Risultati T3:**
- HMI: −3,59° per unità di attività, intervallo nominale 97,5 % [−10,58°, +3,41°], non deciso.
- MWO 1974–2012: −4,93° [−10,21°, +0,34°], descrittivo (S1 non determinato, S2 «stabilità non determinata»).

**Studi prospettici già fatti:**
- **Fase A e B del piano prospettico:**
  - bersaglio T3 dello scenario prescritto su E0 −1,602647° per unità di attività (−0,0668·γ₀);
  - riconoscimento T3 dal 2,3 % al 4,35 %, anche con MDI sintetico;
  - alla scala P2f, il 66–83 % della varianza della pendenza viene dalla componente temporale.
- **Fattibilità DPD** (`docs/T3_LONG_CATALOGUE_FEASIBILITY_DRAFT.md` §8):
  - semilarghezza dell'intervallo nominale alla scala P2f 0,43–0,60·γ₀ per HMI E0;
  - 0,27–0,37·γ₀ per DPD 1996–2016 (0,36–0,44 con dispersione individuale 25°).

### 1.2 Pilota

**Livello 1 (sinottiche):**
- resa proiettata 92,8 % a 50 G, 81,7 % a 100 G;
- fallimenti: 12 finestre con pixel mancanti, 8 mappe mancanti (tutte nel 1998, CR 1938–1940), 12 per polarità;
- Q3 sinottica − MWO: mediana |d_ax| 8,5°, d_γ per terzile di attività non monotono;
- flusso MDI/MWO circa 14;
- fit esplorativo di M: φ = 0,29, κ = −0,98 al bordo, σ²ₓ = 16,7, dichiarato poco informativo.

**Livello 2 (full-disk, regola A1, immagine A):**
- resa campionaria 61/90; proiettata 47,0 % (M1 94,7 %, U 30,4 %);
- 20/90 gruppi fuori dominio μ, 9/90 senza magnetogramma;
- Q2 sinottica − full-disk: d_γ −0,6° (−1,0° a 100 G) con intervalli nominali che escludono zero, mediana |d_ax| 1,4°;
- per terzile di attività, d_γ −0,53 / −0,79 / −1,19° a 50 G (descrittivo, intervalli che contengono zero);
- A − B: mediana |d_ax| 0,7° a 1,6–3,2 h;
- fd − MWO e sinottica − MWO sugli stessi 49 gruppi: 6,8° e 7,1°.

**Letteratura:** deviazione standard dei tilt 29–31° in tutti i cicli ed emisferi (McClintock & Norton 2013, verificato
in lettura primaria il 18 novembre). È la dispersione **totale osservata**, che comprende errore di misura e
variazione temporale: non è σ_int (§5).

### 1.3 Conteggi preparatori (non ciechi)

Regole fissate prima di contare in `docs/MDI_Q4_PREP_COUNTS_RULES.md` (SHA-256 `9ce409fc…`); script
`scripts/mdi_q4_prep_counts.py`; output `results/MDI_Q4_PREP_COUNTS/`. Nessun tilt letto (colonne lette dichiarate in
META.json); 21 riscontri su 21 superati.
- **Classi di attività e area della selezione** (C1): ricostruite senza discordanze dai terzili di A_main e dell'area
  DPD in `results/MDI_PILOT_SELECTION/META.json` (`edges.A_main` = 0,8168, 1,7158; `edges.area` = 3, 18 msh).
  `CLASS_EDGES.json` dell'analisi L1 contiene solo i confini della separazione e non si usa per l'attività.
- **Mappe** (C2): mappe mancanti nell'inventario = {1938, 1939, 1940}. La regola delle mappe richieste del pilota
  (CT_g ± 8°) riproduce i 530 record L1: N e N_ephemeris uguali, mappe richieste = mappe registrate per gli 8
  `map_missing`, nessun record riuscito con una mappa mancante. Popolazione: 127 gruppi con mappe richieste mancanti,
  2 con N ≠ N_ephemeris.
- **Filtri** (C3): 5401 gruppi; −117 per data > 2010-04-30; −4 per CR(t_DPD) ≥ 2096 → **MF 5280**; −127 mappe
  mancanti, −2 N ambiguo → **MS 5151**. Estremi MF: 1996-05-07 (CR 1909) → 2010-04-20 (CR 2095). 218 gruppi hanno
  t_DPD in [1998-06-01, 1998-11-01).
- **Cicli × emisfero** (C4, gruppi della popolazione, resa non applicata):

  | Ciclo | MS N | MS S | MF N | MF S |
  |---|---|---|---|---|
  | 22 | 20 | 13 | 20 | 13 |
  | 23 | 2268 | 2687 | 2344 | 2740 |
  | 24 | 80 | 83 | 80 | 83 |

  MDI da solo è quindi in sostanza una misura sul ciclo 23 (96 % dei gruppi).
- **Rese** (C5): la proiezione deterministica r/n con le numerosità N delle celle riproduce tutte le rese proiettate
  pubblicate (22 righe L1, 24 righe L2 A1 immagine A; differenza relativa massima 3,7e-16), con somme, pesi N/n = 1/π e
  abbinamenti verificati.
- **Celle** (C6): MS, dopo aver tolto le 8 unità con mappe mancanti (nessuna riuscita), ha n ≥ 6 in tutte le 36
  celle. MF ha n2 = 2 o 3 in **tutte** le 36 celle (7 celle con 0 successi, 15 con tutti riusciti); per coorte,
  senza il filtro 4 del §3.1: M1 49/54 (n efficace di Kish 29,1), U 12/36 (32,1).
- **Donatori di flusso e latitudine** (C7, 50 G; bersagli = i 5151 gruppi di MS, non quelli di MF):
  - classi di |lat|: terzili **globali** della popolazione MS filtrata (11,46°, 19,23°), incrociati con la cella di
    selezione dei donatori. Solo il 58,6 % dei bersagli ha almeno 5 donatori nella propria cella × classe (soglia
    fissata 90 %: L-T non adottata);
  - 5 donatori più vicini in |lat| nella cella: ogni cella ha almeno 5 donatori, ma il 90° percentile della distanza
    massima è 10,3° (mediana 4,9°; soglia fissata 5°: L-NN non adottata);
  - a 100 G: 48,0 %, 12,3°, 5,5°;
  - le due regole candidate non soddisfano i criteri fissati con questi donatori: serve l'emendamento A2 (§3.5).
- **Limiti dei conteggi:** i 21 riscontri sono controlli di coerenza, non validazioni scientifiche. Lo script
  preparatorio stampa i riscontri falliti ma termina senza errore; non si modifica, perché il suo SHA è registrato
  negli output. Se fosse riusato come gate, dovrebbe uscire con codice non nullo.

## 2. Domanda

Con gli stimatori già studiati, e sotto ipotesi dichiarate sul rumore, sulla resa e sugli scarti, quale precisione
attesa avrebbe la pendenza β₃ di T3 misurata con la procedura del pilota sui gruppi DPD 1996–2010:
- da sola;
- insieme al campione HMI di T3;
- per ciascuno dei due prodotti MDI?

Lo stimatore è la pendenza WLS di T3 sui record, nel riferimento normale a varianza nota.
- **Che cosa è analitico:** la varianza di β̂, condizionata al disegno.
- **Che cosa è casuale:** il disegno stesso. Inclusione dei gruppi, rese per strato e flussi sono estratti in 20
  realizzazioni. Mediana, minimo e massimo sulle realizzazioni descrivono la variabilità del disegno sotto le ipotesi;
  non sono un intervallo calibrato dell'incertezza sul progetto.
- La valutazione non valida la procedura M sui disegni MDI e non dice quanto il Sole renderebbe osservabile.

## 3. Disegni

### 3.1 Popolazione, filtri e record

**Base comune:** la popolazione eleggibile del pilota (`results/MDI_PILOT_SELECTION/POPULATION.csv`, 5401 gruppi).
Ogni gruppo ha un solo record, al giorno scelto dal pilota.

**Filtri, contati separatamente e in quest'ordine** (C3):
1. data di t_DPD ≤ 2010-04-30;
2. CR(t_DPD) < 2096, con CR(t) = max{c : cr_start(c) ≤ t} e `cr_start` (Meeus) della fase A;
3. solo MS: mappe richieste disgiunte da {1938, 1939, 1940}, con la regola del pilota (C2); gruppi con
   N ≠ N_ephemeris esclusi;
4. solo MF: t_DPD fuori da [1998-06-01, 1998-11-01), convenzione E2_GAP già usata per MDI nella fase A (perdita
   di SOHO). È una convenzione per uno scenario indicativo, non un inventario né una disponibilità misurata: i due
   gruppi di livello 2 del pilota in quell'intervallo (8266m del 1998-07-12 e 8350 del 1998-10-08) non hanno
   magnetogramma, ma due casi non dimostrano l'assenza di immagini in tutto l'intervallo.

**Disegni risultanti:** MS 5151 gruppi, MF 5280 − 218 = 5062 gruppi (i 218 del filtro 4 sono tutti nei filtri 1–2,
C3). Per coorte, N originarie M1 1396, U 4005; N di MF dopo i filtri M1 1338, U 3724. Il codice registra le N
originarie e filtrate per cella, per MS e per MF. I due disegni MDI non
dipendono dalla presenza di H. Il periodo MDI finisce a CR 2095; H comincia a CR 2096 (emendamento A1 della fase A):
fra i due non c'è lacuna di rotazioni.

**Grandezze di ogni record MDI:**
- emisfero dalla colonna `hemisphere` della popolazione; sin|λ| dalla latitudine DPD;
- attività A: SILSO emisferica mensile normalizzata alla media HMI 2010-05 → 2026-09 (`run_p2.load_silso`, chiave
  `monthly`), nel mese di t_DPD. È la stessa regola dei record HMI di E0 (`add_activity`, mese del record);
- CR = CR(t_DPD); t_years = `years(cr_start(CR))` e ciclo = `cycle_of_time(cr_start(CR))` della fase A
  (minimi m₂₃ = 1996-08, m₂₄ = 2008-12), come per gli slot MDI della fase A;
- nessuna separazione dei cicli per latitudine, approssimazione dichiarata come in T3 su MWO.

**Sensibilità di attività:** A_main del pilota (aree DPD, normalizzazione MWO 1974–2012), **solo per MDI da solo**.
Nei disegni combinati non si mescola con l'indice SILSO di H.

**Classi di attività degli strati.** Le classi `act_class` delle rese e dei flussi sono i terzili di A_main della
selezione (C1). Sono distinte dall'attività SILSO della regressione e non si ricalcolano sulla popolazione filtrata.

| Codice | Disegno | Resa | Pesi Φ |
|---|---|---|---|
| H | HMI E0, il campione S di T3 (2485 record, CR 2096–2316) | — | flussi P1 |
| MS | MDI sinottico, filtri 1–3 | per cella di selezione (§3.2) | donatori L1 (§3.5) |
| MF | MDI full-disk con la geometria congelata, filtri 1, 2, 4 | per pool di coorte (§3.3) | come MS (§3.5) |
| MS+H | MS ∪ H | come sopra | come sopra |
| MF+H | MF ∪ H | come sopra | come sopra |

### 3.2 Resa MS

- **Strati:** le 36 celle di selezione attività × emisfero × area × coorte.
- **Conteggi:** n e successi `ok` (50 G; `ok100` per la soglia di sensibilità) delle unità L1 della cella, tolte le
  unità con mappe richieste mancanti (8 in tutto, nessuna riuscita). Tutte le celle hanno n ≥ 6: nessun pool.
- **Modello:** per realizzazione, p_c ~ Beta(r_c + ½, n_c − r_c + ½), indipendente per cella. Un gruppo di MS nella
  cella c entra nel disegno se U_g < p_c (§3.6).
- La Beta introduce uno smoothing dichiarato: la sua media (r + ½)/(n + 1) non è r/n. Il codice riporta la resa
  attesa del disegno con e senza smoothing e filtri, separatamente dalla riproduzione deterministica (§6).

### 3.3 Resa MF (proiezione indicativa)

- **Conteggi:** successi della regola A1, immagine A, da `L2_RECORDS.csv`. Le 2 unità di livello 2 del filtro 4
  (8266m M1, 8350 U, entrambe senza magnetogramma) si tolgono da n e da r.
- **Pesi:** w = 1/π₂ = N_c^orig / n2_c^orig della selezione originaria, conservati dopo la restrizione del dominio e
  sommati sulle sole unità ammissibili. n2_c^orig non si sostituisce con il conteggio dopo il filtro.
- **Due letture fissate ora e presentate sempre insieme:**
  - **principale, pool per coorte.** Scelta per parsimonia (2 o 3 unità per cella) e per il contrasto già osservato
    fra le coorti, assumendo omogeneità della resa dentro ciascuna coorte. Non è l'unica dimensione rilevante: il
    rapporto L2 mostra anche rese proiettate per area di 29,8 / 35,1 / 75,1 %, sintesi descrittive correlate e non
    una graduatoria di fattori. Dimensioni perse: attività, emisfero, area;
  - **affiancata, pool coorte × attività:** tocca direttamente la distribuzione della leva di x₃.
  - Ulteriore sensibilità: pool coorte × area.
- **Stima del pool:** p̂ = Σ w·ok / Σ w sulle unità ammissibili del pool. È una stima a rapporto nel dominio filtrato,
  non un totale di Horvitz–Thompson né il rapporto esatto della popolazione filtrata. Valori dopo il filtro 4 (già
  noti, non ciechi):

  | Pool | ok/n | p̂ | n_eff (Kish) |
  |---|---|---|---|
  | M1 | 49/53 | 0,9541 | 28,72 |
  | U | 12/35 | 0,3087 | 31,37 |
  | M1 × attività 1 / 2 / 3 | 16/17, 16/18, 17/18 | 0,953 / 0,910 / 0,983 | 11,1 / 11,7 / 11,3 |
  | U × attività 1 / 2 / 3 | 5/11, 5/12, 2/12 | 0,356 / 0,393 / 0,143 | 10,1 / 11,1 / 11,0 |

  Non coincidono con il 94,7 / 30,4 % del rapporto L2, che resta il riferimento storico senza filtri.
- **Modello d'incertezza:** n_eff = (Σw)²/Σw² (Kish), r_eff = p̂·n_eff; per realizzazione
  p_pool ~ Beta(r_eff + ½, n_eff − r_eff + ½), **una sola estrazione per pool**, condivisa da tutte le celle del pool.
  - È un **modello approssimato scelto per la proiezione indicativa**, non la distribuzione a posteriori esatta per
    un campionamento stratificato senza reinserimento.
  - Kish descrive la disuguaglianza dei pesi, ma non garantisce che tutta la varianza della resa sia rappresentata.
    Non incorpora la struttura per celle, le frazioni campionarie né le differenze di successo fra celle.
  - La propagazione dell'incertezza sulla resa MF è quindi condizionata a questa scelta e non è verificata rispetto
    al disegno campionario. Q4 non potrà concludere nulla che dipenda da una rappresentazione esatta di questa
    incertezza.
- **Disponibilità dei magnetogrammi.** Il «nessun magnetogramma» (7/88 fuori dal filtro 4) è un'ipotesi sulla
  popolazione, già inclusa nella resa del pool; si riporta accanto la stima pesata corrispondente.
  - Sensibilità **deterministiche**, non stime: resa MF moltiplicata per un fattore fisso 0,8 e, separatamente, 0,6
    negli anni senza gruppi di livello 2 nel pilota (1996 e 2008). Il fattore non si estrae.

### 3.4 Pesi dei disegni combinati

- La scala relativa dei pesi MDI e HMI non è calibrata. Principale: Φ MDI come misurato.
- Sensibilità ×0,5 e ×2: non coprono una scala relativa ignota.
- **Alternativa fissata, non calibrazione:** pesi normalizzati per strumento, Φ̃_i = Φ_i / media(Φ dello strumento
  nel disegno). Cambia lo stimatore: dà a ogni strumento lo stesso peso medio per record.
- I risultati sono sempre riportati anche separati per strumento. Quelli combinati sono condizionati all'ipotesi di
  scarti fra strumenti non dipendenti dall'attività (§7).

### 3.5 Flussi (pesi Φ)

- **Requisito del protocollo §7:** conservare la relazione del flusso con area, latitudine e attività. Le due regole
  candidate fissate prima dei conteggi (C7) non soddisfano i criteri fissati con questi donatori.
- **Emendamento A2 del protocollo del pilota** (proposto, non cieco), in un file separato:
  `docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2_DRAFT.md`. Il protocollo originale resta intatto.
  - Il requisito originario viene **attenuato, non soddisfatto**.
  - Si conservano le **classi** di attività, area, emisfero e coorte (cella di selezione), non la loro distribuzione
    congiunta esatta.
  - La latitudine è approssimata dal vicinato in |lat| dentro la cella. Il vicinato limita una distanza, ma non
    verifica la relazione flusso–latitudine.
  - A2 si congela prima della nota; entrambi i riferimenti si registrano prima di ogni calcolo Q4.
- **Regola principale (L-NN):**
  - donatori = record L1 riusciti alla soglia del disegno (50 G; 100 G con `ok100`) nella stessa cella di selezione
    del bersaglio. Dentro la cella π₁ è costante, quindi l'estrazione uniforme non cambia la miscela;
  - per ogni bersaglio, i 5 donatori più vicini in |lat|; parità: distanza, poi ordine (noaa, day);
  - per realizzazione, un donatore estratto uniformemente fra i 5 (§3.6);
  - Φ_g = area_g × ρ_d, con ρ_d = (|flusso positivo| + |flusso negativo|) / area DPD del donatore, dalle colonne
    di flusso della soglia del disegno. Non si legge nessuna colonna di tilt.
- **Sensibilità senza latitudine:** donatore uniforme fra tutti i donatori della cella.
- **Strati del flusso e della resa sono separati:** la resa usa celle (MS) o pool (MF), il flusso la cella con
  vicinato. Ogni cella ha almeno 5 donatori (C7): nessuna unione per il flusso. Se nei dati del run una cella ne
  avesse meno, il disegno è «non calcolabile» (§8).
- **Distanze in |lat|:** i valori di C7 (mediana 4,9°, 90° percentile 10,3°) descrivono i bersagli MS. Per i
  bersagli MF il codice riporta le stesse distanze come conteggio descrittivo; nessuna precisione è coinvolta.
- **MF** usa gli stessi Φ di MS: che i donatori sinottici rappresentino anche gruppi senza misura sinottica è
  un'ipotesi. Il rapporto sin/fd di Q2 (mediana 0,87, 10°–90° percentile 0,65–0,96) motiva la sensibilità
  Φ_MF = Φ_MS / ρ, ma non dimostra che i pesi relativi cambino poco. ρ si estrae uniformemente:
  - a 50 G, dai 61 `flux_ratio` di `Q2_PAIRS_A1_main.csv`;
  - a 100 G, dai 59 `flux_ratio` di `Q2_PAIRS_A1_sens100.csv`.

### 3.6 Realizzazioni e numeri casuali comuni

- **20 realizzazioni**, numero fisso. Non si aumenta dopo aver visto risultati vicini alle soglie senza una nuova regola.
- **Variabili casuali indicizzate e stabili.** Per la realizzazione r (0–19) e la componente k, un generatore
  `np.random.default_rng(SEED0 + 1000·k + r)` produce un vettore di uniformi nell'ordine fisso della sua lista:
  - k = 0: U_g, inclusione, una per riga di POPULATION (5401, ordine del file). Il gruppo entra se U_g < p del suo
    strato;
  - k = 1: V_c, rese delle 36 celle MS, nell'ordine di CELLS.csv. p_c = quantile Beta (`scipy.stats.beta.ppf`) di V_c;
  - k = 2: V_pool, rese dei pool MF, 14 valori in quest'ordine: M1, U; M1 × attività 1–3, U × attività 1–3;
    M1 × area 1–3, U × area 1–3. Le letture con pool diversi usano quindi uniformi diverse;
  - k = 3: D_g, scelta del donatore, una per riga di POPULATION: indice ⌊5·D_g⌋ fra i 5 donatori ordinati
    (distanza, poi (noaa, day)). Nella sensibilità senza latitudine: ⌊n_c·D_g⌋ fra i donatori della cella ordinati
    per (noaa, day);
  - k = 4: R_g, scelta di ρ per la sensibilità MF, una per riga di POPULATION: indice ⌊n_ρ·R_g⌋ nell'ordine del file
    Q2_PAIRS.
- Le stesse uniformi valgono a 50 e a 100 G; cambiano solo le soglie e i conteggi.
- **Appaiamento effettivo:**
  - MS, MS+H, MF e MF+H della stessa realizzazione usano gli stessi U_g e D_g;
  - H è identico in tutte le realizzazioni;
  - un gruppo presente in MS e in MF ha lo stesso Φ (a parte la sensibilità con ρ).
- **Semi:** SEED0 = 35 200 000; le componenti 0–4 e le realizzazioni 0–19 occupano 35 200 000–35 204 019.
  - Verificato in lettura il 24 novembre: la zona è disgiunta da `USED_RANGES` della fase A (massimo 33 200 000) e
    nessun file di `scripts/`, `python/` o `docs/` contiene numeri nella zona 35 200 000–35 299 999.
  - Il codice ripete la verifica su `USED_RANGES` e la registra.

## 4. Modello e bersaglio

**Adattatore della matrice, proprio di Q4.** Riusa `p2d.wls_row`, ma non `_finish`, che si ferma con errore sulle
colonne dipendenti non nulle.
- **Colonne in ordine fisso:**
  1. intercetti I{c}{h} = 1[ciclo c, emisfero h]·sin|λ|, cicli crescenti, N prima di S;
  2. termini di strumento, solo nei disegni combinati:
     - M24N, M24S = M·1[c = 24, h]·sin|λ|, come in `t3_design`;
     - per il modello bJ: M_x3 = M·(A − 1)·sin|λ|;
     - per il modello bA: M_N, M_S = M·1[h], M_A = M·(A − 1);
  3. x₃ = (A − 1)·sin|λ|, sempre per ultima.
- **Riduzione per rango incrementale.** Ogni colonna di disturbo si aggiunge, nell'ordine, solo se aumenta il rango
  della matrice pesata (righe × √w). Le colonne scartate si registrano. x₃ non si scarta mai: β₃ è identificabile se
  rango([Z, x₃]) = rango(Z) + 1, altrimenti il disegno è «non calcolabile» (§8).
- **Rango:** colonne pesate e normalizzate a norma unitaria; SVD; tolleranza = max(n, p)·ε·σ_max (default NumPy). La
  normalizzazione serve solo al rango, non cambia la stima.
- **Casi attesi, da verificare con prove sintetiche prima del codice reale:**
  - in H, M24N/M24S sono nulle (M = 0) e cadono, come in E0 della fase A;
  - in MDI da solo, M = 1: M24N/M24S coincidono con I24N/I24S e cadono; bJ e bA non si applicano (M_x3 coincide
    con x₃).
- **Modelli:**
  - (a) comune MDI, per MS e MF da soli;
  - (a) comune combinato;
  - protetti bJ e bA della fase A, solo per i combinati: per J β è la pendenza HMI, per A il coefficiente comune dopo
    il controllo degli scarti additivi.
- **Bersaglio** (A0 della fase A):
  - proiezione WLS della rampa Δγ_i = −δ(Ā_c)·24°·sin|λ_i|, con δ(a) = δ_max·clip((a − A_lo)/(A_hi − A_lo), 0, 1)
    (`ramp` della fase A) e Ā_c la media di A dei record della cella (CR, emisfero) del disegno;
  - δ_max = 0,20 (secondario 0,10);
  - principale: A_lo = 0,5020189558504007, A_hi = 2,7602501179328134, i quantili 5–95 % di E0 letti a precisione
    piena da `results/PROSPECTIVE_PHASE_A/RAW.csv.gz` (colonne `A_lo_ext`, `A_hi_ext` della riga E0);
  - sensibilità: quantili ricalcolati sul disegno.

## 5. Rumore e scarti

Il protocollo del pilota (§7) chiede di fissare qui σ²ₓ, κ e la definizione di σ_e.

**Rumore individuale del tilt:** σ_e,i² = σ_int² + σ_m,i².
- **σ_int, dispersione intrinseca del modello:**
  - 15° principale (scala P2f, come fase A e T3 su MWO);
  - 25° e 30° come sensibilità. Il 30° è vicino alla dispersione **totale** osservata di McClintock & Norton (2013):
    usato come σ_int insieme a σ_m e a σ_x conta due volte misura e variazione temporale. È uno scenario alto
    dichiarato, non un valore realistico.
  - Si applica a MDI e a HMI.
- **σ_m, errore di misura MDI:** {0; 2°; 10°}, **principale 2°**. Sono scenari scelti, non stime: il pilota non
  misura l'errore di misura.
  - 2° ≈ mediana |d_ax| di Q2 (sinottica − full-disk) / 0,6745: scala equivalente sotto una normale centrata, non una
    stima separata dell'errore MDI. La ripetibilità A − B (≈ 1,1°) combina evoluzione ed errori correlati.
  - 10° ≈ mediana |d_ax| fd − MWO / 0,6745, attribuita tutta a MDI: **scenario alto scelto, non limite superiore
    verificato.** Differenze assiali, code, avvolgimento ed errori correlati impediscono di trattarlo come limite.
  - Code pesanti non rappresentate: il riferimento è normale, limite dichiarato.
  - Per HMI σ_m = 0, come nella fase A: l'errore di misura HMI è implicito nella scala P2f.
- Errori individuali indipendenti fra record e indipendenti dalla componente temporale.

**Componente temporale per cella (CR, emisfero):**
- σ_x = 7,5° × {0,5; 1; 2};
- forme (generatori di `diag_t5_oracle.k_true`):
  - AR(1) φ = 0,5, κ = 0 (scenario 1);
  - AR(1) φ = 0,9, κ = 0 (scenario 2);
  - salti di 20 CR (scenario 7), κ = 0: solo blocchi dello stesso emisfero;
  - sensibilità: scenari 3 (φ = 0,9, κ = −0,8) e 4 (φ = 0,5, κ = +0,6).
- **Ritardi:** differenze effettive di CR fra le celle, senza comprimere nulla.
- **Principale:** una sola componente solare comune a MDI e HMI, con la covarianza continua fra le celle MDI
  (CR ≤ 2095) e HMI (CR ≥ 2096).
- **Sensibilità:** blocchi incrociati MDI–HMI azzerati, covarianze interne identiche. Rappresenta componenti
  indipendenti fra i due periodi, non un dato verificato.
- Entrambe le matrici devono risultare simmetriche e semidefinite positive: autovalore minimo ≥ −1e-10·autovalore
  massimo. Altrimenti si ha un arresto tecnico.
- Stessa ampiezza per i due strumenti. Il fit esplorativo del pilota (φ = 0,29, κ = −0,98 al bordo) non si usa come
  scenario: il protocollo lo dichiara poco informativo per costruzione.

**Varianza generalizzata** (la `t3_var` della fase A ha σ fissi e non si riusa invariata):
Var(β̂) = Σ a_i²σ_e,i² + σ_x²·bᵀKb, con a la riga WLS dei record e b_c = Σ_{i∈c} a_i. Riscontro: con σ_int = 15,
σ_m = 0 e gli scenari della fase A deve dare la varianza di `t3_var` su E0 (§6).

**Scarti (distorsione, non precisione):**
- **Disegni combinati:** famiglie A e J della fase A (`bias_bases`), limiti C ∈ {0,25; 0,5} nelle unità del
  bersaglio, e tolleranza (lo scarto di attività che sposta β di metà del bersaglio).
- **MDI da solo:** uno scarto di misura MDI della forma c·(A − 1)·sin|λ| coincide con x₃ e sposta β esattamente di c.
  Non è separabile e non si calcola: si dichiara. La stabilità interna di MDI non è verificata.
- **Differenza fra prodotti (scenario descrittivo non cieco):**
  - d_k = mediana di d_γ del gruppo `activity k` di `Q2_SUMMARY_A1_main.csv` (−0,53, −0,79, −1,19°; a 100 G da
    `…_sens100.csv`: −0,58, −1,29, −1,34°). Il codice legge solo questa colonna per questi tre gruppi e verifica i
    valori arrotondati della nota;
  - classi = `act_class` della selezione (terzili di A_main, C1);
  - Q2 = sinottica − full-disk: si riporta m = Σ a_i·d_{k(i)} sui record MS, cioè lo spostamento di β fra i due
    prodotti se la differenza osservata valesse per i gruppi futuri. Non è una distorsione assoluta di MS rispetto
    al vero;
  - gli intervalli dei terzili contengono zero: non è uno scarto dimostrato. Nessuna inferenza causale.

## 6. Calcolo e prodotti

**Varianza analitica condizionata a ogni realizzazione del disegno**, livello 97,5 %, z = `Z` della fase A a
precisione piena (2,241402727604947; 2,2414 è solo l'arrotondamento per il testo).

**Configurazioni.** Non si calcola il prodotto cartesiano di tutte le sensibilità. Si calcolano:
1. **griglia di rumore completa** per ogni disegno (H, MS, MF, MS+H, MF+H), ogni modello applicabile e le due soglie
   (50 e 100 G):
   - σ_int ∈ {15, 25, 30}, σ_m ∈ {0, 2, 10};
   - le 9 combinazioni forma × scala (scenari 1, 2, 7 × σ_x 0,5/1/2) più gli scenari 3 e 4 alle tre scale;
   - tutto il resto alla configurazione di riferimento (§7);
2. **sensibilità una alla volta:** per ciascuna sensibilità elencata sotto si calcolano le tre forme principali a
   σ_x = 7,5°, in **entrambe** le configurazioni (σ_int, σ_m,MDI) = (15°, 2°) e (30°, 10°). Tutti gli altri parametri
   restano quelli di riferimento. Non si incrociano sensibilità diverse. H mantiene σ_m,HMI = 0.
   - pool MF coorte × attività (sempre affiancato) e coorte × area;
   - fattori di disponibilità 0,8 e 0,6;
   - flussi senza latitudine; Φ_MF = Φ_MS / ρ;
   - pesi ×0,5, ×2 e normalizzati per strumento (solo combinati);
   - covarianza con blocchi incrociati azzerati (solo combinati);
   - attività A_main (solo MDI da solo);
   - quantili del bersaglio ricalcolati sul disegno;
3. δ_max 0,20 e 0,10 in tutte le righe (il bersaglio scala linearmente).

**Per disegno, modello, rumore, resa e flusso:**
- record, celle, rotazioni; gruppi esclusi per filtro e per resa;
- colonne usate e scartate;
- bersaglio Δβ (° per unità di attività e in γ₀);
- SE; semilarghezza h = z·SE in γ₀; rapporto h/h_H nella stessa realizzazione;
- SE/|Δβ|; frequenza di riconoscimento dello scenario; quota temporale della varianza;
- tolleranza e distorsioni;
- mediana, minimo e massimo sulle realizzazioni calcolabili, con n_ok calcolabili e n_fail = 20 − n_ok.

**Prove prima della corsa (arresto tecnico se fallisce una):**
1. **Riproduzione di E0.** Riferimento: `results/PROSPECTIVE_PHASE_A/RAW.csv.gz`, righe ext = E0, test = T3 (tutte le
   famiglie e i modelli, noise 0–8). H con σ_int = 15, σ_m = 0 deve riprodurre:
   - colonne usate e scartate;
   - bersaglio −1,602647454341313 (relativo 1e-12);
   - i 9 SE e le quote temporali di ogni modello (relativo 1e-12).
2. **Riproduzione deterministica delle rese.** Senza Beta, pool e filtri Q4, r/n e le N delle celle riproducono
   `Q1_YIELD_PROJECTED.csv` e le righe dell'immagine A di `YIELD_A1.csv` (relativo 1e-12), come in C5.
   - Separatamente, senza pretendere identità, si quantifica quanto cambiano la resa attesa le singole modifiche:
     media della Beta, pool, filtri Q4.
3. **Prove sintetiche,** con risultati attesi ricavati a mano o con formule indipendenti dal codice sotto controllo:
   - celle con pesi diseguali, r = 0, r = n, celle vuote, pool;
   - colonne dipendenti e rango incrementale;
   - PSD dopo l'azzeramento dei blocchi incrociati;
   - stabilità dei numeri casuali al cambiare del disegno;
   - verifica che nessuna colonna di tilt venga letta.

## 7. Lettura e uso per la decisione

**Le soglie sono preferenze pratiche, fissate prima dei calcoli; non sono criteri con calibrazione scientifica.**
- 0,7 su h significa circa metà della varianza (0,7² ≈ 0,49): MDI porterebbe almeno l'informazione di H.
- 0,9 significa circa un quinto di varianza in meno: sotto, il guadagno non giustifica da solo un catalogo.
- 1,1 per MF: si tollera un intervallo più largo del 10 % in cambio della geometria più diretta del full-disk.

**Configurazione di riferimento:**
- σ_int = 15°, σ_m = 2°, σ_x = 7,5°;
- resa principale (§3.2, §3.3), flussi L-NN, pesi ×1;
- modello (a), scarti nulli;
- mediana su 20 realizzazioni del rapporto calcolato nella stessa realizzazione.

**Contributo di MDI a T3 (MS+H rispetto a H):**
- **«utile come limite»** se h(MS+H) ≤ 0,7·h(H) per ciascuna delle tre forme principali e resta ≤ 0,8·h(H) con
  σ_int = 30° e σ_m = 10° (altri parametri di riferimento);
- **«marginale»** se non è utile, ma h(MS+H) ≤ 0,9·h(H) per tutte e tre le forme;
- altrimenti: **«riduzione inferiore al criterio fissato, nelle configurazioni esaminate»**.

**Misura su un altro ciclo:** MS (o MF) da solo con h ≤ h(H) per le tre forme principali si registra come «misura
T3 su un altro periodo/ciclo (essenzialmente il 23), con precisione prospettica almeno pari». Non è una replica
indipendente: restano ipotesi condivise e possibili correlazioni temporali. Non autorizza una lettura multiciclo di
MDI da solo.

**Prodotto:** MF si considera solo se h(MF+H) ≤ 1,1·h(MS+H) per ciascuna delle tre forme principali, nella
configurazione di riferimento, sia con il pool per coorte sia con il pool coorte × attività. La scelta finale considera
anche la differenza fra prodotti (§5), che Q4 descrive ma non risolve.

**Sempre accanto, senza criterio:**
- rapporto del modello protetto (bJ, bA) nella stessa configurazione. Un «utile» del modello (a) presuppone scarti
  fra strumenti non dipendenti dall'attività, non verificati, e non diventa una raccomandazione incondizionata;
- risultati con i pesi normalizzati per strumento e con le sensibilità ×0,5 e ×2;
- riconoscimento dello scenario prescritto: la fase A lo dà basso con qualunque estensione, e l'uso realistico è un
  intervallo più stretto, non il riconoscimento.

**Realizzazioni non calcolabili:** se n_fail > 0 in una configurazione usata da un criterio, quel criterio non dà
classificazione («utile», «marginale», MF considerato, misura su un altro ciclo). Si riportano il risultato
condizionato alle n_ok realizzazioni calcolabili e le cause.

**La decisione resta dell'utente con Codex.** Q4 non produce un verdetto su T3 e non stima β₃.

## 8. Condizioni di non calcolabilità

- β₃ non identificabile in una realizzazione: «non calcolabile», con le colonne responsabili.
- Un pool o una cella di resa senza unità dopo i filtri, o una cella di flusso con meno di 5 donatori: il disegno è
  «non calcolabile», con lo strato.
- Mesi senza attività SILSO: i record si escludono e si contano. Oltre il 5 % dei record, il disegno è segnalato.
- Una prova del §6 fallita: arresto tecnico, nessun prodotto.
- **MDI da solo come misura separata** (MS e MF). I conteggi (§1.3) mostrano che il ciclo 22 ha solo 20 e 13
  gruppi: il requisito «tre cicli per emisfero» della revisione 1 renderebbe impossibile la misura e si abbandona
  (scelta non cieca). Si distinguono:
  - identificabilità algebrica: rango, come sopra;
  - requisito pratico scelto: almeno 50 record del ciclo 23 in ciascun emisfero nella realizzazione. Altrimenti il
    disegno MDI da solo è «non calcolabile come misura separata» e resta nei combinati.
  - Il requisito non equivale alla capacità di confrontare più cicli.

## 9. Che cosa non fa

- Non scarica dati e non misura tilt.
- Non valida la procedura M sui disegni MDI: le frequenze sono nel riferimento normale a varianza nota.
- Non stima l'errore di misura MDI né la sua dipendenza dall'attività.
- Non inventaria i magnetogrammi full-disk: la disponibilità fuori dai 90 giorni del pilota è un'ipotesi.
- Non tratta BARD-MDI, che resta un controllo esterno separato, da anticipare solo se Q4 risulta sensibile a
  un'ipotesi che quel confronto può sostenere.
- Non tratta la serie BL combinata né la sorgente BL.
- Non riapre T3 su HMI o su MWO.

## 10. Codice e sequenza

**Riuso, importando senza modificare:**
- da `scripts/prospective_phase_a.py`: `cr_start`, `cycle_of_time`, `years`, `e0_records`, `load_inputs`, `bias_bases`,
  `freqs`, costanti `GAMMA0`, `Z`, `DMAX`, `NOISE`, `USED_RANGES`;
- `ramp` di `scripts/t5_proxy_sensitivity.py`; `k_true` di `python/sharpbl/diag_t5_oracle.py`; `p2d.wls_row`;
  `run_p2.load_silso`;
- `group_rotation` di `scripts/mdi_synoptic_adapter.py` e la regola delle mappe richieste (come in C2).

**Nuovo:**
- adattatore della matrice con rango incrementale;
- varianza generalizzata;
- filtri, rese per cella e per pool con estrazione Beta;
- donatori L-NN;
- numeri casuali indicizzati;
- prove del §6.

**Input, con percorso e SHA-256 registrati negli output:**
- `results/MDI_PILOT_SELECTION/`: `POPULATION.csv`, `SAMPLE.csv`, `CELLS.csv`, `META.json`;
- `results/MDI_PILOT_L1/L1_RECORDS.csv`: solo identificativi, stato, `maps`, N, N_ephemeris e colonne di flusso;
- `results/MDI_PILOT_L2/L2_RECORDS.csv`: solo `rule`, `noaa`, `day`, `image`, `status`;
- `results/MDI_SYNOPTIC_AUDIT/FILES.csv`: solo `CAR_ROT`;
- `results/MDI_PILOT_ANALYSIS_L1/Q1_YIELD_PROJECTED.csv` e `results/MDI_PILOT_ANALYSIS_L2/YIELD_A1.csv` (prove);
- `results/MDI_PILOT_ANALYSIS_L2/Q2_PAIRS_A1_main.csv` e `Q2_PAIRS_A1_sens100.csv` (solo `flux_ratio`);
  `Q2_SUMMARY_A1_main.csv`, `Q2_SUMMARY_A1_sens100.csv` (solo `median_d_gamma` dei gruppi `activity 1–3`);
- `results/PROSPECTIVE_PHASE_A/RAW.csv.gz` (riferimento E0 e quantili);
- campione S di HMI (catalogo P1) e serie SILSO, attraverso `load_inputs` della fase A;
- `results/MDI_Q4_PREP_COUNTS/META.json`: il codice verifica di ritrovare gli stessi conteggi C2–C7;
- `docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2.md` congelato, con il suo file FREEZE.

**Sequenza:**
1. revisione di questa bozza e della bozza di A2;
2. congelamento: A2 prima, poi la nota (SHA in file FREEZE, con semi e impronte di tutti gli input);
3. codice e selftest, revisione;
4. corsa unica;
5. conservazione prima della lettura;
6. riconteggio indipendente;
7. rapporto descrittivo;
8. decisione dell'utente.

## 11. Punti aperti per la revisione

Nessun punto di metodo aperto: i cinque punti della revisione 2 hanno avuto parere favorevole con limiti, recepiti
nei §3.3, §3.5, §5, §7 e §8. Si chiede la chiusura documentale della revisione 3 e della bozza di A2.

## 12. Modifiche

**Dalla revisione 1 alla 2:**

- Resa MF ricostruita nelle celle con N e pesi 1/π2, pool per coorte con Beta condivisa e n efficace (rilievo 1).
- Filtri data e CR < 2096 separati; mappe mancanti = {1938, 1939, 1940}: «CR 1998» della revisione 1 era l'anno;
  esclusione dalle mappe richieste; filtro 4 di MF (rilievo 2).
- Adattatore della matrice e varianza generalizzata al posto del riuso diretto di `_finish` e `t3_var` (rilievo 3).
- Flussi con donatori della cella di selezione e vicinato in |lat|; emendamento A2 per la regola fissata prima dei
  conteggi; percentile 0,65–0,96 solo come motivo della sensibilità (rilievo 4).
- «Inviluppo superiore» sostituito; σ_int distinto dalla dispersione totale di letteratura (rilievo 5).
- Specifica: numeri casuali indicizzati, attività nel mese del record, quantili E0 a precisione piena, κ = 0 per
  steps20, covarianza continua con sensibilità a blocchi azzerati, riproduzione di E0, input completi, k/20 (rilievo 6).
- Soglie motivate come preferenze pratiche, formulazioni sostituite, modello protetto sempre accanto (rilievo 7).
- Classi di attività dalla fonte corretta (`META.json` della selezione), non da `CLASS_EDGES.json`.

**Dalla revisione 2 alla 3** (`MDI_Q4_NOTA_REVISIONE2_REVISIONE_CODEX.txt`):
1. Beta con n efficace dichiarata come modello approssimato, non verificato rispetto al disegno campionario (§3.3).
2. Pesi MF originari 1/π₂ sulle unità ammissibili; stima a rapporto nel dominio filtrato; rese dopo il filtro 4
   (M1 49/53, U 12/35) distinte dal riferimento storico; N originarie e filtrate registrate (§3.1, §3.3).
3. Motivazione del pool per coorte corretta (parsimonia, omogeneità assunta); coorte × attività sempre affiancata
   (§3.3).
4. n_ok e n_fail; criterio MF per tutte e tre le forme e per entrambi i pool; requisito sul ciclo 23 per MS e MF
   (§6–§8).
5. ρ a 100 G dai 59 rapporti sens100; configurazioni elencate; fattori di disponibilità deterministici; componenti
   casuali riordinate; SEED0 fissato e verificato; Z a precisione piena; terzili di |lat| globali; distanze C7 solo
   per i bersagli MS (§1.3, §3.5, §3.6, §6).
6. A2 in un file separato, con formulazione ristretta (§3.5).

**Dalla revisione 3 alla 3.1** (`MDI_Q4_NOTA_REVISIONE3_REVISIONE_CODEX.txt`): §6, punto 2 delle configurazioni,
riscritto con il testo proposto da Codex. Le sensibilità una alla volta si calcolano sia a (15°, 2°) sia a (30°, 10°).
Nessun altro cambiamento. La revisione 3 (SHA `d0574435…`) è conservata in
`reviews/MDI_Q4_REVISION3_d0574435/` della cartella di consegna MWO.

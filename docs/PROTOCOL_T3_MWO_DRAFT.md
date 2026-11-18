# T3 sul catalogo magnetico Mount Wilson 1974–2012 — bozza di protocollo

**BOZZA NON CONGELATA, 18 novembre 2026 (Claude), revisione 3 dopo la revisione di Codex della revisione 2 (`1be456f`).**
Modifiche rispetto alla revisione 2:
- la fusione di epoche è sostituita dalla verifica dell'identificabilità di β₃;
- S1 è un controllo relativo fra epoche, con soglia descritta come 10 % di γ₀ e bootstrap fissato;
- S2 ha una precedenza esplicita fra gli esiti e riporta copertura e perdite del sottoinsieme con tilt DPD;
- le sensibilità di attività sono fissate ora, indipendentemente dal controllo di omogeneità;
- corretta la frase sull'assegnazione dei cicli;
- registrate le fonti lette (Ulrich et al. 2002 §2; Győri et al. 2017) e il controllo di omogeneità di DPD
  (`results/DPD_ACTIVITY_HOMOGENEITY/`); nella tabella delle epoche i confini osservati negli header sono distinti dalle date
  documentate.
- dopo la revisione della revisione 3: seme di S1 69 000 001 (61 000 001 collideva con la griglia), S1 «non determinato» nella
  regola finale e nella tabella degli esiti, g, Δβ e C calcolati sulla matrice ridotta a rango pieno.

Modifiche della revisione 2 rispetto alla revisione 1 (`38b81a5`):
- isolamento applicato al giorno candidato, con registro delle perdite;
- termini di epoca con controllo del rango e forma additiva come sensibilità;
- S1 riscritto per emisfero e in unità di coefficiente di Joy;
- S2 con condizione di equivalenza;
- E6 rinominata e E7 divisa al cambio del 1996;
- classe di risoluzione su entrambe le dimensioni;
- effetto simulato unico (rampa) con valore vero proiettato sulla matrice MWO;
- rumore e scala temporale dichiarati;
- omogeneità dell'attività DPD da verificare.

Da rivedere con Codex prima del congelamento.

Nessun tilt MWO fuori dal pilota è stato calcolato, e nessun tilt DPD in luce bianca è stato calcolato o letto. Per
scrivere il testo sono stati usati solo metadati:
- l'inventario degli header MWO (`results/MWO_HEADER_INVENTORY/`, `scripts/mwo_header_inventory.py`, solo keyword, nessun pixel);
- i conteggi dei gruppi DPD con magnetogramma MWO lo stesso giorno (§2), da posizioni DPD e date degli header;
- il controllo descrittivo della serie di attività DPD (§3), che usa solo aree, fonti giornaliere e SILSO.

Base: pilota MWO (`docs/PROTOCOL_MWO_PILOT.md`, risultati in `docs/MWO_PILOT_RESULTS.md`: variante utilizzabile) e
bozza T3 su DPD (`docs/PROTOCOL_T3_DPD_DRAFT.md`, §8b), che questo protocollo sostituisce per la via magnetica.

**Non cieco.** Sono noti:
- T3 su HMI: −3,59° per unità di attività, intervallo [−10,58°; +3,41°];
- la fase A e il calcolo analitico su DPD;
- il pilota: mediana d_γ −0,69°, mediana |d_ax| 4,40°, rapporto di flusso 0,16;
- la letteratura sulla dipendenza fra cicli (Dasi-Espuig et al. 2010; Jiao et al. 2021).

I tilt del catalogo lungo restano **sigillati** fino alla lettura della validazione (§7).

## 1. Domanda, popolazione e prodotto principale

Il coefficiente di Joy delle regioni bipolari dipende dall'attività emisferica **dentro** il ciclo, nei cicli 21–23
(più le code dei cicli 20 e 24), misurato con la stessa grandezza di P1, cioè il tilt magnetico con le polarità?

- **Popolazione.** La risposta riguarda le **regioni isolate e misurabili** sui magnetogrammi MWO: gruppi DPD senza altri
  gruppi nella finestra di misura, con le due polarità sopra 50 G alla risoluzione MWO (§2). Non riguarda tutte le
  regioni. Questa popolazione è diversa dal campione S di P1, e il confronto con HMI va letto con questa avvertenza.
- **Prodotto principale:** l'intervallo della pendenza β₃.
- **Verdetto** (`supportato`, `opposto`, `non deciso`): solo se la validazione (§7) e i controlli di stabilità (§6) sono
  superati.
- **Fuori da questo protocollo:** la dipendenza fra cicli (forza del ciclo). È un'altra domanda.

## 2. Campione

**Periodo.** Date UT dal 1974-01-01 al 2012-12-31: i magnetogrammi MWO Fe I dell'archivio vanno fino al 2013-01 e i
gruppi DPD (`gDPD<anno>.txt`, già locali con SHA-256) coprono il periodo.

**Magnetogrammi.**
- Solo Fe I 5250,2 Å: famiglie `MP00_5250*` e `*fe1*`, riconosciute come nella pipeline MWO congelata. Na I è escluso.
- Mancano il 1979–1980 (archivi non utilizzabili) e il 1997 (nessun Fe I).
- Si considerano solo i magnetogrammi dello stesso giorno UT che superano i controlli di effemeridi della pipeline
  (|ΔCENLON| ≤ 18°, |ΔB0| ≤ 0,5°).

**Classe di risoluzione** (da entrambe le dimensioni d'osservazione, DXB_OBS e DYB_OBS):

| Classe | DXB_OBS | DYB_OBS |
|---|---|---|
| R1, circa 9,5″×13″ | < 11″ | < 15″ |
| R2, circa 13″×20″ | 11″–14″ | ≥ 18″ |
| R3, circa 14″×17″ | ≥ 13,5″ | 15″–19″ |
| R0 | valori mancanti o fuori da tutte le classi | |

- Le classi si assegnano nell'ordine R1, R2, R3: un magnetogramma che rientra in due classi prende la prima.
- Ordine di preferenza nella scelta: R1, poi R2, poi R3, poi R0.
- Dentro la classe scelta, vince il TAVG-UT più vicino all'ora DPD del gruppo; a parità, il TAVG-UT più basso.
- Il valore numerico della risoluzione dentro una classe non conta.
- La composizione per classe è riportata per epoca, per verificare quanto la scelta renda omogenea la risoluzione.
- Sensibilità: solo record in R1.

**Giorni candidati e isolamento.** Un giorno è candidato per un gruppo DPD (stringa NOAA, lettere comprese) se:
- il gruppo ha una riga `g` con area WS corretta ≥ 1 e |λ| ≤ 45°;
- esiste un magnetogramma scelto come sopra;
- **il gruppo è isolato quel giorno**, cioè nessun altro gruppo DPD dello stesso giorno ha il centro nella finestra di misura.

L'isolamento si applica quindi **prima** della scelta del giorno, non al record già scelto.

**Record.**
- I giorni candidati si ordinano per |LCM| crescente.
- Il record è il primo giorno in cui la misura riesce: finestra nel dominio μ ≥ 0,8, due polarità sopra soglia ed effemeridi valide.
- La regola dipende anche dal campo: un gruppo debole può fallire vicino al meridiano e riuscire più lontano, oppure mai.
  Per questo si registrano, per ogni record:
  - la posizione del giorno scelto nell'ordine dei candidati;
  - |LCM|;
  - le cause di fallimento dei giorni precedenti.
- Si riportano le perdite (gruppi senza record e giorni scartati) per attività (terzili), ciclo, epoca ed emisfero.
- Sensibilità: solo record scelti al primo giorno candidato.

**Misura.** È identica al pilota congelato:
- finestra |λ − λ_DPD| ≤ 6°, |L − L_DPD| ≤ 8°;
- B_r = B_LOS/μ, con 50 G ≤ |B_r| ≤ 4000 G;
- baricentri pesati con |B_r|/μ sulla sfera;
- convenzione di P1: la testa è la polarità più a ovest; γ = sign(λ̄)·asin(sin tilt), positivo se la testa è più vicina
  all'equatore;
- nessuna correzione di rotazione fra l'ora DPD e l'ora MWO dello stesso giorno, come nel pilota;
- lettore e geometria della pipeline congelata, incluso il float32 prima di BSCALE (`results/MWO_PILOT_FLUX_DIAGNOSIS/`).

Grandezze salvate per record: latitudine media pesata col flusso λ̄, flusso nella finestra Φ_MWO, segno della polarità di
testa, segno di Hale atteso dal ciclo, distanza dei baricentri e classe di risoluzione.

**Sensibilità «tutti i record».** Stessa regola senza la condizione di isolamento sui giorni candidati.

**Conteggi dai soli metadati** (limite superiore, prima delle esclusioni di misura; isolamento valutato nel giorno con
|LCM| minimo, quindi solo indicativo per la regola sopra):
- 8802 gruppi con almeno un giorno candidato, su 445 rotazioni di Carrington; 7704 isolati;
- per ciclo, nord/sud: 20 164/238; 21 1017/1184; 22 1205/1392; 23 1397/1528; 24 397/280;
- nel pilota era valutabile il 79 % degli abbinati, ma il campione S di P1 ha regioni più grandi dei gruppi DPD: la frazione
  qui sarà minore.

**Copertura minima.** Lo studio è informativo solo se:
- ci sono almeno **3000** record isolati valutabili;
- ognuno dei cicli 21, 22 e 23 ne ha almeno **300 per emisfero**.

Altrimenti l'esito è «non concludente»: si riportano solo le cause e i conteggi.

## 3. Attività, cicli, modello

**Attività principale.**
- Area WS corretta dei gruppi DPD: somma giornaliera per emisfero, media mensile sui giorni osservati, normalizzata alla
  media 1974–2012.
- La serie è indipendente da MWO.
- La sua omogeneità non è garantita. Secondo Győri et al. (2017, MNRAS 465, 1259), DPD si basa sulle immagini di Gyula e
  Debrecen e riempie i buchi con immagini di osservatori di tutto il mondo; le aree DPD differiscono di qualche per cento da
  quelle di HMI e della fonte di Greenwich.
- **Controllo descrittivo fatto prima del congelamento** (`scripts/dpd_activity_homogeneity.py`,
  `results/DPD_ACTIVITY_HOMOGENEITY/`, solo aree, fonti giornaliere e SILSO):
  - fonte prevalente per anno, dal codice di osservatorio delle righe giornaliere: Gyula quasi sempre (38–88 %), con
    Debrecen, Kislovodsk, Kanzelhöhe e Mitaka; **SOHO/MDI fornisce il 93 % dei giorni nel 2006 e nel 2007 e il 99 % nel
    2010**; Kanzelhöhe il 66 % nel 2011;
  - rapporto annuo fra area WS corretta media e numero SILSO totale medio: da 4,8 (2008) a 12,8 (2002, 2005). Il rapporto
    cresce con l'attività e scende ai minimi, e nel ciclo 23 è più alto che nel 21. La variazione può avere origine
    solare (il rapporto area/numero non è costante) oltre che dalle fonti: il controllo non decide;
  - correlazione mensile fra attività DPD emisferica e SILSO emisferico, 1992–2012: 0,94 a nord e 0,92 a sud.
- **Sensibilità fissate ora, indipendentemente dal controllo:**
  - (a) attività DPD calcolata solo sui giorni con fonte Gyula o Debrecen (le due fonti proprie del catalogo; i mesi senza
    tali giorni restano senza attività e i loro record escono da questa sensibilità);
  - (b) SILSO emisferico, 1992–2012;
  - (c) SILSO totale ripartito per emisfero con le frazioni di area DPD del mese. Questa sensibilità conserva una dipendenza
    da DPD nella ripartizione emisferica, e lo si dichiara.
- Le unità sono diverse da quelle di HMI: il confronto si fa sull'effetto fra il 5° e il 95° quantile di attività di cella.

**Cicli.**
- Il ciclo dipende dalla data, con minimi 1976-03, 1986-09, 1996-08 e 2008-12, come nella bozza DPD.
- Non c'è separazione per latitudine nelle sovrapposizioni: è un'approssimazione dichiarata. La validazione del §7
  verifica la procedura statistica **condizionatamente** a queste assegnazioni; gli errori di assegnazione non sono generati
  nelle simulazioni e quindi non sono valutati lì.
- Sensibilità: esclusione dei record entro ±1 anno da ciascun minimo, dove gli errori di assegnazione si concentrano.

**Modello principale.**
- γ_i = Σ_{c,h} k_{c,h}·sin|λ̄_i| + Σ_{(e,h) ≠ riferimento} δ_{e,h}·sin|λ̄_i| + β₃·(A_i − 1)·sin|λ̄_i|.
- Gli intercetti ciclo × emisfero (k) sono quelli di T3 su HMI, costruiti solo per le coppie (ciclo, emisfero) presenti
  nel campione.
- δ_{e,h} sono **spostamenti del coefficiente di Joy** per epoca strumentale × emisfero (§4), costruiti solo per le coppie
  presenti, con l'epoca più numerosa come riferimento in ciascun emisfero.
- Pesi: Φ_MWO, l'analogo di Φ in P1. Parametro: β₃, in gradi per unità di attività.
- **Identificabilità di β₃** (nessuna fusione di epoche: fondere epoche cambia il modello e può cancellare differenze
  strumentali vere):
  - matrice pesata W^½X; ranghi calcolati con la SVD e la tolleranza standard di NumPy (`matrix_rank`);
  - β₃ è **identificabile** se rango([Z, x₃]) = rango(Z) + 1, con Z le colonne diverse da x₃, cioè se x₃ non sta nello
    spazio delle altre colonne;
  - se β₃ è identificabile ma Z ha colonne ridondanti, queste si eliminano senza cambiare lo spazio delle colonne. Ordine
    fisso: intercetti ciclo × emisfero, poi spostamenti di epoca in ordine di tempo e di emisfero (N prima di S); si scorre
    l'elenco e si scarta ogni colonna che non aumenta il rango delle precedenti. Il modello e β₃ non cambiano;
  - **se β₃ non è identificabile, l'esito è «non concludente»**;
  - si riportano le colonne eliminate (vuote o ridondanti), il numero di condizionamento della matrice ridotta e il rapporto
    fra l'errore standard analitico di β₃ con e senza termini di epoca (stesso calcolo della fase A), per mostrare quanto i
    termini di epoca costino in precisione;
  - il controllo si fa sul disegno, prima della validazione; la matrice ridotta è quella usata da validazione e stima.

**Sensibilità senza verdetto.**
- Forma **additiva** dello scarto di epoca: δ'_{e,h} come intercetti senza sin|λ̄|, cioè uno scarto costante del tilt.
- Modello senza termini di epoca (forma esatta di T3 su HMI).
- Pesi = area DPD.
- Tutti i record (§2).
- Solo record in R1.
- Solo record al primo giorno candidato.
- Esclusione dei record dal 2010-05 (sovrapposti al campione HMI di T3).
- Attività: le tre sensibilità (a), (b), (c) sopra.

## 4. Epoche strumentali

**Dai metadati.** L'inventario degli header registra per ogni magnetogramma:
- MRKMOD, l'hardware secondo il commento dell'header: 0 = datex, 256 = ael, 1280–1283 = fm, 1284 = 24ch;
- la famiglia dei file, DXB/DYB_OBS, PSEPMA e BSCALE.

MRKMOD è assente nei file moderni. Confini (Fe I, 1974–2012): le colonne «Dal» e «Al» sono **confini osservati negli
header**; la colonna «Documentazione» riporta ciò che dicono le fonti lette, senza attribuire alle fonti date che non
danno.

| Epoca | Indicatore dagli header | Dal | Al | Magnetogrammi | Giorni | Documentazione |
|---|---|---|---|---|---|---|
| E1 datex | MRKMOD 0 | 1974-01-02 | 1974-07-09 | 128 | 119 | solo il commento dell'header |
| E2 ael | MRKMOD 256 | 1974-07-11 (prime prove 1974-04-18) | 1981-12-08 | 1412 | 1295 | solo il commento dell'header |
| E3 fm-0 | MRKMOD 1280 | 1982-01-03 | 1984-09-08 | 799 | 652 | sistema descritto da Howard et al. (1983), citato da Ulrich et al. 2002; data non verificata |
| E4 fm-1 | MRKMOD 1281 | 1984-09-06 | 1989-04-11 | 10 262 | 1252 | solo il commento dell'header |
| E5 fm-2 | MRKMOD 1282 | 1989-04-11 | 1993-09-23 | 10 188 | 1221 | solo il commento dell'header |
| E6 fm-3 | MRKMOD 1283 | 1993-09-22 | 1994-12-30 | 4034 | 362 | solo il commento dell'header |
| E7 moderna, prima | file `*fe1*`, PSEPMA circa 66–69 | 1995-03-25 | 1996-04-08 | 305 | 305 | Ulrich et al. 2002 §2: insiemi di fibre per il nuovo sistema acquisiti nel 1995 |
| E8 moderna, dopo | file `*fe1*`, PSEPMA circa 77–78 | 1996-04-13 | 2012-12-07 | 3810 | 3590 | Ulrich et al. 2002 §2: «Starting in 1996», nuovo sistema a 24 canali e nuovo reticolo (367,5 righe/mm, ordini 7–9, al posto di quello a 632 righe/mm in quinto ordine); **nessun giorno indicato** |

Note sulla tabella:
- **Correzione rispetto alla revisione 1.** MRKMOD 1283 appartiene a fm (1280–1283), non a 24ch: E6 è rinominata.
- **Divisione di E7.** Ulrich et al. (2002, §2) descrivono l'avvio del sistema a 24 canali nel 1996. Negli header, nei file
  moderni:
  - PSEPMA salta da circa 66,8 a circa 77,8 fra il 1996-04-08 e il 1996-04-13;
  - BSCALE passa da 0,1 a 0,05 il 1996-07-05.

  Il confine è il salto di PSEPMA, cioè un confine **osservato negli header** e compatibile con la documentazione (il
  cambio di reticolo e di campionamento spettrale cambia la separazione delle porte). Ulrich et al. 2002 indicano solo
  l'anno 1996, non il giorno: la coincidenza è plausibile ma non dimostrata, e così si riporta. Il cambio di BSCALE resta
  un sotto-periodo descrittivo (scala di memorizzazione).
- Nel 1984-09 → 1994 ci sono circa 10 scansioni al giorno in R2 e R1; la regola del §2 sceglie R1 dove esiste (R1 è
  presente in circa 1195 dei 1252 giorni di E4, 1089 su 1221 di E5 e 319 su 362 di E6).
- I giorni di transizione con due valori di MRKMOD si assegnano per magnetogramma.

**Dalla documentazione (letta il 18 novembre).** Ulrich et al. 2002 (ApJS 139, 259), §2, documenta solo il passaggio del
1996 al sistema a 24 canali e rimanda a Howard et al. (1983) per il sistema precedente; non fornisce date per i cambi
1974–1994. Altre fonti dell'osservatorio non sono state lette. Le epoche E1–E6 poggiano quindi **solo sugli header**,
e lo si dichiara. Le date documentate possono solo dividere un'epoca, mai fonderne due; nessuna data documentata nuova
divide le epoche della tabella.

**Calibrazione.** Ulrich et al. 2002 (§3) descrivono una correzione di saturazione, cioè un fattore moltiplicativo
sul campo che dipende dalla riga e dalla posizione sul disco. Non è verificato se i magnetogrammi dell'archivio la
includano. Un fattore uniforme nella finestra non cambia i baricentri; uno che varia con μ dentro la finestra li sposta
poco. Lo si dichiara come limite e non si corregge.

**Epoche piccole.** Le epoche con meno di **50** record isolati valutabili per emisfero (probabilmente E1, E6 ed E7)
restano nel modello con il loro termine δ, ma nei controlli del §6 si dichiarano «non verificabili».

## 5. Riferimenti disponibili per epoca

| Riferimento | Periodo | Epoche | Grandezza | Uso |
|---|---|---|---|---|
| DPD, tilt in luce bianca calcolati qui da `sDPD` (bozza DPD §3) | 1974–2012 | E1–E8 | tilt senza polarità; peso = area | S1, S2 (§6) |
| P1 (HMI) | 2010-05 → 2012-12 | E8 | tilt magnetico, stessa grandezza | già nel pilota; ripetuto sul catalogo (descrittivo) |
| MDI (SMARP), se l'utente decide il catalogo MDI descrittivo | 1996–2010 | E8 | tilt magnetico | descrittivo; facoltativo, non condizione |
| MWO stesso giorno, R2 contro R1 | 1984-09 → 1994 | E4–E6 | stesso strumento, due risoluzioni | effetto interno della risoluzione (descrittivo) |

**Natura del confronto con DPD.** È un controllo **relativo** fra una misura magnetica (baricentri delle polarità sopra
50 G, LOS/μ, risoluzione circa 10–20″) e una fotografica (baricentri delle macchie pesati per area, senza polarità e senza
facole). Le differenze attese sono:
- fisiche: il tilt magnetico include le plage, quello in luce bianca solo le macchie;
- osservative: risoluzione, orari diversi nello stesso giorno, fonti DPD diverse.

Uno scarto costante non indica un errore di MWO. Ciò che conta per T3 è se lo scarto **cambia** fra epoche (S1) o con
l'attività (S2).

- Prima del 1996 l'unico riferimento esterno è DPD in luce bianca.
- Anche DPD cambia fonti di osservazione nel tempo (Baranyi et al. 2016; Győri et al. 2017): i cambi documentati si
  registrano prima del congelamento e si riportano accanto alle epoche MWO in S1, per non attribuire a MWO un salto di DPD.
- I file `sDPD` 1974–2012 si scaricano dopo il congelamento, con SHA-256.

## 6. Controlli di stabilità della misura (prima della lettura di β₃)

Si calcolano sui record isolati valutabili che hanno anche un tilt in luce bianca, con d_WL = γ_MWO − γ_WL (asse,
convenzione di Joy). I risultati si conservano in Git prima che la stima di β₃ venga letta.

**Sottoinsieme dei controlli.** S1 e S2 usano i record isolati valutabili che hanno anche un tilt in luce bianca valido
(almeno una macchia in testa e una in coda, §3 della bozza DPD). Si riportano copertura e perdite di questo sottoinsieme
rispetto al campione di β₃: numero di record, frazione, e perdite per attività (terzili), ciclo, epoca ed emisfero. Se il
sottoinsieme contiene meno del 70 % dei record del campione di β₃, lo si dichiara come limite del controllo.

**S1. Scarto relativo fra epoche, per emisfero, in unità di coefficiente di Joy.**
- Modello per d_WL: d_WL = Σ_{e,h} a_{e,h}·sin|λ̄| + Σ_{e,h} b_{e,h} + errore, pesi Φ_MWO.
  - a_{e,h} è lo scarto di coefficiente di Joy fra MWO e luce bianca per epoca ed emisfero;
  - b_{e,h} è lo scarto additivo.
- Usare i coefficienti invece delle mediane del tilt evita che la diversa distribuzione delle latitudini fra epoche
  produca differenze di tilt mediano a parità di coefficiente.
- Per ogni epoca verificabile ed emisfero si calcola a_{e,h} − ā_h (ā_h media delle a_{e,h} sulle epoche verificabili,
  pesata con la somma dei pesi Φ_MWO di ciascuna epoca), con intervallo bootstrap percentile al 95 %.
- **Bootstrap.** Blocchi di 6 CR consecutive (circa mezzo anno), non sovrapposti, definiti dentro ciascuna epoca a partire
  dalla prima CR dell'epoca; si ricampionano con reinserimento i blocchi di ciascuna epoca, con entrambi gli emisferi
  insieme per conservare la correlazione nord-sud; **2000 repliche**; generatore NumPy `default_rng`, seme **69 000 001**
  (non usato nel repository al 18 novembre; fuori dall'intervallo dei semi della validazione, 60 000 000 + 100 000·c + k con
  c < 90; il selftest lo confronta con l'elenco effettivo di tutti i semi della griglia). Repliche con matrice singolare:
  scartate e contate; se superano il 5 %, S1 è **«non determinato»**.
- Esiti di S1: «non determinato» se le repliche singolari superano il 5 %; altrimenti «instabile» se per qualche (e, h)
  l'intervallo esclude zero **e** |a_{e,h} − ā_h| > **2,4°**; altrimenti «stabile fra epoche».
  - 2,4° è il **10 % di γ₀ = 24°**: una soglia operativa, scelta come ordine di grandezza dell'effetto studiato. Non è la
    metà della pendenza proiettata dello scenario al 20 % (Δβ₂₀, §7), che è un'altra grandezza.
  - Il valore 2,107° della revisione 1 viene da un altro confronto (BARD-MDI) ed è abbandonato.
- Le differenze b_{e,h} si riportano senza criterio, insieme alla fonte DPD prevalente in ciascuna epoca (da
  `results/DPD_ACTIVITY_HOMOGENEITY/SOURCE_SHARE_BY_YEAR.csv`), per non attribuire a MWO uno scarto dovuto a un cambio di
  fonte di DPD (per esempio SOHO/MDI nel 2006–2007 e nel 2010, dentro E8).
- **Che cosa dice S1.** S1 è un controllo **relativo fra epoche**: dice se il coefficiente MWO, rispetto a quello in luce
  bianca, cambia da un'epoca all'altra oltre la soglia. Il modello stima un coefficiente costante per epoca e **non
  verifica derive dentro un'epoca**. Uno spostamento costante per epoca è comunque assorbito dai termini δ_{e,h} del
  modello principale. Le derive dentro le epoche sono un limite dichiarato; S2 ne controlla la parte che segue l'attività.

**S2. Scarto contro l'attività, con equivalenza.**
- Si stima per d_WL lo stesso modello principale del §3 (stessi termini di ciclo e di epoca) e la procedura M dà
  l'intervallo nominale 97,5 % della pendenza di attività dello scarto, β₃^WL.
- Margine **C = 0,5·|Δβ₂₀|**, dove Δβ₂₀ è il valore vero dell'effetto simulato al 20 % (§7), calcolato sul disegno del
  sottoinsieme del controllo e sulla sua matrice a rango pieno X_r (riduzione del §3), con i pesi del controllo.
- Esiti, **in quest'ordine di precedenza**:
  1. **«scarto contenuto»** se l'intero intervallo cade in [−C, +C]. Se in più l'intervallo esclude zero, si registra
     separatamente «scarto contenuto, distinguibile da zero»: l'esito operativo resta «scarto contenuto»;
  2. altrimenti **«dipendente dall'attività»** se l'intervallo esclude zero;
  3. altrimenti **«stabilità non determinata»** (intervallo che contiene zero ma esce da [−C, +C] per mancanza di
     precisione).
- Solo «scarto contenuto» permette il verdetto su β₃.
- Un esito «dipendente dall'attività» non dice quale delle due misure dipenda dall'attività: lo si dichiara e non si
  corregge β₃ a posteriori.
- S2 si ripete per emisfero e con P1 su 2010–2012, entrambi descrittivi.

**S3. Accordo di Hale.** Frazione di polarità di testa concorde con il segno di Hale atteso, per epoca ed emisfero
(descrittivo: controllo del segno della calibrazione e degli errori grossolani).

**S4. Contaminazione e selezione.**
- Per terzile di attività: frazione dei gruppi esclusi per non isolamento, posizione media del giorno scelto nell'ordine
  dei candidati e |LCM| medio.
- d_WL nella sensibilità «tutti i record», per isolati e non isolati (descrittivo).

**Regola.** β₃ è riportato come **descrittivo**, senza verdetto e con la causa, se:
- S1 è «instabile» o «non determinato», oppure
- S2 non è «scarto contenuto», oppure
- le epoche non verificabili contengono più del **20 %** dei record isolati valutabili.

## 7. Validazione statistica sul disegno del catalogo lungo (tilt sigillati)

**Ordine e sigillo.** Il runner misura tutti i record e scrive:
- `DESIGN.csv`: date, CR, emisfero, λ̄, Φ_MWO, area DPD, attività, ciclo, epoca, classe di risoluzione, isolamento, posizione
  nell'ordine dei candidati, |LCM| e cause; nessun tilt e nessun segno di polarità;
- `SEALED.csv.gz`: tilt, polarità di testa, baricentri.

`SEALED` si conserva in Git con il suo SHA-256 e **non si legge** finché la validazione non è stata conservata, ricontata
e letta. Gli script di validazione aprono solo `DESIGN.csv`; un test verifica che non aprano `SEALED`.

**Generatore.** È quello di P2f, sul disegno MWO (record isolati valutabili, matrice del modello principale con i termini
di epoca):
- rumore individuale **15°** (scala di P2f);
- componente temporale per cella (CR, emisfero) con deviazione standard **7,5°** (rapporto 0,5 come in P2f) e le forme P2f.

**Un solo tipo di effetto: la rampa di attività** dello scenario prescritto della fase A e della bozza DPD:
- Δγ_i = −e·γ₀·clip((Ā_c − q₅)/(q₉₅ − q₅), 0, 1)·sin|λ̄_i|, con γ₀ = 24°, Ā_c l'attività media della cella del record e q₅, q₉₅
  i quantili 5 % e 95 % di Ā_c sul disegno;
- e = 0,1 e 0,2 (riduzione massima del 10 % e del 20 % del coefficiente);
- **valore vero** Δβ_e = g·Δγ, con g la riga di β₃ della soluzione WLS (X_r'WX_r)⁻¹X_r'W, dove X_r è la **matrice a rango
  pieno** ottenuta dalla matrice completa MWO (termini di epoca inclusi) con la riduzione del §3 (come `target` nella fase
  A). Sulla matrice originale con colonne ridondanti (X'WX)⁻¹ non esiste; la riduzione non cambia lo spazio delle colonne e
  quindi β₃. Anche C (§6) e la stima di β₃ usano X_r;
- copertura e coda di esclusione si misurano rispetto a Δβ_e, mai rispetto a −e·γ₀;
- non si simula una pendenza lineare −0,2·γ₀ per unità di attività, che è un altro bersaglio;
- Δβ₂₀ è anche la base del margine C di S2.

**Criteri.** Sono quelli di P2f (`docs/PROTOCOL_P2F_VALIDATED_TEST.md` §5), sugli scenari 0, 1, 2, 7, 9:
- **sotto nulla**, 10 000 cataloghi per scenario: in ogni scenario falsi verdetti ≤ 3,0 %, ciascun verso ≤ 1,75 %, `errore` ≤ 1 %;
- **sotto effetto**, scenari 1, 2, 7, 9 × e = 0,1 e 0,2, con 2000 cataloghi per combinazione: copertura ≥ 96,5 % e coda di
  esclusione ≤ 2,0 % rispetto a Δβ_e; potenza riportata senza criterio;
- **completezza** come in `scripts/hmi_followups.py`: numero esatto di cataloghi, indici e semi attesi, nessun duplicato;
- semi nuovi: 60 000 000 + 100 000·configurazione + replica (base 60 000 000 non usata da nessuno script del progetto al
  18 novembre); il seme di S1 (69 000 001) è fuori da questo insieme, e il selftest lo verifica sull'elenco effettivo.

**Sensibilità del rumore (senza effetto sul verdetto).** Sono 2000 cataloghi per scenario sotto nulla con rumore
individuale 25°. Sono riportati senza criterio e **non** servono a sostenere il verdetto, che si appoggia solo alla
validazione a 15°. Motivo: non c'è una fonte verificata che fissi la dispersione intrinseca dei tilt magnetici MWO. La
mediana di disaccordo del pilota (4,4°) misura la differenza fra due misure, non la dispersione delle regioni.

**Esecuzione.**
- Il benchmark sul pool reale precede la griglia; i processi sono 5.
- **Nessun limite di durata** (decisione dell'utente); il calcolo gira staccato.
- Totale 50 000 + 16 000 + 10 000 = 76 000 unità.

**Se la validazione a 15° fallisce,** β₃ è descrittivo: intervallo nominale con avvertenza, nessun verdetto.

## 8. Esiti possibili

| Condizione | Esito |
|---|---|
| copertura del §2 non raggiunta | non concludente (solo cause e conteggi) |
| β₃ non identificabile (§3) | non concludente |
| validazione a 15° fallita | β₃ descrittivo |
| S1 «instabile» o «non determinato», S2 non «scarto contenuto», o epoche non verificabili > 20 % | β₃ descrittivo, con la causa |
| tutto superato | `supportato` (estremo superiore < 0), `opposto` (estremo inferiore > 0) o `non deciso`; intervallo sempre riportato come limite, sulla scala di Δβ_e («una riduzione oltre il X % sulla rampa è esclusa, nei soli scenari validati») |

Lettura accanto a HMI:
- si riportano entrambi gli intervalli, anche come effetto fra i quantili 5–95 % dell'attività di ciascun disegno;
- popolazioni diverse (§1);
- i due campioni si sovrappongono nel 2010–2012, e la sensibilità del §3 li separa.

## 9. Esecuzione e ordine

1. Revisione di Codex della revisione 3. Le fonti (Ulrich et al. 2002 §2; Győri et al. 2017) e il controllo descrittivo
   dell'attività DPD (§3) sono già stati fatti e registrati.
2. Congelamento.
3. Download di `sDPD` con SHA-256.
4. Misura del catalogo (runner + riconteggio indipendente della misura, come per il pilota), con i tilt sigillati.
5. Identificabilità di β₃, riduzione delle colonne ridondanti, calcolo di Δβ_e e di C sul disegno.
6. Validazione, conservazione, riconteggio e lettura.
7. Apertura del sigillo, calcolo dei tilt in luce bianca, controlli S1–S4, conservazione.
8. Stima di β₃ una sola volta.
9. Riconteggio indipendente e rapporto.

## 10. Questioni risolte dalle revisioni di Codex

Revisione 2 (precisazioni prima del congelamento):

| # | Questione | Decisione |
|---|---|---|
| 1 | Fusione delle epoche | sostituita dalla verifica dell'identificabilità di β₃; colonne ridondanti eliminate senza cambiare lo spazio delle colonne; β₃ non identificabile → non concludente |
| 2 | S1 | controllo relativo fra epoche, senza pretese sulle derive interne; 2,4° = 10 % di γ₀; bootstrap a blocchi di 6 CR, 2000 repliche, seme 69 000 001 (corretto dopo la revisione della revisione 3: 61 000 001 coincideva con un seme della griglia) |
| 3 | S2 | precedenza: «scarto contenuto» prima di «dipendente»; «distinguibile da zero» registrato a parte; copertura e perdite del sottoinsieme con tilt DPD |
| 4 | Attività | sensibilità (a) Gyula/Debrecen, (b) SILSO emisferico, (c) SILSO totale ripartito con DPD, fissate ora; il controllo di omogeneità resta descrittivo |
| 5 | Cicli | la validazione è condizionata alle assegnazioni; resta la sensibilità ±1 anno dai minimi |

Revisione 1:

| # | Questione | Decisione |
|---|---|---|
| 1 | Isolamento | principale, applicato ai giorni candidati; tutti i record come sensibilità; popolazione dichiarata |
| 2 | Termini di epoca | principali, come spostamenti del coefficiente di Joy; controllo del rango; forma additiva e modello senza epoche come sensibilità |
| 3 | S1/S2 | S1 per emisfero sui coefficienti; S2 con equivalenza C = 0,5·\|Δβ₂₀\| e stato «stabilità non determinata» |
| 4 | Scelta del magnetogramma | classe di risoluzione su due dimensioni, poi vicinanza temporale |
| 5 | Rumore | 15° con scala temporale 7,5°; 25° solo come sensibilità senza effetto sul verdetto |

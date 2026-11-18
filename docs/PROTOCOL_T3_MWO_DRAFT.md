# T3 sul catalogo magnetico Mount Wilson 1974–2012 — bozza di protocollo

**BOZZA NON CONGELATA, 18 novembre 2026 (Claude), revisione 2 dopo la revisione di Codex della revisione 1 (`38b81a5`).**
Modifiche rispetto alla revisione 1:
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
- i conteggi dei gruppi DPD con magnetogramma MWO lo stesso giorno (§2), da posizioni DPD e date degli header.

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
- La sua omogeneità **va verificata**: DPD usa immagini di più osservatori, e la documentazione segnala differenze nelle
  misure delle aree fra fonti (Győri et al. 2017).
- Prima del congelamento, sulla sola serie di attività (nessun tilt), si fa un controllo descrittivo:
  - rapporto fra l'area DPD e il numero di macchie SILSO totale per anno, 1974–2012;
  - confronto con SILSO emisferico 1992–2012;
  - i cambi di fonte di DPD documentati, segnati sul grafico.
- Se il rapporto mostra salti in corrispondenza dei cambi di fonte, lo si dichiara e si aggiunge come sensibilità
  l'attività da SILSO totale ripartita per emisfero con le aree DPD.
- SILSO emisferico copre solo dal 1992: è una sensibilità per 1992–2012.
- Le unità sono diverse da quelle di HMI: il confronto si fa sull'effetto fra il 5° e il 95° quantile di attività di cella.

**Cicli.**
- Il ciclo dipende dalla data, con minimi 1976-03, 1986-09, 1996-08 e 2008-12, come nella bozza DPD.
- Non c'è separazione per latitudine nelle sovrapposizioni: è un'approssimazione dichiarata, inclusa nella validazione.
- Sensibilità: esclusione dei record entro ±1 anno da ciascun minimo.

**Modello principale.**
- γ_i = Σ_{c,h} k_{c,h}·sin|λ̄_i| + Σ_{(e,h) ≠ riferimento} δ_{e,h}·sin|λ̄_i| + β₃·(A_i − 1)·sin|λ̄_i|.
- Gli intercetti ciclo × emisfero (k) sono quelli di T3 su HMI, costruiti solo per le coppie (ciclo, emisfero) presenti
  nel campione.
- δ_{e,h} sono **spostamenti del coefficiente di Joy** per epoca strumentale × emisfero (§4), costruiti solo per le coppie
  presenti, con l'epoca più numerosa come riferimento in ciascun emisfero.
- Pesi: Φ_MWO, l'analogo di Φ in P1. Parametro: β₃, in gradi per unità di attività.
- **Identificabilità:**
  - la matrice pesata deve avere rango pieno (come `_finish` della fase A);
  - si riportano le colonne eliminate perché vuote e il numero di condizionamento;
  - un'epoca contenuta interamente in un solo ciclo resta identificabile solo se quel ciclo copre anche altre epoche;
  - se il rango è difettivo, si fondono le epoche secondo una regola fissa: l'epoca con meno record si unisce alla vicina
    nel tempo con la stessa classe di risoluzione prevalente, e la fusione è registrata;
  - il controllo si fa sul disegno, prima della validazione.

**Sensibilità senza verdetto.**
- Forma **additiva** dello scarto di epoca: δ'_{e,h} come intercetti senza sin|λ̄|, cioè uno scarto costante del tilt.
- Modello senza termini di epoca (forma esatta di T3 su HMI).
- Pesi = area DPD.
- Tutti i record (§2).
- Solo record in R1.
- Solo record al primo giorno candidato.
- Esclusione dei record dal 2010-05 (sovrapposti al campione HMI di T3).
- Attività SILSO emisferica 1992–2012.

## 4. Epoche strumentali

**Dai metadati.** L'inventario degli header registra per ogni magnetogramma:
- MRKMOD, l'hardware secondo il commento dell'header: 0 = datex, 256 = ael, 1280–1283 = fm, 1284 = 24ch;
- la famiglia dei file, DXB/DYB_OBS, PSEPMA e BSCALE.

MRKMOD è assente nei file moderni. Proposta di confini (Fe I, 1974–2012):

| Epoca | Indicatore dagli header | Dal | Al | Magnetogrammi | Giorni |
|---|---|---|---|---|---|
| E1 datex | MRKMOD 0 | 1974-01-02 | 1974-07-09 | 128 | 119 |
| E2 ael | MRKMOD 256 | 1974-07-11 (prime prove 1974-04-18) | 1981-12-08 | 1412 | 1295 |
| E3 fm-0 | MRKMOD 1280 | 1982-01-03 | 1984-09-08 | 799 | 652 |
| E4 fm-1 | MRKMOD 1281 | 1984-09-06 | 1989-04-11 | 10 262 | 1252 |
| E5 fm-2 | MRKMOD 1282 | 1989-04-11 | 1993-09-23 | 10 188 | 1221 |
| E6 fm-3 | MRKMOD 1283 | 1993-09-22 | 1994-12-30 | 4034 | 362 |
| E7 moderna, prima | file `*fe1*`, PSEPMA circa 66–69 | 1995-03-25 | 1996-04-08 | 305 | 305 |
| E8 moderna, dopo | file `*fe1*`, PSEPMA circa 77–78 | 1996-04-13 | 2012-12-07 | 3810 | 3590 |

Note sulla tabella:
- **Correzione rispetto alla revisione 1.** MRKMOD 1283 appartiene a fm (1280–1283), non a 24ch: E6 è rinominata.
- **Divisione di E7.** Ulrich et al. (2002, §2) descrivono l'avvio del sistema a 24 canali nel 1996. Negli header, nei file
  moderni:
  - PSEPMA salta da circa 66,8 a circa 77,8 fra il 1996-04-08 e il 1996-04-13;
  - BSCALE passa da 0,1 a 0,05 il 1996-07-05.

  Il confine proposto è il salto di PSEPMA; il cambio di BSCALE resta un sotto-periodo descrittivo (scala di
  memorizzazione). **Da riconciliare prima del congelamento** con la data esatta in Ulrich et al. 2002: se la fonte indica
  un'altra data, il confine si sposta lì e il salto di PSEPMA diventa un sotto-periodo registrato.
- Nel 1984-09 → 1994 ci sono circa 10 scansioni al giorno in R2 e R1; la regola del §2 sceglie R1 dove esiste (R1 è
  presente in circa 1195 dei 1252 giorni di E4, 1089 su 1221 di E5 e 319 su 362 di E6).
- I giorni di transizione con due valori di MRKMOD si assegnano per magnetogramma.

**Dalla documentazione.** Prima del congelamento si leggono le date dei cambi strumentali in Ulrich et al. 2002 e nelle
altre fonti dell'osservatorio, e si registrano accanto alla tabella. Una data documentata che non coincide con un cambio
di header si aggiunge come confine: le date documentate possono solo dividere un'epoca, mai fonderne due (salvo la
regola di identificabilità del §3).

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

**S1. Stabilità fra epoche, per emisfero, in unità di coefficiente di Joy.**
- Modello per d_WL: d_WL = Σ_{e,h} a_{e,h}·sin|λ̄| + Σ_{e,h} b_{e,h} + errore, pesi Φ_MWO.
  - a_{e,h} è lo scarto di coefficiente di Joy fra MWO e luce bianca per epoca ed emisfero;
  - b_{e,h} è lo scarto additivo.
- Usare i coefficienti invece delle mediane del tilt evita che la diversa distribuzione delle latitudini fra epoche
  produca differenze di tilt mediano a parità di coefficiente.
- Per ogni epoca verificabile ed emisfero si calcola a_{e,h} − ā_h (ā_h media pesata sulle epoche), con intervallo
  bootstrap a blocchi di CR al 95 %.
- Esito «instabile» se per qualche (e, h) l'intervallo esclude zero **e** |a_{e,h} − ā_h| > **0,1·γ₀ = 2,4°**.
  - È una soglia operativa, pari alla metà dell'effetto simulato più grande, e non deriva da questo confronto.
  - Il valore 2,107° della revisione 1 viene da un altro confronto (BARD-MDI) ed è abbandonato.
- Le differenze b_{e,h} e gli scarti di DPD in corrispondenza dei suoi cambi di fonte si riportano senza criterio.
- **Rilevanza per β₃.** Uno spostamento costante del coefficiente per epoca è già assorbito dai termini δ_{e,h} del modello
  principale. S1 serve a verificare che dentro ogni epoca la scala sia stabile e che i termini δ bastino; un esito
  «instabile» indica che la scala MWO cambia in modo non descritto dalle epoche.

**S2. Scarto contro l'attività, con equivalenza.**
- Si stima per d_WL lo stesso modello principale del §3 (stessi termini di ciclo e di epoca) e la procedura M dà
  l'intervallo nominale 97,5 % della pendenza di attività dello scarto, β₃^WL.
- Margine **C = 0,5·|Δβ₂₀|**, dove Δβ₂₀ è il valore vero dell'effetto simulato al 20 % (§7), calcolato sul disegno e sulla
  matrice MWO con i pesi del controllo.
- Esiti:
  - **«scarto contenuto»** se l'intero intervallo cade in [−C, +C];
  - **«dipendente dall'attività»** se l'intervallo esclude zero;
  - **«stabilità non determinata»** in tutti gli altri casi, cioè intervallo che contiene zero ma esce da [−C, +C] per mancanza
    di precisione.
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
- S1 è «instabile», oppure
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
- **valore vero** Δβ_e = g·Δγ, con g la riga di β₃ della soluzione WLS (X'WX)⁻¹X'W sulla **matrice completa MWO**, termini di
  epoca inclusi (come `target` nella fase A);
- copertura e coda di esclusione si misurano rispetto a Δβ_e, mai rispetto a −e·γ₀;
- non si simula una pendenza lineare −0,2·γ₀ per unità di attività, che è un altro bersaglio;
- Δβ₂₀ è anche la base del margine C di S2.

**Criteri.** Sono quelli di P2f (`docs/PROTOCOL_P2F_VALIDATED_TEST.md` §5), sugli scenari 0, 1, 2, 7, 9:
- **sotto nulla**, 10 000 cataloghi per scenario: in ogni scenario falsi verdetti ≤ 3,0 %, ciascun verso ≤ 1,75 %, `errore` ≤ 1 %;
- **sotto effetto**, scenari 1, 2, 7, 9 × e = 0,1 e 0,2, con 2000 cataloghi per combinazione: copertura ≥ 96,5 % e coda di
  esclusione ≤ 2,0 % rispetto a Δβ_e; potenza riportata senza criterio;
- **completezza** come in `scripts/hmi_followups.py`: numero esatto di cataloghi, indici e semi attesi, nessun duplicato;
- semi nuovi, disgiunti da tutti quelli usati e registrati.

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
| rango difettivo anche dopo la regola di fusione | non concludente |
| validazione a 15° fallita | β₃ descrittivo |
| S1 instabile, S2 non «scarto contenuto», o epoche non verificabili > 20 % | β₃ descrittivo, con la causa |
| tutto superato | `supportato` (estremo superiore < 0), `opposto` (estremo inferiore > 0) o `non deciso`; intervallo sempre riportato come limite, sulla scala di Δβ_e («una riduzione oltre il X % sulla rampa è esclusa, nei soli scenari validati») |

Lettura accanto a HMI:
- si riportano entrambi gli intervalli, anche come effetto fra i quantili 5–95 % dell'attività di ciascun disegno;
- popolazioni diverse (§1);
- i due campioni si sovrappongono nel 2010–2012, e la sensibilità del §3 li separa.

## 9. Esecuzione e ordine

1. Revisione di Codex della revisione 2.
2. Lettura delle fonti documentali sulle epoche (Ulrich et al. 2002 per MWO; Baranyi et al. 2016 e Győri et al. 2017 per
   DPD) e loro registrazione.
3. Controllo descrittivo di omogeneità della serie di attività DPD (§3).
4. Congelamento.
5. Download di `sDPD` con SHA-256.
6. Misura del catalogo (runner + riconteggio indipendente della misura, come per il pilota), con i tilt sigillati.
7. Controllo del rango e calcolo di Δβ_e e di C sul disegno.
8. Validazione, conservazione, riconteggio e lettura.
9. Apertura del sigillo, calcolo dei tilt in luce bianca, controlli S1–S4, conservazione.
10. Stima di β₃ una sola volta.
11. Riconteggio indipendente e rapporto.

## 10. Questioni risolte dalla revisione di Codex (revisione 1)

| # | Questione | Decisione |
|---|---|---|
| 1 | Isolamento | principale, applicato ai giorni candidati; tutti i record come sensibilità; popolazione dichiarata |
| 2 | Termini di epoca | principali, come spostamenti del coefficiente di Joy; controllo del rango; forma additiva e modello senza epoche come sensibilità |
| 3 | S1/S2 | S1 per emisfero sui coefficienti; S2 con equivalenza C = 0,5·\|Δβ₂₀\| e stato «stabilità non determinata» |
| 4 | Scelta del magnetogramma | classe di risoluzione su due dimensioni, poi vicinanza temporale |
| 5 | Rumore | 15° con scala temporale 7,5°; 25° solo come sensibilità senza effetto sul verdetto |

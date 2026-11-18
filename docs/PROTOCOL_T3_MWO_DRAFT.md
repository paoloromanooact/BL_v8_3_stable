# T3 sul catalogo magnetico Mount Wilson 1974–2012 — bozza di protocollo

**BOZZA NON CONGELATA, 18 novembre 2026 (Claude, revisione 1). Da rivedere con Codex prima del congelamento.**
Nessun tilt MWO fuori dal pilota è stato calcolato, e nessun tilt DPD in luce bianca è stato calcolato o letto.
Per scrivere il testo sono stati usati solo metadati:
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

## 1. Domanda e prodotto principale

Il coefficiente di Joy delle regioni bipolari dipende dall'attività emisferica **dentro** il ciclo, nei cicli 21–23
(più le code dei cicli 20 e 24), misurato con la stessa grandezza di P1, cioè il tilt magnetico con le polarità?

- **Prodotto principale:** l'intervallo della pendenza T3, letto accanto a quello HMI.
- **Verdetto** (`supportato`, `opposto`, `non deciso`): solo se la validazione del §7 e i controlli di stabilità del §6 sono superati.
- **Fuori da questo protocollo:** la dipendenza fra cicli (forza del ciclo). È un'altra domanda.

## 2. Campione

**Periodo.** Date UT dal 1974-01-01 al 2012-12-31: i magnetogrammi MWO Fe I dell'archivio vanno fino al 2013-01 e i
gruppi DPD (`gDPD<anno>.txt`, già locali con SHA-256) coprono il periodo.

**Magnetogrammi.**
- Solo Fe I 5250,2 Å: famiglie `MP00_5250*` e `*fe1*`, riconosciute come nella pipeline MWO congelata. Na I è escluso.
- Mancano il 1979–1980 (archivi non utilizzabili) e il 1997 (nessun Fe I).
- Fra i magnetogrammi Fe I dello stesso giorno UT che superano i controlli di effemeridi della pipeline (|ΔCENLON| ≤ 18°, |ΔB0| ≤ 0,5°), si sceglie:
  1. quello con la **risoluzione d'osservazione più fine** (DYB_OBS minimo);
  2. a parità, quello con TAVG-UT più vicino all'ora DPD del gruppo.

  Motivo: dal 1984-09 al 1994 ci sono circa 10 scansioni al giorno, in parte a 13″×20″ e in parte a 9,5″×13″. La regola rende la
  risoluzione il più possibile omogenea fra le epoche, perché la scansione a 9,5″×13″ esiste in quasi tutti i giorni dal 1974-12
  (tabella del §4).

**Record.**
- Per ogni gruppo DPD (stringa NOAA, lettere comprese) si ordinano i giorni candidati per |LCM| crescente.
- Un giorno è candidato se ha una riga `g` DPD con area WS corretta ≥ 1, |λ| ≤ 45° e un magnetogramma MWO scelto come sopra.
- Il record è il primo giorno in cui la misura riesce, cioè con finestra nel dominio μ ≥ 0,8 e due polarità sopra soglia.
- L'ordine dipende solo dalla posizione e non dal tilt. Le cause di fallimento sono registrate.

**Misura.** È identica al pilota congelato:
- finestra |λ − λ_DPD| ≤ 6°, |L − L_DPD| ≤ 8°;
- B_r = B_LOS/μ, con 50 G ≤ |B_r| ≤ 4000 G;
- baricentri pesati con |B_r|/μ sulla sfera;
- convenzione di P1: la testa è la polarità più a ovest; γ = sign(λ̄)·asin(sin tilt), positivo se la testa è più vicina all'equatore;
- nessuna correzione di rotazione fra l'ora DPD e l'ora MWO dello stesso giorno, come nel pilota;
- lettore e geometria della pipeline congelata, incluso il float32 prima di BSCALE (diagnosi in `results/MWO_PILOT_FLUX_DIAGNOSIS/`).

  Grandezze salvate per record: latitudine media pesata col flusso (λ̄), flusso nella finestra Φ_MWO, segno della polarità
  di testa, segno di Hale atteso dal ciclo e distanza dei baricentri.

**Isolamento** (proposta). Un record è **isolato** se nessun altro gruppo DPD dello stesso giorno ha il centro dentro la sua finestra.
- Con l'attività cresce la probabilità che regioni vicine entrino nella finestra e spostino i baricentri. Questo è un errore di tilt che dipende proprio dall'attività, e quindi può distorcere T3 direttamente.
- **L'analisi principale usa i record isolati**; tutti i record sono una sensibilità.
- La frazione di record non isolati in funzione dell'attività è riportata.

**Conteggi dai soli metadati** (limite superiore, prima delle esclusioni di misura):
- 8802 gruppi con almeno un giorno candidato, su 445 rotazioni di Carrington; 7704 sono isolati nel giorno con |LCM| minimo.
- Per ciclo, nord/sud: 20 164/238; 21 1017/1184; 22 1205/1392; 23 1397/1528; 24 397/280.
- Nel pilota era valutabile il 79 % degli abbinati, ma il campione S di P1 ha regioni più grandi dei gruppi DPD: la frazione qui sarà minore.

**Copertura minima.** Lo studio è informativo solo se:
- ci sono almeno **3000** record isolati valutabili;
- ognuno dei cicli 21, 22 e 23 ne ha almeno **300 per emisfero**.

Altrimenti l'esito è «non concludente»: si riportano solo le cause e i conteggi.

## 3. Attività, cicli, modello

- **Attività principale.**
  - Area WS corretta dei gruppi DPD: somma giornaliera per emisfero, media mensile sui giorni osservati, normalizzata alla media 1974–2012.
  - La serie è omogenea su tutto il periodo e indipendente da MWO.
  - SILSO emisferico copre solo dal 1992, quindi è una sensibilità per 1992–2012.
  - Le unità sono diverse da quelle di HMI: il confronto si fa sull'effetto fra il 5° e il 95° quantile di attività di cella.
- **Cicli.**
  - Il ciclo dipende dalla data, con minimi 1976-03, 1986-09, 1996-08 e 2008-12, come nella bozza DPD.
  - Non c'è separazione per latitudine nelle sovrapposizioni: è un'approssimazione dichiarata, il cui effetto è nella validazione.
  - Sensibilità: esclusione dei record entro ±1 anno da ciascun minimo.
- **Modello principale.**
  - γ_i = Σ_{c,h} k_{c,h}·sin|λ̄_i| + Σ_{e≠E7,h} δ_{e,h}·sin|λ̄_i| + β₃·(A_i − 1)·sin|λ̄_i|.
  - Gli intercetti ciclo × emisfero sono quelli di T3 su HMI.
  - Gli spostamenti del coefficiente di Joy per **epoca strumentale × emisfero** (§4) assorbono salti di scala fra
    epoche, che non sono allineate ai cicli.
  - Pesi: Φ_MWO, l'analogo di Φ in P1. Celle (CR, emisfero) per la componente temporale.
  - Parametro: β₃, in gradi per unità di attività.
- **Sensibilità senza verdetto.**
  - Modello senza termini di epoca, cioè la forma esatta di T3 su HMI.
  - Pesi = area DPD.
  - Tutti i record, non solo gli isolati.
  - Esclusione dei record dal 2010-05, che si sovrappongono al campione HMI di T3.
  - Solo magnetogrammi a 9,5″×13″.

## 4. Epoche strumentali

**Dai metadati.** L'inventario degli header (`results/MWO_HEADER_INVENTORY/`) registra per ogni magnetogramma:
- MRKMOD, l'hardware secondo il commento dell'header: 0 = datex, 256 = ael, 1280–1283 = fm, 1284 = 24ch;
- la famiglia dei file, la risoluzione d'osservazione DXB/DYB_OBS, PSEPMA e BSCALE.

Epoche fissate qui, dai cambi di MRKMOD e di famiglia (Fe I, 1974–2012):

| Epoca | MRKMOD | Dal | Al | Magnetogrammi | Giorni | Risoluzione d'osservazione |
|---|---|---|---|---|---|---|
| E1 datex | 0 | 1974-01-02 | 1974-07-09 | 128 | 119 | 14″×17″ |
| E2 ael | 256 | 1974-07-11 (prime prove 1974-04-18) | 1981-12-08 | 1412 | 1295 | 9,5″×13″ dal 1974-12 (14″×17″ prima) |
| E3 fm | 1280 | 1982-01-03 | 1984-09-08 | 799 | 652 | 9,5″×13″ |
| E4 fm | 1281 | 1984-09-06 | 1989-04-11 | 10 262 | 1252 | dal 1986 circa 10 scansioni/giorno, 13″×20″ e 9,5″×13″ |
| E5 fm | 1282 | 1989-04-11 | 1993-09-23 | 10 188 | 1221 | come E4 |
| E6 24ch | 1283 | 1993-09-22 | 1994-12-30 | 4034 | 362 | come E4 |
| E7 moderna | assente | 1995-03-25 | 2012-12-07 | 4115 | 3895 | 9,5″×13″ (379 a 13″×20″) |

Note sulla tabella:
- PSEPMA (separazione delle porte, in mÅ) è 0 fino al 1981, circa 82–85 in E3–E6 e circa 77,6 in E7.
- BSCALE vale 0,05 dal 1996-07-05 al 2007-12-21, con brevi ritorni a 0,1 nel 2007. È una scala di memorizzazione, non un
  cambio di strumento: si riporta come sotto-periodo descrittivo, non come epoca.
- I giorni di transizione con due valori di MRKMOD si assegnano per magnetogramma.

**Dalla documentazione.** Ulrich et al. (2002, ApJS 139, 259) descrivono la storia del magnetografo MWO. Prima del
congelamento vanno lette le date dei cambi riportate lì e in altre fonti dell'osservatorio, e confrontate con la tabella.
Se una data documentata non coincide con un cambio di header, si aggiunge come confine: in quel caso un'epoca può
dividersi, mai fondersi. La tabella congelata sarà quella risultante.

**Epoche piccole.** Le epoche con meno di **50** record isolati valutabili per emisfero (probabilmente E1 ed E6)
restano nel modello con il loro termine δ, ma nei controlli del §6 si dichiarano «non verificabili».

## 5. Riferimenti disponibili per epoca

| Riferimento | Periodo | Epoche | Grandezza | Uso |
|---|---|---|---|---|
| DPD, tilt in luce bianca calcolati qui da `sDPD` (bozza DPD §3) | 1974–2012 | E1–E7 | tilt senza polarità; peso = area | controllo principale di stabilità e di dipendenza dall'attività (§6) |
| P1 (HMI) | 2010-05 → 2012-12 | E7 | tilt magnetico, stessa grandezza | già nel pilota; ripetuto sul catalogo (descrittivo) |
| MDI (SMARP), se l'utente decide il catalogo MDI descrittivo | 1996–2010 | E7 | tilt magnetico | descrittivo; facoltativo, non condizione |
| MWO stesso giorno, due risoluzioni | 1984-09 → 1994 | E4–E6 | stesso strumento, scansioni 13″×20″ contro 9,5″×13″ | effetto interno della risoluzione (descrittivo) |

- **Prima del 1996 l'unico riferimento esterno è DPD in luce bianca.** Anche DPD cambia fonti di osservazione nel tempo;
  le sue epoche vanno lette nella documentazione di Debrecen (Baranyi et al. 2016; Győri et al. 2017) e registrate
  prima del congelamento.
- Il tilt in luce bianca non ha polarità. Per i confronti si usano la differenza assiale e la convenzione di Joy, come per MDI–HMI.
- I file `sDPD` 1974–2012 si scaricano dopo il congelamento, con SHA-256.

## 6. Controlli di stabilità della misura (prima della lettura di β₃)

Si calcolano sui record isolati valutabili, con le differenze d_WL = γ_MWO − γ_WL (asse, convenzione di Joy) e i risultati
si conservano in Git prima che la stima di β₃ venga letta. Le soglie sono proposte, da fissare al congelamento.

**S1. Scarto per epoca.**
- Per ogni epoca verificabile: mediana di d_WL e la sua differenza dalla mediana complessiva, con intervallo bootstrap a blocchi di CR al 95 %.
- Esito «instabile» se in un'epoca la differenza supera **2,107°** e l'intervallo esclude zero.
- Si riporta anche il coefficiente di Joy MWO/WL per epoca (rapporto dei k stimati sullo stesso insieme).

**S2. Scarto contro l'attività.**
- Si stima lo stesso modello del §3 con d_WL al posto di γ, e la procedura M dà un intervallo nominale per la pendenza di attività dello scarto.
- Esito «dipendente dall'attività» se l'intervallo esclude zero.
- Si riporta anche la semilarghezza dell'intervallo, per dire quale distorsione resta compatibile.
- S2 si ripete per emisfero (descrittivo) e con P1 su 2010–2012 (descrittivo).

**S3. Accordo di Hale.** Frazione di polarità di testa concorde con il segno di Hale atteso, per epoca ed emisfero. È
descrittivo: è un controllo del segno della calibrazione e degli errori grossolani, non un criterio.

**S4. Contaminazione.** Frazione di record non isolati e d_WL degli isolati contro i non isolati, per terzile di
attività (descrittivo).

**Regola.**
- Se S1 dà «instabile» o S2 dà «dipendente dall'attività», β₃ è riportato come **descrittivo**, senza verdetto, con la causa.
- Un esito S2 «dipendente dall'attività» non dice quale delle due misure (MWO o luce bianca) dipenda dall'attività:
  lo si dichiara e non si corregge β₃ a posteriori.
- Le epoche non verificabili sono elencate; se contengono più del **20 %** dei record isolati valutabili, β₃ è descrittivo.

## 7. Validazione statistica sul disegno del catalogo lungo (tilt sigillati)

**Ordine e sigillo.** Il runner misura tutti i record e scrive:
- `DESIGN.csv`: date, CR, emisfero, λ̄, Φ_MWO, area DPD, attività, ciclo, epoca, isolamento, cause; nessun tilt e nessun segno di polarità;
- `SEALED.csv.gz`: tilt, polarità di testa, baricentri.

`SEALED` si conserva in Git con il suo SHA-256 e **non si legge** finché la validazione non è stata conservata, ricontata
e letta. Gli script di validazione aprono solo `DESIGN.csv`; un test verifica che non aprano `SEALED`.

**Generatore.** È quello di P2f, sul disegno MWO (record isolati valutabili, modello principale del §3):
- rumore individuale 15° (scala di P2f) e componente temporale per cella con le forme P2f;
- sensibilità a 25° (dispersione dei tilt in luce bianca secondo McClintock & Norton 2013).

**Criteri.** Sono quelli di P2f (`docs/PROTOCOL_P2F_VALIDATED_TEST.md` §5), sugli scenari 0, 1, 2, 7, 9 come per Q1/Q2:
- **sotto nulla**, 10 000 cataloghi per scenario a 15°: in ogni scenario falsi verdetti ≤ 3,0 %, ciascun verso ≤ 1,75 %, `errore` ≤ 1 %;
- **sotto effetto**, scenari 1, 2, 7, 9 × effetti −0,1·γ₀ e −0,2·γ₀ (scenario prescritto della bozza DPD: −e·24°·sin|λ| fra i quantili 5–95 % dell'attività di cella), 2000 cataloghi per combinazione: copertura ≥ 96,5 % e coda di esclusione ≤ 2,0 %; potenza riportata senza criterio;
- **a 25°**, 2000 cataloghi per scenario sotto nulla, con lo stesso criterio. Se la validazione passa a 15° e fallisce a 25°, il verdetto è emesso con questa avvertenza;
- **completezza** come in `scripts/hmi_followups.py`: numero esatto di cataloghi, indici e semi attesi, nessun duplicato;
- semi nuovi, disgiunti da tutti quelli usati e registrati.

**Esecuzione.**
- Il benchmark sul pool reale precede la griglia; i processi sono 5, il numero più veloce misurato su questa macchina.
- **Nessun limite di durata** (decisione dell'utente); il calcolo gira staccato.
- Totale 50 000 + 16 000 + 10 000 = 76 000 unità.

**Se la validazione a 15° fallisce,** β₃ è descrittivo: intervallo nominale con avvertenza, nessun verdetto.

## 8. Esiti possibili

| Condizione | Esito |
|---|---|
| copertura del §2 non raggiunta | non concludente (solo cause e conteggi) |
| validazione a 15° fallita | β₃ descrittivo |
| S1 instabile, S2 dipendente dall'attività o epoche non verificabili > 20 % | β₃ descrittivo, con la causa |
| tutto superato | `supportato` (estremo superiore < 0), `opposto` (estremo inferiore > 0) o `non deciso`; intervallo sempre riportato come limite («un effetto oltre X è escluso, nei soli scenari validati») |

Lettura accanto a HMI:
- si riportano entrambi gli intervalli, anche come effetto fra i quantili 5–95 % dell'attività di ciascun disegno;
- i due campioni si sovrappongono nel 2010–2012, e la sensibilità del §3 li separa.

## 9. Esecuzione e ordine

1. Revisione di Codex della bozza.
2. Lettura delle fonti documentali sulle epoche (MWO, DPD) e loro registrazione.
3. Congelamento.
4. Download di `sDPD` con SHA-256.
5. Misura del catalogo (runner + riconteggio indipendente della misura, come per il pilota), con i tilt sigillati.
6. Validazione sul disegno, conservazione, riconteggio e lettura.
7. Apertura del sigillo, controlli S1–S4, conservazione.
8. Stima di β₃ una sola volta.
9. Riconteggio indipendente e rapporto.

## 10. Questioni aperte per la revisione

1. Isolamento come analisi principale (§2), oppure come sensibilità con tutti i record come principale.
2. Termini di epoca nel modello principale (§3), oppure solo come sensibilità, mantenendo la forma esatta di HMI come principale.
3. Soglie di S1 (2,107°) e di S2 (intervallo che esclude zero), e regola del 20 % sulle epoche non verificabili. Con un
   intervallo largo, S2 può passare per mancanza di potenza: si potrebbe aggiungere una condizione di equivalenza
   (semilarghezza ≤ metà dell'effetto −0,2·γ₀).
4. Scelta del magnetogramma più fine nel giorno (§2) contro quello più vicino all'ora DPD.
5. Rumore individuale del generatore: 15° come P2f, oppure una scala ricavata dal pilota (|d_ax| mediana 4,4° su P1).

# Pilota MDI — nota prospettica Q4: precisione attesa di T3 con un catalogo MDI 1996–2010

**BOZZA, revisione 1, 24 novembre 2026 (Claude). Non congelata, da rivedere con Codex.** È la nota prevista dal
protocollo congelato del pilota (`docs/PROTOCOL_MDI_TILT_PILOT.md` §7): si scrive dopo la lettura del pilota e
**prima di qualsiasi calcolo prospettico**. Per scriverla:
- nessun calcolo prospettico;
- nessuna simulazione;
- nessun dato nuovo.

I numeri citati sono risultati già conservati. Il congelamento di questa nota non autorizza i calcoli: l'avvio resta
una decisione dell'utente.

## 0. Obiettivo servito e decisione

- **Obiettivo servito:** il secondo del progetto, il quenching del tilt con l'attività (T3).
- **Decisione che informa:**
  - se costruire il catalogo MDI completo 1996–2010 per T3;
  - con quale prodotto (sinottico o full-disk).
- **Cosa aggiunge rispetto alla fase A del piano prospettico** (`docs/PROSPECTIVE_PHASE_A_RESULTS.md`). Lì MDI (E2)
  era un disegno sintetico: celle HMI ricampionate con l'attività del 1996–2010, resa f e rumore k come griglie
  esplorative. Qui il disegno è quello reale:
  - i 5401 gruppi DPD eleggibili del pilota;
  - con le rese misurate per prodotto;
  - con i flussi MDI misurati;
  - con scenari di errore di misura ancorati, come scale e non come stime, ai confronti del pilota.
- **Non serve all'obiettivo 1** (sorgente BL). La differenza di scala del flusso con MWO resta aperta e richiede una
  specifica propria. Q4 usa i flussi MDI solo come pesi della regressione T3.

## 1. Informazioni già note (nota non cieca)

**Risultati T3:**
- HMI: −3,59° per unità di attività, intervallo nominale 97,5 % [−10,58°, +3,41°], non deciso.
- MWO 1974–2012: −4,93° [−10,21°, +0,34°], descrittivo (S1 non determinato, S2 «stabilità non determinata»).

**Studi prospettici già fatti:**
- **Fase A e B del piano prospettico:**
  - bersaglio T3 dello scenario prescritto su E0 −1,603° per unità di attività (−0,0668·γ₀);
  - riconoscimento T3 dal 2,3 % al 4,35 %, anche con MDI sintetico;
  - alla scala P2f, il 66–83 % della varianza della pendenza viene dalla componente temporale.
- **Fattibilità DPD** (`docs/T3_LONG_CATALOGUE_FEASIBILITY_DRAFT.md` §8):
  - semilarghezza dell'intervallo nominale alla scala P2f 0,43–0,60·γ₀ per HMI E0;
  - 0,27–0,37·γ₀ per DPD 1996–2016 (0,36–0,44 con dispersione individuale 25°).

**Pilota, livello 1 (sinottiche):**
- resa proiettata 92,8 % a 50 G, 81,7 % a 100 G;
- fallimenti per mappe mancanti (CR 1938–1940, 1998), pixel mancanti, polarità;
- Q3 sinottica − MWO: mediana |d_ax| 8,5°, d_γ per terzile di attività non monotono;
- flusso MDI/MWO circa 14;
- fit esplorativo di M: φ = 0,29, κ = −0,98 al bordo, σ²ₓ = 16,7, dichiarato poco informativo.

**Pilota, livello 2 (full-disk):**
- resa A proiettata 47,0 %, M1 94,7 %, U 30,4 %;
- 20/90 gruppi fuori dominio μ, 9/90 senza magnetogramma;
- Q2: d_γ −0,6° (−1,0° a 100 G) con intervalli nominali che escludono zero, mediana |d_ax| 1,4°;
- per terzile di attività, d_γ −0,5 / −0,8 / −1,2° (descrittivo);
- A − B: mediana |d_ax| 0,7° a 1,6–3,2 h;
- fd − MWO e sinottica − MWO sugli stessi 49 gruppi: 6,8° e 7,1°.

**Letteratura:** deviazione standard dei tilt 29–31° in tutti i cicli ed emisferi (McClintock & Norton 2013, verificato
in lettura primaria il 18 novembre).

## 2. Domanda

Con gli stimatori già studiati, e sotto ipotesi dichiarate sul rumore, sulla resa e sugli scarti, quale precisione
attesa avrebbe la pendenza β₃ di T3 misurata con la procedura del pilota sui gruppi DPD 1996–2010:
- da sola;
- insieme al campione HMI di T3;
- per ciascuno dei due prodotti MDI?

Lo stimatore è la pendenza WLS di T3 sui record, nel riferimento normale a varianza nota. La valutazione:
- è analitica e condizionata ai disegni generati;
- non valida la procedura M sui disegni MDI;
- non dice quanto il Sole renderebbe osservabile.

## 3. Disegni

**Base comune: la popolazione eleggibile del pilota** (`results/MDI_PILOT_SELECTION/POPULATION.csv`, 5401 gruppi,
1996-05-01 → 2010-10-31).
- Ogni gruppo ha un solo record, al giorno scelto dal pilota, con:
  - latitudine DPD;
  - data t_DPD e rotazione di Carrington;
  - area DPD, classi di attività e area, coorte.
- **Rese.** Un gruppo entra nel disegno con probabilità pari alla resa del suo strato (punto 4). Le rotazioni senza
  mappa sinottica (CR 1938–1940) escludono **in modo deterministico** i loro gruppi dal disegno sinottico. Nella
  resa dello strato non si conta quindi la causa «mappa mancante» di quelle rotazioni, per non contarla due volte.

| Codice | Disegno | Resa | Pesi Φ |
|---|---|---|---|
| H | HMI E0, il campione S di T3 (2485 record, CR 2096–2316) | — | flussi P1 |
| MS | MDI sinottico, popolazione 1996-05 → 2010-04 | per cella × coorte, dal livello 1 | flussi sinottici (punto 5) |
| MF | MDI full-disk con la geometria congelata, stesso periodo | per coorte, dal livello 2 (regola A1) | come MS (punto 5) |
| MS+H | MS ∪ H | come sopra | come sopra |
| MF+H | MF ∪ H | come sopra | come sopra |

1. **Periodo MDI nei disegni:** 1996-05 → 2010-04. I gruppi dopo il 2010-04-30 si escludono anche da MS e MF da soli,
   per avere lo stesso disegno MDI con o senza HMI. CR 2096 appartiene solo a H, come nell'emendamento A1 della
   fase A. Si riporta il numero dei gruppi esclusi.
2. **Attività:**
   - principale: serie SILSO emisferica, normalizzata alla media HMI 2010-05 → 2026-09, con la stessa funzione mensile
     della fase A (`monthly_activity`). Così l'unità di attività è la stessa di HMI;
   - sensibilità: A_main del pilota (aree DPD), con la sua normalizzazione.
3. **Cicli:**
   - ciclo del tempo con i minimi della fase A (m₂₃ = 1996-08, m₂₄ = 2008-12);
   - per MDI i cicli presenti sono la coda del 22, il 23 e l'inizio del 24;
   - nessuna separazione per latitudine, approssimazione dichiarata come in T3 su MWO.
4. **Rese per strato e propagazione dell'incertezza:**
   - **MS:**
     - strato = cella (attività × emisfero × area) × coorte, dai conteggi di `Q1_YIELD_CELLS.csv` (n e riusciti a 50 G;
       a 100 G per la soglia di sensibilità);
     - con le rotazioni prive di mappa escluse dal disegno, dal conteggio dello strato si tolgono le misure fallite
       per «mappa mancante» in quelle rotazioni.
   - **MF:**
     - strato = coorte (M1, U), dai conteggi della regola A1 per l'immagine A (49/54 e 12/36);
     - sensibilità: strato = coorte × classe di area, con l'unione qui sotto quando una combinazione ha meno di
       5 gruppi.
   - **Incertezza:** per ogni realizzazione del disegno la resa di ciascuno strato si estrae da Beta(r + ½, n − r + ½),
       con r riusciti su n. L'incertezza campionaria della resa si propaga così sulle realizzazioni.
   - **Strati senza dati** (n = 0), unione in ordine fisso:
     1. stessa coorte e stessa attività, classe di area adiacente inferiore, poi superiore;
     2. poi attività adiacente inferiore, poi superiore;
     3. poi tutte le celle della stessa coorte.
     - Gli emisferi si uniscono solo all'ultimo passo.
     - Le unioni si registrano.
   - **Disponibilità full-disk nei periodi non inventariati.** Il pilota ha inventariato i metadati full-disk solo per
     i giorni dei 90 gruppi di livello 2.
     - Principale: la frazione «nessun magnetogramma ammissibile» del pilota (9/90), già inclusa nella resa di MF,
       vale per tutto il periodo.
     - Sensibilità dichiarate, non stime: disponibilità ridotta di un fattore 0,8 e 0,6 negli anni senza gruppi
       di livello 2 riusciti nel pilota.
5. **Flussi (pesi Φ), con la relazione con area, latitudine e attività:**
   - Per ogni gruppo del disegno, Φ_i = area_i × r_i. Il rapporto r_i = Φ/area si estrae dai gruppi del campione di
     livello 1 misurati con successo nello stesso strato (attività × area × emisfero), con unione come al punto 4.
   - Così il flusso conserva:
     - l'area del gruppo;
     - la dipendenza osservata del rapporto flusso/area da attività, area ed emisfero.
     - La latitudine entra attraverso lo strato di attività e l'emisfero; non si modella oltre, limite dichiarato.
   - **MF** usa gli stessi Φ di MS: il rapporto fd/sinottica di Q2 (mediana 0,87, 10°–90° percentile 0,65–0,96) cambia
     poco i pesi relativi dentro MDI. Sensibilità: Φ_MF = Φ_MS / ρ, con ρ estratto dai rapporti sin/fd di Q2.
   - **Disegni combinati:** la scala relativa dei pesi MDI e HMI non è calibrata. Principale: Φ MDI come misurato;
     sensibilità con i Φ MDI moltiplicati per 0,5 e per 2.
6. **Realizzazioni:**
   - 20 per disegno e configurazione di resa e flusso;
   - semi in una zona nuova, da registrare al congelamento e da verificare disgiunta da quelle già usate;
   - si riportano mediana, minimo e massimo delle grandezze del §6.

## 4. Modello e bersaglio

- **Matrice T3** della fase A (`t3_design`):
  - intercetti ciclo × emisfero moltiplicati per sin|λ|;
  - colonna x₃ = (A_i − 1)·sin|λ_i|;
  - pesi Φ_i.
  - Il coefficiente d'interesse si identifica per nome di colonna.
- **Identificabilità:** come in T3 su MWO (§3), β₃ è identificabile se rango([Z, x₃]) = rango(Z) + 1. Le colonne
  ridondanti di Z si eliminano nell'ordine fisso degli intercetti.
- **Modelli dei disegni combinati:**
  - (a) comune;
  - (b) protetto, famiglie J e A come nella fase A (§4 del piano prospettico), con lo stesso significato di β: per J
    la pendenza HMI, per A il coefficiente comune dopo il controllo degli scarti additivi.
- **Bersaglio** (A0 della fase A):
  - proiezione WLS della rampa Δγ_i = −δ(Ā_c)·24°·sin|λ_i| sulla matrice del disegno;
  - δ_max = 0,20 (secondario 0,10);
  - quantili 5–95 % e normalizzazione HMI fissi (principale); quantili ricalcolati sul disegno come sensibilità.

## 5. Rumore e scarti

Il protocollo del pilota (§7) chiede di fissare qui σ²ₓ, κ e la definizione di σ_e.

**Rumore individuale del tilt:** σ_e² = σ_int² + σ_m².
- **σ_int, dispersione intrinseca delle regioni:**
  - 15° principale (scala P2f, come fase A e T3 su MWO);
  - 25° e 30° come sensibilità (30° ≈ McClintock & Norton 2013).
  - Si applica a MDI e a HMI.
- **σ_m, errore di misura MDI:** {0; 2°; 10°}. Il pilota non misura l'errore di misura: questi valori sono **scale**,
  non stime.
  - 2° ≈ scala robusta delle differenze Q2 sinottica − full-disk (mediana |d_ax| 1,43°/0,6745). La ripetibilità
    A − B (0,72°/0,6745 ≈ 1,1°) è più piccola, ma combina evoluzione ed errori correlati e non diventa un errore
    di misura.
  - 10° ≈ scala robusta delle differenze fd − MWO sugli stessi gruppi (6,77°/0,6745), attribuita **interamente** a
    MDI come inviluppo superiore. Comprende anche MWO e circa 8 h di evoluzione.
  - Code pesanti (coppie oltre 45°) non rappresentate: il riferimento è normale, limite dichiarato.
  - Per HMI σ_m = 0, come nella fase A: l'errore di misura HMI è implicito nella scala P2f.

**Componente temporale per cella (CR, emisfero):**
- σ_x = 7,5° × {0,5; 1; 2};
- forme e correlazione fra emisferi κ:
  - AR(1) φ = 0,5, κ = 0;
  - AR(1) φ = 0,9, κ = 0;
  - salti di 20 CR, come nella fase A;
  - sensibilità con i generatori P2f 3 (φ = 0,9, κ = −0,8) e 4 (φ = 0,5, κ = +0,6).
- Stessa ampiezza per i due strumenti: è la stessa componente solare.
- Il fit esplorativo del pilota (φ = 0,29, κ = −0,98 al bordo, σ²ₓ = 16,7) non si usa come scenario. Il protocollo lo
  dichiara poco informativo per costruzione, e κ è al bordo.

**Scarti (distorsione, non precisione):**
- **Disegni combinati:** famiglie A e J della fase A, con limiti C ∈ {0,25; 0,5} nelle unità del bersaglio e
  tolleranza, cioè lo scarto di attività che sposta β di metà del bersaglio.
- **MDI da solo:** la sola tolleranza a una deriva interna con l'attività. Senza termini di epoca MDI: la stabilità
  interna di MDI non è verificata (limite).
- **Scarto fra prodotti, descrittivo e non cieco:** la distorsione m prodotta su MS da uno scarto per terzile di
  attività uguale alle mediane osservate di d_γ di Q2 (−0,53, −0,79, −1,19° a 50 G; −0,58, −1,29, −1,34° a 100 G).
  - Serve solo a dire se differenze fra prodotti dell'ordine osservato sarebbero piccole o grandi rispetto al
    bersaglio.
  - Gli intervalli di quei terzili contengono zero: non è uno scarto dimostrato.

## 6. Calcolo e prodotti

**Solo analitico**, con le formule A0 e A1 della fase A per T3:
- Var(β̂) = Σ a_i²σ_{e,i}² + σ_x²·bᵀKb, con a la riga WLS dei record e b_c = Σ_{i∈c} a_i;
- livello 97,5 %, z = 2,2414.

**Per disegno, modello, rumore, resa e flusso:**
- record, celle, rotazioni e gruppi esclusi;
- bersaglio Δβ (° per unità di attività e in γ₀);
- SE; semilarghezza h = z·SE in γ₀; rapporto h/h_H;
- SE/|Δβ|;
- frequenza di riconoscimento dello scenario;
- quota temporale della varianza;
- tolleranza e distorsioni.

**Prova di riproduzione prima della corsa:** H riproduce bersaglio e SE di E0 della fase A (−1,60265°; SE entro 1e-12
relativo). Se la prova fallisce, la corsa si ferma con errore tecnico.

## 7. Lettura e uso per la decisione

Proposta da fissare al congelamento, prima dei calcoli. Riferimento: alla scala P2f (σ_int = 15°, σ_x = 7,5°), per
le tre forme temporali principali, modello (a), scarti nulli, mediana sulle realizzazioni.

**Contributo di MDI a T3 (disegno MS+H rispetto a H):**
- **«utile come limite»** se h(MS+H) ≤ 0,7·h(H) per tutte e tre le forme e resta ≤ 0,8·h(H) con σ_int = 30° e
  σ_m = 10°;
- **«marginale»** se non è utile, ma h(MS+H) ≤ 0,9·h(H) per tutte e tre le forme;
- **«nessun contributo apprezzabile»** altrimenti.

**Replica indipendente:** MS da solo con h(MS) ≤ h(H) si registra come «replica su un altro ciclo con precisione
almeno pari». È descrittivo e non sostituisce il raccordo.

**Prodotto:**
- MF si considera solo se h(MF+H) ≤ 1,1·h(MS+H). Altrimenti la perdita di resa del full-disk costa troppa precisione.
- La scelta finale considera anche la distorsione fra prodotti (§5), che Q4 descrive ma non risolve.

**Valori che non possono reggere la decisione:**
- **Riconoscimento dello scenario prescritto:** si riporta senza criterio. La fase A lo dà basso con qualunque
  estensione, e l'uso realistico è un intervallo più stretto, non il riconoscimento.
- **Modello protetto (b) e scarti:** si riportano accanto, senza criterio, perché il giudizio sul raccordo MDI–HMI
  resti esplicito. Un «utile come limite» del modello (a) presuppone scarti fra strumenti non dipendenti
  dall'attività, non ancora verificati.

**La decisione resta dell'utente con Codex.** Q4 non produce un verdetto su T3 e non stima β₃.

## 8. Condizioni di non calcolabilità

- β₃ non identificabile in un disegno: quel disegno è «non calcolabile», con le colonne responsabili.
- Uno strato senza dati che resta tale dopo tutte le unioni del §3: il disegno è «non calcolabile», con lo strato.
- Mesi senza attività SILSO: i record si escludono e si contano. Oltre il 5 % dei record, il disegno è segnalato.
- Prova di riproduzione di E0 fallita: arresto tecnico, nessun prodotto.
- Meno di 3 cicli × emisfero con almeno 50 record in MS: il disegno MDI da solo è «non calcolabile» come replica
  (resta nei combinati).

## 9. Che cosa non fa

- Non scarica dati e non misura tilt.
- Non valida la procedura M sui disegni MDI: le frequenze sono nel riferimento normale a varianza nota.
- Non stima l'errore di misura MDI né la sua dipendenza dall'attività.
- Non tratta BARD-MDI, che resta un controllo esterno separato, da anticipare solo se Q4 risulta sensibile a
  un'ipotesi che quel confronto può sostenere.
- Non tratta la serie BL combinata né la sorgente BL.
- Non riapre T3 su HMI o su MWO.

## 10. Codice e sequenza

**Codice:**
- Lo script nuovo riusa, importandole senza modificarle, le funzioni già rivedute della fase A
  (`scripts/prospective_phase_a.py`: `t3_design`, `t3_var`, `t3_delta_gamma`, `bias_bases`, `freqs`,
  `monthly_activity`, calendario) e il generatore della covarianza temporale P2f (`k_true` di `python/sharpbl/diag_t5_oracle.py`, già usato dalla fase A).
- Le parti nuove sono:
  - il disegno dalla popolazione;
  - le rese per strato con estrazione Beta;
  - i flussi per strato;
  - le unioni.
- Selftest con:
  - la riproduzione di E0;
  - strati vuoti e unioni;
  - controllo che nessun tilt MDI venga letto. Il disegno usa solo POPULATION, i conteggi delle rese e i flussi e le
    aree dei gruppi misurati.

**Input, con SHA-256 registrati negli output:**
- `POPULATION.csv`, `SAMPLE.csv`;
- `Q1_YIELD_CELLS.csv`, `L1_RECORDS.csv` (solo flussi e aree);
- `YIELD_A1.csv` e coppie Q2 (solo rapporti di flusso);
- il campione S di HMI e la serie SILSO della fase A.

**Sequenza:**
1. revisione di questa bozza;
2. congelamento (SHA in un file FREEZE);
3. codice e selftest, revisione;
4. corsa unica;
5. conservazione prima della lettura;
6. riconteggio indipendente;
7. rapporto descrittivo;
8. decisione dell'utente.

## 11. Punti aperti per la revisione

1. Le soglie del §7 (0,7, 0,8, 0,9 e 1,1) sono una proposta: vanno fissate o cambiate prima del congelamento.
2. Le scale di σ_m (2° e 10°) sono ancorate a quantità che non sono errori di misura: è accettabile come inviluppo
   dichiarato?
3. Le rese di MF hanno solo due strati (coorte), da 90 gruppi: basta, o serve dichiarare MF solo indicativo?
4. La scala relativa dei pesi MDI/HMI (sensibilità 0,5 e 2): è sufficiente, o conviene una normalizzazione per
   strumento come scelta principale?
5. Lo scarto fra prodotti del §5 usa le mediane di Q2 per terzile, che sono note: va tenuto come descrizione o tolto?

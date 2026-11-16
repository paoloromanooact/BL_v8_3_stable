# Quanta informazione in più servirebbe? Piano prospettico per T5 e T3 — bozza

**BOZZA NON CONGELATA, revisione 1 — 2026-11-16.** Da rivedere con Codex **prima di qualunque calcolo**. Nessun
calcolo prospettico, nessuna simulazione e nessun dato MDI usati per scriverla; i numeri del §2 sono descrittori del
disegno HMI già esistente o risultati già conservati. **Non cieco**: risultati T3, validazione P2f, T5-D1/D2 e
sensibilità della potenza sono noti.

## 0. Portata

La valutazione è **condizionata agli stimatori studiati**: la pendenza WLS di T5 sulle celle (procedura M e il suo
riferimento a varianza nota O) e la pendenza WLS di T3 sui record. Non valida T5 né T3, non applica nulla ai dati
reali, non stima il beneficio di stimatori diversi. Serve a una sola decisione: se un'estensione dei dati possa
rendere distinguibile lo scenario prescritto, e quale, prima di investire su MDI o su un metodo HMI diverso.
MDI operativo e studio morfologico di S restano in pausa.

## 1. Domanda

Sotto ipotesi esplicite sul rumore e sugli scarti fra strumenti, **quante osservazioni solari aggiuntive**
(anni, rotazioni di Carrington, regioni) servirebbero perché la riduzione prescritta del 20 % della componente di
Joy sia riconosciuta con una frequenza utile, e quanto un mancato riconoscimento diventerebbe informativo? Con
risposte **separate per T5 e per T3**. Le repliche Monte Carlo non sono osservazioni: servono solo a stimare con
precisione la potenza di un disegno dato.

## 2. Elementi fissati

**Scenario prescritto** (dalla [nota del proxy](T5_PROXY_SENSITIVITY_NOTE.md), invariato): γ' = γ − δ(Â)·24°·sin|λ|,
con δ che sale linearmente da 0 al quantile 5 % a δ_max al quantile 95 % dell'attività di cella replicata sui
record T5. Principale
δ_max = 0,20 («riduzione del 20 %»); secondario δ_max = 0,10.

**Bersagli.**
- T5: Δβ = −3,669·10⁻²⁶ G/Mx = **−0,1031·η̄ per unità di Â** per δ_max = 0,20 (e −0,0515·η̄ per 0,10), dagli output
  conservati (`results/T5_PROXY_SENSITIVITY/SUMMARY.csv`, `39c010c`). Non −0,2·η̄.
- T3: la pendenza del coefficiente di Joy prodotta dallo stesso scenario non è ancora stata calcolata. È il **primo
  passo** del §5 (A0): proiezione WLS di −δ(Â)·24° sulla colonna (Â − 1) del modello T3, con i pesi e il disegno
  T3, deterministica e senza rumore. Si riporterà accanto al bersaglio storico della griglia T3 (−0,2·γ₀).
- Quando il disegno cambia, i bersagli si ricalcolano sul disegno esteso con la stessa regola e gli stessi quantili
  definiti sulla serie estesa; si riportano anche i valori con i quantili HMI, per separare l'effetto della rampa.

**Livello**: intervallo nominale 97,5 %, un verso all'1,25 %, come in P2f. Normalizzazione dell'attività: quella
HMI (media 2010-05 → 2026-09), mantenuta fissa sull'estensione perché l'unità della pendenza non cambi.

**Disegno HMI di riferimento (E0)**, descrittori: CR 2096–2316 (221 rotazioni, 210 con record); T5 318 celle
(168 N, 150 S) in 176 rotazioni, 2375 record, 7,5 record per cella; T3 2485 record in 394 celle; deviazione
standard pesata dell'attività di cella 0,82. Dalla sensibilità della potenza già conservata: deviazione standard
di β̂_WLS di T5 sotto nulla 0,07–0,27·η̄ a seconda del rumore, 0,10–0,14·η̄ alla scala P2f.

## 3. Estensioni considerate

| Codice | Che cosa aggiunge | Ipotesi sull'attività |
|---|---|---|
| E0 | nulla (riferimento) | osservata |
| E1 | maturazione HMI: altri 5 anni (circa 67 rotazioni) | analoga alla fase discendente del ciclo 24, da SILSO; ipotesi, non previsione |
| E2 | MDI, copertura **nominale** 1996-01 → 2010-10 (circa 199 rotazioni), meno la lacuna 1998-06/10 (circa 5 rotazioni) e meno le rotazioni del 2010 già coperte da HMI | SILSO emisferico osservato del ciclo 23 e della coda del 24 |
| E3 | E1 + E2 | come sopra |
| E4 | come E2, con raccordo fra strumenti perfetto | riferimento ottimistico, non uno scenario realistico |

**Regioni per cella aggiuntive.** Per HMI (E1) si usa la relazione osservata fra numero di record per cella e
attività nel disegno E0. Per MDI (E2) la stessa relazione moltiplicata per un **fattore di resa** f ∈ {0,5; 0,75;
1}: la risoluzione e il rumore MDI fanno superare la selezione a meno regioni, in misura non ancora nota. Flusso Φ
per record dalla distribuzione condizionata all'attività del disegno E0. Celle con almeno 3 regioni, come oggi.
Sono ipotesi dichiarate: l'inventario MDI, quando ripartirà, potrà sostituirle con i conteggi reali.

## 4. Ipotesi sul rumore e sugli scarti fra strumenti

**Rumore temporale**: le stesse 3 forme × 3 scale della sensibilità della potenza (AR(1) φ = 0,5 e 0,9, salti di
20 CR; scale 0,5, 1, 2 della scala P2f), applicate anche ai dati aggiunti, con la stessa ampiezza per entrambi gli
strumenti in assenza di informazione migliore. **Rumore individuale**: η̄ per record HMI come in P2f; per i record
MDI inflazionato di un fattore k ∈ {1; 1,5; 2}, perché il rumore dei magnetogrammi MDI è 2,6–4,2 volte quello HMI
per pixel e il suo effetto sul tilt e su D* non è noto. Per T3 gli analoghi in gradi del generatore P2f.

**Scarti fra strumenti** (il punto critico: uno scarto può imitare o mascherare il quenching). Termine additivo
sulle risposte dei soli record MDI:

  s(t, Â) = c₀ + c₁·(Â − 1) + c₂·(t − t_ref)/T,

con c₀ costante, c₁ dipendente dall'attività (per esempio una risposta di scala diversa nei campi forti, più
frequenti ad alta attività), c₂ deriva temporale. Conseguenze con il modello attuale:
- c₀ è assorbito dagli intercetti del ciclo 23, **ma non nel ciclo 24**, osservato da MDI fino a ottobre 2010 e poi
  da HMI: lì produce uno spostamento non assorbito;
- c₁ entra direttamente nella pendenza come distorsione;
- c₂ si confonde in parte con l'attività, che varia nel tempo.

La sovrapposizione del 2010 cade vicino al minimo: non permette di misurare c₁. I valori degli scarti non si
stimano qui: si esplorano per **griglia**, c₁ ∈ {0; ±0,25; ±0,5} × |bersaglio|, c₂ analogamente su tutto il
periodo MDI, c₀ ∈ {0; ±0,5} × la deviazione standard degli intercetti stimati in E0. Due analisi per ciascuna
estensione MDI:
- **(a) modello attuale** con intercetti ciclo × emisfero (più un intercetto separato per la parte MDI del ciclo
  24): riporta distorsione e potenza in funzione degli scarti;
- **(b) modello protetto** con un termine strumento × attività: assorbe c₁ ma usa i dati MDI soprattutto per la
  loro pendenza interna. Riporta quanto beneficio resta.
Si riporta inoltre la **tolleranza**: il |c₁| che sposta la pendenza di metà del bersaglio. Se la tolleranza è
più piccola di ciò che un confronto nella sovrapposizione potrebbe verificare, il beneficio di (a) non è
utilizzabile senza (b).

## 5. Valutazione: prima analitica, poi solo le simulazioni necessarie

**A0. Bersagli.** T3 sul disegno E0, poi T5 e T3 su ogni disegno esteso (§2). Deterministico.

**A1. Precisione analitica della WLS.** Per un disegno dato e un rumore noto, la varianza della pendenza WLS è
quella del riferimento O: σ_x²·bᵀKb + Σ g_c² v_c, con K la covarianza temporale vera e v_c la varianza di cella.
Si costruiscono disegni sintetici estesi con le ipotesi del §3 (attività da SILSO, celle e pesi) e si calcola la
varianza senza Monte Carlo. La sensibilità della potenza ha mostrato che con O la potenza osservata è vicina
all'approssimazione normale Φ(|Δβ|/SE − 2,24): la si usa come stima orientativa, sapendo che nei salti e con la
varianza stimata di M può scostarsi. La distorsione dagli scarti è g·s, anch'essa analitica. Per i disegni sintetici
che dipendono da estrazioni (Φ, numero di regioni) si usano 20 realizzazioni con semi nuovi e si riporta la
dispersione; non sono repliche di rumore.

**Prodotti di A1**, per T5 e T3 separatamente, per ogni estensione, rumore, f, k e scarto: SE/|bersaglio|;
frequenza di riconoscimento approssimata; distorsione/|bersaglio|; numero di rotazioni o di anni aggiuntivi (per
estrapolazione dentro la famiglia E1/E2) per arrivare all'obiettivo del §6.

**B. Simulazioni, solo dove servono.** Con M (varianza stimata, forma vera del rumore) su disegni estesi sintetici,
1000 cataloghi per configurazione, solo per le combinazioni in cui A1 dà una frequenza di riconoscimento fra il
30 % e il 70 % alla scala P2f, o in cui l'approssimazione normale è dubbia (salti). Nessuna simulazione dove A1 dà
meno del 20 % in tutte le ipotesi plausibili, o più del 90 %. Semi da un intervallo nuovo e disgiunto (proposta
34 000 000–34 999 999), verificato contro tutti quelli già usati. Le durate si stimano dopo aver fissato il disegno,
con un benchmark come in A1 del piano di potenza.

## 6. Significato dell'obiettivo del 50 %

Obiettivo **operativo**, non una garanzia: un'estensione è «potenzialmente sufficiente» per uno scenario se, alla
scala di rumore P2f e con falsi verdetti nominali, la riduzione del 20 % è riconosciuta almeno metà delle volte.
Con il 50 % un mancato riconoscimento resta poco informativo: lo scenario e l'assenza di effetto restano entrambi
plausibili. Per questo si riporta anche la quantità complementare: la frequenza con cui, **in assenza di effetto**,
l'intervallo esclude la riduzione del 20 % (l'estremo inferiore sopra il bersaglio). Solo quando anche questa è
alta un esito «non deciso» diventa un'indicazione contro lo scenario. Il 50 % è motivato come soglia minima per
giustificare l'investimento; la scelta finale resta dell'utente con Codex, alla luce di entrambe le frequenze.

## 7. T5 e T3: benefici distinti

- **T5** usa le celle e l'efficienza η = ΣD*/ΣΦ. Con MDI richiede un D* da campo LOS (Br ≈ B_LOS/μ), la cui
  confrontabilità non è verificata; il rumore MDI pesa sulla misura del dipolo. Partenza bassa: alla scala P2f
  riconoscimento 8–11 % in E0.
- **T3** usa i record e il tilt dai centroidi, meno direttamente legato all'ampiezza del campo ma influenzato dalla
  risoluzione e dalla morfologia; il suo bersaglio per lo stesso scenario si calcola in A0. Partenza: potenza della
  validazione P2f del 4,6–11,1 % a −0,2·γ₀.
- I due test hanno scarti strumentali di natura diversa (in G/Mx per T5, in gradi per T3): le griglie del §4 si
  definiscono separatamente, in unità del rispettivo bersaglio.
- Un'estensione insufficiente per T5 può essere utile per T3, e viceversa; né l'una né l'altra esclude il valore
  descrittivo di una serie MDI.

## 8. Che cosa non fa

Nessun dato MDI, nessuna verifica della confrontabilità reale, nessun nuovo stimatore, nessuna decisione
automatica. Le estensioni E1–E4 sono ipotesi di disegno; i risultati diranno «sotto queste ipotesi, con la WLS
studiata», non quanto il Sole renderebbe osservabile.

## 9. Punti aperti per la revisione

1. Griglie degli scarti c₀, c₁, c₂: ampiezze e forma (lineare in Â, o legata alla frazione di campo forte).
2. Fattore di resa f e inflazione k: valori plausibili prima dell'inventario MDI.
3. Ipotesi di attività per E1 (fase discendente del ciclo 24 come analogo).
4. Soglie di avvio delle simulazioni B (30–70 %, meno del 20 %, più del 90 %).
5. Se includere già in A1 il modello protetto (b) per T3, o solo per T5.
6. Se il bersaglio va ricalcolato con i quantili della serie estesa o mantenuto con quelli HMI (proposta:
   riportarli entrambi, decidere quale sia principale prima dei calcoli).

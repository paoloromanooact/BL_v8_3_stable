# Piano prospettico, fase A: risultati

**2026-11-18. Analitico, descrittivo, non cieco.** Piano `docs/PROSPECTIVE_INFORMATION_PLAN.md` (congelato in
`71c7d17`, SHA-256 `c92be19b…`), emendamento A1 `docs/PROSPECTIVE_INFORMATION_PLAN_A1.md` (`551d829`, SHA-256
`61c766eb…`, calendario delle estensioni, registrato prima della corsa dopo la revisione di Codex). Script
`scripts/prospective_phase_a.py` (`ecf0714`), selftest 40/40 con le prove di riproduzione del §9. Corsa unica sul
commit `6f4b416` (stesso script; il commit aggiunge solo l'handoff di Codex), 327 s, esito «eseguita». Output in
`results/PROSPECTIVE_PHASE_A/`, conservati **prima della lettura** in `56a5944`. Controllo indipendente
`scripts/prospective_phase_a_check.py`: **10/10**, ricevuta in `results/PROSPECTIVE_PHASE_A_CHECK/RECEIPT.json`.
Riconteggio scientifico indipendente (richiesto da Codex dopo la sua verifica degli hash e dei selftest 40/40):
`scripts/prospective_phase_a_recount.py`, che non importa lo script della fase A, ricostruisce dal registro dei
posti E0 e le 60 realizzazioni di E1, E2 ed E3 con f = 1 (calendario, trasferimento del ciclo, celle, matrici,
bersaglio del proxy e covarianza scritti a parte) e confronta bersagli e SE del modello (a), k = 1, AR(1) 0,5 e
salti alla scala P2f: **244 righe su 244 concordi**, scarto relativo massimo 4·10⁻¹⁵ (ricevuta in
`results/PROSPECTIVE_PHASE_A_RECOUNT/RECEIPT.json`). Il documento è stato scritto dopo il controllo 10/10 e prima
di questo riconteggio, che non cambia nessun numero.

Valutazione **condizionata agli stimatori studiati** (pendenza WLS di T5 sulle celle e di T3 sui record, con varianza
nota nel riferimento normale) e ai disegni generati: copie ricampionate di celle HMI con attività di altri periodi
(piano §8). Le frequenze dicono «sotto queste ipotesi, con la WLS studiata», non quanto il Sole renderebbe osservabile.
Nessun dato MDI, nessuna simulazione di cataloghi, nessuna applicazione ai dati reali.

## 1. Bersagli (A0)

| Test | Bersaglio su E0, δ_max = 0,20 | δ_max = 0,10 | Nota |
|---|---|---|---|
| T5 | −3,669·10⁻²⁶ G/Mx = **−0,1031·η̄** | −0,0515·η̄ | riprodotto da `39c010c` |
| T3 | **−1,6026° per unità di attività = −0,0668·γ₀** | −0,8013° | calcolato per la prima volta; confermato da Codex con una WLS separata |

Il bersaglio T3 dello scenario prescritto è **circa tre volte più piccolo** del −0,2·γ₀ della griglia storica: la
potenza del 4,6–11,1 % della validazione P2f si riferiva a un effetto più grande di quello qui prescritto.
Sui disegni estesi i bersagli sono ricalcolati per disegno e matrice; con il modello (b) restano quelli di E0.

## 2. Disegni generati

20 realizzazioni per estensione e resa f. Mediane: E1 aggiunge 134 posti (41 vuoti, 254 record); E2 368 posti
(184 CR × 2, 74 vuoti, 1213 record sulla mediana delle tre rese); E3 502 posti. Nessun record scartato per ciclo
< 22. Strati: terzili comuni 0,483 e 1,287; su 24 strati richiesti, 20 propri, 3 uniti al terzile inferiore,
1 a tutte le classi dell'emisfero (`STRATA_MERGES.csv`). I posti di E1 hanno poche regioni per posto (finestra
analoga sul declino del ciclo 24).

## 3. Frequenza di riconoscimento dello scenario (A1)

Riconoscimento = verdetto `supportato` sotto lo scenario prescritto (δ_max = 0,20), mediana [min–max] sulle 20
realizzazioni; scala di rumore P2f, modello (a), nessuno scarto fra strumenti. Obiettivo operativo del §6: 50 %.

| Disegno | T5, AR(1) 0,5 | T5, AR(1) 0,9 | T5, salti 20 CR | T3, AR(1) 0,5 |
|---|---|---|---|---|
| E0 (HMI attuale) | 10,7 % | 7,2 % | 6,6 % | 2,9 % |
| E1 (HMI + 5 anni) | 11,4 % | 7,6 % | 6,9 % | 3,0 % |
| E2, f = 1, k = 1 | 18,4 % [16,3–19,6] | 11,3 % | 10,1 % | 4,3 % |
| E2, f = 0,75, k = 1,5 | 14,7 % [12,9–16,2] | 9,9 % | 8,9 % | 3,8 % |
| E3, f = 1, k = 1 | 19,2 % [17,2–22,2] | 11,5 % | 10,3 % | 4,3 % |
| E3, f = 0,75, k = 1,5 | 15,7 % [13,7–17,5] | 10,3 % | 9,3 % | 3,9 % |
| E4 (= E2 senza scarti) | 18,4 % | 11,3 % | 10,1 % | 4,3 % |

Il valore di E0 per T5 coincide con il riferimento O dello studio di potenza (SE uguali entro 7·10⁻¹⁶).

- **Nessuna estensione è «potenzialmente sufficiente»** nel senso del §6. Nelle condizioni del criterio (scala P2f,
  modello (a), scarto nullo) il massimo delle mediane è 19,2 % per T5 e 4,35 % per T3.
- **Fuori da quelle condizioni.** Con il rumore temporale dimezzato e scarto nullo T5 arriva al 38,5 % su E3 (43,8 %
  nella realizzazione migliore). Includendo gli scarti strumentali della griglia si trova anche 55,3 % (E3, rumore
  dimezzato, c₀ = −0,1, c₁ = −0,5, c₂ = +0,25), ma lì i falsi `supportato` sotto nulla salgono dall'1,25 % al 3,44 %:
  è il caso in cui lo scarto fra strumenti imita una parte del segnale, non un guadagno di informazione.
- **T3 è rilevato raramente nei disegni studiati**: alla scala P2f, nelle configurazioni a scarto nullo del modello
  (a), il riconoscimento del bersaglio del 20 % (−1,603° per unità di attività) va dal 2,3 % al 4,35 %; al più 6,6 %
  con rumore dimezzato. Il calcolo quantifica la difficoltà di rilevare quella pendenza rispetto alla sua
  incertezza; non permette di attribuirne la causa alla sola ampiezza del bersaglio. L'esito osservativo di T3
  resta «non deciso».
- **Con δ_max = 0,10** T5 arriva al 6,0 % su E3 (4,1 % su E0).
- **Modello protetto (b), due protezioni diverse.** Per T5 e T3-J il modello separa le pendenze dei due strumenti:
  aggiungendo il solo MDI la frequenza di T5 resta al valore HMI (10,7 % con AR(1) 0,5), perché l'informazione di
  MDI sulla pendenza è assorbita dal termine strumentale. Per T3-A il parametro resta una pendenza di Joy comune,
  corretta per uno scarto additivo del tilt: nella stessa configurazione, con resa completa e rumore individuale
  uguale (E2, f = 1, k = 1), si passa dal 2,94 % al 3,15 %. Il guadagno è piccolo. Il guadagno pieno di MDI del
  modello (a) presuppone un raccordo senza scarti dipendenti dall'attività.
- La frequenza con cui l'intervallo **esclude** la riduzione del 20 % sotto nulla coincide, senza scarti, con il
  riconoscimento dell'alternativa simmetrica (per T5: 10,7 % su E0, 19,2 % su E3); non è una garanzia separata.

## 4. Scarti fra strumenti (modello (a), analisi di sensibilità (c))

Tolleranza: lo scarto di attività che sposta β di metà del bersaglio vale circa **1,35–1,43 unità** per T5 e
1,4–1,7 per T3 (unità del §4 del piano, cioè dell'ordine dell'effetto stesso). È uno scarto ipotetico: il suo
valore effettivo fra MDI e HMI resta da misurare. Nei casi peggiori entro C = 0,5
(E3, f = 0,75, k = 1,5, AR(1) 0,5 alla scala P2f): riconoscimento T5 dal 15,7 % al 11,0 %; falsi `supportato`
sotto nulla da 1,25 % a 2,1 %. Sull'intera griglia di scarti (costanti, attività, derive) il massimo dei falsi
`supportato` sotto nulla resta 2,3 % per T5 e 1,6 % per T3 in questa configurazione. Scarti dell'ordine
dell'effetto non creano molti falsi verdetti, ma lo scenario stesso resta poco riconoscibile.

## 5. Fase B

Dei 114 candidati (§5 B) **4 sono selezionati**, tutti T5 con modello (a) e coefficiente di scarto di attività
−0,5 (E2 ed E3). Per le realizzazioni selezionate le frequenze analitiche sono 11,8 % e 12,1 % con i salti, 20,4 % e
21,3 % con AR(1) 0,5. Nessun candidato T3 né del modello (b). La fase B verificherebbe come si comporta la
procedura M su questi casi, falsi verdetti compresi. **Quattro candidati selezionati, fase B rinviata**: la
priorità passa al confronto osservativo MDI–HMI; la decisione resta dell'utente con Codex.

## 6. Lettura

Con gli stimatori studiati, **né la maturazione di HMI né l'aggiunta di MDI 1996–2010 rendono distinguibile la
riduzione prescritta del 20 % della componente di Joy**: per T5 il riconoscimento passa da circa 1 volta su 10 a
circa 1 su 5 nel caso più favorevole; per T3 resta poche volte su 100. Il risultato T3 «non deciso» e lo stato
descrittivo di T5 non cambiano. Questo non dimostra che il quenching sia assente o irrilevante: dice che i dati
disponibili, con questi metodi, non bastano a riconoscerlo all'ampiezza prescritta. La fase A dice quanto si
guadagnerebbe se le misure fossero raccordabili; il confronto MDI–HMI affronta la domanda aperta, cioè quanto
cambiano tilt, flusso e dipolo misurando la stessa regione con i due strumenti. È un risultato osservativo utile
anche se T3 resta non deciso e T5 descrittivo.

**Bacino del confronto MDI–HMI** (certificato geometrico offline, riconteggio di Codex concorde su 2602 abbinamenti
su 2602): 1917 abbinamenti certificati fra istanti di osservazione, che corrispondono a 65 coppie distinte di
regioni; le componenti separate bastano per formare le 12 coppie previste. Solo 52 abbinamenti certificati hanno
QUALITY MDI = 0. Questo descrive il bacino disponibile; la composizione delle 12 coppie si conoscerà dopo la
selezione.

Limiti: disegni sintetici da celle HMI; rumore e scarti con le griglie esplorative del piano; frequenze nel
riferimento normale con varianza nota, il cui rapporto con una procedura a varianza stimata non è verificato qui
(sarebbe un oggetto della fase B); nessuno stimatore diverso dalla WLS.

## 7. Prodotti

`RAW.csv.gz` (30 294 righe: disegno × test/famiglia × modello × rumore × k), `FREQUENCIES.csv.gz` (mediana/min/max
sulle realizzazioni per ogni combinazione di scarti), `SENSITIVITY_C.csv`, `B_SELECTION.csv`, `DESIGNS.csv`,
`SLOTS.csv.gz`, `STRATA_E0.csv`, `STRATA_MERGES.csv`, `META.json` (hash di piano, emendamento, script, input e
prodotti).

# Piano prospettico, fase A: risultati

**2026-11-18. Analitico, descrittivo, non cieco.** Piano `docs/PROSPECTIVE_INFORMATION_PLAN.md` (congelato in
`71c7d17`, SHA-256 `c92be19b…`), emendamento A1 `docs/PROSPECTIVE_INFORMATION_PLAN_A1.md` (`551d829`, SHA-256
`61c766eb…`, calendario delle estensioni, registrato prima della corsa dopo la revisione di Codex). Script
`scripts/prospective_phase_a.py` (`ecf0714`), selftest 40/40 con le prove di riproduzione del §9. Corsa unica sul
commit `6f4b416` (stesso script; il commit aggiunge solo l'handoff di Codex), 327 s, esito «eseguita». Output in
`results/PROSPECTIVE_PHASE_A/`, conservati **prima della lettura** in `56a5944`. Controllo indipendente
`scripts/prospective_phase_a_check.py`: **10/10**, ricevuta in `results/PROSPECTIVE_PHASE_A_CHECK/RECEIPT.json`.

Valutazione **condizionata agli stimatori studiati** (pendenza WLS di T5 sulle celle e di T3 sui record, con varianza
nota nel riferimento normale) e ai disegni generati: copie ricampionate di celle HMI con attività di altri periodi
(piano §8). Le frequenze dicono «sotto queste ipotesi, con la WLS studiata», non quanto il Sole renderebbe osservabile.
Nessun dato MDI, nessuna simulazione di cataloghi, nessuna applicazione ai dati reali.

## 1. Bersagli (A0)

| Test | Bersaglio su E0, δ_max = 0,20 | δ_max = 0,10 | Nota |
|---|---|---|---|
| T5 | −3,669·10⁻²⁶ G/Mx = **−0,1031·η̄** | −0,0515·η̄ | riprodotto da `39c010c` |
| T3 | **−1,6026° per unità di attività = −0,0668·γ₀** | — | calcolato per la prima volta; confermato da Codex con una WLS separata |

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

- **Nessuna estensione è «potenzialmente sufficiente»** nel senso del §6. Il massimo su tutte le configurazioni è
  T5 su E3 con rumore temporale dimezzato: 38 % (mediana; 44 % nella realizzazione migliore).
- **T3 resta di fatto non riconoscibile**: 2–4 % alla scala P2f, al più 6,6 % con rumore dimezzato, vicino al
  livello dei falsi verdetti (1,25 %). La causa principale è l'ampiezza del bersaglio, non la quantità di dati.
- **Con δ_max = 0,10** T5 arriva al 6,0 % su E3 (4,1 % su E0).
- **Modello protetto (b)**: il termine strumentale assorbe l'informazione di MDI sulla pendenza; le frequenze
  tornano a quelle di E0 (T5 10,7 %) o poco sopra (T3-A 3,2 %). Il guadagno di MDI esiste solo se si assume un
  raccordo senza scarti dipendenti dall'attività.
- La frequenza con cui l'intervallo **esclude** la riduzione del 20 % sotto nulla coincide, senza scarti, con il
  riconoscimento dell'alternativa simmetrica (per T5: 10,7 % su E0, 19,2 % su E3); non è una garanzia separata.

## 4. Scarti fra strumenti (modello (a), analisi di sensibilità (c))

Tolleranza: lo scarto di attività che sposta β di metà del bersaglio vale circa **1,35–1,43 unità** per T5 e
1,4–1,7 per T3 (unità del §4 del piano, cioè dell'ordine dell'effetto stesso). Nei casi peggiori entro C = 0,5
(E3, f = 0,75, k = 1,5, AR(1) 0,5 alla scala P2f): riconoscimento T5 dal 15,7 % al 11,0 %; falsi `supportato`
sotto nulla da 1,25 % a 2,1 %. Sull'intera griglia di scarti (costanti, attività, derive) il massimo dei falsi
`supportato` sotto nulla resta 2,3 % per T5 e 1,6 % per T3 in questa configurazione. Scarti dell'ordine
dell'effetto non creano molti falsi verdetti, ma lo scenario stesso resta poco riconoscibile.

## 5. Fase B

Dei 114 candidati (§5 B) solo **4 cadono nelle bande**, tutti T5 con modello (a) e coefficiente di scarto −0,5
(E2 ed E3; AR(1) 0,5 e salti), con frequenza analitica 0,11–0,24. Nessun candidato T3 né del modello (b).
Le simulazioni con M verificherebbero l'approssimazione normale in casi con riconoscimento attorno al 20 %; non
potrebbero cambiare la conclusione del §3. Non avviate: la decisione è dell'utente con Codex.

## 6. Lettura

Con gli stimatori studiati, **né la maturazione di HMI né l'aggiunta di MDI 1996–2010 rendono distinguibile la
riduzione prescritta del 20 % della componente di Joy**: per T5 il riconoscimento passa da circa 1 volta su 10 a
circa 1 su 5 nel caso più favorevole; per T3 resta poche volte su 100. Il risultato T3 «non deciso» e lo stato
descrittivo di T5 non cambiano. Questo non dimostra che il quenching sia assente o irrilevante: dice che i dati
disponibili, con questi metodi, non bastano a riconoscerlo all'ampiezza prescritta. Il confronto MDI–HMI resta
utile come misura descrittiva della confrontabilità fra strumenti, non come strada verso un test del quenching.

Limiti: disegni sintetici da celle HMI; rumore e scarti con le griglie esplorative del piano; varianza nota
(riferimento normale), quindi frequenze ottimistiche rispetto a una procedura con varianza stimata; nessuno
stimatore diverso dalla WLS.

## 7. Prodotti

`RAW.csv.gz` (30 294 righe: disegno × test/famiglia × modello × rumore × k), `FREQUENCIES.csv.gz` (mediana/min/max
sulle realizzazioni per ogni combinazione di scarti), `SENSITIVITY_C.csv`, `B_SELECTION.csv`, `DESIGNS.csv`,
`SLOTS.csv.gz`, `STRATA_E0.csv`, `STRATA_MERGES.csv`, `META.json` (hash di piano, emendamento, script, input e
prodotti).

# T5-D2 — controlli oracolo sulla procedura M nello scenario a salti — bozza

**BOZZA NON CONGELATA — 2026-11-13.** Diagnostica, **non cieca** (T5-D1 e gli output della
validazione P2f sono già stati letti). Non cambia lo stato di T5 (descrittivo), non modifica la
procedura M, il protocollo P2f o i suoi output, e non usa risposte reali. Si congela con un commit
dopo la revisione; il codice si scrive dopo.

## 1. Domanda

In T5-D1, nello scenario 7 (salti ±1 su blocchi di 20 CR, indipendenti tra emisferi) la media di SE²
è il 14 % più piccola della varianza empirica della pendenza (R = 0,858), e la pendenza standardizzata
con la propria dispersione ha code più strette del normale, mentre il rapporto pendenza/SE le ha più
larghe. Indizio: l'eccesso di falsi verdetti viene dall'errore standard stimato, non da pendenze
estreme. **Quale componente della stima della varianza ne è responsabile: la funzione di varianza
individuale, il modello temporale AR(1) (sbagliato per costruzione in presenza di salti), o la loro
combinazione?**

## 2. La covarianza vera dei salti (perché l'oracolo non è «φ e κ veri»)

Nello scenario 7 non esistono parametri AR(1) veri. Il generatore (`p2f_validation.gen_x`, kind
`steps`) assegna a ogni CR t il livello del blocco ⌊(t + p)/L⌋, con fase p uniforme in {0, …, L−1}
estratta per catalogo e livelli ±1 indipendenti per blocco. Mediando sulla fase, la covarianza
incondizionata della componente per rotazione è, per ritardo τ in CR:

K_steps(τ) = max(0, 1 − |τ|/L),

con L = 20 nello scenario 7 e L = 13 nello scenario 10. Tra emisferi: 0 nello scenario 7 (livelli
indipendenti), K_steps(τ) nello scenario 10 (livelli comuni). La varianza della componente nella
risposta di cella T5 è σ_x² = (0,5·η̄)² = 3,1684·10⁻⁵⁰ (G/Mx)², come negli scenari AR(1).
La formula è esatta per la covarianza **marginale sulla fase** (quella rilevante per la varianza
incondizionata della pendenza); condizionatamente a una fase la covarianza è a gradini. La correttezza
della formula si verifica prima dell'esecuzione (§6, prova 2).

La varianza individuale vera nello scenario 7 (rumore normale omoschedastico) è σ_i² = η̄² per ogni
regione nella scala z_i = D*_i/Φ_i (generatore `responses`, c_i = 1).

## 3. Bracci (stessi cataloghi, appaiati)

Ogni braccio riusa **gli stessi cataloghi sintetici della validazione** (stessi semi
`p2f_validation.seed_null` e `seed_effect`, ricostruiti in modo deterministico), cambiando solo i
pezzi della varianza indicati. β̂ è identico in tutti i bracci (dipende solo dai dati).

| Braccio | Varianza individuale | Componente temporale | Scopo |
|---|---|---|---|
| A0 | stimata (funzione di varianza, A2) | stimata (REML AR(1)) | **riproduzione**: deve coincidere con `VALIDATION_RAW` (β̂, SE, intervallo, verdetto) |
| A1 | **vera** (σ_i² = η̄²) | stimata (REML AR(1) ristimata con la v vera) | effetto della sola componente individuale |
| A2 | stimata | **vera** (σ_x² K_steps, o AR(1) vero negli scenari di controllo) | effetto della sola componente temporale |
| A3 | vera | vera | controllo: la formula della varianza diventa esatta; atteso R ≈ 1 per costruzione |

Nessun braccio introduce nuovi numeri casuali: non servono semi nuovi. La riproduzione A0 è una porta:
se anche una sola riga non coincide entro la precisione fissata (§6), ci si ferma.

## 4. Scenari e numerosità

| Scenario | Ruolo | Cataloghi |
|---|---|---|
| 7, nulla | caso fallito (decisivo per questa diagnosi) | 10 000 (tutti) |
| 7, effetto −0,3·η̄ | combinazione fallita (copertura, coda inferiore) | 2000 (tutti) |
| 10, nulla | salti comuni tra emisferi (contrasto) | 10 000 (tutti) |
| 1 e 2, nulla | controlli AR(1), dove A2 usa i parametri AR(1) veri | 2000 ciascuno (k = 0…1999) |

Solo T5. Costo stimato: la REML (A0, A1) è la parte cara, circa 1 s per catalogo; circa 2 × 26 000
stime REML, 1–1,5 ore su 12 processi. A2 e A3 non richiedono ottimizzazione.

## 5. Grandezze e regole di lettura (fissate prima)

Per braccio e scenario: R = media(s²)/varianza empirica di r (come T5-D1), SD(z), quantili di z
all'1,25 % e al 98,75 %, falsi verdetti sui tentativi (sotto nulla), copertura e due code (sotto
effetto), errori Monte Carlo binomiali; confronto appaiato con A0 sugli stessi cataloghi (verdetti
cambiati nei due versi). Gli esiti `errore` restano nel denominatore come nel protocollo P2f.

Lettura, descrittiva, scritta prima di vedere i bracci:
- **A2 riporta R vicino a 1 e i falsi verdetti nel limite, A1 no** → la causa principale è il modello
  temporale AR(1) inadeguato ai salti. Candidate coerenti per un seguito (non decise qui): covarianza
  temporale più flessibile, oppure errore standard robusto alla dipendenza su una scala di circa 20 CR.
- **A1 sì, A2 no** → la causa è la funzione di varianza individuale. Candidate: forma della funzione di
  varianza o sua stima.
- **Né A1 né A2 da soli, A3 sì** → interazione tra le due stime.
- **Nemmeno A3** → la differenza viene dalla forma non gaussiana della distribuzione (livelli ±1): il
  riferimento normale per l'intervallo è inadeguato. Candidate: calibrazione del riferimento.
- I controlli 1 e 2 devono dare A0 ≈ A2 ≈ A3 (R vicino a 1): se no, si riporta e si interpreta con
  cautela.

«Vicino a 1» e «nel limite» sono letture descrittive con errore Monte Carlo, non criteri di
accettazione. **Nessuna correzione scelta qui**: qualunque procedura nuova per T5 richiede un
protocollo proprio, scritto prima, e una validazione nuova con semi nuovi e scenari fissati prima,
compreso lo scenario 7. Non si toglie lo scenario 7 e non si riscala SE con un fattore ricavato da
questi risultati.

## 6. Controlli prima dell'esecuzione

1. Prove sul codice con dati costruiti a mano: sostituzione dei pezzi della varianza, funzione
   K_steps, matrici simmetriche e semidefinite positive.
2. Verifica della covarianza dei salti: per L = 20 e L = 13, la covarianza empirica di `gen_x` su
   200 000 serie (semi 28 000 000 + k, disgiunti da tutti quelli usati) coincide con K_steps entro
   l'errore Monte Carlo atteso.
3. Riproduzione A0 su 50 cataloghi dello scenario 7 rispetto a `VALIDATION_RAW` (β̂ e SE con scarto
   relativo ≤ 10⁻⁹, verdetti identici) **prima** dell'esecuzione completa; poi su tutti, come porta.
4. Provenienza: commit pulito, SHA-256 di questo piano, di `VALIDATION_RAW.csv.gz` e del codice
   negli output; controllo indipendente e riconteggio prima di leggere le sintesi.

## 7. Da decidere in revisione

- Se aggiungere un braccio A2' con la **migliore approssimazione AR(1)** della covarianza dei salti (φ,
  κ, σ_x² che minimizzano la distanza da K_steps), per separare «AR(1) stimato male» da «AR(1)
  inadatto in ogni caso».
- Se includere gli effetti −0,1, −0,2 e −0,35 dello scenario 7 (oggi solo −0,3).
- Numerosità dei controlli 1 e 2 (2000 proposti).

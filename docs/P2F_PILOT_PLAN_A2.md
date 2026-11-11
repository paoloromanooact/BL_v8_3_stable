# Emendamento A2 al piano del pilota P2f — funzione di varianza della candidata M

Stato: **registrato il 2026-11-11 dopo il fallimento del test preliminare 2 e prima di
modificare il codice.** È un emendamento **non cieco rispetto a quel test**: lo motiva il
fallimento conservato agli atti (`results/P2F_PILOT/PRELIM_*_RUN1.csv`, commit `0eb7bd6`;
test eseguiti sul commit `e98b3bf`). Il piano (`docs/P2F_PILOT_PLAN.md`) e A1 restano agli
atti; A2 sostituisce **solo** A1 §1 (stima della funzione di varianza) e precisa A1 §6
(test). Il pilota resta fermo fino al superamento dei test.

## 1. Che cosa è fallito

Test 2, 200 repliche sul disegno reale T3 con rumore eteroschedastico noto:
- b̂ medio −0,427 contro −0,5 (soglia ±0,05; deviazione standard tra repliche 0,031);
- â medio spostato di −0,079 (soglia ±0,05).

Causa: dividere e_i² per (1 − 2h_i + Σ_j h_j²) rende corretto il valore atteso solo se le
varianze nella cella sono uguali. Con varianze diverse mescola σ_i² con le varianze delle
regioni di peso grande della stessa cella, e la pendenza risulta attenuata.

## 2. Nuovo stimatore (sostituisce A1 §1)

- **Covariata:** x_i = log Φ_i − m, con m la media di log Φ sulle unità del test (T3: le
  2485 regioni; T5: le 2375 regioni delle celle).
- **Modello:** σ_i² = exp(a + b x_i).
- **Risposte:** q_i = e_i², con e_i = r_i − u_{t,h} il residuo rispetto alla media di cella
  pesata (pesi w_i = Φ_i, h_i = w_i / W_cella), r_i i residui del fit nullo di P2 come in A1.
- **Media attesa**, nella forma stabile:
  μ_i(a, b) = (1 − h_i)² σ_i² + Σ_{j≠i, j∈cella} h_j² σ_j².
  La somma sugli altri si calcola senza sottrazioni, come somma di una somma cumulata
  precedente e di una successiva dentro la cella, entrambe di termini positivi.
- **Celle con una sola unità:** μ_i = 0 e residuo identicamente nullo. Si **escludono dalla
  stima** della funzione di varianza, ma restano nell'analisi: alle loro regioni si assegna la
  varianza prevista dal modello, σ̂²(Φ_i).
- **Residui quadratici nulli** (q_i = 0 in celle con almeno 2 unità): si **tengono**. Il
  criterio non usa log q_i, quindi non serve escluderli. Se ce ne sono, si contano.
- **Criterio di stima:** quasi-verosimiglianza gamma, cioè si minimizza
  Q(a, b) = (1/n) Σ_i [q_i / μ_i + log μ_i] sulle unità in celle con almeno 2 unità.
  Q è un **criterio di stima**, non una verosimiglianza: non implica che i q_i siano
  indipendenti (quelli della stessa cella non lo sono).
- **Esattezza:** la formula di μ_i è esatta per errori individuali indipendenti e centrati
  nella cella, rispetto alla media di cella. Ignora l'errore della media stimata del fit
  nullo (di ordine 1/n); i suoi effetti restano da verificare, nel test 2 e nel pilota.
- **Partenza:** b0 = 0 e a0 = log[ Σ q_i / Σ ((1 − h_i)² + Σ_{j≠i} h_j²) ], cioè la stima a
  varianza costante.
- **Vincoli:** a ∈ [a0 − 20; a0 + 20], b ∈ [−5; 5].
- **Ottimizzazione:** L-BFGS-B (scipy), `ftol` = 10⁻¹², `gtol` = 10⁻⁸, al più 500
  iterazioni, gradiente analitico. È valida se l'ottimizzatore dichiara convergenza, Q è finita
  e l'ottimo non è su un vincolo. Altrimenti il catalogo ha esito `errore`.
- **Uso:** σ̂²(Φ_i) per tutte le regioni entra in v_{t,h} e nella parte individuale di
  Var(β̂) come in A1 §2.

## 3. Test (precisa A1 §6)

- **Test 2** con condizioni e soglie **invariate** (|media(b̂) + 0,5| ≤ 0,05;
  |media(â) − a| ≤ 0,05), su due gruppi, che devono passare **entrambi**:
  - 2a: le stesse 200 repliche dell'esecuzione 1 (semi 5 000 200 + k);
  - 2b: 200 repliche nuove (semi 5 000 600 + k, k = 0…199), mai usate. La non
    sovrapposizione con tutti gli altri semi è verificata nel codice.
- **Test 1, 3, 4 e 5 e controllo dei semi:** si rieseguono sul nuovo commit, con condizioni
  invariate.
- **Se il test 2a o il 2b fallisce:** ci si ferma, **senza ritoccare il metodo nello stesso
  tentativo**. La candidata M non entra nel pilota senza un nuovo piano; si decide allora se
  proseguire con la sola candidata B.
- **Esito:** il superamento di tutti i test autorizza il pilota di sviluppo. Non è una
  validazione di M.

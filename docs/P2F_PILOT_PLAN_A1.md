# Emendamento A1 al piano del pilota P2f

Stato: **registrato il 2026-11-11 prima di scrivere ed eseguire qualunque codice del
pilota**, dopo la revisione del piano (`docs/P2F_PILOT_PLAN.md`, commit `83b0fc1`, SHA-256
`4dceb568…`), che resta agli atti e invariato. A1 sostituisce o precisa solo i punti indicati.

## 1. Funzione di varianza della candidata M (precisa piano §4, M.2)

La divisione per (1 − 2h_i + Σ_{j∈cella} h_j²) rende corretto il valore atteso solo se le
varianze nella cella sono uguali. Con varianze diverse tra regioni **non** ricostruisce
esattamente σ²(Φ_i): è un'**approssimazione candidata**. La sua tenuta si verifica nel test
preliminare 2 (§6) e nello scenario eteroschedastico 5, non si presume.

**Stima:** regressione gamma a legame logaritmico, log E[p_i] = a + b·(log Φ_i − m), con m la
media di log Φ nel disegno. I dati sono le pseudo-osservazioni p_i delle regioni in celle con
almeno 2 unità e p_i > 0 (gli esclusi si contano). Stima per minimi quadrati iterativi
(IRLS), partenza da a = log(media p), b = 0; convergenza quando max |Δ(a, b)| < 10⁻⁸, al più
100 iterazioni. Se non converge, il catalogo ha esito `errore`.

## 2. Effetti fissi e massima verosimiglianza ristretta (sostituisce piano §4, M.1 e M.4)

La REML lavora sulle **risposte medie di cella**, non sui residui di un fit precedente, con la
matrice degli effetti fissi effettiva sulle celle:
- **T3:** per la cella (t, h) con peso W_{t,h} = Σ_{i∈(t,h)} w_i, risposta
  ȳ_{t,h} = Σ w_i γ_i / W_{t,h}. Le colonne della matrice degli effetti fissi sono le 4
  combinazioni ciclo × emisfero; l'elemento (t, h; c, h') vale
  1{h = h'} · Σ_{i∈(t,h), ciclo c} w_i sin|λ_i| / W_{t,h}. È l'aggregazione esatta della
  media nulla di P2 (γ0_{c,h} sin|λ_i|); una cella con regioni di due cicli ha due elementi
  non nulli.
- **T5:** risposte η_c delle 318 celle di P2; effetti fissi = indicatori ciclo × emisfero
  delle celle (`run_p2.ch_columns(c, 1.0)`), come nel modello nullo di P2.
- **Covarianza:** V = σ_x² K(φ, κ) + diag(v), con K la covarianza dell'AR(1) bivariato
  stazionario ristretta alle celle osservate e v le varianze di campionamento della funzione
  di varianza (§1): v_{t,h} = Σ w_i² σ̂²(Φ_i) / W² per T3, Σ_{i∈c} Φ_i² σ̂_z²(Φ_i) / Φ_c² per T5.
- **Log-verosimiglianza ristretta:**
  ℓ = −½ [log|V| + log|XᵀV⁻¹X| + yᵀ(V⁻¹ − V⁻¹X(XᵀV⁻¹X)⁻¹XᵀV⁻¹)y], tramite Cholesky.
- **Parametri:** φ ∈ [0; 0,98], κ ∈ [−0,98; 0,98], θ = log σ_x² ∈
  [log(10⁻⁶ s0); log(10³ s0)], con s0 la varianza dei residui di cella del fit dei minimi
  quadrati ordinari sulla stessa matrice degli effetti fissi (celle con pesi uguali).
- **Cinque punti iniziali:** (φ, κ) ∈ {(0; 0), (0,5; 0), (0,9; 0), (0,5; −0,5), (0,5; 0,5)},
  con θ0 = log max(s0 − media(v), 0,1·s0).
- **Ottimizzazione:** L-BFGS-B (scipy), `ftol` = 10⁻¹⁰, `gtol` = 10⁻⁶, al più 500
  iterazioni. Un avvio è valido se l'ottimizzatore dichiara convergenza e ℓ è finita. Si
  sceglie l'avvio valido con ℓ massima. Se nessun avvio è valido, il catalogo ha esito
  `errore`. Un ottimo con σ_x² al limite inferiore si registra (`sigma_x_at_lower`) e vale
  come componente temporale nulla.
- **Matrici:** se una fattorizzazione di Cholesky fallisce durante l'ottimizzazione, ℓ = −∞
  per quel punto; se XᵀV⁻¹X ha numero di condizione > 10¹² all'ottimo, esito `errore`.

**Decisione della candidata M:** Var(β̂) = σ̂_x² bᵀK(φ̂, κ̂)b + Σ_i a_i² σ̂²(Φ_i) (per T5 sulle
celle: Σ_c g_c² v̂_c + σ̂_x² b_cᵀK b_c). β̂ è la stima WLS di P2 sul catalogo. Falso verdetto
se |β̂| / √Var(β̂) > z_0,0125. Se Var(β̂) non è finita o non è positiva, esito `errore`.

## 3. Candidata B: dettagli (precisa piano §4, B.2–B.4)

- **Pesi di Webb:** w ∈ {−√(3/2), −1, −√(1/2), +√(1/2), +1, +√(3/2)}, ciascuno con
  probabilità 1/6, indipendenti per cluster e per replica.
- **Statistica osservata:** WLS del modello completo di P2 (T3: regioni con pesi Φ; T5: celle
  con pesi ΣΦ); β̂; residui û; errore robusto per cluster
  V_CR1 = c · (XᵀWX)⁻¹ [Σ_g (X_gᵀ W_g û_g)(X_gᵀ W_g û_g)ᵀ] (XᵀWX)⁻¹, con
  c = G/(G − 1) · (n − 1)/(n − k); t = β̂ / √V_CR1[β, β].
- **Repliche (nulla imposta):** fit WLS del modello nullo (senza attività), valori ŷ0 e
  residui r̃ = y − ŷ0; per ogni replica y* = ŷ0 + r̃ ⊙ w_{g(i)}. Su y* si **ristimano** il
  modello completo, β̂*, i residui û* e V_CR1*, poi t* = β̂* / √V_CR1*[β, β]. Il calcolo è
  vettorizzato; il test preliminare 3 ne verifica l'identità con il calcolo diretto.
- **p-value:** p_basso = (1 + #{t* ≤ t})/(B + 1), p_alto = (1 + #{t* ≥ t})/(B + 1), B = 9999,
  soglia 0,0125 per verso.
- **Casi degeneri:** se XᵀWX ha numero di condizione > 10¹², o se V_CR1 osservata o una
  qualunque V_CR1* non è finita o non è positiva, esito `errore`.

## 4. Conteggi, casi senza esito e potenza (precisa piano §5)

- **Falsi verdetti:** contati sui **1000 tentativi** per scenario, test e candidata (un esito
  `errore` non è un falso verdetto); si riporta anche la frequenza tra i cataloghi con esito.
  La regola di mantenimento usa i 1000 tentativi (≤ 40) **e** la frazione di `errore` (≤ 2%).
- **Potenza:** denominatore = **tutti i 300 tentativi** per scenario ed effetto; un `errore`
  conta come mancato rilevamento. Così una candidata che fallisce nei cataloghi difficili non
  è favorita. Si riporta anche la potenza tra i cataloghi con esito.

## 5. Varianze nulle e altri casi (completa piano §6.4)

- Celle con una sola unità: nessuna pseudo-osservazione (escluse dalla funzione di varianza,
  che fornisce comunque σ̂²(Φ_i) per quelle regioni).
- Un σ̂² non finito, una v non finita o un'ottimizzazione senza avvii validi danno `errore`.
- Nessuno stato `errore` produce un verdetto.

## 6. Test preliminari (sostituisce piano §6.3; semi 5 000 000 + k)

Si eseguono prima del pilota; il pilota parte solo se **tutti** superano le condizioni.
1. **REML su serie sintetiche:** 200 serie con 2 emisferi × 400 CR, 15% delle celle mancanti
   a caso, due effetti fissi costanti (uno per emisfero), v = 0,25 nota, σ_x² = 1, φ = 0,8,
   κ = 0,5. Condizioni: avvii validi in almeno 198 serie su 200;
   |media(φ̂) − 0,8| ≤ 0,02; |media(κ̂) − 0,5| ≤ 0,05; |media(σ̂_x²) − 1| ≤ 0,10.
2. **Funzione di varianza sul disegno reale T3:** 200 repliche con γ_i = 15 c_i ε_i, c_i
   eteroschedastico come nello scenario 5, nessuna componente temporale. Valori veri
   b = −0,5 e a = log 225 − 0,5·(m − log mediana Φ). Condizioni: |media(b̂) + 0,5| ≤ 0,05 e
   |media(â) − a| ≤ 0,05. Si riportano anche gli scarti, perché la funzione è
   un'approssimazione (§1).
3. **Wild cluster bootstrap, vettorizzato contro diretto:** 30 unità, 5 cluster, 3 regressori,
   B = 200 con pesi fissati; condizioni: max |t*_vett − t*_dir| ≤ 10⁻¹⁰ e p-value identici.
4. **Varianza di β̂ della candidata M con parametri veri:** su un catalogo di sviluppo
   (V1, k = 0, semi 40000) con i parametri veri e la varianza individuale vera al posto delle
   stime, Var(β̂) coincide con V_true di A (scarto relativo ≤ 10⁻⁹). Verifica a e b.
5. **Nessuna risposta reale:** il disegno costruito non contiene `sintilt`, `d_axial_bal_g`,
   `s_bl`, `gamma`, `d_star` né colonne derivate (asserzione).

Se un test fallisce, il pilota non parte; correzioni del codice o delle condizioni richiedono
un emendamento registrato prima di rieseguire i test.

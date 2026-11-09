# Piano del controllo diagnostico A — varianza nulla simulata contro varianza vera di β̂

Stato: **registrato il 2026-11-09 prima di scrivere ed eseguire il codice di A.**
**Sviluppo diagnostico**, non validazione indipendente di un eventuale P2f e non verdetto: non
cambia alcun risultato, conteggio storico o decisione di P2/P2d/P2e. Contesto:
`docs/DIAGNOSTIC_P2E.md`. Lo script registrerà nei propri output il commit e lo SHA-256 di
questo file.

## 1. Domanda

Nei cataloghi sintetici della validazione P2e, la varianza della distribuzione nulla che la
procedura simula è uguale alla varianza vera di β̂? Se no, quale parte (componente
individuale o temporale) e quanto questo spiega i falsi verdetti osservati per scenario?
Serve a valutare le ipotesi H1–H3 di `docs/DIAGNOSTIC_P2E.md`; non le dimostra.

## 2. Materiale

- Scenari V0–V6, cataloghi esterni senza quenching, k = 0…1999, semi 40000 + k (gli stessi
  della validazione P2e, già materiale di sviluppo), test T3 e T5: 28 000 coppie
  catalogo × test. Nessun numero casuale nuovo: A è analitico.
- Codice esistente usato senza modifiche: `p2d.synthetic_catalog_p2d`, `run_p2.samples`,
  `run_p2.add_activity`, `p2d.design_t3`, `p2d.design_t5`, `p2d.linear_pieces` con
  `ESTIMATOR = "p2e"`, esattamente come in `p2d.one_outer`.

## 3. Formule

**Rappresentazione lineare (esatta, a disegno fissato).** β̂ = Σ_i a_i y_i, con a_i il
contributo di ogni unità (`coef_unit` di `linear_pieces`): T3 a_i = g_i (riga di WLS del
modello completo, pesi Φ, regressori di P2), y_i = γ_i; T5 a_i = g_{c(i)} Φ_i / Φ_{c(i)},
y_i = z_i = D*_i / Φ_i. Si definisce b_{t,h} = Σ_{i ∈ (t,h)} a_i sulla griglia di CR della
procedura (vuoti inclusi) e per i due emisferi. a e b includono quindi pesi, regressori
(attività, latitudine, ciclo × emisfero) e aggregazione in celle.

**Modello vero** (generatore `synthetic_catalog_p2d`, β = 0):
- T3: y_i = γ0 s_i + σ_e c_i ε_i + σ_x x_{t(i),h(i)}, σ_e = 15, σ_x = 7,5;
- T5: y_i = η0 (1 + c_i ε_i + 0,5 x_{t(i),h(i)}), cioè σ_e = η0 c_i, σ_x = 0,5 η0;
- c_i = (Φ_i / mediana Φ)^−0,25 in V4, altrimenti 1; ε_i indipendenti N(0, 1);
- x componente dello scenario, varianza marginale 1, covarianza K sulla griglia:
  - V0: K = 0;
  - V1–V4 (AR(1)): K[(t,h),(s,h')] = φ^|t−s| · (1 se h = h', altrimenti κ);
  - V5 (AR(2), φ1 = 0,5, φ2 = 0,3): stesso emisfero ρ_|t−s| con ρ0 = 1,
    ρ1 = φ1/(1 − φ2), ρ_k = φ1 ρ_{k−1} + φ2 ρ_{k−2}; emisferi indipendenti.
    **Approssimazione:** il generatore normalizza con la deviazione standard campionaria
    della serie simulata, non con quella di popolazione;
  - V6 (salti): livelli ±1 equiprobabili, indipendenti tra blocchi ed emisferi, blocchi di
    20 CR allineati alla prima CR del catalogo sintetico completo. La varianza è calcolata
    **rispetto alla distribuzione dei livelli casuali, a partizione in blocchi fissata dal
    disegno**: K = 1 se stesso emisfero e stesso blocco, altrimenti 0.

**Varianza vera:** V_true = Σ_i a_i² Var(e_i) + σ_x² bᵀ K b, con Var(e_i) = σ_e² c_i² (T3) o
η0² c_i² (T5). Media vera: Σ_i a_i E[y_i] (attesa 0: la media vera sta nello spazio dei
regressori nulli).

**Varianza simulata dalla procedura** (P2d §1–§3 con P2e): V_model = Σ_i (a_i ẽ_i)² +
σ̂_u² bᵀ K̂ b, con ẽ_i = e_i / √(1 − h_i) (residui con correzione per la leva, wild bootstrap
di Rademacher) e K̂ la covarianza AR(1) bivariata stazionaria con φ̂, κ̂; termine temporale
nullo se σ̂_u² = 0. Solo per i cataloghi applicabili. Media simulata: `const` di
`linear_pieces` (attesa 0).

**Grandezze per catalogo e test:**
- R = V_model / V_true; R_ind = Σ(a ẽ)² / Σ a² Var(e) (parte individuale);
  R_tmp = σ̂_u² bᵀK̂b / (σ_x² bᵀKb) (parte temporale, dove definita);
- **oracolo analitico** (V1–V4): V_oracle = Σ(a ẽ)² + σ_x² bᵀ K_vero b, R_oracle =
  V_oracle / V_true (parametri temporali veri, parte individuale come nella procedura);
- **miglior AR(1)** (V5, V6): AR(1) con varianza vera e autocorrelazione vera al ritardo 1
  (V5: 0,714; V6: 19/20 = 0,95), κ = 0; R_AR1 = parte temporale con questo AR(1) / parte
  temporale vera;
- **frequenza prevista di falsi verdetti** (approssimazione normale, z = 2,2414 per
  l'1,25% per verso): p = Φ((m − z √V_model − μ)/√V_true) + Φ((μ − m − z √V_model)/√V_true),
  con m la media simulata e μ la media vera; analogamente p_oracle.

**Sintesi per scenario e test:** mediana e percentili 10–90 di R, R_ind, R_tmp, R_oracle,
R_AR1; media di p e di p_oracle sui cataloghi applicabili, confrontata con la frequenza
osservata tra gli applicabili (validazione P2e) e il suo errore binomiale; media di p tra i
cataloghi con e senza falso verdetto osservato; correlazione di Spearman tra R e φ̂.

## 4. Controlli obbligatori (se uno fallisce, A si ferma e lo si riporta)

1. φ̂, κ̂, σ̂_u² e applicabilità ricalcolati coincidono con quelli registrati in
   `P2E_VALIDATION_RAW.csv.gz` (scarto ≤ 10⁻⁹ in valore relativo; NaN concordi).
2. Σ_i a_i y_i coincide con la stima osservata di `linear_pieces` (scarto relativo ≤ 10⁻⁹).
3. |m| e |μ| ≤ 10⁻⁶ √V_true.
4. Le componenti del generatore usate per K e c_i (griglia, blocchi, c_i) coincidono con
   quelle che producono il catalogo (ricostruzione verificata sul catalogo stesso).
5. Numero di regioni con |γ| > 90° (dove γ = arcsin(sin γ) non vale): riportato; se non
   nullo, la rappresentazione di T3 è approssimata per quelle regioni.

## 5. Interpretazioni previste (fissate prima dell'esecuzione)

- **I1 — sufficienza.** In uno scenario, se |p medio − frequenza osservata| ≤ 2 errori
  binomiali, la discrepanza di varianza (in approssimazione normale) basta a rendere conto
  della frequenza osservata; altrimenti contribuiscono altri fattori (non normalità,
  dipendenza tra β̂ e parametri stimati nello stesso catalogo, aspetti non rappresentati) e A
  non spiega la frequenza.
- **I2 — H1.** Se in V1–V3 R_oracle mediano è in [0,95; 1,05] e p_oracle ≤ 3,0% per T3 e T5,
  mentre R mediano < 0,95 e p > p_oracle, l'eccesso è coerente con la stima dei parametri
  temporali (H1) entro questo modello. Se R_oracle mediano < 0,95, contribuisce la parte
  individuale (wild bootstrap con leva).
- **I3 — H2.** Coerente se R_tmp mediano è più vicino a 1 in V4 che in V2.
- **I4 — H3.** Coerente se R_AR1 mediano < 0,95 in V5 e in V6.
- **I5.** Nessuna di queste condizioni stabilisce una causa: si dirà "coerente / non
  coerente con l'ipotesi". Se I1 non vale in uno scenario, le conclusioni di I2–I4 per
  quello scenario restano parziali.

## 6. Dopo A

La decisione sul controllo B (oracolo con simulazione completa) si prende dopo aver visto A:
B serve soprattutto se I1 non vale (la varianza non basta a spiegare le frequenze) o se
l'attribuzione di I2 non è netta.

## 7. Output

`results/DIAGNOSTIC/A_BY_CATALOGUE.csv.gz` (per catalogo e test), `A_SUMMARY.csv` (per
scenario e test), `A_CHECKS.csv` (controlli di §4); script
`python/sharpbl/diag_a_variance.py`; risultati in `docs/DIAGNOSTIC_A_RESULTS.md`.

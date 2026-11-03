# Protocollo P2d — Test di T3 e T5 calibrato per simulazione (emendamento di P2/P2b)

Stato: **congelato il 2026-11-03** (commit, revisione 3), prima delle
simulazioni esterne e di qualunque esecuzione di P2 sui dati reali. Informazioni già viste:
`docs/SEEN_BEFORE_FREEZE_2026-11-03.md` e la calibrazione sintetica di P2b
(RUN1, prima riga; RUN2 completa, `results/P2/P2B_CALIBRATION_RUN2_N100.*`).
Nessun risultato di P2 sui dati reali.

## 0. Perché, e che cosa questa procedura può garantire

RUN2 (100 cataloghi sintetici per scenario) mostra che con residui correlati
tra rotazioni il bootstrap di P2 sottostima l'incertezza (falsi positivi fino
a 31–38/100 contro 2,5 nominali) e che la regola di P2b **migliora** senza
portare i test al livello nominale (T5 10–11/100; T3 6/100 con ρ = 0,8).

P2d calibra la decisione simulando l'ipotesi nulla con un modello dei residui
stimato sui dati. Il livello nominale vale **rispetto al modello simulato**,
entro l'errore Monte Carlo. Se correlazione, eteroschedasticità o dipendenza
tra emisferi sono rappresentate male, la garanzia **non** si trasferisce ai
dati reali, e la stima dei parametri dai dati aggiunge incertezza (limite
generale dei test bootstrap). Per questo la procedura completa, compresa la
stima dei parametri, è validata su simulazioni esterne (§5), con criteri di
accettazione e ripiego fissati qui (§6). Le conclusioni restano comunque
**condizionate al modello dei residui** di §1–§2.

## 1. Modello sotto l'ipotesi nulla per T3 (unità = regione)

Campione S di P2, attività `A_monthly`, pesi w_i = Φ_i.

- **Media:** γ_i = γ0_{c,h} sin|λ_i| (P2 senza il termine di attività),
  stimata per WLS sui dati reali; residui r_i = γ_i − γ̂0_{c,h} sin|λ_i|.
- **Componente per rotazione ed emisfero:** u_{t,h} = media pesata (w_i) dei
  r_i con CR = t ed emisfero h.
- **Componente individuale:** e_i = r_i − u_{t(i),h(i)}.
- **Simulazione:** γ*_i = γ̂0_{c,h} sin|λ_i| + u*_{t(i),h(i)} + e_i v_i,
  con v_i = ±1 equiprobabili (wild bootstrap di Rademacher: ogni regione
  conserva la propria varianza) e u* dal modello temporale di §3.

## 2. Modello sotto l'ipotesi nulla per T5 (unità = cella CR × emisfero)

Le celle di T5 sono aggregati di regioni con pesi diversi: gli errori delle
celle si simulano **a livello di regione** e poi si aggregano come in P2, così
che la loro varianza dipenda dai pesi come nei dati.

- Per ogni regione del campione S che appartiene a una cella con almeno 3
  regioni: z_i = D*_i / Φ_i.
- **Media:** η_{c,h} stimata come in P2 (WLS sulle celle, pesi ΣΦ).
  Residui di regione r_i = z_i − η̂_{c,h}.
- **Componente per rotazione ed emisfero:** u_{t,h} = Σ Φ_i r_i / Σ Φ_i nella
  cella (t, h); componente individuale e_i = r_i − u_{t,h}.
- **Simulazione:** z*_i = η̂_{c,h} + u*_{t,h} + e_i v_i (v_i Rademacher);
  cella: η*_k = Σ Φ_i z*_i / Σ Φ_i; poi la stessa regressione di P2
  (pesi ΣΦ). L'errore simulato della cella k = (t, h) è quindi
  u*_{t,h} + Σ Φ_i e_i v_i / Σ Φ_i, con due componenti:
  - **temporale condivisa**: u*_{t,h} è la stessa per tutte le regioni della
    cella; ha varianza σ_u², è correlata tra CR consecutive (φ) e tra i due
    emisferi della stessa CR (κ, tramite le innovazioni w_t di §3);
  - **individuale**: varianza condizionata Σ Φ_i² e_i² / (Σ Φ_i)², che dipende
    dai pesi come nei dati, indipendente tra celle.

## 3. Modello temporale (comune, stimato separatamente per T3 e T5)

Sulla griglia di **tutti** i numeri di CR consecutivi tra il primo e
l'ultimo del campione (vuoti inclusi; le CR senza dati non sono osservate ma
il processo le attraversa):
u_t = φ u_{t−1} + w_t, w_t ~ N(0, Σ), Σ = σ_w² [[1, κ], [κ, 1]],
con φ e σ_w comuni ai due emisferi e κ la correlazione tra emisferi.
Partenza dalla distribuzione stazionaria (varianza σ_w² / (1 − φ²)).

**Stima (metodo dei momenti) e vincoli:**
- φ̂: regressione senza intercetta di u_{t,h} su u_{t−1,h} con le coppie di
  CR consecutive entrambe presenti (i due emisferi insieme). Vincolo di
  stazionarietà: φ̂ ∈ [0; 0,95]; un valore stimato fuori dall'intervallo si
  porta al bordo più vicino e si registra `phi_at_boundary`.
- σ_u² = varianza pesata di u_{t,h} meno la media della varianza di
  campionamento della media di cella (Σ w_i² e_i² / (Σ w_i)²). Se negativa:
  σ_u² = 0 (nessuna componente per rotazione), si registra
  `sigma_u_at_boundary`. σ_w² = σ_u² (1 − φ̂²).
- κ̂: correlazione tra u_{t,N} − φ̂ u_{t−1,N} e u_{t,S} − φ̂ u_{t−1,S} sulle CR
  con entrambi gli emisferi e la CR precedente presenti; vincolo
  κ̂ ∈ [−0,95; 0,95], bordo registrato come `kappa_at_boundary`.
- **Fallimenti con esito prestabilito:** la scarsità di dati non dimostra
  una dipendenza assente, quindi un parametro non stimabile **non** si pone a
  zero. P2d **non è applicabile** al test, e vale il ripiego descrittivo di
  §6, se si verifica almeno una delle condizioni: meno di 30 CR con dati;
  meno di 20 coppie di CR consecutive per φ̂ (`phi_not_estimable`); meno di
  20 CR utili per κ̂ (`kappa_not_estimable`). I bordi dei vincoli (φ̂ = 0 o
  0,95, σ_u² = 0, κ̂ = ±0,95) **non** sono fallimenti: si registrano e la
  procedura prosegue. Nessun altro intervento manuale. Nella validazione
  (§5) la non applicabilità è un esito possibile della procedura completa e
  se ne riporta la frequenza; un catalogo con esito "non applicabile" conta
  come "nessun verdetto" (non come falso positivo).

## 4. Regola di decisione

- Statistica: la stessa stima β̂ di P2 (T3: β_T; T5: β_η), ricalcolata su
  ogni campione simulato con lo stesso disegno (unità, pesi, latitudini,
  attività, CR, emisferi).
- **M = 20 000** campioni simulati per test (circa 250 valori in ciascuna coda
  all'1,25%); semi 20261109 (T3) e 20261110 (T5).
- **p-value Monte Carlo per verso**, con la correzione per M finito (il
  valore osservato conta come una delle repliche: 1 al numeratore, M + 1 al
  denominatore) e i pareggi contati come "almeno altrettanto estremi", cioè a
  sfavore della decisione:
  p_basso = (1 + #{β̂* ≤ β̂}) / (M + 1), p_alto = (1 + #{β̂* ≥ β̂}) / (M + 1).
- Verso previsto (β < 0 per T3 e T5): **"quenching supportato (P2d)"** se
  p_basso ≤ 0,0125; verso opposto: **"segno opposto (P2d)"** se
  p_alto ≤ 0,0125; altrimenti **"non deciso (P2d)"**. Livello 2,5% per
  ciascun test (1,25% per verso); con due test (Bonferroni, come in P2) la
  probabilità di almeno un falso verdetto tra T3 e T5 ha come riferimento al
  massimo il 5%.
- **Relazione con P2/P2b.** Per ciascun test separatamente: il verdetto P2d
  **sostituisce** i verdetti di P2 e P2b se e solo se la validazione (§5) di
  quel test soddisfa il criterio di §6; altrimenti per quel test vale il
  ripiego di §6. I verdetti P2 e `verdict_p2b` si riportano sempre accanto.
- Robustezza (P2 §5): la stessa procedura P2d sulle sensibilità S1–S6
  (M = 5000); il verdetto è "robusto" con la regola di P2 §5 applicata ai
  p-value P2d (stesso segno della stima e p del verso ≤ 0,025 in almeno 4 su 6).
- La condizione su T1 (legge di Joy) di P2 resta.

## 5. Validazione della procedura completa (simulazioni esterne)

Cataloghi sintetici (disegno sintetico di P2: 6000 regioni, attività SILSO
vera), **senza quenching**. Per ciascun catalogo esterno si esegue la
**procedura completa**: stima di media e parametri (§1–§3, con i vincoli e i
fallimenti), calibrazione interna con M = 20 000, decisione (§4).
**2000 cataloghi esterni per scenario**, semi 30000 + k.

| Scenario | Componente per rotazione | Specificazione |
|---|---|---|
| V0 | assente | corretta (φ = 0) |
| V1 | AR(1), φ = 0,5, κ = 0 | corretta |
| V2 | AR(1), φ = 0,8, κ = 0 | corretta |
| V3 | AR(1), φ = 0,8, κ = 0,6 | corretta |
| V4 | AR(1), φ = 0,8; rumore individuale eteroschedastico, sd ∝ Φ^−0,25 | corretta |
| V5 | AR(2), φ1 = 0,5, φ2 = 0,3 | **errata** (robustezza) |
| V6 | salti di livello: media a gradini di 20 CR, ampiezza = sd | **errata** (robustezza) |

Ampiezza della componente per rotazione: sd pari a metà del rumore
individuale, come in RUN2. Si riportano per scenario e test: falsi positivi
nel verso previsto e opposto (conteggio su 2000 e frazione), totale, limite
superiore **unilaterale al 95% di Clopper–Pearson**, errore Monte Carlo,
frequenza di "non deciso", frequenza dei bordi e dei fallimenti di §3, e la
frequenza di almeno un falso verdetto tra T3 e T5 (riferimento ≤ 5%). Potenza
con quenching iniettato (β = −0,2·γ0 per T3, −0,2·η0 per T5) in V1 e V2.
Costo stimato: circa 2,3 s per calibrazione interna (6000 regioni × 20 000
campioni), quindi circa 18 ore di calcolo su un processo, circa 1,5–2 ore in
parallelo su 12 processi (la macchina ne ha 16; il disegno resta fisso e la
stima usa le statistiche sufficienti di WLS).

## 6. Accettazione e ripiego (fissati prima dei risultati)

**Obiettivo nominale e limite di accettazione.** L'**obiettivo nominale** di
ciascun test è un livello del 2,5% (§4). Il criterio di accettazione **non**
certifica il 2,5%: certifica che, **negli scenari verificati**, il livello
vero non supera un **limite di accettazione del 4%** (fino a 1,6 volte il
nominale). Con due test al 4% la probabilità di almeno un falso verdetto
resta sotto circa l'8% (1 − 0,96²). Testi e risultati distinguono sempre
"obiettivo nominale 2,5%" e "limite di accettazione 4% negli scenari
verificati".

- **Accettazione, per ciascun test separatamente (T3 e T5 possono superarla o
  fallirla indipendentemente):** in **tutti** gli scenari correttamente
  specificati (V0–V4) il limite superiore unilaterale al 95% (Clopper–Pearson)
  della frazione di falsi positivi del test (entrambi i versi) è ≤ 4%, cioè
  **al massimo 65 falsi positivi su 2000** cataloghi (66 su 2000 dà un limite
  superiore di Clopper–Pearson sopra il 4%). Caratteristiche del criterio per
  un singolo scenario (binomiale, calcolate prima dei risultati): con livello
  vero 2,5% è superato con probabilità 0,984; con 3% 0,77; con 4% 0,05. Per
  tutti e cinque gli scenari insieme, con livello vero 2,5% in ciascuno, la
  probabilità di superarlo è 0,984⁵ ≈ 0,92 **assumendo gli scenari
  indipendenti** (lo sono: cataloghi e semi distinti). Il criterio può quindi
  fallire anche per una procedura ben calibrata (circa 8% di probabilità), e
  lo si dichiara.
- **Se accettata:** il verdetto P2d del test si riporta con la frase
  "obiettivo nominale 2,5%; livello vero entro il limite di accettazione del 4%
  negli scenari verificati, rispetto al modello dei residui di P2d (AR(1)
  bivariato per rotazione ed emisfero, rumore individuale eteroschedastico)".
- **Scenari di robustezza (V5, V6):** non decidono l'accettazione. Se il loro
  limite superiore supera il 4%, la sintesi lo dichiara e limita la
  conclusione alle ipotesi del modello, **senza** affermare una calibrazione
  generale.
- **Ripiego** (validazione non superata, oppure P2d non applicabile per §3):
  quel test si riporta **solo come descrittivo** (stima e intervalli di P2,
  P2b, p-value P2d), **senza verdetto**, e lo si dichiara nella sintesi.
  Nessun'altra procedura si prova dopo aver visto i risultati della
  validazione, salvo un nuovo protocollo che dichiari di averli visti.

## 7. Diagnostica sul campione reale (si riporta)

φ̂, σ̂_u, κ̂ con i flag di §3, numero di coppie usate, ACF dei residui per CR
ai ritardi 1–13 (P2b §3) e confronto con l'ACF media dei campioni simulati.
La diagnostica **informa** sull'adeguatezza del modello; **non** stabilisce un
unico "ρ vero", e un'autocorrelazione non significativa (a qualunque ritardo)
**non** esclude una dipendenza rilevante. Nessuna regola di P2d dipende dalla
significatività dell'ACF.

## 8. Output

`results/P2/P2D_VALIDATION.csv` (§5), `P2D_PARAMETERS.csv` (§3, §7),
`P2D_TESTS.csv` (§4, per variante), colonna `verdict_p2d` in `P2_SUMMARY.csv`.

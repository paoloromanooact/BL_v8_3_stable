# Piano del controllo diagnostico C — componente individuale e correzione per la leva

Stato: **registrato il 2026-11-09 prima di scrivere ed eseguire il codice di C.**
**Sviluppo diagnostico**, non validazione indipendente di un eventuale P2f e non verdetto: non
cambia alcun risultato, conteggio storico o decisione di P2/P2d/P2e. Contesto:
`docs/DIAGNOSTIC_A_RESULTS.md` §4 (componente individuale simulata circa il 15% più piccola
del vero, osservazione post hoc) e `docs/DIAGNOSTIC_B_RESULTS.md` (con i parametri temporali
veri resta un eccesso di 0,5–1 punto; V1 non cambia). Lo script registrerà nei propri output
il commit e lo SHA-256 di questo file.

## 1. Domande

1. La sottostima della componente individuale osservata in A è spiegata dalla correzione per
   la leva 1/(1 − h_i), insufficiente per le unità di peso grande (ipotesi H5)?
2. Con i parametri temporali veri, rendere corretta la varianza attesa della componente
   individuale elimina l'eccesso residuo di B, in particolare in V1?
3. Il meccanismo di simulazione e decisione, con modello nullo esattamente vero, dà il livello
   nominale? (controllo di base, necessario per leggere 2)

C **non** dà per accertato che la sottostima del 15% spieghi l'eccesso.

## 2. Materiale

- Scenari **V1** (caso principale) e **V4** (confronto: rumore eteroschedastico, R_ind ≈ 0,93
  in A), k = 0…1999, semi 40000 + k: gli stessi cataloghi di sviluppo di P2e, A e B. Test T3
  e T5. Per la parte analitica (§3.1) anche V2 e V3 (costo trascurabile).
- Procedura P2e invariata salvo quanto indicato per ciascun braccio; parametri temporali
  **veri** in tutti i bracci simulati (come B).

## 3. Bracci

### 3.1 Analitico (H5)

Per ogni catalogo e test, con h_i = w_i / W_cella (pesi Φ, celle CR × emisfero, come in
`cell_components`) e σ_i² la varianza vera del rumore individuale (T3: (15 c_i)²; T5:
(η0 c_i)²; c_i come in A), il valore atteso del residuo di cella è
E[e_i²] = σ_i² (1 − 2 h_i) + Σ_{j ∈ cella} h_j² σ_j²
(la componente temporale è costante nella cella e si elide; si trascura l'errore della media
stimata, di ordine 1/n). La varianza individuale attesa nella procedura è
Σ_i a_i² E[e_i²] / max(1 − h_i, 0,05), quella vera Σ_i a_i² σ_i²; il loro rapporto è
R_ind_atteso. Si confronta con R_ind realizzato di A (stessi cataloghi), e si riporta la quota
di Σ a_i² σ_i² dovuta alle unità con h_i > 0,3.

### 3.2 C1 — oracolo completo (controllo di base)

Simulazione nulla con parametri temporali veri e componente individuale **vera**: al posto di
a_i ẽ_i v_i (Rademacher) si usa a_i σ_i z_i con z_i ~ N(0, 1). Media simulata e regola di
decisione invariate. Semi della calibrazione interna: 260000 + 2k (T3), 260001 + 2k (T5)
(nuovi: la sequenza di numeri casuali differisce comunque da quella di B).

### 3.3 C2 — oracolo con componente individuale corretta in valore atteso

Come B (parametri temporali veri, wild bootstrap di Rademacher sui residui con leva), ma con
ogni termine a_i ẽ_i moltiplicato per s_i = √(σ_i² / E[ẽ_i²]), dove
E[ẽ_i²] = E[e_i²] / max(1 − h_i, 0,05) (§3.1). La varianza attesa della componente
individuale diventa quella vera; i residui restano quelli dei dati. **Stessi semi di B**
(60000 + 2k, 60001 + 2k) e stessa sequenza di numeri casuali: confronto appaiato con B.

## 4. Grandezze riportate (per scenario e test)

Falsi verdetti nei due versi, totale su 2000 e tra gli applicabili, errore binomiale, limite
CP unilaterale al 95%, frequenza di non applicabilità (come in P2e); per C2 i conteggi
appaiati con B (falsi in entrambi, solo B, solo C2; verdetti cambiati per tipo); per §3.1
mediana e percentili 10–90 di R_ind_atteso e di R_ind di A, e la quota delle unità con
h_i > 0,3.

## 5. Controlli obbligatori (se uno fallisce, C si ferma e lo si riporta)

1. Con s_i = 1 il codice di C2 riproduce i verdetti di B sui primi 25 cataloghi di V1 e V4
   (100 confronti, 0 differenze).
2. Con le formule di §3.1 e c_i = 1, nei cataloghi di V1 la somma Σ_i a_i² E[e_i²] è finita
   e positiva in tutti i cataloghi applicabili.

## 6. Interpretazioni previste (fissate prima dell'esecuzione)

- **K0 — controllo di base.** Se C1 dà una frequenza entro 2 errori binomiali dal 2,5% in V1
  e V4 (per T3 e T5), il meccanismo di simulazione e decisione è adeguato quando il modello
  nullo è vero. Altrimenti il problema sta in parti diverse dai parametri del modello nullo
  (rappresentazione, regola di decisione, generatore) e C2 non si interpreta.
- **K1 — H5.** Se la mediana di R_ind_atteso differisce di non più di 0,03 dalla mediana di
  R_ind di A in ciascuno scenario, la correzione per la leva rende conto della sottostima
  (coerente con H5). Altrimenti la sottostima ha altre cause.
- **K2 — eccesso residuo.** Valutata solo se K0 vale. Se in uno scenario C2 è entro 2 errori
  binomiali da C1 e ha limite CP ≤ 4%, la sottostima della componente individuale è coerente
  con l'eccesso residuo di B in quello scenario. Se C2 è entro 2 errori binomiali da B e
  supera C1 di più di 2 errori, la componente individuale non spiega l'eccesso residuo.
  Casi intermedi: si riportano come parziali.
- **K3.** Nessuna di queste condizioni stabilisce una causa; un limite CP ≤ 4% non dimostra
  il livello nominale del 2,5%.

## 7. Costo

Circa 9,5 s di CPU per catalogo per braccio simulato (misurato in B): 2 bracci × 2 scenari ×
2000 cataloghi ≈ 76 000 s di CPU, circa 1 ora e 50 minuti su 12 processi; la parte
analitica richiede pochi minuti.

## 8. Output

`results/DIAGNOSTIC/C_RAW.csv.gz`, `C_SUMMARY.csv`, `C_ANALYTIC.csv`, `C_CHECKS.csv`; script
`python/sharpbl/diag_c_individual.py`; risultati in `docs/DIAGNOSTIC_C_RESULTS.md`.

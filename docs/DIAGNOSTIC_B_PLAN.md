# Piano del controllo diagnostico B — procedura P2e con i parametri temporali veri (oracolo)

Stato: **registrato il 2026-11-09 prima di scrivere ed eseguire il codice di B.**
**Sviluppo diagnostico**, non validazione indipendente di un eventuale P2f e non verdetto: non
cambia alcun risultato, conteggio storico o decisione di P2/P2d/P2e. Contesto:
`docs/DIAGNOSTIC_P2E.md`, `docs/DIAGNOSTIC_A_RESULTS.md`. Lo script registrerà nei propri
output il commit e lo SHA-256 di questo file.

## 1. Domanda

Se la procedura P2e usasse i parametri temporali veri invece di quelli stimati, quanti falsi
verdetti darebbe negli scenari V1–V4? Serve a distinguere il contributo della **stima dei
parametri temporali** (H1) dagli altri aspetti della procedura. B **non** verifica
l'ipotesi sulla sottostima della componente individuale (`docs/DIAGNOSTIC_A_RESULTS.md` §4),
che resta da verificare separatamente, e non chiude da solo la diagnosi.

## 2. Materiale e procedura

- Scenari V1, V2, V3 e V4 (V4 come confronto con V2), cataloghi senza quenching,
  k = 0…1999, semi 40000 + k: gli stessi cataloghi di sviluppo della validazione P2e.
- **Procedura P2e invariata** (`p2d.linear_pieces` con `ESTIMATOR = "p2e"`, stima della
  media, componente individuale con correzione per la leva e segni di Rademacher, simulazione
  AR(1) bivariata stazionaria, M = 20 000, regola di decisione di P2d §4), con **una sola
  sostituzione**: nei parametri usati dalla simulazione nulla, φ̂, κ̂ e σ̂_u² sono sostituiti
  dai valori veri dello scenario:
  - φ: 0,5 (V1), 0,8 (V2, V3, V4); κ: 0 (V1, V2, V4), 0,6 (V3);
  - σ_u²: (0,5 · 15)² = 56,25 per T3; (0,5 · η0)² = 10⁻⁴⁸ per T5 (η0 = 2·10⁻²⁴).
- **Semi della calibrazione interna uguali a quelli della validazione P2e** (60000 + 2k per
  T3, 60001 + 2k per T5): ogni catalogo usa gli stessi numeri casuali dell'esecuzione
  originale, quindi il confronto con P2e è appaiato e la differenza viene solo dai parametri.
- **Applicabilità:** invariata. Un catalogo non applicabile nella procedura originale resta
  non applicabile (la sostituzione riguarda solo i parametri della simulazione); se ne
  riporta la frequenza.

## 3. Grandezze riportate (per scenario e test)

- falsi verdetti nei due versi, totale su 2000 e tra gli applicabili; limite superiore
  unilaterale al 95% di Clopper–Pearson; errore Monte Carlo (binomiale) della frequenza;
- frequenza di non applicabilità;
- confronto appaiato con P2e originale sugli stessi cataloghi: falsi verdetti in entrambe,
  solo nell'originale, solo nell'oracolo;
- confronto con le previsioni di A: frequenza oracolo di B contro p oracolo medio di A, e
  frequenza originale contro p prevista di A, in unità di errore binomiale.

## 4. Controlli obbligatori (se uno fallisce, B si ferma e lo si riporta)

1. **Riproduzione dell'originale:** con i parametri stimati (nessuna sostituzione), il codice
   di B riproduce il verdetto registrato in `P2E_VALIDATION_RAW.csv.gz` sui primi 25
   cataloghi di ogni scenario, per T3 e T5 (200 confronti, 0 differenze).
2. I parametri effettivamente usati nella simulazione oracolo sono quelli di §2 (registrati
   per ogni catalogo).

## 5. Interpretazioni previste (fissate prima dell'esecuzione)

- **J1.** Se in V1–V3 la frequenza oracolo tra gli applicabili è entro 2 errori binomiali dal
  p oracolo di A e il limite di Clopper–Pearson su 2000 è ≤ 4% per T3 e T5, allora con i
  parametri temporali veri la procedura rispetterebbe il limite in questi scenari: l'eccesso
  di P2e è coerente con la stima dei parametri temporali. Un eventuale scarto residuo da 2,5%
  riguarda altri aspetti (per esempio la componente individuale), non verificati da B.
- **J2.** Se in uno scenario tra V1 e V3 il limite di Clopper–Pearson oracolo supera il 4%, la
  stima dei parametri non è l'unica causa: contribuiscono altri aspetti della procedura
  (componente individuale, stima della media, non normalità, struttura della simulazione).
- **J3.** Se le frequenze oracolo di V2 e V4 differiscono di non più di 2 errori binomiali
  combinati, la differenza tra V2 e V4 in P2e è coerente con la diversa stima dei parametri
  (H2).
- **J4.** Se la frequenza oracolo differisce dal p oracolo di A di più di 2 errori binomiali,
  le approssimazioni di A (normalità, parametri fissi) non bastano per quello scenario.
- **J5.** Nessuna di queste condizioni stabilisce una causa: si dirà "coerente / non
  coerente".

## 6. Costo

Circa 2,3 s per calibrazione interna × 2000 cataloghi × 4 scenari × 2 test, più 200
riproduzioni: circa 10 ore di CPU, circa un'ora su 12 processi.

## 7. Output

`results/DIAGNOSTIC/B_RAW.csv.gz` (per catalogo e test), `B_SUMMARY.csv`, `B_CHECKS.csv`;
script `python/sharpbl/diag_b_oracle.py`; risultati in `docs/DIAGNOSTIC_B_RESULTS.md`.

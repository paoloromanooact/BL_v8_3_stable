# Emendamento A2 al protocollo morfologico HMI — classi definite dall'organizzazione del campo

Stato: **registrato il 2026-11-13 dopo la taratura dei due lettori e prima di qualunque lettura delle 90
schede nuove.** **Non cieco rispetto alla taratura**: lo motiva l'ambiguità comune ai due lettori sulla
scheda di riferimento R11 (`docs/MORPHOLOGY_CALIBRATION_COMPARISON.md`, `7197774`). Il protocollo
(`21dfe6d`) e l'emendamento A1 (`67f5e1a`) restano agli atti; A2 sostituisce solo le regole operative
delle classi (§3, «Regole operative per i casi di confine», punti 1–3).

## 1. Motivazione

La distinzione tra le classi dipende dall'**organizzazione del campo** dentro la maschera, non dalla
presenza di macchie, perché la domanda morfologica è se l'asse tra i due centroidi rappresenti una sola
coppia bipolare. La scelta non è motivata da conseguenze sui risultati (numero di U, contributo a
Σ|S_BL|). Più gruppi magnetici non dimostrano da soli la presenza di più regioni fisiche.

## 2. Regole (sostituiscono i punti 1–3; la regola 4 su U resta)

- **A** — una coppia bipolare **dominante** riconoscibile, anche composta da plage.
- **B** — più concentrazioni **separate e comparabili**, anche di sola plage, senza una coppia dominante.
- **D** — configurazione **chiaramente sbilanciata**, oppure diffusa e frammentata **senza gruppi
  riconoscibili**.
- **U** — il confine resta irrisolto nelle immagini disponibili; si scrivono le alternative.

Le due viste fisse (±1500 G e ±300 G), il divieto di usare numeri, NOAA o centroidi nel primo passaggio
e tutte le altre parti del protocollo restano invariati.

## 3. Taratura

La classificazione originale di R11 resta **U per entrambi i lettori**, con gli hash originali
(`a851aadd…`, `51f67b69…`). La classe secondo la regola emendata si registra in una **colonna separata**
del documento di confronto, senza modificare i file bloccati. Le 90 letture usano le regole di A2.

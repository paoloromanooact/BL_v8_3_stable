# Prova tecnica del controllo HARP dominanti (2 HARP) — non è il controllo del campione

Eseguita il 2026-11-11 alle 15:16 con `dominant_harp_check.py --limit 2 --out <scratchpad>`, prima
del controllo completo, per verificare il codice; output copiati qui senza modifiche.
- HARP esaminate: 393 e 5249 (gruppo 24N, ranghi 1 e 2 delle dominanti). `DOMINANT_HARP_SELECTION.csv`
  contiene la selezione completa (120 HARP), identica a quella che userà il controllo completo.
- Provenienza registrata: commit `a41c451` con albero **non pulito** (`git_dirty` = 1): la
  correzione delle coordinate della figura era in corso e committata subito dopo in `c61bf2d`.
- Correzione dichiarata: nella prima versione della figura i centroidi (longitudine in
  (−180°, 180°]) erano confrontati con la mappa (longitudine in [0°, 360°)) senza riduzione modulo
  360°, e il segmento dei centroidi non compariva; la correzione riguarda solo la figura, non i
  valori dei controlli (identici prima e dopo).
- Esito tecnico: valori P1 riprodotti esattamente (scarto 0 su S_BL, tilt e d) per le due HARP.

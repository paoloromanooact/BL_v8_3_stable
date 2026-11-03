# Protocollo P1d — Ricomparse delle regioni ed evoluzione tra record (emendamento di P1)

Stato: **congelato il 2026-11-03**, prima della serie P1 completa e di
qualunque esecuzione di P2 sui dati veri. Aggiunge flag, una variante e
controlli; **non modifica** P1, P1b, P1c né P2, che restano validi. Lo script
registra lo SHA-256 di P1, P1b, P1c e P1d negli output.

## 0. Perché, e cosa è già stato visto (in parte non cieco)

Da una revisione esterna del branch: una regione che sopravvive a una
rotazione solare riceve una **nuova HARP** al passaggio successivo, quindi nelle
somme per rotazione (P1 §7) e nel test T5 di P2 il suo contributo può essere
contato più volte. Inoltre il record vicino al meridiano centrale misura la
regione in un solo istante, mentre la regione evolve.

Visto finora, oltre a quanto dichiarato in P1, P1b e P1c: la serie P1 parziale
(record 2010-05 → 2012) e le sue figure, prodotte come controllo di qualità
durante il download. Le regole qui sotto usano solo posizioni e tempi dai
metadati SHARP, non polarità, tilt o S_BL.

## 1. Ricomparse (regola)

Per ogni HARP con record primario si usano dai metadati del record primario:
tempo t, latitudine λ = LAT_FWT, longitudine di Carrington
L = LON_FWT + CRLN_OBS (modulo 360).

Una HARP j è **ricomparsa** di una HARP i precedente se valgono tutte:
- 20 ≤ t_j − t_i ≤ 34 giorni (una rotazione, ±7 giorni);
- stesso emisfero e |λ_j − λ_i| ≤ 5°;
- |L_j − L_pred| ≤ 10° (con L avvolto in ±180°), dove
  L_pred = L_i + (ω(λ̄) − ω_C)·(t_j − t_i), λ̄ = (λ_i + λ_j)/2,
  ω(λ) = 14,713 − 2,396 sin²λ − 1,787 sin⁴λ gradi/giorno (rotazione
  differenziale delle strutture magnetiche, Snodgrass & Ulrich 1990) e
  ω_C = 14,1844 gradi/giorno (rotazione siderale di Carrington).

Se una HARP j ha più candidati i, si sceglie quello con la distanza minore
d = √[(Δλ/5°)² + (ΔL/10°)²]; ogni HARP i può avere al massimo una ricomparsa
(assegnazione in ordine di d crescente). Le catene i → j → k definiscono una
**famiglia**; la prima HARP della famiglia è l'**originale**.

Colonne nel catalogo: `recurrence_of` (HARP precedente o vuoto),
`family_id`, `family_rank` (0 = originale, 1 = prima ricomparsa, …).

## 2. Variante e sensibilità

- **P1, somme per CR (§7):** variante **E** = come A, solo le HARP originali
  (`family_rank` = 0).
- **P2:** sensibilità **S8** = campione S senza ricomparse (`family_rank` = 0).
  S8 si riporta accanto alle altre ma **non entra** nel criterio di robustezza
  di P2 §5, che resta invariato.

## 3. Evoluzione tra record primario e di controllo (descrittivo)

Per le HARP con record primario e di controllo distinti, entrambi con
`valid_bl` = 1: distribuzione di Δ tilt ridotto, del rapporto S_BL(controllo) /
S_BL(primario), frazione con lo stesso segno di D* e con lo stesso
`hale_sign`, e di |Δt| tra i due record. Si riportano mediana e percentili
16–84 in `P1_CHECKS.csv`; nessuna soglia.

## 4. Controlli (si riportano)

- Numero di ricomparse, di famiglie, distribuzione di `family_rank`.
- Frazione del flusso Φ della variante A dovuta a ricomparse, per anno.

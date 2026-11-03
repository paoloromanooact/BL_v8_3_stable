# Protocollo P1c — Regola del ciclo nelle sovrapposizioni (emendamento di P1 §5)

Stato: **congelato il 2026-11-03**, prima di qualunque misura di polarità,
tilt o S_BL della serie. Modifica **solo** il punto 4 del §5 di
`PROTOCOL_P1_SBL_SERIES.md` (SHA-256 `72f24c68…`); P1 e P1b restano validi e
non vengono modificati. Lo script registra lo SHA-256 di P1, P1b, P1c e P2
negli output.

## 0. Perché, e cosa è già stato visto (non cieco)

La regola di P1 §5 è stata applicata (`python/sharpbl/cycle_boundary.py`,
tabella `results/P1/CYCLE_BOUNDARY_FITS.csv`) alle |LAT_FWT| dei record
primari. In alcuni gruppi la mistura di due gaussiane divide in due
componenti la distribuzione di latitudine di **un solo ciclo**, che non è
gaussiana, e assegnerebbe al ciclo vecchio regioni a latitudine media:

| Gruppo | media "vecchio" | media "nuovo" | esito con P1 |
|---|---|---|---|
| 2010-01 → 2010-07 | 20,0° (peso 0,89) | 30,7° | regioni a ~20° nel ciclo 23 |
| 2010-07 → 2011-01 | 17,8° | 24,0° | sotto ~19,6° nel ciclo 23 |
| 2021-07 → 2022-01 | 17,5° | 23,6° | sotto ~18,5° nel ciclo 24 |

Fisicamente, vicino ai minimi le regioni del ciclo vecchio emergono a bassa
latitudine (sotto circa 12°) e quelle del ciclo nuovo ad alta latitudine
(sopra circa 18°), come nel diagramma a farfalla.

**Le soglie qui sotto sono state fissate dopo aver visto quella tabella.** La
tabella contiene solo latitudini dai metadati: nessuna polarità, nessun tilt,
nessun S_BL. I test sul segno Hale e quelli di P2 restano quindi indipendenti
da questa scelta.

## 1. Regola (sostituisce P1 §5, punto 4)

Dopo il fit della mistura (P1 §5, punti 1–3, invariati), un gruppo è
considerato **di due cicli** solo se valgono tutte:
- peso di ciascuna componente ≥ 0,05;
- media della componente vecchia **≤ 12°**;
- media della componente nuova **≥ 18°**;
- distanza tra le medie **≥ 8°**.

Altrimenti il gruppo è di un solo ciclo e decide la data (stato
`DATE_IN_WINDOW`). Nei gruppi di due cicli il punto 5 di P1 §5 resta
invariato (p_new, soglia 0,5, AMBIGUOUS se 0,2 < p_new < 0,8).

## 2. Effetto atteso (dalla tabella già vista)

Passano alla data i gruppi 2010-01 → 2010-07, 2010-07 → 2011-01,
2017-07 → 2018-01 (medie 8,0° e 15,0°) e 2021-07 → 2022-01. Restano separati
per latitudine 2018-07 → 2019-01, 2019-01 → 2019-07 e 2019-07 → 2020-07.

## 3. Controllo

La tabella dei gruppi riporta, per ogni gruppo, lo stato con la regola P1 e
con la regola P1c, e il numero di regioni per stato di ciclo.

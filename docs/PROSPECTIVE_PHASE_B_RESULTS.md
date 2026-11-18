# Piano prospettico, fase B: risultati

**2026-11-18. Simulazioni, descrittivo, non cieco.** Piano `docs/PROSPECTIVE_INFORMATION_PLAN.md` (`71c7d17`) §5 B,
emendamento A1 (`551d829`); candidati dalla fase A (`results/PROSPECTIVE_PHASE_A/B_SELECTION.csv`): tutti T5, famiglia
F5, modello (a), scarto di attività −0,5, f = 0,75, k = 1,5. Script `scripts/prospective_phase_b.py` (`9cc4cf7`),
selftest 12/12; corsa unica su `9cc4cf7`, 4000 unità appaiate (1000 cataloghi sotto nulla e 1000 sotto lo scenario per
candidato, procedura M di P2f invariata), 1,76 ore. **Il benchmark aveva previsto 0,40 ore** (misurava soprattutto la
costruzione dei disegni): errore dichiarato, la corsa resta molto sotto il tetto di 8 ore del piano. Output in
`results/PROSPECTIVE_PHASE_B/`, conservati prima della lettura in `aad6683`. Controllo indipendente (hash, righe e semi,
intervalli = β ∓ z·SE, verdetti coerenti con gli intervalli, riepilogo ricontato dai dati grezzi): superato.
Nota tecnica: nel `SUMMARY.csv` il valore `null` della colonna `signal` viene letto da pandas come mancante; va letto
con `keep_default_na=False`.

| j | Disegno, rumore | Falsi `supportato` sotto nulla (previsione analitica) | `opposto` sotto nulla | Riconoscimento (previsione) | Copertura | R | Errori |
|---|---|---|---|---|---|---|---|
| 0 | E2, AR(1) 0,5 | 2,2 % (2,2 %) | 0,2 % | 19,7 % (20,4 %) | 97,6 % | 1,04 | 0 |
| 1 | E2, salti 20 CR | 1,8 % (1,9 %) | 0,6 % | 11,8 % (11,8 %) | 97,5 % | 1,00 | 1 |
| 2 | E3, AR(1) 0,5 | 1,5 % (2,1 %) | 0,9 % | 19,0 % (21,3 %) | 97,4 % | 1,05 | 2 |
| 3 | E3, salti 20 CR | 1,7 % (1,9 %) | 0,8 % | 13,4 % (12,1 %) | 97,5 % | 1,00 | 0–1 |

R = mediana dell'errore standard / deviazione standard delle stime; copertura del bersaglio (0 o Δβ). Errore Monte Carlo
di una frequenza del 20 % su 1000 cataloghi: circa 1,3 punti.

**Lettura.** Nei quattro casi la procedura M segue la previsione analitica della fase A entro l'errore Monte Carlo, con
copertura nominale e R ≈ 1, anche con il rumore a salti, in cui la validazione P2f di T5 aveva fallito: qui gli scarti
e i disegni sono diversi, quindi non è una nuova validazione di T5. I numeri della fase A (riconoscimento della riduzione
del 20 % al più circa 1 volta su 5 con MDI) sono confermati dalla procedura effettiva. T5 resta descrittivo
(decisione del 18 novembre).

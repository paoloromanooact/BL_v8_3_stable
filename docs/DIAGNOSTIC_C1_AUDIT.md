# Verifica di coerenza di C1: generatore, distribuzione nulla e p-value

Data: 2026-11-09. **Verifica d'implementazione post hoc, non preregistrata**, fatta dopo
aver visto i risultati di C (`docs/DIAGNOSTIC_C_RESULTS.md`); nessuna simulazione nuova,
nessun verdetto. Usa solo output esistenti (`A_BY_CATALOGUE.csv.gz`, `C_RAW_RUN1.csv.gz`).
Script `python/sharpbl/diag_c1_audit.py`; tabelle `results/DIAGNOSTIC/AUDIT_C1_*.csv`.

## 1. Domanda

C1 (modello nullo esatto) dà circa 3,0–3,15% di falsi verdetti invece del 2,5%. Prima di
provare cataloghi nuovi: generatore, distribuzione nulla e p-value sono coerenti tra loro?
Semi nuovi non correggerebbero un errore d'implementazione.

## 2. Controlli del codice

- **p-value e regola di decisione** (`p2d.decide`): p_basso = (1 + #{β* ≤ β̂})/(M + 1),
  pareggi a sfavore, soglia 0,0125 per verso. Con M = 20 000 la decisione equivale a β̂ sotto
  il 250° valore simulato più piccolo (o sopra il 250° più grande): livello 250/20 001 ≈
  1,25% per verso. Conforme a P2d §4.
- **Distribuzione nulla di C1** (`diag_c_individual.simulate`, braccio C1): componente
  temporale AR(1) bivariata stazionaria con i parametri veri (`p2d.simulate_ar1`, partenza
  dalla distribuzione stazionaria) più a_i σ_i z_i con z_i normali; media `const` = 0 (A,
  controllo 3). È la distribuzione esatta di β̂ sotto il modello del generatore, se la
  varianza vera di A (piano A §3) è corretta.
- **Generatore** (`p2d.synthetic_catalog_p2d`, `p2d.cr_component`): AR(1) con partenza
  stazionaria e innovazioni √(1 − φ²); rumore individuale normale; γ ricostruito senza
  distorsione salvo |γ| > 90° (345 regioni in tutto, A).

## 3. Controlli numerici sui cataloghi esistenti

**Decisione Monte Carlo contro decisione esatta.** Con il modello esatto la decisione si può
calcolare senza simulazione: falso verdetto se |z| > 2,2414, con z = (β̂ − μ)/√V_true (A).
Concordanza con i verdetti Monte Carlo di C1 (`AUDIT_C1_MC_VS_EXACT.csv`): 1998, 1996, 1999,
1999 su 2000 (V1 T3, V1 T5, V4 T3, V4 T5). I casi discordanti hanno |z| entro 0,04 dalla
soglia (errore Monte Carlo del quantile). **La parte Monte Carlo e il calcolo dei p-value
sono coerenti con la distribuzione esatta**; lo scostamento di C1 non nasce lì.

**Distribuzione di z per scenario** (`AUDIT_C1_Z_BY_SCENARIO.csv`; con il modello corretto
z ~ N(0, 1); errore della varianza ≈ 0,032 su 2000 cataloghi):

| Scenario | var(z) T3 / T5 | |z| > 2,2414 T3 / T5 |
|---|---|---|
| V0 | 1,01 / 1,06 | 2,45% / 3,25% |
| V1 | 1,07 / 1,07 | 3,10% / 3,05% |
| V2 | 1,05 / 1,07 | 3,20% / 3,10% |
| V3 | 1,04 / 1,04 | 2,80% / 3,10% |
| V4 | 1,05 / 1,07 | 3,15% / 3,05% |
| V5 | 1,00 / 1,00 | 2,20% / 2,25% |
| V6 | 1,00 / 0,99 | 2,50% / 2,40% |

**Dipendenza tra scenari** (`AUDIT_C1_Z_CORR.csv`): la correlazione di z tra scenari per lo
stesso k è 0,87–1,00 tra V1, V2, V3 e V4, e circa 0 tra questi, V0, V5 e V6. Motivo: tutti
gli scenari usano gli stessi semi dei cataloghi (40000 + k in P2e, 30000 + k in P2d, come
prescritto da P2d §5), e negli scenari AR(1) `cr_component` consuma lo stesso numero di
numeri casuali, quindi V1–V4 condividono disegno e rumore individuale e differiscono solo
nella componente per rotazione. V0, V5 e V6 consumano un numero diverso di numeri casuali e
danno realizzazioni diverse.

**Gruppi indipendenti** (un rappresentante per gruppo: V0, V1 per V1–V4, V5, V6;
`AUDIT_C1_POOLED_INDEPENDENT.csv`): frequenza esatta di |z| > 2,2414 pari a 2,56% (T3),
2,74% (T5), 2,65% ± 0,13 complessiva su 16 000, cioè circa 1,2 errori sopra il 2,5%.

## 4. Lettura (descrittiva)

- Nessuna discrepanza d'implementazione rilevata tra generatore, distribuzione nulla e
  p-value: la decisione Monte Carlo coincide con quella esatta, e nei gruppi diversi da
  V1–V4 la distribuzione di z è compatibile con N(0, 1).
- Il livello di circa il 3% di C1 in V1 e V4 riflette soprattutto una **sola realizzazione**,
  condivisa da V1–V4, in cui |z| supera la soglia nel 3,05–3,20% dei cataloghi (var(z)
  1,04–1,07, cioè 1,2–2,2 errori sopra 1). Sui gruppi indipendenti la frequenza complessiva
  è 2,65%: compatibile con il 2,5% entro l'incertezza, senza dimostrarlo.

## 5. Conseguenza per la validazione originale (da documentare, non modifica i risultati)

P2d §6 assume gli scenari indipendenti («lo sono: cataloghi e semi distinti») per calcolare
la probabilità di superare il criterio in tutti e cinque (0,984⁵ ≈ 0,92). Con gli stessi
semi per tutti gli scenari, prescritti dallo stesso protocollo (§5), V1–V4 **non** sono
indipendenti: condividono la realizzazione appena descritta. I fallimenti di V1, V2 e V3
non sono quindi tre evidenze indipendenti. Una parte del loro eccesso (circa 0,6 punti nella
frequenza esatta di questa realizzazione) sarebbe presente anche con una procedura esatta.
Questo non cambia il risultato storico (la validazione non è superata) né le conclusioni di
A, B e C, che sono confronti appaiati sugli stessi cataloghi. Una validazione futura deve
usare semi distinti per scenario.

## 6. Prossimo passo proposto

Una verifica di C1 su cataloghi nuovi può essere fatta **analiticamente** (decisione esatta
da z, giustificata dalla concordanza di §3), quindi con molti cataloghi e semi nuovi distinti
per scenario, in pochi minuti. Numerosità, semi, criterio e regola di arresto vanno fissati
in un piano registrato prima dell'esecuzione. Questa verifica riguarda solo C1 e non valida
P2f.

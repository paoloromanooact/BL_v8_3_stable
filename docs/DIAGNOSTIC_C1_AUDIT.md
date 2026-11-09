# Verifica di coerenza di C1: generatore, distribuzione nulla e p-value

Data: 2026-11-09. **Verifica d'implementazione post hoc, non preregistrata**, fatta dopo
aver visto i risultati di C (`docs/DIAGNOSTIC_C_RESULTS.md`); nessuna simulazione nuova,
nessun verdetto. Usa solo output esistenti (`A_BY_CATALOGUE.csv.gz`, `C_RAW_RUN1.csv.gz`).
Script `python/sharpbl/diag_c1_audit.py`; tabelle `results/DIAGNOSTIC/AUDIT_C1_*.csv`.

## 1. Domanda

C1 (modello nullo del generatore) dà circa 3,0–3,15% di falsi verdetti invece del 2,5%. Prima di
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
  controllo 3). È la distribuzione di β̂ sotto il modello del generatore, se la varianza vera
  di A (piano A §3) è corretta: esatta per T5; per T3 a meno della trasformazione
  γ → sin γ → γ (§4).
- **Generatore** (`p2d.synthetic_catalog_p2d`, `p2d.cr_component`): AR(1) con partenza
  stazionaria e innovazioni √(1 − φ²); rumore individuale normale; γ ricostruito senza
  distorsione salvo |γ| > 90° (345 regioni in tutto, A).

## 3. Controlli numerici sui cataloghi esistenti

**Decisione Monte Carlo contro decisione analitica.** Sotto il modello del generatore la decisione si può
calcolare senza simulazione: falso verdetto se |z| > 2,2414, con z = (β̂ − μ)/√V_true (A).
Concordanza con i verdetti Monte Carlo di C1 (`AUDIT_C1_MC_VS_EXACT.csv`): 1998, 1996, 1999,
1999 su 2000 (V1 T3, V1 T5, V4 T3, V4 T5). I casi discordanti hanno |z| entro 0,04 dalla
soglia (errore Monte Carlo del quantile). **La parte Monte Carlo e il calcolo dei p-value
sono coerenti con la distribuzione analitica**; lo scostamento di C1 non nasce lì.

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
`AUDIT_C1_POOLED_INDEPENDENT.csv`): frequenza analitica di |z| > z_0,0125 pari a 2,56% (T3),
2,74% (T5), 2,65% ± 0,13 complessiva su 16 000, cioè circa 1,2 errori sopra il 2,5%.

## 4. Controlli diretti richiesti dalla revisione

Script `python/sharpbl/diag_c1_checks.py`; tabelle `results/DIAGNOSTIC/C1_CHECKS_DIRECT.csv`,
`C1_INPUTS_RESIM_BY_CATALOGUE.csv.gz`, `C1_T3_TRANSFORM.csv`,
`C1_T3_TRANSFORM_BY_CATALOGUE.csv.gz`. Soglia normale z_0,0125 a precisione completa
(`norm.ppf(1 − 0,0125)`); 2,2414 è solo il valore arrotondato nel testo.

**Finitezza di C1.** Il controllo `5_run1_C1_verdicts_valid` di A1 verificava solo che i
verdetti appartenessero all'elenco consentito, il che non esclude simulazioni NaN (il
difetto di C2 lo ha mostrato). Due verifiche dirette, con copertura diversa:
- **ingressi, su tutti i cataloghi** (V1 e V4, T3 e T5: 8000): a_i, σ_i (> 0), B, `const` e
  parametri veri finiti. 0 fallimenti. Ingressi finiti sostengono la stabilità numerica
  della simulazione, ma non sono una verifica diretta delle simulazioni;
- **simulazioni, verifica campionaria** (primi 100 cataloghi per scenario, 400 casi): C1
  rieseguito con gli stessi semi (260000 + 2k + t), tutte le simulazioni finite (0
  fallimenti) e tutti i verdetti uguali a quelli dell'esecuzione 1 (0 differenze). È l'unica
  verifica diretta delle simulazioni: quelle degli altri 3600 casi non sono state rigenerate.

**T3 e la trasformazione γ → sin γ → γ.** Per ogni catalogo di V0–V6 (14 000) la pendenza
calcolata con γ del generatore, senza la trasformazione, è confrontata con quella osservata
(che coincide con quella di A in 14 000 casi su 14 000):

Denominatori (`C1_T3_UNITS.csv`, script `diag_c1_t3_units.py`): 2000 cataloghi per scenario;
11 519 523 regioni nei disegni T3 di ciascuno scenario (uguali tra scenari perché i semi dei
cataloghi sono gli stessi), 80 636 661 in tutto.

| Scenario | Cataloghi con almeno una regione con \|γ\| > 90° | Regioni con \|γ\| > 90° | Max \|Δβ\| (gradi per unità di Â) | Max \|Δβ\| / √V_true | Decisioni analitiche cambiate (\|z\| > z_0,0125) |
|---|---|---|---|---|---|
| V0 | 1 su 2000 | 1 su 11 519 523 | 0,0005 | 0,0004 | 0 su 2000 |
| V1 | 11 su 2000 | 11 su 11 519 523 | 0,017 | 0,007 | 0 su 2000 |
| V2 | 14 su 2000 | 14 su 11 519 523 | 0,017 | 0,005 | 0 su 2000 |
| V3 | 14 su 2000 | 14 su 11 519 523 | 0,017 | 0,004 | 0 su 2000 |
| V4 | 256 su 2000 | 273 su 11 519 523 | 0,010 | 0,003 | 0 su 2000 |
| V5 | 22 su 2000 | 23 su 11 519 523 | 0,051 | 0,014 | 0 su 2000 |
| V6 | 9 su 2000 | 9 su 11 519 523 | 0,016 | 0,003 | 0 su 2000 |
| Totale | 327 su 14 000 | 345 su 80 636 661 | | | 0 su 14 000 |

I due conteggi sono diversi perché un catalogo può contenere più di una di queste regioni.

Nel **confronto analitico** (decisione |z| > z_0,0125 con e senza trasformazione) la
trasformazione è un'**approssimazione senza effetto sulle decisioni nei cataloghi
esaminati**: gli scarti della pendenza sono al più l'1,4% di una deviazione standard di β̂,
nessuna decisione analitica cambia e var(z) è uguale alla quarta cifra decimale. Il confronto
**non** riguarda i verdetti Monte Carlo di C1, che non sono stati ricalcolati con γ del
generatore; dato che le decisioni Monte Carlo e analitiche di C1 concordano in 1996–1999 casi
su 2000 (§3), un effetto sui verdetti Monte Carlo è improbabile, ma non è stato verificato.
Entro questo confronto, la trasformazione non spiega lo scostamento di C1 dal 2,5%.

## 5. Lettura (descrittiva)

- Nessuna discrepanza d'implementazione rilevata tra generatore, distribuzione nulla e
  p-value: la decisione Monte Carlo coincide con quella analitica, e nei gruppi diversi da
  V1–V4 la distribuzione di z è compatibile con N(0, 1).
- Il livello di circa il 3% di C1 in V1 e V4 riflette soprattutto una **sola realizzazione**,
  condivisa da V1–V4, in cui |z| supera la soglia nel 3,05–3,20% dei cataloghi (var(z)
  1,04–1,07, cioè 1,2–2,2 errori sopra 1). Sui gruppi indipendenti la frequenza complessiva
  è 2,65%: compatibile con il 2,5% entro l'incertezza, senza dimostrarlo.

## 6. Conseguenza per la validazione originale (da documentare, non modifica i risultati)

P2d §6 assume gli scenari indipendenti («lo sono: cataloghi e semi distinti») per calcolare
la probabilità di superare il criterio in tutti e cinque (0,984⁵ ≈ 0,92). Con gli stessi
semi per tutti gli scenari, prescritti dallo stesso protocollo (§5), V1–V4 **non** sono
indipendenti: condividono la realizzazione appena descritta. I fallimenti di V1, V2 e V3
non sono quindi tre evidenze indipendenti. Una parte del loro eccesso (circa 0,6 punti nella
frequenza analitica di questa realizzazione) comparirebbe anche con una decisione analitica
basata sulla distribuzione del generatore.
Questo non cambia il risultato storico (la validazione non è superata) né le conclusioni di
A, B e C, che sono confronti appaiati sugli stessi cataloghi. Una validazione futura deve
usare semi distinti per scenario.

## 7. Prossimo passo proposto

Una verifica di C1 su cataloghi nuovi può essere fatta **analiticamente** (decisione analitica
da z, giustificata dalla concordanza di §3), quindi con molti cataloghi e semi nuovi distinti
per scenario, in pochi minuti. Numerosità, semi, criterio e regola di arresto vanno fissati
in un piano registrato prima dell'esecuzione. Questa verifica riguarda solo C1 e non valida
P2f.

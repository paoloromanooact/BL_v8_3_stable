# Risultati del controllo diagnostico A

Data: 2026-11-09. **Sviluppo diagnostico, non validazione e non verdetto**; nessun
risultato, conteggio storico o decisione di P2/P2d/P2e cambia. Piano registrato prima del
codice: `docs/DIAGNOSTIC_A_PLAN.md` (commit `49508e5`, SHA-256 `eb19dd53…`); script
`python/sharpbl/diag_a_variance.py` (commit `5315103`, eseguito ad albero pulito).
Tabelle: `results/DIAGNOSTIC/A_SUMMARY.csv`, `A_CHECKS.csv`, `A_BY_CATALOGUE.csv.gz`.

## 1. Controlli obbligatori (piano §4)

Tutti superati su 28 000 coppie catalogo × test (V0–V6, k = 0…1999, T3 e T5):
parametri e applicabilità ricalcolati identici a quelli della validazione P2e;
rappresentazione lineare di β̂ esatta; medie vera e simulata nulle (≤ 10⁻⁶ √V_true);
generatore e allineamento delle unità ricostruiti. Controllo riportato: 345 regioni in tutto
(su 14 000 cataloghi T3) con |γ| > 90°, dove la rappresentazione di T3 è approssimata:
trascurabile.

## 2. Risultati per scenario

R = V_model / V_true (mediana sui cataloghi applicabili); R_ind e R_tmp: parti individuale e
temporale; R_oracle: con i parametri temporali veri; p: frequenza di falsi verdetti prevista
in approssimazione normale (media sui cataloghi applicabili); "oss.": frequenza osservata
nella validazione P2e tra gli applicabili, con il suo errore binomiale (se).

| Scenario, test | R | R_ind | R_tmp | R_oracle | p prevista | p oracolo | oss. (se) | (p − oss.)/se |
|---|---|---|---|---|---|---|---|---|
| V0 T3 | 1,01 | 0,85 | – | – | 2,55% | – | 2,53% (0,42) | +0,0 |
| V0 T5 | 1,01 | 0,85 | – | – | 2,52% | – | 2,66% (0,44) | −0,3 |
| V1 T3 | 0,96 | 0,85 | 0,98 | 0,97 | 3,02% | 2,73% | 3,45% (0,41) | −1,1 |
| V1 T5 | 0,96 | 0,85 | 0,98 | 0,97 | 3,08% | 2,72% | 3,30% (0,40) | −0,5 |
| V2 T3 | 0,82 | 0,85 | 0,82 | 0,99 | 4,78% | 2,60% | 4,00% (0,44) | +1,8 |
| V2 T5 | 0,82 | 0,85 | 0,82 | 0,99 | 4,93% | 2,59% | 4,55% (0,47) | +0,8 |
| V3 T3 | 0,77 | 0,85 | 0,76 | 0,99 | 5,79% | 2,57% | 4,65% (0,47) | +2,4 |
| V3 T5 | 0,77 | 0,85 | 0,76 | 0,99 | 5,87% | 2,57% | 4,46% (0,46) | +3,1 |
| V4 T3 | 0,92 | 0,93 | 0,92 | 1,00 | 3,78% | 2,52% | 2,90% (0,38) | +2,3 |
| V4 T5 | 0,93 | 0,93 | 0,93 | 1,00 | 3,84% | 2,52% | 3,10% (0,39) | +1,9 |
| V5 T3 | 0,57 | 0,85 | 0,54 | – | 9,30% | – | 9,50% (0,66) | −0,3 |
| V5 T5 | 0,55 | 0,85 | 0,53 | – | 9,84% | – | 9,65% (0,66) | +0,3 |
| V6 T3 | 0,75 | 0,85 | 0,74 | – | 7,44% | – | 7,04% (0,61) | +0,7 |
| V6 T5 | 0,74 | 0,85 | 0,73 | – | 7,50% | – | 5,53% (0,54) | +3,6 |

Miglior AR(1) (R_AR1, mediana): V5 0,64 (T3) e 0,63 (T5); V6 1,10 e 1,16. Correlazione di
Spearman tra R e φ̂ nei cataloghi: 0,77–0,89 in V1–V5, 0,50–0,58 in V6, 0,30–0,34 in V0.
p prevista media nei cataloghi con un falso verdetto osservato e in quelli senza:
per esempio V3 T3 6,3% contro 5,8%, V6 T5 13,2% contro 7,2%.

## 3. Lettura secondo le interpretazioni registrate (piano §5)

- **I1, sufficienza** (|p − oss.| ≤ 2 se): vale in V0, V1, V2, V5 (entrambi i test) e in
  V6 T3, V4 T5; **non vale** in V3 (T3 +2,4 se, T5 +3,1 se), V4 T3 (+2,3 se), V6 T5
  (+3,6 se). Dove non vale, la previsione **supera** la frequenza osservata: la sola
  discrepanza di varianza, in approssimazione normale e trattando i parametri come fissi,
  sovrastima i falsi verdetti; altri fattori (per esempio la dipendenza tra β̂ e parametri
  stimati nello stesso catalogo, o la non normalità) li riducono. Per questi scenari le
  conclusioni seguenti restano parziali.
- **I2, H1** (V1–V3: R_oracle mediano in [0,95; 1,05], p oracolo ≤ 3,0%, R mediano < 0,95,
  p > p oracolo): **soddisfatta in V2 e V3** (R 0,82 e 0,77; R_oracle 0,99; p oracolo 2,6%):
  l'eccesso è coerente con la stima dei parametri temporali entro questo modello, con la
  riserva di I1 per V3. **Non soddisfatta in V1** in senso stretto: R mediano 0,956 (non
  < 0,95), anche se p prevista (3,0%) supera p oracolo (2,7%). R_oracle ≥ 0,95 ovunque: per
  il criterio registrato la parte individuale non è il fattore principale in V1–V3.
- **I3, H2:** coerente. R_tmp mediano 0,92–0,93 in V4 contro 0,82 in V2.
- **I4, H3:** coerente in **V5** (R_AR1 0,63–0,64: anche il miglior AR(1) sottostima la
  varianza temporale di un AR(2)); **non coerente in V6** (R_AR1 1,10–1,16: un AR(1) con
  l'autocorrelazione vera al ritardo 1 sovrastimerebbe la varianza dei salti). In V6 la
  sottostima viene dal φ̂ stimato (0,88, R_tmp 0,74), non da un limite strutturale dell'AR(1)
  sui ritardi lunghi.
- **I5:** nessuna di queste condizioni stabilisce una causa.

## 4. Osservazione non prevista dal piano (da verificare)

R_ind è circa 0,85 in tutti gli scenari con rumore omoschedastico e 0,93 in V4: la parte
individuale simulata (wild bootstrap con correzione per la leva 1/(1 − h_i)) è circa il 15%
più piccola di quella vera. Ipotesi, **formulata dopo aver visto A**: la correzione per la
leva non basta per le regioni di peso grande, che dominano β̂ (con pesi Φ i loro a_i sono i
più grandi e la loro leva nella cella è alta); in V4 il loro rumore è minore e il difetto
pesa meno. In V0 l'effetto è compensato da una componente temporale spuria (σ̂_u² > 0 per
caso), da cui R ≈ 1. In V1–V3 la parte temporale domina e R_oracle resta 0,97–0,99.

## 5. Sintesi

Entro il modello degli scenari:
- V2 e V3 sono coerenti con H1, cioè con una distribuzione nulla troppo stretta per φ̂ e κ̂
  sottostimati;
- V4 è coerente con H2;
- V5 è coerente con H3;
- V6 dipende dal φ̂ stimato;
- la parte individuale è sottostimata di circa il 15% (osservazione post hoc).

La varianza da sola **non** rende conto delle frequenze osservate in V3, V4 T3 e V6 T5, dove
le sovrastima. Il caso V1, che con V2 e V3 ha determinato il fallimento della validazione,
resta al limite: R 0,96, p prevista 3,0%, p osservata 3,4%.

## 6. Decisione su B

Il piano (§6) indica B soprattutto se I1 non vale o se l'attribuzione di I2 non è netta:
entrambe le condizioni si verificano (I1 in V3, V4 T3, V6 T5; I2 in V1). La decisione spetta
all'utente. Un B utile, da registrare prima, eseguirebbe la procedura completa di P2e con i
parametri temporali veri al posto di quelli stimati in V1–V3 (ed eventualmente V4), sugli
stessi cataloghi di sviluppo. La previsione di A è circa 2,6–2,7% di falsi verdetti; se B la
conferma, la stima dei parametri temporali spiega l'eccesso anche senza le approssimazioni di
A. Costo stimato: circa un'ora su 12 processi.

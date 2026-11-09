# Risultati del controllo diagnostico C (componente individuale e leva)

Data: 2026-11-09. **Sviluppo diagnostico, non validazione e non verdetto**; nessun
risultato, conteggio storico o decisione di P2/P2d/P2e cambia.

| Elemento | Riferimento |
|---|---|
| Piano preregistrato | `docs/DIAGNOSTIC_C_PLAN.md` (commit `df63fd2`, SHA-256 `77398d76…`) |
| Implementazione, esecuzione 1 | `python/sharpbl/diag_c_individual.py` (commit `c56779f`); output `results/DIAGNOSTIC/C_*_RUN1.*`, log locale `logs/diag_c_run1.log` |
| Emendamento (non cieco, dopo l'ispezione dell'esecuzione 1) | `docs/DIAGNOSTIC_C_PLAN_A1.md` (commit `f275f0d`) |
| Implementazione, riesecuzione di C2 | `python/sharpbl/diag_c2_a1.py` (commit `555c973`); output `C2_A1_*`, log locale `logs/diag_c2_a1.log` |

**Controlli diretti successivi** (finitezza di C1 e trasformazione di T3):
`docs/DIAGNOSTIC_C1_AUDIT.md` §4.

**Terminologia.** C1 simula la distribuzione di β̂ sotto il modello del generatore (parametri
temporali veri, componente individuale normale con varianza vera). Per T5 la rappresentazione
lineare di β̂ è esatta; per T3 ignora la trasformazione γ → sin γ → γ, che non conserva γ per
|γ| > 90°: nel confronto analitico è un'**approssimazione senza effetto sulle decisioni nei
cataloghi esaminati**
(`docs/DIAGNOSTIC_C1_AUDIT.md` §4). Per questo C1 non è chiamato "modello esatto".

## 1. Esecuzione 1 e validità delle parti

- **C2-T3 dell'esecuzione 1: non valido** e non interpretato. Nelle celle con una sola unità
  il fattore di scala era infinito e le simulazioni NaN; la regola di decisione ha dato
  "quenching supportato" (838 contro 58 di C1). Conservato com'è.
- **C2-T5 dell'esecuzione 1: utilizzabile.** Nessun catalogo T5 ha unità con E[ẽ²] = 0 e
  i verdetti della riesecuzione coincidono con quelli dell'esecuzione 1 (4000 su 4000;
  controllo 4 di A1). Le cifre sotto per C2 sono quelle della riesecuzione.
- **Analitica e C1 dell'esecuzione 1: validi.** Tutte le grandezze finite (16 000 righe
  analitiche, 8000 verdetti C1); ogni catalogo è calcolato in una chiamata indipendente
  (controllo 5 di A1).

## 2. Controlli obbligatori

Piano §5: riproduzione di B con s_i = 1 (100 su 100), somma Σ a_i² E[e_i²] finita e positiva
(4000 su 4000). A1 §4: valori per unità finiti (8000 su 8000); simulazioni finite e nessuno
stato di errore (8000 su 8000); simulazioni del braccio B riprodotte **numericamente
identiche** (40 su 40) e verdetti di B riprodotti (100 su 100); T5 come sopra. Tutti superati.

## 3. Parte analitica (ipotesi H5)

| Scenario | R_ind atteso (mediana; p10–p90) | R_ind di A (mediana) | Differenza | Quota della varianza individuale vera nelle unità con h > 0,3 (sono circa il 2% delle unità) |
|---|---|---|---|---|
| V1 T3 / T5 | 0,864 / 0,863 (0,81–0,89) | 0,851 / 0,846 | +0,013 / +0,017 | 0,32 |
| V2 T3 / T5 | 0,864 / 0,863 | 0,851 / 0,846 | +0,013 / +0,017 | 0,32 |
| V3 T3 / T5 | 0,864 / 0,863 | 0,852 / 0,846 | +0,013 / +0,017 | 0,32 |
| V4 T3 / T5 | 0,936 / 0,936 | 0,930 / 0,927 | +0,006 / +0,009 | 0,19 |

**K1:** soddisfatta (differenze ≤ 0,03): la correzione per la leva 1/(1 − h_i) rende conto
della sottostima della componente individuale osservata in A, coerente con H5. Nel 21% dei
cataloghi T3 c'è almeno una cella con una sola unità, dove il residuo è identicamente nullo
(limite strutturale del bootstrap dei residui di cella; `DIAGNOSTIC_C_PLAN_A1.md` §2); in T5
nessuna.

## 4. Bracci simulati (2000 cataloghi per scenario e test; frequenze tra gli applicabili, tutti applicabili)

| Scenario, test | P2e originale | B (parametri temporali veri) | **C2** (B + componente individuale corretta) | **C1** (modello nullo del generatore) | CP di C2 |
|---|---|---|---|---|---|
| V1 T3 | 3,45% (69) | 3,50% (70) | 3,15% (63) ± 0,39 | 3,00% (60) ± 0,38 | 3,87% |
| V1 T5 | 3,30% (66) | 3,35% (67) | 3,05% (61) ± 0,38 | 3,15% (63) ± 0,39 | 3,76% |
| V4 T3 | 2,90% (58) | 3,00% (60) | 2,95% (59) ± 0,38 | 3,10% (62) ± 0,39 | 3,65% |
| V4 T5 | 3,10% (62) | 3,10% (62) | 3,10% (62) ± 0,39 | 3,00% (60) ± 0,38 | 3,82% |

**Confronti appaiati per catalogo** (falsi verdetti in entrambi / solo nel primo / solo nel
secondo; p esatto sui discordanti, **descrittivo**):

| | V1 T3 | V1 T5 | V4 T3 | V4 T5 |
|---|---|---|---|---|
| B contro C2 (stessi numeri casuali) | 63 / 7 / 0 | 61 / 6 / 0 | 59 / 1 / 0 | 62 / 0 / 0 |
| B contro C1 (stessi cataloghi, semi interni diversi) | 60 / 10 / 0 (p 0,002) | 62 / 5 / 1 (p 0,22) | 59 / 1 / 3 | 60 / 2 / 0 |
| C2 contro C1 | 59 / 4 / 1 (p 0,38) | 59 / 2 / 4 (p 0,69) | 58 / 1 / 4 | 60 / 2 / 0 |

I falsi verdetti dipendono soprattutto dal catalogo (β̂ estremo) e poco dai numeri casuali
della calibrazione interna: anche con semi diversi, B e C1 condividono 59–62 cataloghi.

## 5. Lettura secondo le interpretazioni registrate

- **K0 — controllo di base: soddisfatto** secondo il criterio registrato: C1 è entro 2 errori
  binomiali dal 2,5% in V1 e V4, per T3 e T5 (+1,3, +1,7, +1,5, +1,3 errori).
  **Questo non dimostra che il livello sia il 2,5%.** Le quattro frequenze sono tutte sopra
  il 2,5%, ma non sono osservazioni indipendenti: V1 e V4 usano gli stessi semi dei
  cataloghi e della calibrazione interna, e i loro falsi verdetti C1 cadono in gran parte
  negli stessi cataloghi (45 su 60–62 in T3, 39 su 60–63 in T5). Per T3 e T5 dello stesso
  scenario i cataloghi con falso verdetto in comune sono 2, contro circa 1,9 attesi se le
  decisioni fossero indipendenti: non c'è evidenza di associazione, ma questo **non dimostra**
  l'indipendenza (T3 e T5 condividono il disegno del catalogo).
  Lo scostamento positivo resta un punto da controllare con cataloghi nuovi.
- **K2 — V1:** C2 è entro 2 errori binomiali da C1 (+0,15 e −0,10 punti) e ha limite CP
  ≤ 4%. Per il criterio registrato, la sottostima della componente individuale è coerente con
  l'eccesso residuo di B in V1. Rispetto a B, la correzione toglie 7 (T3) e 6 (T5) falsi
  verdetti e non ne aggiunge.
- **K2 — V4:** B, C2 e C1 coincidono entro l'incertezza; in V4 non c'era un eccesso residuo
  da spiegare (componente individuale meno sottostimata, R_ind ≈ 0,93).
- **K3:** nessuna condizione stabilisce una causa; un limite CP ≤ 4% non dimostra il livello
  nominale del 2,5%.

## 6. Quadro descrittivo di V1 (indizio, non attribuzione)

Falsi verdetti T3 / T5 su 2000:
- P2e originale: 69 / 66;
- con i parametri temporali veri (B): 70 / 67, nessun guadagno netto;
- correggendo anche la componente individuale (C2): 63 / 61;
- con il modello nullo del generatore (C1): 60 / 63.

Il limite di accettazione era 65. Correggendo la componente individuale, C2 dà frequenze
vicine a C1 e rispetta il limite CP previsto; la vicinanza non dimostra equivalenza. Anche un
test esatto al 2,5% produce falsi verdetti (circa 50 attesi su 2000): la presenza dei circa
60 cataloghi con falso verdetto in C1 **non** è una causa aggiuntiva del fallimento. La
questione aperta è lo **scostamento dal nominale** (circa 3,0–3,15% invece di 2,5%): se sia
una fluttuazione di questi 2000 cataloghi, un difetto di implementazione o un effetto
strutturale non è stabilito.

## 7. Stato della diagnosi (punto 4)

Entro il modello degli scenari:
- **V2–V3:** la stima dei parametri temporali è coerente con la maggior parte dell'eccesso
  (A, B).
- **V1:** la componente individuale sottostimata dalla correzione per la leva, incluse le
  celle con una sola unità, è coerente con l'eccesso residuo (C): correggendola, C2 dà
  frequenze vicine a C1 e rispetta il limite CP (vicinanza, non equivalenza).
- **Tutti gli scenari:** con il modello nullo del generatore resta un livello di circa il 3,0–3,15% sugli
  stessi cataloghi, da verificare con cataloghi nuovi prima di qualunque conclusione.
- **Non applicabile alla procedura reale:** il termine oracolo di A1 usa la varianza vera.
  Una procedura per i dati reali avrebbe bisogno di un metodo diverso per la componente
  individuale. Questo è materiale per la valutazione di P2f (punto 5), non una soluzione.

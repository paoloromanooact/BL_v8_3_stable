# Risultati del controllo diagnostico D (livello di C1 su cataloghi nuovi)

Data: 2026-11-09. **Sviluppo diagnostico, non validazione di P2f e non verdetto**; nessun
risultato, conteggio storico o decisione di P2/P2d/P2e cambia.

| Elemento | Riferimento |
|---|---|
| Piano preregistrato | `docs/DIAGNOSTIC_D_PLAN.md` (commit `ef56df9`, SHA-256 `e530af4a…`) |
| Emendamento A1, prima di codice e risultati | `docs/DIAGNOSTIC_D_PLAN_A1.md` (commit `cfddaee`, SHA-256 `120fc46d…`) |
| Implementazione | `python/sharpbl/diag_d_new_seeds.py` (commit `b1f8eaf`; provata solo sui cataloghi di sviluppo con `--dev`, output di prova cancellati) |
| Esecuzione unica | 2026-11-09, 18:06–19:01, albero pulito; output `results/DIAGNOSTIC/D_*`, log locale `logs/diag_d.log` |

## 1. Controlli obbligatori (piano §5)

Tutti superati:
- semi nuovi, distinti e senza sovrapposizioni con quelli usati;
- codice invariato rispetto ad A sul catalogo di sviluppo k = 0 di V1 e V4 (4 su 4);
- β̂, μ e V_true finiti con V_true > 0, e |μ| ≤ 10⁻⁶ √V_true (100 000 su 100 000);
- simulazioni Monte Carlo del campione finite (400 su 400);
- decisioni Monte Carlo e analitiche concordi salvo casi vicini alla soglia. C'è un solo caso
  discordante, V4 T3 k = 49, con |z| = 2,229 contro la soglia 2,241.

## 2. Criteri (piano §4 con A1 §3; errore raggruppato per catalogo (scenario, k))

| Criterio | Scenari, test | Indicatori / cataloghi | f | SE | (f − 2,5%)/SE | Esito |
|---|---|---|---|---|---|---|
| **D1** (principale) | V1, V4; T3, T5 | 40 000 / 20 000 | 2,485% | 0,078 punti | −0,19 | **compatibile con il 2,5% nella nuova prova** |
| D2 | V0–V4; T3, T5 | 100 000 / 50 000 | 2,506% | 0,049 punti | +0,12 | compatibile con il 2,5% nella nuova prova |

## 3. Per scenario e test (D3, descrittivo; 10 000 cataloghi ciascuno)

| Scenario | f T3 (z) | f T5 (z) | var(z) T3 / T5 (errore 0,014) |
|---|---|---|---|
| V0 | 2,61% (+0,7) | 2,71% (+1,3) | 0,993 / 1,014 |
| V1 | 2,52% (+0,1) | 2,57% (+0,4) | 0,992 / 1,008 |
| V2 | 2,38% (−0,8) | 2,29% (−1,4) | 1,013 / 1,006 |
| V3 | 2,71% (+1,3) | 2,42% (−0,5) | 1,031 / 0,984 |
| V4 | 2,53% (+0,2) | 2,32% (−1,2) | 1,006 / 0,987 |

Nessuna frequenza è oltre 2 errori dal 2,5%. Tra le varianze di z, una sola cella è oltre 2
errori da 1 (V3 T3, 1,031, +2,2), in linea con quanto atteso per caso su 10 celle; non se ne
trae nessuna conclusione.

## 4. Lettura secondo il piano (§4, §6; A1 §5)

- **D1:** nella nuova prova, con cataloghi indipendenti e semi distinti per scenario, la
  decisione al 2,5% sotto il modello nullo del generatore dà una frequenza **compatibile con
  il 2,5%**, così come per D2. Questo non dimostra il livello nominale (D4). Il risultato
  riguarda il modello del generatore e la decisione analitica; la concordanza con la
  decisione Monte Carlo è verificata sul campione di 400 casi.
- Lo scostamento di C1 nei cataloghi di sviluppo (3,0–3,15% in V1 e V4) è quindi **coerente
  con una proprietà della realizzazione di sviluppo**, condivisa da V1–V4
  (`docs/DIAGNOSTIC_C1_AUDIT.md`), e non con un difetto del generatore, della rappresentazione
  o della decisione rilevabile a questa precisione (errore circa 0,08 punti).
- **Regola di arresto (§6):** il livello è compatibile, quindi la diagnosi di C1 si chiude e
  il passo successivo è la progettazione di P2f (punto 5 della lista operativa). D non
  valida P2f.

## 5. Conseguenze per la diagnosi complessiva (punto 4)

Entro il modello degli scenari e sui cataloghi di sviluppo:
- la sottostima dei parametri temporali è coerente con la maggior parte dell'eccesso in
  V2–V3 (A, B);
- la componente individuale sottostimata dalla correzione per la leva, incluse le celle con
  una sola unità, è coerente con l'eccesso residuo in V1 (C);
- il livello di circa il 3% che restava con il modello nullo del generatore è coerente con la
  realizzazione condivisa dei cataloghi di sviluppo (D).

Per P2f restano da progettare una stima dei parametri temporali meno distorta e una gestione
della componente individuale utilizzabile sui dati reali; il termine oracolo di C non lo è.
P2f andrà validato con semi nuovi e **distinti per scenario**, con regola di arresto e
condizioni fissate prima dell'esecuzione.

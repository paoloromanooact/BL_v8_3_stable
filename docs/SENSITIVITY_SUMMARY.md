# Quadro delle sensibilità: ricomparse candidate e istante della misura

Data: 2026-11-09. **Descrittivo, nessun verdetto.** Raccoglie sensibilità già eseguite
(P1d/P1e, P2 S5 e S8) e aggiunge solo aggregazioni del catalogo P1 già esistente.
Tabelle: `results/DIAGNOSTIC/SENS_*.csv`, rigenerate da `python/sharpbl/diag_summary.py`.

## 0. Varianti già disponibili (verificate sui file)

- Somme P1 per CR ed emisfero (`results/P1/P1_SBL_BY_CR_HEMISPHERE.csv`): varianti A, B, C,
  D, E, L. E = A con le sole HARP originali (`family_rank` = 0; P1d §2, regola di P1e).
- Test P2 (`results/P2/P2_T*.csv`): S, S1–S8, L. S5 = record di controllo al posto del
  primario; S8 = S senza ricomparse candidate.
- P1e usa **una sola** regola di associazione (finestre ±3°/±6° fissate nel protocollo): non
  esistono varianti con finestre diverse, e non se ne aggiungono ora.
- Il confronto primario–controllo per HARP è in `results/EXPLORATORY/PRIMARY_VS_CONTROL*.csv`
  (`docs/EXPLORATORY_RESULTS.md` §4).

Non si calcolano per ora incertezze bootstrap dei rapporti né nuove finestre: non servono
per questo riepilogo descrittivo.

## 1. Effetto sui test (`SENS_TESTS.csv`)

Attività `A_monthly`; intervalli bootstrap di P2 al 95%, **senza copertura garantita**
(`docs/P2_DECISION_DESCRIPTIVE_FALLBACK.md`). Ogni variante usa il **proprio** campione.

| Test | S (principale) | S8 (senza ricomparse candidate) | S5 (record di controllo) |
|---|---|---|---|
| T3, gradi per unità di Â | −3,6 [−7,5; 0,7]; 2485 regioni, 210 CR | −3,8 [−8,1; 0,8]; 2102, 208 | −3,3 [−7,2; 1,2]; 4001, 219 |
| T4, gradi per unità di Â | −0,63 [−1,10; −0,12] | −0,63 [−1,14; −0,04] | −0,58 [−1,08; 0,02] |
| T5, β_η (D*) | −1,5·10⁻²⁶ [−7,5; 4,9]·10⁻²⁶; 318 celle | −1,3·10⁻²⁸ [−7,0; 7,9]·10⁻²⁶; 305 celle | +2,1·10⁻²⁶ [−2,6; 7,3]·10⁻²⁶; 355 celle |

**Normalizzazione di T5.** η̄ = media delle η di cella pesata con ΣΦ, sulle celle di T5
(almeno 3 regioni). Campione S: η̄ = 3,56·10⁻²⁵ G/Mx (il valore 3,6·10⁻²⁵ citato in
`docs/P2_RESULTS_DESCRIPTIVE.md`); S8: 3,32·10⁻²⁵; S5: 2,53·10⁻²⁵. β_η / η̄:

| | con η̄ di S | con η̄ propria |
|---|---|---|
| S | −0,042 [−0,21; +0,14] | −0,042 |
| S8 | −0,0004 [−0,20; +0,22] | −0,0004 |
| S5 | +0,058 [−0,07; +0,21] | +0,082 |

Le differenze tra varianti stanno dentro gli intervalli. Nessuna di queste stime è un
verdetto: una pendenza negativa non dimostra il quenching; una vicina a zero non dimostra
un'efficienza costante.

## 2. Effetto sulle somme (`SENS_SUMS.csv`, `SENS_SUMS_RATIOS.csv`)

Record validi (`valid_bl` = 1); ciclo ed emisfero del record stesso. Somme **nette**
(con segno) e **assolute**; le nette risentono delle cancellazioni tra contributi di segno
opposto, quindi i rapporti tra somme nette vanno letti con le assolute accanto.

**Ricomparse candidate** (rispetto ad A, record primari; campione proprio):

| Ciclo / emisfero | n A | ricomparse (n, %) | S_BL netta E/A | Σ\|S_BL\| E/A | D_bal netta E/A | Φ E/A |
|---|---|---|---|---|---|---|
| 24 N | 1112 | 128 (11,5%) | 0,72 | 0,77 | 0,72 | 0,78 |
| 24 S | 1007 | 91 (9,0%) | 0,75 | 0,76 | 0,76 | 0,83 |
| 25 N | 1010 | 89 (8,8%) | 0,72 | 0,74 | 0,71 | 0,77 |
| 25 S | 1060 | 102 (9,6%) | 0,72 | 0,76 | 0,72 | 0,76 |

Le ricomparse candidate sono il 9–12% dei record primari validi ma portano il 23–26% di
Σ|S_BL| e il 17–24% di ΣΦ. Il peso elevato è **compatibile** con regioni grandi e longeve;
questa spiegazione non è verificata. P1e non dimostra che una candidata sia la stessa
regione, e una ricomparsa può contenere flusso nuovo: la variante E è una sensibilità, non
una serie corretta.

Per singola cella CR × emisfero (`SENS_SUMS_CELLS_E_VS_A.csv`): E cambia 235 celle su 424;
la mediana di |E − A| su tutte le celle è il 5,0% della mediana di |A| per S_BL (4,5% per
D_bal, 6,6% per Φ); sulle sole celle cambiate è il 54% (S_BL), 53% (D_bal), 34% (Φ).
Controllo: la somma di S_BL della variante A sulle celle coincide con quella del catalogo.

**Record di controllo al posto del primario.** Il confronto mescola selezione (il controllo
è il record di flusso massimo entro ±60°, più spesso valido), posizione sul disco ed
evoluzione; non va letto come effetto dell'evoluzione.

| Ciclo / emisfero | n controllo / n A (campione proprio) | S_BL netta | Σ\|S_BL\| | Φ | n (HARP comuni) | S_BL netta | Σ\|S_BL\| | Φ |
|---|---|---|---|---|---|---|---|---|
| 24 N | 1547 / 1112 | 1,67 | 1,66 | 2,18 | 1095 | 1,66 | 1,63 | 2,08 |
| 24 S | 1394 / 1007 | 1,51 | 1,59 | 2,02 | 986 / 985 | 1,50 | 1,56 | 1,94 |
| 25 N | 1395 / 1010 | 1,19 | 1,55 | 1,98 | 993 / 991 | 1,18 | 1,53 | 1,91 |
| 25 S | 1503 / 1060 | 1,38 | 1,47 | 1,89 | 1030 / 1033 | 1,38 | 1,45 | 1,83 |

"HARP comuni" = HARP con primario e controllo entrambi validi; i conteggi per ciclo ed
emisfero possono differire di poche unità perché ciclo o emisfero del record di controllo
possono differire da quelli del primario. Nel ciclo 25 nord il rapporto netto (1,19) è
molto più basso di quello assoluto (1,55): effetto delle cancellazioni.

## 3. Che cosa manca

Non serve altro per chiudere il riepilogo descrittivo. Restano possibili, ma non pianificati:
incertezze dei rapporti, dipolo cumulato con la variante E, finestre di associazione
alternative (richiederebbero un nuovo protocollo).

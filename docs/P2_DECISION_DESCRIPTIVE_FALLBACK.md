# Decisione su P2: T3 e T5 descrittivi (ripiego di P2d §6)

Data: 2026-11-03. Basata sulla validazione di P2e (`results/P2/P2E_VALIDATION*.csv`,
`P2E_ACCEPTANCE.csv`; commit dei risultati `3da29da`, eseguita al commit `3fcd702`).

## Esito della validazione

Il criterio di accettazione congelato (P2d §6, con P2e: limite superiore
unilaterale al 95% di Clopper–Pearson della frazione di falsi verdetti ≤ 4%,
cioè al massimo 65 su 2000, in tutti gli scenari correttamente specificati
V0–V4) **non è soddisfatto né da T3 né da T5**: superano il limite gli
scenari V1 (69 e 66 falsi verdetti su 2000), V2 (80, 91) e V3 (93, 89). Gli
scenari di robustezza confermano la cautela: AR(2) circa 9,5%, salti di
livello 4,9–6,2%. Nessuna nuova procedura (P2f) viene avviata ora.

## Che cosa è accertato e che cosa no (aggiunto il 2026-11-09)

È accertato solo il mancato superamento della validazione statistica. Il
mancato verdetto **non** va attribuito automaticamente al numero di cicli (due
cicli HMI): il ruolo distinto di numerosità, dipendenza temporale e stima del
rumore non è ancora chiarito. Elementi già presenti in `P2E_VALIDATION.csv`,
da diagnosticare prima di un eventuale P2f:
- il criterio è soddisfatto in V0 (senza persistenza) e in V4 (AR(1), φ = 0,8,
  rumore eteroschedastico), non in V1–V3 (AR(1), φ = 0,5–0,8);
- V2 e V4 hanno lo stesso φ ma esito diverso;
- in V0 il test non è applicabile nel 31–32% dei cataloghi (ripiego), con φ̂
  al bordo nel 55–58% dei casi.

## Formulazione da usare nel rapporto e nell'articolo

> T3 e T5 sono presentati come analisi descrittive. La procedura inferenziale
> non ha superato il criterio di calibrazione prestabilito; pertanto non si
> formulano verdetti confermativi a favore o contro il quenching.

## Accortezze di presentazione

- Gli intervalli (P2, P2b) e i p-value Monte Carlo (P2d/P2e) restano
  visibili, ma la loro copertura o il loro livello nominale **non sono
  garantiti** negli scenari problematici: un intervallo che esclude zero o un
  p-value piccolo **non** autorizza un verdetto.
- Le potenze della validazione (V1: T3 0,57, T5 0,90; V2: T3 0,33, T5 0,56)
  descrivono una procedura che **non** ha superato la calibrazione: non sono
  potenze di un test validato al 2,5%.
- Il ripiego non invalida C1 (P3) né dimostra l'assenza di quenching:
  significa che la procedura non controlla abbastanza bene i falsi verdetti
  per sostenere una conclusione confermativa. La questione inferenziale sul
  quenching resta aperta.
- La validazione negativa si conserva integralmente (tabelle, dati grezzi,
  parametri, potenza).

## Effetto sul codice

`run_p2.py` legge `results/P2/P2E_ACCEPTANCE.csv`: per ogni test non
accettato la colonna `verdict_final` vale "descrittivo (ripiego P2d §6)" e i
verdetti di P2, P2b e P2d si riportano solo come informazione storica, con la
nota che non costituiscono verdetti.

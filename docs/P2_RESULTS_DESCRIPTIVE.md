# Risultati di P2 sui dati reali — solo descrittivi

Serie P1 completa e validata (commit dei risultati `120f852`, eseguita al
commit `3947ee8`). Esecuzione di P2: `python/sharpbl/run_p2.py`; tabelle in
`results/P2/P2_*.csv`, `P2B_*.csv`, `P2D_TESTS.csv`.

> T3 e T5 sono presentati come analisi descrittive. La procedura inferenziale
> non ha superato il criterio di calibrazione prestabilito; pertanto non si
> formulano verdetti confermativi a favore o contro il quenching.
> (`docs/P2_DECISION_DESCRIPTIVE_FALLBACK.md`)

**Lettura degli intervalli.** Gli intervalli sotto vengono dal bootstrap di
P2 (CR intere) o di P2b (blocchi mobili). La validazione di P2d/P2e ha mostrato
che, con residui correlati tra rotazioni, questo tipo di procedura non
mantiene il livello nominale: la loro copertura **non è garantita** e un
intervallo che esclude zero **non** autorizza un verdetto.

## Campione

Campione principale S: 2485 regioni (Φ ≥ 10²¹ Mx, valide, almeno 20 pixel per
polarità, nessuna regione AMBIGUOUS), 210 rotazioni di Carrington. T5: 318
celle CR × emisfero con almeno 3 regioni (2375 regioni, 176 CR).

## T1 — legge di Joy (controllo, invariato rispetto a P2)

γ = γ0 sin|λ|, pesato con Φ: γ0 = **24,1°** [20,7; 27,6] (IC 95%). Per ciclo ed
emisfero: c24N 25,5° [17,1; 34,3], c24S 20,3° [14,5; 26,3], c25N 29,2°
[21,8; 36,4], c25S 21,7° [15,9; 28,2]. Verdetto di P2: "legge di Joy presente".

## T2 — tilt tra cicli a pari fase (descrittivo per P2)

γ0(ciclo 25) − γ0(ciclo 24) = **+3,3°** [−4,1; 10,1] (2238 regioni): differenza
stimata positiva ma incerta.

## T3 — tilt contro attività dentro il ciclo (descrittivo)

β_T (gradi per unità di attività normalizzata, A_monthly) = **−3,6**
[−7,5; 0,7] (IC 95%, CR intere); [−8,0; 1,3] (IC 97,5%). Rispetto a γ0:
circa −0,15 per unità di Â. Blocchi mobili (P2b): L = 3 [−7,8; 1,8], L = 6
[−8,0; 2,5], L = 13 [−7,7; 2,4]. Con altre misure di attività: A_smooth13
−3,6 [−9,0; 2,4]; A_usflux −4,6 [−7,9; −0,8]. Segno della stima nelle
sensibilità S1–S6: negativo in 6 su 6. p-value Monte Carlo P2d/P2e (solo
informativo, procedura non accettata): p_basso = 0,21.

## T4 — latitudine contro attività dentro il ciclo (descrittivo per P2)

β_L (gradi per unità di Â) = **−0,63** [−1,10; −0,12]; A_smooth13 −1,00
[−1,99; 0,02]; A_usflux −0,42 [−0,70; −0,002]. Pendenza descrittiva
**negativa**, opposta alla previsione considerata (β_L > 0). Un intervallo che
esclude zero, con copertura non garantita, non basta a stabilire una
contraddizione fisica.

## T5 — efficienza della sorgente contro attività (descrittivo)

β_η (D* per unità di flusso, per unità di Â) = **−1,5·10⁻²⁶** [−7,5·10⁻²⁶;
4,9·10⁻²⁶] (IC 95%); rispetto all'efficienza media η̄ = 3,6·10⁻²⁵ G/Mx è
circa −0,04 per unità di Â [−0,21; +0,14]. Blocchi mobili: intervalli
analoghi, tutti comprendono zero. Con S* al posto di D*, con il fattore di
latitudine (λ_R = 8°, 12°, 15°) e con le altre misure di attività gli
intervalli comprendono zero. Sensibilità S1–S6: stesso segno in 5 su 6.
P2d/P2e: **non applicabile** sui dati reali (κ non stimabile, P2d §3).

## Diagnostica (P2b §3, P2d §7)

Autocorrelazione delle medie per CR dei residui: ritardo 1 = 0,16 (T3) e 0,13
(T5), al livello della banda ±1,96/√N (0,14–0,15); ai ritardi 2–13 tra −0,16 e
+0,16. Parametri stimati con P2e: T3 φ̂ = 0,53, κ̂ = −0,85; T5 φ̂ = 0,91,
κ̂ non stimabile. La diagnostica informa sul modello dei residui e non
stabilisce un "ρ vero".

## T0 — potenza sul disegno reale (informativo, procedura di P2 non validata)

Rilevamento con la regola di P2 per β_T = −0,1/−0,2/−0,3·γ0: 0,04 / 0,13 /
0,35; falsi positivi senza effetto iniettato 0,035. Sono frequenze di
rilevamento della procedura di P2, **non validata**, sul disegno reale: non
sono potenze di un test validato al 2,5% e non dimostrano da sole che due
cicli HMI siano intrinsecamente insufficienti.

## Sintesi descrittiva

Sui cicli 24–25 la legge di Joy è chiaramente presente. Dentro il ciclo, la
pendenza del tilt rispetto all'attività è stimata negativa in tutte le
varianti (il verso atteso da un quenching del tilt), con intervalli che in
genere comprendono zero. Per l'efficienza della sorgente la pendenza stimata è
vicina a zero, con ampia incertezza: non è dimostrata l'assenza di un effetto.
La latitudine di emersione ha una pendenza descrittiva negativa, opposta alla
previsione considerata. Tra i cicli, la differenza del coefficiente di Joy è
stimata positiva ma incerta. Nessuna di queste osservazioni costituisce un
verdetto: la questione inferenziale sul quenching resta aperta.

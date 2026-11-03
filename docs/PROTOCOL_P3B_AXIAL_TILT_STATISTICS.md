# Protocollo P3b — Statistiche del tilt come dato assiale (emendamento di P3)

Stato: **congelato il 2026-11-03** (commit), prima di eseguire P3. Modifica **solo** la riga del tilt nella tabella di P3 §5 e il
paragrafo "Tilt come asse del bipolo"; il resto di P3 (SHA-256 `37e10421…`)
resta valido. Informazioni già viste: `docs/SEEN_BEFORE_FREEZE_2026-11-03.md`
(nessun abbinamento con BARD è stato eseguito).

## 0. Perché

In P3 lo Spearman del tilt si calcolava dopo aver portato il nostro valore nel
ramo più vicino a quello di BARD (γ_BARD + Δγ). Così la rappresentazione del
nostro tilt dipende dal riferimento con cui viene correlato: i ranghi possono
cambiare e l'accordo può apparire migliore. Non è solo una questione grafica.

## 1. Misura principale: distanza angolare assiale

Il tilt γ è un **asse** (definito modulo 180°). Per ogni coppia abbinata:
δ = |((γ_nostro − γ_BARD + 90°) mod 180°) − 90°|, con δ ∈ [0°, 90°].

**Misura principale:** mediana di δ, con intervallo al 95% dal bootstrap per
famiglie di P3 §5 (2000 ricampionamenti, seme 20261108).
**Criterio operativo:** mediana di δ ≤ 10° (stessa soglia e motivazione di P3).

## 2. Associazione per dati assiali (sostituisce lo Spearman di P3)

Si raddoppiano gli angoli (a = 2γ_nostro, b = 2γ_BARD, che sono angoli
circolari ordinari) e si calcola la **correlazione circolare di Fisher & Lee
(1983, Biometrika 70, 327)**, nella forma di calcolo:

ρ_FL = 4(A·B − C·D) / √[(n² − E² − F²)(n² − G² − H²)],

con A = Σ cos a_i cos b_i, B = Σ sin a_i sin b_i, C = Σ cos a_i sin b_i,
D = Σ sin a_i cos b_i, E = Σ cos 2a_i, F = Σ sin 2a_i, G = Σ cos 2b_i,
H = Σ sin 2b_i (somme su i = 1..n). ρ_FL ∈ [−1, 1] non dipende dalla scelta
dell'origine o del ramo degli angoli. Verifica numerica (dati simulati, prima
del congelamento): la forma di calcolo coincide con la definizione per coppie
Σ_{i<j} sin(a_i−a_j) sin(b_i−b_j) / √[Σ sin²(a_i−a_j) Σ sin²(b_i−b_j)] fino
alla sesta cifra, e non cambia se si cambia il ramo di uno dei due angoli.

Si riporta con il suo intervallo al 95% (stesso bootstrap per famiglie).
**Criterio operativo:** limite inferiore dell'intervallo al 95% di ρ_FL > 0
(associazione positiva presente). Non si fissa una soglia sul valore: per
questa misura non abbiamo un riferimento di letteratura su cui motivarla, e la
concordanza quantitativa è già nel criterio su δ.

## 3. Spearman su rappresentazione fissa (solo descrittivo)

Si riporta anche lo Spearman tra γ_nostro e γ_BARD, entrambi nella
rappresentazione **fissa** [−90°, 90°), senza alcun allineamento di ramo.
Limite dichiarato: per assi vicini a ±90° (bipoli quasi nord-sud) il salto tra
−90° e +90° può alterare i ranghi; per questo non ha criterio.

## 4. Casi non definiti e repliche degeneri

- ρ_FL è **non definita** se n < 3 o se un fattore del denominatore è ≤ 0
  (per esempio tutti gli assi uguali). Sul campione: il criterio di §2 è
  "non valutabile" e quindi **non soddisfatto**.
- Nel bootstrap una replica è **degenere** se ρ_FL non è definita in quella
  replica. Le repliche degeneri **non si eliminano in silenzio**: si riporta
  il loro numero; l'intervallo si calcola sulle repliche definite; se le
  degeneri sono più dell'1% l'intervallo è segnalato come "instabile" e il
  criterio di §2 è "non valutabile", quindi non soddisfatto.
- La mediana di δ è definita per n ≥ 1; con n = 0 il criterio di §1 è "non
  valutabile" e non soddisfatto.

## 5. Tabella di P3 §5, riga del tilt (sostituita)

| Grandezza | Statistica | Criterio operativo |
|---|---|---|
| γ (asse) | mediana di δ con IC 95%; ρ_FL con IC 95%; Spearman su rappresentazione fissa | mediana δ ≤ 10° **e** limite inferiore IC 95% di ρ_FL > 0; Spearman solo riportato |

**I due criteri devono essere soddisfatti entrambi.** Il limite inferiore di
ρ_FL sopra zero indica solo un'associazione positiva, non un accordo
sufficiente; l'accordo quantitativo è il criterio sulla mediana di δ.

**Cambiamento della regola di decisione.** P3b sostituisce il criterio di P3
"Spearman ρ ≥ 0,6 e mediana |Δγ| ≤ 10°" con "mediana δ ≤ 10° e limite
inferiore IC 95% di ρ_FL > 0". Cambia lo stimatore **e** la regola: la soglia
0,6 sulla correlazione scompare, sostituita da un requisito più debole di
associazione positiva; il requisito sull'accordo (δ ≤ 10°) resta invariato.

Polarità leading e segno Hale restano verifiche separate, come in P3.

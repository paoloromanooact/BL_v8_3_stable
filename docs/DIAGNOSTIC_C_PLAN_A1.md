# Emendamento A1 al piano del controllo diagnostico C (braccio C2)

Stato: **registrato il 2026-11-09 dopo l'ispezione della prima esecuzione di C e prima della
riesecuzione di C2.** Emendamento **non cieco**: è scritto dopo aver visto, nel log della
prima esecuzione, gli avvisi di divisione per zero nel braccio C2. Il piano originale
(`docs/DIAGNOSTIC_C_PLAN.md`, commit `df63fd2`, SHA-256 `77398d76…`) resta agli atti e
invariato; A1 sostituisce solo quanto indicato sotto.

## 1. Che cosa è successo nella prima esecuzione

Nelle celle CR × emisfero con una sola unità la leva è h_i = 1: il residuo di cella è
identicamente nullo (e_i = 0) e anche E[e_i²] = 0 (piano §3.1). Il fattore di C2
s_i = √(σ_i² / E[ẽ_i²]) diventa infinito e il termine a_i ẽ_i s_i vale 0 · ∞ = NaN; la
simulazione nulla del catalogo diventa NaN e la regola di decisione, con confronti falsi su
NaN, dà p = 1/(M + 1) e quindi un verdetto. Il piano non prevedeva il caso; il controllo
obbligatorio 2 riguardava solo la somma.

**Decisioni sulla prima esecuzione:**
- **C2-T3 non valido.** Si conserva com'è (output con suffisso `_RUN1`, log
  `logs/diag_c_run1.log`) e non si interpreta.
- **C2-T5 utilizzabile solo se verificato:** T5 usa celle con almeno 3 regioni; lo si
  considera utilizzabile solo se, ricalcolati, tutti i fattori di scala e i termini
  individuali risultano finiti in ogni catalogo. In ogni caso C2 si riesegue per intero con
  A1 (§3), e il confronto con la prima esecuzione per T5 è un controllo (§4).
- **Parte analitica e C1** non usano s_i: si verificano finiti e non contaminati (§4) e,
  superate le verifiche, si interpretano come previsto dal piano.

## 2. Limite strutturale (osservazione)

Da un residuo di cella identicamente nullo il bootstrap dei residui non può ricostruire il
rumore individuale: nelle celle con una sola unità la procedura P2e simula una componente
individuale nulla. Questo è coerente con il meccanismo dell'ipotesi H5 (leva), ma non ne
quantifica il contributo complessivo ai falsi verdetti; lo fanno, nei limiti del piano, la
parte analitica e C2.

## 3. Modifica del braccio C2

- Per le unità con E[ẽ_i²] > 0: termine a_i ẽ_i s_i v_i come nel piano (Rademacher, stessa
  sequenza casuale di B).
- Per le unità con E[ẽ_i²] = 0 (celle con una sola unità): il termine bootstrap è nullo e si
  aggiunge un termine gaussiano **a_i σ_i z_i**, con z_i ~ N(0, 1) da un **generatore
  separato** (semi 360000 + 2k per T3, 360001 + 2k per T5), così che la sequenza casuale
  del braccio B resti intatta.
- Il termine usa la **varianza vera**: è un controllo **oracolo**, non una soluzione
  applicabile ai dati reali.
- Si riesegue **solo C2** (V1 e V4, T3 e T5, k = 0…1999); C1 e la parte analitica non si
  rieseguono.

## 4. Controlli obbligatori aggiunti

Un NaN non deve mai produrre un verdetto: o ferma il calcolo, o dà lo stato esplicito
`errore (non finito)`, che conta come controllo fallito.
1. **Per unità:** σ_i finita e > 0; E[e_i²] ed E[ẽ_i²] finite e ≥ 0; s_i finito per tutte
   le unità con E[ẽ_i²] > 0; termini individuali finiti.
2. **Simulazioni:** tutti i valori simulati finiti in ogni catalogo; altrimenti stato di
   errore e controllo fallito.
3. **Riproduzione numerica del braccio B:** con s_i = 1 e senza termine aggiuntivo, i valori
   simulati coincidono esattamente con quelli di `diag_b_oracle.null_sims` sui primi 10
   cataloghi di V1 e V4 (T3 e T5), e i verdetti coincidono con `B_RAW.csv.gz` sui primi 25
   (come il controllo 1 del piano).
4. **Prima esecuzione, T5:** se nessun catalogo T5 ha unità con E[ẽ_i²] = 0, i verdetti
   C2-T5 della riesecuzione coincidono con quelli della prima esecuzione (stessi semi, nessun
   termine aggiuntivo).
5. **Analitica e C1 della prima esecuzione:** tutte le grandezze finite; nessun stato
   condiviso tra bracci (ogni catalogo è calcolato in una chiamata indipendente).

Le interpretazioni K0–K3 del piano restano invariate; per C2 si applicano alla riesecuzione.

## 5. Output

Prima esecuzione: `results/DIAGNOSTIC/C_*_RUN1.*` (conservati). Riesecuzione di C2:
`C2_A1_RAW.csv.gz`, `C2_A1_SUMMARY.csv`, `C2_A1_CHECKS.csv`; risultati complessivi in
`docs/DIAGNOSTIC_C_RESULTS.md`.

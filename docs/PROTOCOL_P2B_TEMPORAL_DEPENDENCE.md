# Protocollo P2b — Dipendenza temporale tra rotazioni nel bootstrap (emendamento di P2)

Stato: **congelato il 2026-11-03**, prima di qualunque esecuzione di P2 sui
dati veri (P2 è stato eseguito solo su cataloghi sintetici). Aggiunge un
controllo sulle incertezze e una condizione al verdetto; il resto di P2
(SHA-256 `bb8bb080…`) resta valido e non viene modificato.

## 0. Perché

Da una revisione esterna: il bootstrap di P2 ricampiona rotazioni di
Carrington (CR) intere e conserva la dipendenza **dentro** ogni rotazione, ma
non quella **tra rotazioni consecutive**. L'attività emisferica varia
lentamente, quindi i residui dei modelli di T3 e T5 possono essere correlati
su più rotazioni e gli intervalli di P2 possono risultare troppo stretti. La
verifica di calibrazione fatta finora (cataloghi sintetici, falsi positivi
T3 1/40, T5 2/40) usava residui **indipendenti** tra rotazioni e non poteva
rilevare questo effetto.

Visto finora: la serie P1 parziale (2010-05 → 2012) e le figure di controllo;
nessun risultato di P2 sui dati veri.

## 1. Bootstrap a blocchi mobili

Per T1, T2, T3, T4 e T5, campione S e attività `A_monthly`, oltre al
bootstrap di P2 si calcola un **bootstrap a blocchi mobili di CR consecutive**:
- lunghezze di blocco L ∈ {3, 6, 13} rotazioni;
- un ricampionamento è formato da ⌈N_span / L⌉ blocchi, dove N_span è il
  numero di numeri di CR tra il primo e l'ultimo del campione; ogni blocco
  parte da un numero di CR estratto uniformemente tra il primo e
  (ultimo − L + 1) e contiene le CR con numero in [inizio, inizio + L − 1]
  presenti nel campione (le CR senza regioni non contribuiscono);
- 2000 ricampionamenti, seme 20261105; intervalli a percentile al 95% e al
  97,5%.

## 2. Condizione sul verdetto

Il verdetto di P2 §5 per T3 e T5 resta quello calcolato con il bootstrap di
P2. Si aggiunge la colonna `verdict_p2b`:
- uguale al verdetto di P2 se, per **tutte** le lunghezze L ∈ {3, 6, 13},
  l'intervallo al 97,5% porta allo stesso verdetto;
- altrimenti **"non deciso (dipendenza temporale)"**.

Nella sintesi finale e in ogni testo si cita `verdict_p2b`; il verdetto di P2
si riporta accanto.

## 3. Diagnostica dei residui (si riporta)

Per T3 e T5: media dei residui per CR (pesata come nel fit) e la sua
autocorrelazione ai ritardi 1–13 rotazioni, con la banda ±1,96/√N.

## 4. Calibrazione su cataloghi sintetici con residui correlati

Come nei test sintetici di P2 (attività SILSO vera, tilt e flussi
sintetici, nessun quenching iniettato), aggiungendo a ogni regione una
componente comune alla sua CR che segue un processo AR(1) tra CR consecutive,
con ρ ∈ {0; 0,5; 0,8} e deviazione standard pari a metà di quella del rumore
per regione. Per ogni ρ, 40 cataloghi: frazione di verdetti diversi da "non
deciso" con il bootstrap di P2 e con `verdict_p2b`. Si riporta; nessuna regola
viene cambiata dopo.

## 5. Output

`results/P2/P2B_MOVING_BLOCKS.csv`, `P2B_RESIDUAL_ACF.csv`,
`P2B_CALIBRATION.csv`; colonna `verdict_p2b` in `P2_SUMMARY.csv`.

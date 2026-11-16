# Emendamento A2 al piano di sensibilità della potenza T5

Stato: **registrato il 2026-11-16 dopo il fallimento della porta di compatibilità e dopo la revisione di
Codex del commit `ca71107`, prima di qualunque modifica del codice e di qualunque nuova esecuzione.**
Piano (`4b67632`, SHA-256 `fac76b1a…`) e A1 (`8dc6d48`, SHA-256 `60323789…`) restano agli atti e
invariati. **Non cieco**: l'esito della porta e la diagnosi sono noti.

## 0. Che cosa è successo e che cosa A2 non fa

- Script `b769892`. Ricevute conservate in `9a64e88`: selftest 53/53 superato; porta
  (`GATE_b769892ffdd6`) **36/40, non superata**. I 20 cataloghi nulli dello scenario 7 coincidono; in 4
  dei 20 cataloghi dello scenario 2 a −0,1 lo SE di M differisce da `VALIDATION_RAW` di 3,3·10⁻⁶–1,50·10⁻⁵
  relativo, con β̂ entro 1,6·10⁻¹⁵ e verdetti uguali. La sequenza si è fermata (§6.6): benchmark e griglia
  non eseguiti.
- **A2 è una revisione successiva al fallimento.** Non equivale al superamento retroattivo della vecchia
  porta, che resta «non superata» con le sue ricevute. Non si ritocca l'ottimizzatore di M e **non si
  allarga la tolleranza 10⁻⁹**.

## 1. La porta diventa due verifiche separate (sostituisce §6.6 per le nuove esecuzioni)

**(a) Compatibilità storica.** M, chiamata attraverso il wrapper dello script (`method_m`), su cataloghi
costruiti con il **percorso P2f originale** (`V.responses(design, s, rng, beta_frac)`, stessi semi della
validazione: 20 cataloghi dello scenario 2 a effetto −0,1 e 20 dello scenario 7 sotto nulla) contro
`VALIDATION_RAW.csv.gz` (test T5): β̂ e SE entro **10⁻⁹ relativo** (tolleranza originale), verdetto
uguale. Se fallisce, ci si ferma. Lo SE ottenuto sul percorso con iniezione successiva si registra accanto,
**solo descrittivo, senza tolleranza e senza effetto sull'esito**.

**(b) Correttezza dell'iniezione appaiata.** Restano i controlli del selftest su mapping, medie di cella e
pendenze con le tolleranze di A1 (§6.2, controlli 2a e 2e). Si aggiungono, con le tolleranze di A1 per le
grandezze in G/Mx (|a − b| ≤ 10⁻¹²·η̄) e l'uguaglianza esatta per gli oggetti interi o di disegno:
- **risposte individuali usate da M** (z_i = d*_i/Φ_i dei 2375 record T5) del percorso con iniezione contro
  il percorso P2f originale, per L con e = −0,1 nelle tre forme a x_scale = 1; Φ_i, pesi di aggregazione e
  mappa record → cella identici;
- **per ogni unità di lavoro** (selftest, benchmark ed esecuzione): z_i(segnale) − z_i(N) uguale alla media
  aggiunta del record (η̄·e_L·(Ā_c − 1) per L, Δη_c per S), e **residui entro cella** usati da M
  (`V.cell_residuals`) uguali a quelli di N. Una media di cella corretta da sola non esclude
  un'alterazione della dispersione dentro la cella; questo controllo la esclude. Una violazione è un
  errore tecnico.

## 2. Diagnosi: formulazione corretta e supplemento descrittivo

La diagnosi `bf24b7f` (output `438ef56`) si legge così, al posto delle formulazioni precedenti (handoff,
changelog e messaggi di commit di `9a64e88`–`ca71107`):
- nei casi perturbati esaminati, **differenze di arrotondamento possono impedire la riproduzione dello SE
  di M entro 10⁻⁹**. Non è vero che lo SE sia riproducibile solo con ingressi identici al bit: in 15 dei 20
  casi gli ingressi differiscono e lo SE coincide al bit;
- 10⁻⁵ è **l'ordine degli scarti osservati** (massimo 1,50·10⁻⁵ sul percorso con iniezione, 1,18·10⁻⁵
  con la sonda), non un limite garantito;
- 1,03·10⁻¹⁵ è **max|Δη_c|/η̄**, non l'errore relativo di ciascun η_c;
- M contiene due ottimizzazioni (funzione di varianza individuale e REML); la diagnosi ha registrato solo i
  parametri REML, quindi **l'attribuzione alla sola REML non è isolata**;
- G riusa la covarianza stimata da M: **la sua sensibilità numerica non è stata quantificata**.

**Supplemento diagnostico** (fissato qui, prima di eseguirlo; descrittivo, nessuna tolleranza, nessuna
decisione): uno script separato ripete i tre percorsi della diagnosi (A originale, B con iniezione
successiva, P sonda 1 + 10⁻¹⁵) sugli stessi 20 cataloghi e registra, oltre a quanto già registrato,
var_a, var_b, la massima differenza relativa delle varianze individuali ricostruite rispetto ad A, e β̂_G,
SE_G e verdetto di G per A, B e P con le differenze rispetto ad A. Nessuna soglia viene scelta dopo averle
viste.

## 3. Correzioni del codice richieste prima del benchmark (regole d'implementazione)

1. **Prerequisiti imposti dal codice.** Il benchmark rifiuta di partire senza ricevute positive di selftest
   e della nuova porta; l'esecuzione rifiuta senza ricevute positive di selftest, porta e benchmark.
2. **Ricevute legate alla configurazione, non al solo script.** Una ricevuta vale solo se coincidono:
   SHA-256 dello script, del piano, di A1 e di A2; SHA-256 di ogni modulo scientifico importato da
   `python/sharpbl/`; SHA-256 degli input (`CELLS.csv`, `SUMMARY.csv` del proxy, `VALIDATION_RAW.csv.gz`,
   `ORACLE_RAW.csv.gz`, catalogo P1, file SILSO); impronta del disegno ricostruito; ambiente (Python,
   NumPy, SciPy, pandas, `OMP_NUM_THREADS`). Una ricevuta si accetta solo con esito positivo esplicito
   (selftest «superato», porta «superata», benchmark «eseguito: entro il limite» con zero errori tecnici);
   `within_limit` da solo non basta.
3. **Differenze appaiate fra metodi** (§4 del piano): per ogni configurazione di rumore, segnale e coppia
   di metodi fra M, G, B, O, differenza appaiata della frequenza di `supportato` (e sotto nulla anche dei
   falsi verdetti) con l'errore della formula di T5-D2 §6.5, sui tentativi appaiati, errori inclusi.
4. **Validità centrale dei risultati dichiarati riusciti.** Ogni riga con stato `ok` deve avere: per M, G,
   O β̂, SE > 0, lo, hi e statistica finiti e verdetto coerente con l'intervallo; per B statistica finita,
   p_low e p_high in (0, 1], numero di cluster intero ≥ 2 e verdetto uguale a `P.verdict_b`. Una riga `ok`
   che non rispetta queste condizioni è un **errore tecnico**, non un tentativo riuscito.
5. Ogni correzione ha un test di regressione nel selftest (anche con esempi artificiali, come B con
   statistica e p-value non finiti, ricevute con esito negativo, benchmark senza ricevute).

## 4. Sequenza

A2 (questo commit) → correzioni del codice (commit) → supplemento diagnostico (§2) → selftest → nuova
porta (§1a) → solo se superata, benchmark (A1 §2) → revisione del codice e degli esiti preliminari →
griglia completa. Le ricevute del primo tentativo restano agli atti; i nuovi selftest e porte si scrivono
in cartelle nuove. Semi dei selftest come in A1 (33 000 050–33 000 099); nessun seme nuovo.

# A1: caso senza mappe utilizzabili e campi della ricevuta (revisione Codex di f17d230)

27 novembre 2026, Claude. **Solo sintetici**: nessun pixel osservato, nessuna corsa reale, A1 **non congelato**.
Revisione di riferimento: `/home/gianluca/MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/reviews/A1_F17D230_CODEX_20261127/REVIEW.md`.
Pilastro: sorgente BL dentro lo SFT (fase solo HMI). Log in `reviews/A1_EMPTY_CASE_FIX_20261127/`.

## 1. Il difetto

Se nessuna regione dà dipoli, `build()` andava in crash in `summarise()` → `ratio_table()` con
`KeyError: ['D_scale'] not in index`, prima di arrivare a `convergence()` e allo stato tecnico. Succede in due casi:
- tutte le letture falliscono;
- tutte le patch hanno una sola polarità.

REGIONS non aveva la colonna `D_scale` e DIPOLES non aveva colonne. Il ramo `no_usable_convergence_case` esisteva, ma
non veniva raggiunto.

## 2. Correzioni

Runner `scripts/sft_map_bipole_pilot.py`:
- **Formati espliciti** anche per le tabelle vuote: `DIP_COLS` (DIPOLES), `SUMMARY_COLS` (SUMMARY), `RATIOS_KEEP`
  (RATIOS). Se i dizionari prodotti non coincidono con il formato dichiarato, l'esecuzione si ferma con un errore
  esplicito: nessuna colonna viene persa in silenzio.
- **Nessun dipolo:** `summarise()` restituisce SUMMARY e RATIOS vuoti con le loro colonne. `convergence()` dà
  `no_usable_convergence_case` e la corsa non è valida.
- **Stato tecnico fino ai prodotti:** META riceve `technical_status` (`no_dipoles` oppure `ok`), `regions_ok_100G` e
  `dipole_rows`, oltre a `numerical_status` e `run_valid`.
- I fallimenti restano tutti nei denominatori. Nessun dipolo nullo inventato, nessuna regione sostituita.
- **`gate()`:** il nuovo `a1_receipt_problems()` rende obbligatori nella ricevuta A1 tre campi del §4:
  - `parent_receipt_sha256`, uguale alla ricevuta padre fissata;
  - `freeze_commit`, antenato di HEAD e contenente il testo A1 con lo stesso SHA;
  - `not_blind`, la dichiarazione di non cecità.

Riconteggio `scripts/sft_map_bipole_pilot_recount.py`, con codice proprio:
- DIPOLES con colonne esplicite anche quando è vuoto;
- `own_ratios` e `own_summary` vuoti con colonne esplicite. Il filtro sulle righe ora usa un vettore booleano, così
  non degenera quando la tabella è vuota;
- RATIOS e CONVERGENCE confrontati anche quando sono vuoti, protetti da `guarded`. Prima «vuoto» era un rifiuto
  automatico, che non distingueva un prodotto mancante da un caso senza dati. Un prodotto vuoto con un riconteggio
  non vuoto resta un rifiuto;
- controllo A1 reale con gli stessi tre campi della ricevuta, più il blob del testo A1 al commit di congelamento.

Bozza `docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_DRAFT.md`:
- §2bis(c) riformulato come osservazione locale: nei casi e nei raffinamenti sintetici provati non è bastato; non è
  dimostrato in generale;
- §4: elenco dei campi obbligatori della ricevuta e della propagazione dello stato tecnico.

## 3. Regressioni

Runner, `selftest_empty`, con N = 8 senza preflight: si esercitano solo questi rami.
- **read_error:** ogni lettura solleva OSError. 102 righe `read_error:OSError`, DIPOLES, SUMMARY e RATIOS vuoti con le
  loro colonne, `no_usable_convergence_case` e `no_dipoles`, corsa non valida, fallimenti per causa uguali a 2 × il
  campione.
- **unipolar:** |Br| su ogni patch. 102 righe `no_two_polarities` e stessi stati.
- **mixed:** una sola HARP leggibile. Dipoli solo per quella HARP, riepiloghi presenti, le altre HARP nei denominatori;
  validità coerente con lo stato numerico (a N = 8: `convergence_failed`).
- **Campi della ricevuta A1:** una ricevuta vuota dà tre problemi. Una ricevuta con commit HEAD, che però non contiene
  il testo A1, dà solo quello del commit.

Riconteggio, `selftest_empty`: i prodotti del runner nei tre casi, dopo un passaggio per CSV come nel percorso reale,
vengono letti senza crash. SAMPLE, REGIONS, DIPOLES, SUMMARY, RATIOS, DENOMINATORS, MANIFEST e CONVERGENCE
coincidono con il riconteggio; la ricevuta è rifiutata («run declared valid» fallito).

Prove rapide prima dei lanci lunghi:
- controllo statico dei nomi: nessun nome non definito;
- runner, 3 casi: 3/3 in 7 s;
- riconteggio, 3 casi con preflight fittizio: al primo giro 1/3, perché il DIPOLES vuoto del riconteggio non aveva
  colonne. Corretto, poi 3/3 in 9 s.

## 3bis. Secondo giro, dopo la lettura Codex in corso d'opera

Fonte: `reviews/A1_EMPTY_FIX_REVIEW_20261127/REVIEW.md` (repository MWO), letta sulla versione del primo lancio.
1. **`not_blind`**: `str(x).strip()` accettava null, false, 0, [] e {}. Ora runner e riconteggio richiedono una stringa
   non vuota. Regressioni: null, false, true, 0, 1.0, [], {}, stringa vuota e solo spazi sono rifiutati; una
   dichiarazione testuale è accettata.
2. **Commit di congelamento nel riconteggio**: nuova `a1_receipt_issues(a1, run_head)`, con codice proprio. Il commit
   deve essere antenato del commit della **corsa** (`git_head` di META, non l'HEAD corrente) e contenere il testo A1
   con lo SHA della ricevuta. Regressione: HEAD~1 come congelamento con HEAD come corsa è accettato; il contrario è
   rifiutato.
3. **Campi tecnici di META ricontati**: nuova `technical_issues()`. Presenza e tipo (interi veri, non booleani) dei
   campi; `regions_ok_100G` e `dipole_rows` da REGIONS e DIPOLES propri; `no_dipoles` se e solo se non ci sono
   dipoli; una corsa senza dipoli dichiarata valida è rifiutata. Nuove manomissioni nel selftest del riconteggio:
   campo mancante, valore alterato (+1), conteggio frazionario (+0,5), `no_dipoles` con dipoli presenti.

Bozza A1 §4 allineata: la dichiarazione è testuale e il commit è antenato del commit della corsa. Prova rapida dei
tre punti, comprese le regressioni del caso vuoto: 9/9 in 13 s.

## 4. Selftest completi

Due versioni, con esiti conservati separatamente (Codex ha chiesto di non interrompere il lancio 1 dopo la sua
lettura). I file esatti di ciascun lancio sono stati copiati prima di ogni modifica successiva.

| Versione | Runner `--selftest` | Riconteggio `--selftest` |
|---|---|---|
| Lancio 1 (09:47): caso vuoto e campi della ricevuta | **24/24** | **36/36** (33 precedenti + 3 casi senza mappe) |
| Finale (10:03): più i tre completamenti del §3bis | **24/24** | **41/41** (36 + 4 manomissioni dei campi di META + campi della ricevuta) |

- I 24 del runner sono i 20 precedenti più `read_error`, `unipolar`, `mixed` e i campi della ricevuta A1. Nella
  versione finale l'ultimo controlla anche che null, false, true, 0, 1.0, [], {} e stringhe vuote siano rifiutati
  come `not_blind`.
- In entrambe le versioni restano positivi il preflight (N 400 respinto, N 800 accettato), la convergenza
  (stato ok), il riconteggio completo della corsa sintetica e le 32 manomissioni già presenti.
- Il «[FALLITO]» nella riga «convergence requirement not met although the values agree» è, come nel 33/33 di
  f17d230, il controllo interno citato dal rifiuto atteso, non un test fallito.
- Log: `reviews/A1_EMPTY_CASE_FIX_20261127/launch1_*.log` e `final_*.log`. Gli avvisi di pandas
  (PerformanceWarning) sono rimasti nei log così come prodotti.
- Sono selftest su sintetici: non producono ricevute e non autorizzano corse osservate. A1 non è congelato.

## SHA-256 dei file eseguiti

| File | Lancio 1 | Finale |
|---|---|---|
| scripts/sft_map_bipole_pilot.py | c76bc55845ef3a422dc2a4c59470063b474c27642b7ef6c229dd3bf565bedac9 | e08941414a564cb5a47f666e71aba5184ddaeee95b10ea915c392103980cb16f |
| scripts/sft_map_bipole_pilot_recount.py | 923b5c7ae5fa73ff824d1b668c74ffa148b67f0515c4c1c721f82a5284d2883e | 227c40713d9f368009f72e53828644396be4911adbb95ce5ccce964e50468093 |
| docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_DRAFT.md | 0cb0d339e3c8f38ad8eb21ab455d0a807bf4b29c5b063cd858c41fe6e3f23ae5 | 44a924e9fe78737e691ba5d5a1cf4c7d9e8db3f8aebadbc66c157b2e9f6d957c |

I file su disco alle 10:37 coincidono con la colonna «Finale» (verificato con `sha256sum`). Il core
`python/sharpbl/sft_core.py` è invariato (053e622b…).

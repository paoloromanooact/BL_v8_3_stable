# Q4 — verifica preliminare delle correzioni del riconteggio

25 novembre 2026, Codex. Fotografia della copia di lavoro non ancora
committata di `scripts/mdi_q4_recount.py`, SHA-256
`6024dc6157f57cb5acf0bf7ed2238ba52c9a9599d79451eb62ada6558cb9a489`.
Non e una chiusura su un commit definitivo. Il file di Claude non e stato
modificato, aggiunto allo staging o committato da questa revisione.

## Cosa e risolto

La sonda precedente e stata rieseguita su una copia immutabile del codice:
la base sintetica di due realizzazioni passa; tutte le sei alterazioni
accettate da 0344bc3 ora sono rifiutate (tolleranze RAW negative e SUMMARY
zero, YIELD_EFFECTS duplicato/etichetta alterata, scelte META sostituite,
conteggio CELL_COUNTS frazionario).

Sono presenti il confronto completo di YIELD_EFFECTS, la verifica delle
scelte e il gate dei file correnti. Il controllo diretto degli hash sul
percorso reale non trova problemi, senza chiamare il riconteggio reale
ne leggere RAW/SUMMARY/CRITERIA di Q4. Il campo META aggiuntivo della vecchia
sonda e ancora accettato sul percorso sintetico: non e un rilievo, perche
lo schema META completo e richiesto soltanto sul percorso reale.

## Due dettagli residui da chiudere

### 1. Conteggi in SUMMARY e nei dettagli JSON dei criteri

La verifica esatta ora riguarda le colonne nominate in EXACT, ma non
le statistiche dei conteggi ne i conteggi nidificati nel JSON:

- `json_close({'x': {'n_ok': 2}}, {'x': {'n_ok': 2.000000001}})` restituisce True;
- `close_cols` accetta `n_records_min = 5223.000000001` invece di 5223;
- come problema di tipo collegato, `n_mdi = False` viene accettato come 0.

Queste sono prove dei comparatori, non mutazioni eseguite sui risultati
reali. La chiamata di confronto di CRITERIA usa direttamente quel
comparatore JSON.

Fissare il dominio per significato del campo: conteggi base e min/max
finiti, interi e non negativi ove previsto; mediane dei conteggi possono
essere semintere, ma si confrontano esattamente (senza tolleranza float).
I conteggi `n_ok`/`n_fail` nei dettagli dei criteri devono avere lo stesso
controllo di dominio ed uguaglianza esatta. Rifiutare booleani nelle colonne
di conteggio. Non applicare queste restrizioni a Kish n_eff, pesi o altre
grandezze realmente continue.

### 2. Bersaglio nullo: non accettare una tolleranza finita arbitraria

Il controllo RAW usa `big | (nul & zero_or_inf)`: il ramo `big` resta
valido anche quando `nul` e vero. Quindi un bersaglio esattamente zero e
B1 esattamente zero accettano una tolleranza 1e30, poi normalizzata allo
stesso sentinel della tolleranza legittima.

Prova con una riga generata da `nrows` con tutti i bersagli nulli e B1=0:
la formula produce +inf. Cambiando una sola tolleranza in 1e30 passano sia
il controllo del dominio sia il confronto normalizzato RAW. Questa prova
non e una corsa completa di `check`, ma percorre esattamente i suoi due
controlli pertinenti alla riga RAW.

Richiedere rami separati per bersaglio nullo e non nullo, mantenendo la
regola gia dichiarata (0 o +inf quando nullo; grande positivo o +inf solo
quando non nullo). Una riga fallita resta mancante. I valori undefined e
le tolleranze delle famiglie non protette non devono essere normalizzati
indiscriminatamente.

## Consegna e seguito

- Prove: `scripts/mdi_q4_recount_domain_review_probe.py` (solo righe
  sintetiche e controlli di hash; uscita negativa finche restano i casi).
- Esiti aggregati: `docs/MDI_Q4_RECOUNT_WORKING_REVIEW_RESULTS.json`.
- Fotografia riproducibile come patch contro 0344bc3:
  `reviews/MDI_Q4_RECOUNT_WORKING_6024dc6/source.patch`.
- La sonda di regressione completa e quella gia conservata,
  `scripts/mdi_q4_recount_review_probe.py`, caricata sulla fotografia con
  hash sopra. Non e stato rieseguito tutto il selftest dell'autore.

Claude puo completare questi dettagli e committare la versione definitiva;
Codex verifica quel commit prima del `--check` reale. Runner Q4 e prodotti
restano intatti; niente rilancio Q4, nessuna classificazione scientifica
letta. I due protocolli SFT restano la linea prioritaria separata.

# Pilota MDI L2 — chiusura della revisione prima della misura

23 novembre 2026, Codex. Revisioni esaminate: `913ab1d` (fase 5) e `85609aa`
(download conservato). Correzioni a `f550fdb` chiuse con l'aggiunta descritta qui.

## Decisione

Runner e riconteggio della fase 5 approvati per l'uso nell'ordine del
protocollo congelato. Nessuna modifica di soglie, finestre, campione, QUALITY
o analisi scientifiche. Nessuna misura reale o richiesta di rete eseguita
in questa revisione.

## Codice e prove

Le correzioni di 913ab1d sono confermate: stop prima dei FITS per prodotti
invalidi; controllo di pair_status e delle colonne esportate; conteggi interi
esatti e segno leading nel dominio; INTERVAL ignoto trattato senza crash e
senza sostituirlo con zero. I cinque controesempi precedenti sono rifiutati.

Un legame residuo era assente: una selezione con META diverso ma ricevuta
aggiornata poteva superare il gate, pur non essendo quella nominata dai
metadati conservati. Aggiunta sia al runner sia al riconteggio la condizione
`metadata.selection_meta_sha256 == SHA256(selection/META.json)`.
Una nuova regressione controlla espressamente questo caso.

- Runner: selftest 16/16.
- Riconteggio: selftest 25/25.
- Sonda indipendente `mdi_pilot_l2_review_probe.py`: 7/7; solo FITS sintetici,
  metadati conservati e lettori sostituiti da sentinelle nei test dei gate.
- Le prove reali di gate non aprono FITS e devono restituire nessun problema.

Controlli del repository: sintassi e launcher positivi; 154 test superati nel
sandbox e quattro test locali bloccati esclusivamente dalla creazione del
socket. Ripetuti solo quei quattro fuori dal sandbox: 4/4 positivi, quindi
158/158 complessivi. Nessun contatto JSOC. `git diff --check` positivo.

## Download, verifica indipendente

Ricontati dai prodotti conservati: 161 path unici, esattamente quelli del
piano, con lo stesso T_REC e SHA del META del piano. Tutti i checkpoint sono
ok al primo tentativo. Ricalcolati gli SHA-256 e controllate le dimensioni
dei 161 file sul disco: concordi con il checkpoint; nessun FITS estraneo.
Lettura binaria solo per gli hash: nessun pixel interpretato o tilt calcolato.
Non ripetuto qui il controllo delle dimensioni delle immagini dichiarato
nell'handoff del download.

RUN_001 e checkpoint coerenti; 251 inizi e 251 chiusure nel registro,
nessuna prenotazione aperta, 412 richieste e 243994274 byte complessivi.
Restano invariati i tetti congelati. Nessun nuovo download necessario.

## Sequenza autorizzata tecnicamente

1. Da albero tracciato pulito, eseguire `mdi_pilot_measure_l2.py --run`.
2. Conservare L2_RECORDS e META in Git prima di leggere tilt o confronti.
3. Eseguire `mdi_pilot_l2_recount.py --check`; conservare la ricevuta.
4. Solo dopo ricevuta positiva completa, leggere e documentare gli esiti
   descrittivi. L'analisi dei confronti Q2 e della ripetibilita deve rispettare
   il protocollo e avere il proprio codice rivisto prima dell'esecuzione.

Nessuna sostituzione di gruppi o immagini fallite. I vincoli geometrici
restano quelli congelati: 20 delle 81 finestre A fuori dominio, quindi al piu
61 misurabili prima degli altri fallimenti; quiete con zero/un lato valido
51/30. Le perdite si riportano. Quiete non disponibile non significa rumore
nullo. Il pilota non fornisce un verdetto T3 o una calibrazione automatica
della sorgente BL.

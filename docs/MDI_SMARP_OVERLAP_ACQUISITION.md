# MDI/SMARP — acquisizione verificata dei metadati della sovrapposizione

2026-11-16. Corsa `schema_20261116_http_ac06138`, fase `overlap`, sul commit
`44871255fcf5d82307d79cc4379027b00cb3c54f`, albero tracciato pulito. Codice, mappa e regole già verificati; nessuna
modifica di protocolli o pipeline HMI. **Solo metadati**, nessun export, staging o FITS. L'utente ha
approvato il proseguimento dopo il preventivo dei conteggi; questo passaggio si ferma prima dello storico.

## Acquisizione e conteggi

33 elenchi acquisiti, tutti HTTP/DRMS riusciti, nell'ordine del piano: sei finestre mensili SMARP della
sovrapposizione, 26 finestre HMI con margini, infine il blocco full-disk MDI 2010 gennaio–ottobre già previsto.
Durata della fase circa 286 s. Registro cumulativo: **272 tentativi, 45 924 964 byte, 119 611 righe**,
636,5 s, chiuso regolarmente. Tetti di 1000 tentativi, 1 GiB, 2 milioni di righe e 90 minuti invariati.

| Profilo | Ricevute | Accettate dopo filtro semiaperto | Righe di bordo | Identificativi di patch distinti |
|---|---:|---:|---:|---:|
| SMARP, maggio–ottobre 2010 | 11414 | 11387 | 27 | 127 TARPNUM |
| HMI, finestra con margini | 103833 | 103709 | 124 | 139 HARPNUM |
| Full-disk MDI, gennaio–ottobre 2010 | 4516 | 4515 | 1 | non applicabile |

Le 152 righe di bordo sono conservate separatamente; nessun tempo illeggibile e nessun duplicato identico
fra le righe accettate. Qui «accettato» significa solo appartenente all'intervallo semiaperto e con identità
coerente: non è un filtro di qualità scientifica. Nessun record è stato escluso per QUALITY o flusso.

Per HMI, tre righe accettate appartengono al margine e non alla finestra scientifica
`[2010-05-01, 2010-10-29)` TAI. Nella finestra scientifica restano **103706 record e 139 HARPNUM**;
nessuna HARP è presente soltanto nei margini. Il numero di patch non identifica regioni fisiche indipendenti.
127/137 della letteratura erano valori di contesto, non un obiettivo da raggiungere: nessuna selezione è
stata aggiustata per far coincidere i conteggi. Non sono ancora calcolati i grafi di associazione.

## Un dato emerso sui prodotti full-disk

Sui 4515 record full-disk del blocco gennaio–ottobre 2010:

| INTERVAL grezzo | Record | Trattamento con la regola già registrata |
|---|---:|---|
| `300.00` s | 2466 | `documented_5min` |
| `30.00` s | 1760 | `unknown/value_not_mapped` |
| `MISSING` | 289 | `unknown/value_not_mapped` |

Non compare il valore 60 s nella parte acquisita. I 30 s non sono riclassificati come prodotto da un minuto
in base al valore osservato o al numero atteso di prodotti. Servono una definizione documentata del prodotto
ed eventualmente una nuova regola prima della relativa applicazione. DPC è conservato grezzo, senza decodifica
presunta. Queste sono le frequenze delle sorgenti full-disk di gennaio–ottobre, non la miscela dei prodotti
nelle patch SMARP. Il collegamento delle patch al full-disk resta non documentato e il relativo stato ignoto.
Nessuna stima del rumore per pixel o del raccordo strumentale è derivata da questi conteggi.

## Integrità e misure di costo

Verifica indipendente senza importare il raccoglitore: lista delle finestre esattamente uguale alle 33 foglie
non vuote della parte `overlap`; conteggi delle liste uguali ai conteggi preliminari; chiavi richieste uguali
alla mappa registrata; hash dei corpi originali; colonne e lunghezze coerenti; filtro temporale, righe di bordo
e identità; ogni valore e molteplicità dei CSV confrontati con la ricostruzione dai JSON originali; provenienza,
configurazione, totali di righe e misure del primo blocco per profilo. Tutte le verifiche sono superate.

Il verificatore è specifico della corsa e della fase; è stato preparato durante l'acquisizione, prima della
lettura del riepilogo finale. Le descrizioni dei prodotti qui sopra sono conteggi dei campi registrati, dopo il
controllo di integrità, senza nuova classificazione. Script e ricevute restano nella cartella locale della corsa:
`OVERLAP_CHECK.py`, `OVERLAP_CHECK.json` e `OVERLAP_DESCRIPTORS.json`, rispettivamente SHA-256
`d4be02c81f0c5d54c425866c9bb4b858debc4d3e1b7c81e2775fd9129ed20f82`, `2187f8e8306c224554777c4f33baed5e972391b28721f180452f71cb37cdfe00` e
`77a9c54e7a766f8f335128a6f9494b6878f17fd8faaf8152d31041c412dc9c3c`. Le risposte originali non sono state modificate.

Hash della fase e degli artefatti:

- `PHASE_overlap_003.json`: `1c93dcb3f0bea01917c29541c5bfb375abb5e01f26f5e1f733e7913e49b1a75c`
- `LIST_RECEIPTS.jsonl`: `f4adcf34b52437acdd3373312d891f91f233a188c432df4699b6dbcaf4f2f15f`
- `RECORDS_smarp_overlap.csv.gz`: `3a46a70c388eeb50527d82db6a0206e7d48067f39e0fce67b56ef8ef4888aae7`
- `RECORDS_hmi_overlap.csv.gz`: `808f634de36dc1ef83fb01b79a3bffe728b88fd361b69b879c1244b43669593d`
- `RECORDS_fd_min.csv.gz`: `742c64d4a07fde8fc226f58da4d12bc53dbe05d4eb95d0f1525c3c2af9e1a3ce`

`PROFILE_MEASURES.json` conserva le misure dei primi blocchi SMARP overlap, HMI overlap e full-disk.
Manca ancora il primo blocco del profilo **SMARP minimo storico**: il preventivo completo di payload non viene
registrato prima di averne misurato il costo, come prevede il piano. Nessuna densità di byte del profilo ricco
è sostituita arbitrariamente a quella del profilo minimo.

## Arresto e limiti

Lo storico non è avviato: non esiste `RECORDS_smarp_min.csv.gz`; il solo blocco full-disk 2010 sarà riusato,
non riscaricato. Nessun lookup ausiliario, classificazione nuova, analisi del quenching o download di mappe.
Disponibilità dei record di catalogo non certifica disponibilità dei FITS. Centri delle patch utilizzabili
secondo la mappa; riquadri non ricostruiti senza dimensioni. Prossimo passo da decidere separatamente: lettura
dei metadati della sovrapposizione oppure avvio dello storico con la misura iniziale e il preventivo di payload.
Nessun push. Piano prospettico e morfologia S in pausa.

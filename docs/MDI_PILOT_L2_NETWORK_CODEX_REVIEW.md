# Pilota MDI L2 — revisione offline di metadati, registro, download e adattatore

Codex, codice fino a 0e32539 (0491c03 e adattatore a267c1b). Nessuna rete eseguita.

**Non ancora via a --fetch, neppure per i metadati.** La finestra ±10h, il confronto delle due regole QUALITY
senza cambiare gruppi/giorni e i parser temporali migliorati sono corretti come impostazione. Tuttavia il registro
non conta ancora alcuni byte ricevuti e il passo dei metadati non verifica la provenienza della selezione.
Questi punti si possono chiudere prima e indipendentemente dai problemi del downloader/adattatore.

## A. Prima dei soli metadati

### A1. Byte falliti/interrotti e prenotazione del budget

`http_json` perde il numero di byte dopo un errore HTTP, JSON o lettura parziale; `fetch` registra sempre zero
nel ramo except. La sonda simula 1234 byte ricevuti prima dell'errore e 800 al secondo tentativo: il registro
contiene 800, invece di 2034. Inoltre un tentativo metadata aperto conta zero byte e `can_start('metadata', 0)`
permette un nuovo trasferimento con un solo byte residuo nel budget.

Trasportare i contatori effettivi anche nelle eccezioni, conservare la risposta ricevuta e prenotare prima della
richiesta il limite massimo metadata (attualmente 5 MB), entro il residuo globale. L'interruzione senza end deve
conservare quella prenotazione; non trasformarla in zero. Distinguere risposta HTTP, parsing e scelta scientifica.
Le prenotazioni e la verifica del budget vanno rese atomiche, o protette da un lock globale che impedisca due
corse concorrenti. Non basta avere un file append-only senza un vincolo sull'avvio.

Prove: errore HTTP con corpo, JSON invalido dopo lettura, connessione interrotta con corpo parziale, tentativo
aperto, budget residuo inferiore al limite metadata e seconda corsa concorrente. Nessuna prova richiede JSOC.

### A2. Provenienza prima di qualsiasi chiamata al trasporto

`fetch` verifica solo SHA del protocollo, non prodotti e ricevuta della selezione, legame al protocollo, unicità
e appartenenza delle unità L2. La sonda passa un SAMPLE sintetico senza ricevuta e con META `{}`: il trasporto
viene invocato due volte. È necessario lo stesso gate stretto già adottato nelle fasi locali, prima della lettura
operativa e della prima richiesta. La corsa reale richiede codice conservato/albero tracciato pulito e un elenco
L2 legato ai prodotti verificati. Usare fixture consistenti o un percorso sintetico dichiarato nei test.

### A3. Risposte mancanti, QUALITY e denominatori

- Con una QUALITY valida e una mancante, pandas converte `quality_int` in float: `composition` tenta il formato
  esadecimale su un float e solleva ValueError. Usare un tipo intero nullable o normalizzare esplicitamente;
  conservare sia il dato originario sia lo stato di parsing. Le QUALITY non interpretabili non sono qualità zero.
- Con INTERVAL mancante per A e numerico per un altro record, il mancante diventa NaN: `is None` non lo rileva.
  La sonda produce `no_pair`, anziché `no_pair_interval_unknown`. Gestire assenza, None e NaN in modo coerente.
- I gruppi con richiesta fallita non entrano in `groups`, quindi spariscono dal denominatore delle alternative:
  su due gruppi selezionati (uno fallito, uno risposto), ADMISSIBLE_ALTERNATIVES riporta `n_groups=1`.
  Riportare tutti i gruppi/celle selezionati, richieste riuscite/fallite e disponibilità non determinata separata
  dall'assenza di A o B in una risposta valida. Non usare risposte mancanti come prova a favore di una regola QUALITY.
- Salvare risposte/esiti progressivamente prima della composizione: un errore di parsing tardivo non deve far
  perdere le risposte già ricevute. Con tutte le richieste fallite o vuote, scrivere schemi completi e stato
  esplicito incompleto/non determinato; non omettere silenziosamente prodotti obbligatori.

È opportuno aggiungere un riconteggio offline di scelte A/B, composizione e alternative dalle risposte conservate,
senza nuove richieste, prima di decidere un emendamento. La scelta congelata resta l'unica a produrre il piano.

## B. Downloader — chiusura separata prima dei FITS

La ripresa **non verifica uno SHA precedente**. Per ogni file esistente il codice controlla forma/dimensione e
calcola un nuovo hash, senza leggerne uno atteso da un registro verificato. La sonda modifica tutti i pixel di un
FITS sintetico mantenendo dimensioni e forma; viene accettato come `present`, senza richieste.

Serve un checkpoint/manifesto persistente legato a record, percorso, metadati e hash del file completato. Un file
senza provenienza nota non è un download già verificato; un hash discordante deve fermare la ripresa senza
sovrascrittura. Usare quel checkpoint anche per impedire di azzerare i due tentativi per file cambiando destinazione
del manifesto: ora attempts=0 e il contatore degli errori si azzerano a ogni run.

Il piano e il manifesto devono rendere esplicita la completezza: il codice può oggi terminare con exit 0 anche
con file falliti, purché non scatti l'arresto per errori consecutivi. Uno stadio successivo non deve confondere
questo caso con un'acquisizione completa. Verificare legami alla selezione, registro e piano corrente prima dei GET.
I byte e le richieste reali del trasporto A1 vanno mantenuti; una stima conservativa va dichiarata tale.

## C. Adattatore — prima della misura L2

- `int(k.get('QUALITY', 0))` accetta una QUALITY assente come zero e rifiuta una stringa JSOC valida
  `'0x00000000'` con ValueError. La sonda con dati e geometria sintetici produce `ok` senza QUALITY.
  Richiedere un valore esplicito e interpretabile (con la regola congelata/amendata), altrimenti stato di rifiuto.
- `pixel_area_cm2` usa CDELT1 al quadrato. In generale occorre il modulo del prodotto CDELT1*CDELT2;
  con scale sintetiche 2 e 3 arcsec il codice dà 2/3 dell'area corretta. Se si assume pixel quadrato, verificarlo
  ed eventualmente rifiutare la geometria discordante, non ignorare CDELT2.
- Manca una suite dell'adattatore per B0/CROTA non nulli, entrambi i segni, geometria avanti/indietro, campo LOS
  noto, BLANK/scalatura, dominio mu sull'intera finestra e area/flusso sintetici. La prova su un gruppo reale
  è uno smoke test dichiarato, non una verifica generale della registrazione o del segno del campo.
  Riconteggio della geometria/misura da completare nella fase 5. Non si richiedono nuove immagini per questi test.

## Esiti della revisione

Selftest esistenti rieseguiti: metadati 13/13, registro 3/3, downloader 7/7. La sonda aggiuntiva
`scripts/mdi_l2_network_review_probe.py` riproduce tutti i casi sopra su dati temporanei sintetici e trasporti
simulati; non apre socket. Il fatto che i selftest passino non chiude questi controesempi.

Ordine pratico: chiudere A, poi revisione mirata e autorizzazione dell'utente per soli metadati; conservare e
ricontare i metadati, poi decidere QUALITY senza FITS. B e C possono essere sistemati in parallelo, ma il loro
via resta distinto. Nessun cambiamento a L1, HMI/MWO, obiettivi scientifici o protocolli congelati.

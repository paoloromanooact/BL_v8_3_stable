# MDI L2 — via tecnico alla sola acquisizione dei metadati

Codex, revisione di 329be47 dopo b49fcba. Nessuna richiesta di rete eseguita.

## Acquisizione: correzioni verificate e via circoscritto

I casi di A1–A3 sono stati recepiti: prenotazioni sotto lock, tentativi aperti conteggiati, errori con byte/stadio,
RunLock nel percorso dei metadati, provenienza della selezione prima del trasporto, QUALITY nullable e INTERVAL
mancante distinti, denominatori con richieste fallite e risposte progressive. Non si allargano QUALITY o campione.

Durante la revisione sono state corrette altre condizioni del trasporto, con test offline:

1. `choose` non gestiva una risposta valida con zero record: l'array vuoto degli ammissibili era float e `~`
   sollevava TypeError. Ora è esplicitamente booleano: l'esito è `no_magnetogram`, non un errore globale di derivazione.
2. L'ultimo `read1(65536)` poteva superare i 5 MB prenotati: la sonda leggeva 5046272 byte. Ogni lettura è ora
   limitata al residuo; il raggiungimento del tetto produce un errore esplicito invece di accettare un corpo capato.
3. Vengono contati anche i byte di `IncompleteRead.partial`; una prova conta 4 byte già restituiti più 2 parziali.
   Se un trasporto fallisce senza fornire contatori, si conserva una stima prudente pari alla prenotazione e alle
   due richieste riservate, dichiarandola come tale, anziché registrare zero.

Selftest dopo le correzioni: metadati 16/16; registro 4/4. Questi cambiamenti non alterano regole scientifiche,
selezione, soglie, protocolli o risultati L1.

**Via tecnico al comando di acquisizione dei soli metadati, dal commit di questa revisione e dopo l'autorizzazione
esplicita dell'utente.** Il perimetro è quello delle 90 unità L2 già selezionate, una richiesta per unità, senza
retry automatici o redirect. Restano attivi i limiti cumulativi e il tetto per risposta. Conservare gli output e
il registro anche se incompleti; nessun FITS o cambiamento di gruppi/giorni è autorizzato qui.

## Riconteggio: non ancora approvato per decidere QUALITY

Il nuovo riconteggio 2/2 costituisce un primo controllo, ma non certifica ancora tutti i prodotti.
La sonda `scripts/mdi_metadata_block_A_review_probe.py` parte da una corsa sintetica positiva e accetta ancora,
con hash aggiornati, le quattro mutazioni seguenti:

- `DOWNLOAD_PLAN.size = 1`;
- `CHOICES.A_path = '/SUMevil/wrong'`;
- `CHOICES.A_dt_h = 100`;
- `META.completeness = 'incomplete'` e `requests_ok = 0` su una corsa completa.

Il checker non confronta DISCARDED e confronta solo una parte di CHOICES/GROUPS/piano; copia la completezza
senza ricostruirla. Non verifica protocollo e provenienza completa della selezione: lo SHA del META non controlla
gli hash effettivi dei suoi prodotti e la ricevuta. Inoltre la propria classificazione collassa ogni QUALITY
non interpretabile in `missing`, mentre il runner distingue `missing` e `unparsable`.

Prima di usare QUALITY × INTERVAL per un emendamento:

1. Confrontare tutti i prodotti, con colonne/chiavi/ordine, percorsi, dimensioni note/ignote, intervalli e tempi,
   classi, motivi dei record scartati e tutti gli esiti dei due insiemi QUALITY. Ricostruire la completezza,
   n richieste riuscite, n unità e copertura; verificare unicità/appartenenza delle risposte e status/schema JSOC.
2. Verificare protocollo, prodotti e ricevuta stretta della selezione prima di leggerli. Legare anche gli esiti
   di richiesta al registro conservato (snapshot/prefisso, dato che il registro potrà crescere con i FITS).
   Distinguere verifica completa dei metadati acquisiti da copertura incompleta delle 90 unità.
3. Aggiungere mutazioni dei campi ora ignorati e basi valide con risposta vuota, errore, QUALITY mancante/non
   interpretabile, INTERVAL misto, duplicati e risposta extra. Un risultato sintetico non deve produrre una
   ricevuta reale completa; il checker deve distinguere il proprio stato da un parametro `real=True` non verificato.

Questi lavori sono offline e possono procedere mentre si attende l'autorizzazione o l'acquisizione. Non richiedono
un nuovo download delle stesse risposte: ANSWERS.jsonl resta il punto di partenza.

## Cosa resta escluso dal via

- Nessuna decisione su QUALITY né emendamento finché il riconteggio non è chiuso e i metadati non sono conservati
  e verificati. Dichiarare che i risultati L1/2010 erano già noti; non presentare il percorso come interamente cieco.
- I blocchi B e C di b49fcba restano aperti: questo via non copre downloader, ripresa FITS, adattatore o misura L2.
- Nessun nuovo T3, Q4, serie BL combinata o simulazione lunga. Gli obiettivi scientifici restano invariati.

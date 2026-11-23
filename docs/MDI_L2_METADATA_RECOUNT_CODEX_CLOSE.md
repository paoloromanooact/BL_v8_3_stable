# MDI L2 — chiusura della revisione del riconteggio dei metadati

Codex, revisione di 34fc26b. Acquisizione conservata in 98ee895; nessuna nuova rete eseguita.

Il riconteggio rafforzato recepisce i rilievi: ricostruzione indipendente e confronto completo dei prodotti,
dimensioni note/ignote, tempi, percorsi, motivi di scarto, QUALITY mancante/non interpretabile, denominatori,
completezza e provenienza della selezione. Le basi sintetiche includono risposte vuote e fallite; le ricevute
di quelle prove restano parziali e non vengono scritte sul percorso reale.

## Ultimo controllo aggiunto in revisione

Risposta e registro potevano concordare sulla stessa richiesta sbagliata: cambiando ds e target del registro
in una finestra del 1999, per una selezione del 2000, la base e il controesempio erano entrambi accettati.
Questo non indica un problema nella corsa acquisita, ma una lacuna del riconteggio.

Aggiunta la ricostruzione propria di serie, istante DPD e finestra simmetrica ±10h con conversione UTC→TAI.
Le query vengono confrontate con la selezione, oltre che col registro. La regressione ora rifiuta quel caso.
La ricevuta registra anche SHA e numero di righe del prefisso di registro controllato, oltre allo SHA dello script:
il successivo append di eventi FITS non deve alterare la prova del prefisso già verificato.

Non sono cambiate acquisizione, risposte, prodotti derivati, selezione, protocollo o regole QUALITY.

## Verifica svolta

- Selftest originale 14/14 rieseguito; dopo il controllo delle query: **15/15**.
- Sonda indipendente: base sintetica accettata, finestra sbagliata coerente fra risposta/registro ora rifiutata.
- Verificati gli hash dei sette prodotti conservati e l'identità byte per byte con 98ee895.
- Verificato il registro conservato: 90 start/end metadata, 90 richieste, 349154 byte, senza eventi FITS;
  protocollo e META della selezione coincidono con i legami dell'acquisizione.
- Nessuna composizione QUALITY × INTERVAL o scelta A/B reale ispezionata per anticipare l'interpretazione;
  il controllo ha riguardato codice, dati sintetici, hash e contatori di provenienza.

## Via al passo successivo

**Via al riconteggio reale con --check dal commit di questa revisione.** Conservare la ricevuta completa
e positiva prima di leggere/interpretare QUALITY × INTERVAL. Se il controllo fallisce, conservare l'esito
e fermare il passo dipendente, senza rifare richieste per correggere un problema puramente offline.

Dopo il riconteggio positivo: lettura dei metadati e proposta di eventuale emendamento QUALITY, congelato prima
dei FITS L2 e dichiarato dopo risultati L1/2010 già noti. Nessun allargamento automatico a 0x200 e nessuna
nuova acquisizione sono autorizzati da questa chiusura. Downloader, adattatore e misura L2 restano separati.

Gli avvisi pandas di futura modifica della concatenazione non hanno fatto fallire i test; non costituiscono
un risultato scientifico. L'oracolo geometrico indipendente 2d5b99e resta disponibile per il blocco C.

# MDI L2 — chiusura tecnica di piano A1, downloader e adattatore

23 novembre 2026, Codex. Revisione di `20e1d73` e dei predecessori
`b6f6658`, `6591de5`, `ecbf218`, `1f56eea`. Nessuna richiesta di rete,
nessun magnetogramma reale letto e nessun tilt misurato in questa revisione.

## Esito

Piano A1, blocco B (download) e blocco C (adattatore) approvati con le
correzioni di questa revisione. Il piano conservato resta invariato:
159 file principali e due supplementari per le assegnazioni originali,
161 file unici. Non si rigenerano scelte, prodotti o ricevute storiche.

Il via è tecnico: prima di `mdi_fd_fetch.py --fetch` serve l'autorizzazione
esplicita dell'utente ai FITS. Il download può precedere il completamento
del codice della misura L2, perché non calcola tilt. La misura L2 e il suo
riconteggio devono invece essere rivisti prima dell'esecuzione.

## Tre correzioni riprodotte e verificate

1. Un'interruzione fra l'inizio del trasferimento e la scrittura del checkpoint
   permetteva di oltrepassare il limite di due tentativi. Ora il conteggio
   deriva dagli inizi persistenti del registro condiviso, anche se ancora
   aperti. Il checkpoint deve essere compatibile con quel registro.
2. Il trasporto validato salva i contatori nel sidecar anche quando fallisce,
   ma non li inoltra nell'eccezione. Il wrapper recupera il contatore fresco,
   scarta prima i sidecar precedenti e, se il contatore manca, conta
   prudenzialmente due richieste dichiarandolo stimato. Il trasporto
   `transfer_a1` resta invariato.
3. Planner e riconteggio verificavano il META della selezione, senza verificare
   i contenuti effettivi dei tre CSV. Ora controllano insieme esatto dei
   prodotti, hash reali, ricevuta completa della selezione e ricevuta dei
   metadati ancorata al congelamento A1. Una latitudine cambiata nel SAMPLE
   lasciando il META invariato viene rifiutata.

Queste sono correzioni di integrità e contabilità: protocollo, soglie,
QUALITY ammesse, budget e assegnazioni scientifiche non cambiano.

## Verifiche

- Downloader: selftest 12/12, con trasferimenti simulati e FITS sintetici.
- Planner: selftest 7/7.
- Riconteggio del piano: selftest 8/8, inclusa la selezione alterata;
  il piano conservato supera anche il confronto completo offline.
- Oracolo geometrico indipendente: 23/23, 324 configurazioni geometriche,
  pixel rettangolari, LOS/mu, BLANK e QUALITY. Accetta esplicitamente 0x200
  sotto A1; rifiuta 0x201, 0x280 e 0x600. Non valida la calibrazione fisica
  dei dati reali.
- Sonda indipendente `scripts/mdi_l2_download_review_probe.py`: due tentativi
  interrotti, nessuna terza chiamata; un errore con sidecar conta una richiesta;
  selezione alterata rifiutata. La sonda usa solo trasporti simulati e i
  metadati gia conservati, senza rete o FITS reali.

Controlli del repository: sintassi e launcher positivi; pytest 154 casi positivi
nel sandbox e quattro test di trasporto locale bloccati esclusivamente dalla
creazione del socket. Ripetuti i soli quattro casi con permessi per localhost:
4/4 positivi, quindi 158/158 complessivi. Nessun contatto JSOC. `git diff --check`
positivo.

## Passo successivo

Dopo autorizzazione: download dal commit che contiene questa chiusura,
conservazione di checkpoint, registro e RUN prima della lettura, verifica
SHA e completezza. Le 322 richieste FITS sono una previsione con un tentativo
e un redirect per file: con le 90 richieste di metadati fanno 412.
Fallimenti e riprese restano conteggiati nel tetto cumulativo di 600 richieste,
220 file e 1,5 GB; una prenotazione da 32 MiB viene sostituita dai byte effettivi.
Il raggiungimento dei tetti puo produrre un'esecuzione incompleta, con uscita 2.
Nessuna nuova autorizzazione alla rete e implicita in questa revisione.

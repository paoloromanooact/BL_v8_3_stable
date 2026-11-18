# Secondo campione MDI–HMI — protocollo CONGELATO

**CONGELATO il 18 novembre 2026** dopo le revisioni di Codex (metodologica della rev. 1 e del codice `6f40618`; via al congelamento dopo la rimozione del limite complessivo di 30 minuti). Testo della bozza revisione 2 (conservata in `docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE_DRAFT.md`, che ha ancora il limite di 30 minuti); SHA-256 e commit in `docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE_FREEZE.json`. La revisione 2 recepiva NPIX come filtro e non garanzia, segnalazioni separate per secondo campione e unione, verifica
del tilt in R0 dichiarata a parte. Al congelamento nessuna selezione, richiesta a JSOC o mappa nuova. Estende il protocollo congelato
`docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON.md` (`6d6fd12`) con l'emendamento A1 (`c409666`): tutto ciò che non è
scritto qui resta identico (strati, certificato geometrico del §8, regola QUALITY, rami A1/A2/B, dominio μ, soglie
100/10000 G, misure, d_γ, sintesi, soglia operativa di 2,107°, limite per T3).

## 1. Perché un secondo campione

Il primo campione (`docs/MDI_HMI_SMALL_COMPARISON_RESULTS.md`) ha dato B su 4 coppie su 12 e uno strato vuoto, quindi
copertura incompleta e decisione aperta. Le perdite non dipendono dal confronto ma dalla selezione al minimo: 4 HARP e
6 TARP senza pixel della patch nell'istante scelto, 3 HMI con una sola polarità, una bitmap SMARP con codici non
documentati.

**Non cieco.** Le regole sotto sono scritte dopo aver visto gli stati di disponibilità del primo campione e i suoi
risultati (differenze di tilt, flussi, dipoli). Il controllo che le motiva usa solo metadati: nelle 12 coppie
**NPIX mancante (USFLUXL = 0) coincide con i record senza maschera utilizzabile**, su entrambi gli strumenti: 11 record
su 24, cioè 4 HMI e 6 SMARP con maschera vuota verificata, più 1 SMARP (TARP 13670) rifiutato dall'adattatore per codici
di bitmap non documentati (1 e 2), caso distinto. Delle 5 coppie con NPIX presente su entrambi, 4 hanno dato B e una
(HARP 107) una sola polarità. Nessuna soglia di flusso è adottata: sarebbe tarata su un solo caso.

NPIX > 0 è **un filtro sui metadati, non una garanzia**: 24 record non bastano a stabilire che funzioni sempre. Nel
secondo campione restano possibili maschere vuote, codici di bitmap non documentati e una sola polarità; la maschera
si verifica comunque sulle mappe e ogni perdita si registra con la sua causa, senza sostituzioni.

## 2. Regole nuove

1. **Pixel della patch su entrambi.** Oltre alle condizioni del §3 congelato e al certificato geometrico, un arco è
   eleggibile solo se NPIX è finito e > 0 sia nel record SMARP sia in quello HMI (campi già salvati nei record
   dell'inventario, `schema_20261116_http_ac06138`). NPIX mancante, non numerico o nullo esclude l'arco con motivo.
   La regola si applica prima della scelta dell'arco per coppia e strato, che resta quella del §3.
2. **Indipendenza dal primo campione.** Si escludono le 12 componenti G10 usate nel primo campione: nessuna regione
   già misurata rientra.
3. **Dimensione.** Fino a **5 coppie per strato (20)**, stesso giro N centrale, S centrale, N laterale, S laterale,
   stessa regola di una componente per coppia, nessun riempimento fra strati. Ordine per SHA-256 di
   `MDI_HMI_PILOT_V2|TARPNUM|HARPNUM` (prefisso nuovo, per non riprodurre l'ordine del primo campione).
4. **Bipolarità non garantita.** Nessun metadato salvato la assicura; le coppie con una sola polarità restano perdite
   registrate, senza sostituzioni.

Bacino stimato dai soli metadati (archi certificati, NPIX > 0 su entrambi, componenti del primo campione escluse):
1217 archi, 47 coppie e 47 componenti; componenti per strato N centrale 32, S centrale 10, N laterale 28, S laterale
11, di cui 34 presenti in più strati. Il riempimento effettivo dei due strati sud si conoscerà solo applicando il giro.
Fra gli archi del bacino 28 hanno QUALITY MDI = 0.

## 3. Acquisizione

Stesso trasporto dell'emendamento A1 (un redirect ammesso verso jsoc1 con TLS verificato, arresto dopo 3 errori
consecutivi della stessa classe), con il downloader già provato. Prima del download: disponibilità dei segmenti con
`rs_list` per record esatto, come nel primo campione. Budget nuovo e separato: al più 450 richieste HTTP (disponibilità,
keyword e FITS, ogni richiesta contata, redirect compresi), **nessun limite complessivo di tempo** (decisione dell'utente,
18 novembre; restano i timeout delle singole richieste), 512 MiB e 32 MiB per file; al più due
tentativi per file. Stima: circa 140 FITS e 10–12 MB.

## 4. Analisi e lettura

- Le misure del primo e del secondo campione si riportano **separate e poi insieme** (fino a 32 coppie, di cui
  valutabili quelle del primo, 4 per B, più quelle del secondo). L'unione è dichiarata ora, prima delle mappe.
- La soglia operativa di 2,107° e la regola di copertura del §5 congelato si applicano al secondo campione e
  all'unione, separatamente. **Se scatta una segnalazione nel secondo campione oppure nell'unione, la decisione resta
  aperta**: una segnalazione del secondo campione non viene assorbita dall'aggregazione con il primo. Con almeno una
  coppia B valutabile in ciascuno dei quattro strati nell'unione e nessuna segnalazione né nel secondo campione né
  nell'unione, il seguito proponibile resta un protocollo per un catalogo **descrittivo** MDI; la decisione finale è
  dell'utente. La segnalazione del primo campione (nord, n = 1) resta documentata e discussa nel rapporto finale;
  il secondo campione è progettato conoscendola.
- **R0 con verifica del tilt dichiarata a parte.** R0 applica P1 invariata a tutti i record HMI selezionati. Se un
  record coincide con un record storico di P1 ed è **bipolare** in entrambi, si confrontano anche tilt, centroidi e
  D_bal con il catalogo; se nessuna coincidenza è bipolare, si registra che **la riproduzione storica del tilt resta non
  verificata**, come nel primo campione (HARP 191 unipolare). Flusso e latitudine si riportano comunque.
- Stesse due implementazioni indipendenti del primo campione (runner sui kernel di Codex e riconteggio di Claude),
  output conservati prima della lettura, confronto riga per riga.
- Il limite per T3 resta invariato: la scala di circa 0,4° non è risolvibile e nessun esito autorizza un T3 combinato.

## 5. Porte prima del congelamento

1. Revisione di Codex delle regole 1–4, del budget e della dichiarazione di non cecità.
2. Script di selezione con prove offline (riuso della logica verificata di `scripts/mdi_hmi_selection_check.py`);
   doppia selezione indipendente come nel primo campione.
3. Solo dopo il congelamento: disponibilità, download, R0, confronti.

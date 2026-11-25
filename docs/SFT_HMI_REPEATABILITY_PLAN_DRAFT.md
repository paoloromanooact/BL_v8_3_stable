# HMI: ripetibilità a breve intervallo e incertezza dei confronti SFT — bozza

25 novembre 2026, Codex. **Bozza non congelata; nessuna misura sui pixel eseguita.**
Decisione dell'utente: affrontare il §7 del pilota osservativo, come preparazione del confronto bayesiano HMI,
invece di dichiarare subito l'errore non stimato e rinviare il lavoro.

## Scopo e limiti

Serve all'obiettivo sorgente BL (errore osservativo e discrepanza nell'evoluzione locale) e puo informare la
componente di misura del modello di quenching HMI. Non stima automaticamente la dispersione intrinseca dei tilt
ne la dipendenza temporale fra rotazioni, che restano componenti del modello bayesiano BQ.

La prima uscita e la **distribuzione delle differenze osservate a breve intervallo**. Non coincide con un errore
strumentale assoluto: comprende evoluzione, preparazione delle mappe, errori correlati e selezione dei record.
Con due misure X1 e X2, Var(X2-X1) include Var(e1)+Var(e2)-2Cov(e1,e2), oltre all'evoluzione reale e alle eventuali
covarianze con essa. Dividere automaticamente la deviazione delle differenze per sqrt(2) non e giustificato.
Una dispersione piccola non e neppure un limite superiore garantito all'errore delle singole misure.

## Prima fase: fattibilità dai soli metadati e header

Lo script `scripts/sft_hmi_repeatability_metadata_audit.py`:

- elenca le collezioni locali e la precedenza dei percorsi duplicati;
- ricostruisce le coppie consecutive della stessa HARP usando T_OBS esplicito in TAI, conservando il confronto
  con la precedente conta nominale di 299 coppie/296 HARP basata sui nomi;
- legge dimensioni e keyword, mai array magnetici; registra hash dei keys e degli header, copertura WCS sullo
  stesso ramo di longitudine e area geometrica di C con la regola gia proposta nel pilota;
- descrive la sovrapposizione con l'intero bacino primario-controllo eleggibile, le famiglie note e possibili
  intersezioni spazio-temporali di bounding box;
- conta una riserva conservativa escludendo tutto quel bacino, le sue famiglie note e le possibili intersezioni.
  Questo e un conteggio di disponibilita, non una nuova selezione scientifica congelata.

I valori di pixel mancanti e la copertura di campi finiti non sono verificabili dagli header. Non dichiarare
l'indipendenza sulla sola diversita degli HARPNUM. Le coppie che condividono record/famiglie devono restare
raggruppate. Eventuali identita/corrispondenze fisiche non ricostruibili restano limiti espliciti.

## Seconda fase: specifica della misura prima dei pixel

Prima della misura, Claude e Codex completano e congelano una specifica collegata al §7. Deve fissare:

1. La popolazione e la regola deterministica di scelta delle coppie, con tempi reali, disponibilita, qualita,
   geometria, famiglie e cause di perdita; nessun rimpiazzo deciso dalle differenze misurate.
2. L'esclusione delle HARP e delle componenti collegate al campione SFT conservato. Finche il campione non e
   conservato, l'audit del bacino intero e soltanto una verifica conservativa di disponibilita.
3. Preparazione coerente con il pilota: WCS, area dei pixel, dominio comune, mappe grezze e varianti P1/bilanciate
   distinte; registrare anche lo scarto introdotto dalla rimappatura, senza compensarlo con una calibrazione.
4. Osservabili: dipolo locale D_C, flussi delle polarita e netto, centroidi, separazione e tilt; valori non
   definiti espliciti, differenze circolari/assiali, confronto sullo stesso supporto. Separare le differenze
   osservate da quelle eventualmente corrette con un trasporto prescritto: la correzione non e una verita nota.
5. Riepiloghi e incertezza per gruppi indipendenti, dipendenza dall'intervallo temporale, latitudine, dimensione
   e distanza dal meridiano; numero limitato di suddivisioni fissate prima delle differenze. Non trattare migliaia
   di pixel o piu coppie della stessa HARP come repliche indipendenti.
6. Codice e riconteggio indipendente, prove sintetiche con errori noti e correlati, mappe immutate, evoluzione
   imposta e cambi di campo di vista. Conservazione degli output prima della lettura e rapporto dedicato.

## Terza fase: uso bayesiano

Il ranking BT richiede una likelihood con errore di osservazione **e discrepanza del modello**. Le differenze
entro due ore informano una scala empirica; il trasferimento al confronto a 1–4,5 giorni richiede assunzioni
esplicite e sensibilita. Non estrapolare automaticamente la varianza proporzionalmente al tempo e non porre
l'emersione non modellata uguale al rumore strumentale.

La likelihood congiunta deve considerare che dipolo, flussi e geometria vengono dalle stesse mappe. Prior,
separazione sviluppo/verifica, controlli predittivi e criteri del ranking vanno fissati prima della verifica.
Se le coppie non consentono di identificare separatamente gli errori, si riporta la scala di ripetibilita e si
modella l'incertezza residua con sensibilita dichiarate: non si inventa una calibrazione assoluta.

## Assegnazioni e prossimo passo

- Codex: audit indipendente dei metadati, questa proposta e revisione della specifica/riconteggio.
- Claude: continua A1 e le correzioni del pilota mappa-bipolo; usa la consegna di questo audit senza duplicarlo.
- Poi: recepire i conteggi nel §7 della bozza osservativa, completare la specifica di ripetibilita, revisione
  incrociata e congelamento prima dei pixel. Nessun fit bayesiano o pilota osservato parte da questa bozza.

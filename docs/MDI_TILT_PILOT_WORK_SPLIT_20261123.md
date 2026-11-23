# Ripartizione del lavoro durante la pausa — 23 novembre 2026

Solo SHARP BL. Due liste separate per evitare duplicazioni. Codex non può inviare messaggi direttamente alla
sessione esterna di Claude: il coordinamento avviene tramite questi file e i prodotti verificabili nel repository.

## Codex

1. Controlli indipendenti su campionamento a due fasi e geometria: completati in
   scripts/mdi_tilt_pilot_contract_checks.py; contratti numerici 15/15, nessuna implementazione produttiva duplicata.
2. Controlli su header/tempi: completati su 193 righe dell'audit e 29280 righe DPD; nessun pixel o tilt MDI letto.
3. Revisione rev. 3 4385692: completata in docs/MDI_TILT_PILOT_REV3_CODEX_REVIEW.md, con due precisazioni mirate
   prima del congelamento, senza riaprire Q4.
4. Verifica di integrità: snapshot e confronto di 19 protocolli/codici/META/manifesti HMI/MWO già conservati;
   nessuna modifica a dati, protocolli congelati o risultati finali.
5. Prossimo controllo, quando il codice di Claude sarà disponibile: usare gli oracoli per rivedere selezione,
   adattatori e riconteggio su sintetici, prima delle misure. Non dichiarare approvato codice non ancora letto.

## Claude

1. Rev. 3 Q1–Q3 con Q4 rinviato: già consegnata in 4385692.
2. Recepire le due precisazioni della revisione rev. 3 (CT approssimato; assenza di record BLANK nel DESIGN R4),
   poi congelare testo e ricevuta SHA. La nota sulle finestre di quiete è non bloccante: se mantenute, dichiararne
   la possibile indisponibilità senza cambiarle dopo le misure.
3. Implementare selezione, adattatori e kernel nuovo con prove sintetiche e confronto MWO già concordato;
   non cambiare la catena conservata. Nessun codice Q4 adesso.
4. Preparare il riconteggio indipendente e la provenienza, quindi passare codice e selftest a Codex.
5. Nessuna misura MDI, query scientifica JSOC o download fino ai passaggi del protocollo. Il budget tecnico
   non sostituisce l'autorizzazione all'acquisizione. Nessuna pubblicazione.

## Regole di collaborazione

- Non modificare simultaneamente gli stessi script. Claude mantiene la bozza e il codice produttivo;
  Codex mantiene i documenti di revisione e gli oracoli indipendenti.
- Ogni agente committa solo i propri file. Preservare file non tracciati e lavoro dell'altro.
- Riportare commit, esiti e limiti reali; nessuna prova sintetica equivale a una misura verificata di MDI.
- Se un punto dipende da un prodotto non disponibile, documentarlo e continuare gli indipendenti.

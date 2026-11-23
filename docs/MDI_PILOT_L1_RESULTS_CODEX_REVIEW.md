# Pilota MDI L1 — revisione del rapporto e seguito

Oggetto: rapporto 79fb406, corsa eda3515, riconteggio ba71036. Codex.

## Chiusura del rapporto

Controllati gli hash effettivi dei prodotti e il legame della ricevuta completa 13/13 al META dell'analisi.
Ricalcolate separatamente le rese pesate dalla selezione e dagli stati L1: 0,9282355 e 0,8170709,
denominatore proiettato 5401. Confermati 251 confronti principali, mediana |d_ax| 8,4789 gradi,
7,171% oltre 45 gradi e mediana del rapporto di flusso 13,6667. Non ripetuta l'intera analisi/bootstrap.

Il rapporto è approvato con le precisazioni applicate:

- Popolazione DPD eleggibile del periodo maggio 1996–ottobre 2010, con porzioni dei cicli adiacenti al 23;
  il 92,8% è una stima proiettata, non il conteggio di tutte le regioni del ciclo 23.
- La resa proiettata non è monotona con l'attività (89,9 / 94,3 / 94,2%). Le differenze M1/U non isolano
  causalmente la selezione; Q3 riporta mediane non pesate delle coppie M1 misurate del campione bilanciato.
- Le due soglie non sono repliche indipendenti. Gli intervalli nominali sotto zero in alcuni sottogruppi
  non dimostrano una dipendenza sistematica o uno strumento responsabile.
- La causa del rapporto di flusso non è identificata. Alla soglia principale entrambi i percorsi usano 50 G:
  non attribuire il fattore 13,7 a diverse soglie nominali. Il passaggio a 100 G non isola tutte le componenti.
  L'intervallo 7–21 riguarda mediane di sottogruppi, non i rapporti individuali (circa 4,20–226,83).
- La MAD riassume le finestre disponibili, non il rumore dell'intero archivio. Il fit M resta esplorativo.
- Q2 valuterà differenze sinottiche/full-disk sul sottoinsieme L2, senza assumere automaticamente corretto
  il full-disk o identificare le cause degli scarti da MWO. Q4 sarà condizionato agli scenari dichiarati.

Nessun numero scientifico, output conservato, soglia o protocollo è stato cambiato.

## QUALITY: percorso proposto, non autorizzazione di rete

Un solo record 2010 non descrive il periodo 1996–2010. Prima dei FITS è sensato acquisire soltanto metadati
dei 90 gruppi L2 già selezionati, mantenendo le risposte non filtrate per QUALITY.
Preparare QUALITY × INTERVAL per periodo/cella/coorte, e conteggi di A e coppie A/B ottenibili con QUALITY=0
e con l'eventuale insieme {0,0x200}, senza misurare immagini né cambiare gruppi o giorni.

La definizione primaria già acquisita è documentata in `MDI_SMARP_METADATA_CLARIFICATIONS.md`:
0x200 = MDI non in PRIME 60; non è una prova che i prodotti siano equivalenti né un indicatore univoco del
tempo di integrazione. La vecchia tabella full-disk del 2010 contiene sia INTERVAL=30 sia INTERVAL=300
all'interno di 0x200. Non estenderla automaticamente a tutto il periodo storico.

Dopo i metadati si potrà scrivere un eventuale emendamento separato e congelato prima dei FITS L2, dichiarando
che i risultati L1 e i confronti 2010 erano già noti. Lasciare intatta la regola originale QUALITY=0 e riportarne
la copertura; un allargamento non certifica omogeneità o una calibrazione. INTERVAL e modo restano registrati.

## Prima di usare il codice dei metadati

Il codice a267c1b è ancora incompleto e non riceve qui il via a --fetch. Dalla lettura emergono almeno:

1. La query va da t_DPD−6h a t_DPD+10h, ma B può precedere A di 4h: con A a −6h occorrono dati fino a −10h.
   Prevedere una finestra simmetrica ±10h (o query dipendenti equivalenti), senza cambiare la scelta A/B.
2. `jsoc_to_utc` dichiara di accettare secondi frazionari ma li tronca con `[11:19]`: preservarli e provare
   istanti interi/frazionari, secondi=60, UTC/TAI e i bordi di ±6h e ±4h.
3. Il registro locale del tentativo non è ancora il registro condiviso di metadati+FITS. Prima della rete
   chiudere provenienza, contabilità cumulativa di richieste/byte anche falliti o parziali, riprese e redirect;
   dichiarare gli esiti incompleti e non trattare dimensioni ignote come zero.

Questa è un'indicazione preliminare per il codice in lavorazione, non una revisione completa di adattatore,
trasporto o downloader. Nessuna richiesta di rete eseguita e nessuna autorizzazione dell'utente inferita.

I due obiettivi restano sorgente BL e quenching del tilt. Q1/Q3 sono un risultato descrittivo del pilota;
una serie BL combinata e un nuovo T3 richiedono specifiche proprie, non derivano automaticamente da questi esiti.

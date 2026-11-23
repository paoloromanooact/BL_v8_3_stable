# Pilota MDI — emendamento A1: QUALITY ammessa per il livello 2 e confronto con la regola originale

**CONGELATO dopo la revisione Codex di 68ab474, prima dei FITS L2. Non autorizza scaricamenti.**
- Testo revisionato e congelato prima dei FITS L2. La ricevuta separata ne registra SHA-256 e commit.
- Modifica soltanto la regola di ammissibilità dei metadati del livello 2 (§4 del protocollo congelato,
  SHA `77367350…`). Le prenotazioni e i tetti del registro restano invariati. Si specifica anche il controllo
  secondario con le assegnazioni originali. Tutto il resto resta invariato.

## Non è cieco: cosa era già noto

- Esiti del livello 1, sulle mappe sinottiche (`docs/MDI_PILOT_L1_RESULTS.md`): rese, scarti relativi MDI − MWO.
- Confronti MDI–HMI del 2010 e controllo geometrico su un FITS MDI locale.
- Diagnostica offline di Codex sulle assegnazioni: 2 file originali fuori dal piano ampliato e 3 coppie
  con QUALITY diversa a INTERVAL invariato; nessuna misura di tilt nuova.
- La composizione QUALITY × INTERVAL dei 90 gruppi del livello 2 e i conteggi di A e delle coppie A/B sotto le due
  regole, letti dopo la conservazione (`98ee895`) e il riconteggio 12/12 (`9d3e937`).

**Nessun FITS è stato acquisito nella nuova fase L2 e nessun confronto di tilt L2 è stato calcolato.**
Restano già noti i confronti del 2010 e il controllo geometrico su un FITS locale, dichiarati sopra: questo
percorso non è presentato come interamente cieco.

## Cosa mostrano i metadati (finestre di ±6 h attorno a t_DPD, 90 gruppi, tutte le richieste riuscite)

**Occorrenze dei record nelle finestre acquisite del campione** (non un censimento dell’intero archivio):

| QUALITY | record con INTERVAL 30 s | record con INTERVAL 300 s |
|---|---|---|
| 0 | 38 | 21 |
| **0x200** (bit 9: MDI non in PRIME 60) | **293** | **226** |
| altri valori (0x201, 0x280, 0x600, 0x1d, 0x3d, 0x10205, …) | 6 | 23 |

- Il valore 0 compare quasi solo nel 1999–2000 (57 dei 59 record con QUALITY 0); dal 2001 i record sono quasi tutti
  0x200.

**Gruppi con un'immagine A e con una coppia A/B:**

| Regola | A | coppia A/B |
|---|---|---|
| congelata, {0} | **12 / 90** | 9 |
| {0, 0x200} | **81 / 90** | 78 |

Per gruppo:
- per coorte, M1 e U: 5 e 7 con la regola congelata, 50 e 31 con {0, 0x200};
- per attività, terzili 1/2/3: 2/2/8 con la regola congelata, 25/26/30 con {0, 0x200};
- con la regola congelata le A cadono quasi tutte nel 1999–2000.

**Conseguenza.** Con la regola originale Q2 avrebbe al più 12 immagini A e la ripetibilità 9 coppie da metadati,
con una forte concentrazione temporale e nel terzile più attivo. Il confronto sarebbe limitato a quella copertura,
non generalizzabile da solo all’intero periodo.

## Regola emendata

1. **QUALITY ammessa per il livello 2: {0, 0x200}.**
   - Il bit 9 (0x200) è documentato come «MDI non in PRIME 60» (`docs/MDI_SMARP_METADATA_CLARIFICATIONS.md`, tabella
     standard MDI): un flag di **modo operativo**, che da solo non documenta un errore di telemetria o elaborazione.
     Questo non dimostra l’assenza di effetti strumentali né l’equivalenza dei modi.
   - Restano esclusi tutti gli altri valori, compresi quelli con il bit 10 (0x400, raggi cosmici, per esempio 0x600)
     o con i bit 0–8 (telemetria, dati mancanti, puntamento). Gli stati «mancante» e «non interpretabile» restano
     esclusi.
   - L'ammissione non certifica omogeneità né una calibrazione fra i modi.
2. **Scelta di A e B invariata nelle regole**: ±6 h, coppia con lo stesso INTERVAL numerico entro 4 h, spareggi. Si
   applica con l'insieme {0, 0x200}.
   - La coppia A/B continua a richiedere lo stesso INTERVAL, quindi i modi 30 s e 300 s non si mescolano nella
     ripetibilità.
   - La QUALITY di A e B si registra per record, con il conteggio delle transizioni di QUALITY nelle coppie.
     Nei metadati sono presenti 3 coppie con QUALITY diversa pur avendo lo stesso INTERVAL; non si
     escludono a posteriori. Stesso INTERVAL non significa necessariamente stesso stato operativo.
3. **Risultati riportati in modo da separare i modi**, tutti descrittivi:
   - Q2, Q3 full-disk e ripetibilità, sull'insieme ammesso;
   - per QUALITY di A (0 contro 0x200) e per INTERVAL di A (30 contro 300 s);
   - si riportano la copertura e una tabella secondaria sotto la regola originale: 12 gruppi con A e 9 coppie,
     usando le **assegnazioni originali di A/B**, non filtrando per QUALITY le nuove assegnazioni.
     Sono disponibilità da metadati: eventuali fallimenti di trasferimento o misura si riportano senza sostituzioni.
     Tre A cambiano passando alla regola ampliata; 2 file originali non rientrano nel nuovo insieme di 159.
     Il piano include anche questi 2 file per il solo controllo secondario: **161 file unici** in totale,
     senza aggiungere gruppi o giorni. Il controllo originale resta limitato al suo piccolo sottoinsieme.
4. **Nuovo piano senza nuove richieste**: le scelte e il piano si rigenerano dalle risposte conservate
   (`ANSWERS.jsonl`), con codice rivisto, conservazione e riconteggio. Nessuna nuova interrogazione a JSOC.

## Budget: prenotazioni e consumi rimangono distinti

- Le dimensioni dei segmenti non sono disponibili nei metadati (vuoto o «NA»); rimangono ignote, non zero.
- Si mantiene il limite/prenotazione preesistente di **32 MiB** per tentativo con dimensione ignota.
  Per un tentativo concluso, il registro sostituisce la prenotazione con i byte effettivi; per un tentativo
  interrotto senza fine conserva la prenotazione prudente. Non si sommano 32 MiB per ogni file riuscito.
- La previsione iniziale «arresto dopo circa 46 file» era quindi errata per lo scaricamento sequenziale.
  Una prova sintetica con 161 file da 1,6 MB termina con 257949154 byte totali, incluse le richieste metadata,
  pur prenotando 32 MiB a ogni tentativo. Questa prova controlla il registro, non predice le dimensioni reali.
- I 42 FITS locali (1,41–1,57 MB) sono un riferimento per una stima, non un limite dimostrato per tutto il piano.
  Non si introduce il nuovo limite di 4 MB sulla base di quel sottoinsieme.
- Il riferimento con un solo tentativo e un redirect per file è **90 + 2×161 = 412 richieste**. Fallimenti,
  riprese e trasferimenti parziali consumano budget aggiuntivo. Non si promettono 640 MB come massimo complessivo.
- Restano i tetti cumulativi di **600 richieste, 220 file e 1,5 GB**, tutti i tentativi inclusi; raggiungerli
  impone l’arresto e la dichiarazione della copertura incompleta, senza sostituzioni o allargamenti automatici.

## Cosa non cambia

- Selezione, gruppi, giorni, soglie, finestre di misura, analisi e tetti cumulativi del registro.
- Il congelamento dell'emendamento non autorizza la rete: lo scaricamento dei FITS richiede la chiusura dei
  blocchi B e C, un nuovo via di Codex e l'autorizzazione esplicita dell'utente.

## Decisioni fissate con questa revisione

- Ammessi esattamente 0 e 0x200; **non** 0x201, 0x280 o altri valori composti.
- Nessuna modifica del limite/prenotazione di 32 MiB né dei tetti cumulativi.
- Tabella originale separata, con assegnazioni A/B originali e due file supplementari esplicitamente etichettati.
- Nuovi piano e ricevuta in una cartella distinta, legati agli SHA di protocollo, A1, metadati e riconteggio;
  i prodotti originali di 98ee895 e le due ricevute di riconteggio restano intatti.

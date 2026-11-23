# Pilota MDI — emendamento A1 (BOZZA): QUALITY ammessa per il livello 2 e prenotazione per file

**BOZZA, 24 novembre 2026 (Claude). Non congelata, non applicata.**
- Va rivista da Codex e congelata **prima** di qualsiasi scaricamento di FITS.
- Modifica soltanto la regola di ammissibilità dei metadati del livello 2 (§4 del protocollo congelato,
  SHA `77367350…`) e la prenotazione del registro per i FITS. Tutto il resto resta invariato.

## Non è cieco: cosa era già noto

- Esiti del livello 1, sulle mappe sinottiche (`docs/MDI_PILOT_L1_RESULTS.md`): rese, scarti relativi MDI − MWO.
- Confronti MDI–HMI del 2010.
- La composizione QUALITY × INTERVAL dei 90 gruppi del livello 2 e i conteggi di A e delle coppie A/B sotto le due
  regole, letti dopo la conservazione (`98ee895`) e il riconteggio 12/12 (`9d3e937`).

**Nessun magnetogramma del livello 2 è stato scaricato o guardato.**

## Cosa mostrano i metadati (finestre di ±6 h attorno a t_DPD, 90 gruppi, tutte le richieste riuscite)

**QUALITY dei record:**

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

**Conseguenza.** Con la regola congelata Q2 e la ripetibilità poggerebbero su 12 gruppi, concentrati in due anni e
nel terzile più attivo: il confronto sinottica–full-disk non rappresenterebbe né il ciclo né le classi.

## Regola proposta

1. **QUALITY ammessa per il livello 2: {0, 0x200}.**
   - Il bit 9 (0x200) è documentato come «MDI non in PRIME 60» (`docs/MDI_SMARP_METADATA_CLARIFICATIONS.md`, tabella
     standard MDI): un flag di **modo operativo**, non un difetto del dato.
   - Restano esclusi tutti gli altri valori, compresi quelli con il bit 10 (0x400, raggi cosmici, per esempio 0x600)
     o con i bit 0–8 (telemetria, dati mancanti, puntamento). Gli stati «mancante» e «non interpretabile» restano
     esclusi.
   - L'ammissione non certifica omogeneità né una calibrazione fra i modi.
2. **Scelta di A e B invariata nelle regole**: ±6 h, coppia con lo stesso INTERVAL numerico entro 4 h, spareggi. Si
   applica con l'insieme {0, 0x200}.
   - La coppia A/B continua a richiedere lo stesso INTERVAL, quindi i modi 30 s e 300 s non si mescolano nella
     ripetibilità.
   - La QUALITY di A e B si registra per record.
3. **Risultati riportati in modo da separare i modi**, tutti descrittivi:
   - Q2, Q3 full-disk e ripetibilità, sull'insieme ammesso;
   - per QUALITY di A (0 contro 0x200) e per INTERVAL di A (30 contro 300 s);
   - si riportano anche la copertura e, dove possibile, gli esiti sotto la regola congelata originale (12 gruppi).
4. **Nuovo piano senza nuove richieste**: le scelte e il piano si rigenerano dalle risposte conservate
   (`ANSWERS.jsonl`), con codice rivisto, conservazione e riconteggio. Nessuna nuova interrogazione a JSOC.

## Prenotazione per file (tecnica, legata al registro)

- JSOC non ha restituito le dimensioni dei segmenti: la colonna `*size*` è vuota o «NA» per tutti i record scelti.
- Con dimensione ignota il registro riserva il tetto di 32 MB per file: il tetto cumulativo di 1,5 GB fermerebbe lo
  scaricamento dopo circa 46 file, contro circa 159 file del piano emendato.
- **Proposta: prenotazione di 4 MB per file** di questa serie quando la dimensione è ignota. È circa 2,5 volte il
  massimo osservato su 42 FITS `mdi.fd_M_96m_lev182` locali (1,41–1,57 MB).
  - Il trasferimento resta limitato a quel valore: un file più grande fallisce come «limite» e si conta, non si
    accetta.
  - Su ~159 file il caso peggiore è circa 640 MB, entro 1,5 GB.
  - Le richieste previste sono 90 + circa 2 × 159, sotto 600.

## Cosa non cambia

- Selezione, gruppi, giorni, soglie, finestre di misura, analisi e tetti cumulativi del registro.
- Il congelamento dell'emendamento non autorizza la rete: lo scaricamento dei FITS richiede la chiusura dei
  blocchi B e C, un nuovo via di Codex e l'autorizzazione esplicita dell'utente.

## Questioni per la revisione

1. Se ammettere anche 0x201, 0x280 e simili (bit 0 o 7 con il bit 9): proposta di no, perché sono pochi e i bit 0–7
   segnalano problemi.
2. Il valore di 4 MB e il comportamento del limite per file.
3. Se riportare gli esiti sotto la regola congelata (12 gruppi) come tabella separata o solo come copertura.

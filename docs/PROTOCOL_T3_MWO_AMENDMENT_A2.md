# Emendamento A2 al protocollo T3 su MWO — 18 magnetogrammi con campo ×100 e saturato

**CONGELATO il 20 novembre 2026 da Codex, dopo revisione di 8534f48 e prove sintetiche complete, prima della misura R3.**
Protocollo di riferimento: `docs/PROTOCOL_T3_MWO.md` (SHA-256 `4408a0ee…`), §2 «Magnetogrammi»; emendamento A1
(`bc88452b…`) invariato. **Cieco rispetto ai tilt del catalogo lungo:** restano sigillati; la decisione usa solo header e valori dei pixel.
I risultati del pilota recente MWO e dei confronti HMI/MDI erano già noti.

## Problema

Codex ha notato che i quattro record con peso maggiore del catalogo R2 (NOAA 5668, 5669, 5671, 5678; 1989-09-04/05)
fanno circa il 92 % della somma dei pesi al quadrato e circa il 13 % del flusso totale. Vengono da due magnetogrammi
con header GV = 0,03, mentre tutti gli altri record selezionati hanno GV = 3.

**Controllo dei pixel** (lettore congelato e maschere della misura, disco con μ ≥ 0,8, senza BLANK), sulle scansioni
del 3–5 settembre 1989:
- scansioni con GV = 3: mediana di |B| 2,4–2,7 G, 99° percentile 100–150 G;
- scansioni con GV = 0,03: mediana di |B| 230–285 G (circa ×100, come 3/0,03), 99° percentile e massimo 3276,7 G, pari
  a 32767·BSCALE. I dati sono **saturati**: il fattore 100 non è correggibile, perché il troncamento ha perso
  l'informazione.

Flussi dei quattro record: 3–7·10²³ Mx, contro una mediana del catalogo di 1,2·10²¹ Mx.

**Coincidenza con il progetto del flusso polare.** L'elenco dei 18 file con GV = 0,03 nell'inventario degli header
(6 del 21 ottobre 1988 e 12 del 3–5 settembre 1989) coincide esattamente con i 18 file esclusi dal controllo
qualità congelato di quel progetto: `results/MWO_AUDIT/AUDIT/MWO_STRICT_QC_EXCLUDED_FITS.csv` nel repository
MWO-HMI-MDI, SHA-256 `0594aa66…`, motivazione «pathological field distribution».

## Modifica

1. **Esclusione di un elenco preciso**, non di una regola generale: i 18 file di
   `docs/PROTOCOL_T3_MWO_AMENDMENT_A2_EXCLUDED_FITS.csv` (nome, data, TAVG-UT, GV, dimensione, SHA-256 del contenuto
   del membro dell'archivio). Una regola «GV ≠ 3» toglierebbe anche i magnetogrammi Na I con GV = 1,33, che sono un
   caso diverso e comunque esclusi da T3 come righe Na.
   **Identità del CSV congelato (SHA-256):** `8b7ddba53c54c9771d32da2bb98e2b086f47972765769c823cd8f70349c4758f`. Runner e riconteggio devono verificarla.
   Il numero di membri deve essere 18, senza duplicati; un elenco diverso richiede un nuovo emendamento.
2. **Prima della scelta del magnetogramma.** I file dell'elenco non sono candidati per nessun giorno: la regola
   congelata (classe di risoluzione, poi vicinanza all'ora DPD, poi TAVG minimo) sceglie fra le scansioni restanti
   dello stesso giorno UTC, e la regola del primo giorno riuscito resta invariata. Le regioni coinvolte possono
   quindi essere recuperate da scansioni sane dello stesso giorno o da altri giorni candidati; non vengono cancellate.
3. **Verifica dell'identità.** Runner e riconteggio leggono lo stesso elenco. Il runner verifica lo SHA-256 dei
   membri esclusi quando li incontra e registra in MAGNETOGRAMS lo stato `excluded_A2`. Il riconteggio ricostruisce
   l'esclusione con il proprio lettore e confronta.
4. **Nuova misura R3** in una destinazione nuova (`results/T3_MWO_CATALOGUE_R3`), seguita da riconteggio, controllo
   del disegno, riconteggio del disegno e precisione analitica attesa. R2 resta conservato.
5. **Pesi:** nessun cambiamento in questo emendamento. L'analisi principale resta pesata con Φ_MWO; l'eventuale
   cambiamento si decide dopo i controlli su R3, con un emendamento separato e motivato non solo dall'ampiezza
   dell'intervallo.

Nessun'altra regola del protocollo cambia.

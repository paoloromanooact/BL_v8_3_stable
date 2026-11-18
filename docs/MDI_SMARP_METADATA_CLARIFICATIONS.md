# MDI/SMARP: chiarimenti prima del piccolo confronto reale

Preparazione del 18 novembre 2026, non cieca ai metadati e ai risultati HMI già conservati.
Nessuna nuova query JSOC, mappa, selezione o trasformazione di risposte reali.
Questa nota non modifica il piano dell'inventario o le sue associazioni.

## Che cosa è stato verificato

| Tema | Evidenza primaria | Conseguenza operativa |
|---|---|---|
| LOS CEA | `smarp.c` rimappa il segmento magnetogram come scalare | La CEA non lo trasforma in Br; LOS/μ è un'approssimazione separata |
| QUALITY e T_OBS SMARP | `createCeaRecord` copia entrambi dal record mharp di ingresso | Sono ereditati; non attribuire a QUALITY una definizione HMI |
| Collegamento alla sorgente | `smarp.c` registra MTARP; `m2lostarp.c` registra MDATA e PDATA sul record LOS selezionato | Esiste un percorso di provenienza nel codice, ma i link dei record della corsa non sono stati acquisiti |
| Tempo DRMS | `drms_keyword_slotval2indexval` converte il valore in un indice con epoca, passo e regole di arrotondamento | Essere assegnato a uno slot non impone che il valore T_REC sia esattamente epoca + n·passo |
| Tempi nella migrazione MDI | `ACT_TIME` conserva T_REC e T_OBS distinti, usa INTERVAL per EXPTIME e T_OBS−EXPTIME/2 per DATE__OBS | Non confondere cadenza, intervallo di integrazione, slot e tempo di osservazione |
| Bitmap SMARP | `smarp_functions.c` documenta il bit 32 di appartenenza e i codici combinati con il continuo | Per la maschera di patch usare l'appartenenza, non il solo flag di campo attivo o la presenza di macchie |

Riferimenti al codice ufficiale JSOC-SDP, versione fissata `0cf0b90d354705ed866fdba040772b0d712de785`:

- [smarp.c, copia delle keyword e link](https://github.com/JSOC-SDP/proj/blob/0cf0b90d354705ed866fdba040772b0d712de785/sharp/apps/smarp.c#L485): righe 495–523;
  rimappatura scalare in `mapScaler`, dopo `createCeaRecord`.
- [m2lostarp.c, selezione e link](https://github.com/JSOC-SDP/proj/blob/0cf0b90d354705ed866fdba040772b0d712de785/mag/patch/apps/m2lostarp.c#L126): righe 126–145 e 190–210.
- [ingest_dsds_to_drms.c, tempi](https://github.com/JSOC-SDP/proj/blob/0cf0b90d354705ed866fdba040772b0d712de785/dsdsmigr/apps/ingest_dsds_to_drms.c#L710): righe 710–738.
- [smarp_functions.c, bitmap](https://github.com/JSOC-SDP/proj/blob/0cf0b90d354705ed866fdba040772b0d712de785/sharp/apps/smarp_functions.c#L15): definizioni iniziali.
- [drms_keyword.c, indice di slot](https://github.com/JSOC-SDP/drms/blob/76c2f2887cdd3585dd5b6b4a6198bb77c80285fd/base/drms/libs/api/drms_keyword.c#L2721),
  versione DRMS `76c2f2887cdd3585dd5b6b4a6198bb77c80285fd`, righe 2721–2924.

Si tratta di evidenze sul codice pubblicato. Non è stata dimostrata l'identità fra queste revisioni
e tutti i moduli usati per produrre ogni record della corsa: CODEVER7, versioni e link effettivi
andranno confrontati nel futuro piano. Non trasformare la catena suggerita dal codice in una sorgente
per-record già confermata. Le fonti sono state lette attraverso il connettore GitHub, senza richieste
di inventario; copie locali di consultazione sotto `/tmp/bl_mdi_preparation/sources/`.

Per la geometria HMI, la distinzione fra griglia rimappata e componenti del vettore è esplicitata da
[Sun, nota tecnica SHARP](https://arxiv.org/abs/1309.2392); Br è radiale, Bt verso sud e Bp verso ovest,
come nella [scheda NASA/SPASE SHARP CEA](https://spase-metadata.org/NASA/NumericalData/SDO/HMI/SHARP/CEA/PT720S).
Le direzioni del vettore non coincidono in generale con gli assi del ritaglio CEA.

## Che cosa resta irrisolto

**QUALITY MDI 0x200.** Non è stata verificata una tabella primaria dei bit applicabile al prodotto
SMARP acquisito. La documentazione Stanford indicata dalla letteratura
([MDI lev182](http://soi.stanford.edu/mdi/observables/fd_m_96m_lev182/),
[interpolazione del continuo](http://jsoc.stanford.edu/data/mdi/mdi-tarp/mdi-interp-ic/)) non era
accessibile attraverso il lettore web. Il tentativo diretto nel sandbox ha fallito la risoluzione del
nome; il successivo tentativo con autorizzazione è stato interrotto dai riavvii e non ha lasciato
un file verificabile. Non è dimostrata un'indisponibilità generale del server. Non sono stati usati
come definizione né una pagina secondaria né i bit HMI. Nessun filtro QUALITY è stato introdotto.

**Prodotto 1/5 minuti.** La classificazione registrata resta esattamente 60/300 secondi di INTERVAL.
I 30 s e i valori mancanti rimangono ignoti. Il solo DPC non è decodificato senza una definizione.
La provenienza patch–full-disk richiede i link effettivi e la relativa documentazione. Interrogare
`mdi.lostarp_96m` esulerebbe dall'inventario congelato: servirà una specifica nuova, non un aggiramento.

**Slot full-disk.** Il codice DRMS spiega perché un valore possa non coincidere col centro dello slot.
È una spiegazione strutturale, non la prova dell'origine precisa dei 30 s osservati. Mancano gli
indici e i dettagli della produzione necessari per ricostruire la griglia effettiva per record.
Non traslare i tempi e non dedurre lacune da un confronto letterale con l'epoca dichiarata.

**Tempi fra strumenti.** Nel confronto già conservato, T_REC coincide ma 76/8949 archi univoci G5
hanno |ΔT_OBS| > 360 s. Il futuro piano può proporre un criterio sul tempo effettivo, dichiarandolo
informato da questo audit. Non cambia retroattivamente i grafi dell'inventario. Cfr.
[risultati della sovrapposizione](MDI_SMARP_OVERLAP_RESULTS.md).

## Blocco e attività indipendenti

La definizione dei filtri di qualità e l'attribuzione del rumore MDI per record restano bloccate
dalle fonti mancanti. Questo non impedisce la bozza descrittiva e le prove geometriche sintetiche.
Impedisce di presentare la bozza come pronta al congelamento o di avviare un campione già certificato
come scientificamente confrontabile. Nessuna nuova calibrazione o conclusione sul quenching.

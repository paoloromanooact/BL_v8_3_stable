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
| QUALITY MDI 0x200 | Tabella standard MDI: bit 9 = non in PRIME 60 | È un flag di modo operativo; non è una definizione di shutterless o, da solo, di dato inutilizzabile |
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

**QUALITY MDI 0x200: definizione ora verificata.** Il vecchio indirizzo lev182 senza `.html` restituisce
404, ma l'[indice ufficiale MDI](http://soi.stanford.edu/mdi/observables/) collega la
[scheda corretta lev182](http://soi.stanford.edu/mdi/observables/fd_m_96m_lev182.html) e la
[tabella magnetica](http://soi.stanford.edu/production/QUALITY/bits.fd_M.html).
Questa rinvia alla [tabella standard MDI](http://soi.stanford.edu/production/QUALITY/DATASWtable.html):
il bit 9 (0x200) indica che MDI non è in PRIME 60. Il bit 10 (0x400) segnala raggi cosmici; i bit 0–7
riguardano problemi di telemetria, dati mancanti o elaborazione, il bit 8 una anomalia di puntamento.
Non confondere questi significati con quelli HMI. Un valore composto come 0x600 contiene anche 0x400.
La pagina standard è storica (2003): per il bit alto, in particolare, va usata la semantica del prodotto
migrato lev182, che documenta i record senza immagine, non la sola nota legacy sullo stato PROBLEM.

L'acquisizione diretta HTTP delle pagine corrette è riuscita il 18 novembre (solo documentazione pubblica,
nessuna query a serie). Nessun redirect è stato seguito automaticamente: gli URL indicati sullo stesso
server sono stati letti separatamente con limiti di 25 s e 2 MiB per richiesta. Il precedente blocco del
lettore web non dimostrava indisponibilità della documentazione. La nota iniziale del commit `4186079`
è superata da questa verifica. Corpi originali, intestazioni e SHA-256 sono conservati localmente.

**Continuo interpolato.** La [nota primaria JSOC](http://jsoc.stanford.edu/data/mdi/mdi-tarp/mdi-interp-ic/)
conferma l'uso di T_OBS come tempo effettivo, distinto da T_REC. Definisce anche flag specifici della serie
`mdi.fd_Ic_interp`: 0x10000 per il criterio di interpolazione oltre 18 h, 0x20000/0x40000 per il segmento
segnaposto/triviale oltre 36 h. Questi bit non diventano automaticamente i bit QUALITY del magnetogramma
SMARP: occorre tracciare le effettive sorgenti e propagazioni. Nessun filtro su questa serie viene applicato.

**Prodotto 1/5 minuti.** La classificazione registrata resta esattamente 60/300 secondi di INTERVAL. La scheda primaria
lev182 descrive osservazioni da 30 s, singole o mediate su cinque campioni consecutivi a cadenza di
un minuto: questo chiarisce che cadenza e integrazione non coincidono, ma non modifica la regola
già eseguita né assegna automaticamente una RMS ai record con INTERVAL=30.
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

Il significato nativo del bit dominante è risolto. La nuova bozza propone esplicitamente di ammettere
QUALITY MDI pari a 0 oppure 0x200, con flag di modo conservato, ed escludere gli altri valori; HMI resta
QUALITY=0 per il piccolo campione. È una proposta operativa non congelata, non una certificazione di
qualità o di equivalenza fra modi. Non è stata applicata all'inventario o a un campione.
Restano aperti sorgente per-record, revisione produttiva e rumore di integrazione. La bozza e i nuclei
sintetici sono preparati; servono revisione esterna e autorizzazione separata prima del congelamento.
Nessuna calibrazione o nuova conclusione sul quenching.

## Conservazione delle fonti e dei controlli

Corpi e intestazioni HTTP, copie del codice primario, ricevuta della preparazione e log dei test
restano locali in `data/sharp/metadata_inventory_mdi/documentation_20261118/`, esclusi da Git.
Ricevuta HTTP SHA-256: `c61b4efb7158589e6da057ee76be75f933266bda3d586630e0fee3e3987f037c`.
Registro dell’inventario byte-identico prima/dopo questa conservazione: SHA-256 `b2b6643784843816eef9411ed1584c90f501706a5d93c9a5a0b79f5cc376f933`.

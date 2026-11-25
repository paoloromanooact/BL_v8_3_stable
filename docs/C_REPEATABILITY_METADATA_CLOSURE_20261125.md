# Ripetibilita C — chiusura della fattibilita dai metadati (Codex, 25 novembre 2026)

Obiettivo: preparare la scala delle differenze osservate per il confronto della sorgente BL/trasporto.
Segue C rev.3, non congelata. Nessun FITS aperto, array magnetico letto, nuova misura di tilt/flusso o rete.
USFLUX e un valore **gia contenuto nei metadati** SHARP, non il flusso della finestra C misurato ora.

## Risultato preliminare

| Quantita | Numero |
|---|---:|
| Bacino osservativo protetto | 1020 intervalli |
| Coppie locali entro 7200 s di T_OBS | 296 |
| Nodi del grafo complessivo | 1316 |
| Archi (HARP, famiglia o intervallo+bbox) | 98 |
| Coppie in componenti connesse al bacino protetto | 33 |
| Coppie valutabili con i soli filtri di metadati proposti | **82** |
| HARP distinte | 80 |
| Componenti che contengono le 82 coppie | 79 |
| USFLUX iniziale finito e positivo | 82/82 |
| OBS_VR disponibile nei keys locali | 0/82 |
| Lag nella classe (0;1,5 h] / (1,5;2 h] | 39 / 43 |

Le precedenti 86 coppie di riserva diventano 82 per il limite **gia proposto** |LON_FWT|<=60 ai due istanti:
HARP 1705, 2130, 4718 e 6002. Non sono esclusioni basate su differenze magnetiche.
La verifica usa componenti connesse, non solo esclusioni dirette contro il bacino. Mantiene i collegamenti
anche attraverso coppie non valutabili geometricamente: e una precauzione dichiarata della bozza.
79 componenti non sono una dimostrazione di indipendenza completa: famiglie candidate e associazioni non
ricostruite restano limiti. Non e stata eseguita alcuna identificazione di nests.

## Flusso e copertura

I terzili provvisori USFLUX sono calcolabili senza nuovi pixel:
- primo confine 4,907442e21 Mx;
- secondo confine circa 1,38655e22 Mx;
- classi 28 / 26 / 28 coppie, senza dividere i valori uguali per riempire le classi.

Il codice usa quantili con interpolazione lineare (pandas). Rendere esplicita questa convenzione nel testo
prima del congelamento; non riutilizzare i confini dopo eventuali cambi della popolazione senza registrarlo.
Si tratta di metadati della regione SHARP, non della misura del campo grezzo sul dominio comune C_fin.

Anni: 2010 6, 2011 21, 2012 6, 2013 18, 2014 11, 2015 12, 2016 6, 2017 1, 2022 1 coppie.
La copertura resta concentrata nella prima parte di HMI: non trasferire automaticamente la distribuzione
di differenze a tutta l'era o al campione osservativo. OBS_VR mancante viene segnalato, non ricostruito da T_OBS.

## Metodo, provenienza e controlli

`scripts/sft_c_metadata_closure.py`:
- verifica gli SHA dei prodotti dell'audit 78cffda e del catalogo P1;
- carica dal catalogo solo identita, ruoli, validita e famiglia; dei keys.json legge e conserva in memoria
  solo la lista esplicita di keyword di geometria/tempo/qualita e USFLUX/OBS_VR;
- rilegge i keys nominati dall'audit verificandone gli SHA; niente scansione libera per scegliere altri file;
- tempi TAI con aritmetica intera dei nanosecondi, secondi=60 come riporto: 7200 e 7201 non si confondono con
  gli arrotondamenti binari di astropy. Nessuna conversione UTC e nessun allargamento della finestra;
- ricostruisce il bacino 1-4,5 giorni dai metadati e il grafo con HARP, famiglia e sovrapposizione temporale/bbox
  periodica. Le bounding box del bacino usano le shape inferite da CRPIX, come l'audit iniziale;
- riusa l'area geometrica e il controllo shape gia conservati nell'audit. Non ricalcola C_geo dai pixel,
  non valuta valori finiti, C_fin o C_rot. Il runner vero deve verificarli con gli header effettivi;
- produce CANDIDATES, NODES, EDGES, SUMMARY, SELFTEST e META con impronte degli input realmente consultati.

Selftest **10/10**: secondi frazionari, 7200/7201, riporto 60, collegamento transitivo, periodicita della bbox,
qualita mancante mai interpretata come zero.

`scripts/sft_c_metadata_graph_check.py` ricostruisce gli archi dalle tabelle e la separazione/partizione con
una visita breadth-first, senza importare l'audit o il suo union-find: **8/8**. Verifica inoltre hash dei prodotti,
conteggi, terzili e lag. E un controllo indipendente delle tabelle del grafo, **non** un secondo lettore WCS
ne un riconteggio delle misure FITS. Non emette una ricevuta scientifica completa.

Prodotti in `reviews/C_REPEATABILITY_METADATA_CLOSURE_20261125/AUDIT/`; controllo del grafo separato in
`reviews/C_REPEATABILITY_METADATA_CLOSURE_20261125/GRAPH_CHECK.json`.
Il primo output in /tmp e stato seguito da una seconda copia identica nei conteggi dopo aver reso portabile
il percorso di default dello script. Nessun cambiamento di regola o scelta dei dati; la versione conservata
registra lo SHA del codice finale. Entrambe erano sole verifiche di metadati, non corse scientifiche.

## Che cosa resta

82 e la disponibilita provvisoria, **non la numerosita finale** e non una stima di sigma. Prima dei pixel:
1. revisione/congelamento della specifica C, incluse convenzioni dei quantili e dipendenze geometriche;
2. controllo dell'elenco effettivo dei semi e legami con gli input del pilota osservativo;
3. runner e riconteggio sintetici per preparazione delle mappe, misure e statistiche;
4. poi misura conservata e ricontata: la copertura finita puo ridurre ancora il campione.

C resta in parallelo a BQ, senza bloccare la sua specifica. Nests sospesi e SINDy separato.

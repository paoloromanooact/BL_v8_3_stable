# Audit MWO — 18 novembre, ripreso il 20 novembre 2026

Revisione di Codex, senza misura del catalogo lungo e senza nuovi tilt reali. Le verifiche usano l'inventario
salvato degli header, i gDPD e i prodotti già conservati del pilota. Non cambiano il protocollo congelato,
le soglie o la scala dei campi. Il progetto del flusso polare e SINDy resta separato.

## Calibrazione fisica e versione dell'archivio

Ulrich et al. (2002, §§1–4) distinguono la correzione della saturazione dalla regolazione dello zero magnetico.
La prima entra in alcuni prodotti; i risultati di quel lavoro, salvo il dipolo globale, non la incorporano.
La correzione dello zero descritta nel lavoro era stata applicata dal 1996 e non ancora alla serie precedente.
La data pubblicata per il nuovo sistema a 24 canali è solo il 1996. Queste indicazioni non certificano le correzioni
presenti nei nostri file nativi. [Fonte primaria, testo completo](https://www.predsci.com/~pete/research/magnetogram-workshops/1st-workshop/papers/ulrich02a.pdf).

Ulrich et al. (2009) propongono per i campi sinottici MWO il fattore 4,15 − 2,82 sin²ρ, dipendente dalla distanza
angolare dal centro del disco e dal confronto fra campionamenti spettrali. Non è una conversione universale di
ogni prodotto MWO. La formula qui viene registrata come informazione documentale e non viene applicata.
[Studio della risposta delle righe spettrali](https://arxiv.org/pdf/0812.2294).

La pubblicazione di rilascio del 2024 descrive file interpolati a 256 × 256 pixel e riportati alle 20 UT mediante
rotazione differenziale. I 30 938 header Fe I del nostro archivio 1974–2012 descrivono invece immagini 512 × 512,
con TAVG-UT variabile. Quindi la descrizione di quel rilascio non identifica da sola il trattamento dei nostri
file. La stessa pubblicazione documenta aumenti della cadenza e modifiche strumentali, non una prova di omogeneità
invariante nel tempo. [Ulrich, Boyden e Tran 2024](https://link.springer.com/article/10.1007/s11207-024-02390-z).

Il lettore congelato locale applica BSCALE e BZERO dopo la conversione in float32. Non contiene una correzione
esplicita della saturazione. Questo descrive il lettore, non la riduzione fatta a monte. BUNIT è gauss;
BSCALE vale 0,1 o 0,05 e BZERO è zero. GV è documentato come fattore di Landé, ICHK come indicatore del rapporto
di intensità, PSEPMA come separazione delle porte. Nessuno di questi campi prova che la saturazione sia corretta.
GV vale 0,03 in 18 file, contro 3 negli altri 30 920. L'anomalia resta registrata, senza riscalature automatiche.

Resta aperta la provenienza delle correzioni di saturazione e dello zero nel prodotto nativo. Non si può
aggiungere un fattore dalla letteratura senza escludere una doppia correzione. Un fattore uniforme positivo
lascia invariati i centroidi solo se l'insieme dei pixel selezionati rimane fisso; soglie, fattori spaziali e pesi
fra regioni possono cambiare tilt e pendenza. I controlli S1–S2 restano relativi a DPD e non certificano questa
calibrazione assoluta. La misura descrittiva congelata può documentare il limite; un trattamento nuovo richiede
un emendamento prima dell'uso.

## Capacità dei metadati prima dei controlli di effemeridi e della misura

Riproduzione in sola lettura con `scripts/t3_mwo_metadata_audit.py --out /tmp/t3_mwo_metadata_audit.json`.
Verificati gli hash di HEADERS.csv.gz e BY_YEAR.csv contro META.json e i 41 file DPD usati contro il manifesto
locale. SHA-256 dell'inventario degli header `65a14b8674575713cfe293846a2119a0e898d4881549448b0430afd1ab7f7467`.
Il programma non importa il runner e non apre pixel magnetici.

Sono letti 96 161 record gDPD, inclusi 75 con secondi uguali a 60; 3623 righe intermittenti restano fuori.
Fra i giorni con area ≥ 1 e |latitudine| ≤ 45°, 35 410 non hanno una scansione Fe I nell'inventario salvato.
Restano 56 557 giorni candidati, dei quali 50 621 isolati. Per questi conteggi soltanto, ogni gruppo è
rappresentato dal primo giorno in ordine di |LCM|, senza provare la misura magnetica.

| Ciclo | Gruppi isolati Nord | Gruppi isolati Sud |
|---|---:|---:|
| 20 | 249 | 323 |
| 21 | 1523 | 1698 |
| 22 | 1786 | 2047 |
| 23 | 1829 | 2112 |
| 24 | 591 | 427 |

Sono 12 585 gruppi isolati potenziali in 450 CR; senza isolamento, 13 266. Non sono il campione definitivo né
un aggiornamento dei conteggi congelati 8802/7704. Qui manca il filtro di effemeridi e l'isolamento si applica
ai giorni prima della scelta. L'inventario salvato non comprende CENLON e B0 necessari per il filtro. Il runner
completo dovrà riconciliare i denominatori attraverso MAGNETOGRAMS, ATTEMPTS e LOSSES. Nessuna copertura minima
è dichiarata superata da questi conteggi.

| Epoca | Nord | Sud |
|---|---:|---:|
| E1 | 66 | 118 |
| E2 | 1023 | 931 |
| E3 | 582 | 871 |
| E4 | 504 | 501 |
| E5 | 1192 | 1429 |
| E6 | 112 | 155 |
| E7 | 63 | 50 |
| E8 | 2436 | 2552 |

E1 e soprattutto E7 sono fragili rispetto alla soglia di verificabilità di 50 record per emisfero. Le
esclusioni di effemeridi, geometria e misura possono renderle non verificabili. Le classi di risoluzione
potenziali fra gli isolati sono R1 11 195, R2 997, R3 322, R0 71. L'alta frazione di R1 deriva dalla scelta
prioritaria della classe fine, anche quando le scansioni R2 sono più numerose. Resta da misurare la perdita
per attività e per classe dopo la selezione effettiva.

## Correzione necessaria del giorno UTC

TAVG-UT supera o raggiunge 24 ore in 2797 header, fino a 32,58 ore. Il nome del file identifica il giorno della
sessione osservativa, mentre l'istante è quel giorno più TAVG-UT. Runner e riconteggio calcolavano correttamente
l'istante ma raggruppavano le scansioni con il giorno del nome. Questo violava la regola congelata dello stesso
giorno UTC. Ora la chiave è la data dell'istante completo; `filename_day` resta nel registro del runner.
Due prove con FITS sintetici falliscono sul codice precedente e passano sul corretto.

Il problema tocca anche tre abbinamenti del pilota già conservato, diagnosticati leggendo soltanto i tempi
nel suo ROWS.csv. Nessun risultato storico è sostituito.

| HARP | Giorno UTC del riferimento P1 | Istante UTC MWO |
|---|---|---|
| 421 | 2011-03-17 | 2011-03-18 00:22:22,8 |
| 495 | 2011-04-13 | 2011-04-14 00:16:51,6 |
| 1527 | 2012-04-05 | 2012-04-06 00:29:16,8 |

Il pilota non può quindi essere descritto come interamente composto da abbinamenti nello stesso giorno UTC.
La sua regola numerica resta quella storicamente applicata; non è dimostrato se correggere questi tre
abbinamenti ne cambierebbe l'esito. Il catalogo lungo deve usare la chiave UTC corretta.

Due header hanno TAVG-UT = −32,768 (`1978/MP00_5250MWO_00_0781226_3234.fits` e
`1984/MP00_5250078_00_0840621_3513.fits`). La ricostruzione del tempo resta dubbia; nessuna correzione del nome
o dell'orario viene inventata. Devono comparire fra i controlli di effemeridi e le cause di esclusione.

## Catalogo misurato durante l'interruzione della revisione

Al rientro del 20 novembre il catalogo è già conservato in `f718114`, con rapporto e riconteggio in
`dad6f6b`. Il file DESIGN.csv contiene 5229 record isolati e 5941 nell'insieme completo. Confrontando
solo day e la data UTC di obs_time, risultano 32 discordanti negli isolati e 30 nell'insieme completo.
Il riconteggio 12/12 riproduceva lo stesso errore di raggruppamento del runner e non lo rilevava.

La corsa e la ricevuta storiche restano immutate. Prima dell'analisi statistica occorre rigenerare
la selezione e la misura con il raggruppamento UTC corretto, in una destinazione nuova e con i tilt
ancora sigillati. I conteggi di copertura della corsa precedente non certificano la selezione corretta.
Questo audit non rilancia la misura e non legge SEALED.csv.gz.

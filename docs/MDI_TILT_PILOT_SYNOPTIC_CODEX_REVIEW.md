# Pilota MDI — integrazione sulle sinottiche disponibili, 23 novembre 2026

Oggetto: inventario corretto 2d46931, proposta (c) sinottiche + (a) full-disk.
Il parere df999fc resta valido per il full-disk; questa integrazione distingue il nuovo prodotto sinottico.

## Verifica locale effettuata

Elencati in sola lettura 193 file mdi.synoptic_mr_polfil_96m.<CR>.Br_polfil.fits nella cartella indicata
nell'inventario; intervallo 1909–2104, mancanti esattamente 1938, 1939, 1940.
Nessun array di campo letto né tilt misurato. Nell'header del primo file (CR 1909), HDU 1:
- NAXIS1/2 = 3600/1440; BUNIT = Mx/cm^2; CONTENT = Carrington Synoptic Chart Of Mr Field;
- CTYPE1/2 = CRLN-CEA / CRLT-CEA; CUNIT2 = Sine Latitude;
- CDELT1 = -0.1; CDELT2 = 0.001388888888888889; CRPIX1/2 = 1800 / 720.5;
- CRVAL1 = 687060 (longitudine Carrington estesa), CRVAL2 = 0;
- T_START/T_STOP in TAI, HISTORY indica una correzione Carrington-Time del 2013.
Non sono ancora verificati tutti gli header, la provenienza completa, gli hash, la copertura pixel di CR1937,
il dominio del polar filling o la ricetta esatta di costruzione della specifica serie locale.

## Giudizio sul metodo

Le sinottiche non sono inutilizzabili per definizione per lo studio di regioni attive. Approvo che entrino
nella bozza come prodotto distinto da valutare. Non approvo l'assunzione che vicinanza di MWO al meridiano
implichi uno scarto piccolo, né il trasferimento delle proprietà del rumore dal full-disk alla sinottica.

Il disegno in due livelli è sensato se il confronto sinottica/full-disk è parte del pilota iniziale e viene
valutato prima di adottare le sinottiche per il catalogo operativo o il calcolo prospettico di T3. È possibile
iniziare con controlli locali e prove sintetiche senza aspettare la rete; non misurare subito tutte le regioni
1996–2010 prima di fissare regole e criteri del pilota.

## Vincoli per la bozza

1. **Provenienza esatta.** Registrare hash dei file, serie/segmento/revisione, header, lacune e riempimenti.
   Il prodotto è Br_polfil: verificare quali latitudini siano modificate dal riempimento e che le finestre
   scientifiche usino dati osservati. Non adottare una ricetta temporale di un'altra serie MDI per analogia.

2. **Adattatore sinottico proprio.** Il campo è già radiale: non dividerlo ancora per mu. Sulla griglia
   uniforme in longitudine e sin(latitudine), l'area è R_sun^2 * |Delta longitudine in radianti| * |Delta sinlat|,
   non l'area proiettata divisa per mu di MWO/full-disk. Centroidi pesati con |Br| per area di superficie.
   Leggere segno degli assi, origine FITS, longitudine estesa/modulo 360 e sinlat dagli header; non trattare
   l'asse verticale come latitudine in gradi. Prove sintetiche con bipolo noto, asse longitudinale invertito,
   flusso uniforme e bordo della mappa. Un numero maggiore di pixel rimappati non equivale a migliore risoluzione.

3. **Identità e tempi dei gruppi.** Fissare passaggio al meridiano della regione, giorno/posizione DPD e
   associazione con la rotazione corretta; non basta la longitudine modulo 360. Le colonne della sinottica
   provengono da tempi diversi e le polarità possono avere tempi effettivi differenti. Vicino al taglio
   0/360 non unire semplicemente le due estremità della stessa mappa: possono appartenere a passaggi separati
   da una rotazione. Stabilire uso delle mappe adiacenti o esclusione motivata delle finestre al bordo.
   Una regione non diventa più osservazioni indipendenti scegliendo più righe giornaliere DPD.

4. **Confronto full-disk nello stesso pilota.** Sottoinsieme fissato per attività, emisfero, area/geometria,
   includendo le condizioni più difficili, senza selezione sui tilt o sull'accordo. Fissare il tempo di
   riferimento alla ricetta della sinottica, confrontare con una o più immagini MDI a tempi documentati,
   e dichiarare risoluzione, soglie e modalità di esposizione. Il confronto quantifica una differenza fra
   prodotti che include composizione temporale, rimappatura, risoluzione e misura; non isola automaticamente
   la sola media temporale. I file 2010–2011 già disponibili non sostituiscono il controllo sul ciclo 23.
   Una piccola differenza media non basta a controllare dipendenze da attività/dimensione.

5. **Confronto MWO separato.** Stesso gruppo non significa stessa misura temporale. Registrare scarto
   temporale dal passaggio e dal riferimento DPD/MWO; la media |LCM| di 7 gradi non è un limite massimo e non
   dimostra che l'evoluzione sia trascurabile. È un confronto relativo con una componente di composizione
   temporale ulteriore; nessun riferimento corretto per definizione e nessuna calibrazione trasferita.

6. **Resa, rumore e correlazione.** Le sinottiche permettono di studiare disponibilità, resa della misura
   sinottica e distribuzione dei risultati. Un composito per CR non separa rumore strumentale, evoluzione,
   interpolazione e variazione fisica tra regioni. Non promettere di stimare separatamente queste componenti
   o di ricavarne direttamente la precisione del futuro catalogo full-disk. Il disegno prospettico deve
   dichiarare se riguarda tilt sinottici o istantanei, e usare sensibilità per componenti non identificate.

7. **Campione e scelte.** Restano validi i due obiettivi campionari del parere precedente: copertura MDI da
   DPD indipendente da MWO e sottoinsieme abbinato. Fissare soglie per il prodotto sinottico senza importare
   automaticamente 100 G, rumore, pixel minimi o pesi validi per un'immagine nativa. L'eventuale T3 ha
   stimando, matrice, effetto proiettato e validazione propri; non riaprire i risultati HMI/MWO precedenti.

## Fonti e precedente utile

- Getachew, Virtanen & Mursula 2019, ApJ 874:116, §4:
  https://cc.oulu.fi/~kmursula/publications/Getachew_ApJ_2019.pdf
  Descrive le sinottiche MDI allora analizzate (3600x1080, non la serie polfil locale 3600x1440) come composti
  di misure vicine al meridiano, con media di circa 20 immagini e larghezza temporale di circa un giorno.
  È una motivazione del controllo temporale, non la prova della ricetta esatta dei file locali.
- Sun 2018, Polar Field Correction for HMI Line-of-Sight Synoptic Data:
  https://arxiv.org/abs/1801.04265
  Riferimento al trattamento polare; verificare applicabilità/versione della serie MDI utilizzata.
- Database e codice originali di Wang, Jiang & Luo (ARISE):
  https://github.com/Wang-Ruihui/A-live-homogeneous-database-of-solar-active-regions
  README consultato: cataloghi con e senza regioni ricorrenti, coordinate dei centroidi per polarità e
  parametri magnetici da mdi.synoptic_Mr_96m / HMI. Precedenti: ApJS 268:55 (2023),
  https://doi.org/10.3847/1538-4365/acef1b e ApJ 971:110 (2024), https://doi.org/10.3847/1538-4357/ad5b5f.
  Valutarne documentazione e disponibilità dei parametri prima di duplicare lavoro; popolazione e metodo
  non sono automaticamente quelli DPD. Nessuna tabella scaricata o usata per selezionare il pilota qui.

Ricerca documentale web effettuata; le pagine SOI/JSOC direttamente tentate non erano accessibili con il
lettore web. Nessuna acquisizione di nuovi magnetogrammi o query scientifica JSOC eseguita.

## Passo successivo

Claude può scrivere la bozza del pilota in due livelli con questi vincoli. Primo passo operativo locale:
inventario completo degli header/provenienza e test dell'adattatore; misure solo dopo protocollo e codice
rivisti. Il sottocampione full-disk deve precedere la decisione sul metodo del catalogo, non essere rinviato
a dopo la sua elaborazione completa. Nessuna equivalenza con i tilt istantanei è assunta.

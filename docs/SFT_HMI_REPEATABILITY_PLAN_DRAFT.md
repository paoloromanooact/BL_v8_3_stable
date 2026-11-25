# HMI: ripetibilità a breve intervallo per il confronto SFT — specifica rev. 2, BOZZA

25 novembre 2026, Codex. **Da rivedere e congelare prima delle misure sui pixel.**
Sostituisce la proposta generale di 78cffda; non modifica protocolli congelati. Collegata al §7 della bozza
`PROTOCOL_SFT_OBSERVED_EVOLUTION_DRAFT.md` e al piano C/BT. Obiettivo: sorgente BL, incertezza osservativa e confronto
con l'evoluzione. Nests in pausa su richiesta dell'utente; nessuna identificazione di nests fa parte di C.

## 0. Informazione gia vista e risultato cercato

Sono noti P1/P1d e i risultati BL/quenching precedenti. L'audit Codex 78cffda ha letto solo metadati/header:
299 coppie nominali, 296 effettive entro due ore, 86 coppie/84 HARP nella riserva geometrica con esclusioni dirette
conservative. Questi conteggi non sono una selezione definitiva. Nessuna differenza magnetica di C e stata letta.

Stimiamo una **distribuzione di differenze osservate a breve intervallo**, non il rumore strumentale puro.
Se X_j = f_j + e_j, allora Var(X_1-X_0) comprende evoluzione, varianze e covarianze degli errori. Non dividere
automaticamente per sqrt(2), non dichiarare un limite superiore all'errore singolo e non generalizzare la scala
misurata a tutte le regioni o a intervalli di giorni senza verifiche.

## 1. Input e provenienza

Vincolare al congelamento gli SHA di:

- audit `reviews/SFT_HMI_REPEATABILITY_METADATA_20261125/` (insieme esatto di PAIRS, HEADERS, KEYWORDS, META, SELFTEST);
- catalogo P1, limitando il caricamento preliminare a identita, T_REC, ruolo, validita, famiglia e rango;
- bozza osservativa e codice/metodo geometrico adottato, dipendenze P1 per lettura/WCS e misura;
- manifesto del disegno di C, script e riconteggio approvati, ambiente e versioni scientifiche.

I Br/bitmap/keys sono quelli nominati da HEADERS, non file trovati per somiglianza. Prima dei pixel si registra
lo SHA completo dei loro byte, senza calcolare misure. Copie discordanti o input cambiati fermano la catena:
nessuna precedenza implicita fra versioni diverse. T_OBS esplicito TAI, secondi frazionari conservati; una
conversione in UTC, se esportata, usa astropy e non una sottrazione fissa. Nessun download.

## 2. Popolazione e selezione deterministica proposta

1. Tutte le coppie consecutive locali della stessa HARP con 0 < Delta T_OBS <= 7200 s, come nell'audit;
   conservare anche le tre coppie nominali da 7201 s fra le escluse. Nessuna tolleranza fisica che allarghi le 2 h.
2. Br/bitmap con shape coerenti, WCS e tempi interpretabili; QUALITY di entrambi in {0,128}, come P1/P1b.
   Sensibilita: sole coppie con entrambi QUALITY 0. Nessun nuovo significato attribuito al bit 128.
3. Entrambi i record entro |LON_FWT| <= 60 gradi, soglia di visibilita gia usata per il controllo P1; non e un
   limite mu per ricostruire Br, che e gia radiale. Posizione al meridiano e latitudine sempre riportate.
4. Area geometrica C >= 25 deg² con lo stesso metodo del pilota osservativo; copertura finita verificata dopo.
5. Escludere i collegamenti con **tutto il bacino osservativo** primario-controllo su T_OBS (1020 HARP nell'audit,
   prima della sua selezione geometrica), non soltanto le HARP poi estratte. Definire prima il grafo del §3.
6. Usare tutte le coppie rimanenti, nessun campionamento casuale e nessuna sostituzione in caso di fallimento.
   Manifesto e esclusioni conservati prima della misura. I nuovi conteggi di fattibilita sono metadati, dichiarati
   gia noti al congelamento; 86 e un precedente conteggio di riserva, non una numerosita garantita.

Questa e una popolazione di ripetibilita osservabile: non un campione rappresentativo dell'intera era HMI o
di tutte le emersioni. Le associazioni NOAA non sono una chiave fisica uno-a-uno e non filtrano la selezione.

## 3. Dipendenze e separazione dalla verifica

Nodi: coppie ravvicinate e intervalli primario-controllo del bacino osservativo. Arco se si condivide una HARP,
una famiglia P1e nota, un record, oppure se gli intervalli temporali si intersecano **e** le bounding box WCS
iniziali si intersecano sullo stesso ramo di longitudine (periodicita 360 gradi). Usare componenti connesse:
nessuna coppia di C in una componente contenente un nodo del bacino osservativo e ammessa. La bounding box e
un controllo conservativo, non una prova di identita; registrare tipo di arco ed esclusione.

Fra le coppie di C rimaste, le componenti definiscono i gruppi di riepilogo e ricampionamento. La famiglia P1e
resta candidata e non certifica identita fisica. Non cercare nuovi nests: la dipendenza non ricostruita rimane
un limite, con sensibilita temporale del §6. Prima dell'uso BT ricontrollare i legami col campione SFT effettivo
conservato: nessuna unita di calibrazione compare nella verifica.

## 4. Preparazione delle mappe e dominio fisso

- Principale: tutti i pixel Br finiti con |Br| <= 10000 G, senza soglia, bitmap o bilanciamento, come il principale
  del pilota osservativo. Varianti distinte: maschera P1 bitmap >=33 e |Br| >=100 G; campo bilanciato con riscalatura
  separata delle due polarita, se entrambe presenti. Non riempire buchi con zeri scambiandoli per osservazioni.
- Griglia a 0,06 gradi, ramo del primo CRVAL1. Estremi inferiori = minimo dei centri WCS di entrambe le patch meno
  1 grado; celle sino a coprire il massimo piu 1 grado, arrotondamento per eccesso. Aree sferiche esatte.
- C_geo = erode(P0) intersezione P1, con le impronte dai centri WCS, margini direzionali del pilota alla massima
  diffusione/velocita della sua griglia (466,8 km²/s, Du=0,041 km/s, p=2,33), Delta T_OBS reale e arrotondamento
  per eccesso del margine in celle. Questa regola e geometrica: non si evolve il campo per la misura principale.
- C_fin aggiunge il requisito di copertura valida a entrambi gli istanti. Una cella con centri di pixel non finiti
  o sopra il cap non e valida; descrivere nei prodotti la copertura geometrica e quella finita. Usare lo stesso
  C_fin per entrambe le mappe e le loro varianti. Area finale <25 deg²: `finite_coverage_insufficient`.
- Deposito conservativo del flusso con pesi lineari in longitudine e sin(latitudine), stessa operazione ai due
  istanti; conservazione del flusso e dipolo sul supporto completo. Fuori dal supporto dei centri: stato esplicito,
  nessun clipping. Registrare variazioni di flusso per polarita e centroidi dovute alla rimappatura, che puo
  cancellare polarita entro una cella. Non correggerle riscalando gli esiti.
- Sensibilita numerica su tutte le coppie valutabili: griglia 0,03 gradi e confronto sullo stesso supporto fisico
  costituito dalle celle fini figlie di C_fin. Nessuna nuova selezione piu favorevole a griglia fine. Prima dei
  dati fissare nei test l'errore di preparazione rispetto alle scale del §5; non presentarlo come rumore solare.

## 5. Osservabili e differenze

Per ogni istante sullo stesso C_fin: D_C geografico in G, Phi+, Phi-, netto e unsigned in Mx, centroidi vettoriali
in gradi, separazione, tilt P1, latitudine media. Nessuna convenzione di Hale modifica D_C.
Delta X = X(t1)-X(t0); tilt con differenza assiale, longitudini circolari; riportare separatamente il cambio di
polarita leading. Una sola polarita rende tilt/separazione non definiti; i flussi e D restano riportati.

Conservare unita fisiche e scale relative esplicite:

- S_D = 3 Phi_unsigned(t0)/(8 pi R²), e Delta D_C/S_D se S_D>0; non dividere per D(t0), che puo essere quasi nullo.
- Flussi: differenze assolute, normalizzazione all'unsigned iniziale se positivo, log-rapporti per polarita solo
  se entrambi i flussi positivi. Nessun epsilon e nessuna imputazione di un dato assente con zero.
- Angoli: statistiche assiali/circolari, non una gaussiana ordinaria applicata senza controllo vicino al taglio.

La differenza osservata principale non sottrae una previsione SFT. Eventuali differenze dopo sola rotazione
sono un prodotto supplementare separato, sotto specifica esplicita e con gli stessi dati/supporti.

## 6. Riepiloghi e incertezza

Tutti i selezionati restano nei denominatori; rendere cause multiple, causa principale e stati per variante.
Nessuna esclusione per differenze grandi. Per ogni quantita dare n coppie, HARP, famiglie/componenti e CR.

Principale: scegliere idealmente una componente a caso e poi una sua coppia, cioe peso per coppia
1/(K n_componente). Riportare media, mediana, quantili 10/90%, RMS centrata e mediana del modulo delle differenze.
Per dati lineari RMS = sqrt(sum w_i(Delta_i-media_w)^2), descrittiva, senza chiamarla stima non distorta di sigma.
MAD scalata 1,4826 come misura robusta dichiarata, non automaticamente sigma strumentale. A fianco statistiche
non pesate delle coppie, cosi l'effetto dei record ripetuti e visibile.

Per gli angoli usare risultante circolare di exp(i Delta) o exp(2i Delta) per l'assiale, media circolare e
concentrazione; risultante nulla => dispersione circolare non definita. Riportare quantili dei moduli delle
distanze da zero, non quantili ordinari degli angoli firmati al taglio. Non costruire intervalli percentile
lineari per la media circolare: in questa versione se ne riporta solo il valore e la risultante. Le differenze vicino al taglio e i cambi
di leading restano visibili, non vengono ritagliati per costruire una sigma piccola.

Riepiloghi fissati: totale, due emisferi, Delta t in (0;1,5 h] e (1,5;2 h]; flusso, latitudine e distanza dal
meridiano riportati per coppia come covariate, senza altri tagli scelti dopo la lettura. Distribuzione per anno
e popolazione coperta sempre mostrate. Sensibilita QUALITY solo 0 e variante P1/bilanciata separate.

Intervalli descrittivi percentile 95% con 2000 repliche: ricampionare le K componenti con reinserimento, tenendo
tutte le coppie di ogni estrazione e pesandole coerentemente. Seme proposto 36_300_001 nella zona 36_300_000–999:
verificare l'assenza di collisioni nell'elenco effettivo prima del congelamento. Con meno di 10 componenti,
riportare soli conteggi/statistiche senza intervallo bootstrap, soglia operativa dichiarata. Sensibilita:
ricampionamento di blocchi temporali non sovrapposti di 6 CR; una componente resta intera nel blocco della sua
prima CR. Intervalli nominali, senza copertura validata; nessuna prova che i gruppi siano del tutto indipendenti.

## 7. Collegamento alla likelihood BT/BQ

C fornisce una scala empirica della differenza a circa 1–2 h. Non identifica separatamente rumore dei due
record, loro correlazione ed evoluzione: niente divisione automatica per sqrt(2), niente estrapolazione lineare
ai giorni e niente sostituzione della discrepanza del modello con questa scala.

Il protocollo bayesiano successivo deve definire quali osservabili usa e come la loro dipendenza entra nella
likelihood. Deve considerare errori della mappa iniziale oltre che del controllo, variabilita intrinseca e
processi non modellati. Se adotta una conversione da C, riportarla come assunzione con sensibilita (per esempio
scale 0,5/1/2 rispetto al riferimento esplicitamente definito), non come errore strumentale misurato. Nessuna
somma in quadratura senza dichiarare ipotesi di indipendenza e covarianze.

BQ non e bloccato scientificamente da C e non riceve automaticamente la stessa scala: per il quenching restano
dispersione dei tilt e dipendenza fra CR da stimare/controllare. La loro dominanza non e assunta in anticipo.
Nests restano sospesi; non entra in C o BQ una classificazione non ancora costruita.

## 8. Prodotti, prove e cancelli

1. Disegno e manifesto preliminari dai metadati; protocollo definitivo dopo revisione incrociata. Record di
   congelamento con SHA e disclosure, senza modificare il testo successivamente.
2. Runner e riconteggio indipendente su sintetici: stessa mappa, rotazione nota, errori noti indipendenti e
   correlati, campo nuovo, cambi di supporto, valori mancanti, una polarita, zero flusso, periodicita e angoli
   al taglio. Errori di input devono fermare prima delle misure; le fixture non producono ricevute complete.
3. Prova esatta sui sintetici: per coppie con errori generati di varianza sigma² e correlazione rho,
   Var(Delta)=2 sigma²(1-rho) quando non c'e evoluzione. Serve a verificare codice e interpretazione, non a
   imporre rho=0 ai dati. Nessun solutore SFT e necessario per il principale di C.
4. Corse reali su codice e input conservati: SELECTION/EXCLUSIONS, INPUT_MANIFEST, MEASUREMENTS, DIFFERENCES,
   COMPONENTS, SUMMARY, BOOTSTRAP e META, con colonne e chiavi esatte e hash all'inizio/fine. Destinazioni nuove,
   nessuna sovrascrittura dei prodotti precedenti; salvataggio prima della lettura.
5. Riconteggio da FITS con propria misura e regole di riepilogo; la dipendenza dal lettore/WCS P1, se condivisa,
   e dichiarata. Ricevuta completa legata al META e ai prodotti; nessuna lettura del rapporto di risultati prima
   della sua conservazione. Rifiutare righe extra/mancanti, conteggi non interi, hash obsoleti e esiti manomessi.
6. Rapporto con distribuzioni osservate, limiti di copertura e di trasferimento. Nessun test del quenching,
   ranking bayesiano o parametro fisico SFT stimato da questa sola corsa.

## 9. Per il controllo incrociato prima del congelamento

Confermare selezione completa del §2 e grafo del §3, definizione di C_fin e rimappatura del §4, scale e
riepiloghi del §5–6, elenco effettivo dei semi e schema dei prodotti. La bozza fissa proposte concrete;
non autorizza una misura mentre codice e protocollo sono ancora in revisione.

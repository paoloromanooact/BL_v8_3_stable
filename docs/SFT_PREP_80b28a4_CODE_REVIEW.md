# Revisione del codice SFT preparatorio b3f1745 / e317200 / 80b28a4

25 novembre 2026, Codex. Revisione limitata ai tre file e alle loro impronte
conservate in `docs/SFT_PREP_80b28a4_REVIEW_RESULTS.json`. Nessun FITS o pixel
osservato letto, nessun download e nessun pilota scientifico eseguito.
Le prove sotto usano impulsi, campi sintetici piccoli e algebra numerica.

**Esito: codice utile per lo sviluppo sintetico, non ancora approvato per
le corse osservate.** Le scelte fisiche gia concordate restano valide;
i risultati dei selftest non chiudono ancora gli aspetti numerici sotto.
La revisione dei protocolli `SFT_790cad1_FINAL_REVIEW.md` resta applicabile.

## 1. Cosa e confermato

Ho rieseguito le tre prove `p1_consistency()` di 80b28a4, senza eseguire le
intere suite piu costose: D del profilo bilanciato e D_bal P1 concordano
entro 1,5e-15 relativo; D locale e D P1 entro 1,9e-16; i flussi delle due
polarita coincidono nel caso specifico. Queste sono prove positive su una
patch CEA sintetica obliqua e sugli ingredienti effettivamente selezionati.

La formula geografica di D, le unita e la rotazione relativa a Carrington
sono coerenti con le scelte del protocollo. La conservazione del momento
del deposito in s e verificata per punti interni ai centri del reticolo.

La precisazione su tau e corretta: il fattore exp(-t/tau) e esatto per
l'equazione continua con decadimento uniforme. CN sul generatore con tau
non coincide esattamente con CN senza tau moltiplicato per l'esponenziale;
la convergenza al secondo ordine della differenza e un controllo legittimo.
Non imporre identita a precisione macchina fra i due algoritmi discreti.

Non ho rieseguito integralmente i 14/14 e 8/8 dell'autore; ho aggiunto
controlli mirati dei casi che quelle suite non coprono.

## 2. Priorita alta: positivita e metodo di avvezione

Controprove sugli operatori effettivi del codice, con una sola polarita
iniziale e massa iniziale normalizzata:

| Caso | Minimo dopo la tappa | Massa finale / iniziale |
|---|---:|---:|
| 1D sola diffusione, N400, 1 giorno | -0,27739 | 1 |
| 1D sola avvezione centrata, eta=0, 600 s | -0,000491 | 1 |
| 2D sola avvezione, blocco positivo, 600 s | -0,01192 | 1 |
| 2D sola diffusione, 59–61°, passo 0,06°, 600 s | -0,30454 | 1 |

Sono polarita numeriche artificiali, non cancellazione fra polarita
iniziali opposte. Il caso 1D eta=0 e un limite analitico della funzione,
non un parametro del pilota: mostra che lo stencil centrato non e
monotono in generale. Per la griglia fisica ammessa si puo verificare
esplicitamente il dominio in cui il generatore ha tassi fuori diagonale
non negativi; il solo sottopasso CN non corregge uno stencil che non li ha.

Per 2D il problema si presenta anche con i coefficienti fisici proposti.
In particolare non e sufficiente un dipolo o un flusso netto corretto
per certificare flussi unsigned, segni e centroidi. Il clipping a zero
usato nel test della rotazione nasconde eventuali valori negativi: il
controllo della positivita va fatto PRIMA e senza clipping riparatore.

Recepire e87fff7: scegliere integratore, sottopassi/CFL e ricostruzione
monotona dichiarati; nella seconda ordine 2D manca ancora il limitatore.
Aggiungere impulsi, fronti netti e gaussiane non negative, alle risoluzioni
e ai parametri estremi, con controllo di massa e positivita separati.
Il solo D(3 anni) convergente non basta. Il codice 1D e attualmente
centrato in avvezione: non chiamarlo upwind senza cambiarne lo stencil.

## 3. Deposito: D e flusso netto esatti, unsigned e centroidi no

La frase «le due catene partono esattamente dalle grandezze del catalogo»
va limitata alle identita dimostrate e a quella patch sintetica.

Controesempio con due pixel distanti 0,03° (passo HMI), flussi +1 e -1,
e griglia locale a 0,06°:
- Phi_pos e Phi_neg dei pixel = 1 e 1;
- Phi_pos e Phi_neg del campo depositato = circa 0,5 e 0,5;
- D depositato / D dei pixel = 1 entro arrotondamento;
- centroide positivo: -0,015° nei pixel, circa -0,030° sulla griglia.

Non e necessariamente un errore di implementazione: sommando flussi
firmati nelle stesse celle si perde flusso unsigned per coarsening.
Preservare F e F*sin(lat) non preserva i centroidi vettoriali o tutte le
altre quantita non lineari. Non forzare Phi con una riscalatura successiva
che rompa le identita del dipolo.

Conservare separatamente misure sui pixel e sulla griglia iniziale e
riportare questa differenza prima del trasporto; provarne la convergenza
sui casi misti. Aggiungere una prova del principale del punto 3 SENZA
bitmap e soglia: `p1_consistency()` usa attualmente solo pixel P1 sopra
100 G, quindi non copre il campo grezzo principale con le parti deboli.
Le misure osservate e simulate devono avere lo stesso operatore di
rimappatura/scoring, come fissato nella revisione del protocollo.

I punti fuori dal supporto dei centri sono ancora clippati, pur essendo
contati. I runner dovranno rifiutare esplicitamente il caso o applicare
una rappresentazione concordata; non ignorare `nout` e dichiarare D
conservato. Nessun aggiustamento dopo la lettura degli esiti.

## 4. Gaussiane e coordinate sferiche

Due problemi nella costruzione della griglia:
- il passo predefinito dipende da sigma MAX, mentre deve risolvere la
  componente piu stretta. Con sigma 0,2° e 1° viene chiesto 0,05° anziche
  un passo non superiore a 0,02°;
- centri 179° e -179° producono un riquadro di 372° di longitudine,
  anziche una rappresentazione locale attraverso la cucitura. Nessun
  array enorme e stato allocato nella prova: e stata intercettata la
  richiesta della griglia. E un problema anche di costo e di conteggio
  delle aree, non solo della convenzione delle etichette.

Unwrap su un ramo comune prima dei bounding box e del deposito; coordinate
periodiche e celle fisiche non duplicate. Risolvere sigma MIN, dichiarare
supporto/troncamento (ora 7 sigma) e verificarne l'errore. Evitare una
latitudine oltre i poli: `sphere_grid((89,91),...)` restituisce oggi anche
aree negative. Validare geometria, passi e larghezze; non normalizzare una
gaussiana con una somma di aree non fisica.

## 5. Durate reali e contratto delle misure

`LocalBox.evolve` accetta solo durate multiple di dt. T_OBS non garantisce
questa proprieta: un intervallo positivo di 601 s viene rifiutato.
Serve l'ultimo sottopasso con la durata effettiva, sia nella parte
avvettiva sia in quella implicita. Un tempo negativo di -600 s invece
oggi viene accettato restituendo il campo invariato: rifiutarlo
esplicitamente. Validare anche dt positivo/finito, dimensioni e tempi.

`field_measures` deve distinguere l'assenza di una polarita dall'assenza
di tutte le informazioni: con una sola polarita positiva il suo flusso
viene dato ma il suo centroide resta NaN. Per il punto 3, che ammette
controlli con una sola polarita, conservare il centroide disponibile,
lasciando separazione/tilt/leading non definiti. Completare gli output
previsti (latitudine media e D_bal, ove definiti) e gli stati espliciti.
Verificare coordinate finite ed aree positive, senza affidarsi al solo
Br finito per riconoscere un ingresso valido.

## 6. Q4: chiusura ora verificabile su commit

Durante la revisione e arrivato `d303c3a`: SHA del riconteggio
`a6c0a72d227c26d15f5ca584f22bdf12e63c3222028ffe4eaab3f33aa0233398`,
identico alla fotografia gia approvata con condizioni in e87fff7.
Ho verificato la copia del codice e il log completo dell'autore:
**46 righe OK, zero FALLITO, finale «selftest: 46/46 superati»**.
Non ho rieseguito quei 46 test; le mie prove indipendenti della base,
dei sei controesempi e dei cinque casi di dominio sono gia conservate.

Log dell'autore preservato byte per byte in
`reviews/MDI_Q4_RECOUNT_d303c3a_CODEX/SELFTEST.txt`, con provenienza e hash.
La cartella di origine nel repo MWO contiene soltanto materiale di revisione
BL: non e un prodotto scientifico del progetto polare/SINDy importato qui.

**Le condizioni del via al solo riconteggio Q4 reale sono soddisfatte.**
Nessun rilancio Q4; dopo il check, conservare la ricevuta completa prima
della lettura/rapporto. Non ho letto i risultati o il log della corsa
scientifica Q4, ne eseguito il riconteggio reale in questa revisione.

## Seguito concreto

Claude recepisce gli aggiustamenti numerici con i test sopra, mantenendo
il lavoro sui sintetici. In parallelo aggiorna e congela i protocolli
secondo e87fff7, inclusa la fattibilita geometrica del punto 3. Poi revisione
dei runner e dei riconteggi prima di qualunque misura sui dati osservati.
Questa consegna non cambia le scelte fisiche o riapre T3/T5.

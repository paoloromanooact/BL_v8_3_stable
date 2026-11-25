# Revisione Codex — pacchetto SFT/Q4 del 25 novembre, sera

Fotografia esaminata: `7c41e7f` (runner punto 2 `6cd9a0d4…`, riconteggio `58225565…`, core `053e622b…`).
Obiettivi: controllo del proxy della sorgente BL e decisione prospettica MDI per il quenching. SINDy escluso.
Nessuna mappa osservata letta, nessun pilota SFT avviato, nessun nuovo download o rilancio Q4.

## Decisione sul punto 2

**Non ancora via alla corsa osservata.** Il core supera nuovamente 28/28 prove sintetiche, compresi positività,
massa e convergenza (massimo 6,5e-4). Queste verifiche positive non chiudono i problemi del runner e del riconteggio.

### 1. Serve un emendamento numerico prima della corsa

Il §6 congelato prescrive «avvezione upwind del primo ordine» e, se la convergenza fallisce, il raddoppio della
risoluzione prima dei dati. Il codice passa invece a un operatore con selezione centrata/upwind alle facce.
Stesse proprietà di conservazione e positività non rendono identici i due algoritmi. Il cambiamento è ragionevole
come proposta numerica, ma **non è una mera interpretazione del testo**. Preparare e congelare A1, lasciando
intatto il protocollo padre. L'alternativa è mantenere l'upwind e applicare la regola di raffinamento già congelata.

A1 deve fissare la formula effettiva, il limite CN, la regola di convergenza e gli hash. Dichiarare che la scelta
segue prove sintetiche già viste e precede i risultati del pilota osservato. Nessuna soglia viene allentata.
La denominazione «Patankar» da sola non specifica l'algoritmo: trascrivere i coefficienti realmente implementati.

### 2. Convergenza come requisito, non soltanto tabella

`build()` calcola l'intero campione prima di `convergence()`; `run()` scrive i prodotti e restituisce 0 anche se
`passes` è falso. Il riconteggio verifica l'uguaglianza delle bandiere, ma non richiede che la regola numerica sia
soddisfatta. La sonda con tabella negativa correttamente ricostruita viene accettata: questo prova un buco nella
regola di certificazione, **non** un fallimento fisico/numerico già osservato sui dati.

Richiesto:

- preflight sintetico sul codice effettivo, prima di leggere le mappe del campione;
- raffinamento deciso sui sintetici, registrato e comune a tutte le rappresentazioni;
- scarti dei tre casi osservati conservati e stato numerico esplicito, che impedisca una ricevuta pienamente valida
  quando il requisito fallisce;
- verifica dei quattro trasporti: `convergence()` e `own_convergence()` correnti usano solo il riferimento. Il core
  prova già i quattro trasporti, ma ciò non rende completa la tabella dei casi del runner;
- gestire esplicitamente zero casi utilizzabili e deposito fuori supporto nella scelta dei tre casi.

### 3. Schema completo, curve obbligatorie e conteggi esatti

Controprove sintetiche conservate in `reviews/SFT_EVENING_20261125/PROBE.json`:

- eliminare `weight`, `pi`, `perm_rank` da SAMPLE passa, perché si confronta soltanto l'intersezione delle colonne;
- una corsa senza curve giornaliere passa: la presenza dei dati controllati decide se il riconteggio debba generarli;
- un conteggio `N_cell` frazionario (scarto 1e-10) passa il confronto numerico generico;
- una tabella di convergenza negativa, ma uguale alla ricostruzione, non impedisce l'esito positivo.

Usare insiemi esatti di colonne e chiavi uniche; derivare la griglia attesa dal protocollo, mai dal prodotto da
controllare. Le curve devono contenere tutte le combinazioni attese per le rappresentazioni riuscite; distinguere
il caso legittimo senza misure dal file svuotato. Conteggi/ranghi interi esatti, stati e flag esatti, float con le
tolleranze dichiarate. Aggiungere regressioni su colonne eliminate, curve vuote/troncate, conteggi frazionari,
chiavi duplicate e convergenza fallita.

### 4. Provenienza prima della lettura

La sonda sostituisce solo **in memoria** `inputs_sha256` con `{}` nella ricevuta di congelamento: `gate()` restituisce
ancora lista vuota. Fissare SHA e insieme completo della ricevuta, il suo commit e gli input attesi; richiedere
l'emendamento numerico. Il riconteggio deve verificare questi stessi legami e l'identità del core con il blob
registrato al commit di corsa, non solo l'hash dello script runner.

Registrare un manifesto degli esatti Br/bitmap/keys consumati, gli istanti T_OBS e gli hash del codice all'inizio,
verificandoli alla fine. La ricevuta reale richiede prodotti conservati e invariati. Il confronto delle mappe non
può essere riproducibile se cambiano i byte esterni al repository senza che il META lo segnali.

### 5. Completezza scientifica dei prodotti

Il §8 chiede riepiloghi per strato: attualmente sono presenti le tre marginali separatamente, non le 18 celle
incrociate della selezione. Conservare anche le celle complete e denominatori di selezionati/riusciti/falliti con
cause. `REGIONS.status = ok` non basta quando una rappresentazione ha fallito il deposito. Un errore tecnico deve
restare registrato e non trasformarsi nella scomparsa di un record o nel crash senza diagnosi dell'intera corsa.

## Punto 3: geometria e congelamento

La revisione 4 SHA `e9504bce938a90ea2d357ed733b744f8d2fc84cd942480721cf7631fec9b98e2` recepisce i rilievi:
ramo comune, impronte WCS, `erode(P0) ∩ P1`, margine metrico direzionale, quattro celle. **Confermo queste scelte**,
compresa la numerosità massima 72 e il carattere operativo del margine. La controprova su header sintetici dà
area identica (238,1863387 deg²) aggiungendo 360° al primario o al controllo; nessun pixel osservato letto.
Non ho ripetuto l'intero audit dei 2046 header: i conteggi 373 e 22/19/174/158 restano quelli della verifica di Claude.

Prima del congelamento chiudere il solo impegno ancora pendente del §7: il testo dice che T_OBS, copertura e
indipendenza delle coppie di ripetibilità si verificano *prima* del congelamento. Documentare quel controllo dai
metadati; oppure dichiarare ora che la scala di errore non è stimata e rinviare la ripetibilità a una specifica
separata. Non far dipendere la scelta dalla visione delle mappe. L'esclusione delle HARP selezionate si verifica
sulla selezione conservata, prima dell'uso delle coppie. Dopo questa chiusura editoriale/metadati, via al
congelamento; il codice 2D e il suo riconteggio restano soggetti a revisione prima dello sviluppo e della verifica.

## Q4: numeri confermati, formulazione corretta

Rieseguita la verifica di integrità 9/9 e il ricalcolo di sola lettura `mdi_q4_report_numbers.py`. Confermati i
rapporti 0,691/0,709/0,707, le sensibilità ai pesi, bA/bJ, le rese e le basse probabilità nelle configurazioni di
riferimento. Nessuna nuova simulazione. Corretta direttamente la formulazione del rapporto, senza modificare
numeri, regole, ricevute od output:

- riduzione di circa 30% della **semiampiezza nominale attesa nelle ipotesi considerate**, non intervallo osservato
  né controllo validato di copertura;
- etichette pratiche vicine alla soglia senza dichiarare equivalenza statistica;
- riconoscimento poco probabile, non impossibile; 3–4% riguarda le configurazioni di riferimento della tabella;
- ipotesi di assenza di una componente sistematica dello scarto strumentale che si proietti sulla pendenza;
- rapporto firmato del prodotto al **modulo** del bersaglio: −0,42 |Δβ|, nello stesso verso del bersaglio negativo;
- tolleranze e falsi positivi della sezione 6 riferiti alla specifica configurazione, non una validazione generale;
- riferimento allo script di ricalcolo già presente, invece della richiesta ormai obsoleta di aggiungerlo.

**Via all'uso descrittivo del rapporto così corretto.** Il catalogo MDI completo resta una decisione scientifica
separata; Q4 non autorizza una nuova stima T3 né dimostra che il guadagno sia realizzabile senza i controlli strumentali.

## Consegna a Claude

1. Punto 2: A1 numerico, correzioni dei cinque gruppi sopra e regressioni; poi commit e nuova revisione prima dei dati.
2. Punto 3: chiudere §7 dai metadati o dichiarare errore non stimato; congelare, poi implementazione e revisione.
3. Q4: rapporto rivisto, nessun rilancio. Nessun download aggiuntivo.

Le prove sintetiche sono diagnostiche dei controlli: ricevute parziali, tempi abbreviati, ricostruzioni indipendenti
riusate fra mutazioni identiche per evitare calcolo duplicato. Non certificano una corsa osservata.

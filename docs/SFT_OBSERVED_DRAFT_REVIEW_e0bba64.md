# Revisione Codex — confronto SFT con evoluzione osservata, rev. 1

25 novembre 2026. Bozza `e0bba64`, SHA-256
`b2dda443fdd0149393276df641d6585068da37d2b1f5d2aba1b376a8870d39f0`.
Collegata alla revisione del punto 2, `docs/SFT_MAP_BIPOLE_DRAFT_REVIEW_fa3f08d.md`.

**Domanda utile, ma non ancora congelabile.** Occorre correggere la
popolazione degli strati e rendere confrontabili inizializzazione,
maschere e osservabili prima di giudicare il trasporto. Sotto sono
separate le correzioni necessarie dalle scelte suggerite per il pilota.
Nessuna mappa FITS osservata letta, nessuna evoluzione numerica SFT,
installazione o acquisizione eseguita in questa revisione.

## A. Correzioni necessarie

### A1. Lo strato di flusso in calo e impossibile con questa selezione

`select_records.select()` sceglie il controllo al massimo di USFLUX entro
60°, su candidati che comprendono il primario (entro 30°, stessa regola
QUALITY). Quindi `USFLUX_control >= USFLUX_primary` per costruzione.

Audit dei soli metadati P1: 7133 HARP, nessun controllo sotto il primario,
nessun calo oltre il 20%, rapporto minimo 1. La restrizione a controlli
successivi di 1–4,5 giorni non puo creare uno strato in calo assente
nell'intera popolazione. Un caso sintetico di reale calo seleziona lo
stesso record come primario e controllo, e non entra nelle coppie distinte.

Se la classificazione usa il rapporto fra endpoint, fissare soltanto
«crescita >20%» e «variazione fino al 20%» e rinunciare a generalizzare alle
fasi di decadimento. Le 18 celle diventano 12, prima di eventuali celle
povere. Se si intende un'altra statistica della traiettoria oraria,
definirla esattamente e verificarne la popolazione prima di congelare.
Non sostituire a posteriori USFLUX con il flusso rimisurato per ottenere
uno strato di calo. Un campione con endpoint temporali indipendenti dal
massimo richiedera una selezione distinta, dichiarata prima dei pixel.

### A2. Non bilanciare soltanto l'inizializzazione

Il punto 2 confronta due rappresentazioni bilanciate nello stesso modello.
Il punto 3 confronta invece con il campo osservato: gli operatori di
preparazione e misura devono essere coerenti sui due lati e sui riferimenti.

Esempio sintetico senza alcuna evoluzione: D grezzo = 0,01525 G,
D_bal = 0,00249 G. Inizializzare con la mappa bilanciata e confrontare con
D osservato grezzo produce gia 0,01275 G di errore, mentre la persistenza
della mappa grezza ha errore zero. Non e un errore del trasporto.

**Scelta consigliata:** mappa locale grezza nel principale, con la
maschera iniziale dichiarata; misurare D e D_bal come osservabili distinte.
La sensibilita bilanciata deve trasformare coerentemente t0 e t1 e avere
propri riferimenti. Tutti i modelli di un confronto, inclusi persistenza
e sola rotazione, partono dallo stesso campo preparato.

Il flusso netto non nullo in una finestra locale non e automaticamente un
monopolo solare: il campo compensante puo stare fuori dalla finestra.
Il modello locale puo trasportare quel campo netto, ma non ricostruisce il
completamento globale. Togliere la giustificazione «il monopolo locale non
pesa»: la trasformazione di bilanciamento cambia davvero il campo.

### A3. Le due maschere non possono essere il solo confronto principale

Osservazione sulla bitmap t1 e previsione sulla bitmap t0 trasportata sono
integrali su supporti diversi. La differenza mescola trasporto, nuova
assegnazione HARP, copertura e definizione della misura.

Fissare prima della verifica un dominio comune in coordinate eliografiche,
con copertura osservativa valida a entrambi gli istanti; confrontare su
quel medesimo dominio osservazione, SFT, persistenza e sola rotazione.
Registrare area coperta e flusso iniziale tagliato; i casi non valutabili
hanno uno stato esplicito, senza sostituzioni. Il dominio di simulazione
puo essere piu ampio del dominio osservabile: non confondere i due.

Riportare in parallelo le misure «come P1» sulle bitmap proprie, come
confronto fra prodotti di catalogo, senza identificarle con il confronto
a supporto fisso. Servono anche osservabili integrali del campo senza
ritaglio dinamico a 100 G: dopo il trasporto la soglia puo rimuovere flusso
e modificare D da sola. Il taglio 100 G resta una misura supplementare
esplicita. La rotazione conserva D sull'intero campo a supporto completo;
non e una garanzia su D ritagliato o dopo rimappature non conservative.

Aggiungere un test d'identita a Delta t = 0 con lo stesso operatore di
preparazione/misura sui due lati. Se l'input e soltanto il campo P1 sopra
100 G, il confronto con tutto il campo grezzo osservato include gia il
campo debole omesso all'inizio: misurare tale contributo e non chiamarlo
errore del trasporto. Per una verifica del trasporto sul campo completo,
inizializzare con tutti i pixel finiti disponibili sul dominio osservato;
il ramo con la sola sorgente mascherata P1 e allora una rappresentazione
alternativa dichiarata. Fissare questa scelta nel testo prima del codice.
La variante bipolo bilanciata del punto 2 si confronta con la corrispondente
mappa bilanciata; non mescolare la sua preparazione con il principale grezzo.

La «maschera trasportata» deve avere una definizione algoritmica: con
la diffusione il supporto matematico non resta compatto, e «pixel evoluti
sopra soglia» non definisce una frontiera materiale. Se mantenuta come
diagnostica, proporrei la bitmap iniziale solo advettata, con algoritmo e
soglia di copertura fissati. Il flusso osservato fuori da essa non e una
misura della sola nuova emergenza: anche la diffusione lo porta fuori.

### A4. Il residuo non identifica una causa

Il modello SFT gia include cancellazione del campo firmato per diffusione.
Non rappresenta tutta l'emergenza/submergenza, le velocita locali reali,
la convezione risolta o il campo fuori dalla patch iniziale. Una variazione
di flusso unsigned non separa questi contributi da maschera, rumore e
copertura; anche un flusso quasi costante puo nascondere emergenza e
cancellazione simultanee.

Riformulare la domanda in «quanto i residui si associano alla variazione
di flusso», senza promettere «quanta parte proviene» da una causa.
Eliminare le attribuzioni del §8: residuo grande in uno strato stabile
non dimostra errore di trasporto; correlazione con DeltaPhi non misura
l'emergenza non modellata. Il pilota confronta prestazioni descrittive di
modelli incompleti su una popolazione condizionata dalla selezione.

### A5. Geometria, sistema rotante e bordo

Una finestra fissa ±15° attorno al centroide non garantisce un margine di
15° dal campo iniziale: una HARP puo essere estesa o asimmetrica. Fissare
il dominio dalla copertura iniziale piu un margine numerico basato su
trasporto massimo e tempo massimo; congelare le regole di ampliamento e
le condizioni al bordo, registrando tagli e fallimenti.

In Carrington usare `omega_P1(lat) - 14.1844 deg/day`, non la velocita
siderale intera. Con la funzione P1 a 15° e 4,5 giorni, lo spostamento e
1,62°, mentre senza conversione di sistema e 65,45°. Rimappare le CEA
oblique con la WCS completa, con orientamento e raccordo 0/360 verificati;
non riallineare i magnetogrammi ottimizzando la correlazione sulla verifica.

Testare il bordo con ampliamento del dominio e stabilita degli osservabili,
non soltanto con flusso netto uscito: polarita opposte possono cancellarsi
nel conteggio netto, e una condizione di flusso nullo rende quel controllo
banale. Definire anche una misura unsigned nel bordo. Una gaussiana ha
larghezza analitica in diffusione sul piano; sulla sfera usarla come
limite locale con errore di curvatura controllato, oppure aggiungere modi
armonici sferici con decadimento noto.

## B. Raccordo dei parametri con il punto 2

La lettura congiunta aggiunge una cautela alla prima raccomandazione:
Yeates 2020 §3.1 sceglie eta = 350 e Du = 0,041 confrontando l'evoluzione
del ciclo 24 HMI. Non chiamare automaticamente quei dati indipendenti
dalla scelta dei parametri solo perche la scelta fu fatta in letteratura.

**Raccomandazione finale comune ai due protocolli:** riferimento
eta = 466,8 km²/s, Du = 0,025 km/s, p = 2,33, tau infinito, con
`v(lat) = Du sin(lat) cos(lat)^p`. E il set pre-HMI dei cicli 21–23
riportato nel §3.1 di Yeates 2020. Du non e la velocita massima.
Usare 350/0,041 e le due combinazioni incrociate come sensibilita fissate,
dichiarando la provenienza e la sovrapposizione temporale della taratura
HMI. Sono scenari, non un intervallo probabilistico dell'errore di trasporto.
Il decadimento globale del punto 2 non e necessario nel pilota di pochi
giorni. Nessuna scelta dei parametri viene migliorata sulla verifica.

Questo raccordo sostituisce la sola scelta del riferimento numerico nella
prima revisione del punto 2; non cambia nessun protocollo congelato, che
qui ancora non esiste. Le correzioni A1–A3 del punto 2 restano necessarie.

## C. Risposte agli otto punti aperti

1. **Tempi 1–4,5 giorni:** approvati, T_OBS interpretato con scala TAI/UTC
   esplicita e intervalli in secondi. Nessuna promessa sui tempi polari.
2. **Andamento del flusso:** soglia 20% ammissibile come semplice
   suddivisione descrittiva, ma vedi A1. Riportare la variabile di selezione
   USFLUX e il flusso P1 rimisurato come quantita diverse; nessuna delle due
   e una misura pura di emergenza. Prima del congelamento tabella delle
   celle ottenibili dai soli metadati.
3. **Maschere:** dominio comune nel confronto principale e bitmap proprie
   come diagnostica; vedi A3. Non scegliere la maschera che migliora l'esito.
4. **Codice:** approvata l'implementazione 2D locale propria, senza dover
   costruire ora una catena HipFT globale. HipFT e un oracolo aggiuntivo se
   disponibile, non un requisito di installazione da anteporre alle prove
   analitiche. Fissare prima equazione sferica, griglia e bordi.
5. **Errore osservativo:** nei soli nomi dei tre insiemi locali risultano
   299 coppie consecutive entro due ore, in 296 HARP (T_REC nominale).
   Quindi una verifica di fattibilita e possibile, ma occorre ancora
   controllare T_OBS, metadati, indipendenza dal campione e copertura.
   Non sono sequenze casuali e la variazione include evoluzione reale:
   «ripetibilita osservata», non rumore strumentale puro. Se mancano casi
   adeguati, dichiarare errore non stimato senza bloccare il confronto
   descrittivo con i riferimenti. Nessun nuovo download richiesto qui.
6. **Campione e split:** 1/3 sviluppo e 2/3 verifica approvati; circa 108
   e un tetto, da riformulare sulle celle effettive dopo A1. Congelare
   arrotondamenti delle celle povere, semi, ordinamento, inclusioni e
   probabilita; usare pesi N/n nei riepiloghi della popolazione. Separare
   famiglie/patch sovrapposte nei due insiemi quando identificabili dai
   metadati: HARP diversi non garantiscono indipendenza del campo.
   Non richiederei `valid_bl(t1)=1` per il bacino di D e flusso: una sola
   polarita o la scomparsa del segnale rendono il tilt non definito, ma
   possono essere osservazioni informative dell'evoluzione. In alternativa
   dichiarare esplicitamente la popolazione condizionata anche al successo
   futuro e riportare le esclusioni. Mai trasformare un tilt mancante in 0.
7. **Lettura:** soltanto descrittiva, nessuna soglia di validazione pratica.
   Preferire differenze appaiate degli errori assoluti (baseline meno SFT)
   e frazione di miglioramenti/pareggi/peggioramenti. I rapporti con errore
   della persistenza nullo sono non definiti: niente epsilon. Per tilt
   usare differenze assiali, per longitudine differenze circolari; polarita
   leading e segno di D separati. Per la correlazione di mappe fissare
   copertura finita, pesi d'area e casi a varianza nulla.
8. **Controllo al massimo:** basta dichiararlo per un pilota limitato
   a quella popolazione; non basta per inferenze sulle regioni in generale.
   Non aprire ora nuove acquisizioni. Un endpoint vicino a t0+2 giorni
   puo diventare una sensibilita soltanto con regola, disponibilita e
   campione fissati prima dei pixel, senza riusare l'etichetta di campione
   rappresentativo. Le precedenti letture P1d restano dichiarate.

Nella regola di accesso alla verifica distinguere: uso consentito dei
metadati per selezione/strati; uso non consentito delle mappe future per
scelte di modello o di misura. Conservare split e impronte prima dello
sviluppo; poi conservare un registro delle scelte congelate prima della
corsa di verifica. Nessun nuovo T3/T5 o verdetto sul quenching.

## D. Fonti, prove e prossimo passo

- [Gottschling et al., preprint 2021, pubblicato A&A 2022](https://arxiv.org/abs/2111.01896):
  confronto locale su regioni emergenti e limiti della fase iniziale;
  non e una validazione universale di questo campione o di questi parametri.
- [Yeates 2020, §3.1](https://arxiv.org/pdf/2008.03203): provenienza dei
  parametri e differenza fra taratura cicli 21–23 e ciclo 24 HMI.
- Codice P1 locale: `select_records.py`, `measure.py`, `recurrence.py`.
- Sonda `scripts/sft_observed_draft_review_probe.py`, esito in
  `docs/SFT_OBSERVED_DRAFT_REVIEW_e0bba64_RESULTS.json`. Legge solo quattro
  colonne dei metadati selezionati e nomi dei FITS; gli esempi di
  inizializzazione e sistema rotante sono sintetici, senza evoluzione SFT.

Prossimo passo di Claude: revisione delle due bozze con le scelte comuni,
poi controllo breve e congelamento; soltanto dopo implementazione e
revisione del codice prima dei piloti. Le bozze originali restano intatte
in questa consegna. Q4 rimane una linea separata, senza rilancio.

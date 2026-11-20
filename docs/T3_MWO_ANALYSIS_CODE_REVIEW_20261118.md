# Revisione della consegna statistica T3 MWO — 18 novembre 2026

## 20 novembre — riconteggio di stabilità 7fd1121: miglioramenti confermati, due rilievi residui

Rivisto il nuovo riconteggio e la patch non applicata. Selftest 16/16 positivo: la nuova fixture
end-to-end copre C, S1, S2 per emisfero, P1 e tabelle descrittive; le tredici mutazioni previste
sono rifiutate. Il vecchio probe f72 non è direttamente riutilizzabile: alla nuova firma va passato
il riferimento P1 sintetico, altrimenti fallisce la baseline per una fixture non aggiornata.

Due controesempi ulteriori, riproducibili con
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/t3_mwo_stability_recount_residual_probe.py`:

1. **Dominio dei parametri S2.** Sul campione sintetico integro, impostando phi=-0,1 e ricalcolando
   SE e limiti coerentemente, il controllo completo rimane positivo. La covarianza è calcolabile,
   ma phi non appartiene al dominio M congelato [0; 0,98]. `s2_recompute` deve controllare finitezza,
   dominio REML dei cinque parametri, SE finito e positivo e limiti finiti, prima di qualsiasi confronto.
   Applicare alle stime complessive, emisferiche e P1. Provare anche sigma_x2 <= 0 e kappa fuori dominio.
2. **Catena prima di SEALED.** `chain_problems` controlla le ricevute e i legami dello STABILITY META,
   ma non i legami check META → catalogo e validation META → check, né ACCEPTANCE.problems.
   Con una validazione legata a un disegno obsoleto e `problems=['incomplete grid']` restituisce comunque
   lista vuota, anche se il ramo principale di analisi la rifiuterebbe. Verificare questi legami e
   distinguere validazione negativa valida (via descrittiva) da validazione tecnicamente invalida
   (nessuna apertura). Nel probe solo `committed` è simulato, per isolare la guardia dai file Git reali.

Il probe restituisce 1 finché uno dei due casi viene accettato. Nessuna risposta reale sigillata letta.
Le correzioni possono restare nel riconteggio separato; nessuna modifica o ripartenza della validazione
attiva è richiesta da questi due rilievi. La patch resta non applicata; manca ancora il via al nuovo
riconteggio come requisito affidabile della stima finale.


## Revisione di S1–S4 e della patch estesa f72c25c — 20 novembre 2026

La prova completa di check() è stata eseguita su dati interamente sintetici, senza aprire i tilt MWO
reali e senza cambiare i file della validazione in corso. Il nuovo probe riproducibile è
`scripts/t3_mwo_stability_recount_review_probe.py`. Genera 120 record isolati più quattro non isolati,
i file gDPD/sDPD di prova e tutti gli output previsti; S1 usa le 2000 repliche e il seme congelati.
La risposta di controllo è costruita con un coefficiente noto; gli SE usano parametri di varianza
noti, senza riottimizzare M. La baseline completa passa. Nelle prove di modifica si riusa soltanto
S1, perché disegno e risposte sono identici; vengono ricostruiti gli altri controlli.

**Esito: il nuovo riconteggio non è ancora approvato come condizione per stimare β₃.**
Il confronto di S1 da solo è corretto, ma il percorso completo può certificare output sbagliati.
La validazione sintetica già in esecuzione non è coinvolta e può proseguire.

### 1. C è letto dall'output che dovrebbe essere verificato

In check(), C viene da STABILITY.json e non dalla ricostruzione sul sottoinsieme WL. Nella baseline
sintetica C = 1,30909 e β dello scarto = 2,61818: S2 è dipendente dall'attività e la regola dà
«descrittivo». Gonfiando soltanto C a 130,909 e aggiornando gli esiti dichiarati in STABILITY.json,
lo stesso riconteggio restituisce True e una ricevuta completa per «verdetto».

Gli hash dei prodotti sintetici vengono aggiornati a ogni modifica per isolare la verifica scientifica.
Il problema non riguarda un hash ignorato: è un valore derivato non ricalcolato indipendentemente.

Prima di emettere una ricevuta valida occorre ricostruire C con la propria matrice e la propria riga
QR sul sottoinsieme WL, confrontarlo con TARGETS e STABILITY e derivare S2 e la regola finale da quel
valore. Vanno confrontati anche i limiti salvati, distinguibile da zero, stato, numerosità e S2 per
emisfero. Gli intervalli ricostruiti attualmente sono usati per il solo stato, senza confrontare i
limiti scritti nel file. La prova con limiti S2 cambiati lascia passare il controllo.

### 2. Alcune uscite sono soltanto presenti, non ricontate

Le altre prove con output modificati vengono accettate:
- conteggio e mediana di S2_P1.json portati a 999;
- mediane di S4_DWL_ALL.csv cambiate, comprese quelle per terzile;
- epoche in S3_HALE.csv rinominate, lasciando invariati conteggi e frazioni;
- flag di S1_TABLE.csv invertiti, lasciando invariati coefficienti e stato generale;
- β di un risultato S2 emisferico cambiato senza conseguenze.

Il controllo deve verificare le chiavi e tutte le quantità dichiarate, non solo alcuni array:
S1 per epoca/emisfero, limiti e flag; S3 con le etichette; S4 principale e aggiuntivi con numerosità,
frazioni, posizione del giorno, |LCM|, mediane, medie ed errori descrittivi; quote delle fonti DPD.
Per P1 servono confronto degli abbinamenti, differenze, conteggi, mediana e fit descrittivo, con un
lettore indipendente. S2_P1_MATCHED.csv attualmente non è nemmeno obbligatorio nel controllo di presenza.
I casi vuoti, non identificabili e di errore devono restare stati espliciti e verificabili.

### 3. Provenienza e sigillo del riconteggio

Prima di aprire SEALED il nuovo script controlla soltanto che la cartella di stabilità sia conservata
in Git. La catena del lettore principale è più forte: un file di stabilità esistente non sostituisce
le ricevute e la lettura registrata della validazione. Il riconteggio deve verificarne i prerequisiti
e i legami agli ingressi correnti, e verificare il META del catalogo, del controllo del disegno e della
validazione usati dalla stabilità. Il writer di stabilità deve registrare quei legami; la patch attuale
aggiunge solo l'hash di extras. Non occorre importare il modulo di analisi per controllare questi metadati.
Il percorso sintetico può disabilitare Git esplicitamente, ma il comando reale deve custodire il sigillo.

### Patch e seguito

La parte della patch che impone la ricevuta di stabilità prima di --estimate è corretta. Ho esteso
`scripts/t3_mwo_stability_wiring_probe.py`: in una copia temporanea la stima rifiuta ricevuta assente,
parziale o legata a un META diverso, e accetta quella completa e correttamente legata. Questo verifica
il collegamento, non rende affidabile una ricevuta positiva generata dal riconteggio ancora incompleto.

La patch resta non applicata. La precedente approvazione del collegamento delle uscite descrittive
non costituisce approvazione del nuovo riconteggio. Prima della stima occorrono correzioni e una prova
completa: baseline positiva e rifiuto di ciascuna modifica, con ricevuta negativa o parziale coerente.
Nessuna soglia, parametro scientifico o risultato reale è cambiato in questa revisione.


## Rapporto HMI e collegamento delle uscite descrittive — 20 novembre 2026

Verificati i prodotti HMI conservati in 9dc41ad e la ricevuta 19/19 di a72ce2d. Dieci stime e dieci SE
ricostruiti nuovamente, con scarti relativi massimi 6,7e-13 e 2,9e-13. Intervalli e stato descrittivo coerenti;
verificati hash di ESTIMATES e legame al META della validazione. Nessuna nuova simulazione o stima di MWO.

Il rapporto HMI è aggiornato senza cambiare i numeri: la fase emisferica non rimuove la stima centrale
negativa di Q2 in questo modello; non identifica la causa né esclude ogni ruolo dello sfasamento.
L'estremo nominale +0,20 non è un vincolo fisico validato. Per Q3 le stime centrali sono positive,
ma tutti gli intervalli nominali includono zero: non dimostrano una crescita né escludono un quenching
locale. Il confronto con uno studio sul campo massimo non è un test della stessa relazione sul flusso.

**Patch 6fadf10 approvata per l'applicazione dopo la fine, la conservazione e il riconteggio della
validazione, e dopo la sua lettura registrata.** Non applicata al codice attivo in questa revisione.

`git apply --check` passa. Ho applicato la patch soltanto a copie temporanee di analisi ed extras e
provato l'intero percorso stability() su ingressi sintetici. Il probe riproducibile è
`scripts/t3_mwo_stability_wiring_probe.py`: replica i quattro test del modulo e verifica che il
collegamento produca i cinque file aggiuntivi, registri extras_sha256 e blocchi la lettura del sigillo
quando IMPLEMENTED è False. I metodi statistici sono sostituiti con risposte sintetiche durante questa
prova di collegamento; non è una validazione scientifica e non apre file sigillati reali.

La modifica aggiunge soltanto uscite descrittive e la provenienza del modulo: non cambia matrice,
procedura M o regola finale. Dopo l'applicazione andranno conservati il nuovo commit e gli hash della
fase di stabilità, distinti da quelli della validazione già eseguita. Conservare la corsa con il suo
codice originale e non modificare script o ingressi mentre la griglia è in esecuzione.

Per interpretare S4, dichiarare i denominatori: S4_ISOLATION riguarda i gruppi misurabili dell'insieme
«tutti», classificati secondo la presenza di un record nel campione isolato; S4_DWL_ALL distingue
invece l'isolamento del record effettivamente scelto. I terzili nel codice hanno riferimenti diversi
(insieme tutti e suo sottoinsieme con WL valido); riportarli come tali, senza trattare le etichette
1–3 come intervalli identici. I controlli descrivono la selezione, non la correggono.

Il controllo dei soli identificativi P1 trova duplicati NOAA/giorno fuori dalla finestra 2010–2012,
ma nessuno dentro quella del confronto. Nessun tilt MWO sigillato letto. Hash dei due file attivi
verificati prima e dopo le prove: invariati.


## Chiusura dei rilievi su 8129c01 — 20 novembre 2026

Verifica di Codex eseguita durante la validazione già avviata, senza modificare codice o ingressi della corsa.
Script di analisi SHA-256 `cb5ecccb88d66b813dbede6382a2502f4bc32059b086d5cb02de2752589f9490`;
riconteggio `17def5bfc2d7357000e0f4fd44e2ee623414f7ce0faaff9fb71d2707df3b911d`.

**I due rilievi bloccanti della revisione precedente sono chiusi. La validazione sintetica può proseguire.**
La sonda della varianza sul codice corrente rifiuta la seconda riga con sigma_x2 NaN: una riga invalida
nel denominatore, accettazione falsa, riconteggio 7/8 con technical_ok false. Non viene più emessa una
ricevuta positiva. Il codice richiede parametri finiti e nel dominio REML; ogni scarto SE viene verificato
esplicitamente come finito. Una ricostruzione su un sottoinsieme marca partial true.

Con fixture sintetiche dotate di ricevute complete ho verificato separatamente che la catena:
- ammette una validazione negativa ma tecnicamente valida per la via descrittiva;
- rifiuta ricevute senza conteggi, 0/0 o senza i controlli richiesti;
- richiede il riconteggio del disegno legato al META;
- rifiuta la vecchia validazione dopo un cambiamento del controllo del disegno.

Sul repository reale chain_problem('validate') non segnala impedimenti; la stabilità rifiuta perché
la validazione non è ancora conservata. In aggiunta, il codice richiede IMPLEMENTED True nel modulo
separato delle uscite descrittive, prima della lettura del sigillo. Il modulo è attualmente False e
non viene usato dalla validazione: scriverlo separatamente non cambia i file eseguiti dalla griglia.
Questo controllo non ne approva ancora il collegamento o il contenuto per S1-S4.

Controllati gli hash dichiarati dei prodotti non sigillati di R2 e del controllo del disegno, e il
legame della ricevuta indipendente 6/6 al META. Confermati i bersagli −0,5417308898 e −1,0834617795,
C = 0,5428552449 e disponibilità WL 4696/5225. Precisazione di conteggio: le 24 colonne elencate in
kept sono i termini diversi da x3; la matrice completa comprende anche x3, quindi 25 colonne.

I sei file registrati da provenance() (script, tre moduli, DESIGN e TARGETS) coincidono con il contenuto
del commit di avvio 8129c01. Nessuno è modificato da questa revisione. Il log della corsa riporta
selftest iniziale 41/41 e benchmark di 108 unità su tutte le 18 configurazioni: 249 secondi con cinque
processi, previsione 48,86 ore per 76 000 unità, senza tetto di durata. È una previsione sotto il carico
misurato, da confrontare con l'avanzamento reale.

Restano per la fine della corsa conservazione, riconteggio completo e lettura della validazione.
Il collegamento e la revisione delle uscite descrittive precederanno S1-S4 e l'apertura del sigillo.
Nessun nuovo tilt reale, stima HMI o risultato fisico è stato letto o prodotto per questa verifica.


## Revisione di f12d093 — 20 novembre 2026

Questa sezione aggiorna la revisione di 678ff2f conservata sotto. Fonte esaminata:
`scripts/t3_mwo_analysis.py`, SHA-256 `f0a6acca30df8b1bafebfdc81ee45d82bc47e2bf69b1854dd616b77d30056259`;
riconteggio `scripts/t3_mwo_analysis_recount.py`, SHA-256
`0881aa0f823d4be88317b85b549a750428adef35f3d2018fd192c1cc46b9f766`.

**Esito: i sei interventi sono presenti, ma la validazione lunga richiede ancora le correzioni sotto.**
La disponibilità WL non calcola angoli, le matrici su un solo emisfero e le sensibilità vuote sono gestite,
i valori veri sono richiesti nell'accettazione, il benchmark copre le configurazioni con semi separati.
È presente il nuovo riconteggio indipendente della statistica. Selftest ripetuti: runner 37/37 e riconteggio 4/4.

### 1. Parametri della varianza non finiti: runner e riconteggio li accettano

`row_problems()` controlla beta, SE, limiti e valore vero, ma non `var_a`, `var_b`, `phi`, `kappa`, `sigma_x2`.
Anche il riconteggio li omette dalla validità numerica. La successiva riduzione `max()` può ignorare un NaN
quando non è il primo elemento: non è una verifica che tutti gli scarti siano finiti.

Controesempio riproducibile con `scripts/t3_mwo_variance_review_probe.py`, su un disegno sintetico e 54 righe
(tre per configurazione). Si cambia soltanto `sigma_x2` della seconda riga in NaN, mantenendo gli SE, gli
intervalli e gli indicatori coerenti. Gli hash dei prodotti sintetici vengono aggiornati per isolare il
controllo numerico. Risultato su f12d093:

- `summarise()` restituisce accettazione positiva e nessun problema;
- `check_validation()` restituisce True;
- la ricevuta riporta 8/8, `technical_ok: true`, e afferma di avere ricostruito tutti i 54 SE.

Correzione richiesta prima della griglia: includere tutti i parametri salvati della varianza nei controlli
numerici e verificarne i domini; controllare esplicitamente la finitezza di ogni SE ricostruito e del suo
scarto, mantenendo le righe invalide nei denominatori. La ricevuta non deve diventare positiva se una
ricostruzione fallisce. Il parametro di prova `se_rows` deve inoltre essere incompatibile con la scrittura
di una ricevuta completa, oppure registrare un controllo parziale non utilizzabile dalla catena.

### 2. La catena non verifica tutti i legami e accetta ricevute senza controlli

Controesempio con `scripts/t3_mwo_chain_review_probe.py`: cartelle e ricevute interamente sintetiche;
`committed()` è sostituito con True per verificare il solo contratto dei metadati, senza aggirare Git.
La catena iniziale passa. Cambiando soltanto il META del controllo del disegno, la validazione precedente
resta accettata dalla guardia di `stability`: manca il confronto tra
`validation/META.design_check_meta_sha256` e lo SHA del controllo del disegno corrente.

Il medesimo probe mostra che `validate` non richiede la ricevuta indipendente del controllo del disegno.
Inoltre una ricevuta del catalogo con il solo hash del META, senza `passed` e `total`, viene accettata:
`None == None`. `receipt_ok()` accetta anche `{}` o `passed=total=0` quando non è richiesto un legame META.

Correzione richiesta: richiedere conteggi interi positivi e coerenti, verifiche esplicitamente superate,
assenza di parzialità e legami agli ingressi correnti; rendere necessario il riconteggio del disegno prima
della validazione; verificare il legame validazione → controllo del disegno anche al momento di aprire
il sigillo. Una validazione scientificamente negativa resta distinta da una tecnicamente non valida.

### 3. Perimetro prima delle fasi successive alla validazione

Il via futuro al controllo del disegno e alla validazione non deve valere come via all'apertura del sigillo.
Prima di S1–S4 occorre completare e rivedere anche gli output descrittivi richiesti dal protocollo: fonte
DPD accanto alle epoche di S1, confronto S2 con P1 nel 2010–2012, frazione di esclusi per non isolamento e
d_WL della sensibilità «tutti i record». `s4_table()` attualmente descrive soltanto il campione isolato,
nel quale n_neighbours è zero per costruzione; non ricostruisce questi due ultimi controlli.

### Catalogo R2 e seguito

Verificati sui soli metadati gli hash dichiarati di DESIGN, ATTEMPTS, COVERAGE, MAGNETOGRAMS e LOSSES.
Confermati 5225 record isolati e 5944 complessivi; nessuna discordanza fra giorno DPD e data UTC MWO nei
record o nei tentativi che hanno un magnetogramma. Copertura per ciclo ed emisfero coincidente con la nota
di Claude. SEALED non letto. Durante la revisione è arrivata la ricevuta completa in deaa14f:
13/13, partial false, legata allo SHA del META corrente; nessuna discordanza UTC o di selezione.

Dopo la ricevuta positiva e completa di R2 si può fare il controllo del disegno senza tilt, seguito dal
suo riconteggio. Prima della griglia lunga vanno chiusi i punti 1–2. Nessuna soglia, matrice scientifica,
regola congelata o risultato storico è stata modificata per questa revisione.


Revisione di Codex del commit `678ff2f`, file `scripts/t3_mwo_analysis.py`, SHA-256
`c30549af6bd4dbd9e58a375256700e3b0ede01080ca160049f11f619e1f70360`.
Selftest dell’autore ripetuto: 25/25. Prove dei rilievi soltanto sintetiche. Nessuna misura del catalogo lungo, nessun tilt reale in luce bianca e nessuna
stima HMI nuova. Il codice di Claude resta invariato per consentirgli di applicare le correzioni.

**Esito: la consegna richiede correzioni prima dell'esecuzione sui dati reali.** La costruzione di x₃,
la riduzione delle colonne, la proiezione della rampa e il margine C seguono l'impostazione del protocollo;
le guardie e alcuni percorsi di esecuzione non la rispettano ancora.

I controesempi sono riproducibili con `scripts/t3_mwo_analysis_review_probe.py`, senza leggere i dati reali.

## 1. Disponibilità in luce bianca prima del sigillo

`design_check()` chiama `wl_for_records(..., tilt=False)`, che chiama ugualmente `wl_tilt()` e soltanto dopo
scarta l'angolo. Calcola quindi tilt reali prima della validazione, nonostante il commento e la descrizione
iniziale affermino il contrario. Un controesempio sostituisce `wl_tilt` con una funzione che solleva
`REAL_TILT_CALCULATION_ATTEMPTED`: la chiamata con `tilt=False` la esegue.

Separare il controllo dei requisiti geometrici e delle aree positive dal calcolo dell'angolo. La disponibilità
può verificare le due metà del gruppo, ma non chiamare la funzione che restituisce il tilt. Provare anche
l'assenza della chiamata, non solo che il valore restituito sia NaN.

## 2. I sottoinsiemi di un solo emisfero non funzionano

`reference_epochs()` itera sempre su N e S e applica `min()` anche al conteggio vuoto. `columns()` su un disegno
sintetico del solo Nord termina con `ValueError: min() arg is an empty sequence`. `stability()` costruisce
proprio queste matrici nei due controlli S2 per emisfero: il percorso normale si interromperebbe.

Costruire i riferimenti soltanto per gli emisferi presenti. Gestire separatamente il campione vuoto, che può
comparire in una sensibilità o nel sottoinsieme con luce bianca. Il controesempio `fit_beta3(d.iloc[:0])`
produce lo stesso errore. Un esito non determinato deve essere rappresentato senza un'eccezione accidentale.

## 3. Il sigillo verifica solo la presenza in Git

`read_sealed()` richiede soltanto che la cartella di validazione sia committata. Non verifica una ricevuta del
riconteggio né la lettura della validazione prevista dal §7. Anche `gate_problem()` controlla la conservazione
delle directory, senza collegare i prodotti e le ricevute ai loro hash. Con `committed=True` simulato la
lettura passa immediatamente, senza un altro controllo.

Serve il legame fra disegno, validazione completa, ricevuta indipendente e registrazione della lettura.
Il riconteggio del catalogo deve precedere l'analisi del disegno. Un esito scientificamente negativo della
validazione può portare alla descrizione prevista dal protocollo: non va confuso con un errore tecnico del
riconteggio o con una validazione incompleta. La guardia deve distinguere questi stati.

## 4. Identificabilità e copertura non fermano i percorsi successivi

`_init()` calcola `info` ma non ne controlla `identifiable` prima di costruire g e lanciare la validazione.
La presenza in Git di IDENTIFIABILITY.json con esito negativo non blocca `--validate`. In `stability()`
`info_s` non viene controllato prima del fit S2; C può essere None. `estimate()` accede a beta, se e limiti
anche quando `fit_beta3()` restituisce soltanto `identifiable=False`.

Propagare esplicitamente «non concludente» o «stabilità non determinata» nelle condizioni previste. Non usare
la pseudoinversa per attribuire un coefficiente d'interesse a una matrice in cui quel coefficiente non è
identificabile. Aggiungere prove dei percorsi completi, oltre al test isolato di `reduce()`.

## 5. La validazione accetta righe numericamente non valide

Su una griglia completa di 76 000 righe sintetiche, `summarise()` accetta sia una riga riuscita con SE NaN
sia, separatamente, un verdetto estraneo agli stati previsti. Usa direttamente le colonne covered e lo_above
senza riconciliarle con beta, intervallo e valore vero. Non verifica inoltre che il valore vero salvato sia
la proiezione del disegno usato.

Per ogni riga riuscita verificare campi finiti, SE positivo, intervallo ordinato e compatibile con beta/SE,
stato ammesso e indicatori coerenti con il valore vero. Una riga non valida deve impedire l'accettazione;
non va cancellata dal denominatore. Il riconteggio statistico della consegna 2 deve ricostruire anche questi
controlli e la decisione, senza importare la funzione che la produce.

## 6. Benchmark e provenienza

Il benchmark usa soltanto scenario 0 e replica le stesse 40 unità cinque volte. Non rappresenta la griglia
con componente temporale e non distingue il costo dei diversi scenari. Provare sul pool reale un insieme
stratificato con semi fuori dalla griglia e riportare avvio e lavoro effettivo. Non occorre introdurre un
tetto di durata, che il protocollo attuale non prevede.

`validate()` registra già `start_commit`; invece `write_out()` registra commit e SHA dello script al termine.
Con lavoro contemporaneo può descrivere una revisione diversa da quella caricata dai worker. Registrare
prima della corsa gli hash di script, moduli e ingressi, conservarli negli output e verificarli alla fine.
Il `start_commit` già presente è utile e va mantenuto.

## Seguito

Il giorno UTC è corretto separatamente nella consegna di misura e nel suo riconteggio. Questa revisione
statistica non applica modifiche al file di Claude. Prima del via occorrono correzioni, regressioni sui
controesempi e revisione del riconteggio statistico, che non è ancora presente in questa consegna.
Il superamento del selftest sintetico dell'autore non chiude i percorsi sopra descritti.

Ripresa del 20 novembre: il file statistico è ancora identico alla revisione sopra. Nel frattempo è
comparso il catalogo `f718114`, ma il controllo indipendente dei metadati rileva il difetto UTC
descritto nell'audit collegato. Non usarlo come ingresso della validazione o della stima finché
la misura corretta non è conservata e ricontata. Nessun tilt sigillato letto per questa verifica.

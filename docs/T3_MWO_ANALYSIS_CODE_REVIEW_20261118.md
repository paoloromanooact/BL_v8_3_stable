# Revisione della consegna statistica T3 MWO — 18 novembre 2026

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

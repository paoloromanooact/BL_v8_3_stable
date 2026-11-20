# Revisione della consegna statistica T3 MWO — 18 novembre 2026

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

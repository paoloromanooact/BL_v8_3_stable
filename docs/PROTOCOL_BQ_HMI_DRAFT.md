# BQ-HMI — confronto bayesiano della dipendenza del tilt dall'attività: BOZZA rev. 4

25 novembre 2026, Codex. **Non congelata; nessun fit reale o lettura di risultati bayesiani.**
Priorita operativa aggiornata dall'utente: BQ-HMI, poi BQ-M; C prosegue come preparazione di BT e i piloti SFT
restano in chiusura. Nests in lista ma sospesi. Nessuna serie polare o analisi SINDy entra in questo lavoro.

## 0. Domanda e informazione già nota

Sul campione HMI di T3, quanto i dati distinguono un modello senza termine di attività da uno con pendenza
libera? Le stime P2/P2f e Q1–Q3 sono note: questo progetto è **non cieco**, non una nuova conferma preregistrata
prima dei dati originali. Conserva l'esito T3 precedente «non deciso» e T5 descrittivo.

Un confronto bayesiano non promette un verdetto né rende identificabile un effetto privo di informazione.
Lo scopo è quantificare posteriori, adeguatezza e capacità predittiva sotto ipotesi esplicite.

## 1. Campione, risposta e matrice

- Stessi record primari/both del campione S: valid_bl=1, cicli 24/25, Phi>=1e21 Mx, npos/nneg>=20,
  cycle_state diverso da AMBIGUOUS, attività principale disponibile. Attesi 2485 record, 394 celle CR/emisfero e 42 celle singleton (da ricontare); chiave (HARPNUM,T_REC)
  unica. Un conteggio differente o una chiave cambiata ferma la preparazione, non viene ignorato.
- Risposta esattamente come P2: gamma = sign(lat_mean_deg) * degrees(arcsin(clip(sintilt,-1,1))). Non sostituire
  questa risposta con il semplice tilt assiale: le convenzioni non sono intercambiabili.
- s=sin|lat_mean_deg|, a=A_monthly-1; A da SILSO emisferico mensile normalizzato come P2 sul periodo
  maggio 2010–settembre 2026. Nessuna selezione sulla risposta o sulla grandezza del quenching.
- Quattro colonne s*indicatore(ciclo,emisfero); colonna x3=a*s. CR e famiglie P1e conservate. Dati angolari in gradi.
- Prima della corsa: manifesto delle chiavi e del disegno, input/definizioni/codice con SHA, controllo indipendente
  delle colonne, delle normalizzazioni e del rango. Usare tutti i CR interi fra primo e ultimo, propagando il
  processo temporale anche nei CR senza regioni. Nessuna nuova classificazione di nests.

## 2. Candidati e media proposta

M0: gamma_i = k_(c,h) s_i + u_(CR,h) + b_famiglia + epsilon_i.
MQ: stessa forma, con l'aggiunta beta a_i s_i. beta può avere entrambi i segni.

Le prior degli elementi comuni sono identiche nei due modelli. u descrive la componente condivisa delle regioni
della stessa CR/emisfero, non un errore indipendente per regione. Le famiglie sono quelle P1e già definite,
con il loro carattere candidato; b è un effetto condiviso additivo del tilt. Sensibilità predefinite da fissare
prima della corsa: senza b e campione S8, con gli stessi candidati M0/MQ. Non cercare il sottocampione che dà
la preferenza più netta. Nests esclusi dalla fase attuale; la dipendenza residua non ricostruita è dichiarata.

**Sensibilita temporale obbligatoria e simmetrica:** aggiungere a entrambi i candidati v_(CR,h)*s_i,
con v AR(1) bivariato stazionario distinto da u e a priori indipendente da u, b e beta. Proposta:
sigma_v~half-Normal(20 gradi), z_phi_v,z_kappa_v~N(0,1), trasformazioni tanh come per u.
Non sottrarre a posteriori la proiezione di v sull'attivita: imporrebbe la separazione desiderata.
Queste prior restano da verificare con le prove a priori. Fissare entrambe le scale half-Normal
5 e 20 gradi per sigma_v come sensibilita predefinite, con 20 riferimento della variante v. Sul disegno
esportare separatamente la varianza a priori di beta*a*s e di v*s e le loro proiezioni sul regressore.
Una prior ampia per v puo assorbire il segnale, ma non dimostra in anticipo una preferenza per M0: l'effetto
sulle evidenze e da misurare con sintetici beta!=0,v=0 e beta=0,v!=0 per entrambe le scale.
Non regolare sigma_v sui risultati HMI per ottenere una preferenza. Riportare tutte le varianti. Una variazione lenta del coefficiente di Joy puo
imitare beta: il ranking con/senza v e il recupero sintetico sono parte dei risultati, non una selezione
post hoc della sola variante favorevole. Un allargamento o una forte dipendenza dalle prior e un limite
alla separazione dei contributi, non una prova causale.

## 3. Likelihood ed errori: proposta da rivedere prima del congelamento

L1 principale: likelihood gaussiana **di lavoro**, condizionata a u e b, con
sigma_i = sigma0 exp(q log10(Phi_i/1e21 Mx)). La dispersione individuale comprende evoluzione/morfologia e misura:
non identifica da sola le due componenti. Il flusso è un possibile predittore della dispersione, non un numero
di repliche né un esponente con unità arbitrarie della likelihood.

u_t è un AR(1) bivariato stazionario per CR, con varianza marginale sigma_x², correlazione emisferica kappa e
persistenza phi. Proposta: phi=tanh(z_phi), kappa=tanh(z_kappa), senza il limite REML artificiale di 0,98.
La distribuzione iniziale è stazionaria e la griglia temporale non comprime i CR mancanti. b_f ~N(0,sigma_f²).
Una sola osservazione per famiglia non separa autonomamente sigma_f dalla varianza individuale;
la presenza di famiglie replicate e di eteroschedasticita puo fornire informazione: verificarla sul disegno.
Contare famiglie singleton/replicate, non confondere questi conteggi con le celle CR singleton.
Conteggi preparatori noti senza risposta (9740a7f): 221 CR nel calendario, 2149 famiglie, 1862 singleton e
287 replicate con 623 record. Vincolare input e ricontare prima del fit; non sono 2149 repliche indipendenti.
phi e kappa possono essere negativi; le trasformazioni tanh non impongono persistenza positiva.

L2 predefinita: residui individuali Student-t con nu=4 **fisso**, stessi effetti u/b (e v nella sensibilita)
e stessa deviazione standard sigma_i di L1. La scala della t e sigma_i*sqrt((nu-2)/nu).
Miscela equivalente: lambda_i~Gamma(nu/2, rate=nu/2), epsilon_i|lambda_i~N(0, sigma_i^2*(nu-2)/(nu*lambda_i)).
L1 e L2 si riportano entrambe; non si sceglie la famiglia dopo aver visto beta o il ranking.
La proposta nu-1~Gamma consentirebbe varianza infinita per nu<=2: non e adottata. nu libero o altri valori
richiedono una scelta separata prima dei dati. Integrare le scale nella previsione, mai stimarle usando
le risposte escluse e poi trattarle come note. L'evidenza L2 resta opzionale e subordinata a verifiche.
Il BIC L2 e per ora non stabilito; non riciclare la likelihood gaussiana condizionata alle scale.

**L3 limitata, proposta concreta da verificare:** gamma deriva dal ripiegamento in [-90,90], non
da un troncamento. Definire theta come angolo latente **gia firmato per emisfero**: gamma=F(theta),
F(theta)=180/pi*arcsin(sin(pi*theta/180)). Non moltiplicare di nuovo per sign(lat).
Condizionatamente agli effetti condivisi, theta~N(mu,sigma_i^2), stessa mu di L1. Per -90<gamma<90:

f(gamma|mu,sigma_i) = sum_k [ NormalPDF(gamma+360*k;mu,sigma_i)
                         + NormalPDF(180-gamma+360*k;mu,sigma_i) ].

Unita gradi: Jacobiano assoluto uno su ciascun ramo. Gli estremi hanno misura nulla; dichiarare il
trattamento numerico di valori esattamente +/-90 senza crearvi atomi. Nessuna assunzione sigma<=40:
le prior hanno supporto illimitato. Scegliere immagini con controllo esplicito della coda omessa e somma
log-sum-exp, prova di normalizzazione anche a sigma=150 e 400 gradi. La densita e periodica in mu e
ha ambiguita riflesse: verificare modi/alias, non presumere identificazione del tilt latente.
La formula riproduce il ripiegamento matematico, non dimostra una distribuzione fisica gaussiana del
vero tilt. Beta e un coefficiente **latente** in L3; calcolare E[gamma|x] e la sua proiezione sul disegno
per il confronto con T3. L1/L2 sono likelihood di lavoro sul gamma osservato, con un bersaglio distinto.
Nessuna semplice divisione degli angoli o trasposizione del posteriore fra le tre likelihood.

Il dato gamma esatto ammette i latenti theta=gamma+360*k oppure theta=180-gamma+360*k.
Il passo condizionale di theta e un'estrazione **discreta** di ramo/intero con pesi gaussiani, non un
Gibbs gaussiano continuo. Dati i rami, i coefficienti/effetti possono avere condizionali gaussiane.
Per L2 lambda ha condizionale Gamma solo mantenendo la struttura condizionale richiesta: vedi singleton
nel §7. L3 e una sensibilita predefinita; evidenza e BIC non stabiliti e non richiesti in questa fase.
Prima del congelamento decidere supporto, troncamento adattivo, parametrizzazione e prove dei rami;
nessun fit L3 fino a queste verifiche. Non scegliere L1/L2/L3 dopo averne visto il ranking.

C non è un prerequisito per iniziare la specifica BQ: le coppie ravvicinate non stimano automaticamente sigma_i,
sigma_x o sigma_f. Un futuro uso di C richiede confrontabilità del campione e modello della correlazione fra
errori; non inserire una sigma singola come già calibrata e non assumere la dominanza del rumore intrinseco.

## 4. Prior proposte, proprie e con sensibilità

Proposte numeriche per la revisione, non parametri già congelati:

- k_(c,h) ~ N(0,40²) gradi; nessuna imposizione del segno del coefficiente osservato.
- beta in MQ ~ N(0,10²) gradi per unità di attività. Sensibilita predefinite: deviazioni 2,5; 5; 20; 40 gradi, con 10 principale. Stesse prior comuni in ogni confronto.
- sigma0 ~ half-Normal(30 gradi), sigma_x ~ half-Normal(10 gradi), sigma_f ~ half-Normal(5 gradi).
- q~N(0;1²), con sensibilita N(0;(0,5)²) nella scala log10 del flusso; z_phi,z_kappa~N(0,1).
- Probabilità a priori M0/MQ pari a 1/2, se vengono calcolate probabilità di modello.

Tutte le densità e costanti di normalizzazione entrano nell'evidenza. Il protocollo definitivo conserva anche
la predizione a priori sul disegno HMI. Eventuali modifiche dopo queste prove ma prima del fit reale sono
registrate come sviluppo, senza cancellare le versioni precedenti. Le prior devono essere definite anche
negli stati in cui una componente di varianza è scarsamente identificata.

La scala di attivita HMI resta P2. Per una futura trasformazione a'=c*a, c noto e non nullo,
beta'=beta/c e p'(beta')=|c| p(c*beta'): preservare la distribuzione dell'effetto e l'evidenza.
Se cambia anche il centro, a'=c*a+d, trasformare congiuntamente k'=k-beta*d/c e beta'=beta/c;
non reimporre prior indipendenti su k' e beta'. La scala comune multi-strumento si fissa in BQ-M,
non si inventa ora una nuova normalizzazione per HMI. Registrare fattori e Jacobiani.

## 5. Bersaglio e confronto con T3 storico

Con la media lineare proposta, beta è la variazione del coefficiente di Joy per unità di attività. Inferenza
bayesiana e WLS con pesi Phi sono stimatori diversi: non si convertono l'intervallo P2f o un p-value in un
Bayes factor. Per verificare il bersaglio, proiettare la media strutturale sulla matrice T3 con i pesi storici:
nel caso lineare correttamente specificato la proiezione restituisce beta. Separare la media strutturale dalla
realizzazione della componente temporale e da eventuali effetti di gruppo.

Se si usa un modello angolare non lineare, ricalcolare e nominare il contrasto/proiezione della media predittiva;
non chiamare automaticamente beta un parametro di posizione con un significato diverso. Una rampa del 20%
del coefficiente di Joy non corrisponde automaticamente a beta=-0,2*gamma0: il bersaglio si proietta sul disegno,
come nelle analisi prospettiche. Questo vale anche per il confronto con la letteratura tra cicli.

## 6. Ranking e uscite

Principale: posteriori e confronto predittivo M0/MQ, con incertezza dei punteggi. Riportare P(beta<0|MQ,dati)
e probabilità oltre un effetto operativo fissato prima (bersaglio proiettato), senza confonderle con P(MQ|dati)
o con la probabilità di un meccanismo fisico corretto. Intervalli credibili e diagnostica completi.

**Confronto principale: previsione di blocchi interni al periodo osservato**, non previsione del ciclo futuro.
Dividere i CR interi da primo a ultimo in 10 intervalli contigui, lunghezze che differiscono al piu di uno
(resto assegnato ai primi intervalli). Tutti i record nel blocco sono verifica. Escludere dalla stima anche
11 CR per lato e **tutti** i membri di ogni famiglia presente nella verifica, ovunque siano nel calendario.
Non assegnare tutti i membri al blocco del primo: altererebbe il bersaglio temporale. Ogni record ha un solo
blocco di verifica. Le osservazioni eliminate per famiglia/buffer non entrano nel punteggio di quel blocco.
Controllare prima dei fit supporto di ciclo/emisfero, rango e intervallo di attivita del training; non spostare
i confini usando gamma. Se manca un coefficiente, segnalarne la previsione dominata dalla prior.

Il buffer 11 corrisponde a |phi|^11<0,05 **solo** per |phi|=0,75; non garantisce indipendenza nella prior corrente.
Ripetere lo stesso schema con buffer 22 come sensibilita, riportando la dipendenza dal buffer e la perdita
di training. La densita del blocco integra gli stati correlati condizionati ai soli dati di training:
puo usare tempi precedenti e successivi, quindi e interpolazione temporale e non un vero forecast.
Nessuna garanzia di isolamento per persistenze vicine a uno. Stesso schema per L1/L2 e M0/MQ.
Conteggi preparatori dei blocchi gia noti (9740a7f), senza risposta: blocco 8 contiene A=4,05, training
massimo 3,35; con buffer 22 nel ciclo 25 restano 45 N/61 S. E estrapolazione in attivita anche nel confronto
interno, non eliminarla o ridisegnare il blocco dopo i punteggi. Blocco 5 ha 22 record. Riportare numerosita,
range A, supporto ciclo/emisfero e perdite per ogni blocco; non trattarli come 10 esperimenti equivalenti.
Punteggio: somma delle log-densita congiunte di ciascun blocco e differenze per blocco; non considerare i
10 punteggi come repliche certamente indipendenti per costruire un intervallo artificiosamente stretto.

**Secondario: previsione solo in avanti.** Primi 60% dei CR in training, poi quattro blocchi contigui del 10%,
con arrotondamenti deterministici da esportare nel manifesto. Rimuovere dal training i familiari di verifica;
aggiornare solo dopo il punteggio del blocco. Mostrare separatamente i blocchi del ciclo 25 per cui i k_(25,h)
non hanno supporto nel training: questo confronto include il trasferimento fra cicli e puo essere dominato
dalla prior. Non usarlo da solo come giudizio sulla pendenza dentro il ciclo. L'attivita e covariata data,
non previsione SILSO. Integrare gli stati futuri, senza condizionarli alle risposte di verifica.

Non sommare log-probabilità marginali di record correlati come se fossero indipendenti. Valutare la densità
predittiva congiunta o una fattorizzazione condizionata corretta; controllare l'errore Monte Carlo. Quattro blocchi
non autorizzano da soli una classifica precisa: dare differenze per blocco e incertezza, anche se non distinguibili.

Secondario, solo se il calcolo è verificato: evidenze e Bayes factor con errore numerico e sensibilità alle prior.
Non usare REML o massimi di likelihood come evidenze. Nel caso gaussiano, con covarianza C_psi e prior gaussiana
propria V_theta, l'integrazione dei coefficienti dà y~N(0,C_psi+X V_theta X^T), poi si integra sui parametri psi.
Questa identità fornisce un riferimento indipendente per i casi sintetici; la massa a beta=0 resta distinta
dalla probabilità del segno nel modello continuo.

Per ogni likelihood/struttura annidata verificata, Savage-Dickey e un secondo calcolo possibile:
BF_0Q = p(beta=0|y,MQ)/p(beta=0|MQ), solo se la prior dei parametri comuni sotto M0 coincide con quella
condizionata a beta=0 sotto MQ. Verificare identita, normalizzazioni e indipendenza proposte; non usare una
stima puntuale di densita senza errore Monte Carlo. In L1 integrare analiticamente i coefficienti per
calcolare l'ordinata condizionale e poi mediarla sul posteriore delle covarianze (Rao-Blackwell).
Un controllo che condivide campioni/covarianze non e una validazione completamente indipendente.
Ripetere i fit per le prior di beta prescritte, oppure usare pesi solo con diagnostica di sovrapposizione
ed ESS adeguati e regole fissate prima. Non riusare il posteriore tau=10 per tutte le tau senza controllo.

## 6bis. BIC: controllo secondario, con condizioni di applicabilita

Aggiunto su richiesta dell'utente prima di qualsiasi fit BQ. Nel caso regolare classico:

BIC = -2 ell_ML(theta_hat; y) + k log n. BIC piu basso e preferito.
Definizione del contrasto: Delta BIC = BIC_MQ - BIC_M0; negativo favorisce MQ.
Sotto le condizioni dell'approssimazione, log BF_Q0 e circa -Delta BIC/2, non un'identita o una probabilita
che il quenching sia fisicamente vero. Le etichette convenzionali 2/6/10 non sono soglie calibrate per questi
cataloghi e non diventano una regola di verdetto. Le ipotesi del BIC non si riducono a una generica prior larga.

**Likelihood:** stimare per ML la densita dei medesimi record, con tutte le normalizzazioni e la covarianza
specificata, integrando gli effetti casuali u e b secondo la loro distribuzione. I coefficienti fissi si
massimizzano, non si integrano con la loro prior nel calcolo ML. Questa likelihood marginale rispetto agli
effetti casuali non e l'evidenza bayesiana, che integra anche coefficienti e iperparametri con le prior.
Non usare REML per il confronto di effetti fissi diversi, MAP, picchi posteriori, BLUP condizionati agli
stessi dati come se fossero fissi, o la log-likelihood di regioni assunte indipendenti.

**k:** dimensione nominale dei parametri stimati della likelihood marginale, non numero di latenti e non
numero effettivo della complessita predittiva. Per la proposta gaussiana attuale, se tutti sono identificabili:
4 coefficienti ciclo-emisfero + 6 parametri di covarianza/dispersione (sigma0,q,sigma_x,phi,kappa,sigma_f),
quindi k0=10 e kQ=11. Registrare l'elenco effettivo; una likelihood o una struttura diversa cambia il conteggio.
Non aggiungere un parametro per ogni stato CR o famiglia dopo averli gia integrati.
La variante con v aggiunge sigma_v,phi_v,kappa_v: k0=13, kQ=14 se identificati, e cambia anche la
verifica delle condizioni asintotiche. I conteggi 10/11 non valgono per ogni variante.

**n e asintotica:** non scegliere arbitrariamente regioni, CR o blocchi per ottenere la classifica voluta.
La dipendenza non vieta ogni BIC, ma richiede una giustificazione del regime di crescita dell'informazione.
Nei modelli misti i parametri possono richiedere penalita differenti; i blocchi temporali non sono
indipendenti solo perche li si chiama blocchi. Prima del congelamento della regola BIC documentare quale
approssimazione si applica al modello con CR/famiglie e perche; non trasferire automaticamente al nostro
modello incrociato una formula derivata per gruppi indipendenti.

Se tale giustificazione manca, marcare il BIC come **non stabilito per il modello**. Si possono riportare
-2 ell_ML + k log(N_regioni) e l'analogo con N_CR solo come **sensibilita euristica della penalizzazione**,
con quei nomi: non due Bayes factor o due BIC entrambi giustificati. Lasciare invariati likelihood, dati e k;
non aggregare i dati in un solo ramo fingendo di confrontare la stessa likelihood.

**Cancellazione delle condizioni regolari:** varianze al bordo, parametri non identificati, correlazioni
quasi unitarie e ottimi non verificati richiedono uno stato esplicito. Per esempio, sigma_x=0 rende phi/kappa
non identificati; sigma_f e sigma0 possono essere poco separabili con molte famiglie singleton. Il solo
conteggio k=10/11 non sana questi problemi. Verificare ML, curvature/identificabilita e precisione numerica;
non convertire meccanicamente Delta BIC in probabilita di modello quando l'approssimazione non e giustificata.

**Prodotto:** tabella con modello, hash del campione, tipo di likelihood, ell_ML, elenco dei parametri/k,
regola di penalizzazione e suo razionale, n/growth regime, BIC se applicabile, stato ML/bordi/identificabilita,
Delta BIC e motivo di eventuale mancato calcolo. Verifica indipendente su casi gaussiani noti prima dei dati.
Non e previsto alcun calcolo reale di BIC finche likelihood e regola non sono congelate.

Riportare separatamente confronto predittivo, evidenze con prior proprie (se calcolabili) e BIC diagnostico.
I primi due restano quelli del §6. Le discordanze possono riflettere obiettivi diversi, prior, asintotica,
specificazione o errori numerici: non dimostrano automaticamente che i dati non distinguano i modelli.
Le conclusioni fisiche restano condizionate anche all'adeguatezza dei candidati.

Riferimenti metodologici primari consultati:
- Schwarz (1978), *Estimating the Dimension of a Model*, Ann. Stat. 6, 461–464:
  https://www.andrew.cmu.edu/user/kk3n/simplicity/schwarzbic.pdf
- Delattre e Poursat, *An iterative algorithm for joint covariate and random effect selection in mixed effects
  models*, §2.2: https://arxiv.org/html/1612.02405 (consultato il 25 novembre 2026).

## 7. Prove, diagnostica e catena

Prima dei dati: casi con beta noto nullo/negativo/positivo, famiglie note, AR(1) forte, salti di livello,
eteroschedasticità e dipendenza non modellata. Controlli di implementazione e calibrazione da simulazione sotto
le prior sono distinti dai controlli di robustezza a generatori diversi. Non estendere a BQ la validazione di M.
Obbligatori: coefficiente k(t) variabile con fase senza beta, con somiglianza crescente ad a(t); nulli con
code t4; beta vero senza v con v attivo, v senza beta, entrambe le scale 5/20;
normalizzazione/alias di L3 e campionamento discreto dei rami; confondimento sigma_f/sigma0; cicli assenti nel training. Con beta e k(t)*s indistinguibili i test
devono rivelare sensibilita/ambiguita, non imporre un recupero impossibile. Riportare frequenze di preferenza
errata sotto ogni generatore con incertezza Monte Carlo; generatori e numerosita da fissare prima dei fit reali.

Campionamento: proposta quattro catene, Rhat<=1,01 ed ESS bulk/tail>=400 per beta e parametri di scala/correlazione,
nessuna divergenza irrisolta se si usa HMC, diagnostica specifica del kernel altrimenti; controllare anche ridotte identificabilità e sensibilità alle inizializzazioni.
Impostazioni, semi effettivi, benchmark e regole di estensione delle catene da congelare con l'implementazione;
nessun limite di durata delle corse imposto da questa bozza. L'adattamento Metropolis e confinato al
warm-up; la fase salvata usa un kernel fissato. Proposte di estensione, numero massimo di estensioni e
stati di arresto tecnico devono essere fissati con il runner prima del congelamento operativo.
Con diagnostica insufficiente: esito tecnico,
non una preferenza per il modello che ha campionato meglio. Densità marginali: controllo indipendente e
precisione richiesta da fissare prima del confronto reale.

Controlli predittivi: residui/medie per CR ed emisfero, code, vincoli angolari, gruppi, relazione con flusso e
attività. Possono risultare inadeguati entrambi i candidati. Input/codice/protocolli con SHA, albero e input
conservati, output prima della lettura, riconteggio e rapporto separato. Nessun fit reale finché le scelte
aperte sono chiuse e codice/likelihood verificati. Nessuna libreria nuova installata per scrivere la bozza.

**Ambiente proposto:** numpy/scipy locali possono bastare, ma un campionatore proprio non e approvato solo
per questo. Woodbury/determinante e precisione AR(1) verificati contro Cholesky densa su sintetici; registrare
Jacobian dei parametri trasformati e differenza fra likelihood marginale ML e densita integrata bayesiana.
In L1 integrare le famiglie singleton esattamente nella diagonale, +sigma_f^2: non occorrono latenti
singleton nel Woodbury. Con u: 442+287=729 dimensioni; con u e v: 884+287=1171, sul disegno noto.
In L2, condizionatamente a lambda, la diagonale singleton e sigma_i^2*(nu-2)/(nu*lambda_i)+sigma_f^2.
NON e una t con SD sqrt(sigma_i^2+sigma_f^2). Integrando b_single, la condizionale di lambda non e piu
la semplice Gamma coniugata: o mantenere b_single per quel Gibbs o aggiornare lambda con kernel corretto.
In L3 si possono sommare le varianze gaussiane singleton nel theta latente, poi applicare il ripiegamento.
Non sommarle a una varianza gaussiana del gamma osservato.
Benchmark aee64df: accordo denso/Woodbury su risposte sintetiche e struttura reale, non verifica del sampler.
La stima circa 2 h e per un numero ipotizzato di valutazioni del caso base: slice, quattro catene, CV,
prior multiple e likelihood diverse possono richiedere molto di piu. Benchmark per valutazione != durata.

Proposta di campionatore: slice per coordinate trasformate, larghezze adattate solo nel warm-up, con stepping-out
/shrinkage verificato e Jacobiani. Numero di passi/espansioni, gestione dei fallimenti e composizione per
coefficienti/effetti da fissare con il codice. Proposta di estensione: lunghezza base e raddoppi fino a 4 volte
la base, poi stato tecnico, non nuove prior o modelli; base e semi da congelare prima dei dati. L2/L3 richiedono
i kernel corretti sopra, non un generico "Gibbs gaussiano".
Bridge sampling opzionale: controllo su integrali gaussiani noti, quadratura ridotta e Savage-Dickey con
errori numerici; separare campioni usati per costruire la proposta e per stimare l'integrale. Se i controlli
falliscono, nessuna evidenza pubblicabile e nessun vincitore per difetto tecnico. Nessuna installazione ora.

## 8. Estensione BQ-M: requisiti prima del codice multi-strumento

- Inventario delle sovrapposizioni affidato a Claude; questa bozza non lo duplica. I cataloghi non si mediano.
- Una likelihood si fattorizza condizionatamente ai latenti e alle dipendenze dichiarate, non sulle misure
  marginali considerate indipendenti. Stessa regione a ore diverse o con prodotti diversi richiede un modello
  dell'evoluzione e degli operatori di misura, non l'identità imposta di ogni tilt osservato.
- DPD luce bianca è un confronto relativo, non uno standard assoluto magnetico. In generale lo scarto osservato
  è b_MWO(A,t)-b_DPD(A,t)+differenza fisica fra misure: non identifica b_MWO separatamente senza ulteriori ipotesi.
  Lo stesso segnale solare può essere confuso con una deriva di strumento; un ponte non garantisce che si separino.
- Fissare un riferimento risolve una convenzione di scala/offset, non dimostra che esso misuri la verità fisica.
  Parametri solari comuni e loro trasportabilità fra popolazioni sono ipotesi da controllare, non risultati.
- Simulazioni con trasformazioni che lasciano invariata la likelihood devono riconoscere la non identificabilità.
  Se posteriori/ranking sono governati dalle prior di deriva, dichiararlo; consentire «non identificato».
- Dipendenza dentro il ciclo e tra ampiezze di cicli sono due bersagli distinti. I cicli 20 e 24 in MWO sono
  parziali e HMI copre una parte del 25: non contare cinque cicli completi e indipendenti.

BQ-M richiede una specifica e validazione del calcolo proprie dopo BQ-HMI; non riabilita T3 MWO o T5.

## 9. Consegna per la revisione incrociata

Claude rivede: campione/risposta e identificabilità; famiglia della likelihood angolare e significato di beta;
prior proposte e loro predizione; trattamento delle famiglie; schema della verifica temporale ed evidenze;
ambiente/semi/costi; likelihood ML, conteggio dei parametri e applicabilita della penalita BIC (§6bis).
Poi si congela il testo prima del fit. Nests e nuovi dati complementari restano sospesi.

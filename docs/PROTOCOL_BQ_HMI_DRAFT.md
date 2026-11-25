# BQ-HMI — confronto bayesiano della dipendenza del tilt dall'attività: BOZZA rev. 2

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
  cycle_state diverso da AMBIGUOUS, attività principale disponibile. Attesi 2485 record; chiave (HARPNUM,T_REC)
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

## 3. Likelihood ed errori: proposta da rivedere prima del congelamento

Prima versione proposta: likelihood gaussiana **di lavoro**, condizionata a u e b, con
sigma_i = sigma0 exp(q log10(Phi_i/1e21 Mx)). La dispersione individuale comprende evoluzione/morfologia e misura:
non identifica da sola le due componenti. Il flusso è un possibile predittore della dispersione, non un numero
di repliche né un esponente con unità arbitrarie della likelihood.

u_t è un AR(1) bivariato stazionario per CR, con varianza marginale sigma_x², correlazione emisferica kappa e
persistenza phi. Proposta: phi=tanh(z_phi), kappa=tanh(z_kappa), senza il limite REML artificiale di 0,98.
La distribuzione iniziale è stazionaria e la griglia temporale non comprime i CR mancanti. b_f ~N(0,sigma_f²).
I gruppi singleton non forniscono informazione distinta su sigma_f e sigma0: verificarne la separabilità.

**Scelte non da nascondere:** gamma deriva da una trasformazione limitata a [-90,90]. La normale è un'approssimazione,
non una densità esatta della misura angolare. Prima del congelamento, controllare predizioni a priori e definire
una sensibilità con likelihood angolare/limitata coerente; non scegliere la famiglia dopo aver visto quale
favorisce il quenching. Una likelihood normalizzata su supporto diverso può anche cambiare il significato del
parametro di posizione rispetto alla media: la mappa verso il bersaglio deve essere esplicita.

C non è un prerequisito per iniziare la specifica BQ: le coppie ravvicinate non stimano automaticamente sigma_i,
sigma_x o sigma_f. Un futuro uso di C richiede confrontabilità del campione e modello della correlazione fra
errori; non inserire una sigma singola come già calibrata e non assumere la dominanza del rumore intrinseco.

## 4. Prior proposte, proprie e con sensibilità

Proposte numeriche per la revisione, non parametri già congelati:

- k_(c,h) ~ N(0,40²) gradi; nessuna imposizione del segno del coefficiente osservato.
- beta in MQ ~ N(0,10²) gradi per unità di attività. Sensibilità predefinite: deviazione 5 e 20 gradi.
- sigma0 ~ half-Normal(30 gradi), sigma_x ~ half-Normal(10 gradi), sigma_f ~ half-Normal(5 gradi).
- q~N(0;(0,5)²) nella scala log10 del flusso; z_phi,z_kappa~N(0,1).
- Probabilità a priori M0/MQ pari a 1/2, se vengono calcolate probabilità di modello.

Tutte le densità e costanti di normalizzazione entrano nell'evidenza. Il protocollo definitivo conserva anche
la predizione a priori sul disegno HMI. Eventuali modifiche dopo queste prove ma prima del fit reale sono
registrate come sviluppo, senza cancellare le versioni precedenti. Le prior devono essere definite anche
negli stati in cui una componente di varianza è scarsamente identificata.

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

Per la previsione: proposta di quattro blocchi futuri contigui sul calendario CR, dopo un primo 60% di CR di
addestramento; blocchi successivi di 10%, aggiornamento solo dopo la valutazione del blocco precedente. Le famiglie
del blocco di verifica non possono contribuire con altri membri alla stima. Definire il trattamento dei gruppi
che attraversano il bordo prima della corsa. Le attività SILSO sono covariate date: non è una previsione di SSN.
Integrare i futuri stati temporali e gli effetti nuovi, senza usare le risposte di verifica per ricostruirli.

Non sommare log-probabilità marginali di record correlati come se fossero indipendenti. Valutare la densità
predittiva congiunta o una fattorizzazione condizionata corretta; controllare l'errore Monte Carlo. Quattro blocchi
non autorizzano da soli una classifica precisa: dare differenze per blocco e incertezza, anche se non distinguibili.

Secondario, solo se il calcolo è verificato: evidenze e Bayes factor con errore numerico e sensibilità alle prior.
Non usare REML o massimi di likelihood come evidenze. Nel caso gaussiano, con covarianza C_psi e prior gaussiana
propria V_theta, l'integrazione dei coefficienti dà y~N(0,C_psi+X V_theta X^T), poi si integra sui parametri psi.
Questa identità fornisce un riferimento indipendente per i casi sintetici; la massa a beta=0 resta distinta
dalla probabilità del segno nel modello continuo.

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

Campionamento: proposta quattro catene, Rhat<=1,01 ed ESS bulk/tail>=400 per beta e parametri di scala/correlazione,
nessuna divergenza irrisolta; controllare anche ridotte identificabilità e sensibilità alle inizializzazioni.
Impostazioni, semi effettivi, benchmark e regole di estensione delle catene da congelare con l'implementazione;
nessun limite di durata delle corse imposto da questa bozza. Con diagnostica insufficiente: esito tecnico,
non una preferenza per il modello che ha campionato meglio. Densità marginali: controllo indipendente e
precisione richiesta da fissare prima del confronto reale.

Controlli predittivi: residui/medie per CR ed emisfero, code, vincoli angolari, gruppi, relazione con flusso e
attività. Possono risultare inadeguati entrambi i candidati. Input/codice/protocolli con SHA, albero e input
conservati, output prima della lettura, riconteggio e rapporto separato. Nessun fit reale finché le scelte
aperte sono chiuse e codice/likelihood verificati. Nessuna libreria nuova installata per scrivere la bozza.

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

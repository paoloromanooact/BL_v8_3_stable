# HMI: sensibilità della misura BL a LOS, risoluzione e rumore — bozza H1

**BOZZA NON CONGELATA — 2026-11-13.** Richiesta dell'utente: preparare prima il
protocollo, poi revisione e congelamento, codice e prove sintetiche, infine esecuzione.
Questo documento propone scelte concrete da rivedere. Nessuna selezione è stata
eseguita, nessun nuovo segmento interrogato o scaricato, nessuna risposta trasformata
calcolata. Tutti i numeri operativi sotto sono proposte, non soglie fisiche validate.
P1, P2 e P2f restano i riferimenti storici; non vengono modificati o rieseguiti.

## 1. Domanda e prodotto finale

**Domanda:** sul disegno HMI, le approssimazioni LOS e le degradazioni simulate
cambiano tilt, flusso, sorgente e dipolo in modo dipendente dall'attività solare,
capace di contaminare la ricerca del quenching?

Confronti appaiati: stessa HARP, stesso record primario, stessi dati di attività,
con diversa rappresentazione del campo. Br HMI è il riferimento strumentale, non
la verità fisica. Lo studio misura differenze fra pipeline simulate; non misura
nuovamente il quenching e non riproduce integralmente MDI.

Prodotti: elenco congelato delle HARP, inventario e hash degli input, tabella per
HARP e trasformazione, perdite di confrontabilità, differenze e diagnostiche in
funzione dell'attività, figure e relazione con esiti «compatibile con il budget»,
«supera il budget» o «inconclusivo». Anche un esito favorevole richiede dopo un
confronto con MDI reale e una valutazione separata del beneficio statistico.

## 2. Non cecità e scelte già informate dai dati

Sono già noti P1, BARD/P3, sensibilità, diagnosi A–D, pilota/validazione P2f e il
risultato reale T3 (non deciso). Le 120 HARP dominanti/controlli e le 30 schede 25S
sono già state esaminate. Il presente sviluppo è dichiaratamente non cieco.
La griglia degli effetti di P2f e i casi complessi informano le proposte sotto;
non verranno scelti campioni o tolleranze per migliorare il risultato T3.

Le classi visive non diventano esclusioni. Una HARP con più NOAA può essere un
complesso fisico: l'esperimento conserva questo limite della misura per HARP.

## 3. Campione proposto: fino a 64 estratte e 16 prove di stress

### 3.1 Campione principale

Base: i 2485 record primari HARP del campione S con A_monthly finita, ricostruiti
con il codice/dati usati nell'applicazione T3 su 42fcd01. Conservarne le chiavi
HARPNUM,T_REC e gli hash di catalogo, selezione, SILSO e codice; riprodurre il
conteggio e confrontare il disegno con quello P2f prima di interrogare JSOC.

Strati: ciclo×emisfero (24N,24S,25N,25S) × attività bassa/alta × flusso basso/alto
× complessità di catalogo (NOAA_NUM≤1 contro ≥2). Le due mediane sono calcolate
separatamente sulla base di ciascun ciclo×emisfero, senza usare tilt o S_BL;
valori uguali alla mediana assegnati al livello basso. Sono covariate di disegno,
non risultati di un nuovo test. Nessuna pretesa che NOAA_NUM identifichi il numero
esatto di bipoli fisici.

Per ognuno dei 32 strati estrarre due HARP senza reimmissione, dalla lista ordinata
HARPNUM,T_REC. Un solo generatore default_rng(26000000), gruppi nell'ordine sopra,
poi attività bassa/alta, flusso basso/alto, complessità bassa/alta. Se uno strato
ha meno di due elementi, prenderli tutti, registrando lo strato vuoto/scarso;
nessun riempimento opportunistico da altri strati. Dimensione massima 64.
Probabilità d'inclusione pi_i=min(2,N_strato)/N_strato registrata per ogni estratta.

### 3.2 Prove di stress

Per ciascun ciclo×emisfero, le quattro HARP con |S_BL| più grande nella base S,
con pari merito risolti per HARPNUM,T_REC. Fino a 16, in parte già note. Unire
senza duplicare i download: una HARP estratta e dominante mantiene entrambi i
ruoli; totale di record distinti ≤80. I casi di stress non entrano come campione
probabilistico nelle stime pesate del §7; si riportano singolarmente.

### 3.3 Copertura e acquisizione

Prima dei nuovi campi: salvare lista, strati, numerosità, pesi e hash in un commit.
Inventariare latitudine, attività, flusso, date e geometria dell'osservatore già
nei metadati. La posizione dei primari vicino al meridiano limita il dominio di μ:
questa prova non rappresenta automaticamente il lembo né le fasi della vita di
ogni regione. μ pixel per pixel è calcolato dalla WCS e dalla posizione finita
dell'osservatore, non solo dalla longitudine e non dal centro della patch.

Download tentato SOLO sulle chiavi congelate, prodotti definitivi allo stesso
T_REC: Bt,Bp e magnetogram da hmi.sharp_cea_720s; magnetogram nativo da
hmi.sharp_720s per il ramo ottico. Br,bitmap e relativi metadati locali P1 si
conservano byte-identici. Inventario preliminare di segmenti, unità, QUALITY,
WCS, tempi effettivi e disponibilità prima del download. Mai sostituire un record
con il tempo vicino o una HARP «simile». Assenze registrate, nessuna sostituzione.

## 4. Rami del confronto e quantità mantenute fisse

| Ramo | Campo usato nella misura | Che cosa distingue |
|---|---|---|
| R0 | Br HMI P1 sulla CEA originale | riferimento e controllo di riproduzione |
| R1 | LOS proiettato dal vettore HMI, diviso per μ sulla griglia originale | approssimazione radiale, a inversione comune |
| R2 | magnetogram LOS HMI misurato, diviso per μ sulla griglia originale | aggiunge la differenza fra algoritmi LOS e vettoriale |
| R3 | LOS nativo HMI con sola integrazione sui pixel finali, poi CEA 0,12° e divisione per μ | campionamento/rimappatura, con specifica comune |
| R4 | come R3 con PSF aggiuntiva, senza nuovo rumore | effetto della risposta spaziale simulata |
| R5 | come R4, con rumore aggiunto secondo §5 | sensibilità a due livelli e due covarianze di rumore |

R1 deve usare Br,Bt,Bp con i loro segni e versori eliografici; Btheta è positivo
verso sud. La LOS è la proiezione verso l'osservatore, con stessa convenzione del
segmento magnetogram. Non identificare LOS vettoriale e LOS magnetografico.

Congelare per HARP il ciclo e l'emisfero P1, il record, A_monthly e la sua
normalizzazione HMI. Una variazione della latitudine misurata non deve cambiare
silenziosamente il ciclo: un'eventuale assegnazione diversa va solo registrata
come diagnostica separata. Leading e Hale ricalcolati con il ciclo fissato.

La maschera spaziale è l'impronta della bitmap P1≥33, mantenuta fissa. Soglia sul
campo radiale/proxy: |B|≥100G, massimo assoluto 10000G, come P1. Per μ≤0 o pixel
non finiti: nessuna divisione; registrare area esclusa. Dominio candidato μ≥0,8
sulla maschera; le parti fuori dominio non si tagliano silenziosamente: confronto
principale non disponibile per quella HARP, con motivo e quota interessata.
Questa soglia è una proposta da rivedere prima del congelamento.

Sulla griglia grossa la frazione coperta di ciascun pixel e la sua area devono
entrare nei pesi: non moltiplicare il campo per la frazione e poi confrontarlo
con100G, perché cambierebbe la soglia. Riportare separatamente la perdita di
risoluzione delle polarità. Il filtro20pixel di P2 NON si copia sui pixel grossi:
si registra l'area fisica sopra soglia per polarità, confrontata con20pixel della
CEA fine. Sono diagnostiche di eleggibilità, non una nuova applicazione P2f.

## 5. Modello di degradazione: proposta e limiti da chiudere in revisione

Ordine proposto R4/R5: LOS osservato nella geometria nativa → convoluzione nel
piano del cielo → integrazione sul campionamento bersaglio → rumore sul dato
campionato → rimappatura CEA → divisione per μ bersaglio → misura. Registrare
kernel, matrici/interpolazioni, aree e gestione dei margini. Non assumere che le
operazioni commutino; niente semplice salto di un pixel ogni quattro.

**PSF proposta:** gaussiane circolari di FWHM effettiva HMI=1″ e bersaglio=4″;
kernel aggiuntivo di FWHM sqrt(4²−1²)″. Sono un modello operativo approssimato,
non la PSF strumentale MDI misurata. Pixel bersaglio di2″ nel piano del cielo,
poi CEA0,12°; conservare il riferimento della griglia e la fase del campionamento.
Proposta: origine della griglia bersaglio allineata al riferimento WCS osservatore,
non ricentrata su una macchia per ottimizzare l'accordo.

Margine richiesto: almeno5sigma del kernel oltre il dominio analizzato. Se il
ritaglio nativo non offre contesto sufficiente, niente riempimento a zero o
riflessione del bordo: registrare il ramo non disponibile. Un eventuale download
di contesto full-disk richiede un emendamento e un budget dichiarato prima.

**Rumore candidato:** RMS26,4G (MDI1min) e16,2G (MDI5min), con due scenari di
covarianza sul piano bersaglio: indipendente oppure gaussiana con lunghezza di
correlazione di un pixel bersaglio (definizione kernel da fissare nella specifica).
Questi scenari non ricostruiscono il leakage p-mode o la sua distribuzione reale.

Il rumore HMI esiste già: usare un modello HMI con RMS6,3G nel nativo e propagare
la sua covarianza attraverso gli operatori. Aggiungere soltanto la componente
necessaria per raggiungere la covarianza bersaglio. Se la differenza di covarianza
non è semidefinita positiva, lo scenario non è definito: stop, non troncare gli
autovalori senza dichiararlo. Il modello di partenza è un'approssimazione e
richiede revisione:6,3G non è una misura per ogni pixel di questo campione.

20 repliche per HARP e scenario, stessi numeri casuali di base per confronti
appaiati compatibili. SeedSequence con entropia26000001 e spawn_key
(HARPNUM,indice_record_congelato,scenario,replica); nessun riuso ambiguo di semi.
Mantenere separate dispersione fra repliche e variabilità fra HARP. La cadenza
96min e l'integrazione1/5min NON vengono simulate da una sola mappa HMI720s:
il limite temporale resta esplicito e sarà oggetto del confronto MDI reale.

Nessun fattore1,40 o intercetta−0,18 applicato per costruire questi rami. Si resta
sulla scala HMI: una riscalatura MDI richiede il confronto reale successivo.

## 6. Quantità registrate, inclusi i fallimenti

Per ogni record, ramo e replica: Φ± eΦtotale, centroidi sferici,d,λ,tilt e sua
differenza assiale modulo180°, leading,Hale,S_BL,D,D_bal,D*=s_ciclo D_bal,
η=D*/Φ e S_BL/Φ (unità diverse); area e conteggio per polarità, sbilancio,
qualità, dominioμ e copertura della maschera. Stato esplicito: possibile,
impossibile per polarità assente, fuori dominio, input mancante o errore numerico.
Mai sostituire un fallimento con misura zero o cancellarlo dall'inventario.

Per tilt riportare differenza assiale e anche γ=sign(λ)asin(sinα), quella di T3,
separatamente: una differenza modulo180° non deve nascondere cambi di Hale o di
ramo della trasformazione T3. Non aggiornare real_T3 o scegliere varianti dal
loro apparente accordo con la pendenza osservata.

Differenze assolute, relative solo con denominatore non nullo, cambi di segno,
quote di flusso e di |S_BL| dei confrontabili e dei non confrontabili. Aggregati
firmati e somma dei moduli distinti; le prove di stress restano riconoscibili.
Nessuna somma del campione è chiamata somma dell'intero ciclo. Nessuna Φ daLOS
è sostituita al flusso P1 nelle ponderazioni del confronto principale.

## 7. Legame con il quenching: diagnostiche e budget proposti

Nel campione principale confrontabile, per ciascun ramo, stimare una pendenza
DIAGNOSTICA del cambiamento Δγ=γ_ramo−γ_R0 rispetto ad(A−1)sin|λ_R0|, con gli
stessi quattro termini ciclo×emisfero moltiplicati per sin|λ_R0|. Pesi Φ_R0/pi_i.
Non è una seconda stima del quenching reale: descrive l'alterazione del modello
indotta dal ramo simulato, condizionatamente al campione e alla sua copertura.

Perη, riportare il cambiamento controA con intercette ciclo×emisfero, stesso peso
di riferimento dichiarato; è una diagnostica regionale, NON il test T5 per celle.
Le stime non sono confrontate con il β reale per scegliere o correggere i rami.
L'inclusione probabilistica non recupera automaticamente le HARP perse: niente
imputazione o riponderazione delle mancate misure come se mancassero a caso.

Intervalli descrittivi95% mediante2000 bootstrap a famiglie candidate P1e, mai a
pixel o repliche; le repliche di rumore si mediano dentro ciascuna HARP prima del
bootstrap. Riportare la numerosità effettiva delle famiglie; eventuali famiglie
che attraversano strati si ricampionano insieme. La dipendenza temporale fra
famiglie diverse non è coperta da questa scelta: intervalli NON validati,
nessun test inferenziale o dichiarazione di equivalenza. Sensibilità descrittiva
ulteriore a blocchi di CR da definire prima del congelamento se richiesta.

**Budget di misura candidato:** un quarto dell'effetto di riferimento0,2del
protocolloP2f, cioè0,05×24°=1,2° per unità di attività per la pendenza diΔγ e
0,05×eta_bar per quella diΔη (eta_bar=3,56e−25G/Mx). È una tolleranza di
pianificazione da discutere, NON una soglia universale o derivata dalla potenza.

Proposta di lettura PER OGNI ramo/scenario (nessuna scelta del migliore):
- intervallo descrittivo interamente nel budget: «compatibile col budget nel
  campione e nel modello simulato», non equivalenza dimostrata;
- intervallo interamente fuori: «supera il budget nella diagnostica»;
- altrimenti: «inconclusivo».
Se mancano rami, copertura o rango del disegno, esito complessivo inconclusivo,
non successo. Questa lettura non è ancora pronta per un'accettazione formale:
intervalli e dipendenze richiedono la decisione D4 sotto.

## 8. Controlli, arresto e costo

Prima delle risposte nuove: congelare protocollo e lista campione; poi codice,
prove sintetiche su campi uniformi/radiali, geometria obliqua, passaggio ai±180°,
conservazione di area e flusso firmato nell'integrazione, maschera frazionaria,
assenza di polarità, μ, kernel e rumore. Un campo radiale sintetico deve dare
LOS=μBr e recuperareBr con divisione punto per punto prima della degradazione.
Verificare unità/versori con tolleranze numeriche fissate nel codice e revisionate
prima di eseguire mappe reali. R0 deve riprodurre P1 entro precisione numerica
esplicitamente fissata; un fallimento blocca i rami successivi.

Esecuzione da commit pulito, una volta con configurazione registrata. SHA256 di
protocollo, input, lista, codice e ambiente in ogni output. File originali
immutati; risultati nuovi separati, controllo indipendente prima di leggere le
sintesi. Difetti scoperti dopo un esito: conservare run fallito, emendamento,
dichiarazione non cieca e nuova esecuzione esplicitamente delimitata.

Limiti di spesa proposti: prima inventario, poi preventivo da dimensioni dei
segmenti; massimo2GB nuovi dati e2ore di calcolo su4processi, senza installare
nell'ambiente P2f. Questi sono tetti operativi, NON una stima misurata. Se il
preventivo supera il tetto, arresto prima del download; nessuna riduzione del
campione dopo aver visto risposte. Salvare avanzamento/risultati parziali se si
supera il tempo; niente aumento automatico del budget.

## 9. Decisioni da chiudere prima del congelamento

| ID | Decisione proposta | Che cosa serve per chiuderla |
|---|---|---|
|D1|64estratte stratificate più16stress, solo primariS|verifica di copertura senza nuove risposte e revisione delle numerosità|
|D2|dominioμ≥0,8 e maschera spaziale P1 fissa|decidere trattamento di patch estese, margini e frazioni d'area; nessun trackerTARP simulato|
|D3|PSF gaussiana, livelli/covarianze del rumore di§5|specifica riproducibile degli operatori, stadio del rumore, griglia e positività della covarianza; non sono caratteristicheMDI misurate|
|D4|pendenze diagnostiche, bootstrap e budget0,05della scala|decidere se mantenerle solo descrittive oppure progettare/validare una regola di accettazione prima di usarle come porta alla faseMDI|
|D5|20repliche,2GB,2ore|preventivo dei dati e prova tecnica su sintetici, senza leggere nuove risposte reali|

**Stato finale della bozza:** una proposta concreta per revisione, con cinque
scelte aperte. Nessun download, codice dell'esperimento o calcolo autorizzato dal
solo deposito della bozza. Il passo seguente è risolvere D1–D5 e congelare il
protocollo, non passare direttamente alle mappe.

## 10. Fonti e limiti di attribuzione

Studio locale `MDI_SMARP_FEASIBILITY.md` versione d96f6ec e revisione esterna.
[Sun, nota sulle coordinate SHARP](https://arxiv.org/html/1309.2392): distinguere
rimappatura e trasformazione del vettore.
[Bobra et al.2014](https://arxiv.org/html/1404.1879), tabellaA.8: magnetogramCEA
rimaneLOS. [Hoeksema et al.2014](https://arxiv.org/html/1404.1881),§7.2.3:
algoritmoLOS e inversione possono differire.
[Liu et al.2012](https://link.springer.com/article/10.1007/s11207-012-9976-x):
valoriLOS e rumore richiamati nello studio; nessuna PSF gaussiana o covarianza
esatta di questo protocollo è attribuita al loro articolo.
Tutte le scelte di campione,budget,repliche,PSF e criteri qui sono nostre proposte.

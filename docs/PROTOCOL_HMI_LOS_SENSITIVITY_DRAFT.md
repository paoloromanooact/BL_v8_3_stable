# HMI: sensibilità della misura BL a LOS, risoluzione e rumore — bozza H1

**RINVIATA per decisione dell'utente (2026-11-13).** La priorità è lo studio
HMI della sorgente e del quenching. La degradazione verso MDI e la prova di
precisione qui proposta non si avviano. Il testo seguente conserva la bozza
non congelata; non è il piano operativo corrente. Vedi [HANDOFF](HANDOFF.md).

**BOZZA NON CONGELATA, revisione 2 — 2026-11-13.** Richiesta dell'utente: preparare prima il
protocollo, poi revisione e congelamento, codice e prove sintetiche, infine esecuzione.
Questo documento propone scelte concrete da rivedere. Nessuna selezione è stata
eseguita, nessun nuovo segmento interrogato o scaricato, nessuna risposta trasformata
calcolata. Tutti i numeri operativi sotto sono proposte, non soglie fisiche validate.
P1, P2 e P2f restano i riferimenti storici; non vengono modificati o rieseguiti.

## 1. Domanda e prodotto finale

**Domanda:** sul disegno HMI, le approssimazioni LOS e le degradazioni simulate
cambiano tilt, flusso, sorgente e dipolo in modo dipendente dall'attività solare,
capace di contaminare la ricerca del quenching? Introducono inoltre spostamenti
medi diversi per ciclo×emisfero, confondibili con differenze fra cicli?

Confronti appaiati: stessa HARP, stesso record primario, stessi dati di attività,
con diversa rappresentazione del campo. Br HMI è il riferimento strumentale, non
la verità fisica. Lo studio misura differenze fra pipeline simulate; non misura
nuovamente il quenching e non riproduce integralmente MDI.

Prodotti: elenco congelato delle HARP, inventario e hash degli input, tabella per
HARP e trasformazione, perdite di confrontabilità, spostamenti medi per ciclo ed
emisfero, pendenze descrittive degli errori contro attività, precisione attesa e
osservata, figure e relazione. **Esperimento interamente descrittivo:** nessun
esito «compatibile», «supera il budget» o accettazione globale. Le scale di §7
sono riferimenti di lettura, non soglie decisionali. L'avvio del confronto MDI
NON dipende dal superamento di un criterio di questo esperimento: richiederà una
decisione e un protocollo propri. Non si cerca un metodo «che passa» ritoccando
campione o simulazioni dopo averne visto le risposte.

## 2. Non cecità e scelte già informate dai dati

Sono già noti P1, BARD/P3, sensibilità, diagnosi A–D, pilota/validazione P2f e il
risultato reale T3 (non deciso). Le 120 HARP dominanti/controlli e le 30 schede 25S
sono già state esaminate. Il presente sviluppo è dichiaratamente non cieco.
La griglia degli effetti di P2f e i casi complessi informano le proposte sotto;
non verranno scelti campioni o tolleranze per migliorare il risultato T3.

Le classi visive non diventano esclusioni. Una HARP con più NOAA può essere un
complesso fisico: l'esperimento conserva questo limite della misura per HARP.

## 3. Precisione preventiva, due campioni annidati e acquisizione

### 3.1 Pianificazione su sole covariate e risposte sintetiche

Prima di qualsiasi nuovo segmento o risposta R1/R2, preparare una prova di
precisione separata: piano e scelte registrati prima del codice e dei calcoli.
Si usano soltanto identificativi e covariate del disegno S (Φ, A, latitudine,
ciclo, emisfero, CR e famiglie candidate); nessun tilt reale, nessun R1 osservato
e nessuna selezione in base alla pendenza reale. Le regole delle prove di stress
possono usare |S_BL| già noto, ma quegli elementi restano fuori dalla simulazione
del campione probabilistico.

Proposta di griglia: campioni massimi N=80,160,320 secondo §3.2; 1000 repliche per
configurazione. Δγ sintetico con dispersione individuale 1°,3°,6°, centro zero
oppure pendenza diagnostica di 1,2° per unità di attività; componente comune di
famiglia con SD 0 o 1°, componente per CR AR(1) con SD 0 o 1° e φ=0,8 (fattoriale
completo). Sono scenari di pianificazione, NON stime della dispersione R1 né un
modello dello strumento. Identificativi, covariate, rumore e semi separati: proposta
SeedSequence(27000000) con chiavi (N,scenario,replica), elenco degli scenari in
ordine esplicito da registrare prima del codice. Eventuali semi del bootstrap
interno in uno spazio distinto, SeedSequence(27000001).

Per ogni configurazione riportare rango e condizionamento, errore standard e
semilarghezza dell'intervallo, bias/dispersione della pendenza e delle medie,
numero di famiglie, fallimenti, mediana e quantili 10/90 delle larghezze. Le
prestazioni sono condizionate ai rumori ipotizzati; non validano intervalli sul
processo reale. I casi con correlazione per CR mostrano il limite del bootstrap
solo a famiglie. Usare la stessa procedura descrittiva prevista in §7.

Obiettivo di precisione di pianificazione: semilarghezza attesa della pendenza
Δγ di ordine 1,2° o inferiore; mostrare anche il rapporto fra larghezza e quella
scala, per scenario, senza un esito complessivo di accettazione. Presentare
precisione e costo per tutti e tre gli N. **Scelta finale di N prima di congelare
la lista e scaricare risposte**, proposta iniziale N=160 per R1/R2; se neppure
N=320 dà precisione utile nei regimi plausibili, riformulare l'obiettivo o
accettare esplicitamente precisione limitata. Nessun aumento guidato dalle
risposte reali. Non usare un primo R1 per ottimizzare N dopo aver visto la
pendenza: una futura ricalibrazione sulla dispersione sarebbe un emendamento
non cieco separato, non previsto dall'esecuzione unica qui proposta.

### 3.2 Campione principale R0–R2: più informazione sulle code di attività

Base: i 2485 record primari HARP S con A_monthly finita del disegno P2f, usando
codice/input di 42fcd01. Verificare conteggio e chiavi senza ricalcolare T3.

Per ogni ciclo×emisfero (24N,24S,25N,25S) dividere l'attività mediante quartili
empirici q25/q75: bassa A≤q25, centrale q25<A<q75, alta A≥q75. Definire i quantili
con interpolazione lineare; se q25=q75 assegnare gli uguali alla fascia centrale
e dichiarare la degenerazione. Il limite basso ha precedenza sugli uguali a q25
quando i quartili sono distinti. Flusso basso/alto rispetto alla mediana di Φ
nell'intero gruppo, uguali al livello basso; complessità NOAA_NUM≤1 contro ≥2.
NOAA non identifica automaticamente un numero di bipoli fisici indipendenti.

Strati: 4 gruppi × 3 fasce A × 2 flussi × 2 complessità =48. Estrarre senza
reimmissione n=2k per ognuna delle fasce estrema bassa/alta e n=k per la centrale,
con k=1,2,4 rispettivamente per N massimo 80,160,320. Mantenere quindi probabilità
positiva anche nella fascia centrale, senza affermare che il campione riproduca
la distribuzione dell'intero catalogo. Pesi principali Φ; Φ/pi solo sensibilità.

Un generatore default_rng(26000000), ordine gruppi sopra, fascia bassa/centrale/alta,
flusso basso/alto, complessità bassa/alta; lista ordinata HARPNUM,T_REC. Produrre
un'unica permutazione per strato e prenderne i primi n: i tre campioni sono
annidati. Se uno strato è scarso prendere tutti gli elementi e registrarlo,
senza rimpiazzi fra strati. Registrare N_strato,n_strato,pi=min(n,N_strato)/N_strato.
N finale rimane aperto fino alla prova di precisione; nessuna estrazione svolta
nel deposito di questa bozza.

### 3.3 Sottocampione R3–R5 e prove di stress

Per limitare il costo dei rami ottici e delle repliche, usare il sottocampione
annidato k=1, fino a80HARP, indipendentemente da N scelto per R1/R2. I confronti
fra R2,R3,R4,R5 sono sempre ricalcolati sullo stesso sottoinsieme confrontabile;
non sottrarre pendenze stimate su campioni diversi attribuendole al solo ramo.

Prove di stress: quattro HARP con |S_BL| più grande per ciclo×emisfero nella baseS,
pari merito per HARPNUM,T_REC, fino a16 già in parte note. Unire per il download
senza duplicati; stress fuori dalle stime principali se non estratto anche nel
campione probabilistico. Fino a336 record distinti per R1/R2 e96 per R3–R5; il
preventivo può imporre un arresto PRIMA dei download, non una selezione a posteriori.

### 3.4 Esclusioni, copertura e acquisizione

Prima dei nuovi campi: commit della lista finale, strati, campioni annidati,
probabilità e hash. Inventariare covariate, WCS e metadati disponibili. La posizione
dei primari limita il dominio μ; nessuna generalizzazione automatica al lembo.
Calcolare μ pixel per pixel dall'osservatore finito, non dal centro della patch.

Produrre una **tabella di flusso per ramo e per strato A**, anche per ciclo×emisfero,
flusso e complessità: candidati, selezionati, tentativi, input mancanti, μ fuori
dominio, margine PSF insufficiente, polarità assente, errore e confrontabili.
Conservare più motivi per record e anche il conteggio delle loro unioni, evitando
di sommare percentuali sovrapposte come se fossero casi distinti. Denominatori
espliciti (selezionati oppure tentativi dello specifico ramo), anche per repliche.

Riportare per inclusi/esclusi distribuzioni di A,Φ,latitudine,μ,NOAA_NUM e quote
baseline di flusso/|S_BL|. Verificare in particolare se μ≥0,8 su TUTTA la maschera
e il margine5σ eliminino maggiormente code di attività o complessi grandi. Se
questo avviene le pendenze sui sopravvissuti sono condizionate alla selezione,
non una stima non distorta dell'effetto strumentale sul catalogo. Nessuna
imputazione, nessun peso correttivo per mancate misure assunto valido a priori.
Le percentuali citate dal revisore (4%, medie A1,28/1,44) sono indizi, non nuove
misure verificate qui: l'esito va ricostruito sul dominio e sulla maschera effettivi.

Download SOLO su chiavi congelate: Bt,Bp,magnetogramCEA per R1/R2; magnetogram
nativo solo per R3–R5. Br/bitmap/metadati P1 immutati. Inventario preliminare di
segmenti, unità, QUALITY,WCS, tempi e dimensioni; nessuna sostituzione con tempi
oHARP simili. La selezione definitiva non può dipendere dal segno delle differenze.

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
Per densità di flusso LOS, G e Mx cm⁻² sono unità equivalenti. Le RMS qui si
riferiscono alla LOS prima della divisione: sul proxy radiale il rumore locale
cresce come σ_LOS/μ e la covarianza diventa C_ij/(μ_i μ_j), oltre agli effetti
della rimappatura. Non imporre una RMS radiale costante dopo la divisione.

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

## 7. Analisi solo descrittiva: spostamenti medi e dipendenza dall'attività

### 7.1 Popolazione e pesi dichiarati

**Principale:** pesi Φ_R0 sul campione probabilistico selezionato e confrontabile.
Descrive quel campione, deliberatamente arricchito nelle code di A; non è una
stima automatica dell'intero catalogo. **Sensibilità:** Φ_R0/pi_i sul medesimo
insieme; cambia l'obiettivo verso il catalogo di campionamento e può aumentare
la variabilità. Non dichiarare i due pesi equivalenti né scegliere il risultato
più stretto. Le probabilità di campionamento non correggono le perdite successive.
Stress separati; confronti incrementali sul comune sottoinsieme; riportare sempre
numerosità, famiglie e distribuzioni dei pesi/quote massime di peso.

### 7.2 Spostamenti medi per ciclo×emisfero (primo risultato)

Per ramo/scenario e per i quattro gruppi riportare media pesata, mediana e
intervallo descrittivo di Δγ, ΔΦ/Φ_R0 e Δη; aggiungere ΔS_BL e ΔD_bal, cambi di
segno, differenze firmate e somma dei moduli con denominatori del campione
espliciti. Baseline e ramo entrambi confrontabili; denominatori nulli/non finiti
indicati e mai sostituiti conzero. Mostrare anche differenze fra gruppi: possono
mimare uno spostamento fra cicli o emisferi, ma non stimano un biasMDI osservato.

Scale illustrative proposte, NON criteri: per Δγ la media pesata nel gruppo di
1,2°sin|λ_R0| (effetto sul tilt di una variazione del coefficiente Joy di1,2°);
per ΔΦ/Φ una linea ±5%; per Δη ±0,05eta_bar. Tenere distinte le unità:1,2° è una
scala del coefficiente Joy, non uno spostamento uniforme del tilt delle regioni.
Le scale sono scelte di pianificazione, non limiti strumentali dimostrati.

### 7.3 Pendenze diagnostiche

Δγ=γ_ramo−γ_R0 contro (A−1)sin|λ_R0| con quattro termini ciclo×emisfero
moltiplicati per sin|λ_R0|; pesi principali Φ_R0. Per Δη, cambiamento contro A−1
con intercette ciclo×emisfero: diagnostica REGIONALE, non testT5 per celle.
Aggiungere ΔΦ/Φ_R0 contro A−1 con le stesse intercette per distinguere il flusso.
Nessuna nuova stima del quenching e nessuna correzione del βT3 osservato.

Minimi operativi proposti per il modello a quattro gruppi: almeno4HARP distinte
e almeno3famiglie per gruppo dopo le perdite, almeno due valori distinti del
regressore (A−1)sin|λ| e qualche sin|λ| non nullo in ciascun gruppo. Questi
minimi NON garantiscono precisione o rango: richiedere anche rango5 della
matrice del tilt e numero di condizione≤10^12 per X'WX con pesi normalizzati alla
media1. Se falliscono, pendenza «non stimabile», con motivo; le medie dei gruppi
con dati rimangono descrivibili. Per i modelli con intercette non moltiplicate
per sin|λ| applicare analoghe verifiche. Non aggregare gruppi dopo aver visto
le risposte per recuperare una pendenza.

### 7.4 Incertezza e lettura

Intervalli descrittivi95% da2000 bootstrap a famiglie candidateP1e; una famiglia
attraverso più strati/gruppi si ricampiona come unità, mai pixel o repliche.
Le20repliche di rumore sono mediate dentroHARP prima del bootstrap e la loro
dispersione riportata separatamente. Nei bootstrap con rango perso registrare
il fallimento; se più del10% fallisce non riportare l'intervallo, lasciando stima
e conteggio. Se meno di3famiglie in un gruppo, riportare soltanto descrizione e
numerosità per quel gruppo. Sono cautele operative proposte, non validazione
della copertura. La correlazione temporale fra famiglie diverse resta un limite;
la prova sintetica§3.1 ne mostrerà la sensibilità. Nessun claim inferenziale.

Affiancare precisione attesa e osservata e scale illustrative di §7.2. Per la
pendenza Δγ mostrare ±1,2°/unitàA (0,05×24°), perΔη ±0,05eta_bar con
eta_bar=3,56e−25G/Mx. **Nessuna classificazione pass/fail o «compatibile»**,
nessuna equivalenza dimostrata, nessuna correzione scelta dal segno osservato.
Una barra larga è informazione sulla precisione insufficiente di questo disegno,
non prova di assenza di distorsione. Una barra stretta resta condizionata a
campione, selezione, modello del rumore e intervallo descrittivo non validato.

La faseMDI non ha una porta automatica in questa prova. Un suo eventuale avvio
sarà deciso con un piano separato, usando insieme grandezza degli scostamenti,
precisione, copertura, perdite legate all'attività e limiti del modello simulato.
## 8. Controlli, arresto e costo

Per l’esperimento sulle mappe, prima delle risposte nuove: congelare protocollo
e lista campione; poi codice,
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
segmenti; massimo2GB nuovi dati e2ore di calcolo su4processi per l’esperimento sulle mappe, senza installare
nell'ambiente P2f. Questi sono tetti operativi, NON una stima misurata. Se il
preventivo supera il tetto, arresto prima del download; nessuna riduzione del
campione dopo aver visto risposte. Il preventivo deve distinguere R1/R2 estesi,
R3–R5 sul sottoinsieme e prova preventiva sintetica (budget separato da fissare
nel suo piano prima del codice). Se precisione e costo sono incompatibili,
segnalarlo prima dei dati: non promettere che il limite2GB copra N=320. Salvare avanzamento/risultati parziali se si
supera il tempo; niente aumento automatico del budget.

## 9. Decisioni e revisione recepita

**D4 chiusa nella bozza:** esperimento solo descrittivo, niente accettazione o
porta versoMDI. PesiΦ principali e Φ/pi come sensibilità con obiettivi distinti.
Spostamenti medi per ciclo×emisfero parte integrante dell'analisi, non soltanto
pendenze. Resta da congelare la specifica completa dopo la pianificazione.

| ID | Proposta aggiornata | Prima del congelamento |
|---|---|---|
|D1|code A sovracampionate, fascia centrale mantenuta; N=80/160/320 per R1/R2, sottocampione k=1 per R3–R5|piano della prova sintetica e confronto di precisione/costo; scelta di N prima dei dati|
|D2|μ≥0,8 e maschera P1 fissa; perdite e motivi per fascia A/gruppo/complessità|dominio esatto, frazioni d'area e verifica dei margini con sole covariate/metadati|
|D3|PSF/rumore di§5, LOS prima e dopo divisione per μ distinti|operatori, covarianza, stadio del rumore e positività; nessuna equivalenza dichiarata aMDI|
|D4|solo descrittivo; medie per gruppo, pendenze e due schemi di pesi|rivedere i minimi operativi e il bootstrap, senza creare regole di successo|
|D5|20repliche,2GB/2ore per le mappe, prova sintetica separata|preventivo distinto per rami e budget della pianificazione prima di eseguirla|

Revisione2, dopo i rilievi dell'utente/revisore sulla prima bozza: introdotta la
precisione preventiva, concentrazione del campione nelle code senza eliminare il
centro, peso principaleΦ con obiettivo esplicito, esclusioni per attività e medie
per ciclo×emisfero. Tolti i tre esiti di accettazione; aggiunti minimi di disegno
e scaling del rumore conμ. Le osservazioni numeriche del revisore sulle HARP
escluse non sono state trattate come verifiche già svolte da questa revisione.

**Stato:** bozza non congelata; nessuna prova sintetica, selezione o download
eseguito. Primo passo successivo: rivedere questa versione e registrare il piano
della sola valutazione sintetica di precisione. Il protocollo sulle mappe si
congela dopo averne risolto numerosità, costo e specifiche; non partire da R1
per decidere retroattivamente il campione.

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

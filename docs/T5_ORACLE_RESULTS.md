# T5-D2 — rapporto dei risultati: struttura preparata

**BOZZA DI SOLA STRUTTURA — 2026-11-13. Nessun risultato T5-D2 inserito.**
Questo file è preparato prima dell'apertura degli output scientifici della
corsa, per raccogliere poi controlli, risultati e limiti senza cambiare le
regole di lettura. Non è un protocollo, non congela nuovi criteri e non
attesta che la corsa sia terminata. Lo stato del processo non è stato
ricontrollato durante questa preparazione. `DA INSERIRE` non significa zero.

## 1. Domanda e stato scientifico

T5 studia la dipendenza dell'efficienza del proxy della sorgente BL
rispetto all'attività. La procedura M non ha superato la validazione P2f
nello scenario 7, con livelli ±1 su blocchi di 20 CR. T5-D1 ha rilevato,
negli output salvati della validazione P2f (`5c3b664`), ora materiale di
sviluppo, R = media(SE²)/varianza empirica(beta) circa
0,858 sotto nulla. Si tratta di una carenza di circa il 14,2% nella media
di SE², non nel valore di SE e non in una componente già identificata.
R da solo non descrive le code o i falsi verdetti.

T5-D2 confronta sostituzioni oracolo delle componenti della varianza sugli
stessi cataloghi sintetici già usati nella validazione. Non raccoglie nuove
osservazioni, non verifica il quenching sui dati reali e non valida una
nuova procedura. Gli oracoli usano quantità note soltanto nelle simulazioni.
**T5 resta descrittivo. T3 resta non deciso, senza nuove esecuzioni.**

## 2. Provenienza e ordine dei passaggi

| Elemento | Riferimento documentato o campo da completare |
|---|---|
| Protocollo storico congelato | [PROTOCOL_T5_ORACLE.md](PROTOCOL_T5_ORACLE.md), `f77d39b`; conservato invariato |
| Emendamento da applicare nella lettura | [PROTOCOL_T5_ORACLE_A1.md](PROTOCOL_T5_ORACLE_A1.md), `2b334bb`; prevale sui punti sostituiti |
| Produttore atteso | `2bf262f1b99d6a884ed72686047dc089911e5eff`, albero tracciato pulito: da confermare sugli output |
| Avvio registrato | 2026-11-13 13:56:57 Europe/Rome, nota `d284592`; PID wrapper 1141311, PID Python 1141317 |
| Fine, durata, uscita | Log `logs/t5_oracle.log`: «32000/32000 cataloghi» e marcatore `fatto`, ultimo aggiornamento 2026-11-13 18:45:25 Europe/Rome; durata circa 4 h 48 min (stima del piano 1,5–2,5 h). Codice di uscita del processo non registrato |
| Ricevuta preliminare | Dieci prove passate, già registrate; hash atteso in [fotografia degli input](T5_ORACLE_POSTCHECK_INPUTS_SHA256.csv) |
| Codice del verificatore separato | `9bd1e2e`; 77 prove costruite a mano passate; ricevuta legata allo SHA del codice, non all'HEAD documentale successivo |
| Controllo effettivo sui risultati | Eseguito il 2026-11-14 sul commit pulito `94606c6` con `t5_oracle_postcheck.py --check` (codice `ac591b47…`, ricevuta 77/77): **54/54 controlli superati**, nessuna discrepanza; esiti in `results/T5_ORACLE_POSTCHECK/` |
| Conservazione degli output | Quattro output, ricevuta preliminare e controllo conservati nel commit successivo al controllo, prima di leggere i risultati; hash prima/dopo identici in `results/T5_ORACLE_POSTCHECK/META.json` |
| Interpretazione e revisione | Data, autore/modello, esposizioni precedenti e rilievi DA INSERIRE |

Distinguere il produttore degli output T5-D2, quello della validazione P2f
originale (`5c3b664`) e il commit del verificatore. Non richiedere che siano
lo stesso HEAD. Registrare versioni dell'ambiente e ricevute effettivamente
usate; non attribuire alla corsa un ambiente dedotto solo dal file dei requisiti.

L'emendamento A1 dichiara una prova tecnica su quattro cataloghi sintetici
della validazione P2f prima della registrazione dell'emendamento e del commit del codice. Questo
limite di cecità resta dichiarato, senza ripresentare il lavoro come cieco.

## 3. Bracci e quantità sostituite

La stima beta deve restare identica tra bracci dello stesso catalogo.
Cambiano la varianza e, dove specificato, la sua stima temporale.

| Braccio nel CSV | Varianza individuale | Componente temporale | Confronto da descrivere |
|---|---|---|---|
| A0 | stimata | REML AR(1) stimata | Riproduzione della procedura M rispetto al raw P2f |
| A1a | vera | parametri temporali stimati di A0, tenuti fissi | Sostituzione della sola varianza individuale nella formula |
| A1b | vera | REML AR(1) ristimata con rumore di cella vero | Effetto aggiuntivo della ristima rispetto ad A1a |
| A2 | stimata | scala e covarianza temporale vere | Sostituzione della componente temporale |
| A3 | vera | scala e covarianza temporale vere | Varianza nota sul disegno fisso; non garantisce code normali |
| A2p (A2′ nel testo) | stimata | scala vera e approssimazione AR(1) lag per lag | Confronto della specifica approssimazione con A2; soltanto 7 e 10 |

Con salti, la covarianza usata dagli oracoli è marginale rispetto alla fase:
K(tau) = max(0, 1 - abs(tau)/L). Lo scenario 7 ha livelli indipendenti nei due
emisferi ma fase dei salti condivisa: covarianza incrociata nulla non significa
indipendenza completa dei due processi. Nello scenario 10 i livelli sono
comuni. Non modificare il generatore storico per correggere una descrizione.

A2p usa phi* = 0,9106 nel 7 e 0,8657 nel 10; kappa* = 0 e 0,98. Nel 10 il
limite 0,98 differisce da kappa = 1 del generatore. Sono valori documentati
della costruzione, non risultati della corsa. Il criterio pesa i ritardi
uniformemente e non ottimizza la proiezione sul contrasto di beta.

## 4. Porta tecnica prima dell'interpretazione

Seguire la [guida del verificatore separato](T5_ORACLE_POSTCHECK_README.md).
Il controllore storico non basta come unica verifica finale: parsing di
`null` e controlli incompleti sono rilievi sul sorgente, non difetti già
osservati nelle tabelle della corsa.

Sequenza da completare dopo la fine della corsa:

1. Accertare fine, quattro file completi e assenza di modifiche in corso;
   annotare eventuali esposizioni accidentali a risultati nel log.
2. Rivedere il nuovo verificatore rispetto alla specifica, prima della
   lettura scientifica; la revisione della preparazione non è ancora conclusa.
3. Eseguire il controllo separato in una cartella nuova. Conservare anche
   ogni eventuale rapporto fallito, senza sovrascrivere gli originali.
4. Verificare provenienza, hash prima/dopo, chiavi esatte, A0 contro P2f,
   finitezza, intervalli, verità, code, riepiloghi e appaiamenti.
5. Se fallisce un controllo, chiarire la discrepanza prima di adottare una
   sintesi. Se passa, conservare output e controlli prima dell'interpretazione.

Il contratto prevede 32000 cataloghi, 188000 righe raw, 46 gruppi di riepilogo
e 38 confronti appaiati. Sono numerosità del piano, non conteggi verificati
in questo documento. Le 77 prove del verificatore e i 60 test ordinari del
repository non sono il controllo effettivo di questi output.

**Limite del verificatore, da riportare con i risultati.** Per i bracci
A1a, A1b, A2 e A2p il verificatore controlla soltanto la coerenza interna
(intervalli centrati, semi-intervalli, verdetti, code, riconteggi): non
ricalcola i loro SE. Un SE sbagliato ma usato in modo coerente passerebbe.
Solo A0 ha un riferimento esterno (raw P2f); A3 ha il solo controllo
strutturale dell'SE costante per scenario. Inoltre 77/77 non equivale a 77
verifiche indipendenti: circa nove prove hanno valori attesi fissati a mano,
le altre sono alterazioni o confronti del riconteggio con sé stesso. Un caso
con una riga errore e valori calcolati a mano è stato provato esternamente il
2026-11-14 (`scripts/t5_postcheck_external_probe.py`, fuori dalla ricevuta;
[revisione incrociata](CROSS_REVIEW_2026-11-14.md)).
La prova migliora la trasparenza ma non colma il limite sugli SE: la sua
sufficienza dipende dalle conclusioni che si vorranno sostenere.

| Verifica effettiva | Esito da inserire |
|---|---|
| Integrità, provenienza e impronta degli input | Superato: 18 hash degli input, produttore `2bf262f` pulito su ogni riga e nei metadati, 10 prove preliminari |
| Chiavi, numerosità e assenza di duplicati | Superato: 188000 righe, 46 gruppi, 38 confronti, chiavi esatte |
| Riproduzione A0 su tutte le 32000 chiavi pertinenti | Superato; 22 righe errore senza beta nel riferimento P2f, dichiarate e non confrontate numericamente |
| Pendenze uguali fra bracci, verità, stati, intervalli e code | Superato |
| Riconteggio completo del riepilogo e delle matrici appaiate | Superato: tutte le colonne, nessuna inversione di segno, 16 celle per confronto |
| A3 senza errori e SE costante per scenario sul disegno fisso | Superato (controllo strutturale, non di normalità) |
| File invariati durante la lettura | Superato: hash identici prima e dopo |
| SE dei bracci A1a, A1b, A2, A2p | Non ricalcolati dal verificatore: solo coerenza interna (vedi sopra) |
| Rilievi della revisione e loro risoluzione | DA INSERIRE |

## 5. Numerosità, denominatori e definizioni

| Cataloghi previsti | N previsto per braccio | Bracci previsti |
|---|---|---|
| Nulla, scenario 7 | 10000 | A0, A1a, A1b, A2, A3, A2p |
| Effetti -0,1 / -0,2 / -0,3 / -0,35, scenario 7 | 2000 per effetto | A0, A1a, A1b, A2, A3, A2p |
| Nulla, scenario 10 | 10000 | A0, A1a, A1b, A2, A3, A2p |
| Nulla, scenario 1 e 2 | 2000 per scenario | A0, A1a, A1b, A2, A3 |

La scala del generatore è eta0 = 3,56e-25 G/Mx, distinta da una media stimata
ora sui dati reali. r = (beta - beta_vero)/eta0; s = SE/eta0; z = r/s.
R = media(s²)/var(r), varianza campionaria con ddof=1; SD(z) con ddof=1;
quantili lineari di z alle probabilità 0,0125 e 0,9875. Il riferimento
normale ha quantili ±Phi^-1(0,9875), non soglie arrotondate nel calcolo.

R, SD(z) e quantili riguardano i casi numerici validi di ciascun braccio:
riportare sempre N valido ed errori. Le frequenze di falsi verdetti,
copertura e code mantengono tutti i tentativi al denominatore. Gli errori
non sono falsi verdetti sotto nulla e sono non copertura sotto effetto,
come nelle convenzioni originali; non eliminarli silenziosamente.
MCSE binomiale della singola frequenza = sqrt(f*(1-f)/N).

Coda inferiore (`below`): beta_vero < lo; coda superiore (`above`):
beta_vero > hi. I valori esattamente agli estremi sono coperti.
I due nomi descrivono la posizione del parametro rispetto all'intervallo,
non il verso fisico del quenching. Errori Monte Carlo e dispersioni delle
simulazioni non sono incertezze sul processo solare osservato.

## 6. Tabelle dei risultati — tutte da compilare

Tutte le celle scientifiche qui sotto sono segnaposto. I soli numeri già
riportati sono quelli previsti dal piano. Inserire N osservato, validi ed
errori prima dei momenti; confermare la concordanza con i riconteggi.

### 6.1 Nulla: frequenze e varianza per scenario e braccio

| Scenario | Braccio | N previsto | N osservato / valido / errori | R | Falsi: supportato / opposto / totale | Frequenza ± MCSE |
|---|---|---|---|---|---|---|
| 7 | A0 | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 7 | A1a | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 7 | A1b | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 7 | A2 | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 7 | A3 | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 7 | A2p | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 10 | A0 | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 10 | A1a | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 10 | A1b | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 10 | A2 | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 10 | A3 | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 10 | A2p | 10000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 1 | A0 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 1 | A1a | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 1 | A1b | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 1 | A2 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 1 | A3 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 2 | A0 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 2 | A1a | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 2 | A1b | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 2 | A2 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| 2 | A3 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |

### 6.2 Scenario 7 sotto effetto: copertura e code

Gli effetti sono coefficienti in unità eta0; beta_vero = effetto*eta0.
Riportare copertura anche in conteggi e MCSE, oltre alla percentuale;
conservare separati i due versi delle mancate coperture.

| Effetto | Braccio | N previsto | N osservato / valido / errori | R | Coperti/N; copertura ± MCSE | Below/N | Above/N |
|---|---|---|---|---|---|---|---|
| -0,1 | A0 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,1 | A1a | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,1 | A1b | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,1 | A2 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,1 | A3 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,1 | A2p | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,2 | A0 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,2 | A1a | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,2 | A1b | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,2 | A2 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,2 | A3 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,2 | A2p | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,3 | A0 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,3 | A1a | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,3 | A1b | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,3 | A2 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,3 | A3 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,3 | A2p | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,35 | A0 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,35 | A1a | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,35 | A1b | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,35 | A2 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,35 | A3 | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |
| -0,35 | A2p | 2000 | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE | DA INSERIRE |

### 6.3 Dispersione e quantili di z

Tabella da collegare a tutti i 46 gruppi di `RECOUNTS.csv`, includendo
N valido, SD(z), q0,0125 e q0,9875. Non usare beta/SE sotto effetto:
la centratura corretta è (beta - beta_vero)/SE.

**DA INSERIRE: tabella completa o allegato con i 46 gruppi, dopo verifica.**

### 6.4 Confronti appaiati rispetto ad A0

Usare le stesse chiavi di catalogo. Riportare le 38 combinazioni previste
con N tentativi, N entrambi validi, stati uguali e due conteggi deciso/non
deciso. Conservare anche le 16 celle della matrice completa degli stati
per ciascun confronto, comprese le transizioni da/a errore. Non trasformare
`errore` in `non deciso` e non confrontare i bracci come campioni indipendenti.

Le MCSE delle frequenze singole non sono automaticamente errori della loro
differenza appaiata. Il presente schema non introduce test o soglie nuovi
per tali differenze. Se A0 ha beta mancante nel riferimento P2f in una
riga errore, indicare quanti valori non erano stati conservati: nessun
confronto numerico fittizio.

**DA INSERIRE: tabella dei 38 confronti e riferimento alle matrici 4×4.**

## 7. Lettura vincolata all'emendamento A1

Questa griglia riporta le letture già registrate, non nuove decisioni.
«Vicino al riferimento» e «nel limite» restano confronti descrittivi con
incertezza Monte Carlo; non sono una nuova accettazione di T5. Leggere
insieme varianza, code, copertura, errori e cambiamenti appaiati.

| Confronto previsto | Lettura consentita se osservato | Cosa non conclude |
|---|---|---|
| A2 vicino al riferimento (R circa 1 e falsi verdetti nel limite), A1a no | Compatibile con un ruolo principale della componente temporale, modello e stima, in questi cataloghi | Non identifica un difetto unico o un metodo correttivo già valido |
| A1a vicino al riferimento, A2 no | Compatibile con un ruolo principale della varianza individuale nella formula | Non dimostra che la forma della funzione sia la sola causa |
| A1b differisce da A1a | La ristima temporale cambia il risultato quando si cambia la varianza individuale | Non dimostra una specifica interazione |
| Solo A3 vicino al riferimento | La sostituzione congiunta migliora la calibrazione in questi cataloghi | Non isola una causa né dimostra un'interazione |
| Neppure A3 migliora le code o le frequenze | Compatibile, tra le altre spiegazioni, con un ruolo della forma non gaussiana rispetto al riferimento normale | La varianza vera non rende automaticamente normale la distribuzione |
| A2p vicino o distante da A2 | Descrive l'effetto della specifica approssimazione lag per lag | Non dimostra adeguatezza o inadeguatezza generale di ogni AR(1) |
| Controlli 1 e 2 anomali | Riportare lo scarto e riesaminare la diagnosi con cautela | Non ignorarli perché lo scenario d'interesse è il 7 |

Il confronto A2p–A0 cambia anche la scala temporale stimata in quella vera:
non attribuirlo esclusivamente a phi o kappa. Nel confronto A2p–A2 resta
la stessa componente individuale stimata e cambia la covarianza temporale
specificata. Nessuna conclusione va dedotta dal solo R, né da una sola
combinazione scelta dopo aver visto i risultati.

Il §7 del protocollo congelato legge A2′ in modo generale («se A2′ resta
vicino ad A0, la forma AR(1) è inadatta ai salti»). In base ad A1 §3, che
qualifica A2′ come la specifica approssimazione lag per lag, quella lettura
generale **non si adotta**: l'esito di A2′ descrive solo questa
approssimazione. Allo stesso modo l'«indizio» del protocollo §1 (eccesso di
falsi verdetti dovuto all'errore standard stimato) è più forte di quanto
T5-D1 ha stabilito e non va riportato come risultato.

**Interpretazione effettiva: DA SCRIVERE soltanto dopo i controlli.**

## 8. Incidenti, discrepanze ed esposizioni da rendicontare

Conservare separati fatti documentati, segnalazioni dell'operatore e
verifiche ancora da fare. Non cancellare i primi tentativi o correggere
retroattivamente il protocollo congelato.

- Prova tecnica su quattro cataloghi: già dichiarata nell'emendamento A1.
- Confusione wrapper/Python e secondo avvio interrotto senza scrittura:
  episodio riferito dalla sessione di esecuzione; confermare i dettagli
  tecnici prima del consuntivo, senza trasformare la segnalazione in un
  secondo run scientifico completato.
- Fascia di semi della verifica preliminare di covarianza dello scenario
  10: il codice usa 28200000+k, mentre la formulazione generale del piano
  indica 28000000+k. Dichiarare la differenza del solo pretest, senza
  modificarlo né confonderla con i semi dei cataloghi dell'esecuzione.
- Eventuali tabelle viste nel log prima del controllo, problemi del
  verificatore o ricomputazioni: DA INSERIRE, anche se non cambiano i numeri.
- Già documentata la fase comune dei salti del 7: correggere nel rapporto
  eventuali descrizioni di indipendenza completa, lasciando il generatore intatto.

## 9. Conclusioni e possibili passi successivi

**Conclusioni scientifiche nuove: NON ANCORA DISPONIBILI in questo file.**

Dopo la verifica, separare: cosa cambia negli oracoli, quali spiegazioni
restano compatibili, cosa non è distinguibile e quali informazioni
mancherebbero per un metodo utilizzabile sui dati reali. Se la diagnosi è
ambigua, non chiamare T5 irrisolvibile con HMI.

Qualunque candidata successiva deve essere applicabile senza conoscere
le varianze vere; richiede un piano proprio e una validazione con semi
nuovi e scenari fissati prima, incluso il 7. Non si elimina lo scenario
fallito, non si riscalano gli errori standard usando questi esiti e non
si applica T5 reale in base al solo controllo degli oracoli.

Fino a quel passaggio, T5 rimane descrittivo e T3 conserva il risultato
non deciso già registrato. Morfologia, misura P1 e risultati osservativi
restano distinti dalla diagnosi sintetica qui preparata.

## 10. Revisione e conservazione

Richiesta per l'altro agente in [T5_ORACLE_REVIEW_REQUEST.md](T5_ORACLE_REVIEW_REQUEST.md).

Fase 1 svolta il 2026-11-14 da Claude Opus 5.5 sul commit `f38d351`, senza
aprire gli output: [revisione incrociata](CROSS_REVIEW_2026-11-14.md). Nessun
problema bloccante per le attività esaminate, senza approvare conclusioni
T5-D2; verificatore e protocolli invariati; precisazioni
documentali applicate. Un secondo revisore ne ha condiviso le conclusioni.
Non è una revisione cieca né la revisione dell'interpretazione (fase 2).

**DA INSERIRE:** autore e commit esaminato, esito della revisione del
verificatore, esito della revisione scientifica successiva, rilievi e
risoluzioni con commit distinti. Lo stesso agente che ha partecipato al
progetto offre una revisione incrociata, non una verifica cieca dell'intero
studio. La preparazione di questo scheletro non sostituisce quelle revisioni.

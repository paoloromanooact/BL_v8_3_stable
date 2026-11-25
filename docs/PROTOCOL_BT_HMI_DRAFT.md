# BT-HMI — confronto bayesiano del trasporto: BOZZA rev.1

25 novembre 2026, Codex. **Non congelata, nessun codice BT, fit, nuova simulazione o download autorizzato.**
Pilastro: sorgente BL. Solo HMI. Questa e una proposta da rivedere dopo C e i piloti, non una deviazione
che ne cambia parametri, dati o esiti. BQ resta prioritario; BQ-M rinviato, nests sospesi, SINDy separato.

## 0. Domanda e limiti

Sul campione primario→controllo del pilota osservativo, quale modello predice meglio le osservazioni a
1–4,5 giorni, sullo stesso dominio e senza usare quelle osservazioni per scegliere il modello d'errore?
Non e una verifica del campo polare finale, della sorgente integrata di un ciclo o dell'assenza di nuova emersione.

P1/P1d e le analisi precedenti sono gia noti: studio non cieco. Il controllo e scelto al massimo USFLUX
entro la finestra P1, non a un istante estratto indipendentemente dal campo. La popolazione e condizionata
a questa selezione: non chiamare il risultato previsione di un giorno futuro casuale o prova generale di decadimento.
Fissare e dichiarare quali risultati del pilota sono gia stati letti prima del congelamento BT.

## 1. Prerequisiti e separazione dei dati

- Piloti mappa–bipolo ed evoluzione osservata e misura C conservati e ricontati, con versioni/protocolli e SHA.
- Regole di selezione, tempi T_OBS, maschere, geometria, segni, soglie e supporti quelli del pilota approvato.
  Non aprire una diversa finestra per il modello che altrimenti perde casi.
- Riutilizzare la separazione sviluppo/verifica per componenti, famiglie e possibili sovrapposizioni. Conservare
  un manifesto del grafo e delle chiavi; la verifica non entra nella stima di prior, scale o discrepanze.
- Se i risultati della verifica del pilota sono gia letti quando si definisce BT, quella stessa verifica NON
  diventa di nuovo cieca. Prima di procedere scegliere una strategia esplicita: analisi dichiaratamente non
  cieca con valutazione strutturata e suoi limiti, oppure un nuovo insieme ancora escluso dallo sviluppo.
  Il protocollo definitivo registra la scelta; non promettere nuovi casi indipendenti senza inventario.

## 2. Candidati deterministici da rendere probabilistici

- MP: persistenza della mappa iniziale nel sistema di Carrington.
- MR: sola rotazione differenziale rispetto a Carrington.
- MS: SFT con rotazione, flusso meridiano e diffusione, parametri del pilota congelato.

I parametri fisici non si riadattano alla verifica. La griglia di sensibilita del pilota si riporta separata:
non scegliere il suo membro migliore usando i dati di verifica. Eventuale miscela/prior sui membri da fissare
prima, non una nuova ottimizzazione fisica implicita. Inizializzazione dalla mappa principale per tutti;
bipolo come analisi separata di rappresentazione. Confrontare gli stessi oggetti, istanti e osservabili.

## 3. Osservabili: proposta iniziale, da chiudere prima del codice

Primario proposto: dipolo assiale locale D_C osservato sul dominio comune, con scala di unita fissa dichiarata.
In pochi giorni puo cambiare poco fra modelli: un ranking non informativo e un esito ammesso, non motivo per
sostituire il primario dopo il fit. Non dividere per D(t0) quasi nullo.

Secondario proposto: vettore di centroidi di polarita/forma, per valutare il trasporto in posizione. Scelta
esatta delle componenti e likelihood da fissare; usare differenze circolari o coordinate locali con ramo
comune, non una normale sulle longitudini grezze al taglio. Una polarita assente rende queste componenti
non definite: D e flussi restano disponibili dove misurabili.

Flussi e variazioni sono diagnostici e/o componenti secondarie da dichiarare. Non moltiplicare likelihood
indipendenti per pixel, D, tilt, separazione e centroidi ottenuti dalla stessa mappa. Evitare identita come
Phi_net=Phi_pos-Phi_neg in un vettore trattato con covarianza non singolare. Se si usa un vettore congiunto,
modellarne covarianza, unita, componenti mancanti e trasformazioni/Jacobiani. Tenere i punteggi primario e
secondario separati, salvo una distribuzione congiunta realmente specificata.

## 4. Errore iniziale, finale e discrepanza

Schema generativo concettuale: y0=x0+e0, y1=T_m(x0)+d_m+e1. x0 e la regione iniziale latente; T_m il trasporto;
d_m contiene processi non rappresentati e discrepanza, non automaticamente nuova emersione.

Per un trasporto lineare e nella stessa rappresentazione, il residuo y1-T_m(y0) contiene e1-T_m e0+d_m.
La sua parte osservativa ha covarianza

    R11 + T_m R00 T_m^T - R10 T_m^T - T_m R01.

E un'identita non condizionata sotto le ipotesi dichiarate, **non** da sola la likelihood condizionata a y0.
Quella richiede un modello per x0/errori e la corretta integrazione. Per osservabili non lineari (centroidi,
tilt) questa formula non si trasferisce direttamente: propagazione o approssimazione da verificare sui sintetici.
Non aggiungere due sigma scalari in quadratura fingendo che la mappa iniziale sia esatta o gli errori indipendenti.

C misura differenze a 1–2 ore, non R00/R11/R01 separati. Errori correlati possono rendere C troppo piccolo
per i giorni. Fattori 0,5/1/2/4 sono sensibilita, non copertura garantita. Un uso di C richiede confrontabilita
per flusso, geometria, epoca e campione; non chiamare sigma strumentale una scala di differenze.
I residui di persistenza dei soli dati di sviluppo informano il complesso errore+evoluzione, non il rumore puro.

Proposta operativa da studiare: distribuzione di lavoro dei residui con scala condivisa e termini di discrepanza
con la stessa famiglia/prior per i candidati. Eventuali scale specifiche di modello vengono stimate solo nello
sviluppo, con penalizzazione probabilistica coerente; non rendere il modello preferito libero di gonfiare la
varianza senza riportarlo. Priori e dipendenze di gruppo/temporali devono essere fissate prima della verifica.
Censimento di informazione insufficiente e parametri non identificabili esplicito.

La selezione del controllo al massimo USFLUX condiziona anche i residui. Una likelihood meccanistica assoluta
richiede trattare quella selezione; una densita di lavoro calibrata sulla stessa popolazione puo essere usata
per valutazione predittiva condizionata dichiarata, non venduta come evidenza della completezza fisica dell'SFT.

## 5. Ranking e verifica

Principale proposto: log-densita predittiva dei dati di verifica, integrando parametri, effetti nuovi ed errore
iniziale secondo il modello. Dipendenze fra osservabili e regioni rispettate; punteggi per componente/blocco,
non migliaia di pixel come repliche indipendenti. Stessa suddivisione e stessa disponibilita per i candidati.

Riportare differenze dei punteggi con incertezza e adeguatezza assoluta: residui, code, dipendenza da lag,
flusso e geometria. Tutti i modelli possono essere inadeguati. L'eventuale vincitore e relativo ai candidati,
alla popolazione selezionata e alle prior, non una dimostrazione causale del meccanismo di trasporto.

Bayes factor opzionali solo con likelihood/evidenze verificate e prior proprie, con sensibilita. BIC opzionale
secondario solo se ML e condizioni giustificate: non applicare REML o sostituire arbitrariamente n=record con
n=pixel/blocchi. La difficolta del calcolo dell'evidenza non deve bloccare il confronto predittivo verificabile.

## 6. Stati, prove e cancelli

- Input/stencil non validi e fallimenti numerici distinti dai mancati osservabili. Nessuna sostituzione del dato
  fallito con zero; se il campione comune si riduce, pubblicare perdite per modello e cause, non solo i casi facili.
- Test indipendenti: identita del trasporto, sola rotazione nota, diffusione nota; errore iniziale correlato al
  finale; nuova emersione non modellata; polarita assente; taglio angolare; ripetizione di regioni/famiglie;
  modelli indistinguibili a lag breve; errori di supporto e convergenza. Prove senza vittoria obbligatoria di MS.
- Prima della corsa: protocollo operativo e codice approvati/fissati, input e split con SHA, semi/durata/estensioni
  e criteri numerici specificati. Output conservati prima della lettura, riconteggio indipendente e rapporto.
- Nessun uso dei dati di verifica per selezionare la famiglia della likelihood, la scala d'errore o il candidato.

## 7. Decisioni aperte per la revisione

1. Quale parte della verifica e ancora esclusa dallo sviluppo? Dichiarazione di non cecita e strategia concreta.
2. Dipolo primario e vettore secondario: componenti, supporti, mancanze e potere discriminante sul disegno.
3. Modello operativo di errore iniziale/finale e discrepanza: cosa C identifica e cosa deve restare un'ipotesi.
4. Likelihood/prior e dipendenze; campione di sviluppo sufficiente per separare scale e discrepanza?
5. Griglia SFT separata o miscela prespecificata, senza fit dei parametri fisici alla verifica.
6. Punteggi congiunti, ricampionamento per gruppi, regole d'arresto e riconteggio indipendente.

Queste scelte restano aperte: non e un protocollo pronto per congelamento. Prima chiudere BQ/A1/C nelle
rispettive sequenze, poi finalizzare BT con i risultati ammessi e i limiti di non cecita registrati.

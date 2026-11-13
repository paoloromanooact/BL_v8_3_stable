# T5: diagnosi mirata del fallimento sui salti — documento di lavoro

**2026-11-13. Non è un protocollo congelato. Nessun nuovo calcolo eseguito.**
Candidato prioritario HMI, accanto al controllo morfologico. Scopo: capire
il fallimento prima di proporre un'altra procedura per il quenching
dell'efficienza. Non riabilita T5 e non modifica la validazione P2f.

## 1. Punto di partenza

T5 misura η = ΣD*/ΣΦ per cella CR × emisfero. La procedura M usa una
componente individuale e una componente temporale AR(1) bivariata.
Nella [validazione P2f](P2F_VALIDATION_RESULTS.md), lo scenario 7 (salti
di 20 CR, livelli separati fra emisferi) dà 3,35% di falsi verdetti contro
il limite 3%; a effetto −0,3·η̄, copertura 96,1% e coda inferiore 2,3%.
T5 resta descrittivo; nessuna sua applicazione confermativa ai dati reali.

Il risultato non identifica da solo la causa. Né l'insuccesso del bootstrap
B nel pilota né le diagnosi della precedente P2e sono una soluzione già
verificata per M sul disegno reale.

## 2. Domande da separare

| Possibile problema | Controllo da progettare |
|---|---|
| Scala della varianza temporale sottostimata | Confrontare la varianza stimata della pendenza con quella del processo generatore, sullo stesso disegno e con la stessa aggregazione T5. |
| Forma temporale AR(1) inadeguata ai salti | Confrontare la covarianza del generatore con quella AR(1), proiettate sul contrasto che stima β_η; non soltanto φ o autocorrelazione al ritardo 1. |
| Componente individuale o sua stima | Separare contributo individuale e temporale; controllare la funzione di varianza e il peso delle unità influenti. |
| Intervallo normale e code della statistica | Distinguere bias, scala e forma della distribuzione di (β̂−β_vero)/SE, separatamente sotto nulla e sotto effetto. |

Il caso 10 (salti di 13 CR con livello condiviso fra emisferi) è un confronto
utile, ma cambia insieme durata e dipendenza emisferica: non separa le due
cause. Un eventuale confronto fattoriale andrebbe pianificato, non dedotto
dal semplice superamento di quello scenario.

## 3. Primo passo limitato

Preparare un protocollo diagnostico non cieco che usi gli output P2f già
disponibili per T5: scenario 7 sotto nulla e ai quattro effetti, confronti
0/1/2 sotto nulla e 1/2 sotto effetto; scenario 10 solo come contrasto
descrittivo con i limiti indicati. Elencare prima tabelle, grafici e regole
di interpretazione. Le differenze fra scenari sono descrittive, senza
presumere appaiamento dei cataloghi con semi distinti.

Usare dapprima solo `VALIDATION_RAW.csv.gz` e i riassunti, preservandoli.
Per ogni gruppo: numero di tentativi/errori, bias, dispersione di β̂,
SE stimati, distribuzione standardizzata e due code. Non basta un rapporto
fra mediane per spiegare i falsi verdetti: la dipendenza fra errore di stima
e SE è parte della domanda. Gli errori restano nel denominatore dichiarato.

I parametri veri e le covarianze del generatore servirebbero per distinguere
meccanismi. Se richiedono rigenerazioni o bracci oracolo, specificare quei
controlli in un piano successivo prima di eseguirli, sullo stesso disegno
sintetico; nessuna risposta reale necessaria.

## 4. Vincoli del seguito

Gli scenari e i semi P2f, ormai esaminati, diventano materiale di sviluppo
per T5. Un metodo modificato richiede un protocollo nuovo e validazione
indipendente con semi mai usati, scenari a salti ancora decisivi e regola
di arresto. Non cambiare soglie o eliminare lo scenario fallito per farlo passare.

Il passo produce una diagnosi, non la promessa di un test riuscito. Se non
emerge una procedura validabile, T5 rimane descrittivo. La morfologia può
chiarire che cosa significa η nelle HARP complesse, ma non risolve da sola
il controllo dei falsi verdetti. MDI resta rinviato e non è prerequisito.

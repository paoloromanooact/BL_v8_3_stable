# Pilota MDI — revisione dell'analisi descrittiva L1

23 novembre 2026, Codex. Codice 107e78c. Nessuna analisi sul reale eseguita qui.

**Non ancora via a --run.** Le funzioni di resa, le differenze assiali/Joy e la struttura del bootstrap sono
impostate correttamente, ma il riconteggio non certifica ancora tutti i prodotti e alcune scelte non riproducono
il testo congelato. Si corregge il codice; non si cambiano retroattivamente protocollo o risultati conservati.

## 1. Riconteggio: nove controesempi ancora accettati

La sonda `scripts/mdi_pilot_analysis_l1_review_probe.py` usa solo dati sintetici, una base positiva e due repliche
bootstrap per rendere economici i controesempi. Con gli hash dei prodotti aggiornati sono accettate tutte queste
mutazioni, una alla volta:

1. `cause_map_missing = 999` nella tabella delle celle;
2. `ok100 = 999` nelle celle;
3. `N = 999` nelle celle;
4. `projected_yield_100 = 999` nei sottogruppi;
5. `p10_g = 999` nella sintesi della quiete;
6. `d_raw = 999` nella tabella delle coppie;
7. `median_flux_ratio = 999` nel riepilogo Q3;
8. `valid_reps = 0` nei riepiloghi bootstrap;
9. inversione del flag `phi_at_bound` nella sintesi di M.

Ricostruire e confrontare **tutte le colonne e chiavi** degli output, con insieme esatto dei gruppi/celle/cause,
unicità, conteggi e valori mancanti. Comprendere rese main/100 G, numerosità e pesi di popolazione, cause,
percentili e denominatori della quiete, tutte le differenze e informazioni delle coppie, mediane di flusso/tempo,
numero di repliche valide e motivazione degli intervalli mancanti. Un hash aggiornato non sostituisce questo
controllo scientifico. Le ricevute sintetiche o con numero di repliche diverso da 2000 devono restare parziali.

## 2. Terzili di separazione comuni

`q3_pairs(tag)` ricalcola i confini a 100 G: non è quanto prescrive il §5 (confini identici in tutti i confronti).
La sonda ottiene main [4.587807, 7.103964] gradi e sens100 [4.768631, 7.262463].
Fissare una sola volta i confini dalle separazioni delle misure L1 principali riuscite, prima degli scarti;
riusarli a 100 G e successivamente nei confronti full-disk. Farli ricostruire autonomamente nel riconteggio.

I terzili di |LCM| non sono fra le classi fissate nel §5. Per questa corsa ometterei questi sottogruppi aggiuntivi.
Se si vogliono mantenere, serve una nota integrativa dichiarata prima della lettura degli scarti, con un riferimento
unico (per esempio M1 principale) riusato a 100 G: non due classificazioni diverse scelte implicitamente dal codice.

## 3. Distanze temporali e quantità previste

Il protocollo chiede T_AVG MWO contro t_DPD per la sinottica, conservando T_ROT e CT_g per dichiarare il tempo
composito indeterminato. Il codice riporta invece solo `dt_mwo_minus_tcm_h`, rispetto al passaggio stimato.
Esportare t_DPD, istante MWO e la loro differenza; conservare CT_g/T_ROT e, se utile, il confronto con t_cm
come quantità supplementare esplicitamente approssimata. Non attribuire alla sinottica un istante osservativo unico.

Per il confronto fisico conservare anche flussi/componenti e conteggi/aree MDI già disponibili, non il solo rapporto
di flusso. Il rilascio MWO non contiene i conteggi e le aree per polarità: i rapporti di pixel/aree non calcolabili
vanno dichiarati tali, senza inventarli o avviare una nuova misura MWO. Il rapporto non dovrà dichiarare completata
ogni uscita di Q3 se queste informazioni restano indisponibili.

## 4. Provenienza prima della lettura e nel riconteggio

Il runner controlla prodotti e ricevute di selezione/L1; aggiungere l'uguaglianza fra protocollo di L1 e protocollo
corrente e fra SHA del rilascio MWO e quello registrato negli input verificati della selezione. Registrare gli hash
dei moduli della procedura M riusati come dipendenza, oltre al modulo degli angoli.

Il riconteggio dell'analisi verifica solo gli SHA dei META a monte, non gli hash effettivi dei loro prodotti né
le ricevute complete associate. Prima di leggere SAMPLE/L1/MWO deve verificare quegli input e i legami fra loro,
con semantica stretta delle ricevute già adottata. Controllare anche seed/reps nel META dell'analisi.
Regressioni: prodotto L1/SAMPLE modificato con META invariato; ricevuta mancante/parziale; rilascio MWO diverso
da quello della selezione. Nessuna ricevuta completa se un prerequisito non è verificato.

## 5. Risposte ai tre punti aperti

- **M, tolleranza relativa 1e-5:** accettabile come tolleranza numerica dichiarata di questo fit esplorativo,
  senza verdetto. Controllare separatamente stato di errore, finitezza, dominio dei parametri, flag di bordo,
  n/celle/rotazioni. Non saltare i parametri mancanti e poi certificare il resto come fit riuscito. La piccola
  differenza sintetica non dimostra da sola che l'ottimo sia piatto: formulare come sensibilità numerica osservata.
- **BARD-MDI:** rinviato con stato e motivo espliciti; nessuna corrispondenza nuova implicita. Non blocca Q1/Q3
  disponibili. Un eventuale matching avrà una nota separata prima dell'esecuzione.
- **|LCM|:** come sopra; non cambiare gruppi fra soglie nello stesso confronto.

## Verifica e seguito

Selftest runner 14/14; la sonda aggiuntiva parte da una base accettata e riproduce i nove difetti descritti.
Il suo piccolo bootstrap è soltanto una prova di rifiuto delle manomissioni, non una validazione statistica.
Nessun tilt MDI reale o confronto reale letto, nessuna rete o modifica ai risultati HMI/MWO.

Claude corregge questi punti e aggiunge le regressioni, poi revisione mirata prima della corsa reale.
Il perimetro resta Q1 e Q3 descrittivi; Q2/ripetibilità attendono L2, Q4 resta rinviato. Nessuna nuova simulazione lunga.

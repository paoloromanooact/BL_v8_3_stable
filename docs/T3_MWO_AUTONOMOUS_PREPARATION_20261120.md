# Preparazione autonoma Codex — T3 MWO, 20 novembre 2026


## Controllo leggero successivo, 20 novembre circa 17:20

Controllati in sola lettura i processi sul sistema host: padre presente, cinque worker attivi a circa
100 % CPU ciascuno. Dal sandbox i processi host non erano visibili: la verifica è stata ripetuta fuori dal
sandbox. Nessun segnale o cambiamento alla corsa; log ancora al benchmark, previsto prima del primo blocco.

Esaminate le modifiche IN LAVORAZIONE di Claude, senza sovrascriverle o includerle in questo commit:
README distingue ora pilota 2010–2013 e confronto del catalogo 2010–2012, limita il rapporto 16 % al pilota,
distingue il CSV dei 26 esclusi dai registri delle perdite e chiarisce le unità dei coefficienti di Joy;
le fonti non garantiscono più uno scarto magnetico/fotografico costante. La figura di beta3 etichetta i
bersagli come riferimenti della sola analisi principale e le sensibilità come nominali; la figura vuota
P1 viene omessa. Aggiunte barra colore del flusso e didascalia sui punti esterni della boxplot.

Nuova guardia delle figure provata separatamente su metadati sintetici: caso valido accettato, prodotto
cambiato e stima obsoleta rifiutati. Selftest aggiornato 2/2 positivo. Queste prove non leggono risultati
reali. Le modifiche appartengono ancora alla working tree di Claude al momento della verifica; la presente
nota non è una revisione delle nuove voci bibliografiche che Claude sta completando.


Ambito: strumenti di verifica e preparazione del rilascio durante la validazione R4. Nessun tilt del catalogo
lungo è stato letto, nessuna patch applicata alla produzione, nessun dato o modulo della griglia modificato.
L'handoff operativo resta gestito da Claude; questa nota raccoglie il lavoro e i rilievi di Codex.

## Consegne

1. `scripts/t3_mwo_release_recount.py`: verificatore indipendente del rilascio, senza importare l'esportatore
   nel controllo reale. Prima dei dati verifica conservazione e hash di catalogo/stabilità/stima/rilascio,
   ricevuta completa della stima e legami fra i META. Ricostruisce ogni colonna delle due tabelle per identità
   (gruppo, giorno), dizionario delle colonne, copie dei confronti, identità dei 26 FITS esclusi, stime e
   numerosità di Joy e replay indipendente dei percentili al seme fissato. Il replay non valida la copertura
   statistica del bootstrap. Le ricevute sintetiche o interrotte sono parziali; il comando reale viene dopo
   la conservazione del pacchetto. Non è stato eseguito sui tilt reali.
2. `scripts/t3_mwo_final_sequence_probe.py`: prove per stadi su fixture sintetiche in un albero temporaneo,
   senza collegare data/ o results/ reali. Collegamento della patch nella copia, stabilità e proprio
   riconteggio, stima e proprio riconteggio, esportazione e nuovo verificatore. Le fixture dei diversi stadi
   sono separate; non è una nuova validazione di M e non produce ricevute valide per i dati reali.
   Aggiornato il vecchio probe di collegamento con i nuovi META e READ richiesti dal writer.
3. `docs/T3_MWO_R4_FINAL_RUNBOOK.md`: comandi, ordine, prodotti da conservare e controlli di arresto fra le
   fasi. Nessuna autorizzazione ad anticipare la sequenza, nessun comando di interruzione della simulazione.
4. `scripts/t3_mwo_preparation_review.py`: ricostruzione indipendente delle sei tabelle di copertura di
   Claude usando solo metadati, con verifica degli hash degli input e di tutti i prodotti salvati.

## Verifiche eseguite

- Nuovo verificatore: esportazione sintetica valida positiva, valore di tilt modificato rifiutato anche
  aggiornando l'hash del prodotto, ricevuta di stima parziale rifiutata prima di chiamare lettori CSV.
- Prova isolata: tutti e cinque gli stadi del probe superati, inclusi i controesempi e la baseline positiva.
- Sei tabelle di copertura R4 coincidenti; hash dei prodotti corretti. Normalizzati soltanto metadati pandas
  non serializzati e l'interpretazione str/int del terzile letto dai CSV, senza cambiare dati o tolleranze.
- Figure finali di Claude: selftest 1/1 positivo su dati sintetici. Esaminata anche la figura salvata della
  selezione rispetto all'attività: corrisponde alle frazioni ricontate (isolati 24–32 %, tutti 27–38 %).
- Prima della consegna: controllo di sintassi, diff e manifest; script e input della validazione identici
  alla revisione di lancio 89f525f. Non è stato ripetuto il calcolo lungo né tutta la suite del repository:
  le modifiche preparatorie sono verificate con prove mirate e isolate.

## Rilievi a Claude da recepire prima delle figure e del pacchetto reali

1. **Periodo del pilota.** Il README §7 indica 2010–2012 accanto ai 211 record del pilota. Dai soli campi
   temporali e status di MWO_PILOT/ROWS.csv: i candidati coprono 2010-05-03…2013-12-29 e i valutabili
   2010-05-04…2013-01-14. Distinguere il pilota 2010–2013 dal controllo S2-P1 del catalogo 2010–2012.
   Anche il rapporto di flusso 16 % va attribuito al pilota, non generalizzato all'intera sovrapposizione.
2. **Bersagli nella figura delle sensibilità.** `fig_beta3` disegna i TARGETS principali attraverso tutte
   le righe. Cambiando matrice, campione, pesi o attività cambia anche la proiezione dello scenario. Etichettare
   quelle rette come riferimenti della sola analisi principale o mostrarle in un pannello separato.
   La validazione sul disegno principale non certifica automaticamente tutte le sensibilità: precisarlo
   nel titolo/didascalia. Nessun nuovo calcolo di bersagli è richiesto da questa osservazione.
3. **Guardia delle figure.** Il comando reale delle figure finali controlla soltanto la presenza dei META.
   Prima dell'uso reale, richiedere il nuovo riconteggio del rilascio completo e legato, prodotti con hash
   corretti e corrispondenza fra la stima e il rilascio correnti. Una figura da prodotti superati non deve
   apparire come risultato verificato. Gestire esplicitamente n=0 nel confronto P1 senza tracciare una
   mediana NaN. Questo non riguarda la validazione in corso.
4. **Confronti di Joy.** k in gradi nel modello gamma = k sin|lat| non coincide numericamente con la pendenza
   di una regressione tilt-latitudine in gradi per grado. Il confronto con la letteratura richiede le forme
   funzionali, popolazioni, pesi e convenzioni indicati nel piano, e restare descrittivo.
5. **Stato delle esclusioni nel README.** L'esportatore corrente lista i 26 file A2/A3. Il testo «tutti i file
   esclusi» non deve far credere che il CSV includa già i due illeggibili e tutti gli altri stati di mancata
   misura. Distinguere elenco di esclusione strumentale e registri completi di tentativi/perdite.
6. **Leggibilità (non bloccante).** La figura tempo-latitudine colora per log del flusso: aggiungere una barra
   colore o una legenda esplicita. Dichiarare nella didascalia della boxplot che i punti esterni non sono
   mostrati; restano conservati nei dati e non costituisce un'esclusione.

## Precedenti bibliografici

Controllati direttamente anche gli abstract primari di [Li & Ulrich 2012](https://arxiv.org/abs/1209.1642)
e [Wang et al. 2014](https://arxiv.org/abs/1412.2329). Confermano il precedente di tilt magnetici MWO/MDI e il
confronto MWO–DPD. Il catalogo qui preparato non va presentato come il primo. Il conteggio pubblicato di circa
30 600 sunspots non è confrontabile automaticamente con i nostri gruppi DPD a una misura per gruppo: vanno
verificate unità e deduplicazione prima di confrontare dimensioni e resa.

In T3_MWO_REFERENCES.md, la frase «uno scarto costante è atteso e non indica un errore» è troppo forte:
Wang descrive differenze di popolazione e di dipendenza dalla latitudine, non garantisce uno scarto costante
nel tempo o con l'attività. S1 resta un controllo relativo fra epoche. La bibliografia marcata da verificare
resta tale: questa revisione non certifica le voci senza testo completo né la disponibilità del catalogo altrui.

## Come ripetere questi controlli

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/t3_mwo_release_recount.py --selftest
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/t3_mwo_final_sequence_probe.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/t3_mwo_preparation_review.py
```

I nuovi strumenti sono pronti per una revisione incrociata di Claude prima dell'uso sui dati reali.

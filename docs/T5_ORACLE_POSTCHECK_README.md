# T5-D2 — verificatore separato pronto, corsa non esaminata

## Stato e cronologia

Preparazione tecnica del 13 novembre 2026, autorizzata durante l'attesa di
T5-D2. Nessun output scientifico della corsa è stato aperto per scrivere,
provare o documentare questo verificatore. Sono stati letti il sorgente,
i protocolli, il controllo preliminare già esistente e gli hash degli input
pubblicati. Il verificatore e le sue 77 prove non chiamano generatori, fit
o RNG. Nessuna nuova esecuzione scientifica dei protocolli è stata avviata.
Il produttore `2bf262f` e i suoi file restano intatti.

- `bd3616a`: specifica tecnica e fotografia degli input, prima del codice.
- `44e7417`: prima implementazione; 73/73 prove su tabelle costruite a mano,
  eseguite con albero pulito. Ricevuta originale conservata in `RUN1/`.
- `9bd1e2e`: rafforzati la ricevuta, il confronto ai limiti della copertura
  e la prova di scrittura/rilettura completa CSV/GZIP. 77/77 prove, sul
  commit pulito. Ricevuta corrente nella cartella principale dei selftest.

I controlli ordinari del repository sono passati: 60 test pytest, sintassi
di 43 file Python, shell e help del launcher. I due avvisi di correlazione
indefinita provengono dalla prova di input costante P3. La suite ordinaria
usa le proprie fixture sintetiche e i propri semi fissi; non sono output
scientifici di T5-D2. Ricevuta tecnica in `REPOSITORY_CHECKS.json`.

Lo SHA del codice, della specifica e della tabella dei test è nella ricevuta.
I commit successivi di sola documentazione non invalidano i test del codice
invariato. RUN1 resta un archivio riferito al codice precedente, non una
ricevuta utilizzabile con il codice corrente. Nessun test preliminare è
stato invalidato; non ci sono nuove esecuzioni scientifiche.

## Perché un nuovo controllore

La revisione di `diag_t5_oracle.py` ha trovato un problema di lettura:
`pandas.read_csv` senza opzioni sul riepilogo interpreta la stringa `null`
come valore mancante. Inoltre il controllo storico non ricalcola verità,
code, tutti i momenti e i quantili del riepilogo, né i conteggi del file
appaiato. Non basta quindi come controllo finale del contratto documentato.
Questi sono rilievi sul codice e prove costruite a mano, non errori osservati
negli output della corsa. Il controllore storico non è stato modificato.

Il nuovo `python/sharpbl/t5_oracle_postcheck.py` usa `csv` della libreria
standard: conserva `null` come testo, legge esplicitamente i numeri e non
importa il produttore né il suo riepilogo. Confronta:

- tutte le chiavi attese: 188000 righe, 46 gruppi, 38 confronti appaiati;
- produttore atteso, protocolli, emendamento, input e ricevuta preliminare;
- verità iniettate, campi finiti, stati di errore, due semi-intervalli,
  verdetti e indicatori di copertura/coda;
- A0 con tutte le 32000 chiavi pertinenti della validazione originale;
- ogni colonna del riepilogo, inclusi R, dispersione di z, quantili,
  frequenze, errori e incertezze Monte Carlo;
- conteggi appaiati e matrice completa 4×4, mantenendo distinti errore
  e non deciso. I casi validi possono differire tra bracci e sono contati.

Gli A0 errore il cui beta non fu conservato nel riferimento sono dichiarati,
non presentati come confronti numerici riusciti. A3 deve restare senza
errori e avere SE costante per scenario sul disegno fisso. I criteri tecnici,
comprese le tolleranze dimensionali, sono nella specifica già registrata.

## Prove

I 77 controlli usano piccoli esempi deterministici, non cataloghi di
produzione. Comprendono esempi con tutti i quattro esiti, beta zero,
valori attesi noti per varianza, quantili, frequenze e MCSE; alterazioni
intenzionali di chiavi, verità, flag, intervalli, provenienza, metadati,
riferimento A0 e tutte le colonne del riepilogo; matrici appaiate con
errori; limiti chiusi della copertura; rifiuto di ricevute obsolete e di
una corsa incompleta prima dell'apertura dei file scientifici.

Una parte delle tabelle di esempio è costruita usando il riconteggio per
riempire il formato: queste sole prove non sarebbero una verifica numerica
indipendente. Le formule e i quantili hanno perciò anche casi con valori
attesi fissati separatamente. Le prove e la revisione sono interne alla
stessa sessione: non vengono presentate come revisione esterna indipendente.

## Uso dopo la conclusione della corsa

Non è ancora stato eseguito sui file T5-D2. Dopo la fine del processo e
prima dell'interpretazione, il comando preparato è:

```bash
.venv/bin/python python/sharpbl/t5_oracle_postcheck.py --check
```

Il comando richiede la ricevuta dei selftest coerente con il codice e il
marcatore finale letterale `fatto` nel log, oltre ai quattro output. Non
apre gli output se la corsa è incompleta. Scrive soltanto in una cartella
nuova `results/T5_ORACLE_POSTCHECK/` e rifiuta se esiste già; non riscrive
alcun file originale. Conserva hash prima/dopo dei quattro input, provenienza
separata di produttore e verificatore, elenco dei controlli, riconteggi,
discrepanze e transizioni. Il terminale mostra soltanto lo stato tecnico.

Per ripetere le prove del codice invariato, senza usare i risultati:

```bash
.venv/bin/python python/sharpbl/t5_oracle_postcheck.py --selftest --out /tmp/t5-postcheck-selftest-new
```

La cartella deve essere nuova. Se un controllo effettivo fallisce si
conservano rapporto e input, e si chiarisce il problema prima di leggere
le sintesi o adottare un conteggio. Non si ritocca il produttore storico.

## Limiti scientifici invariati

Il superamento del controllore confermerebbe coerenza tecnica, aritmetica
e provenienza negli aspetti controllati, non la validità di una procedura
statistica nuova. T5 resta descrittivo; gli oracoli non sono applicabili
ai dati reali. Un'eventuale nuova procedura richiede un protocollo proprio
e una nuova validazione. Nessun risultato osservativo o protocollo è cambiato.

Nella futura lettura dei risultati ricordare anche la distinzione del
sorgente: lo scenario 7 ha livelli indipendenti nei due emisferi ma fase
dei salti condivisa; non si devono descrivere i due processi come interamente
indipendenti. Il pretest della covarianza dello scenario 10 usa la fascia
28200000+k; la differenza dalla fascia scritta nel piano riguarda il solo
pretest e va dichiarata, senza cambiare retroattivamente gli output.

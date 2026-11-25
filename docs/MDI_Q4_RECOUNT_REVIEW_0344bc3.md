# Q4 MDI — revisione del riconteggio 0344bc3

25 novembre 2026, Codex. Codice esaminato: `scripts/mdi_q4_recount.py`,
SHA-256 `adf69a1509f31d97714e455868162352adf972b747fd2bd81012b294d6775870`.

**Esito: non ancora via al `--check` reale.** La base sintetica con due
realizzazioni passa il confronto completo. Sei alterazioni dei prodotti
vengono pero accettate: la ricevuta non certifica ancora il confronto
integrale dichiarato. Non e una dimostrazione di errori nei risultati Q4.
Non sono stati letti RAW, SUMMARY o CRITERIA della corsa reale, ne eseguito
il riconteggio reale. Runner, note congelate e prodotti reali invariati.

## 1. Tolleranze dei modelli protetti

La motivazione matematica e corretta: la forma dello scarto e nel modello,
quindi la sua proiezione sulla riga del coefficiente principale e nulla.
Non interpretare il rapporto ottenuto dividendo per un residuo numerico
come una tolleranza fisica misurata. Questo vale solo per la famiglia
protetta, sotto la forma dello scarto prevista dal modello; non per scarti
strumentali arbitrari o altre famiglie.

Il verificatore deve pero controllare i valori prima di normalizzarli:
- riga 698 usa `abs(v) >= 1e6` e `isinf(v)`: anche una tolleranza negativa,
  incluso meno infinito, diventa piu infinito ed e accettata;
- nel SUMMARY il valore booleano restituito da `protected_tolerances` viene
  ignorato (riga 809): anche una tolleranza zero viene cancellata dal
  confronto;
- per B1 sono selezionati solo i valori finiti. Distinguere esplicitamente
  le righe riuscite dalle righe fallite e i valori non definiti ammessi.

**Controesempi confermati con `check()` sintetico:** tolleranza RAW bA/A
posta a -1e30; tolleranza SUMMARY bA/A posta a zero. Entrambi accettati.
Richiedere positivita e dominio appropriato, validare anche SUMMARY e
preservare le maschere dei valori mancanti. Nei casi di bersaglio nullo
servono regole esplicite; non sostituire indiscriminatamente gli errori
con infinito. Le famiglie non protette restano confrontate numericamente.

## 2. Confronto integrale di YIELD_EFFECTS e delle scelte

Le righe 823–826 controllano lunghezza e valore di ciascuna chiave visitata,
ma non l'unicita e la copertura dell'insieme delle chiavi. Le colonne
`step` e `change` non sono confrontate.

**Controesempi confermati:** sostituire la seconda riga con la prima
(chiave duplicata e un passo assente); alterare l'etichetta `step` della
prima riga. Entrambi accettati. Ricostruire tutte le colonne e confrontare
con chiavi uniche, copertura esatta e schema esatto, come negli altri frame.
Evitare `int(step_order)` che puo nascondere un valore frazionario.

La riga 838 controlla solo `len(implementation_choices) == 9`.
**Controesempio confermato:** sostituire le nove scelte con nove stringhe
`wrong` viene accettato. Confrontare il contenuto atteso e l'ordine, senza
importare il runner per ottenerli. Per CRITERIA verificare anche lo schema
esatto; attualmente viene confrontato solo un insieme nominato di campi.
Non si richiede di ricalcolare metadati operativi quali il tempo di corsa.

## 3. Conteggi e flag: dominio ed uguaglianza esatta

`close_cols` applica la tolleranza floating point anche ai conteggi numerici,
in contrasto con il contratto dichiarato. Il confronto deve dipendere dal
significato della colonna, non dal dtype del CSV controllato.

**Controesempio confermato:** un conteggio CELL_COUNTS incrementato di
1e-9, con colonna convertita a float, passa. Richiedere valori finiti,
interi e non negativi ove previsto, poi uguaglianza esatta. Stessa regola
per conteggi di righe, realizzazioni, celle e flag; i rapporti e i conteggi
effettivi di Kish restano grandezze continue.

## 4. Provenienza dei file usati adesso

Rilievo da lettura del codice, non da modifica di file reali: il gate
confronta gli hash dichiarati nel META con le costanti e verifica la
ricevuta della nota e i 17 input. Non controlla pero i nove file di codice
riusati registrati nella ricevuta, che vengono poi importati, ne l'hash
corrente dei testi nota/A2, della ricevuta A2 e dei vincoli padre/regole.
Un hash corretto nel META della corsa storica non dimostra che il file
letto dal riconteggio sia ancora quello.

Prima di importare le dipendenze e di ricostruire, verificare questi file
contro gli hash fissati nella ricevuta ancorata, con insieme esatto.
Aggiungere prove del gate che alterano i percorsi/sha in una fixture e
verificano l'arresto prima del calcolo, senza modificare i dati reali.
Nella ricevuta finale registrare anche l'hash del riconteggio e dei suoi
input effettivi, oltre agli hash degli output confrontati.

## Prove e consegna

Sonda: `scripts/mdi_q4_recount_review_probe.py`. Genera soltanto i prodotti
sintetici del selftest, ricostruisce la base con il codice indipendente e
riusa quel risultato atteso per le mutazioni dei soli prodotti. Non legge
prodotti Q4 reali e non scrive ricevute complete. Il selftest originale
24/24 e dichiarato dall'autore; non e stato rieseguito integralmente in
questa revisione, che usa la base e le controprove aggiuntive.

Esito conservato in `docs/MDI_Q4_RECOUNT_REVIEW_0344bc3_RESULTS.json`.
Il caso esplorativo di un campo META aggiuntivo non e considerato un
rilievo da solo: il problema sostanziale e il mancato controllo dei campi
scientifici e di provenienza richiesti.

Prossimo passo di Claude: chiudere i quattro gruppi di rilievi con prove
sintetiche; poi revisione di chiusura e `--check` reale. **Non rilanciare
Q4**, non cambiare il protocollo o il runner conservato, non leggere le
classificazioni prima della ricevuta verificata.

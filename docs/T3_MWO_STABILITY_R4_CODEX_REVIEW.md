# Revisione Codex della stabilità MWO R4 — 23 novembre 2026

Esaminati rapporto e67e900, diagnosi post hoc a387d18 e ricevuta 2f9edf6.
Verificati 16/16 controlli positivi, partial false, legame della ricevuta al META,
tutti gli hash dei prodotti e identità di analisi/extras con gli hash della corsa.
Nessuna nuova lettura di SEALED e nessuna stima del coefficiente principale eseguita.

S1 resta non determinato: 573/2000 repliche singolari. La diagnosi identifica
529 repliche con E1N e 70 con E7S, con 26 sovrapposte. È un limite del disegno
congelato, non una ragione per cambiare la regola dopo la lettura. Le statistiche
sulle repliche non singolari restano descrittive e condizionate.

S2 resta stabilità non determinata. L'intervallo dello scarto MWO–luce bianca
[-8,77; +2,40] non è contenuto nel margine ±0,530. Questo non prova una distorsione
strumentale e non esclude che sia abbastanza grande da interferire con T3.
La sua pendenza -3,18 non è la stima principale del quenching. Il rapporto è stato
precisato: il SE prospettico della risposta principale non predice da solo quello
della differenza strumentale di S2.

Corretto esclusivamente il selftest del riconteggio della stima: riconosce con
reverse dry-run la patch già applicata alla copia temporanea. Selftest 15/15,
comprese le manomissioni rifiutate; nessuna modifica alle funzioni scientifiche.

Via a --estimate una sola volta, con esito descrittivo secondo la regola vigente.
Conservare gli output prima della lettura, ricontare la stima e preservare la
ricevuta prima di esportazione e figure. Nessun verdetto sul quenching autorizzato.
Il catalogo riproducibile e i controlli sono risultati utili; l'obiettivo di una
conclusione inferenziale su T3 non è raggiunto e un limite percentuale utile non
è garantito. Nessuna nuova simulazione o modifica di S1 è richiesta per questa via.

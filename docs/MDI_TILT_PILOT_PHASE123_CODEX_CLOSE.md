# Pilota MDI — chiusura della revisione delle fasi 1–3

23 novembre 2026, Codex. Base c2e7fb3, dopo la revisione 1a1b384.

Le cinque correzioni sono recepite. Via alla selezione reale, conservazione in Git e riconteggio; se completo
e positivo, via alla misura L1, conservazione prima della lettura e riconteggio completo. Un controllo fallito
ferma la fase dipendente. Questa chiusura non autorizza acquisizioni full-disk né le fasi 4–6.

## Verifiche

- Il confronto della selezione copre POPULATION/SAMPLE/CELLS, colonne utilizzate, pesi, chiavi e valori mancanti.
  Le cinque mutazioni originarie, più duplicato, unità, cella e LCM, vengono rifiutate con hash aggiornati.
- Il centro della quiete viene da CT; sono esportati e ricontati stati e valori dei due lati. La sonda al taglio
  0/360 restituisce entrambe le finestre valide e MAD media 11,1195 G, contro il precedente 7,413 G errato.
- Il riconteggio ricostruisce N, controllo con effemeride, coordinate, quantità esportate e quiete; la riga
  N_ambiguous inventata viene rifiutata. Le prove sintetiche non producono una ricevuta reale completa.
- Sono presenti verifiche del protocollo congelato e dei prodotti della selezione prima della lettura;
  gli SHA delle mappe usate sono ricontati con lettore proprio.
- TAI viene convertito esplicitamente in UTC, normalizzando secondi=60 come intervallo. Il diagnostico torna
  a circa 2,663 gradi, entro i 3 gradi congelati; non è la precisione dei tilt.

## Ultima correzione numerica fatta in revisione

La nuova own_ct del riconteggio usava epoca 2398140.2270 e periodo 27.2752316, propri della formula di Meeus,
anche per ricostruire la funzione a periodo medio del runner. Non è la stessa definizione congelata.
Esempio sintetico: 2000-01-01 00:00 UTC, L=187.81178403062745 gradi: runner N=1958, riconteggio N=1957.
Lo scarto in CT è circa 0,520 gradi; l'esempio è a 0,01 gradi dal confine, non sullo spareggio.

Corrette own_ct e la sua inversa sintetica t_for con l'epoca 2398167.329 e il periodo 27.2753 del protocollo.
La formula resta implementata autonomamente; le costanti e i termini periodici di own_eph restano invariati.
Aggiunta regressione sui due lati del confine (N=1957 e N=1958), confrontata anche con il runner.
Non cambiano protocollo, soglie, selezione o misura: non esistono ancora prodotti reali del pilota.

## Esiti dei controlli

- Riconteggio selezione: selftest 11/11.
- Misura/adattatore L1: selftest 19/19, mappe sintetiche e metadati reali, nessun pixel MDI reale.
- Riconteggio L1 dopo la correzione: selftest 19/19.
- Sonda indipendente aggiornata alla nuova API: base valida, tutte le mutazioni originarie rifiutate,
  quiete al taglio corretta e assegnazione N conforme sui due lati del confine.
- Le avvertenze di conversione dei nanosecondi nei tempi sintetici non fanno fallire i controlli.

La revisione non ha eseguito selezioni, misure MDI reali o richieste di rete e non modifica la catena MWO/HMI.

# Stato del progetto

Riepilogo ricostruito il 2026-09-15 da codice, documentazione e risultati locali;
non è una trascrizione delle conversazioni precedenti.

## Esecuzione di riferimento disponibile localmente

Dati dell'8 maggio 2024, 03:12 TAI; soglia 100 G, massimo |Br| 10000 G,
bitmap >= 1, leading XMAX. Il log riporta 26 FITS scaricati, 13 regioni
elaborate e 7 PNG diagnostici.

- 6 valide senza segnalazioni: 11142, 11149, 11159, 11170, 11178, 11190.
- 3 valide classificate anti-Hale: 11150, 11152, 11192.
- 11152 ha anche tilt ridotto elevato, circa 74.9 gradi.
- 4 non valide per una polarità assente sopra soglia: 11182, 11186, 11187, 11189.

FITS, CSV, PNG e log originali restano locali e non sono inclusi in Git.
Il log del giorno completo termina durante l'attesa dell'esportazione JSOC;
non è disponibile un CSV che ne confermi il completamento.

## Punti da verificare

- Validazione fisica delle regioni segnalate e della convenzione XMAX.
- Convenzioni di tilt, segno del proxy e geometria CEA prima dell'uso scientifico.
- Soglia interna di `process_sharp_day`: 1000 G; launcher: 100 G espliciti.
  La preparazione del repository non cambia questa scelta numerica.
- I test IDL presenti sono procedure manuali, non una suite di regressione
  scientifica automatizzata.
- Alcuni errori vengono intercettati per file; controllare righe del CSV e log
  oltre al codice di uscita del processo.

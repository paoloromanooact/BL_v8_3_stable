# Stato del progetto

## Branch `v8.4-python-gianluca` (aggiornato il 2026-11-09)

Obiettivo scientifico: costruire una serie osservativa della sorgente
Babcock–Leighton (S_BL) per l'era HMI e verificare come tilt, latitudine di
emersione ed efficienza della sorgente variano rispetto all'attività. Dettagli:
`README_V84.md`; passaggio di consegne e prossimi passi: `docs/HANDOFF.md`.

S_BL è un proxy della sorgente iniziale, all'emersione; non misura
direttamente il campo polare che resterà al ciclo successivo (intervengono
evoluzione, cancellazione e trasporto superficiale). La serie contiene una
misura per HARP, che non equivale necessariamente a una misura per regione
fisica (ricomparse, HARP complesse o con più regioni NOAA).

Stato, distinto per livello:

| Livello | Stato |
|---|---|
| Elaborazione dei record selezionati | completa: 14195 record, 7133 HARP (2010-05 → 2026-09) |
| Controlli interni obbligatori | superati (`complete_series` = `validation_passed` = 1; il metodo legacy riproduce la v8.3 sul caso 2024-05-08) |
| Confronto esterno con BARD (P3 C1) | accordo su geometria e convenzioni magnetiche nel campione confrontato (999 regioni, ~69% di BARD); C2 riportato senza esito formale |
| Ampiezza della sorgente (Φ, S_BL, D) | **senza** validazione esterna equivalente (flusso nostro/BARD 1,67 in C1) |
| Inferenza sul quenching (P2d/P2e) | validazione **non superata**; T3 e T5 solo descrittivi; cause non ancora diagnosticate |

Documenti dei risultati: `docs/P3_RESULTS_C1.md`, `docs/P2_RESULTS_DESCRIPTIVE.md`,
`docs/P2_DECISION_DESCRIPTIVE_FALLBACK.md`, `docs/EXPLORATORY_RESULTS.md`,
indice in `docs/RESULTS_INDEX.md`.

---

## Stato della v8.3 (registrato il 2026-09-15, conservato)

Riepilogo ricostruito il 2026-09-15 da codice, documentazione e risultati locali;
non è una trascrizione delle conversazioni precedenti. Per i cambiamenti
introdotti dalla v8.4 sul caso qui sotto (bitmap ≥ 33: 11150 e 11192 senza
pixel interni, 11152 Hale normale) vedere `README_V84.md`.

### Esecuzione di riferimento disponibile localmente

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

### Punti da verificare

- Validazione fisica delle regioni segnalate e della convenzione XMAX.
- Convenzioni di tilt, segno del proxy e geometria CEA prima dell'uso scientifico.
- Soglia interna di `process_sharp_day`: 1000 G; launcher: 100 G espliciti.
  La preparazione del repository non cambia questa scelta numerica.
- I test IDL presenti sono procedure manuali, non una suite di regressione
  scientifica automatizzata.
- Alcuni errori vengono intercettati per file; controllare righe del CSV e log
  oltre al codice di uscita del processo.

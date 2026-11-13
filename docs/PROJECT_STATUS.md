# Stato del progetto

## Branch `v8.4-python-gianluca` (aggiornato il 2026-11-13)

Obiettivi: misurare un proxy osservativo della sorgente Babcock–Leighton dalle
HARP HMI e studiarne il quenching rispetto all'attività solare. La priorità
concordata è HMI; MDI/SMARP e l'esperimento di degradazione sono rinviati.

| Livello | Stato attuale |
|---|---|
| Elaborazione P1 | completa: 14195 record, 7133 HARP (2010-05 → 2026-09); una misura per HARP, non necessariamente per regione fisica |
| Controlli interni e BARD | controlli interni superati; accordo BARD su geometria e convenzioni nel campione confrontato |
| Ampiezza della sorgente | senza validazione esterna equivalente: rapporto dei flussi nostro/BARD-HMI circa 1,67, non una calibrazione |
| Diagnosi P2d/P2e | svolte le analisi A–D; hanno motivato lo sviluppo della procedura M, senza riabilitare i verdetti delle procedure storiche |
| Quenching del tilt, P2f T3 | criteri di validazione superati negli scenari provati; applicazione unica: −3,59° per unità di attività, intervallo nominale 97,5% [−10,58°; +3,41°], **non deciso**; nessun effetto della griglia escluso |
| Efficienza della sorgente, T5 | **non validato** per il fallimento sui salti di livello; resta descrittivo |
| HARP dominanti | 120 controllate numericamente; 30 schede 25S esaminate, nessun errore macroscopico riconosciuto; interpretazione del tilt più debole nei complessi |
| Riproducibilità fase 1 | cinque CSV delle figure P1 rigenerati byte-identici, condizionatamente agli input distribuiti; non verifica tutta la catena |

La misura è al record selezionato vicino al meridiano centrale, non
necessariamente all'emersione; S_BL non è il campo polare dopo il trasporto.
Il controllo numerico e la classificazione morfologica rispondono a domande
separate. Le classi complesse non autorizzano esclusioni a posteriori.

Quadro operativo: [misura HMI](HMI_MEASUREMENT_ASSESSMENT.md),
[quenching e sensibilità](HMI_QUENCHING_SYNTHESIS.md),
[bozza di controllo morfologico](PROTOCOL_HMI_MORPHOLOGY_DRAFT.md).
La bozza morfologica revisionata non è congelata né eseguita. Candidato
prioritario accanto alla morfologia: [diagnosi T5 sui salti](T5_JUMPS_DIAGNOSTIC_DESIGN.md),
ancora documento di lavoro. MDI resta una possibile estensione futura,
subordinata alla confrontabilità e al beneficio statistico atteso.
Prossimi passi e cronologia:
[HANDOFF](HANDOFF.md). Risultati originali: [indice](RESULTS_INDEX.md).

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

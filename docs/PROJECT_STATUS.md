# Stato del progetto

## Priorita correnti — 25 novembre 2026

[Piano comune Codex–Claude](BL_WORK_PLAN.md), da leggere a ogni ripresa:

1. **Controllo della sorgente BL nel modello:** piccolo pilota HMI che confronti
   la mappa magnetica osservata e il bipolo del proxy, con lo stesso trasporto SFT.
2. **Controllo contro il Sole:** confronto dell'evoluzione simulata con
   magnetogrammi successivi esclusi dalla scelta dei parametri.

Inventario completato: [consegna SFT/HMI](BL_SFT_HMI_INVENTORY.md).
Punto 1: protocollo congelato, emendamento numerico e correzioni del runner e
del riconteggio richiesti in [revisione serale](SFT_Q4_EVENING_REVIEW_20261125.md).
Punto 2: geometria rev.4 confermata; ripetibilita §7 attiva per decisione
aggiornata dell'utente. Audit Codex T_OBS/header concluso: riserva conservativa
di 86 coppie in 84 HARP; [rapporto](SFT_HMI_REPEATABILITY_METADATA_20261125.md).
Specificare e congelare la misura prima dei pixel; nessun errore ancora
stimato e nessuna corsa del pilota osservato.
Il primo controlla l'approssimazione dentro il modello; il secondo il
confronto con il Sole. Nessuno dei due piloti e ancora eseguito.

**Aggiunte al piano dall'utente:** ranking bayesiano **BQ del quenching HMI**
e **BT del trasporto superficiale HMI**. Specifiche e controlli propri da
fissare; nessun calcolo bayesiano avviato. BT richiede criteri congelati prima
della lettura della verifica osservativa. Le due priorita SFT restano attive.

**Aggiunta successiva dell'utente:** active-region nests HMI, prima
identificazione e contributo osservativo alla sorgente BL, poi analisi
bayesiana delle dipendenze e del quenching. Voce N nel piano comune;
nessun catalogo di nests gia costruito e nessuna nuova misura eseguita.
Le candidate ricomparse P1e non sono una classificazione di nests.

La parte descrittiva del pilota MDI e conclusa. Q4 e eseguita, ricontata e
letta; rapporto [MDI_PILOT_Q4_RESULTS.md](MDI_PILOT_Q4_RESULTS.md), formulazione
rivista in aaf3d6f. Non rilanciarla. Catalogo MDI completo e nuovo T3 restano
decisioni separate. Stato operativo e assegnazioni in [HANDOFF](HANDOFF.md).

La tabella seguente conserva il quadro storico del 15 novembre; per lo stato
operativo aggiornato usare il piano comune e [HANDOFF](HANDOFF.md).


## Quadro storico del branch `v8.4-python-gianluca` (2026-11-15)

Obiettivi: misurare un proxy osservativo della sorgente Babcock–Leighton dalle
HARP HMI e studiarne il quenching rispetto all'attività solare. La priorità
concordata è HMI; MDI/SMARP e l'esperimento di degradazione sono rinviati.

| Livello | Stato attuale |
|---|---|
| Elaborazione P1 | completa: 14195 record, 7133 HARP (2010-05 → 2026-09); una misura per HARP, non necessariamente per regione fisica |
| Controlli interni e BARD | controlli interni superati; accordo BARD su geometria e convenzioni nel campione confrontato |
| Ampiezza della sorgente | senza validazione esterna equivalente: rapporto dei flussi nostro/BARD-HMI circa 1,67, non una calibrazione |
| Diagnosi P2d/P2e | svolte le analisi A–D; hanno motivato lo sviluppo della procedura M, senza riabilitare i verdetti delle procedure storiche |
| Quenching del tilt, P2f T3 | criteri di validazione superati negli scenari provati; applicazione unica: −3,59° per unità di attività, intervallo nominale 97,5% [−10,58°; +3,41°], **non deciso**; nessun effetto della griglia escluso. Potenza 4,55–11,10 % a −0,2·γ0 nei generatori della validazione, non sul processo reale |
| Efficienza della sorgente, T5 | **non validato** per il fallimento sui salti di livello; resta descrittivo |
| Diagnosi T5-D1 | esecuzione unica su 74000 righe sintetiche salvate; 201 controlli superati. Carenza di scala nello scenario 7; seguita da T5-D2 |
| Diagnosi T5-D2 | controlli oracolo su 32000 cataloghi sintetici, verificatore separato 54/54. Nello scenario 7 sotto nulla (salti di 20 CR), con la componente temporale vera R ≈ 0,98 e falsi 1,90–1,94 %, sotto il nominale (conservativo); con la sola varianza individuale vera cambiamenti piccoli. In questa diagnosi e in questi cataloghi è compatibile con un ruolo principale della componente temporale, senza causa unica né metodo correttivo. SE di A2/A3/A2p ricalcolati in modo indipendente entro le dipendenze condivise dichiarate (superato; A1a/A1b no). Revisione incrociata Codex di fase 2, non cieca. Diagnosi sintetica: nulla è trasferito ai dati reali |
| HARP dominanti | 120 controllate numericamente; 30 schede 25S esaminate, nessun errore macroscopico riconosciuto; interpretazione del tilt più debole nei complessi. Vale per le HARP esaminate, non per l'intero catalogo |
| Morfologia HMI A2 | completata: 90 nuove letture, 30 doppie; accordo primario 24/30, C 23/27 casi entrambi valutabili; condizioni operative per la sola proposta di uno studio distinto su S soddisfatte |
| Riproducibilità fase 1 | cinque CSV delle figure P1 rigenerati byte-identici, condizionatamente agli input distribuiti; non verifica tutta la catena |

La misura è al record selezionato vicino al meridiano centrale, non
necessariamente all'emersione; S_BL non è il campo polare dopo il trasporto.
Il controllo numerico e la classificazione morfologica rispondono a domande
separate. Le classi complesse non autorizzano esclusioni a posteriori.

Quadro operativo: [misura HMI](HMI_MEASUREMENT_ASSESSMENT.md),
[quenching e sensibilità](HMI_QUENCHING_SYNTHESIS.md),
[risultati del controllo morfologico](MORPHOLOGY_RESULTS.md).
Il controllo morfologico è concluso, senza classi concordate o modifiche
alla serie. Il passo consentito è proporre un piano separato su S, non
avviarlo automaticamente. Resta distinto il percorso T5: D1 ha motivato il piano
[T5-D2](PROTOCOL_T5_ORACLE.md), con A1, eseguito, verificato e interpretato
([risultati](T5_ORACLE_RESULTS.md)); il lavoro morfologico non ne ha usato gli output.
Nessuna nuova procedura validata: un metodo per T5 richiede un protocollo proprio
e una validazione con semi nuovi, scenario 7 compreso. MDI resta una possibile estensione futura,
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

# Cronologia

## v8.4 (Python, branch `v8.4-python-gianluca`) — in corso

- 2026-11-13: preparata la bozza completa T5-D1 per la diagnosi del fallimento
  sui salti dagli output sintetici P2f salvati: 17 gruppi previsti, formule,
  denominatori/code, prodotti, controlli e arresto fissati per revisione.
  Lista degli otto input/riferimenti con hash e blob Git; nessun codice
  diagnostico o analisi eseguiti. T5 resta descrittivo; le componenti vere
  richiederebbero controlli separati. Aggiornata la priorità nel passaggio
  di consegne. Protocollo ancora da rivedere e congelare, nessun push richiesto.

- 2026-11-13: recepita la revisione del riordino HMI. Bozza morfologica rev. 2:
  mappe senza annotazioni di esito, ordine casuale, seconda lettura di 30 casi,
  morfologia primaria separata dall'indicatore dei centroidi e regola operativa
  proposta prima delle letture. Diagnosi T5 sui salti indicata come candidato
  prioritario e descritta in un documento di lavoro. MDI rinviato, non abbandonato;
  beneficio statistico non garantito. Nessun piano congelato, codice scientifico,
  immagine o output modificato; nessuna nuova analisi o classificazione.

- 2026-11-13: priorità HMI confermata dall'utente; MDI/SMARP e degradazione
  rinviati. Aggiunte sintesi della misura e del quenching dai risultati esistenti,
  e bozza non congelata per completare la lettura delle schede HARP e collegarla
  ai controlli già calcolati. Aggiornati stato, README, indice e passaggio di
  consegne: T3 P2f non deciso, T5 non validato. Nessun dato, codice scientifico,
  protocollo congelato o output modificato; nessun nuovo calcolo scientifico.

- 2026-11-13: revisione2 della bozza soloHMI: prova di precisione preventiva,
  code dell'attività sovracampionate con fascia centrale, campioni annidati per
  rami economici e sottoinsieme ottico, pesiΦ principali, esclusioni per attività,
  spostamenti medi per gruppo; esiti di accettazione rimossi. Bozza non congelata,
  nessun nuovo calcolo o dato acquisito.

- 2026-11-13: bozza non congelata dell'esperimento soloHMI
  (`docs/PROTOCOL_HMI_LOS_SENSITIVITY_DRAFT.md`): domanda collegata al quenching,
  campione e stress separati, confronti LOS/Br e degradazioni simulate, cinque
  scelte da chiudere prima dei calcoli. Nessun dato nuovo o risultato prodotto.

- 2026-11-11: revisione indipendente di `21e7210`, tre precisazioni recepite nelle
  politiche (scala gamma0, semantica se_var_z e confronto esatto status); congelata la sola
  prima verifica di riproducibilità sui cinque CSV delle figure P1, con input/codice/hash
  e budget fissati, nessun rilancio. Aggiunta bozza di fattibilità MDI/SMARP da fonti primarie.

- 2026-11-11: revisione delle bozze di confronto della riproducibilità, senza rilanci:
  chiavi delle 112 tabelle (111 univoche e una tabella vuota), scale fisiche fisse per
  colonna/test/quantità, conteggi e decisioni esatti anche se float, provenienza del riferimento
  distinta da quella del codice, eccezioni storiche dichiarate. Aggiunto il preparatore
  `scripts/repro_draft_tables.py` con controlli sintetici delle politiche. Regole ancora in bozza;
  nessun risultato scientifico o protocollo congelato modificato.

- Porting in Python (`python/sharpbl/`); il codice IDL v8.3 resta come riferimento.
- Geometria: longitudine e latitudine dalla WCS completa (le mappe SHARP CEA sono
  oblique, centrate sulla patch); centroidi, distanza e tilt sulla sfera.
  La latitudine della v8.3 (sin(CRVAL2) + (j - CRPIX2) dmu) sbaglia fino a ~1 grado.
- Bitmap >= 33 (solo pixel interni alla HARP) invece di >= 1.
- Soglia 100 G ovunque.
- Ciclo assegnato per latitudine nelle finestre di sovrapposizione 2010-2011 e 2017-2021.
- Una misura per HARP (record piu' vicino al meridiano centrale), protocollo
  `docs/PROTOCOL_P1_SBL_SERIES.md`.
- Contributo al dipolo assiale D e D_bal, indipendente da Hale e ciclo.
- Metodo `legacy` che riproduce la v8.3 (verificato sul caso 2024-05-08 03:12 TAI)
  e confronto v8.3/v8.4 (`python/sharpbl/compare_test_case.py`).
- Test su bipoli sintetici: `.venv/bin/python -m pytest -q tests`.
- Protocollo `docs/PROTOCOL_P2_QUENCHING.md` (test del quenching) congelato prima della serie P1;
  numero di macchie emisferico SILSO in `ancillary/SILSO_HEMI/` (con provenienza e SHA-256).
- Protocollo `docs/PROTOCOL_P1B_QUALITY_0x80.md`: i record con QUALITY = 0x80
  (QUAL_TEMPERROR, 2016-04 -> 2017-03) sono accettati con flag e varianti di controllo.
- Protocollo `docs/PROTOCOL_P1C_CYCLE_RULE.md`: soglie fisiche sulla mistura di
  latitudini (vecchio <= 12 gradi, nuovo >= 18, distanza >= 8).
- Selezione dei record, download diretto dall'archivio JSOC (as-is, keyword in
  `.keys.json`), regola del ciclo.
- 2026-11-09, revisione della documentazione dopo una revisione esterna (nessun
  risultato cambiato): obiettivo scientifico esplicito; "una misura per HARP"
  invece di "per regione"; S_BL come proxy della sorgente iniziale; stato
  distinto in elaborazione completa, controlli interni, accordo con BARD su
  geometria e convenzioni, ampiezza non validata esternamente; mancato
  superamento di P2d/P2e non attribuito al numero di cicli; `PROJECT_STATUS.md`,
  README, `P3_RESULTS_C1.md`, schema dell'articolo e prossimi passi in `HANDOFF.md`
  allineati. Precisazione successiva: S_BL e D sono misurati all'istante del
  record selezionato (primario vicino al meridiano centrale), non
  necessariamente all'emersione; tolto "sorgente iniziale".
- 2026-11-09, sviluppo diagnostico (nessun risultato esistente cambiato): diagnosi del
  mancato superamento di P2d/P2e (`docs/DIAGNOSTIC_P2E.md`), discrepanza tra codice e P2e §2
  sulla non applicabilità con ĉ0 ≤ 0 (`docs/P2E_V0_APPLICABILITY_DISCREPANCY.md`, codice non
  modificato), quadro delle sensibilità (`docs/SENSITIVITY_SUMMARY.md`), script
  `diag_summary.py` e tabelle in `results/DIAGNOSTIC/`; piano del controllo A registrato prima
  dell'esecuzione (`docs/DIAGNOSTIC_A_PLAN.md`).
- 2026-11-09, controllo diagnostico A eseguito (`diag_a_variance.py`, risultati in
  `docs/DIAGNOSTIC_A_RESULTS.md`): controlli obbligatori superati; V2–V3 coerenti con H1, V4
  con H2, V5 con H3, V6 no; la varianza non basta a spiegare le frequenze in V3, V4 T3, V6 T5;
  parte individuale sottostimata di circa il 15% (osservazione post hoc). Tabelle di
  `diag_summary.py` rigenerate ad albero pulito (cambiano solo commit e flag).
- 2026-11-09, controllo diagnostico B eseguito (`diag_b_oracle.py`, piano registrato prima,
  risultati in `docs/DIAGNOSTIC_B_RESULTS.md`): con i parametri temporali veri i falsi
  verdetti scendono a 3,0–3,2% in V2–V3 (limite CP ≤ 4%) e la differenza V2/V4 scompare; in
  V1 restano invariati (3,4–3,5%, CP 4,1–4,3%); eccesso residuo di 0,5–1 punto sopra il 2,5%
  in tutti gli scenari.
- 2026-11-09, controllo diagnostico C (piano registrato prima; emendamento A1 non cieco dopo
  un difetto NaN nel braccio C2, esecuzione 1 di C2-T3 dichiarata non valida e conservata):
  la correzione per la leva rende conto della sottostima della componente individuale (H5);
  in V1, correggendola, C2 dà frequenze vicine a quelle del modello nullo del generatore (C1, circa
  3,0–3,15%, entro 2 errori dal 2,5% ma tutte sopra; V1 e V4 non indipendenti) e rispetta il
  limite CP; la vicinanza non dimostra equivalenza.
- 2026-11-09, verifica post hoc di coerenza di C1 (`docs/DIAGNOSTIC_C1_AUDIT.md`,
  `diag_c1_audit.py`): decisioni Monte Carlo concordi con quelle analitiche (1996–1999 su 2000);
  V1–V4 condividono la stessa realizzazione casuale (stessi semi in tutti gli scenari,
  correlazione di z 0,87–1,00), contro l'assunzione di indipendenza di P2d §6; sui gruppi
  con realizzazioni del rumore distinte (stesso disegno) la frequenza analitica è 2,65%, errore
  raggruppato per catalogo 0,13 (correzione successiva: questi gruppi non sono detti
  indipendenti; `diag_c1_checks.py` restituisce un codice d'errore se un controllo fallisce).
- 2026-11-09, controllo diagnostico D (piano e emendamento A1 registrati prima del codice;
  esecuzione unica su 50 000 cataloghi nuovi, semi distinti per scenario): decisione al 2,5%
  sotto il modello nullo del generatore compatibile con il 2,5% (D1, V1 e V4: 2,485%, SE 0,078
  punti; D2, V0–V4: 2,506%); diagnosi di C1 chiusa, prossimo passo la progettazione di P2f.
- 2026-11-11, progettazione di P2f (`docs/P2F_DESIGN.md`, documento di lavoro) e piano del
  pilota di sviluppo (`docs/P2F_PILOT_PLAN.md`, registrato prima del codice; emendamento A1 prima
  del codice; emendamento A2 non cieco, dopo il fallimento del test preliminare 2 sulla funzione di
  varianza, esecuzione 1 conservata come `PRELIM_*_RUN1.csv`): due candidate per T3 e T5 sul
  disegno reale congelato senza risposte reali (M: funzione di varianza + REML AR(1) bivariata
  sulle medie di cella, decisione analitica; B: wild cluster bootstrap ristretto su blocchi di
  13 CR con entrambi gli emisferi, pesi di Webb, CR1), 9 scenari nulli × 1000 cataloghi e potenza
  su 2 scenari × 3 effetti × 300. Test preliminari superati sul commit `67058f6`; pilota avviato
  in modo distaccato. Sviluppo, non validazione: nessun verdetto.
- 2026-11-11, nota d'implementazione del pilota (`docs/P2F_PILOT_IMPLEMENTATION_NOTE.md`,
  registrata durante l'esecuzione e prima di leggere gli esiti, dopo una revisione indipendente
  del codice): convenzioni non fissate dal piano (origine dei blocchi T5 alla CR 2097, componenti
  per rotazione separate per test, mediana di Φ sul disegno), conteggi del disegno in
  `results/P2F_PILOT/DESIGN_CHECKS.csv` (`p2f_checks.py design`), controllo di finitezza e
  riconteggio indipendente da eseguire prima dell'interpretazione (`p2f_checks.py raw`, output
  del pilota mai modificati).
- 2026-11-13, studio di fattibilità MDI/SMARP completato (documentale, nessun dato scaricato): fonti
  primarie (Bobra et al. 2021, Liu et al. 2012, Scherrer et al. 1995, Schou et al. 2012, Bobra et al.
  2014, Hoeksema et al. 2014, BARD), differenze strumentali (solo LOS in MDI, sovrapposizione
  maggio–ottobre 2010, griglia 0,12° contro 0,03°, MDI = −0,18 + 1,40 × HMI, rumore circa 4 volte),
  11 questioni aperte e percorso proposto. `docs/MDI_SMARP_FEASIBILITY.md`.
- 2026-11-13, verifica di riproducibilità fase 1 (piano `0f51e61`): `figures_p1.py` di `120f852` in un
  clone pulito e in un ambiente separato rigenera i 5 CSV delle figure P1 (e i 3 PNG) byte-identici;
  confronto formale superato dopo una correzione dichiarata del comparatore (chiavi mancanti per schema,
  regola §2). `docs/REPRO_PHASE1_RESULTS.md`.
- 2026-11-13, esame visivo delle 30 schede del gruppo 25S (un solo lettore): nessun errore confermato;
  classificazione per HARP (bipolo singolo, complesso multiregione, centroide tra regioni, quasi
  unipolare); le classi non sono errori e non autorizzano azioni sul catalogo.
  `docs/DOMINANT_HARP_VISUAL_25S.md`.
- 2026-11-13, controllo delle HARP dominanti (piano `f805c5a`, esecuzione su `1a22e09`): 120 HARP
  (20 dominanti + 10 controlli per ciclo × emisfero), valori P1 riprodotti; segnalazioni frequenti di
  complessità (più regioni NOAA, flusso fuori maschera, multipolarità); sensibilità a maschera e
  pesatura ≤ 3,4 % di Σ|S_BL|, alla soglia fino al 7,1 %; nessun errore confermato; 25S priorità di
  approfondimento. `docs/DOMINANT_HARP_RESULTS.md`.
- 2026-11-13, applicazione di T3 ai dati reali con la procedura M validata (una esecuzione, `42fcd01`):
  β̂_T = −3,59° per unità di attività, intervallo a livello nominale 97,5 % [−10,58°; +3,41°], esito
  «non deciso»; nessun effetto della griglia escluso; potenza validata bassa, quindi non è evidenza
  di assenza. T5 non applicato (non validato). `docs/P2F_RESULTS.md`.
- 2026-11-13, validazione P2f (protocollo congelato `500c56a`, codice `ed90e15`, esecuzione unica
  su `5c3b664`, 152 000 cataloghi, 2026-11-11/12): controllo indipendente superato (23/23) e
  revisione esterna senza discrepanze; **T3 validato** negli scenari provati (falsi verdetti
  1,61–2,97 %, copertura ≥ 96,60 %, potenza 5–11 % a −0,2·γ0), **T5 non validato** (scenario a
  salti: 3,35 % di falsi verdetti; a −0,3 copertura 96,10 %, coda inferiore 2,30 %), resta
  descrittivo. Risultati in `docs/P2F_VALIDATION_RESULTS.md`. Nessun dato reale usato.
- 2026-11-11, pilota di sviluppo P2f eseguito (esecuzione unica, commit `67058f6`, 10:17–12:06,
  `results/P2F_PILOT/PILOT_*`), controllo indipendente prima dell'interpretazione
  (`POST_CHECKS.csv`: 20 controlli superati, nessuna statistica non finita, riconteggio identico)
  e risultati in `docs/P2F_PILOT_RESULTS.md`: con le regole registrate (≤ 40 falsi verdetti su
  1000 in ognuno dei 9 scenari e `errore` ≤ 2 %) la candidata M è mantenuta per T3 (massimo 24)
  e T5 (massimo 34, scenario a salti) e la candidata B non lo è (oltre 40 in 7 scenari su 9 per
  T3 e 8 su 9 per T5, già 32 e 54 senza componente temporale); scelta: M per entrambi i test.
  Potenza di M bassa in T3 (≤ 0,24 agli effetti provati). Sviluppo, non validazione: nessun
  verdetto, nessun dato reale.
- 2026-11-09, controlli diretti su C1 richiesti dalla revisione (`diag_c1_checks.py`):
  ingressi finiti in tutti gli 8000 casi; verifica diretta delle simulazioni solo nei 400
  casi campionati (finite, verdetti identici); per T3, nel confronto analitico, la
  trasformazione γ → sin γ → γ non cambia nessuna decisione nei 14 000 cataloghi esaminati
  (327 cataloghi e 345 regioni su 80 636 661 con |γ| > 90°; |Δβ| ≤ 1,4% di una deviazione
  standard); i verdetti Monte Carlo non sono stati ricalcolati. C1 non è più chiamato
  "modello esatto".

## Preparazione del repository

- Documentazione riallineata alla v8.3 e configurazione portabile dei percorsi.
- Dipendenze Python dichiarate e dati/output/log esclusi da Git.
- Corretto `--help` come primo argomento del launcher.
- Rimosso il keyword IDL inesistente `/ALL` dal percorso `--all-diagnostics`:
  la routine seleziona tutte le righe quando non sono impostati filtri.
- Aggiunto un controllo locale di sintassi e un riepilogo dello stato scientifico.
- Routine numeriche conservate; documentata la differenza fra la soglia
  interna di `process_sharp_day` e quella passata dal launcher.

## v8.3 — aggiornamento diagnostica

- PNG RGB costruiti da array per evitare artefatti di TVSCL/TVRD.
- Contrasto Br fisso, maschere e centroidi sovrapposti.
- Metadati numerici in file di testo associati ai PNG.

## Evoluzione precedente, ricostruita dalle note incluse

- Avvio tramite tcsh/sswidl per inizializzare SolarSoft.
- Separazione fra elaborazione CSV e diagnostica.
- Uso di una maschera comune e gestione automatica dei segni leading/Hale.

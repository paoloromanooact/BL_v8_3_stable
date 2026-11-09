# Cronologia

## v8.4 (Python, branch `v8.4-python-gianluca`) — in corso

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

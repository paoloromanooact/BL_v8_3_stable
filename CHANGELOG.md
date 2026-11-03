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

# Cronologia

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

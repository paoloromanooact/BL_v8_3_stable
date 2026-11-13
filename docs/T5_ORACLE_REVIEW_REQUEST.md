# Richiesta di revisione T5-D2 — due fasi distinte

2026-11-13. Preparata prima della lettura degli output T5-D2 da questa
sessione. Nessun risultato della corsa è anticipato. Repository locale:
`/home/gianluca/BL_v8_3_stable`, branch `v8.4-python-gianluca`.

## Fase 1 — già possibile, senza output scientifici

Leggi AGENTS.md, HANDOFF.md e i seguenti file:

- `docs/PROTOCOL_T5_ORACLE.md` e `docs/PROTOCOL_T5_ORACLE_A1.md`;
- `docs/T5_ORACLE_POSTCHECK_SPEC.md` e `docs/T5_ORACLE_POSTCHECK_INPUTS_SHA256.csv`;
- `python/sharpbl/t5_oracle_postcheck.py` e `docs/T5_ORACLE_POSTCHECK_README.md`;
- ricevute in `results/T5_ORACLE_POSTCHECK_SELFTEST/`, distinguendo RUN1 dal codice finale;
- scheletro `docs/T5_ORACLE_RESULTS.md`.

Confronta le regole con il sorgente storico `diag_t5_oracle.py`, senza
eseguirlo né modificarlo. Non leggere per questa fase i file
`results/T5_ORACLE/ORACLE_*` o tabelle scientifiche nel log.

Verifica e riporta i rilievi prima di proporre modifiche:

1. La stringa `null` resta testo in tutte le tabelle; chiavi e numeri non
   sono accettati tramite troncamenti o confronti approssimati degli identificativi.
2. Le 32000 chiavi dei cataloghi e i bracci producono il contratto di
   188000 righe, 46 gruppi e 38 confronti, senza leggere la corsa per fissarlo.
3. Produttore, controllore, protocolli e riferimento P2f sono distinti;
   ricevuta dei test legata allo SHA del codice; file stabili durante la lettura.
4. Verità, intervalli, entrambi i semi-intervalli, verdetti e code vengono
   ricalcolati; flag binari, errori e beta mancanti nel riferimento sono trattati esplicitamente.
5. Il riepilogo viene ricontato per ogni colonna, con scale corrette per
   valori circa 1e-25, varianze circa 1e-50 e quantità adimensionali. Le
   prove non dimostrano soltanto che una funzione coincide con sé stessa.
6. Gli appaiamenti includono tutti i quattro stati; denominatori e campioni
   validi per braccio sono dichiarati; errori non convertiti in non deciso.
7. Lo scheletro segue A1, senza riprendere le attribuzioni causali più forti
   del protocollo storico sostituite dall'emendamento e senza introdurre
   una nuova soglia inferenziale o una correzione scelta in anticipo.

Le prove possono essere ripetute con --selftest in una nuova directory
/tmp. Non lanciare simulazioni, fit, applicazioni reali, --check sui risultati
o push in questa fase. Riporta commit esaminato, problemi, gravità e parti
non verificate. La revisione incrociata non è cieca al progetto.

## Fase 2 — dopo conclusione, controllo effettivo e conservazione

Questa fase resta da eseguire dopo la conclusione della corsa. Confermare
fine e quattro output completi; usare il verificatore separato in una directory nuova,
chiarire ogni fallimento prima di interpretare i risultati e conservare
hash e controlli. Non rilanciare il produttore né sostituire riferimenti.

La revisione del rapporto compilato dovrà poi controllare:

- completezza dei 46 gruppi, R/SD(z)/quantili, frequenze con MCSE, errori e denominatori;
- nulli ed effetti distinti, copertura e due code, soprattutto scenario 7 a -0,3;
- appaiamenti e differenze tra A1a e A1b; nessun confronto fra bracci trattato come indipendente;
- A3 con varianza nota senza presunzione di normalità; A2p come specifica
  approssimazione con limite kappa=0,98 nel 10, non come ottimo generale;
- controlli 1 e 2 e contrasto con il 10 riportati anche quando scomodi;
- esposizioni e incidenti, origine effettiva dei dati e assenza di cambiamenti retroattivi;
- letture compatibili con ipotesi, senza causa unica o metodo correttivo
  già validato; gli oracoli non sono trasferiti direttamente ai dati reali;
- conclusione: T5 resta descrittivo con M attuale; eventuale seguito ha
  protocollo proprio, semi nuovi e validazione che conserva lo scenario 7.

Un eventuale problema di codice del verificatore richiede correzione e
nuove prove documentate, non l'adattamento dei risultati per farlo passare.
Un controllo tecnico superato non è una nuova validazione scientifica.

## Revisione morfologica separata, già possibile

Resta disponibile anche `docs/MORPHOLOGY_RESULTS.md`, con
`docs/MORPHOLOGY_INTERNAL_REVIEW.md`, letture bloccate, tabelle e metadati.
Verificare 24/30 classi principali, 24/30 C o 23/27 valutabili, denominatori
P1, quote conservative, separazione delle 30 storiche 25S e limite della
regola operativa: soltanto proporre uno studio distinto su S. Non
riclassificare immagini, modificare letture o cercare un consenso per
superare la soglia. La verifica interna di 553 controlli non sostituisce
questa revisione incrociata.

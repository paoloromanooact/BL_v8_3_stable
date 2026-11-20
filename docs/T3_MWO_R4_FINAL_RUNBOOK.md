# T3 MWO R4 — procedura finale dopo la validazione

Preparazione del 20 novembre 2026. Questa procedura non avvia alcuna fase e non cambia il protocollo.
Il benchmark è una previsione: procedere sulla conclusione effettiva del processo e sul suo codice di uscita,
non sull'orario. La revisione resta un passaggio fra le fasi; non concatenare automaticamente tutto lo schema.

## File protetti durante la corsa

`scripts/t3_mwo_analysis.py`, i moduli `p2f_validation.py`, `p2f_pilot.py`, `p2d.py`,
`results/T3_MWO_CATALOGUE_R4/DESIGN.csv` e `results/T3_MWO_DESIGN_CHECK_R4/TARGETS.json` devono restare
identici alla revisione di lancio `89f525f`. La patch si applica soltanto dopo fine, conservazione,
riconteggio e lettura registrata della validazione. R2/R3 e la corsa interrotta restano agli atti.

## Comandi e verifiche

Lavorare dalla radice del repository BL. Usare `.venv/bin/python` con un solo thread BLAS per i controlli.
Non sovrascrivere una destinazione già esistente: individuare prima la provenienza di qualsiasi cartella trovata.

```bash
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
TASK_PROTOCOL_SHA=4408a0ee78d48f65275a1a4936ce687fe324a35598dd5bb18a8f3e53a01df8ff
TASK_A1_SHA=bc88452b382d739866ff801a14aecf596968e092904906d7d7298355a0e063c5
```

1. **Fine della corsa.** Verificare il codice di uscita, il log, META e prodotti. Conservare in Git gli output
   di `results/T3_MWO_VALIDATION_R4` prima di leggere frequenze o verdetti. Una corsa tecnicamente incompleta
   richiede diagnosi; non costituisce una validazione statistica negativa. Non rilanciare automaticamente.
2. **Riconteggio completo della validazione**, senza selezionare un sottoinsieme di righe:

   ```bash
   .venv/bin/python scripts/t3_mwo_analysis_recount.py --check-validation
   ```

   Conservare `results/T3_MWO_VALIDATION_R4_RECOUNT`; esigere tutti i controlli superati, technical_ok vero,
   ricevuta completa, non parziale e legata al META corrente. Revisione prima del passaggio successivo.
3. **Lettura registrata della validazione:**

   ```bash
   .venv/bin/python scripts/t3_mwo_analysis.py --record-reading --protocol-sha "$TASK_PROTOCOL_SHA" --amendment-sha "$TASK_A1_SHA"
   ```

   Conservare `results/T3_MWO_VALIDATION_R4_READING`. Una validazione negativa ma tecnicamente valida consente
   solo il percorso descrittivo. Il verdetto richiede anche tutti i successivi controlli di stabilità.
4. **Patch approvata, a corsa finita:** `git apply --check patches/T3_MWO_STABILITY_WIRING.patch`, poi
   applicarla e conservare il cambiamento in un commit. Registrare gli hash della patch e dei file risultanti;
   non modificare retroattivamente la provenienza della validazione. Ripetere le prove sintetiche mirate se
   la patch è cambiata dopo la revisione.
5. **Apertura prevista per S1–S4**, non ancora esportazione:

   ```bash
   .venv/bin/python scripts/t3_mwo_analysis.py --stability --protocol-sha "$TASK_PROTOCOL_SHA" --amendment-sha "$TASK_A1_SHA"
   ```

   Conservare `results/T3_MWO_STABILITY_R4`, quindi:

   ```bash
   .venv/bin/python scripts/t3_mwo_stability_recount.py --check
   ```

   Conservare `results/T3_MWO_STABILITY_R4_RECOUNT`, completo e legato al META. Revisionare i risultati,
   distinguendo verdetto possibile, descrittivo e non concludente. Non correggere soglie dopo la lettura.
6. **Stima unica**, dopo il controllo della catena e delle ricevute:

   ```bash
   .venv/bin/python scripts/t3_mwo_analysis.py --estimate --protocol-sha "$TASK_PROTOCOL_SHA" --amendment-sha "$TASK_A1_SHA"
   ```

   Conservare `results/T3_MWO_ESTIMATE_R4`, quindi:

   ```bash
   .venv/bin/python scripts/t3_mwo_estimate_recount.py --check
   ```

   Conservare `results/T3_MWO_ESTIMATE_R4_RECOUNT`; interpretare β₃ soltanto dopo il riconteggio positivo.
7. **Esportazione e controllo indipendente:**

   ```bash
   .venv/bin/python scripts/t3_mwo_catalogue_release.py --export
   ```

   Conservare `results/MWO_TILT_CATALOGUE_RELEASE` prima del controllo successivo:

   ```bash
   .venv/bin/python scripts/t3_mwo_release_recount.py --check
   ```

   Conservare la ricevuta in `results/MWO_TILT_CATALOGUE_RELEASE_RECOUNT`. Il replay del bootstrap di Joy
   controlla il calcolo deterministico; non dimostra la copertura statistica degli intervalli descrittivi.
8. **Figure e rapporto.** Usare solo prodotti verificati e i rispettivi hash; rivedere etichette, denominatori,
   copertura parziale dei cicli 20/24 e stato inferenziale. I bersagli proiettati dell'analisi principale non
   sono automaticamente quelli di tutte le sensibilità. Gli intervalli vanno tradotti nello scenario reale,
   senza percentuali di quenching dedotte direttamente da β₃. Deposito pubblico, licenza e autori restano le
   decisioni previste nel piano di rilascio; una verifica tecnica non costituisce pubblicazione.

I push dei passaggi conservati seguono la revisione concordata. Non includere credenziali, FITS nativi o
file preesistenti estranei nel commit. Questo documento non contiene alcun comando di arresto della corsa.

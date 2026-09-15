# SHARP BL — v8.3

Pipeline Python + IDL/SolarSoft per calcolare un proxy della sorgente
Babcock–Leighton (BL) dalle mappe SHARP CEA `hmi.sharp_cea_720s`.
Scarica `Br` e `bitmap` da JSOC, produce un CSV per istante/giorno e genera
immagini diagnostiche dei casi segnalati.

## Installazione

Richiede Python 3.10+, Bash, IDL con licenza e SolarSoft configurato.
Vedi [INSTALL.md](INSTALL.md) per l'ambiente Python e l'avvio SSW.

## Avvio rapido

Dalla radice del repository, con l'ambiente Python attivo:

```bash
export JSOC_EMAIL='you@example.com'  # indirizzo registrato presso JSOC
bash scripts/run_pipeline.sh 2024-05-08 03:12
```

Gli orari sono **TAI**, come nella query JSOC; non sono orari locali o UTC.
Per rielaborare dati già presenti:

```bash
bash scripts/run_pipeline.sh 2024-05-08 03:12 --skip-download
```

Per un giorno completo (può richiedere molti download):

```bash
bash scripts/run_pipeline.sh 2024-05-08 --full-day
```

Omettere l'orario seleziona comunque il giorno completo.
Ogni nuova esecuzione con lo stesso giorno/orario riutilizza i nomi di output
e sovrascrive CSV e log corrispondenti.

## Parametri principali

| Opzione | Default | Significato |
| --- | --- | --- |
| `--threshold` | `100` | Soglia di campo in G per flusso e polarità |
| `--max-abs-br` | `10000` | Massimo valore assoluto del campo ammesso, in G |
| `--bmap-min` | `1` | Valore minimo della bitmap ammesso |
| `--leading-side` | `XMAX` | Lato leading: `XMAX` o `XMIN` |
| `--all-diagnostics` | disattivata | Genera PNG per tutte le righe |
| `--no-diagnostics` | disattivata | Disattiva la generazione PNG |
| `--idl-root` | radice del progetto | Percorso del progetto visto da IDL |
| `--idl-shell` | `tcsh` | Shell che inizializza SolarSoft |
| `--idl-command` | `sswidl` | Comando di avvio IDL |

Elenco completo: `bash scripts/run_pipeline.sh --help`.

## Calcolo e qualità

Il codice implementa `S_BL = hale_sign * Phi * d * cos(lambda) * sin(alpha)`.
`Phi` è il flusso unsigned in Mx; `d` è la separazione dei centroidi in cm;
i centroidi sono pesati con il campo magnetico. Il proxy ha quindi unità Mx cm.
La classificazione Hale/anti-Hale usa data, emisfero e polarità leading.
Il tilt ridotto è salvato separatamente dal tilt orientato usato per il seno.

La pipeline distingue fra risultato numericamente valido (`valid_bl`) e caso
segnalato per controllo (`suspicious_flag`). Una regione anti-Hale può essere
numericamente valida. Quando manca una polarità sopra soglia, il proxy è `NaN`.
La validità numerica non costituisce una verifica fisica della regione.

**Uso diretto IDL:** `process_sharp_day` ha attualmente una soglia predefinita
interna di **1000 G**, mentre il launcher e gli esempi passano esplicitamente
**100 G**. Specificare sempre `THRESHOLD` per rendere il calcolo riproducibile.

## Output e diagnostica

Per l'esempio iniziale:

```text
output/sharp_bl_20240508_0312.csv
output/diagnostics_20240508_0312/*.diagnostic.png
output/diagnostics_20240508_0312/*.diagnostic.png.txt
logs/run_20240508_0312.log
logs/run_20240508_0312_idl.log
logs/run_20240508_0312_idl_batch.pro
```

I PNG usano un contrasto Br di ±1500 G: contorno ciano della bitmap,
contorno arancione dei pixel selezionati per l'analisi, croce gialla del
centroide positivo, croce ciano del negativo e segmento blu fra i centroidi.
Il calcolo CSV è separato dalla diagnostica.

## Struttura

- `idl/`: routine numeriche, elaborazione e diagnostica.
- `python/`: downloader JSOC.
- `scripts/`: launcher, esempi e controlli locali.
- `test/`: procedure IDL per verifiche manuali.
- `docs/`: stato del progetto e istruzioni per il repository.
- `data/`, `output/`, `logs/`: cartelle locali escluse da Git.

## Verifica e stato

```bash
bash scripts/check_repo.sh
```

Questi controlli verificano sintassi Python/Bash e help del launcher, senza
scaricare dati o avviare IDL. Le prove scientifiche richiedono IDL/SSW e FITS.
Vedi [stato del progetto](docs/PROJECT_STATUS.md),
[cronologia](CHANGELOG.md) e [preparazione Git](docs/REPOSITORY.md).

## Licenza

La licenza di distribuzione deve ancora essere scelta dal titolare del codice;
questo repository non include una licenza open source.

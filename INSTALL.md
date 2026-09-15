# Installazione — SHARP BL v8.3

## Python

Dalla radice del repository, con Python 3.10 o successivo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Il file delle dipendenze non blocca le versioni: per documentare una specifica
esecuzione si può salvare `python3 -m pip freeze` insieme ai risultati locali.
Serve un indirizzo email registrato presso JSOC per il download.

## IDL e SolarSoft

Occorrono IDL con licenza, SolarSoft con `READ_SDO` disponibile e `tcsh`.
Il launcher usa `tcsh -c` per avviare `sswidl`: la configurazione locale della
shell deve inizializzare SSW anche nelle sessioni non interattive.

Per verificare manualmente l'ambiente:

```text
tcsh
sswidl
```

Dal prompt IDL:

```idl
resolve_routine, 'read_sdo'
exit
```

## Primo avvio

```bash
export JSOC_EMAIL='you@example.com'
bash scripts/run_pipeline.sh 2024-05-08 03:12
```

Il driver deriva la radice del progetto dalla posizione dello script.
Se IDL vede il filesystem con un percorso diverso, passarlo esplicitamente:

```bash
bash scripts/run_pipeline.sh 2024-05-08 03:12 --idl-root /percorso/visto/da/idl
```

Se l'avvio automatico fallisce, il batch resta in `logs/`:

```bash
tcsh -c 'sswidl < logs/run_20240508_0312_idl_batch.pro'
```

Controllare sempre il log IDL e il CSV: alcune routine intercettano gli errori
per file e proseguono, quindi il solo codice di uscita non certifica che tutte
le regioni siano state elaborate.

# MDI/SMARP — verifica e registrazione offline della mappa dei campi

2026-11-16. Configurazione della corsa `schema_20261116_http_ac06138`, preparata e verificata dopo lo schema,
prima di qualsiasi conteggio o elenco di record. Autorizzazione dell'utente in chat («ok procedi»).
Nessuna nuova richiesta JSOC, nessun download di mappe, nessun output scientifico HMI modificato.

## Provenienza e verifiche

Piano congelato `9269c10`, SHA-256 `a31de02a064b08584281930f4a7c7e0fc4216ab83cc7f69c8ee793ea5bce3be0`, invariato.
Codice e selftest: `50db300d02c0`, SHA-256 `ec4973e830c75820b81a3a16a5fb6c5e57df06a7c9483ed2716029be30d41077`;
**130/130 controlli offline superati**, su albero tracciato pulito. La suite del repository ha inoltre
superato 60/60 test (`PYTHONDONTWRITEBYTECODE=1 bash scripts/check_repo.sh`). Questi sono controlli del
software e della configurazione, non una validazione scientifica delle misure MDI.

Ricevuta locale non aggiunta a Git: `results/MDI_SMARP_INVENTORY_SELFTEST/50db300d02c0/SELFTEST_META.json`,
SHA-256 `8d4d96b571a85b93da78329d03464b0da8f5a6dd7d4e1eedee281abcacf9e329`. CSV dei controlli nella stessa cartella.
Gli schemi salvati sono stati confrontati con le cinque risposte originali e i loro hash nel log; la
proposta iniziale coincide con l'hash della ricevuta della fase schema. Nessuna risposta è stata sostituita.

## Lista esatta dei campi da interrogare

I nomi, tipi e unità sono quelli degli schemi acquisiti; le stringhe originali dei record resteranno
conservate. I campi costanti sono letti dagli schemi, non richiesti per ogni record. `DATAVALS` per le
patch ha ambito segmento e non è richiesto come scalare; quello full-disk è un campo variabile di record.
`magnetogram_bscale/bzero` non vengono usati come calibrazione fra strumenti.

| Profilo | Campi richiesti |
|---|---|
| fd_min | T_REC, T_OBS, QUALITY, DATAVALS, DATE, INTERVAL, DPC, BLD_VERS, BLDVER15, BLDVER18 |
| hmi_overlap | HARPNUM, T_REC, T_OBS, QUALITY, NOAA_AR, NOAA_ARS, NOAA_NUM, CRPIX1, CRPIX2, CRVAL1, CRVAL2, CDELT1, CDELT2, CTYPE1, CTYPE2, CUNIT1, CUNIT2, CROTA2, CRLN_OBS, CRLT_OBS, USFLUXL, AREA, NPIX, LAT_FWT, LON_FWT, CODEVER7, DATE, INSTRUME, BLD_VERS |
| smarp_min | TARPNUM, T_REC, T_OBS, QUALITY, CODEVER7, DATE, INSTRUME, BLD_VERS |
| smarp_overlap | TARPNUM, T_REC, T_OBS, QUALITY, NOAA_AR, NOAA_ARS, NOAA_NUM, CRPIX1, CRPIX2, CRVAL1, CRVAL2, CDELT1, CDELT2, CTYPE1, CTYPE2, CUNIT1, CUNIT2, CROTA2, CRLN_OBS, CRLT_OBS, USFLUXL, AREA, NPIX, LAT_FWT, LON_FWT, CODEVER7, DATE, INSTRUME, BLD_VERS |

`USFLUXL` è il descrittore del flusso lungo la linea di vista in entrambe le serie CEA: non è il flusso
radiale P1. `LAT_FWT/LON_FWT` restano descrittori di centro pesato in Stonyhurst; non sostituiscono il centro
geometrico. QUALITY resta nel significato originale della singola serie; nessun bit MDI è interpretato
come il corrispondente bit HMI per analogia.

## Geometria

Per i due profili CEA sono registrati `CRVAL1/2` come centro della patch esplicitamente documentato dallo
schema. Il codice verifica per record coordinate finite, latitudine nell'intervallo [-90,90], CTYPE
`CRLN-CEA/CRLT-CEA` e unità angolari in gradi. Le longitudini sono periodiche. CRVAL non diventa un centro
per altri profili o in assenza del metodo esplicitamente registrato. Quando è disponibile una WCS completa,
il precedente percorso WCS e il controllo delle origini pixel restano attivi.

Questa alternativa è già prevista dal piano §6.2: non introduce una nuova geometria. Le dimensioni
`NAXIS1/2` non sono esposte dagli schemi delle patch e non sono ricavate da CRPIX. Senza dimensioni
documentate, inviluppo, IoU e `box_only` sono non valutabili, mai zeri sostitutivi. I grafi G5/G10 possono
usare i centri, conservando i limiti sui riquadri e sull'identità fisica delle associazioni.

## Regole di prodotto

Il full-disk MDI espone `INTERVAL`, «Observable integration interval», unità secondi. La regola registra
solo i valori numerici esatti 60 → `documented_1min`, 300 → `documented_5min`. Rappresentazioni equivalenti
come `60`, `60.0`, `60.000000` coincidono; nessun arrotondamento o soglia di prossimità. Altri valori,
non finiti e mancanti restano `unknown`. `DPC` è conservato senza una decodifica presunta.

Nessuna regola `smarp_source_time` o `smarp_source_lookup`: T_OBS nominale delle patch non è documentato
come equivalente al centro effettivo di integrazione full-disk, e il link MTARP conduce a una serie fuori
piano. Le patch restano `unknown/source_not_documented`. Nessuno spostamento automatico di 30 secondi,
nessuna nuova serie e nessun allargamento della tolleranza di 1 s. Le epoche restano proprie di ogni serie.

## Registrazione e arresto

Configurazione e ricevuta locali nella cartella della corsa:

- `FIELD_MAP.csv`: `63b0416967d1bd003b5364b2504399f1823d6287ced842856bbe4b2224aab99d`
- `PRODUCT_RULES.json`: `0f64079baa7ed3a9ed0ff843481c388f5284316f0dcdad56f8f5e1ae0337ed89`
- `FIELD_MAP_REVIEW.json`: `6cbf632dfb6cfa7385e0e70ffb19c9f03a59197d0b0d5c9246660a6579e2deb6`
- `FIELD_MAP_REGISTRATION.json`: `07d5d1c5be9a62d41a30ae4fbd35b894c5c89482e8cd1826459382206a8c7c34`

La revisione registra anche gli hash dei cinque schemi e l'elenco esatto delle richieste. La registrazione
rifiuta configurazioni diverse dalla revisione; l'uso successivo verifica mappa, regole, revisione e schemi.
`--prepare-fields --run-id ...` permette di riprodurre la preparazione dagli schemi acquisiti e dalla
proposta salvata in una copia locale: rifiuta di sovrascrivere una configurazione esistente. Non è una
query di rete e non effettua la registrazione. La registrazione è il comando separato `--register-map`.

Il registro cumulativo è rimasto byte-identico: **20 tentativi, 113972 byte, zero righe**, circa 114,6 s.
Anche il log delle richieste e le risposte originali sono invariati. Nessun conteggio o elenco avviato.
Il prossimo passo di rete è la fase `counts`, con il preventivo del piano, da avviare separatamente.
Nessun via all'inventario completo in questo passaggio. Piano prospettico, HMI e studio S invariati.
La limitazione già annotata sulla migrazione di vecchi registri interrotti resta nota e non riguarda il
registro corrente. Nessun push.

# Regole di confronto per la verifica della riproducibilità — bozza (2026-11-11)

Stato: **bozza per revisione, scritta prima di qualunque rilancio**; si congela con un commit prima
della verifica (`docs/REPRODUCIBILITY_V84.md` §7, punto 1). Nessun rilancio è stato eseguito.
Serve a stabilire **prima** che cosa conta come «riprodotto», in modo che l'esito non dipenda da
scelte fatte guardando le differenze.

## 1. Che cosa si confronta

- I file tracciati in `results/` e `figures/*/data/` (112 tabelle al 2026-11-11), elencati con
  le loro chiavi in `docs/REPRO_COMPARISON_KEYS_DRAFT.csv` (generato in sola lettura dai file
  tracciati). Le figure PNG non si confrontano byte per byte: si confrontano i CSV dei valori
  plottati.
- **Riferimento**: il file tracciato al commit che lo ha prodotto (da `docs/RESULTS_INDEX.md`),
  letto da Git (`git show <commit>:<file>`), non dalla copia di lavoro.
- **Rilancio**: in un clone pulito, con l'ambiente di `requirements-v84.txt`, sullo stesso
  commit del codice registrato nella colonna `git_commit` del riferimento (o su un commit
  successivo con codice scientifico identico, §4).
- Manifesto di hash e rilancio sono due verifiche diverse: il primo controlla che i file
  distribuiti siano integri, il secondo che il codice li rigeneri.

## 2. Lettura dei file

- I `.csv.gz` si confrontano sul **contenuto decompresso**, mai sull'archivio (l'intestazione gzip
  contiene data e nome).
- Lettura con pandas senza conversione automatica dei mancanti (`keep_default_na=False`, poi
  `na_values = ["", "nan", "NaN"]`), così che un valore testuale come `null` resti testo.
- **Intestazione**: stesse colonne nello stesso ordine; una colonna in più o in meno, o un ordine
  diverso, è una differenza di struttura riportata a parte (non si rimedia riordinando).
- **Righe**: se la chiave della tabella è unica (89 tabelle nella bozza), si ordinano entrambe
  per chiave; altrimenti (23 tabelle, da rivedere una per una, §6) si confrontano nell'ordine
  originale, e una permutazione è riportata come differenza. Stesso numero di righe e stesso
  insieme di chiavi, altrimenti differenza di struttura.

## 3. Colonne e tolleranze

| Tipo di colonna | Regola |
|---|---|
| Provenienza (`git_commit`, `git_dirty`, `status`, `sha256_*`, `*_sha256`) | **confronto separato**, §4; mai nella tolleranza numerica |
| Interi, booleani, testo, verdetti, flag | uguaglianza esatta |
| Mancanti | un mancante è uguale solo a un mancante, nella stessa posizione; mancante contro numero è una differenza |
| Numeri in virgola mobile | tre livelli riportati: **identico** (stesso valore binario, NaN = NaN), **entro tolleranza** \|a − b\| ≤ 10⁻¹² + 10⁻⁹·\|b\|, **diverso** |
| Infiniti | uguali solo se dello stesso segno |

Motivazione della tolleranza: con le stesse versioni delle librerie, un solo thread
(`OMP_NUM_THREADS=1`) e semi fissati, il calcolo atteso è **identico**; la tolleranza relativa
10⁻⁹ serve solo a distinguere differenze di ordine di somma (BLAS o piattaforma diverse) da
differenze reali, e una tabella «entro tolleranza ma non identica» si riporta come tale, non come
identica. Nessuna tolleranza per le colonne che entrano in una decisione (verdetti, flag,
conteggi): lì vale l'uguaglianza esatta, e un verdetto diverso è sempre una differenza.

## 4. Provenienza

Per ogni file, distinti: **provenienza originale** (quella del riferimento) e **provenienza della
riproduzione** (commit, `git_dirty`, SHA dei protocolli del rilancio). Il confronto richiede:
- SHA-256 dei protocolli uguali;
- `git_dirty` = 0 nel rilancio;
- se il commit del rilancio differisce da quello originale, l'identità del **codice scientifico**
  tra i due commit: SHA-256 uguali degli script che producono il file e dei moduli che importano
  (elenco da `docs/REPRODUCIBILITY_V84.md` §3), verificata e riportata.
I verificatori legati a un'esecuzione specifica (per esempio `p2f_checks.py vraw`, legato a
`5c3b664`) non si usano per il rilancio: serve un controllo che registri le due provenienze.

## 5. Esito

Per ogni file: identico / entro tolleranza / diverso / non rilanciabile (input esterni
mancanti, §3 dell'inventario) / non eseguibile da ZIP (`git_dirty = −1`). Una sola differenza in
una colonna decisionale rende il file «diverso». La sintesi conta i file per esito e per
cartella; nessun esito si dichiara per i file non rilanciati.

## 6. Da decidere prima del congelamento

- Le chiavi delle 23 tabelle senza chiave unica nella bozza (`key_status` ≠ «unica» in
  `docs/REPRO_COMPARISON_KEYS_DRAFT.csv`): definirle a mano oppure confermare il confronto
  nell'ordine originale.
- Le colonne testuali che contengono date o percorsi assoluti, se ce ne sono (da escludere e
  dichiarare, oppure confrontare).
- I tre livelli e la tolleranza 10⁻¹² + 10⁻⁹·\|b\|.
- L'ordine dei rilanci e quali escludere per costo (validazione P2f, 30+ ore).

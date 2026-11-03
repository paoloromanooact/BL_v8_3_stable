# Protocollo P1b — Record con QUALITY = 0x80 (emendamento di P1)

Stato: **congelato il 2026-11-03**, prima della selezione definitiva dei
record, dello scaricamento dei FITS e di qualunque calcolo della serie.
Modifica **solo** il §4 di `PROTOCOL_P1_SBL_SERIES.md` (SHA-256 `72f24c68…`),
che resta valido in tutto il resto e non viene modificato. Lo script registra
lo SHA-256 di P1, P1b e P2 negli output.

## 0. Perché, e cosa è già stato visto

Con i metadati completi (2010-05 → 2026-09, 8296 HARP) si vede che da
**2016-04 a 2017-03** quasi tutti i record hanno `QUALITY = 0x80`
(`0x00000080`), mentre prima e dopo circa il 90% ha `QUALITY = 0`. Con la
regola di P1 (`QUALITY == 0`) quei mesi resterebbero quasi vuoti
(regioni con record primario: 587 nel 2015, 146 nel 2016).

Secondo la documentazione JSOC
(`http://jsoc.stanford.edu/doc/data/hmi/Quality_Bits/QUALITY.txt` e
`QUALITY.notes`), 0x80 è `QUAL_TEMPERROR`: "code error discovered", impostato
sui record del primo anno della calibrazione "modL" in attesa di un
riprocessamento di `hmi.S_720s` e prodotti derivati, annunciato nel 2017 e mai
avvenuto. Non segnala dati mancanti, eclissi, ISS aperto o altri problemi
osservativi, che hanno bit propri.

Visto finora, oltre a quanto dichiarato in P1: la distribuzione di QUALITY per
mese, il numero di HARP selezionate per anno e il volume stimato. Nessuna
polarità, tilt o S_BL della serie.

## 1. Regola (sostituisce i candidati del §4 di P1)

- **Candidati:** `USFLUX > 0` e `QUALITY ∈ {0, 0x80}` (0x80 esattamente: nessun
  altro bit impostato).
- Record primario e di controllo come in P1 §4 (|LON_FWT| minimo entro 30°;
  USFLUX massimo entro 60°), senza preferenza tra QUALITY 0 e 0x80.
- Ogni record porta il flag `qual_0x80` (1 se QUALITY = 0x80).

## 2. Varianti aggiuntive

- **P1, somme per CR (§7):** variante **D** = come A, senza le regioni con
  `qual_0x80` = 1.
- **P2:** sensibilità **S7** = campione S senza le regioni con `qual_0x80` = 1.
  S7 si riporta accanto a S1–S6 ma **non entra** nel criterio di robustezza
  del §5 di P2 (che resta "almeno 4 su 6"), per non cambiare una regola di
  decisione già congelata.

## 3. Controlli aggiuntivi (si riportano)

- Numero di record con `qual_0x80` = 1 per mese, e numero fuori dal periodo
  2016-04 → 2017-03.
- Per le HARP a cavallo del periodo: confronto della distribuzione di Φ/USFLUX
  e del tilt tra record con QUALITY 0 e 0x80 (descrittivo).

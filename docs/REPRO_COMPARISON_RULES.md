# Regole di confronto per la riproducibilità — bozza revisionata (2026-11-11)

**Bozza per revisione; non congelata.** Nessuna analisi scientifica è stata rilanciata.
Le regole sono preparate leggendo schemi, riferimenti distribuiti, codice e cronologia Git;
sono quindi informate dai risultati già disponibili, ma non da differenze di un nuovo rilancio.
Si congelano con un commit prima della verifica effettiva. Non cambiano P1, P2 o P2f.

## 1. Ambito e tabelle di supporto

L'inventario comprende le **112 tabelle già tracciate** in `results/` e `figures/*/data/` al
commit `6166326`. Non comprende gli output P2f ancora non tracciati dell'esecuzione in corso:
prima della loro futura riproduzione, dovranno entrare in un'estensione dell'inventario e delle
regole, rivista e congelata prima dei relativi rilanci. Le figure PNG non sono confrontate qui;
il confronto dei CSV plottati non certifica da solo la corretta resa grafica.

- `REPRO_COMPARISON_KEYS_DRAFT.csv`: chiave e numerosità di ogni tabella; 111 chiavi univoche
  e una tabella vuota (`POST_CHECKS_NONFINITE_ROWS.csv`). Le 23 chiavi inizialmente mancanti,
  più le cinque emerse restringendo il vocabolario automatico, sono definite esplicitamente.
- `REPRO_COMPARISON_SCALES_DRAFT.csv`: una regola per ciascuna colonna e ciascun selettore
  di righe. Il selettore JSON usa `test` e, quando esiste, `quantity`; `null` significa valore
  mancante, mentre la stringa `"null"` resta testo. Chiavi e provenienza sono incluse.
- `REPRO_GIT_REFERENCES_DRAFT.csv`: commit e blob Git del riferimento, commit registrati nel
  file, stato originale dell'albero, eventuale codice effettivo dichiarato con fonte.

Le tabelle sono prodotte da `scripts/repro_draft_tables.py`, che legge soltanto i dati tracciati
e Git e scrive soltanto queste tre bozze. Non importa moduli scientifici del progetto. Esempio
di preparazione fuori dal repository, da un clone con le dipendenze installate:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/repro_draft_tables.py --out-dir /tmp/bl-repro-draft
```

L'unicità è verificata sulle chiavi proposte; non viene cercata usando colonne di risultati.
Nuove colonne o nuovi file richiedono una politica esplicita prima del rilancio, anziché un
adattamento silenzioso del confronto.

## 2. Riferimento, lettura e righe

Il **reference_commit** è l'ultimo commit che ha modificato il file nell'inventario corrente;
contiene dunque la versione distribuita da confrontare, identificata anche da **reference_blob**.
Si legge con `git show <reference_commit>:<file>`. Non si assume che l'output esista nel commit
del codice: normalmente il deposito dei risultati viene dopo l'esecuzione.

- `.csv.gz`: confronto del contenuto decompresso; l'hash dell'archivio resta un controllo di
  integrità del file distribuito, distinto dalla riproduzione.
- CSV: `keep_default_na=False`, con mancanti espliciti `""`, `"nan"`, `"NaN"`; il testo
  `null` non viene convertito in mancante. Identificativi, date e hash vanno preservati come
  testo quando previsto dallo schema, evitando conversioni numeriche con perdita di precisione.
- Stesse intestazioni e stesso ordine delle colonne. Differenze di schema si riportano come
  tali, senza correggerle automaticamente.
- Stesso numero di righe, chiavi uniche e stesso insieme di chiavi. Si allineano per chiave,
  senza dipendere dall'ordine di completamento dei processi paralleli. Chiavi mancanti
  consentite dallo schema usano un marcatore esplicito per il confronto, senza confonderlo con
  valori testuali effettivi.
- Una tabella vuota deve restare vuota e conservare lo schema; un futuro file non vuoto
  richiede una chiave esplicita prima di riprodurlo.

Le chiavi basate su `row`, come `set, comparison, row` in `P3_BARD_MATCHES.csv`, preservano
l'identificativo originario BARD. Non si rinumerano dopo aver ordinato.

## 3. Valori numerici: unità e scale fisse

Per una voce `scaled`, con valori finiti a (rilancio) e b (riferimento), si usa:

`|a − b| ≤ 10⁻¹² · S + 10⁻⁹ · max(|a|, |b|)`.

S è la scala fissa dichiarata nella tabella, nelle stesse unità dei valori. Non è stimata da
mediane, quantili, minimi o massimi dei risultati. La tolleranza è una proposta numerica di
confronto, non un'incertezza fisica, e non attribuisce a una differenza una causa BLAS dimostrata.

| Grandezza | S e motivazione |
|---|---|
| Pendenze/risposte T3; coefficienti Joy T0–T2 | 24°: scala di pianificazione γ0 fissata nel protocollo P2f §2; non il valore vero di ogni generatore |
| Risposte/pendenze T5 per D* e sue ponderazioni di latitudine | 3,56·10⁻²⁵ G/Mx: η̄ fissata nello stesso protocollo |
| Varianze/covarianze delle risposte T3 e T5 | quadrato della rispettiva scala; anche la deviazione standard di una stima di varianza conserva unità di varianza |
| Efficienza T5 per S* | 1 cm: S*/Φ ha unità di lunghezza, distinte da D*/Φ |
| Pendenza di latitudine T4 e altri angoli geometrici | 1° |
| Flussi, distanze, S_BL e proxy dipolari | una unità fisica: rispettivamente 1 Mx, 1 cm, 1 Mx·cm, 1 G |
| Quantità adimensionali, frazioni, correlazioni, parametri AR | 1 |
| Log-varianza `var_a` e pendenza `var_b` | 1 nelle rispettive parametrizzazioni del codice |

La semantica è definita per colonna e selettore: per esempio `phi` negli stimatori temporali
è persistenza AR, mentre `phi_mx` è flusso. `se` nelle tabelle diagnostiche correnti è errore
Monte Carlo di una frequenza; non si applica a esso la scala della pendenza T5.

**Confronto esatto** per chiavi, verdetti, flag, conteggi grezzi, hash dei FITS e altri valori
categoriali, anche se memorizzati come float a causa di mancanti. Le medie/quantili di conteggi
sono statistiche continue, non conteggi grezzi. La classificazione non dipende dal fatto che
i valori osservati siano interi: anche un flusso di 10²² Mx è una misura continua.

Le 111 voci di politica con semantica non classificata (30 nomi distinti di colonna)
restano esatte; sono esplicite nella tabella e non impediscono il controllo di identità.
Le colonne miste (`value`, stringhe di intervalli, ecc.) e le semantiche non recuperate (per
esempio `sig` nello sviluppo storico di P2e) hanno **confronto conservativo esatto**, motivato
nella tabella. Non si introduce una scala dedotta dai valori per farle passare. Per rendere
tollerante uno di questi confronti servirà un chiarimento della semantica prima del rilancio.

- Un mancante coincide solo con un mancante allineato; infinito solo con infinito dello stesso
  segno. Questi casi si trattano prima della formula per i finiti.
- Una differenza in verdetti, flag o conteggi è sempre una differenza anche se le grandezze
  continue sono entro tolleranza.
- Per ogni colonna continua si riportano massimo scarto assoluto e scarto normalizzato a S.
  Si distinguono identità dei valori letti, uguaglianza entro tolleranza e differenza.
  L'identità dei valori letti non è una dichiarazione di identità dei byte del CSV.
- La medesima regola deve respingere, per esempio, 10⁻²⁵ contro 9·10⁻²⁵ in una pendenza T5.

## 4. Provenienza originale, codice e rilancio

Tre riferimenti distinti: versione distribuita dell'output (`reference_commit` e blob), codice
registrato nell'output (`recorded_code_commits`) e codice del futuro rilancio. La presenza di
un commit in una colonna non prova che sia quello del produttore: alcune tabelle ereditano
colonne di provenienza dagli input. Va verificato nella catena dello script.

I JSON storici P2b dichiarano codice equivalente a `2134f86` (RUN1) e `637c482` (RUN2), distinto
dal HEAD finale registrato nei CSV. Le tabelle di supporto conservano entrambi e citano la fonte;
questa ricognizione non ha ripetuto la verifica di equivalenza del codice dichiarata nei JSON.
Per file senza commit o con `git_dirty = 1`, non si inventa un albero originale pulito: occorre
recuperare la versione effettiva del produttore oppure dichiarare la ricostruzione non completa.

Per il rilancio si richiedono:
1. Clone e albero tracciato pulito; versioni delle librerie fissate, semi e ordine della catena
   conservati. Gli output storici falliti restano conservati con il loro stato.
2. SHA dei protocolli confrontati con quelli dell'esecuzione di riferimento; protocolli
   congelati mai modificati. Per riprodurre una vecchia esecuzione si usa la sua versione.
3. Se cambia il commit, identità verificata del produttore e della sua chiusura di dipendenze
   locali, oltre agli input scientifici; `run_p2`, `p2d`, `p2f_pilot` ecc. non sono intercambiabili
   in base al solo nome. Semplice somiglianza dei risultati non prova identità del codice.
4. Colonne di provenienza confrontate separatamente e conservate entrambe. Gli hash degli input
   si verificano rispetto ai file effettivamente usati, documentando eventuali copie rigenerate
   con metadati di provenienza diversi; non si eliminano tutti gli hash dal controllo.

Date scientifiche (`T_REC`, date di CR, finestre del ciclo) e percorsi/identificativi dei dati
sono confrontati esattamente. Eventuali futuri campi di data di esecuzione o radice locale
richiedono un'esclusione nominativa motivata; non si ignorano tutte le date o tutti i percorsi.
Il verificatore P2f legato a `5c3b664` resta dedicato alla validazione originale; un verificatore
di riproduzione separato dovrà gestire entrambe le provenienze. Nessun suo vincolo viene
rimosso durante la simulazione corrente.

## 5. Esiti e ordine dei futuri rilanci

Esiti distinti: valori identici / entro tolleranza / diversi / schema diverso / non eseguito,
con motivo (input esterni mancanti, produttore non recuperato, blocco da ZIP, costo). Nessun
file non rilanciato viene dichiarato riprodotto. Un manifesto SHA-256 attesta integrità, non
l'avvenuto rilancio. Le statistiche decisionali si ricontrollano anche quando i numeri passano.

Ordine proposto, da congelare insieme all'elenco di file della verifica: controlli di schema,
chiavi, input e provenienza; tabelle/figure derivate già disponibili; P2 e calibrazioni secondo
le dipendenze; diagnosi A–D; pilota; validazione P2f solo in una fase esplicita con relativo
budget di calcolo. Ogni esclusione per costo resta `non eseguito`, non `riprodotto`.

Prima del congelamento: revisione delle politiche conservative esatte e dei limiti storici di
provenienza; fissare il sottoinsieme e i comandi della prima verifica. **Nessun rilancio o
congelamento delle presenti regole è stato effettuato da questa ricognizione.**

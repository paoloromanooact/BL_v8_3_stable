# MDI/SMARP — piano dell'inventario limitato dei metadati

**BOZZA NON CONGELATA, revisione 1 — 2026-11-16.** Preparata per revisione prima del codice e delle
interrogazioni. Non autorizza ancora query JSOC, export o download di mappe. Questa preparazione ha usato
documenti locali e documentazione pubblica; non ha interrogato il catalogo JSOC. Il piano è non cieco
rispetto allo studio di fattibilità e ai risultati HMI già noti.

Documento di partenza: [MDI_SMARP_FEASIBILITY.md](MDI_SMARP_FEASIBILITY.md), aggiornamento `1e02049`.
Obiettivo generale invariato: misura della sorgente Babcock–Leighton e studio del quenching. T3 resta
non deciso; T5 resta descrittivo. La pipeline HMI, i suoi campioni, protocolli e output non cambiano.

## 1. Domande e risultato atteso

L'inventario risponde a Q1, alla parte preliminare di Q2 e a quella documentale di Q7 dello studio:

1. Quali serie e metadati sono interrogabili e con quali definizioni, chiavi e versioni?
2. Qual è la copertura dei **record di catalogo**, con lacune, distribuzione di QUALITY e metadati mancanti?
3. Per quanti record SMARP è documentabile il prodotto MDI sorgente da 1 o 5 minuti? Come varia nel tempo?
4. Quante associazioni TARP–HARP sono candidate nella sovrapposizione, quali sono ambigue e quanto sono
   ripetute nel tempo?

Il risultato è un inventario descrittivo con denominatori e limiti. Distingue:

- record catalogato;
- record valutabile con i metadati richiesti per una specifica operazione;
- mappa effettivamente recuperabile, **non verificata da questo inventario**.

Nessuna misura nuova di Br, flusso, tilt, dipolo, S_BL o efficienza; nessuna stima di quenching, nessuna
riscalatura 1,40 e nessun campione MDI equivalente a S dichiarato. Parametri riassuntivi già presenti nei
metadati possono essere inventariati con il loro nome e significato originari, senza renderli equivalenti
ai parametri HMI o alle misure P1. Non si assegnano ancora i cicli alle TARP.

## 2. Serie, periodo e cadenza da inventariare

Intervalli **TAI**, inizio incluso e fine esclusa. La finestra amministrativa non certifica copertura
osservativa né appartenenza al ciclo 23.

| Serie | Periodo | Uso e interrogazioni previste |
|---|---|---|
| `mdi.smarp_cea_96m` | `[1996-01-01, 2010-10-29)` | inventario principale, tutti i record alla cadenza nativa, senza filtri di qualità o flusso |
| `mdi.fd_M_96m_lev182` | stesso periodo | soli metadati full-disk: separare assenze della sorgente da assenze di patch; ricostruire il prodotto se documentabile |
| `hmi.sharp_cea_720s` | `[2010-05-01, 2010-10-29)` | tutti i record a 12 minuti per le associazioni; nessun sottocampionamento orario dei vecchi file P1 |
| `mdi.smarp_96m` | solo record identificati della serie CEA | schema; lookup mirati se servono link o keyword di provenienza assenti in CEA; non un secondo inventario completo |
| `mdi.fd_Ic_interp` | `[1996-01-01, 2010-10-29)` | schema; soli conteggi per mese se la documentazione non consente di interpretare le lacune del continuo dai primi due inventari |

Sono cinque serie ammesse; nessuna ricerca aperta di altre serie. I lookup seguono al massimo **un link**
esplicitamente documentato, solo verso una delle serie ammesse. Se la ricostruzione richiede altri
prodotti o un ulteriore livello di link, si registra il limite; l'estensione richiede un emendamento.
Non si estende SMARP fino alla fine della missione MDI, aprile 2011.

Le serie e il periodo comune derivano da [B21] e dal repository degli autori [SM]; la disponibilità
attuale è ancora da verificare. La distinzione tra prodotti MDI da 1 e 5 minuti non si ricava dalla
cadenza di 96 minuti [B21].

## 3. Fase 0: schema prima dei record

Dopo revisione e congelamento del piano, lo script raccoglierà per prima cosa lo schema delle cinque
serie: nomi, descrizioni, chiavi primarie e loro ordine, tipi, unità, costanti, keyword, link e definizioni
dei segmenti. Sono ammesse le sole operazioni di lettura `series_struct`/`info`, `rs_summary` e
`rs_list`/`query` [D1–D2]. Niente `export`, `jsoc_fetch`, staging, percorsi SUM o richieste ai file FITS.

Il primo passaggio si ferma dopo lo schema. Produce una **mappa dei campi proposta**, da verificare e
registrare con hash prima dell'interrogazione dei record. Non si assume che SMARP esponga le keyword
SHARP né che keyword omonime abbiano significato identico.

| Categoria | Metadati richiesti; nomi da riscontrare nello schema |
|---|---|
| Identità | serie, tutte le chiavi primarie; `TARPNUM` o `HARPNUM`; `T_REC`, `T_OBS` se presente; identificatore completo del record e numero di revisione/record se esposto |
| Qualità | `QUALITY` originale, tipo e significato documentato dei bit; eventuali altre keyword di qualità e validità presenti |
| Provenienza | link alla sorgente, tempo sorgente, identificatore del prodotto, integrazione/media temporale, versione di elaborazione e data di produzione, se esposti |
| Geometria | sistema di coordinate e unità; centro geometrico della patch, `CRVAL1/2`, `CTYPE1/2`, `CRLN_OBS`, `CRLT_OBS`; estensione e dimensioni se esposte; `LAT_FWT`, `LON_FWT` come descrittori distinti, se presenti |
| Associazioni | `NOAA_AR`, `NOAA_ARS`, `NOAA_NUM`, se presenti; stringhe originali conservate |
| Descrittori del prodotto | `USFLUXL`/`USFLUX`, area e numero di pixel se presenti, con unità e definizione della rispettiva serie; descrizioni di bitmap e segmenti |

La mappa indica per ciascun campo: serie, nome reale, tipo/unità, riferimento della definizione,
normalizzazione proposta e operazioni che ne dipendono. Assenza di un campo facoltativo = `not_exposed`;
assenza di identità o tempo rende impossibile l'inventario dettagliato di quella serie. Coordinate non
interpretabili impediscono l'associazione spaziale, non la tabella di copertura temporale.

Un adattamento puramente nominale documentato nella mappa non cambia il piano. Una nuova interpretazione
scientifica, una soglia, una serie o un criterio di abbinamento richiedono un emendamento prima dell'uso.
Con lo schema remoto non disponibile si termina come **schema non verificato**, senza inventare campi.

## 4. Acquisizione limitata e completezza delle risposte

Implementazione successiva in uno script separato, senza riusare i percorsi di output dei downloader HMI.
Ambiente e versioni effettive, compreso `drms`, registrati; nessun aggiornamento di librerie durante T5.

- Un processo, una richiesta attiva; almeno un secondo tra richieste. Nessuna simulazione e nessun accesso
  ai risultati della griglia T5. L'inventario non parte insieme a un altro rilancio pesante sulla macchina.
- Finestre mensili in ordine cronologico. Per ogni finestra si acquisisce prima il conteggio server
  (`rs_summary`), poi l'elenco, controllando uguaglianza del numero di record e unicità delle chiavi.
- Se il conteggio supera **25 000**, suddivisione deterministica in intervalli di 7 giorni, poi giorni,
  poi intervalli di 96 minuti; nessun sottocampionamento. Un blocco minimo ancora troppo grande resta
  incompleto e ferma l'acquisizione della serie. Il limite delle righe restituite non certifica completezza.
- Estremi delle query costruiti nell'ordine reale delle chiavi primarie. Ogni risposta è filtrata
  localmente sull'intervallo semiaperto richiesto; eventuali righe degli estremi si registrano prima
  della deduplicazione. Conteggio server e righe ricevute si confrontano sul record set interrogato;
  il conteggio locale dopo il filtro si conserva separatamente.
- Massimo **1000 tentativi HTTP complessivi**, **2 000 000 righe accettate distinte** fra tutte le serie,
  **500 MiB di corpi di risposta** complessivi anche falliti o duplicati, **60 minuti di tempo di parete**
  cumulativi per l'inventario. Schema e record hanno ricevute separate; i consumi di tutte le fasi,
  comprese riprese, sono sommati nel registro e sottoposti agli stessi tetti. Il tempo è la somma
  delle durate delle invocazioni, incluse le attese di rete; esclude il tempo fra le fasi per la revisione.
  I tetti sono scelte operative conservative, non una previsione del volume o della durata.
- Timeout per tentativo 45 s, al massimo tre tentativi per richiesta, attese 5 e 15 s; per rate limit
  si rispetta `Retry-After` solo entro il tempo residuo, altrimenti si arresta. Contatori e attese non
  si azzerano alla ripresa. Controlli del tempo anche prima di attese e richieste; il timeout è ridotto
  al tempo residuo. Lettura dei corpi con limite di byte, senza scrivere una risposta oltre il tetto.
- Se un blocco fallisce, non si continua saltandolo. Si conserva la risposta/errore e si dichiara
  l'inventario parziale con intervalli richiesti, completati e non interrogati. Nessun aumento dei tetti
  dopo i risultati senza un nuovo emendamento.

Le risposte originali JSON e le richieste complete senza credenziali sono conservate con hash. Le
conversioni non devono trasformare automaticamente stringhe invalide in numeri mancanti indistinguibili:
valore originale e stato del parsing restano distinti. Un risultato vuoto è assenza di record soltanto
con risposta riuscita e conteggio zero; errore, timeout e intervallo non interrogato hanno stati separati.

## 5. Copertura, qualità e prodotto MDI

### 5.1 Copertura

Riportare per serie, mese e anno: richieste completate, record catalogati, tempi distinti, patch distinte,
prima e ultima epoca, valori mancanti nei campi richiesti. I conteggi di patch per mese non si sommano
per ricavare il numero totale di TARP/HARP. Nessuna interpolazione di epoche o riempimento di lacune.

Per la serie full-disk, usare la griglia temporale nativa con epoca e passo documentati nella mappa dei
campi; per ogni intervallo completo elencare slot assenti, sequenze consecutive e durata. Se l'ancoraggio
della griglia non è documentabile, riportare solo tempi osservati e intervalli fra questi, senza una
percentuale di completezza rispetto a una griglia assunta. Alle finestre parziali non si attribuisce
copertura zero. Per `mdi.fd_Ic_interp`, se interrogata solo con conteggi, non si dichiarano lacune interne
localizzate dai soli conteggi mensili.

**Nessuna patch a un'epoca non significa nessuna osservazione solare.** Distinguere record full-disk
assente, record sorgente presente ma nessuna TARP, patch presenti con qualità segnalata e metadati non
acquisiti. I metadati da soli non distinguono sempre quiete solare, tracciamento e difetto di pipeline:
questi casi restano non determinati. Le lacune note del 1998 e il limite del 2010 sono aspettative da
confrontare con l'inventario, non intervalli da imporre o cancellare.

### 5.2 Qualità

Conservare `QUALITY` originale e rappresentazione intera/esadecimale normalizzata in modo documentato,
compresi segno e larghezza. Riportare distribuzioni di valori e bit documentati, valori sconosciuti,
parsing impossibili e campi assenti, separatamente per serie e periodo. Nessun bit MDI viene interpretato
come l'omonimo HMI per analogia. Il trattamento HMI di 0x80 non è trasferito a MDI.

Conteggio con QUALITY = 0 come **descrittore**, non nuovo criterio di qualità scientifica; nessuna riga
è eliminata dall'inventario per qualità, flusso o numero NOAA. Segnalazioni sul continuo sono interpretate
solo con una specifica del bit verificata e citata. Si registrano anche campi utili a definire in futuro
selezioni, senza affermare quanti record passeranno i filtri in pixel, Br e polarità di S.

### 5.3 Distinzione 1/5 minuti

Per ciascun record SMARP e sorgente full-disk assegnare uno stato:

- `documented_1min`, `documented_5min`: keyword o prodotto/link documentati, con riferimento alla regola;
- `unknown`: informazione assente, significato non documentato o sorgente non risolta;
- `conflict`: evidenze discordanti o più sorgenti incompatibili.

Conservare il record sorgente, il metodo di risoluzione e i valori usati. Un collegamento esplicito e
un'identificazione per solo tempo sono distinti. Il solo tempo può identificare la sorgente soltanto se
lo schema documenta quale tempo usare e il collegamento è univoco entro **1 s**; altrimenti `unknown`.
La classe temporale è il prodotto documentato, non il valore numerico di una keyword chiamata genericamente
"exposure". Non inferire 1/5 minuti da cadenza, anno, rumore atteso o flusso. Nessuna assegnazione di
rumore in pixel CEA viene effettuata qui.

Riportare composizione e frazioni `unknown`/`conflict` sia per **record full-disk/epoche sorgenti distinti**
sia per **record di patch**, con denominatori: più patch possono derivare dalla stessa mappa. La quota
non identificabile è un risultato utile e non viene eliminata per produrre una serie apparentemente pura.

## 6. Associazioni candidate nella sovrapposizione

Periodo `[2010-05-01, 2010-10-29)` TAI, serie CEA definitive. Si usano tutti i record acquisiti; nessuna
associazione dal solo numero NOAA e nessun confronto di valori di tilt o sorgente.

Regola proposta, da confermare in revisione prima del congelamento:

1. Confrontare i **tempi T_REC in TAI**: distanza assoluta non oltre **360 s**, metà della cadenza HMI.
   Conservare anche T_OBS e i suoi scarti se esposti; T_REC non è necessariamente il tempo effettivo di
   esposizione. Non sostituire a posteriori il criterio con T_OBS per aumentare gli abbinamenti.
2. Usare centri **geometrici di patch** in longitudine di Carrington e latitudine eliografica, dopo
   verifica di coordinate e unità nella mappa dei campi. Calcolare distanza di cerchio massimo, con
   longitudini periodiche. `LAT_FWT`/`LON_FWT` non sostituiscono il centro senza un emendamento: sono
   descrittori dipendenti dal campo e dalle definizioni del prodotto. Coordinate mancanti o non
   interpretabili producono `not_assessable`, non una distanza zero.
3. Conservare tutti gli archi entro **5°** e tutti i casi tra **5° e 10°** come fascia separata di
   sensibilità dell'inventario. Cinque e dieci gradi sono tolleranze operative proposte, non errori di
   posizione validati o criteri di identità fisica. Non si scelgono guardando il numero delle coppie.
4. Per ogni record SMARP e per ogni HARPNUM considerare il record HMI temporalmente più vicino entro
   360 s; pari merito al tempo più antico. Si mantengono tutti gli HARPNUM candidati. Nel grafo fra
   record, un arco entro 5° è `unique_at_epoch` solo se entrambi gli estremi hanno grado 1; gli altri
   sono `ambiguous`. I gradi sono calcolati prima dei filtri di qualità e NOAA.
5. Sovrapposizione degli elenchi NOAA, molteplicità e dati NOAA mancanti sono annotazioni separate;
   non risolvono automaticamente il grafo. Nessuna scelta manuale della coppia più plausibile.

Riportare: record senza candidato, non valutabili e ambigui; coppie di record per stato; coppie distinte
TARPNUM–HARPNUM; numero di epoche ripetute per coppia; TARP/HARP coinvolte e componenti connesse del grafo
**a livello di patch**. Le componenti sono raggruppamenti delle associazioni candidate, non famiglie
fisiche dimostrate né osservazioni indipendenti. Distinguere i conteggi entro 5° da quelli nella fascia
5–10°. Per gli archi riportare separatamente QUALITY dei due strumenti, scarti temporali/spaziali e
concordanza NOAA. Nessun filtro magnetico trasferito da P1.

Le coppie sono **candidate a un confronto successivo**: maschere, co-registrazione, contaminazione e
disponibilità dei file richiedono verifiche sulle mappe. Non si dichiarano già coppie scientificamente
utilizzabili. La futura potenza di T3 richiede inoltre disegno in attività/latitudine, assegnazione del
ciclo e incertezza strumentale: non si deduce dal numero di archi.

## 7. Output e provenienza previsti

Cartella nuova per ogni corsa in `data/sharp/metadata_inventory_mdi/<run_id>/` per risposte originali e
schema; non sovrascrivere i metadati HMI esistenti. Tabelle compatte e rapporto, se autorizzati dopo
l'esecuzione, in `results/MDI_SMARP_INVENTORY/<run_id>/` e `docs/MDI_SMARP_METADATA_INVENTORY_RESULTS.md`.
Nessun output è stato prodotto con questa bozza.

| Artefatto | Contenuto minimo |
|---|---|
| `SCHEMA_*`, `FIELD_MAP.csv` | definizioni originali e adattamento proposto/verificato con riferimenti e hash |
| `QUERY_LOG.jsonl`, `RAW_SHA256.csv` | richieste, UTC di esecuzione, serie, intervalli TAI, esito, tentativi, byte, conteggi, file originali e SHA-256 |
| `RECORDS_*.csv.gz` | chiavi, metadati originali/normalizzati e stati; ordine per serie e chiavi primarie |
| `COVERAGE_MONTHLY.csv`, `GAPS.csv` | denominatori, finestre complete/parziali e tipo della lacuna; copertura full-disk distinta dalle patch |
| `QUALITY_SUMMARY.csv`, `PRODUCT_SUMMARY.csv` | valori/bit e prodotti 1/5 minuti, ignoti e conflitti; denominatori per epoca e per patch |
| `OVERLAP_CANDIDATES.csv.gz`, `OVERLAP_SUMMARY.csv` | archi e distanze, ambiguità, fasce spaziali, ripetizioni, conteggi per patch/componenti |
| `CHECKS.csv`, `PROVENANCE.json` | controlli, stato completo/parziale, versione e stato Git del produttore, hash piano/mappa/script/input locali, ambiente |

Identità del record = serie e **tutte** le chiavi primarie documentate; TARPNUM/HARPNUM non sono da soli
una chiave di riga. Revisioni o duplicati conflittuali non si risolvono con "keep last". Una risposta
identica può essere riutilizzata alla ripresa soltanto con richiesta, configurazione e hash uguali;
nessuna seconda acquisizione per scegliere la risposta più favorevole. La revisione remota osservata e
l'ora di acquisizione fanno parte del risultato; un confronto futuro può trovare un archivio aggiornato.

Lo script registra anche gli hash dei riferimenti locali consultati; nessun input scientifico HMI viene
riscritto. Le risposte originali restano locali e non si aggiungono automaticamente a Git. L'eventuale
conservazione di tabelle derivate, manifesto e commit si decide dopo controllo e revisione; nessun push.

## 8. Verifiche e arresto

Prima della rete, prove offline su risposte costruite: errori e zero righe distinti; count/list discordi;
troncamento; confini mensili; tempi TAI/UTC; chiavi duplicate; QUALITY signed/missing; origine 1/5 minuti
ignota o conflittuale; longitudini 0/360; parità temporali; associazioni uno-a-molti; tutti i tetti,
divieto di export/download e ripresa senza azzerare i consumi. Prove prive di dati magnetici reali.

Prima di interpretare l'inventario: riconteggio separato da CSV/JSON salvati, hash e provenienza,
completezza per finestra, chiavi, riconciliazione sorgente/patch e somme dei denominatori, grafo e
partizione dei suoi stati. Un campo mancante previsto è un limite riportato; errore tecnico, hash
discorde, conflitto di identità o conteggio non riconciliato impediscono di certificare completezza.

Se sono raggiunti i tetti o l'archivio non risponde, rapporto **parziale/non verificabile**; non si
trasforma l'intervallo non acquisito in una lacuna solare. Nessuna soglia sul numero minimo di coppie:
l'inventario serve a descrivere la fattibilità, non ad approvare l'estensione.

## 9. Sequenza e decisioni da chiudere in revisione

1. Rivedere questa bozza, in particolare serie/periodi, tetti, regole temporali/spaziali e prodotti ignoti.
2. Congelare piano e SHA-256 in un commit dedicato **prima** del codice; nessuna modifica dei protocolli HMI.
3. Scrivere e provare offline il raccoglitore separato; revisione del codice prima della rete.
4. Eseguire la sola fase schema, conservare risposte e proposta della mappa, far verificare e registrare
   la mappa. Solo dopo avviare l'acquisizione limitata con i consumi cumulativi previsti.
5. Controllo tecnico e riconteggio, rapporto descrittivo e revisione esterna. Nessun download automatico
   al raggiungimento di un numero di coppie.
6. Valutare un **nuovo piano** per potenza prospettica di T3 e confrontabilità strumentale. Lo studio
   morfologico su S non è un prerequisito; T3 dentro i cicli resta distinto dal quenching fra cicli.

Nessuna di queste fasi è stata avviata dalla stesura della bozza. L'eventuale durata della rete sarà
misurata: il tetto di un'ora non è una stima di completamento.

## 10. Fonti consultate per questo piano

- [B21] Bobra et al. 2021, §§II–III e tabella 1,
  [testo completo](https://arxiv.org/html/2108.07918): serie, prodotti e periodo comune. Usato come
  documentazione, non come certificazione della disponibilità odierna dei record.
- [SM] Repository degli autori [mbobra/SMARPs](https://github.com/mbobra/SMARPs), README, consultato
  2026-11-16: risorse di esempio e periodo comune. I notebook non sono stati eseguiti e non si adottano
  automaticamente le loro regole di associazione.
- [D1] [API ufficiale drms.Client](https://docs.sunpy.org/projects/drms/en/stable/generated/api/drms.Client.html):
  schema, keyword, chiavi primarie e query di metadati; distinzione dall'export.
- [D2] [API ufficiale drms.HttpJsonClient](https://docs.sunpy.org/projects/drms/en/latest/generated/api/drms.HttpJsonClient.html):
  conteggio `rs_summary` e risposte JSON. La documentazione web può descrivere una versione diversa da
  quella locale: firme e comportamento vanno verificati offline sulla versione registrata prima del codice.

Le scelte operative (finestre, tetti, soglie di associazione e output) sono proposte di questo piano,
non raccomandazioni delle fonti né criteri già validati.

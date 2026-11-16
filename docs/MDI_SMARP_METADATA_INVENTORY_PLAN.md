# MDI/SMARP — piano dell'inventario limitato dei metadati

**CONGELATO il 2026-11-16**, dopo la verifica esterna della revisione 2 (`c70e91d`) e le tre
precisazioni registrate in §12, **prima del codice del raccoglitore e delle interrogazioni JSOC**.
Dopo il congelamento questo file non si modifica: nuove regole richiedono un emendamento separato,
scritto e registrato prima dell'uso. Il congelamento non avvia query, export o download di mappe.
La preparazione ha usato documenti locali e documentazione pubblica, senza interrogare JSOC.
Il piano è non cieco rispetto allo studio di fattibilità e ai risultati HMI già noti.

Documento di partenza: [MDI_SMARP_FEASIBILITY.md](MDI_SMARP_FEASIBILITY.md), aggiornamento `1e02049`.
Recepisce la revisione interna di Codex e la revisione esterna di Claude Opus 5.5, riunite nei nove punti
trasmessi dall'utente (§11). La revisione interna è dello stesso autore della bozza; non è indipendente.
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
| `hmi.sharp_cea_720s` | `[2010-04-30 23:54, 2010-10-29 00:06)` | cadenza nativa 12 min; margine di 360 s su entrambi i lati della finestra SMARP; record di margine separati nei conteggi |
| `mdi.smarp_96m` | solo record identificati della serie CEA | schema; lookup mirati se servono link o keyword di provenienza assenti in CEA; non un secondo inventario completo |
| `mdi.fd_Ic_interp` | `[1996-01-01, 2010-10-29)` | schema; al più 15 conteggi annuali ausiliari, soltanto se necessari dopo l'inventario principale; nessun elenco |

Sono cinque serie ammesse; nessuna ricerca aperta di altre serie. I lookup seguono al massimo **un link**
esplicitamente documentato, solo verso una delle serie ammesse. Se la ricostruzione richiede altri
prodotti o un ulteriore livello di link, si registra il limite; l'estensione richiede un emendamento.
Non si estende SMARP fino alla fine della missione MDI, aprile 2011.

Le serie e il periodo comune derivano da [B21] e dal repository degli autori [SM]; la disponibilità
attuale è ancora da verificare. La distinzione tra prodotti MDI da 1 e 5 minuti non si ricava dalla
cadenza di 96 minuti [B21]. Quest'ultimo descrive entrambi i prodotti, ma non documenta una keyword che li
distingua: non si presume che l'inventario riuscirà a identificarli record per record.

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
| Geometria (solo sovrapposizione) | sistema/unità, dimensioni per record (`NAXIS1/2` o equivalenti documentati), `CRPIX1/2`, `CRVAL1/2`, `CDELT1/2`, `CTYPE1/2`, `CUNIT1/2` e termini PC/CD, rotazione e parametri di proiezione effettivamente necessari; `CRLN_OBS`/`CRLT_OBS` se richiesti; in alternativa centro/limiti eliografici esplicitamente documentati |
| Associazioni (solo sovrapposizione) | `NOAA_AR`, `NOAA_ARS`, `NOAA_NUM`, se presenti; stringhe originali conservate |
| Descrittori (solo sovrapposizione) | `USFLUXL`/`USFLUX`, area, numero di pixel e centri pesati se esposti, con unità e definizioni originarie; descrizioni di bitmap/segmenti dallo schema |

**Profili di campi.** Per lo storico SMARP fuori dalla sovrapposizione e per il full-disk si richiedono
soltanto identità, tempo, QUALITY e provenienza documentabile. Le costanti dello schema non sono richieste
di nuovo su ogni record se possono essere ricostruite dallo schema salvato. Geometria, NOAA e descrittori
sono richiesti soltanto per SMARP nella sovrapposizione e per HMI nella finestra con margine. Nessun
`**ALL**`: la mappa contiene la lista esatta per ogni profilo e i campi opzionali assenti. Geometria e
attività dello storico per una futura potenza T3 richiederanno una raccolta successiva pianificata: il
presente inventario minimo non produce già quel disegno completo.

La mappa indica per ciascun campo: serie, nome reale, tipo/unità, riferimento della definizione,
normalizzazione proposta e operazioni che ne dipendono. Assenza di un campo facoltativo = `not_exposed`;
assenza di identità o tempo rende impossibile l'inventario dettagliato di quella serie. Coordinate non
interpretabili impediscono l'associazione spaziale, non la tabella di copertura temporale.

Un adattamento puramente nominale documentato nella mappa non cambia il piano. Una nuova interpretazione
scientifica, una soglia, una serie o un criterio di abbinamento richiedono un emendamento prima dell'uso.
Se manca lo schema di una serie principale, si dichiara quella parte non verificabile. L'indisponibilità
di una serie ausiliaria non rende assenti i record delle altre: si rinuncia alla relativa verifica,
con stato esplicito. Non si inventano campi o equivalenze.

## 4. Acquisizione limitata e completezza delle risposte

Implementazione successiva in uno script separato; nessun riuso dei percorsi dei downloader HMI.
**Nessuna fase di rete, nemmeno lo schema, prima della fine della griglia T5**, della revisione del piano
e del codice e del superamento delle prove offline. Ambiente effettivo registrato, senza aggiornamenti.

### 4.1 Trasporto e tetti fissati prima di qualunque misura

`drms 0.9.0` è fissato nei requisiti. La verifica offline di `HttpJsonRequest.raw_data` conferma la lettura
integrale `self._http.read()`: il raccoglitore non usa `Client.query()` o il lettore standard per ricevere
i corpi. Usa un trasporto proprio limitato, con le operazioni JSON di lettura `series_struct`,
`rs_summary`, `rs_list`. Nessun export, staging o richiesta ai file; nessun client opaco che generi
richieste ulteriori non contate. L'eventuale parser drms si usa soltanto su dati già ricevuti e salvati.

Un solo processo e una richiesta attiva; almeno un secondo fra tentativi. Tutti i passaggi usano un unico
registro persistente, anche dopo una ripresa o fra schema e record:

- **1000 tentativi HTTP**, inclusi errori, retry e redirect; redirect automatici disabilitati, ogni
  destinazione va verificata come endpoint di soli metadati e ogni nuova richiesta conta;
- **2 000 000 righe distinte accettate**, su tutte le serie;
- **1 GiB di corpi JSON non compressi ricevuti**, anche parziali, falliti o duplicati, contro 500 MiB
  della revisione 1; i file derivati locali sono contabilizzati separatamente;
- **90 minuti cumulativi di parete delle invocazioni**, incluse ricezione, attese ed elaborazione, contro
  60 minuti della revisione 1. Escluso soltanto il tempo fra invocazioni per la revisione umana.

Volume e tempo sono tetti operativi, non durate o consumi previsti. Sono fissati prima di qualunque
query, dopo la revisione esterna, senza un adeguamento a risultati acquisiti. I profili minimi riducono
il costo dello storico, ma la densità di byte del profilo ricco HMI, a cadenza nativa, non è misurata;
1 GiB lascia margine alla sua variabilità e alle risposte da conservare. Il tetto di 90 minuti lascia
margine anche a latenza, ricezione ed elaborazione, ancora non misurate. Nessuno dei due promette il
completamento: preventivi e limiti effettivi restano attivi come in §4.2.

Massimo tre tentativi per richiesta, attese 5 e 15 s. Timeout di inattività massimo 45 s, ridotto al tempo
residuo, più scadenza complessiva monotona durante connessione e lettura: un server che invia lentamente
byte non deve oltrepassarla. Controllare budget prima di ogni richiesta, attesa e blocco ricevuto; ricezione
e letture bloccanti devono essere interrompibili entro la scadenza. Chiedere `Accept-Encoding: identity`;
una risposta compressa inattesa è arrestata e registrata senza decompressione illimitata. Al tetto di byte
si conserva il prefisso ricevuto con stato `truncated_by_budget`, non come JSON completo. `Retry-After`
si rispetta solo entro il tempo residuo. Nessun contatore si azzera alla ripresa.

### 4.2 Finestre e preventivo esplicito

| Parte | Finestre iniziali | Conteggi | Elenchi | Richieste senza retry/suddivisioni |
|---|---|---:|---:|---:|
| SMARP CEA | 178 mesi, gennaio 1996–ottobre 2010 (ultimo mese parziale) | 178 | 178 | 356 |
| Full-disk MDI | 15 anni di calendario, ultimo fino al 29 ottobre | 15 | 15 | 30 |
| HMI con margini | 26 intervalli consecutivi di massimo 7 giorni, ancorati all'inizio dell'acquisizione | 26 | 26 | 52 |
| Continuo, ausiliario facoltativo | 15 anni, solo conteggi | 15 | 0 | 15 |
| Schema e definizioni | riserva massima iniziale, per cinque serie | — | — | 15 |
| **Preventivo di base** | | | | **468** |

Si riservano inoltre al massimo **200 tentativi** per lookup ausiliari raggruppati e **200** per
suddivisioni/retry: preventivo **868**, margine **132** rispetto al tetto 1000. Queste riserve non
autorizzano a superare il tetto né garantiscono che tutti i retry possibili siano eseguibili. Lo script
ricalcola il preventivo dalle finestre effettive: la tabella non sostituisce il conteggio delle chiamate.
Il caso estremo di tre tentativi per tutte le richieste di base sarebbe `3 × 468 = 1404`, oltre il
tetto: non è garantito. In quel caso si arresta con inventario parziale; non si amplia la riserva per
completare la corsa.

Prima degli elenchi, una fase di **soli conteggi** visita prima la sovrapposizione, poi le restanti
finestre delle tre serie principali. Se un conteggio supera **25 000**, la finestra è suddivisa
deterministicamente: anni in mesi, mesi in intervalli consecutivi di 7 giorni, poi giorni, poi intervalli
di 96 minuti. Niente sottocampionamento. Tutti i conteggi genitori e figli consumano richieste; per gli
elenchi si contano solo le foglie, senza duplicare gli intervalli. Il continuo resta facoltativo e ultimo.

La ricevuta `BUDGET_COUNTS.json` registra consumi, finestre foglia, somma delle righe previste, elenchi
ancora necessari e preventivo totale con riserve. Se richieste o righe previste non rientrano, non si
avvia l'inventario completo: è consentita soltanto la sovrapposizione se il suo preventivo rientra,
dichiarando lo storico `not_started_budget`. Se nemmeno questa rientra si termina ai conteggi.

I conteggi **non misurano i byte**. Le stime del revisore (0,6–0,9 milioni di righe SMARP e 0,2–0,3 milioni
HMI) sono ordini di grandezza, non volumi osservati. Dopo i conteggi, i primi elenchi effettivamente
acquisiti fungono anche da misura di costo e sono riusati, non scartati. Prima lo schema deve fissare i
quattro profili: SMARP minimo, SMARP nella sovrapposizione, full-disk minimo, HMI nella sovrapposizione.
Per ogni profilo si misura sul primo blocco non vuoto la densità di byte JSON e il tempo; un profilo
interamente vuoto non richiede campionamento. Non si scelgono blocchi dopo aver visto le risposte.

Prima dello storico completo si registra `BUDGET_PAYLOAD.json`: byte già ricevuti più **due volte** i
byte/riga misurati per le righe restanti di ogni profilo. Per il tempo:
`T_used + 2·Σ_p[(t_p/N_p)·N_rest,p] + R_rest·(1 s + t_count,max)`, con `t_p` durata di ricezione/parsing
del primo blocco del profilo p, `N_p` sue righe, `R_rest` richieste residue previste e `t_count,max`
massimo tempo osservato per un conteggio riuscito. Si conservano tutte queste quantità; la formula
include intenzionalmente un margine di latenza anche per le liste e non modella il costo futuro dei grafi.
Se il preventivo supera i tetti, si conserva
la sovrapposizione già acquisita e si arresta la parte restante. Il fattore due è un margine operativo,
non un limite probabilistico; i tetti restano attivi sulla ricezione anche se la proiezione è favorevole.
Il primo blocco storico minimo può essere acquisito per questa misura; il resto non parte prima
della ricevuta. Nessuna modifica dei campi o dei tetti per fare rientrare una risposta già vista.

### 4.3 Ordine degli elenchi e integrità

Ordine fissato: **sovrapposizione 2010 (SMARP, HMI e sorgente MDI) → storico MDI → ausiliari**.
I conteggi preliminari sono l'eccezione leggera necessaria al preventivo. Per la sorgente si acquisisce
per primo il blocco annuale 2010 già previsto, riusato anche per gennaio–aprile; nessun secondo elenco
annuale sovrapposto. Per lo storico restano finestre cronologiche. Ogni blocco riuscito è verificato e
salvato prima di passare al successivo. Un blocco fallito non viene saltato per dichiarare completezza.

Lookup ausiliari: prima le sorgenti della sovrapposizione, poi quelle storiche in ordine di tempo e
chiave; deduplicazione delle richieste e cache per sorgente. Massimo 100 record specifici per batch e
200 tentativi totali ausiliari, inclusi conteggi se necessari. Casi non risolti per il tetto restano
`unknown_budget`; non si interrogano solo i casi con identificazione favorevole.

Query nell'ordine reale delle chiavi primarie; intervalli semiaperti verificati localmente. Le righe
aggiunte dal server agli estremi sono annotate prima della deduplicazione. Conteggio server e righe
ricevute si confrontano sul medesimo record set; il conteggio dopo il filtro locale è distinto. Il
limite di righe imposto al server non certifica completezza. Un blocco minimo ancora troppo grande,
una discordanza count/list o un conflitto di identità fermano quella parte come incompleta.

Conservare richieste e JSON originali con hash, stati HTTP/DRMS e contatori. Parsing invalido e dato
assente restano distinti. Zero righe significa assenza di record soltanto con risposta riuscita e
conteggio zero; timeout, errore e intervallo non interrogato non diventano lacune solari.

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
localizzate dai soli conteggi annuali.

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
Se gli ignoti sono prevalenti, il rapporto riporta la copertura di identificazione per periodo e il motivo
(campo non esposto, significato non documentato, sorgente irrisolta o budget), senza stimare la miscela
1/5 minuti dai soli casi risolti. Anche con l'inventario completo, **Q6, rumore per record, resta aperta**
finché il prodotto e il suo trasferimento alla griglia CEA non sono documentati. Non si sostituisce un
rumore unico per l'era MDI.

## 6. Associazioni candidate nella sovrapposizione

Finestra scientifica dei record SMARP: `[2010-05-01, 2010-10-29)` TAI. HMI è acquisito con **360 s di
margine prima e dopo**; i record di margine servono solo all'abbinamento e sono esclusi dai conteggi
di HARP/record nella finestra scientifica, con conteggi separati. Nessuna associazione dal solo NOAA.

### 6.1 Tempi

Registrare `T_REC_epoch`/`T_REC_step` se esposti, o gli equivalenti documentati, le unità e la scala
temporale. Se non esposti restano ignoti; non si deduce un'epoca dalla prima osservazione disponibile.
96 minuti sono 8 passi da 12 minuti: griglie con fase allineata possono dare scarti nulli. Verificare
la fase degli epoch modulo 720 s e riportare la distribuzione degli scarti firmati e di `|ΔT_REC|`.
L'allineamento non è imposto e i record mancanti non sono sostituiti.

Per ogni record SMARP e ogni HARPNUM, scegliere il record HMI temporalmente più vicino entro **360 s**;
pari merito al tempo più antico. Il criterio è T_REC in TAI; conservare T_OBS e gli scarti corrispondenti
se esposti, senza sostituirli al criterio dopo aver visto quanti abbinamenti producono. Tutte le coppie
così ottenute sono il dominio temporale su cui valutare geometria, coordinate mancanti e ambiguità.

### 6.2 Centro e riquadro, senza immagini

Centro = trasformazione WCS del punto `((nx-1)/2, (ny-1)/2)` con origine pixel zero; dimensioni per
record e WCS completa come in §3. **CRPIX nelle intestazioni FITS usa origine 1**: si conserva il valore
originale nell'header passato ad Astropy, senza sottrarre manualmente 1. La chiamata sui pixel centrali
usa esplicitamente origine 0 (`wcs_pix2world(..., 0)`); il controllo equivalente con pixel traslati di
+1 usa origine 1 e deve dare la stessa posizione entro `1e-10°` di distanza sferica. La prova con CRPIX
lontano dal centro verifica anche questa convenzione. `CRVAL1/2` non sono automaticamente il centro. In
alternativa è ammesso un centro geometrico esplicitamente documentato nella mappa dei campi, con metodo
registrato. Senza i dati necessari: `not_assessable`. Nessun uso sostitutivo di centri magnetici pesati.
Distanze di cerchio massimo in coordinate Carrington/eliografiche, longitudini periodiche.

Descrittore prefissato della sovrapposizione dei riquadri: trasformare con la WCS **65 punti per lato**
del bordo esterno dei pixel (`x=-0,5` e `nx-0,5`, `y=-0,5` e `ny-0,5`, estremi inclusi). Ricavare
l'inviluppo nei limiti di longitudine svolta intorno al centro e latitudine. L'inviluppo è approssimato:
le mappe CEA oblique non sono rettangoli in longitudine/latitudine e i soli quattro angoli non bastano
in generale a descriverne il perimetro. Non è l'area della maschera magnetica né un overlap esatto.

Per i due inviluppi calcolare l'intersezione tenendo conto di 0/360°, la frazione sull'area di ciascun
inviluppo e `envelope_iou_65` = intersezione/unione. Usare l'angolo solido del rettangolo sferico,
`Δlon_rad · (sin(lat_max)-sin(lat_min))`. Punti non finiti, ampiezza in longitudine ≥180° o geometria
non documentabile: overlap non valutabile, mai zero di sostituzione. I casi di contatto hanno area zero.
Si conservano metodo e flag di approssimazione; nessuna nuova dipendenza software non revisionata.

L'overlap è un **descrittore**, non una prova di identità. Si annota per tutte le coppie temporali
valutabili; i casi con intersezione positiva ma centro distante oltre 10° si conservano come
`box_only` separati, senza introdurli nei grafi angolari né eliminarli dal rapporto. Questo permette
di segnalare estensioni diverse e patch multi-NOAA senza aggiustare la soglia dopo i risultati.

### 6.3 Grafi, completezza e unicità condizionata

Costruire separatamente **G5**, distanza ≤5°, e **G10**, distanza ≤10°, sugli stessi record temporali
valutabili. Conservare la fascia `5° < distanza ≤10°`. I gradi e gli indicatori di unicità sono
calcolati **separatamente su ciascun grafo**, prima di filtri di qualità o NOAA. Le soglie sono
operative/descrittive, non errori di posizione validati o criteri di identità fisica.

Un arco è unico nel suo grafo solo se entrambi gli estremi hanno grado 1. Riportare distintamente:

1. `unique_in_G5`, `unique_in_G10` e ambiguità che compare allargando a 10°;
2. completezza dell'acquisizione del dominio temporale (query verificate o intervalli mancanti);
3. completezza geometrica dei concorrenti temporali: una HARP con coordinate mancanti non può essere
   esclusa perché non genera un arco; contare questi casi anche per ogni record SMARP;
4. coppie `box_only`, concordanza NOAA e QUALITY di entrambi come descrittori distinti.

Unicità nel grafo dei record valutabili **non** certifica completezza della ricerca, corrispondenza
fisica o osservabilità della regione. L'etichetta resta condizionata al catalogo e al raggio usato anche
quando tutte le query sono complete. Nessuna scelta manuale del candidato più plausibile. Stati di
record (`no_candidate`, `has_candidate`, `not_assessable`), flag di completezza e stati degli archi
hanno denominatori separati e definizioni di partizione nei controlli; un'incompletezza non è "nessun
candidato". Eventuali informazioni parziali sono conservate anche se un altro candidato è valutabile.

Riportare coppie di record, coppie distinte TARPNUM–HARPNUM, ripetizioni temporali e componenti connesse
a livello di patch, per G5 e G10 separatamente; non contare le componenti come famiglie fisiche o
osservazioni indipendenti. Per contesto [B21, §III.1] riporta **127 regioni SMARP e 137 SHARP** nella
sovrapposizione e 6063 TARP nel database descritto allora: non sono coppie abbinate né obiettivi da
raggiungere; un archivio aggiornato e definizioni diverse possono cambiare i conteggi.

Le coppie sono candidate a un confronto futuro. Maschere, co-registrazione, contaminazione, risposta
strumentale e file recuperabili restano da verificare sulle mappe. Nessun filtro magnetico di S è
trasferito; il guadagno di potenza T3 non si deduce dal numero di archi.

## 7. Output e provenienza previsti

Cartella nuova per ogni corsa in `data/sharp/metadata_inventory_mdi/<run_id>/` per risposte originali e
schema; non sovrascrivere i metadati HMI esistenti. Tabelle compatte e rapporto, se autorizzati dopo
l'esecuzione, in `results/MDI_SMARP_INVENTORY/<run_id>/` e `docs/MDI_SMARP_METADATA_INVENTORY_RESULTS.md`.
Nessun output dell'inventario è stato prodotto.

| Artefatto | Contenuto minimo |
|---|---|
| `SCHEMA_*`, `FIELD_MAP.csv` | definizioni originali, profili dei campi, epoch/step, WCS e adattamento proposto/verificato con riferimenti e hash |
| `BUDGET_COUNTS.json`, `BUDGET_PAYLOAD.json` | richieste/righe dal censimento preliminare, byte/tempi misurati dopo i primi elenchi, preventivi e stato della parte non avviata |
| `QUERY_LOG.jsonl`, `RAW_SHA256.csv` | richieste, UTC di esecuzione, serie, intervalli TAI, esito, tentativi, byte, conteggi, file originali e SHA-256 |
| `RECORDS_*.csv.gz` | chiavi, metadati originali/normalizzati e stati; ordine per serie e chiavi primarie |
| `COVERAGE_MONTHLY.csv`, `GAPS.csv` | denominatori, finestre complete/parziali e tipo della lacuna; copertura full-disk distinta dalle patch |
| `QUALITY_SUMMARY.csv`, `PRODUCT_SUMMARY.csv` | valori/bit e prodotti 1/5 minuti, ignoti e conflitti; denominatori per epoca e per patch |
| `OVERLAP_CANDIDATES.csv.gz`, `OVERLAP_SUMMARY.csv` | G5/G10 separati, distanze e scarti di tempo, margini temporali, completezza dei concorrenti, overlap dei riquadri e casi box_only, ambiguità/ripetizioni, patch/componenti |
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
troncamento; finestre annuali/mensili/settimanali e margini ±360 s; tempi TAI/UTC; chiavi duplicate;
QUALITY signed/missing; origine 1/5 minuti
ignota o conflittuale; longitudini 0/360; parità temporali; associazioni uno-a-molti; tutti i tetti,
divieto di export/download e ripresa senza azzerare i consumi. Aggiungere server sintetico a ricezione
lenta ma continua (deadline assoluta), risposta compressa inattesa, retry/redirect, budget di conteggi
e payload, WCS con CRPIX lontano dal centro, perimetri e inviluppi a cavallo di 0/360°, candidato senza
coordinate e unicità in G5 che scompare in G10. Prove prive di dati magnetici reali.

Prima di interpretare l'inventario: riconteggio separato da CSV/JSON salvati, hash e provenienza,
completezza per finestra, chiavi, riconciliazione sorgente/patch e somme dei denominatori, grafo e
partizione dei suoi stati. Un campo mancante previsto è un limite riportato; errore tecnico, hash
discorde, conflitto di identità o conteggio non riconciliato impediscono di certificare completezza.

Se sono raggiunti i tetti o l'archivio non risponde, rapporto **parziale/non verificabile**; non si
trasforma l'intervallo non acquisito in una lacuna solare. Nessuna soglia sul numero minimo di coppie:
l'inventario serve a descrivere la fattibilità, non ad approvare l'estensione.

## 9. Sequenza operativa dopo il congelamento

1. Revisione del piano completata sulla bozza `c70e91d`; precisazioni finali in §12.
2. Piano congelato in un commit dedicato **prima** del codice; SHA-256 e commit registrati separatamente
   come in §12, senza auto-riferimento. Nessuna modifica dei protocolli HMI.
3. Scrivere e provare offline il raccoglitore separato; revisione del trasporto, del budget e del codice
   prima della rete. Verificare la fine della griglia T5 senza aprirne i risultati scientifici.
4. Eseguire la sola fase schema, conservare risposte e proposta della mappa, far verificare e registrare
   la mappa. Solo dopo: conteggi/preventivo → primi elenchi della sovrapposizione → verifica del volume e
   tempo → storico → ausiliari. Ogni passaggio rispetta i consumi cumulativi; non è un via alla rete dato
   dal solo congelamento del piano.
5. Controllo tecnico e riconteggio, rapporto descrittivo e revisione esterna. Nessun download automatico
   al raggiungimento di un numero di coppie.
6. Valutare un **nuovo piano** per potenza prospettica di T3 e confrontabilità strumentale. Lo studio
   morfologico su S non è un prerequisito; T3 dentro i cicli resta distinto dal quenching fra cicli.

Nessuna fase di codice o rete è stata avviata dalla preparazione/congelamento del piano. La durata sarà
misurata: il tetto di 90 minuti non è una stima di completamento.

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

- [A] [Documentazione Astropy WCS](https://docs.astropy.org/en/stable/wcs/example_create_imaging.html):
  riferimento WCS, trasformazione pixel/mondo e origine pixel. I metodi geometrici di questo piano non
  sono raccomandazioni di calibrazione della documentazione.

Le scelte operative (finestre, tetti, soglie di associazione e output) sono fissate da questo piano,
non sono raccomandazioni delle fonti né criteri già validati.


## 11. Revisione 2: provenienza delle correzioni

Revisione interna Codex della propria bozza `5563c8b`, seguita dalla revisione esterna Claude Opus 5.5
e dalla sintesi in nove punti inviata dall'utente. Non sono revisioni cieche; nessun record JSOC usato.

| Punto della sintesi | Recepimento |
|---|---|
| 1. Budget richieste | annuali full-disk/continuo; settimanali HMI; preventivo 468 + 200 + 200 = 868, da ricalcolare dopo i conteggi (§4.2) |
| 2. Ricezione limitata | trasporto proprio, limite byte e deadline durante la ricezione, registro cumulativo (§4.1) |
| 3. Ordine | sovrapposizione prima degli elenchi storici, ausiliari per ultimi e raggruppati (§4.3) |
| 4. Volume/campi | profili minimi nello storico, ricchi solo nella sovrapposizione; conteggi prima degli elenchi; byte stimati soltanto dopo misure di payload (§§3–4) |
| 5. Margini | HMI ±360 s, record di margine distinti (§§2,6.1) |
| 6. Griglie | epoch/step documentati, fase e distribuzioni degli scarti (§6.1) |
| 7. Geometria | centro da WCS completa; overlap approssimato dei riquadri, distinto dalla maschera (§6.2) |
| 8. Unicità | G5/G10 separati, ricerca e geometria complete o parziali distinte dai gradi (§6.3) |
| 9. Ignoti/contesto | rumore per record aperto se prodotto ignoto; conteggi 127/137 riscontrati in B21, non bersagli (§§5.3,6.3) |

Scelte aggiuntive esplicite della revisione: volume massimo da 500 MiB a 1 GiB e tempo da 60 a 90 minuti,
prima di qualunque misura; richieste e righe restano 1000 e 2 milioni. Questa descrive la fase di
bozza della revisione 2; il successivo congelamento con precisazioni è registrato in §12. Studio
morfologico S in pausa, intatto.


## 12. Verifica finale e registrazione del congelamento

L'utente ha trasmesso la verifica esterna di Claude Opus 5.5 su `c70e91d`: nove punti recepiti, somme
ricontrollate, nessun problema bloccante e tre precisazioni prima del congelamento. È una verifica
esterna riportata nella chat, non una prova di esecuzione del raccoglitore. Precisazioni recepite:

1. motivazione dei tetti 1 GiB / 90 minuti, compreso il profilo ricco HMI non misurato (§4.1);
2. origine dei pixel: CRPIX FITS a base 1, centro e chiamata WCS a base 0, equivalenza da verificare
   nelle prove offline previste (§6.2);
3. tre tentativi su tutte le richieste possono superare il budget: arresto parziale esplicito (§4.2).

Il documento è rinominato da `MDI_SMARP_METADATA_INVENTORY_PLAN_DRAFT.md` a
`MDI_SMARP_METADATA_INVENTORY_PLAN.md`. SHA-256 dei byte congelati e commit del congelamento sono
registrati **fuori da questo file**, in `docs/MDI_SMARP_METADATA_INVENTORY_FREEZE.json`, dopo il commit
dedicato e prima del codice. Il raccoglitore dovrà verificare quell'hash e riportarlo nelle ricevute.
La ricevuta non modifica il piano né attesta che il codice o l'inventario esistano già.

Nessuna query eseguita, nessuna mappa scaricata, nessun codice del raccoglitore scritto in questo
passaggio. Rimangono obbligatori i test offline, la revisione del codice e la fine della griglia T5
prima della rete. Nessun risultato T5 aperto per questo congelamento. Nessun push.

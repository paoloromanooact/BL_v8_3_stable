# HMI: interpretabilità del bipolo nelle schede esistenti — bozza

**BOZZA NON CONGELATA — 2026-11-13. Nessuna nuova classificazione eseguita.**
Studio descrittivo limitato, da rivedere prima del congelamento. Non cambia P1,
P2 o P2f. Nessun nuovo test del quenching né selezione di un campione «che passa».

## 1. Domanda e informazione nuova

Quando i due centroidi della misura P1 descrivono un bipolo riconoscibile nella
mappa e quando riassumono più concentrazioni? Queste situazioni si accompagnano
alle sensibilità di maschera e centroidi già misurate?

S4 ha già confrontato HARP con una sola NOAA, ma è un filtro di metadati.
La lettura visuale esistente riguarda solo 25S. L'informazione nuova di questo
passo sarebbe l'estensione agli altri tre gruppi e il collegamento documentato
fra morfologia e controlli numerici esistenti, non una nuova pendenza di T3.

## 2. Campione e input già disponibili

Usare le **120 HARP già selezionate** dal piano dominanti: 20 dominanti e 10
controlli per 24N, 24S, 25N, 25S. Selezione, record e FITS restano quelli del
[piano congelato](DOMINANT_HARP_PLAN.md). Le 30 schede 25S già lette rimangono
un blocco storico; le altre 90 sono il lavoro visuale da completare.

Input: `figures/DOMINANT/`, `results/DOMINANT/DOMINANT_HARP_SELECTION.csv`,
`DOMINANT_HARP_CHECKS.csv`, `DOMINANT_HARP_VARIANTS.csv` e catalogo P1 per
l'appartenenza a S. Non sono necessari nuovi segmenti o download.

Le 120 includono 101 record di S. La base originaria è quella dei primari
validi P1, non S: separare sempre appartenenza a S e risultati per gruppo.
Dominanti e controlli hanno meccanismi di selezione diversi; non aggregarli
come se fossero rappresentativi dell'intero catalogo.

## 3. Lettura e registrazione

Prima delle nuove letture fissare una scheda con HARPNUM, gruppo, lettore,
data, classe, motivo visuale e valutabilità dei centroidi. Classi proposte:

| Classe | Descrizione operativa |
|---|---|
| A | Un sistema bipolare riconoscibile; i centroidi rappresentano le due concentrazioni principali. |
| B | Più sistemi o concentrazioni; un asse globale è calcolabile, ma non è chiaramente quello di un solo bipolo. |
| C | Almeno un centroide è tra concentrazioni distinte della stessa polarità; l'asse è una media fra strutture. |
| D | Configurazione diffusa, frammentata o fortemente sbilanciata; coppia bipolare poco riconoscibile. |
| U | Scheda insufficiente per giudicare. |

Conservare classi miste nei casi di confine e una motivazione testuale. Queste
sono descrizioni della mappa, non identificazioni fisiche delle regioni né
classi di errore. B e C possono coesistere. Per D distinguere sbilanciamento
visibile e frammentazione; non dedurre «decadimento» da un solo istante.

Non usare segno o ampiezza di tilt, S_BL, anti-Hale, attività o risultato del
fit per assegnare una classe favorevole. Il numero NOAA viene confrontato
solo dopo aver registrato la descrizione della mappa. Le schede contengono
già annotazioni numeriche e alcune sono già state viste: la lettura **non è
cieca**. Non dichiararla tale, nemmeno se si evitano le annotazioni.

Registrare separatamente: centroidi dentro concentrazioni o fra esse;
possibile taglio al bordo; giudizio impossibile. Una scheda ritagliata non
verifica l'appartenenza del campo ad altre patch. Richieste di contesto restano
«non verificato», senza espandere automaticamente il campione o i dati.

## 4. Tabelle e lettura dei risultati

Una volta registrate le classi, collegarle agli output esistenti e produrre:

1. Una riga per HARP, distinguendo le 30 classificazioni storiche dalle 90 nuove;
   eventuali rettifiche delle prime conservano etichetta precedente e motivo.
2. Conteggi per gruppo, dominanti/controlli e appartenenza a S; confronto con
   il numero NOAA. Nessun test di significatività o soglia di accettazione.
3. Per classe, contributi netti e Σ|S_BL|, sempre con denominatore esplicito,
   e le differenze già calcolate per bitmap ≥ 1 e pesi uniformi: sia ΣΔ sia
   Σ|Δ|. Riportare anche confronti mancanti; non sostituirli con zero.

La classificazione visiva non ha una validazione contro una verità fisica.
Con un solo lettore, dichiararlo; non inferire riproducibilità tra lettori.
Il campione può illustrare un limite della definizione HARP e individuare casi
da approfondire; non stima la prevalenza dei complessi in S o nell'era HMI.

## 5. Limite del passo e decisione successiva

Completare le 120 righe e le tabelle descrittive, poi fermarsi. Nessuna
segmentazione, esclusione di HARP, ricalcolo di P1, nuova applicazione T3 o
modifica T5. Una classe complessa non prova un errore, né spiega da sola il
risultato «non deciso» del quenching.

Prima dell'esecuzione: revisione della griglia di lettura, congelamento con
commit e hash, poi eventuale codice di aggregazione. Le soglie dei vecchi
controlli numerici restano quelle del piano dominanti. Questo passo non
richiede simulazioni di potenza, degradazione HMI o nuovi dati MDI.

Un eventuale studio successivo sulla popolazione S e sulle pendenze per
morfologia richiede una decisione distinta e un nuovo piano non cieco.

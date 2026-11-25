# HMI: active-region nests e successivo confronto bayesiano — BOZZA rev. 1

25 novembre 2026, Codex. **Non congelata; nessuna identificazione reale o inferenza avviata.**
Piano `BL_WORK_PLAN.md`, voce N, collegata a BQ e BT. Fonti primarie e limiti dei dati complementari:
`HMI_NESTS_FINLEY_METHOD_NOTES.md`. Disponibilita: `HMI_NESTS_FEASIBILITY.md`.

## 0. Domande, informazione gia vista e portata

Obiettivi: sorgente BL e quenching del tilt. I risultati precedenti P1/P1e, morfologia, T3/T5 e MDI/MWO sono
noti; questa proposta e non cieca rispetto a essi. L'inventario ha letto disponibilita, posizioni e identita,
non nuove distribuzioni di tilt, flusso o S_BL. Non modifica gli esiti dei protocolli precedenti.

Domande distinte:

1. Quali concentrazioni spazio-temporali sono candidati di nesting, con quale copertura e ambiguita?
2. Quali contributi osservativi BL hanno i membri, senza trasformare ricomparse in nuove emersioni?
3. Quanto cambia l'inferenza sulla dipendenza del tilt dall'attivita quando si considera la dipendenza fra membri?
4. Per BT, come impedire che una stessa struttura venga usata sia per calibrare sia per verificare il modello?

Un nest fisico richiede evidenza di emersioni ripetute, non soltanto sopravvivenza. Un candidato da catalogo non
viene dichiarato confermato perche un modello bayesiano gli attribuisce un effetto diverso da zero.

## 1. Unita e popolazioni

Proposta: distinguere tre livelli con tabelle e chiavi proprie.

- **Record:** HARPNUM, T_REC, posizione in Carrington, provenienza. Le osservazioni ripetute restano collegate.
- **Famiglia/evento candidato:** identita P1e e informazioni sulla comparsa, con flag di ricomparsa, buchi e
  possibili nuove emersioni. Primo avvistamento non equivale a emersione, soprattutto dal lembo est.
- **Nest candidato:** insieme di eventi/strutture vicine in spazio-tempo; membership, fusioni/scissioni e dubbi
  registrati. Nessuna unione automatica di tutta una catena di vicinanze in un solo oggetto fisico.

Contesto: 8296 HARP nei metadati locali. Contributi P1: solo le 7133 HARP con primario e le misure ammesse dal
protocollo pertinente. Inferenza T3: definire il collegamento agli stessi record del campione S, senza ampliare
silenziosamente il campione in base ai nests trovati. Non usare NOAA come chiave unica o filtro implicito.

## 2. Identificazione: proposta da chiudere prima del congelamento

**Due prodotti separati:** candidati da catalogo HMI e casi con evidenza morfologica di emersioni ripetute.
La seconda verifica puo richiedere AIA e, per la continuita sul lato nascosto, EUI/PHI nelle finestre disponibili.
Nessuna campagna di acquisizione e inclusa automaticamente in questa bozza.

Per la prima versione proponiamo una ricerca in coordinate rotanti che consideri latitudine, longitudine
periodica e tempo. La specifica definitiva deve fissare, senza leggere i contributi BL dei candidati:

- finestra temporale e spaziale, numero minimo di eventi distinti, deriva ammessa e trattamento dell'equatore;
- regola delle appartenenze multiple e dei legami di ricomparsa; bloccare la percolazione di catene che
  colleghino strutture distanti per molti anni senza continuita documentata;
- scelta fra un riferimento di Carrington e una griglia di velocita predefinita; le stesse ricerche e massimi
  si applicano ai controlli casuali. Nessuna velocita scelta per rendere maggiore il quenching;
- popolazione osservabile, criteri di qualita, buchi temporali, censura ai bordi del periodo e incertezza
  delle date; HARP senza primario restano contesto, non sorgenti gia misurate;
- uso delle famiglie P1e: flag ed esclusioni/sensibilita dichiarati, non etichette certe di identita;
- indipendenza da tilt, S_BL e obiettivo del ranking nella costruzione dei gruppi.

Le soglie riportate in letteratura non sono ancora adottate: la nota fonti documenta una discrepanza interna
fra sezioni di Norton e la diversa definizione osservativa dei casi Finley. Prima del codice reale si sceglie
una definizione operativa motivata e se ne fissano le sensibilita; nessuna ottimizzazione sui risultati fisici.

## 3. Prove e controlli dell'identificazione

Prima dei dati: sequenze sintetiche con emersioni distinte, ricomparse, deriva, sovrapposizioni, fusioni e
buchi; casi senza nesting con densita dipendente da ciclo e latitudine. Verificare periodicita 0/360,
ordinamento, duplicati, stabilita agli identificativi e denominatori.

Controlli casuali: mantenere tempi, latitudini, disponibilita e attributi; stabilire l'unita di randomizzazione
prima del calcolo. Se si conserva una famiglia persistente, la traslazione longitudinale va applicata
coerentemente ai suoi membri, invece di distruggerne artificialmente il legame. Ripetere l'intera procedura di
ricerca, comprese eventuali scansioni. Le associazioni casuali non etichettano direttamente i falsi positivi reali.
Semi e numero di repliche restano da riservare dopo controllo delle collisioni, prima delle corse.

I casi Finley 2022/2024 possono guidare una verifica descrittiva delle associazioni, con provenienza esterna
esplicita. Sono casi gia conosciuti e selezionati per attivita, non un campione indipendente rappresentativo
per validare il quenching. Nessuna selezione dei nostri casi in base ai flare o alla dimensione di S_BL.

## 4. Contributi BL: definizioni prima delle somme

Riportare appartenenza, durata/copertura e distribuzioni osservate di flusso, separazione, tilt e S_BL.
Separare conteggi di record, HARP, famiglie ed eventi. Sommare il proxy al meridiano di record diversi non
equivale al flusso nuovo emerso o al contributo finale al polo. Le varianti con/senza candidate ricomparse
sono sensibilita osservativa, non due ricostruzioni certe dell'emersione.

Se non si distingue il campo persistente dal nuovo flusso, l'uscita resta un contributo osservativo definito
sul catalogo. Nel trasporto lineare assialsimmetrico la sola longitudine non cambia il dipolo assiale;
la domanda fisica riguarda anche tempi, latitudini, tilt, flussi e ipotesi di trasporto.

## 5. Confronto bayesiano: disegno iniziale proposto

Sugli stessi dati HMI, un disegno fattoriale distingue dipendenza dall'attivita e dipendenza dal nest:

| Modello candidato | Pendenza di attivita | Effetto del nest |
|---|---|---|
| M0 | nulla | assente |
| MQ | libera, entrambi i segni | assente |
| MN | nulla | gerarchico |
| MQN | libera, entrambi i segni | gerarchico |

Proposta di media, da verificare sui sintetici: [k_(ciclo,emisfero) + beta(A-1) + b_nest] sin|lambda|,
piu componente temporale per CR/emisfero e residuo individuale con dispersione da modellare. Il termine b_nest
modifica il coefficiente di Joy; un semplice spostamento additivo del tilt e una sensibilita distinta.
Per i non membri e le appartenenze ambigue definire esplicitamente likelihood e trattamento dell'incertezza.

**Non ancora scelti:** distribuzione del residuo, processo temporale, prior numeriche, misura degli errori,
varianti dell'effetto del nest e metrica del confronto. I nests di breve durata possono essere confusi con
attivita e tempo: simulare questa mancata identificabilita prima di adattare il modello ai dati.

Il flusso come peso scientifico di P1/T3 non diventa automaticamente precisione osservativa. Non elevare la
likelihood a pesi con unita arbitrarie per poi interpretarli come probabilita o evidenze bayesiane. Fissare il
bersaglio e la relazione fra varianza e flusso; dimostrare che cosa resta confrontabile con T3 storico.

Richiedere controlli predittivi, sensibilita alle prior proprie, campioni posteriori affidabili e confronto
predittivo che escluda gruppi e blocchi temporali; membri dello stesso nest non divisi fra stima e verifica.
Per previsioni reali future, il raggruppamento non puo usare eventi futuri sconosciuti al momento della previsione.
Eventuali Bayes factor richiedono prior di parametro e di modello esplicite e verifica del calcolo delle evidenze.
I pesi predittivi non sono probabilita di verita fisica. Non scegliere la versione di clustering che favorisce MQN.

Uscite: distribuzione di beta, probabilita di segno e oltre una soglia fisica definita prima, varianza fra nests,
incertezza del ranking, sensibilita alle associazioni e adeguatezza di tutti i candidati. Il fatto che un
modello vinca relativamente non dimostra il meccanismo fisico o corregge da solo una classificazione sbagliata.

## 6. Sequenza e responsabilita

1. Inventario e note fonti (Codex, completati; nessun nest classificato).
2. Revisione incrociata delle scelte aperte e specifica definitiva: identificazione prima, ranking dopo.
3. Congelamento con input, codice, semi, regole e disclosure di quanto gia noto.
4. Implementazione, prove sintetiche e riconteggio indipendente; nessuna modifica ai piloti SFT congelati.
5. Identificazione, conservazione e verifica prima della lettura dei contributi; rapporto osservativo.
6. Inferenza bayesiana sotto specifica congelata, controlli e rapporto separato.

Claude continua A1 e la chiusura dei piloti SFT. Non serve duplicare l'inventario qui consegnato. Nessun nuovo
FITS o dato AIA/Solar Orbiter e stato richiesto o scaricato; eventuali dati complementari hanno specifica propria.

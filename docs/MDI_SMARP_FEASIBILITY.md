# MDI/SMARP e ciclo 23 — studio preliminare di fattibilità

Stato: **bozza documentale, 2026-11-11; non è un protocollo**. Nessuna query JSOC,
nessun download di mappe e nessun calcolo scientifico eseguito per questo studio.
Fonti primarie consultate oggi; disponibilità effettiva degli archivi da verificare.

La proposta è verificare prima la confrontabilità della misura BL, poi il beneficio
statistico dell'estensione. Non è ancora giustificata la concatenazione con P1.

## 1. Dati documentati e differenze essenziali

| Aspetto | SMARP/MDI | SHARP/P1 attuale |
|---|---|---|
| Serie | `mdi.smarp_cea_96m` | `hmi.sharp_cea_720s` |
| Campo | lungo la linea di vista (LOS) | `Br` dalla misura vettoriale |
| Cadenza | 96 minuti | 12 minuti; selezione P1 dai metadati orari |
| Griglia CEA documentata | 0,12°/pixel | 0,03°/pixel |
| Maschera | bit magnetici, fotometrici e appartenenza TARP | P1 usa bitmap ≥ 33 e soglia 100 G |

SMARP documenta gennaio 1996–28 ottobre 2010; l'osservazione MDI prosegue oltre,
ma non coincide con la disponibilità SMARP. Rumore e distorsione ottica differiscono
fra strumenti. La rimappatura CEA non ricostruisce il vettore da una misura LOS.
Fonte: [Bobra et al. 2021, §§2–3 e tabelle 1–2](https://arxiv.org/html/2108.07918).
Le scelte P1 nella tabella vengono dal protocollo locale `PROTOCOL_P1_SBL_SERIES.md`.

Il repository degli autori offre esempi per associazione TARP–HARP, maschere,
allineamento e accesso tramite drms. Indica una sovrapposizione **1 maggio–28 ottobre
2010**: non assumere un anno intero nel 2010–2011.
Fonte: [repository SMARPs degli autori](https://github.com/mbobra/SMARPs).

Un lavoro successivo combina parametri SMARP/SHARP dopo filtraggio e riscalatura,
per applicazioni ai brillamenti. Non costituisce una validazione della nostra
misura S_BL, del tilt o dell'efficienza per unità di flusso.
Fonte: [Kosovich et al. 2024, abstract](https://arxiv.org/abs/2401.05591v3).

## 2. Implicazioni per il progetto (valutazione nostra)

S_BL dipende insieme da flusso, distanza fra polarità, latitudine e tilt. Una
correzione moltiplicativa del solo flusso non garantisce centroidi, tilt e somme
comparabili. Anche η = D*/Φ può cambiare: una cancellazione del fattore di flusso
non cancella differenze di selezione, geometria o contributi delle polarità.

La trasformazione candidata Br ≈ B_LOS/μ, con μ = cos dell'angolo eliocentrico,
richiede l'ipotesi di campo radiale. Per proiezione, B_LOS contiene anche le
componenti orizzontali: la divisione non le separa e amplifica il rumore quando μ
è piccolo. Il centro della patch e il centro del disco sono posizioni diverse;
un taglio sulla sola longitudine non fissa μ, che dipende anche da latitudine e B0.
Queste sono implicazioni geometriche, non una correzione già validata.

I conteggi minimi di pixel di P2 non vanno copiati su una griglia diversa: cambierebbe
l'area minima accettata. Servono criteri espressi fisicamente e un nuovo campione
con dichiarazione delle differenze rispetto a P1/P2. Anche i bit di qualità e
maschera vanno decodificati dalla specifica di ciascuna serie, non trasferiti per
somiglianza dei nomi. TARPNUM, HARPNUM e NOAA non sono chiavi intercambiabili.

## 3. Percorso proposto prima di scaricare il ciclo 23

1. **Inventario dei metadati.** Dopo un piano dedicato, verificare serie, segmenti,
   WCS, versioni, qualità, tempi effettivi, copertura e lacune. Conservare risposte
   della query e hash. Definire l'elenco completo delle patch candidate e delle
   esclusioni, evitando di scegliere solo gli abbinamenti riusciti.
2. **Campione della sovrapposizione.** Fissare prima tempi, limiti di μ/longitudine,
   regole spaziali di associazione, fusioni/scissioni e ricomparse. NOAA può aiutare,
   ma non sostituisce la corrispondenza spaziale e temporale. Separare per regione
   i dati di sviluppo da quelli di controllo; istanti della stessa patch non sono
   osservazioni indipendenti. Registrare anche le patch senza corrispondente.
3. **Confronto a passaggi.** Proponiamo HMI Br → HMI LOS con trattamento radiale
   candidato → HMI LOS degradato a risoluzione/campionamento MDI → MDI LOS con lo
   stesso trattamento. Questa scomposizione serve a distinguere proiezione,
   risoluzione e risposta strumentale. Non basta ridurre il numero di pixel:
   risposta spaziale e conservazione del flusso richiedono una specifica.
   Confrontare maschera comune e maschere native, dichiarando quale domanda
   risponde ciascuna variante.
4. **Grandezze da controllare.** Φ positivo/negativo, d, tilt modulo 180°, segno,
   S_BL, D*, η e probabilità di entrare nel campione. Riportare dipendenze da μ,
   latitudine, intensità, area, complessità e tempo. Per somme nette prossime a
   zero usare anche differenze assolute normalizzate a Σ|S_BL|; il solo rapporto
   può essere instabile. Le soglie di accettazione vanno motivate fisicamente e
   fissate prima del controllo, non ricavate per far passare gli abbinamenti.
5. **Valutazione dell'estensione.** L'accordo nella breve sovrapposizione non
   prova la stabilità sull'intero ciclo 23 né la confrontabilità delle regioni
   fuori dal suo intervallo di intensità. Documentare il dominio coperto e quello
   estrapolato; un'eventuale correzione richiede verifiche temporali aggiuntive.

## 4. Beneficio statistico da dimostrare

L'aggiunta di anni e regioni non equivale all'aggiunta dello stesso numero di unità
indipendenti. Il cambio di strumento è associato al cambio di ciclo: una differenza
strumentale residua può confondersi con un effetto fisico fra cicli.

Prima di una serie congiunta proporrei simulazioni sul disegno effettivamente
osservabile, confrontando HMI da solo con HMI+MDI. Vanno incluse selezione e dati
mancanti, dipendenza temporale, incertezza della trasformazione strumentale ed
errori sistematici plausibili dipendenti dall'attività. Le scale di attività e degli
effetti devono essere mantenute confrontabili e definite prima: rinormalizzare
l'attività su un periodo diverso cambia l'unità della pendenza.

Valutare falsi verdetti, copertura e potenza agli stessi effetti scientifici, con
semi indipendenti e regola di arresto. P2f, anche se superasse la validazione HMI,
non sarebbe automaticamente validato sul nuovo disegno. L'estensione può essere
utile per un catalogo descrittivo anche se non rende affidabile l'inferenza.

## 5. Esito e lavoro successivo

**Fattibilità documentale plausibile; confrontabilità quantitativa e guadagno
statistico non misurati.** Il prossimo prodotto è una bozza di protocollo per il
confronto nella sovrapposizione, con campione, metriche, soglie, unità indipendenti
e costi definiti. Non si avvia ora l'estensione completa e non si modifica P1.

Restano aperti: disponibilità corrente JSOC e dimensione del campione utilizzabile,
segmenti/versioni esatti, specifica del campo radiale candidato, risposta spaziale,
trattamento della qualità, criterio di accettazione del confronto, trasferibilità
fuori dalla sovrapposizione e costo del calcolo. Nessuno di questi è un risultato
acquisito da questa lettura.

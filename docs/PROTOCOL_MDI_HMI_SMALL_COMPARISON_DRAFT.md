# Piccolo confronto MDI–HMI — bozza descrittiva

**BOZZA NON CONGELATA — 18 novembre 2026. Nessun campione estratto, nessun download o calcolo reale.**
Proposte da rivedere prima dell'uso; i nuclei numerici sono scritti soltanto per prove sintetiche.
Non modifica i protocolli HMI o quello dell'inventario. La vecchia bozza HMI LOS resta rinviata:
questo è un esperimento più piccolo, senza degradazione, PSF, rumore aggiunto o prova di potenza.

## 1. Domanda e limiti

Descrivere quanto cambiano flusso, centroidi, tilt e dipolo passando da Br a LOS/μ, e fra due strumenti
usati entrambi come LOS/μ. Non stimare il quenching, non validare un test, non stimare una calibrazione
globale o una pendenza contro l'attività. Br HMI è un riferimento strumentale, non la verità.
La sovrapposizione del 2010, vicino al minimo, non determina lo scarto strumentale dipendente dall'attività
che potrebbe imitare il quenching. Non si trasferiscono fattori 1,40 o 1,438 a queste misure.

## 2. Informazioni già viste

Sono noti i risultati HMI, T3 non deciso e T5 descrittivo, le analisi morfologiche e i metadati
dell'inventario. Le soglie proposte sotto sono informate dall'audit di tempi e associazioni del
16 novembre: dichiarazione di non cecità. Nessuna risposta di una nuova mappa trasformata è stata letta.

Input di selezione proposti: soli metadati e grafi salvati dalla corsa `schema_20261116_http_ac06138`,
analisi `198785bb3002`. Congelare gli hash prima di estrarre. Nessun tilt, S_BL, D o differenza fra
strumenti entra nella selezione. I conteggi noti non garantiscono la disponibilità dei segmenti FITS.

## 3. Campione proposto: fino a 12 coppie, nessuna estrazione ora

Una coppia di record è eleggibile se: arco univoco in G5 e ancora univoco in G10, T_OBS finito per
entrambi e |ΔT_OBS| ≤ 360 s; centri documentati, stesso emisfero e |latitudine| ≤ 30° per entrambi;
longitudine di Stonyhurst del centro HMI entro 30°. Coordinate di osservatore complete richieste.
Non usare il numero NOAA per escludere: conservare concordanza/mancanza ed eventuali conflitti.
La definizione del centro dalla WCS/metadati non è il centroide magnetico e non va sostituita con esso.

Formare quattro strati: emisfero N/S × |longitudine HMI| ≤ 15° oppure 15° < |longitudine| ≤ 30°.
Per ogni coppia TARP–HARP e strato scegliere l'arco con |longitudine HMI| minimo, poi |ΔT_OBS| minimo,
poi T_REC più antico, poi chiavi lessicografiche. Ordinare le coppie per SHA-256 della stringa ASCII
`MDI_HMI_PILOT_V1|TARPNUM|HARPNUM` (interi decimali senza zeri iniziali). Scorrere a turno i quattro
strati nell'ordine N centrale, S centrale, N laterale, S laterale; prendere al massimo tre per strato.
Una componente del grafo G10 tra patch può contribuire al massimo una volta. Se la componente è già
usata, scorrere la lista; se lo strato si esaurisce lasciare il posto vuoto. Nessun riempimento fra strati.
Il manifesto finale deve includere tutte le ragioni di esclusione e le chiavi complete di serie/record.

**Qualità: decisione ancora aperta e bloccante.** Registrare i valori grezzi MDI/HMI, senza equipararli.
Prima del congelamento serve una tabella primaria dei bit, una regola esplicita di eleggibilità per
ciascun prodotto e il riesame della sua influenza sul campione. Non proporre QUALITY=0 come default MDI.
Una successiva mancata mappa/polarità/geometria non dà diritto a una sostituzione del record.

## 4. Tre confronti distinti

| Confronto | Campi | Maschera e significato |
|---|---|---|
| A1 | Br HMI contro LOS proiettato da Br,Bt,Bp, poi diviso per μ | Stessa bitmap HMI, stesso record/griglia: approssimazione radiale a inversione comune |
| A2 | Br HMI contro magnetogram HMI misurato/μ | Stessa bitmap/griglia: include le differenze fra algoritmo LOS e inversione vettoriale |
| B | magnetogram MDI/μ contro magnetogram HMI/μ | Ciascuno sulla propria griglia e bitmap: differenze congiunte di misura, risoluzione e segmentazione |

Per A mantenere l'impronta di appartenenza HMI (codici 33/34); per B il bit di appartenenza 32 delle
bitmap native, con codici specifici dello strumento. Non imporre alle bitmap SMARP le classi di macchie.
Non chiamare B un isolamento dell'effetto strumentale: i domini delle patch possono essere diversi.
Nessuna riscalatura, interpolazione, ritaglio adattivo o maschera comune ricostruita per migliorare l'accordo.
Documentare estensione/contatto al bordo e le differenze di impronta nelle schede, senza correggerle.
Una futura misura su un dominio fisico comune richiederà una specifica propria prima di essere usata.

Geometria: coordinate di ogni pixel dalla WCS completa, CRPIX FITS a origine 1 e chiamata pixel a origine 0;
Br,Bt,Bp nei versori sferici locali, non sugli assi del ritaglio. μ calcolato per pixel dall'osservatore
a distanza finita, usando DSUN_OBS e RSUN_REF in metri, e CRLN_OBS/CRLT_OBS nello stesso riferimento
delle coordinate dei pixel. Non aggiungere una seconda correzione del tempo di volo senza una specifica.
Dominio proposto μ ≥ 0,8 su tutta la maschera del ramo; pixel non finiti o fuori dominio rendono il
confronto della patch non disponibile, senza tagli silenziosi. Registrare quantità e posizione dei pixel
responsabili. μ dal centro non sostituisce questa verifica.

Area superficiale esplicita in cm² da WCS CEA verificata e raggio; non usare la stessa area numerica
sulle due griglie. Soglia inclusiva |B_proxy| ≥ 100 G e limite |B_proxy| ≤ 10000 G, come P1; nessun
filtro di 20 pixel sul campionamento grosso. Distinguere le perdite per soglia da quelle di dominio.

## 5. Misure e lettura

Registrare Φ positivo/negativo/totale, centroidi sferici, distanza, tilt orientato e differenza assiale
modulo 180°, D e D_bal. Per ogni confronto: differenze firmate, differenze assolute e rapporto del
flusso solo con denominatore non nullo; conservare anche le differenze dei dipoli senza normalizzarle
con quantità vicine a zero. Nessun fallimento diventa misura zero. Stesse coppie confrontabili per
le tabelle fra rami; riportare anche la tabella completa dei tentativi e delle perdite.

Primo prodotto: una riga per coppia e ramo, schede e mediana/minimo/massimo sul campione disponibile,
distinti per centro/laterale e con denominatori. Nessun intervallo di copertura, bootstrap, equivalenza
o verdetto globale su 12 coppie. Un segno concordante non è prova di meccanismo o di quenching.
Nessuna somma di campione viene chiamata somma di ciclo o misura rappresentativa dell'intero catalogo.

Il nucleo preparato calcola solo grandezze indipendenti dal ciclo. S_BL, D* ed efficienza sono rinviati
finché un adattatore non congeli ciclo/segno/emisfero a un riferimento HMI documentato e ne verifichi
la riproduzione P1. Non assegnare automaticamente tutto il 2010 al ciclo 24 o usare le polarità per
scegliere il ciclo. Questo limite del codice è esplicito, non una nuova definizione della sorgente.

## 6. Acquisizione futura proposta, non autorizzata da questa bozza

Dopo revisione, congelamento, lista e verifica del costo: per al massimo 12 HMI i segmenti
Br,Bt,Bp,bitmap,magnetogram; per al massimo 12 SMARP bitmap,magnetogram. Massimo 84 FITS di patch,
nessun full-disk, continuum o ricerca sostitutiva. Conservare keyword complete, unità, tempi,
versioni, URL, disponibilità e SHA-256 in un manifesto separato. Gli eventuali file locali si possono
riusare solo con identità verificata del record/segmento; non si aprono ora.

Proposta di tetti separati dal registro dell'inventario: 512 MiB di corpi FITS effettivamente ricevuti,
32 MiB per file, 30 minuti cumulativi di acquisizione, 200 tentativi complessivi fra preparazione dei
metadati/risoluzione dei segmenti e download, al massimo due tentativi per file. Misurare le dimensioni
annunciate prima dei corpi; se il preventivo supera il tetto, fermarsi prima dei FITS, senza ridurre
il campione dopo aver visto misure. Durante ricezione applicare anche i limiti reali. Un arresto lascia
manifesto parziale e nessuna pretesa di confronto completo. Trasporto e verifica da rivedere: non scritti ora.

Seguire MTARP→MDATA richiede metadati di una serie oggi fuori dal piano dell'inventario. Prima di
ogni query va aggiunta in questa nuova specifica la serie esatta, l'operazione, i campi e il budget;
non si modifica o aggira il vecchio piano. L'INTERVAL ignoto non viene imputato né associato a un rumore.

## 7. Porte prima del congelamento e dell'esecuzione

1. Revisione della tabella QUALITY nativa e del percorso di sorgente; risolvere o dichiarare che una
   misura resta descrittiva con prodotto di integrazione ignoto. La regola di qualità deve essere concreta.
2. Revisione di campione, maschere, dominio μ, convenzioni LOS, area e tetti; nessuna garanzia statistica.
3. Manifesto di selezione solo dopo congelamento; revisione del successivo adattatore FITS/WCS/tempi e
   del downloader, con test offline; il nucleo puro non li sostituisce.
4. Prova di riproduzione R0 sui record HMI che coincidono con P1; sugli altri confronto con l'identica
   funzione P1 a ciclo fissato, dichiarando che non esiste un risultato storico per quel record.
   Le prove ora superate riguardano soltanto mappe sintetiche, non questa porta reale.
5. Verifica di provenienza, completezza e riconteggio delle differenze prima di interpretare le tabelle.

Fermo prima di congelamento, selezione, download e risposte reali. Il piano prospettico e la morfologia S
restano in pausa. Vedi [chiarimenti e fonti](MDI_SMARP_METADATA_CLARIFICATIONS.md) e
[consegna per il revisore](MDI_HMI_PREPARATION_REVIEW.md).

# Piccolo confronto MDI–HMI — bozza descrittiva

**BOZZA NON CONGELATA, revisione 2 con specifica geometrica proposta al §8 — 18 novembre 2026. Nessun campione estratto, nessun download o calcolo reale.**
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
Applicare la regola di qualità proposta sotto prima di ordinare e scegliere gli archi del campione.

**Blocco geometrico esplicito prima del congelamento.** I limiti del centro sopra non garantiscono
μ ≥ 0,8 sull'impronta. Si mantiene il controllo su tutta la maschera, non sui soli pixel forti. La strada
proposta è un controllo conservativo con estensioni documentate, B0 e distanza/raggio reali di ciascun
satellite, prima dell'ordinamento. L'audit dei soli file già salvati mostra però che LAT/LON_MIN/MAX,
DSUN_OBS e RSUN_REF sono negli schemi ma non nei CSV; NAXIS1/2 non sono keyword degli schemi. Non si
ricavano dimensioni da CRPIX né si sostituisce NPIX a un'estensione geometrica. Anche un rettangolo
di estremi richiede una verifica che contenga l'impronta attuale: non si presume che estremi storici
del transito o coordinate del piano dell'immagine siano limiti eliografici del record.

Perciò l'eleggibilità di dominio e la perdita attesa per strato sono attualmente **non valutabili**,
non zero. I conteggi diagnostici sulle condizioni disponibili sono nel rapporto di revisione; non
sono un campione selezionato né una promessa di 12 confronti. La revisione resta aperta su questo
punto. Servono metadati geometrici aggiuntivi con una specifica/autorizzazione propria, oppure una
nuova scelta esplicita del disegno da rivedere prima del congelamento. Non si passa automaticamente
all'opzione di controllare soltanto i pixel che entrano nella misura e non si abbassa 0,8.

Formare quattro strati: emisfero N/S × |longitudine HMI| ≤ 15° oppure 15° < |longitudine| ≤ 30°.
Per ogni coppia TARP–HARP e strato scegliere l'arco con |longitudine HMI| minimo, poi |ΔT_OBS| minimo,
poi T_REC più antico, poi chiavi lessicografiche. Ordinare le coppie per SHA-256 della stringa ASCII
`MDI_HMI_PILOT_V1|TARPNUM|HARPNUM` (interi decimali senza zeri iniziali). Scorrere a turno i quattro
strati nell'ordine N centrale, S centrale, N laterale, S laterale; prendere al massimo tre per strato.
Una componente del grafo G10 tra patch può contribuire al massimo una volta. Se la componente è già
usata, scorrere la lista; se lo strato si esaurisce lasciare il posto vuoto. Nessun riempimento fra strati.
Il manifesto finale deve includere tutte le ragioni di esclusione e le chiavi complete di serie/record.

**Qualità proposta, da rivedere.** Richiedere QUALITY MDI in {0, 0x200}, QUALITY HMI=0,
valori presenti e interpretabili come interi a 32 bit. Accettare notazione decimale con segno
nell'intervallo [−2^31, 2^32−1] o esadecimale non negativa con prefisso 0x e al massimo 8 cifre;
convertire i decimali negativi al medesimo pattern unsigned mediante q & 0xffffffff. Per esempio
−2147483648 e 0x80000000 hanno lo stesso bit alto e sono entrambi esclusi dalla regola proposta.
Non azzerare il bit 31 e non usare il valore assoluto. Valori mancanti, float, frazioni e valori fuori
intervallo sono non valutabili, non QUALITY=0. Conservare sempre il valore originale. Ogni altro
pattern è escluso con i bit conservati. La tabella primaria MDI definisce 0x200 come modo non PRIME 60: non lo si
chiama shutterless e non lo si presume equivalente al modo standard. Riportare separatamente i due
modi nel manifesto e nelle tabelle; nessuna compensazione per la diversa probabilità di inclusione.
È una scelta prudenziale di un campione tecnico, non la dimostrazione che ogni immagine ammessa sia
utilizzabile o che le escluse siano sempre inutilizzabili. La regola è proposta dopo aver visto le
frequenze dei metadati, prima di selezione/mappe. Una successiva mancata mappa/polarità/geometria non
dà diritto a una sostituzione del record. Vedi le fonti nella nota dei chiarimenti.

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
Dominio proposto μ ≥ 0,8 su tutta la maschera del ramo; pixel fuori dominio rendono il
confronto della patch non disponibile, senza tagli silenziosi. R0 è calcolato dalla funzione P1
invariata, con la sua esclusione dei Br non finiti e oltre il massimo. Per A sulla griglia HMI,
soglia e formula del riferimento restano esattamente P1. Il kernel dei confronti resta più severo:
un pixel non finito nell'impronta rende il confronto non disponibile. Registrare separatamente
`r0_reproduction_status`, motivi/conteggi delle esclusioni P1 e `comparison_status`; un rifiuto del
kernel non si trasforma in fallimento della riproduzione R0. Non imputare NaN con zero, non estendere
le esclusioni P1 agli altri rami e non ricalcolare il riferimento su una loro maschera ridotta. Registrare quantità e posizione dei pixel
responsabili. μ dal centro non sostituisce questa verifica.

Area superficiale esplicita in cm² da WCS CEA verificata e raggio; non usare la stessa area numerica
sulle due griglie. Soglia inclusiva |B_proxy| ≥ 100 G e limite |B_proxy| ≤ 10000 G, come P1. P1 non richiede 20 pixel per polarità: tale filtro è una selezione P2, che non entra qui
né sulla griglia HMI né su quella MDI. Una polarità con un solo pixel può quindi dare una misura P1
valida; quantità piccole non diventano automaticamente affidabili. Distinguere le perdite per soglia da quelle di dominio.

## 5. Misure e lettura

Registrare Φ positivo/negativo/totale, centroidi sferici, distanza, tilt orientato e differenza assiale
modulo 180°, D e D_bal. Per ogni confronto: differenze firmate e assolute di flussi totale/positivo/negativo e delle
latitudini dei centroidi positivo/negativo/medio; longitudini come differenze avvolte in [−180°,180°)
e loro valori assoluti, più spostamento sferico di ciascun centroide. Conservare separatamente il
cambiamento orientato del tilt e quello assiale in [−90°,90°). Rapporto del flusso totale solo con
denominatore non nullo; conservare anche le differenze dei dipoli senza normalizzarle
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

1. Revisione della regola QUALITY proposta sulle fonti native e del percorso di sorgente; risolvere o dichiarare che una
   misura resta descrittiva con prodotto di integrazione ignoto. La regola di qualità deve essere concreta.
2. Revisione di campione, maschere, dominio μ, convenzioni LOS, area e tetti; nessuna garanzia statistica.
3. Manifesto di selezione solo dopo congelamento; revisione del successivo adattatore FITS/WCS/tempi e
   del downloader, con test offline; il nucleo puro non li sostituisce.
4. Prova di riproduzione R0 sui record HMI che coincidono con P1; sugli altri confronto con l'identica
   funzione P1 a ciclo fissato, dichiarando che non esiste un risultato storico per quel record.
   Le prove ora superate riguardano soltanto mappe sintetiche, non questa porta reale. La porta usa
   P1 senza modifiche; ogni confronto con il kernel e i relativi rifiuti sono registrati a parte.
5. Verifica di provenienza, completezza e riconteggio delle differenze prima di interpretare le tabelle.

Fermo prima di congelamento, selezione, download e risposte reali. Il piano prospettico e la morfologia S
restano in pausa. Vedi [chiarimenti e fonti](MDI_SMARP_METADATA_CLARIFICATIONS.md) e
[consegna per il revisore](MDI_HMI_PREPARATION_REVIEW.md).

## 8. Specifica proposta per il controllo preliminare sui metadati

**Per la revisione, prima di acquisire.** La quantità da garantire è il minimo di μ sui centri di tutti i pixel appartenenti alla patch, per entrambi gli strumenti. La certificazione preliminare precede l'ordinamento delle coppie. La verifica sui pixel della bitmap effettiva rimane obbligatoria quando saranno disponibili le mappe.

### Quale informazione serve

Negli schemi salvati di entrambe le serie CEA, LAT_MIN, LAT_MAX, LON_MIN e LON_MAX sono estremi in coordinate Stonyhurst dei pixel della patch. LATDTMIN/MAX e LONDTMIN/MAX descrivono invece il transito. Il segmento bitmap è VARxVAR. Nel sorgente SMARP conservato, findPosition usa gli estremi del transito e arrotonda il numero di righe e colonne del ritaglio CEA. Queste evidenze da sole lasciano aperto se gli estremi istantanei comprendano ogni centro di pixel assegnato alla bitmap **dopo la rimappatura**. La verifica va documentata per entrambe le pipeline e le versioni interessate. Fonti locali: SCHEMA_mdi.smarp_cea_96m.json, SCHEMA_hmi.sharp_cea_720s.json e sharp__apps__smarp.c, funzioni findPosition e setKeys, nei percorsi del rapporto di revisione 2.

Usare uno dei seguenti certificati per ciascun record, registrando fonte, versione, precisione e unità.

1. **Ritaglio CEA.** Se sono documentate e disponibili come metadati le dimensioni effettive (nx, ny) del segmento bitmap di quel record e la WCS completa, calcolare μ su tutti i centri di pixel del ritaglio. Basta elaborare una riga alla volta. Il minimo su questo insieme è un limite inferiore valido per qualsiasi maschera interna. La forma effettiva deve provenire dal segmento per-record. CRPIX e NPIX da soli non la stabiliscono. Nessun uso dei quattro soli angoli o di un reticolo diradato.
2. **Rettangolo eliografico.** Ammesso se la provenienza documenta che i quattro estremi istantanei racchiudono tutti i centri di pixel della bitmap CEA per quella versione. Conservare l'intervallo di longitudine con la sua convenzione documentata, incluse eventuali discontinuità. Arrotondamenti e precisione di serializzazione vanno trattati verso l'esterno. Una fonte ambigua dà esito indeterminato. Se entrambi i certificati sono disponibili, registrarli separatamente e verificare eventuali incompatibilità per le stesse coordinate.

Per longitudine relativa all'osservatore ℓ e latitudine b, porre q = sin(b) sin(B0) + cos(b) cos(B0) cos(ℓ), poi μ = (q − r)/sqrt(1 + r² − 2rq), r = RSUN_REF/DSUN_OBS. Usare epoca e osservatore del record, B0 = CRLT_OBS e unità coerenti con 0 < r < 1. Per Carrington sottrarre CRLN_OBS una volta. Per Stonyhurst verificare a quale meridiano si riferiscano gli estremi rispetto a SOHO o SDO prima di trattarli come ℓ. μ cresce con q. Per un rettangolo in tali coordinate ricavare il minimo del coseno di ℓ sull'intero intervallo, poi minimizzare in b controllando i due estremi e tutti i punti stazionari interni. Trasformazioni non documentate, pixel con WCS non definita e precisione insufficiente vicino alla soglia lasciano il certificato indeterminato.

### Acquisizione proposta dopo revisione

- **Geometria.** Operazione JSOC di sola lettura rs_list su mdi.smarp_cea_96m e hmi.sharp_cea_720s. Riutilizzare le esatte finestre delle ricevute locali LIST_RECEIPTS.jsonl per i due profili overlap (6 MDI e 26 HMI, inclusi i margini HMI). Per ciascuna serie richiedere le due chiavi primarie, LAT_MIN/MAX, LON_MIN/MAX, DSUN_OBS e RSUN_REF. Unire offline alle WCS, effemeridi e versioni già salvate con la chiave completa. Se l'operazione documenta le dimensioni effettive della bitmap nel JSON, includerle nella stessa risposta. Prima dell'accesso identificare e provare su una risposta archiviata o fixture documentata il campo esatto che porta la forma. Un percorso del segmento o una dimensione VARxVAR lascia la forma ignota. Autorizzare l'acquisizione solo se per almeno una via è già documentato il significato necessario in entrambe le serie.
- **Budget proposto.** Per la geometria, 32 richieste di base, massimo 40 tentativi inclusi ripetizioni, 64 MiB di corpi JSON, 10 minuti cumulativi. Sono sottolimiti del confronto del §6 per tentativi e tempo. Registrare separatamente i byte dei metadati e quelli dei FITS. In caso di arresto conservare risposte originali, hash e finestre mancanti. Verificare stato del servizio, conteggi, unicità, valori mancanti, righe di bordo e identità delle chiavi contro le ricevute precedenti. Ogni discordanza va localizzata prima di certificare un record. Registrare versione e hash del lettore. L'inventario congelato mantiene il proprio registro.
- **Provenienza delle integrazioni, fase successiva distinta.** Per le sole coppie eventualmente selezionate, proporre una series_struct di mdi.lostarp_96m per documentare MDATA e la serie destinataria. Risolvere con rs_list il link MTARP del record CEA esatto, poi MDATA del record intermedio esatto. Leggere dalla destinazione verificata mdi.fd_M_96m_lev182 chiavi, identificativo del record, T_OBS, INTERVAL, DPC e QUALITY. Registrare identità di ogni estremo e risposta originale. Al massimo 1 + 3 × 12 = 37 richieste di base, 45 tentativi, 8 MiB JSON e 5 minuti, entro i totali di §6. Casi di link non esposto, destinazione diversa o record non univoco restano con prodotto ignoto e motivo. Non attribuire prodotti per vicinanza temporale. Prima di ogni fase riconciliare i consumi con i tetti complessivi e verificare il costo residuo del download. I sottolimiti sono massimi, non una garanzia di completamento.

### Rapporto prima della selezione

Per ognuno dei quattro strati ripartire gli archi dell'audit (877, 390, 880, 455 nell'ordine N centrale, S centrale, N laterale, S laterale) fra **certificati su entrambi**, **copertura geometrica insufficiente a certificare**, **metadati mancanti o non interpretabili**. Mantenere il dettaglio per strumento, causa e coppia distinta, contando ogni arco una volta. Una coppia con dati mancanti e un altro limite insufficiente figura nella terza categoria con entrambe le cause annotate. Un limite inferiore sotto 0,8 indica che il rettangolo può uscire dal dominio. Per affermare che la maschera lo violi servirebbe un pixel appartenente alla patch che lo dimostri. Riportare sia la quota di archi esclusi dalla preselezione conservativa sia quella con dati mancanti; la perdita fisica effettiva resta distinta. Riportare anche quante componenti G10 hanno almeno un arco certificato per strato e quante sono condivise fra strati, prima di formare qualsiasi lista di mappe.

Per la futura implementazione prevedere casi offline a soglia, un rettangolo che attraversa il meridiano, una parete con estremo interno, una bitmap interamente valida dentro un ritaglio che supera il limite e una coppia con un solo strumento documentato. Se nessuna via documentata garantisce l'impronta su entrambi gli strumenti, il rapporto indicherà il motivo. La scelta successiva da sottoporre a revisione sarà se mantenere la preselezione conservativa o verificare tutta la bitmap dopo l'estrazione, con perdite registrate e senza sostituzioni.

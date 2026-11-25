# Piano comune Codex–Claude — sorgente BL e quenching

**Priorita permanenti concordate dall'utente il 25 novembre 2026:**
1. **Confrontare mappa magnetica HMI e bipolo del proxy, facendoli evolvere nello stesso modello SFT.**
2. **Confrontare l'evoluzione simulata con osservazioni successive, separate dai dati usati per scegliere i parametri.**

Questi sono esattamente i punti 1 e 2 indicati dall'utente. Tenerli in primo
piano in HANDOFF e nelle riprese di entrambe le sessioni. Ogni nuova attivita
deve dichiarare a quale obiettivo serve e che cosa aggiunge. Questo e un
piano di lavoro, **non un protocollo congelato**; non autorizza nuovi download
ne anticipa scelte scientifiche ancora da fissare.

**Voci aggiunte dall'utente il 25 novembre 2026:** ranking bayesiano del
quenching su HMI (BQ) e del trasporto superficiale su HMI (BT). Sono due
confronti distinti, da specificare e congelare; non sono ancora eseguiti.
La preparazione metodologica puo procedere in parallelo, senza ritardare le
priorita 1 e 2. Il ranking BT usa la verifica osservativa del punto 2 e
richiede scelte congelate prima di accedere ai suoi esiti di verifica.

**Ulteriore voce approvata dall'utente:** active-region nests su HMI (N),
prima identificazione e controllo delle emersioni/ricomparse, poi contributo
alla sorgente BL e analisi bayesiana collegata a BQ/BT. Nessun catalogo di
nests o risultato bayesiano e gia disponibile. I due piloti SFT restano le
priorita operative; la specifica N si prepara senza duplicarne il lavoro.

**Decisione piu recente dell'utente (25 novembre, pomeriggio): il lavoro bayesiano passa PRIMA di tutto, i nests
DOPO tutto.** Ordine complessivo:
1. BQ su HMI (§3), che non dipende dai piloti SFT;
2. BQ multi-strumento su piu cicli (§3bis), e BQ-D sui termini da cui dipende il quenching (§3ter);
3. prerequisiti di BT: chiusura del pilota mappa–bipolo (A1 in revisione), ripetibilita (§7) e pilota
   dell'evoluzione osservata. Servono perche BT ne usa la macchina e la verifica;
4. BT (§4);
4bis. voce futura P (§4bis): dalla sorgente BL al campo polare, con un protocollo proprio;
5. **nests (§5) alla fine di tutto**: identificazione, poi effetto di gruppo in BQ/BT. Fino ad allora BQ e BT
   dichiarano non modellata la dipendenza fra membri di uno stesso nest.

Le priorita SFT 1 e 2 qui sopra restano nel piano, ma vengono dopo BQ e BQ-M.

## Due obiettivi del progetto di Paolo

- **Sorgente Babcock–Leighton:** interpretare e verificare il proxy misurato
  sulle regioni, il contributo al dipolo e il rapporto con l'evoluzione.
- **Quenching del tilt:** studiare la dipendenza dall'attivita con incertezze
  e controlli adeguati. HMI, MWO e MDI forniscono misure con limiti distinti.

Questo repository e il progetto BL. MWO/SINDy e un progetto distinto; S42
resta fuori da questo piano. Non trasferire automaticamente serie, risultati
o interpretazioni da quel progetto.

## 1. Priorita: controllo mappa–bipolo nel modello di trasporto

**Domanda:** quanto cambia il dipolo futuro se la regione osservata viene
sostituita dalla rappresentazione bipolare ricavata dagli ingredienti del
nostro proxy? Il confronto controlla l'approssimazione **dentro il modello**.
Non e da solo una validazione contro l'evoluzione del Sole.

### Passi e prodotti

- [x] Inventario del codice SFT riusabile: versione, licenza, geometria,
      trasporto, diffusione, ingresso delle mappe e requisiti di calcolo.
      Inventario dei FITS HMI gia locali e degli istanti disponibili, senza
      promettere che siano sufficienti per tutti i confronti.
- [ ] Specifica del piccolo pilota HMI prima di scegliere i casi: campione
      con regioni semplici e complesse, copertura di latitudine e dimensione;
      numerosita e regola di estrazione da fissare prima della lettura degli
      esiti. Nessuna esclusione perche il risultato e scomodo.
- [ ] Fissare le due rappresentazioni: mappa osservata e bipolo derivato da
      flusso, separazione, tilt, polarita e posizione P1. Definire anche
      estensione e forma delle polarita: quei soli scalari non determinano
      univocamente una mappa bipolare. Dichiarare bilanciamento di flusso,
      fondo, dominio e conversioni di unita; non equiparare S_BL (Mx cm)
      al dipolo assiale (G).
- [ ] Fissare inserimento e istante iniziale: flusso preesistente, parti di
      regione, HARP multiregione e ricomparse. Il catalogo al meridiano non
      e automaticamente un elenco di nuove emersioni da aggiungere al Sole.
- [ ] Congelare protocollo del pilota e criteri di lettura. Stessi parametri
      di trasporto, dominio e fondo per le due rappresentazioni; niente
      ottimizzazione per farle concordare nel risultato finale.
- [ ] Implementare e verificare su casi sintetici indipendenti: unita,
      segni, rimappatura con flusso controllato, conservazione/bilancio del
      flusso secondo il modello, dipolo iniziale e limiti analitici.
- [ ] Eseguire solo dopo revisione. Conservare prima della lettura,
      ricontare e scrivere il rapporto del pilota.

**Uscita minima per regione:** identificazione e morfologia, Phi, posizione,
separazione e tilt, dipolo iniziale delle due mappe, D(t) a tempi fissati,
differenza e incertezza/sensibilita ai trasporti. Per dipoli prossimi a zero
riportare differenze assolute; non rapporti instabili senza avvertenza.
Le prove istantanee gia fatte su D/D_bal e sul proxy compatto sono input
del disegno: non ripeterle come se fossero una nuova verifica evolutiva.

## 2. Priorita: controllo contro l'evoluzione osservata

**Domanda:** il modello inizializzato con le osservazioni riproduce
l'evoluzione successiva, su dati non usati per scegliere i suoi parametri?
Usa la preparazione del punto 1; i controlli di disponibilita dei dati possono
procedere insieme, prima di nuove misure.

### Passi e prodotti

- [ ] Definire osservabili e orizzonti: evoluzione locale nei primi giorni;
      eventuale controllo del dipolo globale su periodi piu lunghi come
      estensione distinta. Un buon accordo locale non valida il campo polare.
- [ ] Definire separazione tra dati di sviluppo/calibrazione e verifica,
      finestre temporali, campo di vista, dominio geometrico e cause di
      perdita. Non assimilare le osservazioni future che si vogliono usare
      come verifica e poi presentarle come previsione indipendente.
- [ ] Definire nuove emersioni durante il confronto e trattamento del flusso
      gia presente/ricomparso. Per il confronto globale occorre tener conto
      delle altre sorgenti; non attribuire direttamente tutta la variazione
      osservata del dipolo a una sola regione.
- [ ] Fissare prima errori osservativi, metriche, controlli di riferimento
      e criteri di lettura. Distinguere errore di rappresentazione della
      regione, ipotesi di trasporto e nuova emergenza non modellata.
- [ ] Protocollo, codice e riconteggio indipendente rivisti, poi esecuzione,
      conservazione, controllo e rapporto.

**Uscita minima:** curve simulate e osservate agli stessi istanti, copertura
ed esclusioni, errori con le unita fisiche appropriate e sensibilita ai
parametri. L'interpretazione dell'ampiezza della sorgente e condizionata a
questi controlli; una correlazione da sola non e una calibrazione.

### §7 attivo: ripetibilita e modello dell'incertezza HMI

**Decisione piu recente dell'utente (25 novembre): affrontare l'errore per
il confronto bayesiano; non rinviarlo dichiarandolo gia non stimato.**
La precedente proposta di rinvio e superata.

- [x] Audit indipendente Codex dei tempi T_OBS, header, geometria e
      sovrapposizione con il bacino del pilota: 296 coppie reali entro 2 h;
      riserva conservativa di 86 coppie/84 HARP con area geometrica sufficiente.
      [Rapporto](SFT_HMI_REPEATABILITY_METADATA_20261125.md).
- [ ] Completare e congelare la [specifica della misura](SFT_HMI_REPEATABILITY_PLAN_DRAFT.md),
      con campione, qualita, famiglie e separazione dal campione di verifica,
      osservabili e codice/riconteggio verificati prima dei pixel.
- [ ] Misurare e ricontare la distribuzione delle differenze ravvicinate;
      preservare gli output prima della lettura e documentare copertura,
      dipendenze e limiti di trasferimento al confronto a 1–4,5 giorni.
- [ ] Integrare l'informazione disponibile nella likelihood BT e, dove
      pertinente, BQ, distinguendo ripetibilita, errore strumentale, dispersione
      intrinseca, correlazione temporale e discrepanza del modello. Non
      identificarli automaticamente con un'unica sigma.

Codex ha svolto l'audit; Claude continua A1 e le correzioni del punto 1.
Il §7 e il congelamento del pilota osservativo si chiudono usando questa
consegna, senza duplicare l'audit. Nessuna scala di errore e ancora misurata.

## 3. BQ — ranking bayesiano del quenching su HMI

**Obiettivo servito:** quenching del tilt. **Domanda iniziale:** sugli stessi
record HMI di T3, quanto i dati distinguono un modello senza dipendenza del
coefficiente di Joy dall'attivita da un modello che la ammette?

**Ambito iniziale delimitato:** HMI da solo, T3 dentro il ciclo. T5, latitudine,
confronti fra cicli e fusione MDI/MWO non entrano automaticamente in questa
analisi. I risultati HMI sono gia noti: il nuovo protocollo dichiara il
carattere non cieco e conserva gli esiti precedenti.

- [ ] Scrivere una specifica separata: stesso campione, osservabile, pesi e
      selezione per tutti i modelli; differenze di popolazione o di bersaglio
      non si confondono con differenze di adeguatezza.
- [ ] Definire un modello con pendenza di attivita nulla e un modello con
      pendenza libera, ammettendo entrambi i segni; eventuale legge fisica di
      quenching come candidato ulteriore solo se fissata nella specifica.
      Conservare termini di Joy, ciclo ed emisfero coerenti con la domanda.
- [ ] Specificare likelihood, dipendenza temporale per CR, relazione della
      dispersione con le caratteristiche delle regioni, prior proprie e
      sensibilita alle prior. I generatori usati nelle validazioni precedenti
      non sono gia modelli bayesiani adattati ai dati.
- [ ] Fissare controlli sintetici, diagnostica del calcolo e controlli
      predittivi. Se la correlazione temporale non e descritta adeguatamente,
      una graduatoria relativa non certifica nessun candidato.
- [ ] Distinguere tre prodotti: distribuzione della pendenza e probabilita
      che sia negativa o oltre una soglia fisica fissata prima; confronto
      predittivo su blocchi temporali/famiglie; eventuali Bayes factor e
      probabilita dei modelli con prior di modello dichiarate. I pesi
      predittivi non sono probabilita che un modello sia fisicamente vero.
- [ ] Protocollo e codice rivisti prima della corsa; output conservati,
      riconteggio e rapporto con incertezza del ranking e possibilita di
      modelli non distinguibili. Nessun verdetto promesso e nessuna conversione
      degli intervalli storici in evidenza bayesiana senza nuova inferenza.

**Uscita:** rapporto bayesiano HMI separato, con posteriori, adeguatezza,
sensibilita e confronto relativo. Non modifica T3/T5 precedenti e non elimina
il limite informativo dei dati o i problemi strumentali delle altre serie.

**BIC aggiunto come controllo secondario:** [bozza BQ rev.2, §6bis](PROTOCOL_BQ_HMI_DRAFT.md).
Richiede ML con effetti casuali integrati, parametri contati esplicitamente e
una giustificazione della penalita per dati dipendenti. Cambiare n da regioni
a CR senza derivazione e solo sensibilita euristica, non un secondo BIC validato.
Nessun BIC reale e stato calcolato; confronto predittivo e sensibilita delle
evidenze restano separati. Nests ancora sospesi.

## 3ter. BQ-D — da quali termini dipende il quenching (dopo BQ-HMI; in parallelo con BQ-M dove servono più cicli)

**Aggiunta dell'utente il 25 novembre 2026:** il quenching è centrale quanto la sorgente, e serve capire da quali
termini dipende. Obiettivo servito: quenching del tilt, e quindi anche la sorgente BL (voce P).

**Domanda.** Fra un numero limitato di dipendenze fissate prima, quali descrivono e prevedono meglio la variazione del
coefficiente di Joy?
- **attività globale dentro il ciclo** (emisferica, come in T3 e BQ-HMI);
- **forza del ciclo** (coefficiente contro ampiezza, alla Jiao et al. 2021): richiede più cicli, quindi BQ-M;
- **flusso della regione** (quenching locale, come Q3);
- **latitudine e fase**: termine separato dal quenching di latitudine (T4), da non confondere;
- **attività locale** (regioni vicine, complessi; più avanti nests): solo quando i raggruppamenti saranno definiti.

**Regole.**
- I candidati sono pochi, elencati nella specifica prima di qualunque fit, ciascuno con la propria prior e la stessa
  base (k_(c,h), u, famiglie). Si confrontano anche le combinazioni previste, non tutte quelle possibili. Niente
  ricerca della combinazione migliore a posteriori.
- È non cieco rispetto a T3, Q1–Q3 e T4 già noti: va dichiarato.
- Si confrontano predizione a blocchi, evidenza dove affidabile e BIC secondario, come in BQ-HMI. Contano anche
  l'identificabilità reciproca dei termini (attività e fase sono correlate nel ciclo; il flusso della regione cresce
  con l'attività) e prove sintetiche con un termine vero alla volta, come nel pilota β contro v.
- Esito possibile: dati compatibili con più dipendenze, senza graduatoria netta.

**Uscita:** rapporto separato. Dove i dati lo permettono, i termini scelti entrano nel bilancio della voce P.

**Assegnazione proposta:** Codex scrive la specifica dopo il congelamento di BQ-HMI; Claude estende il codice BQ (i
regressori sono colonne in più della stessa struttura) e le prove sintetiche.

## 3bis. BQ-M — quenching bayesiano su piu strumenti e piu cicli

**Aggiunta approvata dall'utente il 25 novembre 2026.** Obiettivo servito: quenching del tilt.

**Domanda.** Combinando HMI (cicli 24–25), MWO 1974–2012 (cicli 20–24) e, se costruito, il catalogo MDI completo
(ciclo 23), quanto i dati distinguono un coefficiente di Joy che non dipende dall'attivita da uno che ne dipende?
Si considerano sia la dipendenza dentro il ciclo (T3) sia quella fra cicli (coefficiente contro ampiezza del ciclo,
come Jiao et al. 2021).

**Punto di partenza (non cieco).** Le stime separate sono gia note:
- HMI: −3,59° [−10,58; +3,41], «non deciso»;
- MWO R4: −4,93° [−10,21; +0,34], descrittivo;
- per MWO, la pendenza dello scarto MWO − luce bianca e −3,18° [−8,77; +2,40] (S2).

Il protocollo lo dichiara. Non si sommano ne si mediano gli intervalli gia pubblicati: serve una nuova inferenza
sui record.

**Come si combinano i dati: verosimiglianza congiunta, non somma dei cataloghi.**
- Parametri fisici **comuni**: coefficiente di Joy e sua dipendenza dall'attivita. Termini di ciclo, emisfero e
  fase restano coerenti con BQ-HMI.
- Parametri **per strumento**: scala e offset del tilt, errore di misura, eventuale dipendenza dell'errore dal
  flusso.
  - Per MWO, un termine di deriva con l'attivita, stimato attraverso il ponte con la luce bianca DPD sulle stesse
    regioni. Senza ponte non si separa dal quenching, e la specifica deve dichiararlo.
- **Stessa regione misurata da piu strumenti** (HMI–MWO 2010–2012, MDI–MWO 1996–2010, MDI–HMI 2010–2011): due misure
  dello stesso tilt latente, non due regioni. Si usano per stimare scale ed errori relativi e non contano due volte
  come informazione sul quenching.
- **Indice di attivita** con una definizione unica su tutto il periodo, fissata nella specifica. Unita e
  normalizzazione restano comuni a tutti gli strumenti.
- **Dipendenze**: correlazione temporale per CR, famiglie e ricomparse. I nests (§5) arrivano alla fine del
  piano; prima di allora la loro dipendenza e dichiarata non modellata. Le regioni non si trattano come repliche
  indipendenti.

**Passi.**
- [ ] Prerequisito: BQ-HMI specificato, congelato e funzionante sui sintetici. BQ-M ne estende il modello e non ne
      cambia le scelte a posteriori.
- [ ] Inventario dei record sovrapposti fra strumenti e del ponte DPD luce bianca (bozza T3-DPD esistente). Decidere
      se il catalogo MDI completo entra o resta fuori.
- [ ] Specifica separata:
  - likelihood congiunta, prior di scala/offset/deriva e loro sensibilita;
  - controlli sintetici con quenching noto e deriva strumentale nota, per verificare che i due si separino;
  - controlli predittivi per strumento e per ciclo;
  - confronto con e senza dipendenza fra cicli.
- [ ] Prodotti:
  - distribuzione della pendenza comune e probabilita che sia negativa;
  - contributo di ciascuno strumento (analisi lasciandone fuori uno);
  - confronto predittivo per blocchi di tempo o cicli.
- [ ] Riconteggio indipendente e rapporto separato. Nessun verdetto promesso: con circa cinque cicli la parte fra
      cicli resta debole, e se la deriva di MWO non si identifica il guadagno si riduce.

**Uscita:** rapporto bayesiano multi-strumento, distinto da BQ-HMI. Non modifica T3 HMI, T3 MWO o Q4 MDI.

**Assegnazione proposta:** Codex estende la specifica BQ; Claude prepara inventario delle sovrapposizioni e codice
dopo il congelamento, con revisione incrociata.

## 4. BT — ranking bayesiano del trasporto superficiale su HMI

**Obiettivo servito:** sorgente BL. **Domanda:** quali modelli descrivono meglio
le osservazioni successive delle stesse regioni, agli stessi istanti e sullo
stesso dominio? Candidati iniziali: persistenza, sola rotazione differenziale,
SFT completo. Varianti mappa/bipolo restano confronti di rappresentazione,
identificate separatamente dalle varianti del trasporto.

- [ ] Usare disponibilita e preparazione del pilota osservativo; conservare
      i suoi limiti di selezione (controllo scelto al massimo USFLUX) e la
      separazione sviluppo/verifica per componenti e famiglie.
- [ ] Scrivere un protocollo distinto o un emendamento esplicito prima della
      lettura della verifica. Definire gli osservabili effettivamente messi
      in likelihood e la loro dipendenza: non trattare come indipendenti
      pixel, dipolo, flussi e centroidi derivati dalla stessa mappa.
- [ ] Definire una distribuzione probabilistica di errori e discrepanze per
      tutti i candidati: le simulazioni deterministiche non bastano a
      calcolare un Bayes factor. La ripetibilita osservata comprende evoluzione
      reale e non e automaticamente rumore strumentale.
- [ ] Fissare prior e parametri del confronto senza adattarli alla verifica;
      i parametri fisici congelati dei piloti SFT restano invariati. Eventuali
      nuovi fit fisici richiedono una specifica esplicita separata.
- [ ] Verificare numerica e modello probabilistico sui sintetici, poi
      confronto predittivo sui casi esclusi dallo sviluppo, rispettando
      dipendenze temporali e spaziali. Definire prima il trattamento di
      valori mancanti, fallimenti, denominatori e casi non valutabili.
- [ ] Riportare punteggi predittivi e loro incertezza; eventuali Bayes factor
      solo con evidenze/prior ben definite e sensibilita conservate. Tutti i
      modelli possono risultare inadeguati; nessun vincitore obbligatorio.

**Uscita:** graduatoria relativa e incertezza sull'evoluzione locale a pochi
giorni. Non identifica da sola la causa dei residui, non misura soltanto nuova
emersione e non valida il contributo finale al campo polare globale.

## 4bis. P — dalla sorgente BL al campo polare (voce FUTURA, dopo BQ/BT; nessun lavoro ora)

**Aggiunta dall'utente il 25 novembre 2026 come voce futura.** Obiettivo servito: sorgente BL.

**Domanda.** La somma delle sorgenti BL misurate regione per regione (P1, eventualmente con il trasporto SFT dei
piloti) riproduce la variazione del campo polare osservato ciclo per ciclo ed emisfero per emisfero?

**Perché dopo BQ/BT.** Il passaggio dalla sorgente al dipolo richiede il modello di trasporto e il suo errore. Il
pilota mappa–bipolo, il pilota osservativo e BT servono prima.

**Regole di separazione fra progetti** (questo piano, «Due obiettivi»):
- la serie polare viene dal progetto distinto MWO-HMI-MDI (POLOIDAL_SERIES, scala HMI). Si usa come dato esterno con
  versione e SHA dichiarati, senza modificarla né ricalibrarla da qui;
- nessun trasferimento automatico di risultati o interpretazioni, in nessuna delle due direzioni. Nessun uso della
  serie toroidale SIGNED di quel progetto per scegliere o adattare qualcosa;
- non cieco: entrambe le serie sono note. Serve un protocollo proprio, rivisto e congelato prima del confronto, con
  le scelte (finestre per ciclo, normalizzazioni, trattamento delle regioni non misurate e del flusso fuori dalle
  HARP) fissate prima.

**Limiti già noti da dichiarare:**
- P1 misura vicino al meridiano centrale e copre solo le regioni HARP selezionate;
- l'ampiezza della sorgente non ha una calibrazione esterna (rapporto con BARD-HMI circa 1,67);
- HMI copre circa un ciclo e mezzo; un confronto su più cicli richiede MWO e MDI (cataloghi di BQ-M).

**Letteratura (25 novembre, livello abstract):** [nota](LITERATURE_BL_SOURCE_TO_POLAR_FIELD_20261125.md).
- La domanda non è nuova: SFT con regioni assimilate per HMI; SFT con tilt in luce bianca per i cicli 15–21; database
  MDI+HMI per i cicli 23–25; bipolo contro mappa con una sovrastima di circa il 24 % (Yeates 2020).
- Un nostro contributo avrebbe senso solo con un modello d'errore esplicito e un confronto pre-registrato, con i tilt
  magnetici MWO multi-ciclo e la serie polare omogenea con incertezze.
- Il pilota mappa–bipolo va presentato come replica ed estensione di Yeates (2020) e Wang, Jiang & Wang (2021).

**Assegnazione:** da decidere quando BQ/BT saranno chiusi.

## 5. N — active-region nests HMI, poi confronto bayesiano

**Obiettivi serviti:** sorgente BL e quenching. **Domanda:** quali emersioni
sono raggruppate nello spazio e nel tempo, quale contributo osservativo
producono e quanto la loro dipendenza cambia l'inferenza sul quenching?

Un nest non coincide con una HARP complessa, con una famiglia di candidate
ricomparse P1e o con una longitudine attiva assunta a priori. Occorre
separare nuova emersione, campo persistente e osservazioni ripetute: P1
misura vicino al meridiano, non identifica automaticamente l'emersione.

### Prima: identificazione e caratterizzazione

**Prima consegna Codex completata:** [inventario HMI](HMI_NESTS_FEASIBILITY.md),
197 CSV orari, 8296 HARP; nessun nest identificato. [Note Finley](HMI_NESTS_FINLEY_METHOD_NOTES.md)
e [bozza metodologica N/bayesiana](PROTOCOL_HMI_NESTS_BAYES_DRAFT.md) pronte
per la revisione incrociata. AIA e Solar Orbiter/EUI/PHI sono annotati come
estensione per morfologia e continuita, soprattutto sul lato nascosto;
non sono dati gia acquisiti o un prerequisito assoluto per candidati HMI.


- [x] Inventario mirato dei metadati HMI/NOAA e dei tempi locali: 1300060
      record canonici, 8296 HARP, nessuna keyword di emersione nei CSV.
      Sono una base per candidati, non una certificazione di nuove emersioni.
      Primo avvistamento e passaggio al meridiano non diventano date di
      emersione per convenzione implicita; selftest 7/7, input con SHA.
- [ ] Specifica autonoma, dichiarando risultati P1/P1e e morfologia gia noti:
      coordinate nel sistema rotante, intervalli spaziali e temporali,
      eventuale deriva longitudinale, gestione di famiglie, associazioni
      ambigue e buchi osservativi. Soglie fissate prima delle nuove letture;
      non sceglierle massimizzando quenching o contributo BL.
- [ ] Prove su sequenze sintetiche con nests noti e senza nesting; controllo
      delle associazioni casuali rispettando andamento del ciclo, latitudini
      e disponibilita. La sola vicinanza non certifica identita o causalita.
- [ ] Catalogo verificato dei nests candidati, appartenenza dei record e
      incertezza/ambiguita dell'associazione, durata e copertura. Distinguere
      eventi nuovi da record ripetuti e documentare le perdite.
- [ ] Quantificare tilt, flusso e proxy BL dei membri e del gruppo con
      popolazione esplicita. Non sommare come nuove sorgenti misure ripetute
      di flusso persistente; se le nuove emersioni non sono ricostruibili,
      limitarsi ai contributi osservativi definiti, senza bilancio cumulato
      di emersione o campo polare finale.

- [ ] Inventariare separatamente AIA 304 Å e Solar Orbiter/EUI/PHI per
      epoche di interesse, prima di una eventuale acquisizione. La vista
      terrestre AIA da sola non ricostruisce il lato nascosto; i candidati
      HMI restano utilizzabili con limiti osservativi dichiarati.

### Poi: analisi bayesiana delle dipendenze e dei contributi

- [ ] Integrare in BQ, con protocollo proprio, modelli senza/con dipendenza
      fra membri del nest: effetti gerarchici o correlazioni da definire,
      controllando contemporaneamente ciclo, emisfero, attivita e tempo.
      Verificare identificabilita e incertezza delle appartenenze, senza
      assumere ogni regione come replica indipendente.
- [ ] Confrontare modelli sugli stessi dati e sullo stesso bersaglio:
      adeguatezza, sensibilita alle prior, distribuzione della pendenza e
      prestazioni predittive; eventuali Bayes factor con prior proprie.
      Riportare anche modelli non distinguibili, senza promettere un verdetto.
- [ ] Per BT e per la calibrazione della ripetibilita, evitare membri dello
      stesso nest fra sviluppo/calibrazione e verifica, quando le etichette
      siano disponibili e affidabili. Definire il raggruppamento prima di
      leggere la verifica; nuove regole richiedono un nuovo protocollo o
      emendamento, mai una modifica silenziosa ai piloti congelati.
- [ ] Valutare il contributo dei nests nel trasporto solo con tempi e flussi
      nuovi definiti. Nel modello lineare a coefficienti assialsimmetrici
      il solo raggruppamento in longitudine non cambia il dipolo assiale:
      non attribuire al nesting un effetto fisico che il modello non contiene.

**Uscite:** catalogo di associazioni e rapporto descrittivo prima, rapporto
bayesiano poi. Le famiglie P1e e i controlli morfologici gia eseguiti sono
input, non un'analisi di nesting gia conclusa. L'audit §7 (riserva di 86
coppie) verifica famiglie note e sovrapposizioni, non l'indipendenza da nests
ancora da identificare; resta una disponibilita preliminare.

**Assegnazione:** Codex prepara inventario mirato e specifica metodologica N
insieme a BQ/BT; Claude continua A1 e i piloti SFT, poi revisione incrociata.
Nessuna acquisizione aggiuntiva o nuova misura avviata da questo piano.

## Divisione del lavoro senza duplicazioni

| Passo | Claude | Codex | Stato |
|---|---|---|---|
| Inventario SFT e dati HMI | Usa la consegna per preparare le specifiche; non duplicare l'inventario | Inventario assunto su richiesta dell'utente e completato: codice, versioni, licenze, dati e limiti | completato da Codex, 25 novembre; [consegna](BL_SFT_HMI_INVENTORY.md) |
| Specifica del pilota mappa–bipolo | Prepara emendamento numerico e corregge runner/riconteggio | Rivede chiusura dei rilievi aaf3d6f | protocollo congelato; corsa osservata bloccata, SFT_Q4_EVENING_REVIEW_20261125.md |
| Specifica osservativa | Usa audit Codex per recepire §7 e completare la specifica, senza duplicare il controllo | Audit T_OBS/header completato; specifica della misura e revisione del codice | §7 attivo su richiesta utente; nessun errore ancora stimato, nessun pilota avviato |
| Implementazione | Corregge moduli e prepara runner/rilettori | Riferimenti matematici indipendenti pronti, 20/20, generazione riproducibile | sviluppo sintetico, niente piloti |
| Risultati | Corsa autorizzata, conservazione, riconteggio e prima bozza del rapporto | Revisione di ricevute, risultati e formulazioni | dopo protocolli e codice |
| BQ e BT: specifiche bayesiane | Completa i due piloti SFT; non avvia fit bayesiani senza specifica condivisa | Prepara le proposte metodologiche BQ/BT e le prove indipendenti; consegna per revisione incrociata | aggiunti al piano, nessun calcolo bayesiano avviato |
| N: nests HMI e integrazione bayesiana | Prosegue A1/piloti; rivede la bozza N e le prove prima delle misure | Inventario concluso, note Finley e bozza N/bayesiana consegnate | solo metadati; nessun nest identificato e nessun ranking avviato |

Ogni passaggio riporta commit, prodotto concreto e prossimo passo. Claude
non deve riscrivere gli oracoli di Codex; Codex non deve implementare un
secondo runner al posto di quello assegnato a Claude. I risultati condivisi
sono nei file del repository, non soltanto nei messaggi di chat.

## Linee distinte da mantenere visibili

| Linea | Stato verificato il 25 novembre | Prossimo passo |
|---|---|---|
| MDI Q4: precisione prospettica T3 | Corsa dab5a33, ricevuta 8924285 21/21, audit 9/9; rapporto rivisto in aaf3d6f | Decisione sul catalogo MDI successiva e distinta; nessun rilancio Q4 |
| Catalogo MDI completo / nuovo T3 | Non avviato | Decisione successiva a Q4 e protocollo proprio; nessun verdetto anticipato |
| T5 su HMI | Descrittivo; sviluppo metodologico distinto | Eventuale progetto delimitato per incertezza temporale, solo con specifica e validazione nuove; non e automaticamente risolto dai punti 1–2 |
| T3 MWO | Analisi prevista conclusa come descrittiva | Nessuna sottrazione automatica di S2; eventuali controlli magnetici con MDI sotto specifica separata |
| Serie BL MDI/MWO/HMI | Nessuna unione diretta approvata | Confrontabilita di misura e flussi, popolazione e definizioni prima di qualunque raccordo |

Q4 e conclusa e il rapporto descrittivo e stato rivisto in aaf3d6f.
Le note storiche in HANDOFF che dicono «corsa non avviata» o «risultati non
letti» descrivono stati precedenti. Questo piano non modifica Q4, i suoi
output o le regole congelate.

## Ripresa di ogni sessione

1. Leggere questo piano e la sezione corrente di HANDOFF, poi verificare Git.
2. Dichiarare quale voce viene affrontata e controllare cosa sta facendo
   l'altro agente prima di modificare file condivisi.
3. Aggiornare stati e prossimo passo conservando il richiamo alle priorita
   1 e 2 sopra la cronologia. Non archiviarle sotto una nuova nota Q4/MDI.

**Inventario completato da Codex:** [consegna e fotografia dei dati](BL_SFT_HMI_INVENTORY.md).
**Prossimo lavoro:** Claude chiude i rilievi del punto 1 e il prerequisito
residuo del punto 2; Codex rivede le chiusure e prepara le specifiche BQ/BT e N.
Il ranking BT si definisce prima di leggere la verifica osservativa; BQ e
un'analisi separata, non cieca sui risultati HMI precedenti. Nessuna nuova
corsa o acquisizione e stata lanciata per aggiornare questa lista.

## Fonti di metodo gia consultate

- Yeates, *How good is the bipolar approximation of active regions for surface flux transport?*: https://arxiv.org/abs/2008.03203
- Gottschling e colleghi, *Testing solar surface flux transport models in the first days after active region emergence*: https://arxiv.org/abs/2111.01896
- Yeates e colleghi, *Surface Flux Transport on the Sun*: https://arxiv.org/abs/2303.01209

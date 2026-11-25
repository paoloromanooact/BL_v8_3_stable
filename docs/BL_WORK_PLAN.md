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

## Divisione del lavoro senza duplicazioni

| Passo | Claude | Codex | Stato |
|---|---|---|---|
| Inventario SFT e dati HMI | Usa la consegna per preparare le specifiche; non duplicare l'inventario | Inventario assunto su richiesta dell'utente e completato: codice, versioni, licenze, dati e limiti | completato da Codex, 25 novembre; [consegna](BL_SFT_HMI_INVENTORY.md) |
| Specifica del pilota mappa–bipolo | Prepara emendamento numerico e corregge runner/riconteggio | Rivede chiusura dei rilievi aaf3d6f | protocollo congelato; corsa osservata bloccata, SFT_Q4_EVENING_REVIEW_20261125.md |
| Specifica osservativa | Chiude impegno del §7 sulla ripetibilita, poi congela; codice preparatorio separato | Geometria rev.4 confermata; revisione del codice prima dei dati | non congelata; nessun pilota osservato avviato |
| Implementazione | Corregge moduli e prepara runner/rilettori | Riferimenti matematici indipendenti pronti, 20/20, generazione riproducibile | sviluppo sintetico, niente piloti |
| Risultati | Corsa autorizzata, conservazione, riconteggio e prima bozza del rapporto | Revisione di ricevute, risultati e formulazioni | dopo protocolli e codice |
| BQ e BT: specifiche bayesiane | Completa i due piloti SFT; non avvia fit bayesiani senza specifica condivisa | Prepara le proposte metodologiche BQ/BT e le prove indipendenti; consegna per revisione incrociata | aggiunti al piano, nessun calcolo bayesiano avviato |

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
residuo del punto 2; Codex rivede le chiusure e prepara le specifiche BQ/BT.
Il ranking BT si definisce prima di leggere la verifica osservativa; BQ e
un'analisi separata, non cieca sui risultati HMI precedenti. Nessuna nuova
corsa o acquisizione e stata lanciata per aggiornare questa lista.

## Fonti di metodo gia consultate

- Yeates, *How good is the bipolar approximation of active regions for surface flux transport?*: https://arxiv.org/abs/2008.03203
- Gottschling e colleghi, *Testing solar surface flux transport models in the first days after active region emergence*: https://arxiv.org/abs/2111.01896
- Yeates e colleghi, *Surface Flux Transport on the Sun*: https://arxiv.org/abs/2303.01209

# Piano comune Codex–Claude — sorgente BL e quenching

**Priorita permanenti concordate dall'utente il 25 novembre 2026:**
1. **Confrontare mappa magnetica HMI e bipolo del proxy, facendoli evolvere nello stesso modello SFT.**
2. **Confrontare l'evoluzione simulata con osservazioni successive, separate dai dati usati per scegliere i parametri.**

Questi sono esattamente i punti 1 e 2 indicati dall'utente. Tenerli in primo
piano in HANDOFF e nelle riprese di entrambe le sessioni. Ogni nuova attivita
deve dichiarare a quale obiettivo serve e che cosa aggiunge. Questo e un
piano di lavoro, **non un protocollo congelato**; non autorizza nuovi download
ne anticipa scelte scientifiche ancora da fissare.

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

## Divisione del lavoro senza duplicazioni

| Passo | Claude | Codex | Stato |
|---|---|---|---|
| Inventario SFT e dati HMI | Usa la consegna per preparare le specifiche; non duplicare l'inventario | Inventario assunto su richiesta dell'utente e completato: codice, versioni, licenze, dati e limiti | completato da Codex, 25 novembre; [consegna](BL_SFT_HMI_INVENTORY.md) |
| Specifica del pilota mappa–bipolo | Bozza del protocollo e proposta operativa del campione | Revisione di confronti, unita, bilancio, doppio conteggio, criteri e popolazione | bozza rev. 1 (`docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_DRAFT.md`), in revisione; parti marcate [dopo l'inventario] |
| Specifica osservativa | Bozza su orizzonti, dati successivi e separazione sviluppo/verifica | Verifica indipendente dei confronti e dell'assenza di uso dei dati futuri | da iniziare |
| Implementazione | Runner, adattatori, prove sintetiche e documentazione | Oracoli sintetici, controesempi, revisione e controlli numerici separati | dopo specifiche |
| Risultati | Corsa autorizzata, conservazione, riconteggio e prima bozza del rapporto | Revisione di ricevute, risultati e formulazioni | dopo protocolli e codice |

Ogni passaggio riporta commit, prodotto concreto e prossimo passo. Claude
non deve riscrivere gli oracoli di Codex; Codex non deve implementare un
secondo runner al posto di quello assegnato a Claude. I risultati condivisi
sono nei file del repository, non soltanto nei messaggi di chat.

## Linee distinte da mantenere visibili

| Linea | Stato verificato il 25 novembre | Prossimo passo |
|---|---|---|
| MDI Q4: precisione prospettica T3 | Il codice e approvato in 1c25c2e; **una corsa e gia conservata in dab5a33**. Nessun suo risultato letto per aggiornare questo piano | Revisione del riconteggio di Claude, controllo indipendente, ricevuta, lettura e rapporto; non rilanciare |
| Catalogo MDI completo / nuovo T3 | Non avviato | Decisione successiva a Q4 e protocollo proprio; nessun verdetto anticipato |
| T5 su HMI | Descrittivo; sviluppo metodologico distinto | Eventuale progetto delimitato per incertezza temporale, solo con specifica e validazione nuove; non e automaticamente risolto dai punti 1–2 |
| T3 MWO | Analisi prevista conclusa come descrittiva | Nessuna sottrazione automatica di S2; eventuali controlli magnetici con MDI sotto specifica separata |
| Serie BL MDI/MWO/HMI | Nessuna unione diretta approvata | Confrontabilita di misura e flussi, popolazione e definizioni prima di qualunque raccordo |

Il fatto che Q4 sia gia stata eseguita viene da Git (dab5a33), non dalla
lettura di RAW, SUMMARY o CRITERIA. Le note storiche in HANDOFF che dicono
«corsa non avviata» descrivono uno stato precedente. Questo piano non
modifica Q4, i suoi output o le regole congelate.

## Ripresa di ogni sessione

1. Leggere questo piano e la sezione corrente di HANDOFF, poi verificare Git.
2. Dichiarare quale voce viene affrontata e controllare cosa sta facendo
   l'altro agente prima di modificare file condivisi.
3. Aggiornare stati e prossimo passo conservando il richiamo alle priorita
   1 e 2 sopra la cronologia. Non archiviarle sotto una nuova nota Q4/MDI.

**Inventario completato da Codex:** [consegna e fotografia dei dati](BL_SFT_HMI_INVENTORY.md).
**Prossimo lavoro:** Claude prepara le due specifiche collegate per i punti
1–2; Codex le rivede. Nessuna nuova simulazione o acquisizione lanciata.

## Fonti di metodo gia consultate

- Yeates, *How good is the bipolar approximation of active regions for surface flux transport?*: https://arxiv.org/abs/2008.03203
- Gottschling e colleghi, *Testing solar surface flux transport models in the first days after active region emergence*: https://arxiv.org/abs/2111.01896
- Yeates e colleghi, *Surface Flux Transport on the Sun*: https://arxiv.org/abs/2303.01209

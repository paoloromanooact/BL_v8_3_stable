# Piano di lavoro BL–HMI

**Ultimo aggiornamento:** 27 novembre 2026, sera. Prima versione, concordata fra utente, Codex e Claude.

File vivo: si aggiorna sempre questo file, con una riga qui sopra (data e motivo); le versioni precedenti restano nella
storia di git. Il piano generale resta `docs/BL_WORK_PLAN.md`. Unica modifica rispetto al testo condiviso: la correzione degli SHA del manifesto del
weekend, che era «da fare», risulta fatta (commit f9205ff, cartella `preflight_lf`).

## Obiettivo scientifico generale

Capire quanta parte del campo polare osservato è spiegata dalla sorgente Babcock–Leighton misurata nelle regioni
attive e con quale incertezza.

Il progetto ha due linee scientifiche:

1. Quenching del tilt. Stabilire se l'attività solare riduce il tilt medio delle regioni bipolari, quanto è grande
   l'effetto, da quali variabili dipende e quale forma lo descrive.
2. Sorgente e trasporto superficiale. Verificare se il bipolo del catalogo rappresenta adeguatamente la mappa
   magnetica e se il modello di trasporto riproduce l'evoluzione osservata e il contributo al campo polare.

La fase attuale usa solo HMI. Le analisi con più strumenti e più cicli vengono dopo. Piano generale:
`docs/BL_WORK_PLAN.md`.

## 1. BQ-HMI — Il primo confronto bayesiano

Obiettivo. Stimare quanto potrebbe essere forte il quenching e capire se i dati HMI permettono di distinguerlo da una
variazione temporale della legge di Joy, cioè della relazione fra tilt e latitudine.

Il modello M0 descrive il tilt senza il termine di quenching. MQ aggiunge il termine β aᵢ sinλᵢ, dove aᵢ rappresenta
l'attività. Un β negativo indica una pendenza di Joy più debole quando l'attività aumenta. La sensibilità alla
variazione temporale di Joy va provata in entrambi i modelli e fa parte di BQ-HMI.

### Già ottenuto

- L1 gaussiano: riferimento analitico e riconteggio indipendente verificati sui sintetici.
- L2/L3 robusti: sviluppato il calcolo predittivo sequenziale SMC. Sul blocco da 395 record, la vecchia quadratura L2
  spostava il log-punteggio di circa 0,26. La quadratura in log λ è ora nel codice. In L3, la gestione delle
  preimmagini e il controllo della coda usano la stessa routine anche durante il ringiovanimento.
- Media sugli iperparametri ψ: il driver salva i contributi per catena e iterazione. Il verificatore ricalcola
  log-punteggio, ESS dei pesi ed errore Monte Carlo (MCSE). La sonda da 12 estrazioni sul blocco grande ha misurato
  circa 71 secondi per valutazione SMC in L2 e 101 in L3. L'ESS dei pesi era 5,85 su 12 in L2 e 4,25 su 12 in L3. I
  punteggi sono rimasti non stabiliti.
- Bridge e Savage–Dickey: controllo numerico del Bayes factor per L1. Su 30 repliche indipendenti, la dispersione
  osservata della differenza, 0,062–0,064, è risultata circa 15–20% sopra il MCSE previsto, 0,054. 28 repliche su 30
  erano entro due errori standard. Prima di adottare un margine fisso va verificato se lo scarto si ripete su altri casi
  o più repliche.
- Risultato osservativo precedente: l'analisi T3 del quenching resta inconclusiva. La stima era negativa e l'intervallo
  comprendeva zero. Bozza BQ-HMI: `docs/PROTOCOL_BQ_HMI_DRAFT.md`.

### Da fare adesso

1. Finire il pilota comparativo. È partito alle 17:02 sul blocco 8, da 395 record, con risposta sintetica G1. Esegue
   M0 e MQ in L2 e L3, una corsa alla volta. Il training di L2–M0 ha già superato i controlli.
2. Decidere separatamente per L2 e L3. Entrambi i modelli devono superare la diagnostica del training e ottenere ESS
   dei pesi ≥ 100 e MCSE del log-punteggio ≤ 0,1. Il checkpoint a 40 estrazioni serve a leggere costo e concentrazione
   dei pesi. I checkpoint decisionali sono 120, 160 e 200, in un unico lancio. Fit e contributi già calcolati vengono
   riusati all'interno della corsa.
3. Cambiare strategia se il pilota fallisce. Se il problema è il training, si rivedono catene e riscaldamento. Se
   dominano pochi pesi, si studia come migliorare la media sulle ψ. Se domina il rumore SMC, si valuta il budget di
   particelle o repliche. L3 avrà una verifica propria se resta sotto soglia a 200 estrazioni. Qualunque correzione si
   prova sullo stesso blocco e sulla stessa risposta prima di estenderla.

### Programma del weekend, subordinato al pilota

- La finestra concordata è venerdì alle 19:00 → lunedì alle 09:00, pari a 62 ore. Il pilota preparatorio è partito
  prima. Dalle 06:00 di lunedì si smette di avviare nuovi fit.
- L'estensione attende una decisione esplicita. Per i soli rami promossi, si parte dai blocchi 5 e 6, con G0 senza
  quenching e G1 con quenching. In ciascun confronto M0 e MQ usano la stessa risposta e le stesse maschere.
- Il blocco 3 entra se si può completare per intero con il tetto di 200 estrazioni. Altrimenti si usa il blocco 4 come
  riserva. La scelta dipende dai tempi e dallo stato delle corse, senza guardare quale modello vince.
- Con meno di otto blocchi comuni sufficientemente precisi, consegniamo i risultati per blocco e lasciamo aperta la
  classifica complessiva.
- Manifesto: **fatto** (f9205ff). I CSV sono rigenerati in LF in `reviews/BQ_WEEKEND_20261127/preflight_lf`, con lo
  stesso contenuto. Gli SHA sono verificati da un clone nuovo. Il manifesto del pilota attivo
  (`reviews/BQ_WEEKEND_20261127/preflight`, CRLF) è conservato intatto. L'estensione
  (`reviews/BQ_WEEKEND_20261127/launch_extension.sh`) usa `preflight_lf` ed è pronta ma non avviata.

### Altri punti BQ ancora aperti

- Particelle e repliche. Sganciare il confronto SMC dalla coda S-ID sospesa. Lo script preparato confronta 1×1.000,
  1×2.000 e 2×1.000 particelle. Per decidere se 500 bastano serve una prova dedicata sullo stesso blocco, con la stessa
  risposta e lo stesso ψ. Si valuta dopo il pilota, in isolamento.
- S-ID e identificabilità. Conservare le tre catene già salvate e decidere se chiudere i 13 processi sospesi. Il
  prossimo pilota sarà separato, con 1.500 estrazioni per catena come base e un confronto fra 300 passi di riscaldamento
  e un riscaldamento più lungo. Riprogrammare l'esportazione per il riconteggio su insiemi completi di catene. Lo
  studio esteso e le repliche L3 restano da dimensionare.
- Ordine delle estrazioni di ψ. Prima dei fit osservativi, verificare se conviene distribuire le estrazioni lungo ogni
  catena anziché usare i primi prefissi dopo il riscaldamento. Fissare la regola in anticipo, salvare gli indici e
  verificarne l'effetto sul MCSE.
- Registro dei semi. Tenere nel repository un registro unico di intervallo, uso e script, con controllo delle
  collisioni e indicazione dei riusi intenzionali nei confronti appaiati.
- Analisi HMI. Congelare protocollo, prior, diagnostica, prodotti e regole di confronto prima dei fit osservativi. Il
  risultato scientifico dovrà riportare stima e intervallo credibile di β, probabilità che sia negativo, evidenza
  relativa dei modelli e capacità predittiva sui periodi lasciati fuori.

## 2. BQ-D — Termini e forme del quenching

Obiettivo. Dopo BQ-HMI, capire da quali variabili dipende il quenching e quale forma descrive meglio l'effetto. Anche
questa fase è bayesiana.

- Fissare prima dei nuovi fit pochi candidati, per esempio attività emisferica e flusso della singola regione.
- Confrontare poche forme motivate, per esempio lineare e saturante, con criteri comuni di valutazione.
- Riportare se i dati distinguono i candidati e quanto la conclusione dipende dalle ipotesi.
- La dipendenza dalla forza del ciclo richiede più cicli e va alla fase multi-strumento. L'attività delle regioni vicine
  attende una classificazione dei raggruppamenti. Piano BQ-D: in `docs/BL_WORK_PLAN.md`.

## 3. P1, C, A1 e SFT — Sorgente e verifica osservativa

Obiettivo. Verificare se il bipolo del catalogo riproduce il comportamento della mappa magnetica completa quando
entrambi vengono fatti evolvere con lo stesso modello SFT. Poi confrontare l'evoluzione simulata con mappe HMI
successive.

| Voce | Risultato o prossimo passo |
|---|---|
| P1 — Catalogo HMI | Costruito su 14.195 record e 7.133 HARP, da maggio 2010 a settembre 2026. Il confronto con BARD sostiene le convenzioni geometriche nel campione verificato. La validazione dell'ampiezza assoluta della sorgente resta aperta. |
| C — Ripetibilità | Concluso. Misura su 82 coppie reali a 1–2 ore, riconteggio indipendente 19/19. Scarto centrato del dipolo relativo 0,0088. Dispersione del tilt 3,13° sulla mappa grezza e 1,26° sui pixel P1. È un riferimento empirico sulle differenze a breve distanza. |
| C — Confronto rinviato | Dopo il congelamento del campione del pilota osservativo, confrontare dai soli metadati la copertura dei due bacini per flusso, latitudine e distanza dal meridiano. |
| A1 — Verifica numerica | Congelato e pushato. Testo 9fa6b93, ricevuta 00355af. Resta la decisione separata sull'avvio della corsa mappa–bipolo. |
| SFT — Evoluzione osservata | Verificare la disponibilità delle coppie con gli orari effettivi negli header, fissare la separazione fra sviluppo e verifica, quindi confrontare le simulazioni con mappe successive a 1–4,5 giorni. Conservare e ricontare i prodotti prima di interpretare la verifica. |

Rapporto C: `docs/SFT_HMI_REPEATABILITY_C_REPORT_20261127.md`. Bozza del pilota osservativo:
`docs/PROTOCOL_SFT_OBSERVED_EVOLUTION_DRAFT.md`.

## 4. BT — Confronto bayesiano del trasporto

Obiettivo. Stabilire se SFT prevede l'evoluzione osservata meglio di riferimenti semplici, come persistenza e sola
rotazione differenziale.

Dopo i piloti SFT, fissare l'osservabile principale, oggi proposto come dipolo assiale locale, e definire il modello
d'errore. Vanno tenuti distinti errore della mappa iniziale, errore della mappa successiva, correlazione fra le due
mappe e discrepanza fra simulazione e Sole. C dà una scala a 1–2 ore. Il trasferimento a intervalli di giorni va
specificato e verificato usando lo sviluppo, prima del confronto sulle osservazioni riservate alla verifica. Bozza BT:
`docs/PROTOCOL_BT_HMI_DRAFT.md`.

## 5. P — Bilancio finale del campo polare

Obiettivo. Combinare sorgente, quenching e trasporto per verificare quanto campo polare HMI viene riprodotto, con quale
incertezza e quanto cambia la ricostruzione includendo il quenching. È il traguardo scientifico del progetto e richiede
un protocollo proprio dopo le verifiche precedenti.

## Decisioni già fissate e lavori rinviati

- CPU e memoria. Codex e Claude scelgono il parallelismo in base al lavoro completato all'ora. Per SMC L2/L3 si fa una
  corsa alla volta, con un thread numerico. Per slice S-ID la configurazione misurata migliore è 12 processi a un thread,
  quando gira da sola sulla stessa macchina. Regola condivisa: `docs/HANDOFF.md`.
- T5-D2. La lettura descrittiva è chiusa. Un eventuale nuovo metodo per T5 resta futuro e richiede protocollo e
  validazione propri.
- Fase futura. BQ multi-strumento con MWO/MDI e più cicli è rinviato. I nests restano sospesi. SINDy e S42 sono separati
  dalla coda BL–HMI.

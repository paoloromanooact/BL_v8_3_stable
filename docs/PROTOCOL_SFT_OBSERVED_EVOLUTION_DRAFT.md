# Confronto SFT con l'evoluzione osservata — BOZZA di protocollo (revisione 1, non congelata)

Stato: **bozza per la revisione di Codex**, 25 novembre 2026 (Claude). Non autorizza simulazioni né download.
Piano di riferimento: `docs/BL_WORK_PLAN.md`, priorità 2; lista dell'utente, punto 3. Collegato alla bozza del punto 2
(`docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_DRAFT.md`, revisione 2) e all'inventario di Codex (`docs/BL_SFT_HMI_INVENTORY.md`).

## 0. Obiettivo servito e che cosa aggiunge

- **Obiettivo 1 (sorgente BL).** Il proxy misura la regione in un solo istante, vicino al meridiano centrale. Il pilota
  chiede se un modello SFT inizializzato con quella mappa **riproduce le grandezze osservate pochi giorni dopo**, su
  dati non usati per sceglierne i parametri. Chiede anche quanto della differenza viene dal trasporto e quanto da flusso
  nuovo o scomparso, che il modello non contiene.
- **Che cosa aggiunge al punto 2.** Il punto 2 confronta due rappresentazioni nello stesso modello. Qui il termine di
  confronto è il Sole osservato.
- **Limite.** Pochi giorni e una sola regione per volta: l'accordo locale **non valida** il trasporto sui tempi del
  dipolo globale (anni) né il campo polare. Il controllo globale è un'estensione distinta (§10), non parte del pilota.

## 1. Informazioni già note (non cieco)

- **Dati locali (inventario).** P1 ha per ogni HARP un record primario (|LON_FWT| minimo, ≤ 30°) e uno di controllo.
  In 2836 HARP il controllo è successivo al primario: 2012 ad almeno un giorno, 1572 ad almeno due, 1153 ad almeno
  tre, solo 5 ad almeno cinque. Insieme alle patch BARD, 7173 HARP hanno da 1 a 4 record: non sono sequenze regolari.
- **Selezione del controllo:** è il record con USFLUX massimo entro |LON_FWT| ≤ 60°. **Non è un istante casuale:**
  favorisce le fasi di crescita del flusso e gli istanti di massimo. Questa selezione condiziona tutto il confronto e
  va riportata. Non si corregge scegliendo altri record dopo aver visto gli esiti.
- **Già studiato:** l'evoluzione primario → controllo di tilt, S_BL, segno di D* e hale_sign è descritta in P1d §3
  (`P1_CHECKS.csv`). Le grandezze del controllo sono quindi già state viste in forma aggregata. Il pilota non è cieco e
  lo dichiara.
- **Scale attese del modello.** In tre giorni la diffusione sposta il flusso di circa √(4ηt) ≈ 2° (η = 500 km²/s) e il
  flusso meridiano di circa 0,3° (15 m/s); la rotazione differenziale stira la regione in longitudine. Nei primi giorni
  le variazioni osservate possono essere dominate da emergenza e decadimento, che l'SFT non contiene (Gottschling et al.
  2021, arXiv:2111.01896, studiano proprio questa fase). Per questo il confronto richiede riferimenti espliciti (§6).

## 2. Domanda

Per una regione con mappa iniziale al tempo t₀ (record primario) e osservazione successiva a t₁ = t₀ + Δt (record di
controllo), con 1 ≤ Δt ≤ 4,5 giorni:
- l'SFT inizializzato a t₀ prevede a t₁ le grandezze osservate a t₁ meglio dei riferimenti senza trasporto (§6)?
- la differenza fra previsione e osservazione è spiegata dal cambiamento del flusso totale (nuova emergenza,
  decadimento), che il modello non rappresenta?

## 3. Osservabili

Tutte misurate con il metodo P1 (`measure.py`: maschera bitmap ≥ 33, |Br| ≥ 100 G, WCS completa, T_OBS), sia sulla
mappa osservata a t₁ sia sulla mappa simulata a t₁:
- **dipolo:** D e D_bal (G);
- **flusso:** Φ₊, Φ₋, Φ (Mx);
- **geometria:** latitudini e longitudini di Carrington dei centroidi delle polarità, latitudine media, separazione,
  tilt (convenzione P1);
- **campo, solo come diagnostica:** correlazione pixel per pixel di Br fra simulato e osservato sulla regione comune
  delle due maschere, dopo la rimappatura su una griglia comune.

La grandezza principale per l'obiettivo 1 è **D**; le altre servono a separare le cause.

**Maschera a t₁:** la mappa osservata si misura con la sua maschera a t₁, come farebbe P1. La simulata si misura sulla
maschera di t₀ trasportata (pixel della regione iniziale evoluti, sopra soglia). Le due scelte rispondono a domande
diverse; la differenza di maschera si riporta (frazione di flusso osservato a t₁ fuori dalla maschera trasportata) e
indica nuovo flusso o espansione.

## 4. Popolazione, campione e separazione sviluppo/verifica

- **Bacino:** HARP con record primario e di controllo distinti, entrambi `valid_bl` = 1, controllo successivo al
  primario, 1 ≤ T_OBS(controllo) − T_OBS(primario) ≤ 4,5 giorni, stessa HARP (nessun cambio di numero) e
  `family_rank` = 0.
- **Strati, da metadati:** Δt (1–2, 2–3, 3–4,5 giorni); andamento di USFLUX fra i due record dai metadati orari
  (crescita > 20 %, stabile entro ±20 %, calo > 20 %), come indicatore di emergenza o decadimento, non come esclusione;
  complessità (`NOAA_ARS`, come nel punto 2).
- **Numerosità proposta:** 6 per cella (3 × 3 × 2 = 18 celle), circa 108 regioni, estratte con seme nuovo dalla zona
  verificata disgiunta. Le celle povere si prendono intere e si dichiarano.
- **Separazione sviluppo/verifica, fissata prima di qualsiasi calcolo.** Assegnazione per HARP con una seconda
  permutazione dello stesso seme: un terzo dello sviluppo, due terzi della verifica, stratificata per cella.
  - **Sviluppo:** controlli d'implementazione (rimappatura, maschera trasportata, griglia, condizioni al bordo,
    tolleranze numeriche) e scelta fra le alternative dichiarate al §5, se la revisione ne lascia di aperte.
    Nessuna calibrazione di η o del flusso meridiano: i parametri vengono dalla letteratura (§5).
  - **Verifica:** letta solo dopo il congelamento delle scelte prese sullo sviluppo, con una corsa unica.
  - Le osservazioni a t₁ della verifica non si usano in nessun passo di sviluppo, nemmeno per scegliere la maschera,
    la soglia o i riferimenti.

## 5. Modello

- **Trasporto 2D locale**, perché le osservabili del §3 sono locali: una calotta sferica di ±15° in latitudine e
  longitudine attorno al centroide della regione, griglia regolare in longitudine e sin λ, con rotazione differenziale
  (Snodgrass & Ulrich 1990, come P1d/P1e), flusso meridiano e diffusione. Con Δt ≤ 4,5 giorni il bordo è lontano
  rispetto agli spostamenti attesi (§1); la prova sintetica lo verifica (flusso uscito dal dominio < 10⁻⁶ del totale).
- **Codice:** implementazione propria (volumi finiti, conservativa). HipFT (Apache-2.0, commit 5d41dea0) può servire da
  oracolo esterno su casi sintetici, eseguito da Codex fuori dal repository, se la compilazione risulta possibile.
- **Parametri:** gli stessi del punto 2, trascritti dallo stesso modello pubblicato; due combinazioni di sensibilità
  uguali a quelle del punto 2. Nessun parametro si stima sui dati di questo pilota.
- **Condizione iniziale:** mappa a t₀ con maschera e bilanciamento del punto 2 (riscalatura delle polarità).
  Sensibilità: mappa senza bilanciamento, perché in pochi giorni il monopolo locale non pesa sul trasporto.
- **Variante bipolo:** lo stesso trasporto applicato al bipolo del punto 2. Collega i due pilota: quanto la
  rappresentazione bipolare peggiora la previsione rispetto alla mappa.

## 6. Riferimenti senza trasporto (obbligatori)

La previsione SFT si giudica solo rispetto a riferimenti semplici, sugli stessi casi:
- **persistenza:** la mappa di t₀ invariata, cioè le grandezze di t₀ usate come previsione di t₁;
- **sola rotazione differenziale:** la mappa di t₀ spostata in longitudine secondo ω(λ), senza flusso meridiano né
  diffusione (cambia posizioni e tilt; non cambia D).

Poiché in pochi giorni l'SFT cambia poco D, ci si aspetta che D simulato sia vicino alla persistenza. Il confronto più
informativo riguarda quindi posizioni, tilt e forma. Questa aspettativa è dichiarata ora, prima dei dati.

## 7. Errori osservativi

- Non c'è una stima locale dell'errore di misura di D a t₁: le HARP hanno 1–4 record. Proposta: **ripetibilità a breve
  intervallo** da un sottoinsieme separato di HARP con due record a meno di 2 ore, se i metadati e i file disponibili lo
  permettono (da verificare, senza nuovi download nella revisione 1). Altrimenti l'errore si dichiara non stimato e il
  confronto resta relativo ai riferimenti del §6.
- Br di HMI aumenta il rumore lontano dal centro del disco; il controllo arriva fino a |LON_FWT| ≤ 60°. La distanza dal
  meridiano a t₁ si riporta come covariata e non come esclusione.

## 8. Metriche e lettura

**Per regione e per grandezza X:** errore della previsione e_SFT = X_obs(t₁) − X_SFT(t₁), errori dei riferimenti e_pers
ed e_rot; rapporti |e_SFT|/|e_pers| per le grandezze in cui la persistenza non è identica alla previsione; ΔΦ/Φ
osservato; frazione di flusso osservato fuori dalla maschera trasportata.

**Per strato e totale (verifica):** mediane e quantili 10–90 %; frazione di regioni con |e_SFT| < |e_pers|. Le stesse
grandezze vanno riportate separatamente per gli strati di andamento del flusso (crescita, stabile, calo): l'emergenza
non modellata dovrebbe dominare nella crescita.

**Lettura:** descrittiva, sulla verifica soltanto; lo sviluppo si riporta a parte e non entra nella lettura. Si
distinguono:
- errore di trasporto: e_SFT grande in regioni stabili;
- nuova emergenza o decadimento non modellati: e_SFT legato a ΔΦ;
- rappresentazione della regione: variante bipolo contro mappa.

Una correlazione fra e_SFT e ΔΦ è una descrizione, non una calibrazione. Nessuna soglia di «validazione» è proposta in
questa revisione: se la revisione ne vuole una, va fissata prima della corsa.

## 9. Che cosa non fa

- Non valida il modello sui tempi del dipolo globale né il campo polare.
- Non usa le osservazioni future per scegliere parametri, maschere o riferimenti, né le assimila.
- Non modella l'emergenza durante Δt: la misura come differenza.
- Non scarica dati nella revisione 1; un eventuale bisogno di record a cadenza più fitta va motivato e autorizzato a parte.
- Non modifica P1 né la selezione dei suoi record.

## 10. Estensione distinta, non parte del pilota

**Controllo globale del dipolo:** le sinottiche HMI polfil locali (CR 2097–2312) permettono di misurare il dipolo
assiale osservato per rotazione. Un confronto con l'SFT richiede tutte le sorgenti (assimilazione o somma completa
delle regioni), il trattamento del polar filling e della composizione temporale delle sinottiche. È un protocollo
separato, da scrivere dopo i due pilota. Non si attribuisce la variazione del dipolo globale a una sola regione.

## 11. Codice e sequenza

1. Revisione di questa bozza insieme alla bozza del punto 2 (stessi parametri, maschera e bilanciamento).
2. Congelamento: seme, estrazione, assegnazione sviluppo/verifica e impronte degli input, prima di leggere qualunque
   mappa del campione.
3. Codice: solutore 2D locale, maschera trasportata, riferimenti, misura con `measure.py`. Prove sintetiche: bipolo
   traslato dalla sola rotazione differenziale (posizione analitica); diffusione di una gaussiana (larghezza analitica);
   conservazione del flusso; bordo; segni e orientamento.
4. Corsa sullo sviluppo, rapporto tecnico, congelamento delle scelte; poi corsa unica sulla verifica, conservazione
   prima della lettura, riconteggio indipendente, rapporto descrittivo distinto da quello del punto 2.

## 12. Punti aperti per la revisione

1. Δt da 1 a 4,5 giorni: va bene, dato che oltre 5 giorni ci sono solo 5 casi?
2. Strati di andamento del flusso dai metadati orari (soglia ±20 %): adeguati come indicatori di emergenza o
   decadimento?
3. Maschera osservata a t₁ contro maschera trasportata: tenere entrambe come proposto?
4. Calotta 2D locale propria contro HipFT globale.
5. Errore osservativo: è fattibile la ripetibilità a breve intervallo con i dati locali, o va dichiarato non stimato?
6. Proporzione sviluppo/verifica (1/3 – 2/3) e numerosità (circa 108).
7. Lettura solo descrittiva, oppure una soglia pratica fissata prima della corsa.
8. Selezione del controllo al massimo di USFLUX: basta dichiararla, o serve una sensibilità con un altro criterio
   fissato ora (per esempio, il record successivo più vicino a t₀ + 2 giorni, se presente fra quelli locali)?

# Pilota SFT mappa–bipolo — BOZZA di protocollo (revisione 2, non congelata)

Stato: **bozza per la revisione di Codex**, 25 novembre 2026 (Claude). Non autorizza simulazioni né download.
Rispetto alla revisione 1 (d62c379) recepisce l'inventario di Codex (`docs/BL_SFT_HMI_INVENTORY.md`, 8b2efcd);
modifiche elencate al §12. Piano di riferimento: `docs/BL_WORK_PLAN.md`, priorità 1; lista dell'utente, punto 2.

## 0. Obiettivo servito e che cosa aggiunge

- **Obiettivo 1 (sorgente BL).** Il proxy P1 riassume una regione con pochi ingredienti: flusso, posizione dei centroidi
  delle polarità, separazione, tilt, latitudine media e polarità leading. Il pilota chiede **quanto cambia il
  contributo della regione al dipolo assiale futuro** se, nello stesso modello di trasporto superficiale (SFT), la mappa
  osservata della regione è sostituita dal bipolo costruito con quegli ingredienti.
- **Che cosa aggiunge.** Le prove già fatte sono istantanee: D contro D_bal e proxy compatto al passaggio al meridiano. Il
  pilota aggiunge l'evoluzione: flusso meridiano, diffusione e cancellazione possono dare alla mappa e al bipolo dipoli
  finali diversi anche quando quelli iniziali coincidono.
- **Limite.** È un controllo dell'approssimazione **dentro il modello**. Non verifica il modello contro il Sole, che è
  il compito del protocollo del punto 3. Non calibra S_BL in unità di dipolo e non somma le regioni.

## 1. Informazioni già note (pilota non cieco)

- Catalogo P1 (`results/P1/P1_SBL_CATALOG_BY_HARP.csv`, 14 195 record, 7133 HARP): S_BL, D, D_bal, centroidi, tilt e
  qualità già calcolati e in parte letti nelle analisi P2/T3/T5. Il campione sotto usa solo metadati e colonne di
  identificazione e qualità, ma chi scrive conosce le distribuzioni generali del catalogo.
- Ricomparse candidate P1e: 443 HARP su 7133, in 373 famiglie.
- Il confronto mappa–bipolo in SFT è già stato studiato (Yeates 2020, arXiv:2008.03203, codice `sharps-bmrs`). Questa
  bozza ne riprende l'impostazione generale, ma non ne adotta parametri, bipolo, trattamento dello sbilancio o
  selezione. I valori numerici di quel lavoro non sono usati come criteri.
- Dall'inventario: tutti i record della selezione P1 sono su disco (Br, bitmap, `keys.json`); la WCS richiede il
  `keys.json` (adattatore `geometry.read_sharp` di P1); nessun solver SFT locale; candidati esterni ispezionati ma non
  eseguiti.

## 2. Domanda, modello e grandezze

Per ogni regione i del campione si eseguono due evoluzioni, **con la sola regione i** sulla sfera e campo iniziale
altrove nullo. L'equazione SFT è lineare in B_r, quindi il contributo di una regione non dipende dalle altre.
- **M (mappa):** B_r osservato della regione, con la maschera del §4.
- **B (bipolo):** due polarità costruite dagli ingredienti P1 (§5).

**Riduzione a una dimensione.** Con rotazione differenziale, flusso meridiano, diffusione e decadimento che non
dipendono dalla longitudine, la media in longitudine b(λ, t) = (1/2π) ∫ B_r dφ soddisfa l'equazione 1D

  ∂b/∂t = −(1/(R cos λ)) ∂(v(λ) b cos λ)/∂λ + (η/(R² cos λ)) ∂/∂λ (cos λ ∂b/∂λ) − b/τ,

in cui la rotazione differenziale non compare. Il dipolo assiale dipende solo da b:

  D(t) = 3/(4πR²) ∫ B_r sin λ dA = (3/2) ∫ b(λ, t) sin λ cos λ dλ   (G).

Quindi il confronto M–B sul dipolo dipende **solo dai profili iniziali in latitudine** b_M(λ, 0) e b_B(λ, 0). Questa è
un'ipotesi del modello: coefficienti assialsimmetrici e trasporto lineare, nessuna dipendenza del trasporto dal campo.
Un trasporto 2D serve al punto 3 (mappe locali), non a questo pilota.

Grandezze:
- D_X(t) per X = M, B ai tempi del §7;
- ΔD(t) = D_B(t) − D_M(t), assoluta;
- ΔD(t)/|D_M(t)| solo se |D_M(t)| supera la soglia del §8. Per dipoli vicini a zero si riporta solo la differenza
  assoluta.

Unità: Br di `hmi.sharp_cea_720s` in G (Mx cm⁻²) secondo la definizione della serie. La keyword BUNIT dei sidecar non
è utilizzabile («Invalid KeyLink», inventario §1) e l'unità non si ricava da lì. S_BL è in Mx·cm e il dipolo in G: per
un bipolo compatto D_bal ≈ 3 hale_sign·S_BL/(4πR³), un'approssimazione che non sostituisce il calcolo sulle mappe.

## 3. Campione

- **Popolazione:** HARP con record primario P1, `valid_bl` vero e `family_rank` = 0 (prima apparizione: niente
  ricomparse, che sono stati successivi della stessa regione).
- **Strati, solo da metadati:**
  - complessità: HARP con un solo NOAA associato, contro HARP con più NOAA o senza NOAA (`NOAA_ARS`);
  - flusso: terzili di `USFLUX` del record primario sulla popolazione;
  - latitudine: |LAT_FWT| < 10°, 10–20°, > 20°;
  - il ciclo (24, 25) si riporta, ma non stratifica.
- **Numerosità:** 4 regioni per cella complessità × flusso × latitudine (18 celle), circa 72 regioni. Le celle con meno
  di 4 HARP si prendono intere e si dichiarano. Il modello 1D costa poco: estendere poi l'analisi a tutta la popolazione
  è possibile, ma richiede una decisione separata dopo la lettura del pilota, dichiarata non cieca.
- **Estrazione:** permutazione con seme fissato, in una zona di semi nuova verificata disgiunta da quelle già usate;
  prime 4 per cella; pesi campionari 1/π per cella registrati.
- **Nessuna esclusione dopo la lettura degli esiti.** Le regioni che falliscono per motivi tecnici (geometria, flusso
  nullo dopo la maschera, errore del codice) restano nel denominatore, con la causa.

## 4. Mappa osservata (M)

- **Record:** il record primario P1 (|LON_FWT| ≤ 30°): gli stessi `Br`, `bitmap` e `keys.json` della misura P1, letti
  con l'adattatore P1 (WCS completa, CEA obliqua, area dei pixel R²·Δφ·Δμ). Nessun download.
- **Pixel:** stessa maschera e soglia di P1: Br finito, |Br| ≤ 10 000 G, bitmap ≥ 33, |Br| ≥ 100 G. Così M e B
  partono dallo stesso insieme di pixel e il confronto isola l'approssimazione bipolare dalle scelte di misura. Gli
  altri pixel sono a zero.
- **Flusso preesistente:** la maschera HARP contiene anche flusso non della regione emersa (plage residuo, regioni
  vicine incluse nella HARP). Nel principale resta incluso, come nella misura P1, e il bipolo lo rappresenta
  attraverso centroidi e flusso. Sensibilità: soglia 300 G, che privilegia le parti intense.
- **Bilanciamento:** la mappa mascherata ha in genere Φ₊ ≠ Φ₋, e il monopolo non ha significato fisico in SFT.
  Principale: riscalare ciascuna polarità a Φ̄ = (Φ₊ + Φ₋)/2, cioè B_r → B_r·Φ̄/Φ± sul segno corrispondente; è
  coerente con D_bal e conserva le forme. Sensibilità: sottrazione di un campo uniforme sui pixel mascherati. Si
  riportano sempre lo sbilancio iniziale (Φ₊ − Φ₋)/(Φ₊ + Φ₋) e D prima e dopo il bilanciamento.
- **Profilo in latitudine:** b_M(λ) sulla griglia del modello, per conservazione del flusso. Il flusso B_r dA di ogni
  pixel va alla cella di latitudine che contiene il centro del pixel, e b nella cella j vale Σ B_r dA / (2πR²(sin λ_{j+1}
  − sin λ_j)). Sensibilità alla discretizzazione: ripartizione dei pixel sub-campionati (4 × 4) fra le celle.
- **Prova obbligatoria:** D_M(0) dal profilo uguale a D dei pixel della mappa bilanciata (stessa formula di P1),
  entro una tolleranza fissata con le prove sintetiche di convergenza in risoluzione.

## 5. Bipolo (B)

Gli scalari P1 non determinano una mappa bipolare unica: forma ed estensione sono scelte dichiarate.
- **Posizioni:** i centroidi P1 delle due polarità, (L₊, λ₊) e (L₋, λ₋). Separazione, tilt e latitudine media del
  bipolo coincidono quindi con quelli del catalogo, per costruzione.
- **Flusso:** Φ̄ per ciascuna polarità, con i segni osservati.
- **Forma principale:** due macchie gaussiane sulla sfera, B ∝ exp(−δ²/(2σ²)) con δ la distanza angolare dal
  centroide. σ di ciascuna polarità si ricava dalla sua area sopra soglia: σ = √(A±/(2πR²)) in radianti. La forma è
  quindi fissata da una grandezza misurata, non scelta per far concordare M e B.
- **Profilo:** b_B(λ) si calcola integrando le macchie su una griglia 2D fine (passo non superiore a un decimo di σ),
  poi mediando in longitudine con la stessa regola di conservazione del §4.
- **Sensibilità di forma:** σ fisso a 2° e a 4° per entrambe le polarità; bipolo puntiforme (tutto il flusso nella
  cella di latitudine del centroide).
- **D iniziale.** Il bipolo puntiforme ha D_B(0) = 3/(4πR²)·Φ̄·(sin λ₊ − sin λ₋), con λ± le latitudini dei centroidi
  (media dei vettori unitari rinormalizzata). D_bal usa invece le medie ⟨sin λ⟩±: le due quantità differiscono anche
  per sorgenti puntiformi. Si riportano D_B(0) − D_M(0), D_B(0) − D_bal e D_M(0) − D_bal.
- La procedura di Yeates (`sharps-bmrs`) costruisce un bipolo diverso. Si può aggiungere come sensibilità solo se
  riscritta e documentata sotto questo protocollo; non è la definizione principale.

## 6. Modello di trasporto

Stesso codice, griglia, parametri e tempi per M e B. Nessun parametro si sceglie confrontando M con B.
- **Codice:** implementazione propria dell'equazione 1D del §2 (volumi finiti in sin λ, conservativa), nel repository BL.
  Il nucleo `SFT1` di `sharps-bmrs` (GPL-3.0, commit 2d6566ce) e la versione 1D di `sft-historical` (BSD-2-Clause,
  commit 3cd2f332) servono come **oracoli esterni** nelle prove (eseguiti da Codex fuori dal repository), non come
  codice copiato. L'incorporazione di codice GPL nel repository è una decisione di licenza dell'utente e di Paolo.
- **Parametri di riferimento:** profilo e ampiezza del flusso meridiano, η e τ si trascrivono da **un** modello 1D
  pubblicato e documentato, scelto prima della corsa, con la fonte citata (proposta: i valori predefiniti del commit
  fissato di `sharps-bmrs`, da trascrivere e verificare nella revisione). Decadimento τ assente nel principale; 5 e
  10 anni come sensibilità.
- **Sensibilità di trasporto:** due combinazioni oltre al riferimento, η e ampiezza del flusso meridiano agli estremi
  di un intervallo tratto dalla stessa letteratura e fissato prima della corsa. Uguali per tutte le regioni e per M e
  B; servono a vedere se l'approssimazione dipende dal trasporto, non a sceglierne uno.
- **Istante iniziale:** il T_OBS del record primario (l'inventario raccomanda T_OBS per le misure). Il campo evolve
  senza nuove sorgenti.
- **Convergenza:** risoluzione in latitudine e passo temporale raddoppiati e dimezzati sui casi sintetici e su 3
  regioni del campione estratte con lo stesso seme, prima della lettura dei risultati.

## 7. Tempi di confronto

t = 0, 27 giorni, 6 mesi, 1 anno, 3 anni dall'inserimento. Si attende che a 3 anni il contributo della singola regione
abbia superato la fase di trasporto e cancellazione iniziale. La diffusione continua però a ridurre lentamente il modo
dipolare (scala R²/(2η), circa 15 anni con η = 500 km²/s). Da verificare con il codice, senza cambiare i tempi dopo
aver visto gli esiti. Si salvano anche le curve D_X(t) a passo regolare, per i grafici.

## 8. Prodotti e lettura

**Per regione:** HARP, strati, Φ₊, Φ₋, sbilancio, D e D_bal P1, D_M(0), D_B(0), D_X(t) ai tempi del §7, ΔD(t),
ΔD(t)/|D_M(t)| (con la soglia sotto), separazione, tilt e σ±; lo stesso per ogni sensibilità.

**Per strato e totale:** mediana e quantili 10–90 % di ΔD/|D_M| e di |ΔD|; frazione di regioni con segno di D_B(3 anni)
uguale a quello di D_M(3 anni). Somme dei dipoli solo come descrizione dell'effetto aggregato, con la cautela del §9.

**Soglia per i rapporti:** |D_M(t)| ≥ 0,1 della mediana di |D_M(t)| nel campione allo stesso tempo. Sotto la soglia si
riportano solo differenze assolute. Da confermare in revisione.

**Lettura:** descrittiva. Una preferenza pratica, da fissare prima delle corse e non come criterio scientifico
validato, potrebbe essere: approssimazione bipolare «adeguata nel modello» per uno strato se la mediana di
|ΔD(3 anni)|/|D_M(3 anni)| è ≤ 0,2 con tutti i trasporti. I valori sono proposti per la revisione. Una regione con
grande differenza non si esclude e non si corregge.

## 9. Che cosa non fa

- Non confronta con le osservazioni successive (protocollo del punto 3, con trasporto 2D o locale).
- Non stima il dipolo solare complessivo: le regioni sono simulate da sole; la somma di contributi lineari ignora
  ricomparse e cancellazioni con flusso di altre regioni già presente sul Sole.
- Non tratta trasporti non assialsimmetrici o dipendenti dal campo (per esempio inflow verso le regioni attive).
- Non modifica P1, i suoi record o le sue soglie; non scarica dati.
- Non riapre T3, T5 o Q4.

## 10. Codice e sequenza

1. Revisione di questa bozza (Codex); scelta e trascrizione dei parametri di trasporto; congelamento con SHA, seme e
   impronte degli input.
2. Codice: lettura con l'adattatore P1, maschera, bilanciamento, profilo in latitudine, bipolo, solutore 1D, misura di
   D. Prove sintetiche indipendenti (Codex): flusso netto nullo conservato; per sorgenti puntiformi D(0) uguale alla
   formula; segni, unità e orientamento; limiti analitici (senza flusso meridiano la sola diffusione fa decadere il modo
   l = 1 come exp(−2ηt/R²); il termine τ come exp(−t/τ)); convergenza; confronto con gli oracoli esterni sugli stessi
   profili iniziali.
3. Corsa unica, conservazione prima della lettura, riconteggio indipendente, rapporto descrittivo.

## 11. Punti aperti per la revisione

1. Popolazione con `family_rank` = 0 soltanto, o anche le ricomparse come strato separato?
2. Complessità definita da `NOAA_ARS`: è sufficiente come proxy prima di una classificazione morfologica?
3. Bilanciamento per riscalatura delle polarità contro sottrazione uniforme: quale come principale?
4. σ dalle aree contro σ fisso come forma principale del bipolo.
5. Tempi di confronto e soglia per i rapporti.
6. Preferenza pratica del §8: tenerla, cambiarla o lasciare la lettura solo descrittiva.
7. Riduzione 1D: accettabile come ipotesi dichiarata per questo pilota (solo dipolo assiale)?
8. Parametri di trasporto: quale modello pubblicato trascrivere, e quale intervallo per le sensibilità.
9. Licenza: oracoli esterni eseguiti fuori dal repository, oppure incorporare `SFT1` (GPL-3.0)? Decisione dell'utente
   e di Paolo.

## 12. Modifiche dalla revisione 1 (d62c379)

- Recepito l'inventario (8b2efcd): dati P1 tutti locali, nessun download; WCS dal `keys.json` con l'adattatore P1;
  unità di Br dalla definizione della serie, non da BUNIT; T_OBS come istante iniziale.
- Modello: riduzione 1D esplicita per il dipolo assiale (§2), implementazione propria, codici esterni come oracoli e
  questione di licenza (§6).
- Profili in latitudine per M e B (§4, §5) e nota su D_B(0) puntiforme rispetto a D_bal (§5).
- Convergenza in risoluzione (§6); costo basso e possibile estensione alla popolazione come decisione separata (§3).
- Punti aperti 7–9 aggiunti; tolti i marcatori [dopo l'inventario].

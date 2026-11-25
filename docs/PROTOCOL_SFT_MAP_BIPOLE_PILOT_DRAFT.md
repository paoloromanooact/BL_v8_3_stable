# Pilota SFT mappa–bipolo — BOZZA di protocollo (revisione 3, non congelata)

Stato: **bozza per il controllo finale di Codex prima del congelamento**, 25 novembre 2026 (Claude). Non autorizza
simulazioni né download. Recepisce la revisione di Codex della revisione 2
(`docs/SFT_MAP_BIPOLE_DRAFT_REVIEW_fa3f08d.md`, commit 9aa3fce) e il raccordo dei parametri della revisione del
punto 3 (`docs/SFT_OBSERVED_DRAFT_REVIEW_e0bba64.md`, commit 7f5d703). Modifiche al §13. Piano: `docs/BL_WORK_PLAN.md`,
priorità 1; lista dell'utente, punto 2.

## 0. Obiettivo servito e che cosa aggiunge

- **Obiettivo 1 (sorgente BL).** Il proxy P1 riassume una regione con pochi ingredienti: flussi, centroidi delle
  polarità, separazione, tilt, latitudine media e polarità leading. Il pilota chiede **quanto cambia il contributo del
  campo selezionato al dipolo assiale futuro** se, nello stesso modello di trasporto superficiale (SFT), la mappa
  osservata è sostituita dal bipolo costruito con quegli ingredienti.
- **Che cosa aggiunge.** Le prove già fatte sono istantanee (D contro D_bal, proxy compatto). Il pilota aggiunge
  l'evoluzione: flusso meridiano e diffusione possono dare alla mappa e al bipolo dipoli diversi anche quando quelli
  iniziali coincidono.
- **Limite.** È un controllo dell'approssimazione **dentro il modello**, non una verifica contro il Sole (punto 3), né
  una calibrazione di S_BL o una somma di regioni. L'oggetto è il campo selezionato nella patch all'istante t₀, che
  comprende il flusso preesistente; non è una sorgente pura di nuova emersione.

## 1. Informazioni già note (pilota non cieco)

- Catalogo P1 (`results/P1/P1_SBL_CATALOG_BY_HARP.csv`, 14 195 record, 7133 HARP): S_BL, D, D_bal, centroidi, tilt e
  qualità già calcolati e in parte letti nelle analisi P2/T3/T5. Il campione usa solo metadati e colonne di
  identificazione e qualità; chi scrive conosce le distribuzioni generali del catalogo.
- Ricomparse candidate P1e: 443 HARP su 7133, in 373 famiglie.
- Yeates 2020 (arXiv:2008.03203, codice `sharps-bmrs`) studia lo stesso confronto. Qui se ne riprendono la riduzione
  1D e i parametri di trasporto pubblicati (§6), non il bipolo, il trattamento dello sbilancio o la selezione.
- Inventario (8b2efcd): tutti i record della selezione P1 sono locali (Br, bitmap, `keys.json`); la WCS richiede il
  `keys.json` (adattatore `geometry.read_sharp`); nessun solver SFT locale.

## 2. Domanda, modello e grandezze

Per ogni regione i del campione si eseguono due evoluzioni, **con la sola regione i** sulla sfera e campo iniziale
altrove nullo. L'equazione è lineare in B_r: la differenza M − B evolve con lo stesso operatore, e la sovrapposizione
delle soluzioni include già la cancellazione del campo firmato.
- **M (mappa):** B_r osservato della regione, con la maschera del §4.
- **B (bipolo):** il bipolo costruito dagli ingredienti P1 (§5).

**Riduzione a una dimensione.** Con coefficienti di trasporto indipendenti dalla longitudine (non serve una mappa
iniziale assialsimmetrica), la media in longitudine b(s, t) = (1/2π) ∫ B_r dφ, con s = sin λ, soddisfa

  ∂b/∂t = ∂/∂s [ (η/R²)(1 − s²) ∂b/∂s − (v(arcsin s)/R) √(1 − s²) b ] − b/τ,

con flusso nullo ai poli (s = ±1). La rotazione differenziale non compare. Il dipolo assiale dipende solo da b:

  D(t) = 3/(4πR²) ∫ B_r sin λ dA = (3/2) ∫₋₁¹ b(s, t) s ds   (G).

Quindi il confronto M–B sul dipolo dipende **solo dai profili iniziali in s**.

**Grandezze:**
- D_X(t) per X = M, B ai tempi del §7;
- ΔD(t) = D_B(t) − D_M(t), assoluta;
- ΔD(t)/D_scale con D_scale = 3Φ̄/(4πR²): differenza normalizzata che non diverge quando D_M ≈ 0;
- ΔD(t)/|D_M(t)| solo con la soglia del §8.

**Unità e convenzioni.** Br di `hmi.sharp_cea_720s` in G (Mx cm⁻²) dalla definizione della serie; la keyword BUNIT dei
sidecar non è utilizzabile (inventario §1). R è lo stesso della geometria P1 (`RSUN_REF` dell'header), con conversioni
cm ↔ km esplicite. D è il dipolo geografico (nord positivo), senza orientamento per ciclo o emisfero. Eventuali dipoli
orientati per ciclo si nominano a parte e non sostituiscono D.

**Relazione con S_BL (solo descrittiva).** P1 definisce φ = Φ₊ + Φ₋ e S_BL = hale_sign·φ·d·cos λ·sin α. Il bipolo
puntiforme bilanciato ha D_point = 3Φ̄/(4πR²)(sin λ₊ − sin λ₋), con Φ̄ = φ/2. Nel limite compatto, con le convenzioni
leading → following di P1, D_point ≈ −expected_leading_sign · 3 S_BL/(8πR³) (verificato da Codex su otto bipoli
sintetici entro 1,6·10⁻⁹ relativo). Questa relazione non entra nella misura, che usa i pixel e la formula esatta.

## 3. Campione

- **Popolazione:** HARP con record primario P1 (`role` = `primary` o `both`), `valid_bl` = 1 e `family_rank` = 0 (prima
  apparizione della famiglia candidata P1e, non la prova di una nuova emersione). Nessuno strato di ricomparse.
- **Strati, solo da metadati del record primario:**
  - molteplicità delle associazioni: «un NOAA» (`NOAA_NUM` = 1) contro «altro/ignoto» (`NOAA_NUM` ≠ 1), con un flag
    distinto per NOAA assente (`NOAA_NUM` = 0, `NOAA_ARS` = `MISSING`). È una proxy di molteplicità, non di morfologia
    magnetica: nessuna conclusione su regioni magneticamente semplici o complesse;
  - flusso: terzili di `USFLUX` sulla popolazione, con `numpy.quantile` lineare: classe 1 se x ≤ q₁, 2 se q₁ < x ≤ q₂,
    3 se x > q₂; i record senza `USFLUX` finito restano fuori dalla popolazione e si contano;
  - latitudine: |LAT_FWT| < 10°, 10° ≤ |LAT_FWT| < 20°, |LAT_FWT| ≥ 20°;
  - il ciclo (24, 25) si riporta e non stratifica.
- **Numerosità:** 4 regioni per cella (2 × 3 × 3 = 18 celle), al più 72. Le celle con meno di 4 HARP si prendono intere
  e si dichiarano.
- **Estrazione:** ordinamento canonico per `HARPNUM` crescente; permutazione `numpy.random.default_rng(36_100_000)`
  dell'intera popolazione; per ogni cella, le prime 4 HARP nell'ordine della permutazione. Zona di semi
  36 100 000–36 100 999, verificata libera in `scripts/`, `python/` e `docs/` (25 novembre). Probabilità di inclusione
  π = n/N per cella e pesi N/n registrati.
- **Nessuna esclusione dopo la lettura degli esiti.** I fallimenti tecnici (geometria, flusso nullo dopo la maschera,
  errore del codice) restano nel denominatore della resa, con la causa, separati dai valori non definiti.

## 4. Mappa osservata (M)

- **Record:** il record primario P1, cioè gli stessi `Br`, `bitmap` e `keys.json` della misura P1, letti con
  l'adattatore P1 (WCS completa, CEA obliqua, area dei pixel R²·Δφ·Δμ). Nessun download.
- **Pixel:** maschera e soglia di P1 (Br finito, |Br| ≤ 10 000 G, bitmap ≥ 33, |Br| ≥ 100 G); gli altri pixel a zero.
- **Flusso preesistente:** incluso, come nella misura P1, e dichiarato.
- **Bilanciamento:** ciascuna polarità riscalata a Φ̄ = (Φ₊ + Φ₋)/2 (B_r → B_r·Φ̄/Φ± sul segno corrispondente). Conserva le
  forme e riproduce il D_bal di P1 prima della rimappatura. Nessuna sottrazione uniforme. Si riportano lo sbilancio
  iniziale (Φ₊ − Φ₋)/(Φ₊ + Φ₋) e D prima e dopo il bilanciamento.
- **Sensibilità 300 G:** nuova maschera |Br| ≥ 300 G; flussi, centroidi, Φ̄, bilanciamento e bipolo **ricalcolati** da
  quella maschera per M e per B. Gli ingredienti a 100 G non si riusano; il catalogo P1 resta intatto.
- **Profilo in s (deposito):** ogni pixel ha flusso F = B_r dA e coordinata s = sin λ del suo centro. Il flusso si
  ripartisce fra i due centri di cella adiacenti in s con pesi lineari, w_j = (s_{j+1} − s)/(s_{j+1} − s_j) e
  w_{j+1} = 1 − w_j. Questo conserva esattamente sia il flusso totale sia il primo momento Σ F s, quindi D(0). Il
  deposito nella sola cella che contiene il pixel conserverebbe il flusso ma non il momento: Codex ha mostrato un
  caso in cui annulla D. Ai bordi (s oltre il primo o l'ultimo centro) si usa la cella estrema con un controllo
  dichiarato; con le latitudini attive il caso non dovrebbe presentarsi e viene contato.
- **Controlli distinti:**
  1. **deposito:** flusso e Σ F s dopo il deposito uguali a quelli dei pixel entro 10⁻¹² relativo (identità
     algebrica);
  2. **D_M(0) contro D P1** della mappa bilanciata: stessa quadratura sui centri dei pixel, quindi stessa identità.
     Si riporta la differenza; non si impone a una rappresentazione sub-pixel di riprodurla.

## 5. Bipolo (B)

Gli scalari P1 non determinano una mappa bipolare unica: forma ed estensione sono scelte dichiarate.
- **Principale: bipolo puntiforme.** Flusso +Φ̄ nel centroide P1 della polarità positiva e −Φ̄ in quello della negativa,
  con le latitudini dei centroidi (media dei vettori unitari pesata con |Br|, rinormalizzata). Ogni punto si deposita
  con la regola lineare del §4. Rappresenta direttamente flussi e centroidi P1 senza introdurre una larghezza.
- D_point(0) = 3Φ̄/(4πR²)(sin λ₊ − sin λ₋) differisce in generale da D_bal, che usa ⟨sin λ⟩± pesate con |Br|: la
  latitudine del centroide sferico rinormalizzato non è la media di sin λ. Se ogni polarità della mappa è davvero un
  singolo punto, le due coincidono. Si riportano D_B(0) − D_M(0) e D_B(0) − D_bal.
- **Sensibilità di forma, gaussiane sulla sfera.** Ciascuna componente ha B ∝ exp(−δ²/(2σ²)), con δ la distanza
  angolare dal centro, è normalizzata a flusso Φ̄ (positiva e negativa) **prima** della sovrapposizione e ha il centro
  nel centroide P1. Il campo è la somma delle due componenti, senza riscalature successive. Larghezze: σ ad area
  equivalente, √(A±/(2πR²)) con A± l'area sopra soglia della polarità (una scelta, non una larghezza inferita); σ fisso
  a 2° e a 4°. Le code delle due componenti si cancellano dove si sovrappongono. Codex ha mostrato che con centri a ±1°
  e σ = 2° il campo risultante ha flusso positivo 0,383 e centroide a 2,61°. Per ogni sensibilità si riportano
  quindi i flussi e i centroidi **effettivi** del campo risultante, accanto ai centri delle componenti, senza
  correggerli dopo aver letto gli esiti.
- Le gaussiane si integrano su una griglia 2D fine, con passo non superiore a σ/10 e non superiore a 0,05°, e poi si
  depositano in s con la regola del §4.

## 6. Modello di trasporto

Stesso codice, griglia, parametri e tempi per M e B. Nessun parametro si sceglie confrontando M con B.
- **Riferimento (Yeates 2020, §3.1, eq. 12–13, insieme pre-HMI dei cicli 21–23):** η = 466,8 km²/s;
  v(λ) = D_u sin λ cos^p λ con D_u = 0,025 km/s e p = 2,33 (il massimo di v è circa 9,04 m/s: D_u non è il massimo);
  τ infinito.
- **Sensibilità di trasporto, griglia 2 × 2:** η ∈ {350; 466,8} km²/s × D_u ∈ {0,025; 0,041} km/s, p invariato. Le
  coppie (466,8; 0,025) e (350; 0,041) sono citate nel lavoro; la seconda fu scelta confrontando il ciclo 24 HMI (si
  dichiara la sovrapposizione con i nostri dati). Le combinazioni incrociate sono scenari numerici dichiarati, non
  modelli pubblicati né un intervallo di confidenza.
- **Decadimento:** τ = 5 e 10 anni come sensibilità, applicato come fattore exp(−t/τ) alla soluzione senza decadimento.
  È un'identità dell'equazione lineare, verificata nelle prove (§10), quindi non serve ricalcolare il trasporto.
- **Discretizzazione (fissata ora):** volumi finiti su N = 400 celle uniformi in s ∈ [−1, 1]; flusso nullo alle facce
  polari; schema di Crank–Nicolson sull'operatore lineare completo, con passo Δt = 1 giorno (86 400 s). Convergenza su
  N ∈ {200, 400, 800} e Δt ∈ {2; 1; 0,5} giorni, nei casi sintetici del §10. Criterio fissato ora: variazione relativa di
  D(3 anni) fra N = 400 e 800, e fra Δt = 1 e 0,5 giorni, < 10⁻³. Se il criterio fallisce, si raddoppia la risoluzione
  prima di qualunque dato osservato.
- **Codice:** implementazione propria nel repository BL. `SFT1` di `sharps-bmrs` (GPL-3.0, commit 2d6566ce) e la
  versione 1D di `sft-historical` (BSD-2-Clause, commit 3cd2f332) restano riferimenti esterni separati, con versione e
  licenza registrate. I confronti fra codici a griglie diverse si portano allo stesso problema continuo e a
  convergenza, senza pretendere identità bit per bit. Un secondo codice non sostituisce le prove analitiche.
- **Istante iniziale:** T_OBS del record primario (TAI, con conversione esplicita); il campo evolve senza nuove sorgenti.

## 7. Tempi di confronto

t = 0, 27 giorni, 0,5 anni, 1 anno, 3 anni, con anno = 365,25 giorni di 86 400 s. Tre anni sono un orizzonte fissato,
non la garanzia di uno stato finale: la diffusione continua a ridurre il modo dipolare (scala R²/(2η), circa 16 anni con
η = 466,8 km²/s). Si salvano anche le curve D_X(t) a passo di un giorno, per i grafici.

## 8. Prodotti e lettura

**Per regione:** HARP, strati, flag NOAA assente, Φ₊, Φ₋, sbilancio, D e D_bal P1, D_M(0), D_B(0), D_X(t) ai tempi del §7,
ΔD(t), ΔD(t)/D_scale, ΔD(t)/|D_M(t)| con la soglia sotto, separazione e tilt, flussi e centroidi effettivi delle
sensibilità gaussiane; lo stesso per ogni sensibilità.

**Soglia per i rapporti:** |D_M(t)| ≥ 0,1·m(t), con m(t) la mediana pesata (pesi N/n) di |D_M(t)| nel riferimento
principale. La stessa soglia vale per tutte le varianti; si riportano i denominatori. Se m(t) = 0, nessun rapporto.

**Per strato e totale:** mediana e quantili 10–90 % pesati con N/n di ΔD/D_scale, di |ΔD| e, dove definito, di
ΔD/|D_M|; frazione di regioni con segno di D_B(3 anni) uguale a quello di D_M(3 anni); dipendenza da forma e trasporto.
Il campione non pesato si riporta a parte. Somme di dipoli solo come descrizione, con la cautela del §9.

**Lettura:** descrittiva. Nessuna etichetta di adeguatezza né soglia pratica: si riportano differenze, segni e loro
dipendenza da forma e trasporto, senza trasformare una soglia arbitraria in una validazione della sorgente. Nessuna
regione si esclude o si corregge dopo la lettura.

## 9. Che cosa non fa

- Non confronta con le osservazioni successive (punto 3, trasporto 2D locale).
- Non stima il dipolo solare complessivo. La somma dei contributi lineari di patch osservate ha come limiti il doppio
  conteggio, le ricomparse, le emersioni mancanti e il flusso preesistente, non la linearità.
- Non tratta trasporti non assialsimmetrici o dipendenti dal campo (per esempio gli inflow verso le regioni attive).
- Non modifica P1, i suoi record o le sue soglie; non scarica dati; non riapre T3, T5 o Q4.

## 10. Prove e sequenza

1. **Controllo finale di Codex** e congelamento: SHA, seme, estrazione e impronte degli input, prima di leggere
   qualunque mappa del campione.
2. **Codice:** lettura con l'adattatore P1, maschera, bilanciamento, deposito, bipolo, solutore 1D, misura di D.
3. **Prove sintetiche indipendenti** (Codex):
   - flusso netto e D(0) dopo il deposito;
   - modo l = 1 in sola diffusione: decade come exp(−2ηt/R²);
   - decadimento uniforme: exp(−t/τ) applicato a posteriori uguale al calcolo con τ;
   - riflessione nord/sud e inversione di polarità: segno di D;
   - convergenza spaziale e temporale (§6), con punti nella stessa cella e vicino all'equatore;
   - raccordo di longitudine 0/360 e WCS obliqua, verificati a parte;
   - confronto con i riferimenti esterni sullo stesso problema continuo.
4. **Casi osservati:** tre regioni estratte con lo stesso seme verificano la regola numerica già fissata, senza servire
   a scegliere tolleranze guardando ΔD.
5. Corsa unica, conservazione prima della lettura, riconteggio indipendente, rapporto descrittivo.

## 11. Punti già decisi in revisione (Codex, 9aa3fce)

Popolazione `family_rank` = 0; strati «un NOAA» / «altro o ignoto»; riscalatura senza sottrazione uniforme; bipolo
puntiforme principale con gaussiane come sensibilità; tempi in anni giuliani; lettura senza soglia pratica; riduzione 1D;
parametri pre-HMI con griglia 2 × 2; implementazione propria e riferimenti esterni separati.

## 12. Punti ancora aperti

1. Scelta di N = 400, Crank–Nicolson e Δt = 1 giorno, con il criterio di convergenza 10⁻³: adeguati?
2. Gestione dei pixel con s oltre il primo o l'ultimo centro di cella (§4): cella estrema con conteggio, o estensione
   con celle fantasma?

## 13. Modifiche dalla revisione 2 (fa3f08d)

- A1: corretta la relazione S_BL → D (fattore 1/2 e segno, −expected_leading_sign); resa solo descrittiva; D geografico.
- A2: deposito lineare in s, che conserva flusso e primo momento; due controlli distinti.
- A3: bipolo puntiforme principale; gaussiane come sensibilità, con normalizzazione prima della sovrapposizione e flussi
  e centroidi effettivi riportati; corretta la frase su D_point e D_bal.
- Punti B1–B9 recepiti; parametri pre-HMI di Yeates 2020 con griglia 2 × 2; τ come fattore.
- C: operatore in s con flusso nullo ai poli, discretizzazione e convergenza fissate, prove separate, §9 corretto.
- Strati e estrazione resi operativi (definizioni, pareggi, seme, ordinamento, pesi).

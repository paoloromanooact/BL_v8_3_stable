# Confronto SFT con l'evoluzione osservata — BOZZA di protocollo (revisione 3, non congelata)

Stato: **bozza per il congelamento, con una revisione del disegno da confermare (§12)**, 25 novembre 2026 (Claude).
Non autorizza simulazioni né download. Recepisce le revisioni di Codex 7f5d703 (`docs/SFT_OBSERVED_DRAFT_REVIEW_e0bba64.md`)
ed e87fff7 (`docs/SFT_790cad1_FINAL_REVIEW.md`). Modifiche al §13. Piano: `docs/BL_WORK_PLAN.md`, priorità 2; lista
dell'utente, punto 3. Collegato alla bozza del punto 2 (`docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_DRAFT.md`, revisione 4), con
gli stessi parametri di trasporto.

## 0. Obiettivo servito e che cosa aggiunge

- **Obiettivo 1 (sorgente BL).** Il proxy misura la regione in un solo istante vicino al meridiano centrale. Il pilota
  chiede se un modello SFT inizializzato con la mappa osservata **descrive le grandezze osservate pochi giorni dopo**
  meglio di riferimenti senza trasporto, su dati non usati per scegliere modello e misura, e **quanto i residui si
  associano alla variazione del flusso** fra i due istanti.
- **Che cosa aggiunge al punto 2.** Il punto 2 confronta due rappresentazioni nello stesso modello; qui il termine di
  confronto è il Sole osservato.
- **Limiti.** Confronta prestazioni descrittive di modelli incompleti su una popolazione condizionata dalla selezione.
  Pochi giorni e una regione per volta: l'accordo locale non valida il trasporto sui tempi del dipolo globale né il
  campo polare. I residui non identificano una causa (§8).

## 1. Informazioni già note (non cieco)

- **Dati locali (inventario 8b2efcd).** P1 ha per ogni HARP un record primario (|LON_FWT| minimo, ≤ 30°) e uno di
  controllo. Insieme alle patch BARD, 7173 HARP hanno da 1 a 4 record: non sono sequenze regolari.
- **Selezione del controllo:** il record con USFLUX massimo entro |LON_FWT| ≤ 60°, fra candidati che comprendono il
  primario. Quindi USFLUX(controllo) ≥ USFLUX(primario) **per costruzione**: nessun controllo ha flusso minore
  (verificato da Codex su 7133 HARP). Il confronto riguarda una popolazione al massimo del flusso dichiarato e non si
  generalizza alle fasi di decadimento.
- **Già studiato:** l'evoluzione primario → controllo di tilt, S_BL, segno di D* e hale_sign (P1d §3, `P1_CHECKS.csv`).
- **Conteggi dai soli metadati (25 novembre, T_REC nominale; letti HARPNUM, T_REC, role, USFLUX, NOAA_NUM, family_rank,
  valid_bl).** Bacino con primario `valid_bl` = 1, `family_rank` = 0 e controllo successivo a 1–4,5 giorni:
  **1023 HARP** (265 senza NOAA). Rapporto USFLUX(controllo)/USFLUX(primario):

  | Δt (giorni) | crescita > 20 % (un NOAA / altro o ignoto) | variazione ≤ 20 % (un NOAA / altro o ignoto) |
  |---|---|---|
  | 1–2 | 60 / 68 | 6 / 4 |
  | 2–3 | 83 / 73 | 1 / 2 |
  | 3–4,5 | 434 / 276 | 13 / 3 |

  Le celle «variazione ≤ 20 %» contengono in tutto 29 regioni: per questo l'andamento del flusso non stratifica (§4).
  Per molteplicità × Δt il bacino conta 66, 72, 84, 75, 447, 279 HARP (somma 1023, minimo 66; un NOAA / altro, per
  1–2, 2–3, 3–4,5 giorni). Conteggi preliminari su T_REC; l'estrazione usa T_OBS.
- **Fattibilità geometrica dai soli `keys.json` (25 novembre; nessun pixel letto).** Impronte in Carrington dai bordi
  della griglia CEA, con la WCS dell'adattatore P1; intersezione primario–controllo; erosione con il margine del §3
  calcolato sul massimo della griglia dei parametri. Le patch hanno una mediana di 16,3° × 7,2° (longitudine ×
  latitudine). Con il margine della revisione 2 (isotropo) e 25 deg², solo **207** coppie su 1023 hanno un interno
  utilizzabile, e le celle a 1–3 giorni ne avrebbero 5–8, sotto le 18 previste. Con il **margine direzionale** del §3
  (rotazione solo in longitudine, flusso meridiano solo in latitudine), sempre con √(4ηΔt) e 25 deg², le coppie
  utilizzabili sono **336**: 1–2 giorni 7/9, 2–3 giorni 17/12, 3–4,5 giorni 160/131 (un NOAA / altro). Da qui la revisione
  degli strati del §4. È una scelta di disegno su soli metadati e geometria, prima di qualunque pixel o esito.
- **Scale attese del modello.** In tre giorni la diffusione sposta il flusso di circa √(4ηt) ≈ 2° (η = 466,8 km²/s),
  il flusso meridiano di circa 0,2°; la rotazione differenziale stira la regione in longitudine. Nei primi giorni le
  variazioni osservate possono essere dominate da processi che l'SFT non contiene (Gottschling et al. 2021,
  arXiv:2111.01896, A&A 2022).

## 2. Domanda

Per una regione con mappa al tempo t₀ (record primario) e osservazione a t₁ = t₀ + Δt (record di controllo),
1 ≤ Δt ≤ 4,5 giorni:
- gli errori della previsione SFT a t₁ sono minori di quelli dei riferimenti senza trasporto (§6), sullo stesso dominio
  e con la stessa preparazione?
- quanto gli errori si associano alla variazione del flusso fra t₀ e t₁? È una descrizione, non un'attribuzione causale.

## 3. Campo, dominio e osservabili

**Preparazione comune.** Tutti i modelli di un confronto (SFT, persistenza, sola rotazione) partono dallo **stesso campo
preparato** a t₀, e l'osservazione a t₁ si prepara con lo stesso operatore.

- **Principale: mappa locale grezza.** Il campo iniziale è dato da tutti i pixel finiti della patch CEA a t₀ (Br finito,
  |Br| ≤ 10 000 G), senza soglia, senza bitmap e senza bilanciamento. Il flusso netto non nullo in una finestra locale
  non è un monopolo solare: il campo compensante può stare fuori dalla finestra, e il modello locale trasporta il
  campo così com'è.
- **Rappresentazione alternativa dichiarata: sorgente P1.** Solo i pixel della maschera P1 (bitmap ≥ 33, |Br| ≥ 100 G) a
  t₀. Il confronto con il campo osservato completo a t₁ include allora il campo debole omesso all'inizio: questo
  contributo si misura e non si chiama errore del trasporto.
- **Sensibilità bilanciata:** riscalatura delle polarità a Φ̄ (come nel punto 2) applicata coerentemente a t₀ e a t₁, con
  i suoi riferimenti. La variante bipolo bilanciata del punto 2 si confronta con questa mappa bilanciata, non con il
  principale grezzo.

**Dominio comune (confronto principale).** Griglia di Carrington regolare in latitudine e longitudine (passo 0,06°),
con aree R²·Δφ·(sin λ_nord − sin λ_sud). Il dominio comune C è l'insieme delle celle coperte da pixel finiti **sia**
nella patch a t₀ **sia** in quella a t₁, erose dal bordo della patch a t₀ con un margine **direzionale**, perché il campo
che entra da fuori non è nel modello:
- in longitudine: m_φ = √(4η_max Δt)/R + max_λ |ω(λ) − ω_C|·Δt + 0,5°;
- in latitudine: m_λ = √(4η_max Δt)/R + v_max·Δt/R + 0,5°;
- η_max e v_max sono i massimi sulla griglia dei parametri (η = 466,8 km²/s; D_u = 0,041 km/s, v_max = D_u·max_λ sin λ
  cos^p λ); il massimo di |ω − ω_C| è sulle latitudini della patch. Conversioni: η in km²/s → cm²/s (× 10¹⁰), distanze
  divise per R in cm → radianti → gradi (× 180/π); Δt in secondi (TAI).
- Erosione: una cella resta in C se la distanza in latitudine dal bordo nord e sud della patch iniziale è almeno m_λ e
  quella in longitudine, misurata lungo il parallelo come differenza circolare in gradi, dai bordi est e ovest è almeno
  m_φ. Bordi della patch dall'impronta in Carrington della griglia CEA (WCS completa).
- **Un solo C per caso**, comune a tutti i modelli (SFT, persistenza, sola rotazione) e a tutti i trasporti. Il dominio
  di simulazione e la prova di bordo coprono il caso del margine massimo.
- Il margine è **operativo**, non un limite rigoroso del contributo del campo fuori dalla patch: la diffusione non ha
  supporto finito. Allargare un dominio riempito di zeri verifica il bordo numerico, non ricostruisce il campo solare
  mancante; questo resta un limite dichiarato del confronto.
- Area di C come angolo solido, Σ dA/R² · (180/π)² deg². Con area nulla o minore di 25 deg² (soglia operativa di
  copertura, non fisica) il caso ha lo stato «non valutabile», senza sostituzioni. Si registrano l'area di C, la
  frazione dell'area della patch iniziale e il flusso iniziale fuori da C.

**Osservabili integrali su C, senza soglia** (principale):
- D_C = 3/(4πR²) Σ B_r sin λ dA;
- flussi Φ₊, Φ₋ e flusso netto;
- centroidi delle polarità (media dei vettori unitari pesata con |Br|, rinormalizzata), separazione, tilt (convenzione
  P1), latitudine media.

**Misure supplementari:**
- le stesse osservabili con il taglio |Br| ≥ 100 G su C, sapendo che dopo il trasporto la soglia può da sola rimuovere
  flusso e cambiare D;
- misure «come P1» sulle bitmap proprie di t₀ e t₁ (`measure.py`): confronto fra prodotti di catalogo, distinto dal
  confronto a supporto fisso;
- correlazione di Br fra previsto e osservato su C, solo come diagnostica: pesi d'area, celle finite su entrambi i
  lati; con varianza nulla, non definita.

**Maschera advettata (diagnostica).** Indicatore materiale della bitmap iniziale (≥ 33), trasportato per preimmagine
con la sola rotazione differenziale e il flusso meridiano, senza diffusione: ogni cella a t₁ è suddivisa in 4 × 4
sottopunti; ciascun sottopunto si riporta indietro a t₀ integrando φ̇ = ω(λ) − ω_C e λ̇ = v(λ)/R (Runge–Kutta del quarto
ordine, 100 passi); la cella appartiene alla maschera se almeno 8 dei 16 sottopunti cadono in pixel della bitmap
iniziale. Non è una densità magnetica 0/1 fatta evolvere con il termine compressibile. Il flusso osservato a t₁ fuori
da questa maschera si riporta; non misura la sola nuova emersione, perché anche la diffusione porta flusso fuori.

**Prova d'identità:** a Δt = 0 (t₁ = t₀, stesso file), osservazione e tutte le previsioni coincidono su C con lo stesso
operatore di preparazione e misura.

## 4. Popolazione, campione e separazione sviluppo/verifica

- **Bacino:** HARP con record primario e di controllo distinti, controllo successivo, 1 ≤ T_OBS(controllo) −
  T_OBS(primario) ≤ 4,5 giorni (TAI, intervalli in secondi), stessa HARP, `family_rank` = 0, `valid_bl` = 1 al
  primario. Al controllo non si richiede `valid_bl`: una polarità sola o la scomparsa del segnale sono osservazioni
  informative. Un tilt non definito resta mancante e non diventa mai 0.
- **Fattibilità geometrica (criterio di popolazione, dai soli `keys.json`):** interno di C stimato dalle impronte e
  dal margine del §3 di almeno 25 deg². Le coppie che non lo soddisfano escono dal bacino e si contano per cella. La
  verifica sui pixel finiti si fa dopo, con lo stato «non valutabile».
- **Strati:** Δt (1–3, 3–4,5 giorni; estremi inferiori inclusi) × molteplicità delle associazioni («un NOAA» se
  `NOAA_NUM` = 1, «altro o ignoto» altrimenti, con un flag per NOAA assente): 4 celle, con 24 / 21 / 160 / 131 coppie
  fattibili (stima del §1, su T_REC). Il rapporto
  USFLUX(controllo)/USFLUX(primario) si riporta come covariata continua e con le due classi descrittive del §1, senza
  stratificare. Si riportano separatamente la variabile di selezione USFLUX e il flusso P1 rimisurato: sono quantità
  diverse e nessuna delle due misura soltanto l'emergenza.
- **Numerosità:** 18 per cella, al più 72. Con la stima del §1 la cella più povera ne ha 21. La regola vale comunque:
  una cella con meno di 18 HARP si prende intera.
- **Estrazione:** ordinamento canonico per `HARPNUM`; permutazione `numpy.random.default_rng(36_200_000)`; le prime 18
  per cella. Zona di semi 36 200 000–36 200 999, verificata libera il 25 novembre. Pesi N/n per cella nei riepiloghi della
  popolazione.
- **Separazione sviluppo/verifica, fissata prima di qualsiasi calcolo:**
  1. assegnazione provvisoria: seconda permutazione `default_rng(36_200_001)` delle HARP estratte, per cella; le prime
     ⌊n/3⌋ sono lo sviluppo, le altre la verifica;
  2. grafo delle HARP estratte, con un arco se (a) appartengono alla stessa famiglia P1e, oppure (b) le finestre
     temporali [T_OBS(primario), T_OBS(controllo)] si intersecano **e** le impronte in Carrington delle loro patch a t₀
     si intersecano (longitudini con raccordo 0/360). Patch degli stessi luoghi in anni diversi non sono collegate;
  3. ogni componente connessa va interamente nella parte provvisoria della sua HARP con `HARPNUM` minimo;
  4. la proporzione finale può differire da 1/3 – 2/3: si riportano conteggi per cella, componenti e probabilità di
     assegnazione effettive, senza spostare casi; una cella senza casi di verifica non ha stima.
  HARP diverse non garantiscono l'indipendenza del campo.
  - **Accesso:** i metadati si possono usare per la selezione e gli strati; le mappe a t₁ non si usano per scelte di
    modello o di misura. Lo sviluppo serve solo a controlli d'implementazione (rimappatura, dominio, margine, bordi,
    tolleranze numeriche).
  - Split e impronte si conservano prima dello sviluppo; un registro delle scelte congelate si conserva prima della
    corsa di verifica. La verifica si legge una volta.

## 5. Modello

- **Trasporto 2D locale proprio**, in coordinate di Carrington, su una griglia regolare in longitudine e latitudine
  (passo 0,06°; sensibilità 0,03° e 0,12°):
  ∂B/∂t = −(ω(λ) − ω_C) ∂B/∂φ − (1/(R cos λ)) ∂(v B cos λ)/∂λ + η ∇²_h B,
  con ω(λ) = 14,713 − 2,396 sin²λ − 1,787 sin⁴λ gradi/giorno (la funzione di P1d/P1e) e ω_C = 14,1844 gradi/giorno. Con
  λ = 15° e 4,5 giorni lo spostamento relativo è circa 1,6°; senza sottrarre ω_C sarebbe circa 65°. Senza decadimento.
- **Parametri:** gli stessi del punto 2 (riferimento η = 466,8 km²/s, D_u = 0,025 km/s, p = 2,33) e la stessa griglia
  2 × 2 di sensibilità (η ∈ {350; 466,8}, D_u ∈ {0,025; 0,041}). Il set (350; 0,041) fu scelto in letteratura sul
  ciclo 24 HMI: si dichiara la sovrapposizione temporale. Nessun parametro si migliora sui dati del pilota.
- **Dominio di simulazione:** il riquadro della patch iniziale più 2m_φ per lato in longitudine e 2m_λ in latitudine,
  con i margini massimi del §3; condizione al bordo a flusso nullo. Prova del bordo, separata dalla convergenza:
  allargando il dominio di altri m_φ e m_λ, le osservabili su C cambiano meno di 10⁻⁶ della loro scala (sotto); si
  registra anche il flusso unsigned nella fascia di bordo. Regole di ampliamento e condizioni al bordo fissate ora.
- **Rimappatura** dalle CEA oblique con la WCS completa del `keys.json` (adattatore P1), conservativa nel flusso, con
  orientamento e raccordo 0/360 verificati. Nessun riallineamento dei magnetogrammi che ottimizzi la correlazione.
- **Schema numerico (un solo algoritmo, fissato ora):** volumi finiti con fattori metrici sferici sulla griglia
  uniforme in latitudine e longitudine. Separazione di Strang per ogni passo: mezzo passo di diffusione con
  Crank–Nicolson (operatore a due punti, coefficienti fuori diagonale non negativi), un passo di avvezione con
  ricostruzione TVD minmod e SSP-RK2, mezzo passo di diffusione. Passo Δt = min(600 s, 0,5·CFL dell'avvezione,
  0,9·2/max_i(−L_ii) della diffusione sul mezzo passo), con l'ultimo sottopasso ridotto per arrivare esattamente a t₁;
  il limite di diffusione rende non negativa anche la tappa CN. 600 s è un massimo, non un valore assunto.
- **Convergenza (separata dalla prova del bordo):** passo di griglia 0,06° contro 0,03° e passo temporale dimezzato,
  nei casi sintetici e nei casi di sviluppo. Scale fissate ora: D con D_scale = 3Φ̄₀/(4πR²) del campo iniziale (soglia
  inferiore 10⁻⁶ D_scale); flussi con il flusso unsigned iniziale su C; centroidi e tilt in gradi (differenze circolari
  e assiali); norma L² del campo su C relativa a quella iniziale, così che un momento corretto non nasconda una mappa
  oscillante. Criterio: scarto ≤ 10⁻³ di ciascuna scala; si conservano residui e casi non valutabili. Sono controlli
  numerici, non intervalli osservativi.
- HipFT (Apache-2.0) è un oracolo aggiuntivo se disponibile, non un requisito.

## 6. Riferimenti senza trasporto (obbligatori)

Sullo stesso campo preparato e sullo stesso dominio C:
- **persistenza:** il campo di t₀ invariato;
- **sola rotazione differenziale:** il campo di t₀ spostato in longitudine con ω(λ) − ω_C, senza flusso meridiano né
  diffusione. Sul campo completo e a supporto completo conserva D; su C con il ritaglio non lo garantisce.

Dichiarato prima dei dati: in pochi giorni l'SFT cambia poco D_C, quindi il confronto più informativo riguarda
posizioni, tilt e forma.

## 7. Errori osservativi

- **Ripetibilità osservata:** nei nomi dei file locali Codex ha contato 299 coppie consecutive entro due ore in 296 HARP
  (T_REC nominale). Prima del congelamento si verificano T_OBS, metadati, indipendenza dal campione (le HARP del
  campione sono escluse da questo insieme) e copertura. Se adeguate, le stesse osservabili su C fra i due record
  danno una scala di variazione a breve intervallo. Comprende evoluzione reale: è «ripetibilità osservata», non rumore
  strumentale. Se i casi non sono adeguati, l'errore si dichiara non stimato e il confronto resta relativo ai
  riferimenti.
- La distanza dal meridiano a t₁ si riporta come covariata, non come esclusione.

## 8. Metriche e lettura

**Per regione e per osservabile X:** errori assoluti |e_SFT|, |e_pers|, |e_rot|, con e = X_obs(t₁) − X_mod(t₁), e le
differenze appaiate |e_pers| − |e_SFT| e |e_rot| − |e_SFT|. Il tilt usa differenze assiali, la longitudine differenze
circolari; polarità leading e segno di D si confrontano a parte. Rapporti con errore di persistenza nullo: non definiti,
senza epsilon.

**Per strato e totale (verifica):** mediane e quantili 10–90 % pesati con N/n delle differenze appaiate; frazione di
miglioramenti, pareggi e peggioramenti; associazione descrittiva (Spearman) fra errori e variazione relativa del flusso
(USFLUX e flusso P1 rimisurato, separatamente). Lo sviluppo si riporta a parte e non entra nella lettura.

**Lettura:** soltanto descrittiva, senza soglie di validazione. Un residuo grande in una regione a flusso quasi costante
non dimostra un errore di trasporto: anche con flusso quasi costante possono coesistere emersione e cancellazione. Una
correlazione fra residui e variazione del flusso non misura l'emersione non modellata.

## 9. Che cosa non fa

- Non valida il modello sui tempi del dipolo globale né il campo polare.
- Non usa le mappe future per scelte di modello o di misura e non le assimila.
- Non modella emersione, sommersione, velocità locali reali o campo fuori dalla patch iniziale.
- Non scarica dati; un eventuale bisogno di record a cadenza più fitta, o di un endpoint indipendente dal massimo di
  flusso (per esempio vicino a t₀ + 2 giorni), richiede una selezione distinta, dichiarata prima dei pixel e
  autorizzata a parte.
- Non modifica P1; nessun nuovo T3 o T5 e nessun verdetto sul quenching.

## 10. Estensione distinta

Il controllo del dipolo globale con le sinottiche HMI polfil locali (CR 2097–2312) richiede tutte le sorgenti, il
trattamento del polar filling e della composizione temporale: protocollo separato, dopo i due piloti.

## 11. Prove e sequenza

1. Controllo finale di Codex e congelamento: semi, estrazione, assegnazione sviluppo/verifica, impronte degli input,
   prima di leggere qualunque mappa del campione.
2. Codice: rimappatura, dominio comune e margine, solutore 2D, riferimenti, misure.
3. Prove sintetiche (Codex):
   - identità a Δt = 0;
   - traslazione dovuta alla sola rotazione differenziale (posizione analitica, sistema di Carrington);
   - diffusione di una gaussiana come limite locale, con errore di curvatura controllato, oppure modi armonici
     sferici con decadimento noto;
   - conservazione del flusso e prova del bordo con ampliamento del dominio;
   - segni, orientamento, raccordo 0/360 e WCS obliqua.
4. Corsa sullo sviluppo e rapporto tecnico; congelamento del registro delle scelte; corsa unica sulla verifica;
   conservazione prima della lettura; riconteggio indipendente; rapporto descrittivo distinto da quello del punto 2.

## 12. Punti aperti

1. **Revisione del disegno da confermare (§1, §3, §4):** margine direzionale al posto di quello isotropo, criterio di
   fattibilità geometrica dai `keys.json` nella popolazione, e Δt su due strati (1–3, 3–4,5 giorni). Con il margine
   isotropo della revisione 2 le celle a 1–3 giorni avrebbero 5–8 coppie fattibili. Alternative calcolate sugli stessi
   metadati: margine diffusivo √(2ηΔt) (420 coppie) oppure soglia di 10 deg² (458); non le propongo, perché
   allentano il controllo del campo esterno.
2. Gli altri punti della revisione 2 (margine, maschera advettata, schema 2D e convergenza, split) sono chiusi secondo
   e87fff7.

## 13. Modifiche

**Dalla revisione 2 (790cad1), dopo e87fff7:**
- §3: margine direzionale sul massimo della griglia dei parametri, conversioni scritte, un solo C per caso; margine
  dichiarato operativo; area come angolo solido; erosione definita.
- §1, §4: fattibilità geometrica dai `keys.json` (207 coppie con il margine isotropo, 336 con quello direzionale);
  criterio di popolazione; Δt su due strati; 4 celle, al più 72; correzione editoriale dei conteggi per cella (66, 72,
  84, 75, 447, 279).
- §3: maschera advettata per preimmagine dei sottopunti (indicatore materiale).
- §4: split per componenti connesse di un grafo con archi di famiglia o di sovrapposizione nello spazio e nel tempo.
- §5: schema di Strang con CN a passo limitato per la positività e avvezione TVD minmod + SSP-RK2; 600 s come massimo;
  convergenza con scale per osservabile e norma L² del campo, separata dalla prova del bordo.

**Dalla revisione 1 (e0bba64):**

- A1: tolto lo strato «flusso in calo», impossibile con il controllo al massimo; tabella delle celle dai soli metadati;
  6 celle Δt × molteplicità, con il rapporto di USFLUX come covariata.
- A2: principale sulla mappa grezza; bilanciamento solo come sensibilità coerente su t₀ e t₁; tolta la giustificazione
  sul monopolo locale.
- A3: dominio comune con margine; osservabili integrali senza soglia; misure come P1 e taglio a 100 G come supplementi;
  maschera advettata definita; prova d'identità; inizializzazione con tutti i pixel finiti e sorgente P1 come
  alternativa.
- A4: domanda e lettura riformulate come associazione, senza attribuzioni causali.
- A5: rotazione in Carrington (ω − ω_C), dominio con margine e prova del bordo per ampliamento, WCS completa.
- B: parametri comuni con il punto 2. C1–C8 recepiti: niente `valid_bl` richiesto al controllo; famiglie e patch
  sovrapposte dalla stessa parte; differenze appaiate; regola d'accesso ai dati futuri.

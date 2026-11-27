# Pilota SFT mappa–bipolo — emendamento A1 (numerico): BOZZA

Stato: **bozza per la revisione di Codex**, 25 novembre 2026 (Claude). Emenda il §6 (e il §10, punto 3) del protocollo
congelato `docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT.md` (SHA 380b7982…, ricevuta e2e7176), che resta intatto. Richiesto dalla
revisione di Codex `docs/SFT_Q4_EVENING_REVIEW_20261125.md` (aaf3d6f), §1–§2. Non autorizza corse.

## 0. Perché e che cosa è già noto (non cieco)

- Il §6 congelato fissa l'avvezione **upwind del primo ordine** e un criterio di convergenza:
  |D_fine − D_coarse| ≤ 10⁻³·max(|D_fine|, 10⁻⁶ D_scale), con il raddoppio della risoluzione se fallisce.
- **Prove sintetiche già viste** (codice preparatorio, nessuna mappa osservata). Con l'upwind puro a N = 400 lo scarto
  N 400 → 800 su un bipolo puntiforme sintetico arriva a 5,4·10⁻³, sopra la soglia. Con lo schema ibrido sotto arriva a
  6,5·10⁻⁴, sotto la soglia, con le stesse garanzie di positività e conservazione della massa.
- L'emendamento è quindi una scelta numerica fatta **dopo** prove sintetiche e **prima** di qualunque mappa osservata
  del campione. Lo schema ibrido non allenta soglie; la soglia minima del criterio di convergenza invece si allenta
  (§2bis), come seconda modifica numerica distinta e dichiarata.
- Alternativa equivalente secondo il testo congelato: tenere l'upwind e raddoppiare la risoluzione (N = 800 o più)
  fino al rispetto del criterio. Si preferisce l'ibrido perché a parità di N riduce l'errore di discretizzazione
  dell'avvezione nei punti in cui domina la diffusione, cioè quasi ovunque con i parametri del pilota.

## 1. Testo che sostituisce, nel §6, la riga «flussi diffusivi a due punti e avvezione upwind del primo ordine»

Volumi finiti su N celle uniformi in s ∈ [−1, 1], centri s_j, facce s_f. Per ogni faccia interna:
- conduttanza diffusiva d_f = (η/R²)(1 − s_f²)/Δs;
- tasso avvettivo a_f = v(arcsin s_f)·√(1 − s_f²)/R, con v(λ) = D_u sin λ cos^p λ;
- **regola ibrida (Patankar), coefficienti esatti:**
  - se 2·d_f ≥ |a_f| (numero di Péclet di cella ≤ 2): faccia centrata, c_L,f = c_R,f = a_f/2;
  - altrimenti: faccia upwind del primo ordine, c_L,f = max(a_f, 0), c_R,f = min(a_f, 0);
- flusso di faccia G_f = d_f (b_R − b_L) − (c_L,f b_L + c_R,f b_R); facce polari a flusso nullo (d = a = 0);
- db_j/dt = (G_{j+1/2} − G_{j−1/2})/Δs.

In entrambi i rami i coefficienti fuori diagonale d_f − c_R,f e d_f + c_L,f sono non negativi e le colonne del generatore
L hanno somma nulla: positività e conservazione della massa sono le stesse dell'upwind. Il codice registra la frazione
di facce centrate.

Restano invariati:
- il passo di Crank–Nicolson Δt = min(1 giorno, 0,9·2/max_i(−L_ii)), con il sottopasso finale ridotto ai tempi di
  uscita;
- i parametri e la griglia 2 × 2 di trasporto;
- τ applicato come fattore exp(−t/τ);
- il deposito lineare in s e lo stato `deposition_out_of_range`.

## 2. Convergenza come requisito (sostituisce il paragrafo «Convergenza» del §6 e completa il §10, punto 4)

1. **Controllo preliminare sintetico, sul codice effettivo della corsa, prima di leggere qualunque mappa del campione.**
   - Casi: bipoli puntiformi bilanciati centrati a |λ| = 5°, 15°, 30° e 60° (separazione 2°, tilt 10°), le gaussiane
     della sensibilità di forma con σ = 2° e 4° sugli stessi centri, impulsi in una sola cella.
   - Tutti e quattro i trasporti della griglia; tutti i tempi del §7.
   - Raffinamenti: N 400 → 800 e passo dimezzato, separatamente. Il passo dimezzato è la metà del passo effettivo,
     ½·min(1 giorno, 0,9·2/max_i(−L_ii)), a ogni N, anche quando il limite non è attivo. La stessa regola vale nel §2ter.
   - Criterio: |D_fine − D_coarse| ≤ 10⁻³·max(|D_fine|, f·D_scale), con **f = 10⁻²** al posto di 10⁻⁶ (vedi §2bis:
     è un allentamento della soglia minima, dichiarato e deciso dalla revisione).
   - Positività: nessun valore sotto −10⁻¹²·max sugli impulsi e su ciascuna polarità da sola. Massa entro 10⁻¹²·Σ|F|.
   - Un caso il cui deposito esce dal supporto (a N o a 2N) si registra con lo stato `deposition_out_of_range` e resta
     fuori dal requisito, come nella corsa osservata. Con questi centri accade solo per la gaussiana σ = 4° a 60°, il cui
     cappuccio di 8σ = 32° oltrepassa il polo (verificato sul codice, nessuna mappa letta).
2. **Regola di raffinamento.** Se il criterio fallisce in un caso qualsiasi, N raddoppia (800, poi 1600) e il controllo
   preliminare si ripete per intero. Il primo N che lo supera vale per **tutte** le rappresentazioni e tutti i
   trasporti della corsa. Se nemmeno N = 1600 lo supera, la corsa si ferma con un arresto tecnico e nessun prodotto
   scientifico.
3. **Tre casi osservati (verifica della regola, non scelta).** Sono le prime tre regioni del campione, in ordine di
   permutazione, con stato `ok` e deposito riuscito sia per M sia per il bipolo puntiforme. Per ciascuna si eseguono i
   due raffinamenti, con tutti i trasporti e i tempi, per M e per il bipolo puntiforme.
   - Se un criterio fallisce, la corsa riporta lo stato numerico `convergence_failed`: i prodotti si conservano per
     diagnosi, ma la corsa **non è valida** e il riconteggio non può emettere una ricevuta completa.
   - Con meno di tre regioni utilizzabili si usano quelle disponibili e lo si dichiara. Con nessuna, la corsa non è
     valida.
4. Gli scarti numerici di tutti i casi (sintetici e osservati) si conservano in prodotti dedicati (PREFLIGHT.csv e
   CONVERGENCE.csv, con D_ref e D_fine). Il riconteggio verifica sia l'uguaglianza dei valori sia il rispetto del
   requisito.

## 2bis. Soglia minima del criterio (punto da decidere nella revisione; non cieco rispetto a dati sintetici)

**Che cosa si è visto** (codice effettivo; solo casi sintetici e patch sintetiche del selftest, nessuna mappa osservata):
- Con il criterio del padre, 10⁻³·max(|D_fine|, 10⁻⁶ D_scale):
  - il preflight a N 400 fallisce su 12 righe, tutte bipoli puntiformi a 3 anni o vicini a zero (massimo 4,1·10⁻³);
  - a N 800 passa ogni caso (massimo 4,4·10⁻⁴).
- Sulle patch sintetiche del selftest, il bipolo puntiforme di una regione fallisce a 3 anni con flusso
  D_u = 0,041 km/s:
  - N 400 → 800: 1,4·10⁻³;
  - N 800 → 1600: 7,4·10⁻³.
- In quella regione D(3 anni) vale lo 0,4 % di D_scale; in un'altra, con le polarità a 0,11° di latitudine, lo 0,07 %.
- Gli scarti assoluti restano ≤ 1,6·10⁻⁵ D_scale a N 400 e ≤ 1·10⁻⁵ D_scale a N 800.
- **Causa.** Il bipolo puntiforme è fatto di due delta non risolte dalla griglia. Lo scarto con N oscilla secondo la
  posizione delle delta rispetto ai centri cella e cala lentamente: per lo stesso caso, N 3200 contro 1600 dà ancora
  1,5·10⁻³. Quando D si avvicina a zero, il criterio relativo non si è raggiunto alle risoluzioni provate. Questo
  indica una difficoltà numerica in quei casi: non prova che sia irraggiungibile a ogni N, né esclude da solo un
  errore del codice.
  La rappresentazione M converge regolarmente, al secondo ordine (2,5·10⁻⁴ → 6,5·10⁻⁵).

**Proposta.**
- Soglia minima f = 10⁻²: lo scarto deve stare sotto 10⁻³ in relativo quando |D| ≥ 1 % di D_scale, e sotto 10⁻⁵ D_scale
  in assoluto quando |D| è più piccolo.
- Questo **non** garantisce l'accuratezza dei rapporti: il denominatore 0,1·m(t) è comune, mentre D_scale è della
  regione. Il controesempio algebrico di Codex mostra un rapporto che cambia di 0,45 con f = 10⁻². Per questo la
  risoluzione dei rapporti e dei segni si verifica regione per regione (§2ter).
- Lo stesso f vale per il preflight e per i casi osservati. Il riconteggio lo applica identico.

**Alternative.**
- (a) Tenere 10⁻⁶. La corsa reale rischia `convergence_failed` per ragioni di quasi-cancellazione, non di accuratezza.
- (b) f = 10⁻¹: soglia assoluta 10⁻⁴ D_scale, più robusta ma meno severa sui rapporti vicino alla soglia.
- (c) Ripetere il controllo osservato a 2N prima di dichiarare il fallimento. Per le delta non aiuta: lo scarto non
  cala con N.

**Margine (va pesato nella decisione).**
- Il massimo scarto assoluto del preflight a N 800 è 9,8·10⁻⁶ D_scale: il 98 % della soglia assoluta con f = 10⁻², il
  10 % con f = 10⁻¹.
- Sulle patch sintetiche a N 800 gli scarti del bipolo puntiforme arrivano a 5,5·10⁻⁶ D_scale.
- Con f = 10⁻² la corsa reale può quindi cadere in `convergence_failed` per poco.
- Con f = 10⁻¹ l'errore ammesso vicino alla soglia dei rapporti è più largo, ma quello effettivo resta quello misurato e
  registrato in CONVERGENCE.csv.
- Decisione proposta da Codex (459f141): f = 10⁻², dichiarato come tolleranza assoluta 10⁻⁵ D_scale sullo scarto fra
  griglie, insieme alla regola del §2ter; non 10⁻¹. Il codice lo tiene nella costante `CONV_FLOOR`, identica nel
  runner e nel riconteggio.

**Conseguenza sull'N.** Con f = 10⁻² il preflight passa a N 800, non a 400. Il pilota gira quindi a N 800 per tutte le
rappresentazioni e i trasporti, come prevede la regola del punto 2.

## 2ter. Rapporti e segni: risoluzione numerica per regione (rev. dopo la revisione Codex 459f141)

Lo scarto fra due griglie è un **indicatore di sensibilità numerica**, non un errore garantito rispetto alla
soluzione esatta. Nessuna quantità qui sotto è un bound dimostrato.

**Griglie.** Per ogni regione, soglia, rappresentazione, trasporto e tempo che entrano nei riepiloghi si calcola D
su quattro livelli:
- N (quello della corsa);
- 2N;
- 4N;
- N con passo dimezzato.

Il costo resta basso grazie al problema aggiunto, che dà i pesi g_t con D(t) = g_t·b₀ per ogni griglia e trasporto.
È una scelta di calcolo e non cambia la regola. I fattori τ si applicano a tutti i livelli. D a 2N, 4N e passo
dimezzato si conservano in DIPOLES.

**Rapporti.**
- A ogni livello si ricalcolano m(t) e la soglia 0,1·m(t), con la stessa popolazione e definizione (M a 100 G,
  trasporto di riferimento, pesi N/n), e poi l'ammissibilità |D_M| ≥ 0,1·m(t).
- Stato `below_ratio_threshold`: non ammissibile a tutti i livelli.
- Stato `ratio_resolved`: ammissibile a tutti i livelli e |r_2N − r_N|, |r_4N − r_2N| e |r_N,dt/2 − r_N| tutti ≤ 0,01.
- Stato `ratio_unresolved` negli altri casi, compreso quello in cui l'ammissibilità cambia fra i livelli.
- I quantili dei rapporti usano solo i risolti. Ogni riga della sintesi riporta n_below_ratio_threshold,
  n_ratio_unresolved e n_ratio_resolved, con le quote pesate.
- La regione resta in D, dD/D_scale e nei denominatori di selezione.
- 0,01 è una soglia sullo scarto fra griglie, non un errore assoluto.

**Indicatore per dD/D_scale.** Per ogni riga, max sui livelli di |dD_livello − dD_N|/D_scale, riportato nella
sintesi (mediana pesata e massimo). È un indicatore, non un errore garantito.

**Segni a 3 anni.**
- Stato `sign_unresolved` se il segno di D_B o di D_M cambia fra i livelli.
- La frazione di segni concordi usa solo i risolti; si riporta n_sign_unresolved.

**Per completezza del testo.** Se si avessero veri bound |δM| ≤ e_M e |δB| ≤ e_B con |M| > e_M, varrebbe
|δr| ≤ [e_B + e_M(1+|r|)]/(|M| − e_M), e il rapporto sarebbe non risolto se |M| ≤ e_M. Qui non si dispone di quei
bound: la formula non si applica come garanzia.

**Che cosa resta invariato.**
- Il requisito globale di convergenza (preflight e tre regioni osservate, §2) resta bloccante.
- La non risoluzione di singoli rapporti o segni è uno stato distinto e non invalida la corsa.
- f resta 10⁻², dichiarato come tolleranza assoluta 10⁻⁵ D_scale sullo scarto fra griglie del criterio globale.
- f non si sceglie guardando i risultati osservati.
- Una cella può restare senza quantile dei rapporti.

## 3. Che cosa non cambia

Domanda, campione, rappresentazioni M e B, sensibilità, tempi e lettura del protocollo padre. Ai prodotti si aggiungono
PREFLIGHT, DENOMINATORS e MANIFEST. L'unica soglia toccata è la soglia minima del criterio di convergenza (§2bis),
dichiarata. Nessuna scelta si fa guardando i dipoli osservati.

## 4. Congelamento

Ricevuta con: SHA di questo testo, del protocollo padre e della sua ricevuta, e del codice di trasporto
(`python/sharpbl/sft_core.py`) al commit di congelamento; commit di congelamento; dichiarazione «non cieco rispetto alle
prove sintetiche dell'upwind».

# T5 — sensibilità del proxy del dipolo a uno spostamento prescritto della legge di Joy: nota metodologica

Stato: **congelata il 2026-11-15, prima di scrivere il codice ed eseguire**, dopo due revisioni di Codex
(contenuto proposto; bozza `5c65f53`), le cui correzioni sono recepite. Non è un protocollo inferenziale e
non contiene risultati. Segue la
[nota di fattibilità](T5_FEASIBILITY_NOTE_DRAFT.md) (revisione 2) e le revisioni di Codex dei «prossimi
passi» e del «contenuto proposto», le cui indicazioni sono recepite qui. Non cieca: le potenze esistenti
(validazione P2f, T5-D2) sono note.

## 1. Bersaglio e domanda

**Bersaglio:** il dipolo misurato al record selezionato vicino al meridiano centrale. Non coincide
necessariamente con l'emersione e può includere evoluzione e afflussi già avvenuti. Il contributo finale
al dipolo polare è un bersaglio diverso, escluso.

**Domanda di questa analisi.** Se la componente di Joy del tilt si riducesse con l'attività secondo lo
scenario prescritto (§4), quale pendenza Δβ produrrebbe, nelle unità di T5, sulla geometria del catalogo
fissato? È un'**analisi di sensibilità deterministica, non cieca, condizionata al catalogo e a un proxy a
coppia compatta**. Non è un test, non stima il quenching solare, non è una dimostrazione di quenching né
un test definitivo di fattibilità. Un'associazione con l'attività non identificherebbe da sola il quenching
del tilt o un meccanismo di saturazione.

## 2. Popolazione e disegno (fissati)

- Catalogo `results/P1/P1_SBL_CATALOG_BY_HARP.csv` al commit di esecuzione.
- Campione `S` di `run_p2.samples` e costruzione di `p2d.design_t5`:
  - celle (CR, emisfero) con almeno 3 regioni;
  - 2375 record in 318 celle (numerosità attese, verificate in esecuzione);
  - ciclo della cella pari a quello di flusso massimo;
  - Â_cella = media semplice di A_monthly sulle regioni della cella.
- Regressione T5: η_c = Σd*/ΣΦ per cella, pesi W_c = ΣΦ della cella, colonne degli intercetti
  ciclo-emisfero (`run_p2.ch_columns`) più (Â_cella − 1). La riga della pendenza è
  g = `p2d.wls_row(Xf_c, W_c)`.
- Nessun record escluso dopo aver visto gli effetti.

## 3. Proxy normalizzato e orientato (coppia compatta)

Dalla misura v84 (`measure.py`): D_bal = [3/(8πR²)]·Φ·(⟨sin λ⟩₊ − ⟨sin λ⟩₋), in G, con medie pesate per
|Br| e R = `RSUN_REF` dell'header. D* = S_CYCLE·D_bal, con S_CYCLE = {24: +1, 25: −1}.

Proxy per il record i, in G:

  P*_i(γ) = hale_i · C · Φ_i · cos λ_i · (d_i/R) · sin γ_i,  con C = 3/(8πR²).

- γ_i = sign(lat_i)·degrees(arcsin(sintilt_i)) è la variabile di Joy di `run_p2.prepare`, emisferica.
  sin γ si calcola in radianti.
- **Orientamento.** Con le convenzioni attuali (`S_CYCLE`, `expected_leading_sign`), nei cicli 24 e 25
  vale −s_ciclo·L_i·h_i = hale_i, con L il segno della leading e h = sign(lat). Quindi P* ha
  l'orientamento di D*.
- **Colonne:** `hale_sign`, `phi_mx`, `lat_mean_deg` (λ), `d_cm` (d), `sintilt`, `cycle`.
- **Raggio.** Il catalogo non contiene R. Si usa R = 6,96e10 cm (`geometry.RSUN_CM_DEFAULT`, valore
  nominale di `RSUN_REF` delle SHARP), dichiarato come ipotesi: il catalogo non registra per ogni record il
  valore dell'header.
  - A catalogo fissato (Φ_i e d_cm_i salvati), P* = hale_i·[3/(8π)]·Φ_i·cos λ_i·d_cm_i·sin γ_i / R³.
    Sostituire R con R(1 + ε) moltiplica P*, ΔD, Δβ ed e_ref (con ETA_BAR fisso) per (1 + ε)⁻³ ≈ 1 − 3ε.
  - Rispetto al raggio dell'header di ciascun record vale P*(R_nominale)/P*(R_header,i) = (R_header,i/R_nominale)³.
    Se i raggi differissero fra record, non sarebbe un unico fattore comune: pendenze e confronti aggregati
    potrebbero cambiare.
  - Diverso è ricalcolare la misura da una stessa mappa con un altro raggio: Φ scala come R² e d_cm come R,
    e nel proxy questi fattori cancellano R⁻³. Questa nota usa le colonne salvate, senza ricalcolare.
- **Latitudine nulla.** Se lat_i = 0, sign = 0 e quindi γ_i = 0 come in `run_p2`; poiché anche
  μ_i = γ0·sin|lat_i| = 0, ne seguono P*_i = 0 e ΔD_i = 0. È una convenzione degenere da contare e
  riportare, senza escludere il record. Non afferma che il dipolo fisico sia nullo: per esempio due
  polarità di flusso uguale a ±θ hanno latitudine media 0 ma D_bal ≠ 0. L'identità −s_ciclo·L·h = hale
  vale solo per h = ±1.
- **Natura del proxy.** P* è un'approssimazione di coppia compatta, non una nuova definizione del D_bal
  misurato e non il suo ricalcolo esatto. Anche un buon accordo al livello osservato non dimostra che la
  sua derivata rispetto al tilt sia quella del vero D_bal.

## 4. Scenario (uno solo, additivo nella variabile γ)

- μ_i = γ0·sin|λ_i|, con γ0 = 24° (`p2f_pilot.GAMMA0`). È il riferimento P2f, coerente con il
  coefficiente di Joy circa 24,1° del controllo P2 T1 sugli stessi dati reali: non è una stima fisica
  indipendente e non viene ristimato.
- γ'_i = γ_i − δ(Â_c)·μ_i.
- δ(Â_c) = δ_max · clip((Â_c − A_lo)/(A_hi − A_lo), 0, 1): rampa limitata a entrambi gli estremi.
- A_lo e A_hi sono i quantili 0,05 e 0,95 di Â_cella replicata sui 2375 record T5, con peso unitario per
  record e `numpy.quantile` lineare (default). Si calcolano in esecuzione e si registrano a precisione
  piena. Valori già noti dalla revisione: circa 0,502 e 2,760.
- δ_max ∈ {0,10; 0,20}: due ampiezze illustrative di sensibilità, senza motivazione fisica specifica per
  questo bersaglio.
- **Cosa conserva.** γ'_i − (1 − δ)·μ_i = γ_i − μ_i: lo scarto individuale dal riferimento prescritto
  resta invariato. **Non** si afferma che la dispersione marginale del catalogo resti invariata.
- Perturbazione prescritta alla scala CR-emisfero: non dimostra che l'attività di cella sia la causa fisica
  del tilt.
- Nessuno scenario moltiplicativo e nessuno scenario aggiunto dopo l'esito.

## 5. Grandezze calcolate (una sola esecuzione)

- ΔD_i = P*_i(γ'_i) − P*_i(γ_i), come differenza diretta dei seni: nessun rapporto, nessuna singolarità.
- Δη_c = Σ_i ΔD_i / Σ_i Φ_i (stessa aggregazione di η_c).
- Δβ = g · Δη (G/Mx per unità di Â).
- e_ref = Δβ / ETA_BAR, con ETA_BAR = 3,56e-25 G/Mx, la scala delle simulazioni P2f e T5-D2.
- **Residuo di proiezione.** Si stima per WLS (pesi W_c) Δη sul modello completo Xf_c, cioè intercetti
  ciclo-emisfero più (Â − 1), e si prende il residuo r_c. Si riportano:
  - RMS_W(r) = sqrt(Σ W_c r_c² / Σ W_c);
  - il rapporto RMS_W(r)/RMS_W(Δη − media pesata di Δη); con denominatore nullo si riporta NA con il
    motivo, non inf. Dal rapporto non si ricava nessuna soglia di decisione.
- **Conteggi:**
  - attraversamenti dello zero di γ (sign γ' ≠ sign γ) e casi con |γ'| > 90°;
  - numero di ΔD positivi, negativi e nulli;
  - veri cambi di segno del proxy (sign P*(γ') ≠ sign P*(γ)), con gli zeri contati a parte.
  Sono conseguenze attese dello scenario: non si correggono e non si confondono con errori di convenzione.
- **Qualità del proxy, solo descrittiva**, al livello osservato e con grandezze orientate nelle stesse
  unità (G per record, G/Mx per cella):
  - **per record**, pesi uniformi: correlazione di Pearson fra P*_i(γ_i) e d*_i; RMS di (P*_i − d*_i)
    in G; mediana di P*_i/d*_i sui record con d*_i ≠ 0, con il numero di record con d*_i = 0 riportato a
    parte (nessun ε e nessuna esclusione di valori piccoli); frazione di segni concordi, con gli zeri a
    parte;
  - **per cella**, pesi W_c: correlazione di Pearson pesata e RMS pesata della differenza fra
    ΣP*/ΣΦ e η_c, in G/Mx.

## 6. Controlli

**6.1 Selftest sintetici, senza dati reali, prima dell'esecuzione:**
- lat ≠ 0: il segno di P* coincide con quello di S_CYCLE·D_bal di una coppia compatta costruita a mano,
  per nord e sud, ciclo 24 e 25, Hale e anti-Hale, tilt nullo;
- lat = 0: γ, P* e ΔD sono nulli secondo la convenzione del §3, senza pretendere di riprodurre un D_bal
  fisico non nullo;
- ΔD esatto in casi calcolati a mano;
- rampa δ ai bordi e fuori intervallo; Δβ = 0 per δ_max = 0;
- proiezione: g·Xf_c uguale al vettore che seleziona la colonna dell'attività (rango pieno), e g·y uguale
  alla pendenza di una soluzione WLS separata, su risposte sintetiche note; stesso controllo per il
  residuo di proiezione;
- valori non finiti (NaN, inf) trattati come errori tecnici, mai come controlli superati.

**6.2 Controlli tecnici in esecuzione, sul catalogo, senza usare l'attività:**
- identità P*_i(γ_i) = 3·s_star_i/(8πR³), con s_star = sign(lat)·s_bl di `run_p2.prepare`. La tolleranza
  è relativa alla scala del singolo record: |differenza| ≤ 1e-12·max(|P*_i|, |3 s_star_i/(8πR³)|), con
  uguaglianza esatta richiesta quando entrambi sono 0. È un controllo delle formule derivate da s_bl, non
  una validazione indipendente dell'approssimazione rispetto a D_bal;
- numerosità attese (2375 record, 318 celle): una differenza è un errore da risolvere, non un cambiamento
  silenzioso del campione.

La pendenza reale g·η_c **non** si calcola.

## 7. Uscite e limiti

- Una tabella con:
  - per δ_max: Δβ, e_ref, RMS_W(r), rapporto del residuo e conteggi;
  - A_lo, A_hi, R, numerosità e qualità del proxy.
- Una figura opzionale: Δη_c contro Â_c.
- **Confronto con le potenze** (validazione P2f, T5-D2): **solo contesto**. Stessa proiezione e_ref non
  significa stessa distribuzione di segnale e residui del generatore lineare. Nessuna nuova probabilità di
  rilevazione per questi scenari, nessuna interpolazione. M nello scenario 7 non supera i criteri; gli
  oracoli sono diagnosi.
- **Nessuna regola automatica di decisione.** Dopo l'esecuzione si valuta esplicitamente se progettare il
  passo sulla potenza o rinviare per priorità; resta ammesso un esito non conclusivo.
- **Limiti:**
  - catalogo fissato: niente cambi di evoluzione, selezione, istante del record o rilevabilità;
  - covariazioni osservate fra γ, d e Φ mantenute;
  - proxy a coppia compatta; R nominale;
  - γ0 dal riferimento P2f;
  - ampiezze illustrative.

## 8. Esecuzione

Script `scripts/t5_proxy_sensitivity.py`, scritto dopo il congelamento di questa nota e rivisto rispetto
a essa. Prima i selftest (§6.1), poi una sola esecuzione su commit pulito, con i controlli del §6.2. Uscite
in `results/T5_PROXY_SENSITIVITY/`. Si registrano:
- commit;
- SHA-256 di nota, script e catalogo effettivamente letto;
- definizioni e fonte del disegno;
- numerosità ottenute.
Nessuna simulazione, nessun fit sui dati oltre alla proiezione WLS di Δη, nessuna pendenza reale, nessun
push senza richiesta.

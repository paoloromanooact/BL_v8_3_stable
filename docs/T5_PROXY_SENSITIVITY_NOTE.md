# T5 — sensibilità del proxy del dipolo a uno spostamento prescritto della legge di Joy: nota metodologica

Stato: **bozza del 2026-11-15, da rivedere (Codex) e congelare prima di scrivere il codice ed eseguire.**
Non è un protocollo inferenziale e non contiene risultati. Segue la
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
  - Se R dell'header coincide con quello nominale, P* è esatto rispetto a questa definizione.
  - Se differisse di un fattore (1 + ε), d_cm/R cambierebbe di +ε e C di circa −2ε, quindi P* e Δβ
    cambierebbero di circa −ε in proporzione, senza cambiare segni o confronti relativi.
- **Latitudine nulla.** Se lat_i = 0, sign = 0 e quindi γ_i = 0 come in `run_p2`. Il caso si conta e si
  riporta, senza escluderlo.
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
  - il rapporto RMS_W(r)/RMS_W(Δη − media pesata di Δη), se il denominatore non è nullo.
- **Conteggi:**
  - attraversamenti dello zero di γ (sign γ' ≠ sign γ) e casi con |γ'| > 90°;
  - cambi di segno di ΔD dovuti allo scenario. Sono attesi; non si correggono e non si confondono con
    errori di convenzione.
- **Qualità del proxy, solo descrittiva**, al livello osservato e con grandezze orientate nelle stesse
  unità:
  - P*_i(γ_i) contro d*_i: correlazione, rapporto mediano, scarto;
  - Σ P*/ΣΦ contro η_c per cella;
  - frazione di record con segno concorde.

## 6. Controlli prima dell'esecuzione (selftest, nessun dato reale)

- Algebra del proxy su configurazioni sintetiche: nord e sud, ciclo 24 e 25, Hale e anti-Hale, tilt nullo,
  latitudine nulla. Il segno di P* deve coincidere con quello di S_CYCLE·D_bal di una coppia compatta
  costruita a mano. La differenza ΔD deve essere esatta in casi calcolati a mano.
- Identità sul catalogo, senza usare l'attività: P*_i(γ_i) = 3·s_star_i/(8πR³), dove
  s_star = sign(lat)·s_bl di `run_p2.prepare`. Uguaglianza entro la precisione di macchina.
- g riprodotto: g·η_c deve dare la pendenza T5 di `p2d.design_t5` sui dati del campione. È un controllo di
  coerenza tecnica; il valore si registra ma non si legge come risultato.
- Rampa δ ai bordi e fuori intervallo; Δβ = 0 per δ_max = 0.

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

Script `scripts/t5_proxy_sensitivity.py`, scritto dopo il congelamento di questa nota. Prima il selftest
(§6), poi una sola esecuzione su commit pulito. Uscite in `results/T5_PROXY_SENSITIVITY/`, con SHA-256 di
nota, script e catalogo. Nessuna simulazione, nessun fit sui dati oltre alla proiezione WLS di Δη,
nessun push senza richiesta.

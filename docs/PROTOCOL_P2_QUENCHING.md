# Protocollo P2 — Test osservativi del quenching Babcock–Leighton (v8.4)

Stato: **congelato il 2026-11-03** (commit), **prima** di calcolare
la serie P1. Dopo il congelamento questo file non si modifica: ogni
cambiamento richiede un nuovo protocollo (P2b, …). Lo script che esegue P2
registra lo SHA-256 di questo file e di `PROTOCOL_P1_SBL_SERIES.md` in ogni
output.

## 0. Cosa è già stato visto

- Il caso di prova 2024-05-08 (13 HARP), metodi v8.3 e v8.4.
- I metadati SHARP (posizioni, flusso, QUALITY, numero NOAA) e il numero di
  macchie emisferico SILSO. **Nessun tilt, polarità o S_BL della serie** è
  stato calcolato o guardato quando questo protocollo è stato scritto.

## 1. Domande

Con le sole regioni dell'era HMI (cicli 24 e 25):
- **Q1, quenching del tilt (TQ):** il coefficiente di Joy diminuisce quando
  l'attività è più alta?
- **Q2, quenching in latitudine (LQ):** a parità di fase del ciclo, le
  regioni emergono a latitudini più alte quando l'attività è più alta?
- **Q3, efficienza della sorgente:** il contributo al dipolo per unità di
  flusso emerso diminuisce quando l'attività è più alta?

Con due cicli soli il confronto **tra cicli** ha un solo grado di libertà ed
è riportato come descrittivo. Le decisioni si basano sui test **dentro il
ciclo** (quenching "dinamico"), in cui l'attività varia nel tempo e tra
emisferi.

## 2. Dati e campione

- Catalogo P1 (`P1_SBL_CATALOG_BY_HARP.csv`), metodo v84, record primario.
- **Campione principale (S):** `valid_bl` = 1, Φ ≥ 1·10²¹ Mx, npos ≥ 20 e
  nneg ≥ 20 pixel, `cycle_state` ≠ AMBIGUOUS.
- Sensibilità sul campione (riportate, non decisive):
  - S1: Φ ≥ 5·10²⁰ Mx;
  - S2: Φ ≥ 3·10²¹ Mx;
  - S3: senza le regioni anti-Hale e LARGE_TILT;
  - S4: solo HARP con esattamente una regione NOAA;
  - S5: record di controllo (flusso massimo) al posto del primario;
  - S6: con le regioni AMBIGUOUS;
  - L: metodo legacy (v8.3) sugli stessi record.
- **Attività emisferica A_h(t), indipendente dalle misure SHARP:** numero di
  macchie emisferico mensile SILSO V2.0 (`ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv`,
  SHA-256 nel file `SHA256.txt`) del mese del record e dell'emisfero della
  regione, diviso per la media di A_h su tutto il periodo HMI dello stesso
  emisfero.
  - Sensibilità: A_h media mobile su 13 mesi; somma di USFLUX (metadati) delle
    altre HARP dello stesso emisfero nella stessa CR, esclusa la regione stessa.
- **Fase del ciclo:** φ = (t − t_min) / 11 anni, con t_min = 2008-12 per il
  ciclo 24 e 2019-12 per il ciclo 25.

## 3. Grandezze per regione

- Tilt di Joy: γ = sign(λ) · asin(sin α), in gradi. γ > 0 quando la following
  è più vicina al polo della leading (Joy normale), in entrambi gli emisferi.
- |λ|: latitudine media assoluta.
- Contributo al dipolo con il segno atteso del ciclo:
  D* = s_c · D_bal, con s_c = +1 per il ciclo 24 e −1 per il ciclo 25 (segno
  del dipolo assiale costruito dal ciclo, dalla legge di Hale).
- Φ: flusso unsigned sopra soglia.

## 4. Test

Incertezze: **bootstrap a blocchi sulle rotazioni di Carrington** (si
ricampionano le CR, con tutte le regioni di ciascuna), 2000 ricampionamenti,
seme 20261104. Intervalli a percentile.

### T0 — Controllo di potenza (iniezione sintetica)

Prima dei test reali, su tilt sintetici γ_i = (γ₀ + β·Â_i) sin|λ_i| + ε_i:
latitudini e attività reali del campione S, γ₀ dal fit di T1, ε estratto dai
residui di T1 (ricampionati), β ∈ {0, −0,1·γ₀, −0,2·γ₀, −0,3·γ₀}, 200
realizzazioni. Si riportano bias e frazione di rilevamenti (con la regola di
T3) per ogni β. T0 non cambia nessuna regola: dice quanto è sensibile T3.

### T1 — Legge di Joy (controllo)

Fit pesato con Φ di γ = γ₀ sin|λ|, senza intercetta, separato per ciclo ed
emisfero e complessivo. Atteso γ₀ > 0. Se l'intervallo al 95% di γ₀
complessivo include 0, i test T3 e T5 non vengono interpretati.

### T2 — TQ tra cicli (descrittivo)

γ₀ del ciclo 25 meno γ₀ del ciclo 24, **a pari fase**: per il ciclo 24 si
usano solo le regioni con φ ≤ φ_max, dove φ_max è la fase dell'ultimo record
del ciclo 25. Il ciclo 25 ha un'ampiezza maggiore del 24, quindi il TQ prevede
Δγ₀ < 0. Si riporta stima e intervallo al 95%, senza verdetto.

### T3 — TQ dentro il ciclo (**principale**)

Regressione pesata con Φ:
γ_i = (γ₀,c,h + β_T · (Â_i − 1)) · sin|λ_i| + ε_i,
con un γ₀ per ogni combinazione ciclo × emisfero e un β_T comune.
Il TQ prevede β_T < 0.

### T4 — LQ dentro il ciclo

Regressione pesata con Φ:
|λ_i| = a_c,h + b_1 φ_i + b_2 φ_i² + b_3 φ_i³ + β_L · (Â_i − 1) + ε_i.
Il controllo polinomiale sulla fase toglie la migrazione del diagramma a
farfalla. Il LQ prevede β_L > 0.

### T5 — Efficienza della sorgente (**principale**)

Per ogni CR ed emisfero con almeno 3 regioni del campione S:
η = Σ D* / Σ Φ. Regressione pesata con Σ Φ:
η = η_c,h + β_η · (Ā − 1) + ε,
con Ā la media di Â delle regioni della cella. Il quenching prevede β_η < 0.
Sensibilità: lo stesso con S* = sign(λ) · S_BL al posto di D*; e con
D* · exp(−λ² / (2λ_R²)) per λ_R ∈ {8°, 12°, 15°} (fattore di latitudine sul
dipolo finale), solo descrittivo.

## 5. Regola di decisione

Due test principali (T3, T5), quindi per il verdetto si usa l'intervallo al
**97,5%** (Bonferroni):
- **"quenching supportato"**: l'intervallo esclude 0 dal lato previsto;
- **"segno opposto"**: l'intervallo esclude 0 dal lato opposto;
- **"non deciso"**: l'intervallo include 0.

Il verdetto si dà sul campione S con la variante A. È **robusto** se le
sensibilità S1–S6 hanno lo stesso segno della stima principale e, per
almeno 4 su 6, l'intervallo al 95% esclude 0 dallo stesso lato. T2 e T4 si
riportano con intervalli al 95%, senza verdetto formale. La variante L
(legacy) si riporta per mostrare come cambierebbero le conclusioni con il
metodo v8.3.

## 6. Cosa P2 non fa

- Non usa la serie P1 per scegliere soglie, campioni o regole: tutte sono
  fissate qui.
- Non confronta con il campo polare osservato (sarà un protocollo separato).
- Non attribuisce un meccanismo fisico: un β ≠ 0 indica una dipendenza
  osservativa, compatibile con il quenching ma non una sua dimostrazione
  (effetti di selezione, blending di regioni a alta attività, dipendenza del
  tilt dalla dimensione).

## 7. Output (`results/P2/`)

- `P2_T0_POWER.csv`, `P2_T1_JOY.csv`, `P2_T2_INTERCYCLE.csv`,
  `P2_T3_TILT_QUENCHING.csv`, `P2_T4_LATITUDE_QUENCHING.csv`,
  `P2_T5_EFFICIENCY.csv` — stime, intervalli, verdetti, per ogni variante.
- `P2_SUMMARY.csv` — una riga per test con verdetto e robustezza.
- Figure in `figures/P2/` con i valori tracciati in CSV accanto.

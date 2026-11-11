# Protocollo P2f — test del quenching con la procedura M validata (T3, T5)

Stato: **congelato il 2026-11-11 (sera), prima di scrivere il codice**, dopo due revisioni
esterne della bozza (commit `09562cd`, `2618ca0`, `620920b`). Da questo commit non si modifica;
ogni cambiamento è un emendamento registrato prima del passo che riguarda. Lo script registra
lo SHA-256 di questo file negli output. È
**dichiaratamente non cieco** rispetto a: la validazione fallita P2d/P2e, le diagnosi A–D, il pilota
P2f (`docs/P2F_PILOT_RESULTS.md`) e le stime descrittive sui dati reali
(`docs/P2_RESULTS_DESCRIPTIVE.md`, lette il 2026-11-03). Le decisioni D1–D5 sono state chiuse dopo la
revisione della bozza (§10); il protocollo è congelato con questo commit.

Che cosa fa: fissa la procedura M (una sola), la sua validazione su risposte sintetiche sul disegno
reale congelato, i criteri di accettazione per ciascun test, la regola di decisione e di
esclusione sui dati reali, e l'ordine di esecuzione. Che cosa non fa: non attribuisce un
meccanismo fisico, non dichiara soglie fisiche dimostrate, non autorizza verdetti di assenza
senza un intervallo validato.

## 1. Procedura M (una per test, regole separate)

Riferimento di codice: `candidate_m` in `python/sharpbl/p2f_pilot.py` al commit `67058f6`, con le
regole di `docs/P2F_PILOT_PLAN.md` §4, A1 §2 e A2 §2. Qui si fissa la procedura **esattamente**.
**Differisce dal pilota in un punto, dichiarato e motivato dal pilota (non cieco):** tutti i
residui e la REML usano il **modello completo** (colonne nulle più la colonna dell'attività),
sotto la nulla e sotto l'alternativa. Motivo: nel pilota, con un effetto iniettato, la REML sul
modello nullo gonfiava σ̂_x² (+5–9 % in T3, +18–20 % in T5 a −0,3·scala) e in T3 il segnale
dell'attività non è eliminato dalla sola media di cella, perché sin|λ| varia dentro la cella. La
procedura validata è **una sola**: questa.

**Unità e stima puntuale** (invariate da P2): T3 per WLS a livello di regione con pesi Φ,
γ_i = (γ0_{c,h} + β_T (Â_i − 1)) sin|λ_i|; T5 per WLS sulle 318 celle CR × emisfero con almeno 3
regioni, pesi ΣΦ, η_c = η0_{c,h} + β_η (Ā_c − 1). β̂ = aᵀy con a la riga dell'attività di
(XᵀWX)⁻¹XᵀW.

**Funzione di varianza individuale** (A2 §2 con residui del modello completo): σ²(Φ) =
exp(a + b x), x = log Φ − m, m media di log Φ sulle unità del test (2485 per T3, 2375 per T5);
r_i residui del fit WLS del **modello completo** (T3 a livello di regione con pesi Φ; T5 sulle
celle, riportati alle regioni come z_i − η̂_c); e_i = r_i − u_{t,h} rispetto alla media di cella
pesata di r; media attesa
μ_i = (1 − h_i)² σ_i² + Σ_{j≠i} h_j² σ_j² in forma stabile (esatta per errori individuali
indipendenti e centrati rispetto alla media di cella; **ignora l'errore della media stimata del
fit**, di ordine 1/n, come in A2: usare i residui del fit completo non la rende esatta; la sua
tenuta si verifica nel test preliminare 2 e nello scenario 5); quasi-verosimiglianza gamma; celle con una
sola unità escluse dalla stima ma con σ̂²(Φ_i) assegnata dal modello; residui quadratici nulli
tenuti e contati; partenza, vincoli, L-BFGS-B (`ftol` 10⁻¹², `gtol` 10⁻⁸, 500 iterazioni,
gradiente analitico); non valida se senza convergenza dichiarata, Q non finita o ottimo su un
vincolo → `errore`.

**Componente temporale** (A1 §2): AR(1) bivariato latente x_{t,h} con Cov = σ_x² κ^{1{h≠h'}}
φ^{|t−t'|}, più rumore di campionamento v_{t,h} = Σ w_i² σ̂²(Φ_i)/W² (T3) o Σ Φ_i² σ̂²(Φ_i)/Φ_c²
(T5); massima verosimiglianza ristretta sulle risposte medie di cella con la matrice degli
effetti fissi del **modello completo** aggregata per cella (T3: colonne ciclo × emisfero
Σ w_i sin|λ_i|/W e colonna dell'attività Σ w_i (Â_i − 1) sin|λ_i|/W; T5: indicatori ciclo ×
emisfero delle celle e Ā_c − 1); vincoli φ ∈ [0; 0,98], κ ∈ [−0,98; 0,98],
θ = log σ_x² ∈ [log(10⁻⁶ s0); log(10³ s0)]; cinque avvii fissi; L-BFGS-B (`ftol` 10⁻¹⁰, `gtol` 10⁻⁶,
500 iterazioni); avvio valido se convergenza dichiarata e ℓ finita (una Cholesky fallita vale
penalità 1e100, mai accettata come soluzione); nessun avvio valido o XᵀV⁻¹X con numero di
condizione > 10¹² → `errore`; σ̂_x² al limite inferiore registrato (`sigma_x_at_lower`).

**Varianza e intervallo**: Var(β̂) = σ̂_x² bᵀK(φ̂, κ̂)b + Σ_i a_i² σ̂²(Φ_i) (T5: Σ_c g_c² v̂_c +
σ̂_x² b_cᵀKb_c); intervallo al 97,5 % nominale (Bonferroni su due test principali, come P2 §5):
β̂ ± z_{0,0125} √Var(β̂), con z_{0,0125} = Φ⁻¹(1 − 0,0125) calcolato a precisione completa
(`scipy.stats.norm.ppf`; 2,241 è solo la rappresentazione arrotondata). β̂ non finito, Var non
finita o non positiva, intervallo non finito → `errore`.

**Esiti** (per test): `supportato` se l'estremo superiore < 0; `opposto` se l'estremo
inferiore > 0; `non deciso` altrimenti; `errore` se una stima non è valida (mai un verdetto).
Nessuna regola di arresto interna, nessun secondo tentativo con impostazioni diverse.

**Convenzioni fissate** (dalla nota d'implementazione del pilota): la mediana di Φ nel fattore
eteroschedastico del generatore è quella delle 2485 regioni del disegno; le componenti per
rotazione del generatore sono estratte separatamente per T3 e per T5; i blocchi non servono più
(candidata B scartata).

## 2. Scala degli effetti e griglia (interpretabile, non soglie fisiche)

Gli effetti si esprimono in frazione della scala del test per unità di Â: β_T/γ0 (T3) e β_η/η̄
(T5), con γ0 = 24° e η̄ = 3,56·10⁻²⁵ G/Mx (valori informati dai dati reali, dichiarati; nel
modello nullo non influiscono sui falsi verdetti). Â è il numero di macchie emisferico mensile
SILSO diviso per la sua media sul periodo HMI dello stesso emisfero: Â = 1 è il livello medio
del periodo, non un confronto quiete–attività dentro ciascun ciclo (l'intervallo interquartile
0,93–1,88 descrive solo il campione).

**Griglia:** −0,1, −0,2, −0,3 della scala, con **−0,2 come riferimento centrale di
pianificazione**; **−0,35 effetto supplementare** di «trasferimento del quenching tra cicli»: la sua potenza è
solo riportata, ma i criteri di copertura e di coda inferiore (§5) sono decisivi anche a −0,35. Motivazione, con i limiti:
- Tra cicli, Jiao, Jiang & Wang (2021, A&A 653, A27) trovano per il coefficiente di Joy
  T = −0,00107 S_n + 0,61 (cicli 15–24, S_n massimo lisciato del numero di macchie): pendenza
  relativa intorno a S_n = 150 circa −0,36 per unità di forza relativa del ciclo. Riguarda il
  massimo del ciclo, non l'attività mensile emisferica: trasferirla a T3 è un'**ipotesi
  aggiuntiva**, non una stima della pendenza dentro il ciclo. Le anticorrelazioni di
  Dasi-Espuig et al. (2010; con il corrigendum, r = −0,79 per MW secondo Jiao et al.) non
  fissano una pendenza. I valori per ciclo su MDI/HMI (Zeng et al. 2024) non sono stati
  verificati sulla fonte primaria e **non** entrano nella giustificazione.
- Un esempio leggibile, non una soglia: nel modello γ0 sin|λ|, a 15° di latitudine il tilt
  medio è circa 6,2°; −0,2·γ0 per ΔÂ = 1 vale circa −1,2° a quella latitudine (16–32 % sarebbe
  1–2°). Il «bastano 1–2°» citato da Jiang (2020) da Karak & Miesch (2017) è una proprietà di
  quel modello di dinamo, non una soglia universale né una variazione per unità di Â.
- Per T5, la riduzione del dipolo per inflow (Martin-Belda & Cameron 2017) confronta trasporto
  con e senza inflow, non per unità del nostro proxy; tra cicli molto deboli e molto forti la
  differenza relativa del dipolo nello stesso lavoro è circa il 9 %. Nel dipolo finale (Jiang
  2020) quenching del tilt e della latitudine si rafforzano; T5 misura una quantità diversa,
  prima del trasporto, e non si assume alcuna compensazione.

**Nessun effetto è scelto in base alla potenza.** La potenza si riporta sulla griglia; non è un
criterio di accettazione (§5) e non autorizza verdetti di assenza (§7).

## 3. Disegno congelato e risposte sintetiche

Disegno reale senza risposte, come nel pilota (`p2f_pilot.build_design`, asserzione sulle colonne
di risposta; conteggi in `results/P2F_PILOT/DESIGN_CHECKS.csv`: 2485 regioni, 394 celle T3 di cui
42 singole, 318 celle T5 con 2375 regioni). Generatore del pilota (piano §2): T3
γ_i = (γ0 + β_frac γ0 (Â_i − 1)) sin|λ_i| + σ_e c_i ε_i + σ_x x_{t,h}, σ_e = 15, σ_x = 7,5; T5
z_i = η̄ (1 + β_frac (Ā_c − 1) + c_i ε_i + 0,5 x_{t,h}), con **Ā_c la media semplice di Â sulle
regioni della cella** (quella della regressione T5, `run_p2.cells`), uguale per tutte le regioni
della cella; c_i = 1 o (Φ_i/mediana Φ)^−0,25; ε normale o t₄ a varianza 1; x a varianza
marginale 1 sulla griglia completa delle CR.

**Differenza dal generatore del pilota (dichiarata):** il pilota assegnava l'effetto T5 alle
singole regioni con Â_i; aggregando con i pesi Φ il segnale di cella seguiva la media di Â
pesata con Φ, che differisce dalla media semplice in 215 celle su 318, e un coefficiente
iniettato 0,2 dava una pendenza T5 di 0,19683 in una prova deterministica senza rumore. Con Ā_c
la media aggregata segue esattamente il modello T5 e il parametro iniettato coincide con quello
di cui si verifica la copertura. Nei residui di T5 (cella), sottrarre la previsione del modello
completo, costante nella cella, e ricentrare nella cella elimina la previsione; il passaggio al
fit completo da solo non rimuoverebbe un segnale che varia tra le regioni della cella.
Il generatore del pilota resta quello storico della procedura precedente.

## 4. Scenari di validazione (tutti decisivi, fissati prima)

| s | Componente per rotazione x | Rumore individuale | Nota |
|---|---|---|---|
| 0 | assente | normale | |
| 1 | AR(1) φ = 0,5, κ = 0 | normale | |
| 2 | AR(1) φ = 0,9, κ = 0 | normale | |
| 3 | AR(1) φ = 0,9, κ = −0,8 | normale | |
| 4 | AR(1) φ = 0,5, κ = +0,6 | normale | |
| 5 | AR(1) φ = 0,8, κ = 0 | eteroschedastico | tenuta della funzione di varianza |
| 6 | AR(2) φ1 = 0,5, φ2 = 0,3, emisferi indipendenti | normale | fuori dal modello di M |
| 7 | salti ±1, blocchi di 20 CR, fase per catalogo | normale | fuori dal modello; **decisivo** (3,4 % in T5 nel pilota) |
| 8 | AR(1) φ = 0,8, κ = 0 | t₄ | code pesanti |
| 9 | AR(1) φ = 0,53, κ = −0,85, σ_x raddoppiata (15 per T3; 1,0·η̄ per T5) | eteroschedastico, t₄ | parametri alle stime reali di T3 (P2e), componente temporale forte, tutto insieme |
| 10 | salti ±1, blocchi di 13 CR, **stesso livello nei due emisferi** | normale | salti correlati tra emisferi |
| 11 | AR(2) φ1 = 0,5, φ2 = 0,3 con correlazione κ = −0,8 tra emisferi | normale | AR(2) correlato |

Gli scenari 0–8 sono quelli del pilota (non ciechi); 9–11 sono nuovi. Un solo elenco: non si
aggiungono né tolgono scenari dopo l'esecuzione.

## 5. Numerosità, semi, criteri di accettazione (per test, separati)

- **Falsi verdetti sotto la nulla:** N₀ = 10 000 cataloghi per scenario e test. Criterio: in
  **ognuno** dei 12 scenari, falsi verdetti (`supportato` + `opposto`) ≤ 3,0 % dei 10 000
  tentativi **e** per ciascun verso ≤ 1,75 % **e** `errore` ≤ 1 %. Un `errore` non è un falso
  verdetto e conta solo nel proprio limite.
- **Copertura e potenza sotto effetto:** scenari 1, 2, 7 e 9 × effetti −0,1, −0,2, −0,3, −0,35
  della scala (16 combinazioni per test), N₁ = 2000 cataloghi ciascuna. Si contano
  separatamente, sui 2000 tentativi: intervallo che contiene β vero; estremo inferiore > β vero
  (coda inferiore, quella usata per l'esclusione in §7); estremo superiore < β vero (coda
  superiore); `errore` (vale come non copertura). Criteri: copertura ≥ 96,5 % **e** coda
  inferiore ≤ 2,0 % in ogni combinazione; la coda superiore si riporta. La potenza (frazione di
  `supportato` sui 2000, `errore` = mancato rilevamento) si **riporta** e non è un criterio.
- **Che cosa stabilisce la validazione:** i criteri sono soddisfatti da una procedura al livello
  nominale e scartano con alta probabilità una procedura chiaramente sopra; una copertura
  osservata ≥ 96,5 % **non dimostra** una copertura effettiva del 97,5 %: la risoluzione è
  quella di N₁. Sui dati reali l'intervallo si descrive come «livello nominale 97,5 %; criteri
  di validazione superati negli scenari provati», riportando la copertura osservata e la sua
  incertezza Monte Carlo per ogni combinazione. I quattro scenari sotto effetto sono una verifica selezionata:
  le conclusioni sulla copertura valgono per essi e **non si estendono** agli altri otto.
- **Calcolo delle probabilità di scarto** (binomiale esatta; ipotesi: cataloghi indipendenti,
  frequenza vera ripartita simmetricamente tra i versi, nessun `errore`; gli `errore` riducono i
  falsi verdetti contati e hanno un limite proprio):
  - procedura esattamente al 2,5 %: scartata in almeno uno dei 12 scenari nulli con
    probabilità 1,0 % (0,083 % per scenario, criteri complessivo e per verso insieme);
  - procedura al 3,4 % complessivo (valore del pilota per T5 con i salti), simmetrica: supera
    il solo criterio complessivo di un singolo scenario con probabilità 1,3 %;
  - copertura vera 97,5 % con code simmetriche (1,25 % ciascuna): i criteri di copertura e di
    coda inferiore si valutano **sugli stessi cataloghi** e non sono indipendenti; calcolati
    congiuntamente (multinomiale esatta: coperto, sotto, sopra), una combinazione fallisce con
    probabilità 0,41 % e almeno una delle 16 con il 6,3 % (separatamente sarebbero 4,1 % per
    la copertura e 3,0 % per la coda, 7,0 % se trattate come indipendenti);
  - **in tutto, per test, una procedura esattamente nominale è scartata con probabilità
    7,26 %** (5,1 % senza il criterio sulla coda inferiore). Una copertura vera del 96,5 % passa
    una singola combinazione con probabilità 53 %; una coda inferiore vera del 2,0 % con il 54 %.
  Si accetta questo rischio di scarto a favore della sensibilità sulle deviazioni; non si
  ritoccano i criteri dopo l'esecuzione.
- **Validazione di un test:** tutti i criteri (falsi verdetti nei 12 scenari, copertura e coda
  inferiore nelle 16 combinazioni) soddisfatti. Se uno fallisce, M non è validata per quel test,
  che resta descrittivo; nessuna modifica e riesecuzione senza un nuovo protocollo con semi
  nuovi.
- **Semi** (nuovi, disgiunti da tutti quelli usati: `p2f_pilot.USED`, gli intervalli del pilota
  3 000 000–3 950 300 e 4 000 000–4 950 600 e i suoi test 5 000 000–5 001 000; controllo di non
  sovrapposizione e di unicità nel codice):
  - nulla: 6 000 000 + 100 000·s + k, s = 0…11, k = 0…9999 (fino a 7 109 999);
  - effetto: 7 500 000 + 100 000·j + k, k = 0…1999, con j = 4·i_s + i_e, i_s = 0, 1, 2, 3 per
    gli scenari 1, 2, 7, 9 e i_e = 0, 1, 2, 3 per gli effetti −0,1, −0,2, −0,3, −0,35 (j = 0…15,
    fino a 9 001 999);
  - test del codice: 20 000 000 + k, k < 1000 (nessuna sovrapposizione con gli intervalli
    sopra; il valore 8 000 000 non è più usato dai test).
- **Costo stimato:** 12 × 10 000 + 16 × 2000 = 152 000 cataloghi × 2 test, circa 1 s per
  catalogo-test: 7–9 ore su 12 processi. Esecuzione distaccata, unica.

## 6. Controlli obbligatori (prima e durante)

1. Test del codice (come A1 §6 e A2 §3, stessi criteri, semi 20 000 000 + k; il test 2 con i
   residui del modello completo, test 4 con la matrice completa; **test 6, nuovo:** prova
   deterministica senza rumore (ε = 0, x = 0) con β_frac = −0,2 su T3 e T5: la stima WLS deve
   restituire il coefficiente iniettato con scarto relativo ≤ 10⁻⁹): REML su serie
   sintetiche; funzione di varianza su 2a/2b; Var(β̂) con parametri veri contro V_true di A;
   nessuna colonna di risposta; semi. La validazione parte solo se tutti passano sullo stesso
   commit pulito.
2. Disegno congelato asserito in ogni catalogo: 2485 regioni e 394 celle T3, 318 celle e 2375
   regioni T5.
3. Finitezza di statistiche, parametri e intervalli in ogni riga con esito; controllo
   indipendente e riconteggio (`p2f_checks.py`, adattato) **prima** dell'interpretazione; output
   mai modificati, riconteggi salvati a parte.
4. Provenienza: `git_commit`, `git_dirty` = 0, SHA-256 di questo protocollo e dei piani del
   pilota in ogni output.

## 7. Applicazione ai dati reali (solo per i test validati)

- Si esegue **dopo** il commit degli output della validazione, in un passo separato che legge le
  risposte reali (`sintilt`/γ, `d_axial_bal_g`/D*) con un'opzione esplicita; una sola
  esecuzione per test.
- Per ciascun test validato si riportano: β̂, intervallo («livello nominale 97,5 %; criteri di
  validazione superati negli scenari provati», con copertura osservata e incertezza Monte Carlo
  della validazione, §5), esito (§1), diagnostica
  (â, b̂, φ̂, κ̂, σ̂_x², `sigma_x_at_lower`, avvii validi, residui nulli), e la **lista dei δ
  della griglia esclusi**: un quenching almeno pari a δ (cioè β ≤ −δ·scala) è «escluso dall'intervallo a livello
  nominale 97,5 %, validato negli scenari provati» se l'estremo inferiore dell'intervallo è
  > −δ·scala; si riportano insieme la frequenza osservata della coda inferiore nella
  validazione e la sua incertezza. È l'unico modo previsto di
  affermare un'assenza; potenza alta non lo autorizza.
- Un esito `errore` sui dati reali lascia il test descrittivo.
- **Sensibilità** (stesse formule, senza verdetto, dichiarate non validate): attività
  A_smooth13 e A_usflux; varianti S1–S6 di P2. Si riportano stima e intervallo.
- Formulazioni: «supportato» non attribuisce un meccanismo (selezione, blending, dipendenza
  dalla fase restano possibili); «non deciso» non è assenza; l'esclusione vale per i δ elencati.

## 8. Ordine e regola di arresto

1. Congelamento di questo protocollo (commit). 2. Codice `python/sharpbl/p2f_validation.py`
(validazione) e `p2f_apply.py` (dati reali), test del codice. 3. Validazione, controllo
indipendente, risultati in `docs/P2F_VALIDATION_RESULTS.md`, commit. 4. Applicazione ai soli
test validati, risultati in `docs/P2F_RESULTS.md`. Ogni passo una volta sola; un fallimento si
riporta e si conserva. Emendamenti solo prima del passo che riguardano, dichiarati non ciechi
se successivi a un esito.

## 9. Output

`results/P2F/`: `VALIDATION_RAW.csv.gz`, `VALIDATION_FALSE_VERDICTS.csv`,
`VALIDATION_COVERAGE_POWER.csv`, `VALIDATION_DECISION.csv`, `PRELIM_TESTS.csv`,
`POST_CHECKS*.csv`; `REAL_T3.csv`, `REAL_T5.csv`, `REAL_SENSITIVITY.csv`.

## 10. Decisioni chiuse dopo la revisione della bozza (2026-11-11)

- **D1 chiusa:** modello completo ovunque (residui per la funzione di varianza e matrice degli
  effetti fissi della REML), sotto la nulla e sotto l'alternativa; procedura unica (§1).
- **D2 chiusa:** soglie 3,0 % complessivo, 1,75 % per verso, `errore` ≤ 1 %, copertura ≥ 96,5 %,
  coda inferiore ≤ 2,0 %; calcolo complessivo e ipotesi in §5 (scarto di una procedura nominale
  7,26 % per test, calcolo congiunto).
- **D3 chiusa:** 12 scenari; sotto effetto 1, 2, 7, 9, con conclusioni limitate a essi.
- **D4 chiusa:** griglia −0,1/−0,2/−0,3 con −0,35 supplementare, comune ai due test.
- **D5 chiusa:** A_smooth13, A_usflux, S1–S6 come sensibilità senza verdetto.
- **Semi** corretti (sovrapposizione fra j = 5 e i test eliminata); β̂ finito richiesto; quantile
  a precisione completa.
- **Seconda revisione (2026-11-11):** probabilità congiunta di scarto 7,26 % (non 7,9 %);
  generatore T5 allineato al parametro della regressione (Ā_c, §3) con test deterministico 6;
  avvertenza di A2 sulla media attesa conservata; formulazione «livello nominale 97,5 %; criteri
  di validazione superati negli scenari provati» in §5 e §7.

Dopo il congelamento questo documento non si modifica; ogni cambiamento è un emendamento
registrato prima del passo che riguarda.

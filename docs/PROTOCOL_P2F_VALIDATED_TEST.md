# Protocollo P2f — test del quenching con la procedura M validata (T3, T5)

Stato: **BOZZA per revisione, scritta il 2026-11-11, non congelata.** Diventa protocollo con un
commit dedicato dopo la revisione; da quel momento non si modifica e il codice si scrive dopo. È
**dichiaratamente non cieco** rispetto a: la validazione fallita P2d/P2e, le diagnosi A–D, il pilota
P2f (`docs/P2F_PILOT_RESULTS.md`) e le stime descrittive sui dati reali
(`docs/P2_RESULTS_DESCRIPTIVE.md`, lette il 2026-11-03). Le decisioni aperte sono in §10 e vanno
chiuse prima del congelamento.

Che cosa fa: fissa la procedura M (una sola), la sua validazione su risposte sintetiche sul disegno
reale congelato, i criteri di accettazione per ciascun test, la regola di decisione e di
esclusione sui dati reali, e l'ordine di esecuzione. Che cosa non fa: non attribuisce un
meccanismo fisico, non dichiara soglie fisiche dimostrate, non autorizza verdetti di assenza
senza un intervallo validato.

## 1. Procedura M (una per test, regole separate)

Riferimento di codice: `candidate_m` in `python/sharpbl/p2f_pilot.py` al commit `67058f6`, con le
regole di `docs/P2F_PILOT_PLAN.md` §4, A1 §2 e A2 §2. Qui si fissa la procedura **esattamente**;
dove differisce dal pilota lo si dice (§10, D1).

**Unità e stima puntuale** (invariate da P2): T3 per WLS a livello di regione con pesi Φ,
γ_i = (γ0_{c,h} + β_T (Â_i − 1)) sin|λ_i|; T5 per WLS sulle 318 celle CR × emisfero con almeno 3
regioni, pesi ΣΦ, η_c = η0_{c,h} + β_η (Ā_c − 1). β̂ = aᵀy con a la riga dell'attività di
(XᵀWX)⁻¹XᵀW.

**Funzione di varianza individuale** (A2 §2): σ²(Φ) = exp(a + b x), x = log Φ − m, m media di
log Φ sulle unità del test (2485 per T3, 2375 per T5); residui e_i = r_i − u_{t,h} rispetto alla
media di cella pesata dei residui del fit nullo; media attesa esatta
μ_i = (1 − h_i)² σ_i² + Σ_{j≠i} h_j² σ_j² in forma stabile; quasi-verosimiglianza gamma; celle con una
sola unità escluse dalla stima ma con σ̂²(Φ_i) assegnata dal modello; residui quadratici nulli
tenuti e contati; partenza, vincoli, L-BFGS-B (`ftol` 10⁻¹², `gtol` 10⁻⁸, 500 iterazioni,
gradiente analitico); non valida se senza convergenza dichiarata, Q non finita o ottimo su un
vincolo → `errore`.

**Componente temporale** (A1 §2): AR(1) bivariato latente x_{t,h} con Cov = σ_x² κ^{1{h≠h'}}
φ^{|t−t'|}, più rumore di campionamento v_{t,h} = Σ w_i² σ̂²(Φ_i)/W² (T3) o Σ Φ_i² σ̂²(Φ_i)/Φ_c²
(T5); massima verosimiglianza ristretta sulle risposte medie di cella con la matrice degli
effetti fissi aggregata **[D1: modello nullo come nel pilota, oppure modello completo con la
colonna dell'attività aggregata]**; vincoli φ ∈ [0; 0,98], κ ∈ [−0,98; 0,98],
θ = log σ_x² ∈ [log(10⁻⁶ s0); log(10³ s0)]; cinque avvii fissi; L-BFGS-B (`ftol` 10⁻¹⁰, `gtol` 10⁻⁶,
500 iterazioni); avvio valido se convergenza dichiarata e ℓ finita (una Cholesky fallita vale
penalità 1e100, mai accettata come soluzione); nessun avvio valido o XᵀV⁻¹X con numero di
condizione > 10¹² → `errore`; σ̂_x² al limite inferiore registrato (`sigma_x_at_lower`).

**Varianza e intervallo**: Var(β̂) = σ̂_x² bᵀK(φ̂, κ̂)b + Σ_i a_i² σ̂²(Φ_i) (T5: Σ_c g_c² v̂_c +
σ̂_x² b_cᵀKb_c); intervallo al 97,5 % (Bonferroni su due test principali, come P2 §5):
β̂ ± z_{0,0125} √Var(β̂), z_{0,0125} = 2,241. Var non finita o non positiva → `errore`.

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
pianificazione**; **−0,35 scenario supplementare** di «trasferimento del quenching tra cicli»
(solo riportato). Motivazione, con i limiti:
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
z_i = η̄ (1 + β_frac (Â_i − 1) + c_i ε_i + 0,5 x_{t,h}); c_i = 1 o (Φ_i/mediana Φ)^−0,25; ε
normale o t₄ a varianza 1; x a varianza marginale 1 sulla griglia completa delle CR.

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

- **Falsi verdetti:** N₀ = 10 000 cataloghi per scenario e test (errore binomiale al 2,5 %:
  0,16 punti). Criterio: in **ognuno** dei 12 scenari, falsi verdetti (`supportato` + `opposto`)
  ≤ 3,0 % dei 10 000 tentativi **e** per ciascun verso ≤ 1,75 % **e** `errore` ≤ 1 %. Un
  `errore` non è un falso verdetto e conta nel suo limite. Con questi numeri una procedura al
  livello vero 2,5 % fallisce almeno uno dei 12 scenari con probabilità circa 0,01; una al 3,4 %
  (il valore del pilota per T5 con i salti) supera un singolo scenario con probabilità circa
  0,01.
- **Copertura e potenza sotto effetto:** scenari 1, 2, 7 e 9 × effetti −0,1, −0,2, −0,3, −0,35
  della scala, N₁ = 2000 cataloghi ciascuno (errore binomiale al 97,5 %: 0,35 punti). Criterio di
  copertura: l'intervallo al 97,5 % contiene il β vero in ≥ 96,5 % dei 2000 tentativi in ogni
  combinazione (gli `errore` contano come non copertura). La potenza (frazione di `supportato`
  sui 2000, `errore` = mancato rilevamento) si **riporta** e non è un criterio.
- **Validazione di un test:** tutti i criteri su falsi verdetti e copertura soddisfatti. Se uno
  fallisce, M non è validata per quel test, che resta descrittivo; nessuna modifica e
  riesecuzione senza un nuovo protocollo con semi nuovi.
- **Semi** (nuovi, disgiunti da tutti quelli usati, elenco in `p2f_pilot.USED` più gli
  intervalli del pilota 3 000 000–5 001 000; controllo nel codice): nulla
  6 000 000 + 100 000·s + k, k < 10 000; effetti 7 500 000 + 100 000·j + k, j indice
  scenario-effetto (16 combinazioni), k < 2000; test del codice 8 000 000 + k.
- **Costo stimato:** 12 × 10 000 + 16 × 2000 = 152 000 cataloghi × 2 test, circa 1 s per
  catalogo-test: 8–9 ore su 12 processi. Esecuzione distaccata, unica.

## 6. Controlli obbligatori (prima e durante)

1. Test del codice (come A1 §6 e A2 §3, stessi criteri, semi 8 000 000 + k): REML su serie
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
- Per ciascun test validato si riportano: β̂, intervallo al 97,5 %, esito (§1), diagnostica
  (â, b̂, φ̂, κ̂, σ̂_x², `sigma_x_at_lower`, avvii validi, residui nulli), e la **lista dei δ
  della griglia esclusi**: un quenching almeno pari a δ (cioè β ≤ −δ·scala) è «escluso al
  97,5 %» se l'estremo inferiore dell'intervallo è > −δ·scala. È l'unico modo previsto di
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

## 10. Decisioni aperte prima del congelamento

- **D1 — Effetti fissi della REML.** Nel pilota la REML usa il modello nullo: con un effetto
  iniettato le stime di σ̂_x² risultano gonfiate (pilota: +5–9 % in T3 e +18–20 % in T5 a
  −0,3; φ̂ 0,56 contro 0,50 in T5), quindi l'intervallo è conservativo sotto l'alternativa e la
  potenza cala. Alternativa: REML con la matrice completa (colonne nulle più la colonna
  dell'attività aggregata per cella), che sotto la nulla è lo stesso modello con una colonna in
  più. Proposta: modello completo, dichiarato come cambiamento motivato dal pilota (non cieco).
  La validazione (§5) copre entrambi i casi.
- **D2 — Soglie:** 3,0 % complessivo e 1,75 % per verso su 10 000, copertura ≥ 96,5 % su 2000.
- **D3 — Scenari 9–11** e scenari sotto effetto (1, 2, 7, 9): confermare l'elenco.
- **D4 — Griglia** −0,1/−0,2/−0,3 con −0,35 supplementare, per entrambi i test.
- **D5 — Sensibilità**: A_smooth13, A_usflux, S1–S6, senza verdetto.

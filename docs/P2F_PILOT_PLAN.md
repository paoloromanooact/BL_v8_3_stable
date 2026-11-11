# Piano del pilota di sviluppo per P2f — due procedure candidate sul disegno reale

Stato: **registrato il 2026-11-11 prima di scrivere ed eseguire il codice del pilota.** **Sviluppo, non
validazione**: serve a scegliere e scartare procedure; non produce verdetti, non usa le
risposte reali (γ_i, D*_i) e non autorizza applicazioni ai dati. Contesto e decisioni:
`docs/P2F_DESIGN.md` §7. Lo script registrerà nei propri output il commit e lo SHA-256 di
questo file.

## 1. Disegno reale congelato (requisito (e))

Dal catalogo P1 e dal campione S di P2 (`run_p2.samples`, `add_activity`), **solo variabili di
disegno**:
- **T3:** 2485 regioni su 210 CR (2096–2316), 394 celle CR × emisfero, di cui 42 con una sola
  regione;
- **T5:** 2375 regioni in 318 celle con almeno 3 regioni, 176 CR.

Per ogni regione si usano CR, emisfero, latitudine, Φ, attività `A_monthly`, ciclo e cella.
Le risposte reali sono **sostituite** da risposte sintetiche e il codice verifica che non
vengano lette (§6). Selezione e celle sono quelle sopra, fisse; le risposte sintetiche non le
cambiano.

## 2. Risposte sintetiche sotto la nulla (β = 0)

- **T3:** γ_i = γ0 sin|λ_i| + σ_e c_i ε_i + σ_x x_{t(i),h(i)}, con γ0 = 24, σ_e = 15,
  σ_x = 7,5.
- **T5:** z_i = η̄ (1 + c_i ε_i + 0,5 x_{t(i),h(i)}), con η̄ = 3,56·10⁻²⁵ G/Mx; T5 si calcola
  dalle stesse celle di P2.
- c_i = 1, oppure (Φ_i / mediana Φ)^−0,25 negli scenari eteroschedastici; ε_i ~ N(0, 1) o t
  con 4 gradi di libertà riscalata a varianza 1; x componente per rotazione con varianza
  marginale 1.
- γ0, η̄ e il rapporto σ_x/σ_e sono **informati** da stime già note (dati reali e sviluppo):
  lo si dichiara. Nel modello nullo γ0 ed η̄ non influiscono sui falsi verdetti, perché le
  medie stanno nello spazio dei regressori nulli.

## 3. Scenari del pilota (9, tutti concorrono alla scelta)

| s | Componente per rotazione x | Rumore individuale |
|---|---|---|
| 0 | assente | normale, omoschedastico |
| 1 | AR(1), φ = 0,5, κ = 0 | normale |
| 2 | AR(1), φ = 0,9, κ = 0 | normale |
| 3 | AR(1), φ = 0,9, κ = −0,8 | normale |
| 4 | AR(1), φ = 0,5, κ = +0,6 | normale |
| 5 | AR(1), φ = 0,8, κ = 0 | normale, eteroschedastico |
| 6 | AR(2), φ1 = 0,5, φ2 = 0,3, emisferi indipendenti, varianza di popolazione 1 | normale |
| 7 | salti: livelli ±1 equiprobabili, indipendenti per emisfero e blocco; blocchi di 20 CR con fase uniforme in {0, …, 19}, estratta per catalogo | normale |
| 8 | AR(1), φ = 0,8, κ = 0 | t con 4 gradi di libertà, varianza 1 |

AR partono dalla distribuzione stazionaria (AR(2) con 200 passi di riscaldamento), sulla
griglia completa delle CR tra la prima e l'ultima del disegno. κ = −0,8 e φ = 0,9 sono valori
di una gamma plausibile informata dalle stime reali (T3 κ̂ = −0,85, T5 φ̂ = 0,91), non valori
veri assunti.

## 4. Procedure candidate (applicate separatamente a T3 e T5)

Statistica comune: la stima di P2 (T3 per WLS a livello di regione con pesi Φ; T5 per WLS
sulle celle con pesi ΣΦ), con verso previsto β < 0, livello 1,25% per verso.

**Candidata M (modello temporale, T-2 + I-1):**
1. fit nullo (senza attività) come in P2d; residui r_i; medie di cella u_{t,h};
2. **funzione di varianza (I-1):** σ²(Φ) = exp(a + b log Φ), stimata con regressione gamma a
   legame logaritmico sulle pseudo-osservazioni e_i² / (1 − 2h_i + Σ_{j∈cella} h_j²), nelle
   celle con almeno 2 unità (e_i = r_i − u_{t,h}, h_i = w_i/W_cella);
3. varianza di campionamento delle celle v_{t,h} = Σ w_i² σ̂²(Φ_i) / W²;
4. **componente temporale (T-2):** AR(1) bivariato latente più rumore con varianza v_{t,h},
   parametri (φ, κ, σ_x²) per **massima verosimiglianza ristretta** sulle celle osservate
   (matrice di covarianza densa, effetti fissi = medie per ciclo × emisfero); vincoli
   φ ∈ [0; 0,98], κ ∈ [−0,98; 0,98]; ottimizzazione L-BFGS-B da 5 punti iniziali fissi;
5. **decisione analitica:** Var(β̂) = σ̂_x² bᵀK(φ̂, κ̂)b + Σ_i a_i² σ̂²(Φ_i), con a e b come in
   A; falso verdetto se |β̂| / √Var > z_0,0125 (normale, precisione completa). La concordanza
   Monte Carlo/analitica è stata verificata per il modello del generatore (C1, D), non per
   questa procedura: il pilota usa la forma analitica per entrambe le fasi.

L'incertezza delle stime (funzione di varianza e parametri temporali) entra nella verifica
perché la procedura completa si ristima in ogni catalogo.

**Candidata B (blocchi con emisferi congiunti, T-3 + I-3):**
1. cluster = blocchi di **13 CR consecutive** con **entrambi gli emisferi**, partizione fissa
   a partire dalla prima CR del disegno (T3: 17 blocchi con dati; T5: 16);
2. **wild cluster bootstrap ristretto** (nulla imposta): risposte simulate
   y* = ŷ_nullo + r̂_i · w_g, con pesi di Webb a 6 punti per cluster; B = 9999;
3. statistica t con errore robusto per cluster (CR1: fattore G/(G − 1) · (n − 1)/(n − k));
4. p-value per verso dalla distribuzione di t*, con la correzione per B finito di P2d §4;
   soglia 1,25% per verso.

## 5. Numerosità, semi, criteri e scelta (fissati prima)

- **Falsi verdetti:** 1000 cataloghi per scenario, test e candidata (stesse risposte per le
  due candidate). Con soglia 4%, cioè al massimo 40 falsi verdetti su 1000, una procedura
  con livello vero del 2,5% viene scartata in almeno uno dei 9 scenari con probabilità circa
  0,016; una al 6% supera un singolo scenario con probabilità circa 0,003; una al 3% viene
  scartata con probabilità circa 0,24.
- **Potenza (riportata):** scenari 1 e 2, 300 cataloghi per effetto iniettato
  β = −0,1, −0,2, −0,3 · γ0 (T3) e β_η = −0,1, −0,2, −0,3 · η̄ (T5). Gli effetti di interesse
  scientifico si fisseranno nel protocollo.
- **Semi** (intervalli distinti, controllo di non sovrapposizione nel codice):
  - risposte nulle 3 000 000 + 100 000·s + k (k < 1000);
  - potenza 3 900 000 + 10 000·(3·(s − 1) + e) + k, con e = 0, 1, 2 per gli effetti e k < 300;
  - bootstrap della candidata B 4 000 000 + 100 000·s + 2k + t (nulla), 4 900 000 + 10 000·j + 2k + t
    (potenza, j indice scenario-effetto).
- **Regole di scelta, separate per T3 e T5:**
  - una candidata è **mantenuta** se in **ognuno** dei 9 scenari ha al massimo 40 falsi
    verdetti su 1000 e la frazione di cataloghi senza esito (stima non riuscita) è ≤ 2%;
  - se entrambe sono mantenute, si sceglie quella con la potenza media più alta negli scenari
    1 e 2 all'effetto −0,2 (a parità entro 0,02, la candidata B, che fa meno ipotesi);
  - se una sola è mantenuta, si sceglie quella;
  - se nessuna è mantenuta, per quel test il pilota si ferma: si riporta l'esito e il test
    resta descrittivo, salvo un nuovo motivo documentato e un nuovo piano.
- **Regola di arresto del pilota:** una sola esecuzione con queste impostazioni; non si
  cambiano scenari, soglie o candidate dopo aver visto i risultati. Correzioni di codice dopo
  un controllo fallito richiedono un emendamento registrato prima di rieseguire.

## 6. Controlli obbligatori

1. **Nessuna risposta reale:** il codice costruisce il disegno senza le colonne di risposta
   (`sintilt`, `d_axial_bal_g`, `s_bl` e derivate) e lo verifica con un'asserzione.
2. **Disegno congelato:** 2485 regioni, 394 celle T3, 318 celle T5, identici in ogni catalogo.
3. **Test del codice prima del pilota**, su dati sintetici con semi propri (5 000 000 + k):
   - la massima verosimiglianza ristretta recupera φ, κ, σ_x² entro l'incertezza attesa su
     serie lunghe;
   - la funzione di varianza recupera a e b in un caso eteroschedastico noto;
   - il wild cluster bootstrap dà t* e p-value identici a un'implementazione diretta su un
     caso piccolo.
4. **Finitezza:** stime e statistiche finite in ogni catalogo, altrimenti lo stato esplicito
   `errore` (mai un verdetto), che conta nella frazione senza esito.
5. **Semi:** non sovrapposti a quelli già usati (elenco di `docs/DIAGNOSTIC_D_PLAN.md` §2,
   più D e i suoi semi interni).

## 7. Costo stimato

Candidata M: alcune decine di valutazioni della verosimiglianza su circa 400 celle per
catalogo, circa 1–3 s. Candidata B: 9999 repliche vettorizzate, circa 1–2 s. In tutto
36 000 cataloghi-test per i falsi verdetti più 10 800 per la potenza: stima 3–6 ore su 12
processi, da confermare con i test del codice. Il pilota partirà in modo distaccato.

## 8. Output

`results/P2F_PILOT/` (per catalogo, sintesi per scenario, test e candidata, potenza,
controlli, scelta); script `python/sharpbl/p2f_pilot.py` e test in `tests/`; risultati in
`docs/P2F_PILOT_RESULTS.md`.

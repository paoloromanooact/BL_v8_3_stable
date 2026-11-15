# T5-D2 — nota tecnica: ricalcolo indipendente degli SE degli oracoli A2, A3 e A2p

Stato: **nota tecnica congelata il 2026-11-15, prima di scrivere ed eseguire il codice del ricalcolo.**
Non è un protocollo inferenziale: non cambia letture, soglie o verdetti di T5-D2. Fissa che cosa si
ricalcola, con quale codice, con quali tolleranze e come si leggono gli esiti. Richiesta dalla revisione
di fase 2 (Codex, `8c7801a`) e dai suoi pareri del 2026-11-15; vedi §7.1 e §10 di
[T5_ORACLE_RESULTS.md](T5_ORACLE_RESULTS.md).

**Non cieca.** Gli output T5-D2 (`27a9c7d`) sono già stati letti e interpretati. Sono già noti anche i
conteggi degli errori: 22 cataloghi con `errore` in A2 e 18 in A2p, tutti dovuti alla funzione di varianza.

## 1. Scopo e ambito

Si verifica in modo indipendente la **costruzione** degli errori standard degli oracoli che non usano
la REML, cioè A2, A3 e A2p, su **tutti** i 32000 cataloghi della corsa (stesse chiavi di `JOBS_SPEC`).
A2p ha la stessa struttura di A2 e costa quasi nulla: si include, dichiarandolo.
A0, A1a e A1b richiedono la REML e restano fuori: A0 ha già il riferimento P2f, A1a e A1b restano non
ricalcolati.

## 2. Codice condiviso, riusato e dichiarato

Questi pezzi vengono dalla validazione P2f e si riusano così come sono. Il ricalcolo **non** li verifica.

| Funzione | Ruolo |
|---|---|
| `P.build_design()` | disegno congelato, ricostruito da zero (non si legge `_design.pkl`) |
| `V.seed_null`, `V.seed_effect`, `V.responses` | semi e generatore dei cataloghi |
| `V.units(dd, "T5")` | aggregazione: beta, contrasto `g`, `k_of_i`, `agg`, celle, `phi`, residui |
| `V.cell_residuals`, `P.varfun_fit` | stima della funzione di varianza individuale (ottimizzazione L-BFGS-B) |

Il catalogo rigenerato coincide con quello della corsa se beta coincide con il raw (§5).

## 3. Parte riscritta in modo indipendente

Il codice indipendente **non importa** `diag_t5_oracle.py` e non chiama `V.cell_level`, `P.ar1_k` né
`procedure_m`. Prende le costanti dai testi dei protocolli e le confronta con quelle dei moduli,
registrando l'esito.

- eta0 = 3,56·10⁻²⁵ G/Mx; sigma_x² = (0,5·eta0)²; sigma_i² = eta0²; Z = Phi⁻¹(0,9875) da `scipy.stats.norm`.
- Varianza individuale stimata: s²_i = exp(a + b(log phi_i − media(log phi))), con (a, b) da `P.varfun_fit`.
- Varianza di cella v_c = Σ_{i∈c} agg_i² · s²_i, contrasto b = g, parte individuale Σ_c b_c² v_c.
- Tempi t_c = CR_c − min CR, emisfero h_c = 1 per S.
- Covarianza vera K: scenario 7 = max(0, 1 − |Δt|/20) solo nello stesso emisfero; scenario 10 =
  max(0, 1 − |Δt|/13) fra tutte le celle; scenari 1 e 2 = phi^|Δt| nello stesso emisfero e
  kappa·phi^|Δt| fra emisferi, con (phi, kappa) = (0,5; 0) e (0,9; 0) dal protocollo P2f.
- A2p: phi* ricalcolato con una propria ricerca su griglia (passo 10⁻⁴ in [0; 0,98], ritardi 0…218,
  minimi quadrati a pesi uguali contro K_steps); deve dare 0,9106 (L = 20) e 0,8657 (L = 13);
  kappa* = 0 nello scenario 7 e 0,98 nello scenario 10.
- Var = sigma_x² · bᵀKb + parte individuale (individuale vera per A3, stimata per A2 e A2p);
  SE = sqrt(Var); lo, hi = beta ∓ Z·SE; verdetto, covered, below e above con le regole del rapporto (§5).

## 4. Confronti

**(a) Contro `ORACLE_RAW.csv.gz`**, per ogni catalogo e per i bracci A2, A3 e A2p: beta, SE, lo, hi,
stato (`errore` o valido), verdetto, covered, below e above. Si confronta beta anche per A0, che ha lo
stesso beta: è il controllo di rigenerazione del catalogo.

**(b) Contro i componenti del produttore**, ricalcolati nello stesso processo con le funzioni del
produttore (`diag_t5_oracle.k_true`, `est_sig2`, `PHI_STAR`; `V.cell_level`; `P.ar1_k`). Gli output
salvati contengono solo l'SE finale. Si confrontano: b; v_c vera e stimata; parte individuale vera e
stimata; bᵀK_vera b; bᵀK_A2p b; varianza totale per braccio.

**Tolleranze, fissate qui:** un valore x passa contro il riferimento y se
|x − y| ≤ atol + rtol·|y|, con rtol = 10⁻⁹ e atol = 10⁻¹² × la scala naturale della grandezza.

| Grandezza | Scala per atol |
|---|---|
| beta, SE, lo, hi | eta0 |
| varianze (totale, sigma_x²·bᵀKb, parte individuale, v_c) | eta0² |
| bᵀKb (adimensionale rispetto a b) | max_c b_c² |
| vettore b | max_c abs(b_c) |

Per i vettori si usa il massimo su tutte le componenti. Verdetti, covered, below, above e stati devono
essere identici. Le tolleranze non si cambiano dopo aver visto gli esiti.

## 5. Errori: definizione e classificazione

- **Errore atteso concordante:** nel ricalcolo il pezzo condiviso (`P.varfun_fit` o s² non finita)
  solleva `CandidateError`, oppure v_c non è finita o positiva. Nello stesso catalogo il raw ha
  `errore` per lo stesso braccio, e il messaggio salvato rientra nella stessa classe (funzione di varianza
  o varianze di cella). Si conta a parte e **non** vale come verifica numerica: un errore uguale in due
  codici che condividono quel pezzo non ne certifica la correttezza.
- **Errore inatteso:** qualunque eccezione del codice indipendente diversa da `CandidateError` del pezzo
  condiviso; un `errore` di A3, che per costruzione non deve darne; un `errore` da una parte e un valore
  dall'altra; un messaggio di classe diversa.
- Si riportano a parte le frequenze di errore per scenario e braccio, sui tentativi. Nelle grandezze
  appaiate del rapporto (§6.5) l'errore vale 0 per l'evento «verdetto deciso» sotto nulla e 1 per la
  mancata copertura sotto effetto. Questa nota non le ricalcola.

## 6. Esito

**Superato** se valgono tutte queste condizioni:
- beta rigenerato coincide con il raw in tutti i 32000 cataloghi;
- tutti i confronti (a) e (b) delle righe valide sono entro tolleranza;
- verdetti, flag e stati sono identici;
- tutti gli errori sono attesi e concordanti;
- non ci sono errori inattesi;
- phi* e le costanti coincidono.

**Non superato** altrimenti. In quel caso ci si ferma e si conserva il rapporto del fallimento, senza
modificare gli output T5-D2, il produttore o le tolleranze. La discrepanza si chiarisce prima di toccare
il rapporto dei risultati.

**Cosa significa un esito superato:** la costruzione degli SE di A2, A3 e A2p è verificata entro le
dipendenze condivise del §2. Non verifica il generatore, l'aggregazione, la funzione di varianza, la
REML, i bracci A0, A1a e A1b, né l'ambiente della corsa. Non è una nuova validazione di T5. T5 resta
descrittivo e T3 non deciso. La lettura del rapporto non cambia; cambia solo il limite dichiarato.

## 7. Esecuzione

1. Script `scripts/t5_oracle_se_recompute.py`, scritto dopo il commit di questa nota.
2. `--selftest`: prova su un caso costruito a mano, piccolo (tre celle, K, b e v noti, varianza calcolata
   a mano), più l'alterazione deliberata di un valore per controllare che il confronto la rilevi. Non usa
   cataloghi della corsa.
3. Esecuzione completa unica, distaccata, su commit pulito, in parallelo. Output in
   `results/T5_ORACLE_SE_RECOMPUTE/`:
   - `ROWS.csv.gz` (per catalogo e braccio);
   - `SUMMARY.csv` (per scenario e braccio: N, confronti superati, scarti massimi assoluti e relativi,
     errori attesi e inattesi);
   - `META.json` (commit, SHA-256 di questa nota, dello script e di `ORACLE_RAW.csv.gz` prima e dopo,
     costanti, phi*, versioni dell'ambiente, esito).
4. Prima dell'esecuzione completa la nota e lo script si inviano al revisore (Codex).

Non si modificano produttore, output T5-D2 o protocolli; nessun push.

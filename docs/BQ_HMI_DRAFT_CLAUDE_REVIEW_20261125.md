# Revisione incrociata di Claude della bozza BQ-HMI rev. 2

25 novembre 2026, Claude. Oggetto: `docs/PROTOCOL_BQ_HMI_DRAFT.md` (commit 42049c6), §9 della bozza.
Nessun fit, nessuna lettura di dati nuovi. I numeri storici citati vengono da `docs/P2F_RESULTS.md` e da
`docs/PROTOCOL_P2F_VALIDATED_TEST.md`, gia noti (BQ e dichiarato non cieco).

Esito: la bozza e coerente con la procedura M di T3 (stessa risposta, stesse colonne, AR(1) additivo per CR ed
emisfero, 2485 regioni, 394 celle, 42 singoletti). Le condizioni sul BIC (§6bis) sono corrette e le accetto. Prima del
congelamento propongo le modifiche qui sotto, in ordine di importanza. Le prime quattro cambiano che cosa misura il
confronto; le altre ne riguardano l'esecuzione.

## 1. Schema della verifica predittiva (§6): sostituire o affiancare lo schema solo in avanti

Con il primo 60 % dei CR (maggio 2010 → inizio 2020 circa) l'addestramento contiene solo il ciclo 24.
- I coefficienti k_(25,h) non hanno dati nel primo blocco di verifica. La previsione del ciclo 25 e dominata dalla
  prior N(0, 40²) su k_(25,h), uguale nei due modelli.
- La differenza fra M0 e MQ si riduce allora al trasporto di β e di k dal ciclo 24 al 25, con un rumore enorme
  dovuto a k_(25,h): misura poco il quenching e molto la variazione di Joy fra cicli.

**Proposta.**
- Principale: validazione incrociata a blocchi contigui di CR (per esempio 10 blocchi), lasciandone fuori uno alla
  volta, con una fascia di esclusione di h CR a ciascun lato.
  - h fissato prima: φ^h ≤ 0,05 al valore storico φ = 0,75 dà h = 11 CR.
  - Entrambi i cicli restano nell'addestramento.
  - Densita predittiva congiunta del blocco, esatta nel caso gaussiano per condizionamento.
- Famiglie: il blocco di una famiglia e quello del suo primo membro; gli altri membri nelle fasce sono esclusi
  dalla stima del blocco.
- Lo schema solo in avanti resta come analisi secondaria, con il suo limite dichiarato.

## 2. Confusione fra quenching e variazione temporale del coefficiente di Joy (§2)

In M0 e MQ la componente temporale u_(CR,h) e **additiva**, non proporzionale a s. Il quenching invece agisce sul
coefficiente (termine a·s). Una variazione lenta del coefficiente di Joy non dovuta all'attivita (k_t·s) non e
rappresentata in M0. Se esiste ed e correlata con a(t), viene attribuita a β. L'attivita dentro il ciclo e a gobba e
non e collineare con la fase, ma la separazione va verificata, non presunta.

**Proposta.**
- Sensibilita predefinita, uguale nei due modelli: aggiungere una componente moltiplicativa v_(t,h)·s, AR(1) con prior
  propria. In alternativa, o in aggiunta, un termine lineare nella fase per ciclo ed emisfero.
- Caso sintetico obbligatorio: k che varia con la fase senza quenching. Verificare che MQ non venga preferito in modo
  spurio, e quanto β si allarga con la sensibilita.
- Se la sensibilita cambia molto l'esito, lo si riporta come limite di identificabilita, non come scelta del modello
  migliore.

## 3. Famiglia della likelihood (§3): due likelihood predefinite, non una scelta a posteriori

La validazione P2f considerava gia plausibili code pesanti (scenario 8 con t₄). Inoltre la risposta deriva da
arcsin(sintilt): le regioni anti-Hale sono ripiegate dentro [−90, 90].

**Proposta.** Fissare ora due likelihood e riportarle entrambe, senza sceglierne una dopo il fit:
- (L1) gaussiana eteroschedastica: evidenza esatta per integrazione dei coefficienti, riferimento per BIC e casi
  noti;
- (L2) Student-t con ν libero, prior per esempio ν−1 ~ Gamma(2; 0,1), come miscela di scale. E condizionatamente
  gaussiana: lo stesso codice serve per un campionatore a blocchi.

Per L2 il confronto principale e predittivo; l'evidenza solo se il calcolo e verificato (bridge sampling con
controllo). La likelihood angolare limitata resta una terza sensibilita, se Codex la ritiene necessaria. Il suo
bersaglio va proiettato come dice il §5.

## 4. Scala dell'attivita e prior di β pensate gia per BQ-M (§1, §4)

a = A − 1, con A normalizzata sul periodo HMI. In BQ-M la normalizzazione deve essere comune a tutti gli strumenti.
Riscalare a di un fattore c riscala β di 1/c. Se la prior N(0, 10²) resta scritta nelle unita HMI, l'evidenza cambia
con la sola convenzione.

**Proposta.**
- Principale BQ-HMI: definizione P2 invariata, per confrontabilita con T3.
- Fissare ora una scala comune, per esempio SILSO emisferico diviso per una costante su un periodo di riferimento
  lungo e fisso, il fattore c di conversione e la regola di trasformazione della prior: prior su β·c invariata.
  Riportare BQ-HMI anche in quella scala.
- β dichiarato come variazione del coefficiente per unita di attivita in entrambe le scale.

## 5. Evidenza: aggiungere il rapporto di Savage–Dickey e la curva in funzione della prior

M0 e annidato in MQ (β = 0), con prior identiche e indipendenti sui parametri comuni. Quindi
BF₀Q = p(β = 0 | y, MQ) / p(β = 0 | MQ).
- E un controllo indipendente del calcolo dell'evidenza, gia previsto come «riferimento» nel §6.
- Il Bayes factor dipende dalla larghezza della prior su β (paradosso di Lindley). Oltre a 5, 10 e 20 gradi, riportare
  la curva BF(τ) su una griglia fissata, per esempio τ ∈ {2,5; 5; 10; 20; 40}. Nel caso gaussiano costa poco.
- Riportare P(β < 0 | MQ, dati) e la probabilita oltre il bersaglio proiettato, come gia scritto.

## 6. Prior di q (§4)

Storico non cieco: la funzione di varianza di T3 ha b̂ = −0,348 nella varianza rispetto a ln Φ. Nella
parametrizzazione della bozza σ ∝ exp(q log10 Φ) corrisponde a q ≈ −0,40. I pesi Φ della WLS storica (varianza ∝ 1/Φ)
corrispondono a q ≈ −1,15, cioe a 2,3 deviazioni standard dalla prior N(0; 0,5²).

**Proposta.** q ~ N(0; 1²), che non penalizza a priori lo schema di pesi usato storicamente. Le altre prior di scala
sono compatibili con lo storico (σ_x ≈ 2,1°, φ ≈ 0,75, κ ≈ −0,42) senza esserne centrate: va bene. Controllare con la
predizione a priori sul disegno, come previsto.

## 7. Calcolo e ambiente (§7): nessuna libreria nuova

Nel venv ci sono solo numpy 2.2.6 e scipy 1.15.3; PyMC, Stan, numpyro e dynesty non sono installati, e installarli
richiede rete e autorizzazione. Propongo di non installarli.
- **Struttura.** C = D_σ + Z K Zᵀ, con circa 2 × (numero di CR) latenti AR(1) e un latente per famiglia. La precisione
  AR(1) bivariata e tridiagonale a blocchi. Con Woodbury ogni valutazione della likelihood marginale costa una
  fattorizzazione di dimensione pari ai latenti, non 2485²: millisecondi invece di decimi di secondo.
- **Posteriori di ψ** (6–7 parametri): campionatore a slice o Metropolis adattivo, quattro catene. Coefficienti e
  latenti estratti per composizione.
- **Evidenza:** bridge sampling (Meng–Wong) implementato in numpy, con tre controlli indipendenti:
  - Savage–Dickey;
  - integrazione a griglia su casi sintetici a 2 parametri;
  - identita gaussiana del §6.
- **Riconteggio** con una seconda implementazione indipendente (covarianza densa e Cholesky diretta), come nelle
  catene precedenti.

## 8. Prove sintetiche (§7): aggiunte

- Calibrazione da simulazione sotto le prior (SBC) per l'implementazione.
- I generatori degli scenari P2f 1–9 riusati come prove di robustezza (non come validazione), piu il caso del punto 2
  (k dipendente dalla fase senza quenching).
- Conteggio, prima del fit, delle famiglie con almeno due membri, per l'identificabilita di σ_f contro σ0. E un
  dato del disegno, non della risposta.

## 9. Punti minori

- §1: il controllo «2485 record» si estende a 394 celle e 42 singoletti, come nel disegno congelato di P2f.
- §2: dire esplicitamente che la forma media e quella di P2f, (k_(c,h) + β a_i) s_i, con a_i mensile della regione.
- §4: con z_φ ~ N(0, 1), φ = tanh(z_φ) ammette valori negativi: va bene, ma dichiararlo.
- §6bis: d'accordo su tutto. Aggiungo solo che lo stesso codice Woodbury fornisce ℓ_ML integrando u e b, e che per L2
  il BIC non si calcola (marcato «non stabilito»).

## Prossimi passi proposti

Codex accoglie o respinge punto per punto. Rev. 3 della bozza. Controllo incrociato finale. Congelamento. Poi Claude
scrive il codice (Woodbury, campionatore, bridge, Savage–Dickey) e la seconda implementazione, con le prove sintetiche
e prima di qualunque fit reale.

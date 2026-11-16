# Quanta informazione in più servirebbe? Piano prospettico per T5 e T3 — bozza

**BOZZA NON CONGELATA, revisione 2 — 2026-11-16**, dopo la revisione di Codex della revisione 1 (`630e6dc`),
recepita (§11). Da rivedere di nuovo **prima di qualunque calcolo**. Nessun calcolo prospettico, nessuna
simulazione e nessun dato MDI usati per scriverla; i numeri del §2 sono descrittori del disegno HMI esistente o
risultati già conservati. **Non cieco**: risultati T3, validazione P2f, T5-D1/D2 e sensibilità della potenza sono
noti.

## 0. Portata

La valutazione è **condizionata agli stimatori studiati**: la pendenza WLS di T5 sulle celle (procedura M e il suo
riferimento a varianza nota O) e la pendenza WLS di T3 sui record. Non valida T5 né T3, non applica nulla ai dati
reali, non stima il beneficio di stimatori diversi. Serve a una sola decisione: se un'estensione dei dati possa
rendere distinguibile lo scenario prescritto, e quale, prima di investire su MDI o su un metodo HMI diverso.
M **non è validata sui disegni estesi**: le sue proprietà lì sono un oggetto della fase B, non un presupposto.
MDI operativo e studio morfologico di S restano in pausa. Le pipeline storiche (P1, P2, P2f, potenza T5) non
cambiano.

## 1. Domanda

Sotto ipotesi esplicite sul rumore e sugli scarti fra strumenti, **quante osservazioni solari aggiuntive**
(anni, rotazioni di Carrington, regioni) servirebbero perché la riduzione prescritta del 20 % della componente di
Joy sia riconosciuta con una frequenza utile, con falsi verdetti controllati, **separatamente per T5 e per T3**?
Le repliche Monte Carlo non sono osservazioni: servono solo a stimare con precisione la potenza di un disegno dato.

## 2. Elementi fissati

**Scenario prescritto** (dalla [nota del proxy](T5_PROXY_SENSITIVITY_NOTE.md), invariato): γ' = γ − δ·24°·sin|λ|,
con δ = δ(Â_c) che sale linearmente da 0 al quantile 5 % a δ_max al quantile 95 % dell'attività di cella Â_c
replicata sui record T5. Principale δ_max = 0,20; secondario δ_max = 0,10.

**Quantili e normalizzazione HMI fissi (scelta principale).** I quantili A_lo e A_hi della rampa restano quelli
calcolati sul disegno HMI attuale, e la normalizzazione dell'attività resta la media HMI 2010-05 → 2026-09, anche
sui disegni estesi: così l'effetto fisico prescritto è lo stesso e il confronto misura il beneficio dei dati
aggiunti. **Sensibilità**: quantili ricalcolati sulla serie estesa, riportati a parte.

**Bersagli, ricalcolati per ogni disegno e per ogni matrice del modello** (anche quella protetta, §4):
- **T5**: proiezione WLS delle variazioni di cella Δη_c prodotte dal proxy (stessa formula della nota del proxy,
  record per record) sulla matrice T5 (intercetti ciclo × emisfero, colonna Â_c − 1, pesi W_c = ΣΦ). Sul disegno
  attuale vale −3,669·10⁻²⁶ G/Mx = **−0,1031·η̄** per δ_max = 0,20 e −0,0515·η̄ per 0,10 (`39c010c`), non −0,2·η̄.
- **T3**: proiezione WLS delle variazioni di tilt dei record Δγ_i = −δ(Â_c(i))·24°·sin|λ_i| sulla **matrice T3
  completa** del codice (`p2d.design_t3`): intercetti ciclo × emisfero moltiplicati per sin|λ_i| e colonna
  (Â_i − 1)·sin|λ_i|, con l'attività del record, pesi Φ_i; il bersaglio è l'ultimo coefficiente. Non ancora
  calcolato: è il passo A0. Si riporta accanto al bersaglio storico della griglia T3 (−0,2·γ₀).

**Livello**: intervallo nominale 97,5 %, un verso all'1,25 % (z = 2,2414), come in P2f.

**Disegno HMI di riferimento (E0)**, descrittori: CR 2096–2316 (221 rotazioni, 210 con record); T5 318 celle
(168 N, 150 S) in 176 rotazioni, 2375 record, 7,5 record per cella; T3 2485 record in 394 celle; deviazione
standard pesata dell'attività di cella 0,82. Dalla sensibilità della potenza già conservata: deviazione standard
di β̂_WLS di T5 sotto nulla 0,07–0,27·η̄ a seconda del rumore, 0,10–0,14·η̄ alla scala P2f.

## 3. Estensioni e generatore dei disegni

| Codice | Che cosa aggiunge |
|---|---|
| E0 | nulla (riferimento) |
| E1 | maturazione HMI: 5 anni dopo 2026-09, con attività **trasferita dal ciclo 24** (regola sotto) |
| E2 | MDI, copertura **nominale** 1996-01 → 2010-04 (le rotazioni da maggio 2010 sono già HMI), esclusa la lacuna giugno–ottobre 1998 |
| E3 | E1 + E2 |
| E4 | come E2, con scarti fra strumenti nulli: riferimento ottimistico, solo analitico |

**Trasferimento temporale di E1** (ipotesi dichiarata, non previsione): sia t₂₅ l'intervallo fra il massimo
smussato del ciclo 25 e 2026-09, con i massimi calcolati dalla serie SILSO emisferica a 13 mesi già usata in
`run_p2` (`smooth13`, somma dei due emisferi). La finestra analoga è il quinquennio del ciclo 24 che inizia a
t₂₅ dopo il massimo smussato del ciclo 24. Le rotazioni di E1 seguono 2316 in ordine, e la k-esima rotazione di E1
prende le celle e l'attività emisferica della k-esima rotazione della finestra analoga.

**Rotazioni di E2**: tutte le CR il cui inizio cade in 1996-01-01 → 2010-04-30, escluse quelle che intersecano
1998-06-01 → 1998-10-31; numerazione reale delle CR. Attività: SILSO emisferico mensile osservato, con la
normalizzazione HMI fissa. Cicli: le rotazioni prima del minimo del ciclo 24 (`run_p2.T_MIN[24]` = 2008-12-01)
appartengono al ciclo 23, le successive al ciclo 24 (per le celle, l'etichetta di ciclo del modello viene dalla
regola delle celle modello, sotto).

**Celle modello: ricampionamento congiunto.** Ogni cella aggiunta (CR × emisfero) è una **copia completa di una
cella HMI esistente** del campione S, con tutti i suoi record e tutte le colonne (Φ, latitudine, d, tilt,
segno di Hale, orientamento, D*, ciclo relativo), così che dipendenze fra flusso, latitudine, geometria e
orientamento magnetico restano quelle osservate. La cella modello si estrae, con semi fissati, fra le celle HMI
dello stesso emisfero, della stessa classe di fase del ciclo (cinque classi di uguale ampiezza fra minimo e minimo
successivo, misurate dal minimo del proprio ciclo) e della stessa classe di attività (terzili dell'attività di
cella HMI). Se una classe è vuota si unisce alla classe di attività adiacente, con regola registrata. L'attività
dei record copiati è sostituita da quella della rotazione di arrivo (record per T3, media di cella per T5); la
latitudine resta quella della cella modello. Etichetta di ciclo: «vecchio» o «nuovo» della cella modello,
trasferita ai cicli (23, 24) in E2 e (25, 26) in E1. Le CR senza attività registrata o con attività nulla non
ricevono celle. Nessuna cella è inventata fuori dalle classi osservate.

**Resa e rumore MDI (griglie esplorative, non valori plausibili).** Per E2 ogni record della cella copiata è
conservato con probabilità f ∈ {0,5; 0,75; 1} (seme fissato), poi si applicano le stesse selezioni: celle T5 con
almeno 3 regioni, celle T3 con almeno una regione e singoletti esclusi dalla stima come oggi. Conteggi quindi
interi; celle vuote eliminate. Il rumore individuale dei record MDI è moltiplicato per k ∈ {1; 1,5; 2}.

**Colonne del modello**: intercetti ciclo × emisfero per tutti i cicli presenti (23, 24, 25, e 26 in E1),
più, nei modelli con MDI, un intercetto separato per la parte MDI del ciclo 24 (§4). **Covarianza temporale**
calcolata sulle distanze reali fra numeri di CR, lacune comprese; le CR assenti non entrano.

**Realizzazioni del disegno**: 20 per estensione e combinazione di f, con semi nuovi; si riportano mediana,
minimo e massimo delle grandezze del §5. Non sono repliche di rumore.

## 4. Rumore e scarti fra strumenti

**Rumore temporale**: le 3 forme × 3 scale della sensibilità della potenza (AR(1) φ = 0,5 e 0,9, salti di 20 CR;
scale 0,5, 1, 2 della scala P2f), stessa ampiezza sui due strumenti. **Rumore individuale**: come nel generatore
P2f (T5: η̄ per record; T3: SD_E = 15°), per i record MDI moltiplicato per k.

**Scarti strumentali** sui soli record MDI, distinti per test.
- **T5** (in G/Mx, sulla risposta z_i = D*_i/Φ_i): s = c₀ + c₁·(Â − 1) + c₂·(t − t_ref)/T.
- **T3** (in gradi, sul tilt): due tipi distinti. Scarto **additivo del tilt** s_a = a₀ + a₁·(Â − 1), non
  moltiplicato per sin|λ|: non è assorbito dagli intercetti, che contengono sin|λ|. Scarto **del coefficiente di
  Joy** s_J = (j₀ + j₁·(Â − 1))·sin|λ|: j₀ è assorbito dagli intercetti del ciclo 23 ma non nel ciclo 24 misto,
  j₁ entra nella pendenza. Deriva temporale come per T5.

Griglie: coefficienti di attività (c₁, a₁, j₁) ∈ {0; ±0,25; ±0,5} × |bersaglio del test|; costanti (c₀, a₀, j₀) ∈
{0; ±0,5} × la deviazione standard degli intercetti stimati in E0; derive (c₂) ∈ {0; ±0,25} × |bersaglio| sull'intero
periodo MDI. Tutti i valori sono ipotesi esplorative: la sovrapposizione del 2010, vicina al minimo, non permette di
misurarli.

**Tre modelli, ciascuno con il parametro che stima dichiarato:**
- **(a) attuale**: un'unica pendenza comune ai due strumenti, intercetti ciclo × emisfero più l'intercetto della
  parte MDI del ciclo 24. Stima la pendenza comune **se** gli scarti dipendenti dall'attività sono nulli; altrimenti
  è distorta.
- **(b) protetto**: pendenze separate per HMI e MDI (termine strumento × attività). Il parametro d'interesse è la
  pendenza HMI, identificata essenzialmente dai soli dati HMI: **l'informazione aggiuntiva di MDI sulla pendenza
  può essere interamente assorbita dal termine strumentale**. Si riporta per mostrare quanto beneficio resta quando
  lo scarto non è vincolato; per E1 coincide con (a).
- **(c) distorsione limitata**: modello (a) con l'ipotesi |c₁| (o |a₁|, |j₁|) ≤ C, con C dalla griglia; si riporta
  la frequenza di riconoscimento e di falso verdetto nel caso peggiore entro il limite, cioè con lo scarto di segno
  più sfavorevole.
Per ogni disegno si riporta anche la **tolleranza**: lo scarto dipendente dall'attività che sposta la pendenza (a)
di metà del bersaglio.

## 5. Valutazione: prima analitica, poi solo le simulazioni necessarie

**A0. Bersagli** (§2) per T3 e T5, su E0 e su ogni disegno esteso e matrice. Deterministico.

**A1. Precisione e distorsione analitiche della WLS.**
- **T5**, sulle celle: Var(β̂) = σ_x²·bᵀKb + Σ_c g_c²·v_c, con g la riga WLS di cella, b = g, K la covarianza
  temporale vera sulle CR reali e v_c la varianza di cella dal rumore individuale (con k per MDI), come il
  riferimento O della sensibilità della potenza.
- **T3**, sui record: parte individuale Σ_i a_i²·σ_i², con a la **riga WLS dei record** e σ_i la deviazione del
  rumore individuale del tilt (con k per MDI); parte temporale σ_x²·bᵀKb con b_c = Σ_{i∈c} a_i, aggregata per cella
  come in `cell_level` per T3. La formula sulle medie di cella di T5 non la sostituisce.
- **Distorsione** dagli scarti: m = Σ (riga WLS)·s sulle unità del test.
- **Frequenze nel riferimento normale, con il segno della distorsione**: con β̂ ~ N(Δβ + m, SE²) e z = 2,2414,
  `supportato` ha frequenza Φ(−z − (Δβ + m)/SE) e `opposto` Φ(−z + (Δβ + m)/SE). Sotto nulla (Δβ = 0) le stesse
  formule danno i falsi verdetti **prodotti dallo scarto**: uno scarto negativo aumenta i «riconoscimenti» anche
  senza quenching. Copertura del bersaglio: Φ(z − m/SE) − Φ(−z − m/SE).
- Prodotti per test, estensione, modello, rumore, f, k e scarto: SE/|Δβ|, m/|Δβ|, frequenze di `supportato`,
  `opposto` e copertura sotto nulla e sotto lo scenario, e la tolleranza.

**B. Simulazioni con M, solo per le combinazioni scelte da un algoritmo fissato ora.**
1. *Insieme candidato*: {T3, T5} × {E1, E2, E3} × {(a), (b)} × {ar1_05, ar1_09, steps20} alla scala P2f ×
   coefficiente di attività dello scarto ∈ {0; −0,5; +0,5} × |bersaglio| (costanti e derive nulle), con f = 0,75 e
   k = 1,5 per E2 ed E3. Per E1 lo scarto non esiste e il modello (b) coincide con (a): una sola riga per rumore.
   E4 e il modello (c) restano solo analitici.
2. *Indice*: per ogni candidato, la frequenza analitica di `supportato` sotto lo scenario, p_min e p_max sulle 20
   realizzazioni del disegno.
3. *Selezione*: un candidato AR(1) è scelto se [p_min, p_max] interseca [0,20; 0,90]; un candidato steps20 se
   interseca [0,10; 0,95], banda più larga perché nei salti l'approssimazione normale è meno affidabile. Nessuna
   altra eccezione: un candidato fuori dalla sua banda non è simulato.
4. *Realizzazione del disegno simulata*: quella con p mediana fra le 20; a pari merito la prima per seme.
5. *Tetto*: al più 24 candidati. Se sono di più si tengono quelli con |p_mediana − 0,5| minore, a pari merito
   nell'ordine dell'insieme candidato (T3 prima di T5, poi estensione, modello, rumore, scarto).
6. *Per ogni candidato scelto*: 1000 cataloghi **sotto nulla e 1000 sotto lo scenario**, con lo stesso rumore
   appaiato e gli stessi scarti; si riportano falsi verdetti per verso, `supportato`, copertura, R ed errori, con
   denominatori espliciti, e il confronto con la previsione analitica.
7. *Semi*: candidato j-esimo dell'elenco ordinato, rumore 34 000 000 + 10 000·j + k, k = 0…999 (gli stessi semi
   per nulla e scenario); estrazioni del disegno 34 900 000 + 100·e + r. Disgiunzione da tutti gli intervalli già
   usati verificata dal codice.
8. *Tetto operativo*: benchmark prima del lancio come in A1 del piano di potenza; arresto prima della griglia se
   la durata prevista supera 8 ore su 12 processi.

## 6. Significato dell'obiettivo del 50 %

Obiettivo **operativo**, non una garanzia: un'estensione è «potenzialmente sufficiente» per un test se, alla scala
di rumore P2f, con il modello (a) e scarti nulli, la riduzione del 20 % è riconosciuta almeno metà delle volte, e
se con il modello (c) al limite C = 0,25·|bersaglio| i falsi verdetti restano vicini al nominale. Motivo della
soglia: sotto il 50 % un investimento su nuovi dati darebbe più spesso un esito non deciso che un riconoscimento
anche se lo scenario fosse vero. Con il 50 % un mancato riconoscimento resta poco informativo. La frequenza con cui
l'intervallo esclude la riduzione del 20 % sotto nulla si riporta come lettura complementare, ma **nel riferimento
normale senza distorsione coincide con il riconoscimento dell'alternativa simmetrica**: non è una seconda garanzia
indipendente, e sul singolo risultato conta l'intervallo effettivamente ottenuto. La scelta finale resta
dell'utente con Codex.

## 7. T5 e T3: benefici distinti

- **T5** usa le celle e l'efficienza η = ΣD*/ΣΦ; con MDI richiede un D* da campo LOS, la cui confrontabilità non è
  verificata. Partenza bassa: riconoscimento 8–11 % alla scala P2f in E0.
- **T3** usa i record e il tilt dai centroidi, influenzato da risoluzione e morfologia; bersaglio da A0. Partenza:
  potenza della validazione P2f del 4,6–11,1 % a −0,2·γ₀.
- Scarti di natura diversa (in G/Mx per T5, in gradi e di due tipi per T3), griglie definite in unità del
  rispettivo bersaglio. Un'estensione insufficiente per un test può essere utile per l'altro; nessuna delle due
  valutazioni esclude il valore descrittivo di una serie MDI.

## 8. Che cosa non fa

Nessun dato MDI, nessuna verifica della confrontabilità reale, nessun nuovo stimatore, nessuna decisione
automatica. I disegni estesi sono copie ricampionate di celle HMI con attività di altri periodi: dicono «sotto
queste ipotesi, con la WLS studiata», non quanto il Sole renderebbe osservabile.

## 9. Sequenza

Revisione di questa bozza → congelamento → codice e prove offline (bersagli A0 riprodotti su E0: T5 −0,1031·η̄
dalla nota del proxy; varianza A1 di T5 su E0 uguale al riferimento O della sensibilità della potenza; T3 su E0
uguale alla parte individuale e temporale di `cell_level`) → A0 e A1 → selezione B e benchmark → eventuale B →
rapporto e revisione.

## 10. Punti ancora aperti

1. Ampiezze delle griglie degli scarti e limite C del §6.
2. Numero di classi di fase e di attività per il ricampionamento, e regola di unione delle classi vuote.
3. Se le celle modello di E1 debbano venire solo dalla finestra analoga del ciclo 24 (come scritto) o da tutte le
   celle HMI della stessa classe.

## 11. Revisione di Codex della revisione 1, recepita

1. T3 con bersaglio e varianza propri: proiezione sulla matrice T3 completa con sin|λ| e pesi Φ, parte individuale
   Σ a_i²σ_i² con la riga dei record (§2, §5).
2. Modello protetto con il parametro dichiarato: la pendenza MDI può essere assorbita dal termine strumentale;
   tenuti (a) e (b) per entrambi i test, aggiunto (c); per T3 distinti scarto additivo del tilt e scarto del
   coefficiente di Joy (§4).
3. Generatore completo: ricampionamento congiunto di celle intere con latitudine, ciclo, geometria e orientamento;
   regole per conteggi interi, celle vuote, selezioni T3/T5, colonne dei cicli 23–26, covarianza sulle CR reali
   con le lacune; pipeline storiche invariate (§3).
4. Quantili e normalizzazione HMI fissi come scelta principale, quantili estesi come sensibilità; bersagli
   ricalcolati per disegno e matrice, compreso il modello protetto (§2).
5. Scarti nella valutazione: frequenze con il segno della distorsione, sotto nulla e sotto lo scenario; fase B con
   entrambi, falsi verdetti, copertura ed errori; M non validata sui disegni estesi (§0, §5).
6. Fase B come algoritmo univoco: insieme candidato, indice, bande, precedenza dei salti, realizzazione mediana,
   tetto, semi, benchmark (§5).
Precisazioni: f e k griglie esplorative; trasferimento temporale di E1 fissato esattamente; la frequenza di
esclusione sotto nulla coincide, senza distorsione, con il riconoscimento dell'alternativa simmetrica (§3, §6).

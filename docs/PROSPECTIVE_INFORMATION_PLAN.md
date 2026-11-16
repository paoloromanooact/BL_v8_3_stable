# Quanta informazione in più servirebbe? Piano prospettico per T5 e T3

**CONGELATO il 2026-11-16 come piano conservato, NON avviato.** Il congelamento fissa le regole per un eventuale uso
futuro; l'avvio richiede una decisione esplicita dell'utente (la priorità attuale è tornare ai dati reali MDI:
inventario dei metadati e campione nella sovrapposizione). Da questo commit il file non si modifica; ogni
cambiamento è un emendamento registrato prima dell'uso. SHA-256 e commit del congelamento sono registrati fuori da
questo file, in `docs/PROSPECTIVE_INFORMATION_PLAN_FREEZE.json`. Testo della revisione 4 — dopo le revisioni di Codex della revisione 1 (`630e6dc`,
§11), della revisione 2 (`c4247d0`, §12) e della revisione 3 (`62661f2`, §13), recepite; le revisioni 3 e 4
cambiano solo definizioni, nessuno scenario nuovo. Da rivedere di nuovo **prima di qualunque calcolo**. Nessun calcolo prospettico, nessuna
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

**Bersagli, ricalcolati per ogni disegno e per ogni matrice del modello** (anche quelle protette, §4). Il
coefficiente d'interesse è sempre identificato **per nome di colonna** (§4), non come «ultimo coefficiente»:
- **T5**: proiezione WLS delle variazioni di cella Δη_c prodotte dal proxy (stessa formula della nota del proxy,
  record per record) sulla matrice T5 (§4), coefficiente della colonna x₅ = Â_c − 1, pesi W_c = ΣΦ. Sul disegno
  attuale vale −3,669·10⁻²⁶ G/Mx = **−0,1031·η̄** per δ_max = 0,20 e −0,0515·η̄ per 0,10 (`39c010c`), non −0,2·η̄.
- **T3**: proiezione WLS delle variazioni di tilt dei record Δγ_i = −δ(Â_c(i))·24°·sin|λ_i| sulla **matrice T3
  completa** del codice (`p2d.design_t3`): intercetti ciclo × emisfero moltiplicati per sin|λ_i| e colonna
  (Â_i − 1)·sin|λ_i|, con l'attività del record, pesi Φ_i; il bersaglio è il coefficiente della colonna
  x₃ = (Â_i − 1)·sin|λ_i|. Non ancora calcolato: è il passo A0. Si riporta accanto al bersaglio storico della griglia T3 (−0,2·γ₀).

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

**Posti e date.** Un *posto* è una coppia (CR, emisfero) con osservazioni disponibili. E0: le 221 × 2 coppie di
CR 2096–2316. E2: le CR il cui inizio cade in 1996-01-01 → 2010-04-30, escluse quelle che intersecano
1998-06-01 → 1998-10-31 (dati mancanti, non posti vuoti). E1: le 67 CR successive a 2316. Ogni posto ha la data
d'inizio della sua CR.

**Fase convenzionale.** Fase di un istante rispetto a un ciclo c: (t − m_c)/(11 anni), con m_c il minimo del
ciclo. m₂₄ e m₂₅ sono `run_p2.T_MIN` (2008-12-01, 2019-12-01); m₂₃ è il minimo della serie SILSO smussata a 13 mesi
(`smooth13`, somma dei due emisferi) fra 1995-01 e 1998-12, mese registrato nel piano congelato prima dei calcoli.
Il *ciclo del tempo* di un istante è il ciclo con il minimo più recente; per E1, dove il minimo del ciclo 26 non è
noto, fase e ciclo del tempo sono quelli **della rotazione analoga** (sotto), con il ciclo traslato di +1. Per gli
istanti di E2 **precedenti a m₂₃** (inizio del 1996) il ciclo del tempo è 22 e la fase si calcola rispetto al
minimo convenzionale m₂₂ = m₂₃ − 11 anni (cadono quindi nella classe [0,8; ∞)).
Cinque classi di fase: [0; 0,2), [0,2; 0,4), [0,4; 0,6), [0,6; 0,8), [0,8; ∞).

**Trasferimento di E1** (ipotesi dichiarata, non previsione): sia t₂₅ l'intervallo fra il massimo smussato del
ciclo 25 e 2026-09 (massimi dalla stessa serie `smooth13`). La finestra analoga è il quinquennio del ciclo 24 che
inizia t₂₅ dopo il suo massimo smussato. La k-esima CR di E1 prende **attività emisferica, fase e ciclo del tempo**
dalla k-esima CR della finestra analoga; le celle invece si estraggono dall'**intero insieme HMI** nello strato
corrispondente, come per E2.

**Strati.** Uno strato è (emisfero, classe di fase, terzile di attività emisferica della CR), con i terzili
calcolati sulle CR di E0. Per ogni strato si registrano da E0: il numero di posti, la frazione di posti **senza
alcun record di S** e le celle donatrici (celle T3 di S, cioè con almeno un record). Se uno strato non ha posti o
donatori in E0, si comporta così:
- strato **con posti osservati ma nessun record di S**: probabilità di posto vuoto pari a 1, conservata; non si
  unisce ad altri strati, perché l'unione introdurrebbe osservazioni artificiali;
- strato **senza posti in E0** (nessuna informazione sulla sua probabilità): si unisce secondo un ordine fisso,
  prima il terzile di attività adiacente inferiore, poi quello superiore, poi la classe di fase adiacente
  precedente, poi la successiva, e come ultima risorsa tutte le classi dello stesso emisfero.
Gli **emisferi non si uniscono mai**: copiare una cella nord in un posto sud richiederebbe trasformazioni di
geometria e di orientamento che il piano non definisce. L'ordine è applicato dal codice, senza scelte durante
l'esecuzione, e le unioni sono registrate.

**Generazione di un posto aggiunto.** (1) Con probabilità pari alla frazione di posti vuoti del suo strato in E0, il
posto resta **vuoto** (nessun record di S, che è diverso da dato mancante). (2) Altrimenti si estrae, con semi
fissati, una cella donatrice dello strato e se ne copiano tutti i record con tutte le colonne (Φ, latitudine, d,
tilt, segno di Hale, orientamento, D*), così che le dipendenze fra flusso, latitudine, geometria e orientamento
restano quelle osservate. (3) L'attività dei record copiati diventa quella del posto d'arrivo (per T3 l'attività
del record, per T5 la media di cella ricalcolata). (4) **Etichetta di ciclo**: per ogni record donatore,
o = (ciclo del record) − (ciclo del tempo del donatore), con o ∈ {−1, 0, +1}; il record d'arrivo ha ciclo = (ciclo
del tempo del posto) + o. Il valore +1 esiste nei dati: in S la HARP 7379 del 2019-07-10 è assegnata al ciclo 25,
prima del minimo convenzionale di dicembre 2019 (in S: 2 record con o = +1 e 2 con o = −1 su 2485). Un record il
cui ciclo d'arrivo cadrebbe prima del ciclo 22 si scarta, con conteggio registrato. Così «vecchio» e «nuovo» si trasferiscono senza confondere il ciclo del donatore con quello
d'arrivo. (5) Solo per MDI: ogni record è conservato con probabilità f ∈ {0,5; 0,75; 1} (seme fissato). (6)
Selezioni come oggi: un posto con almeno un record è una cella T3; è anche una cella T5 se ha almeno 3 record. Le
celle T3 con un solo record (singoletti) **restano nella regressione T3** e sono escluse solo dal fit della
funzione di varianza, come nel codice attuale. Conteggi quindi interi; posti senza record eliminati dopo la
selezione.

**Rumore individuale MDI**: moltiplicato per k ∈ {1; 1,5; 2}. f e k sono **griglie esplorative**, non valori
plausibili.

**Colonne e covarianza**: matrici del §4; covarianza temporale sulle distanze reali fra numeri di CR, lacune
comprese.

**Realizzazioni del disegno**: 20 per estensione e valore di f, semi 34 900 000 + 100·e + r (e indice
dell'estensione e di f, r = 0…19); si riportano mediana, minimo e massimo delle grandezze del §5.

## 4. Rumore, scarti fra strumenti e matrici dei modelli

**Rumore temporale**: le 3 forme × 3 scale della sensibilità della potenza (AR(1) φ = 0,5 e 0,9, salti di 20 CR;
scale 0,5, 1, 2 della scala P2f), stessa ampiezza sui due strumenti. **Rumore individuale**: come nel generatore
P2f (T5: η̄ per record; T3: SD_E = 15°), per i record MDI moltiplicato per k.

Notazione: M_i = 1 per i record MDI; I_{c,h} indicatori di ciclo × emisfero per i cicli presenti; I^{M24}_h
indicatore della parte MDI del ciclo 24 nell'emisfero h; t il tempo in anni dal 2010-05-01.

**Famiglie di scarto strumentale** (solo record MDI), con **scale fissate su E0** perché lo stesso scarto fisico
non cambi con il disegno:
- **T5, famiglia F5** (sulla risposta z_i = D*_i/Φ_i, in G/Mx): s = c₀ + c₁(Â − 1) + c₂ t, con c₁ ∈ {0; ±0,25;
  ±0,5} × |Δβ₅(E0)|, c₂ ∈ {0; ±0,25} × |Δβ₅(E0)| per decennio, c₀ ∈ {0; ±0,05; ±0,1} × η̄. Per c₀ **nessun
  risultato conservato** fornisce una scala: sono valori esplorativi dichiarati.
- **T3, famiglia A (additiva del tilt)**, in gradi, non moltiplicata per sin|λ|: s_A = a₀ + a₁(Â − 1), con
  a₀ ∈ {0; ±0,5; ±1} × 2,107° e a₁ ∈ {0; ±0,25; ±0,5} × |Δβ₃(E0)|·s̄, con s̄ la media pesata di sin|λ| in E0 (perché
  a₁ abbia la scala dell'effetto sul tilt). 2,107° è la **mediana della distanza assiale** fra le nostre misure HMI e
  BARD-MDI nella sovrapposizione (P3 C1, `results/P3/P3_BARD_SUMMARY.csv`, `c41fa4c`): una scala di disaccordo,
  non uno scarto con segno misurato.
- **T3, famiglia J (del coefficiente di Joy)**: s_J = (j₀ + j₁(Â − 1))·sin|λ|, con j₀ ∈ {0; ±0,5; ±1} × 2,107°/s̄ e
  j₁ ∈ {0; ±0,25; ±0,5} × |Δβ₃(E0)|.
- Derive per T3 come per T5, in unità di |Δβ₃(E0)|·s̄ per decennio (famiglia A) o di |Δβ₃(E0)| (famiglia J).

**Matrici esatte** (pesi: W_c per T5, Φ_i per T3). Il parametro d'interesse è sempre β, coefficiente di x₅ o x₃.

| Modello | T5 (celle) | T3, famiglia J | T3, famiglia A |
|---|---|---|---|
| (a) attuale | I_{c,h}; I^{M24}_h; x₅ = Â_c − 1 | I_{c,h}·sin\|λ\|; I^{M24}_h·sin\|λ\|; x₃ = (Â − 1)·sin\|λ\| | come J |
| (b) protetto | (a) + M·(Â_c − 1) | (a) + M·(Â − 1)·sin\|λ\| | (a) + M_h (costanti MDI per emisfero) + M·(Â − 1) |

Significato di β nel modello (b), diverso per famiglia:
- **T5 e T3-J**: il termine aggiunto è M·x (M·x₅ o M·x₃), quindi le pendenze di HMI e MDI sono separate e β è la
  pendenza **HMI**, identificata essenzialmente dai soli dati HMI; l'informazione aggiuntiva di MDI sulla pendenza
  può essere interamente assorbita dal termine strumentale.
- **T3-A**: il termine aggiunto è M·(Â − 1), non M·x₃ = M·(Â − 1)·sin|λ|, quindi **non separa le pendenze** del
  coefficiente di Joy. β è il **coefficiente di Joy comune dopo il controllo degli scarti additivi** (costanti MDI
  per emisfero e loro dipendenza lineare dall'attività); quanto MDI contribuisca a β si misura, non si assume. Le derive non sono protette in nessun modello. Per E1 (nessun dato MDI) i modelli (b)
coincidono con (a).

**Condizione di non distorsione**: un modello è non distorto per una famiglia se la **proiezione dello scarto sul
coefficiente β** è nulla, non solo se il coefficiente di attività è nullo. Nel modello (a) possono distorcere β anche
costanti non assorbite (a₀ della famiglia A, c₀ e j₀ nel ciclo 24 se mal assorbite) e derive. La distorsione è
m = Σ (riga WLS di β)·s.

**(c) Analisi di sensibilità alla distorsione** (scelta della revisione 3): **non** è una procedura protetta;
intervalli e verdetti restano quelli ordinari del modello (a). Per un limite C sul coefficiente di attività della
famiglia (|c₁|, |a₁| o |j₁| ≤ C, con C ∈ {0,25; 0,5} nelle unità sopra), si calcolano separatamente: il **caso
peggiore per il riconoscimento** dello scenario (lo scarto con il segno che sposta la pendenza verso zero) e il
**caso peggiore per i falsi riconoscimenti** sotto nulla (lo scarto con il segno che sposta la pendenza verso
valori negativi). Per ogni disegno si riporta inoltre la **tolleranza**: lo scarto di attività che sposta β di metà
del bersaglio.

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
1. *Insieme candidato*: (test, famiglia) ∈ {(T5, F5), (T3, A), (T3, J)} × {E1, E2, E3} × {(a), (b)} ×
   {ar1_05, ar1_09, steps20} alla scala P2f × coefficiente di attività dello scarto della famiglia ∈ {0; −0,5;
   +0,5} nelle unità del §4 (costanti e derive nulle), con f = 0,75 e k = 1,5 per E2 ed E3. Per E1 lo scarto non
   esiste e i modelli (b) coincidono con (a): una sola riga per test e rumore (le famiglie A e J coincidono). E4 e
   l'analisi (c) restano solo analitiche.
2. *Indice*: per ogni candidato, la frequenza analitica di `supportato` sotto lo scenario, p_min e p_max sulle 20
   realizzazioni del disegno.
3. *Selezione*: un candidato AR(1) è scelto se [p_min, p_max] interseca [0,20; 0,90]; un candidato steps20 se
   interseca [0,10; 0,95], banda più larga perché nei salti l'approssimazione normale è meno affidabile. Nessuna
   altra eccezione: un candidato fuori dalla sua banda non è simulato.
4. *Realizzazione del disegno simulata*: la **decima** delle 20 ordinate per p crescente (a pari p, per indice di
   seme crescente); è una realizzazione concreta, non una mediana numerica.
5. *Tetto*: al più 24 candidati. Se sono di più si tengono quelli con |p₁₀ − 0,5| minore (p₁₀ della realizzazione
   del punto 4), a pari merito nell'ordine dell'insieme candidato (T5/F5, T3/A, T3/J, poi estensione, modello,
   rumore, scarto).
6. *Per ogni candidato scelto*: 1000 cataloghi **sotto nulla e 1000 sotto lo scenario**, con lo stesso rumore
   appaiato e gli stessi scarti; si riportano falsi verdetti per verso, `supportato`, copertura, R ed errori, con
   denominatori espliciti, e il confronto con la previsione analitica.
7. *Semi*: j = 0, …, J − 1 indicizza l'**elenco finale dei candidati selezionati** dopo i punti 3–5 (J ≤ 24), non
   l'insieme candidato; rumore 34 000 000 + 10 000·j + k, k = 0…999, quindi al più 34 239 999, sotto la zona
   34 900 000 delle estrazioni del disegno (gli stessi semi
   per nulla e scenario); estrazioni del disegno quelle del §3. Disgiunzione da tutti gli intervalli già
   usati verificata dal codice.
8. *Tetto operativo*: benchmark prima del lancio come in A1 del piano di potenza; arresto prima della griglia se
   la durata prevista supera 8 ore su 12 processi.

## 6. Significato dell'obiettivo del 50 %

Obiettivo **operativo**, non una garanzia: un'estensione è «potenzialmente sufficiente» per un test se, alla scala
di rumore P2f, con il modello (a) e scarti nulli, la riduzione del 20 % è riconosciuta almeno metà delle volte.
L'analisi di sensibilità (c) si riporta accanto, **solo descrittiva e senza criterio**: tolleranza e falsi
riconoscimenti nel caso peggiore entro C, perché il giudizio sull'affidabilità del raccordo resti esplicito. Motivo della
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

## 10. Valori registrati al congelamento

Calcolati con le regole del §3 sulla serie SILSO emisferica smussata a 13 mesi di `run_p2.load_silso()`
(somma dei due emisferi; stesse date anche sulla serie non normalizzata), prima di qualunque calcolo prospettico:
- **m₂₃ = 1996-08** (minimo in 1995-01 → 1998-12); quindi m₂₂ convenzionale = 1985-08;
- **massimo smussato del ciclo 24 = 2014-04** (cercato in 2011-01 → 2016-12);
- **massimo smussato del ciclo 25 = 2024-10** (cercato da 2022-01 all'ultimo mese disponibile, 2026-09);
- t₂₅ = 23 mesi; **finestra analoga di E1 = 2016-03 → 2021-02** (60 mesi), le cui CR forniscono, nell'ordine,
  attività, fase e ciclo del tempo alle 67 CR di E1 (le ultime CR di E1 oltre la fine della finestra riprendono la
  sequenza dall'inizio della finestra, regola registrata qui).
Restano esplorativi e dichiarati come tali: f, k, le griglie degli scarti e i limiti C.

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

## 12. Revisione di Codex della revisione 2 (`c4247d0`), recepita

1. (c) dichiarata **analisi di sensibilità alla distorsione**, con intervalli e verdetti ordinari; caso peggiore per
   il riconoscimento e per i falsi riconoscimenti calcolati separatamente, con segni diversi; nel §6 (c) è solo
   descrittiva, senza criterio (§4, §6).
2. Matrici esatte per T5 e per le due famiglie T3 (J: colonna M·(Â − 1)·sin|λ|; A: costanti MDI per emisfero e
   M·(Â − 1)), coefficiente d'interesse identificato per nome di colonna; condizione di non distorsione come
   proiezione nulla sullo stesso coefficiente, anche per costanti e derive (§2, §4).
3. Posti vuoti rappresentati: frazione di posti senza record di S per strato in E0, distinta dai dati mancanti;
   la resa f agisce dopo (§3).
4. Fase convenzionale con minimi fissati (T_MIN, minimo del ciclo 23 dalla serie smussata), fase e ciclo del tempo di
   E1 dalla rotazione analoga; etichetta vecchio/nuovo trasferita con lo scarto di ciclo o; celle di E1 dall'intero
   insieme HMI dello strato; unione degli strati vuoti con ordine fisso (§3).
5. Singoletti: restano nella regressione T3, esclusi solo dal fit della funzione di varianza; famiglia di scarto
   T3 (A o J) nell'insieme candidato di B; realizzazione simulata = la decima per p crescente (§3, §5).
Scale degli scarti fissate su E0; fonte delle costanti di tilt identificata (P3 C1, 2,107°, `c41fa4c`) e dichiarata
come scala di disaccordo; per c₀ di T5 nessuna fonte, valori esplorativi (§4).

## 13. Revisione di Codex della revisione 3 (`62661f2`), recepita

1. Scarto di ciclo o ∈ {−1, 0, +1}, con il controesempio verificato (HARP 7379, 2019-07-10, ciclo 25; in S 2 record
   con +1 e 2 con −1); istanti di E2 prima del minimo del ciclo 23 assegnati al ciclo 22 con minimo convenzionale
   m₂₃ − 11 anni (§3).
2. Uno strato con posti osservati e nessun record di S conserva la probabilità di vuoto 1 e non si unisce; l'unione
   vale solo per strati senza posti; emisferi mai uniti (§3).
3. β nel modello (b) descritto per famiglia: pendenza HMI per T5 e T3-J; coefficiente di Joy comune dopo il
   controllo degli scarti additivi per T3-A, senza assumere che sia identificato dai soli dati HMI (§4).
4. j indicizza l'elenco finale selezionato (J ≤ 24); semi di rumore al più 34 239 999, disgiunti dalla zona delle
   estrazioni del disegno (§5).

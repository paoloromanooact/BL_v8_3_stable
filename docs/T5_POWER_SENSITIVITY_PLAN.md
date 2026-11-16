# T5 — sensibilità della potenza al segnale, al rumore temporale e al metodo: piano

Stato: **congelato il 2026-11-16, prima di scrivere il codice ed eseguire**, dopo la revisione di Codex
della bozza `bb61bc0` (`T5_POTENZA_PIANO_BOZZA_REVISIONE_CODEX.txt`, 2026-11-15), recepita in §10. Da
questo commit non si modifica; ogni cambiamento è un emendamento registrato prima del passo che
riguarda. Segue la [nota di fattibilità](T5_FEASIBILITY_NOTE_DRAFT.md) (rev. 2, §6 punti 3–5) e i
[risultati della sensibilità del proxy](T5_PROXY_SENSITIVITY_RESULTS.md). Non è una validazione, non
valida nessuna procedura, non applica nulla ai dati reali e non decide da solo la fattibilità di T5.
**Non cieco**: la validazione P2f, T5-D1, T5-D2 e la sensibilità del proxy sono note.

## 1. Domanda

Sul disegno HMI fissato (318 celle CR × emisfero, 2375 record, 2010–2026): se la riduzione prescritta
della componente di Joy fosse presente, **quanto spesso i test la riconoscerebbero**, sotto queste
ipotesi di rumore, e **quanti falsi verdetti** darebbero quando il segnale è assente? In particolare,
quanto la frequenza di `supportato` dipende da:
- **(a) la forma del segnale**: media lineare in Â, come nei generatori P2f, oppure la forma prodotta
  dallo scenario prescritto sul catalogo (risultati del proxy), a **pendenza proiettata esattamente
  uguale**;
- **(b) la scala e la forma della componente temporale** del rumore;
- **(c) il metodo di inferenza**, con le sue frequenze di falso verdetto sotto nulla accanto.

La risposta resta condizionata ai generatori e al disegno: il piano non misura il rumore vero del Sole,
non produce una probabilità reale di rilevazione per HMI e non decide da solo se HMI sia sufficiente o
insufficiente in generale. HMI da solo è il riferimento; un confronto futuro con una serie estesa dovrà
usare le stesse ipotesi e gli stessi metodi.

## 2. Che cosa resta fisso (dal protocollo P2f e da T5-D2)

- Disegno: `P.build_design()` ricostruito; unità T5 di `V.units(dd, "T5")` (`p2d.design_t5`); stima
  puntuale **WLS** sulle celle con pesi W_c = ΣΦ, intercetti ciclo-emisfero e colonna (Ā_c − 1); riga g
  della pendenza (β̂_WLS = g·η, con g·1 = 0 e g·(Ā − 1) = 1).
- Generatore del rumore: `V.responses` con `beta_frac = 0` (rumore individuale di scala η̄ per record;
  componente temporale x_{t,h} a varianza marginale 1, moltiplicata per 0,5·η̄·x_scale;
  η̄ = 3,56·10⁻²⁵ G/Mx). Le medie dei segnali si aggiungono dopo (§3a).
- Verdetti come nelle rispettive procedure originali (§3c); intervallo al 97,5 % nominale,
  Z = Φ⁻¹(0,9875) a precisione completa; `errore` come nel protocollo P2f.
- Nessuna modifica retroattiva a `p2f_validation.py`, `p2f_pilot.py`, `diag_t5_oracle.py`.

## 3. Griglia (fissata prima; nessuna aggiunta dopo l'esito)

### 3a. Segnale, 5 livelli, sullo **stesso rumore**

Per ogni configurazione di rumore n e replica k si genera **un solo catalogo di rumore**
d*_i⁽⁰⁾ = Φ_i·η̄·(1 + rumore_i), e vi si aggiungono le cinque medie:
- `N` nulla: d*_i = d*_i⁽⁰⁾.
- `L1`, `L2` lineare: d*_i = d*_i⁽⁰⁾ + Φ_i·η̄·e_L·(Ā_c − 1), con **e_L esatto** pari alla pendenza
  proiettata dello scenario corrispondente, letta dagli output conservati
  (`results/T5_PROXY_SENSITIVITY/SUMMARY.csv`, `39c010c`, colonna `e_ref`, rappresentazione completa):
  e_L1 = −0,051494066951105075 e e_L2 = −0,10305075387820256. Le etichette −0,05 e −0,10 sono solo
  illustrative.
- `S1`, `S2` scenario del proxy: d*_i = d*_i⁽⁰⁾ + Φ_i·Δη_c, con Δη_c letto da
  `results/T5_PROXY_SENSITIVITY/CELLS.csv` (`39c010c`, SHA-256 `0c899647…`) per δ_max = 0,10 e 0,20.
  Nelle celle del disegno completo che non sono fra le 318 Δη_c = 0 (scartate da `V.units` comunque).

In ogni cella la media aggiunta è costante, quindi η_c = η_c⁽⁰⁾ + (media aggiunta). Bersaglio comune della
pendenza: **Δβ = g·Δη_S = e_L·η̄** (−1,8331887834593406·10⁻²⁶ e −3,668606838064011·10⁻²⁶ G/Mx), uguale per
L e S per costruzione. La parte di Δη_S non descritta dal modello (rapporto delle RMS 0,55) resta nei
residui: è l'effetto della forma che si vuole isolare.

**Invarianti attese** (verificate prima del lancio, §6, e registrate durante l'esecuzione):
- per disegno e pesi fissati e rumore a media nulla, E[β̂_WLS] = g·(η̄·1 + Δη) = g·Δη (perché g·1 = 0);
  la parte fuori dal modello non cambia questa pendenza proiettata ma può cambiare la variabilità stimata
  dai residui;
- a rumore appaiato, **β̂_WLS(L) = β̂_WLS(S) catalogo per catalogo** entro l'arrotondamento in virgola
  mobile (tolleranza: |Δ| ≤ 10⁻¹²·|Δβ| + 10⁻³⁸ G/Mx);
- per `O` (§3c), che usa la stessa WLS e la stessa covarianza vera, anche **SE, intervallo e verdetto
  coincidono fra L e S appaiati**; una differenza (salvo un estremo a distanza ≤ tolleranza dallo zero,
  registrato) è un errore tecnico di mapping, appaiamento o normalizzazione;
- per `M` e `B` la forma può cambiare SE stimati e distribuzione bootstrap pur lasciando identica la
  pendenza WLS: è ciò che il contrasto L/S isola. Non implica una potenza massima generale per HMI.

### 3b. Rumore temporale, 9 configurazioni = 3 forme × 3 scale

- Forme: `ar1_05` (scenario P2f 1: φ = 0,5, κ = 0), `ar1_09` (scenario 2: φ = 0,9, κ = 0), `steps20`
  (scenario 7: salti ±1 su blocchi di 20 CR, livelli indipendenti per emisfero, fase condivisa).
- Scale: 0,25·η̄, 0,5·η̄ (quella P2f), 1,0·η̄, cioè `x_scale` = 0,5, 1, 2. Rumore individuale fisso a η̄.
- Che cosa è già noto: nella validazione P2f la procedura M per T5 ha soddisfatto i criteri sotto nulla
  negli scenari 1 e 2 **alla sola scala x_scale = 1** e non nello scenario 7. Le scale 0,5 e 2 non sono
  state provate: la calibrazione di M lì non è nota, ed è parte di ciò che la griglia esplora. La
  procedura T5 resta non validata.

### 3c. Metodi, 4, con i loro oggetti statistici

| Metodo | Che cosa produce | Verdetto | Copertura, SE, R |
|---|---|---|---|
| `M` | procedura M del protocollo P2f (`V.procedure_m`): β̂_WLS, SE da σ̂_x² bᵀKb + Σ g_c² v̂_c, intervallo normale | `supportato` se hi < 0, `opposto` se lo > 0 | sì, rispetto a Δβ |
| `G` | FGLS: β̂_G = [(XᵀV̂⁻¹X)⁻¹XᵀV̂⁻¹η]_ultimo, V̂ = σ̂_x² K(φ̂, κ̂) + diag(v̂_c) dalla REML di M, Var dall'ultimo elemento di (XᵀV̂⁻¹X)⁻¹ | come M | sì, rispetto a Δβ, con **bias di G rispetto a Δβ riportato** |
| `B` | candidata B del pilota (`P.candidate_b`): statistica t con errore robusto per cluster, p_low, p_high per verso, numero di cluster; stima puntuale WLS condivisa | `P.verdict_b`: `supportato` se p_low ≤ 0,0125, `opposto` se p_high ≤ 0,0125 | **non applicabili** (l'interfaccia non restituisce SE né intervallo); registrati come «n/a: B restituisce solo p-value» |
| `O` | **riferimento a varianza nota**: β̂_WLS con la covarianza vera della WLS sotto il generatore (componente temporale vera e varianza individuale vera, come A3 di T5-D2; per `steps20` K_steps marginale con L = 20), riferimento normale | come M | sì, rispetto a Δβ |

- **G cambia stimatore.** Con V nota la riga GLS è diversa da g; per una media fuori dallo spazio del
  modello la pendenza media di G può differire da g·Δη, e con V̂ stimata dai dati la riga è casuale.
  **Non si attribuisce a G l'identità E[β̂] = Δβ.** Si mantiene la proiezione WLS Δβ come bersaglio
  comune e si riportano esplicitamente media, bias e copertura di G rispetto ad essa; uno spostamento
  sistematico non è letto come maggiore efficienza. Nessun nuovo parametro fisico di ampiezza dello
  scenario è introdotto implicitamente nel codice. Se M dà `errore`, anche G (V̂ non disponibile).
  G richiede la costruzione e la soluzione del sistema di covarianza: il riuso della REML evita di
  ristimarla, non rende il costo nullo (§3e).
- **B non è riscritto.** Si usano `P.candidate_b` e `P.verdict_b` invariati, con `BLOCK = 13` CR come nel
  pilota (cluster = blocchi di 13 CR a partire dalla prima CR delle unità T5, 2097: convenzione della
  nota d'implementazione del pilota) e 9999 repliche di Webb. L'interfaccia richiede un **adattatore**
  dalle unità di `V.units(dd, "T5")` (che non espone `level` né `Xn_c`) al dizionario atteso da
  `P.b_units`: `level = "cell"`, `eta_c`, `W_c`, `Xf_c`, `Xn_c = Xf_c[:, :-1]` (intercetti
  ciclo-emisfero), `cell_cr`. L'adattatore si verifica prima del lancio (§6). Intervalli B e copertura
  richiederebbero un'inversione del test, non prevista: sarebbe un'estensione con un piano proprio.
- **O non è un tetto di calibrazione.** Fornisce la varianza corretta della WLS sotto il generatore
  specificato e usa il riferimento normale; nei salti la distribuzione non è necessariamente normale, e
  conoscere la covarianza non garantisce la copertura nominale esatta. Per questo si riportano anche i
  falsi verdetti di O. O non è disponibile sui dati reali.

Tutti i metodi analizzano le stesse risposte: i confronti fra metodi sono appaiati; i confronti fra
segnali sono appaiati sullo stesso rumore (§3a).

### 3d. Numerosità e semi

- 9 configurazioni di rumore × **N = 1000** repliche = **9000 cataloghi di rumore di base**; × 5 segnali
  = **45 000 risposte**, ciascuna analizzata dai 4 metodi. Il riuso del rumore fra i cinque segnali
  della stessa replica è **intenzionale e dichiarato** (appaiamento), non una collisione di semi.
- **Semi del rumore di base**: 31 000 000 + 100 000·n + k, n = 0…8 (ordine: forma `ar1_05`, `ar1_09`,
  `steps20`; dentro ogni forma scala 0,5, 1, 2), k = 0…999; intervallo 31 000 000–31 800 999. Ogni seme
  inizializza `numpy.random.default_rng(seme)` passato a `V.responses` (costruzione unica, nessun
  `SeedSequence.spawn`).
- **Semi del bootstrap di B**: 32 000 000 + 100 000·n + k, passati a `P.candidate_b` come argomento
  `seed`. Lo stesso seme del bootstrap è usato per i cinque segnali della stessa replica (stessi pesi di
  Webb, appaiamento dichiarato anche per B); intervallo 32 000 000–32 800 999.
- **Semi delle prove fuori griglia** (selftest e misura della durata, §3e e §6): 33 000 000 + k,
  k = 0…99.
- Disgiunti da tutti quelli già usati: `P.USED`, pilota 3 000 000–5 001 000, validazione
  6 000 000–9 002 000, test 20 000 000–20 001 000, pretest T5-D2 28 000 000–28 400 000, selftest del
  ricalcolo 29 500 000–29 500 010. Il codice verifica disgiunzione e unicità dei semi di base e del
  bootstrap prima di partire.

### 3e. Costo

Stima iniziale: M ≈ 1 s, B ≈ 1–2 s per risposta, O e G da misurare; 45 000 risposte × ≈ 2,5 s ≈ 31 h-core,
circa 3 h su 12 processi. **La durata si misura prima del lancio** su 20 cataloghi fuori griglia (semi
33 000 000 + k), senza avviare la griglia per misurarla. Limite: se la stima misurata supera **8 h** su 12
processi, ci si ferma prima del lancio e si riporta; nessuna riduzione della griglia senza emendamento.
Esecuzione unica, distaccata, su commit pulito.

## 4. Grandezze riportate

Per configurazione (rumore × segnale) e metodo, sui 1000 tentativi (errori al denominatore):
- frequenze di `supportato`, `opposto`, `non deciso`, `errore`, con MCSE binomiale;
- sotto nulla: falsi verdetti totali e per verso;
- sotto segnale (M, G, O): copertura del bersaglio Δβ e le due code; per B «n/a»;
- (M, G, O) sui tentativi validi: media di SE, deviazione standard di β̂, R = media(SE²)/var(β̂);
- **β̂_WLS su tutti i cataloghi tecnicamente costruiti**, anche quando una procedura successiva fallisce:
  media e SD incondizionate (controllo di E[β̂_WLS] = Δβ), distinte dalle medie condizionate al successo
  di ciascun metodo (una selezione dovuta agli errori può spostarle);
- per G: media, SD e **bias di β̂_G rispetto a Δβ**, e differenza appaiata β̂_G − β̂_WLS sugli stessi
  cataloghi.

**Incertezza Monte Carlo** con N = 1000 (riportata così, non come «±»): a una frequenza del 2,5 % MCSE
≈ 0,49 punti (semilarghezza normale approssimata al 95 % ≈ 0,97 punti); all'1,25 % per singolo verso MCSE
≈ 0,35 punti; al 50 % MCSE ≈ 1,58 punti (semilarghezza al 95 % ≈ 3,10 punti). N = 1000 non permette una
certificazione precisa del livello vicino al nominale né una graduatoria robusta per differenze di pochi
punti. L'errore delle differenze appaiate (L/S, fra metodi) si calcola sui confronti per replica.

Grezzo per risposta (`RAW.csv.gz`): rumore n, replica k, segnale, seme di base, seme del bootstrap,
metodo, β̂_WLS, β̂ del metodo, SE, lo, hi, p_low, p_high, n_cluster, verdetto, stato (`ok`, `errore`
previsto, errore tecnico), e per M i parametri REML. Riepilogo (`SUMMARY.csv`). `META.json` con commit,
SHA-256 di piano, script, `SUMMARY.csv` e `CELLS.csv` del proxy, `_design` ricostruito, semi, ambiente,
durata, esito.

## 5. Lettura prevista (struttura fissata prima; nessuna soglia)

1. **Forma del segnale** (a): per ogni rumore e metodo, `S1` contro `L1` e `S2` contro `L2` sullo stesso
   rumore, con la differenza appaiata delle frequenze di `supportato` e il suo errore calcolato sulle
   repliche (stessa formula di T5-D2 §6.5). Per O la differenza attesa è nulla (§3a): un valore non nullo
   è un errore tecnico, non un risultato. Risponde a: la forma non lineare dello scenario cambia la
   potenza di M, G e B a parità esatta di pendenza?
2. **Rumore** (b): per ogni segnale e metodo, la frequenza di `supportato` in funzione della scala e della
   forma, con i falsi verdetti sotto nulla della stessa configurazione.
3. **Metodo** (c): per ogni configurazione, potenza e falsi verdetti sotto nulla **insieme**. Con falsi
   verdetti diversi si descrivono le frequenze; **non si dichiara un metodo migliore** perché respinge più
   spesso: una graduatoria a pari livello effettivo richiederebbe una calibrazione distinta, non prevista.
   O è un riferimento a varianza nota, non un metodo.
4. **Vincolo di lettura**: tutte le frequenze valgono per questi generatori e questo disegno, non per il
   Sole. Il risultato si esprime come «in queste condizioni lo scenario X è riconosciuto Y volte su 1000,
   con Z falsi verdetti». Una potenza bassa in tutta la griglia non dimostra un limite di HMI (altri
   stimatori o altre statistiche non sono esplorati); una potenza alta per un metodo non lo valida.

**Nessuna regola automatica, nessuna soglia e nessun ampliamento della griglia dopo aver visto gli esiti.**
Dopo l'esecuzione si valuta esplicitamente, con Codex, uno di tre esiti: (i) un metodo o una direzione
merita un protocollo di sviluppo e validazione con semi nuovi; (ii) rinvio di T5 per priorità, con i
limiti espliciti; (iii) esito non conclusivo.

## 6. Controlli prima dell'esecuzione (selftest, poi porta)

Nessun controllo usa cataloghi della griglia.
1. **Semi**: disgiunzione e unicità dei semi di base, del bootstrap e delle prove.
2. **Iniezione e appaiamento** (senza rumore e con rumore, semi 33 000 000 + k):
   - `S` senza rumore: η_c ricostruita = η̄ + Δη_c esattamente per tutte le 318 celle; mapping
     cella → Δη_c verificato tramite A_cell e W_c di `CELLS.csv` contro `run_p2.cells` sul disegno;
   - `L` con e_L: η_c ricostruita = η̄·(1 + e_L·(Ā_c − 1)) esattamente;
   - g·Δη_S/η̄ e g·(η̄·e_L·(Ā − 1))/η̄ coincidono con e_L (entro 10⁻¹²);
   - con rumore: β̂_WLS(L) = β̂_WLS(S) entro la tolleranza di §3a e, per O, SE e verdetto identici;
   - `L` con e_L = −0,1 (il vecchio effetto, distinto dalla griglia) coincide con `V.responses` con
     `beta_frac = −0,1` a parità di seme entro l'arrotondamento.
3. **G**: su un caso sintetico con V nota coincide con la soluzione GLS esplicita; con
   **V = σ²·diag(1/W_c)** nelle coordinate η originali torna la WLS con pesi W_c (non con V = σ²I, che dà
   la OLS). Esempio di controllo a mano: x = (0, 1, 2), y = (0, 0, 1), pesi (1, 1, 100): OLS dà pendenza
   0,5, WLS 100/167 ≈ 0,5988, GLS con V = diag(1/pesi) 0,5988.
4. **B**: l'adattatore conserva statistica, p_low, p_high, numero di cluster e verdetto di
   `P.candidate_b` rispetto al percorso originale (`P.test_units` e `P.b_units`) sugli stessi dati, su 10
   cataloghi di prova; identità esatta.
5. **O**: riproduce A3 di T5-D2 su 5 cataloghi della validazione (stessi semi, SE entro 10⁻⁹ relativo);
   la covarianza vera usata per `steps20` coincide con K_steps (L = 20, emisferi indipendenti) e la scala
   con (0,5·η̄·x_scale)².
6. **Porta sulla pipeline** (compatibilità, non validazione): `M` riproduce β̂ e SE di
   `VALIDATION_RAW.csv.gz` (test T5) su 20 cataloghi dello scenario 2 a effetto −0,1 e 20 dello scenario 7
   sotto nulla, con gli stessi semi, entro 10⁻⁹ relativo. Se fallisce, ci si ferma. Questa porta non è una
   prova indipendente completa del generatore né una validazione della nuova griglia: vale insieme ai
   controlli 2–5.
7. **Durata** (§3e) su 20 cataloghi fuori griglia.

**Errori.** Gli errori **previsti** delle procedure (funzione di varianza o REML non valide in M e G,
errore di B) restano tentativi al denominatore, registrati con il motivo. Gli errori **tecnici** del
generatore, del mapping, dell'appaiamento o della provenienza (incluse le violazioni delle invarianti di
§3a, valori non finiti nelle iniezioni, hash o Git non validi) **invalidano** l'esecuzione: esito «non
riuscito», output conservati, nessuna lettura dei risultati. Si mantengono le guardie già corrette nello
script del proxy: non finiti controllati prima delle trasformazioni, errori di Git che sollevano invece
di passare per albero pulito, `META.json` scritto sempre con tipo e messaggio dell'eccezione,
`allow_nan = False`, codice di uscita ≠ 0 se non completato.

## 7. Limiti dichiarati

- Generatori sintetici sul disegno HMI; ampiezze di rumore e forme scelte, non stimate dal Sole.
- `S` usa Δη_c da un proxy a coppia compatta con R nominale e γ0 = 24°, ampiezze illustrative.
- `G` e `B` non sono validati; per B non si riportano SE, intervalli né copertura; `O` non è disponibile
  sui dati reali e non garantisce la copertura nominale nei salti.
- N = 1000 per configurazione: risoluzione limitata sui falsi verdetti (§4).
- Nessun'altra forma di dipendenza oltre alle tre scelte; nessun altro stimatore.
- Non cieco.

## 8. Esecuzione

Script `scripts/t5_power_sensitivity.py`, scritto dopo il congelamento e rivisto da Codex prima del
lancio. `--selftest` (§6, punti 1–5 e 7, senza cataloghi della griglia), `--gate` (§6, punto 6),
`--run` (unica, distaccata, 12 processi, `OMP_NUM_THREADS=1`). Output in
`results/T5_POWER_SENSITIVITY/`, conservati in Git prima della lettura. Nessun push senza richiesta.

## 9. Domanda e risposta attesa (formulazione)

Il piano potrà dire: «in queste condizioni riconosciamo lo scenario X Y volte su 1000, con Z falsi
verdetti, con il metodo W». La trasferibilità di quelle condizioni al Sole resta una questione distinta.

## 10. Revisione di Codex della bozza `bb61bc0` (2026-11-15), recepita

1. Pendenze L esatte (e_L = e_ref dagli output conservati) e rumore davvero appaiato: un solo catalogo di
   rumore per replica con le cinque medie sopra; semi per configurazione di rumore e replica, non per
   segnale; semi del bootstrap separati e costruzione unica (§3a, §3d).
2. Invariante WLS e controllo forte L/S appaiati, anche per O; β̂_WLS registrata su tutti i cataloghi
   costruiti (§3a, §4, §6).
3. G cambia stimatore: bersaglio comune Δβ con bias e copertura di G riportati; selftest corretto
   (V = σ²·diag(1/W_c) per tornare alla WLS) con l'esempio a mano; costo di G non nullo (§3c, §6).
4. B con i suoi oggetti (p-value, verdetto con ALPHA per verso), SE/intervallo/copertura non applicabili;
   `BLOCK = 13` e adattatore delle unità verificati (§3c, §6).
5. O come riferimento a varianza nota, non tetto di calibrazione; calibrazione di M limitata alle
   configurazioni già provate (§3b, §3c).
6. N = 1000 mantenuto; incertezze Monte Carlo corrette (MCSE contro semilarghezza al 95 %); nessuna
   graduatoria dei metodi senza calibrazione comune (§4, §5).
7. Porta sulla pipeline come compatibilità; errori previsti distinti da quelli tecnici; guardie dello
   script precedente mantenute (§6).

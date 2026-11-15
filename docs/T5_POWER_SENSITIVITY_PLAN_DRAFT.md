# T5 — sensibilità della potenza al segnale, al rumore temporale e al metodo: piano

Stato: **bozza del 2026-11-15, da rivedere (Codex) e congelare prima di scrivere il codice ed eseguire.**
Segue la [nota di fattibilità](T5_FEASIBILITY_NOTE_DRAFT.md) (rev. 2, §6 punti 3–5) e i
[risultati della sensibilità del proxy](T5_PROXY_SENSITIVITY_RESULTS.md). Non è una validazione, non
valida nessuna procedura, non applica nulla ai dati reali e non decide da solo la fattibilità di T5.
**Non cieco**: la validazione P2f, T5-D1, T5-D2 e la sensibilità del proxy sono note.

## 1. Domanda

Sul disegno HMI fissato (318 celle CR × emisfero, 2375 record, 2010–2026), quanto la probabilità di un
verdetto `supportato` per T5 dipende da:
- **(a) la forma del segnale**: media lineare in Â, come nei generatori P2f, oppure la forma prodotta
  dallo scenario prescritto di riduzione della componente di Joy sul catalogo (risultati del proxy),
  a parità di pendenza proiettata;
- **(b) la scala e la forma della componente temporale** del rumore;
- **(c) il metodo di inferenza**, con le sue frequenze di falso verdetto sotto nulla riportate accanto.

HMI da solo è il riferimento: questo studio non simula serie estese. Qualunque confronto futuro con una
serie estesa dovrà usare le stesse ipotesi e gli stessi metodi di qui.

## 2. Che cosa resta fisso (dal protocollo P2f e da T5-D2)

- Disegno: `P.build_design()` ricostruito; unità T5 di `V.units(dd, "T5")` (`p2d.design_t5`); stima
  puntuale WLS sulle celle con pesi ΣΦ, intercetti ciclo-emisfero e colonna (Â_c − 1); riga g della
  pendenza.
- Generatore delle risposte: `V.responses` (rumore individuale di scala η̄ per record; componente
  temporale x_{t,h} a varianza marginale 1, moltiplicata per 0,5·η̄·x_scale; η̄ = 3,56·10⁻²⁵ G/Mx).
- Verdetto: `supportato` se hi < 0, `opposto` se lo > 0, altrimenti `non deciso`; intervallo al
  97,5 % nominale (Z = Φ⁻¹(0,9875)); `errore` come nel protocollo P2f.
- Nessuna modifica a `p2f_validation.py`, `p2f_pilot.py`, `diag_t5_oracle.py`.

## 3. Griglia (fissata prima; nessuna aggiunta dopo l'esito)

**(a) Segnale, 5 livelli.** Per ogni record i nella cella c:
- `N` nulla: η_c = η̄.
- `L1`, `L2` lineare (generatore P2f): d*_i = Φ_i·η̄·[1 + e·(Â_c − 1) + rumore], con e = −0,05 e −0,10.
  Il valore −0,05 non è nella griglia P2f: serve a confrontare a parità di pendenza con `S1`; −0,10 è
  già nella griglia P2f.
- `S1`, `S2` scenario del proxy: d*_i = Φ_i·[η̄·(1 + rumore) + Δη_c], con Δη_c letto da
  `results/T5_PROXY_SENSITIVITY/CELLS.csv` (`39c010c`, SHA-256 `0c899647…`) per δ_max = 0,10 e 0,20.
  Nelle celle del disegno completo che non sono fra le 318 (meno di 3 record) Δη_c = 0: sono scartate
  da `V.units` comunque.

  Stimando: per `L` il bersaglio è β = e·η̄; per `S`, poiché le colonne ciclo-emisfero sommano a 1 e
  quindi g·1 = 0, E[β̂] = g·Δη = Δβ esattamente (−1,833·10⁻²⁶ e −3,669·10⁻²⁶ G/Mx, cioè
  e_ref = −0,0515 e −0,1031). La copertura si valuta rispetto a questo bersaglio. La parte di Δη non
  descritta dal modello (rapporto delle RMS 0,55) resta nei residui: è l'effetto della forma che si
  vuole misurare.

**(b) Rumore temporale, 9 configurazioni** = 3 forme × 3 scale.
- Forme: `ar1_05` (scenario P2f 1: φ = 0,5, κ = 0), `ar1_09` (scenario 2: φ = 0,9, κ = 0),
  `steps20` (scenario 7: salti ±1 su blocchi di 20 CR, emisferi indipendenti, fase condivisa).
  M è calibrata nei primi due e non nel terzo (validazione P2f); T5-D2 ha mostrato che nel terzo la
  componente temporale è quella che conta.
- Scale: 0,25·η̄, 0,5·η̄ (quella P2f), 1,0·η̄, cioè `x_scale` = 0,5, 1, 2 nel generatore.
  Rumore individuale fisso a η̄.

**(c) Metodi, 4.**
- `M`: procedura M del protocollo P2f (`V.procedure_m`): WLS, funzione di varianza individuale, REML
  AR(1), Var = σ̂_x² bᵀKb + Σ g_c² v̂_c. Validata per T3, non per T5.
- `G`: stima **feasible GLS** con la covarianza stimata da M: V̂ = σ̂_x² K(φ̂, κ̂) + diag(v̂_c);
  β̂_G = (XᵀV̂⁻¹X)⁻¹XᵀV̂⁻¹η, Var dall'ultimo elemento di (XᵀV̂⁻¹X)⁻¹. Non è validata: è un candidato a
  costo nullo dopo M. Se M dà `errore`, anche G.
- `B`: candidata B del pilota P2f (`P.candidate_b`): wild cluster bootstrap ristretto su blocchi di CR
  con pesi di Webb, 9999 repliche; semi del bootstrap derivati dal seme del catalogo. Nel pilota non
  era accettabile per i falsi verdetti; qui serve come contrasto a un metodo che non stima la covarianza.
- `O`: **riferimento oracolo** con la covarianza temporale vera e la varianza individuale vera (come A3 di
  T5-D2), **non** una procedura disponibile: fissa il tetto di calibrazione per la stima WLS a varianza
  nota. Per `steps20` usa K_steps marginale (L = 20) come in T5-D2.

Tutti i metodi usano gli stessi cataloghi (stesso seme): i confronti fra metodi sono appaiati.

**Numerosità.** 5 segnali × 9 rumori = 45 configurazioni × **N = 1000** cataloghi = 45 000 cataloghi.
MCSE binomiale: ±0,5 punti su una frequenza del 2,5 %, ±1,6 punti su una del 50 %. Non è una
validazione (che usava 10 000 sotto nulla): le frequenze sotto nulla qui servono a leggere la potenza,
non a certificare un livello.

**Semi**, nuovi e disgiunti da tutti quelli usati (`P.USED`, pilota 3 000 000–5 001 000, validazione
6 000 000–9 002 000, test 20 000 000–20 001 000, pretest T5-D2 28 200 000–28 400 000, selftest del
ricalcolo 29 500 000–29 500 010): seme = 31 000 000 + 100 000·j + k, con j = 0…44 l'indice di
configurazione (ordine: rumore esterno, segnale interno) e k = 0…999. Bootstrap di B: semi derivati
`seed·10 + t` tramite `numpy.random.SeedSequence(seed).spawn`, dichiarati nel codice. Il codice verifica
disgiunzione e unicità prima di partire.

**Costo stimato.** M ≈ 1 s, B ≈ 1–2 s, G e O trascurabili: 45 000 × ≈ 2,5 s ≈ 31 h-core, circa 3 h su
12 processi. Esecuzione unica, distaccata, su commit pulito.

## 4. Grandezze riportate

Per configurazione e metodo, sui 1000 tentativi (errori al denominatore):
- frequenze di `supportato`, `opposto`, `non deciso`, `errore`, con MCSE binomiale;
- sotto nulla: falsi verdetti totali e per verso;
- sotto segnale: copertura del bersaglio (β = e·η̄ oppure Δβ) e le due code;
- sui tentativi validi: media di SE, deviazione standard di β̂, R = media(SE²)/var(β̂), media di β̂
  (per `S`: controllo di E[β̂] = Δβ);
- per `G`: media e SD di β̂_G confrontate con quelle di β̂_WLS sugli stessi cataloghi (differenza
  appaiata), per vedere se la stima cambia oltre alla varianza.

Grezzo per catalogo (`RAW.csv.gz`): configurazione, seme, metodo, β̂, SE, lo, hi, verdetto, errore, e per
M i parametri REML. Riepilogo (`SUMMARY.csv`). `META.json` con commit, SHA-256 di piano, script, CELLS.csv
e `_design` ricostruito, semi, ambiente, durata.

## 5. Lettura prevista (struttura fissata prima; nessuna soglia)

1. **Forma del segnale** (a): per ogni rumore e metodo, `S1` contro `L1` e `S2` contro `L2`, con la
   differenza appaiata delle frequenze di `supportato` e il suo errore (stessa formula di T5-D2 §6.5).
   Risponde a: la forma non lineare dello scenario cambia la potenza a parità di pendenza?
2. **Rumore** (b): per ogni segnale e metodo, la potenza in funzione della scala e della forma.
   Risponde a: quanto conta non conoscere la scala reale della componente temporale?
3. **Metodo** (c): per ogni configurazione, potenza e falsi verdetti sotto nulla **insieme**; un metodo
   con falsi verdetti più alti non è «più potente». `O` è il riferimento di calibrazione, non un
   metodo.
4. **Vincolo di lettura**: tutte le frequenze valgono per questi generatori e questo disegno, non per il
   Sole; una potenza bassa in tutta la griglia non dimostra un limite di HMI (altri stimatori o altre
   statistiche non sono esplorati qui); una potenza alta per un metodo non lo valida.

**Nessuna regola automatica.** Dopo l'esecuzione si valuta esplicitamente, con Codex, uno di tre esiti:
(i) un metodo o una direzione merita un protocollo di sviluppo e validazione con semi nuovi;
(ii) rinvio di T5 per priorità, con i limiti espliciti; (iii) esito non conclusivo.

## 6. Controlli prima dell'esecuzione (selftest, poi porta)

- Semi: disgiunzione e unicità.
- Iniezione `S` senza rumore: η_c ricostruita = η̄ + Δη_c esattamente per tutte le 318 celle; con rumore,
  mapping cella→Δη_c verificato tramite A_cell e W_c di `CELLS.csv` contro `run_p2.cells` sul disegno.
- Iniezione `L` con x_scale = 1 e e = −0,10: coincide con `V.responses` a parità di seme.
- `G` su un caso sintetico con V nota: coincide con la soluzione GLS esplicita; con V̂ = σ² I torna la WLS.
- `O` riproduce A3 di T5-D2 su 5 cataloghi della validazione (stessi semi, stessi SE entro 10⁻⁹
  relativo): porta sul codice condiviso.
- **Porta sulla pipeline**: `M` riproduce β̂ e SE di `VALIDATION_RAW.csv.gz` (test T5) su 20 cataloghi
  dello scenario 2 a effetto −0,1 e 20 dello scenario 7 sotto nulla, con gli stessi semi, entro 10⁻⁹
  relativo. Se fallisce, ci si ferma.
- Valori non finiti e fallimenti: errori tecnici, META scritto sempre, codice di uscita ≠ 0 se non
  completato.

## 7. Limiti dichiarati

- Generatori sintetici sul disegno HMI; ampiezze di rumore e forme scelte, non stimate dal Sole.
- `S` usa Δη_c da un proxy a coppia compatta con R nominale e γ0 = 24°, ampiezze illustrative.
- `G` e `B` non sono validati; `O` non è disponibile sui dati reali.
- N = 1000 per cella: risoluzione limitata sui falsi verdetti.
- Nessun'altra forma di dipendenza oltre alle tre scelte; nessun altro stimatore.
- Non cieco.

## 8. Esecuzione

Script `scripts/t5_power_sensitivity.py`, scritto dopo il congelamento e rivisto da Codex prima del
lancio. `--selftest` (§6, senza cataloghi della griglia), `--gate` (porta sulla pipeline), `--run`
(unica, distaccata, 12 processi, `OMP_NUM_THREADS=1`). Output in `results/T5_POWER_SENSITIVITY/`,
conservati in Git prima della lettura. Nessun push senza richiesta.

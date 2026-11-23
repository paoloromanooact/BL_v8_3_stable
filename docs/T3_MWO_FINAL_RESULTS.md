# T3 su MWO 1974–2012 (catalogo R4) — stima unica, rilascio locale e figure

23 novembre 2026 (Claude). Catena completa, ogni passo conservato prima della lettura e ricontato:

| Passo | Commit | Controllo indipendente |
|---|---|---|
| Revisione Codex della stabilità, correzione del selftest | `17a479a` | riconteggio della stima, selftest 15/15 |
| `--estimate`, eseguito una sola volta | `e6ac79e` | — |
| Riconteggio della stima | `a636aeb` | 16/16, partial false, esito ricalcolato «descrittivo», verdetto nullo |
| Esportazione del catalogo (locale) | `93f3eb7` | — |
| Controllo del rilascio | `3c88ca5` | 115/115, legato al META del rilascio |
| Figure finali dai prodotti verificati | `e17f37e` | — |

## Stato inferenziale

**Descrittivo, nessun verdetto fisico.** La regola congelata (§6) lo impone per S1 «non determinato» e S2 «stabilità
non determinata» (`docs/T3_MWO_STABILITY_R4_RESULTS.md`, revisione Codex `17a479a`). La validazione accettata a 15°
era necessaria, non sufficiente. L'obiettivo di una conclusione inferenziale su T3 con MWO non è raggiunto.

## β₃ osservato (pendenza del coefficiente di Joy con l'attività, gradi per unità di attività)

- **Analisi principale:** β₃ = **−4,93**, SE 2,35, intervallo nominale 97,5 % **[−10,21, +0,34]**, n = 5223.
  - L'intervallo contiene zero.
  - Contiene anche i bersagli proiettati delle rampe di quenching dell'analisi principale: Δβ₁₀ = −0,53 e
    Δβ₂₀ = −1,06.
  - Non distingue quindi fra assenza di effetto, l'effetto previsto dagli scenari e un effetto di qualche volta
    più grande.
- **Undici sensibilità previste dal protocollo:** stime puntuali fra −3,90 e −8,82. Tutti gli intervalli
  contengono zero.
  - Esempi: tutti i record −3,90 [−8,89, +1,09]; pesi = area DPD −4,01 [−10,25, +2,23]; prima del 2010-05 −4,05
    [−9,49, +1,40]; SILSO emisferico −8,82 [−18,39, +0,75] con n = 2695.
  - Le sensibilità condividono gran parte dei dati: la concordanza dei segni non è un'evidenza aggiuntiva
    indipendente.
  - I loro intervalli non sono coperti dalla validazione del disegno principale.
- **Perché il segno non si può attribuire al Sole:** S2 misura la pendenza dello scarto relativo
  MWO − luce bianca su 4694 record, mentre β₃ riguarda i 5223 record principali. S2 è −3,18
  [−8,77, +2,40], dello stesso segno e ordine di grandezza, ma non distingue uno scarto contenuto
  entro il margine previsto da uno abbastanza grande da interferire con T3. Non dimostra una
  distorsione di MWO: anche la misura fotografica e la relazione fra le due misure possono variare.
  Le due pendenze condividono dati e non sono indipendenti; non si sottrae S2 da β₃ e non si stima
  con questo confronto una quota del segnale attribuibile allo strumento.
- **Parametri della procedura M al bordo del dominio REML:**
  - φ = 0,98 (il limite) nella principale e in otto sensibilità;
  - |κ| = 0,98 in sei sensibilità;
  - σ²ₓ ≈ 2,6·10⁻⁴.

  φ raggiunge il massimo consentito, ma da solo non dimostra che una componente temporale forte
  domini l'incertezza: nella principale σ²ₓ è piccolo e il contributo dipende dall'intera covarianza
  e dalla sua proiezione sul coefficiente. I valori al bordo sono un'avvertenza sulla stima dei
  parametri di covarianza; non sono automaticamente un errore tecnico né una prova di adeguatezza
  del modello. La validazione resta condizionata ai generatori studiati e non certifica la copertura
  dell'intervallo sul processo solare reale.
- **Nessuna percentuale di quenching** si ricava da β₃, come prescrive il runbook. Il rapporto con Δβ₂₀ non
  trasforma questo intervallo in un limite percentuale utile.

## Catalogo (rilascio locale, non pubblicato)

`results/MWO_TILT_CATALOGUE_RELEASE`:
- record: 5223 isolati, 5942 in tutto;
- dizionario delle colonne, 26 magnetogrammi esclusi (A2 e A3), confronti S1–S4, README;
- controllo indipendente 115/115.

Deposito pubblico, licenza e autori restano da decidere con l'utente e Paolo, come prevede il piano. Il catalogo è
nuovo per metodo, controlli e riproducibilità, non come primo catalogo di tilt magnetici MWO (Li & Ulrich 2012).

**Legge di Joy per ciclo** (`JOY_BY_CYCLE.csv`, descrittiva; pesata col flusso; intervalli bootstrap a blocchi di
6 CR, 2000 repliche):

| Ciclo | N | S |
|---|---|---|
| 20 (parziale) | 0,1 [−9,0, 64,6], 53 regioni | 23,2 [16,4, 67,3], 78 regioni |
| 21 | 27,1 [11,4, 40,5] | 22,2 [8,8, 36,2] |
| 22 | 24,2 [16,9, 30,8] | 26,6 [18,5, 36,3] |
| 23 | 16,5 [9,3, 25,2] | 22,5 [13,7, 31,4] |
| 24 (parziale) | 17,5 [3,6, 43,2] | 8,8 [−5,6, 28,8] |

Valori in gradi, k in γ = k·sin|λ|.
- I tre cicli completi hanno intervalli sovrapposti.
- Senza pesi i coefficienti del sud sono più bassi (16–17°), quelli del nord simili.
- Nessuna relazione con l'ampiezza dei cicli è stata cercata né si può leggere da questa tabella.

## Figure originali e revisione di impaginazione

Le figure originali restano in `results/T3_MWO_FINAL_FIGURES`. La revisione di sola presentazione
è in `results/T3_MWO_FINAL_FIGURES_V2`: titolo e assi completi, legenda fuori dai punti,
una sola etichetta «partial» per ciclo, unità del coefficiente di S1 e numerosità per emisfero in S3.
S1 indica che gli intervalli sono condizionati alle repliche non singolari. Gli input numerici
sono gli stessi prodotti verificati; i loro hash sono registrati nel META delle figure.

## Che cosa abbiamo e che cosa no

- **Abbiamo:**
  - un catalogo di tilt magnetici MWO 1974–2012 con controlli di qualità documentati, riconteggi indipendenti a ogni
    passo e confronti con luce bianca DPD e HMI;
  - una procedura validata sul suo disegno;
  - una stima di β₃ con intervallo nominale.
- **Non abbiamo:** un verdetto su T3. L'intervallo è circa dieci volte più largo del bersaglio al 20 %. La stabilità
  strumentale rispetto all'attività non è dimostrata (S2), e S1 è non determinato per due celle non verificabili.

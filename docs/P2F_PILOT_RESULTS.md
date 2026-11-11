# Risultati del pilota di sviluppo P2f — due candidate sul disegno reale congelato

Stato: **esecuzione unica, terminata il 2026-11-11 alle 12:06; documento scritto dopo il controllo
indipendente degli output (§2).** Le regole applicate sono quelle registrate nel piano
(`docs/P2F_PILOT_PLAN.md`, `83b0fc1`) §5 e nell'emendamento A1 (`59971e7`) §4, riportate qui alla
lettera perché il lettore possa verificarne l'applicazione; nessuna soglia, scenario o candidata è
cambiata dopo aver visto i risultati. **Sviluppo, non validazione**: il pilota sceglie o scarta
procedure; non produce verdetti sul quenching, non usa le risposte reali e non autorizza
l'applicazione ai dati. Lo scheletro di questo documento (`76376b7`) è stato scritto durante
l'esecuzione, prima di leggere gli esiti.

Dichiarazione: la tabella di scelta (due righe) è comparsa nell'avviso automatico di fine
esecuzione, letto prima di eseguire il controllo indipendente. Il controllo (`p2f_checks.py raw`)
era già scritto e committato (`c3ebb0d`) prima della fine del pilota; la sua unica modifica
successiva (`c9258fe`) riguarda la lettura della colonna `kind` (il valore `null` era letto come
mancante) ed è avvenuta prima che un qualunque controllo fosse valutato.

## 1. Esecuzione e provenienza

- Codice: `python/sharpbl/p2f_pilot.py`, commit `67058f6`; test preliminari (A1 §6, A2 §3)
  eseguiti sullo stesso commit e **tutti superati** (`results/P2F_PILOT/PRELIM_TESTS.csv`): REML
  su 200 serie sintetiche (200 valide; medie φ̂ 0,797, κ̂ 0,491, σ̂_x² 1,004 contro 0,8, 0,5, 1);
  funzione di varianza sul disegno reale, gruppi 2a e 2b (b̂ medio −0,504 e −0,500 contro −0,5;
  scarto medio di â −0,0006 e +0,0046); bootstrap vettorizzato contro diretto (scarto massimo
  4·10⁻¹⁵, p-value identici); Var(β̂) di M con parametri veri contro V_true di A (scarto relativo
  0 e 2·10⁻¹⁶); nessuna colonna di risposta nel disegno; semi non sovrapposti. L'esecuzione 1
  dei test, fallita sul test 2 (commit `e98b3bf`), è conservata come `PRELIM_*_RUN1.csv`.
- Avvio: 2026-11-11 10:17, distaccato, 12 processi; fine 12:06 (1 h 49 min). Esecuzione unica.
- Output: `results/P2F_PILOT/PILOT_RAW.csv.gz` (43 200 righe: catalogo × test × candidata),
  `PILOT_FALSE_VERDICTS.csv`, `PILOT_POWER.csv`, `PILOT_CHOICE.csv`; `git_commit` = `67058f6`,
  `git_dirty` = 0, SHA-256 dei tre piani uguali a quelli registrati (`4dceb568…`, `1fd8b51a…`,
  `b57bb177…`); `status` = «pilota di sviluppo, nessun verdetto». Nessun `Traceback` nel log.
- Convenzioni d'implementazione non fissate dal piano, dichiarate prima degli esiti
  (`docs/P2F_PILOT_IMPLEMENTATION_NOTE.md` §1): origine dei blocchi di B per T5 alla CR 2097;
  componenti per rotazione estratte separatamente per T3 e T5 (e fase dei salti per test);
  mediana di Φ sulle 2485 regioni del disegno. Il loro effetto non è stato misurato.

## 2. Controllo indipendente prima dell'interpretazione (`POST_CHECKS.csv`, 20 controlli, tutti superati)

- 43 200 righe; un solo `git_commit`, `git_dirty` = 0, SHA-256 dei piani coincidenti.
- In **ogni** riga con esito la statistica è finita: M 21 589 righe (anche `var_a`, `var_b`, φ̂,
  κ̂, σ̂_x² finiti), B 21 600 righe (p-value in (0, 1]). **Zero** righe con esito e statistica non
  finita (`POST_CHECKS_NONFINITE_ROWS.csv` vuoto): la lacuna del punto 6 della nota
  d'implementazione non si è manifestata; la regola `errore` non ha dovuto essere applicata.
- Verdetti ricalcolati dalle statistiche e dalle soglie (z₀,₀₁₂₅ = 2,241; p ≤ 0,0125): identici in
  tutte le righe.
- Riconteggio indipendente (`recount` in `p2f_checks.py`, codice separato da `summarize` del
  pilota) di falsi verdetti, errori, `scenario_ok` (36 righe), potenza (24 righe) e scelta (2
  righe): **identico** alle tabelle del pilota (`POST_CHECKS_*_RECOUNT.csv`). Nessun controllo
  obbligatorio del piano §6 è fallito.

## 3. Falsi verdetti sotto la nulla (9 scenari × 1000 tentativi, per test e candidata)

Regola di mantenimento (piano §5, A1 §4): una candidata è **mantenuta** se in **ognuno** dei 9
scenari ha al massimo 40 falsi verdetti sui 1000 tentativi (un esito `errore` non è un falso
verdetto) **e** una frazione di `errore` ≤ 2 %. Livello nominale 2,5 % (1,25 % per verso); errore
binomiale su 1000 tentativi a 2,5 %: 4,9 falsi. I conteggi «supportato / opposto» sono tra
parentesi. Le stesse risposte sintetiche sono state date alle due candidate.

### 3.1 T3 (tilt)

| s | Scenario | M: falsi / 1000 | M: `errore` | B: falsi / 1000 | B: `errore` |
|---|---|---|---|---|---|
| 0 | nessuna componente, normale | 21 (10 / 11) | 1 | 32 (15 / 17) | 0 |
| 1 | AR(1) φ = 0,5, κ = 0 | 18 (9 / 9) | 1 | 36 (16 / 20) | 0 |
| 2 | AR(1) φ = 0,9, κ = 0 | 23 (12 / 11) | 1 | **80** (46 / 34) | 0 |
| 3 | AR(1) φ = 0,9, κ = −0,8 | 23 (13 / 10) | 0 | **91** (43 / 48) | 0 |
| 4 | AR(1) φ = 0,5, κ = +0,6 | 24 (9 / 15) | 1 | **51** (25 / 26) | 0 |
| 5 | AR(1) φ = 0,8, eteroschedastico | 21 (10 / 11) | 0 | **85** (39 / 46) | 0 |
| 6 | AR(2) φ1 = 0,5, φ2 = 0,3 | 18 (12 / 6) | 0 | **94** (54 / 40) | 0 |
| 7 | salti ±1, blocchi di 20 CR | 19 (6 / 13) | 1 | **118** (55 / 63) | 0 |
| 8 | AR(1) φ = 0,8, t₄ | 21 (10 / 11) | 1 | **75** (43 / 32) | 0 |

M: massimo 24 falsi, `errore` ≤ 0,1 % in ogni scenario → **mantenuta**. B: oltre 40 falsi in 7
scenari su 9 (2–8), nessun `errore` → **non mantenuta**.

### 3.2 T5 (efficienza)

| s | Scenario | M: falsi / 1000 | M: `errore` | B: falsi / 1000 | B: `errore` |
|---|---|---|---|---|---|
| 0 | nessuna componente, normale | 21 (9 / 12) | 1 | **54** (30 / 24) | 0 |
| 1 | AR(1) φ = 0,5, κ = 0 | 23 (14 / 9) | 0 | **49** (20 / 29) | 0 |
| 2 | AR(1) φ = 0,9, κ = 0 | 19 (6 / 13) | 0 | **65** (25 / 40) | 0 |
| 3 | AR(1) φ = 0,9, κ = −0,8 | 23 (13 / 10) | 0 | **63** (33 / 30) | 0 |
| 4 | AR(1) φ = 0,5, κ = +0,6 | 19 (9 / 10) | 1 | 39 (18 / 21) | 0 |
| 5 | AR(1) φ = 0,8, eteroschedastico | 22 (14 / 8) | 0 | **53** (27 / 26) | 0 |
| 6 | AR(2) φ1 = 0,5, φ2 = 0,3 | 18 (8 / 10) | 0 | **58** (34 / 24) | 0 |
| 7 | salti ±1, blocchi di 20 CR | 34 (16 / 18) | 1 | **98** (50 / 48) | 0 |
| 8 | AR(1) φ = 0,8, t₄ | 22 (13 / 9) | 0 | **58** (28 / 30) | 0 |

M: massimo 34 falsi (scenario 7, salti: 3,4 %, sotto la soglia del 4 % ma circa 1,8 errori
binomiali sopra il 2,5 %), `errore` ≤ 0,1 % → **mantenuta**. B: oltre 40 falsi in 8 scenari su 9
(tutti tranne il 4), nessun `errore` → **non mantenuta**.

Osservazioni descrittive (non entrano nella regola): per B, nello scenario 0 senza componente
temporale, i 32 falsi su 1000 di T3 da soli non bastano a stabilire un'inflazione rispetto al
2,5 % (1,4 errori binomiali sopra); i 54 di T5 sono un segnale più netto (5,9 errori sopra), con
17 e 16 cluster. Il rigetto di B è sostenuto dagli altri scenari falliti; la causa non è stata
indagata, può essere un lavoro separato e non va corretta senza un nuovo piano. Per M i falsi
verdetti restano tra 1,8 e 2,4 % in T3 in tutti gli scenari, inclusi AR(2), salti e code pesanti,
che il modello AR(1) di M non contempla; in T5 tra 1,8 e 2,3 % tranne i salti (3,4 %).

## 4. Potenza (scenari 1 e 2; effetti −0,1, −0,2, −0,3 · γ0 per T3 e · η̄ per T5; 300 tentativi)

Regola (A1 §4): denominatore = tutti i 300 tentativi; un `errore` conta come mancato
rilevamento. Potenza tra i cataloghi con esito tra parentesi, dove differisce.

| Test | Scenario | Effetto | M | B |
|---|---|---|---|---|
| T3 | 1 (φ = 0,5) | −0,1 | 0,043 | 0,063 |
| T3 | 1 | −0,2 | 0,120 (1 `errore`) | 0,217 |
| T3 | 1 | −0,3 | 0,240 | 0,333 |
| T3 | 2 (φ = 0,9) | −0,1 | 0,030 | 0,103 |
| T3 | 2 | −0,2 | 0,050 | 0,157 |
| T3 | 2 | −0,3 | 0,167 | 0,343 |
| T5 | 1 (φ = 0,5) | −0,1 | 0,057 | 0,167 |
| T5 | 1 | −0,2 | 0,317 | 0,430 |
| T5 | 1 | −0,3 | 0,653 (0,656; 1 `errore`) | 0,767 |
| T5 | 2 (φ = 0,9) | −0,1 | 0,070 | 0,150 |
| T5 | 2 | −0,2 | 0,210 | 0,350 |
| T5 | 2 | −0,3 | 0,447 | 0,683 |

Potenza media negli scenari 1 e 2 all'effetto −0,2: T3 M 0,085, B 0,187; T5 M 0,263, B 0,390. La
potenza di B è calcolata a un livello effettivo superiore al nominale (§3) e **non è confrontabile**
con quella di M. Con la soglia per verso all'1,25 %, la potenza di M sugli effetti provati è bassa
in T3 (≤ 0,24) e moderata in T5 solo all'effetto −0,3 (0,45–0,65). Errore binomiale su 300
tentativi: circa 0,02–0,03.

## 5. Scelta (piano §5), separata per T3 e T5

Regola: se entrambe mantenute, potenza media più alta negli scenari 1 e 2 all'effetto −0,2 (a
parità entro 0,02 la candidata B); se una sola mantenuta, quella; se nessuna, il test resta
descrittivo.

- **T3: M** (unica mantenuta). **T5: M** (unica mantenuta). `PILOT_CHOICE.csv`, riconteggio
  identico.

La regola della potenza non è stata applicata, perché B non è mantenuta in nessuno dei due test.
La candidata B, nella forma del piano (blocchi di 13 CR con entrambi gli emisferi, pesi di Webb,
CR1, 16–17 cluster), è **scartata** per questo pilota; una sua variante richiederebbe un nuovo
piano e andrebbe dichiarata non cieca rispetto a questi risultati.

## 6. Diagnostica delle candidate (descrittiva, non entra nella scelta; `PILOT_DIAGNOSTICS_M.csv`, `PILOT_ERRORS.csv`)

- **Esiti `errore`**: 11 su 43 200 righe, tutti di M e tutti per «funzione di varianza:
  ottimizzazione non valida» (ottimizzatore senza convergenza dichiarata o ottimo su un vincolo);
  nessuno dalla REML (avvii validi in media 4,97–5,00 su 5), nessuno da varianze non finite. B non
  ha prodotto `errore`.
- **Parametri temporali di M** (mediana e intervallo 10–90 % sui 1000 cataloghi nulli; valori
  del generatore tra parentesi): T3 scenario 1 φ̂ 0,49 [0,35; 0,61] (0,5), scenario 2 0,90
  [0,83; 0,94] (0,9), scenario 3 κ̂ −0,81 [−0,96; −0,59] (−0,8), scenario 4 κ̂ 0,60 [0,39; 0,79]
  (0,6), σ̂_x² 53–56 [35–47; 69–85] negli scenari AR(1) e AR(2) (56,25); T5 analoghi
  (σ̂_x² 3,0–3,2·10⁻⁵⁰ contro 3,17·10⁻⁵⁰). Nello scenario 0 (nessuna componente) σ̂_x² è piccola
  (mediana 2,6 in T3, 4,6 % di 56,25) e al limite inferiore nel 6,7–8,5 % dei cataloghi, con φ̂ e
  κ̂ non identificati (intervallo 10–90 % pari ai vincoli). Nello scenario 7 (salti) l'AR(1)
  assorbe i livelli con φ̂ ≈ 0,94–0,95 e σ̂_x² sopra il valore marginale (63 in T3, 3,9·10⁻⁵⁰ in
  T5); nello scenario 6 (AR(2)) φ̂ ≈ 0,82.
- **Funzione di varianza**: b̂ medio nello scenario 5 −0,500 (T3) e −0,500 (T5), contro −0,5 del
  generatore; negli scenari omoschedastici b̂ medio entro ±0,003 di 0 (intervallo 10–90 % circa
  ±0,045, ±0,085 con le code t₄). Unità usate nella stima: 2443 (T3) e 2375 (T5); nessun residuo
  quadratico nullo in nessun catalogo.
- **Candidata B**: 17 cluster in T3 e 16 in T5 in ogni catalogo.

Questa diagnostica mostra che, sul disegno reale e con le risposte sintetiche del piano, M stima i
parametri del generatore con cui è coerente; non dice nulla sulla loro adeguatezza ai dati reali.

## 7. Che cosa il pilota stabilisce e che cosa no

- Stabilisce, per il protocollo P2f, la candidata da portare alla validazione: **M** per T3 e T5
  (modello temporale AR(1) bivariato per REML sulle medie di cella, funzione di varianza
  σ²(Φ) = exp(a + b log Φ) stimata con quasi-verosimiglianza gamma, decisione analitica).
- **Non valida M**: il protocollo dovrà prevedere una validazione con semi nuovi e distinti,
  scenari fissati prima (inclusi quelli del pilota, che restano non ciechi), criteri di
  accettazione propri e copertura; la regola «≤ 40 su 1000» del pilota è un criterio di
  sviluppo, non di accettazione.
- Non dice nulla sul quenching: nessun dato reale è stato usato; T3 e T5 restano descrittivi.
- La potenza di M agli effetti provati è bassa in T3: gli effetti di interesse scientifico e la
  numerosità vanno fissati nel protocollo con questo dato davanti.
- Le tre convenzioni della nota d'implementazione vanno risolte esplicitamente nel protocollo
  (origine dei blocchi, oggi solo per B; componenti separate per test; mediana di Φ), senza
  cambiarle in funzione di questi risultati.
- Il livello di B in T5 già senza componente temporale è un fatto da capire prima di riproporre
  un bootstrap a blocchi, non da aggiustare in corsa; non serve recuperare B per validare M.

## 8. Revisione esterna dello ZIP `2e197f8` (2026-11-11, incollata dall'utente; adottata)

Il revisore ha ricontato dai dati grezzi (43 200 righe senza chiavi duplicate, nessuna discrepanza
tra statistiche e verdetti, tabelle coincidenti, 11 errori, SHA-256 e provenienza uniformi) e
conferma M per T3 e T5 con le regole del pilota; non ha rieseguito il pilota né i test. Punti da
fissare **prima** del protocollo P2f, recepiti nel passaggio di consegne:
1. T5 con salti (3,4 %): supera il criterio del pilota ma non dimostra il controllo al 2,5 %; lo
   scenario resta decisivo nella validazione finale, con numerosità e criterio fissati
   considerando tutti gli scenari.
2. T3, potenza molto bassa (5–12 % a −0,2·γ0): un futuro mancato rilevamento sarebbe poco
   informativo; gli effetti di interesse vanno motivati scientificamente, non scelti per ottenere
   una potenza favorevole.
3. B: i 32 di T3 nello scenario 0 non bastano da soli a stabilire un'inflazione, i 54 di T5 sì;
   il rigetto resta sostenuto dagli altri scenari; la causa è un lavoro separato.
4. Congelare esattamente la procedura M da validare: gestione degli errori, celle con una sola
   unità, convenzioni del generatore, regole separate per T3 e T5.

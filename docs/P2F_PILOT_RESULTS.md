# Risultati del pilota di sviluppo P2f — scheletro (nessun esito ancora letto)

Stato: **scheletro scritto il 2026-11-11 durante l'esecuzione del pilota, prima di leggere qualunque
esito.** Le sezioni con «[da compilare]» si riempiono solo dopo il controllo indipendente
(`python/sharpbl/p2f_checks.py raw`, `docs/P2F_PILOT_IMPLEMENTATION_NOTE.md` §3). Le regole
applicate sono quelle registrate nel piano (`docs/P2F_PILOT_PLAN.md`, `83b0fc1`) §5 e
nell'emendamento A1 (`59971e7`) §4, riportate qui alla lettera perché il lettore possa verificarne
l'applicazione. **Sviluppo, non validazione**: il pilota sceglie o scarta procedure; non produce
verdetti sul quenching, non usa le risposte reali e non autorizza l'applicazione ai dati.

## 1. Esecuzione e provenienza

- Codice: `python/sharpbl/p2f_pilot.py`, commit `67058f6`; test preliminari superati sullo stesso
  commit (`results/P2F_PILOT/PRELIM_TESTS.csv`), tutti, inclusi 2a e 2b dell'emendamento A2.
- Avvio: 2026-11-11 10:17, distaccato, 12 processi; fine: [da compilare]. Esecuzione unica.
- Output: `results/P2F_PILOT/PILOT_RAW.csv.gz` (per catalogo, test e candidata),
  `PILOT_FALSE_VERDICTS.csv`, `PILOT_POWER.csv`, `PILOT_CHOICE.csv`; `git_commit` =
  [da compilare, atteso `67058f6`], `git_dirty` = [da compilare, atteso 0], SHA-256 dei tre piani
  [da compilare: coincidenza con `4dceb568…`, `1fd8b51a…`, `b57bb177…`].
- Convenzioni d'implementazione non fissate dal piano, dichiarate prima degli esiti:
  `docs/P2F_PILOT_IMPLEMENTATION_NOTE.md` §1 (origine dei blocchi T5 alla CR 2097; componenti per
  rotazione separate per T3 e T5; mediana di Φ sul disegno). Il loro effetto non è stato misurato.

## 2. Controllo indipendente prima dell'interpretazione (`POST_CHECKS.csv`)

[da compilare: numero di righe atteso 43 200; finitezza di statistiche, parametri di M e p-value
di B in ogni riga con esito; verdetti ricalcolati dalle statistiche; righe con esito ma statistica
non finita (attese 0; se presenti, elenco in `POST_CHECKS_NONFINITE_ROWS.csv`, regola `errore`
applicata nel riconteggio salvato a parte, output del pilota immutati); riconteggio indipendente
di falsi verdetti, potenza e scelta uguale alle tabelle del pilota, oppure quali righe
differiscono e perché. Se una discrepanza comporta un controllo obbligatorio fallito (piano §6),
lo si dichiara qui prima di adottare un conteggio.]

## 3. Falsi verdetti sotto la nulla (9 scenari × 1000 tentativi, per test e candidata)

Regola di mantenimento (piano §5, A1 §4): una candidata è **mantenuta** se in **ognuno** dei 9
scenari ha al massimo 40 falsi verdetti sui 1000 tentativi (un esito `errore` non è un falso
verdetto) **e** una frazione di `errore` ≤ 2 %. Si riporta anche la frequenza tra i cataloghi con
esito.

### 3.1 T3

| s | Scenario | M: falsi / 1000 | M: errori | B: falsi / 1000 | B: errori |
|---|---|---|---|---|---|
| 0 | nessuna componente, normale | [ ] | [ ] | [ ] | [ ] |
| 1 | AR(1) φ = 0,5, κ = 0 | [ ] | [ ] | [ ] | [ ] |
| 2 | AR(1) φ = 0,9, κ = 0 | [ ] | [ ] | [ ] | [ ] |
| 3 | AR(1) φ = 0,9, κ = −0,8 | [ ] | [ ] | [ ] | [ ] |
| 4 | AR(1) φ = 0,5, κ = +0,6 | [ ] | [ ] | [ ] | [ ] |
| 5 | AR(1) φ = 0,8, eteroschedastico | [ ] | [ ] | [ ] | [ ] |
| 6 | AR(2) φ1 = 0,5, φ2 = 0,3 | [ ] | [ ] | [ ] | [ ] |
| 7 | salti ±1, blocchi di 20 CR | [ ] | [ ] | [ ] | [ ] |
| 8 | AR(1) φ = 0,8, t₄ | [ ] | [ ] | [ ] | [ ] |

Mantenute: M [ ], B [ ].

### 3.2 T5

[stessa tabella]

Mantenute: M [ ], B [ ].

## 4. Potenza (scenari 1 e 2; effetti −0,1, −0,2, −0,3 · γ0 per T3 e · η̄ per T5; 300 tentativi)

Regola (A1 §4): denominatore = tutti i 300 tentativi; un `errore` conta come mancato
rilevamento. Si riporta anche la potenza tra i cataloghi con esito.

[tabelle per T3 e T5: scenario × effetto × candidata, potenza e potenza tra i validi]

## 5. Scelta (piano §5), separata per T3 e T5

- Se entrambe mantenute: potenza media più alta negli scenari 1 e 2 all'effetto −0,2; a parità
  entro 0,02 la candidata B, che fa meno ipotesi.
- Se una sola mantenuta: quella.
- Se nessuna: per quel test il pilota si ferma, il test resta descrittivo, salvo un nuovo motivo
  documentato e un nuovo piano.

T3: [da compilare]. T5: [da compilare].

## 6. Diagnostica delle candidate (descrittiva, non entra nella scelta)

[da compilare: per M, distribuzione di φ̂, κ̂, σ̂_x², `sigma_x_at_lower`, b̂ della funzione di
varianza, residui nulli contati, motivi degli `errore`; per B, numero di cluster, motivi degli
`errore`. Scenario 5 come verifica della tenuta della funzione di varianza (A1 §1).]

## 7. Che cosa il pilota non stabilisce

- Non valida la candidata scelta: il protocollo P2f dovrà prevedere una validazione con semi
  nuovi e distinti, scenari fissati prima e criteri di accettazione propri.
- Non dice nulla sul quenching: nessun dato reale è stato usato.
- Le tre convenzioni della nota d'implementazione vanno risolte esplicitamente nel protocollo;
  non si cambiano dopo aver visto quale candidata vince.
- Gli effetti di interesse scientifico restano da fissare nel protocollo (piano §5).

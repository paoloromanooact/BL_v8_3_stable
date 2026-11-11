# Risultati della validazione P2f — scheletro (nessun esito ancora letto)

Stato: **scheletro scritto il 2026-11-11 durante l'esecuzione della validazione (PID 968943,
avvio 14:46:47), prima di leggere qualunque esito.** Le sezioni «[da compilare]» si riempiono solo
dopo il controllo indipendente (§2). Le regole applicate sono quelle del protocollo congelato
`docs/PROTOCOL_P2F_VALIDATED_TEST.md` (`500c56a`, SHA-256 `8f030010…`) §5, riportate alla
lettera. **Validazione della procedura M, non applicazione**: nessun dato reale, nessun verdetto
sul quenching.

## 1. Esecuzione e provenienza

- Codice `python/sharpbl/p2f_validation.py` (`ed90e15`); provenienza registrata all'avvio:
  commit **`5c3b664`** (il confronto va fatto con questo, non con HEAD), `git_dirty` = 0.
- Test preliminari (protocollo §6.1): superati su `ed90e15` (`results/P2F/PRELIM_*_ed90e15.csv`)
  e su `5c3b664` (`results/P2F/PRELIM_*.csv`), stessi valori: REML 200/200 valide, φ̂ 0,795,
  κ̂ 0,499, σ̂_x² 0,994; funzione di varianza 2a b̂ −0,501, 2b −0,502, scarto di â ±0,003;
  Var(β̂) contro A scarto 0; recupero deterministico a −0,2 scarto ≤ 3·10⁻¹⁵; disegno 2485/394 e
  318/2375; semi disgiunti.
- Avvio 2026-11-11 14:46:47, 12 processi, fine: [da compilare]. Esecuzione unica.
- Output `results/P2F/VALIDATION_RAW.csv.gz` (304 000 righe attese), `VALIDATION_FALSE_VERDICTS.csv`,
  `VALIDATION_COVERAGE_POWER.csv`, `VALIDATION_DECISION.csv`: `git_commit` [da compilare],
  `git_dirty` [da compilare], SHA del protocollo [da compilare].

## 2. Controllo indipendente prima dell'interpretazione (`POST_CHECKS.csv`)

[da compilare: `p2f_checks.py vraw`: 304 000 righe, chiavi uniche, 24 gruppi nulli da 10 000 e
32 gruppi sotto effetto da 2000, provenienza `5c3b664`, SHA del protocollo invariato, identità
coperti + coda inferiore + coda superiore + errori = tentativi in ogni riga, finitezza,
quantile a precisione completa, verdetti e code ricalcolati dagli intervalli, riconteggio
indipendente di falsi verdetti, copertura, code e decisione. Una discrepanza blocca
l'interpretazione fino al chiarimento.]

## 3. Falsi verdetti sotto la nulla (12 scenari × 10 000, per test)

Criterio (§5): in **ognuno** dei 12 scenari, falsi verdetti ≤ 3,0 % dei 10 000 tentativi **e**
per ciascun verso ≤ 1,75 % **e** `errore` ≤ 1 %. Livello nominale 2,5 %.

| s | Scenario | T3 falsi (sup / opp) | T3 err | T5 falsi (sup / opp) | T5 err |
|---|---|---|---|---|---|
| 0–11 | [da compilare] | | | | |

## 4. Copertura, code e potenza sotto effetto (scenari 1, 2, 7, 9 × effetti −0,1, −0,2, −0,3, −0,35; 2000 ciascuno)

Criteri (§5): copertura ≥ 96,5 % **e** coda inferiore ≤ 2,0 % in ogni combinazione; coda
superiore e potenza riportate. Le conclusioni sulla copertura valgono per i quattro scenari
provati e non si estendono agli altri otto. Copertura osservata con incertezza Monte Carlo.

[tabelle per T3 e T5]

## 5. Decisione per test (§5)

Validato se tutti i criteri su falsi verdetti (12 scenari) e su copertura e coda inferiore (16
combinazioni) sono soddisfatti. T3: [da compilare]. T5: [da compilare]. Un test non validato
resta descrittivo; nessuna modifica e riesecuzione senza un nuovo protocollo con semi nuovi.

## 6. Diagnostica (descrittiva)

[da compilare: parametri stimati di M per scenario, `errore` e motivi, σ̂_x² al limite inferiore.]

## 7. Che cosa stabilisce e che cosa no

- Stabilisce se la procedura M soddisfa i criteri registrati negli scenari provati; «criteri di
  validazione superati» non dimostra una copertura effettiva del 97,5 %.
- Non dice nulla sul quenching: l'applicazione ai dati reali è un passo separato (protocollo §7),
  solo per i test validati e dopo la revisione esterna.

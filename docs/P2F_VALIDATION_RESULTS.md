# Risultati della validazione P2f — procedura M per T3 e T5

Stato: **esecuzione unica, terminata il 2026-11-12 alle 13:45; documento scritto il 2026-11-13 dopo il
controllo indipendente (§2) e una revisione esterna (§8).** Le regole sono quelle del protocollo
congelato `docs/PROTOCOL_P2F_VALIDATED_TEST.md` (`500c56a`, SHA-256 `8f030010…`) §5, applicate alla
lettera. **Validazione della procedura M, non applicazione**: risposte sintetiche sul disegno reale
(nessuna risposta reale), nessun verdetto sul
quenching.

**Dichiarazione.** La tabella di decisione (T3 validato, T5 no) è stata vista nell'ultima riga del
log, letta per verificare la fine del processo, **prima** del controllo indipendente. Il controllo
(`p2f_checks.py vraw`) era scritto e committato prima della fine dell'esecuzione (`0649f30`,
`a518115`) e non è stato modificato dopo. Lo scheletro di questo documento (`0649f30`) è stato scritto
durante l'esecuzione.

## 1. Esecuzione e provenienza

- Codice `python/sharpbl/p2f_validation.py` (`ed90e15`), scritto dopo il congelamento del protocollo.
- Test preliminari (§6.1) superati due volte con gli stessi valori: su `ed90e15`
  (`results/P2F/PRELIM_*_ed90e15.csv`) e su `5c3b664` (`results/P2F/PRELIM_*.csv`). REML 200/200
  valide (φ̂ 0,795, κ̂ 0,499, σ̂_x² 0,994); funzione di varianza 2a/2b b̂ −0,501/−0,502; Var(β̂)
  contro A scarto 0; recupero deterministico a −0,2 scarto ≤ 3·10⁻¹⁵; disegno 2485/394 e 318/2375; semi
  disgiunti.
- Avvio 2026-11-11 14:46:47, distaccato, PID 968943, 12 processi con `OMP_NUM_THREADS=1`; fine
  2026-11-12 13:45 (circa 23 h; ora di fine dalla data di scrittura degli output). Nessun errore nel log.
- Output `results/P2F/VALIDATION_RAW.csv.gz` (304 000 righe), `VALIDATION_FALSE_VERDICTS.csv`,
  `VALIDATION_COVERAGE_POWER.csv`, `VALIDATION_DECISION.csv`: `git_commit` = `5c3b664`,
  `git_dirty` = 0, SHA del protocollo `8f030010…`. Committati in `11b71f4`.

## 2. Controllo indipendente prima dell'interpretazione (`results/P2F/POST_CHECKS.csv`: 23 su 23)

304 000 righe con chiavi uniche e uguali all'insieme esatto atteso (24 gruppi nulli da 10 000, 32 sotto
effetto da 2000); provenienza `5c3b664`, albero pulito, SHA del protocollo invariato; in ogni riga
coperti + coda inferiore + coda superiore + errori = 1; valori finiti in tutte le 303 889 righe con
esito; semi-intervalli (β̂ − lo)/SE e (hi − β̂)/SE uguali al quantile a precisione completa; verdetti e
code ricalcolati dagli intervalli; riconteggio di falsi verdetti, copertura, code e decisione con
codice separato, identico alle tabelle. Errori: 111 su 304 000 (§6).

**Etichetta discordante (dichiarata, output non riscritti):** la colonna `status` di
`results/P2F/POST_CHECKS*.csv` vale «pilota di sviluppo, nessun verdetto», ereditata da
`p2f_pilot.provenance()`, benché il controllo riguardi la validazione. Gli SHA-256 registrati
identificano correttamente i quattro output controllati e il protocollo.

## 3. Falsi verdetti sotto la nulla (12 scenari × 10 000, per test)

Criterio (§5): in ognuno dei 12 scenari falsi verdetti ≤ 3,0 %, per ciascun verso ≤ 1,75 %, `errore`
≤ 1 %. In grassetto i casi che non soddisfano il criterio.

| s | Scenario | T3 falsi % (sup / opp) | T3 err | T5 falsi % (sup / opp) | T5 err |
|---|---|---|---|---|---|
| 0 | nessuna componente | 1,87 (0,91 / 0,96) | 1 | 1,81 (0,87 / 0,94) | 3 |
| 1 | AR(1) φ 0,5 | 2,42 (1,18 / 1,24) | 6 | 2,56 (1,31 / 1,25) | 8 |
| 2 | AR(1) φ 0,9 | 2,79 (1,37 / 1,42) | 5 | 2,85 (1,45 / 1,40) | 4 |
| 3 | AR(1) φ 0,9, κ −0,8 | 2,82 (1,39 / 1,43) | 4 | 2,73 (1,40 / 1,33) | 7 |
| 4 | AR(1) φ 0,5, κ +0,6 | 2,59 (1,38 / 1,21) | 1 | 2,58 (1,22 / 1,36) | 2 |
| 5 | AR(1) φ 0,8, eterosch. | 2,97 (1,55 / 1,42) | 0 | 2,89 (1,49 / 1,40) | 1 |
| 6 | AR(2) | 2,69 (1,36 / 1,33) | 3 | 2,69 (1,26 / 1,43) | 3 |
| 7 | salti 20 CR | 2,56 (1,25 / 1,31) | 3 | **3,35 (1,60 / 1,75)** | 4 |
| 8 | AR(1) φ 0,8, t₄ | 2,78 (1,40 / 1,38) | 2 | 2,99 (1,54 / 1,45) | 8 |
| 9 | stime reali T3, σ_x×2, eterosch., t₄ | 2,43 (1,32 / 1,11) | 1 | 2,35 (1,12 / 1,23) | 0 |
| 10 | salti 13 CR comuni | 1,61 (0,76 / 0,85) | 4 | 1,95 (1,03 / 0,92) | 8 |
| 11 | AR(2), κ −0,8 | 2,52 (1,35 / 1,17) | 1 | 2,64 (1,31 / 1,33) | 3 |

T3: tutti i 12 scenari entro i limiti (falsi verdetti 1,61–2,97 %). T5: 11 scenari entro i limiti;
**scenario 7** (salti ±1 su blocchi di 20 CR, indipendenti tra emisferi) **335 su 10 000 = 3,35 %**
(160 supportato, 175 opposto, 4 errori): supera il limite complessivo del 3,0 %, non quelli per verso.

## 4. Copertura, code e potenza sotto effetto (scenari 1, 2, 7, 9 × 4 effetti; 2000 ciascuno)

Criteri (§5): copertura ≥ 96,5 % e coda inferiore ≤ 2,0 % in ogni combinazione; coda superiore e
potenza riportate. Incertezza Monte Carlo della copertura: errore standard binomiale su 2000. In
grassetto la combinazione che non soddisfa i criteri.

| Test | s | Effetto | Copertura % (± MC) | Coda inf. % | Coda sup. % | Err | Potenza % |
|---|---|---|---|---|---|---|---|
| T3 | 1 | −0,10 | 97,30 ± 0,36 | 1,25 | 1,40 | 1 | 4,70 |
| T3 | 1 | −0,20 | 97,50 ± 0,35 | 1,20 | 1,20 | 2 | 11,10 |
| T3 | 1 | −0,30 | 97,30 ± 0,36 | 1,60 | 1,10 | 0 | 24,65 |
| T3 | 1 | −0,35 | 97,20 ± 0,37 | 1,45 | 1,35 | 0 | 34,70 |
| T3 | 2 | −0,10 | 97,55 ± 0,35 | 0,75 | 1,60 | 2 | 3,75 |
| T3 | 2 | −0,20 | 97,20 ± 0,37 | 1,40 | 1,40 | 0 | 7,80 |
| T3 | 2 | −0,30 | 96,95 ± 0,38 | 1,30 | 1,70 | 1 | 17,50 |
| T3 | 2 | −0,35 | 96,95 ± 0,38 | 1,85 | 1,10 | 2 | 23,80 |
| T3 | 7 | −0,10 | 97,20 ± 0,37 | 1,50 | 1,25 | 1 | 4,00 |
| T3 | 7 | −0,20 | 96,60 ± 0,41 | 1,75 | 1,55 | 2 | 9,55 |
| T3 | 7 | −0,30 | 97,70 ± 0,34 | 1,05 | 1,25 | 0 | 17,25 |
| T3 | 7 | −0,35 | 97,60 ± 0,34 | 1,25 | 1,10 | 1 | 22,75 |
| T3 | 9 | −0,10 | 97,00 ± 0,38 | 1,75 | 1,20 | 1 | 2,25 |
| T3 | 9 | −0,20 | 98,10 ± 0,31 | 1,15 | 0,75 | 0 | 4,55 |
| T3 | 9 | −0,30 | 98,15 ± 0,30 | 0,85 | 1,00 | 0 | 9,25 |
| T3 | 9 | −0,35 | 97,80 ± 0,33 | 1,20 | 1,00 | 0 | 12,85 |
| T5 | 1 | −0,10 | 97,60 ± 0,34 | 1,40 | 1,00 | 0 | 11,25 |
| T5 | 1 | −0,20 | 97,20 ± 0,37 | 1,40 | 1,40 | 0 | 38,50 |
| T5 | 1 | −0,30 | 97,50 ± 0,35 | 1,30 | 1,20 | 0 | 75,10 |
| T5 | 1 | −0,35 | 97,05 ± 0,38 | 1,60 | 1,25 | 2 | 86,75 |
| T5 | 2 | −0,10 | 96,90 ± 0,39 | 1,35 | 1,65 | 2 | 7,80 |
| T5 | 2 | −0,20 | 96,90 ± 0,39 | 1,30 | 1,70 | 2 | 26,30 |
| T5 | 2 | −0,30 | 97,00 ± 0,38 | 1,35 | 1,55 | 2 | 54,60 |
| T5 | 2 | −0,35 | 96,95 ± 0,38 | 1,25 | 1,75 | 1 | 67,65 |
| T5 | 7 | −0,10 | 97,00 ± 0,38 | 1,45 | 1,45 | 2 | 8,50 |
| T5 | 7 | −0,20 | 96,75 ± 0,40 | 1,20 | 2,00 | 1 | 27,35 |
| T5 | 7 | −0,30 | **96,10 ± 0,43** | **2,30** | 1,45 | 3 | 52,70 |
| T5 | 7 | −0,35 | 96,60 ± 0,41 | 1,80 | 1,60 | 0 | 64,25 |
| T5 | 9 | −0,10 | 97,50 ± 0,35 | 1,10 | 1,40 | 0 | 5,10 |
| T5 | 9 | −0,20 | 98,05 ± 0,31 | 1,25 | 0,70 | 0 | 11,60 |
| T5 | 9 | −0,30 | 97,55 ± 0,35 | 1,30 | 1,15 | 0 | 29,95 |
| T5 | 9 | −0,35 | 97,95 ± 0,32 | 0,90 | 1,10 | 1 | 36,55 |

T3: tutte le 16 combinazioni entro i criteri (copertura 96,60–98,15 %, coda inferiore massima 1,85 %).
T5: 15 combinazioni entro i criteri; **scenario 7, effetto −0,3**: 1922 su 2000 coperti (96,10 %),
46 sotto (2,30 %), 29 sopra (1,45 %), 3 errori: falliscono copertura e coda inferiore.

## 5. Decisione (§5)

- **T3: criteri di validazione superati negli scenari provati.** L'intervallo di M si descrive come
  «livello nominale 97,5 %; criteri di validazione superati negli scenari provati». Non dimostra una
  copertura effettiva del 97,5 %; le conclusioni sulla copertura valgono per i quattro scenari sotto
  effetto e non si estendono agli altri otto.
- **T5: non validato.** Fallisce nello scenario a salti (falsi verdetti sotto la nulla e copertura a
  −0,3), lo stesso punto debole emerso nel pilota (3,4 %). T5 **resta descrittivo**; lo scenario fallito
  non si rimuove e nessuna correzione è possibile senza un nuovo protocollo con semi nuovi.

## 6. Diagnostica (descrittiva)

- Errori: 111, tutti «funzione di varianza: ottimizzazione non valida» (44 in T3, 67 in T5); nessuno
  dalla REML. Nessun errore è contato come falso verdetto; sotto effetto vale come mancata copertura e
  mancato rilevamento.
- Parametri stimati (mediane sotto la nulla): φ̂ e κ̂ vicini ai valori del generatore negli scenari AR(1)
  (per esempio φ̂ 0,90 e κ̂ −0,81 nello scenario 3, φ̂ 0,53 e κ̂ −0,85 nello scenario 9); σ̂_x² 53–56 in
  T3 (vero 56,25) e circa 3,1·10⁻⁵⁰ in T5 (vero 3,17·10⁻⁵⁰), 223 e 1,26·10⁻⁴⁹ nello scenario 9 con σ_x
  raddoppiata; b̂ della funzione di varianza −0,50 negli scenari eteroschedastici (5 e 9). Nei salti
  (scenari 7 e 10) l'AR(1) assorbe i livelli con φ̂ 0,91–0,95; nello scenario 10, con salti comuni ai
  due emisferi, κ̂ va al limite 0,98. Nello scenario 0 σ̂_x² è al limite inferiore nel 7,8 % (T3) e
  5,5 % (T5) dei cataloghi.
- Potenza di M per T3: 2,25–34,70 % sugli effetti provati; all'effetto di riferimento −0,2·γ0
  4,55–11,10 % nei quattro scenari. Per T5 (non validato) è solo riportata.

## 7. Che cosa stabilisce e che cosa no

- Stabilisce che la procedura M soddisfa i criteri registrati **per T3** negli scenari provati; per T5
  no.
- Non è evidenza osservativa di quenching: sono state usate solo risposte sintetiche sul disegno reale.
- Con la potenza di T3 (5–11 % a −0,2·γ0), un esito «non deciso» sui dati reali non dimostrerebbe
  assenza di quenching; un'esclusione di un quenching ≥ δ si potrà affermare solo con la regola del
  protocollo §7 (estremo inferiore dell'intervallo > −δ·γ0).
- Prossimo passo, solo per T3: applicazione ai dati reali con `p2f_apply.py --test T3 --real` (una
  sola esecuzione; lo script rifiuta T5 e richiede il controllo indipendente superato sugli stessi
  output), con risultati in `docs/P2F_RESULTS.md`.

## 8. Revisione esterna (2026-11-13, ZIP `0f12ed1`, SHA-256 `60ccbe2c…`)

Il revisore ha ricontato le 304 000 righe con uno script separato che non importa il codice
scientifico (53 asserzioni superate, artefatti fuori dal repository): identità dei quattro output tra
ZIP e repository, 23 controlli originali legati agli stessi hash, commit completo e albero pulito,
identità dei cinque moduli scientifici con `5c3b664`, insieme esatto delle chiavi, finitezza,
semi-intervalli, verdetti, code ed errori ricalcolati, decisione ricostruita con le soglie intere del
protocollo. Nessuna discrepanza. Ha confermato T3 validato e T5 non validato con i numeri di §3–§4, e
ha chiesto di dichiarare la lettura anticipata della decisione nel log (fatto sopra) e l'etichetta
discordante di `POST_CHECKS` (§2). Non è una riesecuzione della stima M per catalogo; fine e durata
riportate non sono certificate dallo ZIP.

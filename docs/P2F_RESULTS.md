# P2f — applicazione ai dati reali della procedura M validata: T3 (tilt contro attività)

Stato: **esecuzione unica, 2026-11-13 alle 09:05, sul commit `42fcd01` (albero pulito)**, dopo la
validazione (`docs/P2F_VALIDATION_RESULTS.md`), il suo controllo indipendente e la revisione esterna.
Regole: protocollo `docs/PROTOCOL_P2F_VALIDATED_TEST.md` (`500c56a`) §1 e §7. **Solo T3**: T5 non è
validato e resta descrittivo (lo script lo ha rifiutato, come previsto). Output
`results/P2F/REAL_T3.csv` e `REAL_T3_SENSITIVITY.csv` (stampa a schermo conservata in `logs/p2f_apply_T3.log`, fuori da Git); provenienza
nei file (commit `42fcd01`, `git_dirty` = 0, protocollo `8f030010…`, validazione `5c3b664`, SHA-256
della decisione di validazione). Un secondo tentativo di esecuzione è stato rifiutato dallo script
(«una sola esecuzione per test»).

**Identità con lo ZIP revisionato (verifica a posteriori, dichiarata).** Il revisore ha esaminato
lo ZIP `0f12ed1` (SHA-256 `60ccbe2c…`); l'applicazione è stata eseguita su `42fcd01`. La richiesta
di verificare l'identità **prima** dell'esecuzione è arrivata dopo; la verifica è stata fatta
subito dopo: tra `0f12ed1` e `42fcd01` sono cambiati solo `CHANGELOG.md`, `docs/HANDOFF.md`,
`docs/P2F_VALIDATION_RESULTS.md` e `docs/RESULTS_INDEX.md`; `python/`, il protocollo,
`results/P2F/` (output della validazione e controlli), `results/P1/`, `ancillary/` e
`requirements-v84.txt` sono **identici** (`git diff --quiet`). Nessuna modifica sostanziale.

## 1. Risultato principale

Modello (P2 §4, T3): γ_i = (γ0,c,h + β_T (Â_i − 1)) sin|λ_i| + ε_i, WLS con pesi Φ, campione S (2485
record primari HARP, 394 celle CR × emisfero), attività `A_monthly` (numero di macchie emisferico mensile SILSO
normalizzato alla media HMI). Il quenching del tilt prevede β_T < 0.

| Grandezza | Valore |
|---|---|
| β̂_T (pendenza del coefficiente di Joy) | **−3,59°** per unità di Â (−0,149·γ0, con γ0 = 24°) |
| Errore standard (procedura M) | 3,12° |
| Intervallo, livello nominale 97,5 %; criteri di validazione superati negli scenari provati | **[−10,58°; +3,41°]**, cioè [−0,441; +0,142]·γ0 |
| Esito (protocollo §1) | **non deciso** (l'intervallo comprende 0) |
| Effetti della griglia esclusi (§7: estremo inferiore > −δ·γ0) | **nessuno** (δ = 0,1, 0,2, 0,3, 0,35: l'estremo inferiore −0,441·γ0 è sotto −0,35·γ0) |

Lettura, con le cautele registrate:
- La stima puntuale è negativa, nel verso previsto dal quenching, ma l'intervallo comprende zero: i
  dati non decidono il segno di β_T con questa procedura.
- **«Non deciso» non è assenza di quenching.** La potenza **osservata nelle simulazioni di
  validazione** all'effetto di riferimento −0,2·γ0 è 4,55–11,10 % nei quattro scenari provati; non è
  una stima della potenza sul processo reale (la componente temporale stimata sui dati reali,
  σ̂_x² = 4,34 deg², è diversa da quella degli scenari sotto effetto, 56,25 o 225 deg²).
- L'intervallo osservato comprende sia β_T = 0 sia l'effetto supplementare −0,35·γ0 della griglia,
  la cui interpretazione come trasferimento del quenching tra cicli all'attività mensile resta
  **ipotetica** (protocollo §2). L'estremo inferiore −0,441·γ0 descrive l'intervallo ottenuto, non un
  limite fisico del quenching.
- Per le esclusioni previste dal protocollo (§7), nessun effetto della griglia è escluso. L'estremo
  superiore dell'intervallo è +0,142·γ0 (+3,41°); non si introduce un criterio di esclusione per
  valori positivi.
- β_T è la pendenza del coefficiente di Joy: per una regione a latitudine fissa la variazione del
  tilt per unità di attività è β_T sin|λ| (per esempio circa −0,9° a 15°), non −3,59° a tutte le
  latitudini. Le unità del campione sono 2485 record primari HARP, non 2485 regioni fisiche
  necessariamente indipendenti.
- L'intervallo vale per il modello e gli scenari della validazione: copertura verificata in quattro
  scenari sotto effetto (AR(1) φ 0,5 e 0,9, salti di 20 CR, parametri alle stime reali con code
  pesanti), non oltre.

## 2. Diagnostica della procedura sui dati reali (descrittiva)

- Funzione di varianza: b̂ = −0,348 (la varianza individuale decresce con Φ, come Φ^−0,35),
  â = 6,42; 2443 regioni nella stima (le 42 celle con una sola regione escluse dalla stima, come da
  protocollo), nessun residuo quadratico nullo.
- Componente temporale: φ̂ = 0,751, κ̂ = −0,423, σ̂_x² = 4,34 deg² (non al limite inferiore); 5 avvii
  validi su 5. La componente per rotazione stimata è molto più piccola di quella usata nei
  generatori della validazione sotto effetto (σ_x² = 56,25 deg², o 225 deg² nello scenario 9). Lo
  scenario 0, senza componente temporale, controlla i falsi verdetti sotto la nulla (1,87 %); non
  estende da solo la copertura sotto effetto ai regimi intermedi, che non sono stati provati.
- Confronto con P2 descrittivo (`docs/P2_RESULTS_DESCRIPTIVE.md`, procedura non validata): stessa
  stima puntuale (−3,6°), intervallo P2 al 97,5 % [−8,0°; 1,3°]; l'intervallo di M è più largo
  ([−10,6°; 3,4°]). Le due procedure non sono confrontabili come verdetti: solo M ha superato una
  validazione.

## 3. Sensibilità (stesse formule, **non validate**, nessun verdetto)

| Campione | Attività | Regioni / celle | β̂_T (°) | Intervallo (non validato) |
|---|---|---|---|---|
| S | A_smooth13 | 2485 / 394 | −3,57 | [−13,54; +6,40] |
| S | A_usflux | 2485 / 394 | −4,61 | [−9,85; +0,62] |
| S1 (Φ ≥ 5·10²⁰ Mx) | A_monthly | 2805 / 410 | −3,43 | [−10,53; +3,67] |
| S2 (Φ ≥ 3·10²¹ Mx) | A_monthly | 1771 / 370 | −3,43 | [−10,51; +3,66] |
| S3 (senza diagnostica) | A_monthly | 2204 / 392 | −1,94 | [−8,80; +4,92] |
| S4 (una sola regione NOAA) | A_monthly | 1479 / 380 | −5,83 | [−14,45; +2,80] |
| S5 (record di controllo) | A_monthly | 4001 / 417 | −3,26 | [−10,81; +4,30] |
| S6 (con AMBIGUOUS) | A_monthly | 2485 / 394 | −3,59 | [−10,58; +3,41] |

- La stima è negativa in tutte le 8 sensibilità e tutti gli intervalli comprendono zero. Le
  sensibilità sono correlate (stessi dati in larga parte), non repliche indipendenti. Gli
  intervalli delle sensibilità non sono validati: la procedura è stata validata solo sul disegno di
  S con `A_monthly`.
- S6 coincide con S perché nel campione non ci sono regioni AMBIGUOUS con le altre condizioni
  soddisfatte (2485 regioni in entrambi).
- A_usflux dà l'intervallo più stretto e più vicino all'esclusione dello zero; è la misura di
  attività più vicina al meccanismo degli inflow, ma non è validata e non si promuove a test
  principale dopo averla vista.

## 4. Che cosa si può dire

- Con la procedura validata, la pendenza del tilt rispetto all'attività dentro il ciclo, nei cicli
  24–25 osservati da HMI, è **stimata negativa ma non distinta da zero**; il risultato è
  **compatibile** sia con l'assenza di dipendenza sia con l'effetto supplementare −0,35·γ0 della
  griglia, la cui interpretazione come trasferimento dal quenching tra cicli resta ipotetica. Il
  risultato osservato non distingue zero dagli effetti negativi della griglia; nelle simulazioni
  provate la potenza è bassa. Non si attribuisce questo limite al solo numero di cicli.
- Non si attribuisce alcun meccanismo; un esito negativo non avrebbe comunque distinto il quenching
  da effetti di selezione o di blending.
- T5 (efficienza della sorgente) resta descrittivo: la procedura non è validata (scenario a salti).

## 5. Revisione esterna (2026-11-13, ZIP `0c22bee`, SHA-256 `1922faa9…`)

Nessuna discrepanza numerica (19 controlli, script indipendente senza i moduli del progetto):
ricostruiti campione S (2485 record, 394 celle, 42 singoletti), pendenza (−3,5874055°), varianza con i
parametri salvati (8,0028 deg² individuale + 1,7309 deg² temporale, SE 3,11988°) e intervallo; esito
«non deciso», nessun effetto della griglia escluso. La ricostruzione non ripete l'ottimo REML né la
stima della funzione di varianza. Le correzioni di formulazione richieste (nessuna esclusione di
effetti positivi, potenza come proprietà delle simulazioni, −0,35·γ0 come effetto ipotetico, unità
come record HARP, β_T come pendenza del coefficiente di Joy, sensibilità correlate) sono state
recepite qui senza cambiare output.

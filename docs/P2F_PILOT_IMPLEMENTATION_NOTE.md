# Nota d'implementazione del pilota P2f — convenzioni non specificate dal piano

Stato: **registrata il 2026-11-11 alle 10:36, mentre il pilota è in esecuzione (PID 948816, circa
1750 cataloghi su 10 800) e prima di leggere qualunque esito.** Si riferisce al codice
`python/sharpbl/p2f_pilot.py` al commit `67058f6` (quello da cui il pilota è partito), al piano
`docs/P2F_PILOT_PLAN.md` (`83b0fc1`) e agli emendamenti A1 (`59971e7`) e A2 (`48039d7`). Nasce da una
revisione indipendente del codice rispetto a piano ed emendamenti, rivista da un revisore esterno.
Non modifica il codice in esecuzione, non introduce regole nuove e non autorizza verdetti. Il
protocollo finale di P2f dovrà risolvere esplicitamente le ambiguità elencate in §1; non si
cambiano partizioni o convenzioni dopo aver visto quale candidata vince.

## 1. Convenzioni adottate dal codice dove il piano non specifica (dichiarate ora)

1. **Origine dei blocchi della candidata B per T5.** Il piano §4 B.1 dice «partizione fissa a
   partire dalla prima CR del disegno». Il codice (`candidate_b`) fa partire i blocchi di 13 CR
   dalla prima CR delle **unità del test**: CR 2096 per T3 (prima CR del disegno) e **CR 2097 per
   T5** (prima cella con almeno 3 regioni). Per T5 i confini dei blocchi sono quindi spostati di
   una rotazione rispetto a una partizione dalla CR 2096. I blocchi con dati sono 16 in entrambe
   le letture (`results/P2F_PILOT/DESIGN_CHECKS.csv`). L'effetto sulla candidata B per T5 **non
   è stato misurato**.
2. **Componenti per rotazione separate tra T3 e T5.** Il piano §2 usa lo stesso simbolo
   x_{t,h} per i due test. Il codice (`responses`) estrae, nello stesso catalogo, **due
   componenti indipendenti**, una per T3 e una per T5, dallo stesso generatore; nello scenario 7
   anche la fase dei salti è estratta due volte (una per test), dove il piano dice «estratta per
   catalogo». Il generatore di P2d usava anch'esso componenti distinte per tilt e dipolo. Le
   regole di scelta sono separate per test, quindi non confrontano i due test tra loro; la
   dipendenza tra gli esiti di T3 e T5 nello stesso catalogo non è usata.
3. **Mediana di Φ nel fattore eteroschedastico** c_i = (Φ_i / mediana Φ)^−0,25 (scenario 5 e
   test preliminare 2). Il codice usa la mediana sulle **2485 regioni del disegno** per entrambi
   i test; per T5 le unità simulate sono 2375 regioni, con mediana diversa
   (6,155·10²¹ contro 6,228·10²¹ Mx, `DESIGN_CHECKS.csv`). Il piano non specifica l'insieme.
   L'effetto non è stato misurato.

## 2. Controllo incompleto e scelta numerica

4. **Disegno congelato.** Il codice asserta in ogni catalogo 2485 regioni T3 e 318 celle T5
   (piano §6.2); non asserta le 394 celle T3 né le 2375 regioni T5. I conteggi sono
   conservati in forma riproducibile in `results/P2F_PILOT/DESIGN_CHECKS.csv`
   (`python/sharpbl/p2f_checks.py design`, dal catalogo P1 senza risposte reali; risposte
   sintetiche con il seme 5 000 950, nell'intervallo riservato ai test e mai usato, solo per
   costruire le unità): 2485 regioni su 210 CR (2096–2316), 394 celle T3 di cui 42 con una sola
   regione, 318 celle T5 con 2375 regioni su 176 CR (2097–2315), 17 e 16 blocchi con dati,
   `sinlat` positivo in entrambi gli emisferi (è sin|λ|), nessuna cella T3 con regioni di due
   cicli.
5. **Cholesky fallita nella REML.** A1 §2 dice ℓ = −∞ per quel punto. Il codice restituisce
   la penalità finita 1e100 al minimizzatore e considera valido un avvio solo se
   l'ottimizzatore dichiara convergenza **e** il valore finale è < 1e99 (`reml_fit`). È
   equivalente a scartare l'avvio purché la penalità non possa essere accettata come soluzione,
   ed è così: un ottimo con valore 1e100 non supera il controllo.

## 3. Lacuna nella gestione degli errori e controllo previsto

6. **Finitezza della statistica di M.** Il codice verifica che Var(β̂) sia finita e positiva,
   ma non che β̂ (e quindi la statistica) sia finito; una statistica non finita produrrebbe il
   verdetto «non deciso» invece dell'esito `errore` del piano §6.4. Prima di interpretare i
   risultati si esegue `python/sharpbl/p2f_checks.py raw`, che su `PILOT_RAW.csv.gz`:
   - verifica che in ogni riga con esito la statistica (M e B), i parametri stimati di M e i
     p-value di B siano finiti, e ricalcola i verdetti dalle statistiche;
   - se trova righe con esito ma statistica non finita, le conserva
     (`POST_CHECKS_NONFINITE_ROWS.csv`), **applica la regola prevista per gli errori** (esito
     `errore`: non è un falso verdetto, conta nella frazione senza esito, nella potenza vale
     come mancato rilevamento) e riconta;
   - riconta in ogni caso, con codice scritto a parte, falsi verdetti, frazioni di `errore`,
     potenza e scelta con le regole del piano §5 e A1 §4, e li confronta con
     `PILOT_FALSE_VERDICTS.csv`, `PILOT_POWER.csv` e `PILOT_CHOICE.csv`.
   Esito in `results/P2F_PILOT/POST_CHECKS.csv`. Se il riconteggio con la regola degli errori
   cambia un conteggio o la scelta, fa fede il riconteggio e la differenza va riportata in
   `docs/P2F_PILOT_RESULTS.md`; «non raggiungibile» si afferma solo se il controllo trova zero
   righe non finite.

## 4. Punti verificati senza discrepanze

Generatore (AR(1) bivariato stazionario con correlazione κ, AR(2) con varianza di popolazione 1 e
200 passi di riscaldamento, salti ±1 con fase uniforme, t₄ riscalata a varianza 1, fattore
eteroschedastico), semi (formule del piano §5, assenza di sovrapposizioni), funzione di varianza
(media attesa esatta in forma stabile, quasi-verosimiglianza gamma, gradiente analitico, partenza,
vincoli, tolleranze, esclusione dei singoletti dalla stima, residui nulli tenuti e contati),
REML (risposte medie di cella, matrice aggregata esatta, covarianza, log-verosimiglianza ristretta,
vincoli, θ₀, cinque avvii, tolleranze, `sigma_x_at_lower`, condizionamento), decisione analitica
di M (verificata con i parametri veri nel test preliminare 4), candidata B (pesi di Webb, B = 9999,
statistica CR1, repliche vettorizzate identiche al calcolo diretto nel test 3, p-value con la
correzione per B finito), conteggi e regole di scelta (≤ 40 falsi su 1000 tentativi, `errore`
≤ 2 %, potenza su tutti i 300 tentativi, parità entro 0,02 a favore di B), controllo che i test
preliminari siano dello stesso commit e dell'albero pulito, provenienza (commit, `git_dirty`,
SHA-256 dei tre piani). Gli SHA-256 dei piani nell'albero coincidono con quelli dei commit
registrati.

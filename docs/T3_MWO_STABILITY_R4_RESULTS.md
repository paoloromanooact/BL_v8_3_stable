# T3 su MWO, catalogo R4 — esiti dei controlli di stabilità S1–S4

23 novembre 2026 (Claude). Oggetto: `--stability` eseguito da `132f722` (patch di collegamento applicata dopo la
revisione di Codex `cf7cc61`), uscite conservate prima della lettura in `5a52d8a`, riconteggio indipendente
`t3_mwo_stability_recount.py --check` **16/16**, ricevuta completa (partial false, legata al META
`b6789830…`) in `2f9edf6`. Diagnosi post hoc di S1 in `a387d18`. La stima di β₃ **non è stata eseguita**.

## Esito della regola congelata (§6)

**β₃ sarà riportato come descrittivo, senza verdetto.** Cause registrate: «S1 non determinato; S2 stabilità non
determinata». Ciascuna delle due basta da sola. La validazione accettata a 15° («verdetto possibile») era una
condizione necessaria, non sufficiente: questa lettura la supera senza contraddirla.

Il terzo criterio della regola è rispettato: le epoche non verificabili (E1, E7) contengono l'1,6 % dei record
isolati, sotto la soglia del 20 %.

## Sottoinsieme del controllo

- Record isolati: 5223. Con tilt in luce bianca DPD utilizzabile: **4694 (89,9 %)**, sopra la soglia del 70 %.
- Celle verificabili: E2–E6 ed E8, per emisfero (12 celle).

## S1 — scarto relativo fra epoche: «non determinato»

- Bootstrap a blocchi di 6 CR, 2000 repliche, seme 69 000 001: **573 repliche singolari (28,7 %)**, sopra la soglia
  del 5 %. Lo stato è quindi «non determinato» per regola.
- **Diagnosi post hoc** (`scripts/t3_mwo_s1_singular_diagnosis.py`, non prevista dal protocollo, non cambia l'esito,
  non legge SEALED): il replay riproduce esattamente le 573 repliche. Tutte vengono da due celle **non verificabili**,
  che il testo congelato mantiene nel modello di S1 (somma su tutte le (e, h)) ma esclude dal confronto:
  - E1N, 5 record in 2 blocchi: 529 repliche con colonne sin|λ̄| e costante collineari;
  - E7S, 17 record in 3 blocchi: 70 repliche.

  Nessuna cella verificabile causa singolarità. L'implementazione segue il testo; la conseguenza (stato deciso da
  celle che non entrano nel confronto) è un limite del disegno di S1, da valutare con Codex. La regola non si cambia
  dopo la lettura.
- Tabella descrittiva (`S1_TABLE.csv`, intervalli percentili sulle 1427 repliche non singolari):
  - una sola cella ha intervallo che esclude zero con |a − ā| > 2,4°: **E4N**, a − ā = −48,4°, intervallo
    [−76,8°, −16,5°];
  - le altre undici includono zero, spesso con intervalli molto larghi (per esempio E6S [−155°, +167°]).

  Se S1 fosse stato determinato con queste repliche, E4N lo avrebbe reso «instabile». Questa è una lettura
  condizionale, non un esito.
- Unità: a_{e,h} è uno scarto di coefficiente di Joy (gradi per unità di sin|λ̄|), non un tilt; gli scarti grandi
  delle celle piccole riflettono anche la leva in latitudine limitata.

## S2 — scarto contro l'attività: «stabilità non determinata»

- Pendenza dello scarto MWO − luce bianca, sullo stesso modello di β₃, procedura M, intervallo nominale 97,5 %:
  **β₃^WL = −3,18 (SE 2,49), intervallo [−8,77, +2,40]**, n = 4694.
- Margine di equivalenza C = 0,5·|Δβ₂₀| = **0,530**, ricalcolato dal riconteggio sul sottoinsieme.
- L'intervallo contiene zero ma esce da [−C, +C], quindi lo stato è «stabilità non determinata». Non è
  «dipendente dall'attività» e non è «scarto contenuto».
- **Limite di precisione, prevedibile dal controllo del disegno:** per lo stato «scarto contenuto» la semiampiezza
  dovrebbe essere ≤ 0,53, cioè SE ≤ 0,24. Il SE osservato è circa dieci volte maggiore, in linea con il rapporto
  SE/|Δβ₂₀| ≈ 1,9 del controllo del disegno R4. Con questa precisione S2 non poteva permettere un verdetto.
- Per emisfero (descrittivo): N −1,70 [−9,89, +6,49] (n 2228); S −4,28 [−11,93, +3,37] (n 2466). Entrambi gli
  intervalli contengono zero.
- φ stimato 0,97 sul campione completo (0,75 nord, 0,98 sud): persistenza temporale alta dello scarto.

## S2 contro P1 (HMI), 2010-05 → 2012-12 (descrittivo)

- **153 coppie** stesso gruppo e stesso giorno. Scarto mediano MWO − P1: **+0,71°**.
- Pendenza contro l'attività: −6,0 [−18,9, +6,9]. L'intervallo contiene zero.
- Il fit ha parametri di varianza al bordo del dominio REML (φ = 0, κ = −0,98). Lo si riporta come limite della
  stima, non come risultato.

## S3 — accordo di Hale (descrittivo)

- Frazione di polarità di testa concorde con Hale, sulle celle con almeno 45 record: **0,79–0,90**. Esempi: E2N
  0,79, E5S 0,81, E8N 0,86, E6N 0,90.
- Celle piccole: E1N 1,00 su 6, E7S 0,78 su 18.
- Nessuna cella mostra un'inversione sistematica di segno.

## S4 — selezione e contaminazione (descrittivo)

- Gruppi esclusi per non isolamento, per terzile di attività crescente: **10,1 %, 12,2 %, 14,0 %**.
- Posizione media del giorno scelto: 1,13 → 1,09. |LCM| medio: 7,4° → 6,5°.
- d_WL nella sensibilità «tutti i record»:
  - isolati: mediana +0,88°, media +0,28° ± 0,48;
  - non isolati: mediana +0,20°, media −1,60° ± 1,42 (793 record).
  - La differenza fra le medie è dell'ordine di un errore combinato; per terzile, gli scarti non isolati hanno
    errori di 2,2–2,8°.
- Fonti DPD per epoca (`S1_DPD_SOURCES.csv`): Gyula prevale ovunque (44–92 %). In E8 SOHO pesa il 13 %, come previsto
  dal controllo di omogeneità.

## Limiti

- S1 è un controllo relativo fra epoche e non verifica le derive dentro un'epoca (§6).
- La validazione ha 19 fit di M non riusciti, conservati nei denominatori; nessuna riga invalida.
- La potenza della validazione per la rampa del 10–20 % è del 2,0–4,7 %. Anche con stabilità favorevole, un effetto
  di quella grandezza sarebbe stato quasi sempre «non deciso».
- Il selftest di `t3_mwo_estimate_recount.py` dà 14/15 con la patch applicata: il test riapplica la patch al file
  già patchato. È un difetto del test, non della stima sintetica né del riconteggio (entrambi superati); senza patch
  dava 15/15. Il file non è stato modificato.

## Prossimo passo

Revisione di Codex di questi esiti. Poi, se approvato, `--estimate` una sola volta: con questa regola produrrà β₃
**descrittivo** (intervallo nominale con avvertenza, nessun verdetto). Seguono il riconteggio della stima, il
rilascio e le figure.

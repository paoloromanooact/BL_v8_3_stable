# Protocollo P2c — Chiarimenti a P2b (nessuna regola cambiata)

Stato: **congelato il 2026-11-03** (commit), prima di qualunque esecuzione di P2 o P2b
sui dati veri. Non modifica le regole di P2b (SHA-256 `271935b8…`): ne rende
esplicite motivazioni, natura e implementazione, su richiesta della revisione
esterna. Informazioni già viste: `docs/SEEN_BEFORE_FREEZE_2026-11-03.md`.
Non avere eseguito P2 sui dati veri non significa non avere visto nulla di
rilevante: in particolare sono state viste parti della serie P1 parziale
(punti 4 e 5 dell'elenco), che contengono tilt, segni e D* del 2010–2013.

## 1. Il rischio, non un fatto

La lenta variazione dell'attività SILSO **non dimostra** che i residui di T3
e T5 siano autocorrelati tra rotazioni, né che gli intervalli di P2 siano
troppo stretti: è un rischio. P2b lo **verifica** (autocorrelazione dei
residui, §3) e ne **misura** l'effetto possibile su cataloghi sintetici (§4).

## 2. Lunghezze dei blocchi

L = 3, 6, 13 rotazioni corrispondono a circa un trimestre, un semestre e un
anno. L'anno è la scala della media mobile su 13 mesi con cui si descrive di
solito l'attività; 3 e 6 coprono correlazioni più brevi (evoluzione di
complessi di attività, ricomparse). Sono una scelta ragionata, non derivata
dai dati.

## 3. Natura della regola "deve reggere con tutti"

`verdict_p2b` richiede lo stesso verdetto con **tutte** le lunghezze: è un
criterio **più conservativo** di P2 da solo e di qualunque singola lunghezza.
Un verdetto "quenching supportato" sopravvive solo se non dipende dalla scelta
di L. Il prezzo è una potenza minore: un effetto vero ma debole può risultare
"non deciso (dipendenza temporale)".

## 4. Implementazione (già nel codice, `run_p2.py`)

- I blocchi sono definiti sui **numeri di CR**: un blocco prende tutte le
  osservazioni di quelle CR, quindi **i due emisferi della stessa CR restano
  insieme** (lo stesso vale per il bootstrap di P2).
- I **vuoti temporali sono conservati**: il blocco copre L numeri di CR
  consecutivi anche se alcune non hanno regioni nel campione; quelle
  posizioni restano vuote invece di essere "compattate".
- Il numero di blocchi per ricampionamento è ⌈N_span / L⌉, con N_span
  calcolato sui numeri di CR (vuoti inclusi).

## 5. Calibrazione prima dei verdetti

La calibrazione di P2b §4 (cataloghi sintetici, 100 per ciascun ρ ∈ {0; 0,5;
0,8}) si riporta con falsi positivi e copertura degli intervalli al 95% e al
97,5% per ogni schema di bootstrap, con l'errore Monte Carlo √[p(1−p)/n],
**prima** di interpretare qualunque verdetto di P2/P2b sui dati reali.

# Ripetibilità C e BQ-HMI: sviluppo del 27 novembre (sintetici)

Claude, 27 novembre 2026. **Solo sintetici**: nessun pixel osservato, nessun fit su risposte osservate, nessun
protocollo congelato. È sviluppo verificato, non ancora chiuso da Codex: le revisioni Codex citate sono nel
repository MWO (`reviews/`). Base: 1bc828a (correzioni C/BQ) e bf85716 (A1).

## C: runner, selftest e riconteggio indipendente

Codice: `scripts/sft_c_repeatability.py`, `scripts/sft_c_repeatability_selftest.py`, `scripts/sft_c_repeatability_recount.py`.

**Runner** (selftest **32/32**)
- Docstring: C_rot è il supporto potenziale conservativo dello schema.
- Rimappatura registrata per epoca (`remap0_*`, `remap1_*`, griglia − pixel sul supporto completo).
- Una pair_key senza componente è rifiutata.
- Griglia: bordo superiore arrotondato per eccesso, come dice il §4 (`grid_range`).
- Sensibilità a 0,03° sulle celle figlie di C_fin, senza nuova selezione. `children()` accetta solo il raffinamento
  esatto 2 × 2: niente tolleranza relativa, niente griglia troncata.
- Assemblaggio operativo (`selection`, `manifest`, `assemble`):
  - lettura separata dal calcolo (`read_error` / `technical_error`);
  - insieme esatto delle chiavi (pair_key, preparazione);
  - `metadata_eligible` rigoroso, selezione vuota senza crash;
  - terzili USFLUX con indice razionale esatto (28/27/27 sui metadati reali);
  - riepiloghi e bootstrap per totale, emisfero, classe di lag e terzile;
  - `run_valid` secondo la bozza §4bis.7.
- `--run` resta rifiutato.

**Riconteggio** (selftest **24/24**)
- Codice proprio, senza importare runner, `sft_local`, `sft_core` o `sft_observed_pilot`. Algoritmi diversi dove
  possibile: deposito con bincount, erosione con tabella delle somme, propagazione stadio per stadio per C_rot.
- 7 coppie sintetiche, ogni chiave delle tre preparazioni; SUMMARY completo (statistiche lineari, assiali e
  circolari) con scale per unità.
- 10 manomissioni rifiutate, compresi booleani usati come conteggi, valori non scalari e il controesempio Codex del
  secondo momento.
- Non copre ancora i prodotti di `assemble()`.

**Bozza** `docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md`, §4bis: scelte accolte, terzili decisi da Codex (i conteggi
dell'audit 28/26/28 restano conservati come provvisori), stati e ricevuta dell'assemblaggio.

Fallimenti conservati in `reviews/C_FOLLOWUP_20261127/`:
- regola di validità a 0,03° sbagliata per aliasing (24/25);
- tolleranze del riconteggio: 1e-12° troppo stretto, tolleranza angolare moltiplicata per 0, scala per colonna,
  scala per riga che mescola Mx e Mx²;
- un errore nel test R5.

## BQ-HMI: diagnostica e densità predittiva del blocco

- **`python/sharpbl/bq_diag.py`** (selftest `scripts/bq_diag_selftest.py` **12/12**)
  - R̂ split rank-normalizzato bulk e ripiegato (R̂ = massimo; NaN con stato esplicito se una componente non è
    valutabile).
  - ESS bulk e di coda.
  - Gate proposto: almeno 4 catene originali, R̂ ≤ 1,01, ESS ≥ 400.
  - Non ancora collegata al campionatore.
- **`python/sharpbl/bq_cvpred.py`** (selftest `scripts/bq_cvpred_selftest.py` **7/7**)
  - Densità predittiva del blocco L1/L2/L3 secondo la bozza §6ter, con la densità ripiegata a limite adattivo
    (T/S ≤ 1e-12).
  - A ψ fisso coincide con il valore analitico L1, con la seconda strada L2 e con l'enumerazione congiunta L3.
  - Lo stimatore diretto **degenera** al crescere del blocco: misure in `reviews/BQ_CVPRED_20261127/` e bozza
    §6ter.8. Restituisce `score_not_established` sotto i filtri provvisori (ESS dei pesi ≥ 100, MCSE ≤ 0,1).
  - Per blocchi HMI serve uno schema sequenziale, da specificare con Codex prima del codice.
- **Bozza** `docs/PROTOCOL_BQ_HMI_DRAFT.md`:
  - prior q principale SD 0,5 (già in 1bc828a);
  - §6ter: densità predittiva L2/L3, esito delle misure, proposta per i blocchi non stabiliti.

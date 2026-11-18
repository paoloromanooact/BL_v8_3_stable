# Emendamento A1 al protocollo T3 su MWO — pixel BLANK (bozza)

**BOZZA NON CONGELATA, 18 novembre 2026 (Claude). Da rivedere con Codex e congelare prima di qualsiasi misura del
catalogo lungo.** Protocollo di riferimento: `docs/PROTOCOL_T3_MWO.md` (SHA-256 `4408a0ee…`), §2 «Misura».

## Problema trovato durante l'implementazione

Il §2 prescrive il lettore della pipeline MWO congelata (`parse_fits_bytes`). Quel lettore applica BSCALE e BZERO ma
**non gestisce la keyword BLANK** (= −32768 negli header MWO): un pixel mancante diventa −32768·BSCALE, cioè −3276,8 G con
BSCALE 0,1 e −1638,4 G con BSCALE 0,05.
- Con μ ≥ 0,8, B_r = B/μ vale fino a −4096 G e −2048 G: nel primo caso supera il taglio di 4000 G solo per μ < 0,82, nel
  secondo mai. Questi pixel entrerebbero nella misura come campo negativo forte e sposterebbero il baricentro negativo.
- La pipeline del flusso polare se ne protegge con il taglio B_LOS > −1600 G; la misura dei tilt del pilota non ha un
  taglio equivalente.

**Controllo descrittivo** (60 file Fe I per anno, nel 1975, 1983, 1988, 1992, 2000 e 2011, solo valori dei pixel, nessun
tilt):
- tutti i file hanno pixel BLANK dentro il disco (r < 0,999), quasi sempre in una corona vicina al bordo: il quantile 1 %
  del raggio dei pixel BLANK ha mediana 0,97–0,99;
- fuori dal dominio delle finestre (μ ≥ 0,8, cioè r ≤ 0,6) in tutti gli anni controllati **tranne il 1975**, dove 2 file
  su 60 hanno in tutto 1018 pixel BLANK con r ≤ 0,6 (raggio minimo 0,40): sono buchi dentro il disco.

## Modifica

1. **Pixel BLANK esclusi.** Un pixel è BLANK se il valore letto dal lettore della pipeline è uguale, in float32, a
   float32(BLANK)·BSCALE + BZERO, calcolato con le stesse operazioni del lettore. I pixel BLANK prendono valore NaN prima
   della misura: la condizione `isfinite(B_r)` del §2 li esclude dai pixel utilizzabili. Il dominio μ della finestra non
   cambia, perché dipende solo dalla geometria.
2. **Finestre con troppi BLANK.** Se più del **5 %** dei pixel della finestra è BLANK, il tentativo fallisce con causa
   `window_blank` e la regola del primo giorno riuscito passa al candidato successivo.
3. **Registro.** Per ogni tentativo si salva il numero di pixel BLANK nella finestra.
4. **Pilota.** Il pilota congelato resta com'è. Controllo descrittivo già fatto (18 novembre, misura di
   `scripts/t3_mwo_catalogue.py` con questo emendamento sui 211 record valutabili del pilota): **nessun record ha pixel
   BLANK nella finestra**, nessuno cambia stato, e il tilt coincide con quello del pilota entro 3·10⁻¹⁴°. Il verdetto del
   pilota non è toccato.

Nessun'altra regola del protocollo cambia.

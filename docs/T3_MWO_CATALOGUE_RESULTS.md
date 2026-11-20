# T3 su MWO: misura del catalogo (consegna 1, senza tilt)

> **Rilievo di Codex del 20 novembre, successivo al riconteggio.** Questa corsa conserva un errore comune
> a runner e riconteggio: il raggruppamento per giorno usava il nome del file invece dell'istante UTC completo.
> Nei soli metadati sono discordanti 32 record isolati e 30 nell'insieme completo. I conteggi e la ricevuta
> sotto rimangono storici; non autorizzano a usare questa selezione per la validazione o la stima di T3.
> Occorre una corsa corretta in una destinazione nuova, con tilt ancora sigillati.
> [Diagnosi e correzione](T3_MWO_METADATA_AND_CALIBRATION_REVIEW.md).

Protocollo `docs/PROTOCOL_T3_MWO.md` (SHA-256 `4408a0ee…`) ed emendamento A1 (`bc88452b…`). Misura avviata il 19 novembre
alle 07:48 da `e4ccd30`, dopo la fine della validazione HMI (via di Codex). Una prima corsa (07:40) si è fermata alla
fine, prima di scrivere qualsiasi prodotto: le ore d'osservazione ISO miste, con e senza frazioni di secondo, non si
convertivano con un formato unico. La correzione ha un test dedicato e il log è conservato in
`results/T3_MWO_CATALOGUE_FAILED_RUNS/`.

Prodotti conservati in Git prima di ogni lettura (`f718114`, `results/T3_MWO_CATALOGUE/`). **`SEALED.csv.gz` non è stato
aperto**: si potrà leggere solo dopo la validazione della consegna 2.

## Riconteggio indipendente: 12/12, controllo completo

Ricevuta in `results/T3_MWO_CATALOGUE_RECOUNT/RECEIPT.json` (`partial: false`):
- 91 967 tentativi con lo stesso stato e lo stesso magnetogramma scelto;
- 11 170 record (isolati e tutti) uguali in giorno, magnetogramma, epoca, classe, emisfero, rango, isolamento, vicini e
  area DPD;
- CR, ciclo, ora e conteggio dei BLANK senza differenze; λ̄, sin|λ|, flusso e attività uguali entro 10⁻¹⁵;
- tilt, γ e segno di testa sigillati: confronto automatico entro 1,1·10⁻¹⁰°, valori non mostrati;
- nessun giorno al limite delle effemeridi e nessuna CR al limite.

## Campione

- **Tentativi:** 91 967 giorni candidati (gruppo × giorno con area ≥ 1 e |λ| ≤ 45°). Esiti:
  - finestra fuori dal dominio μ ≥ 0,8: 38 179;
  - nessun magnetogramma valido: 36 089;
  - misura riuscita: 13 065;
  - una sola polarità: 4610;
  - finestra con più del 5 % di BLANK (A1): 24.
- **Record:** isolati (analisi principale) 5229, tutti 5941.
- **Copertura del §2: informativo.** Record isolati per ciclo ed emisfero:

  | Ciclo | Nord | Sud |
  |---|---|---|
  | 21 | 595 | 657 |
  | 22 | 781 | 900 |
  | 23 | 838 | 937 |

  Soglia: ≥ 3000 in totale e ≥ 300 per ciclo ed emisfero. Code: ciclo 20 132 record, ciclo 24 389 record.
- **Epoche (record isolati, N/S):**

  | Epoca | Nord | Sud |
  |---|---|---|
  | E1 | 6 | 32 |
  | E2 | 382 | 312 |
  | E3 | 226 | 340 |
  | E4 | 182 | 190 |
  | E5 | 543 | 664 |
  | E6 | 61 | 75 |
  | E7 | 27 | 18 |
  | E8 | 1070 | 1101 |

  Non verificabili (< 50 per emisfero): E1 ed E7, con 83 record (1,6 %), sotto il limite del 20 %.
- **Risoluzione:** R1 nella grande maggioranza di ogni epoca tranne E1 (R3, 14″×17″). R2 compare in E4–E8 (15–129 record
  per epoca), R0 in E2–E3 (22 record).
- **Giorno scelto:** il primo candidato nel 91 % dei casi (4760). Due record hanno pixel BLANK nella finestra, sotto la
  soglia del 5 %.
- **Perdite** (gruppi con almeno un giorno ammissibile, giorno di |LCM| minimo): la quota di gruppi con un record cresce
  con l'attività, dal 24 % nel terzile basso al 32 % in quello alto. È atteso, perché le regioni grandi hanno più spesso le
  due polarità sopra 50 G. Va tenuto presente: T3 riguarda la popolazione delle regioni isolate e misurabili (§1).
- **Attività mancanti:** A_own (solo giorni Gyula/Debrecen) in 218 record; SILSO emisferico prima del 1992 in 2529
  record, come atteso.

## Prossimi passi

Consegna 2 (`scripts/t3_mwo_analysis.py`, `678ff2f`, selftest 25/25): revisione di Codex, poi, nell'ordine congelato:
controllo del disegno, validazione (76 000 unità), apertura del sigillo con S1–S4, stima.

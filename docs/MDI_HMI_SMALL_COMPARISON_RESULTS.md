# Piccolo confronto MDI–HMI: risultati

**2026-11-18. Descrittivo, non cieco ai metadati.** Revisione mirata di Codex recepita (scarti fra implementazioni, stati di esclusione, R0, intervalli di flusso); la verifica completa del trasporto A1 resta da fare. Protocollo `docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON.md`
(congelato in `6d6fd12`, SHA-256 `3713236f…`) con emendamento A1 (`c409666`, trasporto dei FITS e budget).
Selezione di Codex (`7a9898e`), ricostruita identica da Claude (`a0df545`). Download A1: 84/84 FITS, 6 168 960 byte,
169 richieste HTTP e 135 s nel budget A1 (tutti da jsoc1.stanford.edu dopo un redirect ammesso). Prodotto di
integrazione MDI (MTARP→MDATA) non verificato: resta ignoto, come consentito dal §7 del protocollo.

Due implementazioni indipendenti, conservate prima della lettura:
- `scripts/mdi_hmi_comparison_run.py` (adattatore e kernel di Codex), corsa valida `results/MDI_HMI_COMPARISON/run_9f80330/`;
- `scripts/mdi_hmi_comparison_recount.py` (Claude, codice separato), `results/MDI_HMI_COMPARISON/recount_d278db3/`.

Stessa valutabilità per tutte le 36 righe e stessi 14 confronti valutabili; scarti massimi 1,214·10⁻⁸ gradi sul tilt e
1,241·10⁻⁸ relativi sui dipoli (entro 1,3·10⁻⁸; arrotondamento float32 delle keyword nell'adattatore). Gli **stati di
esclusione** coincidono tranne uno: per la TARP 13670 il runner riporta il rifiuto dell'adattatore (codici bitmap 1 e 2
non documentati per SMARP), il riconteggio una maschera vuota (non controlla i codici; nessun pixel con il bit 32). Una prima corsa del runner (`run_a6edbae`) divideva per μ
anche il riferimento Br: errore trovato dal riconteggio prima della lettura, corsa superata e conservata.

## 1. R0 e disponibilità delle misure

R0 (funzione P1 invariata sui 12 record HMI): sull'unico record coincidente con P1 (HARP 191) il flusso è riprodotto
con scarto relativo 4,47·10⁻⁸ con le keyword dell'adattatore e 4,67·10⁻⁸ con quelle del riconteggio (precisione delle
keyword); la latitudine entro 4·10⁻⁷. Il record è unipolare: la riproduzione storica del **tilt** resta non verificata.
Nota tecnica: nel `R0.csv` del riconteggio la colonna `rel_phi` vale 0 per un errore di calcolo della colonna; lo scarto
si ricava da `p1_phi` e `hist_phi`.

Le misure disponibili sono molte meno delle 12 coppie selezionate, senza sostituzioni:

| Causa | HMI | MDI |
|---|---|---|
| Maschera della patch vuota (nessun pixel di appartenenza) | 4 (HARP 155, 219, 51, 178) | 6 |
| Una sola polarità sopra 100 G | 3 (HARP 234, 191, 107) | — |
| Bitmap con codici non documentati per SMARP (1 e 2), rifiutata dall'adattatore | — | 1 (TARP 13670) |

Valutabili: **A1 e A2 su 5 coppie, B su 4.** Nessun ramo è stato perso per il dominio μ o per pixel non finiti.
Vicino al minimo del 2010 molte HARP/TARP selezionate non contengono in quell'istante una regione bipolare misurabile;
la selezione non usava conteggi di pixel di appartenenza (non previsti dal protocollo).

## 2. Risultati per coppia

Tilt nella convenzione P1; d_ax = differenza assiale candidato − riferimento; d_γ = sign(λ_HMI)·d_ax (convenzione
di Joy); rapporti candidato/riferimento.

| Confronto | HARP (strato) | d_ax | d_γ | Φ cand/rif | D_bal cand/rif |
|---|---|---|---|---|---|
| A1: LOS ricostruito/μ vs Br | 223 (N centr.) | −0,06° | −0,06° | 0,90 | 0,90 |
| | 114 (S centr.) | −0,65° | +0,65° | 0,81 | 0,76 |
| | 85 (N lat.) | −0,38° | −0,38° | 0,81 | 0,81 |
| | 43 (S centr.) | +0,04° | −0,04° | 0,89 | 0,94 |
| | 67 (S lat.) | +1,39° | −1,39° | 0,72 | 0,67 |
| A2: LOS misurato/μ vs Br | 223 | +0,18° | +0,18° | 0,98 | 0,97 |
| | 114 | −0,42° | +0,42° | 0,81 | 0,78 |
| | 85 | 0,00° | 0,00° | 0,89 | 0,89 |
| | 43 | +0,45° | −0,45° | 0,89 | 1,41 |
| | 67 | +0,79° | −0,79° | 0,72 | 0,69 |
| B: MDI vs HMI, LOS/μ | 223 (N centr.) | +3,81° | +3,81° | 0,73 | 0,48 |
| | 114 (S centr.) | +0,19° | −0,19° | 1,41 | 1,45 |
| | 43 (S centr.) | +0,98° | −0,98° | 1,44 | 2,66 |
| | 67 (S lat.) | +3,31° | −3,31° | 1,27 | 1,04 |

Lo spostamento dei centroidi medi è ≤ 0,09° in A1/A2 e 0,07–0,56° in B. Polarità leading uguale in tutti i confronti.

## 3. Sintesi del protocollo (§5)

| Confronto | gruppo | n | mediana d_γ | media ± s/√n | min / max | mediana \|d_ax\| | segnalazione |
|---|---|---|---|---|---|---|---|
| A1 | tutti | 5 | −0,06° | −0,24° ± 0,33° | −1,39° / +0,65° | 0,38° | — |
| A2 | tutti | 5 | 0,00° | −0,13° ± 0,22° | −0,79° / +0,42° | 0,42° | — |
| B | tutti | 4 | −0,59° | −0,17° ± 1,48° | −3,31° / +3,81° | 2,15° | no |
| B | nord | 1 | +3,81° | — | — | 3,81° | **sì** (n = 1) |
| B | sud | 3 | −0,98° | −1,50° ± 0,94° | −3,31° / −0,19° | 0,98° | no |

**Segnalazione nel nord**, prodotta da una sola coppia (HARP 223 / TARP 13661, QUALITY MDI 0x200): come prevede il
protocollo, non distingue uno scarto sistematico da una fluttuazione. Nel caso, il dipolo MDI è metà di quello HMI
(0,48) e il centroide medio si sposta di 0,56°: differenze congiunte di risoluzione e segmentazione, non isolate.
**Copertura**: per B lo strato nord laterale è interamente mancante; secondo il §5 la copertura è incompleta e la
decisione sul catalogo descrittivo MDI resta **aperta**.

## 4. Lettura

- **Definizione del campo su HMI (A1, A2)**, sulle cinque coppie misurate: passare da Br a LOS/μ cambia il tilt di
  frazioni di grado (mediana di |d_ax| 0,4°, massimo 1,4°), ma riduce il flusso del 10–28 % in A1 e del 2–28 % in A2, e
  il dipolo bilanciato fino al 33 %, con l'eccezione di un D_bal più grande del 41 % (HARP 43, A2). In queste cinque
  coppie la definizione LOS/μ dà tilt vicini a Br; per flussi e dipoli no. Non è una stima per il catalogo.
- **Strumento (B)**: sulle 4 coppie valutabili la differenza di tilt MDI−HMI è 0,2–3,8° in modulo (mediana 2,15°,
  vicina ai 2,1° del confronto con BARD-MDI), mentre flussi (0,73–1,44) e dipoli (0,48–2,66) differiscono molto di più.
  La scala rilevante per T3 (circa 0,4°) non è risolvibile con questi numeri, come il protocollo prevedeva.
- **Limite principale**: 4 coppie B su 12, uno strato vuoto. Un nuovo campione dovrebbe richiedere, prima della
  selezione e con un nuovo protocollo, pixel di appartenenza su entrambi gli strumenti; questo non è un esito del
  confronto ma una lezione sulla selezione al minimo.

Nessun risultato sul quenching; T3 resta non deciso, T5 descrittivo.

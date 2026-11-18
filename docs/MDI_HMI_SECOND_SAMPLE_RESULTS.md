# Secondo campione MDI–HMI: risultati (e unione con il primo)

**2026-11-18. Descrittivo, non cieco** (regole scritte conoscendo il primo campione). Protocollo congelato
`docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE.md` (`bbd719c`, SHA-256 `b7860445…`, senza limite complessivo di tempo), che estende
`docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON.md` (`6d6fd12`) e l'emendamento A1.

- **Selezione** (`scripts/mdi_hmi_second_sample_select.py`): 20 coppie, 5 per strato, componenti del primo campione
  escluse, NPIX > 0 su entrambi; manifesto SHA-256 `e34b4598…`. **Ricostruzione indipendente**
  (`scripts/mdi_hmi_second_sample_check.py`): stesse 20 coppie nello stesso ordine.
- **Disponibilità**: 7 richieste, 140 segmenti su 140 online, 15 350 260 byte annunciati.
- **Download** (trasporto A1): 140 FITS su 140, 327 richieste HTTP in tutto (tetto 450), 15 350 400 byte, 362 s.
- **Due implementazioni** (runner sui kernel di Codex `run_be1b49e`, riconteggio di Claude `recount_be1b49e`), output
  conservati prima della lettura in `e329010`: stessa valutabilità su 60 righe, 49 confronti valutabili; tilt concordi
  entro 2·10⁻⁸ gradi (d_ax 1,71·10⁻⁸), flussi entro 1·10⁻⁸ relativi, dipolo bilanciato entro 1,12·10⁻⁸ relativi;
  **dipolo ordinario** entro 3,19·10⁻⁷ relativi (HARP 86, confronto A1; scarto assoluto 5,09·10⁻¹⁰ G, su un dipolo
  piccolo). Correzione dopo la revisione di Codex: la prima versione dichiarava 1,1·10⁻⁸ anche per il dipolo ordinario.
- **Provenienza**: il `META.json` di `recount_be1b49e` riporta per errore il protocollo del primo campione (`6d6fd12`); il
  riconteggio è stato eseguito per il secondo campione (protocollo `bbd719c`, manifesto `e34b4598…`). Lo script ora
  registra il protocollo passato; gli output conservati non vengono modificati.
- **R0**: la funzione P1 riproduce la misura propria su tutti i record HMI (differenza di flusso 0); **nessun record HMI
  coincide con un record storico di P1, quindi la riproduzione storica del tilt resta non verificata** (§4 del protocollo).

## 1. Disponibilità delle misure

Il filtro NPIX > 0 ha funzionato: confronto B valutabile su **16 coppie su 20** (4 su 12 nel primo campione), A1 su 16 e
A2 su 17. Perdite residue: una sola polarità sopra 100 G in 3–4 record per ramo; nessuna maschera vuota, nessun codice di
bitmap sconosciuto, nessuna perdita per dominio μ.

## 2. Sintesi (protocollo §5, convenzione di Joy d_γ = sign(λ_HMI)·d_ax)

| Confronto | Insieme | n | mediana d_γ | media ± s/√n | min / max | mediana \|d_ax\| | segnalazione (≥ 2,107°) |
|---|---|---|---|---|---|---|---|
| A1 (LOS ricostruito/μ vs Br) | secondo campione | 16 | −0,06° | −0,27° ± 0,18° | −2,23° / +0,92° | 0,30° | — |
| A2 (LOS misurato/μ vs Br) | secondo campione | 17 | −0,19° | −0,32° ± 0,17° | −2,03° / +0,87° | 0,25° | — |
| **B (MDI vs HMI)** | **secondo campione** | 16 | **−0,13°** | −0,95° ± 3,76° | −49,6° / +19,5° | 1,76° | **no** (N −0,91°, S +0,18°) |
| **B** | **unione dei due campioni** | 20 | **−0,21°** | −0,79° ± 3,00° | −49,6° / +19,5° | 1,76° | **no** (N −0,57°, S −0,11°) |

Coppie B valutabili per strato nell'unione: N centrale 6, S centrale 5, N laterale 4, S laterale 5.
Polarità di testa concorde in tutti i confronti valutabili. Rapporto dei flussi B (MDI/HMI) mediano 1,26 (0,04–1,51);
A1 0,85 e A2 0,82: le differenze di flusso e di dipolo restano molto più grandi di quelle di tilt.

**Casi estremi** (riportati, non esclusi: il protocollo non prevede esclusioni): HARP 201/TARP 13634 (d_ax +49,6°,
rapporto di flusso 0,04) e HARP 97/TARP 13533 (+19,5°) sono regioni deboli (circa 5·10²⁰ Mx in HMI) in cui MDI ha
**2–9 pixel** di una polarità sopra 100 G: con la risoluzione di MDI il tilt di queste regioni non è definito bene. Le
mediane non ne risentono; media ed s/√n sì.

## 3. Lettura secondo il protocollo

- Nessuna segnalazione nel secondo campione né nell'unione, e tutti e quattro gli strati hanno coppie B valutabili:
  secondo il §4 del protocollo congelato **il seguito proponibile è un protocollo per un catalogo descrittivo MDI** dei tilt
  del ciclo 23. La decisione finale è dell'utente.
- La segnalazione del primo campione (nord, una sola coppia, HARP 223, +3,81°) resta documentata: nell'unione la mediana
  nord è −0,57°, compatibile con una fluttuazione di una singola regione.
- Lezione per il catalogo: una soglia di flusso o di pixel per polarità in MDI va fissata in quel protocollo (le regioni
  deboli danno tilt MDI non definiti), prima di leggerne i tilt.
- **Limite per T3 invariato**: la scala rilevante è circa 0,4° e lo scarto in funzione dell'attività non è misurabile al
  minimo del 2010; nessun esito autorizza un T3 combinato MDI+HMI.

# Pilota MWO: risultati (protocollo congelato `74e6b582…`)

Protocollo: `docs/PROTOCOL_MWO_PILOT.md` (SHA-256 `74e6b58279c96a9179970aff0609ab078cbb5ef541b419e19b60c9aa84992cfe`,
congelato in `e48b140`, record `ac28492`). Corsa da `ac28492`; output conservati in Git prima della lettura (`edd5b7b`):
`results/MWO_PILOT/`. Riconteggio indipendente: `results/MWO_PILOT_RECOUNT/`. Non cieco (vedi protocollo).

## Esito

**Verdetto della regola congelata: variante MWO utilizzabile** (ricalcolato in modo indipendente dal riconteggio).

| Criterio (campione intero) | Soglia | Valore |
|---|---|---|
| Copertura | ≥ 150 su 267 abbinati, ≥ 50 per emisfero | 211 (N 113, S 98) |
| Accordo sulla polarità leading | ≥ 90 % | 95,7 % |
| Mediana d_γ | \|·\| < 2,107° | −0,69° |
| Mediana \|d_ax\| | ≤ 5° | 4,40° |

Denominatori: 534 candidati P1; 35 senza gruppo DPD, 232 senza magnetogramma MWO del giorno, 267 abbinati; tra questi
29 con finestra fuori dal dominio μ ≥ 0,8 e 27 senza entrambe le polarità sopra 50 G; 211 valutabili.

## Descrittivo (non entra nel verdetto)

| Gruppo | n | mediana d_γ | media d_γ (s/√n) | mediana \|d_ax\| | leading |
|---|---|---|---|---|---|
| tutti | 211 | −0,69° | −1,53° (1,19°) | 4,40° | 95,7 % |
| N | 113 | −1,25° | −1,24° (1,86°) | 5,16° | 95,6 % |
| S | 98 | −0,35° | −1,87° (1,42°) | 4,26° | 95,9 % |
| terzili di flusso P1 2–3 | 141 | −0,54° | −1,05° (1,10°) | 4,33° | 96,5 % |

- 4,40° è la mediana della differenza assiale assoluta \|d_ax\| (5,16° nel solo Nord, sopra la soglia di 5° che però
  si applica al campione intero). Il confronto con la mediana MDI–HMI (2,15°) riguarda campioni diversi e non quantifica,
  da solo, il rumore aggiuntivo di MWO.
- Mediana e media di d_γ compatibili con zero non escludono una distorsione. Possono restare scarti che dipendono
  dall'attività, dall'emisfero o dall'epoca strumentale. Sono i controlli ancora necessari prima di interpretare la
  pendenza di T3.
- Il flusso MWO nella finestra è circa il 16 % del flusso P1 (mediana del rapporto 0,16). È un risultato osservato: il
  pilota non ha isolato quanto dipenda da risoluzione, soglia di 50 G, finestra ±6°/±8° o risposta strumentale. Il
  pilota non usa il flusso come criterio.
- I terzili superiori di flusso P1 non cambiano in modo rilevante il quadro del campione intero.

## Riconteggio indipendente

**Prima ricevuta** (`results/MWO_PILOT_RECOUNT/RECEIPT.json`, conservata invariata in `75e6098`): 5 voci su 6 OK. La rimisura
dai FITS con geometria propria fallisce per il flusso: scarto relativo da −2,6e-8 a −8,6e-9 (mediana −1,7e-8) contro la
tolleranza di 1e-9 fissata prima della corsa. Su 211 record il tilt rientrava (6,9e-7° contro 1e-6°) e la polarità
leading coincideva sempre.

**Diagnosi successiva alla corsa** (Codex, 18 novembre; `results/MWO_PILOT_FLUX_DIAGNOSIS/`): la pipeline MWO congelata
converte gli interi del FITS (BITPIX 16) in float32 prima di applicare BSCALE = 0,1, mentre il riconteggio applicava la
scala in float64. La prima versione di questo rapporto attribuiva lo scarto alla geometria: era sbagliato.

**Seconda ricevuta** (`results/MWO_PILOT_RECOUNT_R2/RECEIPT.json`): il lettore indipendente è stato allineato alla
convenzione numerica della pipeline (opzione `--pipeline-precision` di `scripts/mwo_pilot_recount.py`, con un nuovo
selftest su un FITS int16 con BSCALE 0,1). Le tolleranze non sono cambiate. Risultato 6 voci su 6 OK: flusso entro
3,3e-16 relativo, tilt entro 1,8e-12°, 0 discordanze sulla leading. Candidati, abbinamenti, cause, d_ax, d_γ, tabella
riassuntiva e verdetto sono ricostruiti senza discordanze.

## Prossimi passi (da decidere)

Il via a T3 su MWO 1974–2012 (variante §8b di `docs/PROTOCOL_T3_DPD_DRAFT.md`) richiede un protocollo proprio, rivisto da
Codex e congelato prima di qualsiasi calcolo dei tilt sul periodo lungo. Secondo la revisione di Codex, il pilota
sostiene la costruzione del catalogo magnetico MWO. Prima di interpretare la pendenza, quel protocollo deve verificare la
stabilità fra epoche strumentali e gli scarti in funzione dell'attività (e dell'emisfero).

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

- La mediana di \|d_ax\| (4,4°) è circa il doppio di quella MDI–HMI (2,15°) e vicina alla soglia di 5°; nel solo Nord supera
  5° (5,16°). La variante è utilizzabile con una dispersione per regione maggiore di quella di MDI: per T3 conta come
  rumore di misura in più, non come distorsione (mediana e media di d_γ compatibili con zero entro circa 1,3 s/√n).
- Il flusso MWO nella finestra è circa il 16 % del flusso P1 (mediana del rapporto 0,16). È atteso per via della soglia di 50 G
  sui magnetogrammi MWO a bassa risoluzione e della finestra ±6°/±8°. Il pilota non usa il flusso come criterio.
- Il taglio di flusso non serve: i terzili superiori non migliorano in modo rilevante il campione intero.

## Riconteggio indipendente

Passano cinque voci su sei: hash dei prodotti; ricostruzione indipendente di candidati, abbinamenti e cause (534 / 267,
0 discordanze); d_ax e d_γ; tabella riassuntiva (scarto massimo 1,1e-16); verdetto.

**Una voce fallisce rispetto alla tolleranza fissata prima della corsa**: la rimisura dai FITS con geometria propria. Su
211 record il tilt rientra (scarto massimo 6,9e-7°, tolleranza 1e-6°) e la polarità leading coincide sempre, ma il flusso
supera la tolleranza relativa di 1e-9. Lo scarto relativo è sistematico: mediana −1,7e-8, minimo −2,6e-8, massimo −8,6e-9,
deviazione standard 2,3e-9, nessuna correlazione con il numero di pixel. Questo ordine di grandezza è la precisione float32,
quindi l'origine probabile è un arrotondamento in singola precisione nella geometria della pipeline MWO congelata, che il
runner usa e il riconteggio no. Non è un errore di formula. L'effetto sul pilota è nullo: il flusso non entra nel
verdetto, il tilt è riprodotto entro 1e-6°. La tolleranza non è stata cambiata dopo la corsa; la voce resta FALLITA come
registrata.

## Prossimi passi (da decidere)

Il via a T3 su MWO 1974–2012 (variante §8b di `docs/PROTOCOL_T3_DPD_DRAFT.md`) richiede un protocollo proprio, rivisto da
Codex e congelato prima di qualsiasi calcolo dei tilt sul periodo lungo.

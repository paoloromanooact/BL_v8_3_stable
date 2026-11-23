# Pilota MDI — revisione del codice delle fasi 1–3

23 novembre 2026, Codex. Codice esaminato fino a b5913f6; protocollo congelato d789e15.

Il modulo di misura e l'impostazione del campionamento sono accettabili. Non do ancora il via alla misura L1:
i riconteggi non coprono tutti gli input e gli output che certificano e c'è un errore di longitudine nelle finestre
di quiete. Non serve modificare le soglie o allargare il pilota. Nessuna selezione o misura MDI reale eseguita.

## 1. Selezione: confrontare le colonne effettivamente utilizzate

`mdi_pilot_select_recount.check` confronta le chiavi e i ranghi del SAMPLE, ma non le sue coordinate, t_DPD,
LCM, area, A_main, etichette e tutti i pesi. POPULATION non sostituisce questo controllo: il misuratore legge SAMPLE.
Il controllo delle probabilità usa inoltre una merge interna che può perdere righe, e non controlla w2.

Sonda sintetica: la base passa; cambiando singolarmente lat, lon, t_dpd, A_main o w2 di una riga L2 e aggiornando
gli hash del prodotto, il riconteggio continua a passare. Gli hash garantiscono integrità rispetto al manifesto,
non correttezza del calcolo: per questo queste mutazioni devono fallire anche con hash aggiornati.

Confrontare SAMPLE completo con la selezione ricostruita, compresi tutti i metadati portati dalla popolazione,
pi1/pi2/w1/w2 e valori mancanti; confrontare anche t_DPD/LCM della popolazione, etichette e disavanzi di CELLS.
Richiedere unicità delle chiavi e copertura esatta dei join. Provare le cinque mutazioni sopra e una cella/etichetta
alterata, senza affidarsi al solo hash.

## 2. Quiete: usare il centro fissato, non la mediana delle longitudini

In `mdi_pilot_measure_l1.quiet`, `l_q = median(ex['lon'])` è errato al taglio 0/360: 359 e 1 danno 180.
Usare direttamente la longitudine fisica fissata da CT_q, `(-ct_q) % 360`, per maschera ed esclusione DPD.
Una sonda con due finestre interamente finite, MAD rispettivamente 14,826 e 7,413 G, restituisce 7,413 invece
di 11,1195 G perché scarta quella a cavallo di zero come `finite_below_50pct`.

Il riquadro allargato a semiestensioni 12°/16° è coerente con la finestra originaria 6°/8° più l'allargamento
6°/8° del testo. Non richiede un nuovo taglio. Provare centro a zero, contaminante sui bordi e nessun contaminante;
conservare per ciascun lato lo stato e il valore, da ricontare senza interpretare la MAD come rumore strumentale.

## 3. Riconteggio L1 incompleto: N e quiete sono obbligatori

Il comando reale emette oggi `partial = false` pur non ricostruendo N, N_ephemeris e le finestre di quiete.
`compare` accetta perfino una riga inventata `{status: N_ambiguous, N: 9999, N_ephemeris: 1}` senza data o pixel.
Ricostruire dai metadati della selezione N, CT_g, t_cm e il controllo con effemeridi proprio; confrontare stati
anche per mappe mancanti/rotazione ambigua. La coerenza algebrica fra N e CT_g non verifica l'assegnazione temporale.
Ricontare quiete (tempo, centri, contaminanti DPD, frazione finita, MAD e media dei lati validi).

Completare il confronto delle quantità già esportate: centroidi, lat_bar, aree per polarità, n_win/n_missing_win,
separazione in passi, mappe e relativi metadati, oltre a flussi, tilt, conteggi e leading già controllati.
Confrontare sempre lo stato globale con quello principale ricostruito. Ricevuta completa solo dopo questi controlli;
in loro assenza il percorso è parziale e non può superare il cancello del protocollo.

## 4. Verificare i prodotti a monte prima di usarli

L1 verifica che la ricevuta sia legata a selection META, ma non ricalcola gli hash di SAMPLE/POPULATION/CELLS
prima di leggerli: una modifica di SAMPLE dopo il riconteggio lascia META e ricevuta invariati. Richiedere
insieme esatto dei prodotti, hash effettivi e prerequisiti conservati prima della lettura. Nei riconteggi verificare
il protocollo congelato e gli input pertinenti, non soltanto il valore dichiarato nel META. Il riconteggio L1 deve
anche verificare gli SHA reali delle mappe usate contro l'audit, con lettore proprio.

Prove minime: SAMPLE cambiato dopo la ricevuta, protocollo discordante, mappa modificata, ricevuta mancante/parziale.
La validazione del contenuto e la verifica della provenienza sono controlli distinti.

## 5. Scala temporale degli header

La normalizzazione dei secondi = 60 come intervallo va bene. `parse_jsoc_time` perde però il suffisso TAI e passa
il risultato come UTC alla conversione: il diagnostico arriva a 2,667°, mentre la verifica con TAI convertito a UTC
dava circa 2,663°. Conservare e convertire esplicitamente la scala (per esempio con astropy Time), senza cambiare
la soglia congelata di 3°. Questo riguarda il controllo temporale; non dimostra uno spostamento dei tilt.

## Verifica e prossimo passo

- Rieseguiti: modulo 12/12, selettore 11/11, riconteggio selezione 4/4, misura L1 15/15, riconteggio L1 5/5.
- Sonda indipendente `scripts/mdi_pilot_phase123_review_probe.py`: base sintetica accettata; cinque mutazioni
  del SAMPLE erroneamente accettate, N ambiguo inventato accettato, errore della quiete riprodotto.
- Nessuna rete, pixel MDI reali o tilt MDI letti; le mappe dei test sono sintetiche. MWO rimane invariato.

Claude corregge questi punti e aggiunge le regressioni; poi revisione mirata. Dopo la chiusura: selezione,
conservazione e riconteggio; quindi misura L1, conservazione e riconteggio completo. Nessun via alle fasi di rete.

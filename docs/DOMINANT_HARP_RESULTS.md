# Controllo delle HARP dominanti — risultati (descrittivi)

Stato: **esecuzione unica del controllo completo, 2026-11-13 alle 09:13–09:16, commit `1a22e09`
(albero pulito)**, secondo il piano registrato `docs/DOMINANT_HARP_PLAN.md` (`f805c5a`, SHA-256
`e7767aea…`). Controllo descrittivo della misura: non cambia il catalogo, non produce verdetti, non
interviene sui test P2/P2f. Output in `results/DOMINANT/` (`DOMINANT_HARP_SELECTION.csv`,
`DOMINANT_HARP_CHECKS.csv`, `DOMINANT_HARP_SUMMARY.csv`, `DOMINANT_HARP_VARIANTS.csv`,
`DOMINANT_HARP_FITS_SHA256.csv`), schede in `figures/DOMINANT/` (120 PNG), stampa in
`logs/dominant_harp_check.log` (fuori da Git).

**Prova tecnica distinta.** Prima del controllo completo una prova tecnica su 2 HARP (393 e 5249,
gruppo 24N) è stata eseguita su `a41c451` con albero non pulito e con output fuori dal repository,
conservati in `results/DOMINANT_TRIAL_2HARP/` con la loro provenienza. Durante la prova è stata
corretta la figura (longitudine dei centroidi ridotta modulo 360° rispetto alla mappa); la
correzione riguarda solo le schede, non i valori. I risultati sotto vengono solo dal controllo
completo.

## 1. Campione

- Base: 4189 record primari validi v8.4 dei cicli 24–25 (nessun record di altri cicli escluso).
- Per ciclo × emisfero: 20 dominanti per |S_BL| e 10 controlli estratti (seme 20261111); 120 HARP,
  di cui 101 appartengono anche al campione S di P2.
- Le 20 dominanti portano il 21,5 % (24N), 29,9 % (24S), 29,1 % (25N) e 35,1 % (25S) di Σ|S_BL| del
  gruppo (denominatore: somma dei valori assoluti su tutta la base del gruppo).
- Riproduzione: per tutte le 120 HARP i valori P1 sono riprodotti dai FITS numericamente entro la
  precisione macchina (scarto relativo massimo su S_BL 2·10⁻¹⁶; centroidi con pesi |Br| con scarto
  nullo rispetto a `measure_v84`).

## 2. Livello 1 — segnalazioni (proprietà da esaminare, non errori)

Numero di HARP con ciascun flag (dominanti su 20 / controlli su 10; le due numerosità sono diverse,
quindi si confrontano le frazioni n/20 e n/10, senza alcun test inferenziale):

| Flag | 24N | 24S | 25N | 25S |
|---|---|---|---|---|
| M1 possibile troncamento (maschera sul bordo) | 3 / 1 | 4 / 0 | 9 / 3 | 5 / 2 |
| M2 flusso fuori maschera > 20 % | 5 / 6 | 7 / 5 | 6 / 5 | 9 / 6 |
| M3 multipolare | 7 / 5 | 8 / 2 | 9 / 4 | 5 / 5 |
| P2 leading instabile tra varianti | 1 / 1 | 0 / 0 | 0 / 1 | 0 / 1 |
| C1 centroidi sensibili alla pesatura | 1 / 1 | 5 / 0 | 1 / 0 | 4 / 2 |
| C2 centroidi sensibili alla soglia | 0 / 1 | 0 / 0 | 0 / 0 | 0 / 1 |
| P1 sbilanciata (descrittivo) | 1 / 4 | 0 / 3 | 0 / 4 | 0 / 4 |
| P3 anti-Hale o non definito (descrittivo) | 3 / 2 | 0 / 3 | 0 / 1 | 0 / 4 |
| N1 più regioni NOAA (descrittivo) | 9 / 0 | 16 / 1 | 15 / 1 | 18 / 3 |
| R1 lontano dal meridiano (descrittivo) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| R2 instabile tra record (descrittivo) | 2 / 8 | 4 / 6 | 4 / 6 | 7 / 5 |

- R2 è «non disponibile» per 1 HARP (senza record di controllo valido); nessun caso «non valutabile».
- Quota di Σ|S_BL| del gruppo portata da HARP esaminate con almeno una segnalazione di misura (M1–M3,
  P2, C1–C2): 13,6 % (24N), 22,2 % (24S), 22,8 % (25N), **29,6 % (25S)**. Per la regola del piano,
  il gruppo **25S è una priorità di approfondimento** (> 25 %): una priorità operativa, non una
  percentuale di errore nella serie; non dimostra che la somma cambi.
- Le segnalazioni più frequenti tra le dominanti sono N1 (più regioni NOAA nella HARP), M2 e M3, cioè
  regioni grandi e complesse: sono segnalazioni che da sole non dimostrano errori; che riflettano
  solo complessità fisica non è stabilito prima dell'esame visivo.

## 3. Livello 2 — sensibilità misurate (differenze ricalcolate)

Per ciascuna variante, Δ = Σ (S_BL,variante − S_BL,P1) sulle HARP esaminate con confronto possibile,
rispetto a Σ|S_BL| e alla somma netta dell'intero gruppo. Vale solo per le HARP esaminate.

| Gruppo | Variante | HARP confrontabili / 30 | Quota di Σ\|S_BL\| coperta | Δ / Σ\|S_BL\| | Δ / somma netta |
|---|---|---|---|---|---|
| 24N | soglia 300 G | 27 | 21,9 % | −3,3 % | −7,1 % |
| 24N | bitmap ≥ 1 | 30 | 21,9 % | −1,0 % | −2,1 % |
| 24N | pesi uniformi | 30 | 21,9 % | −1,3 % | −2,8 % |
| 24S | soglia 300 G | 27 | 30,5 % | +4,6 % | −9,5 % |
| 24S | bitmap ≥ 1 | 30 | 30,5 % | −3,4 % | +6,9 % |
| 24S | pesi uniformi | 30 | 30,5 % | −0,4 % | +0,8 % |
| 25N | soglia 300 G | 29 | 29,7 % | −7,1 % | −14,2 % |
| 25N | bitmap ≥ 1 | 30 | 29,7 % | +1,5 % | +3,0 % |
| 25N | pesi uniformi | 30 | 29,7 % | +0,9 % | +1,9 % |
| 25S | soglia 300 G | 28 | 35,4 % | +6,8 % | −12,0 % |
| 25S | bitmap ≥ 1 | 30 | 35,4 % | +0,1 % | −0,2 % |
| 25S | pesi uniformi | 30 | 35,4 % | +1,7 % | −3,0 % |

- Nei gruppi sud il segno di S_BL è negativo, quindi una variazione positiva rispetto a Σ|S_BL|
  riduce il modulo della somma netta.
- **Compensazioni tra HARP.** La differenza netta Δ non misura l'instabilità delle singole HARP:
  contributi di segno opposto si compensano. Aggregazione descrittiva aggiunta dopo la revisione
  esterna (post hoc, non un criterio del piano): somma dei moduli delle differenze per HARP rispetto
  a Σ|S_BL| del gruppo, contro la differenza netta.

  | Gruppo | Soglia 300 G: netto / somma dei moduli | Bitmap ≥ 1: netto / somma dei moduli | Pesi uniformi: netto / somma dei moduli |
  |---|---|---|---|
  | 24N | −3,3 % / 6,1 % | −1,0 % / 3,4 % | −1,3 % / 3,0 % |
  | 24S | +4,6 % / 10,2 % | −3,4 % / 5,5 % | −0,4 % / 2,6 % |
  | 25N | −7,1 % / 9,7 % | +1,5 % / 3,4 % | +0,9 % / 2,8 % |
  | 25S | +6,8 % / 9,7 % | **+0,09 % / 13,1 %** | +1,7 % / 5,7 % |

  In 25S con bitmap ≥ 1 il netto è quasi nullo mentre la somma dei moduli è il 13,1 %: la somma
  cambia poco perché le variazioni si compensano, non perché le singole misure siano stabili. I
  contributi maggiori, di segno opposto, vengono dalle HARP 11786 (+3,64 % di Σ|S_BL|) e 11662
  (−2,89 %), poi 12094 (−1,15 %), 11887 (+1,14 %) e 11930 (+0,92 %), tutte dominanti e in S: sono
  casi influenti, non errori accertati.
- **Soglia 300 G**: in 9 HARP su 120 il confronto è impossibile (una polarità senza pixel sopra
  300 G) e resta fuori dalla somma. La soglia più alta riduce il flusso contato (variazione relativa
  per HARP: mediana −32,5 % su S_BL e −30,2 % su Φ nelle 111 confrontabili), coerente con un ruolo
  importante del flusso, che è una scelta del protocollo P1; cambiano però anche i centroidi, e le
  cause non sono separate per HARP. Le Δ a 300 G (fino al 7,1 % di Σ|S_BL| e al 14,2 % della somma
  netta) non indicano un errore.
- **Bitmap ≥ 1 e pesi uniformi**: Δ entro il 3,4 % di Σ|S_BL| e il 6,9 % della somma netta in tutti i
  gruppi; la HARP singola più influente sposta Σ|S_BL| del gruppo al massimo del 3,6 % (bitmap ≥ 1,
  25S).
- Le sensibilità non certificano le HARP non esaminate (circa il 65–78 % di Σ|S_BL| di ogni gruppo),
  né le somme per CR, l'efficienza, T3 o la scala assoluta della sorgente rispetto a BARD.

## 4. Livello 3 — errori confermati

**Nessun errore confermato finora dai controlli automatici; verifica visiva non eseguita.** Un errore
richiede un'evidenza specifica per HARP (per esempio una maschera che include campo di un'altra
regione visibile nella scheda, o polarità invertite rispetto alla mappa). Le schede sono in
`figures/DOMINANT/`; l'esame visivo, documentato HARP per HARP con il motivo, è in
`docs/DOMINANT_HARP_VISUAL_25S.md` per il gruppo 25S (esame fatto il 2026-11-13 da un solo
lettore): **nessun errore confermato** nelle 30 schede; 10 dominanti su 20 sono complessi
multiregione (classe B) e 5 hanno un centroide tra regioni distinte (classe C: 11487, 9680, 11907,
11727, 12589); 5 controlli su 10 sono regioni quasi unipolari o in decadimento (classe D) con
contributo trascurabile. Le classi B–D non sono errori: derivano dalla definizione «una misura per
HARP» di P1 e dal criterio di validità (20 pixel per polarità), e un loro trattamento richiederebbe
un piano proprio.

## 5. Che cosa si può dire

- Le regioni dominanti sono soprattutto HARP grandi e complesse (più regioni NOAA, flusso fuori
  maschera, multipolarità): segnalazioni che da sole non dimostrano errori.
- Con le varianti di maschera e di pesatura dei centroidi, le **somme firmate** dei gruppi cambiano
  poco nelle HARP esaminate (≤ 3,4 % di Σ|S_BL|), ma per compensazione: le variazioni per HARP
  sommate in modulo arrivano al 13,1 % (25S, bitmap ≥ 1). La soglia su |Br| cambia di più, con un
  ruolo importante del flusso contato.
- Il gruppo 25S supera la soglia di priorità del 25 %: è il primo candidato per un esame visivo
  delle schede e, solo con errori confermati o sensibilità rilevanti, per un piano di emendamento a
  P1. Nessun emendamento scatta da questi flag.

## 6. Revisione esterna (2026-11-13, ZIP `9344e14`, SHA-256 `0c307451…`)

101 controlli superati con uno script indipendente (campione, ordinamenti ed estrazioni ricostruiti
dal catalogo, flag ricalcolati dalle quantità salvate, provenienza, piano e codice immutati, SHA-256 dei
240 FITS coincidenti); nessun esame visivo e nessuna riesecuzione di `measure_v84`. Richieste recepite
senza cambiare output: compensazioni tra HARP esplicitate (§3), «segnalazioni che da sole non
dimostrano errori», «nessun errore confermato finora dai controlli automatici», riproduzione «entro la
precisione macchina», frazioni n/20 e n/10, soglia del 25 % come priorità operativa, nessuna
attribuzione esclusiva al flusso per la soglia 300 G, nessuna convalida del resto della serie.
Passo successivo consigliato dal revisore: esame visivo delle 30 schede di 25S, documentato per HARP.

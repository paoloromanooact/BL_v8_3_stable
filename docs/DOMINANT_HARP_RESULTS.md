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
- Riproduzione: per tutte le 120 HARP i valori P1 sono riprodotti dai FITS (scarto relativo massimo
  su S_BL 2·10⁻¹⁶; centroidi con pesi |Br| identici a `measure_v84`).

## 2. Livello 1 — segnalazioni (proprietà da esaminare, non errori)

Numero di HARP con ciascun flag (dominanti su 20 / controlli su 10):

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
  il gruppo **25S è una priorità di approfondimento** (> 25 %); questo non dimostra che la somma
  cambi.
- Le segnalazioni più frequenti tra le dominanti sono N1 (più regioni NOAA nella HARP), M2 e M3, cioè
  regioni grandi e complesse: sono proprietà attese delle regioni più intense, non errori.

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
- **Soglia 300 G**: in 9 HARP su 120 il confronto è impossibile (una polarità senza pixel sopra
  300 G) e resta fuori dalla somma. La soglia più alta riduce il flusso contato (variazione relativa
  di S_BL per HARP con mediana −32 %), quindi questa variante misura soprattutto la dipendenza di Φ
  dalla soglia, che è una scelta del protocollo P1; le sue Δ (fino al 7,1 % di Σ|S_BL| e al 14,2 %
  della somma netta) non indicano un errore.
- **Bitmap ≥ 1 e pesi uniformi**: Δ entro il 3,4 % di Σ|S_BL| e il 6,9 % della somma netta in tutti i
  gruppi; la HARP singola più influente sposta Σ|S_BL| del gruppo al massimo del 3,6 % (bitmap ≥ 1,
  25S).
- Le sensibilità non certificano le HARP non esaminate (circa il 65–78 % di Σ|S_BL| di ogni gruppo).

## 4. Livello 3 — errori confermati

**Nessun errore confermato.** Un errore richiede un'evidenza specifica per HARP (per esempio una
maschera che include campo di un'altra regione visibile nella scheda, o polarità invertite rispetto
alla mappa); l'esame visivo delle 120 schede non è stato ancora fatto. Le schede sono in
`figures/DOMINANT/`; l'esame, se si fa, va documentato HARP per HARP con il motivo.

## 5. Che cosa si può dire

- Le regioni dominanti sono soprattutto HARP grandi e complesse (più regioni NOAA, flusso fuori
  maschera, multipolarità): sono segnalazioni attese, non errori.
- Con le varianti di maschera e di pesatura dei centroidi, le somme dei gruppi cambiano poco nelle
  HARP esaminate (≤ 3,4 % di Σ|S_BL|); la soglia su |Br| cambia di più, come atteso perché cambia il
  flusso contato.
- Il gruppo 25S supera la soglia di priorità del 25 %: è il primo candidato per un esame visivo
  delle schede e, solo con errori confermati o sensibilità rilevanti, per un piano di emendamento a
  P1. Nessun emendamento scatta da questi flag.

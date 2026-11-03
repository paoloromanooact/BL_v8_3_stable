# Protocollo P3c — Convenzione di `Tilt_rel` e dipendenze dei confronti (emendamento di P3)

Stato: **congelato il 2026-11-03** (commit), prima di qualunque abbinamento
tra le nostre regioni e BARD. Modifica **solo** la riga "Segno di `Tilt_rel`"
di P3 §2 e la regola di sospensione di P3 §2; P3 (SHA-256 `37e10421…`) e P3b
restano validi.

## 0. Perché, e cosa è già stato visto (non cieco)

La prima esecuzione di `run_p3.py` (2026-11-03, circa 12:50) si è fermata
prima di qualunque abbinamento: il codice richiedeva |Tilt_rel + asin(sin α)|
< 0,01° (tolleranza **non** scritta in P3) e sospendeva **tutti** i confronti
per una convenzione indeterminata, mentre P3 sospende solo quelli che ne
dipendono. Visto prima di scrivere questo emendamento, solo dentro BARD:
- `Tilt_rel` coincide con la formula piana di §1 (differenza massima 0,0°,
  file HMI 1457 regioni e MDI dal 2010-05, 90 regioni);
- rispetto al nostro asin(sin α) sferico ha segno opposto nel 100% dei casi e
  |Tilt_rel + asin(sin α)| ha percentili 50/90/99/max = 0,003°/0,019°/0,073°/
  0,196° (HMI) e 0,007°/0,049°/0,147°/0,185° (MDI);
- le frazioni con la tolleranza di 0,01° (79,6% HMI, 61,1% MDI).

## 1. Verifica A — `Tilt_rel` riproduce la formula piana

La descrizione dell'algoritmo nel dataset non scrive la formula del tilt; la
formula seguente è stata **individuata** confrontandola con il catalogo:

Tilt_rel = atan2(λ_lead − λ_follow, |wrap(L_lead − L_follow)| · cos λ_BMR),

in gradi, con leading e following dalla colonna `LeadingPolarity`, λ e L
latitudini e longitudini dei centroidi di polarità, λ_BMR = `BMRLatitude`,
wrap in [−180°, 180°). **Esito "formula piana confermata"** se
|Tilt_rel − formula| ≤ 0,01° in almeno il 99% delle regioni; altrimenti "non
confermata". Si riporta; nessun confronto ne dipende.

## 2. Verifica B — compatibilità tra formula piana e nostra formula sferica

Controllo di **compatibilità, non cieco** (la soglia di 1° è stata scelta dopo
aver visto differenze fino a 0,2°); **non** è una validazione indipendente.
- **Tilt non nullo:** |asin(sin α)| ≥ 0,5°, con α dal nostro ricalcolo sui
  centroidi BARD.
- Esito "compatibile" se: (i) tra i tilt non nulli, segno(Tilt_rel) =
  −segno(asin(sin α)) in almeno il 99%; e (ii) |Tilt_rel + asin(sin α)| ≤ 1°
  in almeno il 99% di tutte le regioni. Altrimenti "non compatibile".
- Si riportano anche i percentili 50/90/99/max di |Tilt_rel + asin(sin α)|
  (confronto descrittivo tra le due formule).

## 3. Dipendenze dei confronti (sostituisce la regola di sospensione di P3 §2)

| Verifica | Se l'esito è indeterminato / negativo |
|---|---|
| Direzione delle longitudini | sospesi **tutti** i confronti di quel livello (HMI o MDI) |
| Riferimento delle longitudini | sospesi **tutti** i confronti di quel livello |
| Significato di `Hale` | sospeso **solo** il confronto "Hale pubblicato" |
| Verifica A (formula piana) | **nessun** confronto sospeso: si riporta |
| Verifica B (compatibilità) | **nessun** confronto sospeso: si riporta |

Il tilt, la polarità leading, la separazione e l'Hale ricalcolato si
ricalcolano dai centroidi (P3 §5) e non dipendono da `Tilt_rel`. Un livello
sospeso non sospende l'altro.

## 4. Verifica dell'implementazione

Un test automatico costruisce un catalogo in cui `Tilt_rel` è sbagliato
(verifiche A e B negative) e controlla che i confronti ricalcolati dai
centroidi restino attivi; un altro controlla che un `Hale` incoerente
sospenda solo "Hale pubblicato".

# Risultati esplorativi per l'articolo

**Esplorativo, serie già osservata.** Piano: `docs/EXPLORATORY_PLAN.md`.
Tabelle: `results/EXPLORATORY/`; figure: `figures/EXPLORATORY/`. Ogni file
riporta lo stato, il commit del codice e gli SHA-256 degli input. Nessuna di
queste analisi produce verdetti.

## 0. Riproduzione esatta (prerequisito del fattoriale)

Le combinazioni estreme del fattoriale riproducono il catalogo P1 già scritto
su disco (commit `120f852`), su tutti i 14195 record
(`FACTORIAL_REPRODUCTION.csv`):
- flag e classificazioni (`valid_bl`, `quality_string`, `diagnostic_reason`,
  `leading_sign`, `hale_sign`, `cycle`, e per la v8.4 `cycle_state`):
  **0 discrepanze** in entrambe le combinazioni;
- valori numerici: 0 discrepanze con la tolleranza
  |Δ| ≤ 10⁻⁹ · max(|x_nuovo|, |x_rif|, scala), dove la scala fa da soglia
  assoluta per valori nulli o piccoli (1 Mx, 1 cm, 1 grado, 10⁻³ per sin α,
  1 Mx·cm); NaN concordi solo se mancanti in entrambi. Massimo scarto
  relativo: 3·10⁻¹⁶ (Φ, d, λ, tilt, S_BL), 10⁻¹³ (sin α, rispetto alla scala).

## 1. Fattoriale maschera (M) × geometria (G) × ciclo (C)

**G è un insieme di modifiche geometriche** (raggio, mappa e media della
latitudine, centroidi, distanza, leading, tilt): il fattoriale separa maschera,
geometria complessiva e ciclo, **non** i singoli componenti di G.

**Validità** (`FACTORIAL_VALIDITY.csv`): dipende **solo da M**. Record validi:
11699 con bitmap ≥ 1, 9997 con bitmap ≥ 33, uguali per G e C; 1702 record
validi in v8.3 diventano non validi in v8.4 (nessuno nel verso opposto);
2496 non sono validi in nessuna combinazione.

**Effetti per record** sul campione valido in tutte le 8 combinazioni (9997
record; `FACTORIAL_EFFECTS_BY_RECORD_SUMMARY.csv`; effetto = media(+) −
media(−) del disegno 2³; mediana del valore assoluto):

| Grandezza | M | G | C | interazioni |
|---|---|---|---|---|
| Φ (relativo) | 0,30 (mediana −30%) | 0,001 | 0 | ≤ 0,0001 |
| d (relativo) | 0,15 | 0,0007 | 0 | ≤ 0,0002 |
| latitudine media | 0,13° | 0,011° | 0 | ≤ 0,003° |
| tilt (assiale) | 5,6° (90° percentile 49°) | 0,13° | 0 | ≤ 0,04° |
| S_BL (relativo) | 0,57 | 0,012 | 0 (in mediana) | ≤ 0,004 |

**Somme per CR ed emisfero** (`FACTORIAL_SBL_SUMS.csv`, 424 celle): mediana di
|effetto| sulle celle rispetto alla mediana di |somma| per cella: M 0,20, G
0,03, C 0, interazioni ≤ 0,004 (campione comune); 0,21, 0,03, 0, ≤ 0,004 con
la validità propria di ogni combinazione.

Lettura: per la misura la correzione che conta è la **maschera**; la
geometria complessiva cambia le grandezze di circa l'1% o meno in mediana; il
ciclo non cambia le grandezze ma solo la classificazione Hale nelle finestre
di sovrapposizione (§2). Le interazioni sono trascurabili.

## 2. Transizioni Hale (`HALE_TRANSITIONS.csv`, `..._BY_RECORD.csv`)

- Denominatore: **4189** record primari validi con Hale definito sia in v8.3
  sia in v8.4. Hale cambiato: **404** (9,6%), **simmetrico**: 202 Hale →
  anti-Hale e 202 anti-Hale → Hale.
- Attribuzione dal fattoriale (la classificazione dipende solo da quel
  fattore): **M 391**, **C 10**, **M e G insieme 3**; nessuna solo da G.
- Peso: le regioni con Hale cambiato portano il 3,4% della somma di |S_BL|
  v8.4 (e il 6,1% della somma netta, che però mescola i due emisferi).
- Casi rappresentativi (`figures/EXPLORATORY/hale_transition_cases.png`, dati
  in `figures/EXPLORATORY/data/`): nei casi da M la maschera ≥ 1 copre tutto
  il riquadro e include campo di altre regioni, e i centroidi si spostano;
  molti casi sono regioni complesse o multipolari. I casi da C sono del
  2018–2020, dove il ciclo assegnato dalla latitudine differisce da quello
  della data. Nessuna delle due classificazioni è assunta corretta per
  definizione.

## 3. Concentrazione e cancellazione della sorgente (`SBL_CONCENTRATION.csv`)

Record primari validi v8.4 (4189). S_BL ha il segno dell'emisfero (sin α),
quindi le somme vanno lette per ciclo ed emisfero:
- il 10% delle regioni con |S_BL| maggiore porta il **62–72%** della somma di
  |S_BL| in ciascun ciclo ed emisfero; il 1% porta il 14–24%;
- contributi di segno opposto si cancellano in parte: per esempio ciclo 24
  nord, positivi 8,7·10³³ e negativi −3,1·10³³ Mx·cm (netto 5,5·10³³);
- togliendo il 1% più estremo la somma netta resta al 63–86% del valore
  completo; togliendo il 10% scende al 18–23% (solo sensibilità descrittiva).

## 4. Record primario contro controllo (`PRIMARY_VS_CONTROL*.csv`)

4073 HARP con i due record distinti e validi; 71 HARP con un solo record
(`role = both`). Il controllo è in mediana 2 giorni prima del primario
(16–84%: −4,1 / +3,8 giorni) e a |lon| mediano 46° (primario 0,2°). Mediane
(16–84%): flusso controllo/primario 2,1× (1,4–4,4×), separazione −9%
(−44%; +50%), Δ tilt assiale 0,2° (−16°; +16°); stesso segno Hale 89%,
stesso segno di S_BL 75%. Le differenze non sono attribuite automaticamente
all'evoluzione: i due record differiscono anche per posizione sul disco e
per la regola di scelta (massimo di USFLUX).

## 5. C1/C2 sul sottoinsieme comune (`P3_C1_C2_COMMON_SUBSET.csv`)

Stesse 829 regioni BARD-HMI presenti in C1, C2-controllo e C2-primario, stessi
criteri di qualità (IC 95% per famiglie):

| | δ mediana | ρ_FL | leading | separazione ρ | \|Δλ\| | flusso nostro/BARD |
|---|---|---|---|---|---|---|
| C1 (contemporaneo) | 3,7° [3,3; 4,1] | 0,69 [0,63; 0,74] | 96,6% | 0,77 | 0,24° | 1,68 |
| C2 controllo | 4,7° [4,1; 5,1] | 0,66 [0,60; 0,71] | 96,6% | 0,70 | 0,30° | 1,82 |
| C2 primario | 7,4° [6,7; 8,0] | 0,53 [0,47; 0,58] | 96,4% | 0,58 | 0,46° | 0,95 |

Sullo stesso sottoinsieme resta l'ordine C1 < C2-controllo < C2-primario per
δ. Con la selezione fissata, la differenza dipende dall'istante del record
(distanza da BARD, posizione sul disco, scelta del record), non dalla
numerosità; queste cause non sono separate tra loro.

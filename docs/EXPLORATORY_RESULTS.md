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

**Effetti per record.** Campione: i **9997 record** (primari e di controllo)
validi in tutte le 8 combinazioni. Per ogni record e grandezza, l'effetto di
un termine è il contrasto del disegno 2³: media sulle 4 combinazioni con il
fattore al livello v8.4 meno media sulle 4 al livello v8.3 (per le
interazioni, il contrasto prodotto). Si riporta la **mediana del valore
assoluto** del contrasto e il 90° percentile, con queste unità:
- tilt: differenza **assoluta assiale** in gradi (differenze modulo 180°);
- latitudine: differenza assoluta in gradi;
- Φ e d: differenza divisa per il valore v8.4 dello stesso record
  (scarto relativo);
- S_BL: differenza **assoluta** in Mx·cm, espressa anche in unità della
  mediana di |S_BL| v8.4 sul campione (1,5·10³⁰ Mx·cm). Lo scarto relativo
  record per record (diviso per |S_BL| del record) è riportato nella tabella
  ma è **instabile** per S_BL vicino a zero e non va usato come sintesi.

| Termine | Φ (relativo) | d (relativo) | latitudine | tilt (assiale) | S_BL (in mediane di \|S_BL\|) |
|---|---|---|---|---|---|
| M | 0,30 | 0,15 | 0,13° | 5,6° (p90 49°) | 0,59 (p90 12,3) |
| G | 0,0010 | 0,0007 | 0,011° | 0,13° (p90 0,59°) | 0,011 (p90 0,83) |
| C | 0 | 0 | 0 | 0 | 0 (diverso da zero nello 0,2% dei record) |
| M×G | 0,0001 | 0,0002 | 0,003° | 0,04° (p90 0,30°) | 0,003 (p90 0,27) |
| M×C, G×C, M×G×C | 0 | 0 | 0 | 0 | 0 (diversi da zero nello 0,2% dei record) |

Il 90° percentile mostra code pesanti: per S_BL l'effetto di G supera 0,8
volte la mediana di |S_BL| nel 10% dei record (regioni grandi), quindi la
geometria non è irrilevante per le regioni più intense anche se lo è in
mediana. Lo stesso vale per l'interazione M×G (p90 0,27).

**Effetto del ciclo.** C non cambia Φ, d, latitudine o tilt, ma cambia
`hale_sign` e quindi **il segno di S_BL**. Nella configurazione v8.4
(M = 33, G = v8.4) cambia `hale_sign` in **20 record** del campione comune
(0,2%), che portano lo 0,015% della somma di |S_BL|; sommando le 4 coppie del
disegno, 80 cambi. L'effetto aggregato quasi nullo deriva da pochi casi di
piccolo peso, non da cancellazioni.

**Somme per CR ed emisfero** (`FACTORIAL_SBL_SUMS.csv`, 424 celle): mediana di
|effetto| sulle celle rispetto alla mediana di |somma| per cella: M 0,20, G
0,030, C 0, M×G 0,003, M×C 0, G×C 0, M×G×C 0 (campione comune); con la
validità propria di ogni combinazione 0,21, 0,031, 0, 0,0035, 0, 0, 0. Le
somme nette possono nascondere differenze individuali, riportate sopra.

Lettura: per la misura la correzione che conta è la **maschera**; la
geometria complessiva cambia le grandezze di circa l'1% in mediana ma molto di
più nelle regioni più intense; il ciclo cambia il segno di S_BL in pochi
record nelle sovrapposizioni.

## 2. Transizioni Hale (`HALE_TRANSITIONS.csv`, `..._BY_RECORD.csv`)

- Denominatore: **4189** record **primari** validi con Hale definito sia in
  v8.3 sia in v8.4; ogni HARP ha un solo record primario, quindi sono 4189
  HARP. Hale cambiato: **404 record = 404 HARP** (9,6%): 202 Hale →
  anti-Hale e 202 anti-Hale → Hale. La simmetria è **descrittiva** e non
  prova l'assenza di effetti sistematici.
- Includendo anche i record di controllo (9997 record validi in entrambi i
  metodi): 1130 record con Hale cambiato, in 1025 HARP distinte.
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

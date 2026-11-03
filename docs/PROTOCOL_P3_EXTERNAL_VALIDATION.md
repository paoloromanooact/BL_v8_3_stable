# Protocollo P3 — Validazione esterna con BARD (coerenza delle misure)

Stato: **congelato il 2026-11-03** (commit) prima di qualunque abbinamento tra
le nostre regioni e un catalogo esterno. Informazioni già viste:
`docs/SEEN_BEFORE_FREEZE_2026-11-03.md` (punti 8 e 10).

## 1. Scopo, livelli e limiti

Confrontare tilt, polarità leading, segno Hale, separazione e latitudine
misurati con il nostro codice (P1 §3) con quelli di un catalogo costruito da
altri, con un altro algoritmo.

- **Livello 1 — stesso strumento, metodo indipendente.** BARD-HMI: regioni
  bipolari da magnetogrammi HMI full-disk in linea di vista. Verifica la
  nostra **implementazione** (WCS, centroidi, segni, tilt); condivide gli
  errori strumentali di HMI.
- **Livello 2 — strumento diverso.** BARD-MDI nel periodo comune con HMI (dal
  2010-05; 90 regioni BARD-MDI). Solo descrittivo, per la scarsa numerosità.

**Limite.** BARD verifica la coerenza delle grandezze misurate tra due
metodi. **Non certifica la maschera SHARP** (bitmap ≥ 33): usa un'altra
segmentazione su un altro prodotto. Sulla maschera dà solo indicazioni
indirette (separazione, rapporto dei flussi).

**Dati.** BARD (Muñoz-Jaramillo, Navarrete & Campusano 2021, ApJ 920, 31;
Harvard Dataverse doi:10.7910/DVN/QEMSZ2), versione 3.0 (2022-06-16, CC0),
file originali CSV con MD5 uguali a quelli pubblicati (HMI `9a53d61d…`, MDI
`f5f1dc04…`), in `data/sharp/external/BARD/` con `PROVENANCE.txt` e
`SHA256.txt`.

## 2. Convenzioni di BARD — risolte prima del confronto

Risolte con la descrizione dell'algoritmo (Muñoz-Jaramillo et al. 2016,
IEEE BigData, nel dataset) e con **verifiche interne a BARD**, senza dati
SHARP salvo la longitudine centrale del disco CRLN_OBS, che è una grandezza
di effemeride e non una misura. La descrizione dell'algoritmo non fissa
esplicitamente direzione delle longitudini e segno del tilt; le verifiche
interne (file HMI, 1457 regioni) danno:

| Convenzione | Verifica | Esito |
|---|---|---|
| Direzione delle longitudini | la polarità `LeadingPolarity` ha la longitudine maggiore | 100% → crescono verso ovest |
| Riferimento delle longitudini | \|BMRLongitude − CRLN_OBS\| ≤ 90° (1447 regioni con CRLN_OBS entro 2 h) | 98,1% → Carrington |
| Segno di `Tilt_rel` | confronto con il tilt ricalcolato dai centroidi | `Tilt_rel` = −asin(sin α) (correlazione −1,000; differenza mediana 0,0°): positivo se la following è a sud della leading |
| Significato di `Hale` | confronto con la polarità attesa nel ciclo 24 | `Hale` = True esattamente quando la leading ha la polarità attesa per il ciclo 24 (100%); tutte le regioni sono assegnate al ciclo 24 |

**Definizione delle verifiche e soglie.** Le soglie per direzione e
riferimento (0,90/0,10 e 0,95) erano nella prima bozza di P3, scritta prima di
calcolarle; la soglia 0,99 per `Tilt_rel` e `Hale` è stata aggiunta **dopo**
aver visto un accordo del 100% (non cieca):
- direzione: frazione F_dir di regioni in cui la `LeadingPolarity` ha
  wrap(L_lead − L_follow) > 0; verso ovest se F_dir ≥ 0,90, verso est se
  F_dir ≤ 0,10, altrimenti indeterminata;
- riferimento: per ogni regione con un record dei metadati SHARP entro 2 ore
  da t_B, D = |wrap(BMRLongitude − CRLN_OBS)|; frazione F_car con D ≤ 90°;
  Carrington se F_car ≥ 0,95, altrimenti indeterminato;
- segno di `Tilt_rel` e significato di `Hale`: accordo ≥ 0,99 con una delle
  due relazioni in tabella, altrimenti indeterminato.

Queste verifiche **stabiliscono solo le convenzioni del catalogo** e non
selezionano regioni. Le regioni con D > 90° (1,9%) e quelle senza CRLN_OBS
entro 2 ore **restano** nel catalogo e passano dall'abbinamento come tutte le
altre; nei conteggi di §3 compaiono come righe a parte. Lo script ripete le
verifiche; se una convenzione risulta indeterminata, il confronto che ne
dipende è **sospeso** e si scrive un nuovo protocollo.

## 3. Quale misura SHARP si confronta, e quando

BARD misura ogni regione a un istante t_B (massimo del flusso). Due confronti,
riportati separatamente:

- **C1 — misura SHARP contemporanea (principale).** Per ogni regione BARD si
  cerca nei metadati orari la HARP abbinata (§4) al record orario più vicino a
  t_B, purché entro **±1 ora** da t_B e con QUALITY ∈ {0, 0x80}. Di quel
  record si scaricano Br e bitmap (stesso metodo di `download_records.py`) e
  si misura con `measure_v84`. Confronta le due misure **nello stesso
  istante**.
- **C2 — record già selezionati (secondario).** Per le stesse coppie, si usa
  la misura della HARP nel catalogo P1: il record di controllo (flusso
  massimo entro ±60°) e, a parte, il record primario. Si riporta |Δt| tra
  t_B e il record. Mostra quanto le misure della serie, prese in istanti
  diversi, si discostano da BARD.

Si riportano il numero di regioni BARD, di abbinamenti, di quelle escluse per
ogni motivo (nessuna HARP entro ±1 ora, QUALITY, abbinamento non trovato,
`valid_bl` = 0) e gli abbinamenti usati in C1 e in C2.

## 4. Abbinamento

Per ogni regione BARD (t_B, latitudine λ_B = BMRLatitude, longitudine
L_B = BMRLongitude, Carrington, in gradi):
- candidate: le HARP con un record orario entro ±1 ora da t_B (si usa il più
  vicino); per esse λ_H = LAT_FWT e L_H = (LON_FWT + CRLN_OBS) mod 360 di quel
  record;
- stesso emisfero, |λ_H − λ_B| ≤ 3° e |wrap(L_H − L_B)| ≤ 6°, con wrap in
  [−180°, 180°);
- distanza d = √[(Δλ/3°)² + (ΔL/6°)²]; assegnazione uno a uno per d
  crescente, a parità per numero HARP crescente e poi per indice di riga BARD
  crescente.

Controllo casuale: si somma a L_B un valore uniforme in [0°, 360°) e si
ripete l'abbinamento; 20 ripetizioni, semi 20261107 + k. Si riporta la
**frequenza di associazioni nel controllo casuale** accanto a quella reale;
non stabilisce quali abbinamenti reali siano sbagliati.

## 5. Grandezze, statistiche e criteri operativi (C1, livello 1)

Campione principale: abbinamenti C1 con `valid_bl` = 1 e Φ ≥ 1·10²¹ Mx.

Grandezze BARD **ricalcolate dai centroidi** di polarità (PLatitude,
PLongitude, NLatitude, NLongitude) con la nostra definizione (P1 §3): tilt nel
piano tangente al punto medio, leading = polarità più a ovest,
γ = sign(λ)·asin(sin α), separazione come distanza di cerchio massimo.

**Tilt come asse del bipolo.** γ è l'angolo dell'asse rispetto all'est
locale, definito modulo 180°, rappresentato in [−90°, 90°) per entrambi i
lati. Differenza **periodica**: Δγ = ((γ_nostro − γ_BARD + 90°) mod 180°) − 90°.
Per la correlazione di Spearman, per evitare che il salto tra −90° e +90°
alteri i ranghi, il nostro valore si rappresenta nel ramo più vicino a quello
di BARD: γ'_nostro = γ_BARD + Δγ; ρ si calcola tra γ_BARD e γ'_nostro.
Polarità leading e segno Hale sono verifiche **separate** dell'orientamento
magnetico (quale polarità sta davanti), che il tilt modulo 180° non contiene.

Incertezze: per ogni indicatore, intervallo al 95% da bootstrap (2000
ricampionamenti, seme 20261108). **Unità ricampionata:** la famiglia P1e
della HARP abbinata (`family_id`), così che le misure di candidate ricomparse
della stessa regione restino insieme; una HARP senza ricomparse è una
famiglia da sola. Si riporta sempre n (abbinamenti) e il numero di famiglie.

| Grandezza | Statistica | Criterio operativo |
|---|---|---|
| γ | Spearman ρ; mediana di \|Δγ\| | ρ ≥ 0,6 e mediana \|Δγ\| ≤ 10° |
| Polarità leading | frazione uguale | ≥ 0,90 |
| Hale ricalcolato (definizione comune) | frazione uguale | ≥ 0,90 |
| Hale pubblicato da BARD | frazione uguale al nostro `hale_sign` | solo riportato |
| Separazione | Spearman ρ; mediana del rapporto | ρ ≥ 0,7 |
| Latitudine | mediana di \|Δλ\| | ≤ 1° |
| Flusso | mediana del rapporto nostro/BARD | solo riportato |

- **Hale ricalcolato** usa per entrambi i lati la stessa regola (polarità
  leading dalla geometria, ciclo da P1/P1c alla data e latitudine della
  regione): verifica la **coerenza delle misure**.
- **Hale pubblicato** confronta il nostro `hale_sign` con la colonna `Hale` di
  BARD, che assegna tutto al ciclo 24: verifica anche la **classificazione**
  esterna, comprese le differenze di assegnazione del ciclo.

**Motivazione dei criteri.** Sono criteri **operativi**, non test statistici.
Il tilt di una singola regione ha un'incertezza tipica dell'ordine di 10°
(rumore, evoluzione, definizione dei centroidi) e la distribuzione dei tilt
ha una dispersione dell'ordine di 20°: due metodi corretti dovrebbero dare
differenze mediane sotto 10° e correlazioni almeno moderate (ρ ≥ 0,6). La
polarità leading e il segno Hale sono robusti per bipoli ben definiti;
disaccordi oltre il 10% indicherebbero un problema di segni o di maschera più
che di rumore. La separazione dipende dalla soglia e dalla segmentazione,
quindi si chiede solo un ordinamento coerente (ρ ≥ 0,7). La latitudine del
baricentro è poco sensibile al metodo (≤ 1°). Si riportano sia il criterio
sulla stima puntuale sia se l'intervallo al 95% resta dentro il criterio.

**Esito:** "coerente con BARD (livello 1)" se tutti i criteri operativi sono
soddisfatti dalle stime puntuali; altrimenti "da investigare", con l'elenco
dei criteri non soddisfatti. Un esito negativo **non** autorizza correzioni
silenziose: ogni modifica al metodo richiede un nuovo protocollo e la
ripetizione di P1, P2 e P3. C2 e il livello 2 si riportano con le stesse
statistiche, senza esito.

## 6. Output (`results/P3/`)

`P3_BARD_CONVENTIONS.csv` (§2), `P3_BARD_SELECTION.csv` (§3, conteggi ed
esclusioni), `P3_BARD_MATCHES.csv` (coppie, con le grandezze dei due lati in
C1 e C2), `P3_RANDOM_CONTROL.csv` (§4), `P3_BARD_SUMMARY.csv` (§5, con
intervalli ed esito); SHA-256 di P1, P1b, P1c, P1d, P1e e P3 in ogni file.

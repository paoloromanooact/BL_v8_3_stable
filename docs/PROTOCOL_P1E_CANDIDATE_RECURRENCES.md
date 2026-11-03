# Protocollo P1e — Ricomparse candidate (sostituisce la regola di P1d §1)

Stato: **congelato il 2026-11-03** (commit), prima della serie P1 completa e di P2 sui
dati veri. Sostituisce **solo** la regola di P1d §1; P1d §2–§4 (variante E,
sensibilità S8, evoluzione, controlli) restano validi e si applicano alla
nuova regola; la variante E va letta come in §0. P1, P1b, P1c, P1d non vengono modificati. Informazioni già
viste: `docs/SEEN_BEFORE_FREEZE_2026-11-03.md` (in particolare i punti 6 e
9). Protocollo **non cieco**: il criterio del lembo è stato scelto dopo la
diagnostica del punto 6; le finestre ±3°/±6° sono state scritte prima di
provarle, poi verificate sui metadati (§4) senza modificarle.

## 0. Che cosa fa e che cosa non fa

La serie principale (variante A di P1) conta ogni HARP con il suo record
primario. Una regione che sopravvive a una rotazione può ricevere una nuova
HARP, e allora entra di nuovo nelle somme. P1e individua **candidate
ricomparse** e definisce la variante E come **sensibilità all'esclusione
delle candidate ricomparse**: per ogni famiglia si tiene solo la prima HARP
(`family_rank` = 0).

E **non** ricostruisce l'emersione e **non** separa il flusso nuovo che può
emergere dentro una regione persistente: dice soltanto quanto cambiano le
somme e i test se si tolgono le HARP che potrebbero essere passaggi ripetuti
della stessa regione. La vicinanza nello spazio e nel tempo non dimostra che
sia la stessa regione. Il flag descrittivo `first_seen_on_disk` = 1 se il
primo record della HARP ha LON_FWT > −60° (comparsa sul disco e non dal lembo
est).

## 1. Regola

**Dati, tutti dai metadati SHARP orari** (`data/sharp/metadata/`):
- per ogni HARP con record primario (P1 §4 con P1b): istante t = T_REC del
  record primario (TAI), latitudine λ = LAT_FWT e longitudine di Carrington
  L = (LON_FWT + CRLN_OBS) mod 360 dello **stesso record**;
- LON_FWT del primo e dell'ultimo record orario della HARP.

**Rotazione differenziale** (Snodgrass & Ulrich 1990, ApJ 351, 309; strutture
magnetiche), velocità siderale in gradi/giorno:
ω(λ) = 14,713 − 2,396 sin²λ − 1,787 sin⁴λ;
rotazione siderale di Carrington ω_C = 14,1844 gradi/giorno.

La HARP j è **candidata ricomparsa** della HARP i se valgono tutte:
1. Δt = t_j − t_i (record primari) con 20 ≤ Δt ≤ 34 giorni;
2. stesso emisfero (segno di λ) e |λ_j − λ_i| ≤ **3°**;
3. longitudine prevista per j:
   L_pred = [L_i + (ω(λ̄) − ω_C)·Δt] mod 360, con Δt in giorni e ω(λ̄)
   calcolata alla **latitudine media delle due HARP** λ̄ = (λ_i + λ_j)/2
   (latitudini con segno; stesso emisfero per la condizione 2);
   ΔL = wrap(L_j − L_pred), dove wrap riporta l'angolo in [−180°, 180°)
   (distanza periodica in longitudine), e |ΔL| ≤ **6°**;
4. **criterio del lembo**: l'ultimo record orario di i ha LON_FWT ≥ 60°
   (esce dal lembo ovest) e il primo record orario di j ha LON_FWT ≤ −60°
   (entra dal lembo est).

**Distanza e spareggi.** Per ogni coppia ammessa
d = √[(Δλ/3°)² + (ΔL/6°)²], con Δλ = λ_j − λ_i. **Tutte** le coppie ammesse
dell'intero periodo si ordinano in un unico elenco globale per d crescente,
poi per numero HARP di j crescente, poi per numero HARP di i crescente; si
scorrono in quest'ordine e una coppia si accetta se j non ha ancora un
predecessore e i non ha ancora un successore (assegnazione uno a uno). Le catene i → j → k definiscono le famiglie;
`family_rank` è la posizione nella catena (0 = prima HARP).

## 2. Frequenza di associazioni nel controllo casuale

Controllo con longitudini casuali: a ogni HARP si somma a CRLN_OBS un valore
uniforme in [0°, 360°) e si riapplica la regola; 20 ripetizioni, semi
20261106 + k. Si riporta la **frequenza di associazioni nel controllo
casuale** (media, minimo, massimo), totale e per anno, accanto alla frequenza
reale. Il confronto dice quante associazioni ci si aspetta per pura
coincidenza con la stessa densità di regioni; è **descrittivo** e **non** è
una stima diretta della contaminazione: non stabilisce quali né quante delle
associazioni reali siano false.

## 3. Uso

Variante E (P1) e sensibilità S8 (P2) come in P1d §2, solo descrittive. Le
ricomparse restano **candidate** in tutti gli output e i testi.

## 4. Verifica sui metadati eseguita prima del congelamento (non cieca)

Codice: `python/sharpbl/recurrence.py` (`recurrences_p1e`,
`random_control_p1e`); tabella per anno
`results/P1/P1E_METADATA_VERIFICATION_BY_YEAR.csv`. Solo metadati.
- HARP con record primario: 7133; candidate ricomparse: 443 (6,2%), in 373
  famiglie, `family_rank` massimo 4.
- Frequenza di associazioni nel controllo casuale: media 1,2% (min 0,9%,
  max 1,4% su 20 ripetizioni); per anno tra 0,2% e 1,5%.
- Per confronto (punto 6 dell'elenco delle informazioni già viste): regola
  P1d 45% contro 19% nel controllo casuale.
- HARP il cui primo record è sul disco (LON_FWT > −60°): 69%.
Le soglie di §1 erano state scritte prima di questa verifica e non sono state
cambiate dopo.

# Piano di controllo delle HARP dominanti (registrato il 2026-11-11)

Stato: **piano registrato (congelato) il 2026-11-11, prima di qualunque codice o lettura mirata
dei FITS**, dopo due revisioni esterne (`282ef4e`, `32ed3b0`). Da questo commit non si modifica;
ogni cambiamento è un emendamento registrato prima dell'esecuzione. È un controllo di qualità della misura, descrittivo:
non cambia il catalogo P1, non produce verdetti e non interviene sui test P2/P2f. Se un controllo
indica un problema sistematico, la correzione richiede un emendamento al protocollo P1 e un
ricalcolo dichiarato, non una modifica in corsa.

## 1. Motivo

Nel catalogo P1 (`docs/EXPLORATORY_RESULTS.md` §3) il 10 % delle regioni con |S_BL| maggiore
porta il 62–72 % della somma di |S_BL| in ciascun ciclo ed emisfero, e l'1 % porta il 14–24 %.
Somme, efficienza e confronti dipendono quindi da poche regioni grandi: va verificato che per
queste la misura (maschera, polarità, centroidi, associazione NOAA, scelta del record) sia
affidabile e non un artefatto.

## 2. Campione (fissato prima)

- **Base**: tutti i record **primari validi v8.4** della serie principale P1 (`role ≠ control`,
  `valid_bl = 1`, cicli 24 e 25; gli stessi filtri delle somme di `run_p1`), dal catalogo
  `results/P1/P1_SBL_CATALOG_BY_HARP.csv`. Il conteggio si ricava dai filtri al momento
  dell'esecuzione e si riporta (il 4189 di `docs/EXPLORATORY_RESULTS.md` §3 ha un denominatore
  proprio, di confronto tra metodi, e non si assume). Per ogni HARP si riporta se appartiene
  anche al campione S di P2.
- **Gruppi**: ciclo × emisfero (24N, 24S, 25N, 25S), nell'ordine dato.
- **Dominanti**: per gruppo, le **20 HARP con |S_BL| maggiore**, ordinate per |S_BL|
  decrescente e, a parità, per `HARPNUM` crescente. Si riporta la quota di Σ|S_BL| del gruppo
  (denominatore: somma dei valori assoluti su tutta la base del gruppo) che portano, distinta
  dalla somma netta Σ S_BL.
- **Controllo**: per gruppo, **10 HARP estratte a caso senza reimmissione** tra le restanti del
  gruppo (base meno le 20 dominanti), dall'elenco ordinato per `HARPNUM` crescente, con un unico
  generatore `numpy.random.default_rng(20261111)` usato nell'ordine dei gruppi 24N, 24S, 25N,
  25S. L'elenco estratto è salvato.
- In tutto 120 HARP, 240 FITS (Br e bitmap) del record primario, già in `data/sharp/fits`.
  Nessun nuovo download.

## 3. Controlli (automatici, soglie fissate prima; esito per HARP = elenco di flag)

| Codice | Che cosa | Come | Flag se |
|---|---|---|---|
| M1 maschera | copertura e troncamento | frazione di pixel con bitmap ≥ 33 che toccano il bordo del riquadro | > 0 pixel di maschera sul bordo (**possibile troncamento**) |
| M2 maschera | flusso fuori maschera | Φ di \|Br\| ≥ 100 G fuori della maschera ≥ 33 ma dentro bitmap ≥ 1, in rapporto a Φ in maschera | > 20 % (**flusso escluso**) |
| M3 maschera | multipolarità | numero di componenti connesse (8-connettività) sopra soglia per polarità | ≥ 3 componenti per una polarità con ≥ 10 % del flusso di quella polarità (**multipolare**) |
| P1 polarità | bilancio | \|Φ₊ − Φ₋\| / (Φ₊ + Φ₋) | > 0,5 (**sbilanciata**) |
| P2 polarità | leading robusto | segno leading ricalcolato con soglie 100 e 300 G e con bitmap ≥ 1 | cambia in almeno una variante (**leading instabile**) |
| P3 polarità | Hale | `hale_sign` | = −1 o 0 (**anti-Hale / non definito**), riportato |
| C1 centroidi | pesatura | centroidi di polarità con **pesi uniformi** (uno per pixel) contro **pesi \|Br\|** (quelli di P1), stessa maschera (bitmap ≥ 33, \|Br\| ≥ 100 G) e stessa geometria sferica di `measure.py` (`hale_case_figures.pixel_centroids` usa già pesi \|Br\| e non serve) | \|Δtilt\| > 10° **o** \|Δd\|/d_P1 > 20 % (**centroidi sensibili alla pesatura**) |
| C2 centroidi | soglia | centroidi (pesi \|Br\|) con soglia 300 G contro 100 G, maschera ≥ 33 | come C1 (**sensibili alla soglia**) |
| N1 NOAA | complessità | `NOAA_NUM` | ≥ 2 (**più regioni NOAA**), riportato con `NOAA_ARS` |
| R1 record | posizione | \|longitudine di Stonyhurst\| del record primario | > 30° (**lontano dal meridiano**) |
| R2 record | stabilità | S_BL del record di controllo / S_BL del primario (da `results/EXPLORATORY/PRIMARY_VS_CONTROL_BY_HARP.csv`, stessa HARP) | < 0,5 o > 2 o segno diverso (**instabile tra record**); se il record di controllo manca (`role = both`) o non è valido: «**non disponibile**», non un flag |

**Definizioni comuni.** Δtilt è la differenza tra gli angoli ridotta modulo 180° **dopo** la
sottrazione: Δtilt = ((α_var − α_P1 + 90°) mod 180°) − 90° (ridurre separatamente gli angoli non
basta vicino a ±90°); Δd è riferita alla d della misura P1 (denominatore d_P1). **Rapporti non
definiti**: se S_BL,P1 = 0, R2 è «non valutabile»; lo stesso per ogni diagnostica con
denominatore nullo (d_P1 = 0, Φ₊ + Φ₋ = 0, flusso in maschera = 0), riportata come tale e mai
sostituita con zero o con un flag. Le varianti sono esattamente queste
combinazioni (soglia su \|Br\|, maschera): P1 = (100 G, bitmap ≥ 33); (300 G, ≥ 33); (100 G, ≥ 1);
per C1 la pesatura uniforme a (100 G, ≥ 33). Se in una variante una polarità non ha pixel sopra
soglia, il confronto è «**impossibile**» e si riporta come tale, senza flag. Per ogni variante si
registrano Φ, d, tilt e S_BL ricalcolati (servono a §4).

Ogni HARP ha inoltre una **scheda visiva** (`figures/DOMINANT/<HARPNUM>.png`): mappa Br con
contorni della maschera ≥ 33 e ≥ 1, centroidi delle polarità (pesati e per conteggio), segmento
leading→following, valori di Φ, d, tilt, S_BL. Le schede servono alla lettura umana e non
producono flag.

## 4. Sintesi e lettura (fissate prima)

Tre livelli, tenuti distinti:
1. **Segnalazioni** (flag di §3): indicano proprietà da esaminare, non errori. Una maschera al
   bordo è un *possibile* troncamento; multipolarità e anti-Hale possono essere proprietà
   fisiche reali; più regioni NOAA è complessità, non errore.
2. **Sensibilità misurate**: per ogni HARP esaminata e per ogni variante v di §3, la differenza
   S_BL,v − S_BL,P1; per gruppo, Δ_v = Σ_{HARP esaminate} (S_BL,v − S_BL,P1) in rapporto a
   **Σ|S_BL| dell'intero gruppo** (denominatore esplicito, tutta la base) e, separatamente, alla
   somma netta Σ S_BL. Vale solo per le HARP esaminate: **non certifica le HARP non esaminate**.
   Per ogni variante si riportano **quante HARP sono confrontabili** (confronto possibile) e
   **quale quota di Σ|S_BL| del gruppo coprono**; le HARP con confronto impossibile restano
   fuori dalla somma e **non si sostituisce una misura mancante con zero**.
3. **Errori confermati**: solo da evidenza specifica documentata per HARP (per esempio
   maschera che include campo di un'altra regione visibile nella scheda, polarità invertita
   rispetto alla mappa), elencati uno per uno con il motivo.

Tabelle: per HARP (`results/DOMINANT/DOMINANT_HARP_CHECKS.csv`: gruppo, rango, dominante o
controllo, appartenenza a S, |S_BL|, quota di Σ|S_BL| del gruppo, valori e flag, valori
ricalcolati per variante, confronti impossibili); per gruppo, frequenze dei flag tra dominanti
e controlli (nessun test statistico) e Δ_v per variante.

Lettura: la quota di Σ|S_BL| del gruppo portata da HARP con segnalazioni di misura (M1–M3, P2,
C1–C2) è una **priorità di approfondimento** se supera il 25 %, non una dimostrazione che la
somma cambi. Si parla di **sensibilità** solo per differenze effettivamente ricalcolate
(livello 2); un valore sotto il 25 % non certifica nulla sulle HARP non esaminate. **Nessun
emendamento a P1 scatta dai flag**: una proposta di emendamento richiede errori confermati o
sensibilità misurate rilevanti, e un piano proprio.

## 5. Esecuzione

- Script `python/sharpbl/dominant_harp_check.py`, scritto dopo la registrazione di questo piano;
  legge solo catalogo, selezione, `PRIMARY_VS_CONTROL*.csv` e i 240 FITS; provenienza (commit,
  SHA-256 di questo piano, di P1 e dei FITS letti) negli output.
- Costo: lettura di 240 FITS e figure, pochi minuti; si esegue con `nice` **dopo** la fine della
  validazione P2f o comunque senza competere con essa.
- Risultati in `docs/DOMINANT_HARP_RESULTS.md`; una sola esecuzione; eventuali correzioni del
  codice dopo un esito richiedono un emendamento registrato.

## 6. Scelte chiuse con il revisore (2026-11-11) e rinvii

- Numerosità 20 + 10 per gruppo: confermata, con ordinamento, pari merito e ordine delle
  estrazioni fissati in §2.
- Base: tutti i primari validi della serie principale P1 (§2), con appartenenza a S riportata.
- Sovrapposizioni tra patch della stessa CR: **rinviate** a un eventuale controllo separato,
  con geometria e corrispondenza temporale da definire.
- Soglie dei flag (§3) e 25 % come priorità di approfondimento (§4): **confermati** dal
  revisore come scelte operative di questo controllo descrittivo, senza validazione fisica.
- Precisazioni finali recepite: Δtilt ridotto dopo la sottrazione; rapporti non definiti «non
  valutabili»; confrontabilità e quota coperta riportate per variante; M1 = «possibile
  troncamento».

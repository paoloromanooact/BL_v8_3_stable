# Piano di controllo delle HARP dominanti — bozza per revisione (2026-11-11)

Stato: **bozza, scritta prima di qualunque codice o lettura mirata dei FITS**; diventa piano
registrato con un commit dopo la revisione. È un controllo di qualità della misura, descrittivo:
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

- Base: record primari validi v8.4 del campione S di P2 (2485 regioni, cicli 24–25, Φ ≥ 10²¹
  Mx, non AMBIGUOUS), stessi file di P2 (`results/P1/P1_SBL_CATALOG_BY_HARP.csv`,
  `run_p2.samples(cat)["S"]`).
- **Gruppi**: ciclo × emisfero (24N, 24S, 25N, 25S).
- **Dominanti**: per gruppo, le **20 HARP con |S_BL| maggiore** (80 in tutto; si riporta la
  quota della somma di |S_BL| del gruppo che portano).
- **Controllo**: per gruppo, **10 HARP estratte a caso** tra le restanti con Φ ≥ 10²¹ Mx (40 in
  tutto; seme 20261111, estrazione senza reimmissione, elenco salvato), per confrontare le
  frequenze dei flag tra dominanti e non dominanti.
- In tutto 120 HARP, 240 FITS (Br e bitmap) del record primario, già scaricati in
  `data/sharp`. Nessun nuovo download.

## 3. Controlli (automatici, soglie fissate prima; esito per HARP = elenco di flag)

| Codice | Che cosa | Come | Flag se |
|---|---|---|---|
| M1 maschera | copertura e troncamento | frazione di pixel con bitmap ≥ 33 che toccano il bordo del riquadro | > 0 pixel di maschera sul bordo (**troncata**) |
| M2 maschera | flusso fuori maschera | Φ di \|Br\| ≥ 100 G fuori della maschera ≥ 33 ma dentro bitmap ≥ 1, in rapporto a Φ in maschera | > 20 % (**flusso escluso**) |
| M3 maschera | multipolarità | numero di componenti connesse (8-connettività) sopra soglia per polarità | ≥ 3 componenti per una polarità con ≥ 10 % del flusso di quella polarità (**multipolare**) |
| P1 polarità | bilancio | \|Φ₊ − Φ₋\| / (Φ₊ + Φ₋) | > 0,5 (**sbilanciata**) |
| P2 polarità | leading robusto | segno leading ricalcolato con soglie 100 e 300 G e con bitmap ≥ 1 | cambia in almeno una variante (**leading instabile**) |
| P3 polarità | Hale | `hale_sign` | = −1 o 0 (**anti-Hale / non definito**), riportato |
| C1 centroidi | pesatura | centroidi pesati con \|Br\| contro centroidi per conteggio di pixel (`hale_case_figures.pixel_centroids`) | tilt cambia > 10° **o** d cambia > 20 % (**centroidi sensibili**) |
| C2 centroidi | soglia | centroidi a 100 G contro 300 G | come C1 |
| N1 NOAA | complessità | `NOAA_NUM` | ≥ 2 (**più regioni NOAA**), riportato con `NOAA_ARS` |
| R1 record | posizione | \|longitudine di Stonyhurst\| del record primario | > 30° (**lontano dal meridiano**) |
| R2 record | stabilità | S_BL del record di controllo / S_BL del primario (da `results/EXPLORATORY/PRIMARY_VS_CONTROL_BY_HARP.csv`, stessa HARP) | < 0,5 o > 2 o segno diverso (**instabile tra record**) |

Ogni HARP ha inoltre una **scheda visiva** (`figures/DOMINANT/<HARPNUM>.png`): mappa Br con
contorni della maschera ≥ 33 e ≥ 1, centroidi delle polarità (pesati e per conteggio), segmento
leading→following, valori di Φ, d, tilt, S_BL. Le schede servono alla lettura umana e non
producono flag.

## 4. Sintesi e lettura (fissate prima)

- Tabella per HARP (`results/DOMINANT/DOMINANT_HARP_CHECKS.csv`): gruppo, rango, |S_BL|, quota
  del gruppo, valori e flag di ogni controllo, dominante/controllo.
- Per gruppo: numero di HARP con ciascun flag tra le 20 dominanti e tra le 10 di controllo;
  **quota della somma di |S_BL| del gruppo portata da HARP con almeno un flag di misura**
  (M1–M3, P2, C1–C2; i flag P1, P3, N1, R1, R2 sono descrittivi).
- Lettura: se in un gruppo le HARP con un flag di misura portano **più del 25 %** della somma
  di |S_BL|, la somma di quel gruppo si dichiara **sensibile alle scelte di misura** e si
  propone un emendamento a P1 con un ricalcolo dichiarato; altrimenti si registra l'esito.
  Nessun flag autorizza a rimuovere una HARP dal catalogo in questo controllo.
- Confronto dominanti/controllo: frequenze dei flag riportate; nessun test statistico.

## 5. Esecuzione

- Script `python/sharpbl/dominant_harp_check.py`, scritto dopo la registrazione di questo piano;
  legge solo catalogo, selezione, `PRIMARY_VS_CONTROL*.csv` e i 240 FITS; provenienza (commit,
  SHA-256 di questo piano, di P1 e dei FITS letti) negli output.
- Costo: lettura di 240 FITS e figure, pochi minuti; si esegue con `nice` **dopo** la fine della
  validazione P2f o comunque senza competere con essa.
- Risultati in `docs/DOMINANT_HARP_RESULTS.md`; una sola esecuzione; eventuali correzioni del
  codice dopo un esito richiedono un emendamento registrato.

## 6. Da decidere con il revisore prima del congelamento

- Numerosità (20 + 10 per gruppo) e soglie dei flag (§3).
- Se usare il campione S (2485) o tutti i record primari validi (4189) come base: proposta S,
  perché è quello dei test.
- Se aggiungere un controllo sulla distanza tra la maschera e le HARP vicine nella stessa CR
  (sovrapposizione di patch), oggi non previsto.

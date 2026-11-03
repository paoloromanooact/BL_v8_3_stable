# Analisi esplorative per l'articolo — inventario e piano

Data: 2026-11-03. **Tutte le analisi di questo piano sono esplorative**: la
serie P1 completa, i risultati di P2 (descrittivi) e di P3 sono già stati
osservati. Nessun protocollo congelato viene modificato; nessuna analisi qui
produce verdetti. Risultati in `results/EXPLORATORY/`, figure in
`figures/EXPLORATORY/`; ogni file porta la colonna/metadato
`status = "esplorativo, serie già osservata"`, il commit del codice e gli
SHA-256 dei file di input.

## 1. Inventario

| Analisi | Esiste già | Dove | Serve calcolo nuovo |
|---|---|---|---|
| Misura v8.4 e legacy per ogni record (14195) | sì | `results/P1/P1_SBL_CATALOG_BY_HARP.csv` (`*` e `leg_*`) | no |
| Confronto v8.3/v8.4 per regione e CR | sì, globale | `results/P1/P1_LEGACY_VS_V84.csv`, fig. 3 | sì: separazione per fattore (§2) |
| Effetto di ciascuna correzione (maschera, geometria, ciclo) | **no** | — | **sì, fattoriale 2×2×2** |
| Transizioni Hale tra metodi | solo il conteggio 404 | fig. 3 | sì: denominatore, verso, attribuzione |
| Concentrazione e cancellazione della sorgente | **no** | — | sì (dal catalogo) |
| Primario contro controllo sulle stesse HARP | parziale (percentili in `P1_CHECKS.csv`) | P1d §3 | sì: differenze appaiate complete |
| C1/C2 sul sottoinsieme comune | **no** (campioni diversi) | — | sì (dalle coppie di `P3_BARD_MATCHES.csv`) |
| Dizionario delle colonne, riproducibilità | parziale (README, protocolli) | — | scrittura |
| Struttura dell'articolo | **no** | — | scrittura |

## 2. Definizione dei fattori del disegno fattoriale

Ogni differenza tra `measure_legacy` e `measure_v84` (`python/sharpbl/measure.py`)
è assegnata a un fattore o tenuta fissa:

| Differenza | legacy (v8.3) | v8.4 | Assegnata a |
|---|---|---|---|
| Soglia bitmap della maschera | ≥ 1 | ≥ 33 | **M** (maschera) |
| Raggio solare per area del pixel e distanze | 6,957·10¹⁰ cm | RSUN_REF (6,96·10¹⁰ cm) | **G** (geometria) |
| Mappa di latitudine | sin(CRVAL2) + (j − CRPIX2)Δμ | WCS completa | **G** |
| Latitudine media | media pesata dei valori di latitudine | centroide sferico dei vettori unitari | **G** |
| Centroidi di polarità | media pesata in coordinate pixel | media pesata dei vettori unitari | **G** |
| Separazione d | distanza in pixel × R√(ΔφΔμ) | cerchio massimo × R | **G** |
| Polarità leading | x del centroide maggiore | più a ovest nel piano tangente | **G** |
| Tilt e sin α | dx, dy in pixel | piano tangente al punto medio | **G** |
| Assegnazione del ciclo | dalla data | data + P1c nelle sovrapposizioni | **C** (ciclo) |
| Soglia di campo, massimo \|Br\|, regola di validità, formula di S_BL, regola Hale dato il ciclo | uguali | uguali | fisse |
| Pixel con WCS non finita esclusi | — | sì | **G** (nessun effetto atteso nelle mappe SHARP) |

Le 8 combinazioni (M, G, C) si calcolano sugli stessi 14195 record. Il fattore
G raggruppa per scelta tutte le differenze geometriche, compreso il raggio; un
sotto-fattoriale di G (latitudine/raggio contro centroidi-distanza-tilt) si
può aggiungere se G risulta rilevante.

## 3. Riproduzione esatta delle combinazioni estreme (test prima del fattoriale)

- (M = 1, G = legacy, C = data) deve riprodurre `measure_legacy`;
  (M = 33, G = v8.4, C = P1c) deve riprodurre `measure_v84`.
- **Riferimento indipendente:** i valori del catalogo P1 già scritto su disco
  (`leg_*` e colonne v8.4 di `P1_SBL_CATALOG_BY_HARP.csv`, commit `120f852`),
  non rigenerati dalla funzione nuova; e, per il caso di prova di Paolo, i
  valori di `measure_legacy` del commit `3947ee8`.
- **Tolleranze:** flag e classificazioni (valid_bl, quality_string,
  leading_sign, hale_sign, cycle, cycle_state, diagnostic_reason) **identici**;
  valori numerici con |Δ| ≤ 10⁻⁹ · max(|x|, scala) dove scala è un valore
  tipico della grandezza (1 Mx·cm per S_BL ~10³⁰, 1 grado per gli angoli),
  per assorbire solo l'arrotondamento della scrittura su CSV.
- Il test è automatico (`tests/`) e gira su tutti i 14195 record; il
  fattoriale si calcola solo se passa.

## 4. Analisi descrittive (in quest'ordine)

1. **Fattoriale** (§2–§3): per validità, flusso, separazione, tilt, Hale, S_BL;
   per HARP e sulle somme per CR ed emisfero. Effetti principali e interazioni
   (contrasti del disegno 2³), e per S_BL due campioni: (a) record validi in
   **tutte** le 8 combinazioni; (b) somme con la validità **propria** di ogni
   combinazione. Cambi di validità riportati a parte.
2. **Transizioni Hale:** denominatore esplicito (record primari validi in
   entrambi i metodi e con Hale definito); versi Hale → anti-Hale e
   anti-Hale → Hale; attribuzione dal fattoriale: un fattore se la
   classificazione dipende solo da quello, altrimenti "più fattori /
   interazione"; peso sulle somme di S_BL; diagnostiche di casi
   rappresentativi (mappe con maschere e centroidi dei due metodi), senza
   considerare corretta per definizione la classificazione nuova.
3. **Concentrazione e cancellazione:** contributo delle HARP con i maggiori
   |S_BL| (1%, 5%, 10%), positivi, negativi, somma netta e somma dei valori
   assoluti, per ciclo ed emisfero; somme senza le regioni estreme come sola
   sensibilità descrittiva.
4. **Primario contro controllo:** differenze appaiate di flusso, tilt,
   separazione, Hale e S_BL; distanza temporale, posizione sul disco, casi in
   cui i record coincidono (`role = both`).
5. **C1/C2 sul sottoinsieme comune:** le coppie BARD presenti in C1, C2
   controllo e C2 primario, con gli stessi criteri di qualità; nessuna
   attribuzione automatica all'evoluzione.

## 5. Materiali per l'articolo

6. Dizionario delle colonne (unità, convenzioni, flag, valori mancanti),
   selezione, copertura, esclusioni, provenienza e comandi di riproduzione;
   tabella di collegamento figure/tabelle → dati → commit.
7. Struttura dell'articolo: correzioni metodologiche, serie, confronto BARD
   al centro; quenching descrittivo e calibrazione fallita documentata.

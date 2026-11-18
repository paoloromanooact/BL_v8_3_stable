# Piccolo confronto MDI/HMI: risposta alla revisione di Claude

Revisione 2 del 18 novembre 2026. Nessun congelamento, campione, nuova query, FITS o risposta reale.
La geometria dell'intera impronta resta un **blocco aperto**, nonostante le correzioni del codice.

## 1. Dominio μ: che cosa consentono i metadati

Per SMARP e HMI gli schemi espongono LAT_MIN/MAX, LON_MIN/MAX, DSUN_OBS e RSUN_REF, ma nessuno di
questi campi è nei CSV acquisiti. NAXIS1/2 non sono keyword degli schemi. Il centro non garantisce il
dominio della maschera, NPIX non ne descrive la forma e le dimensioni non sono inferite da CRPIX.
Nessuna nuova query è stata fatta per colmare questa lacuna. Si mantiene μ ≥ 0,8 su tutta l'impronta;
non si adotta automaticamente il controllo sui soli pixel forti. Va chiusa la specifica dei metadati
aggiuntivi o rivisto esplicitamente il disegno prima del congelamento.

L'audit applica soltanto le condizioni già verificabili della nuova bozza: unicità G5 e G10,
QUALITY proposta, |ΔT_OBS| ≤ 360 s, centri nei limiti e stesso emisfero. Nessun ordinamento, estrazione
o vincolo di una componente per campione è eseguito. Gli stessi sistemi possono comparire in più
strati durante il transito. I numeri sono archi di record ripetuti, non regioni indipendenti.

| Strato | Archi con condizioni disponibili | Coppie distinte | Centri HMI con cosψ < 0,8 | Dominio intera impronta |
|---|---:|---:|---:|---|
| N_central | 877 | 42 | 0 | non valutabile |
| S_central | 390 | 20 | 3 | non valutabile |
| N_lateral | 880 | 48 | 26 | non valutabile |
| S_lateral | 455 | 24 | 53 | non valutabile |

cosψ include il B0 HMI salvato ma assume raggi paralleli: manca D/R per il μ finito. È solo un avviso
sul centro, non una certificazione o una bocciatura della maschera, che potrebbe non contenere il
centro geometrico. La frazione di confronti che si perderanno per strato **non è stimabile** da questi
file. Non riportare né zero perdite né un campione sicuramente disponibile.

## 2. R0 e NaN

R0 usa `measure_v84` congelata, senza cambiare P1. Il kernel rifiuta ancora pixel non finiti dentro
l'impronta; questo diventa un confronto non disponibile separato, non un mancato recupero del
riferimento P1. Due nuove prove sintetiche con NaN/Inf dimostrano che P1 può rimanere valido con un
pixel per polarità mentre il kernel rifiuta la patch. Nessuna imputazione o maschera comune a posteriori.
P1 non ha il filtro 20 pixel: è una selezione P2, esclusa da entrambi i rami di questo esperimento.

## 3. Differenze completate

`paired_differences` ora richiede e confronta Φ totale/positivo/negativo, latitudini e longitudini
avvolte dei tre centroidi, spostamenti sferici, dipoli, distanza e tilt. Conserva differenze firmate
ed assolute, tilt orientato e assiale distinti; non rende confrontabili record con quantità mancanti.
Le prove verificano 359°→1°, l'attraversamento opposto e l'assenza del centroide medio.

## 4. QUALITY × INTERVAL, senza attribuire prodotti alle patch

Tabella sul **full-disk 2010 già acquisito**, record accettati senza righe di bordo. Zeri espliciti
anche per INTERVAL=60. Qui «altri» raggruppa soltanto gli altri pattern QUALITY presenti: il CSV locale
conserva ogni pattern separato, senza scartarlo. Il conteggio non applica la proposta del campione.

| QUALITY full-disk | 60 s | 300 s | 30 s | mancante | totale |
|---|---:|---:|---:|---:|---:|
| 0x00000000 | 0 | 47 | 5 | 0 | 52 |
| 0x00000200 | 0 | 2293 | 1701 | 0 | 3994 |
| altri | 0 | 126 | 54 | 289 | 469 |

0x200 è presente con entrambi gli INTERVAL 30 e 300: non identifica univocamente il prodotto.
Il CSV include anche la sola finestra 2010-05-01 → 2010-10-29. SMARP non ha INTERVAL acquisito né un
link per-record verificato; nessun join per T_REC o somiglianza di QUALITY viene usato per attribuirlo.
La classificazione 60/300 dell'inventario resta intatta. Non è stimata alcuna RMS per questi record.

`parse_quality32` preserva il pattern per decimali signed/unsigned e stringhe esadecimali: −2147483648,
2147483648 e 0x80000000 diventano lo stesso valore, che la proposta esclude. Non rimuove bit o applica
una selezione. Missing, float e fuori intervallo sono errori espliciti. La convenzione è ora nel piano.

## 5. Sorgenti e segni reali

Tutte le 22 copie di fonti previste dalle ricevute sono presenti nella cartella persistente
`data/sharp/metadata_inventory_mdi/documentation_20261118/` e coincidono con gli SHA-256 registrati;
non si dipende da /tmp. Questo verifica le copie registrate, non ogni URL citato nei documenti.
I test dell'adattatore dovranno verificare segno LOS, osservatore SOHO/SDO, unità e tempi sulle
intestazioni reali. Sono ancora da scrivere, non sostituiti dalle prove dei versori su array.

## 6. Verifiche e consegna

Nuovi nuclei: **48 prove sintetiche** (27 originali più 21 casi della revisione). La suite completa
è superata: 108/108 (due avvisi attesi su correlazioni di input costanti), log locale; non è validazione scientifica dei nuovi confronti.
Codice diagnostico `scripts/mdi_overlap_metadata_review.py`: verifica gli input contro gli hash
nell'analisi precedente, riconcilia i totali e controlla l'integrità delle fonti persistenti.
Nessuna interpretazione fisica viene ricavata dai conteggi. Registro dell'inventario immutato.

Artefatti locali: `results/MDI_SMARP_INVENTORY_REVIEW/revision2_20261118/`, esclusi da Git:
`QUALITY_INTERVAL.csv`, `GEOMETRY_FIELDS.csv`, `STRATA_DIAGNOSTIC.csv`, `REVIEW_AUDIT.json` e log delle prove.
Sono diagnostiche non cieche richieste dal revisore, non un campione estratto o un nuovo risultato sul quenching.

**Da rivedere ancora:** il punto 1 rimane aperto per mancanza dei valori geometrici, mentre i punti 2–3
sono specificati e coperti dalle nuove prove. L'adattatore reale e la specifica dei link restano futuri.
Nessun congelamento, query, selezione, mappe, simulazioni o push. T3/T5 e protocolli storici invariati.

## Hash dell'audit locale

- `GEOMETRY_FIELDS.csv`: `035a8efec25b33ef2c0eadc7ea6af8977a5a731cf675179a8de360375fae9dbc`
- `QUALITY_INTERVAL.csv`: `a7d6da6d6672845c64fedfab329f3239dbad297f9c2ab5c58447b2f0125b89eb`
- `REVIEW_AUDIT.json`: `f169ceeb9bede696dff977192dcc2b1df24fddf466e157e9f10f9db67d4749c8`
- `STRATA_DIAGNOSTIC.csv`: `efa442f3f1c9cc1b890c42c9fd3d94c296ebe1dfec13d2897f483baef44f0288`

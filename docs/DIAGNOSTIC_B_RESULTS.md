# Risultati del controllo diagnostico B (oracolo: parametri temporali veri)

Data: 2026-11-09. **Sviluppo diagnostico, non validazione e non verdetto**; nessun
risultato, conteggio storico o decisione di P2/P2d/P2e cambia. Piano registrato prima del
codice: `docs/DIAGNOSTIC_B_PLAN.md` (commit `7d40b9b`, SHA-256 `2653a955…`); script
`python/sharpbl/diag_b_oracle.py` (commit `d171cee`, eseguito ad albero pulito, terminato
alle 12:28). Tabelle: `results/DIAGNOSTIC/B_SUMMARY.csv`, `B_CHECKS.csv`, `B_RAW.csv.gz`.

## 1. Controlli obbligatori (piano §4)

1. Con i parametri stimati il codice di B riproduce i verdetti registrati della validazione
   P2e: 200 confronti (25 cataloghi × 4 scenari × 2 test), 0 differenze.
2. I parametri della simulazione oracolo sono quelli veri in tutti i 15 994 casi applicabili.

## 2. Risultati (2000 cataloghi per scenario e test, stessi cataloghi e stessi semi di P2e)

Frequenze tra gli applicabili, con errore binomiale; limite di Clopper–Pearson (CP)
unilaterale al 95% sui 2000 cataloghi; confronto appaiato con P2e originale.

| Scenario, test | Non applicabili | P2e originale | Oracolo (B) | CP oracolo | Falsi in entrambi / solo P2e / solo oracolo | p oracolo di A | (B − A)/se |
|---|---|---|---|---|---|---|---|
| V1 T3 | 0 | 3,45% (69) | 3,50% (70) ± 0,41 | 4,25% | 59 / 10 / 11 | 2,73% | +1,9 |
| V1 T5 | 0 | 3,30% (66) | 3,35% (67) ± 0,40 | 4,09% | 52 / 14 / 15 | 2,72% | +1,6 |
| V2 T3 | 1 | 4,00% (80) | 3,20% (64) ± 0,39 | 3,93% | 49 / 31 / 15 | 2,60% | +1,5 |
| V2 T5 | 2 | 4,55% (91) | 3,20% (64) ± 0,39 | 3,93% | 46 / 45 / 18 | 2,59% | +1,5 |
| V3 T3 | 0 | 4,65% (93) | 3,00% (60) ± 0,38 | 3,71% | 47 / 46 / 13 | 2,57% | +1,1 |
| V3 T5 | 3 | 4,46% (89) | 3,05% (61) ± 0,39 | 3,76% | 40 / 49 / 21 | 2,57% | +1,3 |
| V4 T3 | 0 | 2,90% (58) | 3,00% (60) ± 0,38 | 3,71% | 41 / 17 / 19 | 2,52% | +1,3 |
| V4 T5 | 0 | 3,10% (62) | 3,10% (62) ± 0,39 | 3,82% | 36 / 26 / 26 | 2,52% | +1,5 |

I falsi verdetti oracolo sono ripartiti tra i due versi senza asimmetria evidente.

**Verdetti cambiati tra P2e e oracolo (stessi cataloghi, stessi semi).** Aggiunto dopo la
prima stesura; conteggi da `B_RAW.csv.gz` e `P2E_VALIDATION_RAW.csv.gz`. "nd" = non deciso.
Nessun catalogo passa direttamente da "quenching supportato" a "segno opposto" o viceversa.

| Scenario, test | Verdetti cambiati | falso → nd | nd → falso | p esatto (McNemar, discordanti sui falsi) |
|---|---|---|---|---|
| V1 T3 | 21 | 10 | 11 | 1,00 |
| V1 T5 | 29 | 14 | 15 | 1,00 |
| V2 T3 | 46 | 31 | 15 | 0,026 |
| V2 T5 | 63 | 45 | 18 | 0,0009 |
| V3 T3 | 59 | 46 | 13 | < 0,0001 |
| V3 T5 | 70 | 49 | 21 | 0,001 |
| V4 T3 | 36 | 17 | 19 | 0,87 |
| V4 T5 | 52 | 26 | 26 | 1,00 |

Il p esatto è descrittivo (non fa parte delle interpretazioni registrate): misura se i
cataloghi che cambiano esito si spostano in un verso preferito. In V2 e V3 i parametri veri
tolgono più falsi verdetti di quanti ne aggiungano; in V1 e V4 i cambiamenti sono
bilanciati, cioè i parametri cambiano quali cataloghi danno un falso verdetto ma non quanti.

## 3. Lettura secondo le interpretazioni registrate (piano §5)

- **J1:** soddisfatta in **V2 e V3**: con i parametri temporali veri la frequenza scende da
  4,0–4,7% a 3,0–3,2%, entro 2 errori binomiali dal p oracolo di A e con limite CP ≤ 4%.
  L'eccesso di P2e in questi scenari è coerente con la stima dei parametri temporali.
  **Non soddisfatta in V1:** limite CP 4,25% (T3) e 4,09% (T5).
- **J2:** vale per **V1**. Con i parametri veri la frequenza non cambia (3,50% contro 3,45%;
  3,35% contro 3,30%) e i falsi verdetti sono quasi gli stessi cataloghi (59 e 52 in
  comune). In V1 la stima dei parametri temporali non spiega l'eccesso: contribuiscono altri
  aspetti della procedura, non identificati da B.
- **J3:** coerente con H2. Oracolo V2 3,20% contro V4 3,00–3,10%: differenza 0,1–0,2
  punti, entro 2 errori binomiali combinati (circa 1,1 punti). La differenza tra V2 e V4 in
  P2e (4,0–4,6% contro 2,9–3,1%) scompare con i parametri veri.
- **J4:** in tutti gli scenari la frequenza oracolo è entro 2 errori binomiali dal p
  oracolo di A, quindi le approssimazioni di A bastano secondo il criterio registrato.
  Descrittivamente però la frequenza oracolo **supera** il p di A in tutti gli 8 casi
  (+1,1 / +1,9 errori).
- **J5:** nessuna di queste condizioni stabilisce una causa.

**Precisazioni.**
- Rispettare il limite di Clopper–Pearson del 4% **non** dimostra che il livello vero sia il
  2,5% nominale: il criterio certifica solo che, negli scenari verificati, il livello vero non
  supera il 4% (P2d §6). Le frequenze oracolo (3,0–3,5%) sono sopra il 2,5%.
- La scomparsa della differenza tra V2 e V4 con i parametri veri è **coerente** con H2, ma non
  ne dimostra il meccanismo (il rumore di campionamento delle celle minore in V4 non è stato
  misurato direttamente).

## 4. Che cosa resta aperto

- **Eccesso residuo con i parametri veri.** In V1–V4 la frequenza oracolo è 3,0–3,5%,
  sopra l'obiettivo nominale del 2,5%. È compatibile con l'osservazione post hoc di A sulla
  componente individuale simulata circa il 15% più piccola del vero
  (`docs/DIAGNOSTIC_A_RESULTS.md` §4), ma B non la verifica: resta un'ipotesi da controllare
  separatamente, con un piano proprio.
- **V1.** È l'unico scenario in cui l'eccesso non dipende dai parametri temporali e in cui
  anche l'oracolo supera il limite di accettazione. Va spiegato prima di un eventuale P2f.
- **V5, V6** (modelli errati) e la regola di non applicabilità non sono toccati da B.

## 5. Sintesi

Entro il modello degli scenari, la sottostima dei parametri temporali rende conto della
maggior parte dell'eccesso in V2 e V3 e della differenza tra V2 e V4. Non rende conto di V1,
e lascia in tutti gli scenari un eccesso residuo di circa 0,5–1 punto sopra il 2,5%. La
diagnosi del punto 4 resta quindi aperta su V1 e sulla componente individuale.

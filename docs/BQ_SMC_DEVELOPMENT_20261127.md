# BQ-HMI: punteggio predittivo sequenziale (SMC), media su ψ, quadratura L2, esportazione (sviluppo, 27 novembre)

Claude, 27 novembre 2026. **Solo sintetici**: risposte sintetiche sul disegno reale T3 (2485 record, solo metadati) o su
disegni sintetici; nessun tilt osservato, nessun fit reale, protocollo BQ in bozza (rev. 4 con §6ter). Pilastro:
quenching. Decisioni Codex richiamate dove servono; le misure sono di sviluppo, non validazioni.

## 1. Perché uno schema sequenziale

Lo stimatore diretto della densità predittiva del blocco (`bq_cvpred`, latenti estratti) degenera al crescere del
blocco: ESS dei pesi 277/12/2,6/1,0 per 7/45/111/197 record in L1, con distorsione fino a −8 nel log e MCSE dichiarato
sottostimato (`reviews/BQ_CVPRED_20261127/`). Anche integrare i latenti e campionare le precisioni L2 dalla prior
degenera (ESS 58 già con 7 record). I blocchi HMI arrivano a 395 record.

## 2. Prototipo SMC a ψ fisso (`python/sharpbl/bq_smc.py`, bozza §6ter.10)

- Stato gaussiano esatto del blocco dal sistema del training; record in ordine; log della predittiva media con i pesi
  del prefisso prima del ricampionamento; Kalman per particella; ringiovanimento con Gibbs a dati aumentati.
- Selftest 8/8 (`reviews/BQ_SMC_20261127/`):
  - stato del blocco uguale al condizionale denso (≤ 3e-15, con una famiglia condivisa);
  - L1 uguale al valore analitico (1e-10; 1,4e-12 sul blocco T3 di 395 record);
  - L2 su 2 record uguale alla somma esatta sui nodi;
  - L3 su 2 record correlati uguale all'enumerazione;
  - ringiovanimento forzato uguale alle corse normali (verifica con 24 repliche e 30000 particelle).
- **Revisione integrata** dopo il benchmark (`python/sharpbl/bq_smc.py` 602e36f6…, selftest 8/8 sul repository,
  `reviews/BQ_SMC_20261127/bq_smc_selftest_integrated.log`):
  - L2 con la griglia in log λ a 200 punti;
  - L3 con una sola routine `images()` per punteggio, proposta e ringiovanimento, con T/S globale.
  Il benchmark del §5 usa ancora la versione precedente (2b29d682…, Gauss–Laguerre a 64 nodi in L2).

## 3. Quadratura L2 (`reviews/BQ_L2_QUADRATURE_20261127/`, `reviews/BQ_L2_RESOLUTION_20261127/`)

- Predittiva di un record con riferimento adattivo (uguale alla t4 esatta entro 4e-15).
  - Gauss–Laguerre generalizzata a 64 nodi: errore del log +6e-4 / +0,031 / −1,1 / −26 a 5 / 10 / 20 / 50 unità di
    scala; con 512 nodi va in overflow.
  - Griglia in log λ a 200 punti: errore massimo 3,6e-15.
- Sullo stesso blocco, stessa risposta, stessi semi del benchmark (griglia − 64 nodi, 1000 particelle):

  | Record | Differenza appaiata | SE | sd fra repliche griglia / 64 nodi | Ricampionamenti medi |
  |---|---|---|---|---|
  | 102 | −0,0188 | 0,0010 (8 coppie) | 0,013 / 0,015 | 0 / 0 |
  | 236 | −0,0190 | 0,0027 (8 coppie) | 0,016 / 0,021 | 0 / 0 |
  | 395 | −0,259 | 0,035 (8 coppie; con 5 coppie, parziale: −0,230 ± 0,051) | 0,073 / 0,068 | 4 / 4,1 |

  L'errore di quadratura a 64 nodi è sistematico e condiviso dalle repliche: la dispersione fra repliche misura
  un'altra componente. Sul blocco di 395 record vale circa 0,23 nel log, più del doppio della dispersione MC e sopra la
  soglia provvisoria 0,1: i 64 nodi non sono accettabili. A 395 record anche la dispersione fra repliche con 1000
  particelle (~0,07) è vicina alla soglia.
- **Controllo 200 contro 400 punti** (blocco di 395 record, 4 coppie, `reviews/BQ_L2_GRID_REFINE_20261127/`): differenza
  −0,026 ± 0,080, non distinguibile dal rumore MC. È un controllo debole a livello di blocco: cambiando i nodi cambia
  anche la sequenza delle estrazioni, quindi l'appaiamento non cancella il rumore (sd della differenza 0,16). Il
  riferimento forte resta il controllo per record (errore ≤ 3,6·10⁻¹⁵ con 200 punti fino a 50 unità di scala).
- **Convenzioni (Codex, 27 novembre).**
  - Il valore a 5 coppie sul blocco di 395 record è **parziale**: stima e SE si aggiornano con tutte e 8 le coppie.
  - La sensibilità alla quadratura (differenza appaiata fra regole) resta distinta dal MCSE (dispersione fra
    repliche).
  - Repliche SMC indipendenti si combinano facendo la media delle **stime di densità** predittiva e poi il logaritmo
    (log-mean-exp), non la media dei log-punteggi; ogni stima SMC della densità è non distorta, il suo log no.
  - La scelta fra più particelle e più repliche mediate si decide sul blocco grande confrontando precisione e costo,
    con le 8 coppie complete.

## 4. Media sulle estrazioni di ψ in L1 (`reviews/BQ_PSI_AVERAGE_20261127/`)

400 estrazioni (4 catene slice × 100, una ogni 5) dal posteriore del training; termine analitico per estrazione. Tre
grandezze distinte:
- **ESS dei pesi**: riguarda la media su ψ;
- **ESS bulk del termine**: riguarda le catene (sotto 400 il gate non è superato per quella quantità);
- **MCSE del log-punteggio**: medie a blocchi dentro le catene.

| Record | Punteggio | MCSE | ESS dei pesi | ESS bulk del termine | R̂ del termine |
|---|---|---|---|---|---|
| 22 | −111,43 | 0,016 | 373 | 334 | 1,008 |
| 102 | −475,59 | 0,018 | 354 | 320 | 0,995 |
| 236 | −1130,74 | 0,037 | 296 | 294 | 1,000 |
| 395 | −1882,60 | 0,049 | 192 | 394 | 1,000 |

- MCSE stabile per blocchi da 4 a 25 estrazioni, vicino al valore iid (`MCSE_BY_BATCH_LENGTH.csv`).
- Riconteggio Codex dai 1600 termini salvati: tutti i 24 MCSE riprodotti; 0,050 stimando la varianza catena per catena.
- Sotto la soglia esplorativa 0,1 in L1. Da verificare in L2/L3.

## 5. Benchmark SMC a ψ fisso (`reviews/BQ_SMC_STABILITY_20261127/`)

8 repliche × 1000 particelle per likelihood e blocco; risposta sintetica sul disegno T3; ψ fisso; versione 2b29d682…
(L2 a 64 nodi). Blocchi 22/102/236 in `reviews/BQ_SMC_STABILITY_20261127/` (corsa fermata durante il blocco 395 per
contesa di memoria; META «running»), blocco 395 in `reviews/BQ_SMC_STABILITY_395_20261127/` (corsa da sola, stessi semi
canonici; ha riprodotto bit per bit le 6 righe già calcolate; sorgenti invariati).

| Likelihood | Record | sd fra repliche | s per replica | Ricampionamenti medi | T/S max |
|---|---|---|---|---|---|
| L1 | 22 / 102 / 236 / 395 | = analitico (Kalman) | 0,001–0,03 | — | — |
| L2 | 22 / 102 / 236 / 395 | 0,003 / 0,015 / 0,020 / 0,068 | 0,1 / 1,3 / 11 / 138 | 0 / 0 / 0 / 4,1 | — |
| L3 | 22 / 102 / 236 / 395 | 0,002 / 0,004 / 0,005 / 0,010 | 3,8 / 18 / 49 / 88 | 0 / 0 / 0 / 0 | ≤ 9,4·10⁻¹⁴ |

- Con una replica da 1000 particelle il MCSE resta sotto 0,1 fino a 395 record (L2 0,068, L3 0,010), a ψ fisso; L2 è
  la parte più variabile e costosa sul blocco grande.
- La scelta fra più particelle e repliche mediate (log-mean-exp delle densità) e l'accettazione dello schema spettano a
  Codex; manca l'integrazione sulle estrazioni di ψ in L2/L3.
- Lezione operativa: due corse SMC contemporanee hanno rallentato ciascuna di 3–10 volte (banda di memoria); da allora
  coda sequenziale e numero di processi scelto per resa totale (`scripts/bq_concurrency_probe.py`).

## 6. Diagnostica ed esportazione

- **`python/sharpbl/bq_diag.py`** (12/12):
  - R̂ rank bulk e ripiegato, ESS bulk e di coda;
  - almeno 4 catene originali;
  - R̂ NaN con stato esplicito quando una componente non è valutabile.
- **`python/sharpbl/bq_export.py`** (4/4):
  - pacchetti `BQ_SYNTHETIC_L1_POINTWISE_V1`;
  - il verificatore indipendente di Codex accetta i pacchetti da catene slice reali (errore massimo 4e-11) e rifiuta un
    pacchetto manomesso.

## 7. Studi sintetici (`docs/BQ_STUDY_DESIGN_DRAFT_20261127.md`)

- Regola `threshold_uncertain` approvata, con estremi inclusi.
- Fasi decise da Codex.
- Pilota di dimensionamento `scripts/bq_sizing_pilot.py` in coda dopo il benchmark; la lunghezza delle catene si
  fissa sui suoi risultati.

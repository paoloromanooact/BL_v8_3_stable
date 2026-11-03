# Informazioni già viste prima del congelamento di P1e, P2c e P3 (2026-11-03, aggiornato ~12:55)

Elenco richiamato dai protocolli P1e, P2c e P3. Tutto ciò che non è in
questo elenco non era stato calcolato o guardato.

1. **Caso di prova di Paolo** (2024-05-08 03:12 TAI, 13 HARP): metodi v8.3 e
   v8.4, tabella `output/test_20240508_compare.csv`.
2. **Metadati SHARP di tutte le HARP** (2010-05 → 2026-09): posizioni,
   flusso USFLUX, QUALITY, numero NOAA; conteggi per anno; volume stimato.
3. **Regola del ciclo**: tabella `results/P1/CYCLE_BOUNDARY_FITS.csv` (solo
   latitudini dai metadati).
4. **Serie P1 parziale, prima prova** (926 record, T_REC 2010-05-01 →
   2011-10-04): catalogo, controlli di P1 §8, figure (diagramma a farfalla
   colorato per segno di D*, somme per CR di S_BL e D_bal con D_bal cumulato,
   confronto v8.3/v8.4 con differenze di tilt e conteggi di cambi Hale e
   validità).
5. **Serie P1 parziale, seconda prova** (2323 record, T_REC 2010-05-01 →
   2013-01-22): stampati solo i controlli (centroidi contro JSOC, Φ/USFLUX,
   frazioni valide, stati del ciclo, conteggi P1d per famiglia, frazione di
   flusso da ricomparse per anno 2010–2013, statistiche di evoluzione
   primario/controllo: Δ tilt, rapporto S_BL, stesso segno di D*, stesso
   hale_sign). Figure non rigenerate.
6. **Diagnostica delle ricomparse su tutte le HARP** (solo metadati, posizioni
   e tempi, 2010–2026): regola P1d 45% di HARP segnate contro 19% con
   longitudini casuali; con criterio del lembo e finestre ±5°/±10°, 11% contro
   3%. Le finestre ±3°/±6° di P1e **non** sono state provate.
7. **P2 e P2b** eseguiti solo su cataloghi sintetici (attività SILSO vera;
   tilt, flussi e dipolo sintetici): test e calibrazione di P2 (falsi
   positivi T3 1/40, T5 2/40; copertura IC95 37/40). Una prima esecuzione
   della calibrazione di P2b §4 (40 cataloghi per ρ) è terminata ma i suoi
   risultati non sono stati letti; è stata sostituita da quella con copertura
   ed errore Monte Carlo (100 per ρ), in esecuzione.
8. **BARD** (Harvard Dataverse doi:10.7910/DVN/QEMSZ2): intestazioni dei file
   HMI e MDI, copertura (HMI 1457 BMR 2010–2016; MDI 2471 BMR 1996–2011, 90
   dopo 2010-05), intervallo delle longitudini (±180°), e la prima riga del
   file HMI calcolata a mano per capire la convenzione del tilt. Nessun
   abbinamento con le nostre regioni.
9. **Verifica di P1e sui metadati** (solo posizioni e tempi): 6,2% di
   candidate ricomparse contro 1,2% nel controllo casuale; tabella per anno.
10. **Verifica delle convenzioni BARD** (P3 §2): versione, MD5 dei file
    originali, direzione e riferimento delle longitudini, relazione tra
    `Tilt_rel` e la nostra convenzione, significato della colonna `Hale`
    (polarità leading attesa nel ciclo 24, accordo 100%; tutte le regioni
    assegnate al ciclo 24). Nessun abbinamento con le nostre regioni.

Dalle 12:33 circa l'aggiornamento orario della serie parziale è sospeso: il
download prosegue, ma nessun nuovo risultato parziale viene consultato fino
al congelamento.

# Controlli indipendenti preparatori del pilota MDI — 23 novembre 2026

Script: scripts/mdi_tilt_pilot_contract_checks.py. Non è un selettore né una pipeline di misura.
Fornisce oracoli indipendenti da confrontare con il futuro codice di Claude; non ne certifica un'implementazione
che ancora non esiste. Nessun download, array magnetico, tilt reale o selezione del pilota.

Comandi:

```bash
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_tilt_pilot_contract_checks.py --selftest
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_tilt_pilot_contract_checks.py --metadata
```

## Risultati sintetici

15/15 contratti numerici superati. Enumerazione esatta, senza Monte Carlo, di piccoli campioni a due fasi:
frequenze marginali pi1=n1/N e pi2=n2/N, totale Horvitz–Thompson non distorto, coorti insufficienti e vuote.
Esempio di M1 sovracampionata: media non pesata del campione 0,5 contro resa di popolazione 1/3;
con i pesi campionari corretti il totale atteso torna a quello della popolazione.

Oracoli geometrici: estremi dell'asse CT, longitudine, sinlat, somma delle aree uguale a 4*pi*R_sun^2,
finestra al bordo che richiede la rotazione cronologicamente adiacente anziché un riavvolgimento della stessa
mappa, CR mancante, spareggio per N. Convenzioni di angoli con entrambi i riavvolgimenti e latitudine zero.
Sono riferimenti per test di segno/scala, non nuove misure o test statistici.

## Metadati reali

- Verificati gli estremi CT ricostruiti in tutte le 193 righe dell'audit contro LON_FRST/LON_LAST.
- La conversione a periodo medio dà CT(T_ROT)-CARRTIME tra -1,3733 e +2,6625 gradi.
- La ricostruzione con L0 di Meeus ed effemeridi dà scarto massimo 0,01283 gradi sui medesimi T_ROT.
- Su 29280 righe gDPD nel periodo e nei tagli preliminari area/latitudine: nessun N differente fra le due
  conversioni. Sono giorni candidati, non gruppi isolati selezionati o componenti del pilota.
- L'errore angolare del periodo medio non è uno spostamento di 26 pixel della finestra: il centro della finestra
  usa la longitudine DPD; CT(t) serve a scegliere N. Non va però presentato come tempo/effemeride esatto.
- Astropy segnala un orario TAI al limite del giorno (secondi pari a 60) fra i metadati, normalizzato dal parser.
  Il futuro lettore deve coprire anche questa rappresentazione; non scartare silenziosamente la mappa.

Non è stato eseguito il controllo di hash di tutti i FITS da 193 mappe in questa fase: il precedente audit
ha già registrato i loro SHA. Il controllo qui usa i metadati conservati e i gDPD, non legge i pixel.

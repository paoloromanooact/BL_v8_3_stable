# MDI full-disk — controlli geometrici indipendenti e passaggio a Claude

Lavoro Codex separato dall'acquisizione e dal riconteggio dei metadati di Claude. Nessuna rete,
lettura di metadati L2 in corso o misura su FITS reali. La catena HMI/MWO e il codice produttivo restano invariati.

Script: `scripts/mdi_fd_geometry_oracle.py`.

```bash
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_fd_geometry_oracle.py --selftest
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_fd_geometry_oracle.py --check-adapter
```

Il primo comando controlla il riferimento indipendente. Il secondo confronta l'adattatore esistente: exit 1
significa discrepanze nei controlli, non errore di infrastruttura. Non chiamano JSOC.

## Costruzione indipendente

- Partenza da punti noti sulla sfera, proiettati in avanti su una base cartesiana osservatore/ovest/nord.
  Si sceglie CRPIX per collocare il punto in un pixel noto e si confronta l'inversa dell'adattatore.
- 324 configurazioni: B0 = −7,25/0/+7,25 gradi; CROTA2 = −31/0/+27/180 gradi;
  scale (2,2), (−2,2), (2,3) arcsec; latitudini −25/0/+25 gradi e CMD −25/0/+25 gradi.
  L0=359 gradi include il taglio 0/360; non si usa il modulo geometrico produttivo per generare i punti.
- Area della sfera verificata con il Jacobiano numerico delle derivate della costruzione cartesiana:
  R_sun^2 * |dv/di × dv/dj|. Controlla indipendentemente il prodotto |CDELT1*CDELT2|/mu,
  anche per scale non quadrate e con segno negativo.
- Due bipoli sintetici, a nord e sud, con campo radiale noto e B_LOS=B_r*mu. Centroidi, flussi e tilt attesi
  sono ricostruiti con algebra vettoriale propria. Si controllano inversione del campo, pixel mancanti sotto/sopra
  il 5%, una finestra che attraversa mu=0,8 e un FITS int16 sintetico con BSCALE/BZERO/BLANK.
- Un controllo di sensibilità distingue l'omissione e la doppia applicazione di LOS/mu: nel caso sintetico
  il flusso positivo diventerebbe rispettivamente 0,9003 e 1,1107 del riferimento corretto.

## Esito sulla versione esaminata

Adattatore `scripts/mdi_fd_adapter.py`, ultimo cambiamento a267c1b,
SHA-256 `51b34818621f2500086f78f2916bb80321b5e50847a99e2b6e169185884e5177`.

- Riferimento indipendente: **4/4**; errore massimo angolare del roundtrip circa 5,7e−14 gradi;
  errore relativo massimo del Jacobiano circa 6,1e−12.
- Confronto complessivo con adattatore: **15/18**, comprendendo i quattro controlli del riferimento.
- Le 324 registrazioni sintetiche coincidono. Per i due bipoli, flussi corretti e tilt entro circa 2e−13 gradi;
  inversione del campo e guardia mu dell'intera finestra funzionano. Scalatura FITS e BLANK funzionano nel file sintetico.
- I tre casi negativi sono quelli già segnalati nel blocco C di b49fcba:
  1. area dei pixel rettangolari: con CDELT1=2 e CDELT2=3 il codice dà 2/3 del Jacobiano;
  2. QUALITY assente accettata come zero;
  3. QUALITY esplicita `'0x00000000'` rifiutata con ValueError.

Questi casi devono essere corretti da Claude nel proprio adattatore. Gli oracoli sono pronti per la verifica
della prossima revisione: non occorre modificare il codice produttivo per eseguire le prove.

## Limiti e seguito

Questo è un controllo del **modello ortografico previsto dal protocollo**, condizionato a keyword corrette,
unità e convenzioni. Non dimostra da solo la registrazione di ogni prodotto reale, la calibrazione del campo,
la sua convenzione di segno documentale o l'equivalenza MDI/MWO/HMI. L'inversione sintetica prova conservazione
del segno e della polarità, non verifica quale segno fisico abbia il dato JSOC reale.

Il caso QUALITY=0x200 è verificato come rifiuto nella regola originale. Un eventuale emendamento richiederà
un'aspettativa di ammissibilità esplicita legata a quel testo; non si allargano qui i valori ammessi.

Per Claude: completare adattatore e misura L2/riconteggio su file propri; usare questi riferimenti per la revisione.
Downloader (blocco B) e riconteggio dei metadati restano lavori distinti. Nessun nuovo test di quenching,
calcolo Q4, serie BL combinata o simulazione lunga è stato avviato.

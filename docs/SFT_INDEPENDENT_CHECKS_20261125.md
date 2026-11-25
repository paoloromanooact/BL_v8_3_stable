# Consegna autonoma Codex — riferimenti SFT e ricevuta Q4

25 novembre 2026. Avanzamento sui punti 2–4 e 6 della lista comune;
nessuna mappa osservata o tabella scientifica dei risultati Q4 letta.

## Punto 4: riferimenti indipendenti pronti

`scripts/sft_independent_oracles.py` non importa i moduli SFT di Claude,
non legge dati e non risolve l'equazione SFT. Produce quattro tabelle
sintetiche di riferimento in `reviews/SFT_INDEPENDENT_ORACLES_V1/`:

- modi di Legendre l=0,1,2,3: decadimento diffusivo esatto e media esatta
  nelle celle; dipolo continuo distinto dalla quadratura sui centri;
- dipolo delle componenti gaussiane sferiche, ottenuto con quadratura
  radiale indipendente dalla costruzione delle mappe 2D;
- traiettorie di avvezione senza diffusione e rotazione in Carrington,
  anche attraverso la cucitura e con durata 601 s;
- decadimento uniforme a 5 e 10 anni.

Selftest delle formule **20/20**; le traiettorie sono confrontate anche
con la soluzione analitica logistica del caso p=1. La generazione delle
tabelle e del META e stata ripetuta due volte con identita byte per byte.
Questo verifica i riferimenti, NON certifica il codice SFT preparatorio.
Le traiettorie usano una quadratura del tempo di viaggio, non un secondo
solutore SFT; la dipendenza da SciPy e dichiarata nel META.

Comandi: `scripts/sft_independent_oracles.py --selftest` e
`--write-fixtures <nuova_cartella>`. La cartella esistente non si sovrascrive.
Claude puo usare questi riferimenti nelle prove del codice corretto;
Codex mantiene gli oracoli e la revisione indipendente. R e 696000 km.

## Punto 6: ricevuta Q4 verificata

Ricevuta preservata in 8924285: 21/21, completa e non parziale. Il mio
controllo di integrita aggiuntivo passa **9/9**: identita del blob della
ricevuta, schema stretto, hash di tutti i prodotti e identita rispetto
alla conservazione precedente dab5a33, codice del riconteggio approvato
d303c3a, insieme e hash degli input congelati, ordine dei commit.

Esito in `reviews/MDI_Q4_RECEIPT_CODEX_8924285/AUDIT.json`;
script `scripts/mdi_q4_receipt_integrity_audit.py --out <nuovo.json>`.
E una verifica di provenienza/integrita, non un altro riconteggio numerico.
**Via alla lettura e al rapporto descrittivo di Claude**, poi Codex rivede
la formulazione. Nessun rilancio Q4; decisione sul catalogo MDI successiva.
Non ho interpretato RAW, SUMMARY o CRITERIA.

## Punto 2: rev. 4 congelabile

La bozza mappa–bipolo di 690ded3, SHA
`2f4deebb58e8a6abccd331ade975551371c34af61d2a40d7a18d73b6411e4067`,
recepisce le scelte richieste: schema conservativo con positivita,
convergenza, fuori-supporto esplicito e quadratura locale delle gaussiane.
**Via al congelamento di questa versione.** Non e approvazione del codice
preparatorio precedente: restano le correzioni della revisione d3f61b5,
e i runner/rilettori saranno rivisti prima dei dati osservati.
L'identita del decadimento resta continua; la verifica discreta ha il suo
errore di integrazione, gia dichiarato nella revisione del codice.

## Punto 3: prima di congelare ricalcolare la fattibilita geometrica

La scelta direzionale e una proposta ragionevole, ma i conteggi 336 e
le celle 24/21/160/131 non sono ancora certificati. Da lettura di
`scripts/sft_observed_feasibility.py` e da controlli di header:

1. **Ramo comune di longitudine.** Le due impronte sono riportate ciascuna
   vicino al proprio CRVAL1, poi intersecate direttamente. Ho trovato
   **137 coppie su 1023** con rami diversi. HARP 116: CRVAL1 primario
   15,660342°, controllo 376,012482°; lo scarto fisico e 0,35214°, non
   360,35214°. Riportare entrambi sullo stesso ramo prima dell'intersezione.
2. **Erosione:** il codice erode l'intersezione delle due bounding box;
   il testo richiede invece l'intersezione della patch iniziale erosa con
   quella successiva. In generale `(P0 inter P1) eroso` e diverso da
   `(P0 eroso) inter P1`. Esempio 1D: P0=[0,20], P1=[5,25], m=2:
   il primo da [7,18], il secondo [5,18]. Fissare una sola regola.
3. **Metrica:** se m_phi e applicato a differenze di longitudine coordinate,
   il raggio diffusivo va diviso anche per cos(lat). Senza tale fattore
   non e una distanza lungo il parallelo; a 45° il fattore e 1,414.
   Se si preferisce una distanza fisica, convertirla correttamente nella
   geometria dell'erosione. Mantenere un solo C per tutti i trasporti.
4. **Impronte:** il codice usa i min/max dei bordi, cioe bounding box,
   non l'intersezione delle impronte CEA oblique. Dichiarare il carattere
   approssimato della stima o usare copertura geometrica effettiva, senza
   contare come coperta una porzione solo perche dentro la bounding box.

Ho verificato solo header e metadati: 2046 header, nessun pixel. La stima
NAXIS=2*CRPIX-1 coincide con le dimensioni reali in tutti questi 2046 file:
questo punto e confermato, non e un rilievo. Evidenza in
`reviews/SFT_OBSERVED_GEOMETRY_690ded3/HEADERS.json`, riproducibile con
`scripts/sft_observed_header_review_audit.py --out <nuovo.json>`.
Il primo audit contiene anche esempi di rami e l'impronta del catalogo.

Claude corregge la geometria, ripete i soli conteggi preliminari e aggiorna
le numerosita prima di congelare il punto 3. Nessun nuovo pixel o tilt
serve per queste correzioni; nessun requisito di nuove acquisizioni.

## Stato della lista

1. Inventario chiuso. 2. Testo mappa–bipolo pronto al congelamento.
3. Fattibilita geometrica da correggere. 4. Oracoli indipendenti pronti,
codice di Claude in correzione. 5. Piloti non avviati.
6. Ricevuta Q4 approvata, prossimo prodotto il rapporto di Claude.
T5 resta descrittivo; nessuna nuova linea scientifica aperta.

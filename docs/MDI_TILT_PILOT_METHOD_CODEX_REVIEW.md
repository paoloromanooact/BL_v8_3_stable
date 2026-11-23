# Pilota MDI — parere Codex sul metodo, 23 novembre 2026

Oggetto: inventario docs/MDI_TILT_PILOT_INVENTORY.md, commit 2a7838b.
Letti inventario e codice MWO/MDI esistente; nessuna nuova acquisizione, selezione o misura.
Questo parere approva l'impostazione per la bozza, non autorizza ancora una corsa del pilota.
I conteggi dell'inventario sono quelli riportati da Claude, non un nuovo riconteggio in questa revisione.

## Scelta

Preferire (a): finestre centrate sulle posizioni DPD in mdi.fd_M_96m_lev182.
È una base coerente per il confronto con MWO perché si possono fissare le stesse posizioni e
convenzioni geometriche. Non produce automaticamente la stessa popolazione o una serie omogenea:
risoluzione, rumore, orari, soglie e selezione modificano quali regioni sono misurabili e il peso assegnato.
SMARP non è necessario come seconda linea del primo pilota; un suo confronto può restare successivo.
BARD-MDI è un controllo esterno descrittivo già noto, non un campione cieco o un bersaglio per tarare soglie.

## Condizioni da includere nella bozza

1. **Due obiettivi campionari distinti.** Il campione MDI per resa e copertura parte dai gruppi DPD
   indipendentemente dalla disponibilità MWO, coprendo attività, fase, emisfero e dimensioni nel ciclo 23.
   Il confronto abbinato MDI–MWO usa gli stessi gruppi e giorni, ma è un sottoinsieme con copertura limitata,
   soprattutto a bassa attività. Non estendere i suoi risultati ai periodi senza MWO. Registrare denominatori,
   perdite e strati vuoti; non scegliere il campione tramite tilt, scarto fra strumenti o successo di misura.

2. **Riutilizzare la definizione, non la funzione strumentale.** mwo_pilot_tilt.measure() richiama geometria
   MWO e calcola l'area tramite R0; non può ricevere direttamente immagini MDI. Separare un adattatore MDI
   che fornisca coordinate eliografiche, mu, campo LOS, maschere e area di superficie per pixel. Riutilizzare
   centroidi sferici, leading, tilt e convenzione di Joy solo dopo questi passaggi. Verificare da header e
   schema proiezione, orientamento/rotazione, unità e segno del campo, scala/BLANK/NaN, raggio e osservatore;
   non assumere che l'adattatore CEA delle patch SMARP sia valido per il full-disk. Prove sintetiche di segno,
   rotazione e scala, più un controllo su header reali prima dell'elaborazione scientifica.

3. **Qualità e soglie proprie di MDI.** Fissare prima campo minimo e massimo, pixel per polarità e/o flusso
   minimo con una motivazione indipendente dai tilt. Non trasferire automaticamente 50 G o 4000 G da MWO,
   né scegliere valori per migliorare BARD o l'accordo MDI–MWO. Registrare pixel per polarità, separazione
   anche rispetto al campionamento dell'immagine, flusso e stato di ogni rifiuto. Definire il dominio mu
   sull'impronta e la regola per dati mancanti. Documentare QUALITY e INTERVAL dai metadati specifici della
   serie: prodotti da 1/5 minuti e modo ignoto non vanno accorpati come se avessero lo stesso rumore.

4. **Abbinamento temporale e misura relativa.** Usare T_OBS convertito correttamente in UTC, non assumere
   che T_REC sia il centro dell'esposizione. Fissare ordine di scelta e massimo scarto temporale prima;
   stesso giorno da solo non garantisce contemporaneità. La scelta operativa per il catalogo MDI e quella
   per il confronto con MWO vanno dichiarate distintamente, se diverse. Conservare ogni candidato e causa
   di rifiuto. MDI–MWO resta differenza congiunta di misura, risoluzione, selezione ed evoluzione fra orari:
   nessuno dei due strumenti è riferimento corretto per definizione. Non convertire un rapporto di flussi
   in calibrazione senza uno studio separato.

5. **Disegno temporale del pilota.** Un campione di regioni sparse per anno può stimare la resa per strato,
   ma non identifica bene una correlazione fra rotazioni. Prevedere finestre temporali contigue distribuite
   in fasi del ciclo, se si vuole informare quella componente, oppure dichiararla non stimata e mantenere
   una griglia di sensibilità. Più immagini della stessa regione non sono regioni indipendenti; differenze
   ravvicinate includono evoluzione reale oltre a rumore. Dichiarare quale quantità sarà stimata e quale
   resterà assunta, senza promettere la separazione di tutte le componenti da un pilota piccolo.

6. **Precisione prospettica di MDI da solo.** Dal pilota ricavare resa, misurabilità e intervalli plausibili
   per il rumore; dall'inventario storico e dalle posizioni DPD costruire il disegno previsto del catalogo.
   Rappresentare selezione, pesi, attività e correlazione temporale. La precisione sul campione del pilota
   non è quella del catalogo completo. Effetto della rampa e matrice MDI si ricalcolano sul nuovo disegno;
   non trasferire automaticamente il bersaglio di HMI/MWO. La validazione della procedura T3 sarà separata.
   Nessun accordo relativo nel confronto MDI–MWO autorizza un verdetto o un'analisi combinata.

7. **Acquisizione per fasi.** La bozza distingue verifica dell'accesso/metadati, selezione deterministica,
   disponibilità e FITS, con ricevute, numero di richieste e byte massimi espliciti. Prima stimare il volume
   dai metadati, deduplicando i full-disk condivisi da più regioni nello stesso istante. Non assumere già
   verificati accesso attuale, unità, modo di esposizione o dimensioni dei file. Usare trasporto con
   reindirizzamenti ammessi esplicitamente, controllo dei certificati e stop su errori ripetuti.
   Nessuna richiesta di rete è stata eseguita da questa revisione.

## Passo successivo

Claude può scrivere la bozza del protocollo su (a), con questi vincoli. Fissare campione, soglie, geometria,
tempi e prodotti prima della misura; poi revisione del protocollo e del codice. Non serve cambiare i risultati
MWO o riaprire T3 precedente. Il pilota MDI appartiene a SHARP BL; S42 resta in pausa nel progetto distinto.

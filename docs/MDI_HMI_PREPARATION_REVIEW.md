# Consegna per la revisione — piccolo confronto MDI/HMI

Preparazione autorizzata dall'utente in sua assenza, punti 1–5. Stato: **bozza e codice puro**, non
protocollo congelato e non applicazione ai dati. I dati dell'inventario restano al commit di analisi
`198785b`, documentato in `827b3cb`. Nessuna selezione o nuova risposta reale in questo lavoro.

## Stato dei cinque punti

| Punto | Stato | Prodotto o blocco |
|---|---|---|
| 1. Qualità MDI | Definizione primaria verificata | 0x200 = non PRIME 60; nuova proposta {0,0x200} da rivedere, nessun filtro applicato |
| 2. Tempi e provenienza | Chiarimenti verificati, legami per-record aperti | Distinzione valore/indice dello slot; percorso MTARP→MDATA documentato nel codice, non acquisito sui record |
| 3. Piccolo confronto | Bozza completata, da rivedere | Fino a 12 coppie, tre confronti separati, criteri informati dall'audit dichiarati, budget proposti |
| 4. Codice offline | Nuclei geometrici e misure indipendenti dal ciclo | Nessun lettore FITS, selettore, downloader o comando di esecuzione reale; adattatori rinviati |
| 5. Consegna | Questo documento e aggiornamenti del passaggio | Fonti fissate, prove sintetiche e domande per il revisore |

Documenti da leggere:

- `MDI_SMARP_METADATA_CLARIFICATIONS.md`: verifiche, fonti primarie con revisioni e problemi irrisolti.
- `PROTOCOL_MDI_HMI_SMALL_COMPARISON_DRAFT.md`: proposte operative, limiti e porte prima del congelamento.
- `../scripts/mdi_overlap_kernels.py`: funzioni pure su array, con geometria P1 riusata esplicitamente.
- `../tests/test_mdi_overlap_kernels.py`: prove sintetiche, senza FITS, cataloghi o risposte salvate.

## Prove e loro limiti

Le 27 prove sintetiche coprono proiezione a osservatore finito (contro un risultato calcolato a mano),
segni Bt/Bp, inversa LOS/μ per un campo radiale, contributi orizzontali, mu nullo e patch non tagliate,
codici bitmap diversi fra strumenti, dipolo di un bipolo analitico, area variabile, soglie inclusive,
centroidi intorno a 0/360°, geometria degenerata, dati mancanti, denominatore nullo e overflow.
Suite ordinaria dopo installazione: 87/87, con due avvisi attesi per correlazioni di input costanti.
Un caso sintetico a area uniforme confronta anche flusso, dipoli, distanza e tilt con `measure_v84`.

Primo lancio nello staging temporaneo: 19 prove superate e due fallite per un nome di parametro del
solo helper del test, duplicato dalla keyword dell'osservatore. Corretto l'helper senza cambiare la
geometria. Dopo l'aggiunta dei casi limite, esito 27/27. Non si tratta di prove su mappe reali o della
porta R0 del piano. Il riuso della geometria P1 è una dipendenza dichiarata, non un controllo indipendente.
Ricevuta e log della preparazione sono locali, non risultati scientifici da aggiungere a Git.

## Richiesta concreta al revisore

1. Verificare che le deduzioni da `smarp.c`, `m2lostarp.c` e DRMS non vengano estese impropriamente
   alle revisioni effettivamente usate nei record. Rivedere la nuova proposta QUALITY con la tabella
   primaria ora recuperata (non PRIME 60, nessuna equivalenza dimostrata fra modi).
2. Rivedere la proposta del campione (G5/G10, tempo effettivo, quattro strati, una componente G10),
   la mancanza di sostituzioni e la sua natura intenzionale, senza rappresentatività statistica.
3. Confermare che il confronto B con maschere native sia letto come differenza congiunta di misura
   e segmentazione, senza chiamarlo calibrazione isolata o prova dello scarto contro l'attività.
4. Controllare versori, osservatore finito, riferimento temporale, gestione di μ/aree e fallimenti;
   i test su array non verificano l'associazione delle keyword alle geometrie reali dei due satelliti.
5. Decidere se il primo prodotto senza S_BL/D*/efficienza sia sufficiente a verificare la pipeline.
   Prima di aggiungerli servono ciclo/emisfero fissi e adattatore P1 separato, non una modifica implicita.
6. Rivedere tetti di 512 MiB/30 min/200 tentativi e la specifica ancora mancante per gli eventuali
   link fuori dalle serie del vecchio inventario. Nessun via alla rete o ai FITS è dato da questa nota.

La regola di qualità è ora concreta ma resta da rivedere con il resto della bozza, senza congelarla
in questo compito. L'altro agente deve riportare i rilievi
prima di modificare i file. Non eseguire la bozza o sviluppare una nuova pendenza di quenching.
Piano prospettico e morfologia S in pausa; nessuna nota o messaggio inviato a Paolo; nessun push.

## Risposta alla prima revisione di Claude — revisione 2

Vedi `MDI_HMI_SMALL_COMPARISON_REV2.md`: metadati geometrici insufficienti a garantire il dominio,
blocco esplicito prima del congelamento; riferimento P1 invariato e rifiuti del kernel separati;
differenze di polarità/centroidi completate, interi QUALITY signed/unsigned specificati, 48 prove
sintetiche. Tabella full-disk QUALITY × INTERVAL senza attribuzione alle patch. Le 22 copie di fonti
registrate persistenti sono state verificate. Non considerare chiusa la revisione sul dominio μ.

# Pilota MDI — revisione e congelamento di A1

Oggetto: bozza 68ab474, metadati 98ee895 e riconteggio 9d3e937. Codex.

## Riconteggio e lettura NA

Confermati ricevuta negativa 11/12 conservata e seconda ricevuta 12/12 completa, legata al META dei metadati.
La correzione `keep_default_na=False, na_values=[""]` preserva correttamente il valore letterale JSOC «NA»;
non modifica tolleranze o dati. Allineato anche il lettore dei file nei test di manomissione, con round_trip:
altrimenti il test poteva alterare involontariamente A_size mentre cercava di provare una mutazione diversa.
Selftest rieseguito 15/15; cambia solo la fixture, non il codice del riconteggio sui prodotti.

## Decisione scientifica operativa

Ammessi esattamente QUALITY=0 e QUALITY=0x200. Esclusi 0x201, 0x280 e tutti gli altri valori, inclusi mancanti
o non interpretabili. Il significato documentato di 0x200 è un modo operativo (non PRIME 60), non una prova
di omogeneità o assenza di effetti strumentali. Soglie, gruppi, giorni e regole temporali A/B restano invariati.

Il testo dichiara gli esiti L1/2010 e i metadati già letti: non è cieco. Ripianificare offline in una cartella
nuova, senza sovrascrivere la selezione originale o le ricevute. Risultati descrittivi distinti per QUALITY e
INTERVAL, con n e copertura. Segnalare anche le coppie con QUALITY diversa a INTERVAL uguale: nei metadati sono 3.

## Controllo sotto la regola originale

Due implementazioni dei selettori sui metadati conservati confermano A/coppie 12/9 contro 81/78 e piani di
21 contro 159 file unici. Tre immagini A originali cambiano sotto la nuova regola; 2 file originali non sono
nel piano ampliato. Filtrare il nuovo A per QUALITY=0 non ricostruisce l'analisi originale.

A1 specifica quindi una tabella secondaria con le assegnazioni originali A/B e i due file aggiuntivi, per un
totale pianificabile di **161 file unici**, senza aggiungere gruppi/giorni. I 12/9 sono disponibilità di metadati,
non una promessa di misurabilità. Non si compensano eventuali fallimenti con altre immagini.

## Budget: correzione del ragionamento iniziale

La prenotazione di 32 MiB viene liberata alla chiusura del tentativo e sostituita dai byte effettivi; soltanto
i tentativi senza fine conservano la riserva. Non esiste un arresto ordinario a 46 file riusciti.
`scripts/mdi_a1_budget_review_probe.py` completa 161 trasferimenti simulati da 1,6 MB, prenotando 32 MiB ogni
volta: 257949154 byte e 412 richieste complessivi, metadata inclusi. Nessuna rete o immagine viene usata.

La proposta di ridurre il tetto a 4 MB è rimossa. I 42 file locali non dimostrano un limite per tutto l'archivio;
un limite inutilmente stretto potrebbe far rifiutare immagini altrimenti ammissibili. Inoltre 640 MB sarebbe
il caso di un tentativo per file, non il caso peggiore inclusi i retry. Due tentativi con due richieste ciascuno
su 159 file darebbero 726 richieste inclusi i 90 metadati: il tetto globale di 600 resterebbe vincolante.

Restano 32 MiB per tentativo ignoto e i tetti di 600 richieste/220 file/1,5 GB. Le stime non garantiscono
di completare il piano: al tetto si arresta e si dichiara l'incompletezza.

## Stato

Testo A1 corretto e congelato separatamente, con ricevuta SHA/commit successiva al commit di congelamento.
Il congelamento **non autorizza FITS**: servono codice del nuovo piano e riconteggio, chiusura dei blocchi B/C,
misura L2 e riconteggio pronti/rivisti, poi l'autorizzazione esplicita dell'utente al download.
I protocolli e risultati HMI/MWO e i prodotti originali MDI rimangono intatti. Nessuna nuova simulazione lunga.

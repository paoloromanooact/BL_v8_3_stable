# HMI: inventario mirato per active-region nests

25 novembre 2026, Codex. Voce N del piano BL: inventario concluso, identificazione e inferenza non eseguite.
Script `scripts/hmi_nests_metadata_inventory.py`; fotografia in `reviews/HMI_NESTS_METADATA_20261125/`.
Solo metadati e colonne d'identita/famiglia P1; nessun FITS, tilt o flusso misurato letto; nessuna rete.

## Disponibilita verificata

| Risorsa/controllo | Esito |
|---|---|
| CSV mensili SHARP locali | 197, maggio 2010–settembre 2026; nessun mese mancante nei nomi |
| Dimensione | 255737505 byte |
| Righe grezze | 1301860 |
| Righe uniche attribuite al mese proprietario | 1300060 |
| Righe al confine mensile registrate nel file adiacente | 1800, rendicontate e non contate due volte |
| Duplicati interni ai file / tempi non validi | 0 / 0 |
| HARP presenti | 8296 |
| HARP con primario P1 / senza primario P1 | 7133 / 1163 |
| HARP con almeno una posizione e QUALITY 0/128, regola P1 esistente | 8258 |
| HARP senza identificatore NOAA nell'intera sequenza locale | 5659 |
| HARP associate a piu identificatori NOAA nel tempo | 560 |
| HARP con almeno un intervallo locale fra record oltre 2 h | 3443 |
| CSV con T_OBS / con keyword esplicita del tempo di emersione | 0 / 0 |

Sono metadati nominalmente orari: T_REC e in TAI, non una data di nuova emersione. I buchi per HARP e le
associazioni NOAA sono descrittori di disponibilita, non criteri di esclusione scelti per cercare nests.
La durata mediana locale di una HARP e circa 6,21 giorni, massimo 23,42; non e la durata di un nest.
Non si identifica un evento nuovo per ogni HARPNUM o numero NOAA.

Il catalogo P1 contiene gia 443 candidate ricomparse: vengono soltanto inventariate, non ricalcolate o
promosse a etichette certe. Le 1163 HARP senza primario P1 sono contesto potenziale per le associazioni,
non nuovi record di sorgente gia misurati. Un filtro NOAA-only restringerebbe molto la popolazione.

## Che cosa possiamo fare con i dati attuali

- Progettare candidati di concentrazione spazio-temporale con identificativi e famiglie espliciti.
- Collegare posizioni in Carrington e sequenze nominali, registrando ambiguita, deriva e copertura.
- Verificare come evitare doppi conteggi e contaminazione fra sviluppo/calibrazione e verifica.
- Preparare controlli sintetici/casuali e un modello bayesiano gerarchico da congelare prima della nuova analisi.

**Non possiamo ancora certificare** tutte le nuove emersioni dentro un campo persistente o la continuita
sul lato nascosto. Le mappe HMI selezionate sono sparse; i metadati orari non sono immagini magnetiche orarie.
Non abbiamo ancora calcolato numero/frazione di nests, loro contributi BL o un ranking bayesiano.

## Fonti e dati complementari

Richiesta dell'utente recepita: [note Finley e tabella AIA/Solar Orbiter](HMI_NESTS_FINLEY_METHOD_NOTES.md).
Finley offre casi seguiti con osservazioni complementari; SPEAR/Norton un riferimento quantitativo basato
su catalogo. Non sono metodi intercambiabili e nessuno rende automaticamente certa la nostra identificazione.
AIA, EUI, PHI e SPEAR non sono stati acquisiti o inventariati come archivi locali da questo script.

## Verifica e prossimo passo

Selftest 7/7: attribuzione del mese, duplicati, calendario, ordinamento, raccordo longitudinale, associazioni
NOAA multiple e mancanti. Input e codice hanno SHA registrati; HARP_AVAILABILITY e INPUTS sono riproducibili.
Il controllo riguarda l'inventario, non una validazione dell'identificazione di nests.

Completare e rivedere `PROTOCOL_HMI_NESTS_BAYES_DRAFT.md`. Prima del congelamento fissare regole di associazione,
controlli, semi, popolazione e modello probabilistico. Codex prepara proposta e verifiche; Claude continua i
piloti SFT, poi revisione incrociata senza duplicare l'inventario.

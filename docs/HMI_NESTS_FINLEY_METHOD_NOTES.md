# Active-region nests — note dai lavori di Finley e dati complementari

25 novembre 2026, Codex. Lettura delle fonti primarie per la specifica N del piano BL. Nessuna nuova
identificazione di nests o misura magnetica. L'estensione AIA/Solar Orbiter e annotata su richiesta dell'utente.

## Finley et al. 2025: definizione e continuità

[A prolific solar flare factory. Nearly continuous monitoring of an active region nest with Solar Orbiter](https://arxiv.org/html/2504.06345v2),
versione arXiv v2; [DOI](https://doi.org/10.1051/0004-6361/202554323), §§1–2.

Il nest e una sede di emersioni ripetute che mantiene attivita coerente per piu rotazioni. Gli autori individuano
un candidato nelle mappe AIA 304 Å e ne seguono morfologia e campo combinando osservazioni terrestri e di
Solar Orbiter. La selezione del caso e dei contorni non e presentata come soluzione unica. Il caso mostra
perche la sola vista terrestre lascia incerta l'evoluzione durante il passaggio sul lato nascosto.

**Uso nella nostra proposta:** riferimento per la distinzione fra persistenza e nuove emersioni e per un
successivo controllo morfologico; il caso studiato non e una validazione statistica del nostro campione BL.

## Finley et al. 2026: nests mobili, fusioni e copertura

[Active nests at solar maximum: How nested flux emergence dominated flaring activity and structured the heliosphere](https://arxiv.org/html/2608.26315v1),
versione arXiv v1 del 26 agosto 2026; [DOI](https://doi.org/10.1051/0004-6361/202662128), §3.

L'identificazione del 2024 usa emissione EUV e posizioni dei flare; il tracciamento in longitudine comprende
associazioni manuali e due nests che convergono fino a non essere piu separabili. AIA ed EUI permettono una
copertura complementare nelle finestre favorevoli. Non e una procedura automatica direttamente trasferibile
ai nostri soli metadati HMI, ne una prova di quenching.

**Uso nella nostra proposta:** registrare deriva, collegamenti ambigui, fusioni/scissioni e finestre di copertura;
non imporre un singolo identificatore fisico certo a ogni componente di un grafo di vicinanza.

## Nota richiesta: AIA e Solar Orbiter

| Risorsa | Che cosa aggiunge al nostro studio | Stato nel progetto |
|---|---|---|
| SDO/HMI | Posizioni, campo fotosferico e ingredienti del proxy BL sul lato terrestre | Metadati orari e mappe selezionate gia locali |
| SDO/AIA, in particolare 304 Å nei lavori citati | Morfologia EUV e continuita dell'attivita dal lato terrestre | Disponibilita locale e campionamento da inventariare; nessuna acquisizione avviata |
| Solar Orbiter/EUI | Vista EUV complementare, compreso il lato nascosto quando la geometria lo consente | Da verificare per epoche e finestre d'interesse; nessuna acquisizione avviata |
| Solar Orbiter/PHI | Osservazioni magnetiche dalla vista di Solar Orbiter, nei periodi disponibili | Da verificare copertura e confrontabilita; nessuna calibrazione HMI/PHI adottata |

**Decisione da mantenere visibile:** AIA e Solar Orbiter sono una possibile estensione importante per uno
studio di continuita comparabile a Finley. Non sono prerequisiti assoluti per definire candidati statistici
HMI. Con HMI soltanto non si dichiara il monitoraggio continuo del lato nascosto. AIA da sola non risolve quel
vuoto. EUV, flusso fotosferico e contributo al dipolo restano osservabili differenti.

Prima di una campagna complementare: scegliere epoche/casi, inventariare prodotti e cadenze, verificare geometria,
unità e confrontabilita, definire costi/acquisizione in una specifica separata. Non sostituire le mappe HMI con
EUV nel calcolo di S_BL e non importare fattori di calibrazione da altri campioni.

## Confronto metodologico: Norton et al.

[Moderate Nesting and Cross-Equatorial Asymmetry of Active Regions in Solar Cycle 24](https://arxiv.org/html/2511.03646v2),
versione arXiv v2 del 2 aprile 2026; [DOI](https://doi.org/10.1007/s12036-026-10157-0), §§2–4.

Questo studio usa SPEAR, con un record per SHARP vicino al meridiano e trattamento delle regioni ritornanti,
per la ricerca quantitativa; le sinottiche servono al confronto visivo. Esplora velocita di rotazione diverse
e controlli con longitudini randomizzate, mantenendo le altre caratteristiche.

**Punto da chiarire prima di adottare soglie:** il §3 e il §4/figura 4 della versione letta riportano gli intervalli
latitudine/longitudine in ordine scambiato. Non incorporare numeri senza una scelta esplicita e documentata.
Una scansione di velocita/soglie richiede lo stesso trattamento nei controlli casuali, non la selezione del solo
massimo osservato.

## Collegamento al bayesiano: proposta nostra, non risultato dei lavori citati

Le fonti guidano identificazione e limiti osservativi. Il modello gerarchico del quenching e il ranking dei
trasporti sono specifiche del nostro progetto: appartenenze incerte e regioni dello stesso nest non devono
apparire come osservazioni indipendenti. Un buon adattamento non rende certa la classificazione dei nests.

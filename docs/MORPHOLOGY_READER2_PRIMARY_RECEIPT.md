# Morfologia HMI — blocco delle 30 classi primarie del lettore 2

Blocco: 2026-11-13T14:03:51Z. Modello `gpt-6.1-sol`, ragionamento alto richiesto.
Le letture applicano protocollo, A1 e A2; partenza da `9a4c4cd2e5501652c32497840fc747eb3a7ffd2b`,
registrazione sul genitore `144513331fab8f1e875f17e2e9fb93fb97e054a8`. Questi riferimenti restano distinti
perche l'altro agente puo lavorare contemporaneamente nel repository.

## Artefatti bloccati

- File privato `results/MORPHOLOGY/private/PRIMARY_READER2.csv`:
  SHA-256 `2e8fd1de8c5f348cdd5bb71a91544478795adbb9d88691e03079741fbf83b2b7`.
- Metadati privati `results/MORPHOLOGY/private/PRIMARY_READER2_META.json`:
  SHA-256 `1552cb8afdda2788e0c5a4787bae0c770bbc0184aed07db99f42e9fc882db066`.
- Impegni pubblici in
  [PRIMARY_READER2_COMMITMENT.csv](../results/MORPHOLOGY/PRIMARY_READER2_COMMITMENT.csv).

Per ogni scheda sono registrati ordine, codice, classe A/B/D/U, eventuali
alternative, motivazione visiva e hash dell'immagine. Sono presenti esattamente
le 30 righe di `READING_ORDER_READER2.csv`, nel medesimo ordine. Le trenta
immagini lette coincidono con i blob Git del riferimento; i protocolli e
l'ordine non sono cambiati. Le etichette non sono incluse in questo documento
ne nei file tracciati, per evitare di influenzare il lettore 1.

## Esposizioni e limiti

Domanda scientifica, risultati T3/T5 e controlli numerici precedenti sono
noti. Sono note le classi storiche 25S; tre vecchie immagini annotate sono
state riaperte nella revisione del piano. Le undici mappe di riferimento
sono state lette e bloccate separatamente. Il confronto della taratura e
l'emendamento A2 costituiscono formazione comune, dichiaratamente non cieca.
Le esposizioni pregresse sono specificate nei metadati.

In questa fase sono state aperte soltanto le trenta immagini `map_` assegnate
al lettore 2, nelle due scale previste. Non sono stati aperti la corrispondenza
codice–HARP, le letture del lettore 1, i relativi riepiloghi sulle 90 nuove,
le altre sessanta mappe o alcuna immagine `cen_`. Non sono stati consultati
cataloghi numerici durante la classificazione. Nessuna associazione a
gruppo, rango o misura e stata ricostruita per i codici anonimi.

Il file delle classi primarie resta bloccato. Nessuna classe conferma un
errore o il numero di regioni fisiche. Nessuna nuova regola o lettura dei
centroidi e stata introdotta.

## Passo successivo

Verificare che siano bloccate anche le 90 classi primarie del lettore 1.
Soltanto dopo il blocco di entrambi puo iniziare il passaggio con i centroidi,
in un file distinto e senza cambiare le classi primarie. Il confronto delle
etichette e le eventuali decisioni concordate vanno registrati separatamente
conservando gli originali e i rispettivi hash. Nessun push eseguito.

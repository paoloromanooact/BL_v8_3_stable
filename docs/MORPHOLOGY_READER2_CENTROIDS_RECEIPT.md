# Morfologia HMI — secondo passaggio del lettore 2

Registrazione bloccata il 2026-11-13T14:16:29Z. Modello `gpt-6.1-sol`, ragionamento alto
richiesto. Sono state aperte soltanto le trenta immagini `cen_` assegnate
al lettore 2, nello stesso ordine del primo passaggio e nelle due scale
fisse del protocollo. I marker sono cerchio positivo e quadrato negativo.

## Condizione di avvio e integrita delle classi primarie

Prima di aprire i centroidi erano registrati il blocco del lettore 1
(`1445133`, impegno `fe9b537b…`, 2026-11-13T13:58:01Z) e quello del lettore 2
(`230f190`, impegno `2e8fd1de…`, 2026-11-13T14:03:51Z). Sono stati verificati
gli impegni pubblici e i relativi commit; le etichette del lettore 1 non
sono state consultate. I file privati primari e della taratura del lettore 2
sono stati verificati byte per byte contro i rispettivi SHA-256, prima e
dopo la registrazione. Le classi A/B/D/U originali non sono cambiate.

## Artefatti distinti e bloccati

- `results/MORPHOLOGY/private/CENTROIDS_READER2.csv`:
  SHA-256 `7fc46899d42437be24090b0653f8ed96ee4b9202d2a1a8f2f74e2cc947a6dd97`.
- `results/MORPHOLOGY/private/CENTROIDS_READER2_META.json`:
  SHA-256 `022ff01e191f7c60fe6c2e5b22f873d23aed438f216c26659ffd8a2cb6b2abdd`.
- Impegni pubblici:
  [CENTROIDS_READER2_COMMITMENT.csv](../results/MORPHOLOGY/CENTROIDS_READER2_COMMITMENT.csv).

Il CSV registra indicatore C (`si`, `no`, `non_valutabile`), polarita che
motiva il giudizio positivo, motivazione e contatto visibile della maschera
con il bordo del riquadro, con relativa nota. Il contatto e un giudizio
visivo sul contorno giallo, senza conteggi numerici dei pixel e senza
inferenze su errori. C riguarda la collocazione dei centroidi rispetto alle
concentrazioni della medesima polarita; i non valutabili restano espliciti.

Sono verificate trenta righe, codici e ordine esatti, hash e blob Git delle
trenta immagini rispetto a `230f1902c6f816ba0bad399dc080a7a5ae417a51`. La provenienza di registrazione
e `230f1902c6f816ba0bad399dc080a7a5ae417a51`; gli hash di protocollo, emendamenti e impegni sono nei metadati.

## Indipendenza e passo successivo

Restano note le esposizioni pregresse gia dichiarate: progetto, tabelle
storiche e taratura comune sotto A2. Non sono stati aperti la corrispondenza
codice–HARP, le sessanta immagini non assegnate, le etichette o le motivazioni
primarie/secondarie del lettore 1 e i suoi riepiloghi sulle novanta nuove.
I giudizi secondari restano privati per non influenzare il suo passaggio C.

Dopo il blocco anche del secondo passaggio del lettore 1, si potranno
confrontare i giudizi originali, conservando i non valutabili e producendo
la matrice di confusione primaria e l'accordo su C prima di discutere i
disaccordi. Eventuali decisioni comuni resteranno separate. Nessun push.

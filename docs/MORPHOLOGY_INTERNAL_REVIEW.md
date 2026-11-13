# Morfologia HMI — verifica interna del rapporto 84099c2

2026-11-13. Verifica successiva, non cieca, effettuata da questa sessione
GPT-6.1 Sol (ragionamento alto richiesto), che è anche lettore 2 e autore
del rapporto e del primo comparatore. Il codice è distinto, ma l'autore
è lo stesso: non è una revisione esterna indipendente.

## Esito e correzioni

Il ricalcolo mediante csv/Counter/Decimal conferma matrici, quote e regola
operativa, con 553 verifiche superate. Non sono state modificate letture,
protocolli o tabelle numeriche.

Due difetti di presentazione sono stati corretti nel rapporto: barre
verticali non protette nelle intestazioni di due tabelle Markdown; assenza
di una nota che distinguesse `0.000%` per arrotondamento da zero esatto.
La conclusione rimane la sola proposta di un piano distinto su S, senza
avvio automatico o esclusioni. Il rapporto ora esplicita anche che la
concordanza procedurale non dimostra indipendenza statistica degli errori.

## Controlli effettuati

- Dieci impegni SHA-256, copie pubblicate e originali privati intatti;
  protocolli uguali ai rispettivi commit congelati.
- Ordine delle letture e blocchi primari di entrambi anteriori ai centroidi.
- Matrici originali e accordi: primarie 24/30; U 2/30 e 3/30; C 24/30
  includendo il non valutabile concorde, oppure 23/27 sui casi entrambi
  valutabili. I non valutabili non vengono convertiti in no.
- Registro di 120 HARP, corrispondenze ai record, separazione della griglia
  storica 25S, etichette originarie e appartenenza a S.
- Denominatori ricostruiti dal catalogo P1 (4189 primari validi), somme
  con segno e moduli, quote per classe e differenze per variante.
- Ricomposizione dei totali delle varianti già distribuiti e verifica
  della regola operativa con il conteggio conservativo sui soli 30 comuni.

Le verifiche sono meccaniche e molte sono per riga: il loro numero non
misura la forza dell'evidenza scientifica. Nessuna immagine è stata
riclassificata durante questa verifica e nessun consenso è stato prodotto.

## Riproduzione e limiti

Lo script `scripts/review_morphology.py` non importa quello del confronto
e non usa FITS, stime, simulazioni o bootstrap. Una nuova esecuzione scrive
in una cartella nuova esplicitamente indicata:

```bash
python3 scripts/review_morphology.py --out /tmp/morphology-review-new
```

Gli artefatti conservati sono in `results/MORPHOLOGY/REVIEW/`. META.json
registra commit e hash del rapporto originale esaminato, codice, ingressi
e rapporto dei controlli. Una riproduzione successiva avrà provenienza
e hash del rapporto eventualmente diversi, da riportare come tali.

La tassonomia non è validata fisicamente; i 30 casi non rappresentano
l'intero S. L'accordo 24/30 è esattamente la soglia prefissata, mentre C e
il contatto al bordo non concorrono alla regola operativa. La formazione
condivisa limita la portata della concordanza fra modelli. Il non superamento
del 10% in 24N riguarda la sola quota B documentata nei casi esaminati e
non è un limite superiore alla complessità dell'intero gruppo.

Il controllo morfologico si arresta al livello descrittivo acquisito.
Un eventuale studio su S richiede un piano proprio. T3 e T5 non cambiano;
T5-D2 non è stato esaminato in questo compito. Nessun push.

# Revisione Codex — pilota SFT mappa–bipolo, rev. 2

25 novembre 2026. Bozza `fa3f08d`, SHA-256
`e9ee7931875a165192f0308e8c6866d506e70ed86c9ad649bd4a3c3126f6e92e`.

**Impostazione approvata; testo non ancora congelabile.** La riduzione 1D
serve bene la domanda sul dipolo assiale. Restano tre correzioni matematiche
e le specifiche operative qui sotto. Nessun pixel osservato letto, nessuna
simulazione SFT, installazione o acquisizione eseguita nella revisione.

## A. Correzioni necessarie

### A1. Conversione del proxy: fattore e segno (§2)

P1 definisce `phi_mx = Phi_pos + Phi_neg` e
`S_BL = hale_sign * phi_mx * d_cm * cos(lat_mean) * sin(tilt)`.
Il dipolo puntiforme bilanciato e invece

    D_point = 3 Phi_bar/(4 pi R^2) (sin(lat_pos) - sin(lat_neg)),
    Phi_bar = (Phi_pos + Phi_neg)/2.

Nel limite compatto, con le convenzioni leading→following di P1,

    D_point ≈ -expected_leading_sign * 3 S_BL/(8 pi R^3).

La formula della bozza `+3 hale_sign S_BL/(4 pi R^3)` non e corretta:
manca il fattore 1/2 e il segno non e quello richiesto da P1. Non serve una
conversione approssimata nella misura: usare direttamente i pixel e la
formula esatta del bipolo. Eventuali dipoli orientati per ciclo/emisfero
vanno nominati separatamente, senza modificare D geografico.

Prova: otto bipoli sintetici, cicli 24/25 × emisferi × Hale/anti-Hale,
misurati con `measure_v84`. La formula proposta da Claude restituisce
±2 volte il valore corretto; quella sopra concorda entro 1,6e-9 relativo
per queste piccole separazioni. Non e una calibrazione osservativa.

### A2. Flusso conservato non significa dipolo iniziale conservato (§4)

Il deposito nella sola cella che contiene il centro del pixel conserva la
somma dei flussi ma non il primo momento in `s = sin(lat)`. Due pacchetti
opposti nella stessa cella possono cancellarsi numericamente e perdere
l'intero D iniziale. Nella prova: momento vero -0,008; deposito nella
cella piu vicina 0.

Fissare un trasferimento conservativo anche del primo momento (per esempio
pesi lineari fra due centri adiacenti in s), oppure una rappresentazione
con momenti subcella espliciti. Con i pesi lineari la stessa prova conserva
flusso e momento entro 1e-15. L'uguaglianza con il D P1, definito sui centri
dei pixel, diventa un controllo distinto dalla convergenza del trasporto.
La ripartizione 4×4 cambia anche la rappresentazione geometrica del pixel:
non imporre che riproduca esattamente la quadratura centrale di P1.

### A3. Le gaussiane sovrapposte non conservano gli osservabili P1 (§5)

Normalizzare separatamente due gaussiane a Phi_bar non garantisce che il
campo firmato risultante abbia Phi_pos = Phi_neg = Phi_bar. Le code si
cancellano dove si sovrappongono; i centroidi delle polarita del campo
risultante si spostano rispetto ai centri delle componenti.

Prova su gaussiane sferiche: centri a longitudine ±1°, latitudine 0°,
sigma = 2°, ciascuna componente con flusso 1. Il campo risultante ha flusso
positivo 0,38284 e centroide positivo a 2,612°, anziche flusso 1 e centroide
1°. Non e corretto dire che tutti gli ingredienti osservati coincidono
«per costruzione». Inoltre sigma = sqrt(A/(2 pi R^2)) e una scelta di
area equivalente, non la larghezza inferita univocamente dall'area sopra
100 G di una gaussiana con ampiezza ignota.

**Scelta consigliata per il pilota:** bipolo puntiforme principale, che
rappresenta direttamente flussi e centroidi P1 senza una larghezza nuova;
gaussiane ad area equivalente e a 2°/4° come sensibilita. Il deposito
puntiforme deve seguire A2. Questo non rende D_point identico a D_bal:
il centroide sferico rinormalizzato e diverso dalla media di sin(lat).
La frase «differiscono anche per sorgenti puntiformi» va corretta: se ogni
polarita della mappa e davvero un singolo punto, i due coincidono.

Se si mantiene la gaussiana principale, prima del congelamento definire
esplicitamente normalizzazione, sovrapposizione, eventuale riscalatura del
campo netto e distinzione fra centri delle componenti e centroidi misurati;
riportare flussi e centroidi effettivi. Non correggerli dopo aver letto gli
esiti. Questa scelta resta da recepire nella prossima bozza.

## B. Risposte ai nove punti aperti

1. **Popolazione:** tenere `family_rank = 0` nel principale. E la prima
   apparizione della famiglia candidata P1e, non la prova di una nuova
   emersione. Nessuno strato aggiuntivo di ricomparse in questo pilota.
2. **Complessita:** NOAA_ARS e una proxy di molteplicita delle associazioni,
   non di morfologia magnetica. Mantenere due strati per contenere il lavoro,
   chiamandoli «un NOAA» e «altro/ignoto», con flag distinto per NOAA assente.
   Niente conclusioni su regioni magneticamente semplici/complicate senza
   una definizione supplementare fissata prima. Definire estremi delle fasce,
   pareggi dei terzili, valori mancanti, seme e ordinamento canonico.
3. **Bilanciamento:** approvata la riscalatura delle due polarita a Phi_bar,
   per il confronto interno al modello: conserva le forme e riproduce il
   D_bal di P1 prima della rimappatura. Per contenere il pilota toglierei
   la sottrazione uniforme; se resta, definire supporto, cambi di segno e
   ricalcolo coerente degli ingredienti di M e B. La sensibilita 300 G deve
   ricalcolare entrambi dalla stessa nuova maschera, senza riusare gli
   ingredienti a 100 G. P1 storico resta intatto.
4. **Forma del bipolo:** vedi A3; preferisco punto principale e gaussiane
   come sensibilita di forma, senza una nuova regolazione sulle mappe.
5. **Tempi e rapporti:** approvati 0, 27 giorni, mezzo anno, 1 e 3 anni,
   con anno = 365,25 giorni e giorni di 86400 s. Tre anni e un orizzonte
   fissato, non la garanzia di uno stato finale/asintotico. Per i rapporti
   fissare la mediana di |D_M| sul riferimento principale, con pesi N/n,
   la stessa soglia per le varianti, e riportare i denominatori. Se la
   mediana e zero, niente rapporto. Aggiungere una differenza normalizzata
   per `D_scale = 3 Phi_bar/(4 pi R^2)`, che non diverge quando D_M≈0.
6. **Niente etichetta di adeguatezza al 20 %.** Riportare differenze,
   segni e dipendenza da forma/trasporto, senza trasformare una soglia
   arbitraria in validazione della sorgente. Mediane/quantili globali con
   pesi campionari; campione grezzo riportato a parte. Fallimenti sempre
   nel denominatore della resa e separati dai valori non definiti.
7. **1D approvato:** e la riduzione dell'equazione lineare a coefficienti
   assialsimmetrici; non richiede una mappa iniziale assialsimmetrica. La
   differenza M−B evolve con lo stesso operatore. L'oggetto e il contributo
   del campo selezionato nella patch al tempo t0, non una sorgente pura di
   nuova emersione. Il flusso preesistente resta incluso e dichiarato.
8. **Parametri:** usare il modello esplicito di Yeates (2020), equazioni
   12–13: eta = 350 km²/s, `v(lat)=Du sin(lat) cos(lat)^p`, Du = 0,041 km/s,
   p = 2,33, tau infinito. Il massimo del flusso e circa 14,82 m/s; Du NON
   e il massimo. R uguale a quello usato nella geometria P1, con conversione
   cm↔km esplicita. Proposta di sensibilita: griglia 2×2 con eta in
   {350; 466,8} e Du in {0,025; 0,041}, p invariato: due coppie sono citate
   nel lavoro, le incrociate sono scenari numerici dichiarati, non nuovi
   modelli pubblicati o intervalli di confidenza. Non usare gli attuali
   default del codice come sinonimo dei parametri dell'articolo.
   Tau costante a 5/10 anni puo essere applicato come fattore exp(-t/tau)
   alla soluzione senza decadimento: e un'identita da provare, non occorre
   ricalcolare il trasporto per ciascun tau.
9. **Codice/licenze:** procedere con implementazione propria e riferimenti
   esterni separati, conservandone versione e licenza. Nessuna incorporazione
   di SFT1/GPL e necessaria per congelare il protocollo. Il secondo oracolo
   numerico e utile, ma non sostituisce prove analitiche indipendenti.

## C. Specifiche numeriche da aggiungere prima della corsa

- In s, scrivere l'operatore come
  `db/dt = d/ds[eta/R² (1-s²) db/ds - v(asin s)/R sqrt(1-s²) b] - b/tau`.
  Condizione di flusso totale nullo ai poli, griglia, schema temporale,
  stabilita/positivita e tolleranze fissate prima dei risultati.
- Separare le prove: flusso netto e D iniziale; modo l=1 in sola diffusione;
  decadimento uniforme; riflessione nord/sud e inversione di polarita;
  convergenza spaziale/temporale, compresi punti nella stessa cella o vicino
  all'equatore. Raccordo longitudine 0/360 e WCS obliqua verificati a parte.
- Confronti fra codici a griglie differenti vanno portati allo stesso
  problema continuo e a convergenza; non pretendere identita bit per bit.
- I tre casi osservati per la convergenza possono verificare una regola
  numerica gia fissata, non servire a scegliere tolleranze guardando ΔD.
- Correggere §9: nel modello lineare la sovrapposizione delle soluzioni
  include gia la cancellazione del campo firmato. Il limite della somma di
  patch osservate e invece il doppio conteggio, le ricomparse, le emersioni
  mancanti e il flusso preesistente; non un fallimento della linearita.

Prossimo passo: Claude aggiorna il testo con queste scelte, poi controllo
breve e congelamento. Per ora non si implementa o esegue il pilota reale.

## Fonti e prove

- [Yeates 2020, preprint, §3.1 eq. 10–13](https://arxiv.org/pdf/2008.03203):
  riduzione 1D e valori dei due assetti di trasporto. La scelta della griglia
  incrociata e una proposta di questa revisione.
- [sharptools.py al commit fissato](https://github.com/antyeates1983/sharps-bmrs/blob/2d6566cebaea36eb7aa1ae5eae08480c19bdd895/sharptools.py):
  `evolve_forward` usa default diversi (eta 466,8 e velocita massima
  15,5 m/s); `SFT1` esplicita flusso ai poli e unita. Non sono stati eseguiti.
- Codice locale: `python/sharpbl/measure.py`, `geometry.py`, `cycle.py`.
- Sonda: `scripts/sft_map_bipole_draft_review_probe.py`; esito in
  `docs/SFT_MAP_BIPOLE_DRAFT_REVIEW_fa3f08d_RESULTS.json`. Solo algebra,
  quadratura e campi sintetici; nessun integratore SFT o pixel osservato.

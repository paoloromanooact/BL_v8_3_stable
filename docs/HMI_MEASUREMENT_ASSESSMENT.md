# HMI: che cosa misura il catalogo e che cosa resta da verificare

2026-11-13. Sintesi dei risultati già distribuiti, senza nuove misure o selezioni.
Priorità concordata: sorgente Babcock–Leighton e quenching nell'era HMI.

## 1. Risultato acquisito

È disponibile il catalogo HMI 2010-05 → 2026-09: 14195 record selezionati,
7133 HARP, di cui 4189 con primario valido nella base del controllo delle dominanti.
P1 produce una misura al record scelto vicino al meridiano centrale, non
necessariamente all'emersione. Le ricomparse candidate e le HARP multiregione
impediscono di equiparare il numero di HARP a quello di regioni fisiche distinte.

| Quantità | Significato e limite |
|---|---|
| S_BL = hale_sign · Φ · d · cos λ · sin α (Mx cm) | Proxy geometrico della sorgente, costruito con due centroidi e una convenzione di Hale. In una HARP complessa l'asse può collegare medie di più concentrazioni. |
| D = 3/(4πR²) Σ Br sin λ dA (G) | Contributo al dipolo assiale sui pixel selezionati, indipendente da Hale e ciclo; risente anche dello sbilancio di flusso della patch. |
| D_bal = 3/(4πR²) Φ̄ (〈sin λ〉+ − 〈sin λ〉−) (G) | Momento bilanciato che elimina il termine di monopolo dovuto allo sbilancio. È la base di D* usato nell'efficienza T5. |

S_BL, D e D_bal sono quantità diverse. Nessuna misura direttamente il campo
polare che sopravviverà al trasporto e alla cancellazione superficiale.
Definizioni: [P1 §3](PROTOCOL_P1_SBL_SERIES.md), [P2 §§3–4](PROTOCOL_P2_QUENCHING.md).

## 2. Evidenza disponibile sulla misura

| Controllo | Risultato | Portata |
|---|---|---|
| Confronto BARD C1 | Accordo su geometria e convenzioni nel campione confrontato: 999 abbinamenti; rapporto dei flussi nostro/BARD circa 1,67 | Non è una calibrazione dell'ampiezza della sorgente né una verifica di tutte le maschere. |
| Ricostruzione delle 120 HARP del controllo dominanti | Valori P1 riprodotti dai FITS entro la precisione macchina | Controllo numerico su quelle HARP. |
| Varianti di maschera, pesatura e soglia sulle 120 HARP | Effetti quantificati nelle tabelle esistenti; con 300 G nove confronti impossibili | Le piccole differenze nette possono nascondere compensazioni. Non certifica le HARP non esaminate. |
| Lettura delle 30 schede 25S | Nessun errore geometrico macroscopico riconosciuto; presenti complessi e centroidi tra concentrazioni distinte | Letture non cieche, campione non rappresentativo dell'intera serie; associazioni fisiche non verificate dalle schede. |
| Riproducibilità fase 1 | Cinque CSV delle figure P1 byte-identici | Condizionata agli input P1 distribuiti; non ricostruisce tutta la catena dai FITS. |

Fonti: [BARD](P3_RESULTS_C1.md), [dominanti](DOMINANT_HARP_RESULTS.md),
[lettura 25S](DOMINANT_HARP_VISUAL_25S.md), [riproducibilità](REPRO_PHASE1_RESULTS.md).
Esempio importante: in 25S la variante bitmap ≥ 1 cambia la somma di circa
+0,09% di Σ|S_BL| del gruppo, ma la somma dei moduli delle variazioni è 13,1%.
Una somma stabile non implica misure individuali stabili.

## 3. Il controllo HMI che aggiungerebbe informazione

La lacuna concreta è la rappresentazione fisica del tilt: **quanto spesso i due
centroidi descrivono un bipolo riconoscibile e quanto spesso un complesso?**
Il filtro «una NOAA» già esistente non risponde a questa domanda.

Il primo passo proposto è completare la lettura delle schede già prodotte,
coprendo anche 24N, 24S e 25N. La bozza revisionata prevede figure senza
annotazioni di esito e due passaggi: sola morfologia, poi posizione dei
centroidi; seconda lettura indipendente su 30 delle 90 nuove schede.
Le classi si collegano alle sensibilità solo dopo il blocco delle letture;
le 30 classificazioni 25S storiche restano separate.
Non richiede nuovi FITS. Il prodotto utile sarebbe una tabella HARP per HARP
che distingua interpretabilità dell'asse e sensibilità della misura, senza
trasformare le classi in errori o eliminare casi dal catalogo.

La [bozza di studio morfologico](PROTOCOL_HMI_MORPHOLOGY_DRAFT.md) delimita questo
passo. Non è ancora congelata e non è stata eseguita. Una verifica sulla
popolazione completa del campione S richiederebbe successivamente un disegno
proprio: le dominanti e i controlli selezionati non sono un campione casuale di S.

Questo controllo serve all'interpretazione della misura. Per una risposta
sul quenching dell'efficienza, il candidato prioritario distinto è la
[diagnosi del fallimento T5 sui salti](T5_JUMPS_DIAGNOSTIC_DESIGN.md).
La prima fase è conclusa: [risultati T5-D1](T5_DIAGNOSTIC_RESULTS.md).
L'attribuzione alle componenti individuale e temporale resta aperta.

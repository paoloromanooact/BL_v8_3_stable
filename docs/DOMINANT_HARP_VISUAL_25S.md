# Esame visivo delle 30 schede del gruppo 25S (HARP dominanti e di controllo)

Stato: **prima lettura fatta il 2026-11-13 da un solo lettore (l'agente, modello Fable 5.1), sulle
schede `figures/DOMINANT/<HARPNUM>.png` prodotte dal controllo completo (`36676a9`, piano `f805c5a`);
corretta lo stesso giorno dopo una seconda lettura esterna (§4), con le correzioni segnalate nel
testo.** La versione della prima lettura è nel commit `7d36b59`. È il
livello 3 del piano (§4): cerca **errori confermati** con evidenza specifica per HARP. È un giudizio
visivo, non una misura: nessun output è stato cambiato, nessun valore ricalcolato. Le classificazioni
sotto sono di chi ha guardato le immagini e vanno considerate opinioni documentate, verificabili
riaprendo le schede. Il gruppo è stato scelto perché supera la soglia di priorità del 25 %
(`docs/DOMINANT_HARP_RESULTS.md` §2).

Convenzioni della scheda: mappa Br (bianco positivo, nero negativo), contorno giallo = maschera
bitmap ≥ 33 (quella di P1), contorno ciano = bitmap ≥ 1; cerchio = centroide positivo, quadrato =
centroide negativo; rosso = pesi |Br| (P1), verde = pesi uniformi; x cresce verso ovest. Nel sud del
ciclo 25 la polarità leading attesa è negativa.

**Classi usate** (una per HARP; nessuna è «errore» salvo la E):
- **A** — bipolo singolo riconoscibile; maschera e centroidi coerenti con l'immagine.
- **B** — complesso di più concentrazioni di campo (di norma con NOAA ≥ 2; `NOAA_NUM` è
  un'associazione di catalogo e non conta da sola le regioni fisiche): la misura è il proxy della
  sorgente calcolato dai centroidi globali del complesso, come previsto dalla definizione «una
  misura per HARP» di P1; centroidi dentro le concentrazioni di campo.
- **C** — complesso in cui almeno un centroide cade **tra** regioni distinte (nel vuoto tra due
  concentrazioni della stessa polarità) o è trascinato da plage diffusa lontana: tilt e separazione
  sono medie poco interpretabili come bipolo; sensibilità alla pesatura o al record.
- **D** — bipolo mal definito per una di due ragioni, distinte [precisato dopo la seconda lettura]:
  **quasi unipolare** (sbilancio di flusso > 0,95: una polarità ha pochi pixel) oppure **morfologia
  frammentata** (plage di entrambe le polarità in isole separate); «in decadimento» non è
  accertabile da un solo istante e non si usa. Contributo a S_BL piccolo nei casi esaminati.
- **E** — errore confermato (polarità invertite rispetto alla mappa, geometria dei marker
  incoerente con l'immagine, maschera palesemente incoerente). L'appartenenza di un blob a un'altra
  HARP **non** è accertabile dalla sola scheda ritagliata (servirebbero le segmentazioni delle patch
  vicine o mappe di contesto) e non è un criterio usabile qui.
- Le etichette miste (A/B, B/C, A/D) sono ammesse per i casi di confine e contano come categorie
  separate nei totali, senza doppio conteggio.

## 1. Dominanti (rango per |S_BL|, quota di Σ|S_BL| del gruppo)

| Rango | HARP | Quota | Classe | Osservazione |
|---|---|---|---|---|
| 1 | 11786 | 3,8 % | B | Complesso lungo circa 6000 px con 11 regioni NOAA; la maschera ≥ 33 copre una catena di regioni più blob separati a destra; i centroidi stanno nella parte centrale, separazione piccola rispetto all'estensione. Molto flusso forte fuori maschera (M2 0,86). Il record di controllo dà un S_BL molto diverso (R2 0,12). |
| 2 | 11662 | 3,5 % | B/C | Grande regione con macchia negativa leading e plage positiva estesa; la maschera include una vasta plage diffusa in basso a sinistra che trascina il centroide positivo (d cambia del 15 % con pesi uniformi). Con bitmap ≥ 1 S_BL cambia di −2,9 % di Σ\|S_BL\| del gruppo: il contributo più sensibile alla maschera. |
| 3 | 12094 | 3,2 % | B | Catena allungata con 11 regioni NOAA; la maschera tocca il bordo **inferiore** del riquadro (572 pixel; nessun contatto sugli altri lati) [corretto: la prima lettura diceva «sinistro»]; regioni separate a destra incluse. Centroidi nella parte centrale. |
| 4 | 11513 | 3,0 % | B | Regione grande con 5 NOAA, polarità intrecciate; centroidi coerenti. |
| 5 | 11487 | 1,7 % | **C** | Due complessi distinti nella stessa HARP: bipolo compatto in alto a sinistra e regione diffusa a destra. Il centroide negativo \|Br\| cade nel vuoto tra i due (quello uniforme ancora più a destra). S_BL ha segno **opposto** a quello del gruppo e il record di controllo ha segno opposto (R2 −0,05). |
| 6 | 13691 | 1,6 % | B | Complesso con più macchie e 5 NOAA; centroidi dentro le concentrazioni; sensibilità alla pesatura (d +24 % con pesi uniformi, flag C1). |
| 7 | 10779 | 1,6 % | A/B | Una regione grande (4 NOAA ravvicinate); bipolo riconoscibile; centroidi coerenti. |
| 8 | 9680 | 1,6 % | **C** | Bipolo principale a destra più una plage estesa e lontana in basso a sinistra, inclusa nella maschera (3 NOAA): il centroide positivo è trascinato verso la plage lontana, l'asse è lungo. Record di controllo di segno opposto (R2 −0,04). Maschera al bordo inferiore (75 pixel). |
| 9 | 8950 | 1,5 % | A | Regione singola grande (macchia negativa, plage positiva); coerente. |
| 10 | 9559 | 1,5 % | A | Macchia negativa grande e plage positiva; coerente. |
| 11 | 11930 | 1,4 % | B | Catena di 9 regioni NOAA su circa 5000 px; centroidi nella parte centrale; M2 0,69. |
| 12 | 12261 | 1,4 % | B/C | Catena di 6 NOAA; il centroide positivo \|Br\| è spostato verso una regione separata a sinistra. |
| 13 | 11907 | 1,2 % | **C** | Due macchie negative distinte (in alto e in basso) con plage positiva in mezzo: il centroide negativo cade tra le due, nel vuoto; il tilt cambia di 12° con pesi uniformi (flag C1); R2 0,44. |
| 14 | 14305 | 1,2 % | B | Complesso allungato, 5 NOAA; centroidi nella parte centrale; maschera al bordo **inferiore** (113 pixel) [corretto: la prima lettura diceva «superiore»]. |
| 15 | 11887 | 1,2 % | B/C | Bipolo compatto (macchia positiva e macchie negative) dentro una maschera che include molta plage diffusa; con pesi uniformi il centroide positivo si sposta di molto verso la plage (d +22 %). S_BL di segno **opposto** al gruppo; record di controllo quasi nullo (R2 0,03). Secondo contributo positivo alla sensibilità bitmap ≥ 1 (+1,1 %). |
| 16 | 8206 | 1,2 % | A | Bipolo con plage; coerente. |
| 17 | 11727 | 1,2 % | **C** | Due bipoli nella stessa HARP (macchie negative a x ≈ 450 e ≈ 1030): il centroide negativo cade tra le due; d cambia del 47 % con pesi uniformi; asse corto (6,5·10⁹ cm) e tilt poco robusto. S_BL di segno **opposto** al gruppo. |
| 18 | 11430 | 1,1 % | B | Complesso con 10 NOAA e maschera in più pezzi; centroidi nella parte centrale; maschera al bordo inferiore (65 pixel); record di controllo di segno opposto (R2 −1,07). |
| 19 | 13911 | 1,1 % | B/C | Due macchie negative in alto, plage positiva al centro, campo negativo diffuso a destra; centroide negativo tra le concentrazioni; Δtilt −6° con pesi uniformi; maschera al bordo inferiore (143 pixel). |
| 20 | 12589 | 1,1 % | **C** | Regione principale a destra più un bipolo separato a sinistra, entrambi nella maschera (4 NOAA): il centroide positivo è trascinato verso la plage del bipolo di sinistra e cade tra le due regioni. |

## 2. Controlli (10 HARP estratte a caso tra le restanti; quota ≤ 0,11 % ciascuna, 13169 la maggiore con 0,109 %)

| HARP | Classe | Osservazione |
|---|---|---|
| 7821 | A | Bipolo pulito (macchia negativa, plage positiva); coerente. |
| 7883 | A/D | Regione piccola (Φ 5,9·10²⁰ Mx), bipolo riconoscibile ma debole; molto campo fuori maschera (M2 1,1); record di controllo di segno opposto. |
| 10658 | A/B | Regione moderata con 4 NOAA; piccola regione separata inclusa in basso; coerente. |
| 11248 | **D** (quasi unipolare) | Plage quasi interamente positiva (sbilancio 0,996, 9 pixel negativi sopra soglia, nessun NOAA): tilt 102°, Hale −1. Valido per P1 (entrambe le polarità non vuote), **fuori da S** per il filtro di P2 (≥ 20 pixel per polarità); contributo trascurabile. |
| 11263 | **C** | Due bipoli distinti (sinistra e destra); il centroide negativo cade tra i due; tilt 179,8°, S_BL quasi nullo; il record di controllo è 16 volte più grande. |
| 12054 | **D** (quasi unipolare) | Regione quasi interamente negativa (sbilancio 0,999, 4 pixel positivi sopra soglia); leading instabile tra varianti, Hale −1; la legenda copre parte del bordo alto della scheda. Valido per P1, **fuori da S**; contributo trascurabile. |
| 12623 | A | Bipolo pulito; nessuna segnalazione. |
| 13147 | D (frammentata) | Plage positiva al centro con campo negativo diffuso in più contorni; sbilancio 0,55; tilt −178°, S_BL quasi nullo. In S. |
| 13169 | **D** (frammentata) | Quattro contorni separati di plage di entrambe le polarità (sbilancio 0,38: **non** quasi unipolare [corretto]), nessun NOAA: bipolo mal definito, i centroidi stanno in blob diversi. In S; è il controllo con la quota maggiore (0,109 %). |
| 13411 | **D** (quasi unipolare) | Regione minuscola (3,5·10²⁰ Mx), sbilancio 0,947, 24 pixel negativi; centroide negativo al bordo superiore della maschera; tilt −102°. Valido per P1, **fuori da S** (Φ < 10²¹ Mx); contributo trascurabile. |

## 3. Sintesi (corretta dopo la seconda lettura; la versione della prima lettura è in `7d36b59`)

- **Errori confermati (classe E): nessuno.** Nelle 30 schede non ho riconosciuto errori geometrici
  macroscopici: polarità coerenti con la mappa, marker dei centroidi nelle concentrazioni di campo o
  tra i contributi che li determinano. **L'appartenenza del campo a regioni fisiche o ad altre HARP
  non è stata verificata**: dalla sola scheda ritagliata non si può stabilire se un blob appartenga a
  un'altra patch.
- **Dominanti (20), conteggio per etichetta come in tabella:** 3 A, 1 A/B, 7 B, 4 B/C, 5 C (11487,
  9680, 11907, 11727, 12589). Quote di Σ|S_BL| del gruppo: A 4,26 %, A/B 1,58 %, B 15,28 %, B/C 7,18 %,
  C 6,76 % (totale 35,06 %); B + B/C + C portano il 29,2 %. Tre HARP (11487, 11887, 11727) hanno
  S_BL di segno opposto a quello del gruppo e contribuiscono alla cancellazione descritta in
  `docs/EXPLORATORY_RESULTS.md` §3. [La prima lettura riportava «5 A, 10 B, 5 C più 4 intermedi»,
  incoerente con la tabella.]
- **Controlli (10):** 2 A, 1 A/B, 1 A/D, 1 C, 5 D; dei cinque D, due sono quasi unipolari (11248,
  12054; sbilancio > 0,95) e tre a morfologia frammentata o sbilanciata (13147, 13169, 13411; 13411
  ha sbilancio 0,947). I cinque D insieme portano lo 0,12 % di Σ|S_BL| del gruppo: una descrizione
  del contributo qui, non una misura d'impatto su T3 o sull'efficienza. [La prima lettura diceva
  «5 quasi unipolari o in decadimento con sbilancio > 0,95», sbagliato per tre su cinque.]
- **Validità P1 e filtro P2 [corretto].** P1 (`measure.quality`) richiede solo entrambe le polarità
  non vuote e grandezze finite; il limite di **20 pixel per polarità** è un filtro del campione S di
  P2 (`run_p2.samples`, con Φ ≥ 10²¹ Mx e le altre condizioni). Per questo 11248 (9 pixel negativi),
  12054 (4 positivi) e 13411 (24 negativi ma Φ < 10²¹ Mx) sono nella serie P1 ma **fuori da S**,
  mentre 13147 e 13169 sono in S.
- **Centroidi tra concentrazioni separate** (classe C): sono visibili nelle schede e possono essere
  la conseguenza della media pesata tra i contributi che li determinano; non costituiscono errori.
- **Che cosa ne segue, e che cosa no.** Le classi B, C e D non sono errori: derivano dalla
  definizione «una misura per HARP, non per regione fisica» (P1) e dai criteri di validità e di
  selezione. Per le HARP dominanti il «tilt» misurato è spesso quello di un complesso e, nei casi C,
  una media tra concentrazioni distinte: l'interpretazione come bipolo di Joy è più debole di quella
  delle regioni singole. S_BL è un proxy della sorgente calcolato da flusso, centroidi, geometria e
  convenzione di Hale; non è il dipolo del complesso né il campo polare dopo il trasporto. Nessuna
  classe va usata per rimuovere HARP o per rilanciare T3 a posteriori; uno studio su segmentazione
  in sotto-regioni o su un criterio di bilancio richiede un piano proprio, registrato prima, con la
  dichiarazione di ciò che è già stato osservato qui.
- **Limiti dell'esame:** un solo lettore per la prima lettura; seconda lettura esterna non cieca
  (§4); schede a risoluzione ridotta; nessuna verifica con segmentazioni delle patch vicine, mappe di
  contesto o serie temporali; le etichette miste sono di confine.

## 4. Seconda lettura esterna (2026-11-13, ZIP `7d36b59`)

Il revisore ha aperto e letto tutte le 30 immagini (note HARP per HARP in artefatti esterni al
repository), dopo aver letto la prima lettura: non è uno studio di concordanza tra lettori
indipendenti. Non ha confermato errori di misura e non ha rilevato errori macroscopici nei marker.
Ha chiesto cinque correzioni, tutte recepite sopra con la segnalazione «[corretto]»: (1) i 20 pixel
per polarità sono un filtro di P2, non di P1, e 11248, 12054 e 13411 sono fuori da S; (2) solo due
dei cinque D hanno sbilancio > 0,95 e 13169 non è quasi unipolare; «decadimento» non è accertabile
da un istante; (3) conteggi delle classi riallineati alle righe (3 A, 1 A/B, 7 B, 4 B/C, 5 C; controlli
2 A, 1 A/B, 1 A/D, 1 C, 5 D); (4) nessuna conclusione categorica sull'assenza di campo di altre HARP;
(5) per 12094 e 14305 il contatto della maschera è sul bordo inferiore (verificato: 572 e 113 pixel,
zero sugli altri lati; anche 13911, 9680 e 11430 toccano solo il bordo inferiore). Le due letture
restano giudizi distinti; gli output non sono stati toccati.

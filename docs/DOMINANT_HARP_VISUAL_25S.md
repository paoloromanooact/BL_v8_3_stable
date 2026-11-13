# Esame visivo delle 30 schede del gruppo 25S (HARP dominanti e di controllo)

Stato: **esame fatto il 2026-11-13 da un solo lettore (l'agente, modello Fable 5.1), sulle schede
`figures/DOMINANT/<HARPNUM>.png` prodotte dal controllo completo (`36676a9`, piano `f805c5a`).** È il
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
- **B** — complesso di più regioni (NOAA ≥ 2) con polarità intrecciate: la misura è il dipolo netto del
  complesso, come previsto dalla definizione «una misura per HARP» di P1; centroidi dentro le
  concentrazioni di campo.
- **C** — complesso in cui almeno un centroide cade **tra** regioni distinte (nel vuoto tra due
  concentrazioni della stessa polarità) o è trascinato da plage diffusa lontana: tilt e separazione
  sono medie poco interpretabili come bipolo; sensibilità alla pesatura o al record.
- **D** — regione quasi unipolare o in decadimento (sbilancio di flusso > 0,5, plage frammentata),
  con bipolo mal definito; contributo a S_BL trascurabile.
- **E** — errore confermato (maschera che include campo di un'altra HARP, polarità invertite rispetto
  alla mappa, geometria incoerente con l'immagine).

## 1. Dominanti (rango per |S_BL|, quota di Σ|S_BL| del gruppo)

| Rango | HARP | Quota | Classe | Osservazione |
|---|---|---|---|---|
| 1 | 11786 | 3,8 % | B | Complesso lungo circa 6000 px con 11 regioni NOAA; la maschera ≥ 33 copre una catena di regioni più blob separati a destra; i centroidi stanno nella parte centrale, separazione piccola rispetto all'estensione. Molto flusso forte fuori maschera (M2 0,86). Il record di controllo dà un S_BL molto diverso (R2 0,12). |
| 2 | 11662 | 3,5 % | B/C | Grande regione con macchia negativa leading e plage positiva estesa; la maschera include una vasta plage diffusa in basso a sinistra che trascina il centroide positivo (d cambia del 15 % con pesi uniformi). Con bitmap ≥ 1 S_BL cambia di −2,9 % di Σ\|S_BL\| del gruppo: il contributo più sensibile alla maschera. |
| 3 | 12094 | 3,2 % | B | Catena allungata con 11 regioni NOAA; contorno della maschera vicino al bordo sinistro (possibile troncamento); regioni separate a destra incluse. Centroidi nella parte centrale. |
| 4 | 11513 | 3,0 % | B | Regione grande con 5 NOAA, polarità intrecciate; centroidi coerenti. |
| 5 | 11487 | 1,7 % | **C** | Due complessi distinti nella stessa HARP: bipolo compatto in alto a sinistra e regione diffusa a destra. Il centroide negativo \|Br\| cade nel vuoto tra i due (quello uniforme ancora più a destra). S_BL ha segno **opposto** a quello del gruppo e il record di controllo ha segno opposto (R2 −0,05). |
| 6 | 13691 | 1,6 % | B | Complesso con più macchie e 5 NOAA; centroidi dentro le concentrazioni; sensibilità alla pesatura (d +24 % con pesi uniformi, flag C1). |
| 7 | 10779 | 1,6 % | A/B | Una regione grande (4 NOAA ravvicinate); bipolo riconoscibile; centroidi coerenti. |
| 8 | 9680 | 1,6 % | **C** | Bipolo principale a destra più una plage estesa e lontana in basso a sinistra, inclusa nella maschera (3 NOAA): il centroide positivo è trascinato verso la plage lontana, l'asse è lungo. Record di controllo di segno opposto (R2 −0,04). Maschera al bordo. |
| 9 | 8950 | 1,5 % | A | Regione singola grande (macchia negativa, plage positiva); coerente. |
| 10 | 9559 | 1,5 % | A | Macchia negativa grande e plage positiva; coerente. |
| 11 | 11930 | 1,4 % | B | Catena di 9 regioni NOAA su circa 5000 px; centroidi nella parte centrale; M2 0,69. |
| 12 | 12261 | 1,4 % | B/C | Catena di 6 NOAA; il centroide positivo \|Br\| è spostato verso una regione separata a sinistra. |
| 13 | 11907 | 1,2 % | **C** | Due macchie negative distinte (in alto e in basso) con plage positiva in mezzo: il centroide negativo cade tra le due, nel vuoto; il tilt cambia di 12° con pesi uniformi (flag C1); R2 0,44. |
| 14 | 14305 | 1,2 % | B | Complesso allungato, 5 NOAA; centroidi nella parte centrale; maschera al bordo superiore. |
| 15 | 11887 | 1,2 % | B/C | Bipolo compatto (macchia positiva e macchie negative) dentro una maschera che include molta plage diffusa; con pesi uniformi il centroide positivo si sposta di molto verso la plage (d +22 %). S_BL di segno **opposto** al gruppo; record di controllo quasi nullo (R2 0,03). Secondo contributo positivo alla sensibilità bitmap ≥ 1 (+1,1 %). |
| 16 | 8206 | 1,2 % | A | Bipolo con plage; coerente. |
| 17 | 11727 | 1,2 % | **C** | Due bipoli nella stessa HARP (macchie negative a x ≈ 450 e ≈ 1030): il centroide negativo cade tra le due; d cambia del 47 % con pesi uniformi; asse corto (6,5·10⁹ cm) e tilt poco robusto. S_BL di segno **opposto** al gruppo. |
| 18 | 11430 | 1,1 % | B | Complesso con 10 NOAA e maschera in più pezzi; centroidi nella parte centrale; record di controllo di segno opposto (R2 −1,07). |
| 19 | 13911 | 1,1 % | B/C | Due macchie negative in alto, plage positiva al centro, campo negativo diffuso a destra; centroide negativo tra le concentrazioni; Δtilt −6° con pesi uniformi; maschera al bordo in basso. |
| 20 | 12589 | 1,1 % | **C** | Regione principale a destra più un bipolo separato a sinistra, entrambi nella maschera (4 NOAA): il centroide positivo è trascinato verso la plage del bipolo di sinistra e cade tra le due regioni. |

## 2. Controlli (10 HARP estratte a caso tra le restanti; quota ≤ 0,1 %)

| HARP | Classe | Osservazione |
|---|---|---|
| 7821 | A | Bipolo pulito (macchia negativa, plage positiva); coerente. |
| 7883 | A/D | Regione piccola (Φ 5,9·10²⁰ Mx), bipolo riconoscibile ma debole; molto campo fuori maschera (M2 1,1); record di controllo di segno opposto. |
| 10658 | A/B | Regione moderata con 4 NOAA; piccola regione separata inclusa in basso; coerente. |
| 11248 | **D** | Plage quasi interamente positiva (sbilancio 0,996, nessun NOAA): il centroide negativo viene da pochi pixel; tilt 102°, Hale −1. Record valido per P1 ma non è un bipolo; contributo trascurabile. |
| 11263 | **C** | Due bipoli distinti (sinistra e destra); il centroide negativo cade tra i due; tilt 179,8°, S_BL quasi nullo; il record di controllo è 16 volte più grande. |
| 12054 | **D** | Regione quasi interamente negativa in decadimento (sbilancio 0,999); il centroide positivo viene da pochi pixel al bordo destro della maschera; leading instabile tra varianti, Hale −1. Contributo trascurabile. |
| 12623 | A | Bipolo pulito; nessuna segnalazione. |
| 13147 | D | Plage positiva al centro con campo negativo diffuso in più contorni; sbilancio 0,55; tilt −178°, S_BL quasi nullo. |
| 13169 | **D** | Quattro contorni separati di plage frammentata di entrambe le polarità, nessun NOAA: non è un bipolo; i centroidi stanno in blob diversi. |
| 13411 | **D** | Regione minuscola (3,5·10²⁰ Mx) quasi unipolare positiva; centroide negativo da pochi pixel al bordo superiore; tilt −102°. Contributo trascurabile. |

## 3. Sintesi

- **Errori confermati (classe E): nessuno.** In nessuna delle 30 schede la maschera include campo
  riconoscibile di un'altra HARP, le polarità sono coerenti con la mappa e la geometria dei
  centroidi corrisponde alle concentrazioni di campo o alla loro media.
- **Dominanti:** 5 di classe A (bipolo singolo), 10 di classe B (complessi multiregione, misura =
  dipolo netto del complesso), 5 di classe C (centroide tra regioni distinte: 11487, 9680, 11907,
  11727, 12589) più 4 casi intermedi B/C. Le classi B e C insieme portano il 30 % circa di Σ\|S_BL\|
  del gruppo tra le 20 dominanti (su 35,1 % esaminato). Tre dominanti di classe C o B/C hanno S_BL
  di segno opposto a quello del gruppo (11487, 11887, 11727): contribuiscono alla cancellazione
  già descritta in `docs/EXPLORATORY_RESULTS.md` §3.
- **Controlli:** 3 bipoli puliti, 1 classe C, 5 di classe D (quasi unipolari o in decadimento, con
  contributo trascurabile) e 1 debole. I record di classe D sono validi per il criterio di P1
  (almeno 20 pixel per polarità sopra soglia) pur avendo sbilancio di flusso > 0,95.
- **Che cosa ne segue, e che cosa no.** Le classi B e C non sono errori: sono la conseguenza della
  definizione «una misura per HARP, non per regione fisica» (P1), già dichiarata come limite. Per
  le HARP dominanti, però, il «tilt» misurato è spesso quello di un complesso, e nei casi C è una
  media tra regioni distinte: i contributi maggiori a S_BL e all'efficienza hanno un'interpretazione
  come bipolo di Joy più debole di quella delle regioni singole. Questo non cambia nessun risultato
  e non autorizza a rimuovere HARP. Se si vorrà trattarlo, serve un piano proprio (per esempio un
  criterio di separazione in sotto-regioni o un criterio di bilancio di flusso per la validità),
  da registrare prima e seguito da un ricalcolo dichiarato: le classi C e D sono candidate
  naturali per quel piano, che non parte da questo esame.
- **Limiti dell'esame:** un solo lettore, schede a risoluzione ridotta, nessuna verifica con i
  magnetogrammi vettoriali o con l'evoluzione temporale; le classi A/B e B/C sono di confine.

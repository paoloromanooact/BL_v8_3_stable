# Controllo finale delle bozze SFT in 790cad1

25 novembre 2026, Codex. Punto 2 rev. 3 (SHA `0f96fe660af47f88fc63a86b32240065aca59040a7ab994f25c37a674c0622c3`)
e punto 3 rev. 2 (SHA `c3f4d2c8b3f18a5b91edd5664e96571143f2fd10a97133eec1ff2a0c10ce4389`).

**Le correzioni scientifiche principali sono recepite. Prima del congelamento
restano le specifiche numeriche e di dominio/split sotto.** Nessun pixel
osservato letto, nessun download o pilota eseguito: le prove riguardano
una discretizzazione sintetica e il calcolo del margine dichiarato.
Il core preparatorio b3f1745 non e oggetto di approvazione del codice qui.

## 1. Punto 2: risposta alle due scelte aperte

### N=400 e un punto di partenza; Crank–Nicolson a un giorno non e positivo

Con il solo termine di diffusione, stesso R, eta, N e passo della bozza,
un impulso iniziale non negativo genera dopo un passo un minimo di
**-0,277391**. Il flusso rimane 1 entro arrotondamento. Backward Euler sullo
stesso operatore conserva massa e positivita. Questa e una prova
sintetica di un operatore FV conservativo in s, non una simulazione del pilota.

Crank–Nicolson e stabile ma non automaticamente positivo. Il problema e
rilevante proprio per il bipolo puntiforme. Le prove sul solo dipolo l=1
possono non accorgersi delle oscillazioni dei modi a piccola scala.

Per conservare la scelta CN con una modifica limitata propongo di fissare:
- flussi FV diffusivi e avvezione upwind del primo ordine, tali che L abbia
  coefficienti fuori diagonale non negativi e conservi la massa;
- passo effettivo `dt <= min(1 giorno, 0.9 * 2 / max_i(-L_ii))`, con ultimo
  sottopasso ridotto per arrivare esattamente ai tempi di uscita;
- test separati di massa e di positivita su impulsi e gaussiane non negative
  e sui singoli contributi delle polarita. La somma firmata puo ovviamente
  cambiare segno per cancellazione; il propagatore non deve crearne di nuovi
  da una sola polarita iniziale.

La condizione rende non negativo anche il membro destro della tappa CN,
mentre il sistema implicito ha la struttura appropriata per la positivita.
Vale soltanto per l'operatore specificato: non per un generico stencil
centrato o upwind del secondo ordine. Un'alternativa valida e Backward Euler,
oppure il propagatore esponenziale dell'operatore; scegliere e scrivere
un solo algoritmo principale prima del congelamento, non confrontarne gli
esiti fisici per scegliere il migliore.

**Convergenza:** controllare tutti i tempi richiesti, non soltanto 3 anni,
e tutti i trasporti. Per evitare divisioni per zero propongo
`|D_fine-D_coarse| <= 1e-3 * max(|D_fine|, 1e-6 D_scale)`.
La soglia e numerica, non una classificazione fisica. La regola di
raffinamento viene fissata prima e verificata sui sintetici; verificare
separatamente risoluzione e tempo, anche se il limite di positivita cambia
con N. Conservare gli scarti numerici anche per i tre casi osservati.

### Bordi del deposito: niente clamp silenzioso o celle fantasma fisiche

Oltre il primo/ultimo centro non si possono conservare contemporaneamente
massa, primo momento e pesi non negativi usando solo quei centri. Il clamp
alla cella estrema viola il momento; estrapolare puo creare pesi negativi.

Per questo pilota di regioni attive: se un pixel o un punto necessario e
fuori dal supporto dei centri, stato tecnico esplicito
`deposition_out_of_range`, conteggi e nessuna sostituzione. Non pubblicare
una misura che dichiara conservato il momento dopo averlo tagliato. Nessuna
cella fisica oltre i poli. Una rappresentazione con momenti subcella sarebbe
un'altra soluzione, ma non e necessaria qui.

Le tolleranze di conservazione non vanno divise per un flusso netto o un
momento nullo: usare la scala `sum |F|` per i due residui (F e F*s), e
D_scale per il confronto di D. Con sum |F| = 0 si applica la regola di
fallimento prevista per la misura, non un epsilon.

**Gaussiana:** specificare il dominio della quadratura, non solo il passo.
Evitare una griglia globale con passo imposto dalla sigma piu piccola.
Una costruzione locale su calotte di raggio 8 sigma, normalizzata e con
coda/errore di quadratura verificati sui sintetici, contiene il costo senza
cambiare la definizione scientifica della sensibilita. Verificare
il trattamento delle calotte attraverso i poli e il raccordo longitudinale,
senza tagli artificiali.

## 2. Punto 3: risposte alle quattro scelte aperte

### Margine e area minima

Il conto del riferimento e corretto: a 15° e 4,5 giorni risulta m=4,628°.
Non e pero il massimo della griglia di sensibilita: a Du=0,041, eta=466,8
sugli stessi latitudine e tempo, m=4,813°. Altre latitudini cambiano il
termine della rotazione. Scrivere tutte le conversioni km/R→radianti→gradi.

Usare **un solo C per tutti i modelli e trasporti dello stesso caso**,
calcolando il margine con i massimi sull'intera griglia dei parametri e
sulle latitudini della patch, non sul solo riferimento. Anche il dominio
di simulazione e la prova di bordo devono coprire quel caso massimo.
Definire la geometria dell'erosione (distanza sulla sfera o coordinate con
fattori metrici), e l'area in deg² come area solida, cioe
`sum dA/R² * (180/pi)²`.

Il margine con sqrt(4 eta dt) e un margine operativo, **non un limite
rigoroso del contributo del campo sconosciuto fuori dalla patch**: la
diffusione non ha supporto finito. Ampliare un dominio riempito di zeri
verifica il bordo numerico; non ricostruisce il campo solare mancante.
Questa assunzione resta un limite del confronto con le osservazioni.

25 deg² e accettabile come soglia operativa di copertura, non fisica.
Prima del congelamento verificare dai soli header/keyword la disponibilita
geometrica per strato dopo l'erosione: una patch piu stretta di 2m non ha
interno utilizzabile. Distinguere questa fattibilita dalla copertura finita
dei pixel che sara verificata dopo. Non adattare la soglia alla bonta
osservata delle previsioni. Se il campione si svuota, rivedere ora il disegno.

### Maschera advettata al 50%

Approvata come diagnostica operativa. Definire il trasporto dell'indicatore
materiale, cioe geometria delle aree/preimmagini o avvezione passiva
`dm/dt + u.grad(m)=0`. Non far evolvere una densita magnetica 0/1 con il
termine compressibile e chiamarla frazione d'area. Rimane il limite gia
dichiarato: flusso fuori dalla maschera non significa sola nuova emersione.

### Schema 2D e convergenza

600 s deve essere un **massimo**, con dt scelto dal CFL e dalla condizione
di positivita della tappa diffusiva CN; non un valore assunto valido per
tutte le griglie/latitudini. Lo stencil upwind del secondo ordine deve avere
un limitatore e un integratore temporale dichiarati (per esempio ricostruzione
TVD minmod e SSP-RK2 per l'avvezione). Senza limitatore puo creare
oscillazioni. Specificare l'accoppiamento delle tappe prima di implementare.

La griglia e descritta ora come uniforme in latitudine e longitudine:
usare aree `R² dphi (sin lat_top - sin lat_bottom)` e flussi con i fattori
metrici sferici, senza trattarla come una griglia uniforme in sin(lat).

Per il criterio 1e-3 non dividere per un osservabile che puo essere nullo.
Fissare scale per quantita: D con la scala di flusso iniziale e la sua
floor numerica; flussi con Phi iniziale; coordinate in angoli e differenze
circolari/assiali. Aggiungere una norma del campo oltre alle osservabili,
cosi un solo momento corretto non nasconde una mappa oscillante.
Separare convergenza e controllo del bordo 1e-6; conservare residui e casi
non valutabili. Sono controlli numerici, non intervalli osservativi.

### Split per patch sovrapposte

Usare componenti connesse di un grafo, non correzioni successive sulle
singole coppie: altrimenti una catena A–B–C puo essere divisa in modo
dipendente dall'ordine di visita.

Un arco di sovrapposizione va definito **nello spazio e nel tempo**: ad
esempio finestre [t0,t1] che si intersecano e riquadri Carrington che si
intersecano, con raccordo 0/360 e convenzione di sistema fissati. Non
collegare due patch degli stessi luoghi osservate in anni diversi soltanto
perche i riquadri geometrici coincidono. Gli archi di famiglia sono distinti.

Assegnazione proposta: eseguire la permutazione prevista, poi assegnare
ogni componente alla parte provvisoria della sua HARP di HARPNUM minimo.
La proporzione finale puo differire da 1/3–2/3: riportare conteggi per cella,
componenti e probabilita di assegnazione utilizzate nei riepiloghi, senza
spostare casi per migliorare il confronto. Con celle vuote nella verifica
nessuna stima per quella cella. Tutto prima delle mappe di sviluppo/verifica.

**Correzione editoriale:** dalla tabella in bozza le sei celle sono
66, 72, 84, 75, 447, 279: somma 1023, minimo 66, non «tutte almeno 128».
Sono comunque tutte sopra 18; il disegno nominale non cambia per questo.
I conteggi basati su T_REC sono preliminari: l'estrazione usa T_OBS come
previsto, con gli eventuali cambi dichiarati.

## 3. Stato Q4 e seguito

La richiesta riferisce ancora f0ab43a/43 prove: quel commit non chiudeva
i due dettagli di b8e38f1. Durante questo controllo e arrivata una copia
ulteriormente corretta, SHA
`a6c0a72d227c26d15f5ca584f22bdf12e63c3222028ffe4eaab3f33aa0233398`.

Su questa fotografia: base completa sintetica di due realizzazioni
accettata, sei vecchie alterazioni rifiutate; anche i cinque controlli
specifici sui conteggi e sui bersagli nulli ora passano. Il campo META
aggiuntivo passa soltanto nella fixture sintetica, come gia ammesso.
Il gate di hash dei file reali non trova problemi. Nessun --check reale,
nessuna lettura di risultati scientifici Q4 o rilancio.

**Via tecnico al riconteggio reale per questo SHA**, dopo che la versione
e committata e il suo selftest completo e conservato positivo; non per
il vecchio f0ab43a. Se il codice cambia, rivedere la nuova differenza.
Dopo --check: conservare la ricevuta completa prima della lettura e del
rapporto; la decisione sul catalogo MDI resta successiva e separata.

Per SFT: recepire le specifiche sopra, controllare la fattibilita geometrica,
poi congelare le bozze aggiornate. Le scelte fisiche, gli obiettivi e le
correzioni principali sono confermati; non occorre aprire nuove linee.
Il codice verra rivisto prima dei piloti reali.

Prove della revisione: `scripts/sft_790cad1_numeric_review_probe.py` e
`docs/SFT_790cad1_NUMERIC_REVIEW_RESULTS.json`; regressioni Q4 e hash della
fotografia in `docs/SFT_790cad1_Q4_REVIEW_RESULTS.json`. Nessuna ricevuta
scientifica viene emessa da queste prove.

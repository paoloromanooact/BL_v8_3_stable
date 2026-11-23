# Revisione Codex della nota di diagnosi S2 — 23 novembre 2026

Oggetto: `docs/T3_MWO_S2_DIAGNOSIS_NOTE_DRAFT.md`, commit a252063; README per il deposito in 2f6d068.
Nessuna diagnosi sui sottoinsiemi reali eseguita in questa revisione. Nessuna nuova stima T3.
L'impostazione descrittiva, successiva alla lettura e senza modifiche all'esito precedente è appropriata.
Prima dell'implementazione recepire le precisazioni seguenti nella nota; prima della corsa reale rivedere il codice.

## 1. D1: ammessa come scomposizione descrittiva, non come nuovo test

Usare esattamente gli stessi record, ordinamento, pesi, attività, sin|latitudine MWO| e matrice ridotta
per le tre risposte. Definire u = gamma_MWO - gamma_WL, d = axial(u), r = d - u e usare la stessa riga g:

`g d = g gamma_MWO - g gamma_WL + g r`.

Riportare tutti i termini, anche g r, e il residuo numerico dell'identità. La quota di riavvolgimenti
va ricavata da r != 0 con tolleranza numerica dichiarata, non soltanto da |u| > 90°: l'implementazione
congelata mappa +90° in -90° (r = -180°). Aggiungere prove sintetiche con riavvolgimenti in entrambi
i versi e al taglio +90°, oltre al caso senza riavvolgimento.

SE e intervalli M per le due componenti sono ammessi solo come nominali non validati per queste risposte.
Non sottrarre i loro SE, non trattare le componenti come indipendenti e non produrre verdetti o etichette
T3 per gamma_WL. La scomposizione non identifica quale strumento o fenomeno causi la differenza.
Sostituire la domanda «se viene dai tilt MWO o da quelli in luce bianca» con «come si scompone, sullo
stesso disegno, fra le due risposte e il termine assiale».

## 2. Soglie di disponibilità e differenze grandi

300 record: accettabile come soglia operativa di presentazione del fit, non come garanzia di precisione,
indipendenza o validità. Riportare anche numero di CR, blocchi di 6 CR, composizione per ciclo/epoca/emisfero,
intervallo di attività e n_eff = (somma pesi)^2 / somma pesi^2, con identificabilità e stato del fit.
Un fit non identificabile o in errore mantiene una riga esplicita; nessuna sostituzione o adattamento della soglia.
Conservare i riassunti D5 anche per i gruppi piccoli. Riportare anche i riassunti N/S, già previsti come
suddivisione nella richiesta iniziale; non aprire ulteriori fit N/S incrociati con tutte le categorie.

|d_WL| > 45°: accettabile come sensibilità scelta dopo la lettura, senza interpretarla come errore di misura.
La selezione è sulla risposta: il cambiamento di pendenza può derivare dal taglio stesso. Non usare D6 per
correggere il catalogo o scegliere una nuova analisi principale. Numero e quota rimossi per attività ed emisfero.

## 3. Togliere la classificazione finale basata su una SE

Eliminare «eterogeneità localizzata», «eterogeneità diffusa» e «troppi sottoinsiemi».
L'assenza di uno spostamento > una SE non dimostra omogeneità o eterogeneità diffusa; «troppi» non è definito.
D2 è un'esclusione, D3/D4 sono fit su sottoinsiemi: i loro spostamenti non hanno la stessa interpretazione.
Non aggiungere adesso i complementi D3/D4 per salvare la classificazione.

Riportare soltanto, per ogni fit previsto, beta, SE nominale, intervallo, numerosità, stato, differenza
rispetto alla beta S2 completa e tale differenza divisa per il SE completo non arrotondato, letto da STABILITY.json.
Questo rapporto è una scala descrittiva, non un test di differenza: i fit sono correlati e gli stimandi cambiano
con il sottoinsieme. Distinguere le colonne «subset» e «leave-one-epoch-out». Nessuna categoria riassuntiva finale.
Eliminare anche il flag della stima dentro ±C: C è il margine del disegno S2 completo, non un margine validato per
ogni popolazione/sottoinsieme. Intervalli e stato bastano; nessuna promozione a equivalenza o causalità.

## 4. Rendere univoci terzili, bootstrap e conteggi

Prima di eseguire, fissare nella nota:
- terzili non pesati con quantili NumPy lineari sui 4694 record completi, confini tenuti fissi in ogni gruppo;
  `searchsorted(confini, valore, side="right") + 1`, pari valori mai separati; se un terzile è vuoto, dichiararlo;
- D2 esattamente le sei esclusioni elencate; D3 esattamente Gyula/altre fonti, con etichetta separata per fonte
  mancante e relativo conteggio; D4 esattamente le nove categorie. Nessuna scelta post hoc della variabile migliore;
- D5 produce n, mediana non pesata, media pesata con Phi e quota non pesata |d_WL| > 45°. Specificare che il bootstrap
  fornisce intervalli per tutte e tre le statistiche, mentre il conteggio resta descrittivo;
- blocchi CR ancorati al minimo CR dell'intero S2: floor((CR - CR_min)/6), mantenendo insieme i due emisferi.
  Le estrazioni dei blocchi dell'insieme completo sono comuni a tutti i riassunti; poi si applicano i gruppi e i
  terzili fissi. 2000 estrazioni, unico RNG dal seme fissato; registrare conteggi delle repliche senza record o con
  denominatore nullo. Nessuna nuova estrazione per rimpiazzarle. Riportare percentili solo con almeno 1900 repliche
  valide; altrimenti intervallo mancante con causa (soglia tecnica, non prova di copertura);
- ordinamento canonico dei record e delle uscite, metodo dei percentili e nessun bootstrap di M dentro D5.

## 5. Seme e provenienza

Verificato 69 600 001 contro l'elenco effettivo di 76 000 semi della griglia, l'elenco del benchmark,
S1 = 69 000 001, Joy = 69 500 001 e gli intervalli USED: nessuna collisione. Il selftest deve ripetere questi
confronti, non solo controllare c < 90. Le 2000 estrazioni da un RNG non corrispondono a 2000 semi consecutivi.

Conservare una versione finale della nota prima della corsa e registrarne lo SHA nel META. Verificare ricevute
complete e hash dei prodotti sorgente prima della lettura, join univoci per gruppo/giorno e 4694 righe con stato WL
valido. Assenza di sovrascrittura e scrittura atomica. Non modificare moduli o prodotti della catena T3 precedente.

Nel riconteggio: g indipendente per D1/D2, identità con termine assiale, stessi gruppi/chiavi, perdita dei record,
quantili e riassunti D5. Il richiamo comune a M per confronto va dichiarato come dipendenza, non come SE verificato
indipendentemente. Provare su sintetici casi al taglio assiale, terzili con pari valori/vuoti, gruppi <300,
non identificabilità e repliche bootstrap vuote. Nessun dato reale richiesto per questi test.

## 6. README del deposito

Il README distingue bene popolazione, precedenti e limiti. Due precisazioni prima dell'impacchettamento:
- in §7 dire che l'intervallo non è contenuto nel margine di equivalenza, anziché «This is neither within…»;
- il README definitivo non va sostituito dentro il rilascio verificato senza ricostruirne il manifesto: preparare
  un pacchetto di deposito separato con proprio META/SHA e legame al rilascio originale. Licenza, autori e deposito
  restano da concordare; nessuna pubblicazione o contatto autorizzati qui.

La verifica di disponibilità di Li & Ulrich è quella riportata da Claude, non una nuova ricerca in questa revisione.
La mancata disponibilità durante la ricerca non prova che un catalogo pubblico non esista.

## Esito della revisione

Via alla revisione della nota e all'implementazione con queste precisazioni. Non ancora alla corsa reale:
prima rivedere codice e prove sintetiche. Il risultato T3 precedente rimane descrittivo, qualunque sia la diagnosi.

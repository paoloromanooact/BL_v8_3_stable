# Revisione del codice della diagnosi S2 — Codex, 23 novembre 2026

Oggetto: commit 9106186, nota finale dd0c035d…, runner ef27c4d7…, riconteggio f1a0aa82….
Selftest ripetuti: runner 21/21, riconteggio 7/7. Nessuna corsa o nuova lettura dei tilt reali.
La metodologia descrittiva resta approvata; non ancora il via alla corsa reale, per i difetti sotto.

## Tre punti richiesti

1. **Terzili:** corretta e conforme alla nota la regola `searchsorted(..., side="right")`.
   Se il primo quantile coincide con il minimo, il primo terzile può restare vuoto. Non dividere i pari valori
   né riempire il terzile. Il riconteggio own_terc ricostruisce la stessa regola anche con i due quantili uguali.
2. **own_design:** costruzione separata corretta, inclusi riferimento di epoca per emisfero e riduzione del rango.
   Verificati sui soli sintetici: base, solo Nord, singola epoca, attività costante non identificabile e riscalatura
   uniforme dei pesi. Identificabilità concorde; scarto massimo fra g indipendente e g dell'analisi 1,67e-16.
   Dipendenze numeriche NumPy condivise, ma nessun richiamo ad A.columns/reduce/g_row nel calcolo indipendente.
3. **s2_fit comune:** ammissibile e dichiarato come dipendenza. Non costituisce verifica indipendente degli SE.
   Va però richiamato anche per controllare i risultati delle componenti D1, che ora non sono confrontati.

## Rilievi da correggere

### 1. Guardie dei prerequisiti: ricevute e manifesti vuoti accettati

`chain_problems()` accetta passed=total=0, checks=[], partial=false con legame al META, e prodotti_sha256={}.
Il controesempio usa solo directory sintetiche e restituisce nessun problema.

Usare la semantica stretta già adottata nella catena T3: interi non booleani, total>0, passed=total,
checks della lunghezza esatta e ogni ok is True, partial false e legame al META obbligatorio.
Non affidarsi alla verità generica di c.get("ok") né a all() su un elenco vuoto.
Verificare insiemi attesi di prodotti e hash, anche della stima (ora il ciclo degli hash controlla solo STAB/REL).
Legare il DESIGN al META corrente del catalogo e verificare i legami STAB/EST/REL ai prodotti correnti.
Gestire file mancanti o JSON incompleti come rifiuto esplicito. Prove: base valida, 0/0, conteggi booleani,
check con ok non booleano, manifesti vuoti, prodotto/stima/disegno modificato e legame obsoleto.

### 2. Il riconteggio non confronta tutte le uscite dichiarate

Controesempi con hash dei prodotti aggiornati e base sintetica valida:
- DECOMPOSITION.json: SE e limiti di M_gamma_wl cambiati a 999/-999/+999 → ricevuta ancora positiva;
- FITS.csv: phi principale cambiato a 123 e phi_at_bound a false → ancora positiva, anche passando fit=…;
- COUNTS.csv: conteggio del terzile 1 dell'area e rimossi D6 per emisfero cambiati a 99999 → ancora positiva.

Il richiamo a fit nel probe usa s2_fit comune con cache delle risposte sintetiche; il check reale esegue gli stessi
confronti di SE/limiti, che attualmente non includono questi campi. Non sono esempi di dati reali sbagliati:
mostrano campi che la ricevuta potrebbe certificare senza verificarli.

Richiesto:
- D1: ricalcolare anche g_r_from_minus180/plus180, massimo scarto d salvato, n, identificabilità e tolleranza;
  confrontare tutti i parametri/SE/limiti delle due componenti col calcolo M comune, dichiarando la dipendenza;
- FITS: verificare state, identificabilità, tutti i parametri M e flag di bordo, non soltanto beta/SE/limiti;
  ricontare n_blocks, composizione ciclo/epoca/emisfero e A_min/A_max. Gestire correttamente le righe in errore
  senza pretendere beta finito: errore M è uno stato da riportare, non una riga riuscita;
- COUNTS: insieme esatto di chiavi univoche, tutti i conteggi, confini dei terzili, rimossi e quote per attività
  ed emisfero, anche terzili vuoti; per denominatore zero quota mancante con causa, non zero tramite max(1,n);
- SUMMARIES: insieme esatto di chiavi univoche e cause di intervallo mancante, oltre ai numeri già ricontati.
Aggiungere le manomissioni sopra ai selftest. La base deve continuare a passare.

### 3. Ricevuta reale e provenienza

`check()` scrive sempre partial=false, anche con sub sintetico, reps ridotte o senza fit/nota.
Il comando reale non richiede che gli output siano conservati in Git prima del riconteggio e confronta gli input
soltanto con le chiavi che trova nel META: un elenco incompleto o vuoto non garantisce la provenienza promessa.

Richiedere un insieme esplicito completo degli input (compresi i moduli P2f/p2d usati da M), gli hash effettivi,
nota e prodotti committati e invariati. Verificare script/moduli e input della corsa; registrare hash prima del
calcolo e controllarli di nuovo prima di scrivere, così META non descrive solo lo stato successivo al calcolo.
Le chiamate sintetiche, con dati iniettati, reps ridotte, nota assente o fit omesso producono ricevute partial=true;
una ricevuta completa richiede il percorso reale con tutti i controlli. Niente scrittura nella cartella reale
delle ricevute nei test. Provare anche la mutazione di un input o della nota dopo la corsa.

## Artefatto e ordine successivo

`scripts/t3_mwo_s2_review_probe.py` conserva la fixture e i controesempi; non legge dati osservativi.
I log dei selftest eseguiti da Codex restano in /tmp/bl_s2_runner_selftest.log e /tmp/bl_s2_recount_selftest.log;
il probe originale e il suo JSON sono in /tmp/bl_s2_code_review/. I percorsi /tmp sono diagnostici, non sorgenti
per riprodurre risultati scientifici.

Claude corregge runner e riconteggio, mantenendo invariata la nota finale e i criteri descrittivi. Queste correzioni
rendono fedeli i controlli alla nota: non cambiano terzili, analisi, soglie o risultato T3. Nuova revisione prima di
--run; poi conservazione, --check, ricevuta e rapporto, come già concordato. Nessuna simulazione lunga richiesta.

## Chiusura dopo c675d39 — 23 novembre 2026

Rilievi chiusi. Ripetuti runner 33/33, riconteggio 22/22 e probe indipendente:
base sintetica accettata, intervalli D1/parametri M/conteggi alterati rifiutati,
ricevute 0/0 e manifesti vuoti rifiutati. Le prove includono nota e input modificati,
chiavi e composizioni dei gruppi, stati espliciti e ricevute sintetiche parziali.

Verificati anche, senza misura o diagnosi reale: chain_problems() senza problemi,
nessun input mancante, seme disgiunto. La nota finale e il codice coincidono con
c675d39. Il controllo completo richiama M come dipendenza dichiarata; la matrice,
le pendenze puntuali e i riassunti sono ricostruiti separatamente. Non si afferma
una nuova verifica indipendente degli SE della procedura comune.

check() restituisce un booleano e rende disponibile la ricevuta in last_receipt:
ammissibile; la scrittura completa richiede il percorso reale e i prerequisiti.
La tolleranza di close() su A_min/A_max è assoluta 1e-12, non relativa come nella
nota di consegna; è adeguata per questo confronto numerico dei valori normalizzati.
Non modifica il disegno, la stima o le soglie della nota finale.

**Via al --run della diagnosi descrittiva**, poi conservazione degli output prima
della lettura, --check, conservazione della ricevuta e rapporto. Nessun nuovo
verdetto, nessuna correzione del catalogo o di beta3. Non eseguire il --estimate
T3 una seconda volta. Questa revisione non ha eseguito --run.

Hash verificati:
- `docs/T3_MWO_S2_DIAGNOSIS_NOTE.md`: `dd0c035dfae648860a9d0204b7290ba315fe02be5bde409b402a582bfe359687`
- `scripts/t3_mwo_s2_diagnosis.py`: `d45dbd5272987c4a99777a79d90c568d1eeb5835899c0fc404a0b49b011aa4ba`
- `scripts/t3_mwo_s2_diagnosis_recount.py`: `ae2b416949ec9d88acadd107dbe95c1ea1d3e5885f3a2150692a9c792b7e75ca`

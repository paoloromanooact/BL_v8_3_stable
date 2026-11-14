# Revisione incrociata del 2026-11-14 — verificatore T5-D2, scheletro T5-D2, morfologia

Revisore: Claude Opus 5.5 (Claude Code). Commit esaminato `f38d351`, in sola lettura.
Revisione incrociata, **non cieca** rispetto al progetto e **non statisticamente indipendente**;
per la morfologia il revisore è lo stesso modello del lettore 1. Output `ORACLE_*` di T5-D2 non aperti.
Un secondo revisore ha letto questo rapporto e ne ha condiviso le conclusioni, con due precisazioni
recepite qui: «nessun problema bloccante» vale soltanto per le attività dei punti 1–3 e non approva
le conclusioni di T5-D2; documentare la prova esterna migliora la trasparenza ma **non colma** il
limite della verifica degli SE dei bracci, e la sua sufficienza dipende dalle conclusioni che si
vorranno sostenere. Il giudizio conclusivo resta aperto fino ai punti 4 e 5.

Testo del rapporto consegnato, invariato salvo questa intestazione e la sezione finale:

```text

Ho finito i punti 1-3 in sola lettura e non ho modificato nulla nel repository. Non ho trovato
problemi bloccanti: ci sono un rilievo di gravità media e alcuni di gravità bassa.

Commit esaminato: f38d351 sul branch v8.4-python-gianluca, albero tracciato pulito. Gli unici
file non tracciati sono results/P2/P2E_VALIDATION_RAW.csv e results/T5_ORACLE/, come previsto.
Gli output ORACLE_* di T5-D2 non li ho aperti.


1. VERIFICATORE T5-D2: UTILIZZABILE
-----------------------------------

- Ricevute: il codice attuale (SHA ac591b47...) e la specifica (9b0e6109...) coincidono con la
  ricevuta finale di 77 prove, eseguita sul commit 9bd1e2e con albero pulito. RUN1 (73 prove,
  codice e007624..., commit 44e7417) si riferisce a una versione precedente. Le 4 prove aggiunte
  dopo sono i due estremi aperti, il giro completo CSV/GZIP e la ricevuta valida. Ho ripetuto il
  selftest in una cartella temporanea: 77/77, stesse prove.

- Coerenza con il produttore storico: ho confrontato il verificatore con diag_t5_oracle.py e con
  l'intestazione del raw P2f, senza eseguirli. Coincidono:
    * colonne e testo "null";
    * effetti scritti come 0.0 e -0.35;
    * git_dirty come intero e testo dello status;
    * phi* arrotondato a 4 cifre, quindi il confronto esatto nel JSON regge;
    * marcatore "fatto" e Z a precisione completa;
    * definizioni appaiate, con "same" che conta anche errore->errore e i due conteggi che usano
      esattamente "non deciso".
  Nel riferimento P2f tutte le righe errore T5 hanno beta vuoto, e la specifica lo prevede.

- Verità A3: sigma_i^2 = eta^2 è corretto per tutti gli scenari usati (1, 2, 7, 10), che sono
  omoschedastici e normali. Il vettore di contrasto per T5 è u["g"], che non dipende dalla
  varianza, quindi beta è davvero identico tra i bracci.

- Prove mie in più: ho aggiunto alterazioni non coperte dai test registrati. Tutte vengono
  rifiutate:
    * R spostato di 1e-7;
    * segno di un quantile invertito;
    * "null" cambiato in '' o in NULL;
    * un conteggio appaiato aumentato di 1.
  Ho anche costruito a mano un gruppo con una riga errore, con R=0,25, quantili -0,9625 e 4,85,
  e denominatori diversi tra momenti e frequenze: il riconteggio coincide.

Rilievi:

- MEDIA: solo circa 9 delle 77 prove hanno valori attesi indipendenti dall'implementazione:
    * il valore di Q;
    * due quantili;
    * una varianza;
    * R e SD(z);
    * frequenze e MCSE su 4 punti;
    * due prove sulle chiavi decimali.
  Il caso valido di base usa recount_group per riempire il riepilogo
  (t5_oracle_postcheck.py:493-495). Il README lo dichiara, ma nessuna prova registrata copre un
  gruppo con errori. Il mio caso a mano copre questa mancanza, ma è esterno alla ricevuta. Lo
  annoterei nel rapporto senza cambiare il codice: cambiarlo richiederebbe un nuovo SHA e una
  nuova ricevuta.

- BASSA: se A0 è in errore mentre il riferimento è valido, verify_a0 va in eccezione (:273-276)
  invece di contare la discrepanza. L'ho provato: il controllo fallisce comunque, ma con il nome
  generico input_structure_exception.

- BASSA, da scrivere nel rapporto: il verificatore controlla soltanto la coerenza interna dei
  bracci A1a/A1b/A2/A2p, cioè intervalli, verdetti e code. Non ricalcola i loro SE. Solo A0 ha un
  riferimento esterno, e A3 ha soltanto il controllo strutturale dell'SE costante.


2. SCHELETRO DEL RAPPORTO T5-D2: CONFORME AD A1
-----------------------------------------------

Le tabelle contano 22 righe sotto nulla più 24 sotto effetto, cioè 46, tutte "DA INSERIRE".
La lettura segue A1:
  * A1a e A1b sono distinti;
  * A3 non è presentato come garanzia di normalità;
  * A2p è descritto come la specifica approssimazione lag per lag;
  * nessun risultato è trasferito ai dati reali.

I commit citati (f77d39b, 2b334bb, d284592, 9bd1e2e) esistono. Anche la fascia di semi
28 200 000+k del pretest sullo scenario 10 è confermata nel codice, alla riga 187.

- MEDIA-BASSA: il par. 7 del protocollo congelato legge A2' in modo generale ("se A2' resta
  vicino ad A0, la forma AR(1) è inadatta ai salti"). A1 par. 3 lo precisa ma non lo sostituisce
  in modo esplicito. Lo scheletro, alla riga 243, adotta già la lettura cauta. Va però scritto
  apertamente che la lettura generale del par. 7 non si adotta, in base ad A1 par. 3, così chi
  legge non vede una contraddizione col protocollo.

- BASSA: T5_ORACLE_RESULTS.md:15 dice "cataloghi di sviluppo" e la riga 46 "quattro cataloghi di
  sviluppo". In realtà T5-D1 ha usato gli output salvati della validazione P2f (5c3b664), e A1
  parla di "cataloghi sintetici della validazione". Proposta: "cataloghi della validazione P2f,
  ora materiale di sviluppo".

- BASSA: alla tabella del par. 4 aggiungerei una riga sul limite del punto 1 (SE dei bracci non
  ricalcolati). Inoltre il rapporto finale non dovrebbe ripetere la frase del protocollo par. 1
  "l'eccesso viene dall'errore standard stimato": è più forte di quanto T5-D1 ha stabilito.


3. MORFOLOGIA: TUTTI I NUMERI RIPRODOTTI IN MODO INDIPENDENTE
-------------------------------------------------------------

Ho ricontato tutto con un mio script, partendo dalle letture bloccate, da CODE_MAP e dal
catalogo P1:

- Hash: 10 su 10 coincidono con gli impegni, sia per le copie pubblicate sia per i file privati.
  La cartella private/ è esclusa da Git.
- Ordine dei blocchi: primarie del lettore 1 alle 13:58Z, primarie del lettore 2 alle 14:03Z,
  C del lettore 2 alle 14:16Z, C del lettore 1 alle 14:20Z.
- Accordi: classe primaria 24/30 con la stessa matrice del rapporto; U assegnate 2/30 e 3/30;
  indicatore C 24/30 sulle tre categorie e 23/27 sui casi valutabili da entrambi; contatto col
  bordo 22/30. I sei disaccordi primari e i sei su C coincidono.
- Quote: base P1 di 1112, 1007, 1010 e 1060 HARP, cioè 4189 regioni con ruolo primary o both.
  Le quote per classe, la composizione dei 30 casi comuni e il blocco storico 25S coincidono fino
  alla terza cifra decimale.
- Regola operativa: quote B conservative 7,090%, 15,186% e 16,194%; le 32 HARP B sono tutte in S.
  La tabella di sensibilità coincide con il CSV.
- La conclusione si limita alla proposta di uno studio distinto su S.

Rilievi:

- MEDIA, trasparenza: il lettore 2 (GPT-6.1 Sol) è anche autore del comparatore, del rapporto e
  della verifica interna. Questo è scritto solo in MORPHOLOGY_INTERNAL_REVIEW.md:3-5. In
  MORPHOLOGY_RESULTS.md par. 1 (righe 33-34) compare soltanto "stesso autore dello script": va
  detto anche lì.

- BASSA: la lettura C del lettore 1 è stata bloccata 4 minuti dopo quella del lettore 2, il cui
  file era sullo stesso disco, privato ma accessibile. Che il lettore 1 non l'abbia visto dipende
  dalla procedura seguita, e non si può verificare dai file. Va dichiarato.


PARTI NON ANCORA VERIFICATE
---------------------------

- Punto 4: la corsa T5-D2 risulta conclusa e i suoi output non sono stati aperti. In
  T5_DIAGNOSTIC_RESULTS.md:91-94 il deficit del 14,2% è già descritto correttamente come riferito
  alla media di SE^2, non a SE né a una componente.
- Punto 5: non l'ho ancora fatto.
- Sensibilità della morfologia: non ho ricalcolato le differenze dai controlli numerici
  originali, ma solo verificato che il rapporto riporti i valori del CSV.


NATURA DI QUESTA REVISIONE
--------------------------

È una revisione incrociata, non cieca rispetto al progetto e non statisticamente indipendente.
Per la morfologia c'è un limite in più: il revisore è Opus 5.5, lo stesso modello del lettore 1.

Correzioni proposte, nessuna applicata: le tre frasi documentali del punto 2, la nota sul
lettore 2 e quella sulla sequenza dei blocchi C nel rapporto morfologico, e l'annotazione del
caso a mano come prova esterna. Il codice del verificatore e i protocolli restano invariati.
```

## Decisioni dopo la revisione (2026-11-14)

- Codice del verificatore, ricevuta dei selftest e protocolli congelati **invariati**.
- La prova esterna è conservata come `scripts/t5_postcheck_external_probe.py`, con l'output in
  `results/T5_ORACLE_POSTCHECK_EXTERNAL_PROBE/PROBE_OUTPUT.txt` (10/10 esiti attesi, verificatore
  SHA `ac591b47…`). Non fa parte della ricevuta registrata. Il caso con errori andrà aggiunto ai
  selftest soltanto in una versione futura del verificatore, con nuova ricevuta.
- Per la versione congelata: si documenta la prova esterna e si **delimita esplicitamente ciò che il
  verificatore garantisce** (coerenza interna, A0 contro P2f, struttura di A3), senza presentarla
  come sostituto di un ricalcolo indipendente degli SE.
- Precisazioni documentali applicate in `T5_ORACLE_RESULTS.md` (§1, §2, §4, §7, §10) e in
  `MORPHOLOGY_RESULTS.md` (§1). Nessun numero, lettura o tabella CSV modificati.
- Restano da fare: controllo effettivo T5-D2 con `--check` (punto 4) e coerenza finale dei documenti (punto 5).

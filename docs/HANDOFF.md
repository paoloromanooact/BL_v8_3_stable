# Cold restart — SHARP BL

## Priorità corrente — HMI e quenching (2026-11-13)

Decisione dell'utente: concentrarsi sulla misura della sorgente BL e sul
quenching con HMI. **MDI/SMARP e la degradazione HMI→MDI sono rinviati**, inclusa
la prova sintetica di precisione. Le bozze restano conservate, non congelate.
Il rinvio non è abbandono: il ciclo 23 potrebbe estendere sostanzialmente la
serie, ma confrontabilità e beneficio statistico restano da verificare.
MDI non è una garanzia di potenza né l'unica via concepibile per migliorarla.

Sono pronti i documenti di lavoro:
- `docs/HMI_MEASUREMENT_ASSESSMENT.md`: definizioni, controlli acquisiti e limite
  dell'interpretazione del tilt nei complessi HARP;
- `docs/HMI_QUENCHING_SYNTHESIS.md`: risultati T3/T4/T5, sensibilità già fatte e
  lacuna residua; distingue P2 storico da P2f;
- `docs/PROTOCOL_HMI_MORPHOLOGY_DRAFT.md`: bozza limitata alle 120 schede già
  prodotte (30 25S storiche, 90 da leggere). Nessuna nuova classificazione,
  selezione o aggregazione eseguita; nessun protocollo nuovo congelato.
- `docs/T5_JUMPS_DIAGNOSTIC_DESIGN.md`: traccia di diagnosi del blocco
  metodologico dell’efficienza, ancora da trasformare in protocollo.

T3 è già applicato una volta: −3,59° per unità di attività, intervallo nominale
97,5% [−10,58°; +3,41°], **non deciso**. T5 non è validato e resta descrittivo.
Le sensibilità non sono nuove conferme. Il filtro S4 «una NOAA» non è una
classificazione di bipoli. Nessuna nuova applicazione di T3 o modifica a P1.

**Due candidati prioritari:**
- **T5, per l'efficienza:** registrare il protocollo della diagnosi mirata
  del fallimento sui salti, a partire dalla traccia non congelata
  `docs/T5_JUMPS_DIAGNOSTIC_DESIGN.md`. Nessun nuovo calcolo avviato. Output e
  semi P2f diventano materiale di sviluppo T5; un metodo modificato richiede
  una nuova validazione indipendente.
- **Morfologia, per interpretare la misura:** rivedere e congelare la bozza
  revisione 2 prima di figure o letture. Sono proposti mappe senza risultati
  numerici, ordine casuale, seconda lettura indipendente di 30 casi e due
  passaggi distinti: morfologia, poi posizione dei centroidi. La vecchia classe
  C è un indicatore secondario e non entra nel criterio operativo. La regola
  proposta per un eventuale studio su S è ancora da congelare; non autorizza
  nuovi fit né esclusioni. Le 30 letture 25S restano storiche e separate.

La potenza simulata non predice con certezza un futuro esito T3. Il problema
metodologico di T5 e quello morfologico hanno scopi distinti; il secondo non
risolve automaticamente il primo.

Prima di ogni nuovo compito consigliare il modello e attendere la scelta
dell'utente. Nessun push senza richiesta. Preservare il CSV non tracciato
`results/P2/P2E_VALIDATION_RAW.csv`.

**Prompt di ripresa corrente:**

> Riprendi SHARP BL in /home/gianluca/BL_v8_3_stable. Leggi AGENTS.md,
> questa sezione e i documenti HMI indicati sopra. Verifica Git. MDI e
> degradazione rinviati. T3 già eseguito, non deciso; T5 descrittivo. Il passo
> proposto è scegliere fra il piano diagnostico T5 sui salti e la revisione
> finale della bozza morfologica. Entrambi richiedono un piano congelato prima
> di eseguire nuove analisi; nessuna simulazione o nuovo fit è avviato.
> Prima consigliami il modello e attendi la mia scelta. Nessun push richiesto.

---

## Cronologia del 2026-11-13 (storica; priorità corrente sopra)

**Stato:** la **validazione P2f è terminata** (esecuzione unica, 2026-11-11 14:46 → 2026-11-12
13:45, provenienza `5c3b664`, albero pulito, protocollo `8f030010…`). Controllo indipendente
superato (23 su 23, riconteggio identico), output committati (`11b71f4`), risultati in
`docs/P2F_VALIDATION_RESULTS.md`, revisione esterna dello ZIP `0f12ed1` senza discrepanze (53
asserzioni, script separato). Nessun processo in esecuzione.

**Esito (protocollo §5, alla lettera):**
- **T3: criteri di validazione superati negli scenari provati** (falsi verdetti 1,61–2,97 % nei 12
  scenari; copertura 96,60–98,15 %, coda inferiore ≤ 1,85 % nelle 16 combinazioni). Potenza bassa:
  4,55–11,10 % all'effetto di riferimento −0,2·γ0, 2,25–34,70 % sugli effetti provati.
- **T5: non validato**: scenario 7 (salti di 20 CR) con 3,35 % di falsi verdetti (limite 3,0 %) e,
  a −0,3, copertura 96,10 % e coda inferiore 2,30 %. **Resta descrittivo**.
- Dichiarazioni: la tabella di decisione è stata vista nell'ultima riga del log prima del
  controllo indipendente; la colonna `status` di `results/P2F/POST_CHECKS*.csv` dice «pilota di
  sviluppo» per un'etichetta ereditata (output non riscritti).

**Fatto il 2026-11-13 alle 09:05: applicazione di T3 ai dati reali** (una esecuzione, commit
`42fcd01`): β̂_T = −3,59° per unità di Â (−0,149·γ0), intervallo a livello nominale 97,5 %
[−10,58°; +3,41°], esito **non deciso**, nessun effetto della griglia escluso; 8 sensibilità non
validate tutte negative e tutte comprendenti zero. Risultati in `docs/P2F_RESULTS.md`; T5 rifiutato
dallo script. **Prossimo passo: revisione esterna di `docs/P2F_RESULTS.md`** (ZIP aggiornato).

(Storico) Comando usato, autorizzato dal revisore dopo il commit dei risultati: `OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_apply.py --test T3 --real`
(una sola esecuzione; lo script rifiuta T5, richiede `POST_CHECKS.csv` superato e legato agli stessi
output e protocollo). Poi `docs/P2F_RESULTS.md` con formulazioni prudenti: «supportato» non
attribuisce un meccanismo; «non deciso» non è assenza (potenza 5–11 % a −0,2); esclusione di un
quenching ≥ δ solo se l'estremo inferiore dell'intervallo è > −δ·γ0; sensibilità non validate.
Poi ZIP e revisione. Push solo su richiesta dell'utente.

**Fatto il 2026-11-13:** correzioni di formulazione di `docs/P2F_RESULTS.md` dopo la revisione esterna
(`1a22e09`); **controllo completo delle HARP dominanti** (`36676a9`, `docs/DOMINANT_HARP_RESULTS.md`):
120 HARP, valori P1 riprodotti, nessun errore confermato (esame visivo delle schede non ancora
fatto), sensibilità a maschera e pesatura ≤ 3,4 % di Σ|S_BL|, gruppo 25S sopra la soglia di
priorità del 25 %; revisione esterna senza discrepanze (101 controlli) e correzioni recepite
(`8e097f1`); **esame visivo delle 30 schede di 25S** fatto e documentato HARP per HARP
(`docs/DOMINANT_HARP_VISUAL_25S.md`), con seconda lettura esterna e cinque correzioni recepite
(validità P1 contro filtro P2, classi D distinte, conteggi riallineati, nessuna conclusione
sull'appartenenza ad altre HARP, bordo inferiore): nessun errore confermato; complessi e centroidi tra
concentrazioni tra le dominanti; nessuna azione sul catalogo senza un piano proprio. **Push fatto su
richiesta dell'utente il 2026-11-13** (`e6f7419`). Poi **verifica di riproducibilità fase 1 superata**
(`docs/REPRO_PHASE1_RESULTS.md`): i 5 CSV delle figure P1 rigenerati byte-identici da `120f852`;
comparatore corretto due volte prima dei confronti successivi (regola §2 sulle chiavi mancanti; NUL
rifiutati e confronti esatti senza float64 dopo la revisione esterna), tre confronti conservati.
Poi **studio di fattibilità MDI/SMARP** completato (`docs/MDI_SMARP_FEASIBILITY.md`): fonti primarie
verificate, tabella delle differenze strumentali, 11 questioni da verificare; esito: fattibilità
plausibile, confrontabilità e guadagno statistico non misurati; passo consigliato: esperimento solo
HMI (Br contro LOS/μ e LOS degradato a MDI). Prossimo: revisione esterna dello studio, nota per Paolo.

**(Storico) Dopo:** controllo delle HARP dominanti (piano `f805c5a`, codice pronto, prova tecnica in
`results/DOMINANT_TRIAL_2HARP/`; eseguire da commit pulito con
`nice -n 10 .venv/bin/python python/sharpbl/dominant_harp_check.py`); fase 1 della verifica di
riproducibilità (`docs/REPRO_PHASE1_PLAN.md`, congelato in `0f51e61`, solo dopo P2f); studio
MDI/SMARP in bozza (`docs/MDI_SMARP_FEASIBILITY.md`).

**Bozza esperimento HMI, revisione2 — 2026-11-13:**
`docs/PROTOCOL_HMI_LOS_SENSITIVITY_DRAFT.md`, non congelato. Recepiti i rilievi:
esperimento solo descrittivo, senza criterio automatico per avviareMDI; precisione
preventiva con risposte sintetiche prima dei nuovi dati; campioni annidati80/160/320
sovracampionando le codeA e mantenendo il centro (N finale da scegliere); R3–R5 su
sottocampione; pesiΦ principali, Φ/pi sensibilità con obiettivo distinto; perdite
per fasciaA e gruppo; spostamenti medi oltre alle pendenze; minimi di disegno e
scaling del rumore conμ. Primo passo: revisione della bozza e piano separato della
prova di precisione, con codice solo dopo registrazione. Nessun nuovo calcolo,
selezione o download svolto; nessuna nuova applicazioneT3. Push non fatto.

**Modo di lavorare:** per ogni nuovo compito l'utente sceglie prima il modello (l'agente lo
consiglia e aspetta). Le osservazioni del revisore esterno arrivano incollate dall'utente; di norma
si adottano.

**Prompt precedente (superato dalla priorità HMI sopra):**

> Riprendi SHARP BL v8.4 nel repository /home/gianluca/BL_v8_3_stable, branch
> v8.4-python-gianluca. Leggi AGENTS.md e docs/HANDOFF.md (sezione "Passaggio di consegne del
> 2026-11-13"), poi docs/P2F_VALIDATION_RESULTS.md e docs/PROTOCOL_P2F_VALIDATED_TEST.md §7.
> Verifica lo stato di Git. T3 è già stato applicato ai dati reali (docs/P2F_RESULTS.md); prossimo
> passo: revisione esterna di docs/MDI_SMARP_FEASIBILITY.md, poi nota per Paolo. Prima di ogni compito consigliami il modello e aspetta. Non fare il push senza
> la mia richiesta.

---

## Passaggio di consegne del 2026-11-11, sera (storico)

**Stato:** il **pilota di sviluppo di P2f** è terminato (esecuzione unica, 10:17–12:06, commit del
codice `67058f6`), gli output sono committati, il controllo indipendente è stato eseguito prima
dell'interpretazione (tutti i 20 controlli superati) e i risultati sono in
`docs/P2F_PILOT_RESULTS.md`. Questa frase riguarda la conclusione del pilota; la validazione successiva è descritta sotto.

**Esito del pilota** (regole registrate nel piano §5 e A1 §4, applicate alla lettera):
- candidata **M** (funzione di varianza + REML AR(1) bivariata sulle medie di cella, decisione
  analitica) **mantenuta** per T3 (massimo 24 falsi verdetti su 1000) e T5 (massimo 34, scenario a
  salti); `errore` ≤ 0,1 %;
- candidata **B** (wild cluster bootstrap ristretto, blocchi di 13 CR, Webb, CR1) **non
  mantenuta**: oltre 40 falsi in 7 scenari su 9 (T3) e 8 su 9 (T5), già 32 e 54 su 1000 senza
  componente temporale;
- **scelta: M per T3 e per T5**. Potenza di M bassa in T3 (≤ 0,24 agli effetti −0,1…−0,3·γ0),
  moderata in T5 solo a −0,3·η̄ (0,45–0,65).
- È **sviluppo, non validazione**: nessun verdetto, nessun dato reale usato. B non va «aggiustata»
  dopo aver visto i risultati; una variante richiede un nuovo piano, dichiarato non cieco.

**Documenti di questa fase**
- Piano `docs/P2F_PILOT_PLAN.md` (`83b0fc1`), emendamenti A1 (`59971e7`) e A2 (`48039d7`, non
  cieco rispetto al test preliminare 2 fallito; esecuzione 1 conservata come `PRELIM_*_RUN1.csv`).
- Nota d'implementazione `docs/P2F_PILOT_IMPLEMENTATION_NOTE.md` (`211b3ed`, registrata durante
  l'esecuzione, prima degli esiti): tre convenzioni non fissate dal piano (origine dei blocchi di
  B per T5 alla CR 2097; componenti per rotazione separate per T3 e T5; mediana di Φ sul
  disegno), conteggi del disegno in `results/P2F_PILOT/DESIGN_CHECKS.csv`, controllo di
  finitezza e riconteggio (`python/sharpbl/p2f_checks.py design | raw | diag`).
- Risultati `docs/P2F_PILOT_RESULTS.md`; voci in `CHANGELOG.md` e `docs/RESULTS_INDEX.md`.

**Stato al 2026-11-11, ore 14:55 (aggiornamento):** il protocollo P2f è **congelato**
(`docs/PROTOCOL_P2F_VALIDATED_TEST.md`, commit `500c56a`, SHA-256 `8f030010…`); il codice è stato
scritto dopo (`python/sharpbl/p2f_validation.py`, commit `ed90e15`); i sei test preliminari
sono stati superati due volte, su `ed90e15` (conservati come `results/P2F/PRELIM_*_ed90e15.csv`)
e su `5c3b664` (`results/P2F/PRELIM_*.csv`, stessi valori). La **validazione è in esecuzione**:
avviata il 2026-11-11 alle 14:46:47 in modo distaccato, **PID 968943**, 12 processi con
`OMP_NUM_THREADS=1`, log `logs/p2f_validation.log` (avanzamento ogni 2500 cataloghi su
152 000), commit del codice e della provenienza **`5c3b664`**, albero pulito; stima iniziale 22:00–23:30 superata: non usarla per prevedere la fine.
Ultima lettura durante la revisione Codex: 5000/152000 lavori nel log; nessuna nuova ETA affidabile. Controllo: `kill -0 968943`, `tail logs/p2f_validation.log`.

**Durante l'esecuzione** si può fare commit (la provenienza è acquisita all'avvio), ma non si
toccano codice scientifico, dipendenze, protocolli, input né `results/P2F/_design.pkl`. Il
controllo finale confronta la provenienza degli output con `5c3b664`, non con il nuovo HEAD.

**A fine esecuzione, nell'ordine:** (1) provenienza degli output `results/P2F/VALIDATION_*`
(`git_commit` = `5c3b664`, `git_dirty` = 0, SHA del protocollo `8f030010…`); (2) controllo
indipendente e riconteggio dai dati grezzi **prima** di leggere le tabelle
(`p2f_checks.py vraw`: 304 000 righe, chiavi uniche, numerosità per gruppo, identità
coperti + coda inferiore + coda superiore + errori = tentativi, verdetti ricalcolati dagli
intervalli, riconteggio senza la funzione di riepilogo della validazione; una discrepanza blocca
l'interpretazione); (3) commit degli output; (4) `docs/P2F_VALIDATION_RESULTS.md` (scheletro
già scritto) con le regole del protocollo §5 alla lettera, per test; (5) CHANGELOG,
RESULTS_INDEX, MANIFEST, ZIP per il revisore; (6) revisione esterna; (7) solo per i test
validati e dopo la revisione: applicazione ai dati reali con `p2f_apply.py` (una esecuzione per
test; rifiuta se il test non è validato o se i suoi risultati esistono già; sensibilità
dichiarate non validate anche negli intervalli), risultati in `docs/P2F_RESULTS.md`. Un test non
validato resta descrittivo. Gli output del pilota restano risultati storici della procedura
precedente (modello nullo).

**Ripresa con Codex, revisione delle bozze di riproducibilità (2026-11-11):**
le modifiche parziali lasciate da Claude sono state conservate e completate. Regole in
`docs/REPRO_COMPARISON_RULES.md` ancora **bozza non congelata**; 112 tabelle tracciate
inventariate, 111 chiavi univoche e una tabella vuota; scale fisse per colonna/test/quantità,
con eta_bar ed eta_bar² per T5 e confronto esatto conservativo per semantiche eterogenee.
`scripts/repro_draft_tables.py` prepara le tre tabelle di supporto senza importare codice
scientifico. Distinti commit del riferimento, commit registrati nei dati ed eccezioni storiche
dei JSON P2b o degli alberi originali non puliti. Verificati schema/chiavi e controlli sintetici
delle politiche numeriche; nessun rilancio di analisi. Prima della verifica effettiva: revisione
e congelamento delle regole, elenco di file/comandi/budget. Gli output P2f in corso non fanno
parte dell'inventario tracciato corrente; andranno aggiunti prima della loro riproduzione.
La validazione originale, i suoi input e `_design.pkl` restano invariati. Nessun push.

**Aggiornamento Codex dopo la revisione indipendente (2026-11-11):**
- Rivisto `21e7210`: 112 riferimenti Git/chiavi verificati, tre rilievi risolti
  (gamma0 a 24°, motivo di se_var_z, status esatto); 29 controlli delle politiche superati.
  Dettagli in `docs/REPRO_REVIEW_21E7210.md`.
- Congelata solo la prima verifica in `docs/REPRO_PHASE1_PLAN.md`: cinque CSV delle figure
  P1, clone isolato al codice/riferimento `120f852`, input e hash fissati, limite 10 minuti.
  Codice del comparatore ancora da scrivere e provare su casi sintetici; rilancio a macchina
  libera dopo P2f e il controllo indipendente. Le altre 107 tabelle restano fuori da questa fase.
- Studio documentale `docs/MDI_SMARP_FEASIBILITY.md`: bozza, fonti primarie, nessun download
  o calcolo. Primo passo proposto: confronto nella sovrapposizione maggio–ottobre 2010,
  separando LOS/Br, risoluzione e strumento; beneficio statistico ancora da misurare.
- Nessun cambiamento a P2f, input, risultati scientifici o protocolli precedenti; nessun push.
- La sessione Codex si è fermata per esaurimento dei token prima di installare questi file,
  rimasti in `/tmp/bl-followup-review`. Installati da Claude la sera del 2026-11-11 con l'ok
  dell'utente: hash di partenza e di arrivo verificati, tabelle DRAFT rigenerate fuori dal
  repository e identiche, `--selftest` 29/29, hash dei 11 file della fase 1 verificati.
  Validazione P2f ancora in corso (30 000/152 000 alle 19:38).

**Prossimi passi**
1. [fatto 2026-11-11] Revisione esterna dello ZIP `2e197f8`: riconteggio dai dati grezzi
   confermato, conclusione operativa corretta (M alla validazione, B scartata nella forma
   provata). Vincoli fissati per il protocollo (`docs/P2F_PILOT_RESULTS.md` §8): (i) lo scenario
   a salti resta decisivo nella validazione, numerosità e criterio fissati su tutti gli scenari;
   (ii) effetti di interesse motivati scientificamente, non scelti per la potenza; (iii) la causa
   del livello di B è un lavoro separato, non serve per validare M; (iv) la procedura M si
   congela esattamente (errori, celle singole, convenzioni del generatore, regole separate T3/T5).
2. [fatto 2026-11-11] Protocollo P2f scritto come bozza (`09562cd`), rivisto due volte dal
   revisore (`2618ca0`, `620920b`) e **congelato** (`500c56a`). Correzioni recepite: il −0,35
   tra cicli (Jiao et al. 2021) non è una pendenza dentro il ciclo; i «1–2°» di Jiang 2020 vengono
   da Karak & Miesch 2017 e non sono una soglia; il 30 % di Martin-Belda & Cameron 2017 non è per
   unità del proxy; i numeri di Zeng et al. 2024 non verificati e lasciati fuori; griglia
   −0,1/−0,2/−0,3 con −0,2 di riferimento e −0,35 supplementare (copertura e coda decisive anche
   lì); modello completo per residui e REML; generatore T5 con la media semplice di attività della
   cella; esclusione di un quenching ≥ δ solo con l'estremo inferiore di un intervallo validato;
   probabilità congiunta di scarto di una procedura nominale 7,26 % per test; A_usflux come
   sensibilità. Codice (`ed90e15`), test preliminari, validazione in corso (sopra).
3. Dalla lista del 2026-11-09, durante l'attesa della validazione (2026-11-11 pomeriggio):
   - riproducibilità (punto 1): **inventario** fatto, `docs/REPRODUCIBILITY_V84.md` (`8ee766e`,
     rivisto in `32ed3b0`): input disponibili, esecuzione possibile e riproduzione verificata
     distinti; senza Git `git_dirty = −1` blocca p2d, pilota e validazione; cinque incongruenze
     da sistemare; la **verifica** (rilanci con regole di confronto fissate prima, manifesto di
     hash) resta da fare a macchina libera;
   - HARP dominanti (punto 2): piano **registrato** `docs/DOMINANT_HARP_PLAN.md` (`f805c5a`,
     SHA-256 `e7767aea…`) dopo due revisioni; codice `python/sharpbl/dominant_harp_check.py`
     (`a41c451`, `c61bf2d`), prova tecnica su 2 HARP con output fuori dal repository (valori P1
     riprodotti esattamente; le due HARP viste — 393 e 5249 del gruppo 24N — vanno dichiarate
     nei risultati). **Esecuzione dopo la fine della validazione P2f**:
     `nice -n 10 .venv/bin/python python/sharpbl/dominant_harp_check.py` (pochi minuti), poi
     `docs/DOMINANT_HARP_RESULTS.md`;
   - restano fattibilità MDI/SMARP (punto 6) e confronto con Paolo (punto 7).
4. **Non fare il push** finché l'utente non lo chiede (di norma dopo la revisione dello ZIP).
   Ultimo commit pubblicato: `23e076a`. Il file non tracciato `results/P2/P2E_VALIDATION_RAW.csv`
   (14 MB, 2026-11-03) è preesistente e va preservato, non committato.

**Modo di lavorare concordato con l'utente**
- Le osservazioni di un revisore esterno arrivano incollate dall'utente; di norma si adottano.
- Ogni regola o analisi nuova ha un piano registrato con un commit **prima** del codice.
  I cambiamenti si fanno con emendamenti, dichiarati non ciechi se scritti dopo aver visto dei
  risultati. Ogni esecuzione è unica e gli output con `git_commit` e `git_dirty` = 0. Gli output
  di un'esecuzione non si modificano mai; riconteggi e riclassificazioni si salvano a parte.
- Il controllo indipendente degli output precede la loro interpretazione.
- Formulazioni prudenti: niente verdetti sul quenching; "compatibile" o "coerente", non
  "dimostra"; denominatori espliciti; distinguere i controlli completi da quelli campionari;
  niente «impatto trascurabile» se non misurato.
- Commit locali; push solo su richiesta, con il token dell'URL `origin` del repository MWO
  passato **solo** sulla riga di comando, mai salvato nella configurazione di questo
  repository.
- Esecuzioni lunghe: `setsid nohup … &`. Per aspettarle si usa `kill -0 <PID>` in un ciclo,
  **non** `pgrep -f` sul nome dello script (il ciclo riconosce sé stesso).
- Rispondere in italiano.

**Prompt da incollare nella nuova sessione:**

> Riprendi SHARP BL v8.4 nel repository /home/gianluca/BL_v8_3_stable, branch
> v8.4-python-gianluca. Leggi AGENTS.md e docs/HANDOFF.md (sezione "Passaggio di consegne del
> 2026-11-11, sera"), poi docs/PROTOCOL_P2F_VALIDATED_TEST.md e docs/P2F_PILOT_RESULTS.md.
> Verifica lo stato di Git e se la validazione P2f (PID 968943, log logs/p2f_validation.log)
> è ancora in corso. Il protocollo docs/PROTOCOL_P2F_VALIDATED_TEST.md è congelato. Quando la
> validazione è finita, segui i passi elencati nel passaggio di consegne (controllo indipendente
> prima dell'interpretazione). Non fare il push senza la mia richiesta.

## Branch `v8.4-python-gianluca` (stato del 2026-11-09)

Questa sezione vale per il branch v8.4 (Gianluca Santagati); la sezione v8.3
più sotto è il passaggio di consegne originale di Paolo, conservato com'è.

**Riprendere in una nuova sessione**
1. Leggere `AGENTS.md`, `README_V84.md` e i protocolli in `docs/PROTOCOL_P*.md`.
2. `git status --short`, `git log --oneline -8`; i protocolli congelati non si
   modificano: una regola nuova richiede un nuovo protocollo scritto prima.
3. Il download dei FITS è completo (14195/14195); non va ripetuto.
4. Riprendere dal primo passo non fatto della lista sotto.

Prompt da incollare:

> Riprendi SHARP BL v8.4 sul branch v8.4-python-gianluca. Leggi AGENTS.md,
> README_V84.md, docs/HANDOFF.md, docs/PROJECT_STATUS.md e i protocolli P1–P3.
> Verifica lo stato di Git, poi continua dal prossimo passo.
> Non modificare i protocolli congelati.

**Fatto**
- Porting Python (`python/sharpbl/`), correzioni (geometria sferica dalla WCS,
  bitmap ≥ 33, soglia 100 G, ciclo per latitudine nelle sovrapposizioni, un
  record per HARP), metodo legacy che riproduce la v8.3 sul caso 2024-05-08.
- Protocolli congelati: P1 (serie), P1b (QUALITY = 0x80), P1c (soglie della
  regola del ciclo, non cieco), P2 (test del quenching).
- Metadati di tutte le HARP (2010-05 → 2026-09; ottobre 2026 non ancora su
  JSOC): 8296 HARP; selezione di 14195 record per 7133 HARP
  (`results/P1/P1_RECORD_SELECTION.csv`); regola del ciclo
  (`results/P1/CYCLE_BOUNDARY_FITS.csv`).
- Script della serie (`run_p1.py`, provato su 926 record) e dei test
  (`run_p2.py`, verificato solo su cataloghi sintetici); 20 test in `tests/`.

**Obiettivo scientifico**: serie osservativa della sorgente BL (una misura per
HARP, non necessariamente per regione fisica) e verifica di tilt, latitudine ed
efficienza rispetto all'attività. S_BL è un proxy della sorgente BL misurato all'istante del
record selezionato (non necessariamente all'emersione), non
del campo polare del ciclo successivo.

**Stato al 2026-11-03 sera** (formulazioni riviste il 2026-11-09)
- Download completo (14195/14195); elaborazione completa dei record selezionati
  e controlli interni obbligatori superati (`complete_series` =
  `validation_passed` = 1), figure in `figures/P1/`.
- P3: C1 "coerente con BARD (livello 1)" per geometria e convenzioni nel
  campione confrontato (~69% di BARD); C2 riportato (`docs/P3_RESULTS_C1.md`).
  L'ampiezza della sorgente non ha una validazione esterna equivalente
  (flusso nostro/BARD 1,67).
- P2: la validazione della procedura calibrata (P2d/P2e) non ha superato il
  criterio; T3 e T5 sono **solo descrittivi** (formulazioni prudenti: T5
  "pendenza vicina a zero con ampia incertezza", non "nullo"; una pendenza
  negativa di T3 non dimostra il quenching) (`docs/P2_DECISION_DESCRIPTIVE_FALLBACK.md`,
  `docs/P2_RESULTS_DESCRIPTIVE.md`). Non riformulare come verdetti. Il mancato
  superamento non va attribuito al numero di cicli: il ruolo di numerosità,
  dipendenza temporale e stima del rumore non è ancora chiarito.
- Tutto ciò che è stato visto prima di ogni congelamento: `docs/SEEN_BEFORE_FREEZE_2026-11-03.md`.

**Prossimi passi** (rivisti il 2026-11-09 dopo una revisione esterna; prima i
punti 1–4, senza nuovi grandi calcoli; ogni regola nuova richiede un nuovo
protocollo, quelli eseguiti si conservano)
1. Riproducibilità: verificare che comandi, dipendenze, input e controlli
   rigenerino catalogo, tabelle e figure; separare ciò che è verificabile dal
   solo repository (o ZIP) da ciò che richiede i FITS esterni.
2. Controllo delle regioni che dominano la sorgente (il 10% più intenso porta il
   62–72% di |S_BL|): maschere, polarità, centroidi, associazioni NOAA.
3. [fatto 2026-11-09, `docs/SENSITIVITY_SUMMARY.md`] Sensibilità alle ricomparse e all'istante della misura: raccogliere
   l'effetto su somme ed efficienza (variante E di P1e, sensibilità S8;
   primario contro controllo, che mescola selezione, posizione sul disco ed
   evoluzione; `docs/EXPLORATORY_RESULTS.md` §4).
4. [in corso: diagnosi in `docs/DIAGNOSTIC_P2E.md`, discrepanza V0 in
   `docs/P2E_V0_APPLICABILITY_DISCREPANCY.md`, controllo A registrato in
   `docs/DIAGNOSTIC_A_PLAN.md` ed eseguito, risultati in `docs/DIAGNOSTIC_A_RESULTS.md`;
   controllo B eseguito, `docs/DIAGNOSTIC_B_RESULTS.md`; controllo C eseguito (con
   emendamento A1), `docs/DIAGNOSTIC_C_RESULTS.md`; verifica di coerenza di C1 in
   `docs/DIAGNOSTIC_C1_AUDIT.md`: nessuna discrepanza d'implementazione, il livello di circa
   il 3% riflette una realizzazione condivisa da V1–V4 (stessi semi in tutti gli scenari);
   controllo D su cataloghi nuovi (piano `docs/DIAGNOSTIC_D_PLAN.md` con A1, risultati
   `docs/DIAGNOSTIC_D_RESULTS.md`): livello compatibile con il 2,5%, diagnosi di C1 chiusa;
   prossimo passo: progettare P2f] Diagnosi del fallimento di P2d/P2e: quali condizioni sintetiche producono
   falsi verdetti eccessivi o parametri non stimabili (passano V0 e V4,
   falliscono V1–V3 con residui AR(1); in V0 test non applicabile nel ~31%
   dei cataloghi). Priorità per l'inferenza.
5. Eventuale P2f solo dopo la diagnosi: nuovo protocollo, dichiaratamente non
   cieco rispetto ai risultati precedenti, validato con simulazioni e semi
   nuovi (falsi verdetti, copertura, capacità di rilevare effetti fisicamente
   interessanti) prima dell'applicazione ai dati.
   Requisiti dalla diagnosi (2026-11-11; le correzioni possibili non sono validate):
   (a) stima dei parametri temporali meno distorta (A, B); (b) gestione della componente
   individuale utilizzabile sui dati reali, incluse le celle con una sola unità (C; il
   termine oracolo non è applicabile); (c) validazione con semi nuovi e distinti per scenario
   e regola di arresto (C1 audit, D); (d) robustezza a dipendenze temporali diverse
   dall'AR(1), in particolare AR(2) e salti di livello (V5, V6), che D non affronta.
   Documento di progettazione (non protocollo): `docs/P2F_DESIGN.md`.
6. MDI / ciclo 23 (SMARP) solo dopo uno studio di fattibilità: quali grandezze
   sono confrontabili con SHARP e come trattare le differenze strumentali.
7. Breve confronto con Paolo sulla sua domanda originaria, in parallelo.

**Dati e ambiente**
- `data/sharp` è un link a `/storage/shared/gianluca/SHARP_BL` (metadati
  ~140 MB, FITS ~4,5 GB, caso di prova). Non sono in Git.
- Ambiente: `python3 -m virtualenv .venv && .venv/bin/pip install -r requirements-v84.txt`.
- Download dei FITS: metodo diretto dall'archivio JSOC (as-is) con le keyword
  DRMS in `.keys.json`. L'export JSOC con più recordset uniti da virgole
  fallisce ("Error status returned from DRMS session"); `**ALL**` non è
  accettato da DRMS per più record insieme.
- Push: richiede credenziali GitHub dell'utente; non salvare token nella
  configurazione del repository.

---

# Cold restart — SHARP BL v8.3

Stato registrato il **2026-09-15**. Questo documento permette a una nuova LLM
o sessione di riprendere senza la chat precedente. È un riepilogo operativo;
le evidenze sono nel codice, nei documenti e nei file locali indicati.

## Avvio in una nuova sessione

1. Leggere `AGENTS.md`, questo documento, `README.md` e
   `docs/PROJECT_STATUS.md`.
2. Eseguire `git status --short`, `git log -3 --oneline`, `git remote -v`.
3. Verificare se Paolo ha fornito nuove indicazioni o l'URL GitHub.
4. Riprendere dal prossimo passo concordato sotto, senza riscaricare dati o
   ripetere la preparazione del repository.

Prompt da incollare in una nuova chat aperta nella cartella del progetto:

> Riprendi il progetto SHARP BL v8.3. Leggi AGENTS.md e docs/HANDOFF.md,
> verifica lo stato Git e continua dal prossimo passo concordato.
> Il repository locale è già preparato e committato. Il push su GitHub è
> autorizzato quando ti fornirò la destinazione e l'autenticazione sarà pronta.
> Preserva dati e risultati locali e non modificare il calcolo scientifico.

## Richieste e decisioni dell'utente

- Paolo ha chiesto il recap della discussione dai file. Non era presente una
  trascrizione; il recap è stato ricostruito da note, codice e risultati.
- Ha chiesto di preparare tutto per un repository e di fare il primo commit.
- Dopo aver considerato GitLab locale sotto VPN, ha scelto di proseguire con
  GitHub: «procedi, poi quando ho creato utente paolo romano su github,
  fai un push».
- L'identità Git locale concordata è **Paolo Romano <paolo.romano@inaf.it>**.
  È configurata solo in questo repository. Non equivale a uno username GitHub.
- Non sono ancora stati specificati URL, username effettivo o visibilità del
  repository remoto. Non è stata scelta una licenza.
- Ultima richiesta: preparare il cold restart con un'altra LLM o nuova sessione.

## Stato Git e percorsi

- Branch: `main`.
- Primo commit: `1a62bd0` — `Prepare SHARP BL v8.3 repository`, 50 file.
- Il presente passaggio di consegne è salvato in un commit successivo: ricavare
  l'hash effettivo da `git log`, senza assumere che il primo commit sia HEAD.
- Nessun remoto configurato al momento di questa preparazione; nessun push
  eseguito. Verificare nuovamente prima di configurare `origin`.
- Radice locale:
  `/media/paolo/e5e3fd23-60c6-4fdc-9d8b-829aebab0352/0_Bonanno_t/BL_v8_3_stable`.
- La shell può mostrare lo stesso progetto come
  `/home/paolo/data/0_Bonanno_t/BL_v8_3_stable`.
- La copia locale include FITS e risultati ignorati: un clone Git da solo non
  li contiene e non è un backup di tali dati.

## Lavoro già completato

- README e INSTALL riallineati alla v8.3; aggiunti requirements.txt,
  .gitignore, .gitattributes, CHANGELOG e documenti in docs/.
- Dati, output, log e ambiente Python esclusi da Git; cartelle mantenute con
  `.gitkeep`. File preesistenti conservati sul disco.
- Rimossi indirizzo personale dagli esempi e percorsi macchina dal launcher;
  la radice viene ricavata dallo script, con `--idl-root` come override.
- Corretto `--help`/`-h` come primo argomento del launcher.
- Corretto `--all-diagnostics`: eliminato `/ALL`, keyword non supportato dalla
  routine IDL; nessun filtro significa già tutte le righe.
- Aggiornati esempi di download e batch IDL e manifest del repository.
- Routine scientifiche non modificate.

## Verifiche già eseguite

- `bash scripts/check_repo.sh`: sintassi Bash, parsing Python e help launcher.
- Launcher provato in directory temporanea con spazi e shell IDL simulata:
  modalità diagnostica standard, tutte le diagnostiche, nessuna diagnostica.
  Verificati batch, soglia esplicita 100D e selezione dei filtri.
- `git diff --cached --check` superato prima del primo commit.
- Verificato che Git includa solo `.gitkeep` sotto data/output/logs.
- Nessun download, installazione dipendenze o nuovo calcolo IDL scientifico
  eseguito durante la preparazione del repository.
- `tcsh` è disponibile; `sswidl` non era nel PATH della shell Bash ispezionata.
  Questo non prova che manchi in tcsh: SolarSoft è inizializzato dalla sua
  configurazione. Non dichiarare il runtime IDL validato dalla nuova sessione.

## Stato scientifico e limiti

La pipeline scarica Br e bitmap SHARP CEA e calcola
`S_BL = hale_sign * Phi * d * cos(lambda) * sin(alpha)`.
Flusso unsigned, centroidi pesati con il campo; leading XMAX predefinito.
Gli orari delle query sono TAI.

Risultati locali preesistenti: 2024-05-08 03:12 TAI, 26 FITS, 13 regioni,
7 PNG. 9 righe numericamente valide, di cui 3 anti-Hale; 4 senza una polarità
sopra soglia. Dettagli e HARPNUM in `docs/PROJECT_STATUS.md`.
Il giorno completo non risulta concluso: log fermo all'attesa JSOC e CSV assente.

Punti aperti da non correggere implicitamente:

- `process_sharp_day` senza THRESHOLD usa 1000 G, mentre il launcher passa
  100 G. Differenza documentata, conservata intenzionalmente in questa attività.
- Convenzioni XMAX, tilt, segno e geometria CEA richiedono validazione fisica.
- Flag numerici OK non certificano correttezza scientifica.
- Alcuni errori per file vengono intercettati; uscita di processo riuscita
  non significa necessariamente tutte le regioni elaborate.
- requirements.txt dichiara dipendenze non bloccate a versioni specifiche.
- Gli esempi in test/ sono procedure IDL manuali, non regressioni automatiche.

## Prossimo passo concordato: push GitHub

Il push è già autorizzato dall'utente per quando il repository sarà disponibile.
Mancano destinazione e autenticazione; non sono stati richiesti token in chat.
Quando Paolo comunica l'URL:

1. Verificare autenticazione locale, URL e stato del remoto.
2. Collegare `origin` all'URL comunicato, se non già configurato. Non sostituire
   un origin diverso senza chiarire la destinazione.
3. Se remoto vuoto, eseguire `git push -u origin main`.
4. Se contiene già commit, ispezionarli e conciliare la storia preservando il
   lavoro; non forzare il push e non eliminare contenuti.
5. Confermare branch e commit pubblicato, confrontando HEAD e ref remoto.

Creazione account, visibilità e licenza restano scelte del proprietario.
Non pubblicare su una destinazione dedotta dal solo nome «Paolo Romano».

## Nota sull'ambiente dell'assistente

Le chiamate shell in sandbox hanno fallito con
`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted` anche in lettura.
È stato necessario il normale meccanismo di approvazione fuori sandbox.
Se ricapita, seguire le autorizzazioni della nuova sessione; questa nota non
costituisce un permesso per aggirare restrizioni. Alcune richieste furono
interrotte dall'utente: controllare lo stato reale dopo ogni interruzione.

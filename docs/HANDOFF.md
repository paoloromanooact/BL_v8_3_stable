# Cold restart — SHARP BL

## ⇒ Passaggio di consegne del 2026-11-11, sera (leggere per primo)

**Stato:** il **pilota di sviluppo di P2f** è terminato (esecuzione unica, 10:17–12:06, commit del
codice `67058f6`), gli output sono committati, il controllo indipendente è stato eseguito prima
dell'interpretazione (tutti i 20 controlli superati) e i risultati sono in
`docs/P2F_PILOT_RESULTS.md`. Nessun processo in esecuzione.

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

**Prossimi passi**
1. Revisione scientifica dei risultati e della scelta (le osservazioni del revisore esterno
   arrivano incollate dall'utente; di norma si adottano). Punti da discutere: il livello di B
   sopra il nominale già senza componente temporale (da capire, non da correggere in corsa); il
   3,4 % di M nello scenario a salti in T5; la potenza bassa di M in T3 e la scelta degli effetti
   di interesse scientifico.
2. Scrivere il **protocollo P2f** (`docs/PROTOCOL_P2F_*.md`), dichiaratamente non cieco rispetto
   al pilota e alle diagnosi: candidata M; validazione con semi nuovi e distinti per scenario,
   scenari fissati prima (anche fuori dal modello AR(1): AR(2), salti, code pesanti), criteri di
   accettazione per falsi verdetti, copertura e potenza, regola di arresto; risoluzione esplicita
   delle tre convenzioni della nota d'implementazione; effetti di interesse scientifico;
   applicazione ai dati reali solo se la validazione passa. Un protocollo scritto prima del
   codice e congelato con un commit.
3. Restano aperti dalla lista del 2026-11-09: riproducibilità (punto 1), regioni dominanti
   (punto 2), fattibilità MDI/SMARP (punto 6), confronto con Paolo (punto 7).
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
> 2026-11-11, sera"), poi docs/P2F_PILOT_RESULTS.md e docs/P2F_PILOT_IMPLEMENTATION_NOTE.md.
> Verifica lo stato di Git. Il prossimo passo è la revisione scientifica dei risultati del
> pilota e poi il protocollo P2f, scritto prima del codice. Non fare il push senza la mia richiesta.

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

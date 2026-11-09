# Cold restart — SHARP BL

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
   `docs/DIAGNOSTIC_A_PLAN.md`; B si decide dopo A] Diagnosi del fallimento di P2d/P2e: quali condizioni sintetiche producono
   falsi verdetti eccessivi o parametri non stimabili (passano V0 e V4,
   falliscono V1–V3 con residui AR(1); in V0 test non applicabile nel ~31%
   dei cataloghi). Priorità per l'inferenza.
5. Eventuale P2f solo dopo la diagnosi: nuovo protocollo, dichiaratamente non
   cieco rispetto ai risultati precedenti, validato con simulazioni e semi
   nuovi (falsi verdetti, copertura, capacità di rilevare effetti fisicamente
   interessanti) prima dell'applicazione ai dati.
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

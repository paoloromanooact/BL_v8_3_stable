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

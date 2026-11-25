# Istruzioni per riprendere il progetto

Prima di lavorare leggere `docs/BL_WORK_PLAN.md` (priorita comuni Codex–Claude),
poi `docs/HANDOFF.md`, `README.md` e `docs/PROJECT_STATUS.md`. Questi documenti descrivono lo stato registrato:
verificare sempre lo stato effettivo con Git prima di agire.

L'ordine operativo segue l'ultima decisione dell'utente riportata in piano e
HANDOFF, non i riepiloghi storici: al 25 novembre BQ-HMI e prioritario, C e
attivo, SFT prepara BT e i nests sono pianificati ma sospesi. I due controlli
SFT restano obiettivi della sorgente BL. Mantenere il richiamo al piano sopra
la cronologia e verificare le assegnazioni Codex/Claude per non duplicare
lavoro. Il piano non sostituisce i protocolli congelati. SINDy e separato.

**Vincolo permanente per Codex e Claude:** ogni attivita serve uno dei due pilastri fissati in testa
al piano: (1) sorgente BL P1 → verifica mappa/bipolo e osservazioni/C → BT; (2) quenching BQ-HMI → BQ-D.
La fase corrente usa solo HMI: BQ-M e futuro, nests sospesi. L'eventuale sintesi P resta nel pilastro BL.
Dichiarare obiettivo e stato del lavoro, senza confondere test sintetici con risultati osservati.
Non aprire altre linee mentre le prove in corso saturano la macchina; privilegiare revisioni/documentazione.

Sul branch `v8.4-python-gianluca` leggere prima `README_V84.md` e i protocolli
`docs/PROTOCOL_P1_SBL_SERIES.md` e `docs/PROTOCOL_P2_QUENCHING.md`: sono
congelati e non si modificano; una regola nuova richiede un nuovo protocollo,
scritto prima di eseguirlo.

- Comunicare con Paolo in italiano, con aggiornamenti brevi e concreti.
- Non modificare convenzioni scientifiche, soglie, segni o geometria per una
  semplice attività di manutenzione del repository.
- Preservare i dati locali in `data/`, `output/`, `logs/`; sono esclusi da Git.
- Non aggiungere FITS, risultati o credenziali ai commit.
- Per controlli offline usare `bash scripts/check_repo.sh` e
  `git diff --check`; i test IDL richiedono un ambiente SSW funzionante.
- Non attribuire ai controlli di sintassi una validazione scientifica.
- Il prossimo passo concordato è il push su GitHub dopo che Paolo avrà
  fornito il repository e sarà disponibile l'autenticazione. Non inventare
  username/URL, non cambiare visibilità e non usare force push.
- Aggiornare il documento di passaggio quando cambiano decisioni o stato.

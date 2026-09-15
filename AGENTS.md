# Istruzioni per riprendere il progetto

Prima di lavorare leggere `docs/HANDOFF.md`, poi `README.md` e
`docs/PROJECT_STATUS.md`. Questi documenti descrivono lo stato registrato:
verificare sempre lo stato effettivo con Git prima di agire.

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

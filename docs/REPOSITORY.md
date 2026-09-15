# Gestione del repository

Il repository contiene codice, documentazione e file di configurazione.
`.gitignore` mantiene locali FITS, prodotti scientifici, log, ambienti Python
e configurazioni personali; le cartelle dati sono mantenute con `.gitkeep`.

## Controlli prima di un commit

```bash
bash scripts/check_repo.sh
git status --short
git diff --check
git diff --cached --stat
```

I dati di riferimento si rigenerano con il comando del README. Per distribuire
in seguito un dataset o una release scientifica, indicarne separatamente
provenienza, parametri e versioni dell'ambiente.

## Primo commit e pubblicazione

Dopo aver verificato i file e configurato la propria identità Git:

```bash
git add .
git diff --cached --stat
git commit -m "Prepare SHARP BL v8.3 repository"
```

Creare un repository remoto vuoto sul servizio scelto, poi sostituire l'URL:

```bash
git remote add origin <URL-del-repository>
git push -u origin main
```

Nome, servizio, visibilità del remoto e licenza sono scelte del proprietario.
Non è stata assegnata automaticamente una licenza al codice.

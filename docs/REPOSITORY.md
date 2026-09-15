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

## Stato e pubblicazione

Il primo commit è già stato creato su `main`:
`1a62bd0` — `Prepare SHARP BL v8.3 repository`.
I commit successivi sono consultabili con `git log --oneline`.
L'identità autore è configurata localmente; non serve ripetere l'inizializzazione.

La destinazione concordata è GitHub, in attesa dell'URL fornito da Paolo e
dell'autenticazione locale. Il push è autorizzato quando questi dati saranno
pronti. Per un remoto vuoto, sostituire l'URL:

```bash
git remote add origin <URL-del-repository>
git push -u origin main
```

Controllare prima `git remote -v` e l'eventuale storia remota; non usare force
push. Visibilità e licenza devono ancora essere scelte dal proprietario.
Vedi [passaggio di consegne](HANDOFF.md) per riprendere in una nuova sessione.

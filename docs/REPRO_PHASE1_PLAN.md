# Riproducibilità: fase 1 — valori delle figure P1

**Congelato nel commit che introduce questo file, prima del codice del comparatore
 e di qualsiasi rilancio della fase 1.** Data: 2026-11-11. Non cieco ai risultati
storici; nessuna differenza di un nuovo rilancio osservata. Una modifica successiva
richiede un emendamento separato prima di eseguire la procedura cambiata.

## Ambito e riferimenti

Questa fase comprende esattamente i cinque CSV sotto `figures/P1/data/` elencati
in `REPRO_PHASE1_FILES.csv`, con tre input e tre moduli di codice fissati tramite
commit, blob Git e SHA-256. Si esegue `figures_p1.py` del commit `120f852`, che
contiene insieme questa versione del codice e i riferimenti delle figure.
Questo è il produttore candidato recuperabile dal deposito: non si inventa un
registro di esecuzione storico che certifichi quale albero fosse in memoria.

Sono congelate per questa fase le sezioni 2–4 di `REPRO_COMPARISON_RULES.md` e le
righe relative ai cinque output nelle tabelle `REPRO_COMPARISON_KEYS_DRAFT.csv` e
`REPRO_COMPARISON_SCALES_DRAFT.csv`, nella versione di questo commit. Il nome DRAFT
resta perché le altre 107 tabelle non sono oggetto della fase. Si registrano gli
SHA-256 di piano, regole e tabelle nel rapporto del futuro confronto.

## Esecuzione differita

Solo a macchina libera, dopo la validazione originale P2f e il suo controllo.
Nessuna esecuzione di questa fase è autorizzata durante la validazione.

Preparare un clone locale isolato e pulito al commit completo indicato nella
lista, senza copiare dati locali non tracciati. Il codice e gli input devono
coincidere con gli hash fissati; salvare i riferimenti prima del comando. Usare
Python 3.10 e un ambiente separato con le versioni `requirements-v84.txt` del
commit di congelamento: non installare né aggiornare l'ambiente del processo P2f.
Registrare versioni esatte di Python/librerie e piattaforma. Sono le versioni
prescritte per il rilancio, non prova dell'ambiente originale delle figure.

Dalla radice del clone, con quell'ambiente attivo:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg \
  timeout 600s python python/sharpbl/figures_p1.py
```

Un processo, limite di 10 minuti esclusa la preparazione. Timeout o errore:
conservare log e output parziali, esito non completato; non cambiare automaticamente
budget o codice. I tre PNG prodotti sono conservati come artefatti accessori:
la loro identità o resa visiva non entra nell'accettazione di questa fase.

## Confronto e accettazione

Prima del rilancio il comparatore deve superare prove sintetiche per chiavi
mancanti/duplicate, righe permutate, NaN/inf, schema diverso, valori minuscoli T5,
conteggi e metadati scientifici alterati. Questi controlli non usano nuovi risultati.

Per tutti e cinque i CSV: schema, cardinalità e insieme delle chiavi identici;
valori esatti nelle colonne exact/exact_key; continui identici o entro la tolleranza
fissata. Provenienza ereditata dagli input (`git_commit`, `git_dirty`, SHA P1–P1e):
**uguaglianza esatta** per questa fase, perché gli input sono fissati byte per byte.
La provenienza del nuovo processo va nel rapporto separato, senza riscrivere i CSV.
Non è sufficiente ignorare le colonne di provenienza.

Il rapporto deve contenere byte-identico sì/no e, separatamente, confronto dei
valori; scarti massimi assoluti e normalizzati, conteggi di mancate corrispondenze,
output mancanti e hash dei riferimenti/rigenerati. Una sola differenza fuori regola
rende la fase non superata; si conserva e diagnostica, senza adattare le tolleranze.
Nessun file escluso è dichiarato riprodotto.

Questa verifica può attestare i valori delle figure condizionatamente agli input
P1 distribuiti. Non ricostruisce P1 dai FITS, non valida P2/P2f, non verifica BARD
e non certifica l'intero progetto. Le altre fasi richiedono comandi, riferimenti
e budget fissati prima dei rispettivi rilanci.

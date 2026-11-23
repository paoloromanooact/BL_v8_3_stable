# Pilota MDI, fase 5 — revisione del codice bedc06c

23 novembre 2026, Codex. Revisione offline. Nessuna rete e nessun FITS reale
letto. I selftest dichiarati sono riprodotti: runner 8/8, riconteggio 16/16.
La base sintetica e coerente, ma cinque controesempi restano aperti.

## Decisione

**Fase 5 non ancora approvata per la misura reale.** Restano approvati piano
A1 e blocchi B/C, con le correzioni di `9185a77`. Il download non dipende dalla
chiusura della fase 5 e richiede comunque l'autorizzazione esplicita dell'utente.
Nessun cambio a campione, QUALITY o dominio geometrico e autorizzato qui.

## 1. Provenienza prima di qualunque misura — necessario

Il runner controlla il piano attraverso `FE.gate()`, ma non verifica i prodotti
e la ricevuta della selezione prima di usare SAMPLE. Copiando la selezione,
modificando una latitudine e lasciando il META invariato, raggiunge `build`.
La sonda sostituisce `build` con un sentinella: nessuna misura viene effettuata.
Il controllo di albero pulito viene simulato nella sonda per isolare questa
lacuna da modifiche concorrenti non pertinenti.

Il riconteggio registra come negativo un hash L2 errato ma prosegue fino a
`expected_rows`, che normalmente legge i FITS. Occorre interrompere prima
quando prodotti o prerequisiti non sono validi. Lo stesso principio vale per
le verifiche negative dei legami a monte nel ramo reale.

Richiesta: gate completo su testo del protocollo padre e A1, prodotti e
ricevute strette della selezione e dei metadati, legami con il piano congelato,
prima di letture di FITS. Verificare anche identita checkpoint/path/T_REC/file
contro il piano; non basta che la riga riporti il suo hash META. Registrare e
verificare nel riconteggio gli input effettivamente usati. Prove: selezione
alterata, protocollo alterato, ricevuta parziale, checkpoint discordante e
prodotto L2 alterato devono fermarsi con zero chiamate al lettore FITS.

## 2. Confronto completo e conteggi interi — necessario

La mutazione del solo `pair_status` in `invented_pair` viene accettata.
Il campo e esportato dal runner ma non compare negli scalari attesi.
Inoltre `value_ok` usa `int(float(theirs))`: un `main_npos` aumentato di 0,4
viene accettato come se fosse lo stesso intero.

Richiesta: ricontare tutti i campi esportati, compresi `pair_status`,
finitezza e integralita esatta dei conteggi (e dominio dei segni). Rifiutare
valori non previsti anche sulle righe senza misura; aggiungere le regressioni.

## 3. INTERVAL ignoto — necessario

Il protocollo §4 ammette A con INTERVAL ignoto in Q2, senza coppia B.
Nel riconteggio `float(kw[c['A']]['INTERVAL'])` invece solleva ValueError
su `MISSING`. La sonda lo riproduce. Un caso ammesso non deve far cadere il
riconteggio.

Richiesta: parsing esplicito dei valori mancanti/non interpretabili, senza
convertirli in zero e con verifica coerente fra keyword, piano e CSV.
Provare almeno A valido con INTERVAL ignoto e B assente, sul percorso completo
runner → CSV → riconteggio.

## Geometria e attese

Riconteggio indipendente dai soli metadati: 81 immagini A; 20 finestre di
misura fuori dominio; quiete con zero/un lato/due lati: 51/30/0. Nessun FITS
letto per questi conteggi.

La regola resta mu >= 0,8 su tutta la finestra. Le perdite geometriche vanno
riportate, senza sostituire gruppi o spostare finestre dopo averle osservate.
Un eventuale massimo di 61 immagini A misurabili e solo un limite superiore,
prima delle esclusioni per dati mancanti e polarita. Le finestre di quiete
sono supplementari: non disponibili non equivale a rumore nullo e non deve
invalidare automaticamente un confronto di tilt altrimenti misurabile.
Non propongo ora un emendamento per aumentare la resa.

## Sonda riproducibile

`env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_pilot_l2_review_probe.py`

Su bedc06c (con 9185a77) la base e accettata e i cinque controlli di regressione
falliscono: esito 1/6, uscita 1. E l'esito atteso di una revisione che riproduce
problemi, non una ricevuta positiva della fase 5. Usa solo FITS sintetici,
trasporti assenti e metadati gia conservati. Non esegue misure reali e non
scrive ricevute o prodotti scientifici.

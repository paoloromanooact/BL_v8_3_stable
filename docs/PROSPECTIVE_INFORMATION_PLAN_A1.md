# Piano prospettico — emendamento A1 (calendario delle estensioni)

**Registrato il 2026-11-18, prima di qualunque esecuzione ufficiale della fase A** (`--run` mai lanciato).
Piano di riferimento: `docs/PROSPECTIVE_INFORMATION_PLAN.md`, congelato in `71c7d17`
(SHA-256 `c92be19b…`), che resta invariato. Origine: revisione di Codex dello script `b6c00c0`.
Non cieco nel senso del piano; nessun risultato della fase A è stato letto. Sono noti soltanto i
conteggi di calendario riportati sotto, ottenuti dal selftest, e il bersaglio T3 su E0 (−1,60265° per
unità di attività), calcolato dal selftest e ricalcolato da Codex.

## 1. Corrispondenza di E1 senza riavvolgimento (sostituisce l'ultima frase del §10, punto t₂₅)

Le CR analoghe sono quelle il cui inizio cade in [2016-03-01, 2021-03-01), in ordine crescente. La
k-esima CR di E1 (CR 2317 + k, k = 0…66) prende attività emisferica, fase e ciclo del tempo (+1) dalla
k-esima CR analoga. Con il calendario adottato le analoghe sono esattamente 67, CR 2175–2241, quindi la
corrispondenza è uno a uno. **Se il numero delle analoghe differisce da quello delle CR di E1, la fase A si
ferma con errore tecnico**: nessun riavvolgimento, nessun troncamento. La regola di riavvolgimento del §10
non si applica.

## 2. CR 2096 appartiene solo a E0 (precisa il §3, posti di E2)

CR 2096 inizia il 2010-04-22 e la regola letterale sulle date la includerebbe anche in E2. È già un posto
di E0 (CR 2096–2316), quindi è esclusa da E2. Con questa precisazione e la lacuna del 1998, E2 conta 184 CR.

## 3. Calendario

Inizio delle CR: Meeus, *Astronomical Algorithms*, cap. 29 (JDE = 2398140,2270 + 27,2752316·C più i
tre termini periodici), letto come data civile. Prova: le 2485 date dei record HMI di S cadono tutte nella
propria CR.

Nessun'altra regola cambia. Lo script registra lo SHA-256 di questo emendamento negli output.

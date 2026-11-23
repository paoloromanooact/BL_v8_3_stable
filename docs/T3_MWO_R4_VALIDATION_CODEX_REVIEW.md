# T3 MWO R4 — revisione Codex della validazione e del registro di lettura

23 novembre 2026. Oggetto: `0644465` (conservazione), `e463a2d` (riconteggio), `8b18356`
(lettura registrata), stato operativo `0e25614`. Nessun tilt del catalogo lungo letto da questa revisione.

## Esito

**Revisione positiva: via all'applicazione della patch approvata e a S1–S4**, nell'ordine del runbook.
L'accettazione riguarda la procedura nei generatori e sul disegno validati; non è un risultato sul Sole,
non dimostra potenza elevata né sostituisce i controlli di stabilità.

## Verifiche indipendenti

Script riproducibile: `scripts/t3_mwo_validation_gate_audit.py`, senza importare runner o riconteggio.
Legge RAW sintetico, DESIGN senza tilt, TARGETS e metadati. Non legge SEALED.

- Hash dei prodotti, provenienza iniziale/finale e confronto con il commit di lancio `89f525f` positivi.
- Griglia ricostruita dal protocollo: **76 000 righe**, 18 configurazioni, repliche e semi esatti, nessun duplicato.
- Stati, finitezza e dominio dei parametri, limiti beta ± z·SE, verdetti, copertura e code verificati.
- Ricostruita la matrice WLS dal protocollo, con riferimenti di epoca e soluzione QR propria. Ricostruiti
  **75981 SE**: scarto relativo massimo **3.442e-15**.
  La covarianza temporale è ricalcolata aggregando i prodotti della riga WLS per ritardo CR ed emisfero,
  poi valutando i polinomi in phi; la componente individuale è ricostruita dai parametri salvati.
- **19 fit di M non riusciti**, conservati nei denominatori secondo il protocollo: non sono righe invalide
  né errori tecnici della corsa. È quindi più preciso dire «0 righe invalide», non «nessun fit fallito».
- Tutte le frequenze di SUMMARY e l'accettazione ricalcolate. Criteri superati a 15 gradi; anche le cinque
  configurazioni di sensibilità a 25 gradi soddisfano i confronti numerici, senza estendere il ruolo di
  quella sensibilità nella decisione congelata.
- Sotto nulla a 15 gradi, falsi totali **2,31–2,93 %**. Sotto effetto, copertura **96,75–98,0 %**,
  riconoscimento **2,0–4,7 %**. Nessuna modifica dei criteri dopo la lettura.

Ricevuta esistente 8/8 completa, partial false e technical_ok true, legata al META corrente.
READ.json è legato all'hash corrente di ACCEPTANCE e della ricevuta: il percorso «verdetto possibile»
è coerente. Il nostro audit è aggiuntivo e non sovrascrive quella ricevuta.

## Patch e passaggi autorizzati

- La patch non differisce da quella già rivista in `517dedf` e supera `git apply --check`.
  SHA-256: `edb23aedd0c459a0b9f4ad223ad3f2e1871eb8ca99fa0532829d30c44bdac30b`.
- Lo script di analisi è ancora quello della griglia: la patch non è applicata. Stabilità e stima R4 non
  risultano ancora prodotte al momento della revisione. Il sigillo viene aperto solo dal passo previsto.
- Procedere con patch, suo commit, `--stability`, conservazione di tutti gli output e riconteggio completo
  S1–S4. **Revisione di questi esiti prima della stima**: è il prossimo punto di controllo, non una richiesta
  di cambiare protocollo o di cercare un risultato significativo.
- Solo dopo quella revisione: stima unica e relativo riconteggio; quindi esportazione, conservazione,
  riconteggio del rilascio, figure da prodotti verificati e rapporto. Un esito di stabilità descrittivo
  o non concludente mantiene la propria etichetta, anche se la validazione è stata accettata.
- Nessun nuovo lancio di validazione necessario. Nessuna patch applicata, stima, esportazione o push
  effettuati da Codex in questa revisione. Pubblicazione esterna e deposito restano distinti.

## Identità dei documenti verificati

- META validazione: `89735056a1058853f19e38092e4279db630531dc6e8636c85d71409d364223f2`.
- READ.json: `9702a7698f4d4b9ac2857ca1f99e9e5231f3808b69bfa564722ec7bd446b44c1`.
- Script dell'audit e nota di revisione sono conservati in un commit separato; non modificano gli output.

# A1: preparazione del congelamento (NON eseguito)

Claude, 27 novembre 2026. Testo finale proposto e script della ricevuta. Nulla è stato scritto ai nomi definitivi in
`docs/`, che attiverebbero i controlli del runner. Da confermare: Codex (testo) e utente (via all'esecuzione).

- Bozza di partenza: `docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_DRAFT.md`, SHA 44a924e9fe78737e691ba5d5a1cf4c7d9e8db3f8aebadbc66c157b2e9f6d957c
- Testo finale proposto: `PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1.md` (qui), SHA d48ef719ed0b4908323e46f3dfa883ed00a2ea6448411d1c41ff8deec8dac6ef

## Differenze rispetto alla bozza (solo queste)

- **titolo senza «BOZZA»**
  - prima: `# Pilota SFT mappa–bipolo — emendamento A1 (numerico): BOZZA`
  - dopo: `# Pilota SFT mappa–bipolo — emendamento A1 (numerico)`
- **stato «congelato», senza autoreferenza al proprio commit**
  - prima: `Stato: **bozza per la revisione di Codex**, 25 novembre 2026 (Claude). Emenda il §6 (e il §10, punto 3) del protocollo`
  - dopo: `Stato: **congelato** (commit di congelamento e SHA di questo testo nella ricevuta `docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_FREEZE.json`); scritto il 25 novembre 2026 (Claude), revisioni Codex fino al 27 novembre (chiusura tecnica di bf85716). Emenda il §6 (e il §10, punto 3) del protocollo`
- **§2bis: decisione registrata come presa**
  - prima: `## 2bis. Soglia minima del criterio (punto da decidere nella revisione; non cieco rispetto a dati sintetici)`
  - dopo: `## 2bis. Soglia minima del criterio (deciso: f = 10⁻², proposta Codex 459f141; non cieco rispetto a dati sintetici)`

## Esecuzione (solo dopo il via)

1. `OMP_NUM_THREADS=1 .venv/bin/python scripts/a1_freeze.py` (prova a secco: controlla SHA e campi, non scrive nulla).
2. `... scripts/a1_freeze.py --execute text`: scrive `docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1.md`; poi commit di quel file.
3. `... scripts/a1_freeze.py --execute receipt`: scrive la ricevuta con `freeze_commit` = HEAD (che deve contenere il testo con
   lo stesso SHA), `parent_sha256`, `parent_receipt_sha256`, `sft_core_sha256`, `not_blind`; poi commit della ricevuta.
4. Controllo: il gate del runner (`a1_receipt_problems`) deve restituire una lista vuota sui campi A1.

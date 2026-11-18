# Diagnosi successiva alla corsa: scarto di flusso nel riconteggio del pilota MWO

Verifica eseguita da Codex il 18 novembre 2026, dopo la corsa e dopo la prima ricevuta del riconteggio
(`results/MWO_PILOT_RECOUNT/RECEIPT.json`, 5/6, voce del flusso fallita a 2,6e-8 contro 1e-9). File copiati senza
modifiche da `/tmp/mwo_flux_precision_review.py` e `/tmp/mwo_flux_precision_review.json`.

Causa: la pipeline MWO congelata converte gli interi del FITS (BITPIX 16) in float32 prima di applicare BSCALE = 0,1;
il primo riconteggio applicava la scala in float64. Rileggendo con la stessa convenzione, sui 211 record lo scarto massimo
è 3,3e-16 relativo per il flusso e 1,8e-12° per il tilt, con 0 discordanze sulla polarità leading. La causa non è
la geometria, come proposto nella prima versione del rapporto.

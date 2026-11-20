# Revisione incrociata di Claude dei materiali di Codex (3c4408f) e recepimento dei rilievi — 20 novembre 2026

Nessun tilt aperto, nessuna patch applicata alla produzione, `scripts/t3_mwo_analysis.py` invariato (validazione R4 in
corsa).

## Strumenti di Codex rieseguiti

- `scripts/t3_mwo_release_recount.py --selftest`: positivo. La sonda del rilascio dà false sui tre casi (giorno
  sigillato errato, gruppo sigillato in più, catalogo superato).
- `scripts/t3_mwo_preparation_review.py`: PASS. Le sei tabelle di copertura sono ricostruite in modo indipendente, con
  hash coincidenti.
- `scripts/t3_mwo_final_sequence_probe.py`: PASS su tutti gli stadi (riconteggi di stima e rilascio, prova generale
  degli strumenti finali), senza toccare sorgenti o input di produzione.
- `docs/T3_MWO_R4_FINAL_RUNBOOK.md`: i comandi, gli SHA del protocollo e di A1 e l'ordine coincidono con la catena
  implementata (`chain_problem`, riconteggi, `--record-reading`, patch, `--stability`, `--estimate`, esportazione,
  verificatore del rilascio).
  - Unica aggiunta suggerita: nel passo 8 indicare `scripts/t3_mwo_final_figures.py --run`, che ora rifiuta di partire
    senza la ricevuta del verificatore del rilascio completa e legata.

## Rilievi di Codex sui materiali di Claude: recepiti

1. **Periodo del pilota.** Nel README, pilota (candidati 2010-05 → 2013-12, valutabili 2010-05-04 → 2013-01-14,
   211 regioni) distinto dal controllo S2-P1 del catalogo (2010-05-01 → 2012-12-31). Il rapporto di flusso del 16 % è
   attribuito al solo pilota.
2. **Bersagli nella figura di β₃.** Le rette sono etichettate come bersagli della sola analisi principale. Il titolo
   dichiara che le sensibilità hanno intervalli nominali, non coperti dalla validazione del disegno principale.
3. **Guardia delle figure finali.** `figure_problem()` richiede:
   - la ricevuta del verificatore del rilascio completa, non parziale, con tutti i controlli superati e legata al META
     del rilascio;
   - prodotti di rilascio e stima uguali ai rispettivi META;
   - il rilascio legato alla stima corrente.

   Il confronto P1 con n = 0 non disegna nulla, quindi nessuna mediana NaN. Selftest 2/2.
4. **Confronti di Joy.** Nel README è precisato che k (in γ = k sin|λ|) non è numericamente la pendenza tilt–latitudine
   in gradi per grado; i confronti restano descrittivi, con forma funzionale, popolazione, pesi e convenzioni
   dichiarati.
5. **Esclusioni.** `EXCLUDED_MAGNETOGRAMS.csv` contiene solo le 26 esclusioni strumentali di A2 e A3. I due file
   illeggibili, le effemeridi fallite e i tentativi falliti sono registrati in MAGNETOGRAMS, ATTEMPTS e LOSSES.
6. **Leggibilità.** Barra colore nella figura tempo–latitudine; la didascalia della boxplot dichiara che i punti esterni
   non sono mostrati ma restano nei dati. Lo script della copertura è aggiornato (selftest 2/2); le figure conservate in
   `results/T3_MWO_COVERAGE_R4` restano quelle della prima versione e saranno rigenerate per il pacchetto finale.

**Riferimenti.** La frase su Wang et al. è attenuata: le differenze fra tilt magnetici e in luce bianca non garantiscono
uno scarto costante nel tempo o con l'attività. Verificati e aggiornati:
- il corrigendum di Dasi-Espuig (A&A 556, C3: r = −0,79 MW, −0,93 KK);
- Ulrich, Boyden e Tran 2024 (Solar Physics 299);
- Baranyi et al. 2016 (Solar Physics 291, 3081–3102);
- Jha et al. (arXiv:1912.13223 e arXiv:2401.04255, rivista da verificare).

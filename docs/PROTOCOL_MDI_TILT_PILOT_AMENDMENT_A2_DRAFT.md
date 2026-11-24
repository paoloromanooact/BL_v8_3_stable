# Pilota MDI — emendamento A2: flussi della nota Q4 e latitudine

**BOZZA, 24 novembre 2026 (Claude). Non congelata, da rivedere con Codex.** Non autorizza calcoli prospettici.
- Modifica soltanto un requisito del §7 del protocollo congelato (`docs/PROTOCOL_MDI_TILT_PILOT.md`, SHA
  `77367350…`): «l'assegnazione dei flussi che conservi la relazione con area, latitudine e attività».
- Il protocollo originale e l'emendamento A1 restano intatti. Tutto il resto resta invariato.
- Si congela **prima** della nota Q4 (`docs/MDI_PILOT_Q4_NOTE_DRAFT.md`); la nota registra entrambi i riferimenti.

## Non è cieco: cosa era già noto

- Tutti i risultati del pilota (L1 e L2), descritti al §1 della nota Q4.
- I conteggi preparatori di `results/MDI_Q4_PREP_COUNTS/` (regole fissate prima di contare in
  `docs/MDI_Q4_PREP_COUNTS_RULES.md`, SHA `9ce409fc…`), in particolare C7. Non è stato letto nessun tilt e non è
  stata calcolata nessuna precisione.

## Motivo

Le regole fissate prima dei conteggi definivano «troppo pochi» come meno di 5 donatori e due regole candidate. Con i
donatori del pilota (498 record L1 riusciti a 50 G in 36 celle di selezione), sui 5151 bersagli MS:
- **L-T**, classi di |lat| (terzili globali della popolazione MS filtrata) dentro la cella di selezione: 58,6 % dei
  bersagli con almeno 5 donatori, contro il 90 % fissato;
- **L-NN**, 5 donatori più vicini in |lat| nella cella: ogni cella ha almeno 5 donatori, ma il 90° percentile della
  distanza massima è 10,3°, contro 5° fissati (mediana 4,9°).
- A 100 G: 48,0 %; 90° percentile 12,3°, mediana 5,5°.

Le due regole candidate non soddisfano i criteri fissati con questi donatori. La regola fissata prevede in questo
caso un emendamento.

## Testo dell'emendamento

Nella nota Q4 il requisito sui flussi del §7 è **attenuato, non soddisfatto**:
1. il flusso di un gruppo del disegno viene da donatori della stessa cella di selezione. Si conservano le **classi**
   di attività (terzili di A_main), area, emisfero e coorte, non la loro distribuzione congiunta esatta;
2. la latitudine è approssimata con i 5 donatori della cella più vicini in |lat| (parità: distanza, poi ordine
   (noaa, day)). Il vicinato limita una distanza in |lat|; non verifica la relazione flusso–latitudine;
3. la distanza in |lat| fra bersaglio e donatori si riporta sempre, per MS e per MF;
4. si riporta sempre, accanto, la sensibilità senza latitudine (donatore uniforme fra i donatori della cella);
5. il fallimento dei criteri originari resta dichiarato nella nota e nel rapporto Q4.

La conservazione della relazione flusso–latitudine resta un limite dichiarato di Q4.

## Cosa non cambia

- Gli altri requisiti del §7: σ²ₓ, κ e σ_e; resa e strati senza dati; disponibilità full-disk; non calcolabilità.
- Il principio che il congelamento del protocollo, di A1 o di A2 non autorizza Q4.

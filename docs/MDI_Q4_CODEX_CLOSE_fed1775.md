# MDI Q4 — chiusura della revisione del codice fed1775

25 novembre 2026, Codex. Script revisionato: `scripts/mdi_q4_prospective.py`,
SHA-256 `033b233bebfa63acfa6743b53ca4e0b9d27548301bb6e45824257514d0667bb6`.

**Esito: pronto tecnicamente per la corsa prevista dalla nota congelata.**
I cinque rilievi della revisione di bb39a23 sono chiusi. Nessuna modifica
al codice produttivo, alla nota Q4 o ad A2 in questa revisione.
Non eseguito `--run`, non creato `results/MDI_Q4_PROSPECTIVE`, nessun dato
scaricato e nessuna precisione calcolata sui disegni MDI reali.
L'avvio resta una decisione dell'utente, come stabilito nella nota congelata.

## Riscontri

1. **Ricevute.** Verificati PIN, insiemi esatti dei 17 input e 9 moduli,
   hash effettivi, riferimenti al padre e ad A2, regole e META preparatori,
   semi e Z, blob e ascendenza dei commit di congelamento. Le controprove
   in memoria non modificano i file. Il controllo reale restituisce [].
2. **Bersaglio nullo.** I rapporti non definiti diventano NaN con flag;
   restano SE, semilarghezza e frequenza sotto lo scenario nullo. Nessun
   epsilon altera il bersaglio. Gestione verificata per tutti i quattro tag.
3. **Fallimenti.** Disegno vuoto con stato esplicito; compute espande i
   fallimenti sulla stessa griglia delle configurazioni previste, incluse
   le varianti combinate. SUMMARY conserva zero successi e conteggia n_fail;
   duplicati di configurazione/realizzazione rifiutati. I criteri non
   classificano quando una realizzazione usata non e calcolabile.
4. **Quattro bersagli.** Rapporti, frequenze, scarti relativi, tolleranze
   e scenari peggiori hanno colonne esplicite per 020/010 e qd_020/qd_010;
   A_lo_design e A_hi_design sono mantenuti in RAW. SE e h sono comuni.
5. **Conteggi e metadati.** CELL_COUNTS contiene le N per le 36 celle
   prima e dopo i filtri; verificati 5401, 5151 MS e 5062 MF. YIELD_EFFECTS
   separa unita, pooling, dominio e media Beta; registra tutte le scelte
   d'implementazione dichiarate e le due regole di gestione.

## Prove eseguite

- `mdi_q4_prospective.py --selftest`: **55/55**, uscita 0. Comprende prove
  sintetiche end-to-end, E0, rese e conteggi preparatori; non una corsa Q4.
- Sonda precedente rieseguita in copia con destinazione temporanea nuova:
  i controesempi originali non riproducono piu i difetti.
- Nuova sonda `scripts/mdi_q4_close_review_probe.py`: **50/50**, uscita 0.
  Su 120 record artificiali confronta la proiezione WLS con una soluzione
  diretta indipendente, i quattro bersagli con la rampa scritta separatamente,
  riconoscimento e casi peggiori con la CDF normale di scipy, tolleranze e
  rapporti. Controlla anche 20/20 fallimenti, un successo su 20 e duplicati.
- Dipendenze dichiarate: la sonda importa il modulo produttivo per interrogarlo;
  alcuni pezzi della varianza usano i coefficienti restituiti dal modulo.
  Non e un riconteggio indipendente dell'intera catena scientifica e non
  sostituisce il riconteggio degli output richiesto dopo la corsa.
- La nota e A2 mantengono gli SHA congelati; i 17 input e 9 moduli sono
  verificati senza modificarli. Nessuna colonna individuale di tilt MDI
  letta dalle sonde aggiuntive.

## Lettura dei prodotti e sequenza

Dopo la decisione dell'utente:
1. `--run` da albero tracciato pulito e codice corrispondente a HEAD;
2. redirigere stdout/stderr a un log: il runner stampa CRITERIA alla fine,
   quindi non leggerlo prima della conservazione;
3. conservare tutti gli output e il log in Git prima della lettura;
4. riconteggio indipendente e conservazione della ricevuta;
5. lettura e rapporto descrittivo, poi decisione sul catalogo/prodotto MDI.

Per YIELD_EFFECTS MF, ogni pool ha il suo ramo che riparte dalla stessa
base con le unita del gap escluse: non leggere il passaggio dall'ultimo
step Beta di un pool al primo step del pool successivo come una catena
lineare a un solo cambiamento. Le etichette identificano i rami.

Non cambia il livello d'evidenza: Q4 stima precisioni condizionate a scenari
nel riferimento normale a varianza nota, non valida M su MDI, non misura
quenching reale e non produce una serie BL combinata. Il modello MF della
resa e approssimato; la conservazione flusso-latitudine resta attenuata,
non soddisfatta, secondo A2. Un esito favorevole non autorizza da solo
la costruzione di un nuovo catalogo o una nuova analisi T3.

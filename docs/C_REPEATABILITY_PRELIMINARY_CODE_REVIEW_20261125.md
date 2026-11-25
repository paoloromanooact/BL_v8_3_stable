# C — revisione preliminare del codice preparatorio (Codex, 25 novembre 2026)

**Non approvato per misure osservate.** Lettura statica della versione di lavoro, non ancora committata da Claude;
nessun nuovo test pesante, FITS osservato o stima. Gli hash in fondo identificano le versioni lette.
Il riconteggio indipendente C manca ancora. Il 11/11 riferito ai sintetici non sostituisce la revisione del codice.

## Rilievi da chiudere

1. **Supporto finito (§4):** `measure_pair`, righe 88–89, usa `OP.coverage` sui soli centri finiti e poi erode
   questa copertura. `coverage` marca la cella True se contiene almeno un centro valido: un pixel non finito
   nella stessa cella di un pixel valido sparisce dal controllo. Il criterio della bozza esclude invece le celle
   contenenti centri invalidi. Separare impronta geometrica C_geo e validita C_fin, e seguire anche lo stencil
   effettivo del deposito. Regressione: due centri nella stessa cella, uno valido e uno NaN/cap; non dichiarare
   osservata integralmente la cella. Nessuno zero imputato deve apparire come dato finito.
2. **Bilanciamento nel dominio:** il controllo righe 75–84 e la riscalatura in `OP.pixels` avvengono su tutta
   la patch, prima della restrizione a C_fin. Una polarita presente solo fuori dal dominio rende la variante
   `ok` anche quando C_fin e monopolare; i flussi misurati nel dominio possono restare sbilanciati. La bozza
   richiede stato non disponibile se manca una polarita su C_fin. Fissare esplicitamente il supporto della
   riscalatura, coerente alla bozza, e ricontrollare entrambe le polarita sul campo effettivamente misurato.
   Regressione con negativo solo fuori C_fin; raw resta misurabile e non si riscalano i suoi flussi.
3. **Leading-change, riga 110:** il segno di lon_pos-lon_neg non e periodico. Positivo a 179 e negativo a -179
   danno +358 anziche -2 gradi. Inoltre si controlla la finitezza della sola lon_pos: una lon_neg NaN puo
   produrre True spurio. Usare la convenzione leading della misura P1 restituita da `measures`; esito non
   definito se a uno dei due istanti mancano le due polarita. Regressioni sul taglio +/-180 e su unipolarita.
4. **Bootstrap, righe 199–214:** MIN_COMPONENTS viene applicato prima del filtro dei valori finiti. Con 15
   componenti ma dati per una sola quantita in una componente puo essere prodotto un intervallo; alcune
   repliche senza dati arrivano a `np.average` vuota. Contare le componenti valutabili per osservabile,
   distinguere mancanti e fallimenti delle repliche, soglia <10 e nessun crash. Dichiarare la regola dei
   pesi dopo le mancanze in coerenza col bersaglio componente→coppia; non cambiare il bersaglio in silenzio.
5. **C_rot, righe 120–133:** "almeno 8 sottopunti su 16" e una nuova regola di copertura rispetto all'intero
   stencil valido richiesto dalla bozza rev.3. Il trasferimento dal pilota osservativo non la autorizza da
   solo per C. Allineare alla regola congelabile: supporto geometrico e validita del trasporto effettivo,
   con caso in cui 8 punti validi e 8 invalidi non devono essere scambiati per copertura integrale. Non
   affermare C_rot=C_fin per costruzione anche in presenza di buchi nel campo iniziale.

Sono rilievi di lettura con controesempi espliciti da implementare nei test, non fallimenti del test 11/11
eseguito da me: non ho rilanciato quel test durante questa revisione.

## Stato della tabella e consegna a Claude

C non e ancora "freeze poi misura": servono correzioni, runner operativo con provenienza/prodotti/riepiloghi,
**riconteggio indipendente ancora da scrivere**, review e freeze prima della corsa osservata. L'attuale --run
rifiutato e corretto come protezione ma non e un gate operativo gia completo. Riepiloghi per lag/emisfero/USFLUX,
raffinamento 0,03 sullo stesso supporto e ricevute richiedono ancora l'assemblaggio completo, non solo funzioni.

Claude chiude i rilievi senza duplicare il suo lavoro gia in corso su A1/BQ. Codex rivedra le versioni committate
e le regressioni. Non modifico i file preparatori di Claude durante le sue prove.

I due pilastri restano sorgente BL e quenching, solo HMI; C serve alla prima. BQ-M rinviato, nests sospesi.

## Versioni lette (SHA-256)

- `scripts/sft_c_repeatability.py`: `6e97dcaa8254ddae077aa4a542d9780bbdb29807e5ff3888fde293e77bf48d6b`
- `scripts/sft_c_repeatability_selftest.py`: `11dd72a882997bcb000ae36b5dcbe8583a41018056685fd7d2b366357d35eebb`
- `scripts/sft_observed_pilot.py`: `dec3c4cea56e9c11760751fe050a424c02481d80b53aacc54657d9bcda972ffb`
- `docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md`: `614e4fbd67be069ef8cc4bf79a4c2f8c30bc07944b6f94006b2736a157d1fba3`

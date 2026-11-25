# A1 SFT in lavorazione: criterio assoluto e precisione dei rapporti

25 novembre 2026, Codex. **Nota preliminare sulla bozza non committata, non chiusura della revisione del codice.**
Nessuna mappa osservata o corsa SFT eseguita. Fonte: `PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_DRAFT.md`, §2bis.
Fotografia letta: SHA-256 `614c96a549fc69793786dc6c8ff3af379598f57a7ed73d27c0ff5b75561d949f`.
La bozza propone di passare da f=1e-6 a f=1e-2 in
|D_fine-D_coarse| <= 1e-3 max(|D_fine|, f D_scale), con alternativa f=1e-1.

## Esito preliminare

La parte di requisito bloccante e raffinamento comune è coerente con la revisione precedente. L'allentamento
è una **seconda modifica numerica**, distinta dallo schema ibrido. Non è già deciso da Codex e non va presentato
come una soglia invariata. La bozza va resa coerente: alcune righe dicono ancora «nessuna soglia allentata».

I fallimenti riferiti alle risoluzioni provate sono evidenza di difficoltà numerica in quei casi, non una prova
che il criterio sia irraggiungibile a qualunque risoluzione né, da soli, una verifica che non ci sia un bug.
L'errore assoluto piccolo è un argomento da quantificare rispetto a ciò che si pubblica.

## Controesempio al trasferimento automatico sui rapporti

Una coppia di dipoli può rispettare il nuovo requisito e avere un rapporto poco risolto, anche oltre la soglia
0,1 m(t) congelata. Controesempio algebrico, **non un caso osservato o una soluzione della PDE**:

- D_scale=1, m(t)=1e-4, D_M=2e-5: il denominatore supera 0,1 m(t)=1e-5.
- D_B(coarse)=2e-5, D_B(fine)=2,9e-5: differenza 9e-6, criterio 9e-4, quindi passa con f=1e-2.
- (D_B-D_M)/D_M cambia da 0 a 0,45.
- Con f=1e-1 il medesimo tipo di esempio può ammettere una variazione 4,5.

Quindi «errore piccolo in D_scale» non implica automaticamente «due ordini sotto la risoluzione dei rapporti».
Il denominatore è fissato da una mediana comune, mentre D_scale è specifica della regione. Senza un limite sul
loro rapporto, la conclusione non segue. La sonda indipendente conserva entrambi gli esempi.

## Indicazioni per la versione da rivedere

1. Distinguere accuratezza di D, di Delta D/D_scale e dei rapporti; non giustificare f con l'arrotondamento delle
   tabelle o il solo fatto che il selftest passa.
2. Se si propone f=1e-2 come soglia assoluta operativa, dichiarare il nuovo errore ammesso e verificare anche
   l'accuratezza effettiva delle quantità derivate. Non approvo automaticamente f=1e-1.
3. Per i rapporti: fissare prima dei dati una regola di verifica e di esito «numericamente non risolto» quando
   il denominatore amplifica l'errore; non togliere la regione dagli altri prodotti o cambiare m(t) dopo la lettura.
4. Riportare i casi quasi nulli, gli scarti firmati/assoluti, il tipo di raffinamento e i parametri. I risultati
   diagnostici di una corsa tecnicamente fallita restano conservati e distinti da una corsa valida.
5. Attendere il commit e le prove del codice definitivo prima della revisione di chiusura. Questa nota non
   modifica il padre congelato, la soglia o i file in lavorazione di Claude.

# Q4 — regole dei conteggi preparatori (fissate prima di contare)

24 novembre 2026 (Claude). Preparazione **non cieca** della revisione 2 di `docs/MDI_PILOT_Q4_NOTE_DRAFT.md`, come
concordato con Codex (`MDI_Q4_NOTA_RISPOSTA_REVISIONE_CODEX.txt`, risposta Q1). Questo file è scritto prima di
eseguire lo script; lo script ne registra lo SHA-256 negli output.

**Limiti:**
- solo conteggi e riscontri su file conservati del pilota;
- nessun tilt letto: da `L1_RECORDS.csv` e `L2_RECORDS.csv` si leggono solo identificativi, stati, mappe e
  rotazioni;
- nessuna precisione prospettica, nessuna simulazione, nessun dato nuovo.

Script: `scripts/mdi_q4_prep_counts.py`. Output: `results/MDI_Q4_PREP_COUNTS/`.

## C1. Classi di attività e di area della selezione

- Fonte: `results/MDI_PILOT_SELECTION/META.json`, `edges.A_main` e `edges.area` (terzili lineari NumPy della
  popolazione; A_main = codice DESIGN MWO normalizzato 1974–2012, aree DPD).
- Ricalcolo: classe = searchsorted(edges, x, right) + 1, su `POPULATION.csv`.
- Riscontro: numero di discordanze con `act_class` e `area_class` registrati. Atteso 0.

## C2. Mappe sinottiche richieste

- Regola del pilota (`scripts/mdi_synoptic_adapter.py`, `group_rotation` ed `extract` con dlon = 8°, margine 0):
  CT_g da `group_rotation`; mappe richieste = {⌊c/360⌋ + 1 per c in (CT_g − 8, CT_g, CT_g + 8)}.
- Mappe mancanti: le CR fra la minima e la massima di `results/MDI_SYNOPTIC_AUDIT/FILES.csv` assenti
  dall'inventario.
- Riscontro sui 530 record di `L1_RECORDS.csv`:
  - N e N_ephemeris ricalcolati uguali a quelli registrati;
  - per `status = map_missing`, mappe richieste = colonna `maps`;
  - per gli altri record con `maps` non vuota, `maps` ⊆ mappe richieste;
  - nessun record riuscito ha mappe richieste nell'insieme mancante.
- Popolazione: gruppi con mappe richieste ∩ mancanti ≠ ∅; gruppi con N ≠ N_ephemeris.

## C3. Filtri del periodo Q4

Contati separatamente e in sequenza, sulla popolazione di 5401 gruppi:
1. data di t_DPD ≤ 2010-04-30;
2. CR(t_DPD) < 2096, con CR(t) = max{c : cr_start(c) ≤ t} e cr_start di Meeus della fase A;
3. solo per MS: mappe richieste disgiunte dalle mancanti; gruppi con N ≠ N_ephemeris esclusi e contati.

Si riportano anche, solo come descrizione, i gruppi con t_DPD in [1998-06-01, 1998-11-01) (lacuna E2 della fase A).

## C4. Cicli × emisfero

- Ciclo del tempo: `cycle_of_time(cr_start(CR(t_DPD)))` della fase A (minimi m₂₃ = 1996-08, m₂₄ = 2008-12).
- Conteggi per ciclo × emisfero, per MS e per MF dopo i filtri C3.
- Riscontro descrittivo per la revisione 2: quante celle ciclo × emisfero hanno almeno 50 gruppi della popolazione
  filtrata (non record attesi: la resa non è applicata).

## C5. Riproduzione deterministica delle rese proiettate

Senza Beta, senza pooling, senza filtri Q4. Celle = attività × emisfero × area × coorte della selezione.
- L1: per ogni insieme di `Q1_YIELD_PROJECTED.csv`, resa = Σ_c N_c·ok_c/n_c / Σ_c N_c (e a 100 G con ok100), con
  N_c, n_c, ok_c ricostruiti da POPULATION, SAMPLE e lo stato di L1_RECORDS.
- L2: per ogni riga di immagine A di `YIELD_A1.csv`, lo stesso con n2 e successi A1 dell'immagine A da L2_RECORDS.
- Riscontri: somme di N (5401), n (530, 90), ok; pesi N_c/n_c uguali a 1/π di SAMPLE; unicità degli abbinamenti
  (noaa, day). Tolleranza: 1e-12 relativa sulle rese pubblicate a precisione piena.
- Un fallimento si riporta e non si corregge in questo passo.

## C6. Celle e pool delle rese

- MS: per ogni cella, n, ok, ok100 dopo aver tolto le unità del campione con mappe richieste mancanti; riscontro che
  nessun successo sia fra le unità tolte.
- MF (regola A1, immagine A): n2 e successi per cella; per cella con n2 < 5 (soglia della bozza), e aggregati per
  coorte × area, coorte × attività, coorte × emisfero e coorte: n, successi, Σ N, resa proiettata e n efficace di Kish
  (Σw)²/Σw² con w = N_c/n_c.

## C7. Donatori di flusso e latitudine

Donatori = record L1 riusciti alla soglia principale (50 G) nella stessa cella di selezione; a 100 G con ok100.
Bersagli = gruppi della popolazione filtrata per MS (C3).

**«Troppo pochi»** = meno di 5 donatori riusciti nello strato del bersaglio.

**Regole candidate, in ordine fisso:**
- **L-T:** classi di |latitudine| = terzili lineari NumPy di |lat| della popolazione filtrata MS, dentro la cella di
  selezione. Adottata se almeno il 90 % dei bersagli ha almeno 5 donatori nella propria cella × classe.
- **L-NN:** i 5 donatori della stessa cella più vicini in |lat| (parità: ordine (noaa, day)). Adottata, se L-T non lo
  è, quando ogni cella con bersagli ha almeno 5 donatori e il 90° percentile, sui bersagli, della distanza massima in
  |lat| fra bersaglio e suoi 5 donatori è ≤ 5°.
- **Emendamento:** se nessuna delle due è adottata, la revisione 2 propone un emendamento non cieco che restringe il
  requisito di latitudine del protocollo §7, motivato con questi conteggi.

Le soglie 90 %, 5 donatori e 5° sono scelte pratiche fissate qui, non derivate dai dati. L'adozione si decide su 50 G;
a 100 G si riporta lo stesso esito come descrizione.

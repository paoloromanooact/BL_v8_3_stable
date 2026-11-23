# T3 su MWO R4 — diagnosi descrittiva di S2 (nota finale prima della corsa)

**Versione finale, 23 novembre 2026 (Claude).**
- Recepisce la revisione di Codex `f8f864c` (`docs/T3_MWO_S2_DIAGNOSIS_CODEX_REVIEW.md`) sulla bozza `a252063`.
- Da questo commit la nota non si modifica; il suo SHA-256 è registrato nel META della corsa.
- **Non eseguita.** La corsa reale richiede prima la revisione di codice e prove sintetiche.

## Natura

- Diagnosi **successiva alla lettura** degli esiti di stabilità e della stima: non è cieca.
- Non è un emendamento: non cambia S2, la regola, l'esito «descrittivo» di β₃, soglie o selezioni.
- Nessun verdetto, nessun nuovo test T3, nessuna classificazione riassuntiva, nessuna attribuzione causale,
  nessuna correzione del catalogo o di β₃, nessuna simulazione lunga.
- Gli intervalli dei sottoinsiemi e delle componenti sono **nominali e non validati**. I fit sono correlati fra loro
  e lo stimando cambia con il sottoinsieme.

## Domande (descrittive)

1. Come si scompone S2, sullo stesso disegno, fra la risposta MWO, la risposta in luce bianca e il termine di
   riavvolgimento assiale.
2. Di quanto cambia la stima escludendo un'epoca o restringendo a una fonte DPD o a un terzile di caratteristiche
   delle regioni.
3. Quanto pesano i record con differenze grandi.

## Dati e controlli prima della lettura

- Sottoinsieme S2: record isolati di R4 con `wl_status == ok`, nell'ordine del DESIGN, come in `stability()`.
  - Devono essere **4694 righe**.
  - γ_WL e d_WL vengono da `results/T3_MWO_STABILITY_R4/WL_TILTS.csv`.
  - γ_MWO viene da `joy_gamma_deg` della tabella isolata del rilascio verificato. Il join su (noaa, giorno UTC) deve
    essere univoco.
  - Nessuna lettura di SEALED.
- Fonte DPD del giorno: dal file giornaliero usato da `scripts/t3_mwo_stability_extras.py` (`daily_sources`).
- Verifiche prima di produrre qualsiasi riga:
  - ricevute complete (partial false, conteggi uguali) dei riconteggi di stabilità, stima e rilascio, legate ai
    rispettivi META;
  - hash dei prodotti sorgente uguali a quelli dichiarati nei META;
  - axial(γ_MWO − γ_WL) uguale a d_WL salvato, entro 1e-9;
  - `s2_fit` sul sottoinsieme ricostruito riproduce β, SE e intervallo di STABILITY.json entro 1e-9.
- Nessuna sovrascrittura. Scrittura atomica: cartella temporanea, poi rinomina.

## Analisi

Ogni fit usa `s2_fit` della catena congelata (stesso modello, stessi pesi Φ_MWO, procedura M, nominale 97,5 %), senza
modificarlo.

**Soglia di presentazione.** Un fit con meno di **300 record** non viene eseguito e mantiene una riga esplicita
(«sotto soglia»). Uno non identificabile o in errore mantiene la sua riga con lo stato. Nessuna sostituzione e nessun
adattamento della soglia. La soglia è operativa e non garantisce precisione, indipendenza o validità.

**Righe dei fit.** Ogni riga riporta:
- colonna `kind` (completo, sottoinsieme, esclusione di un'epoca, sensibilità D6) ed etichetta;
- n, numero di CR, numero di blocchi di 6 CR;
- composizione per ciclo, epoca ed emisfero; minimo e massimo di A_main;
- n_eff = (Σw)²/Σw²;
- identificabilità e stato;
- β, SE nominale, intervallo;
- parametri di M e flag di bordo REML (φ ≤ 1e-9 o ≥ 0,98 − 1e-9; |κ| ≥ 0,98 − 1e-9);
- Δβ = β − β_S2;
- Δβ/SE_S2, con β_S2 e SE_S2 letti non arrotondati da STABILITY.json. È una **scala descrittiva, non un test di
  differenza**.

Nessun flag rispetto a ±C: C è il margine del disegno S2 completo, non un margine per i sottoinsiemi.

**D1. Scomposizione** (stessi record, ordine, pesi, attività, sin|λ̄| MWO e matrice ridotta per tutte le risposte).
- Definizioni: u = γ_MWO − γ_WL, d = axial(u), r = d − u, g = riga WLS di β₃ in `g_row`.
- Identità: g·d = g·γ_MWO − g·γ_WL + g·r. Si riportano tutti e quattro i termini e il residuo numerico.
- Riavvolgimenti: record con |r| > 1e-9. La funzione congelata manda +90° in −90° (r = −180°). Il numero di
  riavvolgimenti e la loro somma pesata si riportano separatamente per r = −180° e per r = +180°.
- Per γ_MWO e γ_WL: SE e intervallo di M come valori nominali non validati per queste risposte.
  - Non si sottraggono i SE e le componenti non si trattano come indipendenti.
  - Nessun verdetto e nessuna etichetta T3 per γ_WL; non si salva il campo «verdict».
- La scomposizione non identifica quale strumento o fenomeno causi la differenza.

**D2. Esclusione di un'epoca.** Esattamente sei fit, `kind = leave-one-epoch-out`: S2 senza E2, E3, E4, E5, E6, E8.
E1 ed E7 restano incluse.

**D3. Fonte DPD.** Esattamente due fit, `kind = subset`:
- fonte GYUL;
- tutte le altre fonti con codice alfabetico.

I record senza riga giornaliera (`(missing)`) o con fonte non alfabetica (`(none)`) restano fuori da entrambi i fit e
sono contati con la loro etichetta.

**D4. Caratteristiche delle regioni.** Esattamente nove fit, `kind = subset`: i terzili di (a) `dpd_area`,
(b) `phi_mwo`, (c) `separation_deg` del rilascio.

**D5. Riassunti per terzile di attività A_main.**
- Gruppi:
  - tutto il sottoinsieme;
  - N e S (solo riassunti, nessun fit N/S incrociato);
  - le sei esclusioni di D2;
  - i due gruppi di D3 e il gruppo delle fonti mancanti o non alfabetiche;
  - le nove categorie di D4.
- Per ogni gruppo e terzile di attività (1, 2, 3 e «tutti»):
  - n;
  - mediana non pesata di d_WL;
  - media pesata con Φ_MWO;
  - quota non pesata di |d_WL| > 45°.
- Il bootstrap dà intervalli per le tre statistiche; n resta descrittivo.

**D6. Differenze grandi.** Un fit con `kind = sensitivity`: S2 senza i record con |d_WL| > 45°.
- Si riportano numero e quota dei rimossi per terzile di attività e per emisfero.
- La selezione è sulla risposta: il cambiamento di pendenza può venire dal taglio stesso.
- Non interpreta i record rimossi come errori di misura e non serve a correggere il catalogo o a scegliere una nuova
  analisi principale.

**D7. Parametri di M.** Inclusi in ogni riga dei fit; nessuna conclusione causale da φ.

## Terzili e bootstrap (regole univoche)

**Terzili.**
- Confini: quantili NumPy lineari non pesati (1/3, 2/3) sui 4694 record completi, tenuti fissi in ogni gruppo.
- Classe = `searchsorted(confini, valore, side="right") + 1`: valori uguali non vengono mai separati.
- Un terzile vuoto è dichiarato tale.
- Vale per A_main (D5) e per le tre variabili di D4.

**Blocchi.** floor((CR − CR_min)/6), con CR_min il minimo dell'intero sottoinsieme S2; i due emisferi stanno insieme.

**Estrazioni.**
- Unico generatore `numpy.random.default_rng(69 600 001)`.
- 2000 estrazioni con reinserimento di tanti blocchi quanti sono quelli distinti del sottoinsieme.
- Le estrazioni sono **comuni** a tutti i riassunti: si ricampiona l'insieme completo, poi si applicano gruppi e
  terzili fissi.
- Nessuna nuova estrazione per rimpiazzare repliche senza record o con denominatore nullo: si contano.
- Intervallo percentile al 95 % (`numpy.quantile`, metodo lineare) solo con almeno **1900** repliche valide;
  altrimenti l'intervallo è mancante, con la causa. È una soglia tecnica, non una prova di copertura.
- Nessun bootstrap di M dentro D5.

**Seme.** 69 600 001. Il selftest lo confronta con l'elenco effettivo dei 76 000 semi della griglia, con gli
intervalli USED, con S1 (69 000 001) e con Joy (69 500 001).

## Uscite

In `results/T3_MWO_S2_DIAGNOSIS_R4/`, con ordinamento canonico:
- `FITS.csv`: D2, D3, D4, D6 e la riga completa;
- `DECOMPOSITION.json`: D1;
- `SUMMARIES.csv`: D5;
- `COUNTS.csv`: fonti, terzili, rimossi D6;
- `META.json`: SHA della nota, dello script, dei moduli e degli input, commit, seme.

Le uscite si conservano in Git prima della lettura.

## Riconteggio indipendente

`scripts/t3_mwo_s2_diagnosis_recount.py` ricostruisce con codice proprio:
- la riga g (WLS propria);
- l'identità con il termine assiale;
- gruppi e chiavi, perdite di record, terzili;
- i riassunti D5, ripetendo le stesse estrazioni.

β, SE e intervalli di M sono richiamati dalla procedura comune: è una **dipendenza dichiarata**, non un SE
verificato in modo indipendente. Il riconteggio produce una ricevuta legata al META.

## Prove sintetiche (senza dati reali)

- Identità D1 senza riavvolgimento; con riavvolgimenti in entrambi i versi; al taglio +90°.
- Terzili con valori uguali e terzile vuoto.
- Gruppi sotto 300 record; fit non identificabile.
- Repliche bootstrap vuote e soglia di 1900.
- Rifiuto di sovrascrivere.
- Seme contro le liste effettive.

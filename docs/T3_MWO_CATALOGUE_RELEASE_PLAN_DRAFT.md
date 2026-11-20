# Rilascio del catalogo di tilt magnetici MWO 1974–2012 — piano (bozza)

**BOZZA, 20 novembre 2026 (Claude), su richiesta dell'utente («dobbiamo cercare di concludere il lavoro»). Da rivedere
con Codex.** È il passo 12 dello schema T3 su MWO e viene **dopo** la stima di β₃: i tilt restano sigillati fino a
quel momento. Lo script di esportazione rifiuta di partire finché la stima non è conservata in Git.

## Scopo

Rendere il catalogo costruito per T3 un prodotto di dati riusabile e pubblicabile:
- una riga per regione misurata;
- tilt magnetico con polarità, misurato sui magnetogrammi Fe I di Mount Wilson con la regola congelata
  (`docs/PROTOCOL_T3_MWO.md`, emendamenti A1–A3);
- provenienza, controlli di qualità e confronti con altri strumenti documentati.

## Contenuto del rilascio

1. **Due tabelle**, perché per lo stesso gruppo i due insiemi possono scegliere giorni diversi (con o senza condizione di
   isolamento):
   - `MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv`: insieme principale di T3, R4 con 5223 regioni;
   - `MWO_TILT_CATALOGUE_ALL_1974_2012.csv`: insieme senza condizione di isolamento, 5942 regioni.

   Colonne, una riga per gruppo DPD:
   - identificazione: NOAA (stringa DPD), giorno UTC, istante MWO, file FITS, epoca, classe di risoluzione, CR, ciclo;
   - posizione: latitudine media pesata col flusso, latitudine, longitudine di Carrington e LCM del gruppo DPD,
     emisfero;
   - misura: tilt (convenzione di P1), variabile di Joy γ, segno della polarità di testa, segno di Hale atteso,
     baricentri delle due polarità, separazione, flusso nella finestra;
   - qualità: isolamento e numero di vicini, rango del giorno scelto, numero di giorni candidati, pixel BLANK nella
     finestra;
   - attività: attività emisferica DPD del mese.
2. **`README`**: definizioni, unità, convenzioni di segno, regola di misura, emendamenti, limiti noti:
   - risoluzione circa 10″–20″;
   - correzione di saturazione e zero non documentata nei FITS nativi;
   - epoche documentate solo dagli header prima del 1996;
   - popolazione delle regioni misurabili, con selezione legata all'attività.
3. **`EXCLUDED_MAGNETOGRAMS.csv`**: i 26 file esclusi (A2 18, A3 8) con motivo e SHA-256; i 2 file illeggibili del
   2013; l'esito dell'audit dei pixel.
4. **`VALIDATION_SUMMARY`**:
   - confronto con HMI (P1) sulle regioni comuni 2010–2012: pilota (211) e controllo S2-P1 del catalogo;
   - confronto con i tilt in luce bianca DPD per epoca (S1, S2);
   - accordo di Hale per epoca (S3);
   - eventuale confronto con MDI 1996–2010, facoltativo, da decidere.
5. **Controllo di coerenza: legge di Joy per ciclo ed emisfero.** Il coefficiente k in γ = k·sin|λ| con WLS pesata col
   flusso e senza pesi, con intervallo bootstrap a blocchi di CR, confrontato in modo solo descrittivo con i valori
   pubblicati. I valori della letteratura vanno verificati sulle fonti primarie prima di citarli.

## Condizioni aggiunte dopo la revisione di Codex (20 novembre)

1. **Prerequisito dell'esportazione definitiva.** Non basta che la stima di β₃ sia in Git: serve anche la ricevuta
   completa e non parziale del suo riconteggio indipendente (`scripts/t3_mwo_estimate_recount.py`), legata allo
   SHA-256 del META della stima. L'esportatore lo verifica (`release_problem`). Per il riconteggio, lo stadio di stima
   salva anche i parametri di varianza di M e i legami a stabilità e catalogo: modifica inclusa nella patch non
   ancora applicata.
2. **Popolazione descritta con precisione** nel README: regioni DPD (area ≥ 1, |λ| ≤ 45°) isolate e misurabili, cioè con
   finestra ±6°/±8° nel dominio μ ≥ 0,8 e due polarità oltre 50 G entro 4000 G, all'istante della scansione scelta. Per
   l'insieme principale il giorno è quello isolato con |LCM| minimo e misura riuscita. Vanno documentati:
   - esclusioni (A1 BLANK, A2 18 file, A3 8 file, 2 illeggibili, effemeridi);
   - perdite per ciclo, emisfero, epoca e terzile di attività (LOSSES.csv);
   - epoche e classi di risoluzione, con la loro composizione;
   - il legame fra selezione e attività: le regioni grandi sono misurabili più spesso.
3. **Legge di Joy per ciclo, definita ora e solo descrittiva:**
   - k in γ = k·sin|λ̄| per ciclo × emisfero, regressione per l'origine;
   - due versioni: pesi Φ_MWO e pesi uguali;
   - intervallo bootstrap percentile al 95 % a blocchi di 6 CR consecutive dentro il gruppo, 2000 repliche, seme
     69 500 001;
   - presentazione: tabella e figura dei k con intervalli, accanto ai valori pubblicati verificati sulle fonti
     primarie, senza test né verdetti. Un confronto inferenziale richiederebbe un piano distinto.
4. **Confronti nella prima versione:** HMI (P1) e DPD in luce bianca. MDI è un'estensione successiva.

**Aspettativa corretta.** Una validazione superata con esito «non deciso» non garantisce un limite stringente:
l'intervallo ottenuto va tradotto nello scenario prescritto (rampa di attività), e β₃ non diventa automaticamente una
percentuale massima di quenching. La forma editoriale si valuterà sui risultati effettivi.

## Ordine

1. Stima di β₃ conservata e ricontata (ricevuta completa e legata).
2. Esportazione (`scripts/t3_mwo_catalogue_release.py --export`).
3. Riconteggio indipendente dell'esportazione: ogni colonna contro DESIGN e SEALED.
4. Legge di Joy per ciclo.
5. README.
6. Revisione di Codex.
7. Deposito: luogo e licenza da decidere con l'utente e con Paolo, per esempio Zenodo con DOI.

## Questioni aperte

- Rilasciare anche l'insieme «tutti» (proposta: sì, come seconda tabella) o solo quello degli isolati.
- Includere il confronto con MDI (richiede il catalogo MDI descrittivo, oggi in pausa).
- Formato: CSV più eventualmente FITS; licenza; autori e ringraziamenti all'osservatorio di Mount Wilson e a Debrecen.

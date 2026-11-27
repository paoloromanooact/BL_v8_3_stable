# Ripetibilità C: pacchetto per il congelamento (BOZZA per la revisione Codex)

Claude, 27 novembre 2026. Pilastro: sorgente BL (incertezza osservativa per il confronto SFT/BT). **Non congelato.**
Raccoglie in un documento ciò che si congelerebbe, ciò che è implementato e verificato e ciò che la bozza prevede ma il
codice non fa ancora, perché Codex possa decidere in una lettura. Nessun pixel osservato è stato letto per C.

## 1. Cosa si congela

| Oggetto | Percorso | SHA-256 |
|---|---|---|
| Specifica (rev. 3 + §4bis, con §4bis.8) | docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md | da64432ab9d3faea243142879016ec49574c48b54442f1ea50cadf5a62e40e41 |
| Runner | scripts/sft_c_repeatability.py | 0f03ec8fd8f8f0a2a700dbd014eb6313941b767a1459969e90f29b230db807a1 |
| Selftest del runner | scripts/sft_c_repeatability_selftest.py | 79f77fec6d4692b8df35cdcb86f55dc0e0bd9411b07895877812b26229518c69 |
| Riconteggio indipendente | scripts/sft_c_repeatability_recount.py | 1d2fcafa43d2844964a400d43bc6cdc9f25b210d465fa2ec72339def277c333a |
| Candidati (audit metadati) | reviews/C_REPEATABILITY_METADATA_CLOSURE_20261125/AUDIT/CANDIDATES.csv | 86449cc2cef35ecce94caebb48b3728f8f8f7bf6cdbc9ed310e4a8018ae3aa85 |
| Geometria condivisa | scripts/sft_observed_pilot.py | dec3c4cea56e9c11760751fe050a424c02481d80b53aacc54657d9bcda972ffb |
| Box locale | python/sharpbl/sft_local.py | 4598f0330a044421f4208832b804799400555c0a87792a20fea100109b83a647 |
| Nucleo SFT (legge di rotazione, misure) | python/sharpbl/sft_core.py | 053e622b1acde6540364d850561c3cc55afedab5f1803541965ffaae4538a554 |
| Lettore e WCS (dipendenza dichiarata) | python/sharpbl/geometry.py | 22e329d8257b3193b4b10979a12cf7961ab4011e75d57264a1de7bf42d6637c2 |
| Nomi dei file SHARP | python/sharpbl/download_records.py | eebe22fffe1231d7e0901f989de147e970e20b1cdacf895c88ec1c9de2ecea36 |

SHA aggiornati il 27 novembre dopo le voci del §4 (commit che segue 7411c58). I file FITS da leggere sono quelli nominati dagli header dei record
selezionati; il loro SHA entra nell'INPUT_MANIFEST prima di ogni misura.

## 2. Popolazione (solo metadati, già nota: non cieco)

- 82 coppie in 79 componenti, 214 esclusioni con il loro motivo.
- Emisferi: N 48, S 34. Classi di lag: 39 entro 1,5 h, 43 fra 1,5 e 2 h.
- Terzili USFLUX 28/27/27, con quantile a indice razionale (decisione Codex; conteggi dell'audit 28/26/28 provvisori).

## 3. Implementato e verificato

- **Misura:**
  - impronte G/V con lo stencil effettivo del deposito; C_fin = erode(V0) ∩ V1;
  - bilanciamento sulle celle di C_fin;
  - leading periodico;
  - rimappatura registrata;
  - C_rot come supporto potenziale conservativo dello schema;
  - griglia a 0,03° sulle figlie di C_fin, solo raffinamento esatto 2 × 2.
- **Assemblaggio:**
  - selezione ed esclusioni;
  - gruppi (emisfero, lag, terzile);
  - ogni coppia misurata una volta;
  - `read_error` distinto da `technical_error`;
  - chiavi (pair_key, preparazione) esatte;
  - denominatori;
  - riepiloghi e bootstrap per gruppo, con pesi componente → coppia dopo i mancanti;
  - manifest prima e dopo;
  - `run_valid` secondo §4bis.7.
- **Prodotti** scritti in modo atomico, con META (hash di ogni prodotto, dei candidati, del codice e della specifica,
  git HEAD); la sovrascrittura è rifiutata.
- **Riconteggio indipendente** (codice proprio): ogni chiave di ogni coppia, SUMMARY completo con scale per unità,
  bootstrap, terzili, denominatori, manifest ricalcolato, validità; prodotti riletti dai CSV.
- **Esiti:** selftest del runner 38/38, riconteggio 42/42 (log in `reviews/C_FREEZE_ITEMS_20261127/`), comprese le
  manomissioni rifiutate (riga tolta, denominatore, classe di terzile, media, bootstrap, validità dichiarata, CSV
  cambiato, file in più, terna aggiunta, conteggio per anno, numero di blocchi, gruppo QUALITY, μ). Il primo giro del
  selftest del runner era 37/38: la data di prova del confine CR 1690 era sbagliata di due giorni nel test (25 invece
  di 27 dicembre 1979, JD 2444235,34 = 27 dicembre 20:09,6); corretto il test, non il codice. Log conservato.

## 4. Voci della specifica: stato al 27 novembre (dopo la decisione Codex "completa 1–6 o dichiara i rinvii")

Tutte implementate nel runner e ricontate con codice proprio, salvo il rinvio dichiarato in 5; testo in §4bis.8 della
specifica. Elenco originale conservato sotto.

| Voce | Stato |
|---|---|
| 1 `--run` | gate() con tutti i campi della ricevuta, SHA di specifica, runner, riconteggio e candidati, freeze_commit antenato di HEAD che contiene la specifica, not_blind testuale, albero pulito, runner = HEAD, uscita assente; poi unicità dei file, assemblaggio, prodotti con lo SHA della ricevuta nel META. `--check` reale del riconteggio legato alla stessa ricevuta |
| 2 QUALITY | dagli header (intero o esadecimale), gruppo both0 / not_both0 / missing |
| 3 Terne | prodotto TRIPLES |
| 4 Blocchi 6 CR | prodotto BOOTSTRAP_BLOCKS, seme 36_300_002, CR dalla regola sinodica media |
| 5 Anni | prodotto YEARS; **rinviato** il confronto col bacino del pilota osservativo (bacino non ancora congelato; nota propria, solo metadati) |
| 6 μ | mu_mean_j e mu_offdisk_cells_j in MEASUREMENTS |
| 7 Copie | ogni record deve risolvere a un solo file Br/bitmap/keys sotto `data/sharp/fits` (runner e riconteggio, codice distinto) |

### Elenco originale (prima del 27 novembre pomeriggio)

1. **Entrata reale `--run`.** Lettura dei FITS reali, cartella dei risultati, controllo della ricevuta di congelamento
   (sul modello del gate A1) e scrittura dei prodotti. Oggi è rifiutata.
2. **Sensibilità QUALITY solo 0 (§2.2).** Serve la colonna QUALITY dei record nei candidati, che oggi non c'è.
3. **Terne locali t, t + 1 h, t + 2 h (§6).** Vanno registrate come collegamenti, non come nuove repliche.
4. **Bootstrap a blocchi temporali di 6 CR (§6),** come sensibilità.
5. **Distribuzione per anno e confronto dai metadati con il bacino del pilota osservativo (§6).**
6. **μ medio geometrico dei pixel di C_fin ai due istanti (§6)**, solo descrittivo.
7. **Copie discordanti di un input (§1):** oggi il manifest rileva un file cambiato, non due copie diverse dello
   stesso record.

Proposta di Claude:
- 1 è necessario prima di qualunque corsa osservata;
- 2–6 sono riepiloghi descrittivi, implementabili prima del congelamento senza cambiare misure o regole;
- 7 dipende da come i FITS sono conservati (una copia per record nel layout attuale).

## 5. Semi e casualità

Uso principale dei numeri casuali: il bootstrap per componenti, con seme 36_300_001 riavviato a ogni chiamata, quindi
indipendente dall'ordine di calcolo; 2000 repliche. Nessun altro RNG nella misura.

Secondo uso, solo nella sensibilità: bootstrap a blocchi di 6 CR, seme 36_300_002 riavviato a ogni chiamata.

## 6. Decisioni richieste a Codex

1. Il rinvio della voce 5 (confronto col bacino osservativo) è accettabile nel testo da congelare?
2. Il formato della ricevuta del §4bis.8.7 è quello da usare?
3. Via al congelamento (testo, poi ricevuta in un commit successivo, come per A1)?

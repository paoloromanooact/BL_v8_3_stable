# Ripetibilità C: pacchetto per il congelamento (BOZZA per la revisione Codex)

Claude, 27 novembre 2026. Pilastro: sorgente BL (incertezza osservativa per il confronto SFT/BT). **Non congelato.**
Raccoglie in un documento ciò che si congelerebbe, ciò che è implementato e verificato e ciò che la bozza prevede ma il
codice non fa ancora, perché Codex possa decidere in una lettura. Nessun pixel osservato è stato letto per C.

## 1. Cosa si congela

| Oggetto | Percorso | SHA-256 |
|---|---|---|
| Specifica (rev. 3 + §4bis) | docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md | 95033bfc5676e8ec7b3f63f85c046207dfd4266d489c4d79abbb0dae1e2ac433 |
| Runner | scripts/sft_c_repeatability.py | 6ce0b0c2ec3964085f0405b125de36c1aae8c8e836418edde11e8f9ba09cad4f |
| Selftest del runner | scripts/sft_c_repeatability_selftest.py | 8f425004f608be452ad7aab3d7477999feb39f3f78d37da16b28d205e1a08996 |
| Riconteggio indipendente | scripts/sft_c_repeatability_recount.py | 6ff2c541208b4c3a7187a681f110348f64266337bd06b1dff3d98d9c43cce84d |
| Candidati (audit metadati) | reviews/C_REPEATABILITY_METADATA_CLOSURE_20261125/AUDIT/CANDIDATES.csv | 86449cc2cef35ecce94caebb48b3728f8f8f7bf6cdbc9ed310e4a8018ae3aa85 |
| Geometria condivisa | scripts/sft_observed_pilot.py | dec3c4cea56e9c11760751fe050a424c02481d80b53aacc54657d9bcda972ffb |
| Box locale | python/sharpbl/sft_local.py | 4598f0330a044421f4208832b804799400555c0a87792a20fea100109b83a647 |
| Nucleo SFT (legge di rotazione, misure) | python/sharpbl/sft_core.py | 053e622b1acde6540364d850561c3cc55afedab5f1803541965ffaae4538a554 |
| Lettore e WCS (dipendenza dichiarata) | python/sharpbl/geometry.py | 22e329d8257b3193b4b10979a12cf7961ab4011e75d57264a1de7bf42d6637c2 |
| Nomi dei file SHARP | python/sharpbl/download_records.py | eebe22fffe1231d7e0901f989de147e970e20b1cdacf895c88ec1c9de2ecea36 |

Commit di riferimento del codice: 0b308f3. I file FITS da leggere sono quelli nominati dagli header dei record
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
- **Esiti:** selftest del runner 32/32, riconteggio 35/35, comprese le manomissioni rifiutate (riga tolta,
  denominatore, classe di terzile, media, bootstrap, validità dichiarata, CSV cambiato, file in più).

## 4. Previsto dalla specifica ma NON ancora implementato (decidere: prima del congelamento o rinviato)

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

Un solo uso di numeri casuali: il bootstrap per componenti, con seme 36_300_001 riavviato a ogni chiamata, quindi
indipendente dall'ordine di calcolo; 2000 repliche. Nessun altro RNG nella misura.

## 6. Decisioni richieste a Codex

1. Quali voci del §4 sono richieste prima del congelamento.
2. Conferma delle scelte del §4bis della specifica, già accolte nelle revisioni del 27 novembre.
3. Formato della ricevuta di congelamento di C: proposta sul modello A1, cioè SHA della specifica, del codice e dei
   candidati, commit di congelamento antenato del commit della corsa e dichiarazione testuale di non cecità.

# HMI SFT §7 — fattibilità della ripetibilità dai metadati

25 novembre 2026, Codex. Richiesta dell'utente: svolgere il lavoro sull'incertezza per il successivo confronto
bayesiano, superando la proposta di dichiararla non stimata e rinviarla. Nessuna misura di campo o simulazione.

## Risultato dell'audit

| Controllo | Esito |
|---|---|
| Coppie consecutive entro 2 h dai nomi T_REC | 299 in 296 HARP |
| Coppie consecutive entro 2 h dagli istanti T_OBS in TAI | 296 in 294 HARP |
| Coppie nominali che escono dal limite | 3, tutte con intervallo reale 7201 s |
| Intervallo reale minimo / mediano / massimo | 3600 / 3600,5 / 7200 s |
| Coppie con area geometrica C almeno 25 deg² | 113 |
| Bacino osservativo primario-controllo eleggibile sui tempi reali | 1020 HARP, prima della fattibilità geometrica |
| Riserva escludendo tutto il bacino, famiglie note e possibili intersezioni spazio-temporali | 263 coppie in 261 HARP |
| Riserva con area C almeno 25 deg² | **86 coppie in 84 HARP** |

La riserva esclude cautelativamente il bacino intero invece del solo campione futuro: e una verifica di
**disponibilità**, non una selezione congelata. La verifica finale usa il campione effettivamente conservato e
il grafo di famiglie/sovrapposizioni. Non si presume indipendenza fra coppie della stessa HARP.

Le tre coppie escluse dal controllo T_OBS riguardano HARP 355, 1727 e 6361. Non si allarga a posteriori la
soglia delle due ore. Il bacino del pilota passa da 1023 sui T_REC nominali a 1020 su T_OBS; il campione finale
si definisce e conserva solo secondo il protocollo congelato, non con questo audit.

## Copertura e limiti registrati

- Nessun errore di metadati nelle 299 coppie nominali; dimensioni Br/bitmap coerenti e corrispondenti ai CRPIX.
- 13 record del vecchio caso di prova 2024-05-08 sono senza keys.json: registrati come errori di disponibilità,
  non appartengono alle coppie ravvicinate. La loro presenza non viene silenziosamente ignorata nell'inventario.
- 56 percorsi di segmento duplicati fra collezioni; precedenza esplicita registrata. L'audit non certifica
  l'identità dei pixel duplicati: il manifesto dei file della futura misura dovrà verificarne gli SHA completi.
- Nelle 296 coppie reali, QUALITY è 0 per 284 e 128 per 12 a entrambi gli istanti. Non viene deciso qui un filtro
  di qualità: la specifica deve motivarlo in coerenza con P1/P1b e riportare le perdite.
- Tutte le HARP delle coppie hanno una famiglia P1 nota. Non dimostra che la ricostruzione delle famiglie sia
  completa per tutti i possibili legami fisici.
- Nella riserva geometrica, le 86 coppie sono distribuite: 2010 6; 2011 21; 2012 8; 2013 18; 2014 12; 2015 13;
  2016 6; 2017 1; 2022 1. La rappresentatività dell'intera era HMI non è garantita.
- C è calcolato su impronte WCS da header con celle 0,06°, ramo longitudinale comune, erosione direzionale e
  angolo solido, come nella bozza del pilota. La copertura di **pixel finiti** richiede ancora le mappe.
- Le possibili intersezioni spazio-temporali sono individuate con bounding box delle impronte: controllo
  conservativo di disponibilità, non prova di identità fisica o grafo finale di selezione.

## Che cosa non abbiamo ancora stimato

**Nessuna sigma osservativa è ancora misurata.** I conteggi mostrano che esistono dati per affrontare il
problema, senza leggere gli esiti del pilota. La specifica della misura deve essere congelata prima dei pixel.

Le differenze ravvicinate comprendono evoluzione reale ed errori eventualmente correlati. Non si divide
automaticamente la loro dispersione per sqrt(2), non la si chiama rumore strumentale puro e non la si presenta
come limite superiore garantito. Per il ranking BT occorre anche una componente di discrepanza del trasporto;
per BQ restano dispersione intrinseca dei tilt e dipendenza fra rotazioni. Queste componenti non sono tutte
identificabili dalle sole coppie ravvicinate.

## Prodotti e prossimo passo

- Script indipendente `scripts/sft_hmi_repeatability_metadata_audit.py`, selftest 9/9: tempi TAI frazionari,
  secondi = 60, confine di 2 h, date errate, erosione rettangolare e raccordo longitudinale.
- `reviews/SFT_HMI_REPEATABILITY_METADATA_20261125/`: PAIRS, HEADERS, KEYWORDS (impronte dei keys consumati), META
  e SELFTEST. Solo metadati/header; nessuna colonna di tilt/flusso misurato del catalogo letta, nessun array
  magnetico letto, nessuna rete. Il codice e le dipendenze di libreria usate per la geometria sono dichiarati.
- Bozza della misura: `docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md`. Va completata e rivista incrociatamente, poi
  congelata prima di stimare le differenze sui pixel. La bozza osservativa deve recepire i conteggi e questa
  scelta nel §7 prima del suo congelamento.

Claude continua il punto 2 mappa-bipolo; questo audit del §7 è la consegna di Codex e non va duplicato. Il lavoro
sull'incertezza resta **attivo**, senza richiesta di nuovo consenso per le operazioni Python già autorizzate.

# MDI/SMARP — verifica della fase dei soli conteggi

2026-11-16. Corsa `schema_20261116_http_ac06138`, fase `counts` autorizzata dall'utente dopo la registrazione
della mappa. Eseguita sul commit `e49e994e9103c5fd8c0e9eb7f4e44e0db523fb84`, albero tracciato pulito. Codice scientifico HMI,
protocolli congelati, mappa registrata e regole di prodotto invariati. Nessun elenco di record, export o FITS.

## Esito e portata

**219 richieste rs_summary, tutte riuscite, 219 finestre finali**, nessun blocco oltre 25 000 record,
nessuna suddivisione aggiuntiva. Durata della fase circa 236 secondi; registro cumulativo a
239 tentativi, 125 293 byte di corpi JSON, 350,5 secondi e **zero righe di record acquisite**.
Le cinque interrogazioni schema precedenti e i 15 tentativi HTTPS falliti restano contati; i tre tentativi
della diagnosi separata restano dichiarati a parte, come già stabilito.

| Serie | Somma dei conteggi sulle finestre |
|---|---:|
| `mdi.smarp_cea_96m` | 640 289 |
| `hmi.sharp_cea_720s` | 103 833 |
| `mdi.fd_M_96m_lev182` | 81 240 |

Il totale è **825 362**. Sono conteggi di record di catalogo per serie e intervallo, non HARP/TARP distinte,
regioni fisiche, mappe recuperabili o record che passerebbero il campione S. Le interrogazioni DRMS includono
entrambi gli estremi: un record sul confine può comparire in due conteggi. Il totale è quindi un preventivo
conservativo prima della selezione locale degli intervalli semiaperti e della deduplicazione degli elenchi.
Non sono ancora misurate qualità, classificazione 1/5 minuti, coppie geometriche o disponibilità dei FITS.

## Preventivo secondo il piano congelato

- Sovrapposizione/prima parte: 119 763 righe preventivate, 33 elenchi non vuoti.
- Storico: 705 599 righe preventivate, 179 elenchi non vuoti.
- Tentativi già usati: 239.
- Riserve mantenute: 200 per lookup ausiliari e 200 per ripetizioni/suddivisioni.
- Totale preventivato: **239 + 33 + 179 + 400 = 851**, sotto il tetto 1000.
- Righe preventivate: **825 362**, sotto il tetto 2 000 000.
- Decisione del codice: `full` **per questi vincoli di richieste e righe**.

Questo non autorizza o garantisce l'esecuzione completa. I tetti di 1 GiB e 90 minuti restano invariati;
byte per riga e tempi vanno misurati sui primi elenchi e proiettati prima dello storico. Il prossimo passo
separato è `overlap`, limitato ai metadati. Nessun elenco avviato in questo passaggio.

## Controllo indipendente

Verifica senza importare il raccoglitore: hash di tutti i corpi JSON; HTTP/DRMS e conteggi interi non negativi;
confronto di ogni foglia con la risposta originale; partizione degli intervalli per profilo, senza buchi o
sovrapposizioni interne dei confini semiaperti; ricostruzione delle somme e del numero di elenchi; ricostruzione
del preventivo e della decisione; provenienza e hash di piano/codice/configurazione; registro chiuso e zero
righe o file di elenchi. Tutte le asserzioni sono superate.

Il verificatore è specifico di questa corsa e della sua provenienza. È stato scritto durante la fase dei
conteggi, dopo aver osservato il primo conteggio e prima della lettura del riepilogo finale; non introduce
soglie o decisioni nuove. Copia e ricevuta locali: `COUNTS_CHECK.py` e `COUNTS_CHECK.json` nella cartella della
corsa, rispettivamente SHA-256 `3d76d49969282bb21dc36f61b572510237b69a3e066f450193732913c0cd33b6` e
`dda26102c1dc776e5e7538e0be4f64ec07200a3fa28c868abd9f2df4554a94b1`. Le risposte originali non sono state modificate.

Artefatti locali della fase:

- `PHASE_counts_002.json`: `8c11cec96fd939558dbea3d144e203919c96908079ec391fb8b636109c653f5e`
- `COUNT_LEAVES.csv`: `ce36555a71512e4a5996efde82e5b9cb7c9ca3ae4c30743b71e46b573da1da53`
- `BUDGET_COUNTS.json`: `c2141dd41959088a8a4a1136b02a2d34cc37296e1e2a4c1000313fb0d3a9c0d1`

Nessun push. Piano prospettico, download MDI e morfologia S restano non avviati/in pausa.

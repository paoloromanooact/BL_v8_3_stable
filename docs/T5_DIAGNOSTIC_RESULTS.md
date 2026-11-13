# T5-D1 — diagnosi dagli output sintetici salvati: risultati

**2026-11-13. Diagnostico e non cieco; nessun nuovo risultato sul quenching reale.**
La procedura M per T5 resta non validata. La diagnosi identifica uno scarto
nella calibrazione complessiva con i salti di 20 CR; la sua attribuzione alle
componenti individuale e temporale resta aperta.

## 1. Provenienza, ordine e controlli

| Passo | Registrazione |
|---|---|
| Piano congelato prima del codice | `85df0e9`, [T5-D1](PROTOCOL_T5_DIAGNOSTIC_SAVED_OUTPUTS.md), SHA-256 `53a05c1fd7c0315eca52b508472c59d6df485c29c8ef2b717e81264d3d600e5d` |
| Codice prima dell'analisi | `3c7359590c3cba91e3c75f5f47532d77c2123c8c`, `python/sharpbl/diag_t5_saved_outputs.py` |
| Esecuzione unica | 2026-11-13 10:16:26–10:16:35 UTC, commit `3c73595`, albero tracciato pulito |
| Output conservati prima dell'interpretazione | `dcc7219`, `results/T5_DIAGNOSTIC/` e `figures/T5_DIAGNOSTIC/` |
| Input | [lista con otto hash e blob Git](T5_DIAGNOSTIC_INPUTS_SHA256.csv); output P2f provenienti da `5c3b664` e controlli con provenienza propria |
| Ambiente | Python 3.10.12; numpy 2.2.6, pandas 2.3.3, scipy 1.15.3, matplotlib 3.8.4 |

**201 controlli su 201 superati**, incluse le 26 prove su tabelle costruite
a mano, ripetute sul commit pulito prima degli input. Le prove sono state
eseguite anche con `--selftest` sullo stesso commit. Controllati hash/blob,
provenienze distinte, chiavi esatte, finitezza, semi-intervalli separati,
verdetti/code, denominatori e riassunti P2f. I momenti sono stati verificati
anche con aritmetica Python separata dalle riduzioni numpy del riepilogo.
Non è una revisione esterna indipendente: codice e controlli hanno lo stesso autore.

Il raw completo ha 304000 righe; il campione previsto ha **74000 righe T5**
in 17 gruppi, comprese **42 righe errore**. Nessuna eliminazione o sostituzione.
Gli hash dei cinque CSV e delle tre figure sono in `T5D_META.json` e sono
stati ricontrollati dopo la scrittura. Nessun errore di esecuzione o rilancio.
Gli output originali, i moduli scientifici e il protocollo P2f sono invariati.

Comandi dalla radice, prima del commit degli output:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python python/sharpbl/diag_t5_saved_outputs.py --selftest
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/bl-t5-mpl .venv/bin/python python/sharpbl/diag_t5_saved_outputs.py --run
```

Lo script rifiuta directory di output già esistenti. Una riproduzione futura
richiede una copia separata pulita con il codice scientifico identico e
provenienza della riproduzione distinta; non rimuovere gli artefatti originali.

## 2. Definizioni e denominatori

η₀ = 3,56·10⁻²⁵ G/Mx; r = (β̂−β_vero)/η₀, s = SE/η₀,
z = r/s, u = (r−media r)/deviazione standard empirica di r.
**R = media(s²)/varianza empirica di r**. R riguarda la varianza complessiva
della pendenza, non una singola componente e non direttamente il valore di SE.

Bias e momenti sono condizionati agli esiti numerici validi. Le frequenze di
copertura, code e falsi verdetti mantengono tutti i tentativi nel denominatore.
Gli errori sono non copertura sotto effetto e non sono falsi verdetti sotto
nulla, come nel protocollo originale. Le barre sul bias sono un errore Monte
Carlo della media simulata, non un intervallo sul processo solare reale.

Coda inferiore = `below`: β_vero < lo, ossia z > q; coda superiore = `above`:
β_vero > hi, ossia z < −q, con q = Φ⁻¹(0,9875). La statistica salvata β̂/SE
è stata controllata ma non usata come z sotto effetto.

## 3. Scala e bias: tutti i gruppi previsti

Sotto nulla, N = 10000 per riga. Bias ± errore Monte Carlo in unità η₀;
le ultime due colonne riportano frequenze sui tentativi.

| Scenario | Errori | Bias ± MC | R | SD(z) | Falsi verdetti | Coda inferiore / superiore (%) |
|---|---|---|---|---|---|---|
| 0 | 3 | 0,00129 ± 0,00057 | 1,1297 | 0,9448 | 181 / 10000 (1,81%) | 0,94 / 0,87 |
| 1 | 8 | 0,00097 ± 0,00102 | 1,0299 | 0,9978 | 256 / 10000 (2,56%) | 1,25 / 1,31 |
| 2 | 4 | -0,00122 ± 0,00131 | 0,9863 | 1,0228 | 285 / 10000 (2,85%) | 1,40 / 1,45 |
| 7 | 4 | 0,00237 ± 0,00142 | 0,8580 | 1,0944 | 335 / 10000 (3,35%) | 1,75 / 1,60 |
| 10 | 8 | 0,00346 ± 0,00144 | 0,9165 | 1,0565 | 195 / 10000 (1,95%) | 0,92 / 1,03 |

Sotto effetto, N = 2000 per riga; effetto in unità η₀ e copertura in percentuale.

| Scenario | Effetto | Errori | Bias ± MC | R | SD(z) | Copertura (%) | Coda inferiore / superiore (%) |
|---|---|---|---|---|---|---|---|
| 1 | -0,10 | 0 | -0,00083 ± 0,00230 | 1,0113 | 1,0038 | 97,60 | 1,40 / 1,00 |
| 1 | -0,20 | 0 | 0,00142 ± 0,00236 | 0,9651 | 1,0272 | 97,20 | 1,40 / 1,40 |
| 1 | -0,30 | 0 | -0,00482 ± 0,00233 | 0,9913 | 1,0166 | 97,50 | 1,30 / 1,20 |
| 1 | -0,35 | 2 | 0,00247 ± 0,00228 | 1,0365 | 0,9953 | 97,05 | 1,60 / 1,25 |
| 2 | -0,10 | 2 | 0,00052 ± 0,00292 | 1,0147 | 1,0073 | 96,90 | 1,35 / 1,65 |
| 2 | -0,20 | 2 | -0,00367 ± 0,00291 | 1,0145 | 1,0052 | 96,90 | 1,30 / 1,70 |
| 2 | -0,30 | 2 | -0,00365 ± 0,00291 | 0,9983 | 1,0200 | 97,00 | 1,35 / 1,55 |
| 2 | -0,35 | 1 | 0,00085 ± 0,00296 | 0,9678 | 1,0317 | 96,95 | 1,25 / 1,75 |
| 7 | -0,10 | 2 | -0,00154 ± 0,00313 | 0,8817 | 1,0750 | 97,00 | 1,45 / 1,45 |
| 7 | -0,20 | 1 | 0,00007 ± 0,00315 | 0,8706 | 1,0897 | 96,75 | 1,20 / 2,00 |
| 7 | -0,30 | 3 | 0,00007 ± 0,00316 | 0,8591 | 1,0981 | 96,10 | 2,30 / 1,45 |
| 7 | -0,35 | 0 | 0,00146 ± 0,00318 | 0,8519 | 1,0968 | 96,60 | 1,80 / 1,60 |

Nel caso 7 sotto nulla, R = 0,858: la media di SE² è circa il **14,2% più
piccola** della varianza empirica di β̂. Non significa che SE sia più
piccolo del 14,2%, né che la varianza temporale sia sottostimata di quella
quota. Il bias è 0,00237·η₀ con errore MC 0,00142·η₀, piccolo rispetto alla
dispersione delle pendenze; non è una prova di bias esattamente nullo.

La stessa carenza di scala si presenta nei quattro gruppi sotto effetto
con salti (R 0,852–0,882). Nei controlli AR(1), R è vicino a uno:
0,986–1,030 sotto nulla e 0,965–1,037 sotto effetto. Questo è un indizio
ripetuto entro il disegno sintetico, non una validazione di un fattore
correttivo. Alcuni piccoli bias nei controlli superano due errori MC:
le analisi sono molteplici e non si trasformano in verdetti confermativi.

## 4. La scala da sola non descrive le code

Quantili all'1,25% e al 98,75% sotto nulla; riferimenti normali −2,2414 e +2,2414:

| Scenario | Quantili di z | Quantili di u |
|---|---|---|
| 0 | -2,1042; 2,1596 | -2,2425; 2,2434 |
| 1 | -2,2579; 2,2353 | -2,2085; 2,2275 |
| 2 | -2,3067; 2,2907 | -2,2253; 2,2288 |
| 7 | -2,3276; 2,3900 | -2,1090; 2,1379 |
| 10 | -2,1593; 2,1603 | -2,0405; 1,9888 |

Con i salti di 20 CR, z ha dispersione e code più ampie dei riferimenti,
mentre u, centrato e scalato con la dispersione empirica, ha quantili delle
code meno estremi del riferimento. Questo distingue la forma marginale
dell'errore da quella del rapporto errore/SE; non prova normalità, né basta
per attribuire la differenza a una sola stima di parametro.

Lo scenario 10 è il controesempio utile: R = 0,9165 e SD(z) = 1,0565, ma
solo 1,95% di falsi verdetti e quantili di u ancora meno estremi. **R<1
non implica da solo eccesso di falsi verdetti.** I salti sono di 13 CR e
condivisi fra emisferi, anziché 20 CR separati: il confronto non identifica
quale differenza sia responsabile. I quantili di tutti i gruppi, compresi
gli effetti, sono in `T5D_QUANTILES.csv`; le figure mostrano solo il tratto
0,5–99,5%, senza descrivere le code oltre quel tratto.

## 5. Dipendenza da SE e parametri stimati

Nel caso 7 sotto nulla, il quintile con SE più piccolo ha frequenze
z>q = 3,10% e z<−q = 2,85%; nel quintile più alto sono 0,55% e 0,90%.
I denominatori sono rispettivamente 2000 e 1999 esiti validi. Un andamento
simile compare anche nel controllo AR(1) scenario 1: 1,95%/2,10% nel primo
quintile e 0,60%/0,75% nell'ultimo. Non è quindi una proprietà esclusiva dei
salti. La correlazione di Spearman fra |r| e SE nello scenario 7 è solo
0,077 sotto nulla. Le tabelle per quintile non sono una prova causale:
SE compare già nel denominatore della statistica e le partizioni sono condizionate.

Nel caso 7, le mediane sono φ̂ = 0,947 e σ̂_x²/η₀² = 0,310 sotto nulla;
sono simili sotto effetto. Non c'è un «φ vero AR(1)» per questo processo.
Questi parametri non misurano direttamente la varianza temporale della
pendenza: non basta cercare un'ampiezza latente piccola per spiegare R.
La pendenza della funzione di varianza individuale è vicina a zero nello
scenario 7 (mediane fra −0,0017 e circa zero), ma ciò non valida il suo
contributo complessivo alla varianza di β̂.

Nel caso 0 senza componente temporale, il 5,53% degli esiti validi ha la
stima di ampiezza al bordo inferiore e R è 1,130; il comportamento è
conservativo sotto nulla (1,81% di falsi verdetti). Nel caso 10 la mediana
κ̂ è al limite superiore 0,98. Non si modificano stime o criteri dopo averli
osservati. Tutte le statistiche dei parametri, avvii validi e residui nulli
sono in `T5D_NUISANCE.csv`.

## 6. Conclusione secondo le regole registrate

- **Scala insufficiente nello scenario 7:** coerente con R inferiore a uno
  e dispersione di z maggiore di uno, sotto nulla e agli effetti provati.
- **Bias dominante:** non emerge come spiegazione principale nello scenario
  7; bias piccoli rispetto alla dispersione non dimostrano assenza di bias.
- **Sola normalità della pendenza:** non accertata. Forma marginale e stima
  di SE vanno distinte; scenario 10 mostra che la scala non basta.
- **Componente responsabile:** non identificata. Questi dati non separano
  contributi individuale/temporale veri né l'effetto delle loro stime.

Il prossimo controllo motivato è un confronto, pianificato separatamente,
con covarianza temporale del generatore e varianza individuale note, sullo
stesso disegno sintetico. I bracci dovrebbero distinguere le sostituzioni
singole e congiunte, dichiarando se e come si ristimano gli altri parametri.
Se anche con varianza vera l'intervallo normale fallisse, servirebbe distinguere
la forma della distribuzione con il generatore completo, non attribuire
automaticamente il problema a una componente.

**Arresto di T5-D1:** i prodotti previsti sono completati. Nessun nuovo
controllo oracolo, fit, ricampionamento o correzione di M eseguito. T5 resta
descrittivo; nessuna applicazione ai dati reali, nessuna modifica a T3.
Prima di ulteriori calcoli serve il piano successivo; gli output P2f restano
materiale di sviluppo e non saranno validazione indipendente di un metodo nuovo.

Figure: [bias e scala](../figures/T5_DIAGNOSTIC/t5d_bias_scale.png),
[quantili](../figures/T5_DIAGNOSTIC/t5d_quantiles.png),
[quintili di SE](../figures/T5_DIAGNOSTIC/t5d_se_tails.png).

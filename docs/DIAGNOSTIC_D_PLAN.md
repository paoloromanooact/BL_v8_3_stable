# Piano del controllo diagnostico D — livello di C1 su cataloghi nuovi

Stato: **registrato il 2026-11-09 prima di scrivere ed eseguire il codice di D.**
**Sviluppo diagnostico**, non validazione di un eventuale P2f e non verdetto: non cambia
alcun risultato, conteggio storico o decisione di P2/P2d/P2e. Contesto:
`docs/DIAGNOSTIC_C_RESULTS.md` (C1 in V1 e V4: 3,0–3,15% invece del 2,5%) e
`docs/DIAGNOSTIC_C1_AUDIT.md` (decisioni Monte Carlo e analitiche concordi; V1–V4
condividono una sola realizzazione; tutti gli scenari condividono il disegno). Lo script
registrerà nei propri output il commit e lo SHA-256 di questo file.

## 1. Domanda

Sotto il modello nullo del generatore, con cataloghi **nuovi e indipendenti** (semi mai usati,
distinti per scenario), la frequenza di falsi verdetti della decisione al livello nominale
del 2,5% è compatibile con il 2,5%? Serve a stabilire se lo scostamento di C1 è una proprietà
dei 2000 cataloghi di sviluppo (realizzazione condivisa) o della struttura (generatore,
rappresentazione, decisione).

## 2. Materiale

- **Scenari:** V1 e V4 (quelli di C1; principali) e V0, V2, V3 (secondari, stesso modello
  AR(1) o nessuna componente). V5 e V6 sono esclusi: il loro modello vero non è quello di
  C1 (V5 con covarianza approssimata in A).
- **Numerosità:** N = 10 000 cataloghi per scenario, test T3 e T5 (100 000 coppie catalogo ×
  test in tutto). Errore binomiale per scenario e test a 2,5%: circa 0,16 punti; uno
  scostamento di 0,5 punti (come in C1) corrisponde a circa 3 errori.
- **Semi nuovi, distinti per scenario e mai usati:** catalogo 1 000 000 + 100 000·s + k, con
  s = 0, 1, 2, 3, 4 per V0, V1, V2, V3, V4 e k = 0…9999. Nessuna sovrapposizione con i semi
  già usati (30000 + k, 40000 + k, 50000 + 2k, 60000 + 2k, 70000 + k, 100000 + k,
  140000 + k, 260000 + 2k, 360000 + 2k, 2026110x). Con semi diversi per scenario, cambiano
  anche il disegno e il rumore: gli scenari sono indipendenti tra loro.
- **Codice esistente invariato:** generatore (`p2d.synthetic_catalog_p2d`), selezione
  (`run_p2.samples`, `add_activity`), disegno (`p2d.design_t3`, `design_t5`), stima lineare e
  varianza vera come in A (`diag_a_variance`: a_i, b, K vera, V_true, μ).

## 3. Decisione

**Analitica** sotto il modello del generatore: falso verdetto se
|β̂ − μ| / √V_true > z_0,0125 (soglia normale a precisione completa), con β̂ calcolato dai
dati del catalogo (compresa la trasformazione γ → sin γ → γ di T3). È giustificata dalla
concordanza con la decisione Monte Carlo di C1 sui cataloghi di sviluppo (1996–1999 su 2000)
e verificata di nuovo qui su un campione (§5, controllo 4).

## 4. Criteri e interpretazioni (fissati prima dell'esecuzione)

Frequenza di falsi verdetti f (entrambi i versi); errore binomiale per scenario e test
(cataloghi indipendenti); per le sintesi che uniscono T3 e T5 (stesso catalogo) errore
**raggruppato per catalogo**.

- **Criterio principale (D1)**, su V1 e V4 insieme, T3 e T5 insieme (40 000 indicatori su
  20 000 cataloghi): se |f − 2,5%| ≤ 2 errori, il livello è **compatibile con il 2,5%** sui
  cataloghi nuovi, e lo scostamento di C1 è coerente con una proprietà della realizzazione
  di sviluppo. Se f − 2,5% > 2 errori, l'eccesso è **confermato** su cataloghi nuovi ed è
  strutturale entro questo modello. Se 2,5% − f > 2 errori, il livello è **sotto** il
  nominale (riportato come tale).
- **Secondario (D2)**, stesso criterio su V0–V4 insieme (100 000 indicatori su 50 000
  cataloghi).
- **Per scenario e test (D3, descrittivo):** f con errore binomiale e var(z) con errore
  √(2/(N − 1)) ≈ 0,014. Con 10 celle ci si aspetta per caso circa mezza cella oltre 2 errori:
  nessuna conclusione da una cella sola.
- **D4.** In ogni caso il risultato riguarda il modello nullo del generatore e la decisione
  analitica; non valida P2f e non dimostra il livello di una procedura con parametri stimati.

## 5. Controlli obbligatori

1. **Codice invariato:** sul catalogo di sviluppo k = 0 (semi 40000) di V1 e V4, β̂, μ e
   V_true coincidono con quelli di `A_BY_CATALOGUE.csv.gz` (scarto relativo ≤ 10⁻⁹).
2. **Finitezza:** β̂, μ, V_true finiti e V_true > 0 in ogni catalogo; |μ| ≤ 10⁻⁶ √V_true.
3. **Semi:** nessun seme usato coincide con quelli elencati in §2 (controllo nel codice).
4. **Decisione Monte Carlo su campione:** sui primi 100 cataloghi nuovi di V1 e V4 (400 casi)
   si esegue anche la simulazione C1 (M = 20 000, semi interni 1 900 000 + 2k + t, nuovi),
   con simulazioni tutte finite; le decisioni Monte Carlo e analitiche coincidono salvo casi
   con ||z| − z_0,0125| < 0,05.

## 6. Regola di arresto

- Se un controllo obbligatorio fallisce, D si ferma, lo si riporta e non si interpreta;
  eventuali correzioni del codice richiedono un emendamento registrato prima di rieseguire.
- **Una sola esecuzione:** dopo aver visto i risultati non si cambiano N, semi, scenari o
  criteri, e non si ripete D per ottenere un esito diverso.
- **Dopo D1:** se il livello è compatibile, la diagnosi di C1 si chiude e si passa alla
  progettazione di P2f (punto 5). Se l'eccesso è confermato, la prossima indagine (struttura
  del generatore, della rappresentazione o della decisione) richiede un piano proprio; P2f
  resta sospeso fino ad allora.

## 7. Costo

Analitico: circa 1 s di CPU per catalogo, 50 000 cataloghi, circa 70 minuti su 12 processi;
campione Monte Carlo (400 casi): pochi minuti.

## 8. Output

`results/DIAGNOSTIC/D_BY_CATALOGUE.csv.gz`, `D_SUMMARY.csv` (per scenario e test),
`D_CRITERIA.csv` (D1, D2), `D_CHECKS.csv`; script `python/sharpbl/diag_d_new_seeds.py`;
risultati in `docs/DIAGNOSTIC_D_RESULTS.md`.

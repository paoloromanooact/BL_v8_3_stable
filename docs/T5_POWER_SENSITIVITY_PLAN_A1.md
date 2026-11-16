# Emendamento A1 al piano di sensibilità della potenza T5

Stato: **registrato il 2026-11-16 dopo la revisione di Codex del piano congelato (`4b67632`, SHA-256
`fac76b1a…`) e prima di qualunque codice o calcolo.** Il piano resta agli atti e invariato. A1 chiude
due ambiguità operative; non cambia la griglia, i segnali, i rumori, i metodi né la lettura.

## 1. Tolleranze, identità e casi di confine (sostituisce le formulazioni di §3a, §5.1 e §6.2)

**Una sola regola per le identità L/S**, valida ovunque il piano le richieda (invarianti di §3a, lettura
di §5.1, controlli di §6.2 e verifiche durante l'esecuzione):
- β̂_WLS(L) e β̂_WLS(S) appaiati devono coincidere entro τ_β = 10⁻¹²·|Δβ| + 10⁻³⁸ G/Mx
  (circa 2,83·10⁻³⁸ G/Mx per L1/S1 e 4,67·10⁻³⁸ per L2/S2). Per O anche gli SE devono coincidere entro
  10⁻¹² in senso relativo.
- I verdetti di O si **conservano entrambi come calcolati**; nessuna riclassificazione. Una differenza
  di verdetto di O fra L e S appaiati è un **caso di confine** se l'estremo che decide il verdetto (hi
  per `supportato`, lo per `opposto`) dista da zero, in almeno uno dei due, non più di
  τ_v = τ_β + Z·|SE_L − SE_S|. I casi di confine si registrano separatamente con i valori.
- Qualunque differenza fuori da queste tolleranze (β̂, SE, o un verdetto diverso che non è un caso di
  confine) è un **errore tecnico** (§6 del piano: esecuzione «non riuscita»).
- Se i controlli con rumore falliscono, **le tolleranze non si allargano** dopo aver visto gli esiti.

**«Esattamente» nelle ricostruzioni numeriche** (§3a, §6.2) significa entro una tolleranza esplicita
dimensionata, non uguaglianza bit per bit: arrotondamenti di circa 10⁻⁴⁰ G/Mx compaiono già nella
costruzione senza rumore.
- Grandezze in G/Mx al livello di cella (η_c ricostruita, medie aggiunte): |a − b| ≤ 10⁻¹²·η̄
  (3,56·10⁻³⁷ G/Mx).
- Pendenze in G/Mx: τ_β come sopra.
- Grandezze adimensionali (e_L, g·Δη/η̄): |a − b| ≤ 10⁻¹².
- **Vietati `np.allclose` e `np.isclose` con le tolleranze predefinite** (atol = 10⁻⁸ accetterebbe
  differenze di 17 ordini di grandezza su queste scale): ogni confronto dichiara rtol e atol.
- I CSV si leggono a precisione completa (`float_precision="round_trip"`).

## 2. Benchmark della durata (precisa §3e e §6.7)

- **Unità di lavoro**, uguale nel benchmark e nell'esecuzione: un catalogo di rumore di base (n, k) con
  tutti e cinque i segnali e tutti e quattro i metodi (M, G, B, O); l'appaiamento L/S si verifica dentro
  l'unità.
- **Cataloghi del benchmark**: 4 per ciascuna delle 9 configurazioni di rumore, 36 unità, semi
  33 000 000 + (4·n + r), r = 0…3 (33 000 000–33 000 035); bootstrap di B con semi 33 100 000 + (4·n + r).
  Sono fuori griglia; i loro verdetti non si riportano né si usano per alcuna lettura.
- **Esecuzione rappresentativa**: stesso pool di 12 processi, `OMP_NUM_THREADS=1`, stessa funzione di
  lavoro e stessa distribuzione dei compiti dell'esecuzione vera. Ogni processo misura il tempo di parete
  di ciascuna unità mentre gli altri lavorano, così la misura include la contesa fra processi.
- **Previsione**: T_prev = Σ_n t̄_n · 1000 / 12, con t̄_n la media dei tempi delle 4 unità della
  configurazione n misurati sotto carico. Si riportano anche il tempo di parete del benchmark e t̄_n per
  configurazione.
- **Arresto**: se T_prev > 8 h, ci si ferma prima della griglia e si riporta; nessuna riduzione della
  griglia senza emendamento. Il limite è un budget operativo sulla durata prevista, non una garanzia sul
  tempo effettivo.
- **Semi dei selftest** (§6.2–6.5), distinti dal benchmark: 33 000 050–33 000 099, bootstrap di B
  33 100 050–33 100 099.

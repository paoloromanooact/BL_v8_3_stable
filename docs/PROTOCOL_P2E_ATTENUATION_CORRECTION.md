# Protocollo P2e — Stima dei parametri temporali corretta per rumore e media stimata (emendamento di P2d)

Stato: **congelato il 2026-11-03** (commit), prima della validazione esterna
di P2d e di qualunque esecuzione di P2 sui dati reali. Sostituisce **solo**
la stima dei parametri di P2d §3 e la componente individuale simulata di P2d
§1–§2; P2d (SHA-256 `7caeee60…`) resta agli atti e tutto il resto (modello,
decisione, validazione, accettazione con limite 4%, ripiego) resta invariato,
salvo i semi di §5.

## 0. Perché, e cosa è già stato visto (sviluppo del metodo, non cieco)

Una prova di tempistica (un catalogo sintetico V2, φ vero 0,8) ha dato
φ̂ = 0,52 (T3) e 0,37 (T5): un **segnale diagnostico**, compatibile con
l'attenuazione da errore di misura, non una stima del bias medio. Poi, come
**sviluppo del metodo**, su cataloghi sintetici con semi 70000 + k (distinti
da quelli di validazione), senza alcun test di decisione:
- 40 cataloghi per V0, V2, V3: φ̂ medio P2d 0,47 / P2e-iniziale 0,64 (vero
  0,8); κ̂ medio in V3 0,21 / 0,33 (vero 0,6) (`results/P2/P2E_DEVELOPMENT_ESTIMATORS.csv`);
- 20 cataloghi V2, T3: la varianza di campionamento delle celle stimata come
  in P2d è il 69,5% di quella vera (pesi disuguali, circa 7,8 regioni
  effettive per cella); con la correzione per la leva (§1) l'88%;
- la stima della media del modello nullo (un'intercetta per ciclo ed
  emisfero) riduce c0 e c1 di circa σ²(1+φ)/((1−φ)n);
- 40 cataloghi V2, T3, con entrambe le correzioni (§1–§2): φ̂ medio 0,74
  (mediana 0,74, sd 0,07), σ̂² medio 60 (vero 56,25). Resta una distorsione
  verso il basso di circa 0,06, che la validazione completa valuterà.

## 1. Modello di osservazione e ipotesi

Per ogni cella (t, h) con t numero di CR e h emisfero:
u_{t,h} = x_{t,h} + ε_{t,h},
dove x è la componente temporale latente (AR(1) bivariato di P2d §3) ed ε è
il rumore di campionamento della media di cella. **Ipotesi:** ε indipendente
nel tempo, **indipendente tra emisferi** (le due celle della stessa CR
contengono regioni diverse) e indipendente da x, con varianza v_{t,h}. Negli
scenari di validazione il rumore individuale è indipendente tra regioni,
quindi anche tra emisferi: l'ipotesi è inclusa nella validazione così com'è.

**Varianza di campionamento con correzione per la leva.** Con w_i i pesi
dell'unità (Φ_i), W = Σ_{cella} w_i, leva h_i = w_i / W, e_i = r_i − u_{t,h}:
v_{t,h} = Σ_{cella} w_i² e_i² / (1 − h_i) / W², con 1 − h_i limitato
inferiormente a 0,05.

**Componente individuale simulata** (sostituisce e_i v_i di P2d §1–§2):
e_i v_i / √(1 − h_i), con lo stesso limite (residui corretti per la leva nel
wild bootstrap).

## 2. Stima dei parametri

Su tutte le celle con dati, **pesi uguali per cella**, centratura sulla
media delle celle ū; coppie solo tra CR **realmente consecutive** (t e t − 1
entrambe presenti nello stesso emisfero; i vuoti non si comprimono).
- ĉ0 = media_celle (u − ū)² − media_celle v;
- ĉ1 = media_coppie (u_t − ū)(u_{t−1} − ū);
- **correzione per la media stimata:** n̄ = (numero di celle con dati) /
  (numero di gruppi ciclo × emisfero con dati), B(φ) = (1 + φ) / ((1 − φ) n̄);
  φ̂ è la soluzione in [0; 0,95] di (φ − B(φ)) / (1 − B(φ)) = ĉ1 / ĉ0
  (metodo di Brent); se l'equazione non ha soluzione nell'intervallo,
  φ̂ = 0 se il primo membro supera il secondo già in 0, altrimenti 0,95, e si
  registra `phi_at_boundary`;
- σ̂_u² = ĉ0 / (1 − B(φ̂)); se ĉ0 ≤ 0: σ̂_u² = 0 (`sigma_u_at_boundary`),
  componente temporale assente nella simulazione, φ̂ e κ̂ non usati;
- innovazioni a_{t,h} = (u_{t,h} − ū) − φ̂ (u_{t−1,h} − ū) sulle CR t con N e
  S presenti in t e t − 1;
  ŝ²_{w,h} = media_t a_{t,h}² − media_t (v_{t,h} + φ̂² v_{t−1,h}) (varianza
  latente delle innovazioni, tolto il rumore);
  κ̂ = media_t a_{t,N} a_{t,S} / √(ŝ²_{w,N} ŝ²_{w,S}). Per l'ipotesi di
  indipendenza tra emisferi di ε, il numeratore non ha termine di rumore. Se
  un ŝ²_{w,h} ≤ 0 (con ĉ0 > 0), κ non è stimabile: ripiego descrittivo come in
  P2d §3. Vincolo κ̂ ∈ [−0,95; 0,95], bordo registrato.
- Si registrano sempre i valori **prima dei vincoli** (ĉ0, ĉ1, rapporto,
  φ grezzo, κ grezzo, ŝ²_{w,h}), i valori troncati e i ripieghi.
- Le condizioni di non applicabilità di P2d §3 (meno di 30 CR, meno di 20
  coppie per φ, meno di 20 CR per κ) restano.

**Effetto della stima della media.** I residui dopo il fit non sono errori
indipendenti; la correzione B(φ) è un'approssimazione al primo ordine per un
AR(1) con media stimata su segmenti di lunghezza n̄. La sua adeguatezza, con
tutte le altre approssimazioni, è valutata dalla validazione completa di P2d
§5, eseguita con questo stimatore.

## 3. Simulazione

Come in P2d §1–§3 con i parametri di §2 e la componente individuale di §1.

## 4. Validazione

Come in P2d §5–§6 (scenari, 2000 cataloghi esterni per scenario, M = 20 000,
limite di accettazione 4%, separata per T3 e T5, ripiego), con la procedura
completa di P2e ristimata in ogni catalogo esterno. Si riportano anche, per
scenario, media e dispersione di φ̂, σ̂_u² e κ̂ rispetto ai valori veri.

## 5. Semi nuovi

Validazione: cataloghi esterni 40000 + k; calibrazione interna 60000 + 2k (T3)
e 60001 + 2k (T5); potenza 140000 + k. Dati reali: 20261111 (T3), 20261112 (T5).

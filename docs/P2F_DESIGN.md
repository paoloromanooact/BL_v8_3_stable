# Progettazione di P2f (documento di lavoro, **non** protocollo)

Data: 2026-11-11. Documento di progettazione da discutere: **non è congelato** e non contiene
regole di decisione in vigore. Il protocollo P2f, se si farà, sarà un file separato
(`docs/PROTOCOL_P2F_*.md`), congelato prima di qualunque validazione o applicazione ai dati.
Le correzioni discusse qui **non sono validate**.

## 0. Cecità: che cosa è già noto

P2f sarà **dichiaratamente non cieco**. Prima di scriverlo sono noti:
- i risultati di P2, P2b, P2d ed P2e sui dati reali (`docs/P2_RESULTS_DESCRIPTIVE.md`):
  - stime e intervalli di T1–T5;
  - parametri temporali stimati: T3 φ̂ = 0,53, κ̂ = −0,85, σ̂_u² = 56,2; T5 φ̂ = 0,91, non
    applicabile per ŝ²_w,S < 0;
- la validazione P2e e la diagnosi A–D (`docs/DIAGNOSTIC_*.md`). I cataloghi e i semi di
  P2d/P2e (30000 + k, 40000 + k e semi interni) e quelli di D (1 000 000 + …) sono
  **materiale di sviluppo**.

## 1. Obiettivo

Una procedura per T3 (pendenza del tilt rispetto all'attività) e T5 (efficienza rispetto
all'attività) che controlli la frequenza di falsi verdetti in un insieme di forme di
dipendenza temporale fissato prima, verificata con una validazione indipendente **prima**
dell'applicazione ai dati. Esito ammesso, e da dichiarare: **nessuna procedura adeguata**. In
quel caso T3 e T5 restano descrittivi.

## 2. Requisiti dalla diagnosi

| | Requisito | Origine |
|---|---|---|
| (a) | stima dei parametri temporali meno distorta, o procedura che non ne dipenda | A, B: φ̂ e κ̂ sottostimati spiegano gran parte dell'eccesso in V2–V3 |
| (b) | componente individuale gestita in modo utilizzabile sui dati reali, incluse le celle con una sola regione | C: correzione per la leva insufficiente; residuo nullo nelle celle singole; il termine oracolo non è applicabile |
| (c) | validazione con semi nuovi **distinti per scenario**, criteri e regola di arresto fissati prima | audit di C1, D |
| (d) | robustezza a dipendenze diverse dall'AR(1), almeno AR(2) e salti di livello | V5, V6: 5–10% di falsi verdetti con P2e |

**Requisito aggiuntivo proposto (e): realismo del disegno di validazione.** I cataloghi
sintetici di P2d/P2e hanno 6000 regioni, di cui circa 5760 entrano nel campione di T3, contro
**2485** regioni reali su 210 CR (T5: 318 celle). Il disegno sintetico ha inoltre tempi
uniformi e latitudini da una legge semplice. La calibrazione su un disegno 2,3 volte più grande
e diverso potrebbe non trasferirsi ai dati reali. Proposta: validare sul **disegno reale**
(tempi, CR, emisferi, latitudini, Φ, attività del campione S, come già fatto in T0),
sostituendo solo le risposte γ_i e z_i con risposte sintetiche sotto la nulla.

**Scenari che mancano rispetto ai dati reali (proposta).** κ negativo (T3 reale κ̂ = −0,85;
gli scenari avevano solo κ = 0 o +0,6), φ vicino a 0,9 (T5 reale 0,91), code più pesanti
della normale nel rumore individuale.

## 3. Alternative

### 3.1 Componente temporale, requisiti (a) e (d)

| | Idea | Pro | Contro |
|---|---|---|---|
| **T-1** | AR(1) di P2e con correzione della distorsione per bootstrap parametrico (stima, simula dal modello stimato, ricorregge) | piccolo cambiamento, mira a V2–V3 | resta legato all'AR(1): non risolve (d) |
| **T-2** | modello a spazio di stati u = x + ε con varianza di ε nota, AR(1) bivariato stimato per massima verosimiglianza ristretta (filtro di Kalman) | tratta in modo esatto rumore, vuoti e media stimata (sostituisce l'approssimazione B(φ)) | ancora AR(1); stima instabile con poche CR |
| **T-3** | inferenza non parametrica a blocchi di CR consecutive: wild cluster bootstrap con cluster = blocchi di lunghezza fissa (per esempio 13 CR, circa un anno) per emisfero, pesi di Webb per pochi cluster | non assume l'AR(1), quindi può rispondere a (d); include la componente individuale | P2b (blocchi mobili, L = 3, 6, 13) **non** ha raggiunto il livello nominale; con circa 16 blocchi per emisfero il numero di cluster è piccolo; potenza probabilmente bassa |
| **T-4** | calibrazione conservativa: p-value massimo su un insieme di confidenza per (φ, κ) (Berger–Boos), eventualmente su una famiglia AR(p) | controllo dei falsi verdetti anche con parametri incerti | conservativo, quindi meno potenza; costoso |

### 3.2 Componente individuale, requisito (b)

| | Idea | Pro | Contro |
|---|---|---|---|
| **I-1** | funzione di varianza stimata su tutte le regioni (per esempio log e_i² contro log Φ_i), poi rumore simulato da quella funzione anche per le celle singole | analogo utilizzabile dell'oracolo; tratta l'eteroschedasticità | dipende dalla forma della funzione; code |
| **I-2** | residui "cancellati" (rispetto alla media di cella senza i), con I-1 per le celle singole | corregge la leva senza modelli | due regimi da giustificare |
| **I-3** | nessuna simulazione separata: la componente individuale è inclusa nell'inferenza a cluster (T-3) | niente formula per la leva | eredita i limiti di T-3 |

## 4. Validazione (requisiti (c) ed (e))

Proposta di struttura, da fissare nel protocollo:
- **Scenari:**
  - corretti per T-1/T-2: AR(1) con φ ∈ {0; 0,5; 0,8; 0,9}, κ ∈ {−0,85; 0; +0,6}, rumore
    omoschedastico ed eteroschedastico;
  - richiesti da (d): AR(2) e salti di livello;
  - rumore con code pesanti (t con 4 gradi di libertà).
- **Disegno:** quello reale del campione S (e).
- **Semi:** nuovi, distinti per scenario, con intervalli dichiarati e controllo di non
  sovrapposizione nel codice; nessun seme di sviluppo.
- **Criterio:** limite CP al 95% della frazione di falsi verdetti ≤ 4% in **tutti** gli
  scenari, compresi AR(2) e salti, perché (d) è un requisito. Errore e criterio fissati prima,
  come in D. Il fatto che il limite CP ≤ 4% non dimostri il 2,5% si dichiara.
- **Potenza:** effetti iniettati (per esempio β = −0,1, −0,2, −0,3 · γ0) riportati. Da
  decidere se fissare una potenza minima sotto la quale la procedura, anche se calibrata, si
  dichiara non utile (proposta: potenza ≥ 0,5 a β = −0,2 γ0).
- **Regola di arresto:**
  - una sola validazione;
  - se fallisce, T3 e T5 restano descrittivi e non si prova un'altra procedura senza un motivo
    nuovo documentato;
  - nessuna applicazione ai dati prima dell'esito.

## 5. Percorso proposto

1. **Discussione di questo documento** (utente e revisore): scelta delle alternative da
   provare e del requisito (e).
2. **Pilota di sviluppo**, con un piano registrato e semi di sviluppo dichiarati:
   - confronto di due o tre combinazioni candidate, per esempio T-2 + I-1 come candidata
     basata su modello e T-3 + I-3 come candidata non parametrica;
   - falsi verdetti e potenza sul disegno reale e su alcuni scenari;
   - dichiarato come sviluppo: non vale come validazione.
3. **Protocollo P2f congelato:** una sola procedura, con scenari, semi, criteri, potenza
   minima e regola di arresto.
4. **Validazione unica.**
5. **Solo se superata:** applicazione a T3 e T5 sui dati reali, con i verdetti nella forma
   fissata dal protocollo.

## 6. Domande aperte

- Va adottato il requisito (e), cioè validare sul disegno reale anziché su quello sintetico
  di P2d?
- Lo scenario con κ negativo, suggerito dalla stima reale di T3, va incluso tra quelli che
  decidono l'accettazione, sapendo che la scelta è informata dai dati?
- AR(2) e salti di livello devono decidere l'accettazione, come richiede (d), o formare una
  fascia di robustezza con un limite proprio?
- Serve una potenza minima? Con due cicli e un regressore lento è possibile che nessuna
  procedura calibrata abbia potenza utile: è un esito da accettare e dichiarare.
- T5 richiede la stessa procedura di T3 o una propria? A livello di celle (318 celle, 176 CR)
  i cluster sono ancora meno.

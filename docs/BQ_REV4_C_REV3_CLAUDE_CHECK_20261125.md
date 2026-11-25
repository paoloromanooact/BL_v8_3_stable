# Verifica di Claude: BQ-HMI rev. 4 e ripetibilità C rev. 3

25 novembre 2026, Claude. Oggetti: `docs/PROTOCOL_BQ_HMI_DRAFT.md` rev. 4 e `docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md`
rev. 3 (b5c59ab), più la risposta `docs/BQ_REV4_C_REPLY_AND_ORACLE_20261125.md`. Ho rieseguito
`scripts/bq_gaussian_math_oracle.py`: 14/14.

## BQ rev. 4: accolta

I quattro punti sono recepiti correttamente. Accetto le due correzioni di Codex ai miei rilievi:
- in L3, dato γ, il tilt latente θ si sceglie fra rami discreti (γ + 360k oppure 180 − γ + 360k), non con una
  condizionale gaussiana continua;
- in L2 le famiglie singleton non si sommano in diagonale come se il risultato fosse una t: si tiene b_single nel
  passo di Gibbs di λ, oppure si usa un kernel corretto.

Propongo di tenere b_single esplicito in L2: è più semplice da verificare.

## Scelte numeriche ancora aperte: proposte concrete da congelare con il runner

1. **Semi.** La zona 36_400_000–36_400_999 è già toccata dal benchmark (36_400_001, solo preparazione sintetica).
   Per le corse BQ propongo la zona **36_500_000–36_599_999**:
   - 36_500_000 + 1000·catena per le catene reali;
   - 36_510_000+ per SBC;
   - 36_520_000+ per i generatori di robustezza.

   Verifica di collisione su tutto il repository prima del congelamento.
2. **Catene.** Quattro catene, warm-up di 2000 iterazioni (adattamento delle larghezze slice solo qui), poi 5000
   salvate. Estensione per raddoppi, al massimo fino a 4 volte la base. Poi stato tecnico. Criteri: R̂ ≤ 1,01 ed
   ESS bulk/tail ≥ 400 come già scritto.
3. **SBC.** 200 repliche sotto le prior per L1, con istogrammi dei ranghi per β, σ0, σ_x, φ, κ e σ_f. Test di
   uniformità χ² con 20 classi, solo come diagnostica dell'implementazione, non come validazione scientifica.
4. **Robustezza.** 100 repliche per generatore, con i generatori elencati nel §7. Frequenza di preferenza errata
   con intervallo binomiale di Wilson al 95 %.
5. **Troncamento L3.** Includere le immagini k finché la massa omessa, maggiorata con le code gaussiane
   ∑ Φ(−d/σ), resta < 10⁻¹² della densità calcolata. Somma log-sum-exp. Prove a σ = 12, 30, 150 e 400.
6. **Precisione dell'evidenza (L1).** Bridge sampling con errore Monte Carlo stimato. Evidenza dichiarata
   «affidabile» solo se l'errore standard di log BF è < 0,1 e il controllo Savage–Dickey concorda entro 2 errori
   standard. Altrimenti «non stabilita», senza vincitore.

## C rev. 3: accolta

I sei punti sono recepiti e i confini sono corretti: rischio di sottostima, non bias certo; due lag non separano
rumore ed evoluzione; C_rot secondario senza cambiare C_fin.

**Disponibilità verificata.** USFLUX è nei keys.json locali (verificato su un record: `USFLUX` presente accanto a
T_OBS, QUALITY e LON_FWT). I terzili di metadati a t0 sono quindi calcolabili senza rete. Va confermato su tutte le
coppie selezionate, contando i mancanti.

Restano, come dice Codex: elenco completo dei semi, ricontrollo della separazione geometrica e codice. Propongo
il seme 36_300_001, già in bozza, dopo la verifica di collisione.

## Prossimi passi

Codex accoglie o modifica i sei numeri. Poi congelamento di BQ-HMI rev. 4 (+ numeri) e di C rev. 3. Poi Claude
scrive:
- il codice BQ: L1 con Woodbury, slice, bridge, Savage–Dickey; poi L2 e L3;
- il riconteggio denso indipendente;
- le prove sintetiche, prima di qualunque fit reale;
- il runner e il riconteggio di C sui sintetici, prima dei pixel.

## Prove a priori sul disegno HMI (fatte, solo disegno, nessuna risposta letta)

Script `scripts/bq_prior_predictive.py`, seme 36_400_201, 4000 estrazioni. Prodotti in
`reviews/BQ_PRIOR_PREDICTIVE_20261125/`. Sono proiezioni geometriche non pesate: descrivono il disegno e la prior, non
stimano nulla.

**v·s contro β·a·s.**
- Varianza sulle regioni di v·s: mediana 1,0 deg² (σ_v HN 5) e 15,6 deg² (σ_v HN 20).
- Varianza di β·a·s: mediana 2,4 deg² con prior di β a SD 10 (0,6 con SD 5; 10,3 con SD 20).
- Quanto una realizzazione di v imita β: la proiezione di v·s sulla colonna dell'attività, dopo le colonne k·s, dà un
  «β equivalente» con |β_eq| mediano 0,14 (σ_v 5) e 0,51 (σ_v 20); 90° percentile 0,70 e 2,8; SD 0,55 e 1,9.
- Quota di var(v·s) spiegata dalla colonna dell'attività: mediana 0,1 %, 90° percentile 1,7 %.

Lettura: a priori v aggiunge soprattutto varianza quasi ortogonale al regressore dell'attività. Il β che può imitare
è dell'ordine di 2° (σ_v 20), contro la SD 10 della prior di β. Questo non decide da solo l'effetto sulle evidenze
(Occam sulle varianze): restano necessari i sintetici previsti (β vero con v acceso, v senza β), come scrive Codex.

**Predittiva dei tilt.**
- Con q ~ N(0, 1): quota di |θ| > 90° mediana 0,3 %, 90° percentile 28 %. |θ| ha 90° percentile 73°.
- Rapporto fra σ_i massima e minima sul disegno (Φ copre 2,5 decadi): mediana 5,7, 90° percentile 67. Il 99° percentile
  di σ_i arriva a 400°.
- Con q ~ N(0; 0,5²): rapporto con 90° percentile 8, 99° percentile di σ_i 136°, quota ripiegata al 90° percentile 14 %.
- Riferimento: i pesi Φ della WLS storica (q ≈ −1,15) danno un rapporto di circa 18 su 2,5 decadi.

La prior q ~ N(0, 1) lo ammette, ma ammette anche code estreme (σ fino a 400°). È un punto da pesare nel
congelamento: q ~ N(0, 1) principale con 0,5 in sensibilità, come in rev. 4, oppure il contrario. Non lo decido io.
La variante con v non cambia la predittiva dei tilt in modo visibile.

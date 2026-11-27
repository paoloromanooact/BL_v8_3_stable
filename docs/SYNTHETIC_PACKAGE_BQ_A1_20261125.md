# Pacchetto consolidato per la revisione Codex: BQ-HMI (sintetici) e A1 mappa–bipolo (selftest)

25 novembre 2026, Claude. **Solo sintetici**: nessun fit su risposte osservate, nessuna corsa osservata, nessun pixel
aperto. Protocolli BQ rev. 4, C rev. 3 e A1 **non congelati**. Ogni prova riporta il codice con il suo SHA-256 (come
eseguito), la configurazione, i semi e gli esiti, compresi fallimenti e diagnostiche. È sviluppo: non una validazione
e non una base per conclusioni sull'evidenza.

Ambiente: Python 3.10.12, numpy 2.2.6, scipy 1.15.3, pandas 2.3.3, OMP_NUM_THREADS=1. Commit del pacchetto:
il commit che introduce questo file (un unico commit con push dopo la conclusione di tutte le prove; l'hash è
riportato nella nota per Codex).

## SHA-256 del codice eseguito

| File | SHA-256 | Note |
|---|---|---|
| python/sharpbl/bq_core.py | 84e608ff003613e2d81a983140f7db3183f1abdd161be4e44bc51a72c4e20c36 | = HEAD bc366aa |
| python/sharpbl/bq_cv.py | ba6d673e93ed7ee796362dfb84e1da8c2b0f0fd4cddb82da9bfca6ceb0af9fa7 | = HEAD |
| python/sharpbl/bq_robust.py | 91aa60255b5a4be92515767fe4b538800cd861bbfe8974bcf8a113f1fbe7ef50 | nuovo: theta_init, cambi di ramo, preimage_init, split_rhat |
| python/sharpbl/bq_bridge.py | ceee6e8d8214b13a7940a3199785c2cc3a862bda980e5d7875c4ff43af0cd7ff | nuovo |
| python/sharpbl/sft_core.py | 053e622b1acde6540364d850561c3cc55afedab5f1803541965ffaae4538a554 | invariato |
| scripts/bq_core_selftest.py | 551b7a8219ca8e8e79135ff089f262c0a10f1a99689f5239e6b9283aa1062d20 | = HEAD |
| scripts/bq_bridge_selftest.py | 63cefd273cbbf95b0c9a2cbc78fb12691da5e19a161c10c49f5e36e36d88794d | nuovo |
| scripts/bq_identifiability_pilot.py | 2066891094d75433906409a3d9c6cb7c6e3eaa5a991c2726ecca2c60d7723ff3 | nuovo |
| scripts/bq_l3_branch_diagnostic.py | cb59a3ea09276fd8c8ddb1b90b27d15437f3df490fef1a25dfa8a2f93f0e2855 | nuovo |
| scripts/sft_map_bipole_pilot.py | fa5eb9bebbac32995f68399da9ecf4602c916ab61b3466d9593db2f8c07acc9a | A1 §2ter, passo dimezzato allineato |
| scripts/sft_map_bipole_pilot_recount.py | 7590e98015ef747cb4cbcbfd54e388d72c7a6ab32a01240a38201fa6524871b1 | A1 §2ter, own_point ripristinata |
| docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_DRAFT.md | dec5655883b775374ddbf9a54efe0ac587f05055b50be46ef67d6e81cbe36182 | bozza, non congelata |

## 1. Selftest BQ (nucleo, validazione incrociata, L2, L3)

- Comando: `OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_core_selftest.py`, seme 36_400_101 e derivati.
- Esito sul codice della tabella: **20/20**.
  - Il primo lancio con L2/L3 aveva dato 17/19, per due difetti dei test: un criterio relativo su covarianze quasi
    nulle e la quadratura senza gli estremi.
  - Il test 17 con il vero β = −30 come bersaglio era mal posto, perché la prior restringe β: è stato riscritto
    contro il riferimento stimato sui tilt latenti veri.
- Tempi di una valutazione sulla struttura reale: 1,7–1,8 ms (u) e 4,6–4,9 ms (u+v).

## 2. Bridge sampling (L1)

- Comando: `OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_bridge_selftest.py`, seme 36_400_501.
- Prova rapida dei casi 1–2, prima del selftest completo:
  - gaussiano in 3 dimensioni: −41,8215 ± 0,0010 contro −41,8199 esatta (1,6 SE);
  - caso unidimensionale asimmetrico: −41,9203 ± 0,0022 contro −41,9186 per quadratura.
- Selftest completo: **4/4**.
  1. Gaussiano esatto: −45,98987 ± 0,00114 contro −45,99079.
  2. Unidimensionale: −39,67631 ± 0,00239 contro −39,67826.
  3. BQ con una coordinata libera: −570,04855 ± 0,00114 contro la quadratura −570,05104 (2,2 SE).
  4. BQ con sei coordinate: log BF₀Q 0,0069 ± 0,0661 dal bridge (M0 e MQ, due catene ciascuno) e 0,0115 ± 0,0116 da
     Savage–Dickey. Concordano, ma non sono controlli del tutto indipendenti (stesso modello, campioni di MQ in
     comune).

## 3. Pilota di identificabilità β contro v

- Comando: `scripts/bq_identifiability_pilot.py --out reviews/BQ_IDENTIFIABILITY_PILOT_20261125`, seme 36_400_301.
- Configurazione: 4 repliche, catena 200 + 400, 10 processi; q ~ N(0; 0,5²).
- Generatori G1–G4, stime MQ senza v / con v HN 5 / con v HN 20, come nel docstring.
- Disegno reale (solo metadati), risposte sintetiche.
- Esiti per replica in FITS.csv, compresi stepping-limit e tempi. Concluso senza errori: 48 stime.
- Medie sulle 4 repliche (β vero tra parentesi; SD = SD a posteriori media; cop. = repliche con |β̂ − β| < 1,96 SD):

| Gen. | Stima | β medio | SD fra repliche | SD | log BF₀Q (min/max) | σ_v | cop. |
|---|---|---|---|---|---|---|---|
| G1 (−5) | senza v | −5,10 | 0,95 | 1,44 | −4,47 (−6,32/−1,84) | — | 4/4 |
| G1 | v HN5 | −5,06 | 0,97 | 1,46 | −3,95 (−6,24/−1,57) | 2,8 (vero 0) | 4/4 |
| G1 | v HN20 | −5,04 | 0,97 | 1,47 | −3,92 (−6,29/−1,39) | 3,4 | 4/4 |
| G2 (0) | senza v | +1,26 | 1,73 | 1,76 | +1,19 (−0,28/+1,83) | — | 3/4 |
| G2 | v HN5 | +0,91 | 1,06 | 1,87 | +1,48 (+1,06/+1,81) | 7,2 (vero 10) | 4/4 |
| G2 | v HN20 | +0,75 | 1,15 | 1,98 | +1,46 (+1,08/+1,80) | 10,7 | 4/4 |
| G3 (−5) | senza v | −5,66 | 1,74 | 1,69 | −4,09 (−6,35/−0,29) | — | 4/4 |
| G3 | v HN5 | −5,46 | 1,51 | 1,75 | −3,15 (−4,49/−0,30) | 6,7 (vero 10) | 4/4 |
| G3 | v HN20 | −5,35 | 1,39 | 1,79 | −2,81 (−4,26/−0,25) | 9,2 | 4/4 |
| G4 (0) | senza v | −4,65 | 1,45 | 1,52 | −3,00 (−5,93/−0,56) | — | 0/4 |
| G4 | v HN5 | −4,63 | 1,51 | 1,53 | −2,92 (−6,16/−0,50) | 3,0 | 0/4 |
| G4 | v HN20 | −4,61 | 1,54 | 1,56 | −2,72 (−6,06/−0,45) | 3,7 | 0/4 |

- Lettura descrittiva (sviluppo, non validazione):
  - G1: recupero e incertezza simili con e senza v; v costa circa 0,5 in log BF₀Q.
  - G2: senza v, β si sposta verso valori positivi (+1,3; una replica su quattro non copre lo zero). Con v lo spostamento
    si riduce (+0,75/+0,9) e la copertura è 4/4: miglioramento parziale. σ_v risente della prior (7,2 con HN5, 10,7 con
    HN20; vero 10).
  - G3: β recuperato; con v l'evidenza per MQ si riduce (log BF₀Q da −4,1 a −2,8/−3,1): v assorbe parte del segnale.
  - G4: limite d'identificabilità per costruzione. Il termine che segue l'attività viene attribuito a β (−4,6,
    copertura 0/4, evidenza a favore di MQ) con e senza v.
- Diagnostica insufficiente per uno studio definitivo:
  - una catena per stima (nessun R̂);
  - catene corte (200 + 400);
  - arresti dello stepping-out frequenti, 282–552 per catena, verosimilmente nel riscaldamento con larghezza
    iniziale 1;
  - solo 4 repliche.

  Lo studio vero richiede numeri e regole fissati prima.
- Lettura, secondo le cautele di Codex:
  - recupero, incertezza e diagnostica complessivi, non replica per replica;
  - in G2, quanto v migliora la separazione e quanto dipende dalla prior;
  - G4 come limite di identificabilità per costruzione.

## 4. Diagnostica dei rami L3 (distinta dal selftest)

- Comando: `scripts/bq_l3_branch_diagnostic.py --out reviews/BQ_L3_BRANCH_DIAGNOSTIC_20261125`, seme 36_400_401.
- Configurazione: 3 catene (rami identità, |γ| > 60 riflessi, riflessione casuale), 300 + 900 iterazioni.
- Dati sintetici con σ0 = 70 e quota ripiegata vera 0,226.
- Esiti:
  - le tre catene concordano: β −10,04 / −9,83 / −9,75 (SD 7,6–8,1), σ0 52,5 / 53,1 / 52,0, quota ripiegata 0,195 in
    tutte;
  - split R̂: β 0,999, log σ0 1,010, quota ripiegata 1,019;
  - ogni regione cambia ramo almeno una volta, con circa 248 cambi per regione su 900 iterazioni.
- **Punto aperto, controllo aggiuntivo sugli stessi dati:**
  - il riferimento stimato sui tilt veri dà σ0 67,8 ± 4,0, q 0,11 ± 0,08 e σ al flusso mediano 72,6;
  - L3 (catena di controllo) dà σ0 54,0, q 0,31 ± 0,21 e σ al flusso mediano 65,8.

  Con il ripiegamento la scala è meno informata e qui risulta più bassa di circa il 10 % al flusso mediano, con la
  quota ripiegata 0,195 contro 0,226. Con una sola realizzazione non distinguo una distorsione sistematica da un caso.
  Servono repliche.
- La concordanza non dimostra un'esplorazione completa sui dati reali.

## 5. A1 mappa–bipolo: selftest

- Runner: `scripts/sft_map_bipole_pilot.py --selftest`.
  - Prima del riallineamento del passo dimezzato: 20/20.
  - Sul codice della tabella (passo dimezzato allineato): **20/20**.
    - Rapporti sintetici: 6651 risolti, 699 sotto soglia, 0 non risolti.
    - Calcolo aggiunto uguale all'evoluzione diretta (1e-10 relativo).
    - Convergenza sulle tre regioni: massimo 7,3e-4, stato ok.
    - Preflight: N 400 respinto, N 800 accettato (massimo 3,3e-4).
- Riconteggio: `scripts/sft_map_bipole_pilot_recount.py --selftest`, codice finale (SHA 36c443fc…, nella tabella in
  fondo): **33/33**, exit 0 (settimo lancio, 25 novembre 17:45–18:16).
  - Riconteggio completo della corsa sintetica OK (preflight proprio, propagatori, gaussiane, riepiloghi,
    denominatori, manifest, convergenza); 32 manomissioni rifiutate.
  - La prova «requisito di convergenza non rispettato con valori concordi» ora passa con la tolleranza 1e-12: il
    riconteggio rifiuta il prodotto perché manca la ricevuta completa. Il «[FALLITO]» stampato in quella riga è il
    controllo interno che il rifiuto riporta, non un fallimento del selftest.
  - Il lancio è partito 0,06 s dopo l'ultimo salvataggio del file (mtime 17:45:24,83; log creato 17:45:24,89):
    l'esito vale per il codice della tabella. Il runner (fa5eb9be…) non è cambiato dopo il suo 20/20.
  - Log conservato in `reviews/BQ_A1_RECOUNT_SELFTEST_20261125/recount_selftest7.log`.
  - È un selftest su sintetici: non produce una ricevuta e non è una validazione su dati osservati.
- Fallimenti e interruzioni registrati:
  1. primo riconteggio fermato a mano perché troppo lento (propagatori densi a N 1600 ricostruiti per caso);
     corretto con cache;
  2. secondo lancio interrotto perché il codice era cambiato (§2ter);
  3. terzo lancio: NameError (own_point cancellata da una mia modifica). Corretto;
  4. quarto lancio interrotto per riallineare il passo dimezzato, su richiesta di Codex;
  5. quinto lancio sul codice allineato: il riconteggio completo della corsa sintetica è OK, e le prime due
     manomissioni sono state rifiutate. Alla terza (chiave duplicata in DIPOLES) own_ratios ha sollevato un
     ValueError invece di rifiutare il prodotto.
     - Corretto: i confronti di SUMMARY e RATIOS, ricalcolati dai prodotti, sono protetti (guarded); un prodotto
       malformato è un rifiuto con il tipo d'errore.
     - Corretta anche la manomissione «N diverso», che usava N = 800, cioè il valore giusto dopo A1; ora usa 400.
     - Prova rapida: con una chiave duplicata i due confronti danno «rifiutato» senza eccezione.

  6. sesto lancio, con il codice guarded e N = 400: **32/33**.
     - Riconteggio completo della corsa sintetica OK; 31 manomissioni rifiutate.
     - Fallita solo la prova «requisito di convergenza non rispettato con valori concordi»: abbassava la tolleranza a
       1e-15, il livello degli arrotondamenti. Al tempo 0 il criterio vale circa 3e-15 in entrambi i codici, quindi
       le etichette di superamento possono divergere fra le due implementazioni.
     - Verificato a parte (runner 3,1e-15, riconteggio 3,3e-15; criteri reali ≥ 2,5e-10). La prova ora usa 1e-12,
       con margine di circa 100 volte da entrambi i lati, e stampa le righe interne.

  7. settimo lancio, con la tolleranza 1e-12: **33/33** (sopra).

  Nessuno dei sette ha prodotto una ricevuta (nel selftest la ricevuta non è prevista).
- Controlli rapidi prima dell'ultimo lancio:
  - nomi non definiti: nessuno;
  - runner contro riconteggio su dati minimi: SUMMARY e RATIOS identici; livelli 2N e 4N entro 1e-14; passo
    dimezzato entro 1,5e-13 anche a N 20/40, dove dt_max vale 26–103 giorni.

## 4bis. Arresti dello stepping-out del pilota: diagnosi per coordinata

Script diagnostico `reviews/BQ_SLICE_HITS_DIAGNOSTIC_20261125/hits_diag.py` (a0aea52561317210fedda2bb720b1742d4238245c0f1427539007e098a0ac228): replica la regola di slice_sweep
contando gli arresti per coordinata e per fase. Caso G3, fit MQ v HN20, catena 200 + 400, seme come nel pilota.
Risultato in RESULT.txt.

- Gli arresti sono pochi per coordinata: 0–10 nel riscaldamento, 3–16 nella fase salvata (400 iterazioni).
- Sono compatibili con la regola di Neal: l'estensione massima m = 50 viene divisa a caso fra i due lati e può darne
  zero a un lato. La regola resta esatta. Non indicano un difetto.
- Informazione utile: con questi generatori (σ_x 2,1 contro σ0 20) i parametri temporali hanno SD a posteriori circa
  uguale a quella della prior sulla scala trasformata: log σ_x 0,94, z_φ 0,90, z_κ 0,96, log σ_v 1,18, z_φ_v 1,08,
  z_κ_v 0,99.
- σ0 e q sono ben identificati (SD 0,03–0,04).
- Lo studio vero deve riportare questa debole identificabilità e la dipendenza dalle prior delle componenti temporali.

## 5bis. Ripetibilità C: runner su sintetici (spec rev. 3 non congelata; --run rifiutato)

- Codice: `scripts/sft_c_repeatability.py` (666b5597542bbd41435bf1921afdb5daa931f18db12e34daba0455bc6808ab24); selftest `scripts/sft_c_repeatability_selftest.py` (1b9485294e8c59660acaf62f9ed7d97af51fdb8f7aceb84e2027f9464ee879ba).
- Riuso della geometria già rivista del pilota osservativo: margini direzionali, copertura dai centri, erosione,
  preparazione dei pixel, LocalBox.
- Esito finale: **11/11** (C_rot incluso; i SHA definitivi sono nella tabella in fondo).
  - A: mappe identiche, differenze nulle.
  - B: rotazione; la differenza di persistenza è 0,720 = shift, quella dopo sola rotazione −0,019.
  - C: rumore correlato; rapporto di varianza 0,14 per ρ = 0,8, atteso 0,2 con 40 coppie.
  - D: una sola polarità → `one_polarity_empty`.
  - E: patch piccola → `finite_coverage_insufficient`.
  - F: statistiche angolari al taglio.
  - G: pesi 1/(K n).
  - H: bootstrap per componenti.
  - I: `--run` rifiutato.
- **Fallimenti del primo giro, conservati:**
  1. test B con patch troppo piccola per i margini a 2 giorni (difetto del test, corretto);
  2. test D: la variante bilanciata con una sola polarità NON dava uno stato esplicito. Riscalava silenziosamente il
     flusso a metà, perché `pixels` del runner osservativo divide per il flusso negativo solo dove ci sono pixel
     negativi. Nel runner C ora c'è un controllo esplicito delle due polarità a entrambi gli istanti.
- **Anomalia da correggere anche in `scripts/sft_observed_pilot.py` (punto 3, non congelato):** la stessa `pixels`
  con kind = balanced va resa esplicita prima del congelamento del punto 3.
- C_rot implementato: C_fin ristretto alle celle la cui pre-immagine per rotazione cade su copertura valida a t0
  (almeno 8 sotto-punti su 16). Persistenza e sola rotazione sono ricalcolate entrambe su C_rot.
  - Con i margini del pilota osservativo, che includono già max|ω − ω_C|·gap, C_rot = C_fin per costruzione
    (verificato: 88,4 = 88,4 deg² a 2 giorni).
  - Il primo test che si aspettava C_rot < C_fin era sbagliato ed è stato corretto. C_rot resta come restrizione di
    sicurezza.
- **Punto 3:** pixels(kind = balanced) ora solleva BalanceUnavailable con una polarità vuota, e run_pair registra
  `balance_unavailable`, mentre le misure grezze restano.
  - Regressione: il flusso grezzo dei pixel è uguale al flusso della mappa intera (rapporto 1,000000000000; su C 1,000),
    quindi non è dimezzato.
  - Selftest `scripts/sft_observed_pilot.py --selftest`: **9/9** (era 8/8 più la regressione).
  - Il runner C usa lo stesso nome di stato.
- Da chiudere nella specifica:
  - terne, terzili USFLUX e classi di lag sono previsti nei riepiloghi, ma non ancora collegati alle tabelle dei
    metadati.

## 5ter. BQ-M: inventario delle sovrapposizioni (solo metadati; compito assegnato a Claude nel §3bis del piano)

Script `scripts/bqm_overlap_inventory.py` (e0124b13667824cd07873d7fdf13b8a6ae4b7bd9edcf617aeabdbbb2e386da75). Prodotto `reviews/BQM_OVERLAP_INVENTORY_20261125/INVENTORY.json`
con gli SHA degli input. Lette solo colonne d'identità e di stato: nessun tilt, Joy o differenza.

- **MWO R4 isolati:** 5223 record, dal 1974-01-02 al 2012-11-26.
  - Per ciclo ed emisfero: 20N 53, 20S 78, 21N 595, 21S 657, 22N 779, 22S 901, 23N 839, 23S 934, 24N 229, 24S 158.
  - I cicli 20 e 24 sono parziali.
- **Ponte in luce bianca DPD** (stato del tilt WL dei record MWO): ok 4694, meno di due macchie 340, un lato vuoto 189.
  - Ok per ciclo: 20: 120; 21: 1129; 22: 1466; 23: 1623; 24: 356.
  - È il ponte per la deriva di MWO; da solo non la identifica (Codex, rev. 4 §8).
- **MWO–HMI:**
  - 153 record già accoppiati nel confronto S2 di T3-MWO (2010-05-04 – 2012-11-24; N 73, S 80; 153 NOAA distinte);
  - nel disegno T3 HMI (2485 regioni, 2020 con NOAA) i record con un NOAA presente in R4 sono 249, tutti del ciclo
    24; 153 di questi sono negli accoppiamenti S2;
  - l'accoppiamento per giorno va definito nella specifica BQ-M. Le stesse regioni misurate da due strumenti sono
    due misure di un tilt latente, e serve un modello dell'evoluzione fra istanti diversi (rev. 4 §8).
- **MDI:**
  - il catalogo completo NON esiste (decisione rimandata dopo Q4);
  - il pilota L2 ha 360 record (ok 133; no magnetogramma 174; fuori dal dominio μ 47; nessuna immagine 6);
  - 292 dei 360 hanno un NOAA presente in R4. Il controllo d'identità MDI–MWO ha 267 + 32 righe.
- **Anomalia trovata e corretta nello script:** in R4 il NOAA è una stringa, e 654 record hanno un suffisso letterale
  (per esempio «11620p»: m 236, a 207, b 74, n 62, …). Il primo conteggio dava 0 sovrapposizioni HMI–R4 per il tipo
  diverso. Ora si confronta la parte numerica.
  - Più regioni MWO con suffisso possono condividere un numero NOAA: l'accoppiamento a regione fisica va deciso nella
    specifica, non qui.

## 6. Decisioni chieste a Codex

- I sei numeri proposti in 3b7903c, con q ~ N(0; 0,5²) principale e SD 1 in sensibilità (accolto).
- Validazione incrociata per L2/L3: la densità predittiva non è gaussiana e va specificata.
- Riconteggio indipendente del codice BQ.
- Numero di repliche e lunghezze delle catene per lo studio di identificabilità vero, dopo questo pilota.
- Diagnostica L3: repliche per il punto su σ0 e q.


## SHA-256 definitivi dei file cambiati dopo la prima tabella

| File | SHA-256 |
|---|---|
| scripts/sft_map_bipole_pilot_recount.py | 36c443fc81006118d1f9af7e0afc4798ca745e5a41516920bd399cbc9595ebc2 (guarded, manomissione N = 400, tolleranza 1e-12; settimo lancio 33/33; sostituisce 5b8e2362…, sesto lancio 32/33) |
| scripts/sft_c_repeatability.py | 6e97dcaa8254ddae077aa4a542d9780bbdb29807e5ff3888fde293e77bf48d6b |
| scripts/sft_c_repeatability_selftest.py | 11dd72a882997bcb000ae36b5dcbe8583a41018056685fd7d2b366357d35eebb |
| scripts/sft_observed_pilot.py | dec3c4cea56e9c11760751fe050a424c02481d80b53aacc54657d9bcda972ffb |
| python/sharpbl/bq_bridge.py | ceee6e8d8214b13a7940a3199785c2cc3a862bda980e5d7875c4ff43af0cd7ff |
| scripts/bq_bridge_selftest.py | 63cefd273cbbf95b0c9a2cbc78fb12691da5e19a161c10c49f5e36e36d88794d |
| scripts/bqm_overlap_inventory.py | e0124b13667824cd07873d7fdf13b8a6ae4b7bd9edcf617aeabdbbb2e386da75 |
| reviews/BQ_SLICE_HITS_DIAGNOSTIC_20261125/hits_diag.py | a0aea52561317210fedda2bb720b1742d4238245c0f1427539007e098a0ac228 |

Tutti gli altri file della prima tabella sono invariati (SHA ricontrollati il 27 novembre prima del commit).

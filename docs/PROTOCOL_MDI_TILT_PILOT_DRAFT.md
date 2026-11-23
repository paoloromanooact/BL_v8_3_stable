# Pilota del catalogo di tilt magnetici MDI 1996–2010 — protocollo (BOZZA)

**BOZZA rev. 1, 23 novembre 2026 (Claude). Da rivedere con Codex prima di qualsiasi misura.**
- Nessun tilt MDI misurato e nessun magnetogramma scaricato.
- Base:
  - inventario `docs/MDI_TILT_PILOT_INVENTORY.md`;
  - audit delle mappe sinottiche `results/MDI_SYNOPTIC_AUDIT` (`511f2dc`);
  - parere di Codex `0afc47c`.

## 0. Scopo e limiti

Il pilota è **descrittivo e preparatorio**. Risponde a quattro domande:
- **Q1. Resa, copertura, rumore e correlazione temporale** delle misure MDI, per stratto. Servono a costruire il
  disegno prospettico del catalogo completo. Non sono la precisione del catalogo completo.
- **Q2. Effetto della composizione sinottica.** Si confrontano tilt da mappe sinottiche e da magnetogrammi istantanei
  full-disk, sullo stesso gruppo. Lo scarto si misura, non si assume piccolo. **Q2 precede la scelta del metodo del
  catalogo completo.**
- **Q3. Scarto relativo MDI–MWO** sugli stessi gruppi, per attività, dimensione e geometria.
  - Nessuno dei due strumenti è assunto corretto.
  - Un accordo non dimostrerebbe che entrambi siano privi di distorsioni e non validerebbe T3.
- **Q4. Precisione prospettica di un nuovo T3 su MDI da solo**, sul disegno ricavato da Q1. È una stima analitica,
  non un verdetto e non una validazione. Un'analisi combinata MDI+MWO si valuta solo dopo.

Il pilota **non stima β₃**, non produce verdetti sul quenching e non costruisce il catalogo completo.

**Precedenti da citare:**
- BARD-MDI (Muñoz-Jaramillo et al. 2021), sul disco e non cieco: solo confronto descrittivo dichiarato;
- Li & Ulrich (2012), tilt MDI 1996–2010;
- ARISE, cataloghi di regioni da mappe sinottiche MDI/HMI (indicato da Codex; riferimento da verificare).

## 1. Dati

**Livello 1, sinottico (sul disco, senza rete)**
- `mdi.synoptic_Mr_polfil_96m`, 193 mappe, CR 1909–2104. SHA-256 in `results/MDI_SYNOPTIC_AUDIT/FILES.csv`.
- Licenza CC0 (header `LICENSE`).
- Griglia: CEA 3600×1440, 0,1° in longitudine di Carrington, passo uniforme in sin λ. Campo **radiale** (Mx cm⁻² ≡ G).
- Costruzione dichiarata negli header: `EQPOINTS` 20, `W_WEIGHT` 'Even', `HWNWIDTH` 20, `IMG_NUM` 10–447.
  - Interpretazione da documentazione HMI: ogni longitudine è la media uniforme dei 20 magnetogrammi più vicini al suo
    passaggio al meridiano centrale. Per MDI a 96 min sarebbero circa 32 h.
  - **Da verificare per la serie MDI** prima del congelamento.
- Mancano le CR 1938–1940. 17 mappe hanno pixel mancanti: 1996, 1998–1999, 2002-02, 2003–2004, 2007-01, 2009-07.

**Livello 2, full-disk (rete, solo dopo autorizzazione esplicita)**
- `mdi.fd_M_96m_lev182`, magnetogrammi LOS istantanei.
- Per ogni gruppo del sottoinsieme: **due magnetogrammi consecutivi** (96 min) vicini all'istante DPD del giorno scelto.
  La coppia serve anche a stimare la ripetibilità della misura.
- Metadati per record: T_REC, T_OBS, QUALITY, INTERVAL, MISSVALS, geometria.
- Trasporto: quello dell'emendamento A1, con il redirect verificato verso jsoc1.
- **Budget proposto: ≤ 220 file, ≤ 1,5 GB, ≤ 600 richieste.**

**Posizioni e attività**
- gDPD/sDPD come per MWO (stessi file e SHA).
- Attività emisferica mensile A_main come nel DESIGN di MWO.

**MWO**
- Tabella isolata del rilascio verificato (`results/MWO_TILT_CATALOGUE_RELEASE`), solo per Q3.
- I tilt MWO sono già aperti e pubblici nel pacchetto locale. Il confronto non è cieco rispetto a MWO e lo si dichiara.

## 2. Popolazione e giorno

- Gruppi DPD 1996-05-01 → 2010-10-31, area corretta ≥ 1 milionesimo, |λ| ≤ 45°. Stessa lettura di MWO, comprese le
  correzioni dei secondi = 60.
- **Giorno del gruppo:** il giorno con |LCM| minimo fra quelli in cui il gruppo è isolato, con la stessa regola di
  isolamento di MWO (nessun altro centro DPD nella finestra quel giorno).
  - Per il livello 1 il giorno serve a individuare il passaggio al meridiano e il tempo di Carrington del gruppo.
  - Per il livello 2 serve a scegliere i magnetogrammi.
- Le chiavi sono (NOAA DPD, giorno UTC), come in MWO.

## 3. Campione del pilota (selezione cieca ai tilt, dai soli metadati DPD)

**Strati:** attività (terzili di A_main sull'epoca MDI, confini 1,20 e 2,22) × emisfero × area DPD (terzili sulla
popolazione eleggibile, fissati prima della selezione). Sono 18 strati.

**Livello 1**
- 30 gruppi per stratto, 540 in tutto, estratti con `numpy.random.default_rng(seme)`. Seme proposto **71 000 001**, da
  verificare contro gli elenchi di semi già usati.
- Metà per stratto con un record MWO isolato lo stesso giorno, se disponibili; l'altra metà dagli altri gruppi.
- Uno stratto con meno gruppi disponibili prende tutti quelli disponibili; lo si dichiara.
- Un gruppo in una CR mancante resta nel campione come «mappa mancante»: conta nella resa.

**Livello 2**
- Sottoinsieme di 90 gruppi del livello 1 con record MWO: 5 per ciascuno dei 18 strati.
- Gli strati vuoti si dichiarano, senza rimpiazzare con altri strati.
- Questo dà circa 180 magnetogrammi.

Le scelte di 30 e 5 per stratto sono operative: bilanciano il costo dello scaricamento con la stima di resa e di
rumore. Codex valuterà se bastano per Q2 e Q4.

## 4. Misura

**Finestra e corpo della misura:** gli stessi di MWO.
- finestra |λ − λ_DPD| ≤ 6°, |L − L_DPD| ≤ 8°;
- centroidi delle due polarità pesati con |B_r| sulla sfera;
- tilt nella convenzione di P1, γ = sign(λ̄)·asin(sin tilt);
- separazione, flusso, polarità di testa e Hale atteso.
- Lo stesso codice di `scripts/t3_mwo_catalogue.py`, estratto in un modulo condiviso senza cambiarne il risultato. Il
  riconteggio verifica l'identità su MWO.

**Adattatore sinottico (livello 1)**
- **Coordinate.**
  - Asse x = tempo di Carrington: CT = CRVAL1 + (i + 1 − CRPIX1)·CDELT1, con CARRTIME = 360·CR − 180. Longitudine
    L = (360·CR − CT) mod 360, da verificare con LON_FRST/LON_LAST nel selftest.
  - Asse y: sin λ = (j + 1 − CRPIX2)·CDELT2.
- **Tempo di Carrington del gruppo:** CT_g = 360·N − L_DPD, con N intero scelto in modo che CT_g sia il più vicino al
  tempo di Carrington dell'istante DPD del giorno scelto.
- **Bordi fra rotazioni:** si cuciono le mappe CR e CR ± 1 lungo CT.
  - Una finestra che tocca una CR mancante fallisce con stato «mappa mancante».
- **Campo già radiale:** nessuna divisione per μ e nessuna soglia μ.
- **Area dei pixel:** costante (griglia CEA a uguale area), Δ(lon in rad)·Δ(sin λ)·R☉².
- **Pixel mancanti:** con più del 5 % della finestra mancante la misura fallisce («finestra incompleta»), come A1.
- Si registrano IMG_NUM della mappa e MISSVALS nella finestra.

**Adattatore full-disk (livello 2)**
- Geometria da CRPIX1/2, CDELT1/2, RSUN_OBS, CRLT_OBS, CRLN_OBS, CROTA2.
- B_r = B_LOS/μ, con μ ≥ 0,8 su tutta la finestra.
- QUALITY = 0, oppure solo bit dichiarati innocui. MISSVALS nella finestra.
- INTERVAL registrato. Il prodotto 1 min / 5 min non viene corretto: è riportato.

**Soglie (fissate ora)**
- Principale: 50 ≤ |B_r| ≤ 4000 G, come MWO, per la confrontabilità di Q3. Sensibilità: 100 G.
- Pixel minimi per polarità: **≥ 10** (livello 1) e **≥ 10** (livello 2). Sotto soglia la misura fallisce («una
  polarità debole»); lo stato è registrato.
- Il rumore si misura (Q1) e non si usa per cambiare le soglie dopo la lettura.

**Scala del campo:** MDI, MWO e HMI hanno scale diverse (MDI ≈ 1,3–1,4 × HMI). I flussi si confrontano solo come
rapporti descrittivi. Le soglie in G non sono equivalenti fra strumenti, e lo si dichiara.

## 5. Analisi descrittive

**Q1 — resa, copertura, rumore, correlazione temporale**
- **Resa per stratto:** gruppi con misura riuscita / gruppi del campione, con le cause dei fallimenti.
- **Rumore del campo:** deviazione standard robusta di B_r in finestre di quiete a bassa latitudine.
  - Livello 1: per mappa.
  - Livello 2: per magnetogramma.
- **Ripetibilità del tilt** (livello 2): differenza assiale fra i due magnetogrammi consecutivi dello stesso gruppo.
- **Correlazione temporale:**
  - procedura M (REML AR(1) per cella CR × emisfero) sui residui di γ dal modello di Joy per ciclo ed emisfero, sul
    livello 1;
  - parametri φ, κ, σ²ₓ e componente individuale, descrittivi e con l'avvertenza del bordo.
  - Il campione del pilota è rado nel tempo: la stima di φ è debole e lo si dichiara.

**Q2 — sinottica contro full-disk** (livello 2)
- Per gruppo: d_γ = γ_syn − γ_fd e |d_ax|.
- Mediana con intervallo bootstrap a blocchi di 6 CR, complessiva e per terzile di attività, area e separazione.
- Rapporto di flusso e numero di pixel.
- Anche la ripetibilità full-disk, per separare composizione e rumore.

**Q3 — MDI contro MWO** (stessi gruppo e giorno)
- Le stesse statistiche per (syn − MWO) sul livello 1 e (fd − MWO) sul livello 2.
- Per terzile di attività, di area e di separazione, e per |LCM| del giorno MWO.
- Accordo delle polarità di testa e di Hale.

**Q4 — disegno prospettico**
- Popolazione eleggibile 1996–2010 per stratto × resa di Q1 = numero atteso di record del catalogo completo.
- Con la struttura di varianza di Q1: SE prospettico di β₃ e potenza per le rampe del 10 % e del 20 %, sul disegno
  proiettato. Stesse formule del controllo del disegno MWO.
- È una previsione condizionata alle assunzioni, non una validazione. Un T3 su MDI richiederebbe protocollo e
  validazione propri.

**BARD-MDI:** sulle regioni comuni, γ di BARD contro il nostro. Descrittivo e non cieco.

## 6. Dopo il pilota (nessuna regola automatica)

La scelta del metodo del catalogo completo (sinottico, full-disk o misto) e la decisione di proseguire si prendono
**dopo** la revisione degli esiti di Q2 e Q1, con i numeri riportati per stratto. Non si estende il pilota fino al
catalogo completo prima di quella revisione.

## 7. Codice, prove, conservazione

- **Script:**
  - `scripts/mdi_tilt_pilot_select.py` (selezione);
  - `scripts/mdi_synoptic_adapter.py` (adattatore sinottico);
  - `scripts/mdi_fd_adapter.py` (adattatore full-disk);
  - `scripts/mdi_tilt_pilot_measure.py` (misura);
  - `scripts/mdi_tilt_pilot_recount.py` (riconteggio indipendente).
  - Modulo condiviso per il corpo della misura, con identità verificata su MWO.
- **Prove sintetiche, prima di qualsiasi misura reale:**
  - mappa sinottica sintetica con un dipolo di tilt noto;
  - cucitura fra rotazioni;
  - finestra incompleta, CR mancante;
  - full-disk sintetico con geometria nota e μ;
  - soglie;
  - identità del corpo di misura sul pilota MWO.
- La selezione si conserva in Git prima di misurare. Gli output si conservano prima della lettura; segue il
  riconteggio indipendente con ricevuta.
- Rete solo per il livello 2, dopo l'approvazione del protocollo e l'autorizzazione esplicita del budget.

## 8. Questioni per la revisione

1. Interpretazione di `EQPOINTS`/`HWNWIDTH` per la serie MDI: va confermata sulla documentazione prima di congelare.
2. Dimensioni del campione (30 e 5 per stratto) e se il livello 2 basta per Q2 per area e attività.
3. Soglia principale di 50 G con sensibilità a 100 G, e minimo di 10 pixel per polarità.
4. Uso di M sul pilota rado per la correlazione temporale (Q1), o una stima alternativa.
5. Giorno del gruppo: |LCM| minimo fra i giorni isolati. Per il livello 1 conta il passaggio al meridiano; i gruppi non
   isolati restano fuori dal pilota come in MWO.
6. Seme 71 000 001 e budget di rete del livello 2.

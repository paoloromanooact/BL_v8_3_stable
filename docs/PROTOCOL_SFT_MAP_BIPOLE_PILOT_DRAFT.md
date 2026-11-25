# Pilota SFT mappa–bipolo — BOZZA di protocollo (revisione 1, non congelata)

Stato: **bozza per la revisione di Codex**, 25 novembre 2026 (Claude). Non autorizza simulazioni né download.
I punti che dipendono dall'inventario del codice SFT e dei dati HMI (in corso, a cura di Codex) sono marcati
**[dopo l'inventario]**. Piano di riferimento: `docs/BL_WORK_PLAN.md`, priorità 1; lista dell'utente, punto 2.

## 0. Obiettivo servito e che cosa aggiunge

- **Obiettivo 1 (sorgente BL).** Il proxy P1 riassume una regione con pochi ingredienti: flusso, posizione dei centroidi
  delle polarità, separazione, tilt, latitudine media e polarità leading. Il pilota chiede **quanto cambia il
  contributo della regione al dipolo assiale futuro** se, nello stesso modello di trasporto superficiale (SFT), la mappa
  osservata della regione è sostituita dal bipolo costruito con quegli ingredienti.
- **Che cosa aggiunge.** Le prove già fatte sono istantanee: D contro D_bal e proxy compatto al passaggio al meridiano. Il
  pilota aggiunge l'evoluzione: deriva, diffusione e cancellazione possono dare alla mappa e al bipolo dipoli finali
  diversi anche quando quelli iniziali coincidono.
- **Limite.** È un controllo dell'approssimazione **dentro il modello**. Non verifica il modello contro il Sole, che è
  il compito del protocollo del punto 3. Non calibra S_BL in unità di dipolo e non somma le regioni.

## 1. Informazioni già note (pilota non cieco)

- Catalogo P1 (`results/P1/P1_SBL_CATALOG_BY_HARP.csv`, 14 195 righe): S_BL, D, D_bal, centroidi, tilt e qualità già
  calcolati e in parte letti nelle analisi P2/T3/T5. Le scelte del campione sotto usano solo metadati e colonne di
  identificazione e qualità, ma chi scrive conosce le distribuzioni generali del catalogo.
- Ricomparse candidate P1e: 443 HARP su 7133, in 373 famiglie.
- In letteratura il confronto mappa–bipolo in SFT è già stato studiato (Yeates 2020, arXiv:2008.03203). Questa bozza
  ne riprende l'impostazione generale. I valori numerici di quel lavoro non sono usati come criteri finché non sono
  verificati nel testo.

## 2. Domanda e grandezze

Per ogni regione i del campione si eseguono due simulazioni SFT, **con la sola regione i** sulla sfera e campo
iniziale altrove nullo. L'equazione SFT è lineare in B_r, quindi il contributo di una regione non dipende dalle altre.
- **M (mappa):** B_r osservato della regione, con la maschera del §4.
- **B (bipolo):** due polarità costruite dagli ingredienti P1 (§5).

Grandezze, in G, con R = R_sun dell'header (come P1):
- D_X(t) = 3/(4πR²) ∫ B_r sin λ dA, per X = M, B, a ogni tempo di confronto (§7);
- ΔD(t) = D_B(t) − D_M(t), assoluta;
- ΔD(t)/|D_M(t)| solo se |D_M(t)| supera una soglia fissata (§8). Per dipoli vicini a zero si riporta solo la
  differenza assoluta.

Unità: S_BL è in Mx·cm e il dipolo in G. Per un bipolo compatto D_bal ≈ 3 hale_sign·S_BL / (4πR³). Questa relazione è
un'approssimazione e non sostituisce il calcolo di D sulle mappe.

## 3. Campione

- **Popolazione:** HARP con record primario P1, `valid_bl` vero, `family_rank` = 0 (prima apparizione: niente
  ricomparse, che sono stati successivi della stessa regione), ciclo assegnato e Br e bitmap del record primario già
  su disco **[dopo l'inventario]**.
- **Strati, solo da metadati:**
  - complessità: HARP con un solo NOAA associato contro HARP con più NOAA o senza NOAA (`NOAA_ARS`). Una
    classificazione morfologica, per esempio δ o Mount Wilson, è possibile solo se una fonte esterna è disponibile
    **[dopo l'inventario]**;
  - flusso: terzili di `USFLUX` del record primario sulla popolazione;
  - latitudine: |LAT_FWT| < 10°, 10–20°, > 20°;
  - ciclo: 24 e 25.
- **Numerosità proposta:** 4 regioni per cella complessità × flusso × latitudine (2 × 3 × 3 = 18 celle), cioè circa 72
  regioni. Le celle con meno di 4 HARP si prendono intere e si dichiarano. Il ciclo si riporta, ma non stratifica, per
  non moltiplicare le celle.
- **Estrazione:** permutazione con seme fissato (zona di semi nuova, verificata disgiunta da quelle già usate), prime 4
  per cella; pesi campionari 1/π per cella registrati.
- **Nessuna esclusione dopo la lettura degli esiti.** Le regioni che falliscono per motivi tecnici (rimappatura,
  flusso nullo dopo la maschera, errore del codice) restano nel denominatore, con la causa.

## 4. Mappa osservata (M)

- **Record:** il record primario P1 (|LON_FWT| ≤ 30°), cioè gli stessi `Br` e `bitmap` CEA della misura P1.
- **Pixel:** stessa maschera e soglia di P1: Br finito, |Br| ≤ 10 000 G, bitmap ≥ 33, |Br| ≥ 100 G. Così M e B
  partono dallo stesso insieme di pixel e il confronto isola l'approssimazione bipolare dalle scelte di misura. Gli
  altri pixel sono a zero.
- **Flusso preesistente:** la maschera HARP contiene anche flusso non della regione emersa (plage residuo, regioni
  vicine incluse nella HARP). Nel principale resta incluso, come nella misura P1, e il bipolo lo rappresenta
  attraverso centroidi e flusso. Sensibilità: soglia 300 G, che privilegia le parti intense.
- **Bilanciamento:** la mappa mascherata ha in genere Φ₊ ≠ Φ₋, e un monopolo in SFT non ha significato fisico.
  Principale: riscalare ciascuna polarità a Φ̄ = (Φ₊ + Φ₋)/2, cioè B_r → B_r·Φ̄/Φ± sul segno corrispondente. È coerente
  con D_bal e conserva le forme. Sensibilità: sottrazione di un campo uniforme sui pixel mascherati. Si riportano
  sempre lo sbilancio iniziale (Φ₊ − Φ₋)/(Φ₊ + Φ₋) e D prima e dopo il bilanciamento.
- **Rimappatura sulla griglia SFT:** conservazione del flusso per cella, con aree sferiche esatte; si dichiara la
  frazione di flusso che resta dopo la rimappatura. Prova obbligatoria: D_M(0) sulla griglia SFT uguale a D_bal P1
  (mappa bilanciata) entro una tolleranza fissata dopo le prove sintetiche **[griglia dopo l'inventario]**.

## 5. Bipolo (B)

Gli scalari P1 non determinano una mappa bipolare unica: forma ed estensione sono scelte dichiarate.
- **Posizioni:** i centroidi P1 delle due polarità, (L₊, λ₊) e (L₋, λ₋). Separazione, tilt e latitudine media del
  bipolo coincidono quindi con quelli del catalogo, per costruzione.
- **Flusso:** Φ̄ per ciascuna polarità, con i segni osservati.
- **Forma principale:** due macchie gaussiane sulla sfera, B ∝ exp(−δ²/(2σ²)) con δ la distanza angolare dal centroide.
  σ di ciascuna polarità si ricava dalla sua area sopra soglia: σ = √(A±/(2π R²)) in radianti. La forma è quindi
  fissata da una grandezza misurata, non scelta per far concordare M e B.
- **Sensibilità di forma:** σ fisso a 2° e a 4° per entrambe le polarità; bipolo puntiforme (una cella per polarità).
- D_B(0) per sorgenti puntiformi è D_bal. Per macchie estese differisce poco: si riportano D_B(0) − D_M(0) e D_B(0) −
  D_bal.

## 6. Modello di trasporto

Stesso codice, griglia, parametri e tempi per M e B. Nessun parametro si sceglie confrontando M con B.
- **Equazione:** ∂B_r/∂t = −Ω(λ) ∂B_r/∂φ − (1/(R cos λ)) ∂(v(λ) B_r cos λ)/∂λ + η ∇²_h B_r − B_r/τ.
- **Parametri di riferimento, da letteratura [codice e valori esatti dopo l'inventario]:**
  - rotazione differenziale delle strutture magnetiche: Snodgrass & Ulrich (1990), la stessa di P1d/P1e;
  - flusso meridiano: profilo e ampiezza di un modello SFT pubblicato (valori tipici 10–15 m/s);
  - diffusività η: valore di riferimento del modello scelto (valori tipici 250–600 km²/s);
  - decadimento τ: assente nel principale; τ = 5 e 10 anni come sensibilità.
- **Sensibilità di trasporto:** due combinazioni oltre al riferimento, η e ampiezza del flusso meridiano agli estremi
  dell'intervallo tipico. Sono le stesse per tutte le regioni e per M e B. Servono a vedere se l'approssimazione
  dipende dal trasporto, non a scegliere un trasporto.
- **Istante iniziale:** il T_REC del record primario. Il campo evolve senza nuove sorgenti.

## 7. Tempi di confronto

t = 0, 27 giorni, 6 mesi, 1 anno, 3 anni dall'inserimento. Si attende che a 3 anni il contributo della singola regione
abbia superato la fase di trasporto e cancellazione iniziale; la diffusione continua però a ridurre lentamente il modo
dipolare (scala R²/(2η), circa 15 anni con η = 500 km²/s). Da verificare con il codice scelto, senza cambiare i tempi
dopo aver visto gli esiti. Si salvano anche le curve D_X(t) a passo regolare, per i grafici.

## 8. Prodotti e lettura

**Per regione:** HARP, strati, Φ₊, Φ₋, sbilancio, frazione di flusso dopo la rimappatura, D e D_bal P1, D_M(0),
D_B(0), D_X(t) ai tempi del §7, ΔD(t), ΔD(t)/|D_M(t)| (con la soglia del §2), separazione e tilt; lo stesso per ogni
sensibilità.

**Per strato e totale:** mediana e quantili 10–90 % di ΔD/|D_M| e di |ΔD|; frazione di regioni con segno di D_B(3 anni)
uguale a quello di D_M(3 anni). I dipoli si sommano solo come grandezza descrittiva dell'effetto aggregato, con la
cautela del §9.

**Soglia per i rapporti:** |D_M(t)| ≥ 0,1 del valore mediano di |D_M(t)| nel campione allo stesso tempo. Sotto la
soglia si riportano solo differenze assolute. La soglia è da confermare in revisione.

**Lettura:** descrittiva. Una preferenza pratica, da fissare prima delle corse e non come criterio scientifico
validato, potrebbe essere: approssimazione bipolare «adeguata nel modello» per uno strato se la mediana di
|ΔD(3 anni)|/|D_M(3 anni)| è ≤ 0,2 con tutti i trasporti. I valori sono proposti per la revisione. Una regione con
grande differenza non si esclude e non si corregge.

## 9. Che cosa non fa

- Non confronta con le osservazioni successive (protocollo del punto 3).
- Non stima il dipolo solare complessivo: le regioni sono simulate da sole; la somma di contributi lineari ignora
  ricomparse e cancellazioni con flusso di altre regioni già presente sul Sole.
- Non modifica P1, i suoi record o le sue soglie; non scarica nuovi dati salvo decisione separata dopo l'inventario.
- Non riapre T3, T5 o Q4.

## 10. Codice e sequenza

1. Inventario (Codex) → scelta del codice SFT, della griglia e dei parametri: revisione 2 di questa bozza.
2. Revisione della bozza (Codex); congelamento con SHA, seme e impronte degli input.
3. Codice: rimappatura, bilanciamento, costruzione del bipolo, simulazione, misura di D. Prove sintetiche indipendenti
   (Codex): un bipolo noto conserva il flusso netto nullo; per sorgenti puntiformi D(0) = D_bal; segni, unità e
   orientamento di L; limiti analitici: la sola rotazione differenziale conserva il dipolo assiale, la sola diffusione lo
   fa decadere come exp(−2ηt/R²) (modo l = 1), il termine τ come exp(−t/τ).
4. Corsa unica, conservazione prima della lettura, riconteggio indipendente, rapporto descrittivo.

## 11. Punti aperti per la revisione

1. Popolazione con `family_rank` = 0 soltanto, o anche le ricomparse come strato separato?
2. Complessità definita da `NOAA_ARS`: è sufficiente come proxy prima di una classificazione morfologica?
3. Bilanciamento per riscalatura delle polarità contro sottrazione uniforme: quale come principale?
4. σ dalle aree contro σ fisso come forma principale del bipolo.
5. Tempi di confronto e soglia per i rapporti.
6. Preferenza pratica del §8: tenerla, cambiarla o lasciare la lettura solo descrittiva.
7. Numerosità: circa 72 regioni in 18 celle bastano per un pilota, dati i costi di calcolo **[dopo l'inventario]**?

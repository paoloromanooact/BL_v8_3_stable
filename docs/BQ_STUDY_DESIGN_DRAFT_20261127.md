# BQ-HMI: disegno degli studi sintetici da registrare (BOZZA, non congelata)

Claude, 27 novembre 2026. Pilastro: quenching (BQ-HMI). Raccoglie le decisioni già prese da Codex (revisione di
f17d230, §1 e §4, nel repository MWO) e il costo misurato oggi. Solo sintetici sul disegno reale T3 (2485 record, solo
metadati: CR, emisfero, latitudine, attività, flusso, famiglia; nessun tilt osservato). **Non cieco:** sono noti il
pilota di identificabilità (4 repliche, `reviews/BQ_IDENTIFIABILITY_PILOT_20261125/`), la diagnostica L3 a una
realizzazione e i benchmark di oggi. Nessuna corsa lunga parte prima della registrazione (SHA del testo, codice e
manifesto dei semi).

## 1. Studio di identificabilità (S-ID)

**Generatori** (valori veri del pilota: σ0 = 20, q = −0,4, σx = 2,1, φ = 0,75, κ = −0,42, σf = 3, k = 23/25/21/22):

| Gen. | β vero | v (componente temporale di Joy) | Ruolo |
|---|---|---|---|
| G1 | −5 | assente | recupero di β |
| G2 | 0 | AR(1), σv 10, φv 0,95, κv 0,5 | falso quenching da v |
| G3 | −5 | come G2 | β con v attivo |
| G4 | 0 | v_i s_i = −5 a_i s_i | confondimento per costruzione: non identificabile |
| G5 | 0 | assente | nullo puro (proposta) |
| G6 | +5 | assente | segno opposto (proposta) |
| G7 | −5 | assente, φ = 0,99 | persistenza forte (proposta) |
| G8 | 0 | assente, residui t4 stimati con L1 | code non modellate (proposta) |

G5–G8 completano l'elenco chiesto dalla bozza §7 e da Codex; vanno confermati prima della registrazione. G4 è fuori
dalla separazione identificabile: si riportano attribuzione a β e dipendenza dalle prior, senza chiedere il recupero
di zero.

**Stime appaiate per replica:** MQ senza v, MQ con v HN5, MQ con v HN20, sulla stessa risposta sintetica. L1. Le
likelihood L2/L3 entrano in studi separati (§2 e dopo la CV sequenziale).

**Catene** (accolte da Codex): 4 catene, 2000 di riscaldamento + 5000 salvate; larghezze fisse dopo il riscaldamento;
estensioni della fase salvata a 10000 e 20000 iterazioni che continuano lo stato; poi stato tecnico. Gate
(`bq_diag`): almeno 4 catene originali, R̂ rank bulk e ripiegato ≤ 1,01, ESS bulk e di coda ≥ 400 per β, log σ0, q,
log σx, zφ, zκ, log σf e, con v, log σv, zφv, zκv. Una stima che non supera il gate è un fallimento tecnico contato a
parte, mai sostituita.

**Quantità per replica:** media e SD a posteriori di β, intervallo credibile al 95 % e sua copertura, P(β < 0), log BF0Q
di Savage–Dickey con il suo MCSE (medie a blocchi per catena, riferimento appaiato Codex), σv, stato tecnico.

**Riepiloghi:** per generatore e stima: distorsione, RMSE, copertura e ampiezza degli intervalli con MCSE; frequenze
con intervallo di Wilson al 95 % (con 0/100 il limite superiore è circa 3,7 %: non si dichiarano tassi più bassi);
fallimenti tecnici sul totale. **Regola di preferenza (accolta da Codex il 27 novembre come criterio operativo):**
«evidenza di quenching» se P(β < 0) > 0,95 **e** log BF0Q < −log 10, valutata solo sulle stime che superano il gate.
**Soglie incerte per errore Monte Carlo (approvata da Codex il 27 novembre):** dopo che le catene hanno superato il
gate, una replica è `threshold_uncertain` se, per almeno uno dei due criteri, l'intervallo chiuso
[stima − 2 MCSE, stima + 2 MCSE] **raggiunge o attraversa** la soglia (estremi inclusi). Il MCSE di P(β < 0) si calcola
sul contributo per estrazione effettivamente usato nella stima, Φ(−m_s/√v_s) con m_s e v_s media e varianza
condizionali di β all'estrazione s, e quello di log BF0Q sulle ordinate condizionali riscalate; in entrambi i casi con
medie a blocchi dentro ogni catena, conservando ordine e confini delle catene. È una misura della precisione numerica
della decisione, non un esito scientifico. Le repliche incerte restano nel denominatore totale, con un conteggio
distinto dai fallimenti tecnici; nessuna estensione motivata solo dalla vicinanza alla soglia (le estensioni seguono
solo il gate). Per G4, costruito per non essere identificabile, si riporta
quanto l'attribuzione a β dipende dalla prior (v HN5 contro HN20) invece di una frequenza di preferenza. Nessuna
soglia cambiata dopo aver visto i risultati.

**Semi** (zona 36_500_000–36_599_999, accolta): seme = 36_500_000 + 4000·g + 40·r + 4·f + c, con g = generatore
(0–23), r = replica (0–99), f = stima (0–8), c = catena (0–3); la risposta sintetica della replica usa f = 9, c = 3
(slot riservato). La formula è iniettiva sull'intero studio (40·r + 4·f + c ≤ 3999 < 4000). Le stime appaiate
condividono di proposito la stessa risposta (stesso g, r). Il manifesto completo dei semi va scritto e verificato
senza collisioni prima della registrazione.

## 2. Repliche L3 (S-L3)

Accolte da Codex: 100 realizzazioni per ciascun σ0 = 20/40/70 e per q vero 0 e −0,4. Per ogni realizzazione, fit L3 e
fit di riferimento sui tilt latenti veri con le stesse prior. Quattro inizi: identità, riflesso per |γ| > 60, riflesso
casuale, alias traslato di 360°; si verifica che ogni inizio ripieghi sul dato. Si riportano distorsione, RMSE,
copertura e ampiezza per β, σ0, q e σ al flusso mediano, proiezioni osservabili della media, quota dei rami, R̂/ESS e
fallimenti. Un 10 % di differenza in una singola realizzazione non è prova di distorsione. Il limite della coda L3
segue la routine certificata (T/S ≤ 10⁻¹²) prima di questa corsa.

## 3. Costo misurato e decisione richiesta

Benchmark di oggi (un core, disegno T3, risposta sintetica): campionatore slice L1 **0,086 s per iterazione senza v**
(32 valutazioni da 2,7 ms) e **0,30 s con v** (50 valutazioni da 6,1 ms). Con 4 × (2000 + 5000) iterazioni: circa
40 min-core per stima senza v e 2,4 h-core con v; circa 5,5 h-core per replica (tre stime appaiate). **S-ID con 100
repliche × 4 generatori ≈ 2200 h-core (≈ 6 giorni su 16 core); con 8 generatori ≈ 12 giorni.** S-L3 si aggiunge.

Opzioni da decidere **prima** della registrazione (nessuna scelta guardando i risultati):
1. **Lunghezza per ESS misurata:** una corsa di dimensionamento su poche repliche di G1/G2 misura l'ESS per iterazione
   delle quantità del gate. Se 1000–2000 salvate bastano per ESS ≥ 400, la base scende di 2,5–5 volte; restano le
   estensioni automatiche.
2. **Fasi:** prima fase con 100 repliche per G1–G4 e v HN20; HN5 su un sottoinsieme fissato prima (per esempio le
   prime 30 repliche); G5–G8 in una seconda fase.
3. **Parallelismo:** catene e repliche su 16 processi indipendenti, ciascuno a un thread, con semi dal manifesto.
4. **Campionatore più efficiente** per i parametri temporali (debolmente identificati nel pilota): richiederebbe una
   propria verifica prima dell'uso.

Proposta di Claude: 1 + 2 + 3, con la corsa di dimensionamento registrata come sviluppo (non parte dello studio).

**Decisione Codex (27 novembre).**
- *Pilota di dimensionamento* (sviluppo, semi separati): poche repliche di G1–G4 (G3 e G4 inclusi perché sono i casi
  in cui quenching e variazione temporale di Joy si confondono), 4 catene, 2000 di riscaldamento, diagnosi dopo 1000,
  2000 e 5000 estrazioni per catena, comprese le quantità del Bayes factor (ordinata di Savage–Dickey e media
  condizionale di β). Script `scripts/bq_sizing_pilot.py` (2 repliche, stime senza v e v HN20, semi 36_401_000 +
  1000 g + 100 r + 10 f + c, risposta + 99; 16 processi a un thread; catene salvate appena finite). Serve a fissare la
  lunghezza **prima** dello studio.
- *Prima fase* dello studio: G1–G4 × 100 repliche, confronto appaiato senza v e v HN20 su tutte; v HN5 sulle prime 30
  repliche di ogni generatore, fissate nel manifesto; 16 processi a un thread. Ai tempi misurati circa 1480 h-core
  (poco meno di quattro giorni su 16 core) prima delle estensioni; con 1000–2000 estrazioni salvate invece di 5000 il
  costo iniziale scende di circa 1,75–2,33 volte.
- *Seconda fase*: G5–G8, a partire da G5 come controllo di falso positivo sotto il nullo puro.

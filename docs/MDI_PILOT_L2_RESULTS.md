# Pilota MDI, livello 2 (magnetogrammi full-disk) — esiti descrittivi Q2, ripetibilità e Q3 full-disk

24 novembre 2026 (Claude). Protocollo congelato `docs/PROTOCOL_MDI_TILT_PILOT.md` (SHA `77367350…`) ed emendamento
A1 congelato (`0428653`, SHA `73a075e8…`).

## Catena

| Passo | Commit | Controllo |
|---|---|---|
| Selezione (90 gruppi di livello 2, sottoinsieme dei 530 di livello 1) | `b605fd5` | riconteggio 6/6 (`495c32d`) |
| Misura L1 e analisi L1 | `ec859e8`, `eda3515` | riconteggi 6/6 e 13/13 (`4906974`, `ba71036`) |
| Piano A1 e download (161 FITS) | `b6f6658`, `85609aa` | riconteggio del piano 8/8 |
| Misura L2 (run su `fcba552`) | `02aca76` | riconteggio 12/12, 360/360 righe (`b0a38cf`) |
| Analisi L2, codice corretto dopo la revisione Codex (chiusura positiva) | `f089840` | — |
| Corsa dell'analisi L2 | `4249b72` | riconteggio 10/10, partial false (`52849f0`) |

L'indice `MANIFEST.txt` è stato allineato in `6156144`: nei commit dei prodotti `4249b72` e della ricevuta `52849f0`
non era ancora aggiornato. Prodotti e ricevuta erano già conservati in Git; i loro byte e hash sono rimasti invariati.

## Stato e lettura

- **Descrittivo.** Gli intervalli sono bootstrap a blocchi di 6 rotazioni (seme 71 100 001, 2000 repliche),
  nominali e **non validati**. Con meno di 10 coppie si riportano solo n e mediane.
- **Confronti correlati.** I sottogruppi sono molti e condividono le coppie; le soglie 50 e 100 G sugli stessi dati
  non sono repliche indipendenti. Un intervallo nominale che esclude zero in un sottogruppo non basta a dichiarare
  una dipendenza.
- **Nessuno strumento né prodotto è assunto corretto.** Le differenze sono relative:
  - Q2 = sinottica − fd(A);
  - ripetibilità = A − B;
  - Q3FD = fd(A) − MWO.
  - I rapporti sono primo/secondo membro.
- **Regola principale A1** (QUALITY {0, 0x200}). La regola originale {0} è secondaria: 8 immagini A e 5 B misurate,
  ovunque sotto le 10 coppie; le sue tabelle sono conservate ma non commentate oltre le rese.
- **Campione piccolo.** 90 gruppi; 61 con A misurata; 58 coppie A–B; 49 coppie con MWO. Le mediane non pesate
  descrivono le coppie misurate del campione, non la popolazione eleggibile.

## Resa del livello 2 (regola A1)

Denominatore: i 90 gruppi di livello 2, per l'immagine A e per l'immagine B. La resa proiettata sulla popolazione
eleggibile (5401 gruppi) usa i pesi 1/π₂. È lo stimatore a rapporto sum(w2_i I_i)/sum(w2_i), con I_i = 1 per una
misura riuscita, calcolato sui 90 gruppi estratti. È una stima della resa nella popolazione eleggibile con queste
regole, non una misura effettuata su tutti i 5401 gruppi; qui non ne è riportata l'incertezza.

| Gruppo | Resa A del campione | Resa A proiettata | Resa B del campione |
|---|---|---|---|
| tutti | 61/90 (67,8 %) | 47,0 % | 59/90 (65,6 %) |
| coorte M1 / U | 49/54 (90,7 %) / 12/36 (33,3 %) | 94,7 / 30,4 % | 87,0 / 33,3 % |
| area 1 / 2 / 3 | 66,7 / 56,7 / 80,0 % | 29,8 / 35,1 / 75,1 % | 66,7 / 56,7 / 73,3 % |
| attività 1 / 2 / 3 | 70,0 / 70,0 / 63,3 % | 41,5 / 52,3 / 47,1 % | 63,3 / 66,7 / 66,7 % |
| INTERVAL di A 30 s / 300 s | 35/48 / 26/33 | 47,9 / 61,3 % | — |
| QUALITY di A 0 / 0x200 | 5/9 / 56/72 | 49,7 / 54,8 % | — |

- **Fallimenti di A (29 su 90):**
  - finestra di misura fuori dal dominio μ ≥ 0,8: 20;
  - nessun magnetogramma ammissibile nel giorno: 9.
  - Nessun fallimento per pixel mancanti, polarità o soglia: a 100 G la resa è identica a quella a 50 G.
- **Fallimenti di B:** fuori dominio μ 19; nessun magnetogramma 9; nessuna immagine B 3.
- **La proiezione è più bassa del campione** perché la coorte U (gruppi senza record MWO isolato nello stesso
  giorno) pesa 4005 dei 5401 gruppi eleggibili e ha resa bassa: 19 dei suoi 36 gruppi hanno la finestra fuori dal
  dominio μ. La causa di questa concentrazione non è stata esaminata.
- **Confronto a 50 G:** resa proiettata 92,8 % per le sinottiche e 47,0 % per le immagini A full-disk selezionate
  vicino a t_DPD, con le regole congelate.
  - Per A i fallimenti osservati sono 20 finestre fuori dal dominio μ ≥ 0,8 e 9 assenze di magnetogramma ammissibile.
  - La disponibilità delle finestre di quiete a ±30° è una quantità distinta e non condiziona la resa del tilt.
  - Cambiare la geometria richiederebbe un emendamento dichiarato non cieco.
- **Regola originale {0}:** A 8/90 (8,9 %, proiettata 9,0 %), B 5/90; 78 gruppi senza magnetogramma ammissibile.

**Zone quiete** (dispersione osservata del campo; non è rumore strumentale)
- Lati validi 24 su 318 (159 immagini misurate). Scartati:
  - per un gruppo DPD nella finestra: 171;
  - fuori dal dominio μ: 120;
  - fuori dal disco: 3.
- 24 immagini con un valore, nessuna con due: mediana 20,6 G (10° percentile 12,7, 90° 22,5).
- La mediana 20,6 G è condizionata alle sole 24 immagini con una finestra valida su 159. Prodotti, geometria,
  epoche e campioni non sono appaiati con le sinottiche: il confronto con 6,1 G non misura un rapporto di rumore né
  un effetto del prodotto.

## Q2 — sinottica − full-disk(A), stesso gruppo

Distanza temporale |T_OBS(A) − t_DPD|: mediana 0,34 h, massimo 1,0 h. L'istante per pixel della sinottica è
indeterminato. La differenza comprende quindi:
- composizione temporale;
- rimappatura;
- risoluzione;
- evoluzione reale.
Non isola la sola composizione sinottica (protocollo §0).

| Gruppo | n | mediana d_ax | mediana d_γ | accordo leading | flusso sin/fd | area sin/fd |
|---|---|---|---|---|---|---|
| tutti (50 G) | 61 | −0,2° [−0,8, +0,6] | −0,6° [−1,2, −0,2] | 100 % | 0,87 | 0,95 |
| tutti (100 G) | 59 | −0,1° [−0,8, +0,4] | −1,0° [−1,6, −0,5] | 100 % | 0,87 | 0,96 |
| emisfero N / S (50 G) | 29 / 32 | −0,6° [−1,3, −0,1] / +0,6° [−0,8, +1,2] | −0,6 / −0,6° | 100 % | 0,85 / 0,90 | 0,95 / 0,95 |
| attività 1 / 2 / 3 (50 G) | 21 / 21 / 19 | −0,1 / −0,5 / −0,4° | −0,5 / −0,8 / −1,2° | 100 % | 0,87 / 0,85 / 0,89 | 0,95 / 0,97 / 0,95 |
| separazione 1 / 2 / 3 (50 G) | 18 / 21 / 22 | −0,4 / −0,2 / −0,2° | +0,3 / −0,5 / −1,0° | 100 % | 0,74 / 0,87 / 0,90 | 0,82 / 0,89 / 0,98 |
| INTERVAL 30 s / 300 s (50 G) | 35 / 26 | −0,4 / −0,1° | −1,2 / −0,6° | 100 % | 0,85 / 0,89 | 0,93 / 0,96 |

Fra parentesi gli intervalli bootstrap al 95 %, non validati.

- **Mediane delle differenze di tilt entro circa 1°.**
  - Per l'insieme completo, gli intervalli di d_ax contengono zero.
  - La mediana di d_γ = sign(λ_DPD)·d_ax è −0,6° a 50 G e −1,0° a 100 G; entrambi gli intervalli nominali
    escludono zero.
  - Nei due emisferi le mediane campionarie di d_ax hanno segni opposti, e quelle di d_γ sono entrambe negative.
    È una descrizione del campione, senza identificazione della causa o esclusione di errori di riferimento.
  - Lo scarto è piccolo rispetto alla dispersione per coppia e le soglie non sono indipendenti: è da tenere
    presente nella scelta del metodo, non è una distorsione dimostrata.
- **Dispersione per coppia** (calcolo in lettura, vedi sotto): mediana di |d_ax| 1,4°, 90° percentile 17,5°,
  2 coppie oltre 45° (0 a 100 G).
- **Polarità leading:** concorda in tutte le coppie.
- **Flusso:**
  - flusso sinottico/full-disk: mediana 0,87 (10° percentile 0,65, 90° 0,96);
  - aree: mediana 0,95;
  - pixel: rapporto 1,7, ma dipende dalle griglie dei due prodotti e non è una differenza fisica.
  - Il flusso sinottico è più basso, di più nelle separazioni piccole (0,74).
- **Le 8 coppie con |d_ax| > 10°:**
  - 7 hanno separazione sinottica sotto il primo terzile (3,97°);
  - comprendono le 4 coppie con gli scarti A − B più grandi (sezione seguente);
  - in questi gruppi la misura full-disk varia già fra due immagini a 1,6 h.

## Ripetibilità — A − B (full-disk, stesso INTERVAL)

|Δt| = 96 min per 53 coppie, 97 min per una, 192 min per 4; B precede A in 7 coppie. La differenza comprende
evoluzione reale ed errori eventualmente correlati: il pilota non li separa.

| Gruppo | n | mediana d_ax | mediana d_γ | accordo leading | flusso A/B |
|---|---|---|---|---|---|
| tutti (50 G) | 58 | 0,0° [−0,3, +0,3] | +0,1° [−0,3, +0,3] | 98,3 % [94,6, 100] | 0,998 |
| tutti (100 G) | 58 | −0,1° [−0,4, +0,05] | 0,0° [−0,2, +0,3] | 98,3 % [94,0, 100] | 0,998 |
| INTERVAL 30 s / 300 s (50 G) | 32 / 26 | +0,3 / −0,1° | +0,1 / +0,1° | 96,9 / 100 % | 0,998 / 0,998 |
| transizione di QUALITY sì (50 G) | 2 | +0,15° | −0,2° | 100 % | 1,004 |

- **Dispersione per coppia:** mediana di |d_ax| 0,7°, 90° percentile 3,9°, una coppia oltre 45° (0 a 100 G).
- **Flusso:** rapporto A/B fra 0,97 e 1,01 (10°–90° percentile).
- **La polarità leading cambia in una coppia** (10070m, 2002-08-14, separazione 0,1°; d_ax 89°).
- Nei sottogruppi un solo intervallo nominale esclude zero (attività 1, d_γ +0,26° [+0,01, +0,80], 50 G). Con
  molti intervalli correlati e copertura nominale non validata, questo risultato isolato non dimostra una dipendenza.
- **Transizioni di QUALITY:** solo 2 coppie misurate; non permettono una lettura.
- **Lettura:** nelle 58 coppie, con |Δt| mediano 1,6 h e intervallo 1,6–3,2 h, la mediana di |d_ax| è 0,7°.
  Questo scarto combina evoluzione ed errori eventualmente correlati; non stima l'errore della singola misura.

## Q3FD — full-disk(A) − MWO, coorte M1

Distanza temporale |MWO − T_OBS(A)|: mediana 8,2 h (da 0,4 a 13,6 h), molto maggiore che in Q2 e nella
ripetibilità.

| Gruppo | n | mediana d_ax | mediana d_γ | accordo leading | flusso fd/MWO |
|---|---|---|---|---|---|
| tutti (50 G) | 49 | +0,8° [−1,8, +4,8] | +0,4° [−3,4, +2,2] | 93,9 % [88,5, 100] | 18,0 |
| tutti (100 G) | 49 | +1,4° [−1,2, +3,7] | −1,0° [−3,0, +0,9] | 93,9 % | 15,2 |
| attività 1 / 2 / 3 (50 G) | 16 / 16 / 17 | −0,2 / +0,3 / +3,4° | +0,2 / +1,7 / −3,4° | 100 / 100 / 82,4 % | 16,9 / 23,8 / 18,0 |
| area 1 / 2 / 3 (50 G) | 17 / 14 / 18 | 0,0 / +0,2 / +1,2° | +2,2 / −0,7 / −0,4° | 94,1 / 85,7 / 100 % | 24,1 / 27,5 / 7,7 |
| separazione 1 / 2 / 3 (50 G) | 16 / 15 / 18 | −4,2 / +4,8 / −1,4° | +0,1 / −3,0 / +1,5° | 93,8 / 93,3 / 94,4 % | 17,2 / 20,9 / 19,7 |

- **Complessivamente** le mediane sono vicine a zero e gli intervalli lo contengono.
  - Dispersione per coppia: mediana di |d_ax| 6,8°, 90° percentile 32°, 4 coppie oltre 45° (8,2 %).
  - La polarità leading discorda in 3 coppie.
- **Due sottogruppi presentano intervalli nominali che escludono zero** (tre intervalli):
  - separazione 2, d_ax +4,8° [+0,8, +16,4] a 50 G e +4,5° [+2,1, +16,2] a 100 G;
  - attività 3 a 100 G, d_γ −2,9° [−13,5, −2,5]; a 50 G −3,4° [−16,9, +0,9].
  - Il segno di quest'ultimo è lo stesso del terzile più attivo nel confronto sinottica − MWO del livello 1
    (−1,7°), ma i due confronti non sono indipendenti: stessi gruppi e stessi record MWO, in parte.
  - Con confronti correlati e intervalli non validati questi due sottogruppi non dimostrano una dipendenza
    dall'attività o dalla geometria.
- **Rapporto di flusso fd/MWO:** mediana 18,0 (15,2 a 100 G), 10°–90° percentile 6,3–55,7. È più alto per le
  regioni piccole (area 1–2: 24–28; area 3: 7,7).

## Stessi gruppi: sinottica e full-disk contro MWO (calcolo appaiato in lettura)

Sui 49 gruppi di Q3FD, ho unito le coppie Q3FD con le coppie sinottica − MWO conservate dell'analisi L1 della stessa
soglia (`Q3_PAIRS_main.csv` a 50 G, `Q3_PAIRS_sens100.csv` a 100 G), su NOAA e giorno, una a una; il record MWO
(istante, tilt, polarità leading, flusso) è lo stesso nei due file. Coppie comuni: 49/49 a 50 G, 48/49 a 100 G.

| 50 G, stessi 49 gruppi | mediana d_ax | mediana d_γ | mediana \|d_ax\| | 90° perc. \|d_ax\| | oltre 45° | accordo leading | flusso / MWO |
|---|---|---|---|---|---|---|---|
| fd(A) − MWO | +0,8° | +0,4° | 6,8° | 32,3° | 4 | 93,9 % | 18,0 |
| sinottica − MWO | +1,8° | −2,0° | 7,1° | 31,1° | 3 | 93,9 % | 14,7 |

- **Lo scarto per coppia rispetto a MWO è simile con i due prodotti MDI.**
  - Correlazione di Spearman fra |d_ax(fd − MWO)| e |d_ax(sin − MWO)|: 0,88.
  - Il full-disk ha lo scarto assoluto minore in 26 coppie su 49.
  - A 100 G: mediane di |d_ax| 7,5° e 5,8°, Spearman 0,87, 24 su 48.
- Sulle 49 coppie comuni a 50 G, le due distribuzioni degli scarti assoluti rispetto allo stesso record MWO hanno
  mediane e 90° percentili vicini. A 100 G, sulle 48 coppie comuni, le mediane sono 7,5° e 5,8°.
  - Sono confronti descrittivi, senza intervalli per il confronto appaiato né un criterio di equivalenza: non
    quantificano e non escludono il contributo della composizione sinottica.
  - I due scarti condividono il record MWO, quindi anche la correlazione elevata non identifica quale contributo
    produca gli scarti. L'origine degli scarti resta non identificata.
- **Flusso:** l'ampio rapporto di flusso rispetto a MWO è presente con entrambi i prodotti MDI: sui 49 gruppi comuni la
  mediana è 18,0 per fd/MWO e 14,7 per sinottica/MWO. Il passaggio al full-disk non elimina la differenza osservata;
  questo confronto non ne identifica la causa.
- Questo confronto appaiato non è nel codice rivisto. È un calcolo fatto in lettura sui prodotti conservati, con le
  definizioni scritte sopra; il protocollo (§5) prevede entrambi i confronti con MWO.

## Calcoli in lettura (non nel codice rivisto)

Sono calcolati sui prodotti conservati `4249b72` (L2) ed `eda3515` (L1), senza nuove scelte:
- mediana e 90° percentile di |d_ax|;
- numero di coppie oltre 45°;
- percentili del rapporto di flusso;
- distanze temporali;
- elenchi delle coppie con scarti grandi (soglie descrittive: |d_ax| > 10° per Q2; > 5° o cambio di polarità per
  A − B; confine di separazione 3,97°);
- confronto appaiato sinottica/full-disk contro MWO sugli stessi gruppi, a entrambe le soglie.

Li riproduce `scripts/mdi_pilot_l2_report_numbers.py`. Lo script:
- è di sola lettura;
- unisce i file L1 e L2 della stessa soglia una a una e verifica che il record MWO sia lo stesso;
- stampa tutti i valori citati.

Non è codice di analisi preregistrato e non fa parte del riconteggio 10/10.

## Cosa dice per i due obiettivi

- **Quenching (T3):**
  - **Prodotto per il catalogo (Q2 precede la scelta del metodo):**
    - nel campione le mediane delle differenze Q2 sono circa entro 1°;
    - la mediana di |d_ax| è 1,4° a 50 G, con 90° percentile 17,5°;
    - la mediana della differenza d_γ sinottica − full-disk è −0,6° a 50 G e −1,0° a 100 G, con intervalli nominali
      non validati che escludono zero: da considerare nella scelta del metodo.
  - **Resa:** le sinottiche hanno resa proiettata del 92,8 %, i full-disk del giorno DPD con la geometria congelata
    del 47 %.
  - Il pilota non dice quale prodotto sia più vicino al tilt vero.
  - **Ripetibilità:** nelle 58 coppie (|Δt| 1,6–3,2 h) la mediana di |d_ax| è 0,7°; combina evoluzione ed errori
    eventualmente correlati. Q4 potrà usarla come informazione già nota, non come errore di misura.
  - **Scarto con MWO:** sui 49 gruppi comuni a 50 G, le mediane di |d_ax| sono 6,8° per full-disk e 7,1° per
    sinottica. Il confronto è descrittivo e non identifica l'origine degli scarti né esclude un contributo della
    composizione sinottica.
- **Sorgente BL:**
  - sul campione Q2 a 50 G, la mediana del rapporto sin/fd è 0,870, equivalente a una mediana fd/sin di circa 1,149;
    non è una calibrazione;
  - l'ampio rapporto di flusso rispetto a MWO è presente con entrambi i prodotti MDI (mediane 14,7 e 18,0 sugli
    stessi gruppi).
  - Un'unione diretta con MWO richiede ancora una specifica propria.
- **Restano rinviati:** Q4 (nota prospettica separata, che dovrà dichiarare quali risultati del pilota sono già
  noti), BARD-MDI e la serie BL combinata.

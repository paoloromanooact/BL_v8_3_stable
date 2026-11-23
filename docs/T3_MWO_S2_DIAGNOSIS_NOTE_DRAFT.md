# T3 su MWO R4 — diagnosi descrittiva di S2 (bozza della nota, da rivedere prima dell'esecuzione)

**BOZZA, 23 novembre 2026 (Claude). Non eseguita.**
- È una diagnosi **successiva alla lettura** degli esiti di stabilità e della stima. Non è cieca e lo dichiara.
- Non è un emendamento del protocollo: non cambia S2, la regola, l'esito «descrittivo» di β₃ né alcuna soglia.
- Nessun verdetto, nessun nuovo criterio di accettazione, nessuna simulazione lunga.

## Scopo

Documentare **l'eterogeneità** della pendenza dello scarto MWO − luce bianca contro l'attività:
- S2 = −3,18, intervallo nominale 97,5 % [−8,77, +2,40];
- n = 4694, margine C = 0,530.

Le domande sono tre:
- da quali sottoinsiemi viene;
- se viene dai tilt MWO o da quelli in luce bianca;
- se dipende da pochi record con differenze grandi.

La nota **non promette** di identificarne la causa né di recuperare un verdetto. Ogni risultato resta descrittivo e
condizionato alle scelte elencate qui, tutte fissate prima di esaminare i sottoinsiemi.

## Dati

- Sottoinsieme di S2: i 4694 record isolati con `wl_status == ok`.
  - Fonti: `results/T3_MWO_STABILITY_R4/WL_TILTS.csv` (d_WL, γ_WL), il DESIGN di R4 e la tabella isolata del rilascio
    verificato (γ_MWO, separazione, flusso).
  - Nessuna nuova lettura di SEALED: i tilt sono già nel rilascio verificato.
- Fonte DPD per record: dal file giornaliero già usato in `scripts/t3_mwo_stability_extras.py`.
- Hash di tutti gli input registrati nel META.

## Analisi fissate (tutte riportate, qualunque sia l'esito)

Il modello e la procedura sono quelli di S2: `s2_fit`, stessi termini, stessi pesi Φ_MWO, procedura M, intervallo
nominale 97,5 %.
- Un sottoinsieme con meno di **300 record**, o non identificabile, riceve solo i riassunti per terzile (D5), con lo
  stato dichiarato.
- Gli intervalli dei sottoinsiemi **non sono validati** e non vanno letti come test.
- Le pendenze dei sottoinsiemi non sono indipendenti fra loro.

**D1. Scomposizione MWO / luce bianca.** La stima puntuale di M è lineare nella risposta (β = g·y con la riga WLS del
disegno ridotto). Sullo stesso sottoinsieme e con lo stesso disegno, quindi, β(d_WL) = β(γ_MWO) − β(γ_WL) quando
d_WL = γ_MWO − γ_WL senza riavvolgimento assiale. Si riportano:
- β(γ_MWO) e β(γ_WL) sui 4694 record, ciascuno con SE e intervallo di M;
- la quota di record con riavvolgimento assiale (|γ_MWO − γ_WL| > 90°);
- il residuo della scomposizione dovuto al riavvolgimento.

β(γ_WL) è una pendenza di Joy con l'attività **in luce bianca**, sullo stesso disegno. È descrittiva e non è un
test T3 in luce bianca: la validazione MWO non la copre.

**D2. Una epoca esclusa alla volta.** S2 rifatto escludendo, una per volta, ciascuna delle epoche E2–E6 ed E8. Le
epoche non verificabili E1 ed E7 restano incluse, come in S2. Sono 6 stime.

**D3. Fonte DPD.** S2 su due sottoinsiemi:
- record da Gyula;
- record da tutte le altre fonti.

**D4. Caratteristiche delle regioni.** S2 per terzile, con i terzili calcolati sui 4694 record, di:
- (a) area DPD;
- (b) flusso nella finestra Φ_MWO;
- (c) separazione delle due polarità.

Sono 9 stime.

**D5. Riassunti per terzile di attività (A_main).** Per tutto il sottoinsieme e per ciascun gruppo di D2–D4:
- mediana e media pesata di d_WL;
- quota di record con |d_WL| > 45°;
- intervallo bootstrap percentile al 95 % a blocchi di 6 CR (2000 repliche, seme **69 600 001**, da verificare
  contro i semi già usati: griglia 60 000 000 + 100 000·c + k con c < 90, S1 69 000 001, Joy 69 500 001).

**D6. Peso dei record con differenze grandi.** S2 rifatto escludendo i record con |d_WL| > 45°, con il loro numero
per terzile di attività. Soglia fissata ora. È una sensibilità diagnostica, non una nuova regola di selezione.

**D7. Persistenza del modello.** Parametri di M (φ, κ, σ²ₓ, componenti individuali) e stato del bordo REML per ogni
stima. Non se ne trae alcuna conclusione sulla causa: φ al bordo descrive il modello stimato.

## Lettura prevista (fissata ora)

- Per ogni stima si riportano β, SE, intervallo e n, più due flag descrittivi: l'intervallo contiene zero o no; la
  stima puntuale è dentro [−C, +C] o no. Nessun gruppo viene promosso a «scarto contenuto».
- Le frasi ammesse sono descrittive, per esempio: «la pendenza si riduce/resta simile escludendo E5», «la componente
  MWO e quella in luce bianca hanno stima puntuale …».
- Non sono ammesse attribuzioni causali («è dovuto a SOHO», «è uno strumento») né correzioni di β₃.
- **Esito della nota**, una delle tre frasi:
  1. **eterogeneità localizzata:** escludere una singola epoca, fonte o terzile cambia la stima puntuale di S2 di più
     di **una SE** di S2 (2,49);
  2. **eterogeneità diffusa:** nessuna singola esclusione la cambia di più di una SE;
  3. **non valutabile:** troppi sottoinsiemi sotto 300 record o non identificabili.

  La soglia di una SE è operativa e fissata ora; non è un criterio inferenziale.
- Un eventuale problema correggibile (per esempio un errore di misura in un'epoca) richiederebbe un nuovo protocollo,
  congelato prima e validato separatamente. Questa nota non lo applica.

## Codice e controlli

- `scripts/t3_mwo_s2_diagnosis.py`, scritto dopo la revisione di questa nota.
  - Usa le funzioni congelate di `t3_mwo_analysis.py` (`s2_fit`, `columns`, `reduce`) senza modificarle.
  - Selftest su dati sintetici: scomposizione D1 esatta senza riavvolgimento; rifiuto di sovrascrivere; seme;
    sottoinsiemi sotto soglia.
- Uscite in `results/T3_MWO_S2_DIAGNOSIS_R4/`, conservate in Git prima della lettura.
- Riconteggio indipendente almeno di D1 e D2, con codice proprio per la riga WLS. Il calcolo M di riferimento può
  essere richiamato.
- Durata attesa: qualche minuto (circa 20 fit di M e 2000 repliche bootstrap di medie).

## Questioni per Codex

1. D1 è ammissibile come descrittiva, o la pendenza in luce bianca va tenuta fuori perché somiglia a un nuovo test T3?
2. La soglia di 300 record e quella di |d_WL| > 45° (D6).
3. La regola di esito basata su una SE di S2.

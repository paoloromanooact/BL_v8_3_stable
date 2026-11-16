# HMI: che cosa è stato misurato, che cosa si sa sul quenching, che cosa resta aperto

2026-11-13, aggiornata il 2026-11-15 (T5-D2) e **consolidata il 2026-11-16** dopo la chiusura della fase
diagnostica di T5. Sintesi interna di risultati esistenti; nessuna nuova misura, selezione o applicazione ai dati
reali. Ogni numero ha un documento di origine, indicato nel testo.

Domanda del progetto: all'aumentare dell'attività, la sorgente Babcock–Leighton si autolimita attraverso il tilt,
la latitudine o l'efficienza per unità di flusso? **Risposta attuale: non conclusiva.** Non è dimostrata né la
presenza né l'assenza del quenching nei dati HMI.

## 1. Che cosa misura il proxy

Catalogo HMI 2010-05 → 2026-09 ([misura](HMI_MEASUREMENT_ASSESSMENT.md)): 14 195 record selezionati, 7133 HARP,
di cui 4189 con primario valido nella base del controllo delle dominanti. P1 misura ogni HARP a un record vicino
al meridiano centrale, non necessariamente all'emersione. Le grandezze:

| Quantità | Significato | Limite |
|---|---|---|
| S_BL = hale_sign · Φ · d · cos λ · sin α | proxy geometrico della sorgente, da due centroidi e una convenzione di Hale | in una HARP complessa l'asse può collegare medie di più concentrazioni |
| D = 3/(4πR²) Σ Br sin λ dA | contributo al dipolo assiale dei pixel selezionati | risente dello sbilancio di flusso della patch |
| D_bal | momento bilanciato, senza il termine di monopolo; base di D* e dell'efficienza η = ΣD*/ΣΦ di T5 | nessuna delle tre misura il campo polare che sopravviverà al trasporto |

Controlli della misura già fatti: valori P1 riprodotti dai FITS entro la precisione macchina sulle 120 HARP del
controllo dominanti; confronto con BARD (999 abbinamenti, rapporto dei flussi circa 1,67; con BARD-MDI nella
sovrapposizione 68 abbinamenti in 62 famiglie, scarto mediano del tilt 2,1°, rapporto dei flussi 1,17): accordo
di geometria e convenzioni, non calibrazione dell'ampiezza; varianti di maschera e pesatura con effetti netti
piccoli ma compensazioni interne non trascurabili (in 25S la variante bitmap ≥ 1 sposta la somma dello 0,09 % e
la somma dei moduli delle variazioni del 13,1 %); riproducibilità di fase 1 superata, condizionata agli input
distribuiti.

**Lettura morfologica.** Il [controllo morfologico](MORPHOLOGY_RESULTS.md) ha classificato 90 HARP nuove (più 30
storiche) in classi A (coppia dominante), B (più concentrazioni comparabili), D (diffusa o sbilanciata), U; due
lettori, accordo 24/30 sulle doppie letture, esattamente alla soglia operativa. Le HARP di classe B portano l'8,1 %,
il 15,2 % e il 16,2 % di Σ|S_BL| nei tre gruppi esaminati. Conseguenza per l'interpretazione: nei complessi
magnetici il proxy rappresenta il **contributo netto della HARP**; leggerlo come il tilt di un singolo bipolo
richiede cautela. Le quote riguardano i casi esaminati, non la prevalenza in tutta la serie; lo studio
rappresentativo su S è in bozza e in pausa ([piano](PROTOCOL_HMI_MORPHOLOGY_S_DRAFT.md)). Nessuna HARP è esclusa
e nessun test è rilanciato in base alle classi.

Per T5 il proxy compatto a coppia riproduce D* al livello osservato (Pearson 0,990 per record, 0,995 per cella,
[sensibilità del proxy](T5_PROXY_SENSITIVITY_RESULTS.md)); una riduzione prescritta del 10 % e del 20 % della
componente di Joy si traduce in pendenze T5 di −0,0515·η̄ e −0,1031·η̄ per unità di attività, con una parte del
segnale (rapporto delle RMS 0,55) fuori dal modello lineare.

## 2. Risultati sul quenching

| Domanda | Risultato | Conclusione consentita |
|---|---|---|
| Il tilt segue la legge di Joy? | coefficiente complessivo circa 24,1° (controllo P2 T1) | la relazione media è presente; non dimostra quenching |
| Il coefficiente di Joy diminuisce con l'attività dentro il ciclo? **T3** | procedura M validata negli scenari provati e applicata una volta: β̂_T = −3,59° per unità di Â (−0,149·γ₀), intervallo nominale 97,5 % [−10,58°; +3,41°] ([−0,44; +0,14]·γ₀); 2485 record, 394 celle | **non deciso**: l'intervallo comprende zero e tutti gli effetti negativi della griglia pre-registrata |
| La latitudine cresce con l'attività, a pari fase? T4 | pendenza descrittiva −0,63° per unità di Â, verso opposto alla previsione | nessun verdetto: intervallo storico senza copertura garantita |
| L'efficienza η diminuisce con l'attività? **T5** | stima storica circa −0,04·η̄, incerta; M non supera la validazione nello scenario a salti | **descrittivo; sviluppo operativo rinviato** (§3) |

T3 misura la variazione del coefficiente di Joy **dentro** i cicli 24 e 25, con intercetti separati per ciclo ed
emisfero: non è la relazione fra ampiezze di cicli diversi. La stima puntuale è negativa, nel verso del quenching,
ma la sua incertezza la rende compatibile anche con l'assenza di effetto. Le otto sensibilità (tutte negative,
tutti gli intervalli comprendenti zero) sono correlate e non validate: non sono conferme indipendenti. Fonti:
[P2 storico](P2_RESULTS_DESCRIPTIVE.md), [T3](P2F_RESULTS.md), [validazione](P2F_VALIDATION_RESULTS.md).

## 3. T5: che cosa hanno chiarito le diagnosi e perché è rinviato

1. **Validazione P2f**: T5 fallisce lo scenario a salti di livello (3,35 % di falsi verdetti contro il limite del
   3 %; a −0,3·η̄ copertura 96,1 % contro 96,5 %).
2. **T5-D1 e T5-D2** ([risultati](T5_DIAGNOSTIC_RESULTS.md), [oracolo](T5_ORACLE_RESULTS.md)): nei salti di 20 CR
   la varianza stimata è troppo piccola (R ≈ 0,86); con la componente temporale vera R ≈ 0,98 e falsi verdetti
   1,9 %. Esito compatibile con un ruolo principale del modello temporale AR(1) e della sua stima REML, senza una
   causa unica identificata.
3. **Sensibilità della potenza** ([risultati](T5_POWER_SENSITIVITY_RESULTS.md)): 9000 cataloghi di rumore di base,
   cinque segnali e quattro metodi (M; G, una GLS stimata; B, un bootstrap a cluster; O, la stessa WLS con la
   varianza vera), 3 forme × 3 scale di rumore temporale. Negli scenari provati **M rileva raramente la riduzione
   prescritta**: per la riduzione del 20 % circa 18–19 volte su 100 a metà della scala di rumore di P2f, 8–11 alla
   scala di P2f, 4–5 alla scala doppia; per il 10 % al più 7. La forma realistica del segnale non penalizza M; la
   scala del rumore temporale pesa molto. La bassa frequenza persiste con la varianza vera della stessa WLS (O): non
   è un problema di stima della varianza. G e B riconoscono più spesso ma con falsi verdetti in eccesso in diverse
   configurazioni (B fino al 12 %), e senza un confronto a pari livello effettivo non c'è una graduatoria dei
   metodi. Stimatori diversi dalla WLS non sono stati esplorati.
4. **Decisione (2026-11-16, esito ii del piano)**: sviluppo operativo di T5 rinviato, senza altri tentativi; tutti
   gli output conservati. Il rinvio è una scelta di priorità: non dimostra che T5 sia irrisolvibile con HMI né che
   l'efficienza sia costante.

## 4. Che cosa non occorre ripetere

Sensibilità P2f (filtro «una NOAA», altre sette varianti), ricomparse candidate (P1e/S8), confronto
primario–controllo, HARP dominanti e letture 25S: i quadri esistono e i loro limiti sono documentati
([sensibilità](SENSITIVITY_SUMMARY.md), [dominanti](DOMINANT_HARP_RESULTS.md)). Rilanciare T3 su sottocampioni
morfologici o con varianti non validate produrrebbe stime correlate, non evidenza nuova.

## 5. Che cosa è aperto e sequenza decisa

La parte aperta è **un'inferenza conclusiva sul quenching**. Due strade, nessuna con esito garantito:
- **più informazione** con l'estensione MDI/SMARP al ciclo 23 ([fattibilità](MDI_SMARP_FEASIBILITY.md),
  [piano dell'inventario](MDI_SMARP_METADATA_INVENTORY_PLAN.md) congelato, raccoglitore scritto e provato
  offline; prima acquisizione dello schema bloccata da un errore TLS, lavoro fermo): la confrontabilità fra
  strumenti e il beneficio per T3 non sono quantificati, e aggiungere anni non garantisce informazione utile;
- **una procedura HMI diversa** (altro stimatore o altra statistica per T5, o uno sviluppo per T3), che
  richiederebbe protocollo e validazione propri con semi nuovi, scenario a salti compreso.

Sequenza concordata con il revisore: (1) questa sintesi; (2) **bozza di un piano prospettico**, da rivedere prima
dei calcoli, che stimi quante osservazioni solari aggiuntive (regioni, rotazioni, anni) servirebbero per rendere
distinguibile la riduzione prescritta del 20 % (pendenza T5 di circa −0,103·η̄, non −0,2·η̄), partendo da una stima
analitica orientativa e poi dalle simulazioni necessarie, con un'incertezza fra strumenti che possa dipendere da
attività e tempo (uno scarto strumentale può imitare il quenching) e con il 50 % come obiettivo operativo da
motivare, non come garanzia che un mancato rilevamento diventi informativo; (3) solo dopo, la scelta
dell'investimento. Un guadagno insufficiente per T5 non escluderebbe da solo l'utilità di MDI per T3 o per il
catalogo descrittivo. MDI operativo e morfologia di S restano in pausa.

Il risultato T3, il catalogo P1 e i controlli della misura restano i riferimenti acquisiti.

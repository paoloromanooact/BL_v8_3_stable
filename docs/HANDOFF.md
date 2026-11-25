# Cold restart — SHARP BL

## BQ rev.4, C rev.3 e riferimento matematico (Codex)

- [Risposta a Claude e prove](BQ_REV4_C_REPLY_AND_ORACLE_20261125.md): accolti 5aabb2d e 527b63e con precisazioni. BQ rev.4: scale v 5/20, L3 ripiegata predefinita con rami discreti/alias/coda da verificare, singleton integrati con modello corretto, slice da implementare e provare. Nessun fit.
- C rev.3: rischio di sottostima a giorni, fattori 0,5/1/2/4 non garantiti, due lag e secondo momento, rotazione secondaria su supporto comune, terzili USFLUX di metadati con mancanti espliciti, confronto di rappresentativita. Disponibilita e semi da chiudere prima del congelamento; nessun pixel o sigma misurata.
- `scripts/bq_gaussian_math_oracle.py`: 14/14 identita/controesempi sintetici deterministici, input e codice produttivi non importati. Covarianze, singleton, Woodbury/denso, Savage-Dickey, predizione a blocchi, densita ripiegata e rischio breve/giorni. Non e validazione MCMC.
- Conteggi/benchmark di Claude accolti come preparatori, non risultati posteriori; blocco 8 estrapola in attivita e il costo totale BQ non e stimato dal solo caso base.
- Claude rivede entrambe le bozze; A1 e i suoi script non modificati da questa consegna. C in parallelo, BQ-M dopo BQ; nests sospesi.


## Revisione incrociata BQ rev.3 e A1 ccd49f9 (Codex)

- [Revisione e consegna a Claude](BQ_A1_CROSS_REVIEW_20261125.md): otto punti BQ recepiti con correzioni; bozza rev.3 non congelata. Blocchi interni principali, previsione in avanti separata, sensibilita Joy temporale, L1/L2 t4 con SD coerente, prior e prove ancora da finalizzare. Nessun fit.
- A1 non ancora congelabile: scarto fra griglie non e errore garantito; formula del rapporto al primo ordine insufficiente. Bound finito e controesempio documentati. f=1e-2 accettabile come tolleranza di scarto solo con regola numerica esplicita delle grandezze derivate; nessun allargamento automatico a 1e-1.
- Proposta: controlli N/2N/4N e passo su tutti i rapporti destinati ai riepiloghi, stato/eleggibilita stabili e differenze <=0,01; m(t) verificato con la stessa popolazione, denominatori e quote di irrisolti. Da recepire e rivedere nel testo e nel codice, non una corsa approvata.
- Sei controlli algebrici deterministici conservati, non validazione PDE o bayesiana. Riconteggio SFT finale/selftest da consegnare: questa revisione non dichiara i cinque gruppi del codice integralmente chiusi.
- BQ al primo posto, C attivo in parallelo, BQ-M successivo. Nests sospesi; nessuna serie SINDy coinvolta.


## BIC aggiunto alla bozza BQ (prima dei fit)

- [BQ rev.2, §6bis](PROTOCOL_BQ_HMI_DRAFT.md): BIC come controllo secondario, non conversione dei risultati REML storici. ML marginale rispetto ai latenti, effetti fissi massimizzati, conteggio nominale dei parametri e asintotica da giustificare.
- Proposta gaussiana attuale: k0=10, kQ=11 se tutti i parametri sono identificabili; gli stati CR/famiglia integrati non si contano come singoli parametri liberi. Bordi/identificabilita e ottimizzazione devono essere verificati.
- Non approvata la proposta di due BIC validati ottenuti cambiando solo n (regioni/CR). Eventuali due formule sono sensibilita euristica della penalizzazione se manca una derivazione applicabile. Nessun valore BIC reale calcolato.
- Predizione, Bayes factor espliciti e BIC hanno condizioni/obiettivi diversi: riportare e spiegare eventuali discordanze, senza imporre un vincitore o attribuirle automaticamente a poca informazione.
- Nests sospesi; BQ-HMI prioritario e C attivo. Claude rivede la bozza prima del codice e del congelamento.


## Consegna Codex: BQ-HMI, specifica C e nests sospesi

**Decisioni correnti dell'utente:** BQ-HMI al primo posto, BQ-M dopo; C attivo e SFT continua a preparare BT.
**Nests in lista ma fermi:** nessuna identificazione, analisi o acquisizione AIA/Solar Orbiter finche l'utente
non riattiva questa voce. Non leggere «alla fine del piano» come avvio automatico.

- [BQ-HMI, bozza rev.1](PROTOCOL_BQ_HMI_DRAFT.md): stesso campione T3, risposta P2 esatta, M0/MQ, dipendenze temporali/famiglie, prior proprie proposte, bersaglio e verifica predittiva. Prima del congelamento chiudere likelihood angolare, prior/diagnostica, ambiente e semi. Nessun fit reale.
- [C, specifica rev.2](SFT_HMI_REPEATABILITY_PLAN_DRAFT.md): selezione, grafo transitivo di separazione dal bacino osservativo, dominio finito, misure, statistiche angolari e ricampionamento per gruppi. La riserva 86/84 e disponibilita, non numerosita finale. Da rivedere e congelare; runner/riconteggio di misura ancora da scrivere. **Nessuna sigma osservativa ancora misurata.**
- [A1, nota numerica preliminare](SFT_A1_WORKING_TOLERANCE_REVIEW_20261125.md): f=1e-2 non garantisce accuratezza dei rapporti vicino a zero; controesempio 0→0,45 pur passando il criterio. Non approvato automaticamente f=1e-1; precisare requisito per le quantita derivate e attendere il commit definitivo per la chiusura.
- `scripts/bq_c_math_reference.py`: 18/18 controlli algebrici su sintetici deterministici, conservati in `reviews/C_BQ_PREPARATION_20261125/`. Sono riferimenti/casi avversi, non validazione di un fit o di una misura osservata.
- BQ-M: DPD e un ponte relativo, non identifica automaticamente la deriva assoluta di MWO. Ore/prodotti diversi richiedono un modello della misura e dell'evoluzione; dettagli nella bozza BQ §8. L'inventario delle sovrapposizioni resta affidato a Claude.
- `BL_WORK_PLAN.md` era in modifica da Claude: Codex non l'ha toccato o incluso nel commit. Allineare l'ordine corrente, lo stato sospeso N e queste consegne quando si chiude quella modifica. Codex non ha toccato i due script SFT in lavorazione.


## Consegna Codex: nests HMI, Finley e bozza bayesiana

- [Inventario](HMI_NESTS_FEASIBILITY.md) concluso: 197 CSV, 1300060 record canonici, 8296 HARP; 7133 con primario P1. 1800 righe ai confini mensili rendicontate; nessun nuovo tilt/flusso misurato letto o nest classificato. Script e input con SHA; selftest 7/7.
- [Note Finley](HMI_NESTS_FINLEY_METHOD_NOTES.md): letti i lavori 2025 (arXiv 2504.06345v2) e 2026 (2608.26315v1), piu Norton (2511.03646v2). AIA 304 Å, EUI e PHI annotati su richiesta dell'utente per un futuro studio di continuita; nessuna acquisizione. AIA terrestre da sola non risolve il lato nascosto.
- [Bozza N/bayesiana](PROTOCOL_HMI_NESTS_BAYES_DRAFT.md) rev.1: identita, candidati contro nests documentati, controlli di associazione, contributi BL senza doppi conteggi e proposta M0/MQ/MN/MQN con/senza attivita e dipendenza dal nest. Soglie/prior/semi non ancora congelati; nessun clustering o fit reale.
- Claude continua A1 e le correzioni SFT; rivede questa consegna senza duplicare l'inventario. Il reperimento di AIA/Solar Orbiter e il ranking richiedono specifiche distinte dai piloti gia congelati.


## Aggiunta dell'utente: active-region nests HMI, poi analisi bayesiana

- Nuova voce **N** nel [piano comune](BL_WORK_PLAN.md): identificare nests candidati, distinguendo nuove emersioni, ricomparse e HARP complesse; poi caratterizzazione della sorgente BL e integrazione bayesiana in BQ/BT.
- Codex prepara inventario mirato e specifica; Claude continua A1 e le correzioni dei piloti SFT. Non duplicare le attivita e non modificare protocolli congelati per introdurre i nests.
- Prima della nuova inferenza: controlli dell'associazione, classificazioni ambigue, dipendenze fra membri e separazione dei gruppi fra sviluppo/calibrazione e verifica. L'audit della ripetibilita non ha ancora verificato legami di nesting.
- Nessun nest gia classificato, nessuna nuova misura o corsa bayesiana eseguita con questo aggiornamento.


## Decisione aggiornata dell'utente: §7 da svolgere per l'analisi bayesiana

- Superata la proposta di rinviare la ripetibilita dichiarando l'errore non stimato. Il lavoro e **attivo**; Codex ha eseguito l'audit preliminare dai soli metadati, lasciando Claude su A1 e le correzioni del punto 2 mappa-bipolo.
- [Consegna](SFT_HMI_REPEATABILITY_METADATA_20261125.md): 299 coppie nominali diventano 296/294 HARP usando T_OBS; tre durano 7201 s. Riserva cautelativa di **86 coppie/84 HARP** con area C almeno 25 deg², esclusi intero bacino osservativo, famiglie note e possibili sovrapposizioni. Audit, manifesti e selftest 9/9 conservati; nessun pixel magnetico letto.
- [Specifica di misura in bozza](SFT_HMI_REPEATABILITY_PLAN_DRAFT.md): completare, rivedere e congelare prima dei pixel; poi misura e riconteggio. La sigma non e ancora stimata. Ripetibilita include evoluzione ed errori correlati e non determina da sola l'errore strumentale o la discrepanza del trasporto.
- Recepire il controllo nel §7 della bozza osservativa prima del congelamento. Per il ranking BT restano da fissare likelihood, prior e verifica; nessun ranking o pilota osservato e stato lanciato.


## Stato precedente, superato dalla decisione sopra: punto 3 §7 in pausa

- Il controllo di ripetibilità del §7 del punto 3 è **in pausa** per decisione dell'utente; di conseguenza il congelamento del punto 3 resta sospeso (bozza rev. 4, geometria confermata da Codex). Runner preparatorio `scripts/sft_observed_pilot.py` (865e6b4, 8/8 sintetico) non eseguibile sui dati.
- Lavoro corrente di Claude: punto 2, emendamento numerico A1 (schema ibrido) e correzioni dei cinque gruppi della revisione `SFT_Q4_EVENING_REVIEW_20261125.md`.

## Nuove voci approvate dall'utente — ranking bayesiano HMI (25 novembre)

- Aggiunte al [piano permanente](BL_WORK_PLAN.md) **BQ, quenching HMI**, e **BT, trasporto superficiale HMI**; specifiche da scrivere, nessun ranking calcolato.
- BQ: inizialmente T3 su HMI da solo, modello senza dipendenza dall'attivita contro pendenza libera; likelihood temporale, prior, adeguatezza, confronto predittivo ed eventuali Bayes factor da fissare. Analisi dichiaratamente non cieca rispetto ai risultati HMI gia noti.
- BT: persistenza, sola rotazione e SFT sulle stesse osservazioni successive; modello probabilistico degli errori e criteri congelati prima della lettura della verifica. Confronto mappa/bipolo distinto dal ranking dei trasporti.
- Codex prepara le specifiche metodologiche; Claude continua la chiusura dei piloti SFT, poi revisione incrociata. Nessuna modifica ai protocolli congelati; nessun fit, download o nuova corsa autorizzato dal solo aggiornamento del piano.


## Revisione Codex del pacchetto serale (25 novembre)

- [Revisione e compiti concreti](SFT_Q4_EVENING_REVIEW_20261125.md). Punto 2 **non ancora avviabile**: serve emendamento per il passaggio dall’upwind congelato all’ibrido; inoltre correggere schema completo del riconteggio, curve obbligatorie, conteggi esatti, gate della ricevuta e gestione della convergenza.
- Controprove sintetiche in `reviews/SFT_EVENING_20261125/`; nessuna mappa osservata letta. Core 28/28; cinque controlli difettosi riprodotti, non una certificazione della corsa.
- Punto 3: approvate le correzioni geometriche rev.4; prima del congelamento chiudere l’impegno del §7 sulla ripetibilità dai metadati o dichiarare esplicitamente la scala di errore non stimata. Codice da rivedere prima dei dati.
- Q4: integrità 9/9 e numeri principali confermati; formulazione corretta direttamente nel rapporto. Riduzione attesa condizionata delle semiampiezze, non intervalli validati già ottenuti; nessun rilancio.


## Stato al 25 novembre, sera (Claude da solo; Codex senza token)

- Punto 2 congelato (3637250, ricevuta e2e7176). Runner `scripts/sft_map_bipole_pilot.py` (12/12) e riconteggio `scripts/sft_map_bipole_pilot_recount.py` (10/10) su dati sintetici; nessuna corsa: serve la revisione del codice di Codex. Il §6 dice «upwind del primo ordine», il codice usa l'ibrido di Patankar (stesse garanzie, convergenza 6,5e-4 invece di 5,4e-3): da chiarire con Codex.
- Punto 3: bozza rev. 4 (247ff35) con fattibilità v2 (373 coppie; celle 22/19/174/158); in attesa di conferma e congelamento.
- Q4: rapporto `docs/MDI_PILOT_Q4_RESULTS.md` (6a90933) da rivedere nella formulazione.
- Richiesta unica per Codex: `PACCHETTO_PER_CODEX_20261125_SERA.txt` (radice del repo MWO).

> **PIANO PERMANENTE CODEX–CLAUDE: [BL_WORK_PLAN.md](BL_WORK_PLAN.md).**
> **Priorita 1:** mappa HMI contro bipolo del proxy, evoluti nello stesso SFT.
> **Priorita 2:** evoluzione simulata contro osservazioni successive indipendenti.
> **Voci pianificate BQ/BT:** ranking bayesiano HMI del quenching e del trasporto superficiale; specifiche prima dei calcoli e, per BT, prima della lettura della verifica.
> **Voce N:** nests HMI da identificare e verificare prima della relativa analisi bayesiana; distinti dalle ricomparse.
> Mantenere questo richiamo sopra la cronologia. Sono i punti 1 e 2 indicati
> dall'utente, non i passi del pilota MDI.


## Consegna autonoma Codex: oracoli e verifica Q4 (25 novembre)

- [Consegna completa](SFT_INDEPENDENT_CHECKS_20261125.md): riferimenti matematici SFT indipendenti, 20/20; tabelle rigenerate identiche due volte. Nessun solutore di Claude importato e nessuna mappa osservata letta.
- Q4: ricevuta 8924285 completa 21/21 verificata con ulteriori 9/9 controlli di integrita. Via alla lettura e al rapporto di Claude, poi revisione; nessun risultato numerico Q4 interpretato da Codex e nessun rilancio.
- Punto 2 rev.4 SHA 2f4deebb…: via al congelamento del testo; codice ancora da correggere/rivedere prima dei dati.
- Punto 3 rev.3: prima del congelamento correggere la fattibilita. 137/1023 coppie hanno CRVAL1 su rami diversi; riportare sullo stesso ramo. Coerenza dell'ordine di erosione/intersezione, metrica cos(lat) del margine longitudinale e bounding box contro vere impronte CEA da fissare; ricalcolare i conteggi.
- Verificati 2046 header, nessun pixel: le dimensioni inferite da CRPIX coincidono tutte con NAXIS. Claude corregge geometria e codice; Codex mantiene gli oracoli e rivede. Piloti non avviati.

## SFT preparatorio: revisione Codex di b3f1745/e317200/80b28a4 (25 novembre)

- [Revisione del codice](SFT_PREP_80b28a4_CODE_REVIEW.md): tre coerenze P1 riprodotte nel caso sintetico; non ancora via alle mappe osservate. Positivita, gaussiane/cuciture, tempi T_OBS e contratto delle misure da completare.
- Controprove con massa conservata ma polarita artificiali: 1D CN -0,277; 2D avvezione -0,012; 2D diffusione -0,305, da campi iniziali non negativi. Non riparare con clipping.
- Deposito misto: D esatto ma Phi per polarita scende da 1 a 0,5 e il centroide si sposta. L'identita P1 dei flussi non e generale: registrare/rifinire gli scarti di rimappatura, non forzare una riscalatura.
- Q4 **chiuso il via tecnico su d303c3a**, SHA a6c0a72d…: verificati codice corrispondente e log completo dell'autore 46/46, preservato con provenienza in reviews/MDI_Q4_RECOUNT_d303c3a_CODEX. Puo procedere il solo riconteggio reale, poi ricevuta prima della lettura; niente rilancio Q4. Nessun risultato scientifico Q4 letto da Codex.
- Bozze SFT da completare/congelare secondo e87fff7, poi revisione dei runner e riconteggi prima dei piloti. Nessun pixel osservato letto o download fatto nella revisione.

## SFT 790cad1: controllo finale e Q4 a6c0a72d… (25 novembre)

- [Revisione finale](SFT_790cad1_FINAL_REVIEW.md): correzioni scientifiche principali recepite; prima del congelamento fissare positività del solutore, dominio comune a tutta la griglia e split per componenti con sovrapposizione spazio-temporale.
- Prova sintetica CN: impulso positivo, N=400 e dt=1 giorno → minimo -0,277 nonostante massa conservata. Proposto sottopasso con vincolo di positività dell'operatore; nessuna evoluzione di dati reali.
- Margine a 15°/4,5 giorni: 4,628° nel riferimento, 4,813° nella sensibilità veloce; mantenere lo stesso C fra tutti i confronti e dichiarare il campo ignoto esterno. Verifica geometrica da header prima del congelamento.
- Q4: f0ab43a non conteneva gli ultimi due dettagli. La nuova fotografia SHA a6c0a72d… li chiude: base sintetica valida, sei mutazioni precedenti e cinque casi di dominio rifiutati. Via tecnico al solo riconteggio reale per QUESTO SHA, dopo commit e selftest completo conservato; se il codice cambia, rivedere la differenza. Nessuna corsa Q4 da rilanciare.
- Nessuna bozza modificata/congelata in questa revisione, nessun pixel osservato o risultato scientifico Q4 letto. Vecchie sezioni sotto sono la cronologia.

## Q4 — correzioni in lavorazione, verifica preliminare Codex (25 novembre)

- Fotografia non committata SHA 6024dc61…: base sintetica valida e sei controesempi precedenti ora rifiutati; gate corrente degli hash senza problemi.
- [Consegna preliminare](MDI_Q4_RECOUNT_WORKING_REVIEW.md): restano conteggi esatti anche nei riepiloghi/JSON e dominio della tolleranza con bersaglio nullo. Sonda specifica e fotografia patch conservate, nessuna modifica al file in lavorazione di Claude.
- Claude completa e committa; revisione sul commit definitivo prima del `--check` reale. Nessun risultato Q4 reale letto e nessuna nuova corsa. La sezione su 0344bc3 sotto e la revisione precedente.

## Q4 — revisione Codex del riconteggio 0344bc3 (25 novembre)

- Non ancora via al `--check` reale: [rilievi e controprove](MDI_Q4_RECOUNT_REVIEW_0344bc3.md).
- Base sintetica con due realizzazioni accettata; sei alterazioni dei prodotti passano impropriamente. Da correggere: tolleranze protette, tabelle/etichette/scelte complete, conteggi esatti e gate dei file correnti.
- Claude corregge il riconteggio e aggiunge le regressioni; Codex rivede la chiusura. Runner, protocolli e output reali invariati; nessun risultato Q4 letto. Non rilanciare Q4.

## SFT mappa–bipolo: revisione Codex di fa3f08d (25 novembre)

- Impostazione 1D approvata, bozza non ancora congelabile: [revisione e decisioni sui nove punti](SFT_MAP_BIPOLE_DRAFT_REVIEW_fa3f08d.md).
- Tre correzioni provate sui sintetici: formula S_BL→D (fattore e segno), deposito conservativo del dipolo iniziale, gaussiane sovrapposte (flussi/centroidi non conservati automaticamente).
- Proposti bipolo puntiforme principale, gaussiane come sensibilita; trasporto Yeates 2020 esplicito con scenari fissati; nessuna soglia di adeguatezza al 20 %.
- Claude recepisce le scelte prima del congelamento. Nessun pixel osservato o simulazione SFT eseguita nella revisione. Punto 3 in revisione separata, con scelte comuni da raccordare.

## SFT evoluzione osservata: revisione Codex di e0bba64 (25 novembre)

- Bozza non congelabile: [correzioni e decisioni sugli otto punti](SFT_OBSERVED_DRAFT_REVIEW_e0bba64.md).
- Metadati: 7133/7133 controlli con USFLUX almeno pari al primario; lo strato «calo >20%» e impossibile con endpoint al massimo. Riformulare celle e popolazione.
- Da rendere coerenti: campo iniziale/target bilanciato o grezzo, dominio comune di valutazione, maschere e soglie, sistema Carrington e margine dai bordi. I residui non separano causalmente trasporto ed emergenza.
- Raccordo finale dei parametri fra i due piloti: riferimento pre-HMI eta 466,8 km²/s, Du 0,025 km/s, p 2,33; set 350/0,041 e incroci come sensibilita dichiarate. Aggiornata anche la sola raccomandazione del riferimento nella revisione del punto 2, che non e un protocollo congelato.
- Disponibilita nominale di 299 coppie entro 2 h in 296 HARP; e fattibilita da nomi/T_REC, non stima del rumore osservativo.
- Claude aggiorna entrambe le bozze; poi controllo breve e congelamento prima del codice. Solo metadati e casi sintetici verificati, nessuna mappa reale letta o evoluzione SFT eseguita. Q4 resta separato.

## Lista dell'utente (25 novembre 2026), nell'ordine

1. Inventario SFT e dati HMI disponibili. Completato da Codex su richiesta dell’utente; consegna e limiti in `docs/BL_SFT_HMI_INVENTORY.md`. Claude usa questa consegna per i punti 2 e 3.
2. Protocollo del pilota mappa–bipolo — prima priorità. Campione, costruzione del bipolo, trattamento del flusso preesistente e delle ricomparse, parametri di trasporto e tempi di confronto. Claude scrive la bozza, Codex la rivede.
3. Protocollo del confronto con l'evoluzione osservata — seconda priorità. Osservabili, intervalli temporali e separazione fra dati di sviluppo e verifica; procede insieme al punto 2.
4. Codice e prove indipendenti. Claude implementa; Codex controlla formule, unità, segni, bilancio del flusso e casi sintetici. Protocolli congelati prima delle corse.
5. Esecuzione dei due piloti. Prima conservazione degli output, poi riconteggio e lettura. Due rapporti distinti: approssimazione bipolare nel modello e accordo con il Sole osservato.
6. Chiudere Q4 MDI, su una linea separata. La corsa è già conservata: servono revisione del riconteggio, verifica e rapporto. Poi la decisione sul catalogo MDI completo per T3. Non va rilanciata.

Dettagli e divisione dei compiti: `docs/BL_WORK_PLAN.md`.

Stato al 25 novembre: punto 1 chiuso da Codex (8b2efcd, `docs/BL_SFT_HMI_INVENTORY.md`); punto 2, bozza rev. 3 (`docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_DRAFT.md`) dopo la revisione Codex 9aa3fce; punto 3, bozza rev. 2 (`docs/PROTOCOL_SFT_OBSERVED_EVOLUTION_DRAFT.md`) dopo la revisione Codex 7f5d703; entrambe in attesa del controllo finale prima del congelamento; punto 6, riconteggio Q4 0344bc3 in attesa di revisione (`MDI_Q4_RICONTEGGIO_PER_CODEX.txt`).

## MDI Q4 — corsa unica eseguita; riconteggio indipendente scritto (25 novembre 2026)

- Corsa autorizzata dall'utente dopo la chiusura Codex di fed1775. Eseguita su 1c25c2e pulito, uscita 0, ~11 min; selftest interno 55/55. Output e log conservati prima della lettura in dab5a33 (`results/MDI_Q4_PROSPECTIVE/`, con `RUN.log` e `RUN.exit`). Risultati NON ancora letti.
- `scripts/mdi_q4_recount.py` (selftest 24/24):
  - non importa il runner;
  - codice proprio per calendario, SILSO, filtri, rese, pool, donatori L-NN, numeri casuali, matrice e rango, riga WLS via QR, covarianze AR(1) e a gradini, bersagli, scarti, frequenze, SUMMARY, CRITERIA, DESIGNS, YIELD_EFFECTS, CELL_COUNTS, MF_POOLS;
  - dipendenze dichiarate: record HMI di E0 (`load_inputs`/`e0_records` della fase A) e regola delle rotazioni e delle mappe richieste.
- Rilievo emerso: nei modelli protetti B1 della propria famiglia è zero per costruzione (bA→A, bJ→J), quindi `tol_units_{fam}_*` è rumore numerico di grandezza arbitraria. Il riconteggio verifica B1 trascurabile e confronta quelle tolleranze come illimitate. Nel rapporto non vanno lette.
- Controlli preliminari del percorso reale in prova a secco: 6/6. Prossimo passo: revisione Codex del riconteggio, poi `--check`, ricevuta, lettura e rapporto.

## Inventario SFT/HMI completato da Codex — 25 novembre 2026

- Su richiesta dell'utente il punto operativo 1 e stato svolto da Codex: `docs/BL_SFT_HMI_INVENTORY.md`, fotografie in `docs/BL_SFT_INVENTORY/`, script `scripts/bl_sft_local_inventory.py`.
- Dati P1 presenti per 14195/14195 record: Br, bitmap e keys.json. 2836 HARP hanno il controllo successivo al primario; sono disponibilita, non un campione validato di evoluzione.
- Codici esterni con commit/licenza verificati: sharps-bmrs (Python SFT1, GPL-3.0), sft-historical (Fortran 1D, BSD-2-Clause), HipFT (2D, Apache-2.0). Nessuna installazione o esecuzione esterna.
- Distinguere 1D per D(t) sotto ipotesi assialsimmetriche da 2D per la mappa locale; la pipeline esterna completa non sostituisce P1.
- **Prossimo compito di Claude:** bozze delle due specifiche del piano, usando l'inventario; non rifarlo da zero. **Codex:** revisione indipendente delle specifiche e dei test. Il riconteggio Q4 resta lavoro separato di Claude, non toccato.
- Nessun pixel FITS o tilt letto, nessuna simulazione, nuovo download scientifico o lettura dei risultati Q4.

## Stato operativo, 25 novembre 2026

- L'utente ha chiesto che i due controlli della sorgente BL restino in primo piano per entrambi gli agenti.
- Piano comune e divisione dei compiti in `docs/BL_WORK_PLAN.md`: inventario SFT/dati HMI, due specifiche collegate, prove e revisione prima delle misure. Inventario completato nella consegna sopra; restano le specifiche, nessun nuovo run o download eseguito.
- **Q4 e gia stata eseguita da Claude e conservata in dab5a33**, dopo il via tecnico 1c25c2e. Non rilanciare. Riconteggio e rapporto sono il seguito; `scripts/mdi_q4_recount.py` e conservato in 0344bc3, in revisione separata. Nessun output scientifico Q4 letto per aggiornare questo piano.
- Le sezioni sotto sono cronologia: «non avviato» descrive stati precedenti, non lo stato corrente.


## MDI Q4 — codice fed1775 tecnicamente approvato (25 novembre 2026)

- Chiusura in `docs/MDI_Q4_CODEX_CLOSE_fed1775.md`; i cinque rilievi di bb39a23 sono chiusi.
- Selftest 55/55 e sonda numerica aggiuntiva `scripts/mdi_q4_close_review_probe.py` 50/50; controesempi precedenti risolti.
- Nota Q4, A2 e codice produttivo invariati in questa revisione. Nessun --run o calcolo prospettico MDI eseguito.
- La decisione dell'utente sulla corsa resta da acquisire secondo la nota congelata; nessun lancio automatico.
- Dopo decisione: run pulito con log rediretto, conservazione degli output prima della lettura (il runner stampa CRITERIA), riconteggio indipendente, rapporto e decisione sul catalogo.
- Q4 resta una valutazione condizionata a scenari, senza verdetto sul Sole e senza serie BL combinata.


## MDI Q4 — codice corretto dopo la revisione Codex di bb39a23 (25 novembre 2026)

- `scripts/mdi_q4_prospective.py` (SHA `033b233b…`): selftest 55/55 (era 31/31), nessuna corsa sui disegni MDI; nota e A2 congelati intatti.
- Correzioni, punto per punto:
  1. `receipts_ok` ancorata: SHA delle due ricevute fissati; insiemi attesi (17 input, 9 codici) e hash; parent; ricevuta A2 citata dalla nota; regole e META dei conteggi; seed_zone; blob di nota e A2 ai commit di congelamento, antenati di HEAD. 13 controprove in memoria, una alterazione per caso.
  2. Bersaglio nullo: SE, h e riconoscimento conservati; rapporti al bersaglio NaN con flag `target_null_*`; nessun epsilon.
  3. Disegno vuoto: stato `empty_design`. I fallimenti sono espansi sulla griglia prevista (anche varianti di peso e covarianza dei combinati). SUMMARY ha tutte le chiavi, con n_ok e n_fail. Provati zero successi e un fallimento; i criteri non classificano.
  4. Prodotti dipendenti dal bersaglio per `020`, `010`, `qd_020`, `qd_010`; A_lo_design e A_hi_design in RAW.
  5. `CELL_COUNTS.csv` (N originarie e dopo ogni filtro per cella, domini MS/MF; reale 5401/5151/5062). YIELD_EFFECTS a un cambiamento per passo. Le 7 scelte più due regole di gestione in `IMPLEMENTATION_CHOICES`, registrate nel META.
- La sonda di Codex (`reviews/MDI_Q4_CODE_bb39a23/`, cartella MWO) non riproduce più i difetti. Prossimo passo: chiusura di Codex, poi decisione dell'utente sulla corsa.

## MDI — nota prospettica Q4 ed emendamento A2 congelati (24 novembre 2026)

- Bozza `docs/MDI_PILOT_Q4_NOTE_DRAFT.md`: revisione 1 in b856beb (rivista, non pronta); revisione 2 (SHA `7fe6cc76…`) rivista ma non conservata (lacuna dichiarata); revisione 3 (`d0574435…`) e 3.1 (`f77c0310…`) conservate anche in `reviews/` della cartella di consegna MWO.
- Conteggi preparatori non ciechi: regole fissate prima di contare (`docs/MDI_Q4_PREP_COUNTS_RULES.md`, `9ce409fc…`), `scripts/mdi_q4_prep_counts.py`, `results/MDI_Q4_PREP_COUNTS/` (21/21 riscontri; nessun tilt letto). Esiti principali: MS 5151 e MF 5062 gruppi; ciclo 22 solo 20/13 gruppi; rese proiettate L1/L2 riprodotte entro 3,7e-16; le due regole sulla latitudine non soddisfano i criteri fissati → emendamento A2.
- Bozza `docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2_DRAFT.md` (`3457b90d…`): requisito flusso–latitudine del §7 attenuato, non soddisfatto (classi della cella di selezione, 5 donatori più vicini in |lat|).
- Chiusura documentale Codex (`MDI_Q4_NOTA_CHIUSURA_CODEX.txt`): A2 e nota 3.1 pronte per il congelamento, A2 prima. Non è una validazione scientifica né un risultato prospettico.
- A2 congelato: `docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2.md` (bozza rivista + sola intestazione di congelamento); ricevuta `docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2_FREEZE.json` (SHA `c8340770…`, commit d94057f).
- Nota congelata: `docs/MDI_PILOT_Q4_NOTE.md` (revisione 3.1 + intestazione di congelamento e riferimento ad A2 congelato); ricevuta `docs/MDI_PILOT_Q4_NOTE_FREEZE.json` (SHA `e13a3a72…`, commit 1674f57; semi, Z, impronte di input e codice riusato).
- Codice Q4 scritto: `scripts/mdi_q4_prospective.py` (selftest 31/31: prove sintetiche del §6.3, riproduzione di E0 su 36 righe e di `t3_var`, rese deterministiche 46 righe a 3,7e-16, conteggi preparatori, end-to-end sintetico). Nessuna corsa sui disegni MDI. Revisione Codex del codice (`MDI_Q4_CODICE_REVISIONE_CODEX.txt`, cartella MWO): non ancora pronto per la corsa, 5 rilievi (ricevute verificate solo in parte, bersaglio nullo, disegni vuoti e configurazioni tutte fallite, prodotti per target_qd e δ 0,10, tabella delle N per cella e scelte in META). Prossimo passo: correggere il codice (non nota né A2) con regressioni sintetiche e tornare da Codex. `--run` richiede albero pulito, script uguale a HEAD e ricevute di congelamento concordi.

## MDI L2 — fase 6 chiusa: rapporto rivisto da Codex (chiusura positiva su 891521c)

- Chiusura della revisione del rapporto (24 novembre 2026): nessun rilievo residuo su `docs/MDI_PILOT_L2_RESULTS.md` né su `scripts/mdi_pilot_l2_report_numbers.py`.
- Lo script concorda con la verifica indipendente di Codex in 84 confronti su 84 (riscontri numerici e di integrità, non validazione degli intervalli). Prodotti L2 e ricevuta 10/10 invariati.
- Il rapporto vale come descrizione del pilota con i limiti esplicitati; dalla chiusura non derivano una validazione scientifica né la scelta del prodotto per il catalogo.
- Parte descrittiva del pilota MDI completa (L1: Q1, Q3; L2: Q2, ripetibilità, Q3 full-disk). Rinviati e separati: nota prospettica Q4, BARD-MDI, serie BL combinata.
- Rapporti di Codex nella cartella di consegna MWO: `MDI_L2_RAPPORTO_REVISIONE_CODEX.txt`, `MDI_L2_RAPPORTO_CHIUSURA_CODEX.txt`; prove in `reviews/MDI_L2_REPORT_6156144/` e `reviews/MDI_L2_REPORT_CLOSE_891521c/`.

## MDI L2 — fase 6 eseguita; rapporto descrittivo

- Correzioni f089840 (chiusura Codex positiva, sonda 87/87); run su f089840, prodotti 4249b72, riconteggio 10/10 partial false 52849f0.
- Rapporto: `docs/MDI_PILOT_L2_RESULTS.md` (descrittivo, intervalli non validati). In sintesi, regola A1:
  - resa A 61/90, proiettata 47 % (coorte U fuori dominio μ); quiete 24/318 lati, mediana 20,6 G;
  - Q2 sinottica − fd(A), 61 coppie: d_ax −0,2°, d_γ −0,6° [−1,2, −0,2] (−1,0° a 100 G), |d_ax| mediano 1,4°, flusso sin/fd 0,87, leading 100 %;
  - A − B, 58 coppie a 1,6 h: d_ax 0,0°, |d_ax| mediano 0,7°, leading 98,3 %;
  - Q3FD fd(A) − MWO, 49 coppie: d_ax +0,8°, |d_ax| mediano 6,8°, flusso 18,0; sugli stessi 49 gruppi sinottica − MWO dà 7,1° (Spearman 0,88). Confronto descrittivo: non identifica l'origine degli scarti né esclude un contributo della composizione sinottica.
- Calcoli in lettura (dispersioni per coppia, confronto appaiato con le coppie L1) dichiarati nel rapporto; li riproduce `scripts/mdi_pilot_l2_report_numbers.py` (sola lettura, non preregistrato).
- Revisione Codex del rapporto (6156144): numeri confermati; testo corretto (confronto appaiato non dimostra irrilevanza della composizione sinottica; quiete distinta dalla resa; arrotondamenti). Q4 (nota separata), BARD-MDI e serie combinata restano rinviati.

## MDI L2 — fase 6: correzioni dopo la revisione Codex di 3c79d78, da chiudere prima del run

- Revisione Codex (offline, 17/17 condizioni riprodotte): formule coerenti con Q2/Q3 e A1; due lacune del verificatore, nessuna nelle formule.
- Provenienza: insiemi attesi dei prodotti a monte fissati nel codice (non più dal manifesto sotto controllo, manifesto vuoto rifiutato); protocollo congelato verificato in SEL/L1/AN1/PLAN/L2, A1 in PLAN/L2; legami L1 → ricevuta della selezione, AN1 → META e ricevute di selezione e L1 e rilascio MWO, L2 → metadati del piano. Il run registra l'hash del CLASS_EDGES.json usato, confrontato col manifesto AN1; il riconteggio lo verifica. Stessi contratti, codice indipendente, nel gate del runner e nel riconteggio.
- Note: il riconteggio definisce il testo atteso di NOTES.json e della nota della quiete (non importato dal runner) e confronta ogni chiave e valore.
- Regressioni: struttura sintetica del gate (`gate_fixture`) con 20 controesempi (i cinque di Codex e i legami analoghi) più byte cambiati; runner 40/40, riconteggio con note invertite/pesi/regola originale/nota della quiete rifiutate.
- Gate reale (solo META, ricevute e hash): nessun problema con i nuovi contratti. Analisi non eseguita: serve la revisione di chiusura.

## MDI L2 — misura eseguita; codice dell'analisi (fase 6) scritto, da rivedere prima del run

- Misura L2: run su fcba552, prodotti 02aca76, riconteggio 12/12 (b0a38cf). Esiti A1: A ok 61, fuori mu 20, nessun magnetogramma 9; B ok 59; 58 coppie complete. Originale: A ok 8, B ok 5. Quiete: 24 immagini su 159 con un lato valido.
- `scripts/mdi_pilot_analysis_l2.py` (selftest 18/18): per regola (A1 principale, originale secondaria) e soglia (50/100 G):
  - resa sui 90 gruppi per A e B, con cause e w2 = 1/pi2, e perdite per anno, INTERVAL e QUALITY di A;
  - quiete (senza lati validi «non disponibile»);
  - Q2 = sinottica − fd(A); REPEAT = A − B con Δt dal piano; Q3FD = fd(A) − MWO (M1, MWO − t_DPD e MWO − T_OBS(A)).
  - Gruppi per QUALITY/INTERVAL di A (e transizione di QUALITY per REPEAT); un sottoinsieme vuoto ha n = 0.
  - Bootstrap come L1; classi di separazione = terzili L1, uguali a CLASS_EDGES dell'analisi L1.
- `scripts/mdi_pilot_analysis_l2_recount.py` (selftest 19/19): ricostruzione propria e confronto completo; 14 manomissioni rifiutate; confronti vuoti; 2000 repliche uguali al runner.
- Gate reale: nessun problema; colonne d'ingresso presenti. Nessun run dell'analisi sui dati reali: si attende la revisione.

## MDI L2 — misura e riconteggio approvati

- Revisione di 913ab1d chiusa: `docs/MDI_PILOT_L2_CODEX_CLOSE.md`.
- Aggiunto l'ultimo legame selezione-META/metadati, anche nel riconteggio; nessuna regola scientifica cambiata.
- Runner 16/16, riconteggio 25/25, sonda indipendente 7/7.
- Download 85609aa ricontato: 161 file, hash/byte/path/T_REC concordi; 412 richieste, 243994274 byte, zero prenotazioni aperte.
- Via tecnico: --run da albero pulito, conservare prodotti prima della lettura, --check e conservare ricevuta completa.
- Nessuna misura reale fatta da Codex. Analisi dei confronti Q2 da rivedere prima della sua esecuzione.


## MDI L2 — revisione fase 5: correzioni necessarie prima della misura

- bedc06c rivisto: `docs/MDI_PILOT_L2_CODEX_REVIEW.md`; selftest esistenti 8/8 e 16/16 riprodotti.
- Sonda `scripts/mdi_pilot_l2_review_probe.py`: base coerente, cinque difetti riprodotti (uscita 1 attesa).
- Da chiudere: gate completo prima dei FITS; pair_status e conteggi interi; INTERVAL ignoto senza crash.
- Confermati da sole keyword: 20/81 finestre A fuori mu, quiete 51 senza lati e 30 con un lato.
- Nessun emendamento geometrico proposto; nessuna rete o misura reale eseguita nella revisione.
- Piano A1 e blocchi B/C restano approvati in 9185a77; download separato, previa autorizzazione utente.


## MDI L2 — piano A1 e blocchi B/C approvati tecnicamente

- Revisione di 20e1d73 chiusa in `docs/MDI_L2_FITS_CODEX_CLOSE.md`.
- Piano conservato: 161 file, 159 principali e due original-only; nessuna scelta cambiata.
- Corretti tentativi interrotti, contatori degli errori dal sidecar e hash effettivi della selezione.
- Downloader 12/12, planner 7/7, riconteggio piano 8/8, adattatore/oracolo 23/23; sonda indipendente positiva.
- Via tecnico al download, solo dopo autorizzazione esplicita dell'utente ai FITS. Nessuna rete eseguita qui.
- Il download puo precedere la misura L2; runner e riconteggio della misura devono essere rivisti prima dell'uso.


## MDI L2 — emendamento A1 congelato, nessun via ai FITS

- Congelamento `0428653`; ricevuta `docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json`.

- Testo `docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md`; revisione in `docs/MDI_TILT_PILOT_A1_CODEX_REVIEW.md`.
- QUALITY esattamente {0,0x200}; altri esclusi. Scelte principali A/B invariate, risultati distinti per QUALITY/INTERVAL.
- Controllo originale con assegnazioni originali: due file supplementari, 161 file unici pianificabili; nessun nuovo gruppo.
- Prenotazione di 32 MiB mantenuta: non si accumula per file riuscito. Rimossa la riduzione non necessaria a 4 MB.
- Correzione NA approvata; lettore dei test allineato per non introdurre mutazioni collaterali, selftest 15/15.
- Ora codice/piano A1 offline in cartella nuova e riconteggio; chiusura B/C e successiva autorizzazione utente prima dei FITS.

## MDI L2 — riconteggio dei metadati approvato

- Revisione di 34fc26b chiusa: `docs/MDI_L2_METADATA_RECOUNT_CODEX_CLOSE.md`.
- Aggiunto controllo indipendente di serie/istante/finestra ±10h e impronta del prefisso di registro; selftest 15/15.
- Hash dei prodotti e registro identici a 98ee895: 90 richieste, 349154 byte; composizione QUALITY non letta qui.
- Via a --check reale, conservazione della ricevuta positiva, poi lettura e proposta di eventuale emendamento.
- Nessun FITS, allargamento QUALITY o nuova rete autorizzati. Blocchi B/C e misura L2 ancora separati.

## MDI L2 — via tecnico ai soli metadati, riconteggio ancora da chiudere

- 329be47 rivisto in `docs/MDI_L2_METADATA_ACQUISITION_CODEX_REVIEW.md`.
- Corrette in revisione risposta vuota, limite reale del corpo, byte IncompleteRead e fallback prudente; metadati 16/16.
- Via tecnico alla sola acquisizione dei metadati delle 90 unità L2, dopo autorizzazione esplicita dell'utente.
- Riconteggio non ancora approvato per QUALITY: quattro mutazioni accettate, prodotti e provenienza incompleti.
- Conservare risposte e registro; nessun emendamento QUALITY prima della chiusura del riconteggio.
- Downloader/adattatore restano nei blocchi B/C aperti. Nessuna rete eseguita in questa revisione.

## Pilota MDI L2 — revisione offline della rete

- Revisione di 0e32539 in `docs/MDI_PILOT_L2_NETWORK_CODEX_REVIEW.md`; nessun via alla rete.
- Prima dei metadati: byte falliti/interrotti e prenotazione, gate di selezione, QUALITY mancante, denominatori con fallimenti.
- Downloader separato: ripresa senza hash atteso e tentativi cumulativi; completezza esplicita.
- Adattatore: QUALITY assente/hex, area con CDELT1/CDELT2, prove geometriche indipendenti da completare.
- Test esistenti 13/13, 3/3 e 7/7; sonda offline aggiuntiva conserva i controesempi. Nessun FITS reale letto o rete usata.
- Chiudere prima i soli metadati, poi autorizzazione utente; downloader/adattatore hanno cancelli separati.

## Pilota MDI L1 — rapporto descrittivo rivisto

- Rapporto 79fb406 rivisto; dettagli in `docs/MDI_PILOT_L1_RESULTS_CODEX_REVIEW.md`.
- Hash, ricevuta 13/13 e principali aggregati controllati; tabelle e risultati numerici invariati.
- Precisati popolazione/resa stimata, confronti correlati, scarti relativi e causa non identificata del rapporto di flusso.
- Proposto passo di soli metadati per QUALITY × INTERVAL dei 90 gruppi L2; nessuna rete autorizzata o eseguita.
- Codice metadati ancora da chiudere: finestra B precedente fino a −10h, frazioni di secondo e registro cumulativo.
- Un eventuale emendamento QUALITY va congelato prima dei FITS L2 e dichiarato dopo i risultati L1 già noti.

## 23 novembre — chiusura della revisione dell'analisi MDI L1

- Correzioni 5959250 verificate; dettagli in `docs/MDI_PILOT_ANALYSIS_L1_CODEX_CLOSE.md`.
- Corrette in revisione la lettura degli orari ISO interi/frazionari e la riproduzione dello stato errore di M.
- Via alla corsa descrittiva Q1/Q3: run, conservazione prima della lettura, riconteggio completo, rapporto.
- BARD e rapporti MWO indisponibili dichiarati; Q2/ripetibilità attendono L2, Q4 separato.
- Nessuna analisi dei tilt reali eseguita qui. Rete e serie BL combinata non autorizzate da questa revisione.

## 23 novembre — revisione dell'analisi MDI L1

- Revisione di 107e78c in `docs/MDI_PILOT_ANALYSIS_L1_CODEX_REVIEW.md`; non ancora via alla corsa reale.
- Nove mutazioni sintetiche accettate dal riconteggio; sonda conservata. Completare controllo degli output e input.
- Confini di separazione unici fra soglie; correggere distanza temporale MWO−DPD e dichiarare quantità indisponibili.
- BARD rinviabile esplicitamente; classi aggiuntive |LCM| da omettere o specificare con nota prima degli scarti.
- Nessuna analisi reale, rete o nuova simulazione lunga avviata. Protocollo e risultati conservati invariati.

## 23 novembre — chiusura della revisione MDI fasi 1–3

- Correzioni c2e7fb3 verificate: `docs/MDI_TILT_PILOT_PHASE123_CODEX_CLOSE.md`.
- Corrette in revisione le costanti di own_ct/t_for nel riconteggio; regressione sui due lati del confine N.
- Selftest: selezione ricontata 11/11, misura L1 19/19, riconteggio L1 19/19; sonda indipendente aggiornata.
- Via alla selezione, conservazione e riconteggio; se positivo e completo, misura L1, conservazione e riconteggio.
- Nessuna selezione o misura reale eseguita qui. Acquisizione full-disk separata, non autorizzata dalla revisione.

## 23 novembre — revisione del codice MDI fasi 1–3

- Revisione di b5913f6: `docs/MDI_TILT_PILOT_PHASE123_CODEX_REVIEW.md`; non ancora via alla misura L1.
- Cinque mutazioni del SAMPLE e un N ambiguo inventato sono accettati dai riconteggi; quiete errata al taglio 0/360.
- Da completare: confronto delle colonne, N/effemeridi/quiete, provenienza degli input e scala TAI degli header.
- Tutti i selftest esistenti eseguiti passano (12, 11, 4, 15 e 5); sonda sintetica separata conservata.
- Nessuna selezione o misura MDI reale, nessuna rete. Claude corregge il codice senza modificare regole/soglie.

## 23 novembre — controlli autonomi e revisione 3 MDI

- Liste separate Codex/Claude: `docs/MDI_TILT_PILOT_WORK_SPLIT_20261123.md`.
- Oracoli indipendenti preparati: contratti numerici 15/15, metadati 193 mappe e 29280 righe DPD;
  non è ancora un test del codice produttivo di Claude.
- Rev. 3 4385692 metodologicamente approvata; prima del congelamento precisare tolleranza della conversione
  CT a periodo medio e assenza di record con BLANK nel DESIGN R4. Dettagli nella revisione rev. 3.
- Nessuna assegnazione N diversa fra periodo medio ed effemeridi nei record DPD controllati; periodo medio
  non è però un tempo esatto. Nessuna misura o acquisizione MDI eseguita.
- Protocolli/codici/META HMI/MWO protetti: 19 file invariati durante la preparazione. Q4 resta rinviato.

## 23 novembre — revisione 2 del protocollo pilota MDI

- Revisione di 8f8b188 in `docs/MDI_TILT_PILOT_REV2_CODEX_REVIEW.md`; nessuna misura/acquisizione.
- Accettabili allocazioni 15/15 e 3/2, finestre ±6h/4h e confronto MWO su sottoinsieme deterministico.
- Precisare pesi delle due fasi su M1 e M0∪M2, INTERVAL mancante, quiete, bootstrap e tagli angolari.
- Consigliato congelare Q1–Q3 e rinviare Q4 a nota separata: la griglia e le regole del disegno non sono ancora complete.
- Verificati i tre semi; DOI ARISE forniti. Serve il testo finale prima del congelamento, senza allargare il pilota.

## 23 novembre — risorsa MDI sinottica verificata e metodo precisato

- Confermati 193 file locali, CR1909–2104 meno 1938–1940; letto un header, nessun array/tilt.
- Parere in `docs/MDI_TILT_PILOT_SYNOPTIC_CODEX_REVIEW.md`: sinottiche utilizzabili come prodotto da valutare,
  confronto full-disk nel pilota prima di adottarle per il catalogo/T3. Nessuna piccola differenza presunta.
- Br già radiale; area su griglia lon/sinlat, tempi per longitudine e bordi CR da gestire con adattatore proprio.
- Precedente pubblico ARISE individuato; nessun suo dato scaricato. Nota bibliografica e limiti nella revisione.
- Via alla bozza rivista, non alla misura completa. Nessuna acquisizione JSOC o trasferimento di risultati di altri progetti.

## 23 novembre — impostazione del pilota MDI rivista

- Inventario 2a7838b letto; parere in `docs/MDI_TILT_PILOT_METHOD_CODEX_REVIEW.md`.
- Preferito metodo (a), finestre DPD sul full-disk MDI; nuovo adattatore strumentale, kernel geometrico condivisibile.
- Distinguere campione MDI da DPD e sottoinsieme abbinato MWO; copertura e precisione prospettica non dal solo overlap.
- Precisati qualità/soglie, prodotti 1/5 min, tempi UTC e necessità di disegno temporale adeguato alla correlazione.
- Via alla bozza, nessuna misura o acquisizione eseguita; protocollo e codice da rivedere prima della corsa.

## 23 novembre — pacchetto locale del catalogo MWO rivisto

- Approvati script 67eac4b e pacchetto 02708d1; revisione in `docs/MWO_TILT_CATALOGUE_DEPOSIT_CODEX_REVIEW.md`.
- Selftest 11/11, check 6/6, 16 checksum positivi; 13 prodotti confrontati byte per byte con il rilascio.
- Pacchetto 17 file, record 5223/5942, README esteso e snapshot dei metadati originali coerenti.
- Nessuna pubblicazione. Licenza, autori, crediti definitivi e repository da concordare con utente e Paolo.
- Per pubblicare: versione definitiva separata con manifesti aggiornati; conservare V1. Esito T3 invariato.

## 23 novembre — diagnosi S2 conclusa e rivista da Codex

- Modifica round_trip d606806 approvata dopo verifica; fit S2 riprodotto esattamente, selftest 33/33 e 22/22.
- Ricevuta 19/19 e hash confermati; diciannove pendenze ricostruite separatamente entro 3,48e-13.
- Rapporto precisato: termine assiale non è correzione, senza E8 non è equivalenza, area terzile 3 non è verdetto;
  area e separazione hanno andamenti puntuali diversi, quote e medie marginali non spiegano la causa.
- Revisione in `docs/T3_MWO_S2_DIAGNOSIS_RESULTS_CODEX_REVIEW.md`; esito T3 invariato.
- Diagnosi chiusa. Priorità alla preparazione del deposito; eventuale studio di confrontabilità separato da pianificare.

## 23 novembre — via alla diagnosi descrittiva S2 (c675d39 rivisto)

- Rilievi chiusi in `docs/T3_MWO_S2_DIAGNOSIS_CODE_REVIEW.md`: runner 33/33, riconteggio 22/22;
  probe: base accettata e tutti i controesempi rifiutati. Catena integra, nessun input mancante.
- Via a --run, conservazione prima della lettura, --check e rapporto descrittivo, nell'ordine già concordato.
- Nessuna diagnosi reale eseguita da Codex; nota e codice invariati, nessun cambiamento a T3.
- Tolleranza A_min/A_max verificata: assoluta 1e-12; uso comune di M dichiarato nel riconteggio.

## 23 novembre — codice della diagnosi S2: correzioni richieste prima della corsa

- Revisione 9106186: `docs/T3_MWO_S2_DIAGNOSIS_CODE_REVIEW.md`; selftest ripetuti 21/21 e 7/7.
- Terzili, matrice indipendente e dipendenza comune da M approvati metodologicamente.
- Probe sintetico: accettati intervalli D1, parametri M e conteggi alterati; guardia accetta ricevute 0/0.
- Correggere controlli e completezza/provenienza delle ricevute; nuova revisione prima del --run.
- Nessuna diagnosi reale eseguita da Codex. Script dei controesempi `scripts/t3_mwo_s2_review_probe.py`.

## 23 novembre — bozza diagnostica S2 rivista da Codex

- Revisione di a252063 in `docs/T3_MWO_S2_DIAGNOSIS_CODEX_REVIEW.md`; nessuna diagnosi reale eseguita.
- D1 ammessa come scomposizione, incluso il termine di riavvolgimento; non nuovo test T3.
- Soglie 300 e 45 gradi solo operative; eliminare la classificazione localizzata/diffusa e i flag rispetto a C.
- Seme 69 600 001 disgiunto dalla griglia effettiva, benchmark, S1 e Joy; identità assiale provata su sintetici.
- Claude aggiorna nota e implementa; revisione del codice prima della corsa reale. Nessun nuovo verdetto.
- README deposito: precisare equivalenza e pacchetto separato, senza alterare il rilascio verificato.

## 23 novembre — revisione finale Codex e figure V2

- Revisione di rapporto e prodotti completata: `docs/T3_MWO_FINAL_CODEX_REVIEW.md`.
- Confermati hash, ricevute 16/16 e 115/115 e dodici intervalli comprendenti zero.
- Precisati S2 (controllo relativo, non correzione) e phi al bordo (non prova di componente dominante).
- Figure corrette in `results/T3_MWO_FINAL_FIGURES_V2`, stessi input verificati; originali conservate.
- T3 MWO chiuso come descrittivo; restano da concordare deposito, licenza e autori. Nessuna pubblicazione.

## 23 novembre, tarda mattina — T3 MWO R4 chiuso (descrittivo); rilascio locale verificato

- Catena completata: stima `e6ac79e`, riconteggio 16/16 `a636aeb`, esportazione `93f3eb7`, controllo del rilascio
  115/115 `3c88ca5`, figure `e17f37e`. Rapporto: `docs/T3_MWO_FINAL_RESULTS.md`.
- **β₃ = −4,93 [−10,21, +0,34]: descrittivo, nessun verdetto.** Lo scarto strumentale S2, −3,18, ha lo stesso segno
  e ordine di grandezza. M è al bordo, con φ = 0,98.
- Aperti:
  - revisione Codex del rapporto;
  - impaginazione delle figure, da correggere in una nuova cartella;
  - deposito, licenza e autori (utente e Paolo);
  - estensione MDI; S42 nel progetto MWO/SINDy.

## 23 novembre — stato operativo (Claude): stabilità R4 eseguita e ricontata, in attesa di Codex prima della stima

- Revisione positiva di Codex della validazione (`cf7cc61`). Patch di collegamento applicata in `132f722`.
- `--stability` (apertura autorizzata del sigillo) conservato in `5a52d8a`. Riconteggio 16/16 in `2f9edf6`.
  Diagnosi post hoc di S1 in `a387d18`. Rapporto: `docs/T3_MWO_STABILITY_R4_RESULTS.md`.
- **Regola: β₃ descrittivo**, per S1 «non determinato» e S2 «stabilità non determinata».
  - S1: 573/2000 repliche singolari, tutte dalle celle non verificabili E1N ed E7S.
  - S2: −3,18 [−8,77, +2,40] con C = 0,53.
- **Fermo prima di `--estimate`:** serve la revisione di Codex degli esiti di stabilità.

## 22 novembre mattina — stato operativo (Claude): validazione R4 chiusa, in attesa della revisione di Codex

- **Validazione T3 MWO su R4 terminata:** codice d'uscita 0, «accepted (15 deg): True». Conservata in `0644465`.
- **Riconteggio indipendente:** `t3_mwo_analysis_recount.py --check-validation` 8/8, ricevuta con partial false e
  technical_ok true. Griglia completa (76 000 righe, 0 invalide), 75 981 SE ricalcolati (scarto relativo massimo
  3,4e-15), accettazione a 15° ricontata. Conservato in `e463a2d`.
- **Lettura registrata:** `--record-reading` → `results/T3_MWO_VALIDATION_R4_READING/READ.json`, con path
  «verdetto possibile» e il commit di lettura `e463a2d`. Conservata in `8b18356` e inviata con push.
- **Tutti i 18 scenari rispettano i criteri.** Sotto il nullo (sd_e 15°) i verdetti falsi vanno dal 2,31 % al 2,93 %
  (soglia 3 %). Il punto più vicino alla soglia è lo scenario 7: 2,93 %, con il lato «supportato» all'1,61 % (soglia
  1,75 %). La copertura sotto effetto va dal 96,75 % al 98,0 %. La potenza per la rampa del 10–20 % è fra il 2 e il
  4,7 %: un verdetto è possibile, ma un effetto delle dimensioni previste non sarebbe quasi mai rilevato.
- **Fermo qui:** la patch `patches/T3_MWO_STABILITY_WIRING.patch` non è applicata, `--stability` non è eseguito e i
  tilt restano sigillati finché Codex non rivede `e463a2d` e `8b18356`. Il resto della catena è invariato (punti 4–10
  sotto).

## 20 novembre sera — stato operativo (Claude): validazione R4 in corsa, preparazione del rilascio

- **Corsa in atto:** validazione T3 MWO su R4, lanciata alle 16:35 da `89f525f` (staccata, 5 processi). Log
  `logs/t3_mwo_validation_R4_20261120_163501.log`, codice d'uscita nel `.exit` omonimo. Benchmark: 108 unità
  stratificate in 269 s, previsione 58,7 h, cioè fine attesa verso il 23 novembre alle 3 circa. **Non modificare
  `scripts/t3_mwo_analysis.py` finché non termina**: la corsa ne verifica l'hash all'inizio e alla fine.
- **Catena alla fine della corsa, nell'ordine** (ogni passo conservato in Git, ricontato e rivisto da Codex prima del
  successivo):
  1. conservare `results/T3_MWO_VALIDATION_R4`;
  2. `t3_mwo_analysis_recount.py --check-validation`;
  3. `t3_mwo_analysis.py --record-reading`;
  4. applicare `patches/T3_MWO_STABILITY_WIRING.patch`;
  5. `--stability` (apre il sigillo);
  6. `t3_mwo_stability_recount.py --check`;
  7. `--estimate` (una sola volta);
  8. `t3_mwo_estimate_recount.py --check`;
  9. `t3_mwo_catalogue_release.py --export`;
  10. `t3_mwo_final_figures.py --run`.

  SHA dei testi congelati: protocollo `4408a0ee…`, A1 `bc88452b…`, A2 `0d50aa16…`, A3 `27df9bb7…`.
- **Preparazione del rilascio fatta stasera (Claude), nessun tilt aperto:**
  - copertura di R4 dai soli metadati: `results/T3_MWO_COVERAGE_R4` (tabelle e 5 figure; la quota di gruppi con record
    isolato passa dal 24 % al 32 % fra il terzile di attività più basso e il più alto);
  - README del catalogo: `docs/MWO_TILT_CATALOGUE_README_DRAFT.md` (popolazione, convenzioni, epoche, colonne,
    esclusioni, limiti, provenienza);
  - figure finali: `scripts/t3_mwo_final_figures.py`, provato solo su dati sintetici;
  - riferimenti verificati: `docs/T3_MWO_REFERENCES.md`. **Li & Ulrich (2012, ApJ 758, 115) hanno già misurato i
    tilt magnetici MWO 1974–2012**: il nostro catalogo va presentato come nuovo per metodo, controlli e rilascio
    riproducibile, non come il primo. Anche Wang et al. (2014, ApJ 796, 1) confrontano i tilt MWO con quelli DPD in
    luce bianca, cioè l'analogo del nostro S1.
- **Push:** il remote di questo repository usa ora un token nuovo, fornito dall'utente il 20 novembre; il vecchio era
  scaduto. `git push` funziona.

## 20 novembre — d50f895 rivisto: sei rilievi finali chiusi, validazione R4 invariata

- Rieseguiti i selftest: riconteggio della stima 15/15, esportatore 7/7; git apply --check della patch positivo.
- Aggiornata la fixture del probe della stima: catalogo, controllo del disegno, validazione negativa ma valida,
  registro di lettura, prodotti e hash di stabilità, ricevuta e META della stima sono coerenti. La baseline
  passa sia nel ramo sintetico sia nel ramo che richiede conservazione Git (solo committed è simulato).
  Rifiutati tutti i tre controesempi di cb41c53: FINAL con numeri/stato/scenario errati; ricevuta con un check
  fallito; prodotto STABILITY modificato con META invariato per creare un verdetto. Il vecchio probe si
  fermava sulla fixture incompleta, non su una regressione del nuovo verificatore.
- Aggiornato anche il probe del rilascio: prima passa una vera esportazione sintetica, con entrambe le tabelle,
  tutti i file COMPARISONS previsti, README, hash e nessuna cartella partial residua. Poi sono rifiutati i tre
  casi di b2a7944: giorno discordante, riga SEALED aggiuntiva, catalogo obsoleto. Nell'ultimo caso viene
  verificato che nessun lettore dei dati del catalogo venga chiamato dopo il rifiuto della guardia.
- Confrontati il codice nuovo e l'estensione della patch: FINAL verificato per intero, ricevute con semantica
  completa, controllo dei prodotti a monte prima dei tilt; esportazione con chiavi identiche e scrittura
  atomica. Documentazione della popolazione e Joy descrittivo con conteggi e cicli parziali presenti.
- I sei rilievi di cb41c53 e b2a7944 sono chiusi nei percorsi provati. Via tecnico all'uso di questi strumenti
  quando raggiunto il rispettivo stadio del protocollo: fine e conservazione della validazione, riconteggio
  completo e lettura registrata, applicazione della patch, S1-S4 conservati e ricontati, stima unica, suo
  riconteggio, poi esportazione e riconteggio dell'esportazione. Nessun via ad anticipare le fasi.
- Questa revisione aggiorna solo i probe e la documentazione. Script della griglia, moduli P2f/p2d, DESIGN R4
  e TARGETS coincidono con 89f525f; nessuna patch applicata, nessun tilt reale letto, nessuna corsa riavviata.
- Prima di un deposito pubblico restano i prodotti effettivi e il loro controllo finale, oltre alle decisioni
  su autori/licenza/destinazione previste dal piano. Nessun push o deposito effettuato da Codex.


## 20 novembre — riconteggio finale della stima dc035f1: tre rilievi prima del rilascio

Rivisti scripts/t3_mwo_estimate_recount.py e il relativo ampliamento della patch, sempre non applicata.
Selftest rieseguito: 7/7 positivo. La ricostruzione del disegno e di beta/SE per le dodici analisi è coerente
nel percorso sintetico di base.
Il probe scripts/t3_mwo_estimate_recount_review_probe.py produce una baseline positiva con tutti i dodici
sottoinsiemi, poi riproduce i tre difetti seguenti. Non legge alcun tilt reale; solo committed() è simulato
per esercitare il ramo di guardia che richiede la conservazione Git.

1. **FINAL non verificato completamente.** Alterando SE, limiti, main_state e targets di FINAL.json e
   aggiornando il suo hash nel META, la ricevuta rimane positiva. Il check confronta solo outcome/verdict
   e beta3. Confrontare SE, lo, hi e stato con la riga principale ricontata; targets con TARGETS del controllo
   del disegno corrente e motivi con la regola di stabilità. Gestire esplicitamente valori mancanti/non finiti
   negli stati senza stima. Una ricevuta finale deve verificare anche i numeri che finiranno nel rapporto.
2. **Ricevuta della stabilità con checks falliti ancora accettata.** Con passed=total=1, partial=false e
   hash META corretto, ma checks=[{ok:false}], il comando require_git=True restituisce successo. Richiedere
   la lista completa di esattamente total controlli tutti positivi, conteggi interi positivi (non booleani),
   oltre al legame dell'hash; stessa semantica delle altre ricevute della catena.
3. **Prodotti a monte non verificati prima di SEALED.** Una STABILITY.json modificata da descrittivo a
   verdetto, con il META di stabilità e la vecchia ricevuta rimasti invariati, viene accettata se FINAL segue
   la regola modificata. La ricevuta resta legata allo stesso META ma il prodotto non corrisponde più al suo
   hash. Verificare i prodotti effettivi di stabilità e catalogo contro i rispettivi META e la catena fino a
   validazione/lettura, prima di aprire SEALED. Nei fallimenti dei prerequisiti non proseguire nella lettura.

La patch aggiunge correttamente parametri M alle righe stimate e legami del META di stima a catalogo e
stabilità; il suo allineamento è positivo. Questi collegamenti non sostituiscono il controllo degli hash
reali dei prodotti, né il confronto completo di FINAL. Il nuovo riconteggio non è ancora approvato come
certificazione della stima/rilascio. Restano anche i tre rilievi separati dell'esportatore in b2a7944.

Validazione R4 invariata e indipendente da questi strumenti finali: nessun riavvio necessario. Il log ha
ora un benchmark di 58,67 ore (108 unità stratificate in 269 s su cinque processi), indicativo del carico,
non una scadenza garantita. Nessun codice o input della griglia modificato; nessuna patch applicata.


## 20 novembre — rilascio del catalogo MWO: piano integrato, esportatore ancora da correggere

- Verificate le ricevute R4 18/18 e disegno 6/6, complete e legate ai META correnti. Script di analisi,
  tre moduli P2f/p2d, DESIGN R4 e TARGETS coincidono con 89f525f, revisione del lancio della validazione.
  Il log riporta selftest 41/41; nessun benchmark finale era ancora presente alla lettura del log.
- Piano di rilascio condiviso come attività preparatoria leggera, con due tabelle separate per isolati e
  tutti e definizioni di selezione/provenienza. Integrati i requisiti della catena completa e del riconteggio
  della stima prima di esportare; definito il controllo di Joy come descrittivo con intervalli nominali.
  Il piano resta bozza, deposito/licenza/autori da concordare; nessuna pubblicazione o nuovo dato reale letto.
- Esportatore aggiornato dc035f1: selftest 5/5 positivo; è stato aggiunto il requisito di una ricevuta completa
  e legata al META della stima. Rimangono tre controesempi sintetici riproducibili nel probe: giorno SEALED
  discordante; riga SEALED aggiuntiva; stima e ricevuta legate a un catalogo obsoleto che consentono comunque
  di raggiungere il lettore SEALED del catalogo corrente. Il probe simula soltanto la conservazione Git e
  intercetta la lettura prima di aprire dati reali. Nessun valore sigillato reale viene letto.
- dc035f1 aggiunge anche scripts/t3_mwo_estimate_recount.py e amplia la patch della stima: questi nuovi pezzi
  richiedono una revisione dedicata prima dell'uso. La loro presenza non certifica automaticamente il rilascio.
- Correzioni: guardia completa prima della lettura, join con uguaglianza delle chiavi (insieme, gruppo, giorno),
  controllo dei prodotti e scrittura transazionale; selftest temporanei indipendenti dallo stato reale di EST.
  Il pacchetto attuale non scrive README né riassunto dei confronti; --joy è menzionato ma non esiste nella CLI
  (Joy viene già calcolato da --export). Allineare interfaccia e descrizione alla versione finale del piano.
- Il coefficiente di Joy descrittivo va accompagnato da numerosità di regioni/CR/blocchi, repliche non valide e
  copertura parziale dei cicli 20 e 24. Nessun verdetto o garanzia di pubblicabilità derivato dal solo intervallo.
- Validazione R4 può proseguire: nessuna modifica a codice o input in esecuzione e nessun riavvio richiesto.
  La patch di stabilità dell'altra sessione è stata lasciata intatta e non applicata da questa revisione. Rilascio reale bloccato fino alla correzione e alla revisione della guardia.


## 20 novembre — revisione del codice A3 fd3fe95: via alla misura R4

- Rivisto il diff completo del runner e del riconteggio: A3 escluso prima della selezione, con verifica
  dello SHA del contenuto di ogni membro e stato excluded_A3 separato da excluded_A2. Il comando reale
  richiede l'hash A3, verifica elenchi disgiunti e presenza di tutti i 18+8 membri, poi registra i due
  hash di emendamento/elenco nel META. Nessuna variazione di geometria, pesi o regola del primo successo.
- Selftest eseguiti nuovamente: runner 22/22, riconteggio 28/28. Provati i due percorsi A2 e A3 su archivi
  sintetici: esclusione reale, scansione sana dello stesso giorno, SHA errato, membro etichettato sotto
  l'emendamento errato, marcatura mancante anche con hash di prodotto aggiornato. Non letti tilt reali.
- Verificati direttamente il legame dei CSV ai testi congelati, l'accordo dei due lettori e l'assenza di
  sovrapposizione (18 A2, 8 A3). Gate sui quattro documenti congelati positivo, R4 ancora assente.
- Controllati i percorsi: misura, analisi, riconteggi e patch usano tutti R4; nessun riuso delle cartelle
  R2/R3 per le nuove fasi. git apply --check positivo; la patch di stabilità resta non applicata.
- Nessun nuovo rilievo bloccante in fd3fe95. **Via alla misura R4**, conservazione dei prodotti e riconteggio
  indipendente completo, senza leggere i tilt; poi controllo del disegno e suo riconteggio, precisione
  attesa a pesi invariati. La validazione lunga viene dopo questi passaggi, non parte da questa revisione.
- Nessun codice di produzione modificato dalla revisione. Nessun avvio di R4 o push da Codex.


A3 congelato nel commit 27294ce, SHA-256 27df9bb794e41f24b7b521fb23da3f70f4b1bc733264384c036f10a0836437de; ricevuta in `docs/PROTOCOL_T3_MWO_AMENDMENT_A3_FREEZE.json`. Prima di R4 resta la revisione dell’implementazione.


## 20 novembre — revisione metodologica di A3, otto esclusioni confermate

- R3: verificata la ricevuta 15/15 completa, legata al META corrente; non ripetuta la misura lunga e nessun
  valore sigillato letto. I risultati di precisione restano condizionali al rumore analitico, non potenza di M.
- Ricostruiti con codice proprio dai riepiloghi PIXELS e MAGNETOGRAMS tutti i riferimenti e gli otto file.
  Nomi, numerosità, mediana di riferimento e rapporto coincidono con il CSV A3 entro 1e-12.
- Corretto un dettaglio necessario prima del congelamento: il calcolo salvato usa sette date UTC
  giorno-3…giorno+3, non 72 ore prima/dopo l'istante. Quest'ultima variante dà gli stessi otto nomi ma
  numeri di riferimento diversi (54,56,56,97 invece di 63,63,62,102 per i casi del 1986).
- Specificati esclusione del membro stesso, riferimenti finiti, estremi inclusi, assenza di ricorsione A3,
  confronto indeterminato senza riferimento valido e debolezza con uno o due confronti. Nessun nuovo file
  aggiunto all'elenco e nessuna nuova esclusione implicita nei casi indeterminati.
- 30 952 file: 18 A2, due illeggibili e 33 con zero pixel centrali utilizzabili; 30 899 confrontabili,
  37 senza riferimenti e 30 862 rapporti finiti. I 33 generano 55 tentativi falliti (16 BLANK, 39 dominio mu)
  e zero record R3. Confermati 2373/56317 tentativi con meno di tre riferimenti. Il vuoto (2,5;3] è confermato.
- Dichiarate la variante stesso-giorno scartata dopo l'audit e la portata operativa del controllo:
  nessuna certificazione globale dell'archivio, nessun tasso di falsi allarmi validato.
- Script riproducibile scripts/mwo_a3_rule_check.py (--selftest, --check), senza importare il codice della
  misura. Legge soltanto riepiloghi e metadati; verifica hash dei prodotti e cecità rispetto ai tilt.
- Via al congelamento metodologico e all'implementazione di A3, con pesi a flusso invariati.
  Prima di R4 occorre la revisione del codice e la prova completa A2+A3, ripiego sul file sano e hash/marker
  errati. Non lanciati R4 né validazione; patch di stabilità non applicata.


A2 congelato nel commit 22caa4d, SHA-256 0d50aa1692f2972a0c676f448ea9a0c0db7205fb53efc44c371e9215c531349d; ricevuta in `docs/PROTOCOL_T3_MWO_AMENDMENT_A2_FREEZE.json`.


## 20 novembre — A2 rivisto e congelato prima di R3

- Rivisti emendamento e implementazione di 8534f48. Elenco di 18 nomi unici coincidente con le esclusioni
  STRICT_QC del progetto del flusso polare; nessuna regola generale su GV e nessuna riscalatura.
- Aggiunta una prova end-to-end con un membro effettivamente escluso. Senza A2 quel membro vince il
  tie-break finale; con A2 runner e riconteggio scelgono la scansione sana dello stesso giorno UTC.
  Provati il lettore indipendente della lista, lo SHA errato e la marcatura excluded_A2 mancante
  anche dopo l'aggiornamento dell'hash del prodotto. Il riconteggio completo della fixture passa.
- Fissato nel testo di A2 lo SHA-256 del CSV esclusioni; il runner lo verifica prima di leggere gli
  archivi. Il comando reale di riconteggio confronta testo, CSV e due hash del META del catalogo.
  Verificato anche il rifiuto di una lista modificata. Il runner pretende 18 membri distinti.
- Selftest runner 20/20, riconteggio 22/22. check_repo: 142/146 nel sandbox; i quattro test del server
  locale erano bloccati dai permessi socket e passano 4/4 fuori dal sandbox. Totale 146/146; due
  avvisi già noti sulle correlazioni costanti. git diff --check e git apply --check della patch positivi.
- A2 congelato in docs/PROTOCOL_T3_MWO_AMENDMENT_A2.md; registro separato con hash e commit.
  Specificata la cecità rispetto al catalogo lungo: i risultati del pilota erano già noti.
- Via alla misura R3 e al suo riconteggio, poi al controllo del disegno e alla precisione prospettica.
  I pesi restano a flusso. La nuova validazione attende questi controlli e la decisione sui pesi.
  Nessuna misura R3 eseguita da questa revisione; R2 conservato; patch finale ancora non applicata.


## 20 novembre — riconteggio di stabilità 7fd1121: miglioramenti confermati, due rilievi residui

Rivisto il nuovo riconteggio e la patch non applicata. Selftest 16/16 positivo: la nuova fixture
end-to-end copre C, S1, S2 per emisfero, P1 e tabelle descrittive; le tredici mutazioni previste
sono rifiutate. Il vecchio probe f72 non è direttamente riutilizzabile: alla nuova firma va passato
il riferimento P1 sintetico, altrimenti fallisce la baseline per una fixture non aggiornata.

Due controesempi ulteriori, riproducibili con
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/t3_mwo_stability_recount_residual_probe.py`:

1. **Dominio dei parametri S2.** Sul campione sintetico integro, impostando phi=-0,1 e ricalcolando
   SE e limiti coerentemente, il controllo completo rimane positivo. La covarianza è calcolabile,
   ma phi non appartiene al dominio M congelato [0; 0,98]. `s2_recompute` deve controllare finitezza,
   dominio REML dei cinque parametri, SE finito e positivo e limiti finiti, prima di qualsiasi confronto.
   Applicare alle stime complessive, emisferiche e P1. Provare anche sigma_x2 <= 0 e kappa fuori dominio.
2. **Catena prima di SEALED.** `chain_problems` controlla le ricevute e i legami dello STABILITY META,
   ma non i legami check META → catalogo e validation META → check, né ACCEPTANCE.problems.
   Con una validazione legata a un disegno obsoleto e `problems=['incomplete grid']` restituisce comunque
   lista vuota, anche se il ramo principale di analisi la rifiuterebbe. Verificare questi legami e
   distinguere validazione negativa valida (via descrittiva) da validazione tecnicamente invalida
   (nessuna apertura). Nel probe solo `committed` è simulato, per isolare la guardia dai file Git reali.

Il probe restituisce 1 finché uno dei due casi viene accettato. Nessuna risposta reale sigillata letta.
Le correzioni possono restare nel riconteggio separato; nessuna modifica o ripartenza della validazione
attiva è richiesta da questi due rilievi. La patch resta non applicata; manca ancora il via al nuovo
riconteggio come requisito affidabile della stima finale.


## 20 novembre, Codex — diagnosi dei pesi prima di decidere un emendamento

- Ricontate le precisioni normali di riferimento sui soli metadati: indice Kish 192,51 con flusso,
  1105,92 con area e 5225 con pesi uguali; riconoscimento della rampa 20% circa 2,54%, 3,60%, 5,83%
  sotto rumore individuale 15 gradi e temporale AR(1) phi .5, scala 7,5. Sono ipotesi analitiche,
  non l'esito di M né una previsione certa sui tilt reali. Nessun tilt sigillato letto.
- **Prima di cambiare pesi, diagnosticare due magnetogrammi.** I quattro pesi maggiori producono il
  91,97% della somma dei quadrati e il 12,99% del flusso totale: NOAA 5671 (1989-09-05), 5669, 5668 e
  5678 (1989-09-04). Tutti hanno GV 0,03, contro 3 negli altri 5221 record. Le ultime due aree DPD sono
  solo 14 e 18: non basta parlare di regioni grandissime. L'anomalia GV era già segnalata nell'audit.
- File 1989/MP00_5250078_00_0890904_1726.fits e 1989/MP00_5250078_00_0890905_1764.fits.
  La coincidenza non prova un errore del campo o una riscalatura: nessuna divisione per 100 né
  esclusione automatica. Verificare provenienza e significato degli header prima di decidere.
- Nota e comando riproducibile in T3_MWO_METADATA_AND_CALIBRATION_REVIEW.md. L'indice Kish misura
  concentrazione, non il numero di dati indipendenti di T3. Cambiando pesi cambia anche il bersaglio
  proiettato della rampa. Area DPD è già una sensibilità descrittiva del protocollo.
- La corsa attiva è invariata e resta riferita al disegno corrente. Un eventuale catalogo corretto
  o una nuova analisi principale richiederebbero emendamento e verifica/validazione pertinenti;
  i risultati della corsa non si trasferiscono automaticamente a un disegno diverso.

## 20 novembre, Codex — prova completa del riconteggio S1-S4 f72c25c

- Prova end-to-end su 120 record isolati sintetici più quattro non isolati, con gDPD/sDPD di prova,
  tutte le uscite e 2000 repliche S1 al seme congelato. Baseline positiva; nessun tilt reale letto.
- Il nuovo riconteggio NON è ancora approvato come guardia di beta3: usa C da STABILITY invece di
  ricalcolarlo sul disegno WL. Nel probe C passa da 1,30909 a 130,909 e un caso descrittivo diventa
  «verdetto», con ricevuta ancora positiva. Vanno ricostruiti C, gli intervalli e S2 per emisfero.
- Altri output modificati passano: dati P1, mediane S4, etichette S3 e flag S1. Il controllo deve
  coprire tutte le quantità dichiarate, con chiavi, numerosità e regola finale indipendente.
- Verificare anche la catena e gli ingressi prima che il riconteggio apra SEALED. Dettagli e
  correzioni nella sezione aggiornata di T3_MWO_ANALYSIS_CODE_REVIEW_20261118.md. Probe riproducibile
  scripts/t3_mwo_stability_recount_review_probe.py: restituisce errore finché accetta una modifica.
- La patch estesa richiede correttamente una ricevuta completa prima di --estimate: probe su
  copia temporanea rifiuta ricevuta assente, parziale e di un META diverso. Questo collegamento
  non rende affidabile una ricevuta prodotta dal riconteggio incompleto.
- Nessuna modifica a script o ingressi della validazione in corso; nessun riavvio necessario.
  Patch sempre non applicata, stabilità e stima non autorizzate sulla base del nuovo checker.

## 20 novembre, Codex — stime HMI descrittive e patch finale MWO riviste

- Confermati i dieci risultati HMI di 9dc41ad, ricevuta 19/19 in a72ce2d: stime e SE nuovamente ricostruiti
  entro 7e-13 relativi. Rapporto HMI_FOLLOWUPS_RESULTS.md corretto direttamente, senza cambiare numeri:
  la fase emisferica non rimuove la stima negativa nel modello; +0,20 non è un limite fisico validato;
  Q3 ha stime centrali positive ma tutti gli intervalli nominali includono zero. Nessun verdetto di quenching.
- Patch patches/T3_MWO_STABILITY_WIRING.patch (6fadf10) verificata con apply --check e in una copia temporanea.
  Prova sintetica del collegamento: cinque file aggiuntivi, hash del modulo, blocco con IMPLEMENTED False.
  Probe riproducibile scripts/t3_mwo_stability_wiring_probe.py; nessun tilt MWO sigillato letto.
- Via alla patch soltanto dopo fine, conservazione, riconteggio e lettura registrata della validazione.
  Non applicata ora; script attivo e modulo extras invariati. La validazione continua con la propria provenienza.
- La futura lettura di S4 deve distinguere gruppi da record e i riferimenti dei terzili, come indicato nella
  revisione. Nessuna nuova soglia o correzione statistica introdotta.

## 20 novembre, Codex — rilievi statistici chiusi, validazione MWO in corso

- Confermate le correzioni in 8129c01 con sonde sintetiche: sigma_x2 NaN rifiutato, ricevuta 7/8 e
  technical_ok false; ricevute senza controlli, riconteggio del disegno mancante e validazione legata
  al disegno precedente rifiutati. La via descrittiva per una validazione negativa valida resta aperta.
- Controllo del disegno conservato e ricontato 6/6: bersagli -0,5417308898 e -1,0834617795; C 0,5428552449;
  WL disponibile per 4696/5225. La matrice ha 24 termini di disturbo più x3, quindi 25 colonne.
- Verifica fatta durante la corsa già avviata da 8129c01. Script, tre moduli P2f/p2d, DESIGN e TARGETS
  coincidono con quella revisione. Non modificarli mentre la validazione è in esecuzione.
- Log logs/t3_mwo_validation_20261120_105856.log: selftest iniziale 41/41; benchmark 108 unità stratificate,
  249 s su cinque processi; previsione 48,86 ore, circa due giorni, senza tetto di durata.
- Le due precedenti condizioni bloccanti sono chiuse. La validazione può proseguire; la stabilità resta
  bloccata. Il modulo separato t3_mwo_stability_extras.py ha IMPLEMENTED False e non è ancora collegato
  né approvato per l'uso. Collegamento e revisione dopo la validazione, prima di S1-S4 e dell'apertura.
- Nessun tilt sigillato o risultato fisico letto da Codex. A fine corsa: conservazione, riconteggio completo,
  lettura; poi il seguito previsto dal protocollo. Dettagli nella sezione aggiornata della revisione statistica.

## 20 novembre, Codex — revisione della consegna statistica f12d093 e catalogo R2

- R2 conservato in 566122f, 5225 isolati e 5944 complessivi. Controllo diretto dei metadati positivo:
  hash dichiarati dei cinque prodotti non sigillati e stesso giorno UTC in tutti i record e tentativi
  con magnetogramma. Nessun valore del file sigillato letto. Riconteggio completo arrivato durante
  la revisione: 13/13, partial false, legato al META corrente e conservato in deaa14f.
- Correzioni ai sei punti presenti in f12d093, selftest ripetuti 37/37 e 4/4. Due difetti residui
  riprodotti su dati sintetici, prima della validazione lunga:
  1. sigma_x2 NaN nella seconda riga è accettato dal runner e dal riconteggio, con ricevuta 8/8.
     I parametri salvati non entrano nella finitezza e max può ignorare scarti NaN.
  2. La catena accetta una validazione relativa a un controllo del disegno precedente, non richiede
     il riconteggio del disegno e accetta ricevute senza conteggi o con zero controlli.
- Rilievi e correzioni richieste nella sezione aggiornata di
  [T3_MWO_ANALYSIS_CODE_REVIEW_20261118.md](T3_MWO_ANALYSIS_CODE_REVIEW_20261118.md), con due nuovi probe
  sintetici riproducibili. Codice di analisi e riconteggio di Claude non modificato.
- Dopo ricevuta completa positiva di R2: via al solo controllo del disegno senza tilt e al suo
  riconteggio. La validazione lunga attende la chiusura dei due rilievi. Nessun via all'apertura
  del sigillo: prima di S1-S4 vanno completati anche gli output descrittivi elencati nella revisione.

## 20 novembre, Codex — audit autonomo ripreso e rilievo sul catalogo già misurato

- Audit delle fonti e dei metadati in [T3_MWO_METADATA_AND_CALIBRATION_REVIEW.md](T3_MWO_METADATA_AND_CALIBRATION_REVIEW.md).
  La calibrazione di saturazione e dello zero già presente nei FITS nativi resta non documentata. Il rilascio
  del 2024 descrive immagini 256×256 alle 20 UT; l'archivio locale usa 512×512 e TAVG variabile. Nessuna nuova
  correzione fisica applicata. Verificati gli hash dell'inventario e dei 41 ingressi DPD usati nell'audit.
- **Corretto un nuovo difetto prima della misura lunga.** In 2797 header TAVG-UT ≥ 24 ore. Runner e riconteggio
  raggruppavano per il giorno del nome anziché per la data UTC dell'istante completo. Ora usano quest'ultima;
  filename_day resta registrato nel runner. Due regressioni su FITS sintetici falliscono entrambe sul codice
  precedente e passano sul corretto. Il pilota storico ha tre abbinamenti interessati, HARP 421, 495 e 1527;
  i suoi risultati restano conservati, con questo limite documentato nell'audit.
- Il conteggio senza effemeridi né misura dà 12 585 gruppi isolati potenziali. Non è il campione definitivo
  e non aggiorna i conteggi congelati. E1 ed E7 sono particolarmente fragili rispetto alla verificabilità
  per emisfero. Dettagli, denominatori e script riproducibile nell'audit.
- **Consegna statistica 678ff2f da correggere prima dell'uso.** Revisione e controesempi in
  [T3_MWO_ANALYSIS_CODE_REVIEW_20261118.md](T3_MWO_ANALYSIS_CODE_REVIEW_20261118.md). Il controllo di disponibilità
  calcola tilt WL prima del sigillo; la matrice su un solo emisfero solleva un'eccezione; il sigillo non richiede
  il riconteggio; servono percorsi espliciti per non identificabilità e righe numeriche non valide. Anche il
  benchmark va reso rappresentativo. File statistico di Claude non modificato.
- **Catalogo f718114 da rigenerare prima dell'analisi statistica.** Il confronto dei soli metadati
  day/obs_time trova 32 record isolati e 30 nell'insieme completo che non sono nello stesso giorno UTC.
  La ricevuta 12/12 di dad6f6b riproduce lo stesso errore del runner. Corsa e ricevuta storiche preservate;
  nessun tilt sigillato letto. Una misura corretta deve usare una destinazione nuova.
- Validazione HMI terminata: q1 e q2_hem non superano i criteri congelati e restano descrittivi
  (rapporto b2898f6). Audit aggiuntivo completato da Codex su 150 000 righe, 35 configurazioni, semi e
  indicatori coerenti; 149 928 SE riprodotti entro 4,1e-13 relativo. Dettagli in
  [HMI_FOLLOWUPS_CODEX_AUDIT_20261120.md](HMI_FOLLOWUPS_CODEX_AUDIT_20261120.md). Nessuna stima HMI reale eseguita.
- Verifiche della correzione UTC: runner 19/19 e riconteggio 16/16; suite 142 test passati nel sandbox e
  quattro test HTTP localhost passati separatamente con i permessi necessari (146 complessivi, due avvisi
  noti sulle correlazioni costanti). Protocolli, pipeline MWO congelata e risultati storici non modificati.

## 18 novembre, Codex — chiusura della consegna T3 MWO, misura e dati

- Revisione di `bc3577f` dopo i rilievi sulla consegna 1. Il runner usa l'istante completo per la CR e il
  riconteggio confronta CR, ciclo, sin|latitudine|, conteggi BLANK, tempi, posizioni, attività e molteplicità.
- Difetto residuo riprodotto su dati sintetici. Un NaN in `DESIGN.sinlat` o in `SEALED.gamma_deg` passava il
  controllo perché il massimo degli scarti poteva ignorarlo. Il riconteggio ora richiede valori finiti per
  le misure numeriche obbligatorie e conserva una ricevuta fallita e parziale quando il controllo fallisce.
  Le attività di sensibilità conservano i valori mancanti previsti dal protocollo.
- Selftest del riconteggio 16/16, con regressioni su NaN e infinito e verifica della ricevuta fallita.
  Verificati i 39 sDPD locali contro gli hash della ricevuta di acquisizione. Totale 81 431 910 byte,
  40 richieste registrate e 39 risposte valide. Nessun tilt in luce bianca calcolato per questa revisione.
- A1 congelato `cfa6886`, SHA-256 `bc88452b382d739866ff801a14aecf596968e092904906d7d7298355a0e063c5`.
  Con queste correzioni i punti 1–2 sono chiusi. La misura lunga può seguire la fine della validazione HMI,
  con i tilt sigillati e il successivo riconteggio secondo il protocollo.

## 18 novembre, pomeriggio (Claude): fase B, roadmap, bozze per Codex

- **Fase B** eseguita e controllata: [PROSPECTIVE_PHASE_B_RESULTS.md](PROSPECTIVE_PHASE_B_RESULTS.md); M segue la
  previsione analitica; T5 resta descrittivo.
- **Roadmap** decisa con l'utente: [ROADMAP_2026-11-18.md](ROADMAP_2026-11-18.md). Punti fondamentali Q1 (T2 reso test,
  ciclo 25 contro 24), Q2 (T4 reso test, con la questione della fase emisferica), Q3 (quenching locale, descrittivo);
  poi T3 su catalogo lungo (MWO magnetico preferito, luce bianca DPD in parallelo).
- **Da rivedere con Codex, in ordine:** `docs/PROTOCOL_HMI_FOLLOWUPS_DRAFT.md` con `scripts/hmi_followups.py` e
  `scripts/hmi_followups_recount.py`; `docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE_DRAFT.md` (rev. 2) con selettore,
  disponibilità e downloader; `docs/T3_LONG_CATALOGUE_FEASIBILITY_DRAFT.md`, `docs/PROTOCOL_T3_DPD_DRAFT.md`,
  `docs/PROTOCOL_MWO_PILOT_DRAFT.md` con `scripts/t3_dpd_feasibility.py` e `scripts/mwo_pilot_tilt.py`.
- **Commit fatti su un worktree** (ramo `t3-dpd-feasibility`, per non cambiare il commit registrato dalla fase B in
  corsa) e riportati qui con cherry-pick nello stesso ordine. I documenti citano gli hash del ramo: 2513f8b → d92d997,
  1f3cee4 → c2b0bf7 (output DPD conservati prima della lettura), f818e12 → 4379e48, 13e9830 → 8ab9975, 98d57ca → abddbb6,
  49b9383 → a5bc76f, 2a0f94f → a433d0b, 5bdd533 → 3aa5556, 4475e49 → 8d361c4.

## Piccolo confronto MDI–HMI eseguito (Claude, Codex senza token) — 18 novembre 2026

Downloader di Codex: prima corsa (`a19d3b6`) con HTTP 302 su tutti gli 84 FITS e 149 tentativi consumati; emendamento
A1 (`c409666`) prima di nuove richieste; diagnosi (redirect a https://jsoc1.stanford.edu, stesso percorso); trasporto A1
(`6904765`, 13 prove offline); download 84/84 (169 richieste, 135 s). R0 superato su HARP 191. Confronti con il runner
sui kernel di Codex (`run_9f80330`) e riconteggio indipendente di Claude (`recount_d278db3`): concordi entro 1e-8.
Valutabili solo A1/A2 su 5 coppie e B su 4 (maschere vuote o una sola polarità al minimo; una bitmap SMARP con codici
non documentati). Risultati in [MDI_HMI_SMALL_COMPARISON_RESULTS.md](MDI_HMI_SMALL_COMPARISON_RESULTS.md):
tilt Br→LOS/μ mediana |d_ax| 0,4°, MDI−HMI mediana |d_ax| 2,15°; flussi e dipoli molto più diversi; segnalazione nel
nord con n = 1; strato N laterale vuoto per B, quindi decisione sul catalogo MDI aperta. Da rivedere con Codex.

## Piccolo confronto MDI–HMI — downloader e adattatore per la revisione di Claude

Il downloader `scripts/mdi_hmi_patch_download.py` senza argomenti esegue solo il preventivo
sui manifesti e sui certificati locali. Dopo la revisione, `--fetch` acquisisce le keyword complete
di un singolo record per richiesta e verifica i percorsi dei segmenti prima dei FITS as-is.
Si contano i precedenti 41 tentativi e il tempo già consumato. Sono riservati 45 tentativi e
300 secondi per la provenienza MTARP→MDATA (§8); il downloader conserva un registro separato
nel percorso fisso `small_comparison_6d6fd12/patch_download/`, con al massimo due tentativi
per elemento incluse le riprese. Una risposta mancante resta annotata. Il controllo di integrità
del download usa identità, lunghezza, firma e SHA-256 locale. La lettura dei pixel è separata.

L’adattatore `scripts/mdi_hmi_patch_io.py` espone `load_selected(slot, HMI, ["bitmap", "Br"])`
per preparare R0; esplicita i segmenti anche per gli altri rami. Verifica SHA, identità, TEMPO TAI,
scala FITS, unità del segmento da schema, WCS CEA nativa, osservatore e minimo di μ contro il
certificato del record. Per la prova storica R0 si confrontano separatamente eventuali differenze
di precisione delle keyword DRMS rispetto ai sidecar P1. Le convenzioni fisiche del segno LOS
restano quelle documentate per i prodotti nativi. Le prove sintetiche sono in
`tests/test_mdi_hmi_patch_io.py`. Consegna precedente alla revisione del codice, al download
e a R0. La verifica delle integrazioni resta un’operazione separata.

## Verifica indipendente della selezione MDI–HMI (Claude) — 18 novembre 2026

Conferma a posteriori del protocollo congelato `6d6fd12` (ordine effettivo: congelamento, selezione `7a9898e`,
rilettura di Claude; nessun emendamento). Selezione ricostruita da `scripts/mdi_hmi_selection_check.py`, scritto
senza leggere `select_pairs.py`, dai certificati della corsa r2: **stesse 12 coppie, stessi archi, stesso ordine**
del manifesto `selection/PAIRS.csv` (SHA-256 `b9128d9b…`); tre per strato, 12 componenti G10 distinte; SHA-256
delle coppie, |ΔT_OBS| ≤ 360 s e QUALITY HMI = 0 verificati. Gli 84 segmenti di `availability/SEGMENTS.csv`
corrispondono esattamente ai 24 record scelti, con dimensioni uguali a quelle del certificato, tutti online
(6 168 876 byte annunciati). I 41 tentativi indicati sotto sono 34 della geometria (tetto §8: 40) più 7 di
disponibilità (tetto §6: 200). Prossimo: revisione del downloader e dell'adattatore, poi R0.

## Piccolo confronto MDI–HMI, protocollo congelato prima della selezione

Recepita la revisione di Claude. Il [protocollo congelato](PROTOCOL_MDI_HMI_SMALL_COMPARISON.md)
fissa d_γ con il segno del riferimento HMI, la soglia descrittiva di 2,107° e s/√n nello stesso
sottoinsieme. Dopo il commit di congelamento `6d6fd12` sono state selezionate 12 coppie, tre per strato e
12 componenti G10 distinte. MDI QUALITY 0x200 in 11 coppie, 0 nella restante. Sette richieste rs_list
su record esatti, un segmento alla volta, confermano lo stato online con percorso, dimensioni e taglia
positiva per tutti gli 84 segmenti (24 MDI, 60 HMI). JSOC riporta complessivamente 6 168 876 byte.
Il codice JSOC archiviato parte da −1 nella somma di *size*: usare prudenzialmente un byte in più
per segmento nel preventivo, verificare poi i byte reali. Inclusa la geometria: 41 tentativi,
circa 550,0 s cumulativi. Nessun corpo FITS trasferito. Manifesto delle coppie, motivi di esclusione,
ricevute originali e manifesto dei segmenti in `data/sharp/metadata_inventory_mdi/small_comparison_6d6fd12/`
(cartella locale). Restano la verifica della provenienza delle integrazioni, la revisione del downloader
e dell’adattatore, poi R0 prima della lettura delle differenze.
La fase B prospettica resta rinviata (quattro candidati). T3 resta non deciso, T5 descrittivo.

## Piano prospettico fase A eseguita; certificato geometrico MDI–HMI — 18 novembre 2026

**Fase A** (Claude; revisione del codice di Codex su `b6c00c0`, emendamento A1 `551d829`, correzioni `ecf0714`):
corsa unica su `6f4b416`, output conservati prima della lettura in `56a5944`, controllo indipendente 10/10.
Risultati in [PROSPECTIVE_PHASE_A_RESULTS.md](PROSPECTIVE_PHASE_A_RESULTS.md): nessuna estensione raggiunge il 50 %;
T5 da 10,7 % (E0) a 19,2 % (E3, f = 1, k = 1), T3 2,9 % → 4,3 % (bersaglio −1,60° = −0,067·γ₀); con il modello
protetto MDI non aggiunge informazione. Fase B: 4 candidati in banda, non avviata (decisione dell'utente con Codex).

**Certificato 1 MDI–HMI** (Claude, `scripts/mdi_hmi_footprint_mu.py`, `568abb9`, offline sulle 32 finestre
acquisite da Codex in `geometry_windows_20261118/`, 34 tentativi, 38,8 MB, 537 s): minimo di μ su tutti i centri
di pixel del ritaglio CEA. Archi certificati su entrambi / coppie: N centrale 838/877 (42/42), S centrale 322/390
(17/20), N laterale 571/880 (40/48), S laterale 186/455 (19/24); nessun dato mancante. Prima corsa
(`footprint_mu_20261118`) superata: trattava come mancanti 148 record ripetuti identici ai bordi delle finestre;
corsa valida `footprint_mu_20261118_r2` (locale, fuori da Git). L'acquisizione è stata ripresa una volta
(`acquire_continuation.py`): da controllare nella revisione. Prossimo passo: revisione dei conteggi, poi congelamento
del protocollo e selezione delle 12 coppie.

## JSOC: prova del campo bitmap.dims — 18 novembre 2026

Due rs_list HTTP 200 sulla coppia tecnica del 2010-05-01 01:36 TAI. La bitmap SMARP del TARP 13394
ha 77 × 70 pixel; quella SHARP della HARP 2 ha 388 × 285 pixel. Le due chiavi, l'ordine degli assi,
CRPIX e la ricostruzione con gli estremi DT concordano. DSUN_OBS, RSUN_REF e le coordinate
dell'osservatore sono presenti. Risposte grezze, SHA-256 e copie delle quattro fonti nella cartella
locale `data/sharp/metadata_inventory_mdi/geometry_probe_20261118/`, ricevuta `RECEIPT.json`.
Addebitati al controllo geometrico 2 tentativi, 2072 byte di corpo e 2,71 s di trasferimento.
Restano 38 tentativi su 40 (32 finestre di base, 6 tentativi di riserva). Il registro dell'inventario
storico è invariato. Questa prova documenta il formato in servizio; il minimo di μ e il numero di coppie
certificabili per strato restano da determinare. Le 32 finestre e i FITS richiedono un passaggio successivo.

## Piccolo confronto MDI/HMI — specifica geometrica per la revisione, 18 novembre 2026

Il §8 di `docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON_DRAFT.md` propone il controllo di μ sull'intera
impronta con metadati del ritaglio CEA o con estremi eliografici dei quali sia documentata la
copertura della bitmap rimappata. Per il revisore resta da verificare per entrambe le serie
l'esistenza di almeno una via: forma effettiva per record e WCS, oppure provenienza degli estremi.
La bozza specifica anche richieste, tetti, stati indeterminati e percorso separato MTARP→MDATA.
È stata preparata offline. Il rapporto per strato e la scelta delle mappe vengono dopo la revisione;
il confronto resta da congelare. Nessuna acquisizione in questo passaggio.

## MDI/HMI: risposta alla revisione di Claude, dominio ancora aperto — 2026-11-18

Revisione 2 non congelata; nessuna selezione, query, mappa o simulazione. Dettagli e hash in
`docs/MDI_HMI_SMALL_COMPARISON_REV2.md`, artefatti locali sotto
`results/MDI_SMARP_INVENTORY_REVIEW/revision2_20261118/` (esclusi da Git).

Punto 1 **non chiuso**: LAT/LON_MIN/MAX, DSUN_OBS, RSUN_REF esistono negli schemi ma non nei CSV;
NAXIS non è keyword. Con i centri non si garantisce mu >= 0,8 sull'intera maschera. Dominio e perdita
per strato non valutabili; nessuna stima pari a zero e nessuna inferenza delle dimensioni da CRPIX.
I soli conteggi diagnostici disponibili sono 877/390/880/455 archi N/S centrali/laterali (non regioni
indipendenti o campione). Occorre una specifica separata dei metadati aggiuntivi o una revisione
esplicita del disegno, prima del congelamento. Non si passa automaticamente ai soli pixel forti.

Punti 2-3 corretti: R0 con P1 invariato e rifiuti del kernel separati; differenze complete per flussi
positivo/negativo e centroidi (longitudini avvolte). Parsing QUALITY signed/unsigned a 32 bit esplicito.
Tabella full-disk QUALITY x INTERVAL: 0x200 compare sia con 30 s sia con 300 s; nessuna attribuzione
alle patch senza link sorgente. Verificate tutte le 22 copie persistenti previste dalle ricevute.
Nuclei verificati con 48 prove sintetiche; suite completa 108/108 (due avvisi attesi), diff-check superato.

**Fermo prima di congelamento e dati reali.** Prossimo: revisione di queste correzioni, soprattutto
come chiudere il dominio mu; adattatore FITS/segni/observer e link non ancora scritti. Non aprire nuove
query per colmare i campi senza una specifica autorizzata. T3/T5 invariati, altri studi in pausa, nessun push.

## MDI/HMI: preparazione del piccolo confronto, non congelata — 2026-11-18

Completati i punti indipendenti della lista autorizzata in assenza dell'utente. Nota delle fonti:
`docs/MDI_SMARP_METADATA_CLARIFICATIONS.md`; nuova bozza circoscritta
`docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON_DRAFT.md`; consegna `docs/MDI_HMI_PREPARATION_REVIEW.md`.
Nessun nuovo record, campione, FITS, trasformazione reale o simulazione. Nessun push.

Confermati nel codice ufficiale: LOS CEA rimappato come scalare, copia di QUALITY/T_OBS, percorso
MTARP/MDATA e distinzione DRMS fra valore e indice di slot. Tabella primaria MDI recuperata: bit 9
0x200 = non PRIME 60, non shutterless. La nuova bozza propone MDI QUALITY in {0,0x200} e HMI=0,
senza applicare il filtro; modo conservato, nessuna equivalenza strumentale presunta. **Restano aperti**
revisioni di produzione e collegamento alla sorgente effettiva per record, integrazione 30 s/rumore
e origine precisa dello scarto dalla griglia full-disk.
Nessun filtro o tempo dell'inventario è cambiato; nessuna query a serie fuori piano.

Bozza: fino a 12 coppie in quattro strati, confronto Br HMI/LOS vettoriale diviso per mu, Br HMI/LOS
misurato diviso per mu, MDI/HMI entrambi LOS/mu sulle maschere native. Niente calibrazione o inferenza
sul quenching; regola di qualità ora concreta, da rivedere prima del congelamento. Tetti e criteri sono proposte da rivedere.
Codice puro `scripts/mdi_overlap_kernels.py`, senza lettore FITS, downloader o --run reale; sole grandezze
indipendenti dal ciclo, senza S_BL/D*/efficienza. Prove sintetiche in `tests/test_mdi_overlap_kernels.py`.
Prove sintetiche 27/27 e suite del repository 87/87 (due avvisi attesi); diff-check superato.
Ricevute e fonti locali in `data/sharp/metadata_inventory_mdi/documentation_20261118/`
(anche staging `/tmp/bl_mdi_preparation/`).

**Fermo prima di congelamento, selezione e mappe.** Prossimo: revisione della consegna, della proposta
QUALITY e della specifica dei link; poi eventuale adattatore FITS/WCS con verifica P1. Piano prospettico e
morfologia S restano in pausa. Nessuna nota o comunicazione a Paolo.

## MDI/SMARP: associazioni della sovrapposizione verificate offline — 2026-11-16

Analisi dal commit pulito `198785b`, 11 controlli superati, nessuna rete o nuova riga acquisita.
127 TARP SMARP e 139 HARP HMI: 121 coppie candidate G5 (112 con almeno un arco univoco tra record),
161 G10; 1555 archi G5 perdono l'unicità all'allargamento. Non sono identità fisiche confermate.
Rapporto e hash: `docs/MDI_SMARP_OVERLAP_RESULTS.md`; output locali sotto
`results/MDI_SMARP_INVENTORY/schema_20261116_http_ac06138/overlap_only/198785bb3002/`.

Limiti prima della scelta delle mappe: definizioni native dei bit QUALITY MDI/SMARP da documentare
(0x200 prevale); T_REC coincidente non garantisce T_OBS vicino (76/8949 archi univoci G5 oltre 360 s).
Audit full-disk: 4500/4515 T_REC sono fuori di 30 s dalla griglia dichiarata; non dedurre lacune
per uguaglianza letterale all'epoca, né correggere tempi senza una regola documentata. Nessun filtro cambiato.

**Prossimo:** chiarire questi metadati, poi piano circoscritto delle mappe, distinguendo Br contro LOS/μ
su HMI dal confronto tra strumenti. Nessuna mappa scaricata, storico non avviato; piano prospettico e
morfologia S in pausa. Registro 272 tentativi, 45924964 byte, 119611 righe, circa 657,2 s. Nessun push.

## MDI/SMARP: elenchi della sovrapposizione acquisiti e verificati — 2026-11-16

Corsa `schema_20261116_http_ac06138`, fase `overlap` sul commit `4487125`, albero tracciato pulito:
33 elenchi di soli metadati acquisiti, riconciliati con i conteggi e verificati contro i JSON originali.
119611 righe accettate: SMARP 11387 (127 TARPNUM), HMI con margini 103709 (139 HARPNUM), full-disk MDI
2010 gennaio–ottobre 4515. Righe di bordo conservate 152; HMI scientifico 103706 record, 139 HARPNUM,
con 3 record di margine esclusi dal conteggio scientifico. Nessun filtro di qualità o flusso.

Registro cumulativo chiuso: 272 tentativi, 45924964 byte, 119611 righe, circa 636,5 s. Nessun export o FITS.
Primi blocchi misurati per i tre profili acquisiti; lo storico SMARP minimo non è ancora misurato e non è
registrato un preventivo di payload incompleto. Storico non avviato, nessun lookup ausiliario.

Dato reale da conservare senza reinterpretazione: INTERVAL full-disk 2010 = 300 s in 2466 record, 30 s in
1760, MISSING in 289. La regola registrata 60/300 lascia ignoti i 30 s: non chiamarli prodotti da un minuto
senza documentazione. DPC grezzo, collegamento patch–sorgente ancora ignoto. Nessuna stima di rumore o
calibrazione strumentale. Dettagli, limiti e hash in `docs/MDI_SMARP_OVERLAP_ACQUISITION.md`.

**Fermo prima dello storico e delle mappe.** Prossimo passo separato: lettura dei metadati acquisiti oppure
storico con il primo blocco minimo e il preventivo di payload prima del resto. Piano prospettico e S in pausa.
Nessun push.

## MDI/SMARP: fase counts conclusa e verificata — 2026-11-16

Corsa `schema_20261116_http_ac06138`, fase `counts` sul commit `e49e994`, albero tracciato pulito:
**219 richieste riuscite, 219 finestre**, zero righe di record acquisite. Registro cumulativo 239 tentativi,
125293 byte, circa 350,5 s. Nessun elenco, download o export. Mappa e regole registrate restano invariate.

Preventivo: somma dei conteggi 825362 (SMARP CEA 640289, HMI 103833, full-disk MDI 81240), comprensiva di
possibili duplicati ai bordi delle finestre inclusive DRMS; non regioni distinte o mappe recuperabili.
33 elenchi della prima parte + 179 dello storico; con 400 riserve e 239 tentativi già usati, totale 851/1000.
Decisione `full` per richieste e righe, non garanzia sul volume o sulla durata: da misurare sui primi elenchi,
con proiezione prima dello storico. Riconteggio indipendente sui JSON e controllo della partizione delle
finestre superati; artefatti originali e COUNTS_CHECK locali nella cartella della corsa.

Dettagli e hash in `docs/MDI_SMARP_COUNTS_REVIEW.md`. **Fermo prima degli elenchi**. Prossimo passo separato:
`overlap` (soli metadati) dopo lettura del preventivo; nessun via automatico allo storico o ai FITS.
Piano prospettico e morfologia S in pausa. Nessun push.

## MDI/SMARP: mappa verificata e registrata offline — 2026-11-16

Stato corrente: configurazione della corsa `schema_20261116_http_ac06138` preparata, verificata e
registrata dopo il via dell'utente. Nessuna richiesta a JSOC in questo passaggio; **20 tentativi cumulativi,
zero righe di record**, registro e log byte-identici a prima. Nessun conteggio o elenco acquisito.

Codice `50db300d02c0`: centro CEA documentato come alternativa del piano §6.2, inviluppi e box_only
sconosciuti senza dimensioni; confronto numerico esatto di INTERVAL (60/300 s) senza arrotondamenti;
preparazione offline riproducibile e controlli sugli hash di configurazione/schemi. Selftest **130/130** su
quel commit, ricevuta locale `results/MDI_SMARP_INVENTORY_SELFTEST/50db300d02c0/`; test repository **60/60**.
Mappa SHA-256 `63b0416967d1bd003b5364b2504399f1823d6287ced842856bbe4b2224aab99d`; regole `0f64079baa7ed3a9ed0ff843481c388f5284316f0dcdad56f8f5e1ae0337ed89`.

Dettagli e hash in `docs/MDI_SMARP_FIELD_MAP_REVIEW.md`; i quattro file FIELD_MAP, PRODUCT_RULES,
FIELD_MAP_REVIEW e FIELD_MAP_REGISTRATION restano nella cartella locale della corsa. DPC conservato grezzo;
nessun collegamento documentato delle patch SMARP al full-disk: prodotto patch `unknown`, senza correggere
T_REC/T_OBS di 30 s o interrogare serie fuori piano. **Prossimo: fase counts separata**, poi verifica del
preventivo prima degli elenchi. Non è stato avviato l'inventario completo. MDI mappe, piano prospettico e
morfologia S restano non avviati/in pausa secondo le decisioni già registrate. Nessun push.

## MDI/SMARP: fase schema riuscita in HTTP, poi fermo — 2026-11-16

Via di Codex alla **sola fase schema** su `2c21550` (script `ac06138`, SHA-256 `b45ca5c8…`, 115/115 ripetuti da Codex).
Run-id `schema_20261116_http_ac06138`: **5 schemi su 5 acquisiti**, 5 tentativi, HTTP 200, 113 972 byte, circa 6 s.
Registro unico `INVENTORY_REGISTRY.json`: 20 tentativi cumulativi (15 della prima corsa + 5), 114,6 s, 0 righe.
Ricevute locali in `data/sharp/metadata_inventory_mdi/` (PHASE SHA-256 `b60b6153984f5384…`, registro `be9631cdf479e5b8…` al termine).
Nessuna registrazione della mappa, nessun conteggio o elenco di record.

Osservazioni per la verifica della mappa dei campi (da decidere con Codex, nessuna azione):
- passo documentato in tutte le serie (5760 s MDI, 720 s HMI); epoche: SMARP CEA, SMARP 96m e SHARP CEA
  1993.01.01_00:00:00_TAI (griglie allineate, 96 min = 8 × 12 min), fd_M_96m e fd_Ic_interp 00:00:30;
- geometria: NAXIS non è una keyword (segmenti VAR×VAR); lo schema documenta CRPIX come centro della patch rispetto
  all'angolo e CRVAL1/2 come longitudine/latitudine al centro della patch: il centro è documentato, mentre
  l'inviluppo dei riquadri richiede una regola per le dimensioni (da decidere, eventualmente con emendamento);
- prodotto 1/5 min: fd_M_96m_lev182 espone INTERVAL («Observable integration interval», s) e DPC («MDI
  DataProductCode»), candidati documentati; il collegamento SMARP → sorgente è il link MTARP verso mdi.lostarp_96m,
  serie non ammessa dal piano; T_REC di SMARP e di fd_M differiscono di 30 s per epoca, quindi l'abbinamento per
  tempo entro 1 s dovrà usare T_OBS solo se documentato come equivalente.
Limitazione nota (Codex): seed_registry non recupera i byte di un corpo parziale nei registri per corsa interrotti;
irrilevante ora (unico registro precedente chiuso, 0 byte), da correggere prima di migrare registri interrotti.

## MDI/SMARP: diagnosi dell'accesso a JSOC (passi 1-2), poi fermo — 2026-11-16

3 tentativi di rete su 6 consentiti, ricevuta `results/MDI_SMARP_ACCESS_DIAGNOSIS/DIAGNOSIS.json` (file grezzi locali
in `data/sharp/metadata_inventory_mdi/access_diagnosis_20261116/`). Nessun proxy; Python, curl e openssl con la stessa
OpenSSL 3.0.2 (SECLEVEL 2, TLS ≥ 1.2). Esito: la negoziazione HTTPS predefinita (TLS ≥ 1.2) fallisce; una
negoziazione limitata a TLS 1.0, solo diagnostica, riesce (cifrario DHE-RSA-AES256-SHA) con un certificato
autofirmato e scaduto (CN localhost.localdomain); non tutte le versioni sono state provate (correzione di
formulazione in `results/MDI_SMARP_ACCESS_DIAGNOSIS/CORRECTION.md`). Non è specifico di Python. HTTP semplice risponde 200 con JSON (schema di
mdi.fd_Ic_interp, 16042 byte, trasferimento chunked, nessun reindirizzamento). Osservazioni per la revisione del
codice: unità del passo dichiarata nella keyword T_REC_step (units 's'), epoca 1993.01.01_00:00:30_TAI di
mdi.fd_Ic_interp (ogni serie conserva la propria). **Passo 3 (via di Codex): trasporto HTTP, unità del passo da
tutte le fonti documentate, registro unico per l'inventario (i 15 tentativi e i 108,9 s della prima fase restano
contabilizzati), test offline**; nessuna richiesta di rete, schema non rilanciato, in attesa di revisione.

## MDI/SMARP: sola fase schema tentata, lavoro fermato — 2026-11-16

Su richiesta dell'utente, dopo la verifica indipendente della correzione TLS di `5c5d8b4`
(SHA-256 `63495fb3c39dcab88844f77ff4d7004f5e1ef16fb712a3954de6d1a8b96d45ac`),
eseguita **soltanto** la fase schema con run-id `schema_20261116_5c5d8b4`.
La prova locale indipendente arresta l'handshake a circa 0,201 s su un limite di 0,2 s;
il timeout residuo del socket può precedere il watchdog (`idle_timeout`), senza sforamento significativo.
Ricevuta ufficiale offline già presente: 105/105, `399966b`.

Provenienza della fase reale: `1abb8a89f52a006e8dbdc0b9e7eb211633c0b6b8`, albero tracciato pulito,
piano congelato invariato. Intervallo UTC 13:46:15–13:48:03 (14:46–14:48 Europe/Rome).
**Nessuno schema acquisito:** cinque serie `schema_not_verified`; 15 tentativi, tutti con
`SSLV3_ALERT_HANDSHAKE_FAILURE`, zero byte di corpo e zero record. Nessuna attribuzione della causa
al server, alla rete o all'ambiente è stata verificata. `outcome=eseguita` ed exit code 0 della fase
non significano successo dell'acquisizione: `result.n_schemas=0` e `SCHEMA_STATUS.json` fanno fede.
Le ricevute, i consumi e i corpi vuoti restano locali in
`data/sharp/metadata_inventory_mdi/schema_20261116_5c5d8b4/`, compresi
`PHASE_schema_001.json`, `SCHEMA_STATUS.json`, `REGISTRY.json` e `raw/QUERY_LOG.jsonl`.
La proposta di mappa non è verificata né registrata. Nessun conteggio/elenco di record, export o FITS;
nessuna modifica del raccoglitore, dell'endpoint, dei protocolli o dei risultati scientifici.

**Fermarsi qui su MDI/SMARP**, come richiesto dall'utente; niente altri tentativi o fasi senza ripresa
esplicita. Prossimo argomento: output T5. Questa revisione non li ha aperti né interpretati; verificare
lo stato corrente delle altre sessioni prima di ripetere controlli già eseguiti. Studio S sempre in pausa.
Nessun push.

## MDI/SMARP: piano dell'inventario congelato — 2026-11-16

Piano definitivo `docs/MDI_SMARP_METADATA_INVENTORY_PLAN.md`, rinominato dal file `_DRAFT.md` dopo la
verifica esterna della rev. 2 (`c70e91d`) trasmessa dall'utente. Recepiti motivo dei tetti 1 GiB/90 min,
CRPIX FITS a origine 1 contro chiamata WCS a origine 0 e caso estremo dei retry oltre budget. Nessun
campo scientifico, soglia di associazione o tetto cambiato rispetto alla rev. 2; è esplicitata la prova
offline di equivalenza delle origini. Il piano ora è immutabile: nuove regole in emendamenti separati.
SHA-256 e commit dedicato in `docs/MDI_SMARP_METADATA_INVENTORY_FREEZE.json`, registrati dopo il commit
del piano e prima del codice. Il riferimento corrente è il file senza `_DRAFT`; le sezioni precedenti
nel tempo sotto restano storiche e il vecchio nome è consultabile in Git a `c70e91d` e `5563c8b`.
**Raccoglitore non scritto, nessuna rete o mappa acquisita.** Prossimo compito: codice separato,
prove offline e revisione del codice. Nessuna query, nemmeno schema, prima della fine della griglia T5
e del superamento di questi passaggi. Stato T5 non ricontrollato, risultati non aperti. Studio S
sempre in pausa; HMI, protocolli e output scientifici invariati. Nessun push.

## MDI/SMARP: inventario metadati, bozza revisione 2 — 2026-11-16

Recepita la sintesi in nove punti della revisione interna Codex e della revisione esterna Claude
(`docs/MDI_SMARP_METADATA_INVENTORY_PLAN_DRAFT.md`, §11). **Non congelata**, nessun raccoglitore scritto,
nessuna query JSOC o download. Full-disk/continuo annuali, HMI settimanale con ±6 min; profili minimi
nello storico; conteggi prima degli elenchi, sovrapposizione prima dello storico e ausiliari per ultimi.
Preventivo nominale verificato offline: 468 richieste di base, 868 con due riserve da 200, tetto 1000.
Proposte ex ante da rivedere: volume 1 GiB e tempo 90 min; 2 milioni di righe invariati. Byte/tempi
si misureranno soltanto nei primi elenchi con trasporto limitato durante la ricezione. Centro WCS completo,
overlap approssimato dei riquadri, grafi G5/G10 e completezza separati, prodotti ignoti con Q6 aperta;
127/137 di B21 sono contesto, non bersagli. **Nessuna rete, nemmeno schema, prima della fine di T5** e
della revisione di piano/codice. Prossimo: revisione della rev. 2, poi congelamento prima del codice.
S resta in pausa; HMI e risultati T3/T5 intatti, nessun risultato della griglia aperto. MANIFEST.txt
verificato rispetto ai file tracciati, invariato perché nessun file aggiunto/rimosso. Nessun push.

## MDI/SMARP: bozza del piano dell'inventario metadati — 2026-11-16

Preparata `docs/MDI_SMARP_METADATA_INVENTORY_PLAN_DRAFT.md`, revisione 1 **non congelata**, su richiesta
dell'utente. Nessuna query JSOC, nessuna acquisizione di metadati o mappe e nessun codice del raccoglitore.
Definisce serie e periodi, fase schema con mappa dei campi da verificare prima dei record, copertura e
qualità distinte dalle mappe recuperabili, origine MDI 1/5 minuti anche ignota, associazioni TARP–HARP
candidate con ambiguità, tetti e controlli. Consultate soltanto documentazione locale e fonti pubbliche.
Prossimo: revisione della bozza; congelamento solo dopo la revisione, poi codice/prove offline e revisione
prima delle interrogazioni. HMI e T3/T5 invariati; nessun risultato della griglia T5 aperto da questo lavoro.
MANIFEST.txt riallineato all'elenco dei file tracciati più la nuova bozza; include anche 24 voci preesistenti
che mancavano nell'elenco, senza aprire o modificare quei file. Nessun push.

## MDI/SMARP: raccoglitore dell'inventario scritto, prove offline superate — 2026-11-16

Piano congelato `9269c10` (SHA-256 `a31de02a…`, ricevuta `b276502`). Raccoglitore `scripts/mdi_smarp_inventory.py`
(commit finale `0ae058ada181`): trasporto proprio limitato, registro persistente, finestre e preventivo, ordine
sovrapposizione → storico → ausiliari, mappa dei campi da registrare dopo lo schema, WCS con origine esplicita,
grafi 5°/10°. Selftest offline 67/67 con un finto JSOC locale e un catalogo sintetico dall'inizio alla fine
(ricevute in `results/MDI_SMARP_INVENTORY_SELFTEST/`). **Nessuna query JSOC.** La revisione del codice di Codex
su `0ae058a` ha trovato otto difetti con controesempi sintetici; corretti senza cambiare il piano (commit `4402ea8722e5`),
selftest 88/88 con una regressione per ogni controesempio. Seconda revisione (su `4402ea8`): cinque difetti
residui corretti (`d3d7854`); la sua ricevuta ufficiale è fallita per una gara fra thread nei test (conservata), corretta in `ba359cd`, selftest 95/95 ripetuto 8 volte (ricevuta `0218e8f`). Terza revisione (su `ba359cd`): tre problemi corretti (`b54f80f`), selftest 104/104. Quarta revisione (su `b54f80f`): handshake TLS sotto il watchdog (`5c5d8b4`), selftest 105/105. Prossimo: via di Codex alla rete.

## MDI/SMARP: studio aggiornato dopo la seconda revisione — 2026-11-16

`docs/MDI_SMARP_FEASIBILITY.md` aggiornato (§8): codice dei cicli oltre la sola fase e segno (`samples()`,
`CH`), rumore per prodotto (mappe di 1 e 5 min), condizioni della relazione 1,40 di Liu et al. 2012 (riportate
dal revisore, testo non accessibile a noi), Kosovich et al. 2024 verificato (dieci regioni, tabella 2),
bersaglio esplicito della potenza prospettica di T3, copertura nominale del ciclo 23 con la lacuna del 1998 e
il limite SMARP di ottobre 2010. Prossimo passo indicato: inventario limitato dei metadati (piano prima,
nessun download). Nessuna query eseguita.

## Sintesi HMI consolidata; prossimo: bozza del piano prospettico — 2026-11-16

`docs/HMI_QUENCHING_SYNTHESIS.md` consolidata come documento interno (proxy e sua lettura morfologica, T3 non
deciso, T5 descrittivo e rinviato con i risultati di potenza, che cosa non ripetere, sequenza decisa). Prossimo
passo concordato con Codex: **bozza di un piano prospettico** da rivedere prima dei calcoli, con i vincoli di
Codex: osservazioni solari aggiuntive (regioni, rotazioni, anni), non repliche Monte Carlo; bersaglio = riduzione
prescritta del 20 % (pendenza T5 ≈ −0,103·η̄); incertezza fra strumenti dipendente da attività e tempo; 50 % come
obiettivo operativo da motivare; prima stima analitica, poi simulazioni; un guadagno insufficiente per T5 non
esclude l'utilità di MDI per T3 o per il catalogo. MDI operativo (errore TLS da risolvere) e morfologia di S in
pausa. Nessun push.

**Piano prospettico CONGELATO come piano conservato, non avviato** (`docs/PROSPECTIVE_INFORMATION_PLAN.md`, rev. 4 dopo
la revisione di `62661f2`: scarto di ciclo −1/0/+1 con HARP 7379, strati vuoti osservati conservati, emisferi mai
uniti, β di T3-A come coefficiente di Joy comune, j sull'elenco finale; valori registrati m₂₃ 1996-08, massimi
2014-04 e 2024-10, finestra analoga 2016-03 → 2021-02). Priorità attuale: dati reali MDI. Storia della bozza
(`docs/PROSPECTIVE_INFORMATION_PLAN_DRAFT.md`, rev. 2 dopo la revisione di Codex
della rev. 1 (`630e6dc`): T3 con matrice e varianza proprie, modelli (a) attuale / (b) protetto / (c) distorsione
limitata con parametro dichiarato, generatore per ricampionamento congiunto di celle HMI, quantili HMI fissi,
frequenze con il segno della distorsione, algoritmo univoco per la fase B. Rev. 3 dopo la revisione di `c4247d0`
(solo definizioni): (c) come analisi di sensibilità, matrici esatte per T5 e per le famiglie T3 A e J, posti vuoti,
fase convenzionale e trasferimento di E1, ordine fisso di unione degli strati, singoletti, realizzazione decima,
scale degli scarti su E0 (tilt: 2,107° da P3 C1). Non congelata, nessun calcolo; in attesa di revisione.

## T5 potenza: risultati letti — 2026-11-16

Esecuzione unica (`44633cb`, 10:38–13:31, 9000 unità, 0 errori tecnici), output `0a6853a`, controllo
indipendente 30/30 (`b12abdb`, `2fb9bd5`), rapporto `docs/T5_POWER_SENSITIVITY_RESULTS.md`. In sintesi, per questi
generatori: M vicino al nominale dei falsi verdetti in 8 configurazioni su 9; riduzione del 20 % riconosciuta da M
al più ~19 % (scala 0,5), 8–11 % alla scala P2f; la forma dello scenario non cambia la potenza di M; O (varianza
nota) non riconosce più di M; G e B riconoscono di più ma con falsi verdetti in eccesso in varie configurazioni
(B fino al 12,2 %). La bassa frequenza persiste con la varianza vera della stessa WLS; stimatori diversi non
esclusi, nessuna graduatoria fra metodi. Revisione di Codex recepita (§7 del rapporto); **Decisione registrata: esito
(ii), rinvio operativo di T5** (§8 del rapporto), risultati conservati, percorso chiuso senza nuovi tentativi.
Prossimo indicato da Codex: sintesi scientifica HMI (proxy, T3, stato descrittivo di T5, limiti morfologici);
poi scelta fra un metodo diverso per HMI e l'estensione MDI (beneficio non quantificato). Raccoglitore MDI in attesa del via di Codex alla fase schema. Nessun push.

## Morfologia di S: bozza di piano — 2026-11-16

**In pausa per decisione dell'utente (2026-11-16):** revisione 3 (`20a3a46`, opzione ridotta, 206 schede, circa 0,3 M token) da inviare a Codex più avanti, insieme alla storia delle revisioni; nessun congelamento, nessuna scheda.

Bozza non congelata `docs/PROTOCOL_HMI_MORPHOLOGY_S_DRAFT.md` (rev. 2 dopo la revisione di Codex: rilettura delle 101 HARP note, 281 schede, lettore 2 distribuito anche sullo strato certo, formule e bootstrap senza reimmissione; costo da decidere prima del congelamento; rev. 1), permessa dalla regola operativa dello
studio morfologico precedente (§7 di `docs/MORPHOLOGY_RESULTS.md`). Prevalenza delle classi A2 in S (2485
record, FITS tutti locali) per conteggio, Φ e |S_BL|, e dipendenza dall'attività; strato certo delle 101 HARP
già lette, 6 strati (terzili di Â × Φ sotto/sopra la mediana), 30 per strato; nessuna esclusione né nuova
pendenza. In attesa della revisione di Codex; nessuna scheda generata. In parallelo Codex rivede lo studio
MDI/SMARP. La griglia T5 è in corso (avviata alle 10:38, PID 1408314).

## T5 potenza: dopo A2, preliminari completi; griglia da avviare dopo la revisione — 2026-11-16

Emendamento A2 `6024237` (SHA-256 `df4912c0…`), script corretto `f19cf15` (SHA-256 `62ca2da4…`),
supplemento diagnostico `scripts/t5_power_gate_diagnostic_v2.py` (descrittivo). Ricevute in
`results/T5_POWER_SENSITIVITY_PRELIM/` (`a8d2cfb` e successivo): selftest 67/67 superato; nuova porta (A2 §1a,
percorso P2f originale, 10⁻⁹) 40/40 superata con differenze nulle; benchmark 36 unità, 0 errori tecnici,
0 errori previsti, 0 casi di confine, T̂ = (1000/12)·Σ t̄_n = (1000/12)·110,99 s ≈ 9250 s ≈ 2,57 h (limite 8 h).
La prima porta resta «non superata». `--run` trova le tre ricevute con lo stesso legame ma **non è stato
lanciato**: attende la revisione del codice e degli esiti preliminari. Nessun push.

## T5 potenza: script, selftest superato, porta di compatibilità NON superata — 2026-11-16

Emendamento A1 (`8dc6d48`, SHA-256 `60323789…`) su piano `4b67632` (`fac76b1a…`). Script
`scripts/t5_power_sensitivity.py` in `b769892` (SHA-256 `88df7231…`). Ricevute in
`results/T5_POWER_SENSITIVITY_PRELIM/` (commit `9a64e88`): **selftest 53/53 superato**; **porta 36/40, non
superata**. I 20 cataloghi nulli dello scenario 7 coincidono esattamente. In 4 dei 20 cataloghi dello
scenario 2 a −0,1, lo SE di M differisce da `VALIDATION_RAW` di 3·10⁻⁶–1,5·10⁻⁵ relativo, con β̂ entro
1,6·10⁻¹⁵ e verdetti uguali. Per il piano §6.6 la sequenza si è fermata: **benchmark e griglia non
eseguiti**. Diagnosi non pre-registrata (`bf24b7f`, output `438ef56`, nessuna riclassificazione): il
percorso P2f originale riproduce lo SE esattamente su 20 casi su 20; il percorso dello script differisce in η_c solo per
l'ordine degli arrotondamenti (max|Δη_c|/η̄ = 1,03·10⁻¹⁵); una sonda che scala gli ingressi di 10⁻¹⁵ cambia
lo SE di M fino a 1,18·10⁻⁵ su 20 casi su 20. Formulazione corretta (A2 §2): nei casi perturbati esaminati,
differenze di arrotondamento possono impedire la riproduzione dello SE entro 10⁻⁹ (in 15 casi su 20 gli
ingressi differiscono e lo SE coincide al bit); 10⁻⁵ è l'ordine osservato, non un limite; l'attribuzione
alla sola REML non è isolata (M contiene anche la funzione di varianza). Emendamento A2
(`docs/T5_POWER_SENSITIVITY_PLAN_A2.md`) dopo la revisione di Codex di `ca71107`: porta divisa in
compatibilità storica (percorso P2f originale, 10⁻⁹) e correttezza dell'iniezione (anche risposte
individuali e residui entro cella), ricevute legate alla configurazione, differenze fra metodi, validità
centrale delle righe. Nessun push.

## T5: piano di sensibilità della potenza congelato — 2026-11-16

Dopo la nota di fattibilità (rev. 2) e la sensibilità del proxy (`39c010c`, risultati `61e0aed`), il piano
`docs/T5_POWER_SENSITIVITY_PLAN.md` è **congelato** dopo la revisione di Codex della bozza `bb61bc0`
(sette gruppi di correzioni recepite, §10): pendenze lineari esatte uguali a quelle dello scenario,
rumore davvero appaiato (9000 cataloghi di rumore, cinque segnali sopra), G con bersaglio WLS comune e
bias riportato, B con i soli verdetti e p-value (adattatore delle unità da verificare), O come
riferimento a varianza nota, incertezze Monte Carlo corrette, errori previsti distinti da quelli tecnici.
Nessun codice scritto, nessuna simulazione. Prossimo: revisione di Codex del testo congelato, poi
`scripts/t5_power_sensitivity.py` con selftest, porta e misura della durata prima del lancio. T5
descrittivo, T3 non deciso. Nessun push.

**Artefatti di scambio con Codex (2026-11-16).** Le note di scambio e la cartella `reviews/` nel repository MWO (artefatti delle verifiche di Codex citati in sei documenti BL) sono state spostate nel cestino su richiesta dell'utente e **ripristinate lo stesso giorno** ai percorsi originali; i 119 file citati coincidono con gli SHA-256 registrati prima della rimozione (`docs/CODEX_REVIEW_ARTEFACTS_REMOVED_2026-11-16.csv`, conservato come registro). Le citazioni nei documenti BL sono di nuovo valide. Le note per Codex si scrivono ora nella chat e l'utente le copia.

## T5-D2: risultati letti e interpretati — 2026-11-15

`docs/T5_ORACLE_RESULTS.md` compilato su `27a9c7d` (§6 tabelle, 46 gruppi e 38 confronti;
§7.1 lettura secondo A1; §9 conclusioni). Scenario 7 sotto nulla: A0 R 0,858, falsi 3,35 %;
A1a e A1b con cambiamenti piccoli rispetto ad A0; A2 R 0,981, falsi 1,94 % (conservativo); A3 simile ad A2; A2p R 0,855, falsi 3,02 %.
Prima riga della griglia A1: risultato compatibile con un ruolo principale della componente
temporale, senza una causa unica. A2p descrive solo l'approssimazione specificata. Con la
varianza vera, ai quantili 1,25/98,75 % e all'intervallo al 97,5 %, z è meno estremo del
riferimento normale (non è una descrizione dell'intera forma delle code). La lettura poggia su A2 e A3: i loro
SE (e quelli di A2p) sono stati poi ricalcolati in modo indipendente con esito superato (sotto); A1a e A1b no. T5 descrittivo, T3 non deciso.
Revisione: tre pareri di Codex e revisione di fase 2 su `8c7801a`, senza problemi bloccanti;
correzioni in `3a4add9`, `8c7801a` e `6e48f3c` (indicatore appaiato §6.5, formulazioni più caute),
verificate da Codex; rilievo 6 (segnaposto) chiuso nel commit successivo.
Ricalcolo indipendente degli SE di A2, A3 e A2p su tutti i 32000 cataloghi (nota `61f8884`, C1 `ed43694`,
script `39b7837`), esito **superato**: 91960 ok, 40 errori attesi concordanti, 0 discrepanze, 0 inattesi;
output `330d007`; rapporto §7.2, verificato da Codex. Limite residuo: A1a e A1b non ricalcolati.
Punto 5 (coerenza dei documenti di sintesi) fatto il 2026-11-15: PROJECT_STATUS, RESULTS_INDEX
(righe T5-D2, due commit segnaposto risolti), README_V84, sintesi HMI, ARTICLE_OUTLINE, CHANGELOG;
precisazioni di perimetro (scenario 7, dipendenze condivise, revisione non cieca) dopo la revisione Codex di `3ed58b2`;
nota storica in REPRODUCIBILITY_V84.
Il «comparatore» della riproducibilità di fase 1 era già concluso il 2026-11-13 (`ceb5d38`,
`3e24bc4`); non è un passo aperto. Aperti, da decidere con l'utente: nota per Paolo; revisione
esterna dello studio MDI/SMARP (rinviato); eventuale proposta di studio distinto su S; un eventuale
metodo per T5 richiede protocollo e validazione propri. Nessun push.

## T5-D2: controllo effettivo superato e output conservati — 2026-11-14

Corsa conclusa il 13/11 alle 18:45 (marcatore `fatto`). `t5_oracle_postcheck.py --check`
sul commit pulito `94606c6`: **54/54 controlli superati**, nessuna discrepanza, file
invariati durante la lettura; 22 righe A0 errore senza beta nel riferimento, dichiarate.
Quattro output `ORACLE_*`, `PRELIM_TESTS.csv` e `results/T5_ORACLE_POSTCHECK/` conservati
in Git **prima di leggere i risultati**: riepiloghi e riconteggi non ancora aperti né
interpretati. Prossimo: compilare `T5_ORACLE_RESULTS.md` e lettura secondo A1 (punto 4,
parte interpretativa), poi punto 5. Limite: SE dei bracci non ricalcolati. Nessun push.

## Revisione incrociata fase 1 (verificatore, scheletro, morfologia) — 2026-11-14

Claude Opus 5.5 ha esaminato `f38d351` in sola lettura, senza aprire gli
output `ORACLE_*`: [CROSS_REVIEW_2026-11-14.md](CROSS_REVIEW_2026-11-14.md).
Nessun problema bloccante per i punti 1–3 (non approva conclusioni T5-D2;
la prova esterna non colma il limite sugli SE dei bracci). Verificatore, ricevuta e protocolli invariati;
selftest ripetuto 77/77. Prova esterna conservata in
`scripts/t5_postcheck_external_probe.py` (10/10, fuori dalla ricevuta).
Morfologia: numeri riprodotti in modo indipendente, ma l'indipendenza delle
letture non è dimostrabile dai file. Precisazioni documentali applicate in
`T5_ORACLE_RESULTS.md` e `MORPHOLOGY_RESULTS.md`: limite degli SE dei bracci
non ricalcolati, lettura generale di A2′ del protocollo §7 non adottata (A1 §3),
ruoli dei lettori e sequenza dei blocchi C. Un secondo revisore ha condiviso
le conclusioni. Prossimi passi: punto 4 (`--check` in cartella nuova, poi
interpretazione) e punto 5 (coerenza finale). Nessun push.

## T5-D2: struttura del rapporto e richiesta di revisione pronte — 2026-11-13

Preparati `docs/T5_ORACLE_RESULTS.md` (BOZZA DI SOLA STRUTTURA) e
`docs/T5_ORACLE_REVIEW_REQUEST.md`. Le 46 righe delle tabelle, 22 sotto
nulla e 24 sotto effetto, contengono soltanto numerosita previste e campi
DA INSERIRE. Non attestano completamento o controlli della corsa.
Nessun output scientifico T5-D2 o tabella nel log aperto; nessun nuovo
calcolo e stato del processo non ricontrollato per questa preparazione.
Richiesta in due fasi: ora revisione del verificatore e della struttura
senza leggere risultati; dopo fine e controllo effettivo, revisione
dell'interpretazione. Per la morfologia resta la revisione incrociata del
rapporto gia disponibile, senza nuove classi o consenso. Nessun push.
I protocolli congelati e il produttore sono invariati. T5 descrittivo,
T3 non deciso; nessuna nuova applicazione reale autorizzata da questi file.

## T5-D2: verificatore separato pronto — 2026-11-13

Specifica `bd3616a` registrata prima del codice. Nuovo verificatore
`python/sharpbl/t5_oracle_postcheck.py`, codice finale `9bd1e2e`: 77/77
prove costruite a mano, su commit pulito; ricevuta e RUN1 (73/73 sul primo
codice) in `results/T5_ORACLE_POSTCHECK_SELFTEST/`. Suite ordinaria 60/60,
due avvisi attesi su input costante. Guida `docs/T5_ORACLE_POSTCHECK_README.md`.
Il produttore e i suoi output non sono stati modificati. **Output scientifici
T5-D2 non aperti, controllo effettivo non eseguito, nessun risultato letto.**
Dopo la conclusione della corsa, prima di interpretarla, usare il nuovo
verificatore con --check: rifiuta una corsa incompleta o una ricevuta obsoleta,
richiede cartella di output nuova e conserva anche i fallimenti. Tiene
separati commit del produttore e del controllore e controlla tutti i conteggi,
i momenti e gli appaiamenti. Non usare il verificatore storico come unica
verifica finale: ha il problema di parsing di null e controlli incompleti.
T5 resta descrittivo. Nessun nuovo protocollo inferenziale o push.

## T5-D2: specifica del controllo separato registrata — 2026-11-13

Prima del nuovo codice, registrati `docs/T5_ORACLE_POSTCHECK_SPEC.md` e la
fotografia SHA-256 degli input. Nasce dalla revisione del sorgente: parsing
di `null` e controlli incompleti nel verificatore storico. Nessun output
scientifico T5-D2 letto, nessuna simulazione o modifica al produttore.
Prossimo: implementare e provare il verificatore su casi costruiti a mano;
non eseguirlo ancora sulla corsa. T5 resta descrittivo. Nessun push.

## Morfologia: verifica interna del rapporto conclusa — 2026-11-13

Il rapporto `84099c2` è stato riesaminato dal medesimo autore con un codice
separato (csv/Decimal, senza comparatore originale): 553 verifiche superate,
nessuna discrepanza numerica. Corretta soltanto la presentazione di due
intestazioni Markdown e chiarito l'arrotondamento delle quote piccole.
Esiti in `docs/MORPHOLOGY_INTERNAL_REVIEW.md` e `results/MORPHOLOGY/REVIEW/`.
È una verifica interna, non una revisione esterna indipendente. L'accordo
primario resta 24/30, esattamente alla soglia operativa; la conclusione è
la sola proposta di uno studio distinto su S, non il suo avvio. Nessuna
lettura, tabella numerica o protocollo modificato. T5-D2 non esaminato.
Il blocco morfologico resta chiuso a questo livello descrittivo; eventuale
revisione esterna distinta e sviluppi futuri non sono avviati. Nessun push.


## Morfologia HMI conclusa — 2026-11-13

Confronto dei lettori e tabelle finali completati; rapporto
`docs/MORPHOLOGY_RESULTS.md`, dati `results/MORPHOLOGY/ANALYSIS/`.
229 verifiche superate; dieci impegni hash verificati prima del confronto,
originali intatti e copie pubblicate in `LOCKED_READINGS/`. Corrispondenza
codice–HARP pubblicata con hash originale. Codice/input `5d9094a`, primo
tentativo fermato dal controllo di unicita sui codici storici vuoti e
conservato; correzione `744eeec` prima del tentativo completato; output
`b660836` prima dell'interpretazione.

Classi primarie: 24/30 coincidenti, esattamente il minimo operativo; U
2/30 per lettore 1 e 3/30 per lettore 2. C: 24/30 sulle tre categorie
(incluso un NV concorde), 23/27 sui casi valutabili da entrambi. Quote B
del proxy totale del gruppo: 8,10%, 15,19%, 16,19% in 24N, 24S, 25N;
conteggio conservativo 7,09%, 15,186%, 16,194%. Regola soddisfatta in due
gruppi su tre: consente soltanto di proporre un piano distinto su S.
Nessuna classe di consenso o esclusione; 25S storico mantenuto separato.
Il compito si arresta qui. Prossimo: revisione del rapporto; nessun nuovo
studio su S o quenching avviato. T5-D2 gestito dall'altra sessione,
output non letti in questo lavoro. T3/T5 invariati. Nessun push.

Le sezioni di passaggio precedenti sotto sono cronologiche e superate
quanto allo stato delle letture morfologiche.


## Morfologia: lettore 2, secondo passaggio bloccato — 2026-11-13

Il lettore 2 (gpt-6.1-sol, ragionamento alto richiesto) ha completato i
30 indicatori C e le note visive sul contatto della maschera con il bordo.
Sono in `results/MORPHOLOGY/private/CENTROIDS_READER2.csv`, con metadati
separati; impegni pubblici in `CENTROIDS_READER2_COMMITMENT.csv` e descrizione
in `docs/MORPHOLOGY_READER2_CENTROIDS_RECEIPT.md`. Avvio dopo il blocco delle
classi primarie di entrambi. File primari e taratura del lettore 2 invariati
nei loro hash. Nessuna etichetta del lettore 1 o corrispondenza codice–HARP
consultata. I giudizi C restano privati fino al blocco del lettore 1; poi
confronto originale prima della discussione dei disaccordi. Nessun push.


## Morfologia: lettore 2, 30 classi primarie bloccate — 2026-11-13

Questa sessione Codex (`gpt-6.1-sol`, ragionamento alto richiesto) ha letto
le 30 sole mappe nell'ordine `READING_ORDER_READER2.csv`, applicando A2.
Classi e motivazioni in `results/MORPHOLOGY/private/PRIMARY_READER2.csv`;
metadati nel file `PRIMARY_READER2_META.json`. Hash pubblici in
`results/MORPHOLOGY/PRIMARY_READER2_COMMITMENT.csv`, registrazione in
`docs/MORPHOLOGY_READER2_PRIMARY_RECEIPT.md`. Nessuna etichetta o riepilogo
delle 90 nuove del lettore 1 consultato; corrispondenza codice–HARP non
aperta; nessuna immagine con centroidi aperta. Le classi restano private
per non influenzare il lettore 1. Prima dei centroidi verificare il blocco
di entrambe le letture primarie. Gli originali non si modificano. Nessun push.


## Taratura morfologica lettore 2 — 2026-11-13

Le 11 mappe di riferimento sono state lette da questa sessione Codex,
modello `gpt-6.1-sol`, ragionamento alto richiesto. Classi e motivazioni
sono bloccate nei file privati `CALIBRATION_READER2.csv` e
`CALIBRATION_READER2_META.json`; hash pubblici in
`results/MORPHOLOGY/CALIBRATION_READER2_COMMITMENT.csv` e descrizione in
`docs/MORPHOLOGY_READER2_CALIBRATION_RECEIPT.md`. Etichette del lettore 1
non aperte; note le classi storiche e il suo riepilogo aggregato gia
comunicato dall'utente (esposizione dichiarata). Nessuna delle 90 nuove
schede o delle versioni con centroidi aperta. Prossimo passo: confronto
delle due tarature bloccate, con eventuali decisioni comuni in un file
separato; le classificazioni originali non si modificano. Nessun push.


## Priorità corrente — HMI e quenching (2026-11-13)

**T5-D1 completato, una sola esecuzione (2026-11-13).** Piano congelato
`85df0e9`, codice `3c73595` (albero pulito), output `dcc7219`. **201/201
controlli superati**, incluse 26 prove costruite a mano; 17 gruppi e 74000
righe T5, 42 errori originali conservati. Risultati in
`docs/T5_DIAGNOSTIC_RESULTS.md`. Nessuna simulazione o risposta reale nuova.
Con salti di 20 CR, media(SE²)/varianza empirica circa 0,858 sotto nulla e
0,852–0,882 sotto effetto; bias piccolo rispetto alla dispersione. La forma
delle code conta: non è identificata una singola componente responsabile.
**T5 resta descrittivo.** Dopo revisione dei risultati, l'eventuale passo
successivo è un piano separato per covarianza temporale e varianza individuale
note; nessun oracolo avviato. Il protocollo T5-D1 congelato resta byte-identico,
SHA-256 `53a05c1fd7c0315eca52b508472c59d6df485c29c8ef2b717e81264d3d600e5d`.
Push non richiesto. Non rilanciare il diagnostico sopra gli output esistenti.

Decisione dell'utente: concentrarsi sulla misura della sorgente BL e sul
quenching con HMI. **MDI/SMARP e la degradazione HMI→MDI sono rinviati**, inclusa
la prova sintetica di precisione. Le bozze restano conservate, non congelate.
Il rinvio non è abbandono: il ciclo 23 potrebbe estendere sostanzialmente la
serie, ma confrontabilità e beneficio statistico restano da verificare.
MDI non è una garanzia di potenza né l'unica via concepibile per migliorarla.

Sono pronti i documenti di lavoro:
- `docs/HMI_MEASUREMENT_ASSESSMENT.md`: definizioni, controlli acquisiti e limite
  dell'interpretazione del tilt nei complessi HARP;
- `docs/HMI_QUENCHING_SYNTHESIS.md`: risultati T3/T4/T5, sensibilità già fatte e
  lacuna residua; distingue P2 storico da P2f;
- `docs/PROTOCOL_HMI_MORPHOLOGY.md`: bozza limitata alle 120 schede già
  prodotte (30 25S storiche, 90 da leggere). Nessuna nuova classificazione,
  selezione o aggregazione eseguita; piano morfologico non congelato.
- `docs/T5_JUMPS_DIAGNOSTIC_DESIGN.md`: traccia del blocco metodologico T5;
- `docs/PROTOCOL_T5_DIAGNOSTIC_SAVED_OUTPUTS.md`: T5-D1 congelato ed eseguito,
  con lista input `docs/T5_DIAGNOSTIC_INPUTS_SHA256.csv` e risultati
  `docs/T5_DIAGNOSTIC_RESULTS.md`; nessuna modifica alla procedura M.

T3 è già applicato una volta: −3,59° per unità di attività, intervallo nominale
97,5% [−10,58°; +3,41°], **non deciso**. T5 non è validato e resta descrittivo.
Le sensibilità non sono nuove conferme. Il filtro S4 «una NOAA» non è una
classificazione di bipoli. Nessuna nuova applicazione di T3 o modifica a P1.

**Priorità corrente e percorso complementare:**
- **T5, diagnosi iniziale conclusa:** rivedere risultati e implementazione
  di T5-D1. Il quadro è coerente con scala di SE insufficiente nello scenario
  7, ma lo scenario 10 mostra che R<1 non implica da solo falsi verdetti in
  eccesso. Per separare le cause serve eventualmente un piano nuovo con
  componenti del generatore note. Non applicare correzioni di scala ai dati
  reali. Output e semi P2f sono sviluppo, non validazione futura indipendente.
- **Morfologia, per interpretare la misura:** rivedere e congelare la bozza
  revisione 2 prima di figure o letture. Sono proposti mappe senza risultati
  numerici, ordine casuale, seconda lettura indipendente di 30 casi e due
  passaggi distinti: morfologia, poi posizione dei centroidi. La vecchia classe
  C è un indicatore secondario e non entra nel criterio operativo. La regola
  proposta per un eventuale studio su S è ancora da congelare; non autorizza
  nuovi fit né esclusioni. Le 30 letture 25S restano storiche e separate.

La potenza simulata non predice con certezza un futuro esito T3. Il problema
metodologico di T5 e quello morfologico hanno scopi distinti; il secondo non
risolve automaticamente il primo.

Prima di ogni nuovo compito consigliare il modello e attendere la scelta
dell'utente. Nessun push senza richiesta. Preservare il CSV non tracciato
`results/P2/P2E_VALIDATION_RAW.csv`.

**Prompt di ripresa corrente:**

> Riprendi SHARP BL in /home/gianluca/BL_v8_3_stable. Leggi AGENTS.md,
> questa sezione e i documenti HMI indicati sopra. Verifica Git. MDI e
> degradazione rinviati. T3 già eseguito, non deciso; T5 descrittivo. Il passo
> T5-D1 è concluso: leggi docs/T5_DIAGNOSTIC_RESULTS.md e il protocollo
> congelato. Prossimo passo: revisione, poi eventuale piano separato con
> componenti note. Non rilanciare il diagnostico o nuovi fit e non applicare
> T5 ai dati reali. La morfologia resta un percorso complementare.
> Prima consigliami il modello e attendi la mia scelta. Nessun push richiesto.

---

## Cronologia del 2026-11-13 (storica; priorità corrente sopra)

**Stato:** la **validazione P2f è terminata** (esecuzione unica, 2026-11-11 14:46 → 2026-11-12
13:45, provenienza `5c3b664`, albero pulito, protocollo `8f030010…`). Controllo indipendente
superato (23 su 23, riconteggio identico), output committati (`11b71f4`), risultati in
`docs/P2F_VALIDATION_RESULTS.md`, revisione esterna dello ZIP `0f12ed1` senza discrepanze (53
asserzioni, script separato). Nessun processo in esecuzione.

**Esito (protocollo §5, alla lettera):**
- **T3: criteri di validazione superati negli scenari provati** (falsi verdetti 1,61–2,97 % nei 12
  scenari; copertura 96,60–98,15 %, coda inferiore ≤ 1,85 % nelle 16 combinazioni). Potenza bassa:
  4,55–11,10 % all'effetto di riferimento −0,2·γ0, 2,25–34,70 % sugli effetti provati.
- **T5: non validato**: scenario 7 (salti di 20 CR) con 3,35 % di falsi verdetti (limite 3,0 %) e,
  a −0,3, copertura 96,10 % e coda inferiore 2,30 %. **Resta descrittivo**.
- Dichiarazioni: la tabella di decisione è stata vista nell'ultima riga del log prima del
  controllo indipendente; la colonna `status` di `results/P2F/POST_CHECKS*.csv` dice «pilota di
  sviluppo» per un'etichetta ereditata (output non riscritti).

**Fatto il 2026-11-13 alle 09:05: applicazione di T3 ai dati reali** (una esecuzione, commit
`42fcd01`): β̂_T = −3,59° per unità di Â (−0,149·γ0), intervallo a livello nominale 97,5 %
[−10,58°; +3,41°], esito **non deciso**, nessun effetto della griglia escluso; 8 sensibilità non
validate tutte negative e tutte comprendenti zero. Risultati in `docs/P2F_RESULTS.md`; T5 rifiutato
dallo script. **Prossimo passo: revisione esterna di `docs/P2F_RESULTS.md`** (ZIP aggiornato).

(Storico) Comando usato, autorizzato dal revisore dopo il commit dei risultati: `OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_apply.py --test T3 --real`
(una sola esecuzione; lo script rifiuta T5, richiede `POST_CHECKS.csv` superato e legato agli stessi
output e protocollo). Poi `docs/P2F_RESULTS.md` con formulazioni prudenti: «supportato» non
attribuisce un meccanismo; «non deciso» non è assenza (potenza 5–11 % a −0,2); esclusione di un
quenching ≥ δ solo se l'estremo inferiore dell'intervallo è > −δ·γ0; sensibilità non validate.
Poi ZIP e revisione. Push solo su richiesta dell'utente.

**Fatto il 2026-11-13:** correzioni di formulazione di `docs/P2F_RESULTS.md` dopo la revisione esterna
(`1a22e09`); **controllo completo delle HARP dominanti** (`36676a9`, `docs/DOMINANT_HARP_RESULTS.md`):
120 HARP, valori P1 riprodotti, nessun errore confermato (esame visivo delle schede non ancora
fatto), sensibilità a maschera e pesatura ≤ 3,4 % di Σ|S_BL|, gruppo 25S sopra la soglia di
priorità del 25 %; revisione esterna senza discrepanze (101 controlli) e correzioni recepite
(`8e097f1`); **esame visivo delle 30 schede di 25S** fatto e documentato HARP per HARP
(`docs/DOMINANT_HARP_VISUAL_25S.md`), con seconda lettura esterna e cinque correzioni recepite
(validità P1 contro filtro P2, classi D distinte, conteggi riallineati, nessuna conclusione
sull'appartenenza ad altre HARP, bordo inferiore): nessun errore confermato; complessi e centroidi tra
concentrazioni tra le dominanti; nessuna azione sul catalogo senza un piano proprio. **Push fatto su
richiesta dell'utente il 2026-11-13** (`e6f7419`). Poi **verifica di riproducibilità fase 1 superata**
(`docs/REPRO_PHASE1_RESULTS.md`): i 5 CSV delle figure P1 rigenerati byte-identici da `120f852`;
comparatore corretto due volte prima dei confronti successivi (regola §2 sulle chiavi mancanti; NUL
rifiutati e confronti esatti senza float64 dopo la revisione esterna), tre confronti conservati.
Poi **studio di fattibilità MDI/SMARP** completato (`docs/MDI_SMARP_FEASIBILITY.md`): fonti primarie
verificate, tabella delle differenze strumentali, 11 questioni da verificare; esito: fattibilità
plausibile, confrontabilità e guadagno statistico non misurati; passo consigliato: esperimento solo
HMI (Br contro LOS/μ e LOS degradato a MDI). Prossimo: revisione esterna dello studio, nota per Paolo.

**(Storico) Dopo:** controllo delle HARP dominanti (piano `f805c5a`, codice pronto, prova tecnica in
`results/DOMINANT_TRIAL_2HARP/`; eseguire da commit pulito con
`nice -n 10 .venv/bin/python python/sharpbl/dominant_harp_check.py`); fase 1 della verifica di
riproducibilità (`docs/REPRO_PHASE1_PLAN.md`, congelato in `0f51e61`, solo dopo P2f); studio
MDI/SMARP in bozza (`docs/MDI_SMARP_FEASIBILITY.md`).

**Bozza esperimento HMI, revisione2 — 2026-11-13:**
`docs/PROTOCOL_HMI_LOS_SENSITIVITY_DRAFT.md`, non congelato. Recepiti i rilievi:
esperimento solo descrittivo, senza criterio automatico per avviareMDI; precisione
preventiva con risposte sintetiche prima dei nuovi dati; campioni annidati80/160/320
sovracampionando le codeA e mantenendo il centro (N finale da scegliere); R3–R5 su
sottocampione; pesiΦ principali, Φ/pi sensibilità con obiettivo distinto; perdite
per fasciaA e gruppo; spostamenti medi oltre alle pendenze; minimi di disegno e
scaling del rumore conμ. Primo passo: revisione della bozza e piano separato della
prova di precisione, con codice solo dopo registrazione. Nessun nuovo calcolo,
selezione o download svolto; nessuna nuova applicazioneT3. Push non fatto.

**Modo di lavorare:** per ogni nuovo compito l'utente sceglie prima il modello (l'agente lo
consiglia e aspetta). Le osservazioni del revisore esterno arrivano incollate dall'utente; di norma
si adottano.

**Prompt precedente (superato dalla priorità HMI sopra):**

> Riprendi SHARP BL v8.4 nel repository /home/gianluca/BL_v8_3_stable, branch
> v8.4-python-gianluca. Leggi AGENTS.md e docs/HANDOFF.md (sezione "Passaggio di consegne del
> 2026-11-13"), poi docs/P2F_VALIDATION_RESULTS.md e docs/PROTOCOL_P2F_VALIDATED_TEST.md §7.
> Verifica lo stato di Git. T3 è già stato applicato ai dati reali (docs/P2F_RESULTS.md); prossimo
> passo: revisione esterna di docs/MDI_SMARP_FEASIBILITY.md, poi nota per Paolo. Prima di ogni compito consigliami il modello e aspetta. Non fare il push senza
> la mia richiesta.

---

**Aggiornamento 2026-11-13 (pomeriggio):** dopo T5-D1 (`1b52769`) il piano T5-D2 dei controlli oracolo
(`docs/PROTOCOL_T5_ORACLE.md`) è stato **congelato in `f77d39b` senza revisione esterna**, perché
l'utente era assente e aveva chiesto di procedere. La revisione esterna successiva ha portato
l'**emendamento A1** (`docs/PROTOCOL_T5_ORACLE_A1.md`): A1 diviso in A1a (sola varianza individuale
vera, parametri temporali di A0) e A1b (con ristima REML), regole di lettura come compatibilità e
non come attribuzione causale, A2' come approssimazione AR(1) lag per lag con il limite κ = 0,98.
A1 è non cieco rispetto a una prova tecnica su 4 cataloghi. Codice `2bf262f`; controlli preliminari
superati (A0 riproduce la validazione su 50 cataloghi, covarianza dei salti verificata). **Esecuzione
unica in corso**: avviata il 2026-11-13 alle 13:56:57, PID 1141311, log `logs/t5_oracle.log`
(32 000 cataloghi, stima 1,5–3 ore). A fine esecuzione: `diag_t5_oracle.py --check` **prima** di
leggere le sintesi, poi commit degli output e `docs/T5_ORACLE_RESULTS.md`. T5 resta descrittivo.

---

## Passaggio di consegne del 2026-11-11, sera (storico)

**Stato:** il **pilota di sviluppo di P2f** è terminato (esecuzione unica, 10:17–12:06, commit del
codice `67058f6`), gli output sono committati, il controllo indipendente è stato eseguito prima
dell'interpretazione (tutti i 20 controlli superati) e i risultati sono in
`docs/P2F_PILOT_RESULTS.md`. Questa frase riguarda la conclusione del pilota; la validazione successiva è descritta sotto.

**Esito del pilota** (regole registrate nel piano §5 e A1 §4, applicate alla lettera):
- candidata **M** (funzione di varianza + REML AR(1) bivariata sulle medie di cella, decisione
  analitica) **mantenuta** per T3 (massimo 24 falsi verdetti su 1000) e T5 (massimo 34, scenario a
  salti); `errore` ≤ 0,1 %;
- candidata **B** (wild cluster bootstrap ristretto, blocchi di 13 CR, Webb, CR1) **non
  mantenuta**: oltre 40 falsi in 7 scenari su 9 (T3) e 8 su 9 (T5), già 32 e 54 su 1000 senza
  componente temporale;
- **scelta: M per T3 e per T5**. Potenza di M bassa in T3 (≤ 0,24 agli effetti −0,1…−0,3·γ0),
  moderata in T5 solo a −0,3·η̄ (0,45–0,65).
- È **sviluppo, non validazione**: nessun verdetto, nessun dato reale usato. B non va «aggiustata»
  dopo aver visto i risultati; una variante richiede un nuovo piano, dichiarato non cieco.

**Documenti di questa fase**
- Piano `docs/P2F_PILOT_PLAN.md` (`83b0fc1`), emendamenti A1 (`59971e7`) e A2 (`48039d7`, non
  cieco rispetto al test preliminare 2 fallito; esecuzione 1 conservata come `PRELIM_*_RUN1.csv`).
- Nota d'implementazione `docs/P2F_PILOT_IMPLEMENTATION_NOTE.md` (`211b3ed`, registrata durante
  l'esecuzione, prima degli esiti): tre convenzioni non fissate dal piano (origine dei blocchi di
  B per T5 alla CR 2097; componenti per rotazione separate per T3 e T5; mediana di Φ sul
  disegno), conteggi del disegno in `results/P2F_PILOT/DESIGN_CHECKS.csv`, controllo di
  finitezza e riconteggio (`python/sharpbl/p2f_checks.py design | raw | diag`).
- Risultati `docs/P2F_PILOT_RESULTS.md`; voci in `CHANGELOG.md` e `docs/RESULTS_INDEX.md`.

**Stato al 2026-11-11, ore 14:55 (aggiornamento):** il protocollo P2f è **congelato**
(`docs/PROTOCOL_P2F_VALIDATED_TEST.md`, commit `500c56a`, SHA-256 `8f030010…`); il codice è stato
scritto dopo (`python/sharpbl/p2f_validation.py`, commit `ed90e15`); i sei test preliminari
sono stati superati due volte, su `ed90e15` (conservati come `results/P2F/PRELIM_*_ed90e15.csv`)
e su `5c3b664` (`results/P2F/PRELIM_*.csv`, stessi valori). La **validazione è in esecuzione**:
avviata il 2026-11-11 alle 14:46:47 in modo distaccato, **PID 968943**, 12 processi con
`OMP_NUM_THREADS=1`, log `logs/p2f_validation.log` (avanzamento ogni 2500 cataloghi su
152 000), commit del codice e della provenienza **`5c3b664`**, albero pulito; stima iniziale 22:00–23:30 superata: non usarla per prevedere la fine.
Ultima lettura durante la revisione Codex: 5000/152000 lavori nel log; nessuna nuova ETA affidabile. Controllo: `kill -0 968943`, `tail logs/p2f_validation.log`.

**Durante l'esecuzione** si può fare commit (la provenienza è acquisita all'avvio), ma non si
toccano codice scientifico, dipendenze, protocolli, input né `results/P2F/_design.pkl`. Il
controllo finale confronta la provenienza degli output con `5c3b664`, non con il nuovo HEAD.

**A fine esecuzione, nell'ordine:** (1) provenienza degli output `results/P2F/VALIDATION_*`
(`git_commit` = `5c3b664`, `git_dirty` = 0, SHA del protocollo `8f030010…`); (2) controllo
indipendente e riconteggio dai dati grezzi **prima** di leggere le tabelle
(`p2f_checks.py vraw`: 304 000 righe, chiavi uniche, numerosità per gruppo, identità
coperti + coda inferiore + coda superiore + errori = tentativi, verdetti ricalcolati dagli
intervalli, riconteggio senza la funzione di riepilogo della validazione; una discrepanza blocca
l'interpretazione); (3) commit degli output; (4) `docs/P2F_VALIDATION_RESULTS.md` (scheletro
già scritto) con le regole del protocollo §5 alla lettera, per test; (5) CHANGELOG,
RESULTS_INDEX, MANIFEST, ZIP per il revisore; (6) revisione esterna; (7) solo per i test
validati e dopo la revisione: applicazione ai dati reali con `p2f_apply.py` (una esecuzione per
test; rifiuta se il test non è validato o se i suoi risultati esistono già; sensibilità
dichiarate non validate anche negli intervalli), risultati in `docs/P2F_RESULTS.md`. Un test non
validato resta descrittivo. Gli output del pilota restano risultati storici della procedura
precedente (modello nullo).

**Ripresa con Codex, revisione delle bozze di riproducibilità (2026-11-11):**
le modifiche parziali lasciate da Claude sono state conservate e completate. Regole in
`docs/REPRO_COMPARISON_RULES.md` ancora **bozza non congelata**; 112 tabelle tracciate
inventariate, 111 chiavi univoche e una tabella vuota; scale fisse per colonna/test/quantità,
con eta_bar ed eta_bar² per T5 e confronto esatto conservativo per semantiche eterogenee.
`scripts/repro_draft_tables.py` prepara le tre tabelle di supporto senza importare codice
scientifico. Distinti commit del riferimento, commit registrati nei dati ed eccezioni storiche
dei JSON P2b o degli alberi originali non puliti. Verificati schema/chiavi e controlli sintetici
delle politiche numeriche; nessun rilancio di analisi. Prima della verifica effettiva: revisione
e congelamento delle regole, elenco di file/comandi/budget. Gli output P2f in corso non fanno
parte dell'inventario tracciato corrente; andranno aggiunti prima della loro riproduzione.
La validazione originale, i suoi input e `_design.pkl` restano invariati. Nessun push.

**Aggiornamento Codex dopo la revisione indipendente (2026-11-11):**
- Rivisto `21e7210`: 112 riferimenti Git/chiavi verificati, tre rilievi risolti
  (gamma0 a 24°, motivo di se_var_z, status esatto); 29 controlli delle politiche superati.
  Dettagli in `docs/REPRO_REVIEW_21E7210.md`.
- Congelata solo la prima verifica in `docs/REPRO_PHASE1_PLAN.md`: cinque CSV delle figure
  P1, clone isolato al codice/riferimento `120f852`, input e hash fissati, limite 10 minuti.
  Codice del comparatore ancora da scrivere e provare su casi sintetici; rilancio a macchina
  libera dopo P2f e il controllo indipendente. Le altre 107 tabelle restano fuori da questa fase.
- Studio documentale `docs/MDI_SMARP_FEASIBILITY.md`: bozza, fonti primarie, nessun download
  o calcolo. Primo passo proposto: confronto nella sovrapposizione maggio–ottobre 2010,
  separando LOS/Br, risoluzione e strumento; beneficio statistico ancora da misurare.
- Nessun cambiamento a P2f, input, risultati scientifici o protocolli precedenti; nessun push.
- La sessione Codex si è fermata per esaurimento dei token prima di installare questi file,
  rimasti in `/tmp/bl-followup-review`. Installati da Claude la sera del 2026-11-11 con l'ok
  dell'utente: hash di partenza e di arrivo verificati, tabelle DRAFT rigenerate fuori dal
  repository e identiche, `--selftest` 29/29, hash dei 11 file della fase 1 verificati.
  Validazione P2f ancora in corso (30 000/152 000 alle 19:38).

**Prossimi passi**
1. [fatto 2026-11-11] Revisione esterna dello ZIP `2e197f8`: riconteggio dai dati grezzi
   confermato, conclusione operativa corretta (M alla validazione, B scartata nella forma
   provata). Vincoli fissati per il protocollo (`docs/P2F_PILOT_RESULTS.md` §8): (i) lo scenario
   a salti resta decisivo nella validazione, numerosità e criterio fissati su tutti gli scenari;
   (ii) effetti di interesse motivati scientificamente, non scelti per la potenza; (iii) la causa
   del livello di B è un lavoro separato, non serve per validare M; (iv) la procedura M si
   congela esattamente (errori, celle singole, convenzioni del generatore, regole separate T3/T5).
2. [fatto 2026-11-11] Protocollo P2f scritto come bozza (`09562cd`), rivisto due volte dal
   revisore (`2618ca0`, `620920b`) e **congelato** (`500c56a`). Correzioni recepite: il −0,35
   tra cicli (Jiao et al. 2021) non è una pendenza dentro il ciclo; i «1–2°» di Jiang 2020 vengono
   da Karak & Miesch 2017 e non sono una soglia; il 30 % di Martin-Belda & Cameron 2017 non è per
   unità del proxy; i numeri di Zeng et al. 2024 non verificati e lasciati fuori; griglia
   −0,1/−0,2/−0,3 con −0,2 di riferimento e −0,35 supplementare (copertura e coda decisive anche
   lì); modello completo per residui e REML; generatore T5 con la media semplice di attività della
   cella; esclusione di un quenching ≥ δ solo con l'estremo inferiore di un intervallo validato;
   probabilità congiunta di scarto di una procedura nominale 7,26 % per test; A_usflux come
   sensibilità. Codice (`ed90e15`), test preliminari, validazione in corso (sopra).
3. Dalla lista del 2026-11-09, durante l'attesa della validazione (2026-11-11 pomeriggio):
   - riproducibilità (punto 1): **inventario** fatto, `docs/REPRODUCIBILITY_V84.md` (`8ee766e`,
     rivisto in `32ed3b0`): input disponibili, esecuzione possibile e riproduzione verificata
     distinti; senza Git `git_dirty = −1` blocca p2d, pilota e validazione; cinque incongruenze
     da sistemare; la **verifica** (rilanci con regole di confronto fissate prima, manifesto di
     hash) resta da fare a macchina libera;
   - HARP dominanti (punto 2): piano **registrato** `docs/DOMINANT_HARP_PLAN.md` (`f805c5a`,
     SHA-256 `e7767aea…`) dopo due revisioni; codice `python/sharpbl/dominant_harp_check.py`
     (`a41c451`, `c61bf2d`), prova tecnica su 2 HARP con output fuori dal repository (valori P1
     riprodotti esattamente; le due HARP viste — 393 e 5249 del gruppo 24N — vanno dichiarate
     nei risultati). **Esecuzione dopo la fine della validazione P2f**:
     `nice -n 10 .venv/bin/python python/sharpbl/dominant_harp_check.py` (pochi minuti), poi
     `docs/DOMINANT_HARP_RESULTS.md`;
   - restano fattibilità MDI/SMARP (punto 6) e confronto con Paolo (punto 7).
4. **Non fare il push** finché l'utente non lo chiede (di norma dopo la revisione dello ZIP).
   Ultimo commit pubblicato: `23e076a`. Il file non tracciato `results/P2/P2E_VALIDATION_RAW.csv`
   (14 MB, 2026-11-03) è preesistente e va preservato, non committato.

**Modo di lavorare concordato con l'utente**
- Le osservazioni di un revisore esterno arrivano incollate dall'utente; di norma si adottano.
- Ogni regola o analisi nuova ha un piano registrato con un commit **prima** del codice.
  I cambiamenti si fanno con emendamenti, dichiarati non ciechi se scritti dopo aver visto dei
  risultati. Ogni esecuzione è unica e gli output con `git_commit` e `git_dirty` = 0. Gli output
  di un'esecuzione non si modificano mai; riconteggi e riclassificazioni si salvano a parte.
- Il controllo indipendente degli output precede la loro interpretazione.
- Formulazioni prudenti: niente verdetti sul quenching; "compatibile" o "coerente", non
  "dimostra"; denominatori espliciti; distinguere i controlli completi da quelli campionari;
  niente «impatto trascurabile» se non misurato.
- Commit locali; push solo su richiesta, con il token dell'URL `origin` del repository MWO
  passato **solo** sulla riga di comando, mai salvato nella configurazione di questo
  repository.
- Esecuzioni lunghe: `setsid nohup … &`. Per aspettarle si usa `kill -0 <PID>` in un ciclo,
  **non** `pgrep -f` sul nome dello script (il ciclo riconosce sé stesso).
- Rispondere in italiano.

**Prompt da incollare nella nuova sessione:**

> Riprendi SHARP BL v8.4 nel repository /home/gianluca/BL_v8_3_stable, branch
> v8.4-python-gianluca. Leggi AGENTS.md e docs/HANDOFF.md (sezione "Passaggio di consegne del
> 2026-11-11, sera"), poi docs/PROTOCOL_P2F_VALIDATED_TEST.md e docs/P2F_PILOT_RESULTS.md.
> Verifica lo stato di Git e se la validazione P2f (PID 968943, log logs/p2f_validation.log)
> è ancora in corso. Il protocollo docs/PROTOCOL_P2F_VALIDATED_TEST.md è congelato. Quando la
> validazione è finita, segui i passi elencati nel passaggio di consegne (controllo indipendente
> prima dell'interpretazione). Non fare il push senza la mia richiesta.

## Branch `v8.4-python-gianluca` (stato del 2026-11-09)

Questa sezione vale per il branch v8.4 (Gianluca Santagati); la sezione v8.3
più sotto è il passaggio di consegne originale di Paolo, conservato com'è.

**Riprendere in una nuova sessione**
1. Leggere `AGENTS.md`, `README_V84.md` e i protocolli in `docs/PROTOCOL_P*.md`.
2. `git status --short`, `git log --oneline -8`; i protocolli congelati non si
   modificano: una regola nuova richiede un nuovo protocollo scritto prima.
3. Il download dei FITS è completo (14195/14195); non va ripetuto.
4. Riprendere dal primo passo non fatto della lista sotto.

Prompt da incollare:

> Riprendi SHARP BL v8.4 sul branch v8.4-python-gianluca. Leggi AGENTS.md,
> README_V84.md, docs/HANDOFF.md, docs/PROJECT_STATUS.md e i protocolli P1–P3.
> Verifica lo stato di Git, poi continua dal prossimo passo.
> Non modificare i protocolli congelati.

**Fatto**
- Porting Python (`python/sharpbl/`), correzioni (geometria sferica dalla WCS,
  bitmap ≥ 33, soglia 100 G, ciclo per latitudine nelle sovrapposizioni, un
  record per HARP), metodo legacy che riproduce la v8.3 sul caso 2024-05-08.
- Protocolli congelati: P1 (serie), P1b (QUALITY = 0x80), P1c (soglie della
  regola del ciclo, non cieco), P2 (test del quenching).
- Metadati di tutte le HARP (2010-05 → 2026-09; ottobre 2026 non ancora su
  JSOC): 8296 HARP; selezione di 14195 record per 7133 HARP
  (`results/P1/P1_RECORD_SELECTION.csv`); regola del ciclo
  (`results/P1/CYCLE_BOUNDARY_FITS.csv`).
- Script della serie (`run_p1.py`, provato su 926 record) e dei test
  (`run_p2.py`, verificato solo su cataloghi sintetici); 20 test in `tests/`.

**Obiettivo scientifico**: serie osservativa della sorgente BL (una misura per
HARP, non necessariamente per regione fisica) e verifica di tilt, latitudine ed
efficienza rispetto all'attività. S_BL è un proxy della sorgente BL misurato all'istante del
record selezionato (non necessariamente all'emersione), non
del campo polare del ciclo successivo.

**Stato al 2026-11-03 sera** (formulazioni riviste il 2026-11-09)
- Download completo (14195/14195); elaborazione completa dei record selezionati
  e controlli interni obbligatori superati (`complete_series` =
  `validation_passed` = 1), figure in `figures/P1/`.
- P3: C1 "coerente con BARD (livello 1)" per geometria e convenzioni nel
  campione confrontato (~69% di BARD); C2 riportato (`docs/P3_RESULTS_C1.md`).
  L'ampiezza della sorgente non ha una validazione esterna equivalente
  (flusso nostro/BARD 1,67).
- P2: la validazione della procedura calibrata (P2d/P2e) non ha superato il
  criterio; T3 e T5 sono **solo descrittivi** (formulazioni prudenti: T5
  "pendenza vicina a zero con ampia incertezza", non "nullo"; una pendenza
  negativa di T3 non dimostra il quenching) (`docs/P2_DECISION_DESCRIPTIVE_FALLBACK.md`,
  `docs/P2_RESULTS_DESCRIPTIVE.md`). Non riformulare come verdetti. Il mancato
  superamento non va attribuito al numero di cicli: il ruolo di numerosità,
  dipendenza temporale e stima del rumore non è ancora chiarito.
- Tutto ciò che è stato visto prima di ogni congelamento: `docs/SEEN_BEFORE_FREEZE_2026-11-03.md`.

**Prossimi passi** (rivisti il 2026-11-09 dopo una revisione esterna; prima i
punti 1–4, senza nuovi grandi calcoli; ogni regola nuova richiede un nuovo
protocollo, quelli eseguiti si conservano)
1. Riproducibilità: verificare che comandi, dipendenze, input e controlli
   rigenerino catalogo, tabelle e figure; separare ciò che è verificabile dal
   solo repository (o ZIP) da ciò che richiede i FITS esterni.
2. Controllo delle regioni che dominano la sorgente (il 10% più intenso porta il
   62–72% di |S_BL|): maschere, polarità, centroidi, associazioni NOAA.
3. [fatto 2026-11-09, `docs/SENSITIVITY_SUMMARY.md`] Sensibilità alle ricomparse e all'istante della misura: raccogliere
   l'effetto su somme ed efficienza (variante E di P1e, sensibilità S8;
   primario contro controllo, che mescola selezione, posizione sul disco ed
   evoluzione; `docs/EXPLORATORY_RESULTS.md` §4).
4. [in corso: diagnosi in `docs/DIAGNOSTIC_P2E.md`, discrepanza V0 in
   `docs/P2E_V0_APPLICABILITY_DISCREPANCY.md`, controllo A registrato in
   `docs/DIAGNOSTIC_A_PLAN.md` ed eseguito, risultati in `docs/DIAGNOSTIC_A_RESULTS.md`;
   controllo B eseguito, `docs/DIAGNOSTIC_B_RESULTS.md`; controllo C eseguito (con
   emendamento A1), `docs/DIAGNOSTIC_C_RESULTS.md`; verifica di coerenza di C1 in
   `docs/DIAGNOSTIC_C1_AUDIT.md`: nessuna discrepanza d'implementazione, il livello di circa
   il 3% riflette una realizzazione condivisa da V1–V4 (stessi semi in tutti gli scenari);
   controllo D su cataloghi nuovi (piano `docs/DIAGNOSTIC_D_PLAN.md` con A1, risultati
   `docs/DIAGNOSTIC_D_RESULTS.md`): livello compatibile con il 2,5%, diagnosi di C1 chiusa;
   prossimo passo: progettare P2f] Diagnosi del fallimento di P2d/P2e: quali condizioni sintetiche producono
   falsi verdetti eccessivi o parametri non stimabili (passano V0 e V4,
   falliscono V1–V3 con residui AR(1); in V0 test non applicabile nel ~31%
   dei cataloghi). Priorità per l'inferenza.
5. Eventuale P2f solo dopo la diagnosi: nuovo protocollo, dichiaratamente non
   cieco rispetto ai risultati precedenti, validato con simulazioni e semi
   nuovi (falsi verdetti, copertura, capacità di rilevare effetti fisicamente
   interessanti) prima dell'applicazione ai dati.
   Requisiti dalla diagnosi (2026-11-11; le correzioni possibili non sono validate):
   (a) stima dei parametri temporali meno distorta (A, B); (b) gestione della componente
   individuale utilizzabile sui dati reali, incluse le celle con una sola unità (C; il
   termine oracolo non è applicabile); (c) validazione con semi nuovi e distinti per scenario
   e regola di arresto (C1 audit, D); (d) robustezza a dipendenze temporali diverse
   dall'AR(1), in particolare AR(2) e salti di livello (V5, V6), che D non affronta.
   Documento di progettazione (non protocollo): `docs/P2F_DESIGN.md`.
6. MDI / ciclo 23 (SMARP) solo dopo uno studio di fattibilità: quali grandezze
   sono confrontabili con SHARP e come trattare le differenze strumentali.
7. Breve confronto con Paolo sulla sua domanda originaria, in parallelo.

**Dati e ambiente**
- `data/sharp` è un link a `/storage/shared/gianluca/SHARP_BL` (metadati
  ~140 MB, FITS ~4,5 GB, caso di prova). Non sono in Git.
- Ambiente: `python3 -m virtualenv .venv && .venv/bin/pip install -r requirements-v84.txt`.
- Download dei FITS: metodo diretto dall'archivio JSOC (as-is) con le keyword
  DRMS in `.keys.json`. L'export JSOC con più recordset uniti da virgole
  fallisce ("Error status returned from DRMS session"); `**ALL**` non è
  accettato da DRMS per più record insieme.
- Push: richiede credenziali GitHub dell'utente; non salvare token nella
  configurazione del repository.

---

# Cold restart — SHARP BL v8.3

Stato registrato il **2026-09-15**. Questo documento permette a una nuova LLM
o sessione di riprendere senza la chat precedente. È un riepilogo operativo;
le evidenze sono nel codice, nei documenti e nei file locali indicati.

## Avvio in una nuova sessione

1. Leggere `AGENTS.md`, questo documento, `README.md` e
   `docs/PROJECT_STATUS.md`.
2. Eseguire `git status --short`, `git log -3 --oneline`, `git remote -v`.
3. Verificare se Paolo ha fornito nuove indicazioni o l'URL GitHub.
4. Riprendere dal prossimo passo concordato sotto, senza riscaricare dati o
   ripetere la preparazione del repository.

Prompt da incollare in una nuova chat aperta nella cartella del progetto:

> Riprendi il progetto SHARP BL v8.3. Leggi AGENTS.md e docs/HANDOFF.md,
> verifica lo stato Git e continua dal prossimo passo concordato.
> Il repository locale è già preparato e committato. Il push su GitHub è
> autorizzato quando ti fornirò la destinazione e l'autenticazione sarà pronta.
> Preserva dati e risultati locali e non modificare il calcolo scientifico.

## Richieste e decisioni dell'utente

- Paolo ha chiesto il recap della discussione dai file. Non era presente una
  trascrizione; il recap è stato ricostruito da note, codice e risultati.
- Ha chiesto di preparare tutto per un repository e di fare il primo commit.
- Dopo aver considerato GitLab locale sotto VPN, ha scelto di proseguire con
  GitHub: «procedi, poi quando ho creato utente paolo romano su github,
  fai un push».
- L'identità Git locale concordata è **Paolo Romano <paolo.romano@inaf.it>**.
  È configurata solo in questo repository. Non equivale a uno username GitHub.
- Non sono ancora stati specificati URL, username effettivo o visibilità del
  repository remoto. Non è stata scelta una licenza.
- Ultima richiesta: preparare il cold restart con un'altra LLM o nuova sessione.

## Stato Git e percorsi

- Branch: `main`.
- Primo commit: `1a62bd0` — `Prepare SHARP BL v8.3 repository`, 50 file.
- Il presente passaggio di consegne è salvato in un commit successivo: ricavare
  l'hash effettivo da `git log`, senza assumere che il primo commit sia HEAD.
- Nessun remoto configurato al momento di questa preparazione; nessun push
  eseguito. Verificare nuovamente prima di configurare `origin`.
- Radice locale:
  `/media/paolo/e5e3fd23-60c6-4fdc-9d8b-829aebab0352/0_Bonanno_t/BL_v8_3_stable`.
- La shell può mostrare lo stesso progetto come
  `/home/paolo/data/0_Bonanno_t/BL_v8_3_stable`.
- La copia locale include FITS e risultati ignorati: un clone Git da solo non
  li contiene e non è un backup di tali dati.

## Lavoro già completato

- README e INSTALL riallineati alla v8.3; aggiunti requirements.txt,
  .gitignore, .gitattributes, CHANGELOG e documenti in docs/.
- Dati, output, log e ambiente Python esclusi da Git; cartelle mantenute con
  `.gitkeep`. File preesistenti conservati sul disco.
- Rimossi indirizzo personale dagli esempi e percorsi macchina dal launcher;
  la radice viene ricavata dallo script, con `--idl-root` come override.
- Corretto `--help`/`-h` come primo argomento del launcher.
- Corretto `--all-diagnostics`: eliminato `/ALL`, keyword non supportato dalla
  routine IDL; nessun filtro significa già tutte le righe.
- Aggiornati esempi di download e batch IDL e manifest del repository.
- Routine scientifiche non modificate.

## Verifiche già eseguite

- `bash scripts/check_repo.sh`: sintassi Bash, parsing Python e help launcher.
- Launcher provato in directory temporanea con spazi e shell IDL simulata:
  modalità diagnostica standard, tutte le diagnostiche, nessuna diagnostica.
  Verificati batch, soglia esplicita 100D e selezione dei filtri.
- `git diff --cached --check` superato prima del primo commit.
- Verificato che Git includa solo `.gitkeep` sotto data/output/logs.
- Nessun download, installazione dipendenze o nuovo calcolo IDL scientifico
  eseguito durante la preparazione del repository.
- `tcsh` è disponibile; `sswidl` non era nel PATH della shell Bash ispezionata.
  Questo non prova che manchi in tcsh: SolarSoft è inizializzato dalla sua
  configurazione. Non dichiarare il runtime IDL validato dalla nuova sessione.

## Stato scientifico e limiti

La pipeline scarica Br e bitmap SHARP CEA e calcola
`S_BL = hale_sign * Phi * d * cos(lambda) * sin(alpha)`.
Flusso unsigned, centroidi pesati con il campo; leading XMAX predefinito.
Gli orari delle query sono TAI.

Risultati locali preesistenti: 2024-05-08 03:12 TAI, 26 FITS, 13 regioni,
7 PNG. 9 righe numericamente valide, di cui 3 anti-Hale; 4 senza una polarità
sopra soglia. Dettagli e HARPNUM in `docs/PROJECT_STATUS.md`.
Il giorno completo non risulta concluso: log fermo all'attesa JSOC e CSV assente.

Punti aperti da non correggere implicitamente:

- `process_sharp_day` senza THRESHOLD usa 1000 G, mentre il launcher passa
  100 G. Differenza documentata, conservata intenzionalmente in questa attività.
- Convenzioni XMAX, tilt, segno e geometria CEA richiedono validazione fisica.
- Flag numerici OK non certificano correttezza scientifica.
- Alcuni errori per file vengono intercettati; uscita di processo riuscita
  non significa necessariamente tutte le regioni elaborate.
- requirements.txt dichiara dipendenze non bloccate a versioni specifiche.
- Gli esempi in test/ sono procedure IDL manuali, non regressioni automatiche.

## Prossimo passo concordato: push GitHub

Il push è già autorizzato dall'utente per quando il repository sarà disponibile.
Mancano destinazione e autenticazione; non sono stati richiesti token in chat.
Quando Paolo comunica l'URL:

1. Verificare autenticazione locale, URL e stato del remoto.
2. Collegare `origin` all'URL comunicato, se non già configurato. Non sostituire
   un origin diverso senza chiarire la destinazione.
3. Se remoto vuoto, eseguire `git push -u origin main`.
4. Se contiene già commit, ispezionarli e conciliare la storia preservando il
   lavoro; non forzare il push e non eliminare contenuti.
5. Confermare branch e commit pubblicato, confrontando HEAD e ref remoto.

Creazione account, visibilità e licenza restano scelte del proprietario.
Non pubblicare su una destinazione dedotta dal solo nome «Paolo Romano».

## Nota sull'ambiente dell'assistente

Le chiamate shell in sandbox hanno fallito con
`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted` anche in lettura.
È stato necessario il normale meccanismo di approvazione fuori sandbox.
Se ricapita, seguire le autorizzazioni della nuova sessione; questa nota non
costituisce un permesso per aggirare restrizioni. Alcune richieste furono
interrotte dall'utente: controllare lo stato reale dopo ogni interruzione.

# Tre analisi ancora possibili con i soli dati HMI — bozza di protocollo

**BOZZA NON CONGELATA, 18 novembre 2026 (Claude), revisione 2 dopo la revisione di Codex** (fase emisferica principale per Q2, criteri di P2f con completezza, rifiuti provati su file temporanei, allineamenti). Nessun calcolo nuovo
sui dati reali per scriverla. Riguarda la domanda del progetto (la sorgente Babcock–Leighton si autolimita attraverso
tilt, latitudine o efficienza?) con il catalogo P1 e il campione S di P2 (2485 record, 2010-05 → 2026-09), invariati.
**Non cieco**: sono noti T3 (−3,59° per unità di attività, [−10,58°; +3,41°]), T4 descrittivo (−0,63° per unità), T5
descrittivo, la fase A e la validazione P2f. Le tre parti sono indipendenti; ognuna ha il suo esito.

Strumento comune: la **procedura M** di P2f (stima REML della componente temporale AR(1) bivariata sulle celle (CR,
emisfero), funzione di varianza individuale, intervallo nominale 97,5 %, un verso all'1,25 %) applicata alla riga WLS
del contrasto d'interesse. M è validata per la pendenza di T3; per ogni contrasto nuovo serve una validazione propria
(§4), con semi nuovi e disgiunti da quelli già usati.

## 1. Q1 — Il coefficiente di Joy è più basso nel ciclo 25, più forte del 24?

**Motivazione.** La letteratura sul quenching fra cicli (Dasi-Espuig et al. 2010; Jiao, Jiang & Wang 2021, cicli 15–24,
T_lin = −0,00107·S_n + 0,61) prevede un coefficiente di Joy minore nei cicli più forti; McClintock & Norton 2013 non
trovano la dipendenza nel nord. HMI osserva i cicli 24 e 25 con lo stesso strumento: il confronto non ha problemi di
raccordo fra strumenti.

**È T2 di P2 reso un test.** P2 ha già stimato questo confronto in modo descrittivo (T2, intervallo da bootstrap a
blocchi, non validato): γ₀(25) − γ₀(24) = **+3,3°** [−4,1; 10,1] al 95 % su 2238 regioni, cioè nel verso opposto alla
previsione del quenching. **Il test non è cieco** al segno né all'ordine di grandezza.

**Modello principale (definizione di T2, invariata per continuità).** γ_i = k₂₄·sin|λ_i|·I₂₄ + k₂₅·sin|λ_i|·I₂₅ + errore,
pesi Φ_i, ciclo del record di P1; contrasto **Δ = k₂₅ − k₂₄**. Finestra di T2: tutti i record del ciclo 25 e i record del
ciclo 24 con fase ≤ φ_max, la fase dell'ultimo record del ciclo 25 (fase convenzionale con `run_p2.T_MIN`, 11 anni).

**Sensibilità dichiarate.** (a) Finestra simmetrica: entrambi i cicli ristretti a [φ_min,24; φ_max], con φ_min,24 = 0,1289279
la fase **osservata** del primo record del ciclo 24 (non il valore arrotondato 0,13): 2187 regioni (con 0,13 letterale
sarebbero 2184), perché HMI inizia nel ciclo 24 a quella fase mentre il ciclo 25 è osservato da fase 0. (b) Coefficienti per ciclo × emisfero e contrasto medio sui
due emisferi, ½[(k₂₅N − k₂₄N) + (k₂₅S − k₂₄S)]; contrasti per emisfero riportati senza verdetto.

**Scala di lettura (non una soglia).** Forza dei cicli = massimo smussato della serie SILSO totale, letto e registrato al
congelamento; con la relazione di Jiao et al. la riduzione relativa attesa del coefficiente è dell'ordine del 10 %
(circa −2,4° su 24°). È un riferimento esterno, ottenuto fra cicli in altri cataloghi e con un'altra definizione del tilt.

**Esito.** `supportato` se l'estremo superiore dell'intervallo è < 0 (ciclo 25 più basso); `opposto` se l'estremo
inferiore è > 0; altrimenti `non deciso`. Si riporta sempre l'intervallo come limite («una riduzione oltre X° è
esclusa»). Solo se la validazione del §4 è superata; altrimenti risultato descrittivo.

**Limiti dichiarati.** Due cicli, uno incompleto: nessuna relazione con la forza del ciclo si stima da due punti; il
risultato dice se i due cicli differiscono, non perché. Possibili differenze di composizione fra cicli (latitudini,
flussi) sono parte del contrasto.

## 2. Q2 — T4 reso un test: la latitudine media cresce con l'attività, a pari fase?

Stima descrittiva di P2: β₄ = **−0,63°** per unità di attività [−1,10; −0,12] (bootstrap, non validato), nel verso
opposto alla previsione.

**Modello (invariato da P2).** |λ_i| = Σ_{c,h} intercetti + polinomio cubico della fase + β₄·(A_i − 1), pesi Φ_i, A_monthly
emisferico come in P2. Parametro: β₄ (gradi per unità di attività). Previsione del quenching di latitudine: β₄ > 0.

**Esito.** `supportato` se l'estremo inferiore è > 0; `opposto` se l'estremo superiore è < 0; altrimenti `non deciso`;
intervallo sempre riportato. La stima descrittiva di P2 (−0,63°) è nota: l'esito del test non è cieco al segno.

**Analisi principale con la fase emisferica (decisione dopo la revisione di Codex, 18 novembre).** La domanda è se, a
pari avanzamento del ciclo nel proprio emisfero, le regioni emergano più in alto quando l'attività è maggiore: la fase
emisferica è più aderente. Fase emisferica = (t − m_{c,h})/11 anni, con m_{c,h} il mese del minimo della serie SILSO
emisferica smussata a 13 mesi, cercato in 2007-01 → 2010-12 (ciclo 24) e 2018-01 → 2021-12 (ciclo 25): nord 2007-12 e
2019-12, sud 2009-02 e 2019-05. La fase convenzionale (T4 storico, −0,63°) è una sensibilità, confrontata direttamente
con il risultato principale. Lo sfasamento come spiegazione del segno di T4 resta un'ipotesi da verificare.

**Motivazione dello sfasamento.** In T4 la fase è
convenzionale, dagli stessi minimi per i due emisferi, mentre nord e sud sono sfasati di un anno o più. Un emisfero è più
attivo vicino al proprio massimo, cioè più avanti nel proprio ciclo, quando le regioni emergono a latitudini più basse:
a pari fase convenzionale «più attività» può significare «emisfero più avanzato», quindi un coefficiente negativo senza
alcun anti-quenching. Proposta: analisi con la **fase emisferica** (minimi della serie SILSO emisferica smussata a
13 mesi, regole sopra). Il generatore della validazione usa la stessa definizione di fase dell'analisi a cui si
applica.

**Generatore per la validazione** (scale fissate a priori): |λ| = media del modello senza attività + rumore individuale con
deviazione standard 6° + componente temporale per cella con scala 3° (rapporto 0,5 come in P2f), forme P2f 0, 1, 2, 7, 9;
sensibilità a 4° e 9° di rumore individuale applicate alla versione emisferica principale. **La media senza attività è
adattata alle latitudini osservate**, che sono la risposta di Q2: la simulazione è quindi **condizionata al campione S**
(stesse latitudini medie per fase, ciclo ed emisfero), non un generatore indipendente dai dati. Effetti per la copertura e
la potenza: β₄ = +1° e +2° per unità di attività. Le scale sono ipotesi di simulazione.

## 3. Q3 — Quenching «locale»: le regioni più forti hanno un coefficiente di Joy minore? (descrittivo)

**Domanda diversa da quella di Paolo** (dipende dalla singola regione, non dall'attività globale), ma collegata al
meccanismo: Jha et al. (MDI/HMI, AutoTAB) trovano una pendenza di Joy che cresce con il campo massimo e poi decresce sopra
circa 2–2,5 kG.

**Modello.** γ_i = Σ_{c,h} k_{c,h}·sin|λ_i| + b·(log₁₀Φ_i − m)·sin|λ_i| + β₃·(A_i − 1)·sin|λ_i|, con m la media pesata di
log₁₀Φ nel campione; il termine di attività è incluso per separare l'effetto locale da quello globale. Prodotti: b con
l'intervallo di M (nominale, **senza verdetto**) e le **differenze** del coefficiente di Joy dei quintili 2–5 di Φ
rispetto al primo quintile (stessa matrice con indicatori di quintile × sin|λ| al posto del termine in b, quintili 2–5;
intervalli nominali). L'analisi con il campo massimo al posto del flusso è **omessa**: il campo massimo non è nel
catalogo P1.

**Limiti.** Φ è correlato con latitudine, fase e attività; la regione complessa (classe B della morfologia) ha flusso
grande e tilt di HARP netto: la lettura resta descrittiva.

## 4. Validazione e ordine

Criteri e numerosità di P2f (`docs/PROTOCOL_P2F_VALIDATED_TEST.md` §5), applicati agli scenari 0, 1, 2, 7, 9 (sottoinsieme
dichiarato dei dodici di P2f), separatamente per i due test principali, Q1 e Q2 con fase emisferica:
- **sotto nulla**: 10 000 cataloghi per scenario; in **ognuno** dei cinque scenari falsi verdetti (`supportato` +
  `opposto`) ≤ 3,0 %, ciascun verso ≤ 1,75 %, `errore` ≤ 1 % dei tentativi;
- **sotto effetto**: scenari 1, 2, 7, 9 × due effetti (Q1: Δ = −0,1·γ₀ e −0,2·γ₀ = −2,4° e −4,8° nel ciclo 25; Q2: +1° e
  +2° per unità di attività), 2000 cataloghi per combinazione; copertura ≥ 96,5 % (`errore` = non copertura) e coda di
  esclusione ≤ 2,0 % (Q1: estremo inferiore sopra il valore vero; Q2: estremo superiore sotto il valore vero); la potenza
  si riporta senza criterio. Questo criterio permette di usare gli intervalli per escludere ampiezze fisiche, nei soli
  scenari provati;
- **sensibilità senza criterio**: Q2 emisferico con rumore individuale 4° e 9° (scenari 1 e 7, 2000 cataloghi), Q2 con
  fase convenzionale (cinque scenari, 2000 cataloghi);
- **completezza**: la validazione è accettata solo se ogni configurazione ha esattamente il numero previsto di cataloghi,
  con indici di replica e semi attesi e senza duplicati; altrimenti è respinta.

Totale 150 000 unità. Benchmark sul pool reale: la macchina ha 8 core fisici e il calcolo è limitato dalla memoria, quindi
il numero di processi è fissato a 5 (rendimento massimo misurato: 1 processo 1,5 unità/s, 4 → 2,9–3,6, 5 → 3,55, 6 → 3,4, 8 → 2,4, 12 → 2,6); durata attesa circa 12 ore. **Tetto: 24 ore**
(accettato dall'utente; il calcolo gira staccato e non consuma risorse di revisione). Se la validazione di un test fallisce,
quel test resta descrittivo. Q3 non ha verdetto: intervalli nominali.

Codice: `scripts/hmi_followups.py` (selftest 21/21: rifiuti del congelamento provati su file temporanei, controesempi di
griglia incompleta, tutta in errore, duplicata, con un verso al 2 % o una coda al 5 %); riconteggio indipendente
`scripts/hmi_followups_recount.py` (5/5: rileva un riepilogo manomesso; ricalcola tutte le frequenze, gli SE di ogni riga e
l'accettazione su una griglia scritta indipendentemente; verifica gli hash della validazione usata dalla stima).

Ordine: revisione di Codex → congelamento → codice e selftest → validazione Q1 e Q2 → stima una sola volta (Q1, Q2, Q3)
→ output conservati prima della lettura → riconteggio indipendente → rapporto.

## 5. Che cosa non cambia

T3 (non deciso), T5 (descrittivo) e i loro documenti; la fase A; nessuna esclusione di record o sottocampione nuovo
oltre alla finestra di fase di Q1, fissata qui.

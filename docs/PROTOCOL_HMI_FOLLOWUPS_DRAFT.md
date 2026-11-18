# Tre analisi ancora possibili con i soli dati HMI — bozza di protocollo

**BOZZA NON CONGELATA, 18 novembre 2026 (Claude). Da rivedere con Codex prima del congelamento.** Nessun calcolo nuovo
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

**Modello.** γ_i = Σ_{c,h} k_{c,h}·sin|λ_i| + errore, con c ∈ {24, 25} (ciclo del record di P1), h ∈ {N, S}, pesi Φ_i.
**Contrasto**: Δ = ½[(k_{25,N} − k_{24,N}) + (k_{25,S} − k_{24,S})], in gradi di coefficiente di Joy. Stessa riga WLS per
M; contrasti per emisfero riportati a parte, senza verdetto.

**Fase confrontabile (analisi principale).** Il ciclo 25 è incompleto (fase ≤ 0,62 al 2026-09) e HMI inizia a fase 0,13
del ciclo 24. Se il coefficiente varia con la fase, il confronto fra un ciclo intero e uno parziale confonde le due cose.
Analisi principale: entrambi i cicli ristretti alla stessa finestra di fase convenzionale [0,13; 0,62] (minimi
`run_p2.T_MIN`, 11 anni). Sensibilità: tutti i record dei due cicli.

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

**Modello (invariato da P2).** |λ_i| = Σ_{c,h} intercetti + polinomio cubico della fase + β₄·(A_i − 1), pesi Φ_i, A_monthly
emisferico come in P2. Parametro: β₄ (gradi per unità di attività). Previsione del quenching di latitudine: β₄ > 0.

**Esito.** `supportato` se l'estremo inferiore è > 0; `opposto` se l'estremo superiore è < 0; altrimenti `non deciso`;
intervallo sempre riportato. La stima descrittiva di P2 (−0,63°) è nota: l'esito del test non è cieco al segno.

**Generatore per la validazione** (scale fissate a priori, non stimate sui dati): |λ| = media del modello senza attività
(stimata sui dati: è il disegno, non la risposta del test) + rumore individuale con deviazione standard 6° + componente
temporale per cella con scala 3° (rapporto 0,5 come in P2f), forme P2f 0, 1, 2, 7, 9; sensibilità a 4° e 9° di rumore
individuale. Effetto per la potenza: β₄ = +1° per unità di attività.

## 3. Q3 — Quenching «locale»: le regioni più forti hanno un coefficiente di Joy minore? (descrittivo)

**Domanda diversa da quella di Paolo** (dipende dalla singola regione, non dall'attività globale), ma collegata al
meccanismo: Jha et al. (MDI/HMI, AutoTAB) trovano una pendenza di Joy che cresce con il campo massimo e poi decresce sopra
circa 2–2,5 kG.

**Modello.** γ_i = Σ_{c,h} k_{c,h}·sin|λ_i| + b·(log₁₀Φ_i − m)·sin|λ_i| + β₃·(A_i − 1)·sin|λ_i|, con m la media pesata di
log₁₀Φ nel campione; il termine di attività è incluso per separare l'effetto locale da quello globale. Prodotti: b con
l'intervallo di M (nominale, **senza verdetto**), il coefficiente di Joy per quintile di Φ (stessa matrice con indicatori
di quintile al posto del termine in b), e la stessa analisi con P1 `phi_mx` sostituito dal campo massimo se disponibile
nel catalogo (altrimenti omessa, dichiarato).

**Limiti.** Φ è correlato con latitudine, fase e attività; la regione complessa (classe B della morfologia) ha flusso
grande e tilt di HARP netto: la lettura resta descrittiva.

## 4. Validazione e ordine

Per Q1 e Q2, prima di qualsiasi stima sui dati reali: generatore P2f sul disegno S (Q1: tilt come in P2f con
SD_E = 15°, SD_X = 7,5°; Q2: §2), scenari 0, 1, 2, 7, 9, **2000 cataloghi sotto nulla ciascuno** e **500 con effetto**
(Q1: Δ = −0,1·γ₀ = −2,4° nel ciclo 25; Q2: +1°) negli scenari 1 e 7. Criterio di P2f: limite superiore di
Clopper–Pearson al 95 % dei falsi verdetti complessivi ≤ 4 % negli scenari correttamente specificati (0, 1, 2); quelli
mal specificati (7, 9) riportati a parte. Benchmark rappresentativo prima della griglia (unità complete, non la sola
costruzione del disegno), tetto 8 ore su 12 processi. Q3 non ha verdetto: nessuna validazione obbligatoria, intervallo
detto nominale.

Ordine: revisione di Codex → congelamento → codice e selftest → validazione Q1 e Q2 → stima una sola volta (Q1, Q2, Q3)
→ output conservati prima della lettura → riconteggio indipendente → rapporto.

## 5. Che cosa non cambia

T3 (non deciso), T5 (descrittivo) e i loro documenti; la fase A; nessuna esclusione di record o sottocampione nuovo
oltre alla finestra di fase di Q1, fissata qui.

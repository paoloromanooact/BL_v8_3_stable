# T3 su un catalogo di tilt lungo: nota di fattibilità

**BOZZA, 18 novembre 2026 (Claude). Nessun dato scaricato, nessun calcolo nuovo; da rivedere con Codex.** Serve a
decidere se valga la pena progettare uno studio separato, non lo progetta. Le fonti sono state lette in una ricerca
rapida (abstract e pagine pubbliche): i numeri della letteratura vanno ricontrollati sulle fonti primarie prima di
usarli in un protocollo, salvo quelli già verificati per P2f (indicati).

## 1. Perché HMI da solo non basta

T3 chiede se il coefficiente di Joy cambia con l'attività **dentro** il ciclo. Su HMI la stima è −3,59° per unità di
attività, intervallo nominale 97,5 % [−10,58°; +3,41°]: non deciso. La fase A (`docs/PROSPECTIVE_PHASE_A_RESULTS.md`)
mostra due cose:

- lo scenario prescritto vale −1,60° per unità di attività (−0,067·γ₀) ed è riconosciuto 2–4 volte su 100;
- alla scala di rumore P2f il **66–83 % della varianza** della pendenza T3 viene dalla componente temporale comune alle
  regioni della stessa rotazione (RAW di fase A, `var_temporal_share`, E0, modello (a)); la dispersione individuale dei
  tilt pesa il resto.

Aggiungere regioni nello stesso intervallo di tempo, o un estimatore più raffinato sulle stesse rotazioni, riduce poco
l'incertezza. Serve osservare **molte più rotazioni e più cicli**. MDI aggiunge un ciclo (E2/E3 in fase A: da 2,9 % a
4,3 %).

## 2. Cataloghi disponibili (da verificare accesso e formato)

| Catalogo | Periodo | Grandezza | Note |
|---|---|---|---|
| Mount Wilson, luce bianca | 1917–1985 (cicli 15–21) | tilt di gruppi da fotografie | storico, usato da Dasi-Espuig et al. 2010 |
| Mount Wilson, disegni | 1917–oggi (cicli 15–24) | tilt da disegni con polarità | Tlatova et al. 2018 |
| Kodaikanal, luce bianca digitalizzata | 1906–1987 (e oltre nelle versioni digitali) | tilt di gruppi | usato anche per la dipendenza dal campo (area come proxy) |
| Debrecen DPD | 1974–2018 (cicli 21–24) | posizioni, aree, tilt giornalieri per gruppo | pubblico dal sito di Debrecen; 2016–2018 da richiesta |
| Debrecen SDD (MDI) / HMIDD | 1996–2010 / 2010– | come DPD, da immagini SOHO/SDO | sovrapposti a MDI/HMI |
| Magnetogrammi MDI/HMI (AutoTAB) | 1996–2018 | tilt magnetico di BMR | Jha et al. |

## 3. Stato della letteratura (rapido)

- **Dipendenza dalla forza del ciclo, fra cicli.** Dasi-Espuig et al. 2010: anticorrelazione fra tilt medio e forza del
  ciclo (MW, KK); con il corrigendum r = −0,79 per MW (verificato per P2f). Ivanov 2012 e McClintock & Norton 2013 non
  la riproducono; per McClintock & Norton la componente stocastica domina e la variazione può differire fra emisferi.
  Jiao, Jiang & Wang 2021 (cicli 15–24, più cataloghi): T_lin = −0,00107·S_n + 0,61, r = −0,85 (verificato per P2f).
  Tlatova et al. 2018 (disegni MW, cicli 15–24): tilt maggiori non danno cicli più forti. Il quadro è **controverso**.
- **Dipendenza dal campo della regione.** Jha et al. (MDI 1996–2011, HMI 2010–2018, AutoTAB): la pendenza di Joy cresce
  con il campo massimo e poi decresce sopra circa 2–2,5 kG; comportamento simile su Kodaikanal con l'area come proxy.
  È una dipendenza dalla singola regione, non dall'attività globale.
- **Dipendenza dall'attività dentro il ciclo (la domanda di T3).** Nella ricerca rapida non ho trovato un test diretto;
  va cercato con cura prima di dichiararne la novità.

## 4. Che cosa cambierebbe un catalogo lungo

- **Più rotazioni.** 1917–1985 sono circa 900 rotazioni contro le 221 di E0; con DPD e MW-disegni si arriva al ciclo 24.
  Se domina la componente temporale, la varianza della pendenza scende circa come l'inverso del numero di rotazioni
  indipendenti: l'errore potrebbe ridursi di un fattore 2 o più. **Non basta assumerlo**: va calcolato sul disegno reale
  del catalogo, come in fase A.
- **Effetto piccolo.** Con SE/|Δβ| ≈ 2,85 su E0, anche un errore dimezzato lascia il riconoscimento dello scenario
  prescritto attorno al 5–10 %. Un catalogo lungo rende più informativo l'**intervallo** (che potrebbe escludere effetti
  grandi come −0,2·γ₀) più che il riconoscimento dello scenario piccolo.
- **Domanda vicina ma diversa.** Con molti cicli si può stimare anche la dipendenza **fra cicli** (forza del ciclo), dove
  gli effetti riportati sono più grandi; sarebbe un secondo test, da dichiarare separato da T3.

## 5. Difficoltà da affrontare prima di un protocollo

1. **Grandezza diversa.** I tilt in luce bianca (posizioni delle macchie) non sono il tilt magnetico dai centroidi di
   flusso di P1; serve un confronto nella sovrapposizione (DPD/SDD contro P1 o contro MDI/HMI), come fatto con BARD.
2. **Polarità e Hale.** Nei cataloghi in luce bianca la polarità non è nota (salvo i disegni MW): niente segno di Hale,
   anti-Hale non riconoscibili; il tilt va definito senza polarità e la differenza dichiarata.
3. **Attività emisferica.** La serie SILSO emisferica usata da P2 parte dal 1992; per 1917–1985 serve un'altra misura
   emisferica (per esempio le aree delle macchie per emisfero, Greenwich/SOON), con una sua normalizzazione.
4. **Omogeneità.** Osservatori, strumenti e criteri di raggruppamento cambiano nel tempo: possibili scarti fra epoche
   che dipendono dall'attività, lo stesso problema del raccordo MDI–HMI su scala più grande.
5. **Pesi e selezione.** P1 pesa con il flusso; nei cataloghi si ha l'area; serve una regola fissata prima.

## 6. Passi proposti, in ordine

1. **Ricerca bibliografica mirata** sul test interno al ciclo (eventuali lavori esistenti) e verifica primaria dei
   numeri del §3.
2. **Acquisizione di un solo catalogo** (DPD, pubblico, 1974–2016, giornaliero) e di una serie emisferica di attività:
   solo file di testo, nessun dato pesante.
3. **Fase analitica come A1**, senza toccare i tilt: sul disegno reale del catalogo (date, latitudini, aree, rotazioni)
   calcolare l'errore atteso della pendenza T3 per gli stessi rumori della fase A. Decide se il catalogo può restringere
   l'intervallo in modo utile, prima di qualunque stima.
4. Solo se il passo 3 è promettente: protocollo congelato (definizione del tilt senza polarità, attività emisferica,
   raccordo con P1 nella sovrapposizione, test interno al ciclo e, separato, test fra cicli).

## 7. Calcolo analitico sul disegno DPD — scelte fissate prima del calcolo (18 novembre, pomeriggio)

Dati: file `gDPD<anno>.txt` 1974–2016 (righe di gruppo), scaricati via HTTP dal sito di Debrecen in
`data/sharp/external_DPD_20261118/` (fuori da Git, con `SHA256SUMS.txt`). **Nessun tilt** viene letto o usato: il
calcolo usa solo date, latitudini e aree dei gruppi, come la fase A usava il disegno HMI.

1. **Record.** Per ogni gruppo (numero NOAA, con le lettere aggiuntive di DPD come gruppi distinti) il record giornaliero
   con |LCM| minimo, purché |LCM| ≤ 60° e area WS corretta > 0; latitudine |λ| ≤ 45°; rotazione di Carrington dalla data
   (calendario di Meeus come in fase A).
2. **Pesi.** Area WS corretta del gruppo (millesimi di emisfero) come sostituto del flusso Φ di P1. Sensibilità: solo
   gruppi con area ≥ 50 millesimi (gruppi con tilt plausibilmente misurabile).
3. **Attività emisferica.** Somma mensile delle aree WS corrette dei gruppi per emisfero (dai record giornalieri
   DPD), media sui giorni con osservazione, normalizzata alla sua media 1974–2016. Non è la serie SILSO di P2:
   cambia la scala dell'unità di attività, non il rapporto SE/|Δβ|, perché il bersaglio usa i quantili.
4. **Cicli.** Ciclo del tempo dai minimi smussati 1976-03, 1986-09, 1996-08, 2008-12; intercetti ciclo × emisfero
   × sin|λ| come in T3; nessuna distinzione vecchio/nuovo per latitudine (approssimazione dichiarata).
5. **Bersaglio e precisione.** Stessi del piano prospettico per T3: Δγ = −δ(Â_c)·24°·sin|λ|, rampa fra i quantili 5 % e
   95 % dell'attività di cella replicata sui record; SE dalla formula A1 con rumore individuale 15° (sensibilità 25°,
   per la dispersione maggiore dei tilt in luce bianca) e rumore temporale AR(1) 0,5, 0,9 e salti di 20 CR alle scale
   0,5, 1, 2 di 7,5°.
6. **Prodotti.** Numero di record, celle e rotazioni; SE/|Δβ|; frequenza di riconoscimento dello scenario; semilarghezza
   dell'intervallo nominale 97,5 % (z·SE) in gradi per unità di attività e in unità di γ₀; stesse grandezze per E0 HMI
   dalla fase A come confronto; anche per i sottoperiodi 1974–1996 e 1996–2016.
7. **Lettura.** Descrittiva: dice se un catalogo come DPD potrebbe stringere l'intervallo di T3, non stima nulla.

## 8bis. Correzione del calendario (revisione di Codex, 18 novembre)

Nella prima corsa `cycle_of()` assegnava al ciclo 21 anche le date precedenti al minimo di marzo 1976 (ciclo 20).
Corretto (`e10c5e3`) e ripetuto il solo calcolo analitico, output conservati prima della lettura in `b7d9861`
(`results/T3_DPD_FEASIBILITY_R2/`; la prima corsa resta conservata). Effetto: semilarghezze cambiate al più di
0,003·γ₀ e riconoscimenti al più di 0,1 punti; **i valori del §8 restano validi alla seconda cifra decimale**. Il caso
aggiuntivo a 30° era stato calcolato con il calendario vecchio; data la differenza trascurabile non è stato ripetuto.

## 8. Risultato del calcolo analitico (output conservati in `1f3cee4` prima della lettura)

Script `scripts/t3_dpd_feasibility.py` (`2513f8b`), selftest 4/4; output `results/T3_DPD_FEASIBILITY/`. Disegni: DPD
1974–2016 19 821 gruppi, 1143 celle, 577 rotazioni; con area ≥ 50 millesimi 6118 gruppi; 1974–1996 11 036; 1996–2016
8785. HMI E0: 2485 record, 210 rotazioni.

Semilarghezza dell'intervallo nominale 97,5 % della pendenza, in unità di γ₀ per unità di attività, scala di rumore
P2f (rumore individuale 15°; tra parentesi 25°):

| Disegno | AR(1) 0,5 | AR(1) 0,9 | salti 20 CR | riconoscimento dello scenario |
|---|---|---|---|---|
| HMI E0 (fase A) | 0,43 | 0,56 | 0,60 | 2,3–2,9 % |
| DPD 1974–2016 | 0,16 (0,22) | 0,19 (0,24) | 0,20 (0,25) | 4,1–5,3 % (3,3–3,7 %) |
| DPD, area ≥ 50 | 0,16 (0,21) | 0,19 (0,24) | 0,20 (0,24) | 4,3–5,6 % |
| DPD 1974–1996 | 0,20 (0,27) | 0,23 (0,30) | 0,24 (0,30) | 3,3–3,9 % |
| DPD 1996–2016 | 0,27 (0,36) | 0,35 (0,42) | 0,37 (0,44) | 2,7–3,4 % |

Lettura, descrittiva:
- con 43 anni e 4 cicli l'intervallo di T3 diventerebbe **circa 2,7–3 volte più stretto** di quello HMI, anche con una
  dispersione dei tilt in luce bianca di 25°; il guadagno viene dal numero di rotazioni, come atteso dalla fase A;
- lo **scenario prescritto piccolo resta poco riconoscibile** (circa 5 volte su 100): sul disegno DPD vale −1,07° per
  unità di attività (unità diversa, attività da aree DPD), con SE/|Δβ| 1,6–2,0;
- l'uso realistico è quindi un **limite più stretto**: un intervallo di ±0,16–0,20·γ₀ per unità di attività potrebbe
  escludere effetti dell'ordine di −0,2·γ₀ (la griglia storica di T3), che HMI non può escludere;
- le unità di attività di HMI (SILSO emisferico) e di DPD (aree emisferiche) non sono identiche: il confronto in unità
  di γ₀ è indicativo; un protocollo dovrebbe fissare un'attività comune o riportare l'effetto in termini di quantili.

**Verifica primaria della letteratura (pomeriggio del 18 novembre).**
- Jiao, Jiang & Wang 2021: la dipendenza studiata è **fra cicli** (coefficiente per ciclo contro forza del ciclo,
  cicli 21–24 in DPD e altri cataloghi); nessun test interno al ciclo.
- McClintock & Norton 2013: tilt medi pesati per area inversamente legati alla forza del ciclo nel sud e su tutto il Sole,
  **nessuna dipendenza nel nord**; il rumore stocastico domina e non permette di determinare la pendenza di Joy sulla
  scala di 11 anni; **deviazione standard dei tilt 29–31°** in tutti i cicli ed emisferi.
- Un test esplicito del coefficiente di Joy contro l'attività **dentro** il ciclo (la domanda di T3) non è emerso in due
  ricerche; esistono studi della variazione dei tilt con la fase del ciclo, che è una domanda diversa (la fase porta con
  sé la latitudine, che T3 già modella con sin|λ|). La novità non è ancora dimostrata.

**Calcolo aggiuntivo dichiarato, eseguito dopo la lettura del §8** (solo analitico, nessun tilt letto): con dispersione
individuale 30°, come in McClintock & Norton, la semilarghezza su DPD 1974–2016 alla scala P2f è 0,25, 0,27 e 0,28·γ₀
(AR(1) 0,5, AR(1) 0,9, salti): ancora 1,7–2,2 volte più stretta di HMI (0,43, 0,56, 0,60).

Il catalogo dei tilt DPD non è stato letto. Prossimo passo, se si procede: verifica primaria della letteratura (§6.1),
poi un protocollo che fissi la definizione del tilt in luce bianca, l'attività emisferica e il raccordo con P1 nella
sovrapposizione 2010–2016, prima di leggere i tilt.

## Fonti consultate

- Baranyi et al., confronto fra tilt di Debrecen e di Mount Wilson/Kodaikanal e legge di Joy, MNRAS 447, 1857
  (https://academic.oup.com/mnras/article/447/2/1857/2593777)
- Jiao, Jiang & Wang 2021, A&A 653, A27 (https://arxiv.org/pdf/2106.11615)
- Tlatova et al. 2018, tilt dei bipoli nei cicli 15–24 (https://arxiv.org/abs/1807.07913)
- McClintock & Norton 2013 (https://arxiv.org/abs/1305.3205)
- Variazione dei tilt con la fase (https://arxiv.org/pdf/2410.21715)
- Jha et al. 2024, quenching dei tilt con AutoTAB (https://arxiv.org/abs/2401.04255v1)
- Wang et al. 2015, tilt magnetici contro luce bianca (https://arxiv.org/html/1412.2329)
- Strumenti in linea di Debrecen (https://arxiv.org/pdf/1606.00669)

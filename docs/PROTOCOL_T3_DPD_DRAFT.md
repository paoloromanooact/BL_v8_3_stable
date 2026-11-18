# T3 sul catalogo Debrecen DPD — bozza di protocollo

**BOZZA NON CONGELATA, 18 novembre 2026 (Claude). Da rivedere con Codex prima del congelamento.** Nessun tilt DPD è
stato scaricato, calcolato o letto. Base: nota di fattibilità `docs/T3_LONG_CATALOGUE_FEASIBILITY_DRAFT.md` (§7–§8).
Non cieco: sono noti il risultato T3 su HMI (−3,59° per unità di attività, [−10,58°; +3,41°]), la fase A e il
calcolo analitico su DPD (semilarghezza attesa 0,16–0,28·γ₀ secondo il rumore). Le pipeline HMI non cambiano.

## 1. Domanda e prodotto principale

Il coefficiente di Joy dei gruppi di macchie dipende dall'attività emisferica **dentro** il ciclo, nei cicli 21–24
(1974–2016)? Il prodotto principale è l'**intervallo** della pendenza, cioè quanto forte può essere un effetto
compatibile con i dati, letto accanto a quello HMI; il verdetto (`supportato`, `opposto`, `non deciso`) segue la regola
di P2f (intervallo nominale 97,5 %, un verso all'1,25 %) **solo se** la procedura supera la validazione del §6. Una
dipendenza fra cicli (forza del ciclo) non è testata qui: è una domanda diversa, da un protocollo separato.

## 2. Dati

- `sDPD<anno>.txt` (righe di macchia) e `gDPD<anno>.txt` (righe di gruppo), 1974–2016, dal sito di Debrecen, con
  SHA-256 registrati all'acquisizione; `dailyDPD1974_2016.txt` per i giorni osservati. Le righe di gruppo sono già in
  `data/sharp/external_DPD_20261118/`; le righe di macchia si scaricano **dopo** il congelamento.
- Il catalogo dei tilt di Debrecen (quattro varianti, interrogazione in linea) al 18 novembre risponde 403. Se torna
  disponibile prima del congelamento, la scelta fra tilt di Debrecen e tilt calcolati qui va fissata nel testo
  congelato; non si usano entrambi per scegliere a posteriori.

## 3. Record e tilt in luce bianca

1. **Giorno di misura.** Per ogni gruppo (stringa NOAA di DPD, lettere aggiuntive comprese) il giorno con |LCM| minimo
   fra quelli con almeno due macchie di area WS corretta > 0, |LCM| ≤ 60° e |λ| ≤ 45°.
2. **Pesi delle macchie.** Area WS corretta; le macchie con area negativa (penombra o ombra condivisa) prendono peso
   zero e la loro area resta nella macchia indicata dal riferimento, come da formato DPD.
3. **Testa e coda.** Centroide del gruppo pesato per area; macchie con longitudine (riferita al centroide, intervallo
   (−180°, 180°]) maggiore di zero = parte di testa (ovest), le altre = coda. Centroidi di testa e coda pesati per area;
   se una parte è vuota il gruppo è escluso (motivo registrato).
4. **Tilt.** α = atan2(λ_testa − λ_coda, (L_testa − L_coda)·cos λ̄) in (−90°, 90°); variabile di Joy
   γ = −sign(λ̄)·α, positiva quando la testa è più vicina all'equatore in entrambi gli emisferi. La polarità è ignota:
   niente segno di Hale, gruppi anti-Hale non riconoscibili (differenza dichiarata rispetto a P1).
5. **Peso del record.** Area WS corretta del gruppo nel giorno di misura (al posto del flusso Φ di P1).

## 4. Attività, cicli, modello

- **Attività emisferica principale.** Somma giornaliera delle aree WS corrette dei gruppi per emisfero, media mensile sui
  giorni osservati, normalizzata alla media 1974–2016 (come nel §7 della nota). Sensibilità: SILSO emisferico
  normalizzato come in P2, solo per 1992–2016.
- **Cicli.** Ciclo del tempo dai minimi 1976-03, 1986-09, 1996-08, 2008-12; nessuna separazione vecchio/nuovo per
  latitudine (approssimazione dichiarata; il suo effetto è stimato nella validazione con lo stesso disegno).
- **Matrice T3.** Intercetti ciclo × emisfero moltiplicati per sin|λ| e colonna x₃ = (A − 1)·sin|λ|, pesi = area; il
  parametro è il coefficiente di x₃. Celle (CR, emisfero) per la componente temporale.

## 5. Bersaglio di lettura

Accanto all'intervallo si riportano: l'intervallo HMI di T3; lo scenario prescritto del piano prospettico ricalcolato
sul disegno DPD (−0,2·24°·sin|λ| fra i quantili 5–95 % dell'attività di cella, circa −1,07° per unità DPD); la
griglia storica −0,2·γ₀. Le unità di attività di HMI e DPD sono diverse: il confronto fra i due intervalli si fa anche
in termini di effetto fra il 5° e il 95° quantile di attività di ciascun disegno.

## 6. Validazione della procedura sul disegno DPD, prima di leggere i tilt

La procedura M di P2f (REML con componente temporale AR(1) bivariata e funzione di varianza individuale) è validata solo
sul disegno HMI. Prima di calcolare i tilt si esegue una validazione sul disegno DPD (date, latitudini, aree; nessun
tilt), con il generatore P2f riscalato a 15° di rumore individuale e anche a 30° (dispersione dei tilt in luce bianca
in McClintock & Norton 2013):

- scenari P2f 0 (nessun rumore temporale), 1 (AR(1) 0,5), 2 (AR(1) 0,9), 7 (salti di 20 CR) e 9 (eteroschedastico con
  t₄), 2000 cataloghi sotto nulla ciascuno, più 500 cataloghi con effetto −0,2·γ₀ negli scenari 1 e 7;
- criterio come in P2f: limite superiore di Clopper–Pearson al 95 % dei falsi verdetti complessivi ≤ 4 % negli scenari
  correttamente specificati (0, 1, 2), e riportati separatamente quelli mal specificati (7, 9);
- semi nuovi, disgiunti da quelli già usati e registrati; benchmark prima della griglia, con tetto di 8 ore su 12
  processi (misurato su un campione di unità rappresentativo, non solo sulla costruzione del disegno).

Se la validazione fallisce negli scenari correttamente specificati, il risultato su DPD è **descrittivo**: si riporta
l'intervallo nominale con questa avvertenza e nessun verdetto.

## 7. Raccordo con P1 nella sovrapposizione (descrittivo)

Per i gruppi DPD 2010-05 → 2016 con numero NOAA presente anche in P1 (HMI): differenza assiale e differenza nella
variabile di Joy fra tilt in luce bianca e tilt magnetico di P1, mediana con minimo e massimo, correlazione circolare,
coefficiente di Joy nei due casi sullo stesso insieme. Serve a dire quanto i due tilt siano la stessa grandezza; non
entra nella stima di T3.

## 8. Alternativa magnetica: Mount Wilson

I tilt **magnetici** dai magnetogrammi di Mount Wilson (e MDI) di Li & Ulrich 2012 (ApJ, ottobre 2012; magnetogrammi
MWO 1974–2012 e MDI 1996–2010, circa 30 600 macchie) coprono più cicli con le polarità, cioè la grandezza di P1.
La pagina indicata nell'articolo (www2.ess.ucla.edu/~jingli/ApJ201210/) non risponde al 18 novembre (timeout):
disponibilità da verificare, eventualmente scrivendo agli autori. Prima di congelare questo protocollo va verificato se quel catalogo è pubblico e con quale
copertura: se lo è, conviene valutare la stessa analisi su di esso (stesso calcolo analitico della nota, poi protocollo
proprio). I magnetogrammi MWO dell'altro progetto (1967–2012) permetterebbero tilt misurati da noi, a costo molto maggiore.

## 9. Ordine

Revisione di Codex → congelamento → acquisizione `sDPD` con SHA-256 → validazione del §6 sul disegno (nessun tilt) →
tilt e stima una sola volta → raccordo del §7 → rapporto con le due implementazioni indipendenti come per MDI–HMI.

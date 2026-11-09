# Risultati di P3 — confronto C1 con BARD (livello 1)

Protocolli: P3, P3b, P3c. Esecuzione: `python/sharpbl/run_p3.py` (commit dei
risultati `9824ac4`). Tabelle in `results/P3/`. C2 (record della serie P1)
è stato eseguito dopo l'elaborazione completa della serie: vedere la sezione
C2 più sotto.

## Conclusione

Sulle 999 regioni del campione C1 HMI, le misure SHARP mostrano accordo con
BARD secondo tutti i criteri operativi preregistrati. Il confronto sostiene la
coerenza dell'implementazione geometrica e delle convenzioni magnetiche nel
campione esaminato.

| Indicatore | Valore [IC 95%, bootstrap per famiglie] | Criterio |
|---|---|---|
| Mediana distanza assiale del tilt δ | 3,4° [3,1; 3,8] | ≤ 10° |
| Fisher & Lee ρ_FL | 0,72 [0,67; 0,76] | limite inferiore > 0 |
| Polarità leading uguale | 97,1% [96,1; 98,1] | ≥ 90% |
| Hale ricalcolato uguale | 97,1% [96,1; 98,1] | ≥ 90% |
| Separazione, Spearman | 0,80 [0,76; 0,83] | ≥ 0,7 |
| Latitudine, mediana \|Δλ\| | 0,21° [0,20; 0,23] | ≤ 1° |

Solo riportati: Spearman del tilt su rappresentazione fissa 0,77; Hale
pubblicato 97,1%; rapporto mediano delle separazioni 0,95; rapporto mediano
dei flussi nostro/BARD 1,67. Livello 2 (BARD-MDI, 68 regioni, descrittivo):
δ 2,1°, ρ_FL 0,83, leading 95,6%.

## Limiti

1. **Copertura.** Le 999 regioni sono circa il 69% delle 1457 regioni BARD.
   L'accordo riguarda questo sottoinsieme: le esclusioni (nessuna HARP in
   posizione 283, non assegnate nell'abbinamento uno a uno 140, QUALITY 18,
   altre 17) e la competizione nell'abbinamento possono selezionare regioni
   più semplici da confrontare.
2. **Flusso.** Il rapporto mediano 1,67 è una differenza materiale. Prodotti
   (Br contro linea di vista) e soglie diversi sono spiegazioni plausibili, ma
   il rapporto da solo non ne identifica la causa. C1 **non** valida
   l'ampiezza di S_BL né del contributo al dipolo.
3. **Ciclo.** Nel 2010–2016 entrambe le classificazioni assegnano le regioni
   al ciclo 24, quindi polarità leading, Hale ricalcolato e Hale pubblicato non
   sono conferme indipendenti; questo confronto **non** verifica la regola di
   assegnazione del ciclo nelle sovrapposizioni.
4. BARD non certifica la maschera SHARP (P3 §1).

## Analisi descrittiva dei disaccordi (senza modificare campione o criteri)

Tabelle: `results/P3/P3_C1_DISCORDANT_DESCRIPTIVE.csv` (righe per regione) e
`P3_C1_DISCORDANT_SUMMARY.csv`. Gruppi: le 29 regioni con leading discordante,
le 29 con lo scarto di tilt maggiore, il resto del campione (954). I primi due
gruppi **si sovrappongono** (13 regioni in comune, 45 regioni distinte in
tutto) e non sono categorie disgiunte; il resto (999 − 45 = 954) è disgiunto
da entrambi. Mediane:

| | Leading discordante | Maggiori scarti di tilt | Resto |
|---|---|---|---|
| Separazione nostra / BARD (gradi) | 1,7 / 2,7 | 2,0 / 3,1 | 4,1 / 4,4 |
| Sbilancio di flusso nostro / BARD | 0,38 / 0,20 | 0,26 / 0,33 | 0,09 / 0,22 |
| Rapporto dei flussi nostro/BARD | 2,4 | 2,4 | 1,7 |
| Frazione HARP con più regioni NOAA | 0,28 | 0,21 | 0,19 |
| Frazione HARP senza regione NOAA | 0,21 | 0,21 | 0,08 |
| Distanza di abbinamento d | 0,28 | 0,36 | 0,15 |

Lettura descrittiva: i disaccordi si concentrano in regioni **compatte**
(separazione circa metà del resto), con un **forte sbilancio** tra le due
polarità nella nostra misura, abbinamenti meno stretti e più spesso HARP con
più regioni NOAA o senza NOAA. Questo è compatibile con differenze di
segmentazione (che cosa entra nella maschera di ciascun metodo), regioni
multipolari e abbinamenti meno certi, più che con un errore sistematico di
segno; non lo dimostra.

## C2 — confronto con i record già selezionati della serie (solo riportato)

Eseguito dopo l'elaborazione completa della serie P1, con i controlli interni
obbligatori superati. Per le stesse coppie di C1,
misura della HARP nel catalogo P1: record di controllo (flusso massimo entro
±60°) e record primario (più vicino al meridiano centrale). 40 HARP abbinate
non hanno record primario e mancano in C2.

| HMI | n (famiglie) | \|Δt\| da BARD, mediana | δ mediana | ρ_FL | leading | separazione ρ | \|Δλ\| mediana | flusso nostro/BARD |
|---|---|---|---|---|---|---|---|---|
| C1 (contemporaneo) | 999 (879) | ≤ 1 h | 3,4° | 0,72 | 97,1% | 0,80 | 0,21° | 1,67 |
| C2 controllo | 962 (842) | 0,5 giorni | 4,5° | 0,68 | 96,9% | 0,73 | 0,27° | 1,82 |
| C2 primario | 829 (722) | 4,1 giorni | 7,4° | 0,53 | 96,4% | 0,58 | 0,46° | 0,95 |

Lettura: l'accordo è peggiore quando la nostra misura è più lontana in tempo
da quella di BARD, il che è compatibile con l'evoluzione delle regioni (P1d §3).
I tre campioni però hanno numerosità e selezioni diverse (999, 962, 829
regioni; il record primario richiede |lon| ≤ 30° e il campione principale
Φ ≥ 10²¹ Mx nell'istante del record), quindi la tabella da sola **non**
attribuisce il peggioramento esclusivamente alla distanza temporale. Lo stesso
vale per il rapporto dei flussi (circa 1,7–1,8 in C1 e C2-controllo, circa
0,95 in C2-primario): una spiegazione compatibile è che BARD misuri al massimo
del flusso e il record primario no, ma la selezione diversa può contribuire.
In ogni caso il rapporto dei flussi non è interpretabile come calibrazione.
La polarità leading resta concorde al 96–97%. Livello 2 (MDI): C2 controllo 66 regioni, δ 3,5°; C2 primario
61 regioni, δ 4,7°. Nessun esito formale per C2 (P3 §3).

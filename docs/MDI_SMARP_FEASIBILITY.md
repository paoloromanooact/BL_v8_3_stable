# MDI/SMARP e ciclo 23 — studio di fattibilità

Stato: **studio documentale, versione del 2026-11-13 (prima bozza del 2026-11-11); non è un
protocollo.** Nessuna query JSOC, nessun download di mappe e nessun calcolo scientifico eseguito per
questo studio. Le affermazioni con una fonte sono verificate sulla fonte indicata (§1); quelle senza
fonte sono valutazioni nostre e lo dicono. Disponibilità effettiva degli archivi da verificare.

**Domanda.** Si può estendere la serie della sorgente BL (P1) e i test del quenching (P2/P2f) al
ciclo 23 usando MDI (SMARP), in modo che le misure siano confrontabili con quelle HMI (SHARP)?
**Risposta breve:** è plausibile come catalogo descrittivo, ma la confrontabilità quantitativa della
misura e il guadagno statistico non sono dimostrati; il primo passo è un confronto nella breve
sovrapposizione, con un protocollo proprio. Non si concatena nulla con P1.

## 1. Fonti primarie consultate

| Rif. | Fonte | Che cosa se ne usa |
|---|---|---|
| [B21] | Bobra, Wright, Sun & Turmon 2021, *SMARPs and SHARPs: Two Solar Cycles of Active Region Data*, ApJS 256, 26 ([arXiv:2108.07918](https://arxiv.org/abs/2108.07918), testo in [ar5iv](https://ar5iv.arxiv.org/html/2108.07918)) | serie, cadenze, copertura, sovrapposizione, griglia CEA, maschere, rumore, confronto dei parametri |
| [B14] | Bobra et al. 2014, *The HMI Vector Magnetic Field Pipeline: SHARPs*, Sol. Phys. 289, 3549 ([arXiv:1404.1879](https://arxiv.org/abs/1404.1879)) | definizione di SHARP, cadenza 12 min, campo vettoriale |
| [H14] | Hoeksema et al. 2014, *The HMI Vector Magnetic Field Pipeline: Overview and Performance*, Sol. Phys. 289, 3483 ([arXiv:1404.1881](https://arxiv.org/html/1404.1881)) | inversione VFISV alla base di Br; §7.2.3: LOS da inversione e LOS magnetografico possono differire nello stesso strumento, soprattutto nei campi forti |
| [S13] | Sun 2013, nota sulle coordinate e sui vettori delle SHARP ([arXiv:1309.2392](https://arxiv.org/html/1309.2392), §§1–2) | rimappatura dei punti e trasformazione dei vettori sono operazioni distinte |
| [L12] | Liu, Hoeksema, Scherrer et al. 2012, *Comparison of Line-of-Sight Magnetograms Taken by SDO/HMI and SOHO/MDI*, Sol. Phys. 279, 295 ([Springer](https://link.springer.com/article/10.1007/s11207-012-9976-x), [ADS](https://ui.adsabs.harvard.edu/abs/2012SoPh..279..295L/abstract)) | relazione MDI–HMI, rumore, perdita di p-mode in MDI |
| [S95] | Scherrer et al. 1995, *The Solar Oscillations Investigation – Michelson Doppler Imager*, Sol. Phys. 162, 129 ([Springer](https://link.springer.com/doi/10.1007/BF00733429)) | strumento MDI, magnetogrammi LOS full-disk ogni 96 min |
| [S12] | Schou et al. 2012, *Design and Ground Calibration of HMI*, Sol. Phys. 275, 229 | strumento HMI (riga Fe I 6173 Å, camere 4096²) |
| [MJ21] | Muñoz-Jaramillo, Navarrete & Campusano 2021, ApJ 920, 31; catalogo BARD v3.0 ([doi:10.7910/DVN/QEMSZ2](https://doi.org/10.7910/DVN/QEMSZ2)) | tilt di regioni bipolari MDI 1996–2010 e HMI 2010–2016; **già in `data/sharp/external/BARD/`** |
| [K24] | Kosovich et al. 2024, *Time Series of Magnetic Field Parameters of Merged MDI and HMI SHARPs* ([arXiv:2401.05591](https://arxiv.org/abs/2401.05591v3)) | esempio di fusione di parametri SMARP/SHARP per i brillamenti |

Non verificati sulla fonte e quindi non usati: i fattori di riscalatura di [K24] (l'abstract non li
riporta); i dettagli del repository [github.com/mbobra/SMARPs](https://github.com/mbobra/SMARPs) oltre
a quanto già riportato nella prima bozza.

## 2. Differenze strumentali e di prodotto

| Aspetto | SMARP / MDI | SHARP / HMI (P1) | Fonte | Conseguenza per noi (valutazione nostra) |
|---|---|---|---|---|
| Serie | `mdi.smarp_96m`, `mdi.smarp_cea_96m` | `hmi.sharp_720s`, `hmi.sharp_cea_720s` | [B21] tab. 1 | nuove query e nuovo inventario dei metadati |
| Copertura | gennaio 1996 – 28 ottobre 2010 | dal 2010 | [B21] | ciclo 23 completo e coda del 24 |
| **Sovrapposizione** | **1 maggio – 28 ottobre 2010** (circa 6 mesi, vicino al minimo) | | [B21] | poche regioni per il confronto; [B21] ne confronta 51 regioni NOAA |
| Cadenza | 96 minuti | 12 minuti | [B21], [S95], [B14] | record vicino al meridiano meno preciso (fino a ±48 min) |
| **Campo misurato** | **solo linea di vista (LOS)** | vettore completo; P1 usa **Br** | [B21], [H14] | **S_BL, D e il tilt di P1 non sono calcolabili nello stesso modo**: serve un Br approssimato |
| Br nel prodotto CEA | non fornito: il segmento `magnetogram` CEA è il campo LOS rimappato, non trasformato in Br | Br dall'inversione | [B21], [B14] tab. A.8, [S13] | la rimappatura CEA sposta i punti, non trasforma il vettore. Per proiezione B_LOS = μ·Br + termine delle componenti orizzontali: B_LOS = Br è garantito solo al centro del **disco**, non al centro della patch [corretto dopo la revisione: la prima versione parlava del centro della patch]. Br ≈ B_LOS/μ è un'ipotesi di campo radiale, da validare (§3) |
| Griglia CEA | 0,12°/pixel | 0,03°/pixel | [B21] | area del pixel 16 volte maggiore ([B21] scala CMASKL per 16); soglie in pixel non trasferibili |
| Riga e risoluzione | Ni I 6768 Å, risoluzione circa 4″ | Fe I 6173 Å, 4096², risoluzione circa 1″ | [L12], [S12] | risposta diversa a campi forti e a risoluzione; centroidi e separazioni da verificare |
| **Scala della densità di flusso LOS** | **MDI = −0,18 + 1,40 × HMI** (densità di flusso LOS in Mx cm⁻², magnetogrammi full-disk, MDI ricalibrato), con dipendenza dalla distanza dal centro del disco | | [L12] (abstract; pagina ed equazione del fit e sue condizioni da recuperare dal testo completo) | è una relazione affine pixel per pixel della densità di flusso, non una calibrazione di Φ integrato: non si trasferisce automaticamente a somme dei moduli, soglie o Br; l'intercetta non è un offset del flusso totale e 1,40 non è una calibrazione universale |
| Rumore LOS (magnetogrammi full-disk) | 26,4 Mx cm⁻² (1 min), 16,2 (5 min) | 6,3 Mx cm⁻² (720 s); [B21] riporta 6,4 | [L12], [B21] | rapporto MDI/HMI circa 4,2 per i magnetogrammi di 1 min e circa 2,6 per quelli di 5 min [corretto: la prima versione diceva «circa 4 volte»]; la cadenza di 96 min non è il tempo di integrazione; sulla griglia CEA rimappata il rumore è correlato tra pixel; la soglia di 100 G di P1 ha un altro significato in termini di segnale/rumore |
| Altri effetti | perdita di p-mode significativa nei magnetogrammi MDI | praticamente assente | [L12] | rumore spazialmente correlato nei centroidi delle regioni deboli |
| Maschera | TARP: bitmap di attività > 36 | HARP: P1 usa bitmap ≥ 33 | [B21] | definizioni diverse; i codici non sono intercambiabili; TARPNUM ≠ HARPNUM |
| Parametri nella sovrapposizione | SMARP-LOS contro SHARP-LOS: Spearman 0,94 per il flusso non segnato e 0,79 per il gradiente medio; SMARP-LOS contro SHARP vettoriale per il gradiente: 0,36 [corretto: la prima versione attribuiva 0,36 a SHARP-LOS contro vettore]; 51 regioni NOAA co-osservate con osservazioni ripetute, non 51 istanti indipendenti | | [B21] §3.2, fig. 3 | correlazioni di rango, non un'accuratezza assoluta né una calibrazione per regione o per S_BL |
| Tilt bipolari indipendenti | BARD-MDI: tilt 1996–2010 da magnetogrammi MDI | BARD-HMI 2010–2016 | [MJ21] | confronto esterno per il ciclo 23 già disponibile localmente |

**Già misurato nel progetto (P3, livello 2, descrittivo):** le nostre misure HMI confrontate con
BARD-MDI nella sovrapposizione danno 68 abbinamenti in 62 famiglie, distanza assiale mediana del
tilt δ = 2,107°, ρ di Fisher–Lee 0,826, polarità leading concorde nel 95,6 % e rapporto dei flussi
HMI-nostro/MDI-BARD 1,17 (`results/P3/P3_BARD_SUMMARY.csv`, `docs/P3_RESULTS_C1.md`). Non sono 68
osservazioni indipendenti né necessariamente tutte le regioni della sovrapposizione: è un risultato
descrittivo sul campione abbinato con i filtri di P3, con metodi e selezione diversi (BARD non è un
primario HARP), non una prova generale di confrontabilità strumentale o di S_BL. BARD inoltre non è
cieco per questo progetto: i cataloghi sono già stati letti per P3.

## 3. Implicazioni per il progetto (valutazione nostra)

- **Br da LOS.** S_BL usa flusso, separazione, latitudine e tilt calcolati da Br. Con MDI si ha solo
  B_LOS; Br ≈ B_LOS/μ presuppone campo radiale, contiene le componenti orizzontali proiettate e
  amplifica il rumore quando μ è piccolo. Centro della patch e centro del disco sono posizioni
  diverse; un taglio in longitudine non fissa μ. La relazione di [L12] riguarda B_LOS, non Br.
- **Scala.** Il fattore 1,40 di [L12] è una relazione media pixel per pixel su full-disk; non è
  garantito che valga uguale per le regioni forti, vicino al lembo o sulla griglia CEA SMARP. Una
  correzione moltiplicativa del flusso non rende confrontabili centroidi, tilt e somme; η = D*/Φ può
  cambiare anche se il fattore si semplifica (selezione, geometria, contributi delle polarità).
- **Selezione.** I criteri di P1/P2 in pixel (20 pixel per polarità in P2) e la soglia di 100 G vanno
  riformulati in grandezze fisiche (area, flusso, segnale/rumore) e il campione va ridichiarato.
- **Cicli.** La finestra 23/24 esiste già in P1/P1c e la legge di Hale ha già la parità di ciclo in
  `cycle.py` [corretto: la prima versione suggeriva regole nuove]: vanno verificati dominio e
  trasferibilità sui dati MDI. La data di minimo per la fase (`run_p2.T_MIN`) e il segno del dipolo
  del ciclo (`run_p2.S_CYCLE`) coprono solo i cicli 24 e 25: l'estensione va implementata e validata
  senza scegliere segni dai risultati.
- **Attività.** SILSO emisferico copre il ciclo 23 (`ancillary/SILSO_HEMI/`, dal 1992), ma la
  normalizzazione attuale è sulla media del periodo HMI (2010-05 → 2026-09): estenderla cambia
  l'unità della pendenza β e quindi la griglia degli effetti; va decisa prima.
- **Confusione strumento/ciclo.** Il cambio di strumento coincide con il cambio di ciclo: una
  differenza strumentale residua può confondersi con un effetto fisico tra cicli, cioè proprio con il
  quenching tra cicli della letteratura.

## 4. Questioni da verificare (nessuna è risolta da questo studio)

| # | Questione | Come verificarla | Prima di |
|---|---|---|---|
| Q1 | Disponibilità attuale delle serie SMARP su JSOC, segmenti e versioni; copertura e lacune 1996–2010 | inventario dei metadati con un piano, risposte e hash conservati | qualunque download |
| Q2 | Numero di coppie TARP–HARP utilizzabili nella sovrapposizione (maggio–ottobre 2010) | inventario; associazione spaziale e temporale fissata prima, non solo NOAA | stima della potenza del confronto |
| Q3 | Bontà di Br ≈ B_LOS/μ per S_BL, D e tilt | su HMI stesso: Br contro LOS/μ, regione per regione | uso di qualunque Br MDI |
| Q4 | Effetto di risoluzione e risposta MDI | HMI LOS degradato a griglia e risoluzione MDI (con una specifica di risposta spaziale) contro MDI LOS | riscalatura |
| Q5 | Validità del fattore 1,40 [L12] per le grandezze di P1 sulla griglia SMARP, in funzione di μ e intensità | confronto per regione nella sovrapposizione | correzione del flusso |
| Q6 | Effetto del rumore MDI (circa 2,6–4,2 volte HMI secondo il magnetogramma) e della perdita di p-mode su soglia, centroidi e regioni deboli | simulazioni con rumore di tipo MDI su mappe HMI | criteri di selezione |
| Q7 | Corrispondenza tra maschere TARP (> 36) e HARP (≥ 33) e tra indicatori di qualità | specifiche delle due serie, non somiglianza dei nomi | campione |
| Q8 | Regole del ciclo 23 (confini 23/24, Hale, fase, segno del dipolo) | nuovo protocollo, come P1c | serie del ciclo 23 |
| Q9 | Normalizzazione dell'attività su un periodo esteso e suo effetto sulla scala degli effetti | decisione registrata prima | test P2/P2f estesi |
| Q10 | Beneficio statistico reale (HMI contro HMI+MDI) per T3, con incertezza della trasformazione e sistematiche dipendenti dall'attività | simulazioni sul disegno osservabile, semi indipendenti, regola di arresto | qualunque test inferenziale esteso |
| Q11 | Trasferibilità fuori dalla sovrapposizione (stabilità di MDI nel tempo, regioni più intense del ciclo 23) | verifiche temporali aggiuntive; dominio coperto contro estrapolato | uso del ciclo 23 intero |

## 5. Percorso proposto

1. **Inventario dei metadati** (Q1, Q2, Q7) con un piano registrato: nessun download di mappe.
2. **Esperimento solo HMI** (Q3, Q4, Q6): una **prova di sensibilità della pipeline a
   trasformazioni simulate**, sulla scala HMI. Non replica MDI e non ne valida risposta spettrale,
   saturazione, distorsioni, tracciamento e maschere, né la stabilità temporale; un esito favorevole
   non autorizza da solo la concatenazione. Confronti separati (proposta da fissare nel protocollo):
   Br HMI di riferimento (con le sue incertezze, non la verità fisica); LOS ottenuto proiettando il
   vettore HMI e diviso per μ, per isolare l'approssimazione radiale; LOS magnetografico HMI diviso
   per μ, per distinguere algoritmo LOS e inversione [H14 §7.2.3]; LOS degradato con risposta
   spaziale, campionamento e rumore dichiarati e poi trattato radialmente. Da fissare **prima** di
   scaricare e calcolare: campione stratificato (μ, flusso, complessità, latitudine, attività), con i
   casi difficili già visti e senza scegliere solo bipoli puliti; PSF e pixel angolari, integrazione e
   antialiasing (una griglia 4 volte più grossa non modella l'ottica); ordine di convoluzione,
   ricampionamento, rumore, rimappatura e divisione per μ; rumore HMI già presente e covarianza del
   rumore aggiunto (livelli 1 e 5 min, repliche con semi fissati); confronti a maschera fissa,
   separati dallo studio di selezione e segmentazione (la bitmap HMI degradata non ricrea il campione
   TARP); tempi di integrazione e cadenza separati; metriche per Φ, d, tilt, S_BL, D/D_bal ed η con
   mancate misure, cambi di validità, segni e compensazioni; soglie motivate e fissate; incertezza a
   livello di HARP o di famiglia, non di pixel o istanti; nessun verdetto sul quenching. Richiede il
   segmento LOS delle SHARP per un campione.
3. **Confronto nella sovrapposizione** (Q5) con un protocollo proprio: campione, associazione,
   unità indipendenti (regioni, non istanti), metriche, soglie e costi fissati prima.
4. **Solo se 2 e 3 lo sostengono:** regole del ciclo 23 (Q8, Q9) e serie descrittiva MDI separata;
   inferenza estesa solo dopo Q10 e una validazione propria. P2f validato su HMI non è
   automaticamente valido sul disegno esteso.
5. **In parallelo, a costo basso:** BARD-MDI [MJ21] offre già tilt e flussi bipolari del ciclo 23
   con un metodo indipendente; può dare un confronto descrittivo del coefficiente di Joy e della sua
   dipendenza dall'attività nel ciclo 23 senza la nostra pipeline, con le cautele di P3 (BARD misura
   al massimo del flusso; il rapporto 1,67 riguarda HMI-nostro contro HMI-BARD, mentre contro
   MDI-BARD è 1,17; nessuno dei due è una calibrazione). Richiede un piano proprio, con denominatori e
   istante di misura dichiarati.

## 6. Esito

**Fattibilità documentale plausibile; confrontabilità quantitativa della misura e guadagno
statistico non misurati.** Gli ostacoli principali sono la mancanza di Br in MDI (S_BL e D di P1
richiedono Br), la sovrapposizione breve e vicina al minimo (maggio–ottobre 2010), la scala del
flusso (MDI = −0,18 + 1,40 × HMI su full-disk, da verificare sulle grandezze di P1) e la confusione
tra strumento e ciclo. Il primo esperimento promettente è la prova di sensibilità solo HMI (§5.2),
pianificabile senza dati MDI; il suo costo relativo non è stato misurato. Non si avvia ora
l'estensione e non si modifica P1. T3 «non deciso» e T5 descrittivo restano tali.

## 7. Revisione esterna (2026-11-13, ZIP `e476509`)

Il revisore ha condiviso la conclusione prudente e chiesto correzioni recepite sopra e segnate
«[corretto]»: geometria (B_LOS = Br solo al centro del disco; la rimappatura CEA non trasforma il
vettore, [S13]); coppia della correlazione 0,36 (SMARP-LOS contro SHARP vettoriale); rapporto del
rumore (circa 4,2 a 1 min, 2,6 a 5 min); qualificazione della relazione 1,40 come relazione di densità
di flusso LOS pixel per pixel; esperimento solo HMI come prova di sensibilità con i punti da fissare
prima; numeri BARD confermati (68 abbinamenti in 62 famiglie, δ 2,107°) con il contesto del rapporto
dei flussi; finestra 23/24 e parità di Hale già presenti. Il revisore non ha avuto accesso al testo
completo di [L12]: l'intercetta −0,18 e le condizioni del fit restano da riscontrare sul testo.

# Revisione Codex della bozza MDI rev. 2 — 23 novembre 2026

Oggetto: docs/PROTOCOL_MDI_TILT_PILOT_DRAFT.md, commit 8f8b188.
Nessuna misura di tilt, selezione di gruppi o acquisizione eseguita da questa revisione.
L'impostazione Q1–Q3 è approvata. Restano precisazioni operative e la separazione consigliata di Q4.
Non allargare il pilota o aggiungere nuovi confronti per recepire questa nota.

## Decisioni sulle questioni aperte

- **15/15 e 3/2:** accettabili per un pilota esplorativo bilanciato, senza garanzia di precisione.
- **A entro ±6 ore e B entro 4 ore:** accettabili come limiti operativi. Non garantiscono contemporaneità
  con MWO o con i contributi della sinottica; riportare gli scarti reali e le mancate coppie.
- **R = 1000:** non è di per sé un problema, ma non risolve le specifiche mancanti di Q4.
  Sono disegni simulati, non 1000 nuovi cataloghi di risposte/validazioni M. Non avviarli ora.
- **Semi:** verificati 71 000 001, 71 100 001, 71 200 001 contro elenco MWO effettivo, benchmark, USED,
  S1, Joy e diagnosi S2: distinti e senza collisioni in questi insiemi.
- **Identità MWO:** sì, usare il pilota già misurato e un piccolo sottoinsieme R4 deterministico,
  fissato da metadati per coprire epoche/emisferi e casi BLANK. Non ricalcolare tutto R4.
  Il kernel va provato con soglie, criteri di pixel, precisione di lettura e area originali MWO,
  non con il nuovo filtro MDI di 10 pixel. Fissare tolleranze prima; non modificare sorgenti o prodotti conservati.

## 1. Definire correttamente le probabilità delle due fasi

L'allocazione è su due coorti: M1 e U = M0 unito M2. Le probabilità non sono calcolate separatamente
sulle numerosità M0 e M2. Per ogni strato, con N_g elementi della coorte, n1_g estratti al livello 1
e n2_g al livello 2, sono pi1 = n1_g/N_g e pi2 = (n1_g/N_g)(n2_g/n1_g) = n2_g/N_g
quando le numerosità sono fissate come da regola; gestire esplicitamente coorti vuote.
M0/M2 restano etichette informative. N/n significa quindi il reciproco della probabilità corretta
della coorte, non N0/n0 o N2/n2 a posteriori. Distinguere pesi campionari dai flussi della misura.
Specificare ordine delle 18 celle, delle due coorti e scelta del sottocampione L2 senza usare il successo L1.
Le mediane non pesate del campione bilanciato descrivono quel campione, non la popolazione completa.

## 2. Completare poche regole operative di Q1–Q3

- A: chiarire che si sceglie il più vicino fra i record ammissibili per i metadati (QUALITY=0),
  entro il limite fissato. Registrare i record scartati e non cercare un'altra immagine dopo un fallimento
  di misura. Per B, INTERVAL deve essere numerico/documentato: due valori mancanti non sono un modo uguale.
  A con modo ignoto può essere descritta come tale in Q2, ma non genera una coppia di ripetibilità omogenea.
- QUALITY=0 è un filtro operativo conservativo, non una dimostrazione di omogeneità o accuratezza.
  Riportarne le perdite per tempo/prodotto. Non allargare i bit ammessi dopo aver visto i tilt.
- Definire le finestre di quiete (posizioni, maschera, esclusione delle regioni) e la statistica robusta
  prima di misurare: per esempio MAD scalata se questa è la scelta, con formula e gestione di vuoti/NaN.
  Non basta «dispersione in finestre di quiete» senza algoritmo. Rimane dispersione osservata, non rumore puro.
- Per Q2/Q3 fissare i confini delle classi di separazione prima di leggerne gli scarti (ad esempio quantili
  delle separazioni misurate nel campione di riferimento sinottico, applicati uguali a tutti i confronti).
  Il bootstrap usa blocchi e estrazioni comuni fra emisferi; riportare n coppie e n blocchi per gruppo.
  Con meno di 10 coppie mantenere la regola già scritta. Se ci sono meno di tre blocchi distinti, riportare
  solo n/mediana e intervallo non valutabile. M2 può restare solo etichetta: per evitare di allargare il pilota,
  consiglio di rinviare il suo confronto MWO in giorni diversi, anziché aprire ora nuove classi temporali.

## 3. Convenzioni e test da rendere espliciti

Definire d_raw = t1 - t2 (che può uscire da ±180), d_dir = (d_raw+180)%360-180 se serve una differenza
orientata, e d_ax = (d_raw+90)%180-90. Non chiamare «grezza in ±180» una quantità già riavvolta.
Q2: ordine candidato sinottico meno riferimento fd(A); Q3: MDI meno MWO. Ripetibilità: ordine dichiarato A/B.
Usare lambda_DPD comune per d_gamma; se lambda_DPD = 0, d_gamma è non definito e si riportano d_ax e leading,
non uno zero artificiale. Il valore di ciascun tilt resta conservato e non viene cambiato da questa convenzione.

Nell'adattatore includere CRVAL2 nella formula generale di sinlat (nei file attuali è zero).
Fissare la conversione t_DPD -> tempo di Carrington e gli spareggi per N; test indipendente su passaggi e bordi
con mappe adiacenti e metadati reali, oltre al dipolo sintetico. Fonti/coordinate non sono un nuovo calcolo di tilt.
Scrivere nell'introduzione «nessun nuovo tilt di questo pilota»: tilt MDI 2010 e BARD sono già stati esaminati.

## 4. Q4: rinviarlo come fase separata, per mantenere circoscritto il pilota

Raccomandazione: il protocollo da congelare ora copre Q1–Q3. Q4 rimane un obiettivo successivo,
non un'esecuzione già autorizzata dal suo congelamento. La sua nota va definita dopo la lettura del pilota,
prima del calcolo prospettico, dichiarando quali informazioni sono già note. Non modifica né riapre T3 precedente.

Motivi concreti: la rev. 2 non fissa numericamente i tre livelli di sigma_x2, kappa, la definizione
residua di sigma_e, la resa/allocazione dei periodi full-disk non inventariati o la gestione dei flussi senza
donatori. La resa puntuale può essere zero su pochi casi; gli strati senza dati non diventano osservati
prendendo una media per attività. L'estrazione di flussi marginali per strato può perdere la relazione con
area/latitudine/attività, che pesa sulla precisione WLS. Queste assunzioni richiedono una specifica propria.
L'eventuale M esplorativa, dichiarata poco informativa, non diventa una misura della covarianza per Q4.

Se si desidera invece congelare anche Q4 adesso, prima completare tutte queste scelte, inclusa propagazione
dell'incertezza sulla resa, regole per gruppi senza donatori e condizioni di non calcolabilità. Non basta R=1000.
La separazione consigliata evita di bloccare il pilota con un secondo studio prospettico completo.

## ARISE e fonti

Inserire ora i riferimenti già verificati dal README degli autori:
- Wang, Jiang & Luo 2023, ApJS 268:55, I. Automatic Detection and Calibration:
  https://doi.org/10.3847/1538-4365/acef1b
- Wang, Jiang & Luo 2024, ApJ 971:110, II. Parameters for Solar Cycle Variability:
  https://doi.org/10.3847/1538-4357/ad5b5f
- https://github.com/Wang-Ruihui/A-live-homogeneous-database-of-solar-active-regions
Le fonti NASA/HMI non dimostrano la ricetta temporale esatta dei file MDI locali; corretta la dichiarazione
ora indeterminata. Non occorre assumere 32 ore per procedere al confronto descrittivo fra prodotti.

## Passo successivo

Aggiornamento mirato del testo, senza nuovi campioni o scenari: Q1–Q3 definiti, Q4 rinviato esplicitamente
come raccomandato. Poi controllo del testo finale per congelamento e revisione del codice prima delle misure.
Budget 220 file/1,5 GB/600 richieste resta un tetto tecnico proposto, non un'autorizzazione di rete.
Soli controlli locali e sintetici fino al passaggio previsto. Nessun nuovo dato MDI acquisito da Codex.

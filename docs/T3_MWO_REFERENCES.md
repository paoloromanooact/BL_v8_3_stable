# T3 su MWO e catalogo di tilt: riferimenti e attribuzioni (verificati il 20 novembre 2026)

Ogni voce dice per che cosa serve e che cosa è stato controllato sulla fonte (abstract o testo). Le voci marcate
**da verificare** non vanno citate con numeri finché non sono controllate sul testo completo.

## Dati e strumenti

- **Mount Wilson, magnetografo della torre di 150 piedi.**
  - Ulrich, R. K., Evans, S., Boyden, J. E., Webster, L. (2002), ApJS 139, 259. Testo completo letto (PDF del workshop
    sui magnetogrammi). §2: sistema a 24 canali «Starting in 1996», nuovo reticolo; §3: correzione di saturazione; la
    correzione dello zero è applicata dal 1996. Usato per le epoche (A3, README) e per i limiti di calibrazione.
  - Ulrich, R. K., Boyden, J. E., Tran, T. (2024), Solar Physics 299, «Calibration and Release of
    Magnetograms/Dopplergrams Obtained at the Mt. Wilson 150-Foot Tower Telescope (MWO)»: archivio 1967–2013.
    Volume verificato; numero d'articolo **da verificare**. Codex l'ha usato
    nell'audit: quel rilascio descrive file 256×256 alle 20 UT, diversi dai nostri file 512×512.
  - Howard, R. et al. (1983): sistema di osservazione precedente, citato da Ulrich et al. 2002. Riferimento completo **da
    verificare**.
- **Debrecen Photoheliographic Data (DPD).**
  - Győri, L., Ludmány, A., Baranyi, T. (2017), MNRAS 465, 1259: confronto fra i cataloghi di Debrecen. Abstract e
    testo letti: DPD da Gyula e Debrecen con buchi riempiti da altri osservatori; aree DPD circa 5 % sotto HMIDD.
  - Baranyi, T., Győri, L., Ludmány, A. (2016), Solar Physics 291, 3081–3102, «On-line Tools for Solar Data Compiled
    at the Debrecen Observatory and Their Extensions with the Greenwich Sunspot Data» (arXiv:1606.00669). Verificato.
- **SDO/HMI e SHARP (P1).**
  - Schou, J. et al. (2012), Solar Physics 275, 229–259: progetto e calibrazione di HMI.
  - Bobra, M. G. et al. (2014), Solar Physics 289, 3549–3578: SHARPs.
- **Numero di macchie SILSO:** WDC-SILSO, Royal Observatory of Belgium, Bruxelles; dicitura di attribuzione come nella
  provenienza di `ancillary/SILSO_*`.

## Lavori sulla stessa grandezza: priorità e confronto (importante per il rilascio e un eventuale articolo)

- **Li, J., Ulrich, R. K. (2012), ApJ 758, 115**, «Long-Term Measurements of Sunspot Magnetic Tilt Angles». Abstract letto:
  tilt di circa 30 600 macchie dai magnetogrammi medi giornalieri MWO 1974–2012 e da MDI 1996–2010; tilt mediamente
  maggiori nel sud che nel nord, con una differenza che cresce con la latitudine.
  - **Il nostro catalogo non è il primo catalogo di tilt magnetici MWO.** Le differenze da dichiarare sono:
    - posizioni dai gruppi DPD;
    - un record per gruppo con la regola congelata del primo giorno riuscito;
    - isolamento;
    - controlli di qualità documentati (A1 BLANK, A2 file GV 0,03, A3 distribuzioni anomale, giorno UTC);
    - riconteggio indipendente;
    - rilascio riproducibile con codice e hash.
  - Il loro catalogo non risultava scaricabile il 18 novembre (pagina in timeout).
  - **Verifica del 23 novembre:**
    - l'articolo (arXiv:1209.1642) non ha una dichiarazione di disponibilità dei dati; le sole tabelle sono
      aggregate (Tabella 1, legge di Hale; Tabella 2, dipendenza dalla latitudine);
    - la pagina degli autori (www2.ess.ucla.edu/~jingli/ApJ201210/) è ancora in timeout. La copia della Wayback
      Machine del 2026-07-20 contiene testo e figure, nessun file di dati;
    - VizieR non rispondeva nemmeno per un catalogo di controllo (Hipparcos): disponibilità lì non determinata.
    - **Nessun catalogo pubblico trovato.** Un confronto record per record richiederebbe di contattare gli autori;
      nessun contatto senza istruzione esplicita dell'utente.
  - Va citato come precedente e, se possibile, confrontato.
- **Wang, Y.-M., Colaninno, R. C., Baranyi, T., Li, J. (2014), ApJ 796, 1**, «Active-Region Tilt Angles: Magnetic Versus
  White-Light Determinations of Joy's Law» (arXiv:1412.2329). Abstract letto: confronto fra tilt in luce bianca DPD e tilt
  magnetici MWO nei cicli 21–23.
  - I tilt in luce bianca sono più piccoli e crescono meno con la latitudine.
  - Cause indicate: macchie della stessa polarità incluse nelle misure in luce bianca; plage, più inclinate delle macchie
    vicine, viste solo nel magnetico.
  - Le grandi incertezze non permettono di stabilire relazioni sistematiche fra tilt e ampiezza dei cicli 16–23.
  - **Rilevante per S1:** Wang et al. descrivono differenze di popolazione e di dipendenza dalla latitudine fra tilt
    magnetici e in luce bianca. Non garantiscono che lo scarto sia costante nel tempo o con l'attività. S1 resta un
    controllo relativo fra epoche e non certifica la calibrazione assoluta.

## Legge di Joy e quenching dei tilt

- **Dasi-Espuig, M., Solanki, S. K., Krivova, N. A., Cameron, R., Peñuela, T. (2010)**, A&A 518, A7, «Sunspot group tilt
  angles and the strength of the solar cycle».
  - Abstract: pendenze della legge di Joy 0,26 (MW) e 0,28 (KK) in gradi di tilt per grado di latitudine;
    anticorrelazione fra tilt medio normalizzato e forza del ciclo, r = −0,95 (MW) e −0,93 (KK) nella versione
    originale.
  - **Corrigendum** (A&A 556, C3, 2013), verificato il 20 novembre. La versione originale usava i tilt medi di ciclo
    di Kodaikanal con le latitudini medie di Mount Wilson. Coefficienti corretti: r = −0,79 per MW e −0,93 per KK;
    l'anticorrelazione è più debole della versione pubblicata. Citare sempre la versione corretta.
- **McClintock, B. H., Norton, A. A. (2013)**, Solar Physics 287, 215–227, «Recovering Joy's law as a function of solar
  cycle, hemisphere, and longitude». Abstract: pendenza della legge di Joy più debole (0,13–0,26), senza imporre tilt
  nullo all'equatore; la componente stocastica domina e impedisce di determinare la pendenza su scala di 11 anni.
- **Jiao, Q., Jiang, J., Wang, Z.-F. (2021)**, A&A 653, A27, «Sunspot tilt angles revisited: Dependence on the solar
  cycle strength».
  - Abstract: dati DPD, anche separati per emisfero, Kodaikanal e Mount Wilson; coefficiente di tilt anticorrelato con
    la forza del ciclo, in modo statisticamente significativo; metodo raccomandato: fit lineare tilt–latitudine senza
    raggruppamento, per gruppi con Δs > 2,5°.
  - La relazione T_lin = −0,00107·S_n + 0,61 (r = −0,85) usata nei protocolli HMI è riportata nel testo, non
    nell'abstract: già verificata per P2f, da ricontrollare prima di una citazione nuova.
  - **Attenzione:** è una dipendenza **fra cicli**, non dall'attività dentro il ciclo (T3).
- **Jha, B. K., Karak, B. B., Mandal, S., Banerjee, D.**, «Magnetic field dependence of bipolar magnetic region tilts on
  the Sun: Indication of tilt quenching» (arXiv:1912.13223), su MDI 1996–2011 e HMI 2010–2018.
  - Abstract letto: la distribuzione di B_max è bimodale; la dispersione dei tilt attorno alla legge di Joy cala con
    B_max; la pendenza γ₀ cresce lentamente con B_max e cala per B_max ≥ 2 kG.
  - Seguito con il catalogo tracciato AutoTAB: arXiv:2401.04255.
  - Rivista e volume **da verificare**. Riguarda il campo massimo della singola regione, non il flusso (Q3) né
    l'attività globale (T3).

## Attribuzioni per il rilascio (testo da concordare con i fornitori)

- Mount Wilson Observatory, 150-ft solar tower, synoptic program (UCLA): ringraziamento e citazione di Ulrich et al.
  2002 e 2024.
- Debrecen Heliophysical Observatory: DPD (Baranyi et al. 2016; Győri et al. 2017).
- SDO/HMI: dati per cortesia di NASA/SDO e dei team scientifici di HMI; SHARP (Bobra et al. 2014).
- WDC-SILSO, Royal Observatory of Belgium.

## Fonti consultate il 20 novembre

- [Li & Ulrich 2012, arXiv:1209.1642](https://arxiv.org/pdf/1209.1642)
- [Wang et al. 2014, arXiv:1412.2329](https://arxiv.org/abs/1412.2329)
- [Dasi-Espuig et al. 2010, A&A](https://www.aanda.org/articles/aa/full_html/2010/10/aa14301-10/aa14301-10.html)
- [McClintock & Norton 2013, Springer](https://link.springer.com/chapter/10.1007/978-1-4899-8005-2_14)
- [Jiao et al. 2021, arXiv:2106.11615](https://arxiv.org/abs/2106.11615)
- [Bobra et al. 2014, arXiv:1404.1879](https://arxiv.org/abs/1404.1879)
- [Schou et al. 2012, ADS](https://ui.adsabs.harvard.edu/abs/2012SoPh..275..229S/abstract)
- [Győri et al. 2017, arXiv:1612.03274](https://arxiv.org/abs/1612.03274v1)
- [Ulrich et al. 2002, PDF](https://www.predsci.com/~pete/research/magnetogram-workshops/1st-workshop/papers/ulrich02a.pdf)

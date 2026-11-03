# Struttura proposta dell'articolo (bozza)

Etichette: **[osservativo]** misure e controlli; **[esplorativo]** analisi dopo
aver visto la serie; **[descrittivo]** test senza verdetto.

## Titolo (proposte)

- *A per-region Babcock–Leighton source series from SDO/HMI SHARP maps
  (2010–2026): corrected geometry and masking, external validation, and the
  limits of inferring quenching*
- *Measuring the Babcock–Leighton source region by region with HMI SHARP:
  methods, validation and a calibrated look at quenching*

## Domanda centrale

Con le mappe SHARP di HMI si può misurare, regione per regione e in modo
verificabile, il contributo di ogni regione attiva alla sorgente
Babcock–Leighton su due cicli? E quanto di ciò che si può dire sul quenching
regge a un controllo della calibrazione inferenziale?

## Sezioni

1. **Introduzione.** Sorgente BL, tilt e quenching (tilt, latitudine,
   efficienza); perché una misura per regione; HMI SHARP; obiettivi.
2. **Dati.** hmi.sharp_cea_720s (Br, bitmap), metadati, selezione di un
   record per HARP (primario al meridiano centrale, controllo al massimo del
   flusso), QUALITY 0x80, ricomparse candidate; download diretto e
   provenienza. BARD (v3.0) per la validazione; SILSO emisferico.
3. **Metodo.** Mappe CEA oblique e WCS; maschera bitmap ≥ 33; centroidi,
   separazione, tilt sulla sfera; S_BL e contributo al dipolo D_bal;
   assegnazione del ciclo nelle sovrapposizioni; protocolli congelati ed
   emendamenti dichiarati (con l'elenco di ciò che era stato visto).
4. **Effetto delle correzioni rispetto alla v8.3 [osservativo, esplorativo].**
   Riproduzione esatta della v8.3; fattoriale maschera × geometria × ciclo:
   validità solo dalla maschera, effetti dominati dalla maschera, geometria
   complessiva ~1%, ciclo solo sulla classificazione Hale nelle
   sovrapposizioni; 404 su 4189 classificazioni Hale cambiate, simmetriche;
   casi diagnostici.
5. **La serie [osservativo].** Catalogo di 7133 HARP, diagramma a farfalla,
   somme per CR ed emisfero, dipolo cumulato iniziale (+4,3 G ciclo 24,
   −2,4 G ciclo 25 finora; non è il dipolo polare); concentrazione della
   sorgente in poche regioni e cancellazione [esplorativo]; primario contro
   controllo [esplorativo].
6. **Validazione esterna con BARD [osservativo].** Convenzioni risolte;
   copertura ed esclusioni; C1: accordo su tutti i criteri preregistrati
   (δ 3,4°, ρ_FL 0,72, leading 97%); limiti (copertura 69%, flusso, ciclo,
   maschera non certificata); C2 e sottoinsieme comune [esplorativo];
   disaccordi in regioni compatte e sbilanciate.
7. **Quenching [descrittivo].** Joy presente (γ0 ≈ 24°); pendenze del tilt,
   dell'efficienza e della latitudine rispetto all'attività con le loro
   incertezze; nessun verdetto confermativo.
8. **Calibrazione dell'inferenza: un risultato negativo documentato.**
   Bootstrap per CR, blocchi mobili, test calibrato per simulazione (P2d/P2e);
   validazione su 7 scenari × 2000 cataloghi: criterio non superato
   (falsi verdetti 3,3–4,7% negli scenari con persistenza, contro il limite
   del 4% e il nominale del 2,5%); scenari mal specificati; potenza della
   procedura non validata. Perché questo conta per gli studi di quenching
   basati su serie brevi e autocorrelate.
9. **Discussione.** Cosa è robusto (misura, maschera, validazione); cosa resta
   aperto (inferenza sul quenching); estensioni: SMARP (ciclo 23) come
   banco di prova confermativo cieco; confronto con il campo polare.
10. **Conclusioni.**

Appendici: dizionario del catalogo; elenco dei protocolli e degli
emendamenti con SHA-256; elenco delle informazioni viste prima di ogni
congelamento; riproduzione.

## Figure principali

1. Mappa SHARP di esempio con maschera ≥ 1 e ≥ 33, centroidi v8.3 e v8.4
   (da `hale_case_figures.py`, uno o due casi).
2. Effetti del fattoriale: per grandezza, effetto di M, G, C e interazioni.
3. Diagramma a farfalla colorato per segno di D* (fig1).
4. Somme per CR ed emisfero e dipolo cumulato iniziale (fig2).
5. Accordo con BARD: δ e separazione, C1 e C2 sul sottoinsieme comune.
6. Validazione P2d/P2e: falsi verdetti per scenario con limite di Clopper–Pearson
   e soglia del 4%.
7. Quenching descrittivo: γ contro attività e η contro attività, con la
   dicitura "descrittivo, nessun verdetto".

## Messaggio da evitare

Nessuna frase che presenti il quenching come rilevato o escluso; nessun
"nullo" per T5; T4 come pendenza descrittiva negativa, non come
contraddizione fisica; il dipolo cumulato è quello iniziale all'emersione.

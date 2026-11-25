# Letteratura: dalla sorgente BL delle regioni al campo polare (voce futura P)

25 novembre 2026, Claude. Ricerca bibliografica fatta su richiesta dell'utente, con accesso alla rete autorizzato.
**Livello di verifica:** abstract, sintesi dei motori di ricerca e pagine arXiv/editore. **Non** ho letto gli articoli
completi. Numeri e affermazioni qui sotto vanno ricontrollati sulla fonte primaria prima di qualunque citazione in un
testo. Collegata a `docs/BL_WORK_PLAN.md` §4bis.

## 1. Che cosa è già stato fatto

**SFT con le regioni osservate come sorgente: il campo polare di un ciclo si riproduce.**
- Simulazione continua 2010–2024 con le regioni attive osservate assimilate come sorgente (arXiv 2506.01416).
  Riproduce l'andamento del dipolo assiale, i tempi d'inversione dei poli e il diagramma a farfalla magnetico di
  HMI, senza diffusione radiale né variazioni ciclo-dipendenti del flusso meridionale. Trova un trasporto polare
  anomalo nell'emisfero sud del ciclo 24: circa il 46 % del flusso non segnato viene da regioni emerse nei CR
  2141–2160. → https://arxiv.org/html/2506.01416v1
- Jiang, Cameron & Schüssler (2015, ApJL 808, L28), «The cause of the weak solar cycle 24».
  → https://arxiv.org/pdf/1507.01764
- Inversione del campo polare e trasporto nel ciclo 24. → https://ar5iv.arxiv.org/html/1410.8867

**Più cicli con le inclinazioni osservate (luce bianca).**
- SFT 1913–1986 (cicli 15–21) con la variazione ciclo per ciclo dei tilt dei gruppi di macchie (Mount Wilson,
  Kodaikanal). Riproduce le inversioni polari se si includono i tilt dipendenti dal ciclo.
  → https://arxiv.org/pdf/1006.3061

**L'approssimazione bipolare** (rilevante anche per il nostro pilota mappa–bipolo).
- Yeates (2020, Sol. Phys. 295, 119): database di regioni bipolari ricavato dalle patch HMI (2010–2020), con flusso
  e dipolo assiale della regione conservati. L'approssimazione bipolare **sovrastima di circa il 24 % il campo polare
  di fine ciclo**, perché trascura le strutture multipolari e asimmetriche. Database e codice sono pubblici.
  → https://ar5iv.labs.arxiv.org/html/2008.03203
- Wang, Jiang & Wang (2021): metodo algebrico generalizzato sulla distribuzione completa del campo della regione
  (SHARP), con un nucleo a funzione d'errore che dipende dalla latitudine. Anche qui l'approssimazione bipolare
  simmetrica sovrastima sistematicamente il dipolo al minimo. → https://arxiv.org/pdf/2104.04307v1

**Contributo delle singole regioni.**
- Petrovay, Nagy & Talafha (2020), metodo algebrico I e II: contributo «ultimo» al dipolo di ogni regione senza
  simulazioni SFT. → https://arxiv.org/pdf/2009.02299 ; https://arxiv.org/pdf/2009.02300
- Whitbread, Yeates & Muñoz-Jaramillo (2018, ApJ):
  - il ~10 % delle regioni più importanti definisce i salti del dipolo, ma il contributo cumulato delle regioni deboli
    non è trascurabile;
  - nel ciclo 23 servono più regioni che nei cicli 21–22;
  - noto il dipolo iniziale, il contributo finale si prevede dalla sola latitudine.

  → https://arxiv.org/pdf/1807.01617
- Nagy et al. (2017), regioni «rogue»: poche regioni anomale (anti-Joy o anti-Hale) vicino all'equatore possono
  pesare molto, fino a fermare la dinamo nei casi estremi. → https://ar5iv.arxiv.org/html/1712.02185

**Database di regioni su più cicli con MDI+HMI** (il lavoro più vicino a un bilancio multi-ciclo).
- Wang, Jiang & Luo (2023, ApJS) e la parte II (2024): database «live» e omogeneo di regioni da magnetogrammi sinottici
  MDI e HMI, dal 1996 (cicli 23–25). Flusso e area calibrati sui periodi comuni; parametri per la variabilità del
  ciclo; contributo al dipolo assiale. Versione 2.0 su Zenodo. → https://arxiv.org/pdf/2308.06914 ;
  https://arxiv.org/pdf/2405.06224

**Quadro teorico e rassegne.**
- Cameron & Schüssler (2015, Science): il flusso toroidale netto generato in un emisfero è determinato dal flusso
  emerso in superficie, principalmente dal campo polare quasi dipolare. → https://ar5iv.arxiv.org/html/1503.08469
- Yeates, Cheung, Jiang, Petrovay & Wang (2023, Space Sci. Rev.), «Surface Flux Transport on the Sun».
  → https://www.arxiv.org/abs/2303.01209
- Petrovay (2020, Living Rev. Sol. Phys.), «Solar cycle prediction». → https://ar5iv.arxiv.org/html/1907.02107

## 2. Che cosa resterebbe di nuovo per noi (valutazione prudente)

La domanda «le regioni osservate costruiscono il campo polare?» è centrale ma **non nuova**. Per HMI (cicli 24–25) un
SFT con le regioni assimilate riproduce già il campo polare; su più cicli esistono SFT con tilt in luce bianca e un
database MDI+HMI per i cicli 23–25. Un contributo nostro avrebbe senso solo in queste direzioni, da verificare:

1. **Bilancio con un modello d'errore esplicito e un confronto pre-registrato:**
   - incertezze di misura per regione, dalla ripetibilità C;
   - discrepanza del trasporto, da BT;
   - dipendenza fra regioni (famiglie e, più avanti, nests);
   - lettura bayesiana del «quanto chiude» il bilancio, invece di un accordo qualitativo.
2. **Tilt magnetici MWO sui cicli 21–23,** con la deriva strumentale modellata e il ponte DPD (BQ-M), invece dei soli
   tilt in luce bianca. Va verificato che nessuno l'abbia già fatto con questi dati.
3. **Serie polare omogenea dal 1966 con incertezze per CR,** dal progetto separato e con le regole di separazione.

Rischi già noti:
- ampiezza della sorgente senza calibrazione esterna (rapporto con BARD-HMI circa 1,67);
- flusso fuori dalle HARP;
- parametri di trasporto confondibili;
- concorrenza diretta del gruppo Wang/Jiang sul database MDI+HMI dei cicli 23–25.

## 3. Conseguenze immediate sul lavoro in corso

- **Pilota mappa–bipolo (punto 1 SFT):** Yeates (2020) e Wang, Jiang & Wang (2021) hanno già misurato su HMI/SHARP che
  il bipolo sovrastima il dipolo finale (circa 24 %). Il nostro pilota va presentato come **replica ed estensione**:
  - campione stratificato e pesato;
  - proxy P1;
  - sensibilità di forma e soglia;
  - confronto con l'evoluzione osservata (punto 2 SFT).

  Non va presentato come primo risultato. I loro numeri sono un termine di confronto da citare, non da usare per
  scegliere parametri (il protocollo è congelato).
- **Voce P:** prima di una specifica serve leggere per intero almeno 2506.01416, Wang–Jiang–Luo I/II, Whitbread 2018
  e Cameron et al. 2010, e verificare se il bilancio multi-ciclo con tilt magnetici esista già.
- **BQ-M:** il database MDI+HMI (Wang, Jiang & Luo) è una possibile fonte di confronto per il ciclo 23. Il suo uso
  richiede una decisione esplicita, senza trasferimento automatico.

## Fonti

- https://arxiv.org/html/2506.01416v1
- https://arxiv.org/pdf/1507.01764
- https://ar5iv.arxiv.org/html/1410.8867
- https://arxiv.org/pdf/1006.3061
- https://ar5iv.labs.arxiv.org/html/2008.03203
- https://arxiv.org/pdf/2104.04307v1
- https://arxiv.org/pdf/2009.02299
- https://arxiv.org/pdf/2009.02300
- https://arxiv.org/pdf/1807.01617
- https://ar5iv.arxiv.org/html/1712.02185
- https://arxiv.org/pdf/2308.06914
- https://arxiv.org/pdf/2405.06224
- https://ar5iv.arxiv.org/html/1503.08469
- https://www.arxiv.org/abs/2303.01209
- https://ar5iv.arxiv.org/html/1907.02107

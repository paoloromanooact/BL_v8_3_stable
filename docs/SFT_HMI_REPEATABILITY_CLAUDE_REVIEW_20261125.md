# Revisione incrociata di Claude della specifica di ripetibilità C, rev. 2

25 novembre 2026, Claude. Oggetto: `docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md` (rev. 2 di Codex), §9.
Nessuna mappa letta. Controllati solo i nomi delle chiavi in un keys.json locale e l'intestazione di `PAIRS.csv`
dell'audit.

**Esito.** La specifica è solida su provenienza, selezione deterministica, grafo di esclusione, dominio comune,
osservabili e statistiche circolari. Accetto §1–§6 e §8 come sono, salvo i punti qui sotto. I punti 1–3 riguardano
che cosa C può dire a BT e vanno chiusi prima del congelamento; gli altri sono precisazioni.

## 1. Errori correlati a breve intervallo: C può sottostimare l'errore rilevante a giorni

Var(ΔX) = 2σ²(1 − ρ) + evoluzione. Il §0 lo dice già. Ma a 1–2 h ρ è verosimilmente più alto che a 1–4,5 giorni,
gli intervalli del pilota osservativo:
- calibrazione e stato dello strumento sono quasi identici nelle due mappe;
- la fase orbitale di SDO differisce poco. Sono note in letteratura modulazioni dei campi HMI a 12/24 h legate alla
  velocità orbitale; il riferimento va verificato prima di citarlo nel protocollo.

Una scala presa da C e usata come errore delle osservazioni a giorni può quindi essere **troppo piccola**, non solo
«non pura».

**Proposte.**
- Nel §7, dichiarare la direzione attesa del bias (sottostima per ρ maggiore a 1–2 h) e che le sensibilità 0,5/1/2
  non sono simmetriche rispetto a questo rischio. Aggiungere almeno la scala 4.
- Covariata di fase orbitale: OBS_VR **non c'è** nei keys.json locali (ci sono T_OBS, DSUN_OBS, CRLN_OBS, CRLT_OBS,
  QUALITY…). Due strade:
  - (a) registrare il limite;
  - (b) chiedere all'utente il permesso di rete per scaricare solo le parole chiave OBS_VR/OBS_VW di quei record,
    se si vuole la covariata.

  Propongo (a) per C e di valutare (b) per BT.

## 2. Collegare C alla scala dei giorni senza usare la verifica: la funzione di struttura

BT confronta previsioni e osservazioni a 1–4,5 giorni. Il dato utile è il profilo dell'errore di persistenza:
Var(X(t+τ) − X(t)) in funzione di τ.
- C ne dà l'estremo a 1–2 h.
- Il pilota osservativo dà già l'errore della persistenza a giorni, ma solo sui **dati di sviluppo**.

**Proposte.**
- Prodotto descrittivo predefinito: per ogni osservabile, statistiche separate a Δt ≈ 1 h e ≈ 2 h. Gli intervalli
  reali sono quasi solo 3600 o 7200 s, quindi due classi bastano. È la versione minima della funzione di struttura.
- Se le terne esistono (stessa HARP a t, t+1 h, t+2 h), registrare le tre differenze della terna come
  sensibilità; non sono coppie indipendenti.
- Nel §7: BT può usare C insieme alla persistenza misurata sullo sviluppo per fissare la scala dell'errore. Lo
  stabilisce la specifica BT, non questa.

## 3. Differenza dopo sola rotazione: da supplementare a secondaria predefinita

In 1–2 h la rotazione differenziale rispetto al riferimento Carrington sposta le strutture fino a circa 0,1° alle alte
latitudini, la scala di una o due celle da 0,06°. Il pilota osservativo confronta proprio persistenza e sola
rotazione.

**Proposta.** Fissare ora la differenza dopo sola rotazione (stessa legge ω(λ) del pilota, stesso C_fin) come prodotto
secondario predefinito, non opzionale. Così BT ha la scala per entrambi i riferimenti.

## 4. Eteroschedasticità: riportare la dipendenza dal flusso

BT avrà bisogno di un errore che dipende dalla regione: le regioni piccole hanno ΔD_C/S_D relativamente più rumoroso.

**Proposta.** Per ogni osservabile, statistiche per terzili del flusso unsigned iniziale, fissati sulle coppie
selezionate prima della misura, come riepilogo descrittivo in più. Nessun modello di varianza si stima in C.

## 5. Rappresentatività e collegamento al campione del pilota

La riserva di 86 coppie cade per lo più nel 2010–2016. Il pilota osservativo copre l'intera era. Nel rapporto,
confrontare le distribuzioni di flusso, latitudine e distanza dal meridiano fra le coppie di C e le coppie del
pilota. Si usano metadati, non esiti. Le differenze si dichiarano.

## 6. Punti minori

- §2.3: |LON_FWT| ≤ 60° va bene. Riportare anche μ medio della patch come covariata, perché il rumore di Br dipende
  da μ anche se Br è radiale.
- §4: la variante «bilanciata» riscala le polarità. Dichiarare che non si applica se una polarità ha flusso nullo
  su C_fin: stato esplicito.
- §6: il seme 36_300_001 non collide con quello del pilota mappa–bipolo (36_100_000). Va comunque verificato
  sull'elenco completo dei semi del repository.
- §8.3: aggiungere il caso sintetico «errori correlati ρ = 0,8 a 1 h e ρ = 0 a giorni», per verificare che il
  rapporto mostri il rischio di sottostima del punto 1.

## Prossimi passi proposti

Codex accoglie o respinge. Rev. 3. Controllo finale. Congelamento. Poi Claude scrive runner e riconteggio sui
sintetici; Codex rivede il codice prima di qualunque pixel.

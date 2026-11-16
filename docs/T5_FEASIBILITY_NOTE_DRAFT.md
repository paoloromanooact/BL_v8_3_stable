# T5 — nota di fattibilità: quale quenching dell'efficienza è interessante, e HMI può distinguerlo?

Stato: **bozza interna, revisione 2 del 2026-11-15**, dopo la verifica delle fonti primarie di Codex
(prima versione `72cd0c8`; revisione in `MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/reviews/T5_FATTIBILITA_72cd0c8/`).
Non è un protocollo, non congela criteri e non contiene nuove simulazioni o applicazioni ai dati reali.
Usa risultati già salvati (validazione P2f, T5-D2), la letteratura e statistiche descrittive del disegno.

**Non cieca.** Le potenze del §4 erano già note all'autore quando ha scritto i §2–§3.

**Revisione 2 accettata da Codex** come bozza documentale corretta rispetto alla verifica delle fonti (2026-11-15).
Non approva un protocollo e non dimostra la fattibilità di un nuovo T5.

**Esito di questa revisione.** La prima versione concludeva che HMI da solo non può distinguere un
quenching fisicamente interessante e che un nuovo metodo migliorerebbe solo la calibrazione. Questa
conclusione **non è sostenuta** e viene ritirata (§5). Resta sostenuto soltanto: *con le procedure e i
generatori finora esaminati, la potenza per effetti piccoli è bassa; il caso a salti resta poco
discriminante anche con gli SE oracolo. Non è dimostrato un limite generale della serie HMI.*
**La fattibilità resta aperta.**

## 1. Domanda

All'aumentare dell'attività, l'efficienza della sorgente BL per unità di flusso diminuisce abbastanza
da contribuire a limitare il ciclo? Prima di decidere se sviluppare un nuovo metodo T5 servono tre cose:
- un bersaglio fisico definito;
- una mappa giustificata fra effetto fisico e pendenza testata;
- una valutazione di quanto la fattibilità dipenda dalle ipotesi sul rumore.

## 2. Che cosa misura T5, e in quali unità

- **Efficienza.** Per cella (CR, emisfero), η = ΣD*/ΣΦ. D* è il momento dipolare bilanciato al record
  selezionato vicino al meridiano centrale, che non coincide necessariamente con l'emersione.
- **Attività.** Â è il numero di macchie emisferico mensile SILSO diviso per la sua media temporale nella
  finestra HMI (197 mesi, 2010-05…2026-09). Le medie sono N = 33,72, S = 34,57 e totale = 68,29: Â = 1 è
  la media temporale HMI di ciascun emisfero.
- **Modello dell'effetto** nel generatore P2f e T5-D2: η = η̄·[1 + e·(Â_cella − 1)]. L'effetto e è la
  variazione di efficienza, in unità di η̄, per unità di Â.

**Popolazione e pesi.** Non esiste un unico intervallo 5–95 % «del T5».

| Popolazione | q05 | q95 | Note |
|---|---|---|---|
| 2485 record del disegno completo (media di cella per record) | 0,35 | 2,70 | media 1,44, mediana 1,39 |
| 2375 record usati da T5 (≥ 3 record per cella) | 0,50 | 2,76 | |
| 318 celle T5 con peso uniforme | 0,40 | 2,65 | |

La regressione T5 pesa ancora in un altro modo, per flusso. Le righe 2375 e 318 sono state
calcolate da Codex sul disegno ricostruito (`MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/reviews/T5_FATTIBILITA_72cd0c8/verifiche_numeriche.json`);
qui non sono state ricalcolate.

**Traduzione illustrativa**, con la prima popolazione (Â_bassa = 0,35, Â_alta = 2,70, ΔÂ = 2,35). Si
distinguono due quantità:
- la variazione in unità di η̄, cioè e·ΔÂ;
- la perdita relativa all'efficienza ad attività bassa, cioè −e·2,35/(1 − 0,65·e).

| e | Δη/η̄ | Perdita rispetto a η(Â_bassa) |
|---|---|---|
| −0,10 | −23,5 % | 22,1 % |
| −0,20 | −47,0 % | 41,6 % |
| −0,30 | −70,5 % | 59,0 % |
| −0,35 | −82,3 % | 67,0 % |

**Ambito fisico di T5.** T5 non misura il dipolo finale dopo il trasporto. Questo però **non** lo rende
insensibile ai meccanismi citati:
- *Latitudine.* Dalla definizione, D_bal/Φ = [3/(8πR²)]·(⟨sin λ⟩₊ − ⟨sin λ⟩₋), pesati per flusso; per
  una coppia compatta è proporzionale a cos λ·(d/R)·sin α. La latitudine entra quindi già nella geometria
  del dipolo istantaneo. T5 non isola il quenching in latitudine del dipolo finale, ma risente dei
  cambiamenti della distribuzione in latitudine (Jiang 2020, §2).
- *Afflussi.* Martin-Belda & Cameron 2016 (A&A 586, A73, §4.2 e fig. 8) mostrano che gli afflussi
  modificano tilt, flusso e dipolo già nelle prime settimane. I loro effetti possono essere presenti al
  record, senza che T5 li possa identificare o quantificare separatamente.

Il bersaglio fisico va dunque fissato prima di ogni decisione: o il dipolo al record, o il contributo
finale al dipolo polare, che richiederebbe un modello di trasporto.

## 3. Letteratura: risultati pubblicati e conversioni condizionate

Le conversioni in e sono **esercizi condizionati a ipotesi aggiuntive**, non stime pubblicate della
pendenza mensile di T5.

a) **Jiao, Jiang & Wang 2021** (A&A 653, A27; §2.2, §3.4.2, eq. 11, fig. 7). Il risultato pubblicato è
   T = 0,61 − 0,00107·S_n nei cicli 15–24, con S_n il massimo del numero totale mensile lisciato su 13
   mesi. È una relazione **fra cicli**.
   - Conversione condizionata, con tre ipotesi: la relazione vale per l'attività mensile dentro il ciclo;
     η è proporzionale a T; i due emisferi variano insieme, così che S_tot = 68,29·Â. Con queste ipotesi
     e = −0,00107·68,29/(0,61 − 0,00107·68,29) = −0,136.
   - Se varia un solo emisfero con l'altro fisso, dS_tot/dÂ_h ≈ 34 e |e| si dimezza circa.
   - Anche coefficiente di Joy, popolazione e ponderazione differiscono dal T5 basato sul dipolo delle HARP.

b) **Karak & Miesch 2017** (ApJ 847, 69; abstract, eq. 10), riportato da Jiang 2020. Il risultato
   pubblicato è che una soppressione del tilt di 1–2° basta a limitare la crescita della loro dinamo.
   - Nel modello il quenching dipende dal campo toroidale progenitore, non dalla nostra Â mensile, e la
     legge di tilt ha δ0 = 35°.
   - Conversione illustrativa: con il riferimento P2 (24°·sin 15° = 6,21°), 1–2° sono il 16,1–32,2 %;
     distribuiti su ΔÂ = 2,35 danno e ≈ −0,069 … −0,137.
   - La scelta di ΔÂ, della latitudine e del tilt di riferimento **non** è prescritta dal lavoro. Il
     risultato motiva l'interesse per effetti piccoli, ma non fissa una soglia.

c) **Martin-Belda & Cameron 2017** (A&A 597, A21; §3.3, §4.2, fig. 8). Nel caso di riferimento la
   riduzione del dipolo rispetto al caso senza afflussi è circa il 30 %. Il circa 9 % è la variazione, con
   il livello di attività, del **rapporto** fra dipolo con afflussi e dipolo senza afflussi. Non è una
   pendenza per unità di Â né un valore di e per l'efficienza istantanea.

**Conseguenza.** L'intervallo −0,07…−0,2 e un «minimo interessante» −0,10 sono **scelte di
pianificazione** sotto ipotesi di trasferimento, non valori fissati dalla letteratura. Una scelta
definitiva richiede prima il bersaglio fisico (§2) e una mappa giustificata fra effetto fisico e
pendenza testata. La stima storica T5 sui dati reali (circa −0,04) resta esclusa, perché sarebbe circolare.

## 4. Potenza già nota (simulazioni sul disegno HMI, non il Sole)

Frequenza di `supportato` su 2000 cataloghi per combinazione. Il riferimento sotto nulla per un solo
verso è circa 1,25 %.

| e | M, sc. 1 (AR(1) φ = 0,5) | M, sc. 2 (φ = 0,9) | M, sc. 9 (eterosch., t₄, temporale ×2) | M, sc. 7 (salti; M non calibrata) | Oracolo A3, sc. 7 | Oracolo A2, sc. 7 |
|---|---|---|---|---|---|---|
| −0,10 | 11,25 % | 7,8 % | 5,1 % | 8,5 % | 6,6 % | 6,5 % |
| −0,20 | 38,5 % | 26,3 % | 11,6 % | 27,4 % | 22,3 % | 22,0 % |
| −0,30 | 75,1 % | 54,6 % | 30,0 % | 52,7 % | 47,0 % | 47,2 % |
| −0,35 | 86,8 % | 67,7 % | 36,6 % | 64,3 % | 58,6 % | 58,5 % |

Fonti: `results/P2F/VALIDATION_COVERAGE_POWER.csv` (M, test T5) e i riconteggi T5-D2. Le frequenze sono
state ricontrollate da Codex.

Cosa queste potenze **non** sono:
- **Non un limite superiore per HMI.** Gli oracoli A2 e A3 tengono la stessa stima WLS di beta e cambiano
  solo la varianza dell'intervallo, con il riferimento normale; con la varianza vera sono anche
  conservativi. Non è dimostrato che stima e test sfruttino in modo ottimale l'informazione del disegno.
  Un metodo diverso (altra stima, altro peso, altra statistica) potrebbe avere potenza diversa, maggiore
  o minore.
- **Non la potenza sul processo reale.** Valgono per rumore individuale η̄, componente temporale 0,5·η̄ e
  le strutture di dipendenza dei generatori. La scala e la forma reali della componente temporale non
  sono note e incidono direttamente sulla fattibilità.
- **Non una graduatoria generale dei metodi.** I confronti fra generatori diversi non la forniscono.

## 5. Lettura (descrittiva)

**Sostenuto.** Con le procedure e i generatori esaminati:
- a e = −0,10 la potenza è al più di circa l'11 %;
- a e = −0,20 va dal 12 al 39 %;
- nello scenario a salti resta bassa anche con gli SE oracolo (6,6 % e 22 %).

**Non sostenuto, e ritirato dalla versione 1:**
- che HMI sia necessariamente insufficiente;
- che un esito «non deciso» sia quasi certo per ogni valore dell'intervallo;
- che un nuovo metodo migliorerebbe soltanto la calibrazione.

Non è neppure garantito che un metodo nuovo migliori abbastanza. La questione è aperta in entrambi i versi.

## 6. Che cosa servirebbe per decidere

1. **Bersaglio fisico:** dipolo al record oppure contributo finale (§2).
2. **Mappa effetto → pendenza:** una relazione giustificata fra il meccanismo considerato (tilt, latitudine,
   afflussi) e la pendenza e testata, con le ipotesi sugli emisferi e sulla popolazione esplicitate.
3. **Sensibilità della fattibilità al rumore:** potenza in funzione di scala e forma della componente
   temporale in un intervallo plausibile, non in un solo generatore.
4. **Metodi considerati:** valutare anche stime e statistiche diverse da quella WLS attuale, non solo SE
   diversi.
5. **Confronto con una serie estesa, se lo si fa:** includere sempre come riferimento HMI da solo, nelle
   stesse ipotesi e con metodi comparabili. Più cicli e MDI possono aiutare, ma le fonti citate non ne
   dimostrano qui la necessità né il beneficio quantitativo.

Ognuno di questi passi richiederebbe un piano proprio. Uno sviluppo di metodo richiede anche una
validazione finale distinta dai cataloghi già visti. I protocolli congelati P2f e T5-D2 non si modificano.

## 7. Limiti della nota

- Non è cieca.
- Le conversioni del §3 sono condizionate a ipotesi dichiarate.
- Le potenze vengono da generatori con ampiezze e dipendenze fissate.
- Popolazione e pesi cambiano gli intervalli di Â (§2).
- Non sono state calcolate potenze nuove e non è stato interpolato nessun valore.

## 8. Decisione: che cosa si può decidere oggi

- **Non** si può concludere che HMI sia insufficiente, né che MDI sia necessario.
- Rimandare un nuovo T5 per priorità o risorse è legittimo, ma è una **decisione operativa**, distinta da
  un'impossibilità dimostrata.
- Se si vuole proseguire sulla fattibilità, il primo passo è definire bersaglio fisico e mappa
  effetto → pendenza (§6, punti 1–2). Solo dopo ha senso un piano di sensibilità della potenza (punti 3–5),
  con criterio di prosecuzione fissato prima.
- T5 resta descrittivo e T3 non deciso.

# T5 — nota di fattibilità: quale quenching dell'efficienza è interessante, e HMI può distinguerlo?

Stato: **bozza interna del 2026-11-15, per la revisione di Codex.** Non è un protocollo, non congela
criteri e non contiene nuove simulazioni o applicazioni ai dati reali. Usa soltanto risultati già salvati
(validazione P2f, T5-D2) e la letteratura già verificata per il protocollo P2f (§2 di
[PROTOCOL_P2F_VALIDATED_TEST.md](PROTOCOL_P2F_VALIDATED_TEST.md)).

**Non cieca.** Le potenze riportate al §4 erano già note all'autore quando ha scelto l'intervallo
fisicamente interessante del §3. Per questo la scelta è motivata solo con la letteratura e con la
conversione delle unità, mostrata per esteso.

## 1. Domanda

All'aumentare dell'attività, l'efficienza della sorgente BL per unità di flusso diminuisce abbastanza
da contribuire a limitare il ciclo? Prima di sviluppare un nuovo metodo T5 si vuole sapere due cose:
1. quale intensità di quenching dell'efficienza è fisicamente interessante;
2. se i dati HMI, anche con un'inferenza ben calibrata, possono distinguerla.

## 2. Che cosa misura T5, e in quali unità

- **Efficienza.** Per cella (CR, emisfero), η = ΣD*/ΣΦ. D* è il momento dipolare bilanciato misurato
  al record selezionato vicino al meridiano centrale ([misura](HMI_MEASUREMENT_ASSESSMENT.md)).
- **Attività.** Â è il numero di macchie emisferico mensile SILSO diviso per la sua media nella finestra
  HMI 2010-05…2026-09. Le medie sono 33,7 (N) e 34,6 (S); la media del numero totale è 68,3. Una
  unità di Â corrisponde quindi a circa 34 macchie emisferiche, cioè circa 68 del numero totale se i due
  emisferi sono simili.
- **Distribuzione della media di Â per cella**, pesata per record (2485 record del disegno): mediana 1,39,
  quantili 5–95 % pari a 0,35–2,70, deviazione standard 0,72.
- **Modello dell'effetto** nel generatore P2f e T5-D2: η = η̄·[1 + e·(Â_cella − 1)]. L'effetto e è la
  variazione relativa di efficienza per unità di Â.

Traduzione in variazione fra attività bassa e alta, cioè fra il 5° e il 95° percentile (ΔÂ ≈ 2,35):

| e (per unità di Â) | Δη/η̄ fra Â = 0,35 e 2,70 |
|---|---|
| −0,10 | −24 % |
| −0,20 | −47 % |
| −0,30 | −70 % |
| −0,35 | −82 % |

**Ambito fisico di T5.** D* è misurato all'istante del record, quindi T5 è sensibile al quenching che
agisce sul tilt (separazione in latitudine delle polarità) e sulla distribuzione del flusso al momento
della misura. Il quenching in latitudine e gli afflussi verso le regioni attive agiscono soprattutto
attraverso il trasporto successivo e il contributo finale al dipolo polare, che T5 non misura
direttamente. Non sono quindi bersagli diretti di T5.

## 3. Intensità fisicamente interessante (dalla letteratura, convertita in unità T5)

a) **Quenching del tilt osservato fra cicli** (Jiao, Jiang & Wang 2021, eq. 11):
   T = 0,61 − 0,00107·S_n, con S_n il massimo del numero totale lisciato su 13 mesi, cicli 15–24.
   *Ipotesi di trasferimento*: si applica la stessa relazione all'attività mensile dentro il ciclo, e si
   assume η proporzionale al coefficiente di tilt.
   - Una unità di Â vale circa 68 nel numero totale, quindi dT/dÂ ≈ −0,073.
   - Rispetto a T(68) ≈ 0,537 si ottiene **e ≈ −0,14**; alla mediana di Â (S ≈ 95) circa −0,144.
   - Limiti: la relazione è misurata fra cicli e usa il massimo del ciclo, non l'attività mensile; η ∝ T è
     un'approssimazione; si passa dall'attività emisferica a quella totale.

b) **Quanto basta in un modello di dinamo** (Karak & Miesch 2017, citato da Jiang 2020). Una riduzione
   del tilt di 1–2° basta a saturare il ciclo in quel modello. Con il tilt medio di circa 6,2° a 15° del
   modello P2 (24°·sin|λ|) sono il 16–32 %.
   - Distribuita sull'intervallo HMI 5–95 % (ΔÂ ≈ 2,35): **e ≈ −0,07 … −0,14**.
   - Distribuita fra attività nulla e media (ΔÂ ≈ 1,4): e ≈ −0,11 … −0,23.
   - Limiti: viene da un modello specifico, non è una soglia universale, e l'intervallo di attività su cui
     si distribuisce la riduzione è una scelta.

c) **Afflussi** (Martin-Belda & Cameron 2017): riduzione del dipolo di circa il 9 % fra cicli deboli e
   forti. Agisce soprattutto nel trasporto, quindi non è osservabile direttamente in D* (§2). Solo
   contesto.

**Intervallo interessante per T5: circa e = −0,07 … −0,2 per unità di Â**, con valore centrale circa −0,14.
Si propone come **minimo interessante e_min = −0,10**, il limite inferiore dell'effetto sufficiente nel
modello e sotto la conversione di Jiao. È una proposta da discutere, non una soglia fisica. La stima
storica T5 sui dati reali (circa −0,04) **non** entra nella scelta, perché sarebbe circolare.

## 4. Potenza già nota (simulazioni sul disegno HMI, non il Sole)

Frequenza di `supportato` su 2000 cataloghi per combinazione. Il riferimento sotto nulla per un solo
verso è circa 1,25 %.

| e | M, scenario 1 (AR(1) φ = 0,5) | M, scenario 2 (φ = 0,9) | M, scenario 9 (eterosch., t₄, componente temporale ×2) | M, scenario 7 (salti, M non calibrata) | Oracolo A3, scenario 7 | Oracolo A2, scenario 7 |
|---|---|---|---|---|---|---|
| −0,10 | 11,3 % | 7,8 % | 5,1 % | 8,5 % | 6,6 % | 6,5 % |
| −0,20 | 38,5 % | 26,3 % | 11,6 % | 27,4 % | 22,3 % | 22,0 % |
| −0,30 | 75,1 % | 54,6 % | 30,0 % | 52,7 % | 47,0 % | 47,2 % |
| −0,35 | 86,8 % | 67,7 % | 36,6 % | 64,3 % | 58,6 % | 58,5 % |

Fonti: `results/P2F/VALIDATION_COVERAGE_POWER.csv` (M, test T5) e i riconteggi T5-D2
(`results/T5_ORACLE_POSTCHECK/PAIRED_TRANSITIONS.csv`). Nello scenario 7 la potenza di M è gonfiata dalla
sottocopertura. Gli oracoli usano varianze vere, impossibili sui dati reali: un metodo utilizzabile avrà
in genere meno potenza dell'oracolo nello stesso scenario.

## 5. Lettura (descrittiva, provvisoria)

- **Al minimo interessante e = −0,10** la potenza è al più dell'11 % in tutti gli scenari provati. Nello
  scenario a salti è del 6,6 % anche per l'oracolo ideale.
- **Al valore centrale −0,14**, che non è nella griglia simulata, la potenza sta fra quelle di −0,10 e
  −0,20. Non si interpola formalmente.
- **All'estremo alto −0,20** si va dal 12 al 39 %, sempre sotto il 50 %.
- **Valori superiori al 50 %** compaiono solo a −0,30/−0,35, cioè con perdite di efficienza del 70–80 %
  fra attività bassa e alta, sopra l'intervallo del §3.

Conclusione provvisoria: con la sola serie HMI (circa 1,5 cicli, 318 celle) un test T5, anche con
un'incertezza temporale calibrata bene, difficilmente distinguerebbe un quenching dell'efficienza
fisicamente interessante. Un «non deciso» sarebbe l'esito atteso qualunque sia il valore vero
nell'intervallo del §3. Un nuovo metodo T5 migliorerebbe la calibrazione, non la capacità di rispondere
alla domanda.

## 6. Che cosa potrebbe cambiare la conclusione

- **Più cicli.** La componente temporale del generatore (scala 0,5·η̄) è persistente su molte rotazioni
  (AR(1) per CR, oppure blocchi di 20 CR nei salti). La potenza dipende soprattutto dal numero di
  blocchi temporali indipendenti e dall'escursione di attività coperta. Estendere la serie, per
  esempio con MDI/SMARP sul ciclo 23, potrebbe aumentarla, ma il guadagno va stimato **prima**: sulla
  confrontabilità e sul disegno pesa lo [studio di fattibilità](MDI_SMARP_FEASIBILITY.md).
- **Misura migliore.** Ridurre il rumore individuale aiuta poco se domina la componente temporale; anche
  questo va quantificato prima.
- **Componente temporale reale.** La sua scala vera non è nota: con una variabilità reale più piccola di
  quella simulata, la potenza sarebbe più alta. È un'incertezza del quadro, non un argomento per una
  conclusione diversa.

## 7. Limiti della nota

- Non è cieca (§ iniziale).
- Le conversioni del §3 sono approssimate e dipendono da ipotesi di trasferimento dichiarate.
- Le potenze vengono da generatori sul disegno HMI con ampiezze di rumore fissate (individuale η̄,
  temporale 0,5·η̄), non dal processo reale.
- La scelta di e_min è un giudizio.
- Nessuna potenza è stata calcolata ex novo e nessun valore intermedio è stato interpolato.

## 8. Decisione proposta

1. Accettare che HMI da solo non è discriminante per T5 nell'intervallo fisicamente interessante: T5
   resta descrittivo e per ora non si sviluppa un nuovo metodo.
2. Se si vuole perseguire la domanda, il prossimo esperimento è un **calcolo di potenza dedicato per una
   serie estesa** (per esempio HMI + MDI, con disegno e rumore plausibili), con criterio di
   prosecuzione fissato prima e senza acquisire dati. Solo se quel calcolo mostra un guadagno sufficiente
   all'e_min concordato ha senso sviluppare e validare il metodo T5.

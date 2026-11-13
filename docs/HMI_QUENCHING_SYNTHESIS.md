# HMI: risultati sul quenching e prossima domanda utile

2026-11-13. Sintesi di risultati esistenti; nessuna nuova applicazione ai dati reali.
Domanda: all'aumentare dell'attività, la sorgente BL si autolimita attraverso
tilt, latitudine o efficienza per unità di flusso?

## 1. Risultati osservativi

| Domanda | Risultato disponibile | Conclusione consentita |
|---|---|---|
| Il tilt segue la legge di Joy? | Coefficiente complessivo circa 24,1° nel controllo P2 T1 | La relazione media è presente nel campione. Non dimostra quenching. |
| Il coefficiente di Joy diminuisce con l'attività dentro il ciclo? T3 | Procedura M: β̂_T = −3,59° per unità di Â; intervallo nominale 97,5% [−10,58°; +3,41°]; 2485 record primari HARP | **Non deciso.** Nessuno degli effetti negativi della griglia preregistrata è escluso. |
| La latitudine cresce con l'attività, a pari fase? T4 | Pendenza descrittiva −0,63° per unità di Â, verso opposto alla previsione considerata | Nessun verdetto: l'intervallo storico non ha copertura garantita. |
| L'efficienza η = ΣD*/ΣΦ diminuisce con l'attività? T5 | Stima storica circa −0,04·η̄ per unità di Â, incerta; M non supera la validazione sui salti di livello | **Resta descrittivo.** Non è stabilita né la diminuzione né la costanza dell'efficienza. |

T3 misura la pendenza del **coefficiente di Joy**: la variazione del tilt a
latitudine fissa è β_T sin|λ|, circa −0,9° a 15° per la stima puntuale.
L'attività è quella emisferica mensile SILSO normalizzata alla media HMI.
Il risultato riguarda variazioni dentro il ciclo, non una legge universale
tra ampiezze di cicli. Fonti: [P2 storico](P2_RESULTS_DESCRIPTIVE.md),
[T3 P2f](P2F_RESULTS.md).

## 2. Perché questo è un avanzamento, pur senza un verdetto fisico

Le diagnosi A–D hanno esaminato i problemi della procedura P2d/P2e; la successiva
validazione P2f ha separato i due test. T3 supera i criteri nei dodici scenari
nulli e nelle sedici combinazioni sotto effetto provate. T5 fallisce lo scenario
a salti: 3,35% di falsi verdetti contro il limite 3%, e a −0,3 copertura 96,1%
contro 96,5%, con coda inferiore 2,3% contro 2%.

Per T3 è quindi disponibile un risultato osservativo con una procedura che ha
superato i criteri negli scenari provati. L'intervallo comprende zero e gli
effetti negativi della griglia: non dimostra assenza di quenching. La potenza
4,55–11,10% a −0,2·γ0 riguarda i generatori della validazione, non è una misura
della potenza sul processo reale. [Validazione](P2F_VALIDATION_RESULTS.md).

## 3. Sensibilità già fatte: che cosa non occorre ripetere

| Controllo esistente | Informazione già ottenuta | Lacuna residua |
|---|---|---|
| P2f S4: esattamente una NOAA | 1479 record; β̂_T −5,83°, intervallo non validato [−14,45°; +2,80°] | Una NOAA non certifica un bipolo semplice; più NOAA non certificano una misura errata. |
| Altre sette sensibilità P2f | Tutte le stime negative, tutti gli intervalli comprendono zero | Sono correlate e non validate; non costituiscono otto conferme indipendenti. |
| P1e/S8: ricomparse candidate | Quadro di effetti sulle somme e test storici già raccolto | Le associazioni non provano identità fisica; possibile flusso nuovo. Non è una serie «corretta». |
| Primario–controllo | Effetti su somme, flusso e stime già disponibili | Selezione, posizione e evoluzione sono mescolate. |
| HARP dominanti e 30 immagini 25S | Sensibilità della misura e complessità riconosciute in casi influenti | Non misurano l'effetto della morfologia su T3 o sull'efficienza nell'intero campione. |

Fonti: [sensibilità P2f](P2F_RESULTS.md#3-sensibilità-stesse-formule-non-validate-nessun-verdetto),
[ricomparse e record](SENSITIVITY_SUMMARY.md), [dominanti](DOMINANT_HARP_RESULTS.md).

## 4. Due priorità HMI, con scopi distinti

1. **T5: prima diagnosi completata.** [T5-D1](PROTOCOL_T5_DIAGNOSTIC_SAVED_OUTPUTS.md)
   è congelato ed eseguito sugli output sintetici salvati, con 201 controlli
   superati. Nei salti di 20 CR, media(SE²)/varianza empirica vale circa 0,86;
   il bias è piccolo rispetto alla dispersione e la forma delle code conta.
   La componente responsabile non è identificata: [risultati](T5_DIAGNOSTIC_RESULTS.md).
   Dopo revisione, il passo motivato è eventualmente un piano distinto con
   componenti del generatore note. Nessuna correzione o nuova applicazione reale;
   un metodo successivo richiede protocollo e validazione indipendente.
2. **Morfologia: interpretabilità della misura.** Completare, dopo revisione
   e congelamento del piano, le letture delle 90 schede mancanti. Versioni
   prive di diagnostiche numeriche, ordine casuale e seconda lettura indipendente
   di 30 casi; descrizione della sola mappa prima di vedere i centroidi.
   [Bozza revisionata](PROTOCOL_HMI_MORPHOLOGY.md). Una regola operativa
   proposta delimita quando progettare uno studio sulla popolazione S; non
   autorizza un nuovo fit o l'eliminazione di HARP complesse.

La morfologia affronta solo indirettamente il quenching. Un sottocampione
ridurrebbe i dati disponibili, ma la sua potenza non è determinata dal solo
numero di record; non eredita la validazione di T3 su S. La bassa potenza
osservata nei generatori non permette di prevedere con certezza un nuovo
esito reale né di attribuire il limite al solo numero di cicli.

Il risultato T3 e il catalogo P1 restano i riferimenti. MDI/SMARP e la
degradazione HMI verso MDI sono **rinviati, non abbandonati**. L'aggiunta del
ciclo 23 potrebbe ampliare sostanzialmente la serie e l'intervallo di attività;
non garantisce maggiore potenza: confrontabilità strumentale, dipendenza
residua e disegno del test vanno verificati. Non è l'unica via concepibile
(maturazione della serie HMI e possibili miglioramenti della misura o del
metodo), né questi miglioramenti sono già dimostrati. Nessuna prova di
precisione o acquisizione MDI è avviata.

# Revisione Codex — BQ rev.3 e A1 mappa–bipolo, 25 novembre 2026

Oggetti: revisione Claude ce51505 della bozza BQ rev.2 e consegna SFT ccd49f9.
Nessun pixel osservato, nuova misura, fit bayesiano o corsa SFT osservata in questa revisione.
Il controllo presente chiude le scelte documentali qui elencate, **non approva ancora il congelamento o le corse**.
Il selftest completo del riconteggio SFT e la sua versione finale restano da consegnare.

## BQ: risposta agli otto rilievi

1. **Accolto con correzioni:** confronto principale su 10 blocchi interni, buffer 11 e sensibilita 22,
   previsione in avanti secondaria. E interpolazione temporale, non previsione del Sole futuro. Il buffer storico
   non garantisce isolamento sotto la prior corrente: a phi=0,98 la correlazione a 11 CR e ancora 0,801.
   Per ogni fold rimuovere dal training tutti i membri delle famiglie di verifica, anche fuori buffer; non
   traslocare i membri di verifica al blocco del primo familiare. Manifestare supporto dei cicli e rango.
2. **Accolto:** v(t,h)*sin|lat| come sensibilita comune a M0/MQ; prior proprie proposte e prova sintetica con Joy
   dipendente dalla fase senza beta. Non forzare ortogonalita ad attivita per ottenere identificabilita.
   Se il generatore riproduce esattamente il regressore di attivita, i dati non possono distinguere le cause:
   verificare che il sistema riconosca il limite, non chiedere un impossibile recupero garantito.
3. **Accolte due likelihood; modificata L2:** normale e t4 con nu fisso, stessa SD marginale sigma_i,
   scala t = sigma_i/sqrt(2). La prior proposta su nu-1 consentiva nu<=2, quindi varianza infinita.
   La robustezza alle code non risolve il supporto angolare: resta da definire la sensibilita limitata prima
   del congelamento, con il suo bersaglio. Non scegliere L1/L2 in base alla risposta.
4. **Accolta invarianza, rinviata nuova scala comune a BQ-M:** a'=c*a implica beta'=beta/c e Jacobiano.
   Se cambia il centro, anche k cambia e le prior si correlano; non ricreare prior indipendenti nella nuova scala.
   HMI resta nella convenzione P2. Non occorre bloccare HMI per scegliere ora la scala multi-strumento.
5. **Accolto condizionatamente:** Savage-Dickey solo con prior comuni compatibili al vincolo beta=0,
   ordinate con errore numerico e prova su integrali noti. Curva delle prior prescritta, non trasferimento
   incontrollato dello stesso posteriore. Bridge e Savage-Dickey possono condividere errori di campionamento;
   non chiamarli due validazioni completamente indipendenti. Evidenze opzionali se non affidabili.
6. **Accolto come proposta da controllare a priori:** q~N(0,1), sensibilita SD 0,5. Non e una scelta per
   riprodurre la stima storica. Rischio di predizioni estreme da valutare prima del fit reale.
7. **Accolta fattibilita numpy/scipy, non la prestazione promessa:** la dimensione Woodbury include le famiglie;
   un campionatore proprio e bridge richiedono verifiche, warm-up/adattamento separato, Jacobiani e benchmark.
   La formula Woodbury non rende ML/evidenza intercambiabili e non prova convergenza del campionamento.
8. **Accolte SBC e robustezza distinte:** famiglie replicate contro celle CR singleton, generatori avversi con
   numero di realizzazioni e criteri ancora da fissare. Nessun trasferimento automatico della validazione P2f.

La bozza BQ rev.3 incorpora queste risposte. Restano aperti: likelihood angolare, prove a priori, semi effettivi,
regole quantitative delle prove/calcolo e applicabilita del BIC; Claude rivede prima del congelamento operativo.
I conteggi BIC 10/11 valgono per il gaussiano base: con v diventano 13/14, se identificabili. Per L2 non stabilito.

## A1: progressi accettati e due correzioni bloccanti

Accolti: dichiarazione dell'allentamento, criterio preliminare bloccante, proposta di stato numerico separato
per rapporti, conservazione della regione negli altri prodotti. La formulazione attuale del §2ter non e pronta.

**R1 — differenza fra griglie non e errore garantito.** Il requisito |D_2N-D_N| <= epsilon misura uno scarto
fra due approssimazioni. Senza una stima d'errore dimostrata non fornisce |D_esatto-D_N|<=epsilon neppure sui
casi controllati. Delta puntiformi, posizione nelle celle e convergenza oscillante rendono inappropriata
una conversione Richardson non verificata. Sostituire "limite garantito" con indicatore di sensibilita numerica.
Se si vuole una garanzia, occorre un vero stimatore/bound, verificato indipendentemente.

**R2 — propagazione del rapporto:** per r=(B-M)/|M|, se |delta M|<=e_M, |delta B|<=e_B e |M|>e_M,

    |delta r| <= [e_B + e_M (1+|r|)] / (|M|-e_M).

Il denominatore |M| della bozza e solo l'approssimazione al primo ordine. Con B=M=1 ed e_B=e_M=0,005
passa la soglia 0,01, ma B'=1,005 e M'=0,995 danno un cambiamento 0,01005025. Se |M|<=e_M il rapporto e
non risolto; questo stato e distinto dal denominatore sotto 0,1*m(t). Anche dD/D_scale deve usare
(e_B+e_M)/D_scale, senza implicare che i due errori abbiano la stessa scala del dipolo.
Il bound finito e rigoroso **solo condizionatamente** a veri bound e_B/e_M: inserire epsilon da scarto di griglia
lo trasforma in indicatore, non in una garanzia.

**Decisione numerica proposta:** mantenere f=1e-2 come tolleranza assoluta dichiarata di 1e-5 D_scale,
non allargare a 1e-1 per far passare il preflight. E accettabile come criterio di scarto fra griglie se
accompagnato dalla seguente regola, da recepire nel testo/codice prima del congelamento:
- verificare N,2N,4N e passo dimezzato per **ogni rapporto che entrerebbe nei riepiloghi**, a tutte le soglie,
  rappresentazioni, trasporti e tempi. Per contenere il costo si puo riusare il propagatore/aggiunto lineare;
  cio non cambia la regola scientifica. I tre casi osservati restano controlli globali di D, non garanzia universale;
- conservare i D e i rapporti alle risoluzioni, le soglie effettive e gli indicatori. Quantili dei rapporti
  solo con classificazione di ammissibilita stabile fra le griglie e scarti di rapporto <=0,01 per entrambi
  i raffinamenti successivi e per il passo. Non utilizzare 0,01 come errore assoluto rispetto alla soluzione esatta;
- m(t), soglia e cambi di eleggibilita ricalcolati a ogni griglia con la **stessa popolazione/definizione**;
  nessuna nuova selezione sul dipolo per abbassare l'indicatore. Se i denominatori o la soglia cambiano lo stato,
  segnalare come non risolto. Nessuna rimozione della regione da D o dD_scaled per questo solo motivo;
- distinguere n_below_ratio_threshold, n_ratio_unresolved e n_ratio_resolved; riportare quote anche pesate.
  Non omettere le mancate risoluzioni dai denominatori di selezione;
- la concordanza dei segni puo essere non risolta vicino a zero: segnalarla separatamente, senza presentare
  il semplice segno a griglia unica come robusto;
- se anche con questa procedura i rapporti non sono risolti, conservarli come diagnostici ed escluderli
  dai quantili; nessun obbligo di avere un quantile per ogni cella. D e dD_scaled restano descrittivi con gli
  indicatori numerici dichiarati. Non scegliere f usando i risultati osservati.

La regola e una proposta di revisione del protocollo, non un emendamento gia congelato. Il controllo di
convergenza globale previsto da A1 resta bloccante; l'irrisoluzione di singoli rapporti e uno stato distinto.
Non e autorizzata una corsa perche un test passa: prima testo aggiornato, implementazione e riconteggio rivisti.

## Controlli effettuati e limiti

`reviews/BQ_A1_CROSS_REVIEW_20261125/MATH_CHECKS.json`: sei controlli deterministici algebrici, tutti positivi:
controesempio al rapporto, bound finito su perturbazioni di entrambi i segni, correlazione a 11 CR,
scala t4 e trasformazione affine dell'attivita. Nessun dato osservato o RNG.

Ho letto testo A1 e sezioni preflight/convergence/summarise di ccd49f9; non dichiaro un audit integrale del nuovo
riconteggio o tutti i cinque gruppi chiusi finche non arriva il suo selftest concluso e il codice definitivo.
La regola ratio_numerically_unresolved e ancora assente nel codice, coerentemente con la consegna di Claude.

Riferimenti primari: Roberts et al. (2017), https://doi.org/10.1111/ecog.02881 (abstract nella pagina autore:
https://florianhartig.github.io/publications/roberts2017cross/); Mulder et al.,
https://arxiv.org/abs/2004.09899; Gronau et al., https://arxiv.org/abs/1703.05984.
La proposta numerica A1 e una derivazione/procedura di questa revisione, non una garanzia tratta dalle fonti.

BQ-HMI prioritario; C attivo in parallelo; BQ-M successivo. Nests ancora sospesi. SINDy separato.

# Q1, Q2 e Q3 su HMI: stime descrittive

Protocollo: `docs/PROTOCOL_HMI_FOLLOWUPS.md` (SHA-256 `316fa968…`). La validazione di Q1 e Q2 non è superata
(`docs/HMI_FOLLOWUPS_VALIDATION_RESULTS.md`); Q3 è descrittivo per protocollo. Tutte le stime sono quindi
**descrittive**: intervalli nominali al 97,5 % della procedura M, senza verdetto.

- Stima eseguita il 20 novembre con il via dell'utente e di Codex.
- Output conservati prima della lettura (`9dc41ad`, `results/HMI_FOLLOWUPS/`).
- Riconteggio indipendente 19/19 (`a72ce2d`, `results/HMI_FOLLOWUPS_RECOUNT/`):
  - ogni stima ricalcolata (scarto relativo 6,7·10⁻¹³);
  - SE ricalcolati dai parametri di M (2,9·10⁻¹³);
  - la stima usa la validazione conservata.

Campione S di P1: 2485 regioni, 2010-05 → 2026-09.

| Analisi | n | Stima | SE | Intervallo nominale 97,5 % |
|---|---|---|---|---|
| Q1: k₂₅ − k₂₄ (finestra di T2) | 2238 | +3,27° | 4,31 | [−6,40; +12,94] |
| Q1 finestra simmetrica | 2187 | +3,18° | 6,68 | [−11,80; +18,15] |
| Q1 media dei due emisferi | 2238 | +3,24° | 4,45 | [−6,72; +13,21] |
| Q2: β₄ con fase emisferica (principale) | 2485 | −0,68° per unità di attività | 0,39 | [−1,56; +0,20] |
| Q2 con fase convenzionale (T4 storico) | 2485 | −0,63° | 0,38 | [−1,49; +0,23] |
| Q3: b, Joy contro log₁₀Φ (per decade di flusso) | 2485 | +9,53° | 4,86 | [−1,36; +20,42] |
| Q3 quintile 2 − quintile 1 di Φ | 2485 | −1,05° | 6,13 | [−14,79; +12,68] |
| Q3 quintile 3 − 1 | 2485 | +5,95° | 5,86 | [−7,19; +19,09] |
| Q3 quintile 4 − 1 | 2485 | +1,71° | 5,75 | [−11,18; +14,60] |
| Q3 quintile 5 − 1 | 2485 | +12,31° | 5,58 | [−0,20; +24,82] |

## Lettura descrittiva e limiti

- **Q1.** La stima centrale del coefficiente di Joy del ciclo 25 è 3,3° sopra quella del ciclo 24.
  L'intervallo nominale include la riduzione di circa −2,3° usata come riferimento nel protocollo,
  lo zero e valori positivi. Questa analisi non individua una differenza di segno determinato.
  L'intervallo di M è più largo di quello di P2, ma anche i livelli nominali differiscono:
  97,5 % qui e 95 % nel bootstrap precedente. La differenza di ampiezza non va attribuita interamente al metodo.
- **Q2.** Sostituire la fase convenzionale con quella emisferica in questo modello non rimuove
  la stima centrale negativa: −0,68° contro −0,63°. Non trova quindi appoggio l'ipotesi specifica
  che questa sostituzione basti a spiegare il segno di T4. Il confronto non identifica la causa
  del segno e non esclude ogni possibile ruolo dello sfasamento emisferico.
  L'intervallo nominale [−1,56°; +0,20°] include zero. Poiché la procedura non ha superato la
  validazione di Q2, +0,20° non è un limite superiore fisico validato: non si può concludere
  che il quenching di latitudine abbia poco spazio o escluderne quantitativamente ampiezze.
- **Q3.** Le stime centrali sono positive: +9,53° per decade di flusso e +12,31° per il contrasto
  quintile 5 meno quintile 1. L'andamento dei quintili non è monotono. Tutti gli intervalli
  nominali riportati, compresi quello della pendenza e quello del contrasto estremo, includono zero.
  Non sono quindi una dimostrazione di crescita del coefficiente di Joy né un'esclusione di
  un quenching locale. Flusso, latitudine, fase, attività e complessità delle regioni possono
  contribuire all'associazione osservata; il termine di attività incluso non risolve da solo
  ogni problema di interpretazione causale.

Il confronto con il lavoro di Jha et al. citato nel protocollo rimane soltanto qualitativo:
quell'analisi usa il campo massimo, questa il flusso. Qui non si misura una soglia in kG e non
si verifica la diminuzione del coefficiente oltre una soglia di campo massimo.

## Che cosa si aggiunge

1. La stima negativa di Q2 persiste con entrambe le definizioni della fase nel modello studiato.
2. Gli intervalli nominali attuali includono zero per Q1, Q2 e tutti i contrasti Q3 riportati.
3. Le stime centrali Q3 vanno nel verso di un coefficiente di Joy maggiore nelle regioni con più
   flusso, con andamento non monotono e ampia incertezza nominale.

Nessuna delle tre analisi dà un verdetto sulla presenza o sull'assenza del quenching. Questi
risultati restano descrittivi e non sostituiscono la validazione o i controlli strumentali di MWO.

## Revisione di Codex del 20 novembre

Confermati gli hash dei prodotti e il legame alla validazione. Ricostruite nuovamente le dieci stime
con le righe QR del riconteggio indipendente e i dieci SE dai parametri salvati: scarti entro 7e-13
relativi. Corretta la formulazione delle conclusioni senza cambiare numeri, intervalli o soglie.
Il riconteggio 19/19 di a72ce2d resta conservato e invariato.

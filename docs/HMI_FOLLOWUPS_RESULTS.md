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

## Lettura (descrittiva, nessun verdetto)

- **Q1.** Il coefficiente di Joy del ciclo 25 è stimato 3,3° più alto di quello del ciclo 24, come la stima descrittiva di
  T2 in P2. L'intervallo di M è più largo del bootstrap di P2 ([−4,1; 10,1]). La riduzione attesa dalla relazione di
  Jiao et al. (circa −2,3°) cade dentro l'intervallo, come lo zero e valori positivi: HMI non distingue fra i due cicli.
- **Q2.** Con la fase emisferica la stima è −0,68°, praticamente uguale a quella con la fase convenzionale (−0,63°).
  **Lo sfasamento fra emisferi non spiega il segno negativo di T4**: l'ipotesi registrata nel protocollo non trova
  appoggio in questi dati. Con l'intervallo di M lo zero è compreso, mentre il bootstrap di P2 lo escludeva. Una
  crescita della latitudine con l'attività oltre circa +0,2° per unità, il verso del quenching di latitudine, è fuori
  dall'intervallo nominale. Questa lettura non è validata: Q2 ha fallito di poco nello scenario a gradini.
- **Q3.** Il coefficiente di Joy tende a **crescere** con il flusso della regione, non a calare:
  - +9,5° per decade di Φ;
  - le regioni del quintile più alto hanno un coefficiente circa 12° più grande di quelle del quintile più basso,
    circa la metà di γ₀;
  - il segno è opposto a un quenching locale; l'andamento per quintili non è monotono (quintile 2 −1,1°, quintile 4
    +1,7°).

  È coerente con la crescita della pendenza di Joy con il campo riportata da Jha et al. Nel campione S non si vede la
  diminuzione oltre 2–2,5 kG che descrivono, ma qui la variabile è il flusso, non il campo massimo, quindi il confronto
  è solo qualitativo. Φ è correlato con latitudine, fase e attività, e le regioni grandi complesse hanno tilt di HARP
  meno netti (limiti del §3 del protocollo): l'associazione è descrittiva.

## Che cosa cambia

Nessuna delle tre analisi dà un verdetto sul quenching. Si aggiungono tre informazioni:
1. lo sfasamento emisferico non spiega T4;
2. sulla latitudine il verso del quenching ha poco spazio nell'intervallo nominale;
3. su HMI non compare un quenching locale del tilt con il flusso della regione; semmai il contrario.

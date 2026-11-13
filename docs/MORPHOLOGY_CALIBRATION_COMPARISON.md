# Taratura morfologica: confronto dei due lettori

Registrato il 2026-11-13 dopo il blocco di entrambe le tarature (lettore 1: `15eaf3e`, SHA-256
`a851aadd…`; lettore 2: `92428fa`, SHA-256 `51f67b69…`). Gli hash dei file privati sono stati
ricontrollati prima del confronto e coincidono con gli impegni pubblicati. I file originali restano
privati e invariati fino al blocco delle letture delle 90; questo documento riporta le sole classi
della taratura (schede di riferimento di 25S, fuori dalla nuova verifica).

| Codice | Classe storica | Lettore 1 (Opus 5.5) | Lettore 2 (GPT-6.1 Sol) |
|---|---|---|---|
| R01 | A | A (alternativa debole B) | A |
| R02 | A | A | A |
| R03 | A | A | A |
| R04 | A | A (alternativa debole B) | A |
| R05 | D (quasi unipolare) | D | D |
| R06 | B | B | B |
| R07 | B | B | B |
| R08 | B | B | B |
| R09 | B | B | B |
| R10 | A | A | A |
| R11 | D (frammentata) | **U: B o D** | **U: B o D** |

**Accordo esatto 11/11** sulla classe primaria. I due lettori non sono ciechi al progetto né alle classi
storiche (visibili in `REFERENCE_SHEETS.csv`); l'accordo su schede di taratura note non misura la
riproducibilità sulle 90 nuove.

**Punto aperto, comune ai due lettori.** R11 (quattro isole di maschera di sola plage, gruppi
riconoscibili, nessuna macchia) cade tra la regola B («una polarità forma due o più gruppi separati
chiaramente comparabili») e la regola D («solo plage frammentata senza gruppi riconoscibili»). Entrambi
l'hanno classificato U, come prevede la regola 4. Il protocollo prevede che, se la taratura mostra
un'ambiguità di regola, la si risolva con un emendamento **prima** delle 90 letture. Opzioni (da
decidere, nessuna applicata):
1. **Lasciare le regole invariate**: le configurazioni di questo tipo diventano U. Rischio: se sono
   frequenti tra i controlli, il limite operativo di 3 U su 30 per lettore può essere superato.
2. **Emendamento che assegna a B** le configurazioni con gruppi separati riconoscibili anche se di sola
   plage, riservando D a quasi unipolare e plage diffusa senza gruppi riconoscibili. Coerente con la
   domanda (l'asse a due centroidi non rappresenta un solo bipolo), ma aumenta la quota di B che entra
   nella regola per lo studio successivo.
3. **Emendamento che assegna a D** le configurazioni di sola plage frammentata in più isole senza
   macchie, riservando B a sistemi con concentrazioni forti. Più conservativo per la regola del 10 %.

## Decisione registrata (emendamento A2)

Scelta l'opzione 2, motivata dall'organizzazione del campo e non dalle conseguenze sui risultati
(`docs/PROTOCOL_HMI_MORPHOLOGY_A2.md`). Le classificazioni originali restano invariate; la colonna
seguente riporta la classe secondo la regola emendata, decisa in comune dopo il confronto.

| Codice | Lettore 1 (originale) | Lettore 2 (originale) | Secondo A2 (decisione comune) |
|---|---|---|---|
| R11 | U: B o D | U: B o D | B |

Le altre dieci schede non cambiano con A2 (A resta A, B resta B, D quasi unipolare resta D).

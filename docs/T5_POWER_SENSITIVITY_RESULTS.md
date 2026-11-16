# T5 — sensibilità della potenza: risultati

**2026-11-16. Descrittivo, non cieco.** Piano `docs/T5_POWER_SENSITIVITY_PLAN.md` (`4b67632`), emendamenti A1
(`8dc6d48`) e A2 (`6024237`). Esecuzione unica sul commit `44633cb`, script `f19cf15` (SHA-256 `62ca2da4…`),
avviata alle 10:38 e finita alle 13:31: esito «eseguita», 9000 cataloghi di rumore, 180 000 risposte, 0 errori
tecnici, 0 casi di confine. Output conservati prima della lettura in `0a6853a`. Controllo indipendente e
riconteggio (`scripts/t5_power_check.py`, `b12abdb`, ricevuta `2fb9bd5`): **30/30 superati**. Non è una
validazione: nessuna procedura è validata, nulla è applicato ai dati reali, T5 resta descrittivo.

Tutte le frequenze valgono **per questi generatori e questo disegno HMI** (318 celle, 2375 record), non per il
Sole. Denominatore: 1000 tentativi per configurazione e metodo, errori inclusi. Incertezza Monte Carlo (§4 del
piano): al 2,5 % MCSE circa 0,5 punti (semilarghezza al 95 % circa 1 punto), al 50 % circa 1,6 punti. Livello
nominale dei falsi verdetti: 2,5 % in totale, 1,25 % per verso. Bersagli: L1/S1 Δβ = −0,0515·η̄ (riduzione
prescritta del 10 %), L2/S2 Δβ = −0,1031·η̄ (20 %).

## 1. Controlli e errori

- Identità di A1 ricalcolate: β̂_WLS(segnale) − β̂_WLS(N) = Δβ e β̂_WLS(L) = β̂_WLS(S) entro τ_β in tutte le
  9000 unità (deviazione massima 0,0065 τ_β); SE di O identico fra i cinque segnali; nessun caso di confine.
- Errori previsti: 28 di M (e quindi 28 di G) su 45 000 risposte (0,06 %), in 5 configurazioni; B e O mai.
- B usa sempre 16 cluster di 13 CR.

## 2. Falsi verdetti sotto nulla (segnale N, su 1000)

Totale (supportato / opposto):

| Rumore | M | G | B | O |
|---|---|---|---|---|
| ar1_05 × 0,5 | 33 (12/21) | 39 (13/26) | 44 (20/24) | 26 (9/17) |
| ar1_05 × 1 | 27 (14/13) | 30 (11/19) | 37 (18/19) | 29 (17/12) |
| ar1_05 × 2 | 24 (19/5) | 30 (20/10) | 37 (19/18) | 19 (13/6) |
| ar1_09 × 0,5 | 27 (11/16) | 54 (24/30) | 66 (36/30) | 26 (10/16) |
| ar1_09 × 1 | 39 (20/19) | 37 (19/18) | 80 (36/44) | 32 (17/15) |
| ar1_09 × 2 | 27 (13/14) | 32 (14/18) | 86 (42/44) | 26 (14/12) |
| steps20 × 0,5 | 29 (16/13) | 35 (17/18) | 57 (30/27) | 17 (11/6) |
| steps20 × 1 | 28 (13/15) | 34 (19/15) | 93 (43/50) | 14 (7/7) |
| steps20 × 2 | 40 (18/22) | 22 (9/13) | 122 (57/65) | 13 (5/8) |

R = media(SE²)/var(β̂) sotto nulla: M 0,77–1,09 (0,77 solo in steps20 × 2), G 0,81–1,02, O 0,93–1,08.
Copertura del bersaglio su tutti i segnali: M 95,8–97,6 %, G 94,4–97,7 %, O 96,8–98,7 %. Lettura: M resta vicino al nominale in otto
configurazioni su nove (2,4–3,9 %); con i salti alla scala doppia, non provata in P2f, SE sottostimato (R 0,77) e
4,0 % di falsi. B eccede il nominale con rumore persistente o a salti (5,7–12,2 %): i suoi verdetti non sono
calibrati in queste condizioni. G eccede in ar1_09 × 0,5 (5,4 %, R 0,81). O è conservativo nei salti (1,3–1,7 %).

## 3. Riconoscimento della riduzione prescritta (`supportato`, su 1000)

L1 S1 | L2 S2 per metodo:

| Rumore | M | G | B | O |
|---|---|---|---|---|
| ar1_05 × 0,5 | 64 64 \| 191 187 | 115 95 \| 370 294 | 93 87 \| 256 243 | 58 58 \| 186 186 |
| ar1_05 × 1 | 49 49 \| 114 114 | 70 62 \| 211 161 | 63 63 \| 154 150 | 48 48 \| 105 105 |
| ar1_05 × 2 | 28 28 \| 41 41 | 47 40 \| 93 73 | 42 39 \| 75 75 | 27 27 \| 45 45 |
| ar1_09 × 0,5 | 70 68 \| 181 179 | 117 100 \| 343 282 | 98 97 \| 255 237 | 64 64 \| 174 174 |
| ar1_09 × 1 | 43 43 \| 82 82 | 87 75 \| 191 165 | 80 77 \| 143 141 | 33 33 \| 66 66 |
| ar1_09 × 2 | 20 20 \| 39 39 | 36 33 \| 91 67 | 66 66 \| 93 94 | 19 19 \| 30 30 |
| steps20 × 0,5 | 73 74 \| 192 193 | 113 93 \| 342 286 | 103 98 \| 256 242 | 57 57 \| 157 157 |
| steps20 × 1 | 35 37 \| 88 88 | 78 71 \| 208 178 | 86 84 \| 149 143 | 25 25 \| 61 61 |
| steps20 × 2 | 35 35 \| 55 55 | 39 32 \| 117 95 | 88 87 \| 124 122 | 14 14 \| 33 33 |

## 4. Lettura prevista (§5 del piano)

1. **Forma del segnale.** A pendenza proiettata uguale, la forma prodotta dallo scenario del proxy non cambia la
   frequenza di `supportato` di M (differenze appaiate S − L fra −4 e +2 per 1000, errore ≤ 2,8) né di O (zero
   esatto, come richiesto da A1). Per B le differenze sono piccole e negative (fino a −18 per 1000, errore 5,3).
   Per G sono negative e crescenti con l'ampiezza (S1 − L1 fino a −20, S2 − L2 fino a −76 per 1000): G stima una
   pendenza GLS diversa dalla proiezione WLS, e per i segnali S la sua media si sposta verso zero (bias fino a
   +0,017·η̄, cioè circa il 16 % di |Δβ| per S2), mentre per L il bias è quello già presente sotto nulla
   (|bias| ≤ 0,0044·η̄). La parte del segnale fuori dal modello (rapporto delle RMS 0,55) non riduce la potenza
   di M; influisce su G attraverso la sua diversa pesatura.
2. **Rumore.** La frequenza di `supportato` dipende soprattutto dalla **scala** della componente temporale. Con
   M e la riduzione del 20 %: 18–19 % alla scala 0,5, 8–11 % alla scala P2f, 4–5,5 % alla scala doppia; con la
   riduzione del 10 % al massimo 7,4 %. La forma del rumore conta meno della scala, a parità di scala.
3. **Metodo.** Potenza e falsi verdetti vanno letti insieme e **non si dichiara un metodo migliore** (§5.3):
   G e B riconoscono più spesso, ma con falsi verdetti più alti in diverse configurazioni (B fino al 12,2 %),
   R < 1 per G in alcune, e per G con bersaglio spostato nei segnali S. O, a varianza nota, non riconosce più
   spesso di M (differenze appaiate O − M fra +4 e −36 per 1000, negative soprattutto nei salti dove O è
   conservativo). Conoscere la varianza vera non aumenta la potenza.
4. **Vincolo di lettura.** In queste condizioni la riduzione del 20 % è riconosciuta da M al più circa 190 volte
   su 1000, con circa 30 falsi verdetti su 1000 sotto nulla; alla scala P2f circa 80–115 volte. Non dimostra un
   limite di HMI: altri stimatori o altre statistiche non sono esplorati, e O non è un tetto della potenza.

## 5. Lettura aggiuntiva, non prevista dal piano

Il rapporto fra il bersaglio |Δβ| e la deviazione standard di β̂_WLS sotto nulla vale 0,19–0,71 per la
riduzione del 10 % e 0,38–1,42 per quella del 20 %. Con il riferimento normale a un verso (1,25 %), questo
rapporto prevede una potenza di 2,0–6,3 % e 3,1–20,7 %; la frequenza osservata con O è 1,4–6,4 % e 3,0–18,6 %.
La potenza bassa è quindi coerente con l'**informazione contenuta nel disegno** sotto questi rumori, non con un
difetto della stima della varianza. È un controllo di coerenza a posteriori, non una regola né una stima di
quanta informazione aggiuntiva servirebbe.

## 6. Esiti da valutare con Codex (§5 del piano)

Il piano prevede tre esiti, da scegliere esplicitamente: (i) un metodo o una direzione merita un protocollo di
sviluppo e validazione con semi nuovi; (ii) rinvio di T5 per priorità, con i limiti espliciti; (iii) esito non
conclusivo. Elementi per la discussione, senza decisione qui:
- nessun metodo provato offre più potenza **a falsi verdetti nominali**; M è il solo vicino al nominale quasi
  ovunque, e O mostra che la varianza nota non cambierebbe il quadro;
- la forma dello scenario non è un ostacolo per M;
- l'informazione del disegno HMI sotto questi rumori è il limite principale: un aumento della potenza richiede
  più informazione (per esempio una serie più lunga) o una statistica diversa, da pianificare a parte;
- l'estensione MDI resta da valutare con il suo inventario e una stima prospettica propria; questi risultati
  non ne stimano il beneficio.

Output: `results/T5_POWER_SENSITIVITY/` (RAW, SUMMARY, PAIRED_LS, PAIRED_METHODS, IDENTITY_DIAGNOSTICS,
UNIT_TIMES, META); controllo `results/T5_POWER_SENSITIVITY_CHECK/b12abdb5dc52/`. Nessun push.

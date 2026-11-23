# Pilota MDI, livello 1 (mappe sinottiche) — esiti descrittivi Q1 e Q3

24 novembre 2026 (Claude). Protocollo congelato `docs/PROTOCOL_MDI_TILT_PILOT.md` (SHA `77367350…`).

## Catena

| Passo | Commit | Controllo |
|---|---|---|
| Selezione | `b605fd5` | riconteggio 6/6 (`495c32d`) |
| Misura L1 | `ec859e8` | riconteggio 6/6, 530/530 record (`4906974`) |
| Analisi Q1/Q3, codice approvato da Codex | `85c1e2c` | — |
| Corsa dell'analisi | `eda3515` | riconteggio 13/13, partial false (`ba71036`) |

## Stato e lettura

- **Descrittivo.** Gli intervalli sono bootstrap a blocchi di 6 rotazioni (seme 71 100 001), nominali e **non
  validati**.
- I gruppi di Q3 sono correlati fra loro e numerosi: qualche intervallo che esclude zero è atteso anche senza un
  effetto.
- Q3 misura **differenze relative MDI(sinottica) − MWO**: non dice quale strumento introduca lo scarto e, da sola,
  non autorizza una serie combinata per la sorgente BL.
- Le mappe sinottiche sono compositi: l'istante per pixel è indeterminato. La distanza riportata è MWO − t_DPD
  (mediana 7,0 h).
- **Restano da fare:**
  - Q2 (sinottica contro full-disk) e la ripetibilità, che richiedono il livello 2;
  - Q4, rinviato;
  - BARD-MDI, rinviato perché non c'è una regola di corrispondenza.

## Q1 — resa, copertura, dispersione (serve a entrambi gli obiettivi)

Denominatore: tutti i 530 gruppi del campione. La resa proiettata sulla popolazione eleggibile (5401 gruppi) usa i
pesi di selezione 1/π₁.

| Gruppo | Resa del campione, 50 G | Resa proiettata, 50 G | Resa proiettata, 100 G |
|---|---|---|---|
| tutti | 498/530 (94,0 %) | 92,8 % | 81,7 % |
| attività 1 / 2 / 3 | 92,0 / 94,4 / 95,5 % | 89,9 / 94,3 / 94,2 % | 72,7 / 85,2 / 87,1 % |
| area 1 / 2 / 3 | 90,6 / 92,8 / 98,3 % | 87,4 / 91,7 / 98,6 % | 72,8 / 75,2 / 96,7 % |
| emisfero N / S | 91,3 / 96,6 % | 89,8 / 95,5 % | 79,3 / 83,8 % |
| coorte M1 / U | 96,5 / 91,5 % | 98,3 / 90,9 % | 98,3 / 75,9 % |

- **Fallimenti alla soglia principale (32):**
  - finestra con pixel mancanti 12;
  - rotazione mancante (1998) 8;
  - meno di 10 pixel per polarità 6;
  - una sola polarità 6.
- **La resa cresce con area e attività.** I gruppi con un record MWO nello stesso giorno (M1) riescono più spesso:
  la loro selezione MWO favorisce regioni misurabili.
- **Dispersione osservata del campo** (MAD scalata nelle finestre di quiete; non è rumore strumentale):
  - lati validi 331 su 1060, gli altri scartati quasi sempre per la presenza di gruppi DPD;
  - 260 gruppi con un valore: mediana 6,1 G (10° percentile 5,0, 90° 8,6).
- **Fit esplorativo di M** su γ (498 misure, 222 celle, 145 rotazioni):
  - φ = 0,29, κ = −0,98 al bordo, σ²ₓ = 16,7, stato «stimato», nel dominio;
  - poco informativo per costruzione: non è una misura della correlazione fra rotazioni e non va usato da solo per Q4.

## Q3 — MDI sinottica − MWO, stesso gruppo e giorno (coorte M1)

Confini di separazione fissati dalle misure L1 principali: 3,97° e 5,94°.

| Gruppo | n | mediana d_ax | mediana d_γ | accordo leading | rapporto di flusso MDI/MWO |
|---|---|---|---|---|---|
| tutti (50 G) | 251 | +1,2° [−1,0, +3,1] | +0,2° [−2,0, +2,4] | 92,4 % [90,1, 94,8] | 13,7 |
| tutti (100 G) | 250 | +0,7° [−1,2, +1,7] | −0,2° [−1,5, +1,7] | 92,8 % | 11,0 |
| attività 1 | 79 | +1,8° | +0,8° [−3,3, +5,0] | 97,5 % | 11,8 |
| attività 2 | 86 | −0,7° | +2,0° [−0,7, +3,5] | 91,9 % | 14,0 |
| attività 3 | 86 | +2,9° | −1,7° [−5,8, −0,3] | 88,4 % | 13,7 |
| area 1 / 2 / 3 | 76 / 86 / 89 | +0,3 / +0,5 / +1,8° | −0,6 / −0,8 / +1,2° | 88,2 / 89,5 / 98,9 % | 20,8 / 19,1 / 7,3 |
| separazione 1 / 2 / 3 | 75 / 94 / 82 | +3,8 / +3,3 / −0,3° | +1,5 / 0,0 / +0,3° | 82,7 / 96,8 / 96,3 % | 14,2 / 11,9 / 15,7 |
| emisfero N / S | 122 / 129 | +1,7 / +1,1° | +1,7 / −1,1° | 90,2 / 94,6 % | 14,1 / 13,5 |

Fra parentesi gli intervalli bootstrap al 95 %, non validati.

- **Complessivamente** le mediane delle differenze di tilt sono vicine a zero e gli intervalli lo contengono.
  - La dispersione per coppia è grande: mediana di |d_ax| 8,5°, e il 7,2 % delle coppie supera 45°.
  - La polarità leading concorda nel 92 % dei casi.
- **Per attività**, d_γ non varia in modo monotono:
  - nel terzile più attivo l'intervallo esclude zero, alla soglia principale (−1,7° [−5,8, −0,3]) e a 100 G
    (−1,7° [−6,2, −0,3]);
  - nel terzile intermedio, a 100 G, l'intervallo è positivo (+1,5° [+0,7, +3,3]).
  - È il tipo di differenza strumentale legata all'attività che interessa T3, ma qui è descrittiva, con molti
    confronti correlati e intervalli non validati: non indica quale dei due strumenti dipenda dall'attività.
- **L'accordo della polarità leading cala** con l'attività (97,5 → 88,4 %) e per separazioni piccole (82,7 %).
- **Il rapporto di flusso MDI/MWO è circa 7–21.**
  - Nasce da soglie, risoluzioni e prodotti diversi: la sinottica è media e composita, la finestra MWO è a 50 G
    alla sua risoluzione.
  - È più alto per le regioni piccole.
  - Va letto come differenza di misura, non come calibrazione.
- **Non calcolabili:** i rapporti di pixel e aree con MWO, perché il rilascio MWO non li contiene.

## Cosa dice per i due obiettivi

- **Quenching (T3):**
  - MDI sinottico misura il 93 % della popolazione eleggibile del ciclo 23. Q4 dirà quale precisione ne deriverebbe.
  - Il confronto con MWO mostra scarti relativi che, in parte, cambiano con l'attività. Servono Q2 e il livello 2
    per capire quanto dipenda dal prodotto sinottico.
- **Sorgente BL:**
  - flussi, separazioni e polarità sono misurati per quasi tutti i gruppi;
  - la grande differenza di scala del flusso fra MDI sinottico e MWO esclude un'unione diretta delle due serie
    senza una specifica propria.

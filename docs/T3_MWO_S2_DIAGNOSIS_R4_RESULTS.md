# T3 su MWO R4 — diagnosi descrittiva di S2: esiti

23 novembre 2026 (Claude). Nota congelata `docs/T3_MWO_S2_DIAGNOSIS_NOTE.md` (SHA `dd0c035d…`), approvata da Codex
in `ed8f2f3`.

## Catena

| Passo | Commit | Esito |
|---|---|---|
| Tentativo 1 da `ed8f2f3` | — | rifiutato dalla propria guardia, nessun prodotto scritto; log in `results/T3_MWO_S2_DIAGNOSIS_R4_ATTEMPT1_REFUSED` |
| Correzione della lettura | `d606806` | lettura `round_trip` di WL_TILTS e del rilascio, in runner e riconteggio; selftest 33/33 e 22/22 |
| Corsa da `d606806` | `99f6134` | uscita 0, tutte le guardie superate; output conservati prima della lettura |
| Riconteggio indipendente | `99ca913` | 19/19, partial false, legato al META |

**Il tentativo 1.** La guardia congelata («`s2_fit` sul sottoinsieme ricostruito riproduce STABILITY.json entro
1e-9») ha fermato la corsa:
- β era identico, ma SE differiva di 1,7e-5.
- Il lettore predefinito di pandas e quello `round_trip` danno differenze massime di 7,1·10⁻¹⁵ su d_WL e γ_WL.
  Codex ha verificato che `round_trip` coincide con la conversione `float` dei valori testuali conservati.
- Su questo sottoinsieme la piccola differenza nella risposta cambia i parametri di covarianza stimati da M:
  SE cambia di −1,704·10⁻⁵, mentre β è identico. Con `round_trip` tutti i nove campi numerici del fit S2
  riproducono esattamente STABILITY.json. È una sensibilità numerica osservata; la curvatura dell'ottimo REML
  non è stata caratterizzata da questa verifica.

Regole, tolleranze e nota sono invariate. La correzione, successiva all'approvazione iniziale, è stata rivista
da Codex insieme agli esiti: `docs/T3_MWO_S2_DIAGNOSIS_RESULTS_CODEX_REVIEW.md`.

## Stato

**Diagnosi descrittiva, successiva alla lettura.**
- Gli intervalli dei sottoinsiemi e delle componenti sono nominali e **non validati**.
- I 19 fit sono correlati fra loro e lo stimando cambia con il sottoinsieme. Δβ/SE_S2 è una scala, non un test.
- Sono molti confronti correlati e gli intervalli non sono validati: una singola esclusione di zero non è
  evidenza confermativa di un effetto nel gruppo.
- Nessuna classificazione e nessuna attribuzione causale. S2, la regola e l'esito descrittivo di β₃
  (−4,93 [−10,21, +0,34]) restano invariati.

Riferimento: S2 = −3,184, SE 2,492, n = 4694.

## D1 — scomposizione sullo stesso disegno

| Termine | Valore |
|---|---|
| g·d (= S2) | −3,184 |
| g·γ_MWO | −4,761 |
| g·γ_WL | +1,425 |
| g·r (termine di riavvolgimento assiale) | +3,002 |
| residuo dell'identità | −4·10⁻¹⁶ |

- **Riavvolgimenti:** 180 record su 4694 (3,8 %).
  - 72 con r = −180°, contributo −0,322;
  - 108 con r = +180°, contributo +3,324.
- **Intervalli nominali di M** (non validati, non sottraibili, componenti non indipendenti):
  - γ_MWO: −4,76 [−10,09, +0,57];
  - γ_WL: +1,42 [−2,46, +5,31];
  - entrambi con φ al bordo (0,98); per γ_WL anche κ al bordo (−0,98).
- **Lettura descrittiva:**
  - sullo stesso disegno, la pendenza dei tilt MWO ha stima puntuale negativa;
  - quella dei tilt in luce bianca ha stima puntuale piccola e positiva, con un intervallo che contiene zero;
  - il termine assiale vale circa +3,0. Senza di esso la differenza delle due pendenze sarebbe −6,19.
  - È il termine necessario per passare dalla differenza delle due risposte codificate alla differenza assiale.
    Non è una correzione da togliere, né una quota di errore strumentale: i 180 record non sono dichiarati errati.
    I contributi dipendono dalla riga g, non soltanto dal numero di riavvolgimenti.
  - La scomposizione non dice quale strumento o fenomeno causi la differenza. I −4,76 riguardano il sottoinsieme
    WL (4694 record), non la stima principale −4,93 sui 5223 record.

## D2–D4, D6 — stime di S2 su sottoinsiemi ed esclusioni

| Tipo | Gruppo | n | β | SE | intervallo nominale | Δβ | Δβ/SE_S2 | bordo REML |
|---|---|---|---|---|---|---|---|---|
| esclusione | senza E2 | 4061 | −5,90 | 2,71 | [−11,96, +0,16] | −2,72 | −1,09 | κ |
| esclusione | senza E3 | 4186 | −3,17 | 2,55 | [−8,89, +2,54] | +0,01 | +0,00 | — |
| esclusione | senza E4 | 4384 | −3,23 | 2,69 | [−9,25, +2,80] | −0,04 | −0,02 | — |
| esclusione | senza E5 | 3628 | −3,13 | 2,88 | [−9,58, +3,31] | +0,05 | +0,02 | — |
| esclusione | senza E6 | 4578 | −3,14 | 2,51 | [−8,76, +2,49] | +0,05 | +0,02 | — |
| esclusione | senza E8 | 2711 | −0,01 | 3,24 | [−7,27, +7,26] | +3,18 | +1,28 | κ |
| sottoinsieme | fonte GYUL | 2747 | −4,60 | 3,39 | [−12,19, +3,00] | −1,41 | −0,57 | φ, κ |
| sottoinsieme | altre fonti | 1947 | −1,06 | 3,97 | [−9,95, +7,84] | +2,13 | +0,85 | φ |
| sottoinsieme | area DPD, terzile 1 | 1526 | +9,91 | 7,44 | [−6,77, +26,59] | +13,09 | +5,25 | — |
| sottoinsieme | area DPD, terzile 2 | 1597 | +5,39 | 4,20 | [−4,02, +14,80] | +8,58 | +3,44 | φ, κ |
| sottoinsieme | area DPD, terzile 3 | 1571 | −7,11 | 2,94 | [−13,70, −0,52] | −3,93 | −1,58 | κ |
| sottoinsieme | Φ_MWO, terzile 1 | 1565 | −2,14 | 4,54 | [−12,31, +8,04] | +1,05 | +0,42 | φ |
| sottoinsieme | Φ_MWO, terzile 2 | 1564 | −3,34 | 3,49 | [−11,16, +4,47] | −0,16 | −0,06 | κ |
| sottoinsieme | Φ_MWO, terzile 3 | 1565 | −3,88 | 3,07 | [−10,76, +2,99] | −0,70 | −0,28 | κ |
| sottoinsieme | separazione, terzile 1 | 1565 | −8,31 | 8,01 | [−26,26, +9,64] | −5,12 | −2,06 | κ |
| sottoinsieme | separazione, terzile 2 | 1564 | −0,97 | 3,67 | [−9,20, +7,26] | +2,22 | +0,89 | φ, κ |
| sottoinsieme | separazione, terzile 3 | 1565 | +0,22 | 2,88 | [−6,24, +6,67] | +3,40 | +1,36 | κ |
| sensibilità | senza \|d_WL\| > 45° | 3869 | −1,18 | 1,58 | [−4,71, +2,36] | +2,01 | +0,81 | φ |

Confini dei terzili:
- area DPD: 15 e 125 milionesimi;
- Φ_MWO: 7,3·10²⁰ e 2,4·10²¹ Mx;
- separazione: 4,13° e 6,22°.

Nessun record senza fonte DPD.

Osservazioni descrittive:
- **Esclusioni di epoca.** Le stime cambiano poco, salvo due:
  - senza E8 (1996–2012, 1983 record) la stima puntuale va a circa zero, ma l'intervallo
    [−7,27, +7,26] non dimostra equivalenza. Togliere E8 cambia anche la copertura temporale, i cicli e il disegno:
    non dimostra un difetto dell'epoca e non autorizza a escluderla dal catalogo;
  - senza E2 (1974–1981) diventa più negativa.
  - Le altre esclusioni spostano la stima di meno di 0,03 SE.
- **Fonte DPD.** La stima è più negativa sui giorni di Gyula che sulle altre fonti. Gli intervalli sono larghi e si
  sovrappongono ampiamente.
- **Area DPD.** Le stime puntuali vanno da positive nei gruppi piccoli a negative nei grandi. Solo il terzile più
  grande ha un intervallo che esclude zero, tra i 19 fit correlati e con intervalli non validati. Non è un nuovo
  verdetto per le regioni grandi né un motivo per sceglierle come nuova analisi principale. Nei gruppi piccoli
  gli intervalli sono molto larghi.
- **Separazione.** La stima passa da più negativa per le separazioni corte a vicina a zero per le lunghe.
  Il verso del cambiamento puntuale è diverso da quello dei terzili di area; nessuno dei tre intervalli esclude zero.
- **Flusso Φ_MWO.** Stime simili fra terzili.
- **Differenze grandi (D6).** Escludendo i 825 record con |d_WL| > 45° (17,6 %), la stima è −1,18, con SE 1,58.
  - La selezione è sulla risposta: il cambiamento può venire dal taglio stesso.
  - Non indica che quei record siano errori di misura.
- **D7, bordo REML.** 13 fit su 19 hanno φ o κ al bordo del dominio, come la stima principale di β₃. Gli SE di
  queste righe vanno letti con questa avvertenza; non se ne trae alcuna causa.

## D5 — riassunti per terzile di attività

Confini dei terzili di A_main: 1,12 e 2,05. Intervalli bootstrap al 95 % su blocchi di 6 CR; 2000 repliche valide per
ogni cella non vuota.

| Gruppo | Statistica | Terzile 1 | Terzile 2 | Terzile 3 |
|---|---|---|---|---|
| tutti | media pesata d_WL | +1,64 [+0,03, +3,30] | +0,47 [−1,51, +2,40] | −1,18 [−3,95, +1,09] |
| tutti | mediana d_WL | +1,14 [+0,37, +2,12] | +0,82 [+0,07, +1,68] | +0,64 [−0,59, +1,49] |
| tutti | quota \|d_WL\| > 45° | 15,3 % [13,4, 17,3] | 17,9 % [16,1, 19,6] | 19,5 % [17,0, 21,9] |

- **La media pesata scende nei tre terzili osservati di attività.** È un riassunto non aggiustato per ciclo,
  emisfero ed epoca: non riproduce né spiega da solo la pendenza parziale S2. La mediana scende meno.
- **La quota osservata di differenze grandi cresce nei tre terzili di attività.** È anche più alta:
  - nei gruppi piccoli: 28,7 % nel primo terzile di area contro 9,9 % nel terzo;
  - con separazione corta: 23,7 % contro 15,1 %;
  - con poco flusso: 21,0 % contro 12,8 %.
- **Esclusione di E8:** la media pesata va da +2,35 a +0,48 fra i terzili 1 e 3, contro +1,64 → −1,18 con tutte le
  epoche.
- Queste quote marginali non separano attività, dimensione e geometria delle regioni e non dimostrano errori di
  misura o differenze fra gruppi nella popolazione solare. Gli intervalli bootstrap restano descrittivi.
- Tutte le 84 celle sono in `SUMMARIES.csv`. Il gruppo «fonte mancante» è vuoto (n = 0, intervalli assenti con causa).

## Limiti

- Diagnosi post hoc, con intervalli non validati e molti confronti correlati.
- Le caratteristiche delle regioni (area, separazione, flusso) sono correlate fra loro e con l'attività.
- Le soglie di 300 record e di 45° sono operative, scelte dopo la lettura degli esiti di stabilità.
- La scomposizione D1 è un'identità algebrica sullo stesso disegno: non separa effetti fisici e strumentali.
- Il risultato T3 resta descrittivo, senza verdetto. Ogni ipotesi suggerita da queste tabelle richiederebbe un nuovo
  protocollo congelato prima e una validazione separata.

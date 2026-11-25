# Pilota MDI — Q4: precisione prospettica di T3 con un catalogo MDI 1996–2010 (rapporto descrittivo)

25 novembre 2026, Claude. **Bozza per la revisione di Codex** (la formulazione va rivista prima di qualunque uso).
Nota congelata `docs/MDI_PILOT_Q4_NOTE.md` (e13a3a72…) con l'emendamento A2 (c8340770…).

## 0. Che cosa è e che cosa non è

- Q4 stima la **precisione attesa** della pendenza T3 (β₃, dipendenza del tilt dall'attività) se si costruisse un
  catalogo MDI 1996–2010. Ci sono due prodotti, sinottico (MS) e full-disk (MF), da soli e insieme al campione HMI (H).
  Serve alla decisione se costruire il catalogo e con quale prodotto.
- È una varianza WLS analitica **condizionata a scenari dichiarati**: rumore individuale, componente temporale, rese,
  flussi. Le 20 realizzazioni descrivono la variabilità del disegno. Non sono intervalli calibrati, non stimano β₃, non
  validano la procedura M su MDI e non dicono nulla sul quenching reale del Sole.
- Le soglie di lettura (0,7, 0,9, 1,1) sono **preferenze pratiche fissate prima dei calcoli** (nota §7), non criteri
  scientifici. **La decisione resta all'utente con Codex.**

## 1. Provenienza

- Corsa unica su 1c25c2e pulito (codice fed1775, approvato da Codex), uscita 0, selftest interno 55/55. Output
  conservati prima della lettura in dab5a33.
- Riconteggio indipendente `scripts/mdi_q4_recount.py` (d303c3a): ricevuta 21/21 non parziale in 8924285, con tutti i
  prodotti ricostruiti e uguali. Verifica di integrità di Codex 9/9 (f4ad0a7). Nessuna realizzazione non calcolabile
  (NOT_COMPUTABLE vuoto, 440 disegni su 440 «ok»).
- Le tolleranze dei modelli protetti (bA per la famiglia A, bJ per la J) sono rumore numerico per costruzione e **non
  si leggono** (riconteggio, controllo dedicato).

## 2. Disegni (configurazione di riferimento, soglia 50 G, mediane sulle 20 realizzazioni)

| Disegno | Record | Resa attesa | Note |
|---|---|---|---|
| H (HMI E0) | 2485 | — | CR 2096–2316 |
| MS | 4705 su 5151 | 0,91 | ciclo 23 ≥ 50 record per emisfero in tutte le realizzazioni |
| MF | 2290 su 5062 | 0,45 | resa per pool di coorte, modello approssimato (nota §3.3) |
| MS+H | 7190 | — | |
| MF+H | 4775 | — | |

- Donatori di flusso L-NN: distanza massima in |λ| fra il gruppo e i 5 donatori, mediana 4,9°, 90° percentile 10,3°.
  Il requisito flusso–latitudine resta attenuato e non soddisfatto (A2).
- Rese deterministiche (YIELD_EFFECTS):
  - MS: 0,928 pubblicata → 0,937 senza le unità con mappe mancanti → 0,910 media Beta nel dominio Q4;
  - MF: 0,470 pubblicata → 0,477 senza le unità del gap → 0,476–0,485 nei pool (lettura per rami, ogni pool riparte
    dalla stessa base).

## 3. Criteri della nota §7

Rapporto h(disegno)/h(riferimento) nella stessa realizzazione: mediana su 20 e, fra parentesi, minimo–massimo. Le tre
forme principali sono AR(1) φ = 0,5, AR(1) φ = 0,9 e salti di 20 CR, a σ_x = 7,5°. Riferimento: σ_int = 15°,
σ_m = 2°, modello (a).

| Criterio | 50 G (principale) | 100 G (sensibilità) |
|---|---|---|
| MS+H / H | 0,691 (0,65–0,74) · 0,709 (0,68–0,74) · 0,707 (0,68–0,74) → **«marginale»** | 0,686 · 0,698 · 0,696 → **«utile come limite»** |
| MS+H / H con (30°, 10°) | 0,741 · 0,741 · 0,737 | 0,738 · 0,733 · 0,729 |
| MS / H | 0,89 (0,83–0,96) · 0,92 · 0,92 → «misura T3 su un altro periodo/ciclo (essenzialmente il 23), con precisione prospettica almeno pari» | 0,90 · 0,92 · 0,92, stessa classe |
| MF / H | 1,07 · 1,03 · 1,02 → «precisione inferiore a H» | 1,05 · 1,01 · 1,00, stessa classe |
| MF+H / MS+H (pool di coorte) | 1,105 (1,03–1,19) · 1,034 · 1,024 → **«MF non considerato (perdita di resa)»** | 1,088 · 1,026 · 1,017 → **«MF da considerare»** |
| MF+H / MS+H (pool coorte × attività) | 1,088 · 1,022 · 1,012 | 1,075 · 1,018 · 1,014 |
| accanto, modello protetto bJ, MS+H / H | 1,000 (per costruzione: in bJ β è la pendenza HMI) | 1,000 |
| accanto, modello protetto bA, MS+H / H | 0,854 · 0,808 · 0,804 | 0,863 · 0,825 · 0,822 |

**Lettura.**
- **Il contributo di MDI sta sulla soglia di 0,7.** A 50 G una forma è sotto la soglia (0,691) e due sono appena sopra
  (0,707 e 0,709). A 100 G tutte e tre sono sotto (0,686–0,698). Lo scarto che cambia la classe (meno di 0,01) è più
  piccolo della variabilità fra realizzazioni (circa 0,65–0,74). Le etichette «marginale» e «utile come limite»
  descrivono quindi lo stesso risultato: un intervallo più stretto di circa il 30 % (h ridotto a circa 0,7 di quello di
  H), vicino al confine fissato.
- **Il prodotto MF dipende dalla forma AR(1) φ = 0,5.** Le altre due forme danno 1,01–1,04; la forma φ = 0,5 dà
  1,09–1,11, a cavallo di 1,1 fra le soglie di 50 e 100 G. MF da solo è meno preciso di H (1,00–1,07), perché la resa
  stimata è circa la metà di quella sinottica.
- **MS da solo:** 0,89–0,92 rispetto a H, sul ciclo 23 essenzialmente. Non è una replica indipendente: ipotesi e
  possibili correlazioni temporali sono condivise.
- **Modelli protetti.** Con bJ MDI non aggiunge informazione sulla pendenza (rapporto 1,000 per costruzione). Con bA il
  rapporto è 0,80–0,85. Un «utile» del modello (a) presuppone scarti fra strumenti indipendenti dall'attività, non
  verificati (nota §7).

## 4. Sensibilità di MS+H / H (50 G, forme principali)

| Sensibilità | Rapporti (φ 0,5 · φ 0,9 · salti) |
|---|---|
| griglia σ_int ∈ {15, 25, 30} × σ_m ∈ {0, 2, 10} | da 0,689–0,708 (15°, 0°) a 0,737–0,741 (30°, 10°) |
| pesi MDI × 0,5 | 0,666 · 0,677 · 0,675 |
| pesi MDI × 2 | 0,754 · 0,776 · 0,773 |
| pesi normalizzati per strumento | 0,677 · 0,693 · 0,691 |
| blocchi di covarianza MDI–HMI azzerati | 0,691 · 0,709 · 0,707 (invariati alla terza cifra) |
| flussi senza latitudine | 0,678 · 0,697 · 0,694 |
| scenari temporali 3 (φ 0,9, κ −0,8) e 4 (φ 0,5, κ +0,6), σ_x × {0,5, 1, 2} | 0,56–0,66 (scenario 3); 0,73–0,74 (scenario 4) |
| forme principali a σ_x × 0,5 e × 2 | 0,72–0,73 (× 0,5); 0,67–0,70 (× 2) |

La scala relativa dei pesi MDI/HMI non è calibrata (nota §3.4): con pesi ×2 il rapporto sale a circa 0,77, con ×0,5
scende a circa 0,67. È la sensibilità più ampia fra quelle esaminate, oltre allo scenario temporale 3.

## 5. Precisione assoluta e riconoscimento dello scenario

Riferimento, 50 G. h in unità di γ₀ = 24°. SE/|Δβ| rispetto al bersaglio con δ_max = 0,20 e quantili E0.

| Disegno | h/γ₀ (φ 0,5 · φ 0,9 · salti) | SE/|Δβ| | Riconoscimento dello scenario |
|---|---|---|---|
| H | 0,43 · 0,56 · 0,60 | 2,9–4,0 | 2,3–2,9 % |
| MS | 0,38 · 0,52 · 0,55 | 2,7–3,9 | 2,4–3,1 % |
| MF | 0,46 · 0,58 · 0,61 | 3,5–4,5 | 2,2–2,5 % |
| MS+H | 0,30 · 0,40 · 0,42 | 2,0–3,0 | 2,8–4,0 % |
| MF+H | 0,32 · 0,41 · 0,44 | 2,3–3,1 | 2,7–3,5 % |

Anche nel disegno combinato l'errore standard resta 2–3 volte la riduzione prescritta: lo scenario non sarebbe
riconoscibile. La frequenza di riconoscimento (3–4 %) è vicina a quella sotto l'ipotesi nulla (1,25 % per lato). Come
nella fase A, l'uso realistico di MDI è **un intervallo più stretto su β₃, non il riconoscimento dello scenario**. Con i
quantili ricalcolati sul disegno i valori sono simili (riconoscimento 2,6–3,5 % per MS+H).

## 6. Scarti fra strumenti e fra prodotti (descrittivi)

- **Differenza fra prodotti (scenario non cieco, nota §5).** Se la differenza Q2 sinottica − full-disk per classe di
  attività valesse per i gruppi futuri, β di MS da solo si sposterebbe di −0,63° per unità di attività. È circa −0,42
  volte il bersaglio (fra −0,46 e −0,36 sulle realizzazioni); per MS+H circa −0,29 volte. Gli intervalli di d_γ di Q2
  contengono zero: è uno scenario, non uno scarto dimostrato, e non è una distorsione assoluta di MS rispetto al vero.
- **Scarti di attività fra strumenti (modello (a), combinati).** La tolleranza, cioè il coefficiente di scarto che
  sposta β di metà del bersaglio, vale circa 0,75 unità per la famiglia A e 0,68 per la J. Nel caso peggiore con
  |C| ≤ 0,5 la frequenza di falso «supportato» sotto l'ipotesi nulla resta intorno al 2 %.
- MDI da solo: uno scarto di misura della forma c·(A − 1)·sin|λ| coincide con x₃ e sposta β esattamente di c. Non è
  separabile e non si calcola (nota §5). La stabilità interna di MDI non è verificata.

## 7. Che cosa resta aperto per la decisione

- Il contributo di MDI a T3 è un intervallo più stretto di circa il 30 % nel modello (a), al confine della soglia
  pratica fissata. Dipende dalla scala relativa dei pesi e dall'ipotesi di scarti fra strumenti indipendenti
  dall'attività; nel modello protetto bA il guadagno è minore (0,80–0,85) e nel bJ nullo per costruzione.
- Sinottico contro full-disk: il sinottico ha resa doppia. Il full-disk si avvicina al sinottico solo in due forme su
  tre, e la scelta dipende anche dalla differenza fra prodotti (§6), che Q4 descrive ma non risolve.
- Nessun riconoscimento dello scenario prescritto in nessun disegno.
- Il catalogo MDI completo e un nuovo T3 restano decisioni separate, con protocollo proprio (`docs/BL_WORK_PLAN.md`).

## 8. Numeri riproducibili

Tutti i valori di questo rapporto vengono da `results/MDI_Q4_PROSPECTIVE/` (CRITERIA, RAW, DESIGNS, YIELD_EFFECTS),
letti dopo la ricevuta 8924285; rapporti appaiati per realizzazione come nella funzione `criteria` del runner. Uno script
di sola lettura che li ricalcoli va aggiunto prima della revisione finale, come per il rapporto L2.

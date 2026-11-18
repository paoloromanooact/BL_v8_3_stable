# Pilota MWO: tilt magnetici da magnetogrammi Mount Wilson contro P1 (2010–2013) — protocollo CONGELATO

**CONGELATO il 18 novembre 2026** dopo due revisioni di Codex (via al congelamento con le scelte approvate: finestra ±6°/±8°, 50 G, soglie 90 %, 2,107°, 5°, UTC, denominatori, copertura, regola sul taglio di flusso; via alla corsa dopo la correzione e la prova completa del riconteggio, `305191e`). Testo della bozza revisione 2, conservata in `docs/PROTOCOL_MWO_PILOT_DRAFT.md`; SHA-256 e commit in `docs/PROTOCOL_MWO_PILOT_FREEZE.json`. Serve a decidere se i tilt magnetici
misurati da noi sui magnetogrammi MWO (risoluzione circa 13″ × 20″) sono abbastanza vicini a P1 da usarli per T3 sul
periodo 1974–2012 (variante §8b di `docs/PROTOCOL_T3_DPD_DRAFT.md`). Nessun tilt MWO è stato calcolato. Codice:
`scripts/mwo_pilot_tilt.py` (selftest 9/9 su magnetogrammi sintetici). Non cieco: noti i risultati HMI, il confronto
MDI–HMI (mediana |d_ax| 2,15° su 4 coppie) e la scala BARD-MDI (2,107°).

## 1. Campione (solo metadati, ricontato dopo la revisione di Codex)

**Tempi.** T_REC di P1 è in TAI; gli orari MWO (TAVG-UT) e le date DPD sono in UT: T_REC si converte in UTC (astropy)
prima di ogni confronto di giorno o di orario. Con la conversione 33 candidati su 534 cambiano giorno.

**Manifesto dei candidati e denominatori.** Candidati: record P1 del campione S con data UTC < 2014-01-01 e numero NOAA,
**534**. Ogni candidato resta nel manifesto con il suo stato: senza gruppo DPD dello stesso numero lo stesso giorno UT
**35**; con gruppo DPD ma senza magnetogramma MWO Fe I lo stesso giorno UT **232**; **abbinati 267** (sostituisce il
conteggio 272, che usava T_REC in TAI come se fosse UT). La misura si tenta su tutti i 267 abbinati; le esclusioni
successive (effemeridi, dominio μ, una sola polarità, tilt P1 mancante) sono riportate con la causa. Conteggi verificati
da due implementazioni (runner e riconteggio indipendente).

## 2. Misura MWO per record

1. **Magnetogramma**: fra quelli Fe I dello stesso giorno UT (riconoscimento della riga come nella pipeline MWO), quello
   con TAVG-UT più vicino al T_REC del record P1; se supera i controlli di effemeridi della pipeline MWO (|ΔCENLON| ≤ 18°,
   |ΔB0| ≤ 0,5° rispetto alla data), altrimenti il successivo più vicino; se nessuno li supera: escluso con motivo.
2. **Centro**: latitudine e longitudine di Carrington del gruppo DPD dello stesso giorno (righe `g`, stesso numero NOAA;
   se più righe, quella con area WS corretta maggiore). Nessuna correzione di rotazione differenziale (stesso giorno).
3. **Finestra**: |λ − λ_DPD| ≤ 6°, |L − L_DPD| ≤ 8° (proposta da rivedere); tutti i pixel della finestra con μ ≥ 0,8,
   altrimenti escluso (dominio come nel confronto MDI–HMI).
4. **Campo e soglie**: B_r = B_LOS/μ; |B_r| ≥ 50 G e ≤ 4000 G (proposta: i campi MWO sono diluiti dalla risoluzione).
5. **Tilt**: baricentri pesati con |B_r|/μ per polarità, sulla sfera; convenzione di P1 (testa = polarità più a ovest,
   `geometry.tilt_deg`); segno della polarità di testa.

**Flusso in Mx (dopo la revisione di Codex).** Flusso = Σ |B_r|·(R☉/R0)²/μ, con R0 il raggio del disco in pixel e
R☉ = 6,96·10¹⁰ cm (raggio nominale di P1): serve per il rapporto di flusso con P1; nei baricentri il fattore si cancella.
Prova sintetica: un campo radiale uniforme di 100 G restituisce 100 G × l'area sferica della finestra entro il 3 %.

**Copertura minima.** Il pilota è informativo solo se almeno **150 dei 267** abbinati sono valutabili (due polarità,
dominio μ, effemeridi, tilt P1) e almeno **50 per emisfero**; altrimenti l'esito è «pilota non concludente» (anche con
zero valutabili) e si riporta la tabella delle cause di esclusione, senza criterio.

## 3. Confronto con P1 e sintesi

Per ogni record: d = tilt_MWO − tilt_P1, d_ax = differenza assiale modulo 180°, d_γ = sign(λ_P1)·d_ax (convenzione di
Joy, come nel protocollo MDI–HMI), accordo della polarità di testa, rapporto dei flussi e distanza dei baricentri.
Sintesi: mediana, minimo, massimo, media e s/√n di d_γ e d_ax, mediana di |d_ax|, frazione di polarità di testa
concordi; per emisfero e per terzile del flusso P1 (per vedere l'effetto della risoluzione sulle regioni piccole).

## 4. Criterio per proseguire (proposta, da fissare prima del congelamento)

La variante MWO è **utilizzabile per T3** se, sui record valutabili: polarità di testa concorde in almeno il 90 %;
|mediana(d_γ)| < 2,107° complessivamente e in ciascun emisfero; mediana di |d_ax| ≤ 5°.
Se il criterio fallisce nell'insieme ma è soddisfatto nei due terzili di flusso più alti **con almeno 30 regioni
valutabili per emisfero** in quei terzili, l'esito è «non utilizzabile così; motiva un protocollo successivo con soglia di
flusso, da validare sul campione ristretto»: non autorizza a usare la variante. Altrimenti la variante MWO non è
utilizzabile e resta la via dei tilt in luce bianca DPD. Il criterio motiva la costruzione del catalogo MWO; **non** autorizza a interpretare una pendenza T3 senza
due verifiche ulteriori: lo scarto MWO–riferimento in funzione dell'attività e la stabilità fra le epoche strumentali
di MWO (stesso limite del protocollo MDI–HMI).

## 5. Esecuzione

Due implementazioni indipendenti (misura e riconteggio), output conservati prima della lettura, confronto riga per riga,
come per MDI–HMI. Nessuna rete: dati MWO e DPD già locali.

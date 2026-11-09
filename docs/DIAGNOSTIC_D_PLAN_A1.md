# Emendamento A1 al piano del controllo diagnostico D

Stato: **registrato il 2026-11-09 prima di scrivere ed eseguire il codice di D**, dopo la
revisione del piano (`docs/DIAGNOSTIC_D_PLAN.md`, commit `ef56df9`, SHA-256 `e530af4a…`), che
resta agli atti e invariato. Nessun risultato di D esiste quando questo emendamento è scritto.
A1 sostituisce solo i punti indicati; il resto del piano vale com'è.

## 1. Raggruppamento per catalogo (sostituisce §4, "errore raggruppato per catalogo")

L'unità di raggruppamento è la coppia **(scenario, k)**: con semi distinti per scenario, i
cataloghi di scenari diversi sono diversi anche se hanno lo stesso k e non si accorpano.

## 2. Semi interni del campione Monte Carlo (sostituisce §5, controllo 4)

Semi della calibrazione interna: **1 900 000 + 10 000·s + 2k + t**, con s come in §2 del piano
(1 per V1, 4 per V4), k = 0…99 e t = 0 per T3, 1 per T5. Intervalli distinti per scenario
(V1: 1 910 000–1 910 199; V4: 1 940 000–1 940 199), senza sovrapposizioni con i semi dei
cataloghi né con quelli già usati.

## 3. Errore standard: formula fissata (precisa §4)

Si usa **solo** l'errore stimato dai dati, con queste formule; l'errore calcolato sotto il
valore nominale non si calcola e non si usa:
- **per scenario e test (D3):** n cataloghi, f = (falsi verdetti)/n,
  SE = √(f (1 − f) / n);
- **sintesi D1 e D2:** per ogni catalogo (s, k) incluso, m_{s,k} = media dei suoi indicatori
  di falso verdetto (T3 e T5); f = media degli indicatori; con G cataloghi inclusi,
  SE = dev. standard campionaria (ddof = 1) degli m_{s,k} / √G.
- In tutti i criteri la statistica è (f − 0,025) / SE e la soglia è ±2.

## 4. Esito sotto il nominale (completa §6)

Se D1 dà 2,5% − f > 2 SE, il livello risulta **sotto il nominale** secondo il criterio fissato:
come per l'eccesso, P2f resta sospeso e la causa si indaga con un piano separato.

## 5. Formulazione dell'eccesso (sostituisce §4, D1)

Se f − 2,5% > 2 SE, si dirà **"eccesso rilevato nella nuova prova secondo il criterio
fissato"**, non "strutturale": la causa (generatore, rappresentazione, decisione o altro)
richiede l'indagine successiva con un piano proprio. Analogamente, |f − 2,5%| ≤ 2 SE si dirà
"compatibile con il 2,5% nella nuova prova", senza dimostrare il livello nominale.

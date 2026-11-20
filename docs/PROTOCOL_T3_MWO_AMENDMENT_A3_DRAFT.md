# Emendamento A3 al protocollo T3 su MWO — magnetogrammi con distribuzione del campo anomala (bozza)

**BOZZA NON CONGELATA, 20 novembre 2026 (Claude). Da rivedere con Codex e congelare prima di una nuova misura.**
Protocollo `docs/PROTOCOL_T3_MWO.md` (`4408a0ee…`); emendamenti A1 (`bc88452b…`) e A2 (`0d50aa16…`) invariati.

**Dichiarazione.** La regola è stata scritta **dopo aver visto l'audit dei pixel** (`results/MWO_PIXEL_AUDIT/`,
`scripts/mwo_pixel_audit.py`, commit `e72b819`), che contiene per ogni magnetogramma Fe I solo statistiche del campo sul
disco centrale. È **cieca rispetto ai tilt**: SEALED di R2 e R3 non è mai stato aperto. Il peso dei record nel
catalogo ha attirato l'attenzione su uno dei casi (NOAA 9119, 2000-08-06), ma non è un criterio: la regola guarda solo
i pixel e le scansioni comparabili.

## Problema

Dopo A2, il record più pesante di R3 (NOAA 9119, 2000-08-06, area DPD 51, Φ_MWO 7,8·10²² Mx, 2,4 volte il secondo)
viene da `2000/m000806_1660_0fe1.fits`. Il file ha GV = 3 ma:
- mediana di |B| sul disco centrale (μ ≥ 0,8, senza BLANK) 27,5 G, contro 2,05 G delle 6 scansioni dei ±3 giorni;
- 99° percentile 1562 G e massimo 1638,3 G = 32767·0,05.

L'audit di tutti i 30 952 magnetogrammi Fe I mostra altri casi con una distribuzione dell'intero campo
incompatibile con le scansioni vicine, oltre ai 18 di A2.

## Regola

Per ogni magnetogramma Fe I non escluso da A2:
- **m** = mediana di |B| sul disco centrale (μ ≥ 0,8, pixel BLANK esclusi, lettore congelato);
- **m_ref** = mediana delle m di tutte le altre scansioni Fe I (escluse quelle di A2) con istante UTC entro ±3 giorni;
- il magnetogramma è **anomalo** se m > 3·m_ref.

Proprietà osservate nell'audit, non scelte per ottenere un risultato:
- il rapporto m/m_ref è sotto 1,62 nel 99,9 % delle scansioni;
- nessuna scansione ha rapporto fra 2,5 e 3, quindi la soglia cade in un vuoto della distribuzione;
- tutti i casi oltre la soglia hanno almeno 5 scansioni di riferimento.

**Elenco risultante, 8 file** (`docs/PROTOCOL_T3_MWO_AMENDMENT_A3_EXCLUDED_FITS.csv`, con m, numero e mediana del
riferimento, rapporto, p99, massimo, frazione saturata e SHA-256 del contenuto del membro; SHA-256 del CSV
`21beaef5…`):

| File | Rapporto m/m_ref | Riferimento | Uso in R3 |
|---|---|---|---|
| 1974-07-16 `MP00_5250MWO_00_0740716_1802` | 3,6 | 5 scansioni | 9 tentativi, 0 record |
| 1975-09-29 `MP00_5250MWO_00_0750929_1763` | 8,4 | 5 | 2 tentativi, 1 record |
| 1986-05-14, 06-01, 06-02, 07-07 (4 file) | 16,8–19,3 | 62–102 | nessuno |
| 1989-09-10 `MP00_5250078_00_0890910_2378` | 17,4 (massimo 59 G: campo quasi uniforme) | 64 | nessuno |
| 2000-08-06 `m000806_1660_0fe1` | 13,4 (saturato) | 6 | 16 tentativi, 1 record |

**Cosa la regola non fa.**
- **La saturazione da sola non è un criterio.** Il file `1999/m990923_1770_0fe1.fits` ha l'8,5 % dei pixel centrali al
  valore massimo ma una mediana normale (rapporto 1,1); resta incluso, e comunque non è mai scelto in R3. Lo si
  riporta come limite.
- **Non si correggono i campi.** I file anomali si escludono e basta.
- **Riferimenti scarsi.** 2373 tentativi su 56 317 usano magnetogrammi con meno di 3 scansioni di riferimento nei
  ±3 giorni: per questi la regola è poco informativa e lo si dichiara.

## Applicazione

Come A2: elenco preciso con SHA-256, esclusione **prima** della scelta del magnetogramma, regola del primo giorno
riuscito invariata, stato `excluded_A3` in MAGNETOGRAMS, verifica nel riconteggio indipendente. Nuova misura **R4**
in una destinazione nuova, poi riconteggio, controllo del disegno, precisione attesa e, una sola volta, la
validazione. Pesi invariati (Φ_MWO).

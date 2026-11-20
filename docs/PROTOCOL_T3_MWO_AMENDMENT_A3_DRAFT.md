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
molto diversa da quella delle scansioni vicine, oltre ai 18 di A2.

## Regola

Per ogni magnetogramma Fe I non escluso da A2:
- **m** = mediana di |B| sul disco centrale (μ ≥ 0,8, pixel BLANK esclusi, lettore congelato);
- **m_ref** = mediana delle m finite di tutte le altre scansioni Fe I, escluse quelle di A2, nelle **sette date
  UTC da giorno−3 a giorno+3, estremi inclusi**. Il giorno deriva dall'istante di osservazione completo
  (data della sessione + TAVG-UT), non dalla sola data del nome del file. Non è un intervallo di ±72 ore.
  Ogni scansione pesa una volta; si esclude solo il membro stesso, anche in presenza di altri membri allo
  stesso istante. Il riferimento non viene ricalcolato rimuovendo ricorsivamente gli otto file di A3;
- il magnetogramma è **anomalo** se m > 3·m_ref (disuguaglianza stretta). Senza m finita, senza altri riferimenti
  o con m_ref non finita/non positiva, il confronto è **indeterminato**, non un controllo superato.
  I casi con uno o due riferimenti sono segnalati come poco informativi; non si introducono altre esclusioni.

La variante «stesso giorno» è stata esaminata e scartata dopo l'audit: produceva cinque segnalazioni aggiuntive
con un solo riferimento a mediana bassa (0,2–0,6 G). Anche questa scelta è successiva all'ispezione dei pixel.

Proprietà osservate nell'audit (non costituiscono una calibrazione del tasso di falsi allarmi):
- il rapporto m/m_ref è sotto 1,62 nel 99,9 % dei rapporti finiti;
- nessuna scansione ha rapporto fra 2,5 e 3, quindi la soglia cade in un vuoto della distribuzione;
- tutti i casi oltre la soglia hanno almeno 5 scansioni di riferimento.

**Elenco risultante, 8 file** (`docs/PROTOCOL_T3_MWO_AMENDMENT_A3_EXCLUDED_FITS.csv`, con m, numero e mediana del
riferimento, rapporto, p99, massimo, frazione saturata e SHA-256 del contenuto del membro; SHA-256 del CSV
`21beaef50e9beca38bc2150996adbf031e1d55192dea60682e4608a802541275`):

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
- **Riferimenti scarsi.** 2373 tentativi su 56 317 usano magnetogrammi con meno di 3 scansioni di riferimento
  nelle sette date UTC: per questi la regola è poco informativa e lo si dichiara. Nel bacino comparabile ci
  sono 37 scansioni senza alcun riferimento e 30 862 rapporti finiti (quantile 99,9 % = 1,6156).
- **Copertura dell'audit.** Oltre ai 18 A2, due file risultano illeggibili e 33 hanno zero pixel utilizzabili
  nel dominio centrale; nessuno dei 33 produce un record selezionato in R3. Questi ultimi compaiono in 55
  tentativi: 16 falliscono per window_blank e 39 per window_outside_mu_domain. Non sono certificati come sani.
- **Limite del controllo.** A3 individua anomalie relative alle scansioni vicine; non dimostra l'omogeneità
  dell'intero archivio né esclude derive, errori comuni a tutte le scansioni vicine o anomalie locali.
  I pesi restano congelati e nessuna soglia viene scelta sui tilt o sulla stima di β₃.

## Applicazione

Come A2: elenco preciso con SHA-256, esclusione **prima** della scelta del magnetogramma, regola del primo giorno
riuscito invariata, stato `excluded_A3` in MAGNETOGRAMS, verifica nel riconteggio indipendente. Nuova misura **R4**
in una destinazione nuova, poi riconteggio, controllo del disegno, precisione attesa e, una sola volta, la
validazione. Pesi invariati (Φ_MWO). L'elenco CSV e il suo hash fanno parte del congelamento; modificarli
richiede un altro emendamento. Prima di avviare R4, l'implementazione deve essere rivista e provata su un
archivio sintetico con un file A3 escluso, recupero di una scansione sana, marcatura e hash errati rifiutati.
Il riconteggio deve verificare separatamente A2 e A3 e il legame degli hash al META.

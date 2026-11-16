# MDI–HMI: associazioni candidate nella sovrapposizione

Analisi offline del 16 novembre 2026, limitata ai metadati già acquisiti. Non è un confronto delle
mappe o una calibrazione e non cambia i risultati sul quenching. Nessun filtro nuovo applicato.

## Provenienza e verifiche

Driver `scripts/mdi_smarp_overlap_analysis.py`, eseguito dal commit pulito
`198785bb300238a188d1b736c07068df5f27e3fc`, dopo il suo selftest offline.
Piano congelato `9269c10`, SHA-256
`a31de02a064b08584281930f4a7c7e0fc4216ab83cc7f69c8ee793ea5bce3be0`.
Raccoglitore e mappa registrata invariati; acquisizione descritta in
[MDI_SMARP_OVERLAP_ACQUISITION.md](MDI_SMARP_OVERLAP_ACQUISITION.md).

Artefatti locali, esclusi da Git:
`results/MDI_SMARP_INVENTORY/schema_20261116_http_ac06138/overlap_only/198785bb3002/`.
`META.json` conserva hash di codice, piano, configurazione e input. `CHECKS.json`: 11 controlli superati,
compresa riconciliazione degli originali e ricalcolo separato di abbinamenti temporali, distanze,
gradi, componenti e partizioni. La geometria documentata e la riconciliazione degli input sono condivise
con il raccoglitore: questi controlli non sono una verifica indipendente dell'identità fisica delle regioni.

Verifiche del repository: `bash scripts/check_repo.sh` superato (60 test, due avvisi attesi
su correlazioni di input costanti); `git diff --check` superato.

Esito `complete_for_overlap_only`, `inventory_complete=false`. Nessuna richiesta di rete aggiunta.
Registro dopo l'analisi: 272 tentativi, 45924964 byte, 119611 righe, circa 657,2 s cumulativi.

## Esito delle associazioni prefissate

11387 record SMARP, 127 TARP; 103709 record HMI con margini, 139 HARP.
Il conteggio scientifico HMI senza i tre record di margine resta 103706, con le stesse 139 HARP.
Si cercano i record HMI più vicini per HARPNUM entro 360 s, con pari merito al più antico;
poi si costruiscono separatamente i grafi entro 5° e 10°, senza filtrare QUALITY o NOAA.

| Descrittore | G5 | G10 |
|---|---:|---:|
| Archi tra record | 9820 | 12072 |
| Archi con entrambi i record di grado 1 | 8949 | 7565 |
| Coppie distinte TARP–HARP candidate | 121 | 161 |
| Coppie con almeno un arco univoco tra record | 112 | 106 |
| Componenti del grafo tra patch | 106 | 96 |
| Record SMARP con candidato | 9761 | 10404 |
| Record SMARP senza candidato | 1626 | 983 |

1555 archi univoci di G5 diventano ambigui in G10. Le 112 coppie con qualche arco univoco non sono
112 osservazioni indipendenti, né coppie confermate come la stessa regione fisica in tutti gli istanti.
Le geometrie dei centri e la ricerca temporale risultano complete per questo ambito; i riquadri restano
non valutabili per tutte le 62036 coppie temporali, perché mancano le dimensioni. Non sono inferite da CRPIX.

## Tempi effettivi e qualità: limiti da risolvere prima delle mappe

Tutte le 62036 coppie temporali hanno lo stesso T_REC nominale. Questo non garantisce simultaneità delle
osservazioni: T_OBS(HMI) − T_OBS(SMARP) va da −2844 a +2736 s. Nell'audit descrittivo successivo,
8873 dei 8949 archi univoci G5 hanno |ΔT_OBS| ≤ 360 s; 76 lo superano. Restano tutti negli output,
con la regola T_REC congelata. Nessuna selezione a posteriori o sostituzione con T_OBS.
Nei medesimi archi NOAA è concordante in 5728 casi e mancante in 3221, senza discordanti;
è un descrittore, non una conferma indipendente dell'abbinamento.

SMARP presenta QUALITY esattamente 0x200 in 10874 record su 11387; solo 262 hanno QUALITY=0.
Prima di selezionare le mappe serve la definizione nativa MDI/SMARP dei bit. Non si trasferiscono
le definizioni HMI e non si interpreta ogni valore non nullo come dato inutilizzabile. Nessun filtro
QUALITY applicato. Le distribuzioni complete dei valori grezzi sono in SUMMARY.json.

L'audit descrittivo ha inoltre controllato la griglia full-disk: rispetto all'epoca dichiarata
1993.01.01_00:00:30_TAI e al passo 5760 s, 4500 dei 4515 T_REC hanno resto 5730 s, e solo 15 resto zero.
La precedente deduzione secondo cui epoche diverse impediscono sempre coincidenze dei T_REC era troppo
forte. Occorre chiarire la semantica dei tempi indicizzati DRMS prima di interpretare le lacune full-disk;
non si traslano silenziosamente i tempi di 30 s. Questa analisi non calcola lacune o copertura storica.
La coincidenza nominale non documenta da sola il collegamento patch–sorgente, che resta ignoto.

`TIMING_AUDIT_POSTHOC.json` conserva questi descrittori aggiuntivi, non preregistrati, senza nuove regole.
INTERVAL=30 s resta ignoto con la regola 60/300 registrata; DPC non reinterpretato.

## Passo successivo circoscritto

Prima documentare i bit MDI/SMARP e il significato dei tempi/sorgenti. Poi scrivere un piano breve del
campione di mappe con criteri, fallimenti e budget fissati prima del download. Separare il confronto
HMI Br contro HMI LOS/μ dal confronto MDI LOS/μ contro HMI LOS/μ, per distinguere approssimazione del
campo radiale e differenze fra strumenti. Non è ancora un piano congelato né un via al download.
La sovrapposizione vicino al minimo non determina uno scarto strumentale dipendente dall'attività.

Storico, mappe e simulazioni non avviati. Piano prospettico e morfologia S restano in pausa. Nessun push.

## Hash degli artefatti locali

- `CHECKS.json`: `213ed032a9b271e5202cec814b76a57613d5d05be39adc8f0977410b35a1d235`
- `META.json`: `b3da0629e3e70c3d9f1f3e1f9cb6367631b291cc67128c51ffb10faff06c1ea7`
- `OVERLAP_CANDIDATES.csv.gz`: `caa25e794eb5ff4f3b4b7dd35bb2dc2070d6166ab9276dff7e7e095f2e7b28d2`
- `PATCH_PAIRS.csv`: `cbabc91147c3f4fdb91f4c15c00347e59104990a9d41ecd0eedfdf1276689208`
- `RECORD_STATES.csv`: `61f796873ab821af1e50773e837ac5182c0b3c489c660744773b6e6af7e56c7b`
- `SUMMARY.json`: `e120281f32d2c3146b62ee70c85b496444af70515ba7a72c9a0f65b13a7f4c68`
- `TIMING_AUDIT_POSTHOC.json`: `5c4174f9fa0e435af446bd315d2d2ab2d53b53180d912c8b54c90f41b9524d1d`

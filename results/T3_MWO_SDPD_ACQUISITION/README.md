# Acquisizione sDPD per T3 su MWO

File `sDPD1974.txt`–`sDPD2012.txt` (righe di macchia DPD) scaricati il 18 novembre 2026 con
`scripts/t3_mwo_fetch_sdpd.py --run` dopo il congelamento del protocollo (`docs/PROTOCOL_T3_MWO.md`, §9 passo 3) e la
revisione di Codex del validatore. I dati restano in `data/sharp/external_sDPD_20261118/` (non tracciati, come gli altri
dati scaricati); qui sono conservati gli hash, l'ora di acquisizione e il registro delle 40 richieste. Una richiesta
(sDPD2011, primo tentativo) ha avuto «connection refused», riuscita al secondo tentativo.

Controllo di coerenza: un download diagnostico precedente degli stessi 39 file (con `curl`, nello scratchpad della
sessione) ha dato file identici byte per byte. Righe con particolarità accettate dal validatore: secondi = 60
(115 righe nel 1977), |LCM| fino a 91,02° al bordo (4 righe nel 1978, 1979, 1998).

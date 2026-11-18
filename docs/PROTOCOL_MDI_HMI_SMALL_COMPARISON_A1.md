# Piccolo confronto MDI–HMI — emendamento A1 (trasporto dei FITS e budget)

**Registrato il 2026-11-18 prima di qualunque nuova richiesta a JSOC.** Protocollo di riferimento
`docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON.md` (congelato in `6d6fd12`, SHA-256 `3713236f…`), che resta invariato.
Selezione, coppie, rami, misure, soglie e sintesi non cambiano. Nessuna mappa è stata ricevuta o letta.

## 1. Che cosa è successo

Il downloader `scripts/mdi_hmi_patch_download.py` (`a19d3b6`, scritto da Codex, rivisto da Claude) con `--fetch` ha
ottenuto le keyword complete dei 24 record (24 richieste riuscite) e ha ricevuto **HTTP 302** su tutte le 84 richieste
dirette dei percorsi `/SUM…/<segmento>.fits`. Il downloader rifiuta i redirect per progetto: nessun corpo FITS
ricevuto. Non si è fermato al primo errore sistematico e ha consumato un tentativo per ciascuno degli 84 file. Totale
dei tentativi del confronto: 41 precedenti + 108 = **149**, contro il tetto di 200 del §6 con 45 riservati alla
provenienza (§8): il tetto residuo non basta per 84 file. Registro conservato in
`data/sharp/metadata_inventory_mdi/small_comparison_6d6fd12/patch_download/LEDGER.json`. Errore di revisione
dichiarato: mancava un arresto sugli errori sistematici.

## 2. Diagnosi (una richiesta)

Una sola richiesta GET, senza seguire redirect, sul primo segmento del manifesto (coppia 1, bitmap SMARP), con
registrazione di stato, intestazioni complete (in particolare `Location`) e al più 64 KiB di corpo. Conta nel nuovo
budget del §4.

## 3. Regola di trasporto, fissata prima della diagnosi

- Se `Location` è un URL assoluto o relativo verso un host in {jsoc.stanford.edu, jsoc1.stanford.edu,
  jsoc2.stanford.edu} e il percorso finale termina con lo stesso `/SUM…/S…/<segmento>.fits` del manifesto (anche con
  un prefisso di percorso del server), si segue **esattamente un redirect** per file. Con schema `https` si usa TLS
  con verifica standard di certificato e nome; non si disattiva mai la verifica. Un secondo redirect, un altro host,
  un altro nome di file o un errore TLS fermano il download con motivo registrato.
- Ogni altra destinazione ferma il download prima dei FITS; il caso si riporta senza ulteriori tentativi.
- Controlli invariati sui corpi: lunghezza annunciata pari a quella del manifesto (o +1 byte), firma FITS, multiplo
  di 2880, SHA-256 locale; lettura dei pixel separata (adattatore invariato).

## 4. Budget nuovo, separato e dichiarato

Il tetto di 200 tentativi del §6 è esaurito da un errore sistematico di trasporto. Si aggiunge un **budget A1 separato**:
al più **250 richieste HTTP** (ogni richiesta conta, anche la seconda di un redirect), **20 minuti** cumulativi, e
lo stesso tetto di **512 MiB** di corpi FITS e 32 MiB per file. Le 45 richieste riservate alla provenienza (§8)
restano riservate e non sono usate qui. Al più due tentativi per file, contando quello fallito del §1 come primo:
resta quindi **un solo tentativo** per ciascun FITS. Le keyword dei 24 record si riusano dal registro del §1, dopo
verifica dei loro SHA-256, senza nuove richieste.

## 5. Arresto sugli errori sistematici

Il download si ferma dopo **3 fallimenti consecutivi** con la stessa classe di errore (stato HTTP, redirect non
ammesso, TLS, lunghezza, firma), senza consumare altri tentativi; un manifesto parziale resta tale, senza sostituzioni.

## 6. Ordine

Registrazione di questo emendamento → diagnosi (§2) → codice di trasporto conforme al §3, con prove offline →
download → R0 → confronti. I risultati del confronto restano descrittivi, come nel protocollo congelato.

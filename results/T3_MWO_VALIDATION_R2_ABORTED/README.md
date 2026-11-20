# Validazione T3 MWO su R2 — interrotta il 20 novembre 2026

Avviata alle 10:58 da `8129c01` sul disegno del catalogo R2 (`results/T3_MWO_CATALOGUE_R2`). Selftest 41/41; benchmark
stratificato con previsione di 48,9 ore. **Interrotta alle circa 14:40** (SIGTERM al gruppo di processi), su proposta di
Claude, accordo di Codex e via dell'utente, dopo circa 3,6 ore di griglia e **prima di qualsiasi scrittura di
prodotti**: la validazione scrive RAW e SUMMARY solo alla fine, quindi non esiste alcun risultato parziale.

Motivo: il disegno R2 contiene 4 record (NOAA 5668, 5669, 5671, 5678; 1989-09-04/05) misurati su magnetogrammi con
GV = 0,03, che hanno il campo scalato di circa 100 volte e sono saturati a 3276,7 G. Sono 18 file in tutto, identici
all'elenco escluso dal controllo qualità congelato del progetto del flusso polare. Una validazione su R2 non potrebbe
certificare il disegno corretto. Il seguito è l'emendamento A2 (esclusione dell'elenco preciso dei 18 file prima della
scelta del magnetogramma), poi il catalogo R3.

# Q1 e Q2 su HMI: esito della validazione

Protocollo: `docs/PROTOCOL_HMI_FOLLOWUPS.md` (SHA-256 `316fa968…`, congelato in `255e658`). Corsa da `8e1ff12`, 5
processi, 150 000 unità in 15,0 ore (previsione 13,4 h; rallentata da altri calcoli sulla macchina). Output conservati in
Git prima della lettura (`45258ad`, `results/HMI_FOLLOWUPS_VALIDATION/`). Riconteggio indipendente della sola
validazione (`scripts/hmi_followups_recount.py --check-validation`, `results/HMI_FOLLOWUPS_VALIDATION_RECOUNT/`), 5 voci
su 5:
- hash dei prodotti;
- SE ricalcolato su ognuna delle 149 928 righe riuscite (scarto relativo massimo 4·10⁻¹³);
- frequenze ricalcolate dai dati grezzi (scarto 0);
- accettazione ricontata su una griglia scritta indipendentemente;
- 35 configurazioni.

La stima sui dati HMI (`--run`) **non è stata eseguita**: richiede un nuovo via.

## Esito

**Nessuno dei due test supera la validazione.** Per il §4 del protocollo, entrambi restano **descrittivi**: se la stima
viene eseguita, Q1 e Q2 si riportano con l'intervallo nominale e l'avvertenza, senza verdetto.

| Test | Configurazione che fallisce | Valore | Limite |
|---|---|---|---|
| Q1 (k₂₅ − k₂₄) | scenario 2 (AR(1) 0,9), nulla | falsi verdetti 4,57 %; «supportato» 2,54 %; «opposto» 2,03 % | 3,0 %; 1,75 % per verso |
| Q1 | scenario 2, effetto −2,4° | copertura 0,956 | ≥ 0,965 |
| Q1 | scenario 2, effetto −4,8° | copertura 0,9485; coda di esclusione 2,10 % | ≥ 0,965; ≤ 2,0 % |
| Q2 emisferico (β₄) | scenario 7 (salti di 20 CR), nulla | falsi verdetti 3,25 % (per verso 1,65 % e 1,60 %) | 3,0 % |
| Q2 emisferico | scenario 7, effetto +1° | copertura 0,962 | ≥ 0,965 |

Tutte le altre configurazioni principali passano: Q1 negli scenari 0, 1, 7 e 9; Q2 negli scenari 0, 1, 2 e 9. La quota
di `errore` è al massimo 0,09 %.

## Lettura

- **Q1** confronta due cicli. Con una componente temporale molto persistente (φ = 0,9) le rotazioni dello stesso ciclo
  si muovono insieme. Il contrasto fra cicli ha quindi poche unità indipendenti, e la stima REML della componente
  temporale ne sottostima la varianza: l'intervallo è troppo stretto in entrambi i versi. È un limite strutturale di un
  confronto fra due soli cicli, non un difetto numerico, e non si corregge con più cataloghi.
- **Q2 emisferico** fallisce di poco (3,25 % contro 3,0 %; copertura 0,962 contro 0,965) solo con salti a gradino di 20
  rotazioni. Questo scenario è mal specificato rispetto all'AR(1) di M, ma il protocollo lo include fra i principali.
- **Sensibilità senza criterio:** Q2 con fase convenzionale nello scenario 7 dà 3,95 % di falsi verdetti; Q2 emisferico
  con rumore 4° nello scenario 7 dà 3,50 %. Lo scenario a gradini è il punto debole anche fuori dall'analisi principale.

## Conseguenze

1. Q1 e Q2, se stimati, sono descrittivi, come T2 e T4 in P2. Le stime descrittive di P2 (T2 +3,3°, T4 −0,63°) restano
   le uniche già note.
2. Eseguire `--run` darebbe gli intervalli nominali di Q1, Q2 e Q3 con l'avvertenza. Serve il via dell'utente e di
   Codex: il valore aggiunto rispetto a P2 sarebbe la fase emisferica di Q2 e il quenching locale di Q3, entrambi
   descrittivi.
3. Un test di Q2 robusto ai gradini richiederebbe un protocollo nuovo, per esempio una procedura con blocchi o una
   componente a gradini nella stima. Non è proposto qui.

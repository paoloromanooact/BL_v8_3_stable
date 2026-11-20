# Audit indipendente della validazione HMI — 20 novembre 2026

Codex ha controllato i prodotti conservati in `45258ad`, senza eseguire la stima HMI sui dati reali.
L'audit `scripts/hmi_followups_validation_audit.py` non importa il runner né il riconteggio di Claude.
Condivide solo la definizione a monte del campione S e dell'attività; ricostruisce i contrasti con QR,
la griglia dei semi e le decisioni. Per la componente temporale somma il prodotto quadratico per lag
in un polinomio AR(1), verificato contro la matrice completa su dati sintetici con pesi di segno diverso.

Riproduzione: `.venv/bin/python scripts/hmi_followups_validation_audit.py --out /tmp/hmi_validation_audit.json`.
L'output richiesto deve essere nuovo. L'audit non scrive nelle directory dei risultati.

- SHA-256 di META.json `a08d0ad3a1a58e046e0145aa1ef0ea1fd9e00ba39a0e5a3ed664b06060da4121`.
- Protocollo congelato e tre hash dei prodotti coincidenti con META. Runner, definizione a monte del
  campione, catalogo P1 e SILSO invariati rispetto al commit di avvio registrato; SHA del runner coerente.
- 150 000 righe in 35 configurazioni, conteggi, indici, semi e ruoli completi e senza duplicati.
- 149 928 righe riuscite e 72 esiti `errore` registrati, conservati nei denominatori.
- Campi numerici delle righe riuscite finiti; SE positivi, intervalli ricostruiti da beta e SE,
  verdetti e indicatori di copertura/esclusione coerenti con l'intervallo e l'effetto generato.
- Tutti gli SE ricostruiti, scarto relativo massimo `4,0123460109953157e-13`.
- Frequenze del riepilogo e accettazione salvata concordi. Nessun problema tecnico nell'audit.

| Test | Scenario | Effetto | Criterio non soddisfatto |
|---|---|---:|---|
| Q1 | 2 | 0° | falsi 4,57%, versi 2,54% e 2,03% |
| Q1 | 2 | −2,4° | copertura 95,6% |
| Q1 | 2 | −4,8° | copertura 94,85%, coda 2,10% |
| Q2 emisferico | 7 | 0° | falsi 3,25% |
| Q2 emisferico | 7 | +1° | copertura 96,2% |

L'audit tecnico è superato; entrambi i test scientifici non superano la propria validazione congelata.
Quindi non sostengono un verdetto inferenziale. Se le stime saranno autorizzate, potranno essere riportate
come descrittive con intervalli nominali e i limiti espliciti. T3 e T5 non cambiano stato per questo audit.

Correzioni al rapporto di Claude: la quota massima di errore è 0,10%, non 0,09%; l'eccesso di falsi verdetti
in Q1 non identifica da solo la causa della sottocopertura né dimostra un limite insuperabile di ogni
procedura per il confronto fra cicli. Una spiegazione tramite stima della componente temporale resta
un'ipotesi da diagnosticare separatamente.

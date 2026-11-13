# Emendamento A1 al protocollo morfologico HMI

Stato: **registrato il 2026-11-13 dopo il congelamento (`21dfe6d`, SHA-256 `2547aeeb…`) e prima di
qualunque codice, immagine o lettura.** Precisa due punti su indicazione del revisore esterno; nessuna
regola di classificazione cambia.

1. **Vista ±300 G (precisa §2).** La frase del protocollo «ogni pixel che entra nella misura è visibile ad
   almeno un terzo della saturazione» va letta così: la scala aumenta il contrasto del campo vicino alla
   soglia P1, ma **non garantisce** che ogni pixel sia distinguibile, perché contano anche la risoluzione
   delle schede e la riduzione dell'immagine. La risoluzione di uscita delle schede si fissa nel codice
   del generatore e si registra.
2. **Taratura (precisa §3).** Durante la taratura sulle 11 schede di riferimento ciascun lettore registra
   classificazioni e disaccordi con hash **prima** del confronto tra lettori. Se dalla taratura emergesse
   la necessità di cambiare regole congelate, serve un emendamento registrato **prima** delle 90 letture.
3. **Ribadito (§4):** le etichette del lettore 1 restano nascoste al lettore 2 fino al blocco della lettura
   del lettore 2.

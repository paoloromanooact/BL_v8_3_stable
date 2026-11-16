# Correzione di formulazione della diagnosi dell'accesso (ricevuta `DIAGNOSIS.json`, `c63ff23`, invariata)

2026-11-16, dopo la revisione di Codex. Nella ricevuta e nell'handoff la frase «l'HTTPS offre solo TLS 1.0» è più
forte dell'evidenza. Le prove mostrano soltanto che la **negoziazione predefinita** (TLS ≥ 1.2, SECLEVEL 2)
**fallisce** e che una negoziazione **limitata a TLS 1.0** con SECLEVEL 0 **riesce**, con un certificato
autofirmato e scaduto; non sono state provate tutte le versioni. La lettura corretta è: l'endpoint HTTPS non ha
negoziato con le impostazioni del client, ha negoziato TLS 1.0 quando questo è stato offerto, e il certificato
non è verificabile. La conclusione operativa non cambia: HTTP risponde direttamente con il JSON.

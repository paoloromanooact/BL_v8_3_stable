# Revisione indipendente delle regole di riproducibilità

Data: 2026-11-11. Oggetto: commit `21e7210`. Revisione svolta da un agente separato
in sola lettura; correzioni preparate dall'agente principale e ricontrollate.
Nessuna analisi scientifica o simulazione rilanciata; nessun esito P2f consultato.

## Verifiche effettuate

- Tutte le 112 tabelle: cardinalità, 111 chiavi univoche e una tabella vuota;
  copertura di colonne/selettori, assenza di politiche duplicate.
- Tutti i 112 riferimenti: commit del file, blob e contenuto distribuito coerenti.
- Lettura mirata dei produttori per scale T5 D*/Φ contro S*/Φ, varianze, flussi,
  parametri AR e conteggi. Non trovata una tolleranza permissiva per i valori T5.
- Provenienza P2b: distinzione conservata fra commit registrato e codice equivalente
  dichiarato dai JSON. Non ripetuta la dimostrazione storica di equivalenza.
- I 23 controlli sintetici originali sono superati. Dopo le correzioni sono 29,
  tutti superati; nessuna simulazione scientifica fa parte di questi controlli.

## Rilievi e risoluzione

| Rilievo | Correzione adottata |
|---|---|
| Testo: coefficienti Joy a 24°; tabella: gamma0 a 1° | gamma0, gamma0_c24 e gamma0_c25 a 24°, coerenti con la scala di pianificazione dichiarata |
| se_var_z descritto come SE di una frequenza | motivazione corretta: errore standard della varianza di z sotto la normale; S=1 invariato |
| status fra i metadati di provenienza | confronto esatto; una diversa qualificazione scientifica deve restare una differenza |

La rigenerazione cambia solo queste politiche (161 status, 13 coefficienti Joy,
4 se_var_z); restano 4298 righe. Le chiavi sono invariate. Nell'inventario Git cambia
il commit della ricognizione a `21e7210`; i riferimenti distribuiti restano gli stessi.

## Congelamento limitato e limiti

Il revisore ha verificato anche i riferimenti degli 11 file della prima fase
(tre moduli, tre input e cinque CSV di riferimento) e non ha rilevato blocchi al
congelamento di `REPRO_PHASE1_PLAN.md`. Per fig3a, HARPNUM e T_REC mancanti fanno
parte della chiave: il comparatore deve usare mancanti distinguibili da ogni
valore testuale, non eliminare quelle righe.

Le regole generali e le righe relative alla prima fase sono congelate nel commit
che introduce quel piano. Le altre tabelle restano inventariate, senza rilancio
pianificato. Il comparatore non è ancora scritto: il suo codice richiederà prove
sintetiche prima dell'esecuzione a macchina libera.

I controlli Git non certificano l'identità dell'eseguibile storico né completano
la provenienza di alberi sporchi, file ereditati e produttori non recuperati.
Il confronto dei valori non certifica da solo la resa dei PNG. Nessuna tabella è
stata dichiarata riprodotta da questa revisione.

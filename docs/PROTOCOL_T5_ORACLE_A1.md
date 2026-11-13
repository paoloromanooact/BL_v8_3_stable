# Emendamento A1 al protocollo T5-D2 (controlli oracolo)

Stato: **registrato il 2026-11-13 dopo la revisione esterna del protocollo congelato `f77d39b`
(SHA-256 `c5763829…`) e prima del commit del codice.** Il protocollo resta agli atti e invariato; A1
sostituisce o precisa solo i punti indicati. **Non cieco rispetto a una prova tecnica**: prima della
revisione il codice (non committato) era stato provato su 4 cataloghi sintetici della validazione
(scenario 7 nulla k = 0, scenario 7 effetto −0,3 k = 1, scenario 10 k = 2, scenario 1 k = 3), con la
stampa degli errori standard dei bracci per quei cataloghi. Nessuna sintesi, nessun conteggio e
nessun altro catalogo è stato visto. La prova non ha cambiato nessuna scelta di questo emendamento,
che recepisce la revisione.

## 1. Il braccio A1 diviso in due (sostituisce la riga A1 di §3)

La revisione osserva che A1, sostituendo la varianza individuale e **ristimando** la REML, mescola due
effetti. Si separano:

| Braccio | Varianza individuale | Componente temporale | Che cosa isola |
|---|---|---|---|
| **A1a** | vera (σ_i² = η̄²) | **parametri temporali di A0** (φ̂, κ̂, σ̂_x² della REML originale), non ristimati | la sola sostituzione della varianza individuale nella formula di Var(β̂) |
| **A1b** | vera | REML AR(1) **ristimata** con la v vera (l'A1 originale) | sostituzione più ristima temporale |

A1a usa i parametri della REML di A0 dello stesso catalogo; se A0 è `errore` per la funzione di
varianza, A1a usa comunque la REML di A0 solo se questa esiste, altrimenti è `errore`. A0, A2, A3 e A2'
sono invariati.

## 2. Regole di lettura (sostituisce §5, elenco «Lettura»)

Gli esiti descrivono **confronti in questi cataloghi sintetici**; ciascuno è **compatibile** con
un'ipotesi, senza attribuire una causa unica:
- **A2 vicino al riferimento (R ≈ 1, falsi verdetti nel limite) e A1a no** → compatibile con un ruolo
  principale della componente temporale (modello AR(1) e sua stima) nello scenario a salti.
- **A1a sì e A2 no** → compatibile con un ruolo principale della varianza individuale nella formula.
- **A1b diverso da A1a** → indica che la ristima temporale cambia il risultato quando cambia la
  varianza individuale: si riporta, senza attribuirla a un'interazione specifica.
- **Solo A3 vicino al riferimento** → la correzione congiunta migliora il risultato in questi cataloghi;
  il termine «interazione» non si usa senza un confronto dedicato.
- **Neppure A3** → compatibile, tra le altre, con un ruolo della forma non gaussiana della
  distribuzione (livelli ±1) rispetto al riferimento normale; non è l'unica spiegazione identificata.
Le candidate correttive elencate nel protocollo restano esempi coerenti con ciascun esito, non scelte.

## 3. Braccio A2' (precisa §3.1 e §7)

A2' si chiama **«approssimazione AR(1) secondo il criterio lag per lag specificato»**, non migliore
approssimazione: il criterio pesa ugualmente i ritardi e non tiene conto di come le covarianze si
proiettano sul contrasto che stima β. Nello scenario 10 κ è fissato al limite 0,98 mentre il generatore
ha κ = 1: il limite si riporta nei risultati. Valori ottenuti dal codice prima dell'esecuzione:
φ* = 0,9106 (scenario 7, L = 20), 0,8657 (scenario 10, L = 13).

## 4. Documentazione

Il passaggio di consegne si riallinea: protocollo congelato in `f77d39b`, emendamento A1, codice e
esecuzione successivi.

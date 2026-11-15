# Chiarimento C1 alla nota tecnica del ricalcolo degli SE degli oracoli T5-D2

Stato: **registrato il 2026-11-15 prima dell'esecuzione completa**, dopo la revisione di Codex dello script
`1e55cf8`. La nota [T5_ORACLE_SE_RECOMPUTE_NOTE.md](T5_ORACLE_SE_RECOMPUTE_NOTE.md) (`61f8884`,
SHA-256 `db53b45f…`) resta agli atti e invariata. C1 precisa i punti sotto senza cambiare l'ambito, le
tolleranze (rtol = 10⁻⁹, atol = 10⁻¹² × scala naturale) o i bracci. Non c'è nessun esito del ricalcolo:
non è ancora stato eseguito su nessun catalogo della corsa.

## 1. Controllo di rigenerazione (precisa la nota §2)

La nota §2 dice: «Il catalogo rigenerato coincide con quello della corsa se beta coincide con il raw».
È più forte del vero. Beta è una sola proiezione dei dati, e cataloghi diversi possono avere la stessa
pendenza. La coincidenza di beta con il raw (A0 e bracci ricalcolati) è un **controllo della rigenerazione**:
compatibile con lo stesso catalogo, dati semi e codice condivisi, ma non una prova dell'identità di tutte
le risposte o dei residui. La corsa originale non ha salvato un'impronta dei cataloghi, e non si può
ricostruire retroattivamente. Nei metadati il campo si chiama `beta_regeneration_check`.

## 2. Regola di tolleranza (applicazione letterale della nota §4)

La nota fissa la regola «per valore» e prende il massimo sulle componenti dei vettori. Lo script `1e55cf8`
usava invece una norma globale, max|x − y|/(atol + rtol·max|y|): era più permissiva sulle componenti
piccole ed è stata corretta. Ora:
- per ogni componente si calcola r_i = |x_i − y_i|/(atol + rtol·|y_i|) e se ne prende il massimo;
- un valore non finito da una delle due parti, forme diverse, un input vuoto o una scala non finita danno
  r = inf (rifiuto);
- con denominatore nullo passa soltanto una differenza esattamente nulla;
- i massimi di più rapporti non saltano mai un NaN.

Per i bracci validi si richiedono anche beta, SE, lo, hi e varianza finiti, con SE e varianza positivi.

## 3. Stati e classi degli errori a tre parti (precisa la nota §5)

Si registrano separatamente stato e classe di errore di tre parti: ricalcolo indipendente, produttore
ricalcolato nello stesso processo e raw. Le classi sono `varfun` e `cell`. Il produttore applica lo stesso
controllo delle varianze di cella della procedura M.
- **Errore atteso concordante** solo se tutte e tre sono `errore` con la stessa classe.
- **Inatteso** in ogni altra combinazione con almeno un errore, comprese queste:
  - errore indipendente e raw con produttore valido;
  - produttore in errore da solo;
  - classi diverse;
  - errore di A3;
  - chiave raw mancante o duplicata;
  - eccezione nel catalogo.

## 4. Insiemi esatti delle chiavi (precisa la nota §6)

L'esito richiede che coincidano esattamente gli insiemi delle chiavi (kind, scenario, effect, k, braccio),
senza duplicati:
- risultati ricalcolati: 92000 righe (32000 A2 + 32000 A3 + 28000 A2p), cioè 22 gruppi (8 per A2 e A3,
  6 per A2p);
- righe raw degli stessi bracci: stesso insieme;
- riferimento A0: le 32000 chiavi di catalogo.

Una riga mancante, duplicata, sostituita o inattesa fa fallire il controllo. Devono valere anche:
- nessuna riga di eccezione;
- nessun esito mancante;
- ok + errori attesi = 92000.

## 5. Conservazione dei fallimenti

- Lo schema delle righe è fisso anche per fallimenti totali.
- Le righe di eccezione si contano nel riepilogo.
- Una finalizzazione scrive sempre `META.json`, con gli hash disponibili e l'eventuale traccia
  dell'eccezione.
- La cartella di uscita deve essere nuova: un tentativo, riuscito o fallito, non si sovrascrive mai.
- Il processo esce con codice 0 solo se l'esito è «superato».

Per ogni braccio si conservano anche i rapporti dei singoli componenti (`r_b`, `r_v`, `r_ind`, `r_bKb`,
`r_sx2_bKb`, `r_var`) e i loro massimi nel riepilogo, per poter diagnosticare un fallimento.

## 6. Prove prima della corsa

Il selftest passa da 26 a 59 prove. Tra le nuove:
- NaN e ±inf in scalari, vettori (anche non in prima posizione) e componenti del produttore;
- alterazione di una componente piccola accanto a una grande;
- zero contro zero;
- tutte le combinazioni discordanti degli stati a tre parti;
- predicato finale con bracci mancanti, chiave duplicata, sostituita o inattesa, A0 mancante, catalogo
  mancante e costante discordante;
- fallimento totale e parziale.

Le sette sonde della revisione (`reviews/T5_D2_SE_SCRIPT_1e55cf8/` nel progetto MWO) sono state ripetute
sul codice corretto con gli stessi input costruiti a mano, e nessun difetto si riproduce più. La ricevuta
precedente (26/26) resta conservata accanto alla nuova.

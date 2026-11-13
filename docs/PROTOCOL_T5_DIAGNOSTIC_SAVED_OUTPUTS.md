# T5-D1 — diagnosi dagli output sintetici P2f già salvati

**BOZZA COMPLETA PER REVISIONE — 2026-11-13; non congelata, non eseguita.**
Protocollo diagnostico non cieco: fallimento di T5 e riassunti P2f già noti.
Prima di scrivere il codice diagnostico, congelare questa versione con un
commit dedicato e registrare il suo SHA-256 negli output. Nessuna nuova
simulazione, stima REML, risposta reale o modifica della procedura M.

## 1. Domanda e limite della risposta

Nello scenario a salti di 20 CR, il fallimento di T5 si accompagna a bias
della pendenza, scala dell'errore standard inadeguata, code non normali o
dipendenza tra errore di stima e SE? Quali aspetti differiscono dai controlli?

Il punto di partenza noto è 3,35% di falsi verdetti sotto la nulla e, a
−0,3·η̄, copertura 96,1% e coda inferiore 2,3%. T5 resta descrittivo.
Questo protocollo organizza la diagnosi, non verifica nuovamente
l'accettazione di M e non cerca soglie con cui farla passare.

I dati salvati non contengono separatamente la varianza individuale e quella
temporale della pendenza, né la covarianza vera proiettata sul contrasto T5.
La dispersione empirica delle pendenze è osservabile sui cataloghi sintetici;
non identifica da sola quale componente del modello sia responsabile.

## 2. Input e provenienza

Elenco chiuso, con SHA-256 dei byte distribuiti e blob Git, in
[T5_DIAGNOSTIC_INPUTS_SHA256.csv](T5_DIAGNOSTIC_INPUTS_SHA256.csv).
Gli input di analisi sono i quattro `results/P2F/VALIDATION_*` e
`POST_CHECKS.csv`; protocollo P2f e due moduli Python sono riferimenti di
definizione, da leggere senza importarli o eseguirli. Non leggere catalogo
P1, pickle del disegno, FITS o `REAL_T3*`/risposte reali.

Provenienza originale attesa dei quattro output: commit
`5c3b664bb3e6bbdddd8a9502801163ed9873ce49`, `git_dirty = 0`, SHA del protocollo
P2f `8f030010ddedb28131a79ea72edd2fe6077c9a04dd236854a86fb170f1cb3ab1`.
Il commit del nuovo script diagnostico sarà distinto. `POST_CHECKS.csv` ha
provenienza propria: verificare i suoi hash degli input e gli esiti, senza
richiedere che il suo commit coincida con quello della simulazione. L'etichetta
storica «pilota» nei controlli è già dichiarata e non viene riscritta.

Trattare la stringa `kind = null` come testo, non come valore mancante
(con pandas: `keep_default_na=False`). Conversione numerica esplicita;
nessuna conversione di stringhe `False` con `bool(stringa)`. Conservare gli
errori originali; non completare campi vuoti con zero.

## 3. Campione diagnostico fissato

Solo T5, con gruppi separati per `(kind, scenario, effect)`:

| Tipo | Scenari | Effetto frazionario | k | Gruppi / righe |
|---|---|---|---|---|
| Nulla | 0, 1, 2, 7, 10 | 0 | 0…9999 | 5 / 50000 |
| Effetto | 1, 2, 7 | −0,1; −0,2; −0,3; −0,35 | 0…1999 | 12 / 24000 |

Totale: **17 gruppi e 74000 righe**, comprese quelle con `verdict = errore`.
Verificare l'insieme esatto delle chiavi `(test, kind, scenario, effect, k)`;
normalizzare gli effetti decimali per le chiavi senza arrotondare i risultati.
Nessun altro scenario, sottocampione o effetto viene aggiunto dopo la lettura.

0 è senza componente temporale; 1 e 2 sono AR(1) con φ 0,5 e 0,9 e κ 0;
7 ha salti di 20 CR separati fra emisferi. 10 ha salti di 13 CR condivisi:
cambia due fattori insieme, quindi è solo un confronto descrittivo e non
isola né la durata dei salti né la dipendenza emisferica. Semi distinti fra
scenari ed effetti: niente confronti appaiati, pooling o test su T3.

## 4. Scala, denominatori e code

Usare η₀ = **3,56·10⁻²⁵ G/Mx**, costante del generatore, non ristimata:
b = β̂/η₀, b₀ = β_vero/η₀, s = SE/η₀, r = b−b₀, z = r/s.
Verificare `beta_true/η₀ = effect`. `stat` salvata vale β̂/SE, quindi sotto
effetto **non** coincide con z: non usarla per diagnosticare la copertura.

Per ogni gruppo, N è il numero di tentativi; m = N−errori. Frequenze di
verdetti, copertura e code hanno denominatore **N**, come P2f. Gli errori non
sono falsi verdetti sotto la nulla; sotto effetto sono non copertura. Bias,
dispersioni e quantili usano solo le m righe con esito numerico valido,
dichiarando sempre m/N: sono condizionati al successo della procedura.

| Conteggio | Definizione, con le convenzioni storiche P2f |
|---|---|
| Coperto | lo ≤ β_vero ≤ hi |
| `below`, coda inferiore | lo > β_vero, ossia z > q: il parametro vero è sotto l'intervallo |
| `above`, coda superiore | hi < β_vero, ossia z < −q |
| Falso verdetto sotto nulla | `supportato` + `opposto`; rispettivamente β̂ < −q·SE e β̂ > q·SE |

q = Φ⁻¹(0,9875), calcolato a precisione completa. Sotto effetto contare anche
`supportato`, ma chiamarlo rilevamento, non falso verdetto. L'identità
coperto + below + above + errore = N deve valere in ogni gruppo.

## 5. Analisi deterministiche, senza ricampionamento

Tutti i gruppi ricevono le stesse analisi. Nessun nuovo seme, bootstrap,
permutazione, ottimizzazione, fit della risposta o confronto fra metodi.

**A. Bias e scala.** Sulle m righe valide riportare media r, suo errore
Monte Carlo √(V_emp/m), V_emp = Σ(r−media r)²/(m−1), MSE = media(r²),
media(s²), mediana s e rapporto R = media(s²)/V_emp. Controllare
MSE = ((m−1)/m) V_emp + (media r)². Non sostituire media(s²) con il
quadrato della mediana di SE. R è un riassunto diagnostico condizionato
al successo, non una stima separata della varianza temporale.

Se m<5 o V_emp≤0, la diagnostica standardizzata non è definita: segnare
il controllo fallito e fermarsi, senza inventare una varianza sostitutiva.

**B. Forma e code.** Riportare media e deviazione standard di z. Confrontare
i quantili di z con quelli normali e quelli di u = (r−media r)/√V_emp
con gli stessi riferimenti, per probabilità fissate
`0.005, 0.0125, 0.025, 0.05, 0.5, 0.95, 0.975, 0.9875, 0.995`.
Quantili campionari con interpolazione lineare (`method='linear'`). u separa
descrittivamente la forma marginale di r da bias e scala empirica; non è
una nuova statistica validata o un controllo oracolo. Per le frequenze su N
riportare √(f(1−f)/N), con l'ipotesi dei cataloghi indipendenti entro gruppo;
non interpretare questo errore come incertezza sul processo solare reale.

**C. Ruolo di SE.** Ordinare le m righe per s crescente, con k come spareggio,
e dividerle in cinque blocchi con `array_split`. Per blocco: m, estremi e
mediana di s, media r, media |r|, media(s²), MSE e quote z>q / z<−q sulle
righe del blocco. Registrare anche la correlazione di Spearman fra |r| e s;
se una variabile è costante, indicare non definita. Il raggruppamento per
SE e il rapporto z contengono dipendenze matematiche: non usarli come prova
causale del motivo dei falsi verdetti.

**D. Parametri.** Sulle righe valide: media, mediana, p10 e p90 di φ, κ,
σ̂_x²/η₀², `var_b`, `var_a−2 log η₀`, `n_varfun`, `n_zero_residuals`;
distribuzione di `n_valid_starts` e quota `sigma_x_at_lower`.
Sono diagnostiche dei parametri stimati, non confronti con la varianza vera
della pendenza. Non attribuire allo scenario 7 un «φ vero» AR(1).

## 6. Prodotti chiusi

Directory nuova `results/T5_DIAGNOSTIC/`, senza sovrascrivere output P2f:

- `T5D_CHECKS.csv`: controlli obbligatori, osservato, atteso, passed;
- `T5D_GROUPS.csv`: 17 righe, conteggi/code e risultati A/B;
- `T5D_QUANTILES.csv`: 153 righe, quantili di z/u e riferimento normale;
- `T5D_SE_QUINTILES.csv`: 85 righe, risultati C;
- `T5D_NUISANCE.csv`: 17 righe, risultati D;
- `T5D_META.json`: commit/albero dello script, versione Python/librerie,
  hash del protocollo e della lista input, hash e provenienza degli input,
  hash degli output, ora iniziale/finale e gruppi previsti.

Ogni CSV registra anche commit diagnostico, albero pulito, SHA-256 del
protocollo congelato e della lista input. La provenienza originale resta
separata in META. Non modificare i file originali per aggiungere metadati.

Tre figure in `figures/T5_DIAGNOSTIC/`: bias e scala per i 17 gruppi;
quantili z/u, con nulla ed effetti distinti; code per quintile di SE.
Ogni figura deve poter essere ricostruita soltanto dai CSV diagnostici.
Relazione `docs/T5_DIAGNOSTIC_RESULTS.md`, solo dopo i controlli. Nessun
nuovo file `VALIDATION_DECISION` o esito di validazione.

## 7. Controlli obbligatori prima dell'interpretazione

1. Prima degli input scientifici, prove del nuovo codice su piccole tabelle
   costruite a mano: stringa null, righe errore, code e uguaglianza agli estremi,
   z sotto effetto, scala η₀, bias/varianza/MSE, spareggi dei quintili,
   correlazione non definita, duplicati/chiavi mancanti e hash non corrispondenti.
   Devono passare sullo stesso commit pulito usato per l'analisi.
2. Hash della lista input e tutti gli hash/blobs dei riferimenti; tutti gli
   esiti del controllo P2f superati e legati ai quattro output attuali;
   provenienza originale corretta, distinta da quella diagnostica.
3. Schema e chiavi esatte, 304000 righe nel raw completo e 74000 nel campione;
   i 17 gruppi hanno le numerosità fissate. Nessuna eliminazione silenziosa.
4. Per gli esiti numerici: β_vero, β̂, SE, estremi e parametri necessari finiti,
   SE>0; `stat = β̂/SE`; semi-intervalli entrambi uguali a q. Verifiche float
   normalizzate con tolleranza assoluta 10⁻¹², relativa 10⁻⁹. Conteggi, flag e
   verdetti esatti. Una riga dichiarata valida ma non finita blocca l'analisi.
5. Ricalcolare verdetti, copertura e code dagli estremi, confrontandoli con
   le colonne del raw. Confrontare conteggi e frequenze con i riassunti P2f
   dei gruppi selezionati; verificare separatamente che T5 resti non validato
   nella decisione storica. Non ricalcolare l'accettazione usando soli 17 gruppi.
6. Controllare identità MSE, partizione in quintili e numeri di righe degli
   output; nessun input o file scientifico originale modificato.

Esiti mancanti o discordanti: fermarsi con codice non zero e conservare il
rapporto dei controlli. Nessuna interpretazione dei grafici prima dei controlli.

## 8. Regole di lettura e arresto

| Risultato osservabile | Lettura permessa; limite |
|---|---|
| Bias visibile rispetto all'errore Monte Carlo | Quantificare lo spostamento; non attribuirlo senza controllo a un meccanismo del fit. |
| R<1 e dispersione di z maggiore del riferimento | Coerente con SE mediamente insufficienti; non separa componente individuale, temporale e loro stime. |
| Quantili di u lontani dai riferimenti normali | La sola correzione di scala potrebbe non bastare; non prova un errore del generatore. |
| Code concentrate nei quintili con SE piccolo | Coerente con un ruolo della stima di SE; in parte dipendenza algebrica, non prova causale. |
| Scenario 10 diverso da 7 | Descrivere la differenza; due fattori cambiati impediscono un'attribuzione univoca. |
| Quadro misto o controlli poco discriminanti | Diagnosi incompleta: non scegliere a posteriori la spiegazione più favorevole. |

Riportare sempre risultati compatibili e contrari alle ipotesi, senza p-value
o nuove soglie di accettazione. Le 17 analisi sono esplorative e molteplici;
uno scarto di due errori Monte Carlo non diventa un verdetto confermativo.

Una sola esecuzione analitica dopo le prove del codice e i controlli input.
Una correzione necessaria richiede nota dell'errore, conservazione RUN1 e
registrazione della correzione prima del nuovo confronto, senza cambiare
gruppi o regole. Terminati i prodotti previsti, fermarsi: nessuna ricerca
automatica di una procedura sostitutiva.

Per separare scala/forma della componente temporale e rumore individuale
potrebbero servire covarianze del generatore e controlli oracolo: **piano
successivo distinto**, prima di rigenerazioni o nuovi calcoli di quel tipo.
Gli output e i semi P2f sono materiale di sviluppo T5. Una procedura modificata
richiede un nuovo protocollo, semi indipendenti e scenari a salti ancora
decisivi. Questo passo non valida T5, non tocca il risultato reale T3 e non
avvia la morfologia o MDI.

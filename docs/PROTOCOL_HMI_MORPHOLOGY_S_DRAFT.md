# Morfologia della popolazione S — bozza di piano

**BOZZA NON CONGELATA, revisione 3 — 2026-11-16: opzione ridotta**, proposta per la revisione di Codex dopo la
decisione dell'utente di contenere il costo delle letture. La revisione 2 (`85cda04`, 281 schede in due
passaggi) recepiva la revisione di Codex della revisione 1 (`9b080c2`) e resta l'alternativa completa (§8).
Le differenze della revisione 3 sono elencate in §11. Nessuna scheda
generata, nessun campione estratto, nessuna lettura. I conteggi di §3 vengono solo dal disegno (attività,
flusso, appartenenza alle HARP già lette); non usano tilt, S_BL per record, verdetti o classi.
**Non cieco**: domanda, risultati T3/T5 e lo studio morfologico precedente sono noti ai lettori.

## 1. Origine e domanda

Lo studio morfologico precedente (`docs/MORPHOLOGY_RESULTS.md`; protocollo `21dfe6d`, A1 `67f5e1a`, A2
`9a4c4cd`) ha soddisfatto la sua regola operativa (§7: classe B ≥ 10 % di Σ|S_BL| in 24S e 25N, accordo
24/30, U ≤ 3/30), **esattamente alla soglia** per l'accordo. L'unico esito consentito è proporre un piano
distinto per uno studio rappresentativo di S. Le 120 HARP lette erano una selezione fissata (dominanti e
controlli) e non stimano la prevalenza in S.

Domanda, descrittiva: **nella popolazione S su cui è stato applicato T3 (2485 record primari HARP, uno per
HARP, cicli 24–25), quanto spesso la misura a due centroidi riassume una configurazione senza una coppia
bipolare dominante (classi B e D), e queste frequenze cambiano con l'attività Â?**

Che cosa può dare: una descrizione di **che cosa rappresentano i tilt misurati** in S. Da solo **non
stabilisce se la morfologia altera la pendenza di T3** (§6).

## 2. Che cosa lo studio non fa

- Nessuna esclusione di HARP, nessuna nuova pendenza, nessun rilancio di T3 o T5, anche su sottoinsiemi di
  classe; nessun confronto di tilt, Hale o S_BL fra classi. T3 resta «non deciso», T5 descrittivo.
- Nessuna modifica di P1, dei flag o dei file e delle letture bloccate dello studio precedente.
- Le classi non sono validate fisicamente: B non prova più regioni fisiche, D non prova un errore.
- Non è un prerequisito dell'estensione MDI: è un approfondimento HMI sull'interpretazione della misura.
  Il percorso più diretto verso un nuovo risultato sul quenching resta T5; MDI avanza separatamente.

## 3. Popolazione, strati e campione

**Popolazione.** S ricostruito come in P2f (`run_p2.samples(cat)["S"]` con `add_activity`, Â finita):
N = 2485 record, 2485 HARP distinte; (24, N) 677, (24, S) 581, (25, N) 609, (25, S) 618. Br e bitmap di tutti
i 2485 record sono già in locale (`data/sharp/fits`): nessun download.

**Strato certo K (101 record, probabilità di inclusione 1).** Le HARP di S già viste nello studio precedente
(75 delle 90 nuove e 26 di 25S, fra cui 10 schede di riferimento). Coprono il 16,3 % di ΣΦ e il 30,8 % di
Σ|S_BL| di S, concentrate ad alta attività e alto flusso, quindi non si escludono. **Opzione ridotta:**
- le **75** lette con le regole A2 nello studio precedente **conservano la classe primaria bloccata del
  lettore 1** (file e hash dello studio precedente, invariati);
- le **26** di 25S (10 schede di riferimento e 16 con sole etichette storiche) si **rileggono** nel nuovo
  formato, mescolate alle schede nuove.

**Limite dichiarato** (revisione di Codex): il riuso introduce una differenza di sessione e di taratura
concentrata ad alta attività (le 75 stanno soprattutto negli strati ad Â alta e Φ alto), che può contribuire
a un'associazione classe–attività. Se ne tiene conto in lettura (§6) e con la sensibilità che esclude K (§5).
Le 10 schede di riferimento restano nella popolazione (appartengono a S), con l'esposizione dichiarata: la loro
lettura non è indipendente dalla taratura, e il loro accordo fra lettori non è una verifica indipendente della
taratura.

**Strati campionati h = 1…6.** Le altre 2384 HARP, divise per terzili di Â su S (tagli 1,1063 e 1,7380) ×
Φ sotto/sopra la mediana su S (6,155·10²¹ Mx). N_h è la **numerosità campionabile**, cioè senza le 101 di K;
le quote di ΣΦ e Σ|S_BL| sono riferite all'intero S e includono la parte in K:

| h | Â | Φ | N_h campionabile | in K | Quota ΣΦ | Quota Σ\|S_BL\| |
|---|---|---|---|---|---|---|
| 1 | basso | < mediana | 495 | 4 | 4,6 % | 3,7 % |
| 2 | basso | ≥ mediana | 318 | 9 | 16,0 % | 16,2 % |
| 3 | medio | < mediana | 400 | 3 | 3,8 % | 2,9 % |
| 4 | medio | ≥ mediana | 395 | 29 | 27,5 % | 27,8 % |
| 5 | alto | < mediana | 338 | 2 | 3,1 % | 2,7 % |
| 6 | alto | ≥ mediana | 438 | 54 | 45,1 % | 46,7 % |

**Allocazione.** n_h = 30 per strato, estrazione senza reimmissione fra le N_h, seme dedicato: **180 HARP
nuove**. Con le 26 riletture di K, **206 schede** per il lettore 1. Nessuno strato aggiuntivo per il decile superiore
di Φ: richiederebbe prima una valutazione della precisione basata sulle sole covariate.

## 4. Schede e lettura (regole A2, un solo passaggio, lotti a contesto nuovo)

- Stesso generatore del protocollo precedente: due viste fisse (±1500 G e ±300 G), contorno della maschera
  P1 (bitmap ≥ 33); nessun numero, flag, NOAA, data, gruppo o HARPNUM; dimensione e risoluzione fisse.
  **Solo la versione mappa**: nessuna versione con i centroidi, nessun indicatore C, nessun contatto al bordo
  (opzione ridotta; C era secondario e fuori dalle stime principali).
- Codici anonimi e ordine casuale delle 206 schede, semi dedicati; corrispondenza codice–HARPNUM in un file
  privato con hash, non stampata, non data ai lettori prima del blocco.
- Classi A2 (A, B, D, U con alternative scritte) e motivazione visiva breve.
- **Lettore 1 in lotti.** La lettura è divisa in **9 lotti** di circa 23 schede, assegnate a caso (seme
  dedicato), quindi ogni lotto mescola strati e strato certo. Ogni lotto è letto da una **sessione nuova dello
  stesso modello** (Claude, modello e versione registrati), così che ogni immagine si paga una volta sola.
  Ogni sessione riceve le stesse istruzioni fisse: il testo delle regole A2, una sintesi testuale della
  taratura (`docs/MORPHOLOGY_CALIBRATION_COMPARISON.md`) e **4 schede di esempio con la classe concordata**
  (R02 A, R06 B, R07 B, R05 D), le stesse per tutti i lotti. Il lotto e la sessione si registrano per scheda.
- **Taratura** (lotto 0, prima dei 9): una sessione nuova legge le 11 schede di riferimento senza classi e
  registra le differenze rispetto alla taratura precedente, come nello studio precedente.
- **Coerenza interna**: 2 schede per lotto ricompaiono, con codice diverso, in un altro lotto (18 duplicati,
  seme dedicato). Si riporta l'accordo fra le due letture dello stesso lettore; per le stime vale la lettura
  del lotto con numero minore (regola fissata ora). È una misura della variabilità fra sessioni, non della
  validità.
- **Lettore 2**: la sessione del revisore esterno, stesse istruzioni ed esempi, **54 schede nuove**: 8 per
  strato fra le 30 estratte e 6 fra le 26 riletture di K, estratte senza reimmissione con seme dedicato, ordine
  separato. Per le 75 riusate si usano le **25 doppie letture già esistenti** dello studio precedente che
  cadono in S (lettore 2 dello studio precedente, regole A2), senza nuove letture.
- Esposizioni dichiarate come nel protocollo precedente: la sessione principale ha scritto il generatore e
  conosce la corrispondenza; le sessioni di lotto ricevono solo le immagini dei loro codici e l'istruzione di
  non aprire altri file del progetto, che non è un vincolo tecnico. Nessuno dei lettori è cieco al progetto.
- Blocco con hash di ogni file di lettura appena scritto, prima di qualunque collegamento ai metadati.

## 5. Grandezze stimate e formule (fissate prima)

Notazione: classe k ∈ {A, B, D, U} e gruppo B+D; I_ik = 1 se il lettore 1 assegna k al record i; s_h il
campione dello strato h; pesi del disegno w_i = 1 in K, w_i = N_h/n_h in s_h; x_i = Φ_i oppure |S_BL,i|.

- **E1, principale: prevalenza per conteggio.**
  p̂_k = [Σ_{i∈K} I_ik + Σ_h (N_h/n_h) Σ_{i∈s_h} I_ik] / N, con N = 2485 = |K| + Σ_h N_h.
- **E2 ed E3, complementari: quote pesate per Φ (pesi della WLS di T3) e per |S_BL|** (stimatore a
  rapporto): q̂_k = [Σ_K x_i I_ik + Σ_h (N_h/n_h) Σ_{s_h} x_i I_ik] / [Σ_K x_i + Σ_h (N_h/n_h) Σ_{s_h} x_i].
  Il denominatore stima il totale X di S, che è noto: si riporta anche il rapporto fra denominatore stimato e
  X come controllo, senza sostituirlo.
- **E4: per terzile di Â**, le stesse formule ristrette ai due strati del terzile e alla parte di K che vi
  cade (N_t = |K_t| + N_h + N_h'): B, D e B+D **separatamente**, per conteggio e pesate per Φ, e la differenza
  fra terzile alto e basso. Con D rara si riportano numerosità e intervalli ampi; B+D risponde a «manca una
  coppia dominante» ma non indica un unico meccanismo.
- **E5**: per ciclo × emisfero, solo descrittivo.
- **Seconda lettura.** Sulle 54 nuove più le 25 esistenti: matrice A/B/D/U non pesata con denominatori, accordo
  complessivo, disaccordi specifici su B, D e U, riportati anche separatamente per le tre parti (strati, 26
  riletture, 75 riusate). Accordo pesato per S con le probabilità di inclusione: π_i = 8/N_h negli strati
  (pesi N_h/8); π_i = 6/26 nelle riletture (peso 26/6); per le 25 coppie esistenti le probabilità del disegno
  dello studio precedente, 7/20 per le dominanti e 3/10 per i controlli del gruppo (pesi 20/7 e 10/3). Le 25
  coppie esistenti vengono da sessioni e tempi diversi dalle nuove: si dichiara. Nessuna soglia automatica di
  affidabilità: un accordo alto può dipendere dalla prevalenza di una sola classe.
- **Sensibilità al riuso.** E1–E4 ricalcolate (i) sulle sole 2384 HARP campionabili, senza K, e (ii) con le 75
  riusate al posto delle letture del lettore 2 dove esistono; servono a vedere quanto la mescolanza di sessioni
  in K pesa sull'associazione con l'attività.
- **Sensibilità ai lettori.** (a) Sensibilità sulle doppie letture: ricalcolo di E1–E4 contando B solo quando
  entrambi assegnano B nelle 79 coppie (classe del lettore 1 altrove); è una sensibilità alle doppie letture
  disponibili, **non** una stima della quota di B concordata in S. (b) Quota di B concordata in S, stimata
  con i pesi del sottocampione del lettore 2: p̂_BB = Σ_{i∈79} (1/π_i) I(B, B)_i / N, con intervallo ampio.
- **U**: categoria propria; si riportano anche i due casi estremi (tutte le U come B, nessuna come B).

**Incertezza.** Due fonti, distinte:
- **campionamento**: solo negli strati h; K non contribuisce alla varianza di campionamento della stima del
  lettore 1. Per E1 varianza analitica stratificata con correzione per popolazione finita,
  V(p̂_k) = Σ_h N_h² (1 − n_h/N_h) s²_hk / n_h / N²; per tutte le stime bootstrap stratificato **rescaled**
  di Rao–Wu–Yue (1992) che rispetta l'estrazione senza reimmissione (m_h = n_h − 1 per strato, pesi
  riscalati con la correzione per popolazione finita), 9999 repliche, seme dedicato, intervalli percentili al
  95 %. Se si usasse il bootstrap con reimmissione semplice, l'approssimazione va dichiarata (frazioni di
  campionamento 6–9 %);
- **classificazione**: anche K ha incertezza di classificazione; non entra negli intervalli e si descrive con
  la seconda lettura e con i duplicati fra lotti (sopra e §4).

## 6. Precisione e lettura prevista (nessuna soglia di decisione)

Precisione indicativa per conteggio, quota vera 0,3: errore standard circa 0,08 nello strato (n = 30), circa
0,06 per terzile, circa 0,08–0,09 per la differenza fra terzile alto e basso (senza considerare K, che la
riduce). Una semilarghezza di 15–20 punti **non** equivale a un'alta probabilità di rilevare una differenza di
quella grandezza: la potenza per una tale differenza sarebbe molto più bassa.

Risultati espressi come «in S, circa X % dei record (Y % di ΣΦ) è classificato B, con intervallo …; nel
terzile alto di attività la quota è … contro … nel basso». **Nessuna regola automatica.** Limiti di lettura:
- una prevalenza di B o D crescente con l'attività **non dimostra** che il tilt sia attenuato: potrebbero
  cambiare dispersione, segno o altro;
- l'assenza di associazione **non esclude** un effetto della morfologia sulla misura;
- con l'opzione ridotta, un'associazione che compaia solo includendo le 75 riusate va letta come possibile
  effetto di sessione, non della popolazione;
- un'eventuale associazione motiverebbe al più un piano separato sulla misura del tilt; non autorizza
  correzioni di T3.

## 7. Costo e sequenza

- Generazione: 206 coppie di FITS locali, 206 immagini (solo mappa); minuti su un processo, con `nice`,
  **dopo** la fine della griglia T5 in corso.
- Lettura, lettore 1: 11 di taratura + 206 + 18 duplicati + 4 esempi per ciascuno dei 9 lotti, circa **270
  immagini** lette una volta sola. Un'immagine (1540 × 467 pixel) vale circa 1000 token in ingresso: con
  istruzioni e risposte, **circa 0,3 milioni di token** (stima grezza, da verificare sul lotto di taratura; se
  la taratura supera di molto la stima, ci si ferma e si riporta prima dei 9 lotti). Lettore 2: circa 60
  immagini.
- Sequenza: revisione di questa bozza → congelamento con hash, semi e allocazione → script delle schede e
  delle verifiche automatiche → taratura → 9 lotti bloccati → seconda lettura → collegamento ai metadati e
  stime → rapporto. Nessun push senza richiesta.

## 8. Opzione ridotta e alternativa completa

**Proposta (revisione 3): opzione ridotta**, 206 schede in un solo passaggio, lettura in lotti a contesto
nuovo, riuso delle 75 letture A2 bloccate, circa 0,3 milioni di token per il lettore 1. Rinunce dichiarate:
nessun indicatore C; mescolanza di sessioni in K ad alta attività; variabilità fra sessioni di lotto (misurata
con i duplicati). **Alternativa completa (revisione 2)**: 281 schede in due passaggi, rilettura delle 101 note,
circa 1–2 milioni di token. Precisione delle stime negli strati uguale nelle due opzioni (30 per strato).

## 9. Semi proposti

2026111601 estrazione degli strati; 2026111602 codici e ordine del lettore 1; 2026111603 sottocampione del
lettore 2 negli strati; 2026111604 ordine del lettore 2; 2026111605 bootstrap; 2026111606 assegnazione ai lotti
e duplicati; 2026111607 sottocampione del lettore 2 fra le 26 riletture. Disgiunti dai semi morfologici precedenti
(2026111301–2026111303) e dagli intervalli in `P.USED`.

## 10. Revisione di Codex della revisione 1 (2026-11-16), recepita

1. 30 per strato, sei strati, prevalenza per conteggio come risultato principale; Φ e |S_BL| complementari;
   nessuno strato per il decile superiore senza una valutazione basata sulle covariate (§3, §5).
2. Rilettura di tutte le 101 HARP note, file storici intatti; il riuso resta un'alternativa dichiarata (§3, §8).
3. Le 10 schede di riferimento restano nella popolazione, con esposizione dichiarata (§3, §4).
4. Seconda lettura distribuita anche sulle 101: 12 da K e 8 per strato; matrice, accordo e disaccordi
   specifici con pesi coerenti con l'estrazione; nessuna soglia automatica del 70 % (§4, §5).
5. D riportata separatamente anche per attività, accanto a B e B+D (§5).
6. Non prerequisito per MDI; T5 percorso più diretto (§2).
Precisazioni tecniche: numerosità campionabili N_h nei pesi (495, 318, 400, 395, 338, 438) e formula del
denominatore (§3, §5); bootstrap coerente con l'estrazione senza reimmissione e distinzione fra incertezza di
campionamento e di classificazione (§5); variante con due B come sensibilità, distinta dalla stima pesata
della quota concordata (§5); semilarghezza diversa dalla potenza e limiti di interpretazione (§6).

## 11. Revisione 3: opzione ridotta (2026-11-16)

Su richiesta dell'utente, per contenere il costo delle letture, rispetto alla revisione 2:
1. riuso delle 75 classi primarie A2 bloccate del lettore 1; rilettura delle sole 26 di 25S (206 schede invece
   di 281), con il limite di sessione dichiarato e due sensibilità (§3, §5, §6);
2. un solo passaggio, sola mappa: niente indicatore C né contatto al bordo (§4);
3. lettura del lettore 1 in 9 lotti a contesto nuovo con istruzioni ed esempi fissi, lotto di taratura,
   18 duplicati fra lotti per la coerenza interna (§4);
4. lettore 2 su 54 schede nuove (8 per strato e 6 fra le 26 riletture) più le 25 doppie letture esistenti fra le
   75 riusate, con pesi del disegno per ciascuna parte (§4, §5);
5. costo stimato circa 0,3 milioni di token per il lettore 1, con arresto se la taratura lo smentisce (§7).
6. lo strato certo si chiama ora K, per non confonderlo con l'indicatore C dei centroidi.
Restano invariati: popolazione, strati, N_h, 30 per strato, formule degli stimatori, bootstrap, limiti di
lettura e il fatto che lo studio non è un prerequisito per MDI.

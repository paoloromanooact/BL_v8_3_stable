# Morfologia della popolazione S — bozza di piano

**BOZZA NON CONGELATA, revisione 2 — 2026-11-16**, dopo la revisione di Codex della revisione 1 (`9b080c2`),
recepita (§10). Resta da decidere il costo delle letture (§8) prima del congelamento. Nessuna scheda
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

**Strato certo C (101 record, probabilità di inclusione 1).** Le HARP di S già viste nello studio precedente
(75 delle 90 nuove e 26 di 25S, fra cui 10 schede di riferimento). Coprono il 16,3 % di ΣΦ e il 30,8 % di
Σ|S_BL| di S, concentrate ad alta attività e alto flusso, quindi non si escludono. **Si rileggono tutte e
101** nel nuovo formato e nella stessa sessione delle nuove, mescolate con esse; i file e le letture storiche
restano intatti e non si usano per le stime. Motivo: riusare 75 classificazioni di un'altra sessione
introdurrebbe una differenza di sessione e di taratura concentrata ad alta attività. Le 10 schede di
riferimento restano nella popolazione (appartengono a S), con l'esposizione dichiarata: la loro lettura non è
indipendente dalla taratura, e il loro accordo fra lettori non è una verifica indipendente della taratura.

**Strati campionati h = 1…6.** Le altre 2384 HARP, divise per terzili di Â su S (tagli 1,1063 e 1,7380) ×
Φ sotto/sopra la mediana su S (6,155·10²¹ Mx). N_h è la **numerosità campionabile**, cioè senza le 101 di C;
le quote di ΣΦ e Σ|S_BL| sono riferite all'intero S e includono la parte in C:

| h | Â | Φ | N_h campionabile | in C | Quota ΣΦ | Quota Σ\|S_BL\| |
|---|---|---|---|---|---|---|
| 1 | basso | < mediana | 495 | 4 | 4,6 % | 3,7 % |
| 2 | basso | ≥ mediana | 318 | 9 | 16,0 % | 16,2 % |
| 3 | medio | < mediana | 400 | 3 | 3,8 % | 2,9 % |
| 4 | medio | ≥ mediana | 395 | 29 | 27,5 % | 27,8 % |
| 5 | alto | < mediana | 338 | 2 | 3,1 % | 2,7 % |
| 6 | alto | ≥ mediana | 438 | 54 | 45,1 % | 46,7 % |

**Allocazione.** n_h = 30 per strato, estrazione senza reimmissione fra le N_h, seme dedicato: **180 HARP
nuove**. Con le 101 di C, **281 schede** per il lettore 1. Nessuno strato aggiuntivo per il decile superiore
di Φ: richiederebbe prima una valutazione della precisione basata sulle sole covariate.

## 4. Schede e lettura (come lo studio precedente, regole A2)

- Stesso generatore del protocollo precedente: due viste fisse (±1500 G e ±300 G), contorno della maschera
  P1 (bitmap ≥ 33), versione con soli marker dei centroidi; nessun numero, flag, NOAA, data, gruppo o
  HARPNUM; dimensione e risoluzione fisse.
- Codici anonimi e ordine casuale delle 281 schede, semi dedicati; corrispondenza codice–HARPNUM in un file
  privato con hash, non stampata, non data ai lettori prima del blocco.
- Classi A2 (A, B, D, U con alternative scritte); due passaggi: prima la mappa e la classe primaria, poi,
  dopo il blocco delle primarie di entrambi i lettori, l'indicatore C e il contatto al bordo. Le classi non
  cambiano dopo aver visto i marker.
- **Taratura**: le 11 schede di riferimento già usate, rilette da ciascun lettore prima delle 281;
  differenze registrate. Le 10 di riferimento in S si leggono di nuovo, anonime, fra le 281.
- **Lettore 1**: la sessione dell'agente (Claude; modello registrato), tutte le 281. **Lettore 2**: la
  sessione del revisore esterno, **60 schede**: 12 estratte senza reimmissione fra le 101 di C e 8 fra le 30
  di ciascuno strato campionato; seme dedicato, ordine separato. Esposizioni dichiarate come nel protocollo
  precedente; nessuno dei due è cieco al progetto.
- Blocco con hash di ogni file di lettura prima di mostrare marker, etichette altrui o numeri.

## 5. Grandezze stimate e formule (fissate prima)

Notazione: classe k ∈ {A, B, D, U} e gruppo B+D; I_ik = 1 se il lettore 1 assegna k al record i; s_h il
campione dello strato h; pesi del disegno w_i = 1 in C, w_i = N_h/n_h in s_h; x_i = Φ_i oppure |S_BL,i|.

- **E1, principale: prevalenza per conteggio.**
  p̂_k = [Σ_{i∈C} I_ik + Σ_h (N_h/n_h) Σ_{i∈s_h} I_ik] / N, con N = 2485 = |C| + Σ_h N_h.
- **E2 ed E3, complementari: quote pesate per Φ (pesi della WLS di T3) e per |S_BL|** (stimatore a
  rapporto): q̂_k = [Σ_C x_i I_ik + Σ_h (N_h/n_h) Σ_{s_h} x_i I_ik] / [Σ_C x_i + Σ_h (N_h/n_h) Σ_{s_h} x_i].
  Il denominatore stima il totale X di S, che è noto: si riporta anche il rapporto fra denominatore stimato e
  X come controllo, senza sostituirlo.
- **E4: per terzile di Â**, le stesse formule ristrette ai due strati del terzile e alla parte di C che vi
  cade (N_t = |C_t| + N_h + N_h'): B, D e B+D **separatamente**, per conteggio e pesate per Φ, e la differenza
  fra terzile alto e basso. Con D rara si riportano numerosità e intervalli ampi; B+D risponde a «manca una
  coppia dominante» ma non indica un unico meccanismo.
- **E5**: per ciclo × emisfero, solo descrittivo.
- **Seconda lettura.** Sulle 60: matrice A/B/D/U non pesata con denominatori, accordo complessivo, disaccordi
  specifici su B, D e U; accordo pesato per S con le probabilità di inclusione del sottocampione
  (π_i = 12/101 in C, π_i = (n_h/N_h)(8/n_h) = 8/N_h negli strati), cioè pesi 101/12 e N_h/8. Nessuna soglia
  automatica di affidabilità: un accordo alto può dipendere dalla prevalenza di una sola classe.
- **Sensibilità ai lettori.** (a) Sensibilità sulle doppie letture: ricalcolo di E1–E4 contando B solo quando
  entrambi assegnano B nelle 60 (classe del lettore 1 altrove); è una sensibilità alle doppie letture
  disponibili, **non** una stima della quota di B concordata in S. (b) Quota di B concordata in S, stimata
  con i pesi del sottocampione del lettore 2: p̂_BB = Σ_{i∈60} (1/π_i) I(B, B)_i / N, con intervallo ampio.
- **U**: categoria propria; si riportano anche i due casi estremi (tutte le U come B, nessuna come B).

**Incertezza.** Due fonti, distinte:
- **campionamento**: solo negli strati h; C non contribuisce alla varianza di campionamento della stima del
  lettore 1. Per E1 varianza analitica stratificata con correzione per popolazione finita,
  V(p̂_k) = Σ_h N_h² (1 − n_h/N_h) s²_hk / n_h / N²; per tutte le stime bootstrap stratificato **rescaled**
  di Rao–Wu–Yue (1992) che rispetta l'estrazione senza reimmissione (m_h = n_h − 1 per strato, pesi
  riscalati con la correzione per popolazione finita), 9999 repliche, seme dedicato, intervalli percentili al
  95 %. Se si usasse il bootstrap con reimmissione semplice, l'approssimazione va dichiarata (frazioni di
  campionamento 6–9 %);
- **classificazione**: anche C ha incertezza di classificazione; non entra negli intervalli e si descrive con
  la seconda lettura (sopra).

## 6. Precisione e lettura prevista (nessuna soglia di decisione)

Precisione indicativa per conteggio, quota vera 0,3: errore standard circa 0,08 nello strato (n = 30), circa
0,06 per terzile, circa 0,08–0,09 per la differenza fra terzile alto e basso (senza considerare C, che la
riduce). Una semilarghezza di 15–20 punti **non** equivale a un'alta probabilità di rilevare una differenza di
quella grandezza: la potenza per una tale differenza sarebbe molto più bassa.

Risultati espressi come «in S, circa X % dei record (Y % di ΣΦ) è classificato B, con intervallo …; nel
terzile alto di attività la quota è … contro … nel basso». **Nessuna regola automatica.** Limiti di lettura:
- una prevalenza di B o D crescente con l'attività **non dimostra** che il tilt sia attenuato: potrebbero
  cambiare dispersione, segno o altro;
- l'assenza di associazione **non esclude** un effetto della morfologia sulla misura;
- un'eventuale associazione motiverebbe al più un piano separato sulla misura del tilt; non autorizza
  correzioni di T3.

## 7. Costo e sequenza

- Generazione: 281 coppie di FITS locali, 562 immagini; minuti su un processo, con `nice`, **dopo** la fine
  della griglia T5 in corso.
- Lettura, la parte cara: lettore 1 11 + 281 schede in due passaggi (circa 580 immagini), lettore 2 11 + 60.
  Ordine di grandezza: un'immagine delle schede attuali (1540 × 467 pixel) vale circa 1000 token in ingresso;
  con motivazioni e contesto, **circa 1–2 milioni di token** per il lettore 1 (stima grezza, da verificare
  sulla taratura).
- Sequenza: decisione sul costo (§8) → congelamento con hash, semi e allocazione → script delle schede e
  delle verifiche automatiche → taratura → letture bloccate → collegamento ai metadati e stime → rapporto.
  Nessun push senza richiesta.

## 8. Decisione aperta prima del congelamento: costo

Opzione raccomandata (revisione di Codex): **281 schede** (180 nuove + rilettura delle 101). Alternativa se il
costo è eccessivo: riuso delle 75 letture A2 bloccate e rilettura delle sole 26 di 25S (**206 schede**),
dichiarando come limite dell'associazione classe–attività la mescolanza di sessioni concentrata ad alta
attività. Un ridimensionamento ulteriore va deciso prima del congelamento, non dopo.

## 9. Semi proposti

2026111601 estrazione degli strati; 2026111602 codici e ordine del lettore 1; 2026111603 sottocampione del
lettore 2; 2026111604 ordine del lettore 2; 2026111605 bootstrap. Disgiunti dai semi morfologici precedenti
(2026111301–2026111303) e dagli intervalli in `P.USED`.

## 10. Revisione di Codex della revisione 1 (2026-11-16), recepita

1. 30 per strato, sei strati, prevalenza per conteggio come risultato principale; Φ e |S_BL| complementari;
   nessuno strato per il decile superiore senza una valutazione basata sulle covariate (§3, §5).
2. Rilettura di tutte le 101 HARP note, file storici intatti; il riuso resta un'alternativa dichiarata (§3, §8).
3. Le 10 schede di riferimento restano nella popolazione, con esposizione dichiarata (§3, §4).
4. Seconda lettura distribuita anche sulle 101: 12 da C e 8 per strato; matrice, accordo e disaccordi
   specifici con pesi coerenti con l'estrazione; nessuna soglia automatica del 70 % (§4, §5).
5. D riportata separatamente anche per attività, accanto a B e B+D (§5).
6. Non prerequisito per MDI; T5 percorso più diretto (§2).
Precisazioni tecniche: numerosità campionabili N_h nei pesi (495, 318, 400, 395, 338, 438) e formula del
denominatore (§3, §5); bootstrap coerente con l'estrazione senza reimmissione e distinzione fra incertezza di
campionamento e di classificazione (§5); variante con due B come sensibilità, distinta dalla stima pesata
della quota concordata (§5); semilarghezza diversa dalla potenza e limiti di interpretazione (§6).

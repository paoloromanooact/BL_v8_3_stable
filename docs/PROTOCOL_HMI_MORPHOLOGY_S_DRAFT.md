# Morfologia della popolazione S — bozza di piano

**BOZZA NON CONGELATA, revisione 1 — 2026-11-16.** Da rivedere (Codex) prima del congelamento. Nessuna
scheda generata, nessun campione estratto, nessuna lettura. I conteggi di §3 vengono solo dal disegno
(attività, flusso, appartenenza alle HARP già lette); non usano tilt, S_BL per record, verdetti o classi.
**Non cieco**: domanda, risultati T3/T5 e lo studio morfologico precedente sono noti ai lettori.

## 1. Origine e domanda

Lo studio morfologico precedente (`docs/MORPHOLOGY_RESULTS.md`; protocollo `21dfe6d`, A1 `67f5e1a`, A2
`9a4c4cd`) ha soddisfatto la sua regola operativa (§7: classe B ≥ 10 % di Σ|S_BL| in 24S e 25N, accordo
24/30, U ≤ 3/30), **esattamente alla soglia** per l'accordo. L'unico esito consentito è proporre un piano
distinto per uno studio rappresentativo di S. Le 120 HARP lette erano una selezione fissata (dominanti e
controlli) e non stimano la prevalenza in S.

Domanda, descrittiva: **nella popolazione S su cui è stato applicato T3 (2485 record primari HARP, uno per
HARP, cicli 24–25), quanto spesso la misura a due centroidi riassume una configurazione senza una coppia
bipolare dominante (classi B e D), e questa frequenza cambia con l'attività Â?**

Perché interessa T3: se la quota di configurazioni senza coppia dominante crescesse con l'attività, il tilt
misurato potrebbe essere diluito in modo correlato con Â, e quindi confondibile con una dipendenza del
coefficiente di Joy dall'attività. Lo studio **descrive** questa possibilità; non la misura sulla pendenza.

## 2. Che cosa lo studio non fa

- Nessuna esclusione di HARP, nessuna nuova pendenza, nessun rilancio di T3 o T5, anche su sottoinsiemi di
  classe; nessun confronto di tilt, Hale o S_BL fra classi. T3 resta «non deciso», T5 descrittivo.
- Nessuna modifica di P1, dei flag o delle letture bloccate dello studio precedente.
- Le classi non sono validate fisicamente: B non prova più regioni fisiche, D non prova un errore.
- Un'eventuale associazione fra classe e attività motiverebbe al più un piano separato (per esempio una
  sensibilità della misura); non autorizza correzioni.

## 3. Popolazione, strati e campione

**Popolazione.** S ricostruito come in P2f (`run_p2.samples(cat)["S"]` con `add_activity`, Â finita):
2485 record, 2485 HARP distinte; (24, N) 677, (24, S) 581, (25, N) 609, (25, S) 618. Br e bitmap di tutti i
2485 record sono già in locale (`data/sharp/fits`): nessun download.

**Strato certo (101 record).** Le HARP di S già lette nello studio precedente: 75 delle 90 nuove (lettura
A2 bloccata del lettore 1) e 26 di 25S (10 schede di riferimento e 16 con sole etichette storiche). Coprono
il 16,3 % di ΣΦ e il 30,8 % di Σ|S_BL| di S, concentrate ad alta attività e alto flusso: **escluderle
sposterebbe le stime pesate**. Proposta:
- le 75 conservano la classe primaria A2 bloccata del lettore 1 (e del lettore 2 dove esiste, per la
  variante conservativa);
- le 26 di 25S si **rileggono** nel nuovo formato con le regole A2, mescolate alle schede nuove;
  esposizione dichiarata (classi storiche note; le 10 di riferimento sono state viste in taratura).

**Strati campionati.** Le 2384 HARP restanti, divise in 6 strati: terzili di Â su S (tagli 1,1063 e
1,7380) × flusso sotto/sopra la mediana di Φ su S (6,155·10²¹ Mx). Composizione (record di S; fra
parentesi quelli già letti; quote di ΣΦ e Σ|S_BL| di S):

| Â | Φ | N (già letti) | Quota ΣΦ | Quota Σ\|S_BL\| |
|---|---|---|---|---|
| basso | < mediana | 499 (4) | 4,6 % | 3,7 % |
| basso | ≥ mediana | 327 (9) | 16,0 % | 16,2 % |
| medio | < mediana | 403 (3) | 3,8 % | 2,9 % |
| medio | ≥ mediana | 424 (29) | 27,5 % | 27,8 % |
| alto | < mediana | 340 (2) | 3,1 % | 2,7 % |
| alto | ≥ mediana | 492 (54) | 45,1 % | 46,7 % |

**Allocazione proposta.** 30 record per strato, estratti senza reimmissione fra quelli non già letti,
seme dedicato: **180 schede nuove + 26 riletture = 206 schede** per il lettore 1. Alternativa da decidere in
revisione: 40 per strato (240 + 26). Il 10 % dei record con Φ maggiore porta il 43,5 % di ΣΦ: le stime pesate
per Φ saranno meno precise di quelle per conteggio. Una variante con il decile superiore di Φ come strato
proprio è possibile, da decidere prima del congelamento.

Precisione indicativa, conteggio semplice, per una quota vera di 0,3: con 30 per strato l'errore standard è
circa 0,08 nello strato e circa 0,06 per terzile di attività (60 record); la differenza fra terzile alto e
basso ha errore standard circa 0,08–0,09. Differenze di prevalenza sotto circa 0,15–0,20 non saranno
risolte. Con 40 per strato, circa 0,07 per la differenza.

## 4. Schede e lettura (come lo studio precedente, regole A2)

- Stesso generatore del protocollo precedente: due viste fisse (±1500 G e ±300 G), contorno della maschera
  P1 (bitmap ≥ 33), versione con soli marker dei centroidi; nessun numero, flag, NOAA, data, gruppo o
  HARPNUM; dimensione e risoluzione fisse.
- Codici anonimi e ordine casuale, semi dedicati; corrispondenza codice–HARPNUM in un file privato con hash,
  non stampata, non data ai lettori prima del blocco.
- Classi A2 (A, B, D, U con alternative scritte); due passaggi: prima la mappa e la classe primaria, poi,
  dopo il blocco delle primarie di entrambi i lettori, l'indicatore C e il contatto al bordo. Le classi non
  cambiano dopo aver visto i marker.
- **Taratura**: le 11 schede di riferimento già usate, rilette da ciascun lettore prima delle nuove;
  differenze registrate. Le 10 di riferimento che stanno in S entrano anche nelle 26 riletture: si dichiara
  che la loro lettura non è indipendente dalla taratura.
- **Lettore 1**: la sessione dell'agente (Claude; modello registrato). **Lettore 2**: la sessione del
  revisore esterno; legge **60 schede** (10 per strato campionato), estratte con seme dedicato, ordine
  separato. Esposizioni dichiarate come nel protocollo precedente; nessuno dei due è cieco al progetto.
- Blocco con hash di ogni file di lettura prima di mostrare marker, etichette altrui o numeri.

## 5. Grandezze stimate (fissate prima)

Stimatori stratificati, con pesi N_h/n_h negli strati campionati e peso 1 nello strato certo:
1. **E1** prevalenza di A, B, D, U in S, per conteggio;
2. **E2** quote pesate per Φ (i pesi della WLS di T3);
3. **E3** quote pesate per |S_BL| (rilevanza per la sorgente);
4. **E4** per terzile di Â: quota di B e di B+D, per conteggio e pesata per Φ; differenza fra terzile alto
   e basso con intervallo;
5. **E5** per ciclo × emisfero, solo descrittivo (numerosità piccole);
6. accordo dei lettori sulle 60 doppie letture: matrice A/B/D/U, accordo esatto con denominatore,
   composizione del sottocampione; C come indicatore secondario.

Incertezza: bootstrap stratificato (ricampionamento dentro gli strati, strato certo fisso), 9999 repliche,
seme dedicato, intervalli percentili al 95 %; per E1 anche gli intervalli analitici stratificati. U resta
una categoria propria; si riportano anche i due casi estremi (tutte le U come B, nessuna U come B).
Variante conservativa: per le doppie letture, B conta solo se entrambi i lettori assegnano B. Stima
principale con lo strato certo; stima secondaria sulle sole 2384 HARP campionabili.

## 6. Lettura prevista (nessuna soglia di decisione)

Risultati espressi come «in S, circa X % dei record (Y % di ΣΦ) è classificato B, con intervallo …; nel
terzile alto di attività la quota è … contro … nel basso». **Nessuna regola automatica.** Domanda per una
discussione successiva con Codex: le quote e la loro dipendenza da Â sono abbastanza grandi da motivare un
piano separato sulla misura del tilt (per esempio una sensibilità dei centroidi per classe)? Un accordo fra
lettori basso (proposta da discutere: sotto 0,7 sulle 60) renderebbe le stime per classe solo indicative.

## 7. Costo e sequenza

- Generazione: 206 coppie di FITS locali, 412 immagini; minuti su un processo, con `nice`, **dopo** la fine
  della griglia T5 in corso.
- La lettura è la parte lunga: circa 206 + 11 schede per il lettore 1 e 60 + 11 per il lettore 2; il costo in
  token delle immagini è alto e va considerato prima del congelamento.
- Sequenza: revisione di questa bozza → congelamento con hash, semi e allocazione → script delle schede e
  delle verifiche automatiche (conteggi, record, assenza di annotazioni) → taratura → letture bloccate →
  collegamento ai metadati e stime → rapporto. Nessun push senza richiesta.

## 8. Punti aperti per la revisione

1. Allocazione: 30 o 40 per strato; decile superiore di Φ come strato proprio.
2. Strato certo: tenere le 75 letture A2 bloccate e rileggere le 26 di 25S, oppure rileggere tutte le 101.
3. Se escludere dallo strato certo le 10 schede di riferimento (lettura non indipendente dalla taratura).
4. Soglia di accordo per considerare le stime solo indicative, oppure nessuna soglia.
5. Se ammettere E4 anche per D separatamente, dato il numero atteso piccolo.
6. Se lo studio vada prima dell'estensione MDI, dato che anche la confrontabilità MDI dipende dalla
   morfologia a risoluzione più bassa.

## 9. Semi proposti

2026111601 estrazione del campione; 2026111602 codici e ordine del lettore 1; 2026111603 sottocampione del
lettore 2; 2026111604 ordine del lettore 2; 2026111605 bootstrap. Disgiunti dai semi morfologici precedenti
(2026111301–2026111303) e dagli intervalli in `P.USED`.

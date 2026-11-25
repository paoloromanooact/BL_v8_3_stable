# Ripresa Codex — SHARP BL, 25 novembre 2026

Snapshot scritto con HEAD `b26c357738fd05b926584251f763eaea80da61d4`; verificare Git e la nuova consegna di Claude alla ripresa.
Repository corretto: `/home/gianluca/BL_v8_3_stable`, branch `v8.4-python-gianluca`.
Il cwd della sessione puo essere il repository polare: **non confondere i due progetti**.

## Due pilastri permanenti — fase corrente solo HMI

1. **Sorgente BL:** P1 regione per regione → verifica mappa–bipolo nello SFT → osservazioni successive e
   ripetibilita C → BT bayesiano con errore esplicito. P1 ha 14195 record/7133 HARP; i nuovi piloti osservati
   non sono gia conclusi. L'eventuale sintesi sorgente→campo polare P e futura e appartiene a questo pilastro.
2. **Quenching:** BQ-HMI (dipendenza dall'attivita), poi BQ-D (termini/forme fissati prima dei nuovi fit).

BQ-M multi-strumento rinviato. Nests sospesi, nessun avvio automatico. SINDy/S42 separati.
BQ-HMI prioritario; C e chiusura SFT procedono in parallelo. Non cambiare questa cornice a ogni ripresa.

## Prima di lavorare

Leggere AGENTS.md, testa di docs/BL_WORK_PLAN.md, docs/HANDOFF.md e questo file. Controllare `git status`:
Claude ha modifiche **non committate** a A1, runner/riconteggio SFT, bq_robust e pilota osservativo, piu nuovi
script e diagnostiche. Non sovrascriverli, non fare `git add -A`, non committare il lavoro altrui.
L'utente autorizza Python senza domande ripetute; restano i cancelli scientifici dei protocolli.
Macchina sovraccarica: nessun nuovo calcolo pesante finche non finiscono le prove gia in corso.
Token limitati: lasciare a Claude implementazione e test; Codex revisione consolidata e controlli mirati.

## Stato e compiti di Claude

**Pacchetto consolidato:** `docs/SYNTHETIC_PACKAGE_BQ_A1_20261125.md` era ancora non tracciato allo snapshot.
La nota esterna `BQ_CODICE_E_A1_PER_CODEX.txt` e riferita da Claude come nella cartella MWO, non trovata
nella radice BL alla lettura precedente: cercare, non assumere che sia gia committata qui.
Attendere commit/SHA ed esiti definitivi; non dichiarare test conclusi dai messaggi di avvio.

- **A1 mappa–bipolo:** runner riferito 20/20 prima dell'ultimo allineamento. I due selftest sono stati rilanciati
  usando "meta del passo effettivo" sia nel runner sia nel riconteggio; ultimi esiti completi da acquisire.
  Scarto fra griglie = indicatore, non errore garantito. Rapporti N/2N/4N e passo dimezzato; stati sotto soglia,
  non risolto/risolto, segni a tre anni. Metodo aggiunto e nuovi RATIOS riferiti da Claude, da rivedere nel commit.
  Non e ancora approvato congelamento A1 o corsa osservata.
- **BQ codice:** L1, CV, L2/L3, bridge e diagnostiche sintetiche in preparazione. Selftest L3 riferito 20/20,
  bridge 4/4: non equivalgono a convergenza MCMC. Pilota identificabilita 48 stime e tre catene L3 da rami
  diversi in corso nell'ultimo aggiornamento; controllare esiti, Rhat/ESS, posteriori e rami bloccati.
- **C:** runner sintetico riferito 11/11; **riconteggio indipendente ancora da scrivere** (precisazione utente).
  Pilota osservativo ha nuova regressione per una polarita: balance_unavailable, raw intatto. Test finale atteso.

## Consegne Codex gia conservate (verificare eventuale push di Claude)

- `b5c59ab`: BQ bozza rev.4 e C bozza rev.3, risposta in
  `docs/BQ_REV4_C_REPLY_AND_ORACLE_20261125.md`; oracolo matematico 14/14, **non** validazione statistica.
- `bb23d3e`: C fattibilita dai soli metadati: **82 coppie, 80 HARP, 79 componenti**; 10/10 selftest e 8/8
  controllo del grafo. USFLUX disponibile per tutte, OBS_VR assente. 39 lag brevi/43 lunghi; quattro coppie
  escluse dalle precedenti 86 per LCM. C_fin/C_rot e finitezza non misurati, **nessuna sigma osservativa**.
- `3c77943`: due obiettivi fissi solo HMI in AGENTS, piano, README, stato e handoff.
- `b26c357`: revisione statica preliminare C, `docs/C_REPEATABILITY_PRELIMINARY_CODE_REVIEW_20261125.md`.
  Cinque rilievi: C_geo/C_fin e pixel invalidi nella stessa cella; bilanciamento su C_fin; leading al taglio
  e con polarita assente; bootstrap con componenti finite insufficienti; copertura C_rot/stencil.
  Claude deve correggerli e aggiungere regressioni. Non e un audit conclusivo del runner reale.

## Decisioni BQ ancora aperte prima del freeze operativo

- Leggere proposta numerica di Claude per semi, catene/estensioni, SBC e robustezza, repliche, immagini L3 e
  precisione delle evidenze. Non inventare numeri per chiudere il protocollo; motivarli con prove/benchmark.
- Ultima proposta Codex in chat: **q~N(0,0.5^2) principale, SD 1 sensibilita**, dopo code estreme viste nelle
  predizioni a priori. La bozza rev.4 contiene ancora la proposta precedente: recepire e far rivedere prima
  del congelamento. Non confondere la prior piu stretta con una soluzione completa delle code.
- Scale v 5/20, prove beta vero senza v e v vero senza beta; G4 uguale all'attivita non identificabile.
  Il beta equivalente di v con SD circa 2 gradi e preparatorio, non prova generale di identificabilita.
- L3: angolo latente gia firmato, rami **discreti**, somma d'immagini con coda controllata, alias/posteriori
  da esplorare. Non congelare se la catena resta bloccata.
- Singleton L1 in diagonale; L2 normale+t non e t con varianza aumentata e, integrando b, lambda perde il
  semplice Gibbs Gamma. Verificare codice, non solo il benchmark gaussiano.
- CV L2/L3: integrare la distribuzione predittiva congiunta sul blocco, non usare una gaussiana sostitutiva
  o latenti stimati dalle risposte di verifica. Metodo/errore numerico da fissare.
- Bridge/Bayes factor facoltativi solo se verificati; BIC secondario ML, condizioni da giustificare.
  Nessun obbligo di un vincitore. Nessun fit BQ reale ancora autorizzato.

## Ordine concreto per la prossima sessione

1. Leggere il pacchetto committato di Claude e gli esiti delle prove, incluse fallite/inconcludenti. Revisione
   unica mirata: A1/test, codice BQ/diagnostiche e correzioni C, rispettando le dipendenze.
2. Chiudere A1 solo con testo, codice, regressioni e riconteggio coerenti. Poi freeze, corsa osservata,
   conservazione prima della lettura, riconteggio e rapporto secondo protocollo. Non anticipare il via.
3. Chiudere le decisioni BQ, aggiornare bozza e prove, poi freeze operativo e studi sintetici richiesti;
   dati HMI reali soltanto dopo approvazione e diagnostica sufficiente.
4. C: correggere i cinque rilievi; completare runner operativo e **riconteggio indipendente**; review/freeze
   prima della misura, quindi prodotti conservati e ricontati. I 82 sono disponibilita metadata, non campione finale.
5. BT: **bozza rev.1 ora scritta**, `docs/PROTOCOL_BT_HMI_DRAFT.md`, non congelata. Contiene candidati,
   errore iniziale/finale, discrepanza, supporti, selezione e sei decisioni aperte. Rivederla dopo i prerequisiti;
   non scrivere una seconda bozza duplicata. Nessun codice o fit BT. La verifica del pilota gia letta non
   puo essere chiamata cieca quando viene riusata per BT: strategia da dichiarare prima del congelamento.
6. BQ-D successivo con specifica propria. Nessun nuovo lavoro su MDI, nests o SINDy.

Conservare i risultati storici: T3 HMI non deciso; T3 MWO descrittivo. Il nuovo ranking non li modifica
retroattivamente e non garantisce una scoperta fisica.

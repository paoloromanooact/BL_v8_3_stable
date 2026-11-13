# HMI: interpretabilità del bipolo nelle schede esistenti — bozza

**BOZZA NON CONGELATA, revisione 3 — 2026-11-13 (pronta per la revisione prima del congelamento; §7 elenca le chiusure).** Nessuna nuova scheda,
classificazione o estrazione è stata prodotta. Le scelte numeriche sotto sono
proposte operative da rivedere prima del congelamento, non criteri fisici validati.
Studio descrittivo; P1, P2 e P2f restano invariati.

## 1. Domanda e informazione nuova

Quanto spesso una misura a due centroidi rappresenta un bipolo riconoscibile
e quanto spesso riassume più concentrazioni? Come si accompagnano queste
configurazioni alle sensibilità già misurate?

S4 («una NOAA») è un filtro di metadati, non una classificazione magnetica.
Questo passo completa il controllo negli altri tre gruppi e distingue la
morfologia della mappa dalla posizione dei centroidi. Non misura nuovamente
il quenching e non seleziona HARP in base al segno del risultato.

## 2. Campione e preparazione delle schede

Conservare le **120 HARP** del [piano dominanti](DOMINANT_HARP_PLAN.md):
20 dominanti e 10 controlli per 24N, 24S, 25N, 25S; 101 appartengono a S.
Le 30 letture 25S sono un blocco storico, le **90 degli altri gruppi** sono
le nuove letture. Non estendere il campione o sostituire schede difficili.

Rigenerare le 90 schede dagli stessi FITS e record, con identica geometria
e maschera P1. Le immagini originali restano intatte. Preparare due versioni:

- **Mappa:** Br con scala comune ±1500 G (saturazione oltre; nessuna scala adattiva, così regioni
  forti e deboli restano confrontabili; le regioni deboli appaiono più tenui e questo va tenuto
  presente nel giudizio D) e contorni di maschera; nessun tilt,
  S_BL, flusso integrato, flag, NOAA, data, gruppo o HARPNUM. Solo un codice
  anonimo; nessun centroide o segmento fra centroidi.
- **Centroidi:** la stessa immagine, aggiungendo soltanto i marker positivo
  e negativo. Nessun valore numerico derivato o flag.

La scala del campo e le coordinate necessarie a leggere la mappa non sono
diagnostiche di esito. La geometria può rivelare l'emisfero: l'anonimizzazione
non garantisce cecità al gruppo. La domanda e i risultati del progetto sono
già noti e parte delle immagini è stata vista (incluse 393 e 5249 nella prova
tecnica); dichiarare la lettura non cieca e registrare le esposizioni note.

Dopo il congelamento, assegnare codici e mescolare le 90 schede con un
generatore dedicato, seme proposto **2026111301**. Conservare la corrispondenza
fra codice, HARPNUM e file con i relativi hash, senza passarla ai lettori prima
del blocco delle etichette. La preparazione non modifica le misure P1.

## 3. Classificazione in due passaggi: evitare circolarità

**Passaggio 1, sola mappa.** Registrare classe primaria e motivazione visiva:

| Classe | Definizione |
|---|---|
| A | Un sistema bipolare riconoscibile, con due concentrazioni principali. |
| B | Più sistemi o concentrazioni: non è riconoscibile una sola coppia bipolare dominante. |
| D | Configurazione diffusa, frammentata o visivamente molto sbilanciata; coppia bipolare poco riconoscibile. |
| U | Immagine insufficiente o giudizio di confine non risolto; conservare le alternative nel testo. |

**Regole operative per i casi di confine (revisione 3).** Si guarda solo il campo forte dentro la
maschera P1 (contorno giallo); la plage debole e sparsa non conta come concentrazione.
1. **A** se, per ciascuna polarità, il campo forte forma **un solo gruppo** (anche con più macchie
   vicine e collegate da campo della stessa polarità) e i due gruppi stanno affiancati.
2. **B** se almeno una polarità forma **due o più gruppi separati** da una zona senza campo forte di
   quella polarità, ciascuno con un peso visivo paragonabile (indicativamente non meno di circa un
   terzo dell'altro), oppure se compaiono due coppie bipolari distinte.
3. **D** se una polarità è appena visibile rispetto all'altra, oppure se entrambe sono solo plage
   frammentata senza gruppi riconoscibili.
4. Se dopo queste regole restano due classi plausibili: classe **U** con le due alternative scritte
   (per esempio «U: A o B»). Le etichette miste non si usano più come classe primaria.

**Schede di riferimento (taratura, prima di leggere).** I lettori guardano, nella sola versione
«mappa», queste schede di 25S già lette e fuori dalla nuova verifica, con la classe indicata:
A — 8950, 9559, 8206, 7821, 12623; B — 11786, 11513, 12094, 11930; D — 11248 (quasi unipolare),
13169 (frammentata). Servono a rendere comuni le regole tra i due lettori; non diventano repliche.

Non dedurre il decadimento da un istante. Non usare componenti connesse,
sbilanciamenti calcolati, numero NOAA, soglie diagnostiche, tilt, Hale o
S_BL per assegnare la classe. Il giudizio di sbilanciamento in D è soltanto
visivo e non va poi trattato come verifica indipendente del flag numerico.

**Passaggio 2, dopo il blocco delle classi primarie di entrambi i lettori.**
Mostrare la versione con centroidi e registrare separatamente l'indicatore
**C: almeno un centroide fra concentrazioni distinte della stessa polarità**
(sì/no/non valutabile), più eventuale contatto al bordo. Non cambiare la
classe primaria dopo aver visto i marker.

C è una proprietà della rappresentazione a centroidi, non una classe primaria
indipendente. Il suo legame con la sensibilità dei centroidi è descrittivo e
in parte legato alla definizione: non valida la misura. Nessuna classe prova
un errore o l'appartenenza del campo ad altre regioni fisiche.

Questa distinzione modifica la griglia della prima bozza: le etichette 25S
storiche A/B/C/D, comprese quelle miste, restano conservate e **non vengono
convertite automaticamente** nelle nuove classi. Riportarle separatamente;
non usare le 30 letture come repliche delle nuove 90.

## 4. Seconda lettura indipendente

Un secondo lettore classifica **30 delle 90** schede, senza vedere le etichette
o motivazioni del primo. Estrarre 10 per gruppo nuovo: 7 dominanti e 3 controlli,
senza reimmissione, nell'ordine 24N, 24S, 25N, con seme **2026111302**; ordine
di presentazione separato con seme **2026111303**. Nessuna scelta per difficoltà
o disaccordo. Se manca il secondo lettore, questa parte resta incompleta.

**Lettori.** Lettore 1: la sessione dell'agente del progetto (Claude; modello e versione registrati
nel file delle letture). Lettore 2: la sessione del revisore esterno (modello e versione registrati).
Esposizioni note, da dichiarare: entrambi conoscono domanda, risultati T3/T5 e le tabelle numeriche
delle 120 HARP; il lettore 1 ha letto le 30 schede 25S e visto le schede 393 e 5249 (24N) nella prova
tecnica; il lettore 2 ha fatto la seconda lettura delle 30 schede 25S dopo la prima. I lettori ricevono
le schede solo tramite codice anonimo; nessuno dei due è cieco al progetto.

Ogni lettore registra codice, data, classe primaria, motivazione e poi C.
Bloccare i file di ciascun passaggio con hash prima di mostrare marker,
etichette altrui o tabelle numeriche. Dichiarare identità e precedenti esposizioni
dei lettori; una seconda lettura dopo aver visto la prima non è indipendente.

Prima di discutere i disaccordi, produrre matrice di confusione A/B/D/U,
accordo esatto n/30 e accordo sull'indicatore C, con denominatori e non valutabili.
Riportare anche la composizione del sottocampione: l'accordo grezzo dipende
dalle frequenze delle classi e non prova validità fisica. Eventuali etichette
concordate dopo confronto restano una colonna separata.

## 5. Tabelle finali e uso operativo prefissato

Solo dopo aver bloccato tutte le letture collegare metadati e numeri:

1. Registro HARP per HARP, distinguendo letture storiche e nuove, dominanti e
   controlli, appartenenza a S; confronto successivo con il numero NOAA.
2. Conteggi per gruppo e contributi netti e Σ|S_BL| per classe. Ogni quota
   indica se il denominatore è il campione esaminato o l'intera base P1 del gruppo.
3. Sensibilità già calcolate per bitmap ≥ 1 e pesi uniformi: sia ΣΔ sia Σ|Δ|,
   confronti mancanti espliciti, nessuno zero sostitutivo. Associazioni
   descrittive, non prove causali né test del quenching.

**Proposta di regola per motivare uno studio sulla popolazione S:**

- La classe primaria **B** porta almeno il **10% di Σ|S_BL| dell'intera base
  P1 del gruppo**, contando solo le HARP qui esaminate, in almeno **due dei
  tre gruppi nuovi**. Il 10% è una soglia di priorità operativa (un decimo
  del proxy in configurazioni senza una coppia unica), non un budget d'errore.
- Sulle 30 doppie letture, almeno **24/30** classi primarie coincidono e
  ciascun lettore assegna U ad al massimo **3/30** schede. Sono requisiti
  pratici proposti, non una validazione della tassonomia.
- Per le schede doppie, verificare la prima condizione sia con le classi del
  primo lettore sia contando B solo quando entrambi assegnano B. Se la scelta
  del lettore cambia il superamento, il criterio è inconclusivo.

Questa regola propone soltanto **di progettare** uno studio rappresentativo
di S. Se le condizioni non si verificano, completare il rapporto e fermarsi;
con disaccordi rilevanti, rivedere prima la griglia in un piano distinto.
Nessuna esclusione dal catalogo o nuova pendenza è autorizzata dalla regola.
Il gruppo 25S, già noto, è contesto e non parte della nuova verifica. C è
escluso dal criterio per evitare la circolarità discussa sopra.

La regola è scelta conoscendo i controlli numerici delle 120 HARP e la
lettura 25S: è una scelta non cieca di priorità, non una verifica confermativa.
La selezione di dominanti e controlli non stima la prevalenza di B in S.
Non si richiede una quota del 25% in tutti i gruppi: in 24N le 30 schede
coprono complessivamente circa il 21,9% di Σ|S_BL|, quindi una tale soglia
sarebbe irraggiungibile già per costruzione.

## 6. Arresto e revisione

**Costo.** Rigenerare le schede legge 90 coppie di FITS già locali e scrive 180 immagini: pochi minuti
su un processo, senza simulazioni. Si fa dopo il congelamento e, se la macchina è occupata da un'altra
esecuzione, con `nice`.

Prima di codice, estrazioni, figure o letture: rivedere e congelare il piano
con commit e hash, inclusi griglia, semi e regola operativa proposta. Poi
verificare che le nuove immagini corrispondano agli stessi record e che non
contengano annotazioni escluse. Non toccare schede storiche, FITS o risultati.

Completare registro e tabelle, poi fermarsi. Nessuna segmentazione, nuovo
campione, nuova applicazione T3 o modifica T5. La robustezza di T5 ai salti
rimane una priorità distinta: [traccia diagnostica](T5_JUMPS_DIAGNOSTIC_DESIGN.md).

## 7. Chiusure della revisione 3 (da confermare in revisione prima del congelamento)

- **Classi:** A, B, D, U con regole operative per i casi di confine e U con alternative scritte;
  niente etichette miste come classe primaria; C solo indicatore del secondo passaggio.
- **Taratura:** 11 schede di riferimento di 25S (§3), viste prima della lettura nella sola versione mappa.
- **Schede anonime:** due versioni (mappa; mappa con marker), scala fissa ±1500 G, nessuna annotazione
  di esito, codici e ordine con seme 2026111301, corrispondenza codice–HARPNUM conservata con hash e
  non data ai lettori prima del blocco.
- **Seconda lettura:** 30 schede (10 per gruppo nuovo: 7 dominanti e 3 controlli), semi 2026111302 e
  2026111303; lettore 2 = sessione del revisore esterno; esposizioni dichiarate.
- **Regola per uno studio successivo:** invariata (B ≥ 10 % di Σ|S_BL| della base del gruppo in almeno
  due dei tre gruppi nuovi; accordo ≥ 24/30, U ≤ 3/30 per lettore; verifica con entrambi i lettori).
- **Restano da confermare:** la soglia indicativa «circa un terzo» del peso visivo per B; la scala fissa
  ±1500 G; la scelta del lettore 2.

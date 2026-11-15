# T5-D2 — rapporto dei risultati

**Struttura preparata il 2026-11-13 prima dell'apertura degli output.
Risultati e interpretazione inseriti il 2026-11-15 (§6, §7.1, §9), dopo il
controllo separato 54/54 e la conservazione degli output (`27a9c7d`).**
Il file non è un protocollo e non congela nuovi criteri. Revisione di fase 2
(Codex) svolta su `8c7801a`; correzioni in `6e48f3c`, verificate da Codex su
`0cdabc3` (§10). Resta aperto il ricalcolo indipendente degli SE degli oracoli (§7.1).

## 1. Domanda e stato scientifico

T5 studia la dipendenza dell'efficienza del proxy della sorgente BL
rispetto all'attività. La procedura M non ha superato la validazione P2f
nello scenario 7, con livelli ±1 su blocchi di 20 CR. T5-D1 ha rilevato,
negli output salvati della validazione P2f (`5c3b664`), ora materiale di
sviluppo, R = media(SE²)/varianza empirica(beta) circa
0,858 sotto nulla. Si tratta di una carenza di circa il 14,2% nella media
di SE², non nel valore di SE e non in una componente già identificata.
R da solo non descrive le code o i falsi verdetti.

T5-D2 confronta sostituzioni oracolo delle componenti della varianza sugli
stessi cataloghi sintetici già usati nella validazione. Non raccoglie nuove
osservazioni, non verifica il quenching sui dati reali e non valida una
nuova procedura. Gli oracoli usano quantità note soltanto nelle simulazioni.
**T5 resta descrittivo. T3 resta non deciso, senza nuove esecuzioni.**

## 2. Provenienza e ordine dei passaggi

| Elemento | Riferimento documentato |
|---|---|
| Protocollo storico congelato | [PROTOCOL_T5_ORACLE.md](PROTOCOL_T5_ORACLE.md), `f77d39b`; conservato invariato |
| Emendamento da applicare nella lettura | [PROTOCOL_T5_ORACLE_A1.md](PROTOCOL_T5_ORACLE_A1.md), `2b334bb`; prevale sui punti sostituiti |
| Produttore atteso | `2bf262f1b99d6a884ed72686047dc089911e5eff`, albero tracciato pulito: confermato su ogni riga e nei metadati degli output (§4) |
| Avvio registrato | 2026-11-13 13:56:57 Europe/Rome, nota `d284592`; PID wrapper 1141311, PID Python 1141317 |
| Fine, durata, uscita | Log `logs/t5_oracle.log`: «32000/32000 cataloghi» e marcatore `fatto`, ultimo aggiornamento 2026-11-13 18:45:25 Europe/Rome; durata circa 4 h 48 min (stima del piano 1,5–2,5 h). Codice di uscita del processo non registrato |
| Ricevuta preliminare | Dieci prove passate, già registrate; hash atteso in [fotografia degli input](T5_ORACLE_POSTCHECK_INPUTS_SHA256.csv) |
| Codice del verificatore separato | `9bd1e2e`; 77 prove costruite a mano passate; ricevuta legata allo SHA del codice, non all'HEAD documentale successivo |
| Controllo effettivo sui risultati | Eseguito il 2026-11-14 sul commit pulito `94606c6` con `t5_oracle_postcheck.py --check` (codice `ac591b47…`, ricevuta 77/77): **54/54 controlli superati**, nessuna discrepanza; esiti in `results/T5_ORACLE_POSTCHECK/` |
| Conservazione degli output | Quattro output, ricevuta preliminare e controllo conservati nel commit successivo al controllo, prima di leggere i risultati; hash prima/dopo identici in `results/T5_ORACLE_POSTCHECK/META.json` |
| Interpretazione e revisione | Interpretazione 2026-11-15, Claude Opus 5.5, su `27a9c7d`; non cieca (§8). Revisione di fase 2: Codex su `8c7801a`, correzioni `6e48f3c` verificate (§10) |

Distinguere il produttore degli output T5-D2, quello della validazione P2f
originale (`5c3b664`) e il commit del verificatore. Non richiedere che siano
lo stesso HEAD. Registrare versioni dell'ambiente e ricevute effettivamente
usate; non attribuire alla corsa un ambiente dedotto solo dal file dei requisiti.

L'emendamento A1 dichiara una prova tecnica su quattro cataloghi sintetici
della validazione P2f prima della registrazione dell'emendamento e del commit del codice. Questo
limite di cecità resta dichiarato, senza ripresentare il lavoro come cieco.

## 3. Bracci e quantità sostituite

La stima beta deve restare identica tra bracci dello stesso catalogo.
Cambiano la varianza e, dove specificato, la sua stima temporale.

| Braccio nel CSV | Varianza individuale | Componente temporale | Confronto da descrivere |
|---|---|---|---|
| A0 | stimata | REML AR(1) stimata | Riproduzione della procedura M rispetto al raw P2f |
| A1a | vera | parametri temporali stimati di A0, tenuti fissi | Sostituzione della sola varianza individuale nella formula |
| A1b | vera | REML AR(1) ristimata con rumore di cella vero | Effetto aggiuntivo della ristima rispetto ad A1a |
| A2 | stimata | scala e covarianza temporale vere | Sostituzione della componente temporale |
| A3 | vera | scala e covarianza temporale vere | Varianza nota sul disegno fisso; non garantisce code normali |
| A2p (A2′ nel testo) | stimata | scala vera e approssimazione AR(1) lag per lag | Confronto della specifica approssimazione con A2; soltanto 7 e 10 |

Con salti, la covarianza usata dagli oracoli è marginale rispetto alla fase:
K(tau) = max(0, 1 - abs(tau)/L). Lo scenario 7 ha livelli indipendenti nei due
emisferi ma fase dei salti condivisa: covarianza incrociata nulla non significa
indipendenza completa dei due processi. Nello scenario 10 i livelli sono
comuni. Non modificare il generatore storico per correggere una descrizione.

A2p usa phi* = 0,9106 nel 7 e 0,8657 nel 10; kappa* = 0 e 0,98. Nel 10 il
limite 0,98 differisce da kappa = 1 del generatore. Sono valori documentati
della costruzione, non risultati della corsa. Il criterio pesa i ritardi
uniformemente e non ottimizza la proiezione sul contrasto di beta.

## 4. Porta tecnica prima dell'interpretazione

Seguire la [guida del verificatore separato](T5_ORACLE_POSTCHECK_README.md).
Il controllore storico non basta come unica verifica finale: parsing di
`null` e controlli incompleti sono rilievi sul sorgente, non difetti già
osservati nelle tabelle della corsa.

Sequenza prevista dopo la fine della corsa, svolta come registrato nella tabella sotto e in §10:

1. Accertare fine, quattro file completi e assenza di modifiche in corso;
   annotare eventuali esposizioni accidentali a risultati nel log.
2. Rivedere il nuovo verificatore rispetto alla specifica, prima della
   lettura scientifica (fase 1 della revisione, 2026-11-14, §10).
3. Eseguire il controllo separato in una cartella nuova. Conservare anche
   ogni eventuale rapporto fallito, senza sovrascrivere gli originali.
4. Verificare provenienza, hash prima/dopo, chiavi esatte, A0 contro P2f,
   finitezza, intervalli, verità, code, riepiloghi e appaiamenti.
5. Se fallisce un controllo, chiarire la discrepanza prima di adottare una
   sintesi. Se passa, conservare output e controlli prima dell'interpretazione.

Il contratto prevede 32000 cataloghi, 188000 righe raw, 46 gruppi di riepilogo
e 38 confronti appaiati. Queste numerosità sono state verificate dal
controllo separato (tabella sotto) e dal riconteggio di revisione (§10). Le 77 prove del verificatore e i 60 test ordinari del
repository non sono il controllo effettivo di questi output.

**Limite del verificatore, da riportare con i risultati.** Per i bracci
A1a, A1b, A2 e A2p il verificatore controlla soltanto la coerenza interna
(intervalli centrati, semi-intervalli, verdetti, code, riconteggi): non
ricalcola i loro SE. Un SE sbagliato ma usato in modo coerente passerebbe.
Solo A0 ha un riferimento esterno (raw P2f); A3 ha il solo controllo
strutturale dell'SE costante per scenario. Inoltre 77/77 non equivale a 77
verifiche indipendenti: circa nove prove hanno valori attesi fissati a mano,
le altre sono alterazioni o confronti del riconteggio con sé stesso. Un caso
con una riga errore e valori calcolati a mano è stato provato esternamente il
2026-11-14 (`scripts/t5_postcheck_external_probe.py`, fuori dalla ricevuta;
[revisione incrociata](CROSS_REVIEW_2026-11-14.md)).
La prova migliora la trasparenza ma non colma il limite sugli SE: la sua
sufficienza dipende dalle conclusioni che si vorranno sostenere.

| Verifica effettiva | Esito |
|---|---|
| Integrità, provenienza e impronta degli input | Superato: 18 hash degli input, produttore `2bf262f` pulito su ogni riga e nei metadati, 10 prove preliminari |
| Chiavi, numerosità e assenza di duplicati | Superato: 188000 righe, 46 gruppi, 38 confronti, chiavi esatte |
| Riproduzione A0 su tutte le 32000 chiavi pertinenti | Superato; 22 righe errore senza beta nel riferimento P2f, dichiarate e non confrontate numericamente |
| Pendenze uguali fra bracci, verità, stati, intervalli e code | Superato |
| Riconteggio completo del riepilogo e delle matrici appaiate | Superato: tutte le colonne, nessuna inversione di segno, 16 celle per confronto |
| A3 senza errori e SE costante per scenario sul disegno fisso | Superato (controllo strutturale, non di normalità) |
| File invariati durante la lettura | Superato: hash identici prima e dopo |
| SE dei bracci A1a, A1b, A2, A2p | Non ricalcolati dal verificatore: solo coerenza interna (vedi sopra) |
| Rilievi della revisione e loro risoluzione | Fase 1 e fase 2 in §10; rilievi 1–5 della fase 2 corretti in `6e48f3c` |

## 5. Numerosità, denominatori e definizioni

| Cataloghi previsti | N previsto per braccio | Bracci previsti |
|---|---|---|
| Nulla, scenario 7 | 10000 | A0, A1a, A1b, A2, A3, A2p |
| Effetti -0,1 / -0,2 / -0,3 / -0,35, scenario 7 | 2000 per effetto | A0, A1a, A1b, A2, A3, A2p |
| Nulla, scenario 10 | 10000 | A0, A1a, A1b, A2, A3, A2p |
| Nulla, scenario 1 e 2 | 2000 per scenario | A0, A1a, A1b, A2, A3 |

La scala del generatore è eta0 = 3,56e-25 G/Mx, distinta da una media stimata
ora sui dati reali. r = (beta - beta_vero)/eta0; s = SE/eta0; z = r/s.
R = media(s²)/var(r), varianza campionaria con ddof=1; SD(z) con ddof=1;
quantili lineari di z alle probabilità 0,0125 e 0,9875. Il riferimento
normale ha quantili ±Phi^-1(0,9875), non soglie arrotondate nel calcolo.

R, SD(z) e quantili riguardano i casi numerici validi di ciascun braccio:
riportare sempre N valido ed errori. Le frequenze di falsi verdetti,
copertura e code mantengono tutti i tentativi al denominatore. Gli errori
non sono falsi verdetti sotto nulla e sono non copertura sotto effetto,
come nelle convenzioni originali; non eliminarli silenziosamente.
MCSE binomiale della singola frequenza = sqrt(f*(1-f)/N).

Coda inferiore (`below`): beta_vero < lo; coda superiore (`above`):
beta_vero > hi. I valori esattamente agli estremi sono coperti.
I due nomi descrivono la posizione del parametro rispetto all'intervallo,
non il verso fisico del quenching. Errori Monte Carlo e dispersioni delle
simulazioni non sono incertezze sul processo solare osservato.

## 6. Risultati

Valori da `results/T5_ORACLE_POSTCHECK/RECOUNTS.csv`, `PAIR_RECOUNTS.csv` e
`PAIRED_TRANSITIONS.csv` (riconteggio separato). Prima della lettura si è
confrontato `ORACLE_SUMMARY.csv` con `RECOUNTS.csv`: 46 gruppi in entrambi, conteggi
identici, momenti con scarto inferiore a 10⁻¹⁵ (3·10⁻¹⁶ con pandas, 4,4·10⁻¹⁶ con csv/float nella revisione). Percentuali sui tentativi,
MCSE binomiale = sqrt(f(1−f)/N). Il quantile normale di riferimento è
±Phi⁻¹(0,9875) = ±2,2414. Come termine di paragone si citano le soglie P2f
(falsi ≤ 3,0 % e ≤ 1,75 % per verso; copertura ≥ 96,5 %; coda inferiore,
qui `below`, ≤ 2,0 %): **non sono criteri di T5-D2 e non validano nessun braccio**.
Gli oracoli usano quantità vere note solo nelle simulazioni.

### 6.1 Nulla: frequenze e varianza per scenario e braccio

| Scenario | Braccio | N previsto | N osservato / valido / errori | R | Falsi: supportato / opposto / totale | Frequenza ± MCSE |
|---|---|---|---|---|---|---|
| 7 | A0 | 10000 | 10000 / 9996 / 4 | 0,8580 | 160 / 175 / 335 | 3,35 ± 0,18 % |
| 7 | A1a | 10000 | 10000 / 9996 / 4 | 0,8574 | 155 / 177 / 332 | 3,32 ± 0,18 % |
| 7 | A1b | 10000 | 10000 / 10000 / 0 | 0,8569 | 158 / 175 / 333 | 3,33 ± 0,18 % |
| 7 | A2 | 10000 | 10000 / 9996 / 4 | 0,9809 | 94 / 100 / 194 | 1,94 ± 0,14 % |
| 7 | A3 | 10000 | 10000 / 10000 / 0 | 0,9806 | 91 / 99 / 190 | 1,90 ± 0,14 % |
| 7 | A2p | 10000 | 10000 / 9996 / 4 | 0,8547 | 135 / 167 / 302 | 3,02 ± 0,17 % |
| 10 | A0 | 10000 | 10000 / 9992 / 8 | 0,9165 | 103 / 92 / 195 | 1,95 ± 0,14 % |
| 10 | A1a | 10000 | 10000 / 9992 / 8 | 0,9157 | 104 / 90 / 194 | 1,94 ± 0,14 % |
| 10 | A1b | 10000 | 10000 / 10000 / 0 | 0,9155 | 101 / 91 / 192 | 1,92 ± 0,14 % |
| 10 | A2 | 10000 | 10000 / 9992 / 8 | 0,9860 | 56 / 50 / 106 | 1,06 ± 0,10 % |
| 10 | A3 | 10000 | 10000 / 10000 / 0 | 0,9847 | 55 / 49 / 104 | 1,04 ± 0,10 % |
| 10 | A2p | 10000 | 10000 / 9992 / 8 | 0,8639 | 97 / 93 / 190 | 1,90 ± 0,14 % |
| 1 | A0 | 2000 | 2000 / 1997 / 3 | 0,9872 | 33 / 24 / 57 | 2,85 ± 0,37 % |
| 1 | A1a | 2000 | 2000 / 1997 / 3 | 0,9861 | 35 / 25 / 60 | 3,00 ± 0,38 % |
| 1 | A1b | 2000 | 2000 / 2000 / 0 | 0,9872 | 35 / 25 / 60 | 3,00 ± 0,38 % |
| 1 | A2 | 2000 | 2000 / 1997 / 3 | 0,9840 | 31 / 29 / 60 | 3,00 ± 0,38 % |
| 1 | A3 | 2000 | 2000 / 2000 / 0 | 0,9840 | 30 / 27 / 57 | 2,85 ± 0,37 % |
| 2 | A0 | 2000 | 2000 / 1999 / 1 | 0,9527 | 32 / 36 / 68 | 3,40 ± 0,41 % |
| 2 | A1a | 2000 | 2000 / 1999 / 1 | 0,9521 | 32 / 36 / 68 | 3,40 ± 0,41 % |
| 2 | A1b | 2000 | 2000 / 2000 / 0 | 0,9523 | 31 / 35 / 66 | 3,30 ± 0,40 % |
| 2 | A2 | 2000 | 2000 / 1999 / 1 | 0,9685 | 25 / 29 / 54 | 2,70 ± 0,36 % |
| 2 | A3 | 2000 | 2000 / 2000 / 0 | 0,9680 | 24 / 30 / 54 | 2,70 ± 0,36 % |

A0 riproduce i valori P2f e T5-D1 (scenario 7: 335/10000, R = 0,8580).
Tutte le righe errore riguardano i bracci che usano la funzione di varianza
stimata (A0, A1a, A2, A2p); A1b e A3 non ne hanno. Il conteggio massimo di
errori è 8 su 10000 (0,08 %) fra i gruppi da 10000; la frequenza massima fra
tutti i gruppi è 3/2000 (0,15 %), nel controllo 1 e a −0,3.

### 6.2 Scenario 7 sotto effetto: copertura e code

| Effetto | Braccio | N previsto | N osservato / valido / errori | R | Coperti/N; copertura ± MCSE | Below/N | Above/N |
|---|---|---|---|---|---|---|---|
| -0,1 | A0 | 2000 | 2000 / 1998 / 2 | 0,8817 | 1940/2000; 97,00 ± 0,38 % | 29/2000 (1,45 %) | 29/2000 (1,45 %) |
| -0,1 | A1a | 2000 | 2000 / 1998 / 2 | 0,8812 | 1941/2000; 97,05 ± 0,38 % | 30/2000 (1,50 %) | 27/2000 (1,35 %) |
| -0,1 | A1b | 2000 | 2000 / 2000 / 0 | 0,8806 | 1941/2000; 97,05 ± 0,38 % | 30/2000 (1,50 %) | 29/2000 (1,45 %) |
| -0,1 | A2 | 2000 | 2000 / 1998 / 2 | 1,0072 | 1965/2000; 98,25 ± 0,29 % | 15/2000 (0,75 %) | 18/2000 (0,90 %) |
| -0,1 | A3 | 2000 | 2000 / 2000 / 0 | 1,0067 | 1967/2000; 98,35 ± 0,28 % | 15/2000 (0,75 %) | 18/2000 (0,90 %) |
| -0,1 | A2p | 2000 | 2000 / 1998 / 2 | 0,8775 | 1948/2000; 97,40 ± 0,36 % | 26/2000 (1,30 %) | 24/2000 (1,20 %) |
| -0,2 | A0 | 2000 | 2000 / 1999 / 1 | 0,8706 | 1935/2000; 96,75 ± 0,40 % | 24/2000 (1,20 %) | 40/2000 (2,00 %) |
| -0,2 | A1a | 2000 | 2000 / 1999 / 1 | 0,8701 | 1934/2000; 96,70 ± 0,40 % | 24/2000 (1,20 %) | 41/2000 (2,05 %) |
| -0,2 | A1b | 2000 | 2000 / 2000 / 0 | 0,8695 | 1937/2000; 96,85 ± 0,39 % | 23/2000 (1,15 %) | 40/2000 (2,00 %) |
| -0,2 | A2 | 2000 | 2000 / 1999 / 1 | 0,9934 | 1969/2000; 98,45 ± 0,28 % | 12/2000 (0,60 %) | 18/2000 (0,90 %) |
| -0,2 | A3 | 2000 | 2000 / 2000 / 0 | 0,9932 | 1970/2000; 98,50 ± 0,27 % | 12/2000 (0,60 %) | 18/2000 (0,90 %) |
| -0,2 | A2p | 2000 | 2000 / 1999 / 1 | 0,8655 | 1944/2000; 97,20 ± 0,37 % | 24/2000 (1,20 %) | 31/2000 (1,55 %) |
| -0,3 | A0 | 2000 | 2000 / 1997 / 3 | 0,8591 | 1922/2000; 96,10 ± 0,43 % | 46/2000 (2,30 %) | 29/2000 (1,45 %) |
| -0,3 | A1a | 2000 | 2000 / 1997 / 3 | 0,8596 | 1921/2000; 96,05 ± 0,44 % | 45/2000 (2,25 %) | 31/2000 (1,55 %) |
| -0,3 | A1b | 2000 | 2000 / 2000 / 0 | 0,8558 | 1926/2000; 96,30 ± 0,42 % | 44/2000 (2,20 %) | 30/2000 (1,50 %) |
| -0,3 | A2 | 2000 | 2000 / 1997 / 3 | 0,9859 | 1958/2000; 97,90 ± 0,32 % | 24/2000 (1,20 %) | 15/2000 (0,75 %) |
| -0,3 | A3 | 2000 | 2000 / 2000 / 0 | 0,9848 | 1961/2000; 98,05 ± 0,31 % | 24/2000 (1,20 %) | 15/2000 (0,75 %) |
| -0,3 | A2p | 2000 | 2000 / 1997 / 3 | 0,8588 | 1939/2000; 96,95 ± 0,38 % | 34/2000 (1,70 %) | 24/2000 (1,20 %) |
| -0,35 | A0 | 2000 | 2000 / 2000 / 0 | 0,8519 | 1932/2000; 96,60 ± 0,41 % | 36/2000 (1,80 %) | 32/2000 (1,60 %) |
| -0,35 | A1a | 2000 | 2000 / 2000 / 0 | 0,8516 | 1933/2000; 96,65 ± 0,40 % | 37/2000 (1,85 %) | 30/2000 (1,50 %) |
| -0,35 | A1b | 2000 | 2000 / 2000 / 0 | 0,8500 | 1933/2000; 96,65 ± 0,40 % | 38/2000 (1,90 %) | 29/2000 (1,45 %) |
| -0,35 | A2 | 2000 | 2000 / 2000 / 0 | 0,9728 | 1965/2000; 98,25 ± 0,29 % | 18/2000 (0,90 %) | 17/2000 (0,85 %) |
| -0,35 | A3 | 2000 | 2000 / 2000 / 0 | 0,9725 | 1964/2000; 98,20 ± 0,30 % | 18/2000 (0,90 %) | 18/2000 (0,90 %) |
| -0,35 | A2p | 2000 | 2000 / 2000 / 0 | 0,8475 | 1944/2000; 97,20 ± 0,37 % | 24/2000 (1,20 %) | 32/2000 (1,60 %) |

Potenza descrittiva (`supportato`/2000, dagli stati appaiati), effetto −0,3:
A0 52,7 %, A1a 52,6 %, A1b 52,9 %, A2 47,2 %, A3 47,0 %, A2p 51,8 %;
effetto −0,35: A0 64,25 %, A2 58,50 %, A3 58,55 %, A2p 64,0 %. Non è un criterio.

### 6.3 Dispersione e quantili di z (46 gruppi)

z = (beta − beta_vero)/SE sui casi validi; riferimento normale ±2,2414.

| Tipo | Scenario | Effetto | Braccio | N valido | SD(z) | q0,0125 | q0,9875 |
|---|---|---|---|---|---|---|---|
| nulla | 1 | 0 | A0 | 1997 | 1,0237 | -2,3835 | 2,1995 |
| nulla | 1 | 0 | A1a | 1997 | 1,0245 | -2,3446 | 2,2245 |
| nulla | 1 | 0 | A1b | 2000 | 1,0238 | -2,3585 | 2,2178 |
| nulla | 1 | 0 | A2 | 1997 | 1,0087 | -2,2937 | 2,2933 |
| nulla | 1 | 0 | A3 | 2000 | 1,0081 | -2,2993 | 2,2902 |
| nulla | 2 | 0 | A0 | 1999 | 1,0401 | -2,3341 | 2,3599 |
| nulla | 2 | 0 | A1a | 1999 | 1,0401 | -2,3183 | 2,3802 |
| nulla | 2 | 0 | A1b | 2000 | 1,0401 | -2,3324 | 2,3805 |
| nulla | 2 | 0 | A2 | 1999 | 1,0168 | -2,2220 | 2,2977 |
| nulla | 2 | 0 | A3 | 2000 | 1,0164 | -2,2105 | 2,2766 |
| nulla | 7 | 0 | A0 | 9996 | 1,0944 | -2,3276 | 2,3900 |
| nulla | 7 | 0 | A1a | 9996 | 1,0951 | -2,3263 | 2,3943 |
| nulla | 7 | 0 | A1b | 10000 | 1,0953 | -2,3220 | 2,3919 |
| nulla | 7 | 0 | A2 | 9996 | 1,0098 | -2,1136 | 2,1787 |
| nulla | 7 | 0 | A3 | 10000 | 1,0099 | -2,1131 | 2,1760 |
| nulla | 7 | 0 | A2p | 9996 | 1,0819 | -2,2660 | 2,3335 |
| nulla | 10 | 0 | A0 | 9992 | 1,0565 | -2,1593 | 2,1603 |
| nulla | 10 | 0 | A1a | 9992 | 1,0570 | -2,1624 | 2,1560 |
| nulla | 10 | 0 | A1b | 10000 | 1,0571 | -2,1520 | 2,1645 |
| nulla | 10 | 0 | A2 | 9992 | 1,0071 | -2,0331 | 2,0187 |
| nulla | 10 | 0 | A3 | 10000 | 1,0077 | -2,0315 | 2,0279 |
| nulla | 10 | 0 | A2p | 9992 | 1,0760 | -2,1725 | 2,1584 |
| effetto | 7 | -0,1 | A0 | 1998 | 1,0750 | -2,2859 | 2,2737 |
| effetto | 7 | -0,1 | A1a | 1998 | 1,0752 | -2,2721 | 2,2886 |
| effetto | 7 | -0,1 | A1b | 2000 | 1,0757 | -2,2810 | 2,2651 |
| effetto | 7 | -0,1 | A2 | 1998 | 0,9968 | -2,0712 | 2,1184 |
| effetto | 7 | -0,1 | A3 | 2000 | 0,9967 | -2,0614 | 2,1013 |
| effetto | 7 | -0,1 | A2p | 1998 | 1,0680 | -2,2204 | 2,2649 |
| effetto | 7 | -0,2 | A0 | 1999 | 1,0897 | -2,3827 | 2,2242 |
| effetto | 7 | -0,2 | A1a | 1999 | 1,0905 | -2,3581 | 2,2195 |
| effetto | 7 | -0,2 | A1b | 2000 | 1,0904 | -2,4025 | 2,1963 |
| effetto | 7 | -0,2 | A2 | 1999 | 1,0032 | -2,1663 | 2,0460 |
| effetto | 7 | -0,2 | A3 | 2000 | 1,0034 | -2,1613 | 2,0361 |
| effetto | 7 | -0,2 | A2p | 1999 | 1,0748 | -2,3216 | 2,1941 |
| effetto | 7 | -0,3 | A0 | 1997 | 1,0981 | -2,2801 | 2,4313 |
| effetto | 7 | -0,3 | A1a | 1997 | 1,0980 | -2,2992 | 2,4218 |
| effetto | 7 | -0,3 | A1b | 2000 | 1,1003 | -2,2803 | 2,4247 |
| effetto | 7 | -0,3 | A2 | 1997 | 1,0072 | -2,0597 | 2,2010 |
| effetto | 7 | -0,3 | A3 | 2000 | 1,0077 | -2,0680 | 2,2191 |
| effetto | 7 | -0,3 | A2p | 1997 | 1,0792 | -2,2056 | 2,3577 |
| effetto | 7 | -0,35 | A0 | 2000 | 1,0968 | -2,3196 | 2,3275 |
| effetto | 7 | -0,35 | A1a | 2000 | 1,0972 | -2,3162 | 2,3275 |
| effetto | 7 | -0,35 | A1b | 2000 | 1,0981 | -2,3332 | 2,3421 |
| effetto | 7 | -0,35 | A2 | 2000 | 1,0141 | -2,1339 | 2,0802 |
| effetto | 7 | -0,35 | A3 | 2000 | 1,0141 | -2,1346 | 2,0766 |
| effetto | 7 | -0,35 | A2p | 2000 | 1,0865 | -2,2862 | 2,2285 |

### 6.4 Confronti appaiati rispetto ad A0 (38)

Stesse chiavi di catalogo. «Stati uguali» conta tutti i tentativi, comprese
le coppie errore/errore. «Deciso solo in A0» e «deciso solo nel braccio»
contano i passaggi fra deciso (`supportato` o `opposto`) e `non deciso`. L'ultima colonna conta
le transizioni da errore di A0 a uno stato valido del braccio, e viceversa.
Le 16 celle di ogni confronto sono in `PAIRED_TRANSITIONS.csv` (608 righe). Non ci sono
inversioni di segno (`supportato` ↔ `opposto`) in nessun confronto.
Le righe errore di A0 senza beta nel riferimento P2f sono 22. Non hanno un
confronto numerico e compaiono qui solo come stati.

| Tipo | Scenario | Effetto | Braccio | N | Entrambi validi | Stati uguali | Deciso solo in A0 | Deciso solo nel braccio | Errore A0→valido / valido→errore A0 |
|---|---|---|---|---|---|---|---|---|---|
| nulla | 7 | 0 | A1a | 10000 | 9996 | 9991 | 6 | 3 | 0 / 0 |
| nulla | 7 | 0 | A1b | 10000 | 9996 | 9986 | 6 | 4 | 4 / 0 |
| nulla | 7 | 0 | A2 | 10000 | 9996 | 9823 | 159 | 18 | 0 / 0 |
| nulla | 7 | 0 | A3 | 10000 | 9996 | 9817 | 162 | 17 | 4 / 0 |
| nulla | 7 | 0 | A2p | 10000 | 9996 | 9837 | 98 | 65 | 0 / 0 |
| nulla | 10 | 0 | A1a | 10000 | 9992 | 9991 | 5 | 4 | 0 / 0 |
| nulla | 10 | 0 | A1b | 10000 | 9992 | 9989 | 3 | 0 | 8 / 0 |
| nulla | 10 | 0 | A2 | 10000 | 9992 | 9885 | 102 | 13 | 0 / 0 |
| nulla | 10 | 0 | A3 | 10000 | 9992 | 9875 | 104 | 13 | 8 / 0 |
| nulla | 10 | 0 | A2p | 10000 | 9992 | 9875 | 65 | 60 | 0 / 0 |
| nulla | 1 | 0 | A1a | 2000 | 1997 | 1993 | 2 | 5 | 0 / 0 |
| nulla | 1 | 0 | A1b | 2000 | 1997 | 1992 | 1 | 4 | 3 / 0 |
| nulla | 1 | 0 | A2 | 2000 | 1997 | 1979 | 9 | 12 | 0 / 0 |
| nulla | 1 | 0 | A3 | 2000 | 1997 | 1975 | 11 | 11 | 3 / 0 |
| nulla | 2 | 0 | A1a | 2000 | 1999 | 1998 | 1 | 1 | 0 / 0 |
| nulla | 2 | 0 | A1b | 2000 | 1999 | 1997 | 2 | 0 | 1 / 0 |
| nulla | 2 | 0 | A2 | 2000 | 1999 | 1968 | 23 | 9 | 0 / 0 |
| nulla | 2 | 0 | A3 | 2000 | 1999 | 1967 | 23 | 9 | 1 / 0 |
| effetto | 7 | -0,1 | A1a | 2000 | 1998 | 1990 | 6 | 4 | 0 / 0 |
| effetto | 7 | -0,1 | A1b | 2000 | 1998 | 1995 | 2 | 1 | 2 / 0 |
| effetto | 7 | -0,1 | A2 | 2000 | 1998 | 1931 | 56 | 13 | 0 / 0 |
| effetto | 7 | -0,1 | A3 | 2000 | 1998 | 1932 | 53 | 13 | 2 / 0 |
| effetto | 7 | -0,1 | A2p | 2000 | 1998 | 1930 | 31 | 39 | 0 / 0 |
| effetto | 7 | -0,2 | A1a | 2000 | 1999 | 1994 | 4 | 2 | 0 / 0 |
| effetto | 7 | -0,2 | A1b | 2000 | 1999 | 1997 | 1 | 1 | 1 / 0 |
| effetto | 7 | -0,2 | A2 | 2000 | 1999 | 1868 | 120 | 12 | 0 / 0 |
| effetto | 7 | -0,2 | A3 | 2000 | 1999 | 1872 | 114 | 13 | 1 / 0 |
| effetto | 7 | -0,2 | A2p | 2000 | 1999 | 1885 | 57 | 58 | 0 / 0 |
| effetto | 7 | -0,3 | A1a | 2000 | 1997 | 1986 | 8 | 6 | 0 / 0 |
| effetto | 7 | -0,3 | A1b | 2000 | 1997 | 1987 | 4 | 6 | 3 / 0 |
| effetto | 7 | -0,3 | A2 | 2000 | 1997 | 1842 | 134 | 24 | 0 / 0 |
| effetto | 7 | -0,3 | A3 | 2000 | 1997 | 1841 | 136 | 20 | 3 / 0 |
| effetto | 7 | -0,3 | A2p | 2000 | 1997 | 1868 | 75 | 57 | 0 / 0 |
| effetto | 7 | -0,35 | A1a | 2000 | 2000 | 1992 | 4 | 4 | 0 / 0 |
| effetto | 7 | -0,35 | A1b | 2000 | 2000 | 1995 | 2 | 3 | 0 / 0 |
| effetto | 7 | -0,35 | A2 | 2000 | 2000 | 1849 | 133 | 18 | 0 / 0 |
| effetto | 7 | -0,35 | A3 | 2000 | 2000 | 1848 | 133 | 19 | 0 / 0 |
| effetto | 7 | -0,35 | A2p | 2000 | 2000 | 1879 | 63 | 58 | 0 / 0 |

Composizione dei passaggi principali (scenario 7, nulla): A0→A2 perde 75
`supportato` e 84 `opposto` e ne guadagna 9 + 9. A0→A3 perde 77 + 85 e ne
guadagna 8 + 9. A0→A2p perde 53 + 45 e ne guadagna 28 + 37, quindi rimescola
i verdetti invece di restringerli. Sotto effetto A2 e A3 convertono soprattutto
`supportato` in `non deciso` (−0,3: 134 e 136 contro 24 e 20).

### 6.5 Indicatore appaiato delle differenze (aggiunto dopo la revisione)

Indicatore descrittivo, **non pre-registrato e non un test**: non si applica
nessuna soglia, coerentemente con §6.4. Script `scripts/t5_reading_paired_indicator.py`,
output `results/T5_ORACLE_READING/PAIRED_INDICATOR.csv`; legge `ORACLE_RAW.csv.gz` senza modificarlo.
L'evento è il verdetto deciso sotto nulla e la mancata copertura sotto effetto
(errore = mancata copertura). b = evento solo in A0, c = evento solo nel braccio.
La differenza delle frequenze è delta = (c − b)/N. Il suo errore Monte Carlo
appaiato è l'errore standard campionario delle differenze
D_i = evento_braccio_i − evento_A0_i, cioè sqrt((b + c − (c − b)²/N)/(N(N − 1))).
La formula presuppone repliche indipendenti e coppie allineate. N comprende
tutti i tentativi appaiati, errori inclusi. La versione in `3a4add9` usava
l'approssimazione di tipo McNemar sqrt(b + c)/N; il revisore ha indicato la
formula completa, che cambia gli errori al più di 0,003 punti e i rapporti
al più di 0,1. Questo errore è più piccolo della MCSE della singola frequenza
e va usato per le differenze fra bracci.

| Gruppo | Braccio | b / c | Differenza (punti %) | Errore appaiato | Rapporto |
|---|---|---|---|---|---|
| 7 nulla | A1a / A1b | 6/3; 6/4 | −0,03; −0,02 | 0,03 | −1,0; −0,6 |
| 7 nulla | A2 / A3 | 159/18; 162/17 | −1,41; −1,45 | 0,13 | −10,7; −10,9 |
| 7 nulla | A2p | 98/65 | −0,33 | 0,13 | −2,6 |
| 7, −0,3 | A1a / A1b | 2/3; 6/2 | +0,05; −0,20 | 0,11; 0,14 | +0,4; −1,4 |
| 7, −0,3 | A2 / A3 | 38/2; 41/2 | −1,80; −1,95 | 0,31; 0,33 | −5,7; −6,0 |
| 7, −0,3 | A2p | 27/10 | −0,85 | 0,30 | −2,8 |
| 10 nulla | A2 / A3 | 102/13; 104/13 | −0,89; −0,91 | 0,11 | −8,3; −8,4 |
| 10 nulla | A2p | 65/60 | −0,05 | 0,11 | −0,4 |
| 1 nulla | A2 / A3 | 9/12; 11/11 | +0,15; 0,00 | 0,23 | +0,7; 0,0 |
| 2 nulla | A2 / A3 | 23/9; 23/9 | −0,70; −0,70 | 0,28 | −2,5; −2,5 |

Le 38 righe complete sono nel CSV. Per A1a e A1b il rapporto resta entro ±1,8 in tutti i gruppi.
Sono 38 confronti descrittivi: un singolo rapporto intorno a 2,5 non va
letto come un risultato forte.

## 7. Lettura vincolata all'emendamento A1

Questa griglia riporta le letture già registrate, non nuove decisioni.
«Vicino al riferimento» e «nel limite» restano confronti descrittivi con
incertezza Monte Carlo; non sono una nuova accettazione di T5. Leggere
insieme varianza, code, copertura, errori e cambiamenti appaiati.

| Confronto previsto | Lettura consentita se osservato | Cosa non conclude |
|---|---|---|
| A2 vicino al riferimento (R circa 1 e falsi verdetti nel limite), A1a no | Compatibile con un ruolo principale della componente temporale, modello e stima, in questi cataloghi | Non identifica un difetto unico o un metodo correttivo già valido |
| A1a vicino al riferimento, A2 no | Compatibile con un ruolo principale della varianza individuale nella formula | Non dimostra che la forma della funzione sia la sola causa |
| A1b differisce da A1a | La ristima temporale cambia il risultato quando si cambia la varianza individuale | Non dimostra una specifica interazione |
| Solo A3 vicino al riferimento | La sostituzione congiunta migliora la calibrazione in questi cataloghi | Non isola una causa né dimostra un'interazione |
| Neppure A3 migliora le code o le frequenze | Compatibile, tra le altre spiegazioni, con un ruolo della forma non gaussiana rispetto al riferimento normale | La varianza vera non rende automaticamente normale la distribuzione |
| A2p vicino o distante da A2 | Descrive l'effetto della specifica approssimazione lag per lag | Non dimostra adeguatezza o inadeguatezza generale di ogni AR(1) |
| Controlli 1 e 2 anomali | Riportare lo scarto e riesaminare la diagnosi con cautela | Non ignorarli perché lo scenario d'interesse è il 7 |

Il confronto A2p–A0 cambia anche la scala temporale stimata in quella vera:
non attribuirlo esclusivamente a phi o kappa. Nel confronto A2p–A2 resta
la stessa componente individuale stimata e cambia la covarianza temporale
specificata. Nessuna conclusione va dedotta dal solo R, né da una sola
combinazione scelta dopo aver visto i risultati.

Il §7 del protocollo congelato legge A2′ in modo generale («se A2′ resta
vicino ad A0, la forma AR(1) è inadatta ai salti»). In base ad A1 §3, che
qualifica A2′ come la specifica approssimazione lag per lag, quella lettura
generale **non si adotta**: l'esito di A2′ descrive solo questa
approssimazione. Allo stesso modo l'«indizio» del protocollo §1 (eccesso di
falsi verdetti dovuto all'errore standard stimato) è più forte di quanto
T5-D1 ha stabilito e non va riportato come risultato.

### 7.1 Interpretazione effettiva (2026-11-15, Claude Opus 5.5, su `27a9c7d`)

Lettura scritta dopo il controllo 54/54 e la conservazione degli output.
Riguarda soltanto i confronti fra bracci in questi cataloghi sintetici. Si
leggono insieme varianza, falsi verdetti, code, copertura e cambiamenti appaiati.

**Fatti osservati, scenario 7 (livelli ±1 indipendenti fra emisferi, fase dei salti condivisa).**

1. *Varianza individuale vera (A1a, A1b).* Produce cambiamenti piccoli
   rispetto ad A0 nelle misure considerate. Sotto nulla: R = 0,857 in entrambi; falsi 3,32 % e 3,33 %
   contro 3,35 %; al massimo 10 su 10000 cataloghi cambiano stato decisionale.
   Sotto effetto −0,3: copertura 96,05 % e 96,30 % contro 96,10 %, `below`
   2,25 % e 2,20 % contro 2,30 %. A1b è simile ad A1a, non identico:
   nello scenario 7 sotto nulla 23 cataloghi su 10000 cambiano stato; la differenza
   dei falsi A1b−A1a è +0,01 punti (errore appaiato circa 0,044), a −0,3 quella di mancata copertura
   −0,25 punti (circa 0,18). La ristima temporale con la varianza individuale
   vera cambia poco il risultato. Nessuno di questi confronti dimostra
   un'equivalenza o l'assenza di un contributo individuale.
2. *Componente temporale vera (A2).* R = 0,981, SD(z) = 1,010, falsi
   194/10000 = 1,94 ± 0,14 % (0,94 % e 1,00 % per verso). Sotto −0,3:
   copertura 97,90 ± 0,32 %, `below` 1,20 %. Il cambiamento è appaiato e
   simmetrico fra i due versi: 159 decisioni di A0 diventano `non deciso`, 18
   fanno il contrario. A2 **non è una calibrazione esatta**: i falsi sono
   circa 4 MCSE sotto il nominale del 2,5 % e la copertura sotto effetto è
   97,9–98,5 % contro il 97,5 % nominale. Con la varianza vera l'intervallo
   è conservativo in questi cataloghi e la potenza scende (§6.2).
3. *Entrambe vere (A3).* Coincide con A2 entro pochi cataloghi: R = 0,981;
   falsi 1,90 %; copertura a −0,3 98,05 %. Quando la componente temporale è
   vera, rendere vera anche quella individuale non aggiunge nulla di osservabile.
4. *Approssimazione AR(1) lag per lag con scala vera (A2p).* Resta molto più
   vicina ad A0 che ad A2: R = 0,855; falsi 3,02 ± 0,17 %; copertura a −0,3
   96,95 % con `below` 1,70 %. Rispetto ad A0 c'è però una riduzione appaiata
   piccola ma non nulla: −0,33 punti di falsi (rapporto −2,6, §6.5) e −0,85
   punti di mancata copertura a −0,3 (rapporto −2,8). Per A2 i valori sono
   −1,41 e −1,80. I verdetti di A2p si rimescolano (98 persi, 65 nuovi)
   invece di restringersi soltanto. Nello scenario 10 la differenza da A0 è piccola e non risolta (−0,05 ± 0,11).
5. *Code.* Con la varianza vera (A2, A3) i quantili di z sono −2,11 e +2,18
   sotto nulla, dentro ±2,24. Ai livelli e alle soglie esaminati
   (quantili 1,25 % e 98,75 %, intervallo al 97,5 %) la distribuzione
   standardizzata è quindi meno estrema del riferimento normale, e i falsi
   verdetti sono meno del nominale (1,9 % contro 2,5 %). Lo stesso succede
   nello scenario 10 (quantili ±2,03, falsi 1,04 %). A quelle soglie lo
   scarto va nel verso opposto a quello che avrebbe fatto fallire anche A3.
   Non è una descrizione dell'intera forma delle code né una prova di
   normalità o non normalità.

**Scenario 10 (livelli comuni).** A0 era già nelle soglie: R = 0,917, falsi
1,95 %. A2 e A3 portano R a 0,986 e 0,985 e i falsi all'1,06 % e all'1,04 %. A2p dà
invece R = 0,864, più basso di A0, con falsi 1,90 %. Qui l'approssimazione usa
kappa = 0,98, mentre il generatore ha kappa = 1. Il limite resta dichiarato e
non è separabile dal resto.

**Controlli 1 e 2 (AR(1)).** A0, A2 e A3 sono vicini, come atteso dal
protocollo. Scenario 1: R da 0,984 a 0,987, falsi da 2,85 % a 3,00 %.
Scenario 2: R di A0 0,953 con falsi 3,40 ± 0,41 %, A2 0,969 e A3 0,968, entrambi con 2,70 %.
Nello scenario 2 lo scarto A0–A2 è di 23 contro 9 decisioni appaiate,
−0,70 punti con errore appaiato 0,28 (rapporto −2,5, §6.5). Una prima
stesura di questo rapporto lo descriveva come «circa 1–2 MCSE»: quel calcolo
usava la MCSE della singola frequenza e sottostimava lo scarto, come ha
rilevato la revisione. Lo scarto non è grande, ma non è trascurabile; resta
uno fra molti confronti descrittivi e non è una conclusione forte. Nello
scenario 2 la forma AR(1) di M è quella giusta, quindi A0 e A2 differiscono
solo per la stima dei parametri temporali (phi = 0,9). Lo scarto **suggerisce** un
contributo della stima REML alla perdita di calibrazione anche quando la forma
è corretta. È circa metà, in punti, di quello dello scenario 7 (−1,41), ma gli
scenari differiscono anche per altro e il confronto non scompone le cause.
Nello scenario 1 (phi = 0,5) lo scarto è piccolo e non risolto (+0,15 ± 0,23, rapporto +0,7).
Seguendo il protocollo, lo si riporta e si legge la diagnosi con cautela. Come riferimento ideale, non come errore Monte Carlo misurato
di R, la varianza campionaria di dati gaussiani indipendenti ha errore
relativo sqrt(2/(N−1)), circa 0,014 per N = 10000 e 0,032 per N = 2000.
Per questi bracci non vale come MCSE di R: il numeratore di R è stimato e
può essere correlato con il denominatore, e gli scenari a salti non sono gaussiani.

**Lettura secondo A1 §2.** Si realizza la prima riga della griglia: A2 è
vicino al riferimento (R ≈ 1, falsi entro il 3,0 % e per verso entro
l'1,75 %; sotto il nominale, quindi conservativo), A1a no. L'esito è **compatibile con un ruolo principale della
componente temporale (modello AR(1) e sua stima) nello scenario a salti, in
questi cataloghi**. Non identifica un difetto unico e non costituisce un
metodo correttivo. A1b simile ad A1a (scarti piccoli, non nulli): la terza riga non si attiva. Non si
realizzano né «solo A3» né «neppure A3», perché A2 basta e A3 non aggiunge.
Il §1 del protocollo congelato parlava di un «indizio» e il §5 di «la causa
principale è»: queste formulazioni non si adottano.

**A2p.** In base ad A1 §3, a parità di scala temporale vera e di varianza
individuale stimata, sostituire K_steps con *questa* approssimazione AR(1)
(criterio lag per lag a pesi uguali, non proiettato sul contrasto di beta)
conserva una parte minore del miglioramento di A2 (§6.5): sotto nulla
−0,33 contro −1,41 punti (circa un quarto), a −0,3 −0,85 contro −1,80
(circa metà), nello scenario 10 −0,05 ± 0,11 (non risolto).
Ciò restringe le spiegazioni ma non chiude la questione, e descrive solo questa
approssimazione. Non dimostra che ogni AR(1) sia inadatta ai salti. La lettura
generale del §7 del protocollo congelato resta non adottata. Il confronto
A2p–A0 cambia sia la scala sia la forma e non si attribuisce a phi o kappa.

**Che cosa resta non distinto.** Non si sa quanto A0 perda calibrazione per la
forma AR(1) in sé e quanto per la stima REML dei suoi parametri. Lo scarto
dello scenario 2 suggerisce che la stima possa contare anche con la forma giusta,
ma non misura la sua quota nello scenario 7. A2p non è la
migliore AR(1) per il contrasto, e nessun braccio usa una forma AR(1)
ottimizzata con i parametri veri. Resta anche aperto quanto della leggerezza
delle code dipenda dai livelli ±1 e quanto dal disegno fisso.

**Limite degli SE dei bracci, da leggere con quanto sopra.** La lettura poggia
soprattutto sugli SE di A2 e A3. Il verificatore separato non ha ricalcolato
gli SE di A1a, A1b, A2 e A2p: ne ha controllato soltanto la coerenza interna.
Per A3 c'è solo il controllo strutturale (SE costante per scenario). Un SE di
A2 sbagliato ma usato coerentemente avrebbe superato i controlli. La
concordanza A2 ≈ A3 e il comportamento atteso nei controlli 1–2
(A0 ≈ A2 ≈ A3) sono coerenze indirette, non un ricalcolo indipendente. Una
stesura precedente diceva che per A2 servisse rieseguire il produttore: è
inesatto. Il sorgente (`diag_t5_oracle.py`, righe 90–130) separa generazione
dei cataloghi, funzione di varianza e costruzione degli oracoli. A2 e A3 non
richiedono la REML; A2 richiede comunque la stima della funzione di varianza
(`P.varfun_fit`), quindi non è privo di ottimizzazione. È proposto un
controllo separato: rigenerazione di tutti i cataloghi dai semi e ricalcolo
indipendente della costruzione degli oracoli, con componenti, contrasto e
beta. **Non è ancora pianificato né svolto.** Se superato, verificherebbe la
costruzione degli oracoli entro le dipendenze condivise (generatore, celle,
funzione di varianza), non tutta la catena. Fino ad allora vale il limite
descritto sopra.

## 8. Incidenti, discrepanze ed esposizioni da rendicontare

Conservare separati fatti documentati, segnalazioni dell'operatore e
verifiche ancora da fare. Non cancellare i primi tentativi o correggere
retroattivamente il protocollo congelato.

- Prova tecnica su quattro cataloghi: già dichiarata nell'emendamento A1.
- Confusione wrapper/Python e secondo avvio interrotto senza scrittura:
  episodio riferito dalla sessione di esecuzione. Resta una segnalazione
  dell'operatore: i dettagli tecnici non sono ricostruibili dai file e
  nessuna revisione li ha certificati. Il log conferma soltanto i 16 contatori
  e il marcatore finale, non il codice di uscita né l'intera storia dei
  processi. Non è un secondo run scientifico completato.
- Fascia di semi della verifica preliminare di covarianza dello scenario
  10: il codice usa 28200000+k, mentre la formulazione generale del piano
  indica 28000000+k. Dichiarare la differenza del solo pretest, senza
  modificarlo né confonderla con i semi dei cataloghi dell'esecuzione.
- Log della corsa (`logs/t5_oracle.log`, 17 righe): contiene soltanto i
  contatori di avanzamento e `fatto`. Nessuna tabella o sintesi è stata vista
  prima del controllo. Nel controllo e nella lettura nessuna ricomputazione ha
  cambiato i numeri. Il riconteggio di questa lettura legge `null` come
  stringa (`keep_default_na=False`). È una precauzione di lettura, non un
  difetto degli output.
- Esposizioni dell'interprete: Claude Opus 5.5 ha partecipato al progetto,
  alla stesura dell'emendamento e alla revisione incrociata di fase 1.
  L'interpretazione non è cieca. La griglia di lettura era fissata prima (A1 §2).
- Già documentata la fase comune dei salti del 7: correggere nel rapporto
  eventuali descrizioni di indipendenza completa, lasciando il generatore intatto.

## 9. Conclusioni e possibili passi successivi

**Conclusioni (2026-11-15), descrittive e limitate a questi cataloghi sintetici.**

- *Cosa cambia negli oracoli.* Rendere vera la componente temporale (scala e
  covarianza dei salti) riporta R vicino a 1 e i falsi verdetti sotto il
  nominale nello scenario 7. Rendere vera la sola varianza individuale, con o
  senza ristima, produce cambiamenti piccoli. L'approssimazione AR(1) lag per lag
  specificata, con scala vera, ne riproduce solo una parte minore. Con la
  varianza vera l'intervallo diventa conservativo, non esatto.
- *Quali spiegazioni restano compatibili.* Un ruolo principale della
  componente temporale come modellata e stimata da M (AR(1) + REML) nello
  scenario a salti. La sostituzione della varianza individuale, con o
  senza ristima temporale, produce cambiamenti piccoli nelle misure considerate
  e non sostiene un suo ruolo principale in questa diagnosi. Non è una
  dimostrazione di equivalenza né dell'assenza di un contributo individuale.
  Non si attribuisce una causa unica.
- *Cosa non è distinguibile.* Non si separano le quote della forma AR(1) in sé
  e della stima dei suoi parametri; lo scenario 2 suggerisce che la stima possa
  contare anche con la forma giusta. Non si distingue l'effetto della specifica
  proiezione A2p da quello di un'AR(1) qualunque. Non si separa l'origine
  delle code leggere.
- *Cosa mancherebbe per un metodo sui dati reali.* Una stima della
  covarianza temporale che non conosca la verità e catturi la dipendenza su
  circa 20 CR. Esempi del protocollo, non scelti: una covarianza più
  flessibile o un SE robusto alla dipendenza. Va considerato anche che
  in questi cataloghi la varianza vera rende l'intervallo conservativo e
  riduce la potenza: a −0,3, 47,2 % con A2 contro 52,7 % di A0. Non si trasferisce questo numero ai dati reali.
- La diagnosi non rende T5 irrisolvibile con HMI. Non si riscala nessun SE con
  questi esiti e non si elimina lo scenario 7.
- I risultati sono condizionati al limite degli SE dei bracci descritto in §7.1.

Dopo la verifica, separare: cosa cambia negli oracoli, quali spiegazioni
restano compatibili, cosa non è distinguibile e quali informazioni
mancherebbero per un metodo utilizzabile sui dati reali. Se la diagnosi è
ambigua, non chiamare T5 irrisolvibile con HMI.

Qualunque candidata successiva deve essere applicabile senza conoscere
le varianze vere; richiede un piano proprio e una validazione con semi
nuovi e scenari fissati prima, incluso il 7. Non si elimina lo scenario
fallito, non si riscalano gli errori standard usando questi esiti e non
si applica T5 reale in base al solo controllo degli oracoli.

Fino a quel passaggio, T5 rimane descrittivo e T3 conserva il risultato
non deciso già registrato. Morfologia, misura P1 e risultati osservativi
restano distinti dalla diagnosi sintetica qui preparata.

## 10. Revisione e conservazione

Richiesta per l'altro agente in [T5_ORACLE_REVIEW_REQUEST.md](T5_ORACLE_REVIEW_REQUEST.md).

Fase 1 svolta il 2026-11-14 da Claude Opus 5.5 sul commit `f38d351`, senza
aprire gli output: [revisione incrociata](CROSS_REVIEW_2026-11-14.md). Nessun
problema bloccante per le attività esaminate, senza approvare conclusioni
T5-D2; verificatore e protocolli invariati; precisazioni
documentali applicate. Un secondo revisore ne ha condiviso le conclusioni.
Non è una revisione cieca né la revisione dell'interpretazione (fase 2).

Interpretazione inserita il 2026-11-15 (Claude Opus 5.5, su `27a9c7d`; commit `70ea4bb`).
Primo parere di Codex, 2026-11-15, basato **solo sul riepilogo** e non sul
rapporto: non certifica i risultati. Rilievi:
(1) A2 non dimostra una calibrazione esatta: è conservativo, con copertura più alta e potenza più bassa;
(2) A2p restringe le spiegazioni senza separare forma e stima;
(3) le differenze piccole richiedono l'errore Monte Carlo appaiato;
(4) il ricalcolo indipendente degli SE di A2 e A3 è il controllo mancante più utile.
Risposte in questo commit: (1) e (2) recepiti in §7.1 e §9; per (3) è stato
aggiunto l'indicatore appaiato in §6.5, che corregge la frase sullo scenario 2
(prima «1–2 MCSE», ora rapporto −2,5) e la descrizione di A2p (piccola
riduzione appaiata, prima «vicina ad A0»). Il punto (4) resta aperto.
Secondo parere di Codex, 2026-11-15, ancora senza revisione completa del
commit: chiede di non leggere il rapporto −2,5 dello scenario 2 come
conclusione forte e di usare la formula completa dell'errore appaiato.
Entrambe le richieste sono recepite nel commit successivo a `3a4add9`. Per il
ricalcolo degli SE preferisce tutti i cataloghi, il confronto anche delle
componenti della varianza e del contrasto, e la distinzione fra errori attesi
e inattesi. Questo parere non è l'esito della revisione di fase 2.

**Revisione di fase 2 (Codex, 2026-11-15, commit `8c7801a`)**, non cieca;
artefatti in `MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/reviews/T5_D2_CODEX_8c7801a/`,
fuori da questo repository. Codex ha ripetuto il verificatore separato (54/54) e
ha fatto un riconteggio indipendente con la sola libreria standard di tutte le
tabelle §6.1–6.5, delle 608 celle e delle 38 righe dell'indicatore appaiato.
Ha confrontato A0 con le 32000 chiavi P2f e verificato gli hash: nessuna
discrepanza. Esito: nessun problema bloccante nell'integrità degli output, nei
riconteggi o nelle tabelle. La lettura centrale (prima riga di A1) è coerente,
condizionata alla correttezza degli SE salvati. Non verifica la diagnosi in
ogni sua parte, perché resta aperto il ricalcolo indipendente degli SE degli oracoli. Rilievi
*da correggere*: (1) la conclusione sulla varianza individuale era più forte
dell'evidenza; (2) la spiegazione tecnica del limite sugli SE era superata.
Rilievi *minori*: (3) imprecisioni numeriche nella prosa; (4) «nullo» invece di
«piccolo/non risolto» e descrizione delle code da circoscrivere; (5)
sqrt(2/(N−1)) non è una MCSE di R; (6) note di preparazione da riallineare.
Risoluzione: (1)–(5) corretti in `6e48f3c`; (6) chiuso nel commit successivo
(segnaposto e note di preparazione riallineati), senza trasformare in fatto
verificato la segnalazione del secondo avvio interrotto.

**Verifica delle correzioni (Codex, 2026-11-15, su `6e48f3c` e `0cdabc3`).**
Rilievi 1–5 recepiti; nessun'altra correzione sostanziale. Hash dei 19 file
pertinenti invariati, tabelle non modificate: il riconteggio e il 54/54
restano validi. Codex considera la parte interpretativa revisionata entro
l'ambito dichiarato, con la conclusione condizionata agli SE salvati. Il
ricalcolo indipendente degli SE di A2 e A3 è un controllo distinto, con
nota tecnica congelata prima dell'esecuzione; non è considerato superato.
Nessuna di queste revisioni è cieca: revisore e autore conoscevano il
progetto e i riepiloghi.

# T5-D2 — specifica del verificatore finale separato

Registrata prima del nuovo codice e prima di aprire gli output scientifici
T5-D2. Controllo tecnico non cieco rispetto a protocollo, A1 e revisione del
codice. Non introduce una regola inferenziale, non modifica le simulazioni
o il loro stato scientifico. Il codice di produzione e i suoi output restano
intatti. Questa specifica si conserva invariata dopo la registrazione.

## 1. Riferimenti e porta di esecuzione

Produttore atteso: `2bf262f1b99d6a884ed72686047dc089911e5eff`, con albero pulito,
come nei dieci controlli preliminari registrati. Il commit del verificatore
e l'HEAD successivo possono essere diversi e sono registrati separatamente.
Gli SHA attesi di protocolli, moduli, dati pubblicati e controlli preliminari
sono in `T5_ORACLE_POSTCHECK_INPUTS_SHA256.csv`, acquisiti senza leggere gli
output della corsa. La validazione P2f di riferimento ha produttore
`5c3b664bb3e6bbdddd8a9502801163ed9873ce49`.

La modalita di controllo effettivo richiede il marcatore finale `fatto` nel
log e tutti i quattro output: ORACLE_RAW.csv.gz, ORACLE_SUMMARY.csv,
ORACLE_PAIRED_VS_A0.csv, ORACLE_META.json. Se mancano, non legge i risultati.
Hash degli output prima e dopo il controllo impediscono di adottare un
confronto su file cambiati durante la lettura. Gli output del verificatore
vanno in una cartella distinta nuova, mai nei file originali.

La modalita --selftest usa esclusivamente tabelle costruite a mano, senza
cataloghi reali o sintetici di produzione, generatori, ottimizzazioni o RNG.
Il controllo reale richiede l'esito dei test sullo stesso SHA del codice e
della specifica, non sullo stesso HEAD: un commit documentale non richiede
la ripetizione di test sul codice invariato.

## 2. Contratto delle tabelle

- 32000 cataloghi: nulla 7 e 10, 10000 ciascuno; quattro effetti del 7
  (-0,1, -0,2, -0,3, -0,35), 2000 ciascuno; nulla 1 e 2, primi 2000 ciascuno.
- A0/A1a/A1b/A2/A3 per tutti; A2p soltanto per 7 e 10. Esattamente 188000
  righe raw, 46 gruppi di riepilogo e 38 confronti appaiati con A0.
- Chiavi complete ed esatte, nessun duplicato; interi finiti senza
  troncamento; effetti canonici con Decimal, senza abbinamenti isclose.
  La stringa `null` resta una stringa in ogni lettura.
- Produttore, albero pulito e tutti gli SHA registrati verificati su ogni
  riga e nei metadati; controllo separato del codice attuale contro la
  fotografia registrata del produttore. Nessuna pretesa di ricostruire
  retroattivamente uno SHA che il produttore non ha salvato.
- Metadati: N lavori, phi_star 0,9106/0,8657, kappa_star 0/0,98,
  sigma_i^2=eta0^2 e sigma_x^2=(0,5 eta0)^2. eta0=3,56e-25 G/Mx.

## 3. Controlli sul raw e su A0

La pendenza e il valore vero sono finiti anche nelle righe errore e la
pendenza e identica tra bracci dello stesso catalogo. Il valore vero e
zero sotto nulla, effetto*eta0 sotto effetto. Quattro soli stati ammessi:
supportato, opposto, non deciso, errore. A3 non da errore.

Nelle righe valide SE e finito e positivo; intervalli finiti, ordinati e
centrati sulla pendenza. I due semi-intervalli sono verificati separatamente
con q=Phi^-1(0,9875) a precisione completa (tolleranza standardizzata 1e-9).
Si ricalcolano verdetto e indicatori binari covered/below/above dagli estremi
e dal valore vero. Gli indicatori errore sono zero, con motivazione presente
e SE/intervallo mancanti; nessun errore diventa un non deciso.

A3 ha varianza nota sul disegno fisso: SE deve essere costante entro ciascuno
scenario, anche tra nulla ed effetti. Questo e un controllo strutturale,
non una nuova verifica della normalita o una calibrazione statistica.

A0 viene abbinato uno a uno a tutte le 32000 chiavi pertinenti del raw P2f,
verificando stati identici. Pendenze e SE presenti nel riferimento si
confrontano entro errore relativo 1e-9; un riferimento zero richiede zero.
Gli estremi si confrontano in scala |beta_ref|+q*SE_ref, tolleranza 1e-9.
Pendenze assenti nel riferimento per righe errore sono contate e dichiarate:
non si fingono confronti dove il valore originale non e stato conservato.

## 4. Riconteggi e confronti

N, errori, coperti, code, verdetti per verso e falsi verdetti sotto nulla
si ricalcolano dal raw, con conteggi esatti. Le frequenze hanno denominatore
tutti i tentativi; gli errori sono non copertura e non falsi verdetti.
MCSE binomiale sqrt(f*(1-f)/N) per le frequenze salvate.

R, SD(z), quantili di z sono ricalcolati solo sui casi numerici validi per
braccio. r=(beta-beta_vero)/eta0, s=SE/eta0, z=r/s; R=media(s^2)/var(r)
con varianza campionaria ddof=1; SD(z) ddof=1. Quantili lineari ordinati
alle probabilita 0,0125 e 0,9875. Servono almeno due casi validi e var(r)>0.
I momenti e i quantili usano aritmetica separata dal riepilogo originale;
tolleranza tecnica 1e-12+1e-9*|atteso| sulle quantita adimensionali. Le
verita iniettate non nulle hanno errore relativo massimo 1e-12; lo zero
e esatto. Queste tolleranze verificano la serializzazione e l'aritmetica,
non cambiano soglie o regole scientifiche.

Ogni colonna del riepilogo originale viene ricontrollata: anche rapporti,
MCSE, errori, code e conteggi separati. I campi dei falsi verdetti restano
non applicabili negli effetti. Non si correggono i valori salvati.

Per ogni braccio rispetto ad A0 si ricostruiscono n, same e i due conteggi
deciso/non-deciso del file appaiato originale, senza equiparare errore a
non deciso. Si conserva inoltre una matrice 4x4 completa, incluse transizioni
da/a errore, e il numero di casi entrambi validi. Le matrici devono coprire
esattamente tutti i tentativi; nessun confronto suggerisce campioni validi
identici quando non lo sono. I verdetti non possono passare direttamente
da supportato a opposto a pendenza identica con intervalli simmetrici.

## 5. Prodotti, arresto e test

Script separato `python/sharpbl/t5_oracle_postcheck.py`, senza importare il
produttore o la sua funzione summarize. Risultati tecnici, riconteggi,
matrici appaiate e metadati in `results/T5_ORACLE_POSTCHECK/`, con hash dei
quattro input, codice, specifica, manifest di riferimento e ricevuta dei test.
Gli input non si sovrascrivono; codice di uscita 0 solo se tutti i controlli
passano. Un fallimento conserva le verifiche tecniche e la provenienza e
impedisce l'adozione delle sintesi. Lo script non stampa i risultati
scientifici, ma solo stato dei controlli e nomi degli eventuali fallimenti.

I test costruiti a mano devono includere: caso corretto con `null`, tutti
gli stati e un beta esattamente zero; A0 errore con beta originale assente;
limiti chiusi della copertura; normalizzazione stretta delle chiavi;
varianze e quantili noti; transizioni da/a errore. Devono essere respinte
alterazioni di chiavi, verita, code, verdetti, semi-intervalli, dati A0,
R/quantili/frequenze/MCSE, conteggi appaiati, provenienza e metadati. I test
devono provare anche il rifiuto di un rapporto selftest riferito ad altro
codice e la mancata lettura degli output quando non c'e il marcatore finale.

La revisione ha osservato un difetto di parsing e verifiche incomplete nel
controllore originale. Il nuovo controllore non modifica quella versione,
ne richiede nuove simulazioni. Il suo superamento non valida T5, non
identifica una causa unica e non autorizza applicazioni ai dati reali.

# Pilota MDI — revisione Codex della rev. 3, 23 novembre 2026

Oggetto: bozza 4385692. Q1–Q3 circoscritti e Q4 rinviato: impostazione approvata.
Campionamento M1/U, pesi delle due fasi, immagini A/B, angoli, stato equatoriale e limiti descrittivi
recepiscono la revisione precedente. Non occorre allargare il pilota o scrivere altro codice prospettico.

**Via al congelamento dopo due precisazioni testuali sotto**, mantenendo le regole MDI e il campione invariati.
Dopo il congelamento: implementazione e revisione del codice prima di qualsiasi misura MDI o rete scientifica.

## 1. Precisione della conversione CT a periodo medio

carrington_continuous_from_date è una conversione a periodo sinodico medio. È stata controllata direttamente
sui T_ROT in TAI, convertiti in UTC, dei 193 header conservati: lo scarto da CARRTIME arriva a 2,66252 gradi.
Non è quindi appropriato promettere un test a precisione di pixel con questa funzione.

La stessa scelta di N è stata confrontata con una conversione basata su L0 di Meeus ed effemeridi su 29280
righe DPD nel periodo e nei tagli preliminari: nessuna divergenza. Non è una selezione del pilota e non usa tilt.
L'approssimazione è ammissibile per la scelta dell'intero N; non dimostra accuratezza temporale o geometrica
per usi diversi. Il centro effettivo della finestra rimane la longitudine DPD, non CT(t) da solo.

Precisazione pronta per la bozza:

> La funzione a periodo medio è usata soltanto per scegliere N e per tempi nominali dichiarati approssimati.
> Nei controlli sugli header T_ROT, la tolleranza è 3 gradi (non una tolleranza di misura del tilt o dei pixel).
> Il riconteggio ricostruisce N con effemeridi/L0 indipendenti e confronta le assegnazioni; una divergenza
> resta un caso esplicito da esaminare prima delle misure. Coordinate e pixel sono ricavati dall'header e
> da CT_g basato su L_DPD. La composizione temporale effettiva dei pixel resta indeterminata.

Questo valore fissa prima delle misure il test dell'approssimazione nota; non allarga soglie su risultati
scientifici. Non usare l'errore in CT come precisione garantita del confronto fra strumenti.

## 2. Casi BLANK per l'identità MWO

Nei 11165 record delle due tabelle di DESIGN R4, n_blank_win è sempre zero. Non esistono quindi tre record
R4 selezionati con BLANK, come assunto nella bozza e nel messaggio di consegna. Non inventarli né cambiare
retroattivamente il catalogo.

Precisazione pronta:

> Il sottoinsieme R4 usa due record per epoca/emisfero presente, ordinati per NOAA e giorno. Gli ulteriori
> casi con n_blank_win>0 si prendono fino a tre se presenti; la loro assenza è dichiarata. Le prove BLANK
> includono obbligatoriamente casi sintetici sotto e sopra il 5%. Come controllo reale aggiuntivo di stato
> e conteggi si possono usare i primi tre tentativi window_blank di ATTEMPTS R4 ordinati per NOAA/giorno,
> confrontando coi dati già conservati, senza produrre un nuovo catalogo o statistiche di tilt.

Il campo si chiama n_blank_win nel DESIGN e n_blank_window nel rilascio. Nelle ATTEMPTS ci sono 23 rifiuti
window_blank, quindi la prova reale degli stati è disponibile. Usare le regole originarie MWO, non quelle MDI.

## Osservazione non bloccante sulle finestre di quiete

Con B0=0, centro del gruppo al meridiano/equatore e finestre quiete centrate a +/-30 gradi con semilarghezza
8 gradi in longitudine, la sola proiezione cos(38 gradi) è circa 0,788, già sotto 0,8. Entrambe possono quindi
essere scartate anche per una regione centrale. La bozza ammette la dispersione non disponibile: la regola può
restare, ma aspettarsi e riportare questa perdita. Non cambiare finestre dopo averne letto la dispersione.
Se si vuole una disponibilità maggiore, fissare ora finestre più piccole nel testo, come scelta di misura distinta;
non è un motivo per allargare automaticamente dominio mu o campione. Nessuna dispersione reale letta qui.

## Verifica e ordine

Preparati oracoli indipendenti in scripts/mdi_tilt_pilot_contract_checks.py e documentati in
MDI_TILT_PILOT_CONTRACT_CHECKS.md: 15/15 contratti numerici e controllo dei metadati, senza pixel o tilt MDI.
I protocolli, codici e metadati finali HMI/MWO protetti durante la preparazione restano invariati.
La revisione non congela il protocollo al posto di Claude e non autorizza acquisizioni.

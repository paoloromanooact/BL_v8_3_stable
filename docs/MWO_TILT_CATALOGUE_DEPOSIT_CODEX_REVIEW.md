# Revisione Codex del pacchetto locale MWO — 23 novembre 2026

Oggetto: scripts/mwo_catalogue_deposit_package.py (67eac4b) e pacchetto
results/MWO_TILT_CATALOGUE_DEPOSIT_V1 (02708d1). Nessuna pubblicazione effettuata.

## Esito

Script e pacchetto locale approvati. Ripetuti selftest 11/11, --check 6/6 e
sha256sum -c: tutti i 16 checksum positivi. Il file dei checksum non comprende
se stesso; il pacchetto contiene 17 file. Non occorre rigenerare dati o analisi.

Controllo separato dal checker dello script:
- mappa delle copie esattamente uguale alla mappa canonica dei 13 prodotti del
  rilascio, con sola rinomina README.md -> README_RELEASE_SHORT.md;
- confronto byte per byte di tutti i 13 prodotti, del RELEASE_META.json originale
  e del README esteso con la sorgente docs/MWO_TILT_CATALOGUE_README.md;
- script e README corrispondono al commit di costruzione registrato nel META;
- nessun file extra o mancante rispetto all'insieme atteso;
- numerosità: 5223 isolati, 5942 tutti, 30 colonne documentate, 26 esclusioni,
  20 righe della legge di Joy. Chiavi gruppo/giorno univoche nelle due tabelle.

Il costruttore richiede ricevuta del rilascio stretta, completa e legata al META,
verifica gli hash e l'insieme dei prodotti, scrive in directory temporanea e
rifiuta di sovrascrivere. Il checker controlla manifesti e legami; le prove
sintetiche esercitano i rifiuti dichiarati. Il rilascio verificato resta intatto.

## Provenienza del pacchetto verificato

- Commit di costruzione: `67eac4b022a08bbce4a48f9be735d15629d8eb81`.
- META del pacchetto: `240b57c05a79448170a0ee0ba554bcb7778f8d8ccd1c494900e8b9aab6e734a6`.
- SHA256SUMS.txt: `cd004b4e5788a6baaa68c534ac12b3dcc94bcb0a0d73b0e40c1115e4cae10b3c`.
- META del rilascio sorgente: `b5879cd37c7687dc2f8965d5f65ebeed8af475fbbb993244d30fe0f15691768c`.

RELEASE_META.json è uno snapshot del rilascio originale, i cui nomi includono
il vecchio README.md; la corrispondenza con i nomi del pacchetto è in
META.json/copied_from_release. SHA256SUMS.txt è il manifesto da usare per
verificare direttamente i file della cartella di deposito.

## Stato e passi rimanenti

Il README espone selezione, dipendenza dall'attività, confronti relativi,
limiti delle epoche e natura descrittiva di T3. Non autorizza un verdetto
sul quenching. Il pacchetto è una preparazione locale: licenza, autori,
crediti/acknowledgements definitivi e repository/DOI restano da concordare.
Prima della pubblicazione, predisporre una versione definitiva con tali
informazioni e il riferimento preciso al codice; aggiornare manifesti e
verifica in una nuova versione, conservando questa V1. Nessun deposito,
contatto con terzi o modifica di dati scientifici autorizzati da questa revisione.

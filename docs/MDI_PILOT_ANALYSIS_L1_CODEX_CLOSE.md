# Pilota MDI — chiusura della revisione dell'analisi descrittiva L1

23 novembre 2026, Codex. Base 5959250, dopo 7cc6604.

Le correzioni richieste sono recepite e i nove controesempi della revisione vengono rifiutati anche con hash
aggiornati. Confini di separazione unici, classi |LCM| omesse, distanza MWO−DPD, grandezze MDI esportate e note
esplicite sono coerenti con il perimetro di Q1/Q3. I rapporti di pixel/aree MWO non disponibili non sono inventati.

La provenienza comprende prodotti e ricevute completi, legami fra META, protocollo, rilascio MWO e dipendenze M.
Le ricevute con dati sintetici o repliche diverse da 2000 restano parziali. I controlli scientifici sono ora
ricostruiti in modo indipendente, eccetto la procedura M comune dichiarata.

## Due correzioni circoscritte fatte in revisione

1. **Orari ISO a precisione mista.** Nei soli metadati delle 260 unità M1, 217 orari MWO hanno secondi
   frazionari, altri no. `pd.to_datetime` senza formato fallisce (per esempio al secondo elemento, un orario
   senza frazioni). Corretto a `format="ISO8601"` nei due calcoli temporali del runner e nella funzione oraria
   indipendente del riconteggio. La fixture sintetica include entrambi i formati e verifica la distanza oraria
   anche con un calcolo per istanti singoli. Nessun tilt reale letto per questa diagnosi.
2. **Errore esplorativo di M.** Il confronto richiedeva parametri non nulli anche quando runner e riconteggio
   riportavano entrambi un errore di M con parametri assenti. Ora il caso None/None è accettato come riproduzione
   dello stato di errore, con stato, messaggio, finitezza e flag confrontati. Non trasforma un errore di M in una
   stima valida e non autorizza un verdetto. Una regressione sintetica verifica la ricostruzione degli altri
   prodotti insieme a un errore esplorativo fedelmente riportato.

La tolleranza relativa 1e-5 resta limitata ai parametri numerici di M. Non sono state modificate regole,
soglie, selezione, misure L1 conservate o protocolli congelati.

## Verifica

- Versione 5959250: selftest runner 14/14 e riconteggio 25/25 rieseguiti.
- Dopo le due correzioni: selftest runner 15/15 e riconteggio 26/26.
- Sonda Codex aggiornata a API, tuple degli input e CLASS_EDGES correnti: base positiva e tutte le nove
  manomissioni originarie rifiutate, senza lettura di confronti reali.
- Coppie sintetiche con timestamp interi/frazionari: runner e ricostruzione indipendente coincidono.

## Via alla sequenza

Via a `--run`, conservazione dei prodotti in Git prima della lettura, `--check` con 2000 repliche, conservazione
della ricevuta completa e rapporto descrittivo. Un riconteggio negativo ferma l'interpretazione dipendente.
Il rapporto distingue campione e popolazione pesata; sinottiche e MWO sono misure relative, non riferimenti
perfetti. La MAD non è rumore strumentale; il fit M resta esplorativo. Nessun beta T3 o verdetto sul quenching.

BARD resta rinviato esplicitamente. Q2 e ripetibilità richiedono L2; Q4 rimane separato. Questo via non autorizza
acquisizioni di rete o una serie BL combinata. La revisione non ha eseguito analisi sui tilt MDI reali.

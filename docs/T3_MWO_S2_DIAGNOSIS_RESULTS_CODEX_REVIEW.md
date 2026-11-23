# Revisione Codex degli esiti della diagnosi S2 — 23 novembre 2026

Oggetto: modifica del lettore d606806, output 99f6134, riconteggio 99ca913 e rapporto dcdb185.
Revisione chiusa con le precisazioni applicate al rapporto. Nessuna modifica alla nota congelata,
ai dati, ai risultati numerici o alla procedura M. Nessuna nuova esecuzione T3.

## Lettura numerica

La sola modifica di codice è float_precision="round_trip" in due letture CSV di runner e riconteggio.
Verificata la coincidenza con float dei campi testuali salvati; la differenza massima dal parser
predefinito è 7,1e-15 su d_WL/gamma_WL. Riprodotti i due fit S2: con round_trip i nove campi
beta/SE/limiti e parametri di covarianza sono identici a STABILITY.json; col parser predefinito
beta resta identico e SE cambia di -1,70358e-5. Non è una nuova scelta del modello o una tolleranza
allargata. Il tentativo rifiutato rimane conservato. L'attribuzione a un ottimo piatto in kappa
resta un'ipotesi numerica: questa revisione non ne profila la curvatura.

Selftest ripetuti dopo la modifica: runner 33/33 e riconteggio 22/22.

## Prodotti ed esiti

Confermati ricevuta 19/19, partial false, legame al META, tutti gli hash dei 19 input dichiarati
e dei quattro prodotti. Ricostruite separatamente la matrice e le pendenze puntuali dei 19 fit:
scarto massimo 3,48e-13. D1 confermata, inclusi 72 riavvolgimenti negativi e 108 positivi.
Confermati 13 fit al bordo e l'unica esclusione nominale di zero nell'area terzile 3.
Verificati i riassunti osservati delle quote per attività, area, separazione e flusso.
Gli SE restano quelli della procedura comune: non si rivendica un nuovo controllo indipendente di M.
Artefatto ripetibile: scripts/t3_mwo_s2_results_audit.py. Non legge SEALED e non riesegue T3.

## Precisazioni del rapporto

- D1 è un'identità che dipende dalla rappresentazione degli angoli. g r non è un errore strumentale
  da sottrarre e il conteggio dei record non ne determina da solo il contributo.
- Senza E8 la stima centrale quasi nulla ha intervallo ampio: non è equivalenza e non prova un
  difetto di E8. Popolazione, copertura temporale e disegno cambiano con l'esclusione.
- Area terzile 3 non è un verdetto: selezione post hoc fra confronti correlati e intervalli non validati.
- Il verso dei cambiamenti per area e separazione è diverso, non analogo. Le quote di differenze
  grandi e le medie per attività sono marginali, non una spiegazione del coefficiente aggiustato S2.

## Eventuale seguito

Queste osservazioni motivano una possibile domanda separata sulla confrontabilità delle misure
magnetiche e fotografiche in funzione di dimensione, geometria e rappresentazione assiale.
Non identificano una correzione applicabile né giustificano un nuovo test T3 dopo un taglio su E8,
area o differenze grandi. Non giustificano da sole un catalogo MDI completo.

Raccomandazione: chiudere qui questa diagnosi e completare il pacchetto del catalogo con i limiti
espliciti. Se si investe ancora sulla confrontabilità, fissare obiettivo ed effetto rilevante,
popolazione e metodo per gli angoli, e valutarne la fattibilità prima di un protocollo operativo;
l'eventuale studio resta separato e dichiarato successivo alla lettura. Nessuna nuova linea
scientifica avviata con questa revisione. S42 resta nel distinto progetto MWO/SINDy.

T3 rimane descrittivo senza verdetto; nessuna percentuale o esclusione del quenching derivata qui.

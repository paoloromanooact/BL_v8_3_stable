# Inventario per i due controlli della sorgente BL

25 novembre 2026, Codex. Punto 1 della lista operativa completato su richiesta
dell'utente: inventario di codice SFT e dati HMI. Non e una scelta definitiva
del modello, un protocollo del pilota o una validazione scientifica.

**Lavoro dell'altro agente:** all'ultima fotografia di Git il seguito Q4 e
il riconteggio (`scripts/mdi_q4_recount.py`, commit 0344bc3, in revisione). Non e possibile
accertare da Git l'attivita in tempo reale della sua sessione. Il file non e
stato letto, modificato o aggiunto a questo lavoro.

## 1. Dati locali verificati

Script riproducibile: `scripts/bl_sft_local_inventory.py --out <nuovo.json>`.
Fotografia completa in `docs/BL_SFT_INVENTORY/LOCAL_INVENTORY.json`; ricerche
aggiuntive per percorso in `EXTRA_HMI_PATHS.json`. Sono stati letti nomi,
dimensioni, selezione P1 senza colonne di misura e 17 coppie deterministiche
di header/keyword (un primo record completo per anno). **Nessun array FITS,
tilt o nuovo flusso misurato; nessun output scientifico Q4 letto.**

| Risorsa | Presenza locale | Uso e limite |
|---|---|---|
| P1 Br + bitmap + keys.json | 14195 record, 7133 HARP, 2010-05-01 → 2026-09-27; tutti i record della selezione presenti | Mappe iniziali per il confronto mappa–bipolo; circa 5,69 GB di FITS |
| Patch del confronto BARD (`fits_p3`) | 1074 record, 1016 HARP, 2010–2016, circa 0,88 GB | Alcuni istanti aggiuntivi; non campione temporale uniforme |
| Caso 2024-05-08 | 13 coppie Br/bitmap | Caso tecnico; non campione indipendente per validare il modello |
| Metadati orari SHARP | Cartella `data/sharp/metadata`, 197 CSV | Servono a progettare tempi e disponibilita; metadati non equivalgono a FITS scaricati |
| HMI sinottiche originali polfil | 216 file, CR2097–2312 senza buchi nei nomi, circa 0,96 GB | Possibile osservabile globale futuro, con composizione temporale e polar filling da trattare |

`data/sharp` risolve in `/storage/shared/gianluca/SHARP_BL`.
Le sinottiche originali si trovano in
`/storage/shared/gianluca/MWO_project/sunpy/data`: qui si sono inventariati
solo i nomi e le dimensioni dei dati osservativi HMI. Nessuna serie calibrata,
coefficiente o risultato SINDy e importato nel progetto BL; i progetti restano
separati. Il conteggio dei file non certifica integrita o correttezza dei pixel.

### Disponibilita di osservazioni successive

Dalle sole chiavi e dagli istanti nominali T_REC (TAI) di P1:
- 7062 HARP hanno primario e controllo distinti; 71 hanno lo stesso record
  per entrambi i ruoli;
- **2836 controlli sono successivi al primario**, 4226 lo precedono;
- fra i successivi, 2012 sono ad almeno un giorno, 1572 ad almeno due,
  1153 ad almeno tre, 5 ad almeno cinque.

Questo rende possibile progettare un primo confronto a due istanti con dati
gia locali. **Non e gia un campione valido di evoluzione libera:** occorre
verificare stessa regione, campo di vista, dominio geometrico, evoluzione
della maschera, nuova emergenza e contaminazione. T_OBS va usato nella misura,
non sostituito indiscriminatamente dal tempo nominale T_REC.

Nell'unione delle tre raccolte di patch (senza duplicare le stesse chiavi)
7173 HARP hanno da uno a quattro record: 108 con uno, 6103 con due, 908 con
 tre e 54 con quattro; nessuna con almeno cinque. E un inventario sparso,
non una sequenza a cadenza regolare. L'unione non sostituisce la popolazione P1.
Non trovati FITS HMI full-disk istantanei nei percorsi aggiuntivi esplicitamente
elencati in EXTRA_HMI_PATHS: non e una ricerca esaustiva di ogni disco del sistema.

Il primario–controllo e gia stato studiato in P1d e altre analisi: un nuovo
controllo SFT su questi dati non va presentato come interamente cieco. Si
possono separare sviluppo e verifica secondo regole nuove e dichiarate, senza
cancellare cio che il progetto ha gia osservato.

### Geometria e keyword

I FITS scaricati as-is non contengono da soli tutta la WCS: in tutti i 17
esempi e necessario il relativo `.keys.json`, come fa `geometry.read_sharp`.
Le keyword effettive campionate danno CRLN-CEA/CRLT-CEA e passo 0,03 gradi.
La proiezione CEA e obliqua: niente mappa lat/lon costruita come se il piano
fosse sempre centrato sull'equatore. L'adattatore P1 gia esiste.

BUNIT nei 17 sidecar vale `Invalid KeyLink`: non e una verifica delle unita.
Per il pilota va documentata l'unita del prodotto Br dalla definizione della
serie; non si ricava l'unita da questa stringa. Non e stata misurata alcuna
anomalia del campo con questo inventario.

## 2. Codice riutilizzabile, versioni e licenze

Versioni e file ispezionati attraverso le fonti ufficiali e il connettore
GitHub, senza installare o eseguire codice esterno. Impronte Git e riferimenti
in `SOFTWARE_REFERENCES.json`. Nessun repository esterno copiato nel progetto.

| Candidato | Commit ispezionato | Licenza dichiarata | Valutazione dell'inventario |
|---|---|---|---|
| [sharps-bmrs](https://github.com/antyeates1983/sharps-bmrs/tree/2d6566cebaea36eb7aa1ae5eae08480c19bdd895) | 2d6566ce… (2021-07-13) | GPL-3.0 | Riferimento diretto per il punto 1: `evolve_forward` evolve sia mappa sia bipolo con la classe Python `SFT1` |
| [sft-historical](https://github.com/antyeates1983/sft-historical/tree/3cd2f3325f3605d466f8c193975d075b8c74c3f2) | 3cd2f332… (2025-10-24) | BSD-2-Clause | Alternativa numerica 1D Fortran con wrapper Python; non il codice 2D per mappe locali |
| [HipFT](https://github.com/predsci/HipFT/tree/5d41dea07138df7abcb5f5930a4bb0147bd10431) | 5d41dea0… (2026-11-06, versione sorgente 1.19.6) | Apache-2.0 | Solver sferico 2D, candidato per il confronto spaziale con osservazioni; maggiore lavoro di compilazione/adattamento |

**Precisazione essenziale su sharps-bmrs:** le mappe iniziali sono 2D, ma
l'evoluzione mostrata usa la loro **media in longitudine in un modello 1D**.
Sotto trasporto lineare con coefficienti assialsimmetrici, la media
longitudinale soddisfa un'equazione 1D e determina il dipolo assiale: questo
e un motivo matematico per considerarlo nel primo controllo D(t). Non
conserva la mappa locale 2D da confrontare pixel per pixel con i giorni
successivi; flussi locali non assialsimmetrici richiedono un modello diverso.

Il riferimento costruisce il proprio bipolo, applica il proprio trattamento
dello sbilancio e filtra regioni/ricomparse. Non si deve eseguire `main.py`
come sostituto della pipeline P1: include acquisizione e scelte diverse.
Vanno isolati il modello di trasporto e, se utile, la forma bipolare, sotto
protocollo. Il bipolo costruito dai nostri centroidi e quello adattato dalla
procedura di Yeates non sono automaticamente la stessa definizione.

**Compatibilita:** nel venv BL non risultano SunPy, h5py o netCDF4; presenti
NumPy 2.2.6, SciPy 1.15.3, Astropy 6.1.7 e drms 0.9.0. Il modulo completo
sharptools importa SunPy e API storiche (es. interp2d): non si presume che
funzioni senza adattamenti nell'ambiente attuale. Il nucleo SFT1 ispezionato
e a volumi finiti e usa array NumPy; nessuna prova di esecuzione effettuata.

Sono disponibili gfortran, make e cmake. Non trovati h5fc, mpif90, MATLAB o
Octave nel PATH. Per HipFT l'ambiente HDF5/parallelismo va verificato prima
di promettere una compilazione. Il README di sft-historical cita NetCDF
Fortran, ma il Makefile e il wrapper della versione fissata ispezionata usano
`gfortran` e `scipy.io.FortranFile`, senza link NetCDF esplicito nel nucleo
1D: la dipendenza va distinta per componente, non dedotta dal solo README.

Nel repository BL e nei percorsi di codice locali esaminati non e stato
identificato un solver SFT gia pronto. I percorsi e i limiti della ricerca
sono nella fotografia aggiuntiva; non e una prova di assenza sull'intera macchina.

## 3. Indicazione concreta per il lavoro successivo

1. **Punto 1, dipolo:** scegliere sotto protocollo un nucleo 1D documentato
   (riferimento Python SFT1 o alternativa Fortran) come primo confronto,
   se si adottano esplicitamente le ipotesi assialsimmetriche. Puo usare
   le mappe P1 gia locali. Fissare bilanciamento, rimappatura, forma del
   bipolo e tempi; verificare casi analitici e convergenza prima dei dati.
2. **Punto 2, osservazioni:** progettare il controllo sulle coppie temporali
   disponibili; per la mappa locale serve un trasporto 2D o un modello
   locale dedicato. Le 2836 coppie successive sono solo il bacino iniziale,
   non la selezione del pilota. Inventariare eventuali nuove acquisizioni
   soltanto dopo avere definito il confronto necessario.
3. Mantenere separati sviluppo e verifica, dati locali e nuove richieste,
   sorgente iniziale e flusso gia presente. Non adottare automaticamente
   parametri, maschere, selezioni o risultati delle implementazioni esterne.

**Consegna a Claude:** l'inventario e stato assunto e completato da Codex
su richiesta dell'utente. Il prossimo lavoro assegnabile a Claude e la
bozza delle due specifiche collegate, con revisione indipendente di Codex.
Non rifare l'inventario da zero; completare solo eventuali lacune necessarie
alla specifica. Q4 e il suo riconteggio proseguono su file separati.

Nessuna nuova simulazione, installazione, misura o acquisizione scientifica
eseguita. Sono state consultate documentazione e parti di sorgenti pubbliche
per stabilire il riuso possibile; i FITS locali sono stati letti solo negli header.

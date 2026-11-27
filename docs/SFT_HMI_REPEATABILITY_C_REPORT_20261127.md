# Ripetibilità HMI a 1–2 ore — rapporto C (§8, punto 6)

27 novembre 2026. Corsa osservativa conservata in `40e89f6`, con specifica congelata in `9c02ee5` e ricevuta di congelamento in `91bca29`. Il META registra `20a673d` come commit della corsa. Il riconteggio indipendente da FITS, con lettore e WCS condivisi dichiarati, ha superato 19 controlli su 19 e ha prodotto la ricevuta. Gli hash dei prodotti conservati coincidono con quelli della ricevuta di riconteggio.

## Popolazione e metodo

Delle coppie esaminate nell'audit, 82 sono state selezionate in 79 componenti e 214 sono state escluse secondo le regole congelate. Tutte le 82 coppie selezionate sono state misurate nelle tre preparazioni. Nessun errore di lettura o di calcolo. Sono 48 al Nord e 34 al Sud. Le classi di lag contengono 39 e 43 coppie. I terzili del flusso iniziale da metadati contengono 28, 27 e 27 coppie. Per anno: 2010 (6), 2011 (21), 2012 (6), 2013 (18), 2014 (11), 2015 (12), 2016 (6), 2017 (1), 2022 (1). Il confronto con il bacino del pilota osservativo rimane rinviato come previsto dalla specifica.

La misura principale usa la differenza t1 − t0 sulla stessa impronta valida `C_fin`, dando uguale peso alle componenti e poi alle coppie valutabili della stessa componente. Per le quantità lineari, lo scarto quadratico centrato è calcolato intorno alla media pesata. Gli intervalli riportati sotto sono percentili nominali al 95% dello scarto, con 2.000 ricampionamenti. Il bootstrap principale ricampiona le componenti, quello di sensibilità ricampiona blocchi di sei rotazioni di Carrington. Per il tilt si usano statistiche assiali.

## Distribuzione osservata sulla mappa grezza

| Differenza | Media | Mediana | Quantili 10–90% | Scarto centrato | IC 95%, componenti | IC 95%, blocchi |
|---|---:|---:|---:|---:|---:|---:|
| Momento di dipolo relativo, ΔD/S_D | +0,00080 | +0,00130 | −0,0104 / +0,0117 | 0,00876 | 0,00714–0,01024 | 0,00707–0,01023 |
| Separazione, gradi | +0,0728 | +0,0621 | −0,0520 / +0,2323 | 0,1228 | 0,0967–0,1448 | 0,0974–0,1478 |
| Flusso non firmato, 10²⁰ Mx | −2,54 | −1,03 | −9,33 / +1,43 | 5,72 | 4,02–7,25 | 3,69–7,61 |

Per il tilt grezzo la media circolare è +0,46°, la dispersione circolare è 3,13° e la mediana e il 90° percentile dei moduli sono 0,74° e 2,02°. Per i soli pixel sorgente P1 le stesse quantità sono +0,11°, 1,26°, 0,34° e 1,73°. Una coppia cambia polarità leading.

Le due classi di lag hanno entrambe scarto centrato del dipolo relativo pari a circa 0,00868. Le medie sono +0,00075 e +0,00088 e i secondi momenti 7,60×10⁻⁵ e 7,62×10⁻⁵. La dispersione circolare del tilt grezzo è 2,04° entro 1,5 h e 3,80° tra 1,5 e 2 h. È un confronto descrittivo fra gruppi di coppie.

## Copertura e sensibilità

- L'area mediana di `C_fin` è 113,5 gradi², con minimo 27,1 e massimo 578,7. Il raffinamento a 0,03° è valutabile in 82 coppie su 82.
- La sola rotazione è valutabile in 72 coppie. Per 10 coppie l'area residua è sotto soglia. Sullo stesso `C_rot`, lo scarto centrato del dipolo grezzo è 0,00535 G dopo la rotazione e 0,00536 G per la persistenza. Le dispersioni circolari del tilt sono rispettivamente 1,69° e 1,66°. Questo confronto è secondario e ha un supporto più piccolo di quello principale.
- Le 79 coppie con QUALITY pari a zero in entrambe le mappe hanno uno scarto del dipolo relativo di 0,00886 e una dispersione del tilt grezzo di 3,18°. La dispersione del tilt grezzo e bilanciato è 3,13° al totale. L'uso dei soli pixel sorgente P1 riduce la dispersione osservata del tilt in questo campione, insieme al cambiamento della preparazione.
- Il valore geometrico mediano di μ è 0,608 al primo istante e 0,614 al secondo. Il campione copre soprattutto il periodo 2010–2016. Le tabelle di corsa conservano anche le distribuzioni per emisfero e terzile del flusso.

## Limiti di trasferimento

C quantifica differenze empiriche fra due mappe a breve distanza temporale. Le differenze includono possibili errori correlati fra i record, evoluzione della regione e sensibilità alla preparazione. La conversione in errore della singola mappa richiederebbe ipotesi su correlazione ed evoluzione. La misura fornisce un riferimento descrittivo a 1–2 ore. Un eventuale uso nella likelihood BT richiede un modello di trasferimento esplicito e prove di sensibilità. BQ conserva la propria stima della dispersione dei tilt e della dipendenza tra rotazioni di Carrington.

Fonti interne al repository BL: `results/SFT_C_REPEATABILITY/{SUMMARY,BOOTSTRAP,BOOTSTRAP_BLOCKS,MEASUREMENTS,DENOMINATORS,YEARS}.csv`, `results/SFT_C_REPEATABILITY/META.json` e `results/SFT_C_REPEATABILITY_RECOUNT/RECEIPT.json`.

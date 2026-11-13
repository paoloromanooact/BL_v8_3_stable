# Morfologia HMI — confronto dei lettori e tabelle finali

**2026-11-13. Studio descrittivo, con esposizioni dichiarate.** Le classi
principali coincidono in **24/30** casi comuni; C coincide in **24/30**, di
cui un accordo su «non valutabile». Nei casi valutabili da entrambi C
coincide in **23/27**. La regola operativa registrata è soddisfatta, esattamente
alla soglia per l'accordo primario. Consente soltanto di proporre un piano
distinto per uno studio rappresentativo di S.

## 1. Provenienza e integrità

- Protocollo congelato `21dfe6d`, [A1](PROTOCOL_HMI_MORPHOLOGY_A1.md)
  `67f5e1a` e [A2](PROTOCOL_HMI_MORPHOLOGY_A2.md) `9a4c4cd`.
- Schede prodotte da `2d7d513`, conservate in `2ac85da`.
- Lettore 1: Opus 5.5; primarie `1445133`, secondarie `c70eb0d`.
- Lettore 2: GPT-6.1 Sol, ragionamento alto richiesto; primarie `230f190`,
  secondarie `5fa2884`. Le primarie di entrambi precedono le due letture C.
- Dieci hash verificati prima di aprire i contenuti per il confronto:
  nove file di lettura/metadati e corrispondenza codice–HARP. Tutti coincidono
  con gli impegni precedentemente pubblicati. I file privati originali
  restano intatti; copie byte-identiche sono ora in `LOCKED_READINGS/`.
- Corrispondenza pubblicata in [CODE_MAP.csv](../results/MORPHOLOGY/CODE_MAP.csv),
  hash `ba4818d0363bd6067ae65cda8288a329556cb83d24aac949eedbe5f56c695f99`.
  La pubblicazione avviene dopo il blocco di tutti i passaggi, senza
  riassegnare i codici.
- Codice e input pubblicati prima delle tabelle in `5d9094a`; correzione
  del collegamento e codice eseguito `744eeec` con albero tracciato pulito.
  Tabelle conservate in `b660836` prima della presente interpretazione.
- **229 verifiche programmatiche superate**; il codice include nove casi
  costruiti a mano. Controllati hash, ordine, chiavi, denominatori, partizioni,
  somme con segno e moduli; riconteggi dei CSV anche con Counter e Decimal.
  Hash delle tabelle e versioni in [META.json](../results/MORPHOLOGY/ANALYSIS/META.json).
  Questi controlli hanno lo stesso autore dello script: non sono una revisione
  esterna indipendente del codice.

La [lista degli input](MORPHOLOGY_COMPARISON_INPUTS_SHA256.csv) distingue i
riferimenti Git preesistenti dalle copie delle letture bloccate. Il produttore
del confronto resta distinto dai produttori originari di P1, controlli numerici
e immagini. Non sono stati aperti FITS o ricalcolate misure magnetiche.

## 2. Campione e portata

Il registro comprende **120 HARP**: 90 nuove con classi A2 del lettore 1 e
30 storiche 25S. Il lettore 2 ha letto 30 delle nuove, nel sottocampione
prefissato. Le undici schede di taratura non sono undici osservazioni nuove
aggiunte al campione: restano formazione comune, non repliche indipendenti.
Le etichette storiche 25S, incluse quelle miste e la vecchia classe C,
rimangono separate; non vengono convertite nella griglia A2 o nell'indicatore C.

Composizione delle 30 letture comuni; le quote hanno per denominatore la
**Σ|S_BL| di tutta la base primaria valida P1 del rispettivo gruppo**:

| Gruppo | Tipo | N | In S | Quota della base P1 |
|---|---|---|---|---|
| 24N | controllo | 3 | 1 | 0.025% |
| 24N | dominante | 7 | 7 | 8.684% |
| 24S | controllo | 3 | 2 | 0.142% |
| 24S | dominante | 7 | 7 | 10.319% |
| 25N | controllo | 3 | 1 | 0.005% |
| 25N | dominante | 7 | 7 | 10.477% |

Le 21 dominanti e i nove controlli comuni sono una selezione fissata,
non rappresentativa di tutte le HARP, di tutta la sorgente o della popolazione S.
Le esposizioni pregresse e la taratura comune impediscono di chiamare i
lettori ciechi al progetto; l'indipendenza riguarda le nuove etichette prima
dei rispettivi blocchi. La nuova concordanza è distinta dall'accordo 11/11
sui riferimenti già noti.

## 3. Classi primarie: confronto prima di discutere i disaccordi

| Lettore 1 / lettore 2 | A | B | D | U |
|---|---|---|---|---|
| A | 11 | 3 | 0 | 0 |
| B | 0 | 9 | 0 | 2 |
| D | 0 | 0 | 3 | 0 |
| U | 1 | 0 | 0 | 1 |

Accordo **24/30 = 80%**, inclusa una U concorde. U assegnate: **2/30** dal
lettore 1 e **3/30** dal lettore 2. Entrambi rispettano i limiti registrati;
l'accordo è esattamente sul minimo di 24. Non è una validazione fisica della
tassonomia e dipende anche dalla composizione del sottocampione.

I sei disaccordi originali, senza arbitraggio o modifica delle letture:

| Codice | HARP | Gruppo | Tipo | Lettore 1 | Lettore 2 |
|---|---|---|---|---|---|
| M002 | 1183 | 24N | dominante | B | U |
| M087 | 3793 | 24S | dominante | A | B |
| M073 | 1484 | 24S | controllo | B | U |
| M051 | 2044 | 24S | dominante | A | B |
| M035 | 6445 | 24S | controllo | U | A |
| M069 | 5163 | 24S | dominante | A | B |

Tre disaccordi sono A/B, due B/U e uno U/A. Le motivazioni e le alternative
originali sono nel [confronto per scheda](../results/MORPHOLOGY/ANALYSIS/COMPARISON.csv).
Le alternative annotate dal lettore 1 anche quando assegna una classe
risolta non sono trasformate automaticamente in U: si conserva la classe
bloccata, senza reinterpretarla dopo il confronto. Non si producono qui
etichette di consenso.

## 4. Indicatore C e non valutabili

C indica almeno un centroide fra concentrazioni distinte della medesima
polarità. È un giudizio sulla rappresentazione a centroidi e non una
verifica indipendente della misura o un errore confermato.

| Lettore 1 / lettore 2 | si | no | non_valutabile |
|---|---|---|---|
| si | 16 | 1 | 0 |
| no | 3 | 7 | 1 |
| non_valutabile | 0 | 1 | 1 |

- Accordo sulle tre categorie: **24/30 = 80%**, incluso un caso in cui
  entrambi hanno registrato «non valutabile».
- Casi valutabili da entrambi: **27**; accordo binario **23/27 = 85,2%**.
- Non valutabili: due per ciascun lettore; tre schede con almeno un non
  valutabile. Sono conservate nei denominatori espliciti, senza convertirle in «no».
- Nei 27 casi entrambi valutabili ci sono quattro contrasti sì/no.

| Codice | HARP | Gruppo | C lettore 1 | C lettore 2 |
|---|---|---|---|---|
| M039 | 6610 | 24N | non_valutabile | no |
| M015 | 2635 | 24N | si | no |
| M077 | 11426 | 25N | no | si |
| M047 | 9523 | 25N | no | non_valutabile |
| M086 | 364 | 24N | no | si |
| M051 | 2044 | 24S | no | si |

L'accordo sul contatto visivo della maschera con il bordo del riquadro è
**22/30 = 73,3%**. È un'indicazione accessoria, non un criterio della regola
operativa né un conteggio numerico di pixel al bordo; non viene usata per
cambiare le classi o i flag automatici già esistenti.

## 5. Contributi alla sorgente, con denominatori dichiarati

Classi del lettore 1 sulle 90 nuove; ogni quota è riferita alla **Σ|S_BL|
dell'intera base P1 del gruppo**, non alla sola porzione esaminata:

| Gruppo | Classe | N | In S | Σ S_BL (Mx cm) | Σ|S_BL| (Mx cm) | Quota della base P1 |
|---|---|---|---|---|---|---|
| 24N | A | 18 | 16 | 9.682931e+32 | 1.514745e+33 | 12.879% |
| 24N | B | 8 | 8 | 5.389512e+32 | 9.526358e+32 | 8.100% |
| 24N | D | 3 | 1 | 1.025054e+32 | 1.106448e+32 | 0.941% |
| 24N | U | 1 | 0 | 5.402650e+27 | 5.402650e+27 | 0.000% |
| 24S | A | 13 | 13 | -8.833860e+32 | 2.159843e+33 | 15.278% |
| 24S | B | 12 | 12 | -1.352465e+33 | 2.147324e+33 | 15.189% |
| 24S | D | 2 | 0 | 1.508843e+30 | 1.949637e+30 | 0.014% |
| 24S | U | 3 | 0 | -8.978720e+28 | 8.978720e+28 | 0.001% |
| 25N | A | 14 | 13 | 1.495993e+33 | 2.290730e+33 | 13.479% |
| 25N | B | 12 | 12 | 2.076086e+33 | 2.752075e+33 | 16.194% |
| 25N | D | 3 | 0 | 3.199593e+30 | 4.919361e+30 | 0.029% |
| 25N | U | 1 | 0 | -2.805594e+28 | 2.805594e+28 | 0.000% |

Le 32 HARP B del lettore 1 appartengono tutte a S in questo campione.
Questo descrive casi esaminati, non la prevalenza di B nell'intero S.
Il segno della somma netta e la somma dei moduli restano distinti, per
conservare le cancellazioni tra contributi opposti.

La griglia storica 25S resta un blocco separato:

| Etichetta storica | N | Σ S_BL (Mx cm) | Quota della base P1 25S |
|---|---|---|---|
| A | 5 | -8.606783e+32 | 4.395% |
| A/B | 2 | -3.037144e+32 | 1.614% |
| A/D | 1 | 4.596293e+29 | 0.002% |
| B | 7 | -2.992551e+33 | 15.283% |
| B/C | 4 | -9.300614e+32 | 7.176% |
| C | 6 | -1.807991e+32 | 6.757% |
| D | 5 | -2.023706e+31 | 0.123% |

Le tabelle complete comprendono anche i conteggi separati per dominanti e
controlli, la lettura del secondo lettore sul suo sottocampione e le
aggregazioni secondo l'indicatore C, sempre con il denominatore specificato.

## 6. Sensibilità già misurate, aggregate per classe

Per le HARP B del lettore 1, differenze rispetto a P1 sulle sole schede
esaminate. Sia ΣΔ sia Σ|Δ| sono divise per **Σ|S_BL| dell'intero gruppo**:

| Gruppo | Variante | Confrontabili / B | ΣΔ / base | Σ|Δ| / base |
|---|---|---|---|---|
| 24N | bmap1 | 8/8 | -1.399% | 2.199% |
| 24N | uniform | 8/8 | -0.911% | 1.553% |
| 24S | bmap1 | 12/12 | -3.254% | 3.738% |
| 24S | uniform | 12/12 | -0.098% | 1.739% |
| 25N | bmap1 | 12/12 | 0.301% | 2.030% |
| 25N | uniform | 12/12 | 0.602% | 1.912% |

Le compensazioni rimangono rilevanti: una piccola differenza netta non
implica stabilità delle singole HARP. Questi valori sono aggregazioni dei
controlli numerici già eseguiti, non nuove misure. Non dimostrano che la
classe causi una sensibilità e non stimano l'effetto della morfologia sul
quenching. Le etichette visive sono state bloccate prima di collegare numeri,
NOAA e identità; ciò riduce la circolarità ma non elimina le esposizioni
pregresse, la selezione del campione o le dipendenze per costruzione di C.

[SENSITIVITY_BY_CLASS.csv](../results/MORPHOLOGY/ANALYSIS/SENSITIVITY_BY_CLASS.csv)
riporta tutte le classi, entrambe le varianti, conteggi mancanti, copertura
confrontabile e rapporti alla somma netta. Un confronto mancante non è
sostituito con zero; quando non ci sono casi confrontabili le differenze
aggregate restano non definite.

## 7. Regola operativa registrata

| Gruppo | Quota B, lettore 1 | Quota conservativa | ≥10% in entrambe |
|---|---|---|---|
| 24N | 8.100% | 7.090% | no |
| 24S | 15.189% | 15.186% | sì |
| 25N | 16.194% | 16.194% | sì |

Nel conteggio conservativo, per le 30 schede comuni B conta soltanto se
entrambi i lettori assegnano B; per le altre 60 resta la classe del primo
lettore. La verifica non sostituisce una seconda lettura di tutte le 90.
Il superamento avviene in **due gruppi su tre** in entrambi i conteggi:
24S e 25N. Nessuna soglia di gruppo cambia esito tra i due conteggi.

Sono soddisfatte tutte le condizioni fissate: almeno due gruppi al 10%,
accordo almeno 24/30 e U al massimo 3/30 per lettore. Sono soglie di priorità
scelte prima delle nuove letture ma conoscendo i controlli precedenti;
non sono criteri di validazione scientifica o budget di errore.

**Esito consentito:** proporre un protocollo distinto per uno studio
rappresentativo di S. Il presente compito si arresta al rapporto e alle
tabelle. Non viene avviato quel nuovo studio, eliminata alcuna HARP,
modificata P1, rilanciato T3 o applicato T5 ai dati reali. T3 resta non
deciso e T5 resta descrittivo; il lavoro T5-D2 appartiene a un percorso
separato e non è stato esaminato qui.

## 8. Primo tentativo e riproduzione

Il primo tentativo con codice `5d9094a` è uscito con errore prima di produrre
le tabelle: il collegamento uno-a-uno includeva anche i codici vuoti delle
30 righe storiche. Il controllo ha rifiutato i duplicati. L'episodio è
conservato in [COMPARISON_RUN1_FAILURE.json](../results/MORPHOLOGY/COMPARISON_RUN1_FAILURE.json).
Il codice è stato corretto filtrando le sole 90 righe codificate e aggiungendo
un caso costruito a mano, poi committato in `744eeec` prima del secondo
tentativo. Nessun cambiamento a letture, criteri o denominatori. Il secondo
tentativo ha completato i prodotti e superato le verifiche.

Comando eseguito sul commit pulito `744eeec`:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nice -n 15 .venv/bin/python python/sharpbl/morphology_compare.py --run
```

Per rigenerare i risultati usare una copia separata al commit `744eeec`,
che contiene codice e tutti gli input pubblicati ma non la directory delle
tabelle derivate. Lo script rifiuta di sovrascrivere output esistenti.
I campi della nuova provenienza e il numero di controlli sui file privati
eventualmente assenti vanno distinti da quelli dell'esecuzione originale;
conteggi, matrici e aggregazioni scientifiche leggono soltanto input tracciati.
Nessun push eseguito in questo compito.

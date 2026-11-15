# T5 — sensibilità del proxy del dipolo: risultati (descrittivi)

Esecuzione unica del 2026-11-15 secondo la [nota congelata](T5_PROXY_SENSITIVITY_NOTE.md) (`d47073c`,
SHA-256 `4c2b8ad8…`), con lo script `scripts/t5_proxy_sensitivity.py` (`9a8adde`, SHA-256 `58554b86…`),
revisionato da Codex prima del lancio (selftest 42/42, audit sintetico 27/27). Codice di uscita 0. Output in
`results/T5_PROXY_SENSITIVITY/`, conservati in `39c010c` prima della lettura.

**Natura.** Analisi di sensibilità deterministica, non cieca, condizionata al catalogo fissato e a un proxy a
coppia compatta. Non è un test, non stima il quenching solare e non decide la fattibilità di T5. La pendenza
reale di T5 non è stata calcolata.

## 1. Controlli in esecuzione (nota §6.2)

| Controllo | Esito |
|---|---|
| Numerosità | 2375 record, 318 celle, come atteso |
| Identità P*(γ_obs) = 3·s_star/(8πR³) | 0 fallimenti; scarto relativo massimo 4,0·10⁻¹³ (tolleranza 1·10⁻¹²) |
| Latitudine nulla | 0 record |
| Catalogo | SHA-256 `67dc6a74…` identico prima e dopo |
| Quantili di Â_cella (record T5, peso unitario) | A_lo = 0,5020189558504007; A_hi = 2,7602501179328134 |

## 2. Qualità del proxy al livello osservato (solo descrittiva)

| Livello | Statistica | Valore |
|---|---|---|
| Record (pesi uniformi) | Pearson P*(γ) contro d* | 0,990 |
| | RMS di P* − d* | 2,97·10⁻³ G |
| | Mediana di P*/d* (d* ≠ 0; d* = 0 in 0 record) | 1,0012 |
| | Segni concordi (record non nulli; zeri: 0) | 99,2 % |
| Cella (pesi W_c) | Pearson pesata ΣP*/ΣΦ contro η_c | 0,995 |
| | RMS pesata della differenza | 4,41·10⁻²⁶ G/Mx |

Il proxy riproduce bene D* al livello osservato. Come da nota §3, questo **non** dimostra che la sua derivata
rispetto al tilt sia quella del vero D_bal.

## 3. Risposta allo spostamento prescritto della legge di Joy

Scenario: γ' = γ − δ(Â_c)·24°·sin|λ|, con δ che sale linearmente da 0 (Â_c ≤ A_lo) a δ_max (Â_c ≥ A_hi).

| δ_max | Δβ (G/Mx per unità di Â) | e_ref = Δβ/η̄ | RMS_W residuo | RMS_W centrata | Rapporto del residuo |
|---|---|---|---|---|---|
| 0,10 | −1,833·10⁻²⁶ | −0,0515 | 1,036·10⁻²⁶ | 1,885·10⁻²⁶ | 0,550 |
| 0,20 | −3,669·10⁻²⁶ | −0,1031 | 2,074·10⁻²⁶ | 3,773·10⁻²⁶ | 0,550 |

| Conteggio | δ_max 0,10 | δ_max 0,20 |
|---|---|---|
| Attraversamenti di γ = 0 | 12 | 28 |
| \|γ'\| > 90° | 0 | 1 |
| ΔD positivi / negativi / nulli | 183 / 2073 / 119 | 183 / 2073 / 119 |
| Cambi di segno del proxy (zeri prima/dopo: 0/0) | 12 | 28 |

I 119 ΔD nulli sono i record in celle con Â_c ≤ A_lo, dove la rampa vale zero. Poiché lo spostamento
riduce sempre γ e sin γ è crescente in [−90°, 90°], il segno di ΔD è l'opposto di hale_sign: i 183 ΔD positivi
sono attesi per le regioni anti-Hale (hale = −1). Non sono errori di convenzione. Verifica a posteriori, solo di
conteggio: nei 2256 record con rampa > 0 le regioni anti-Hale sono esattamente 183. Il caso con |γ'| > 90°
(δ_max = 0,20) è l'unico in cui il seno non è monotono.

## 4. Lettura (descrittiva, entro la nota)

- Nelle unità delle simulazioni, una riduzione del 10 % della componente di Joy fra attività bassa e alta
  corrisponde a e_ref ≈ −0,05; una riduzione del 20 % a e_ref ≈ −0,10. La risposta è quasi esattamente
  lineare in δ_max (−0,0515 e −0,1031).
- **Il segnale iniettato non è equivalente al segnale lineare dei generatori.** Il residuo della proiezione
  sul modello completo è circa il 55 % della variazione centrata (in RMS pesata). Una parte importante di
  Δη_c non è descritta dalla retta in Â: rampa limitata, dipendenza da latitudine, geometria e composizione
  di ogni cella.
- **Contesto, senza nuove probabilità** (nota §7). Nella validazione P2f la procedura M, negli scenari dove T5
  rispetta i criteri (1, 2, 9), ha dato «supportato» nel 5–11 % dei cataloghi a e = −0,10. A e ≈ −0,05 non
  ci sono simulazioni. Per il punto precedente, queste frequenze non si trasferiscono a questo scenario: e_ref
  uguale non significa stessa distribuzione di segnale e residui. Nessuna interpolazione.
- Restano i limiti della nota:
  - catalogo fissato (niente cambi di evoluzione, selezione o rilevabilità);
  - covariazioni osservate mantenute;
  - proxy a coppia compatta;
  - R nominale;
  - γ0 dal riferimento P2f;
  - ampiezze del 10 e del 20 % illustrative.

## 5. Che cosa resta da decidere

Nessuna regola automatica (nota §7). Va valutato esplicitamente se progettare il passo sulla potenza (sensibilità
a scala e forma del rumore e a metodi diversi dalla WLS, con un segnale che rispetti la forma non lineare
trovata qui) oppure rinviare per priorità. È ammesso anche un esito non conclusivo. T5 resta descrittivo e T3
non deciso.

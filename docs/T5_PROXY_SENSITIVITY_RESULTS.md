# T5 — sensibilità del proxy del dipolo: risultati (descrittivi)

Verifica indipendente degli esiti: Codex, 26/26 controlli, artefatti in
`MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/reviews/T5_PROXY_ESITI_39c010c/`.

Esecuzione unica del 2026-11-15 secondo la [nota congelata](T5_PROXY_SENSITIVITY_NOTE.md) (`d47073c`,
SHA-256 `4c2b8ad8…`), con lo script `scripts/t5_proxy_sensitivity.py` (`9a8adde`, SHA-256 `58554b86…`),
revisionato da Codex prima del lancio (selftest 42/42, audit sintetico 27/27). Codice di uscita 0. Output in
`results/T5_PROXY_SENSITIVITY/`, conservati in `39c010c` prima della lettura.

**Natura.** Analisi di sensibilità deterministica, non cieca, condizionata al catalogo fissato e a un proxy a
coppia compatta. Non è un test, non stima il quenching solare e non decide la fattibilità di T5. La pendenza
reale di T5 non è stata calcolata.

**Nota del 2026-11-16:** gli artefatti di revisione di Codex citati qui, nella cartella `reviews/` del progetto MWO, sono stati rimossi su richiesta dell'utente; i loro SHA-256 sono conservati in [CODEX_REVIEW_ARTEFACTS_REMOVED_2026-11-16.csv](CODEX_REVIEW_ARTEFACTS_REMOVED_2026-11-16.csv). Gli esiti delle verifiche restano riportati in questo documento.

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

I 119 ΔD nulli sono i record in celle con Â_c ≤ A_lo, dove la rampa vale zero. Lo spostamento riduce sempre γ.
Per i casi in cui γ e γ' restano in [−90°, 90°], dove sin γ è crescente, il segno di ΔD è l'opposto di
hale_sign. Nell'unico caso che esce dall'intervallo (HARPNUM 4750, da circa −89,31° a −90,10°, differenza dei
seni circa −7,1·10⁻⁵, hale = −1) il segno è verificato direttamente (revisione Codex). I 183 ΔD positivi sono
quindi attesi per le regioni anti-Hale. Non sono errori di convenzione. Verifica a posteriori, solo di
conteggio: nei 2256 record con rampa > 0 le regioni anti-Hale sono esattamente 183. Il caso con |γ'| > 90°
(δ_max = 0,20) è l'unico in cui il seno non è monotono.

## 4. Lettura (descrittiva, entro la nota)

- Nelle unità delle simulazioni, una riduzione del 10 % della componente di Joy fra attività bassa e alta
  corrisponde a e_ref ≈ −0,05; una riduzione del 20 % a e_ref ≈ −0,10. La risposta raddoppia quasi esattamente
  al raddoppio di δ_max (−0,0515 e −0,1031). Questo **non** prova linearità rispetto ad Â: la rampa è limitata
  e la risposta è eterogenea fra celle.
- **Il segnale iniettato non è equivalente al segnale lineare dei generatori.** Il rapporto delle RMS pesate
  fra residuo e variazione centrata è 0,55. In somme di quadrati pesate è circa il 30 % (0,55² ≈ 0,30): il
  modello completo, intercetti ciclo-emisfero compresi, descrive il restante 70 %, che non va attribuito
  tutto alla sola attività. e_ref da solo non rappresenta quindi tutta la risposta iniettata. È una proprietà
  dello scenario prescritto su questo catalogo, non una scoperta sulla forma del quenching solare. Il rapporto
  non separa il contributo di rampa limitata, latitudine, geometria e composizione delle celle, e non dice se la
  potenza su questo scenario sarebbe maggiore o minore di quella dei vecchi generatori.
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
a scala e forma del rumore e a metodi diversi dalla WLS, con un segnale che rappresenti la forma prodotta dallo
scenario prescritto su questo catalogo, senza attribuirle una validazione fisica, e HMI come riferimento) oppure rinviare per priorità. È ammesso anche un esito non conclusivo. T5 resta descrittivo e T3
non deciso.

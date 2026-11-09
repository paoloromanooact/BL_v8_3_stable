# Diagnosi del mancato superamento della validazione P2d/P2e (sviluppo diagnostico)

Data: 2026-11-09. **Sviluppo diagnostico, non validazione e non verdetto.** Usa solo
risultati già prodotti dalla validazione P2e (commit dei risultati `3da29da`, codice
`3fcd702`) e il codice di `python/sharpbl/p2d.py`; nessuna simulazione nuova, nessun dato
reale nuovo. Tabelle: `results/DIAGNOSTIC/DIAG_P2E_*.csv`, `DIAG_P2_REAL_FLAGS.csv`,
rigenerate da `python/sharpbl/diag_summary.py`.

**Cecità.** La diagnosi non espone altri dati reali. Gli scenari di validazione V0–V6 e i
loro semi (cataloghi 40000 + k, calibrazione 60000 + 2k / 60001 + 2k) diventano però
**materiale di sviluppo**: un eventuale P2f dovrà essere verificato in modo indipendente,
con semi nuovi e condizioni fissate prima dell'esecuzione (e con la regola di arresto:
se la verifica indipendente fallisce, T3 e T5 restano descrittivi).

## 1. Che cosa è accertato

Solo il mancato superamento del criterio congelato (P2d §6): in V1, V2 e V3 il limite
superiore di Clopper–Pearson dei falsi verdetti supera il 4% per T3 e per T5; V0 e V4 lo
rispettano. Il ruolo distinto di numerosità, dipendenza temporale e stima del rumore **non**
è accertato. Le ipotesi sotto sono diagnostiche: l'accordo tra scenari non dimostra che la
distorsione dei parametri causi i falsi verdetti.

## 2. Risultati per scenario (`DIAG_P2E_SCENARIOS.csv`)

Falsi verdetti su 2000 cataloghi (entrambi i versi; i non applicabili contano come
"nessun verdetto"); φ̂, κ̂ medi; σ̂_u² medio rispetto al vero.

| Scenario | Falsi T3 / T5 (su 2000) | Limite CP 95% T3 / T5 | φ vero → φ̂ medio (sd) | κ vero → κ̂ medio | σ̂_u² / vero |
|---|---|---|---|---|---|
| V0 | 35 / 36 (1,8%) | 2,3% / 2,4% | 0 → 0,14 (0,25) | – | – (σ_u² = 0) |
| V1 | 69 / 66 | 4,2% / 4,0% | 0,5 → 0,46 (0,07) | 0 → 0,00 | 1,07 |
| V2 | 80 / 91 | 4,8% / 5,4% | 0,8 → 0,74 (0,07) | 0 → 0,00 | 1,06 |
| V3 | 93 / 89 | 5,5% / 5,3% | 0,8 → 0,73 (0,07) | 0,6 → 0,48 | 1,06 |
| V4 | 58 / 62 | 3,6% / 3,8% | 0,8 → 0,78 (0,05) | 0 → 0,00 | 1,02–1,03 |
| V5 (AR(2), errato) | 190 / 193 | 10,7% / 10,8% | ρ₁ = 0,71 → 0,64 | 0 → 0,00 | 1,07 |
| V6 (salti, errato) | 124 / 98 | 7,2% / 5,8% | – → 0,88 | 0 → 0,00 | 1,12–1,13 |

I falsi verdetti sono ripartiti tra i due versi senza asimmetria evidente. Le stime di φ̂ di
T3 e T5 nello stesso catalogo sono scorrelate (|r| ≤ 0,03, `DIAG_P2E_T3_T5_PHI_CORR.csv`),
come atteso: le componenti temporali di tilt ed efficienza sono generate indipendentemente.

## 3. Ipotesi diagnostiche (da verificare)

- **H1 — distorsione residua dei parametri temporali.** Dopo le correzioni di P2e, φ̂ resta
  distorto verso il basso (circa −0,04 in V1, −0,06/−0,07 in V2–V3) e κ̂ in V3 (0,48 contro
  0,6). Un modello nullo meno persistente del vero darebbe una distribuzione simulata troppo
  stretta e troppi falsi verdetti. Coerente a livello di scenario: V3 (anche κ̂ distorto) è
  il peggiore; V0 (φ̂ distorto verso l'alto, quindi conservativo) e V4 (φ̂ meno distorto)
  rispettano il limite. σ̂_u² è invece leggermente sovrastimata (+2–13%), il che
  compenserebbe in parte.
- **H2 — perché V4 differisce da V2.** Stesso φ = 0,8, ma φ̂ medio 0,78 contro 0,74. In V4 il
  rumore individuale decresce con Φ e i pesi sono Φ: il rumore di campionamento della media
  di cella è minore, l'attenuazione da correggere è minore e ne resterebbe meno.
- **H3 — bassa frequenza (V5, V6).** Il regressore (attività) varia sulla scala del ciclo,
  quindi la varianza di β̂ dipenderebbe soprattutto dalla parte a bassa frequenza dei residui;
  un AR(1) sottostima la correlazione ai ritardi lunghi di un AR(2) e di salti di livello.
- **H4 — mancata applicabilità.** Vedi §5 e `docs/P2E_V0_APPLICABILITY_DISCREPANCY.md`.

**Che cosa non le sostiene direttamente.** Dentro ciascuno scenario il legame tra φ̂ e falsi
verdetti è debole e non monotono (`DIAG_P2E_PHI_TERCILES.csv`; per esempio V2 T5: 5,3%,
5,0%, 3,5% dal terzile basso all'alto di φ̂, errori circa 0,8 punti; V2 T3: 3,9%, 3,9%,
4,2%). Il confronto è confuso: un catalogo con φ̂ basso per caso ha anche una realizzazione
meno persistente. Per questo serve un controllo che confronti direttamente la varianza della
distribuzione nulla simulata con la varianza vera di β̂: controllo A,
`docs/DIAGNOSTIC_A_PLAN.md`.

## 4. Dati reali (già noti, `DIAG_P2_REAL_FLAGS.csv`)

- T3: applicabile; φ̂ = 0,53, κ̂ = −0,85, σ̂_u² = 56,2 (ĉ0 > 0).
- T5: non applicabile per κ non stimabile: φ̂ = 0,91, ĉ0 > 0, ma ŝ²_w,S < 0 (varianza latente
  delle innovazioni dell'emisfero sud negativa dopo aver tolto il rumore). È la regola di
  P2e §2, non la discrepanza di §5.

## 5. Mancata applicabilità (`DIAG_P2E_APPLICABILITY.csv`)

| Scenario | Non applicabili T3 / T5 | di cui con ĉ0 ≤ 0 | di cui con ĉ0 > 0 |
|---|---|---|---|
| V0 | 619 / 647 | 118 / 152 | 501 / 495 |
| V2, V3 | 0–3 | 0 | 0–3 |
| V6 | 238 / 229 | 0 | 238 / 229 |
| V1, V4, V5 | 0 | 0 | 0 |

- **ĉ0 ≤ 0 (solo V0):** tutti questi cataloghi risultano non applicabili per una discrepanza
  tra codice e protocollo, documentata a parte (`docs/P2E_V0_APPLICABILITY_DISCREPANCY.md`).
- **ĉ0 > 0 con κ non stimabile (V0, V6):** applicazione della regola di P2e §2 (ŝ²_w,h ≤ 0).
  In V0 accade quando ĉ0 è positivo per caso; la regola rinuncia proprio quando la
  componente temporale è piccola o nulla. In V6 riguarda circa l'11–12% dei cataloghi.
- Tra i cataloghi applicabili di V0 i falsi verdetti sono 2,5% (T3) e 2,7% (T5).

## 6. Prossimo passo

Controllo A (analitico, sui cataloghi di sviluppo), con piano registrato prima
dell'esecuzione: `docs/DIAGNOSTIC_A_PLAN.md`; eseguito, risultati in
`docs/DIAGNOSTIC_A_RESULTS.md`. Controllo B (oracolo con simulazione), piano
`docs/DIAGNOSTIC_B_PLAN.md`, risultati in `docs/DIAGNOSTIC_B_RESULTS.md`.

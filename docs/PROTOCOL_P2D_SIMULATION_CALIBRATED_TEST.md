# Protocollo P2d — Test di T3 e T5 calibrato per simulazione (emendamento di P2/P2b)

Stato: **BOZZA del 2026-11-03, non congelata**. Va congelata prima di
eseguire P2 sui dati reali. Fino ad allora l'interpretazione confermativa di
P2 sui dati reali resta **sospesa**. Informazioni già viste:
`docs/SEEN_BEFORE_FREEZE_2026-11-03.md` e la calibrazione sintetica di P2b
(RUN1, prima riga; RUN2 completa: `results/P2/P2B_CALIBRATION_RUN2_N100.*`).
Nessun risultato di P2 sui dati reali.

## 0. Perché, e cosa questa procedura può garantire

RUN2 mostra che, con residui correlati tra rotazioni (AR(1), ρ = 0,5 e 0,8
nel modello sintetico), il bootstrap di P2 sottostima l'incertezza (falsi
positivi fino a 31–38/100 contro 2,5 nominali) e che la regola di P2b
**migliora** ma non porta T5 al livello nominale (10–11/100), e anche T3 resta
sopra (6/100 con ρ = 0,8).

P2d calibra la decisione simulando l'ipotesi nulla con un modello dei
residui stimato sui dati. Il livello nominale vale **rispetto al modello
simulato**, entro l'errore Monte Carlo. Se correlazione, eteroschedasticità o
dipendenza tra emisferi sono rappresentate male, la garanzia **non** si
trasferisce ai dati reali; stimare i parametri dai dati aggiunge incertezza
(limite generale dei test bootstrap). Per questo la procedura completa,
compresa la stima dei parametri, è validata su simulazioni esterne con
modelli anche diversi da quello usato all'interno (§4), con criteri di
accettazione e un ripiego fissati qui (§5).

## 1. Modello sotto l'ipotesi nulla (β = 0)

Si applica separatamente a T3 (unità = regione) e a T5 (unità = cella CR ×
emisfero), sul campione S di P2 e con l'attività `A_monthly`.

**Media.** Il modello di P2 senza il termine di attività:
- T3: γ_i = γ0_{c,h} · sin|λ_i|;
- T5: η_k = η_{c,h};
con i pesi di P2 (Φ per T3, ΣΦ per T5), stimato per WLS sui dati reali.
Residui r = y − media stimata.

**Componente per rotazione ed emisfero.** u_{t,h} = media pesata dei residui
delle unità con CR = t ed emisfero h. Su tutta la griglia dei numeri di CR
consecutivi tra la prima e l'ultima del campione (vuoti inclusi), u segue un
processo AR(1) bivariato:
u_t = φ u_{t−1} + w_t, con w_t ~ N(0, Σ), Σ = σ_w² [[1, κ], [κ, 1]],
φ e σ_w comuni ai due emisferi, κ = correlazione tra emisferi delle
innovazioni. Le CR senza dati non sono osservate ma il processo le attraversa
(i vuoti si conservano).

**Stima dei parametri** (metodo dei momenti, definito qui):
- φ̂: regressione di u_{t,h} su u_{t−1,h} usando solo le coppie di CR
  consecutive entrambe presenti, i due emisferi insieme, senza intercetta;
  troncato in [0; 0,95];
- varianza: σ_u² = varianza pesata di u_{t,h} meno la media della varianza
  di campionamento della media di cella (residui interni alla cella / numero
  di unità); se negativa, 0; σ_w² = σ_u² (1 − φ̂²);
- κ̂: correlazione tra u_{t,N} − φ̂ u_{t−1,N} e u_{t,S} − φ̂ u_{t−1,S} sulle
  CR in cui sono presenti entrambi gli emisferi e la CR precedente;
  troncata in [−0,95; 0,95].

**Componente individuale (eteroschedastica).** e_i = r_i − u_{t(i),h(i)}.
Nelle simulazioni e*_i = e_i · v_i con v_i = ±1 equiprobabili (wild bootstrap
di Rademacher): ogni unità conserva la propria varianza.

**Dati simulati sotto la nulla:** y* = media stimata + u*_{t,h} + e*_i, con
u* simulato dall'AR(1) bivariato stimato (partenza dalla distribuzione
stazionaria). Disegno invariato: stesse unità, pesi, latitudini, attività,
CR ed emisferi.

## 2. Regola di decisione

- Statistica: la stessa stima β̂ di P2 (T3: β_T; T5: β_η), ricalcolata su
  ogni campione simulato.
- M = 2000 campioni simulati, seme 20261109 (T3) e 20261110 (T5).
- Quantili della distribuzione nulla q_{0,0125} e q_{0,9875}: test bilaterale
  con livello 2,5% **per ciascun test**, contando entrambi i versi (1,25% per
  verso). Con due test principali (Bonferroni, come in P2) la probabilità di
  almeno un falso verdetto tra T3 e T5 ha come riferimento **al massimo il 5%**.
- Verso previsto (β < 0 per T3 e T5): **"quenching supportato (P2d)"** se
  β̂_reale < q_{0,0125}; verso opposto: **"segno opposto (P2d)"** se
  β̂_reale > q_{0,9875}; altrimenti **"non deciso (P2d)"**. Si riporta anche
  il p-value bilaterale Monte Carlo (1 + #{|β̂*| ≥ |β̂|}) / (M + 1).
- **Relazione con P2/P2b.** Il verdetto P2d **sostituisce** quello di P2 e P2b
  per T3 e T5, solo se la procedura è accettata (§5); i verdetti P2 e
  `verdict_p2b` si riportano accanto. Il criterio di robustezza di P2 §5 si
  applica alle sensibilità S1–S6 rifacendo P2d su ciascuna (stessa
  procedura, M = 1000).
- La condizione su T1 (legge di Joy) di P2 resta.

## 3. Diagnostica sul campione reale (si riporta)

φ̂, σ̂_u, κ̂, numero di coppie usate, ACF dei residui per CR ai ritardi 1–13
(P2b §3), e un confronto tra ACF osservata e ACF media dei campioni simulati.
La diagnostica **informa** sull'adeguatezza del modello dei residui; **non**
stabilisce un unico "ρ vero", e un'autocorrelazione non significativa (a
qualunque ritardo) **non** esclude una dipendenza rilevante. Nessuna regola
di P2d dipende dalla significatività dell'ACF.

## 4. Validazione della procedura completa (simulazioni esterne)

Cataloghi sintetici con il disegno sintetico di P2 (6000 regioni,
attività SILSO vera), **senza quenching** (β = 0). Per ciascuno si esegue la
**procedura completa**: stima di media e parametri (§1) e calibrazione
interna (M = 500, per contenere i tempi), poi la decisione (§2).
100 cataloghi esterni per scenario, semi 30000 + k:

| Scenario | Modello dei residui per rotazione | Correttamente specificato? |
|---|---|---|
| V0 | nessuna componente per rotazione | sì (φ = 0) |
| V1 | AR(1), φ = 0,5, κ = 0 | sì |
| V2 | AR(1), φ = 0,8, κ = 0 | sì |
| V3 | AR(1), φ = 0,8, κ = 0,6 | sì |
| V4 | AR(1), φ = 0,8, rumore individuale eteroschedastico (sd ∝ Φ^−0,25) | sì |
| V5 | AR(2), φ1 = 0,5, φ2 = 0,3 | **no** |
| V6 | salti di livello: media a gradini lunghi 20 CR, ampiezza pari a sd | **no** |

Ampiezza della componente per rotazione: sd pari a metà del rumore
individuale, come in RUN2. Si riportano per ogni scenario e test: falsi
positivi (conteggio su 100, frazione, errore Monte Carlo), separatamente nel
verso previsto e opposto, la frequenza di "non deciso", e per ogni scenario la
frequenza di **almeno un** falso verdetto tra T3 e T5 (riferimento ≤ 5%); con
zero eventi si dà il limite superiore unilaterale al 95%, circa 3/100; e la potenza con quenching iniettato
(β = −0,2·γ0 per T3, −0,2·η0 per T5) negli scenari V1 e V2.

## 5. Accettazione e ripiego (fissati prima dei risultati)

- **Accettata** per un test se, in tutti gli scenari correttamente
  specificati (V0–V4), i falsi positivi del test (entrambi i versi) sono
  ≤ 5/100, e negli scenari mal specificati (V5, V6) ≤ 10/100. Il margine
  rispetto al 2,5% nominale tiene conto dell'errore Monte Carlo con 100
  cataloghi (circa 1,6 punti a p = 0,025).
- Se accettata: il verdetto P2d è quello del test (§2), con la frase "livello
  nominale rispetto al modello dei residui di P2d".
- **Ripiego** se non accettata: quel test si riporta **solo come
  descrittivo** (stima e intervalli di P2, P2b e P2d), **senza verdetto**; lo
  si dichiara nella sintesi. Nessuna altra procedura si prova dopo aver visto
  i risultati della validazione, salvo un nuovo protocollo che dichiari di
  averli visti.

## 6. Output

`results/P2/P2D_VALIDATION.csv` (§4), `P2D_PARAMETERS.csv` (§3),
`P2D_TESTS.csv` (§2, per variante), colonna `verdict_p2d` in `P2_SUMMARY.csv`.

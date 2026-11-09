# Discrepanza tra codice e P2e §2 sulla non applicabilità quando ĉ0 ≤ 0

Data: 2026-11-09. Riscontrata durante la diagnosi (`docs/DIAGNOSTIC_P2E.md`). Il codice e i
risultati originali **non** sono modificati.

## Che cosa dice il protocollo

P2e §2: «se ĉ0 ≤ 0: σ̂_u² = 0 (`sigma_u_at_boundary`), componente temporale assente nella
simulazione, φ̂ e κ̂ non usati». Le condizioni di non applicabilità restano quelle di P2d §3
(meno di 30 CR con dati, meno di 20 coppie per φ, meno di 20 CR per κ) e, con ĉ0 > 0, un
ŝ²_w,h ≤ 0.

## Che cosa fa il codice

In `estimate_temporal_p2e` (`python/sharpbl/p2d.py`, righe 144–204; blocco alle righe 185–201) il
conteggio delle CR utili per κ (`n_cr_kappa`) viene calcolato solo se ĉ0 > 0. Con ĉ0 ≤ 0
resta 0, quindi `kappa_not_estimable` = 1 e il test risulta **non applicabile**, anche se il
protocollo prevede che si proceda senza componente temporale.

## Effetto noto

- Nella validazione P2e: 118 cataloghi V0 per T3 e 152 per T5 (su 2000), cioè tutti i
  cataloghi con ĉ0 ≤ 0; negli altri scenari ĉ0 ≤ 0 non si verifica
  (`results/DIAGNOSTIC/DIAG_P2E_APPLICABILITY.csv`).
- Sui dati reali: nessuno (ĉ0 > 0 sia per T3 sia per T5; la non applicabilità di T5 ha
  un'altra causa, `docs/DIAGNOSTIC_P2E.md` §4).

## Che cosa non si sa

La discrepanza **non cambia il conteggio storico** dei falsi verdetti: un catalogo non
applicabile conta come "nessun verdetto", e i conteggi registrati restano quelli. Non si sa
invece quale sarebbe stato l'esito di quei cataloghi con il codice conforme al protocollo:
correggere il codice richiederebbe una nuova esecuzione per conoscerne l'effetto sui falsi
verdetti di V0 e sulla frazione di applicabilità. Con al più 152 cataloghi in più valutati,
un effetto sull'accettazione di V0 (35–36 falsi su 2000, limite 65) è improbabile ma non è
stato verificato.

## Conseguenza

Il codice resta com'è, insieme ai risultati che ha prodotto. Un eventuale P2f deve trattare
in modo esplicito e coerente il caso ĉ0 ≤ 0 (e quello ŝ²_w,h ≤ 0), e verificarlo con test
unitari prima della validazione.

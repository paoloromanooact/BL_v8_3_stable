"""Esecuzione dei protocolli P2 e P2b: test osservativi del quenching BL.

Uso: .venv/bin/python python/sharpbl/run_p2.py
Legge results/P1/P1_SBL_CATALOG_BY_HARP.csv (solo se complete_series = 1 e
validation_passed = 1) e
ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv; scrive results/P2/.

Le funzioni lavorano su un catalogo qualsiasi con le colonne di P1: i test in
tests/test_p2_synthetic.py le verificano su cataloghi sintetici con un
quenching noto, senza usare la serie vera.

Scelte di implementazione non scritte esplicitamente in P2 (dichiarate qui e
nell'output "notes"):
- mese di attivita' = mese di T_REC; media di normalizzazione su 2010-05 → 2026-09;
- media mobile su 13 mesi centrata, con almeno 7 mesi validi agli estremi;
- in T5 il ciclo di una cella CR x emisfero e' quello con il flusso maggiore tra
  le sue regioni;
- variante L: campione con leg_valid_bl = 1 e Phi >= 1e21 (la v8.3 non salva npos,
  nneg ne' lo stato del ciclo); T5 per L usa S* perche' la v8.3 non calcola D.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl.provenance import ROOT, stamp  # noqa: E402

SEED = 20261104
NBOOT = 2000
NREAL_T0 = 200
PHI_MIN = 1e21
NPIX_MIN = 20
T_MIN = {24: pd.Timestamp("2008-12-01"), 25: pd.Timestamp("2019-12-01")}
S_CYCLE = {24: 1.0, 25: -1.0}
NORM_START, NORM_END = "2010-05", "2026-09"
SILSO = ROOT / "ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv"
OUT = ROOT / "results/P2"
CH = [(24, "N"), (24, "S"), (25, "N"), (25, "S")]
ROBUST = ["S1", "S2", "S3", "S4", "S5", "S6"]


# ---------------------------------------------------------------- attivita'

def load_silso(path=SILSO):
    s = pd.read_csv(path, sep=";", header=None, skipinitialspace=True)
    s = s.iloc[:, [0, 1, 4, 5]]
    s.columns = ["year", "month", "N", "S"]
    s["ym"] = s["year"].astype(int).astype(str) + "-" + s["month"].astype(int).map("{:02d}".format)
    s = s.set_index("ym")[["N", "S"]].astype(float).replace(-1.0, np.nan)
    out = {}
    for kind in ("monthly", "smooth13"):
        x = s if kind == "monthly" else s.rolling(13, center=True, min_periods=7).mean()
        norm = x.loc[NORM_START:NORM_END].mean()
        out[kind] = x / norm
    return out


def add_activity(df, silso, sel=None):
    """Colonne A_monthly, A_smooth13, A_usflux (attivita' normalizzata per emisfero)."""
    df = df.copy()
    ym = df["t"].dt.strftime("%Y-%m")
    for kind, tab in silso.items():
        df[f"A_{kind}"] = [tab.at[m, h] if m in tab.index and h in ("N", "S") else np.nan
                           for m, h in zip(ym, df["hemisphere"])]
    if sel is not None:
        p = sel[sel["role"] != "control"].copy()
        p["CR"] = p["CR"].astype(float)
        p["hem"] = np.where(p["LAT_FWT"] >= 0, "N", "S")
        tot = p.groupby(["CR", "hem"])["USFLUX"].sum()
        norm = tot.groupby(level="hem").mean()
        own = df["USFLUX"].fillna(0.0).to_numpy()
        key = list(zip(df["CR"].astype(float), df["hemisphere"]))
        other = np.array([tot.get(k, np.nan) for k in key]) - own
        df["A_usflux"] = other / np.array([norm.get(h, np.nan) for h in df["hemisphere"]])
    else:
        df["A_usflux"] = np.nan
    return df


# ---------------------------------------------------------------- campioni

def prepare(cat, legacy=False):
    df = cat.copy()
    df["t"] = pd.to_datetime(df["T_REC"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
    p = "leg_" if legacy else ""
    df["lat"] = df[f"{p}lat_mean_deg"]
    df["phi"] = df[f"{p}phi_mx"]
    df["cyc"] = df[f"{p}cycle"]
    df["hemisphere"] = np.where(df["lat"] >= 0, "N", "S")
    df["gamma"] = np.sign(df["lat"]) * np.degrees(np.arcsin(np.clip(df[f"{p}sintilt"], -1, 1)))
    df["sinlat"] = np.sin(np.radians(df["lat"].abs()))
    df["s_star"] = np.sign(df["lat"]) * df[f"{p}s_bl"]
    df["d_star"] = df["cyc"].map(S_CYCLE) * (np.nan if legacy else df["d_axial_bal_g"])
    df["phase"] = [(t - T_MIN[c]).days / 365.25 / 11.0 if c in T_MIN else np.nan
                   for t, c in zip(df["t"], df["cyc"])]
    return df


def samples(cat):
    """Campioni di P2 §2 (e S7 di P1b) come dict nome -> DataFrame preparato."""
    v = prepare(cat)
    v = v[v["cyc"].isin([24, 25])]
    base = (v["valid_bl"] == 1) & (v["npos"] >= NPIX_MIN) & (v["nneg"] >= NPIX_MIN)
    prim = v["role"] != "control"
    ctrl = v["role"] != "primary"
    noamb = v["cycle_state"] != "AMBIGUOUS"
    out = {
        "S": v[prim & base & (v["phi"] >= PHI_MIN) & noamb],
        "S1": v[prim & base & (v["phi"] >= 5e20) & noamb],
        "S2": v[prim & base & (v["phi"] >= 3e21) & noamb],
        "S3": v[prim & base & (v["phi"] >= PHI_MIN) & noamb & (v["diagnostic_reason"] == "NONE")],
        "S4": v[prim & base & (v["phi"] >= PHI_MIN) & noamb & (v["NOAA_NUM"] == 1)],
        "S5": v[ctrl & base & (v["phi"] >= PHI_MIN) & noamb],
        "S6": v[prim & base & (v["phi"] >= PHI_MIN)],
        "S7": v[prim & base & (v["phi"] >= PHI_MIN) & noamb & (v["qual_0x80"] == 0)],
    }
    if "family_rank" in v:  # P1d: senza ricomparse (riportata, fuori dalla regola di robustezza)
        out["S8"] = v[prim & base & (v["phi"] >= PHI_MIN) & noamb & (v["family_rank"] == 0)]
    lg = prepare(cat, legacy=True)
    lg = lg[lg["cyc"].isin([24, 25])]
    out["L"] = lg[(lg["role"] != "control") & (lg["leg_valid_bl"] == 1) & (lg["phi"] >= PHI_MIN)]
    return out


# ---------------------------------------------------------------- WLS con bootstrap a blocchi sulle CR

# schema di bootstrap: ("cr",) = CR intere indipendenti (P2); ("moving", L) = blocchi
# mobili di L CR consecutive (P2b). Modificato solo da p2b_moving_blocks().
SCHEME = ("cr",)
SEED_P2B = 20261105
BLOCK_LENGTHS = (3, 6, 13)


def boot_counts(u, scheme, seed, nboot):
    """Matrice (nboot, len(u)) di quante volte ogni CR (numeri u, ordinati) entra in un ricampionamento."""
    rng = np.random.default_rng(seed)
    if scheme[0] == "cr":
        draws = rng.integers(0, len(u), size=(nboot, len(u)))
        return np.stack([np.bincount(d, minlength=len(u)) for d in draws]).astype(float)
    L = int(scheme[1])
    lo, hi = int(u.min()), int(u.max())
    nb = int(np.ceil((hi - lo + 1) / L))
    starts = rng.integers(lo, max(lo, hi - L + 1) + 1, size=(nboot, nb))
    uu = np.asarray(u, float)
    return ((starts[:, :, None] <= uu) & (starts[:, :, None] + L - 1 >= uu)).sum(axis=1).astype(float)


class BlockWLS:
    """WLS con bootstrap a blocchi: statistiche sufficienti X'WX, X'Wy per CR."""

    def __init__(self, X, w, cr, seed=None, nboot=NBOOT):
        X = np.asarray(X, float)
        w = np.asarray(w, float)
        u, g = np.unique(np.asarray(cr, float), return_inverse=True)
        self.k, self.ng, self.g, self.X, self.w, self.u = X.shape[1], len(u), g, X, w, u
        A = np.zeros((self.ng, self.k, self.k))
        np.add.at(A, g, w[:, None, None] * X[:, :, None] * X[:, None, :])
        self.A = A
        if seed is None:
            seed = SEED if SCHEME[0] == "cr" else SEED_P2B
        self.counts = boot_counts(u, SCHEME, seed, nboot)
        self.Ab = np.linalg.pinv((self.counts @ A.reshape(self.ng, -1)).reshape(nboot, self.k, self.k))
        self.Ainv = np.linalg.pinv(A.sum(axis=0))

    def cr_residual_means(self, y, est):
        """Media pesata dei residui per CR (P2b §3), con i numeri di CR."""
        r = np.asarray(y, float) - self.X @ est
        num = np.bincount(self.g, weights=self.w * r, minlength=self.ng)
        den = np.bincount(self.g, weights=self.w, minlength=self.ng)
        return self.u, num / den

    def fit(self, y):
        y = np.asarray(y, float)
        b = np.zeros((self.ng, self.k))
        np.add.at(b, self.g, (self.w * y)[:, None] * self.X)
        est = self.Ainv @ b.sum(axis=0)
        boot = np.einsum("bij,bj->bi", self.Ab, self.counts @ b)
        return est, boot


def ci(draws, level):
    a = (100 - level) / 2
    return np.nanpercentile(draws, [a, 100 - a])


def verdict(lo, hi, predicted):
    if predicted < 0:
        return "quenching supportato" if hi < 0 else ("segno opposto" if lo > 0 else "non deciso")
    return "quenching supportato" if lo > 0 else ("segno opposto" if hi < 0 else "non deciso")


def row(test, variant, activity, est, boot, n, ncr, predicted=None, decide=False, **extra):
    l95, h95 = ci(boot, 95)
    l975, h975 = ci(boot, 97.5)
    r = dict(test=test, variant=variant, activity=activity, estimate=est, ci95_lo=l95, ci95_hi=h95,
             ci975_lo=l975, ci975_hi=h975, n=n, n_cr=ncr)
    if predicted is not None:
        r["predicted_sign"] = int(np.sign(predicted))
        r["verdict"] = verdict(l975, h975, predicted) if decide else ""
    r.update(extra)
    return r


# ---------------------------------------------------------------- test

def ch_columns(d, scale):
    return np.column_stack([((d["cyc"] == c) & (d["hemisphere"] == h)).to_numpy() * scale for c, h in CH])


def t1(d, variant):
    rows = []
    s = d["sinlat"].to_numpy()
    m = BlockWLS(s[:, None], d["phi"], d["CR"])
    est, boot = m.fit(d["gamma"])
    rows.append(row("T1", variant, "", est[0], boot[:, 0], len(d), m.ng, group="all"))
    for c, h in CH:
        dd = d[(d["cyc"] == c) & (d["hemisphere"] == h)]
        if len(dd) < 5:
            continue
        mm = BlockWLS(dd["sinlat"].to_numpy()[:, None], dd["phi"], dd["CR"])
        e, b = mm.fit(dd["gamma"])
        rows.append(row("T1", variant, "", e[0], b[:, 0], len(dd), mm.ng, group=f"c{c}{h}"))
    return rows


def t2(d, variant):
    phase_max = d.loc[d["cyc"] == 25, "phase"].max()
    dd = d[(d["cyc"] == 25) | ((d["cyc"] == 24) & (d["phase"] <= phase_max))]
    s = dd["sinlat"].to_numpy()
    X = np.column_stack([s * (dd["cyc"] == 24), s * (dd["cyc"] == 25)])
    m = BlockWLS(X, dd["phi"], dd["CR"])
    est, boot = m.fit(dd["gamma"])
    return [row("T2", variant, "", est[1] - est[0], boot[:, 1] - boot[:, 0], len(dd), m.ng,
                predicted=-1, phase_max=phase_max, gamma0_c24=est[0], gamma0_c25=est[1])]


def t3_design(d, act):
    s = d["sinlat"].to_numpy()
    return np.column_stack([ch_columns(d, s), (d[act].to_numpy() - 1.0) * s])


def t3(d, variant, act, decide):
    d = d[np.isfinite(d[act])]
    m = BlockWLS(t3_design(d, act), d["phi"], d["CR"])
    est, boot = m.fit(d["gamma"])
    return [row("T3", variant, act, est[-1], boot[:, -1], len(d), m.ng, predicted=-1, decide=decide)]


def t4(d, variant, act):
    d = d[np.isfinite(d[act]) & np.isfinite(d["phase"])]
    ph = d["phase"].to_numpy()
    X = np.column_stack([ch_columns(d, 1.0), ph, ph ** 2, ph ** 3, d[act].to_numpy() - 1.0])
    m = BlockWLS(X, d["phi"], d["CR"])
    est, boot = m.fit(d["lat"].abs())
    return [row("T4", variant, act, est[-1], boot[:, -1], len(d), m.ng, predicted=+1)]


def cells(d, act, qty):
    d = d[np.isfinite(d[act]) & np.isfinite(d[qty])]
    rows = []
    for (cr, h), g in d.groupby(["CR", "hemisphere"]):
        if len(g) < 3:
            continue
        fl = g.groupby("cyc")["phi"].sum()
        rows.append(dict(CR=cr, hemisphere=h, cyc=int(fl.idxmax()), n=len(g), phi=g["phi"].sum(),
                         eta=g[qty].sum() / g["phi"].sum(), abar=g[act].mean()))
    return pd.DataFrame(rows)


def t5(d, variant, act, qty, decide, label=None):
    c = cells(d, act, qty)
    if len(c) < 10:
        return []
    X = np.column_stack([ch_columns(c, 1.0), c["abar"].to_numpy() - 1.0])
    m = BlockWLS(X, c["phi"], c["CR"])
    est, boot = m.fit(c["eta"])
    return [row("T5", variant, act, est[-1], boot[:, -1], int(c["n"].sum()), m.ng, predicted=-1,
                decide=decide, quantity=label or qty, n_cells=len(c))]


def t0(d, act="A_monthly", seed=SEED + 1):
    """Potenza di T3: tilt sintetici con quenching noto sulle latitudini e attivita' reali di S."""
    d = d[np.isfinite(d[act])]
    s = d["sinlat"].to_numpy()
    m1 = BlockWLS(s[:, None], d["phi"], d["CR"])
    g0 = m1.fit(d["gamma"])[0][0]
    resid = d["gamma"].to_numpy() - g0 * s
    m3 = BlockWLS(t3_design(d, act), d["phi"], d["CR"])
    rng = np.random.default_rng(seed)
    a = d[act].to_numpy()
    rows = []
    for frac in (0.0, -0.1, -0.2, -0.3):
        beta = frac * g0
        est, det, fp = [], 0, 0
        for _ in range(NREAL_T0):
            y = (g0 + beta * a) * s + rng.choice(resid, size=len(resid), replace=True)
            e, b = m3.fit(y)
            lo, hi = ci(b[:, -1], 97.5)
            est.append(e[-1])
            det += hi < 0
            fp += lo > 0 or hi < 0
        est = np.array(est)
        rows.append(dict(test="T0", beta_over_gamma0=frac, beta_true=beta, gamma0=g0,
                         bias=float(est.mean() - beta), sd=float(est.std()),
                         detection_fraction=det / NREAL_T0 if frac < 0 else np.nan,
                         false_positive_fraction=fp / NREAL_T0 if frac == 0 else np.nan, n=len(d)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- P2b

def p2b_moving_blocks(d):
    """P2b §1: T1-T5 sul campione S con bootstrap a blocchi mobili di L CR consecutive."""
    global SCHEME
    rows = []
    try:
        for L in BLOCK_LENGTHS:
            SCHEME = ("moving", L)
            part = (t1(d, "S") + t2(d, "S") + t3(d, "S", "A_monthly", True) + t4(d, "S", "A_monthly")
                    + t5(d, "S", "A_monthly", "d_star", True, "D*"))
            for r in part:
                r["block_length"] = L
            rows += part
    finally:
        SCHEME = ("cr",)
    return pd.DataFrame(rows)


def acf_by_cr(u, x, max_lag=13):
    """Autocorrelazione di una serie per numero di CR (CR mancanti esclusi dalle coppie)."""
    s = pd.Series(x, index=np.asarray(u, int)).reindex(range(int(u.min()), int(u.max()) + 1))
    s = s - s.mean()
    out = []
    for lag in range(1, max_lag + 1):
        a, b = s.to_numpy()[:-lag], s.to_numpy()[lag:]
        ok = np.isfinite(a) & np.isfinite(b)
        out.append((lag, float((a[ok] * b[ok]).sum() / np.nansum(s.to_numpy() ** 2)), int(ok.sum())))
    return out


def p2b_residual_acf(d):
    """P2b §3: ACF delle medie per CR dei residui di T3 e T5."""
    rows = []
    dd = d[np.isfinite(d["A_monthly"])]
    m = BlockWLS(t3_design(dd, "A_monthly"), dd["phi"], dd["CR"])
    est, _ = m.fit(dd["gamma"])
    u, r = m.cr_residual_means(dd["gamma"], est)
    for lag, a, n in acf_by_cr(u, r):
        rows.append(dict(test="T3", lag=lag, acf=a, n_pairs=n, band=1.96 / np.sqrt(len(u))))
    c = cells(d, "A_monthly", "d_star")
    X = np.column_stack([ch_columns(c, 1.0), c["abar"].to_numpy() - 1.0])
    m = BlockWLS(X, c["phi"], c["CR"])
    est, _ = m.fit(c["eta"])
    u, r = m.cr_residual_means(c["eta"], est)
    for lag, a, n in acf_by_cr(u, r):
        rows.append(dict(test="T5", lag=lag, acf=a, n_pairs=n, band=1.96 / np.sqrt(len(u))))
    return pd.DataFrame(rows)


def verdict_p2b(main_row, mb, test):
    """P2b §2: stesso verdetto per tutte le lunghezze di blocco, altrimenti non deciso."""
    sub = mb[mb["test"] == test]
    if test == "T5":
        sub = sub[sub["quantity"] == "D*"]
    vs = {verdict(r["ci975_lo"], r["ci975_hi"], -1) for _, r in sub.iterrows()}
    if len(sub) == len(BLOCK_LENGTHS) and vs == {main_row["verdict"]}:
        return main_row["verdict"]
    return "non deciso (dipendenza temporale)"


def synthetic_catalog(beta_t_frac, beta_eta_frac, n=6000, seed=1, rho=0.0):
    """Catalogo sintetico (attivita' SILSO vera; tilt, latitudini, flussi, dipolo sintetici).

    rho > 0 aggiunge a tilt e D* una componente comune per CR con AR(1) tra CR
    consecutive (P2b §4), con deviazione standard meta' del rumore per regione.
    """
    gamma0, eta0, sd_t = 30.0, 2.0e-24, 15.0
    rng = np.random.default_rng(seed)
    silso = load_silso()["monthly"]
    t = pd.to_datetime("2010-06-01") + pd.to_timedelta(rng.uniform(0, 16 * 365.25, n), unit="D")
    cyc = np.where(t < pd.Timestamp("2020-01-01"), 24, 25)
    tmin = np.where(cyc == 24, np.datetime64("2008-12-01"), np.datetime64("2019-12-01"))
    phase = (t.values - tmin).astype("timedelta64[D]").astype(float) / 365.25 / 11
    hem = rng.choice([1, -1], n)
    lat = hem * np.clip(28 - 20 * phase + rng.normal(0, 4, n), 2, 45)
    a = np.array([silso.at[m, "N" if h > 0 else "S"] for m, h in zip(t.strftime("%Y-%m"), hem)])
    s = np.sin(np.radians(np.abs(lat)))
    cr = (2096 + (t - pd.Timestamp("2010-06-01")).days / 27.2753).astype(int)
    e_t = np.zeros(n)
    e_d = np.zeros(n)
    if rho > 0:
        crs = np.arange(cr.min(), cr.max() + 1)
        z = np.zeros((len(crs), 2))
        innov = rng.normal(0, 1, (len(crs), 2)) * np.sqrt(1 - rho ** 2)
        z[0] = rng.normal(0, 1, 2)
        for k in range(1, len(crs)):
            z[k] = rho * z[k - 1] + innov[k]
        idx = cr - crs[0]
        e_t = 0.5 * sd_t * z[idx, 0]
        e_d = 0.5 * z[idx, 1]
    gamma = (gamma0 + beta_t_frac * gamma0 * (a - 1)) * s + rng.normal(0, sd_t, n) + e_t
    phi = 10 ** rng.normal(21.7, 0.4, n)
    dstar = phi * eta0 * (1 + beta_eta_frac * (a - 1) + rng.normal(0, 1, n) + e_d)
    sc = np.where(cyc == 24, 1.0, -1.0)
    sintilt = np.sin(np.radians(gamma)) * np.sign(lat)
    cat = pd.DataFrame({
        "HARPNUM": np.arange(n), "T_REC": t.strftime("%Y.%m.%d_%H:%M:%S_TAI"), "role": "both",
        "qual_0x80": 0, "NOAA_NUM": 1, "USFLUX": phi, "LAT_FWT": lat, "CR": cr,
        "valid_bl": 1, "npos": 100, "nneg": 100, "phi_mx": phi, "lat_mean_deg": lat, "cycle": cyc,
        "cycle_state": "DATE", "sintilt": sintilt, "d_axial_bal_g": dstar / sc,
        "s_bl": np.sign(lat) * dstar * 1e40, "diagnostic_reason": "NONE",
    })
    for c in ("valid_bl", "phi_mx", "lat_mean_deg", "cycle", "sintilt", "s_bl"):
        cat[f"leg_{c}"] = cat[c]
    return cat


def p2b_calibration(n_cat=40, rhos=(0.0, 0.5, 0.8)):
    """P2b §4: frazione di verdetti != 'non deciso' senza quenching, con residui AR(1) tra CR."""
    silso = load_silso()
    rows = []
    for rho in rhos:
        fp = {"T3": [0, 0], "T5": [0, 0]}
        for k in range(n_cat):
            cat = synthetic_catalog(0.0, 0.0, seed=1000 + k, rho=rho)
            d = add_activity(samples(cat)["S"], silso)
            r3 = t3(d, "S", "A_monthly", True)[0]
            r5 = t5(d, "S", "A_monthly", "d_star", True, "D*")[0]
            mb = p2b_moving_blocks(d)
            for test, r in (("T3", r3), ("T5", r5)):
                fp[test][0] += r["verdict"] != "non deciso"
                fp[test][1] += verdict_p2b(r, mb, test) != "non deciso (dipendenza temporale)" and \
                    verdict_p2b(r, mb, test) != "non deciso"
        for test, (a, b) in fp.items():
            rows.append(dict(rho=rho, test=test, n_catalogues=n_cat, false_positive_p2=a / n_cat,
                             false_positive_p2b=b / n_cat))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- esecuzione

def run(cat, sel=None, silso=None, do_t0=True):
    silso = silso or load_silso()
    smp = {k: add_activity(v, silso, sel) for k, v in samples(cat).items()}
    res = {k: [] for k in ("T1", "T2", "T3", "T4", "T5")}
    for name, d in smp.items():
        if len(d) < 20:  # campione vuoto o quasi: nessuna stima
            continue
        decide = name == "S"
        res["T1"] += t1(d, name)
        res["T2"] += t2(d, name)
        acts = ["A_monthly", "A_smooth13", "A_usflux"] if name == "S" else ["A_monthly"]
        for act in acts:
            if not np.isfinite(d[act]).any():
                continue
            main = decide and act == "A_monthly"
            res["T3"] += t3(d, name, act, main)
            res["T4"] += t4(d, name, act)
            if name == "L":
                res["T5"] += t5(d, name, act, "s_star", False, "S*")
            else:
                res["T5"] += t5(d, name, act, "d_star", main, "D*")
                if name == "S" and act == "A_monthly":
                    res["T5"] += t5(d, name, act, "s_star", False, "S*")
                    for lr in (8.0, 12.0, 15.0):
                        d2 = d.assign(d_lr=d["d_star"] * np.exp(-d["lat"] ** 2 / (2 * lr ** 2)))
                        res["T5"] += t5(d2, name, act, "d_lr", False, f"D*·exp(-λ²/2·{lr:.0f}²)")
    tabs = {k: pd.DataFrame(v) for k, v in res.items()}
    tabs["T0"] = t0(smp["S"]) if do_t0 else pd.DataFrame()
    tabs["P2B_MOVING_BLOCKS"] = p2b_moving_blocks(smp["S"])
    tabs["P2B_RESIDUAL_ACF"] = p2b_residual_acf(smp["S"])
    tabs["SUMMARY"] = summary(tabs)
    return tabs


def summary(tabs):
    t1s = tabs["T1"]
    g = t1s[(t1s["variant"] == "S") & (t1s["group"] == "all")].iloc[0]
    joy_ok = g["ci95_lo"] > 0
    out = [dict(test="T1", estimate=g["estimate"], ci95_lo=g["ci95_lo"], ci95_hi=g["ci95_hi"],
                verdict="legge di Joy presente" if joy_ok else "legge di Joy non rilevata: T3 e T5 non interpretati")]
    for test in ("T3", "T5"):
        t = tabs[test]
        main = t[(t["variant"] == "S") & (t["activity"] == "A_monthly")]
        if test == "T5":
            main = main[main["quantity"] == "D*"]
        m = main.iloc[0]
        sens = t[t["variant"].isin(ROBUST) & (t["activity"] == "A_monthly")]
        if test == "T5":
            sens = sens[sens["quantity"] == "D*"]
        same = (np.sign(sens["estimate"]) == np.sign(m["estimate"])).all() and len(sens) == len(ROBUST)
        side = sens["ci95_hi"] < 0 if m["estimate"] < 0 else sens["ci95_lo"] > 0
        robust = bool(same and side.sum() >= 4)
        v = m["verdict"] if joy_ok else "non interpretato (T1)"
        vb = verdict_p2b(m, tabs["P2B_MOVING_BLOCKS"], test) if joy_ok else "non interpretato (T1)"
        out.append(dict(test=test, estimate=m["estimate"], ci975_lo=m["ci975_lo"], ci975_hi=m["ci975_hi"],
                        verdict=v, verdict_p2b=vb, robust=int(robust), n_sens_same_sign=int((np.sign(sens["estimate"]) == np.sign(m["estimate"])).sum()),
                        n_sens_ci95_excluding0=int(side.sum())))
    for test in ("T2", "T4"):
        t = tabs[test]
        m = t[(t["variant"] == "S") & ((t["activity"] == "A_monthly") | (test == "T2"))].iloc[0]
        out.append(dict(test=test, estimate=m["estimate"], ci95_lo=m["ci95_lo"], ci95_hi=m["ci95_hi"],
                        verdict="descrittivo"))
    return pd.DataFrame(out)


def main() -> int:
    cat_path = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
    cat = pd.read_csv(cat_path, low_memory=False)
    if int(cat["complete_series"].iloc[0]) != 1:
        print("il catalogo P1 non e' la serie completa (complete_series = 0): P2 non si esegue")
        return 1
    if "validation_passed" not in cat or int(cat["validation_passed"].iloc[0]) != 1:
        print("i controlli obbligatori di P1 non sono superati (validation_passed != 1): P2 non si esegue")
        return 1
    sel = pd.read_csv(ROOT / "results/P1/P1_RECORD_SELECTION.csv")
    sel = sel.merge(cat[["HARPNUM", "T_REC", "CR"]], on=["HARPNUM", "T_REC"], how="left")
    tabs = run(cat, sel)
    OUT.mkdir(parents=True, exist_ok=True)
    tabs["P2B_CALIBRATION"] = p2b_calibration()
    st = stamp(("P1", "P1b", "P1c", "P1d", "P2", "P2b"))
    names = {"T0": "P2_T0_POWER", "T1": "P2_T1_JOY", "T2": "P2_T2_INTERCYCLE", "T3": "P2_T3_TILT_QUENCHING",
             "T4": "P2_T4_LATITUDE_QUENCHING", "T5": "P2_T5_EFFICIENCY", "SUMMARY": "P2_SUMMARY",
             "P2B_MOVING_BLOCKS": "P2B_MOVING_BLOCKS", "P2B_RESIDUAL_ACF": "P2B_RESIDUAL_ACF",
             "P2B_CALIBRATION": "P2B_CALIBRATION"}
    for k, n in names.items():
        tabs[k].assign(**st).to_csv(OUT / f"{n}.csv", index=False)
    print(tabs["SUMMARY"].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Diagnostic (not committed code path): stepping-out limit hits per coordinate and phase, pilot setting G3 / MQ v HN20."""
import sys, math, numpy as np
sys.path.insert(0,"scripts"); sys.path.insert(0,"python")
import bq_identifiability_pilot as IP
from sharpbl import bq_core as B
D = IP.design_arrays()
rng = np.random.default_rng(IP.SEED + 1000 * 2 + 0)
y = IP.simulate(D, "G3", rng)
prior = dict(B.PRIOR, q_sd=0.5, sigma_v_hn=20.0)
d = B.Design(t=D["t"], h=D["h"], s=D["s"], a=D["a"], lphi=D["lphi"], cell=D["cell"], fam=D["fam"], n_t=D["n_t"], n_cell=4, with_v=True, prior=prior)
logf = lambda z: B.log_post(d, z, y)
x = np.array([math.log(20.0), -0.4, math.log(2.0), 0.9, -0.4, math.log(3.0), math.log(5.0), 1.5, 0.3])
fx = logf(x); W = B.Widths(len(x), 200)
names = d.names(); hits = np.zeros((2, len(x)), int); steps = np.zeros((2, len(x)), int)
r = np.random.default_rng(7)
trace = []
for it in range(600):
    W.update(it, x); ph = 0 if it < 200 else 1
    for j in range(len(x)):
        logy = fx + math.log(r.uniform()); lo = x[j] - W.w[j]*r.uniform(); hi = lo + W.w[j]
        jl = int(math.floor(50*r.uniform())); jr = 49 - jl; xt = x.copy()
        while True:
            xt[j] = lo
            if logf(xt) <= logy: break
            if jl == 0: hits[ph, j] += 1; break
            lo -= W.w[j]; jl -= 1; steps[ph, j] += 1
        while True:
            xt[j] = hi
            if logf(xt) <= logy: break
            if jr == 0: hits[ph, j] += 1; break
            hi += W.w[j]; jr -= 1; steps[ph, j] += 1
        while True:
            xt[j] = r.uniform(lo, hi); ft = logf(xt)
            if ft > logy: x, fx = xt.copy(), ft; break
            if xt[j] < x[j]: lo = xt[j]
            else: hi = xt[j]
    W.record(it, x); trace.append(x.copy())
tr = np.array(trace)
print("coordinate        hits_warm hits_saved steps_warm steps_saved width_final  post_mean  post_sd(saved)")
for j,nm in enumerate(names):
    print(f"{nm:14s} {hits[0,j]:9d} {hits[1,j]:10d} {steps[0,j]:10d} {steps[1,j]:11d} {W.w[j]:11.3f} {tr[200:,j].mean():10.3f} {tr[200:,j].std():10.3f}")

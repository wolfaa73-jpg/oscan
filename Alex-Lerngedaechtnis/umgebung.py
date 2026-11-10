"""Schätzt die Umgebung des künstlichen Körpers (kunstkoerper.GEMESSEN) aus der ersten Hälfte einer Lastaufnahme.
Angeglichen werden die Autokovarianz des Rests nach Abzug der Lastantwort, die Wechselrate der Anzeige und
der Hub, jeweils an 12 Simulationen mit festen Saaten. Braucht scipy. Explorativ, kein Teil der Tests.

Aufruf: umgebung.py messungen/koerper-zufallslast-8h-2026-11-10.csv
"""
import sys, warnings
import numpy as np
from scipy.signal import lfilter
from scipy.optimize import minimize
sys.path.insert(0, ".")
warnings.filterwarnings("ignore")
import vorhersage, kunstkoerper as k
LAGS = (0, 1, 2, 5, 10, 30, 60, 120, 300, 600, 1800)
def tief(x, tau):
    a = 1 / tau
    return lfilter([a], [1, -(1 - a)], x, zi=[x[0] * (1 - a)])[0]
def ou(rng, n, sigma, zeit):
    if sigma <= 0: return np.zeros(n)
    f = np.exp(-1 / zeit)
    e = rng.normal(0, sigma * np.sqrt(1 - f * f), n); e[0] = rng.normal(0, sigma)
    return lfilter([1], [1, -f], e)
def kennzahlen(t, l, tau=30):
    n = len(t)
    X = np.column_stack([np.ones(n), tief(l, tau)])
    w = np.linalg.lstsq(X, t, rcond=None)[0]
    r = t - np.einsum("ij,j->i", X, w)
    ac = [float(np.mean(r[q:] * r[:n - q])) for q in LAGS]
    return np.array(ac + [float((np.diff(t) != 0).mean()), float(w[1])]), w
def sim(l, tau, hub, grund, p, saat):
    rng = np.random.default_rng(saat)
    roh = grund + hub * tief(l, tau) + sum(ou(rng, len(l), s, z) for s, z in p["ou"]) + rng.normal(0, p["weiss"], len(l))
    return np.round(roh)
if __name__ == "__main__":
    t, l = vorhersage.lies(sys.argv[1])
    t = t / 10; n = len(t) // 2
    ziel, w = kennzahlen(t[:n], l[:n])
    skala = np.maximum(np.abs(ziel), 0.02)
    print("echt, erste Hälfte:", np.round(ziel, 3), "Grund %.2f Hub %.2f" % tuple(w))
    def verlust(x, zwei, zeige=False):
        weiss = abs(x[0]); teile = [(abs(x[1]), np.exp(x[2]))] + ([(abs(x[3]), np.exp(x[4]))] if zwei else [])
        hub = abs(x[-1])
        ks = np.mean([kennzahlen(sim(l[:n], 30, hub, w[0], dict(weiss=weiss, ou=teile), s), l[:n])[0] for s in range(12)], axis=0)
        if zeige: print("  sim:", np.round(ks, 3))
        return float(np.sum(((ks - ziel) / skala) ** 2))
    for zwei, start in ((True, [0.15, 0.3, np.log(60), 0.25, np.log(2000), 2.0]),):
        e = minimize(verlust, start, args=(zwei,), method="Nelder-Mead", options=dict(maxiter=500, xatol=1e-2, fatol=1e-3))
        x = e.x
        print("zwei Anteile" if zwei else "ein Anteil", "Verlust %.3f" % e.fun, "weiss %.3f" % abs(x[0]),
              "OU:", [(round(abs(x[i]), 3), round(float(np.exp(x[i + 1])))) for i in range(1, len(x) - 1, 2)], "Hub %.2f" % abs(x[-1]))
        verlust(x, zwei, True)

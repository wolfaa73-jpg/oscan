"""Kälteversuch auswerten: Gewichte (Körper, 10 Takte voraus) und Grenzen allein aus der Bezugsaufnahme,
angewandt auf die neue Aufnahme. Festlegung: beispiele/geraetelaeufe-2026-11/vorab-kaelte-2026-11-10.md.

Aufruf: kaelteversuch.py bezug.csv neu.csv"""
import datetime
import json
import sys
from pathlib import Path

import numpy as np

import vorhersage as vh

A, N = sys.argv[1], sys.argv[2]
H, ANF = 10, 120
ta, la = vh.lies(A); tn, ln = vh.lies(N)
ka = vh.eingaenge(ta, la)[0]; kn = vh.eingaenge(tn, ln)[0]
ia = np.arange(ANF, len(ta) - H)
w = np.linalg.lstsq(ka[ia], ta[ia + H] - vh.BEZUG, rcond=None)[0]
def rest(t, k):
    e = np.zeros(len(t)); e[H:] = (t[H:] - vh.BEZUG - k[:-H] @ w) / 10; return e
ea, en = rest(ta, ka), rest(tn, kn)
g = np.quantile(np.abs(vh.gleitmittel(ea, 20)[ANF:]), 0.999)
sn = vh.gleitmittel(en, 20)
spr = lambda t: np.concatenate([[0], (t[1:] - vh.gleitmittel(t, 5)[:-1]) / 10])
gs = np.quantile(np.abs(spr(ta)[ANF:]), 0.999)
print(f"Takte {len(tn)}, Temperatur {tn.min()/10:.0f} bis {tn.max()/10:.0f} °C, Mittel {tn.mean()/10:.2f}; 8-h-Lauf Mittel {ta.mean()/10:.2f}")
print(f"Grenze Körper {g:.2f} °C, Grenze Sprung {gs:.2f} °C")
print("Je 10 Takte: Uhrzeit (Minute des Beginns laut JSON), Takt, Temperaturen, Last, gemittelter Fehler, Alarm")
t0 = datetime.datetime.strptime(json.loads(Path(N).with_suffix(".json").read_text())["beginn"], "%Y-%m-%d %H:%M")
for a in range(0, len(tn), 10):
    b = min(a + 10, len(tn))
    al = "K" if (np.abs(sn[a:b]) > g).any() and a >= ANF else " "
    sp = "S" if (np.abs(spr(tn)[a:b]) > gs).any() and a >= ANF else " "
    print((t0 + datetime.timedelta(seconds=a)).strftime("%H:%M:%S"), f"{a+1:4d}", " ".join(f"{int(x/10)}" for x in tn[a:b]), f"L{int(ln[a])}", f"{sn[b-1]:+.2f}", al, sp)
al = np.abs(sn) > g; al[:ANF] = False
print("Körper-Alarm Takte:", [int(x)+1 for x in np.flatnonzero(al & ~np.roll(al, 1))], "Dauer gesamt", int(al.sum()))

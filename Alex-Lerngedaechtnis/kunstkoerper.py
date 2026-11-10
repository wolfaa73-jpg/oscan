"""Künstlicher Wärmekörper zum Proben der Auswertung, ohne Gerät. Eine Zeitkonstante, die Last heizt um
einen festen Hub, dazu langsame Drift der Umgebung und Rauschen; ausgegeben wird wie vom Chipsensor in
ganzen Grad. Der Lastplan ist koerper.lastdauern, also derselbe wie im Sketch. Die Zahlen für Zeitkonstante,
Hub, Drift und Rauschen sind grob aus den 24-h-Läufen geschätzt und kein Messergebnis.

Aufruf: kunstkoerper.py ziel.csv --tau 30 --hub 2.0 [--takte 28800] [--last 240 240 20261110] [--saat 1]
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

import koerper


def lastreihe(takte, an_s, aus_s, saat):
    """Lastbit je Sekunde, beginnend mit Arbeit."""
    reihe = []
    dauern = koerper.lastdauern(saat, an_s, aus_s, takte + 2)
    for k, d in enumerate(dauern):
        reihe += [1 - k % 2] * d
        if len(reihe) >= takte:
            break
    return reihe[:takte]


def temperaturen(last, tau, hub, ruhe=37.0, drift=1.0, rauschen=0.3, stufe=1.0, saat=1):
    """Grad je Takt. drift ist die Streuung der Umgebung nach einem Tag (Zufallsweg), stufe die Auflösung."""
    r, t, umgebung, werte = random.Random(saat), 0.0, 0.0, []
    schritt = drift / 86400 ** 0.5
    for bit in last:
        t += (hub * bit - t) / tau
        umgebung += r.gauss(0, schritt)
        roh = ruhe + umgebung + t + r.gauss(0, rauschen)
        werte.append(round(roh / stufe) * stufe if stufe else roh)
    return werte


def schreibe(ziel, last, temp, meta):
    with ziel.open("x", encoding="utf-8", newline="") as datei:
        aus = csv.writer(datei)
        aus.writerow(koerper.KOPF)
        for i, (bit, grad) in enumerate(zip(last, temp), start=1):
            aus.writerow([i, 1000 * i, round(10 * grad), 300000, 300, "OK", 0, 0, bit])
    ziel.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ziel", type=Path)
    p.add_argument("--tau", type=float, required=True)
    p.add_argument("--hub", type=float, required=True)
    p.add_argument("--takte", type=int, default=28800)
    p.add_argument("--last", type=int, nargs=3, default=(240, 240, 20261110), metavar=("AN", "AUS", "SAAT"))
    p.add_argument("--drift", type=float, default=1.0)
    p.add_argument("--rauschen", type=float, default=0.3)
    p.add_argument("--stufe", type=float, default=1.0)
    p.add_argument("--saat", type=int, default=1)
    a = p.parse_args(argv)
    last = lastreihe(a.takte, *a.last)
    temp = temperaturen(last, a.tau, a.hub, drift=a.drift, rauschen=a.rauschen, stufe=a.stufe, saat=a.saat)
    schreibe(a.ziel, last, temp, dict(kuenstlich=True, tau=a.tau, hub=a.hub, last=list(a.last), drift=a.drift,
                                      rauschen=a.rauschen, stufe=a.stufe, saat=a.saat, intervall_ms=1000))
    return 0


if __name__ == "__main__":
    sys.exit(main())

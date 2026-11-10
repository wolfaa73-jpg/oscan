"""Künstlicher Wärmekörper zum Proben der Auswertung, ohne Gerät. Eine Zeitkonstante, die Last heizt um
einen festen Hub, ausgegeben wird wie vom Chipsensor in ganzen Grad. Der Lastplan ist koerper.lastdauern,
also derselbe wie im Sketch.

Zwei Umgebungen:
- GEMESSEN (Vorgabe): an die erste Hälfte des Zufallslast-Laufs vom 10.11.2026 angeglichen, über die
  Autokovarianz des Rests, die Wechselrate der Anzeige und den Hub. Ein schneller Anteil (Streuung 0,33 °C,
  37 s), ein langsamer (0,47 °C, 85 min) und Messrauschen 0,15 °C. Geprüft an der zweiten Hälfte und am
  Lastlauf vom 5.11., siehe beispiele/geraetelaeufe-2026-11/probe-kunstkoerper-gemessen-2026-11-10.md.
- Die alte Annahme (--drift, --rauschen): Zufallsweg und weißes Rauschen. Sie machte „bleibt“ zu schlecht.

Aufruf: kunstkoerper.py ziel.csv [--tau 30 --hub 2.0] [--takte 28800] [--last 240 240 20261110] [--saat 1]
"""
import argparse
import csv
import json
import math
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


# (Streuung °C, Zeit s) je Anteil der Umgebung, Messrauschen °C, Ruhetemperatur °C, Zeitkonstante s, Hub °C.
GEMESSEN = dict(anteile=((0.33, 37.0), (0.47, 5100.0)), rauschen=0.15, ruhe=36.95, tau=30.0, hub=2.0)


def temperaturen(last, tau=GEMESSEN["tau"], hub=GEMESSEN["hub"], ruhe=None, drift=None, rauschen=None, stufe=1.0,
                 saat=1, anteile=None):
    """Grad je Takt. Ohne drift gilt die gemessene Umgebung: je Anteil ein gedämpfter Zufallsweg mit fester
    Streuung und Zeit. Mit drift (Streuung nach einem Tag) gilt die alte Annahme, ein freier Zufallsweg.
    stufe ist die Auflösung der Anzeige, 0 lässt ungerundet."""
    r, t, werte = random.Random(saat), 0.0, []
    alt = drift is not None
    ruhe = (37.0 if alt else GEMESSEN["ruhe"]) if ruhe is None else ruhe
    rauschen = (0.3 if alt else GEMESSEN["rauschen"]) if rauschen is None else rauschen
    anteile = () if alt else (GEMESSEN["anteile"] if anteile is None else anteile)
    schritt = drift / 86400 ** 0.5 if alt else 0.0
    faktor = [math.exp(-1 / zeit) for _, zeit in anteile]
    stand = [r.gauss(0, s) for s, _ in anteile]
    umgebung = 0.0
    for bit in last:
        t += (hub * bit - t) / tau
        umgebung += r.gauss(0, schritt) if alt else 0.0
        for i, (s, _) in enumerate(anteile):
            stand[i] = faktor[i] * stand[i] + r.gauss(0, s * math.sqrt(1 - faktor[i] ** 2))
        roh = ruhe + umgebung + sum(stand) + t + r.gauss(0, rauschen)
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
    p.add_argument("--tau", type=float, default=GEMESSEN["tau"])
    p.add_argument("--hub", type=float, default=GEMESSEN["hub"])
    p.add_argument("--takte", type=int, default=28800)
    p.add_argument("--last", type=int, nargs=3, default=(240, 240, 20261110), metavar=("AN", "AUS", "SAAT"))
    p.add_argument("--drift", type=float, help="alte Annahme: Zufallsweg, Streuung nach einem Tag")
    p.add_argument("--rauschen", type=float)
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

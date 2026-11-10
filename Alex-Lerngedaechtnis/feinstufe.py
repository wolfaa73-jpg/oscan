"""Explorativ: Lernt „Startwert h6/.6“ die Grenze zwischen tiefem und flachem Leck selbst, wenn er den
freien Speicher feiner sieht? Nur vorhandene Aufnahmen, keine Gerätezugriffe. Die Festlegung steht vorab
in messungen/vorab-feinstufe-2026-11-09.md.

KNAPP wird in N gleich breite Stufen zwischen den Grenzen für knapp und voll geteilt, K1 oben. Jede Stufe
erbt „Ki → VOLL“ mit 3 Beobachtungen. Das Erbe verblasst mit jedem eigenen Ausgang (Halbwertszeit 6), die
Erfahrung nach der Kontextregel (Halbwertszeit 6). Schwelle 0,6, Mindestbeleg 3, Blick über
kern.blick_voraus. N = 1 muss Takt für Takt „Startwert h6/.6“ aus pruefung24h.py gleichen. Gezählt wird mit
pruefung24h.zaehlen über die groben Speicherwörter, dazu je Leckdurchgang.
"""
import argparse
import os
import statistics
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import koerper
from kern import blick_voraus
from kostenlabor import wahrscheinlichkeiten
from pruefung24h import zaehlen
from vokabular import stufen_je_signal

STUFEN = (1, 2, 4, 8, 16)
HORIZONTE = (30, 60)
SCHWELLE, MINDESTBELEG, ERBE, HALBWERTSZEIT = 0.6, 3, 3.0, 6.0
HOCH, VOLL = "SPEICHER_KNAPP", "SPEICHER_VOLL"


def feinwort(heap, g, n):
    """OK, K1 bis Kn oder VOLL, mit denselben Vergleichen wie vokabular.stufen_je_signal."""
    if heap <= g.heap_ausfall:
        return "VOLL"
    if heap > g.heap_schwach:
        return "OK"
    return f"K{(g.heap_schwach - heap) * n // (g.heap_schwach - g.heap_ausfall) + 1}"


def ist_voll(wort):
    return wort == "VOLL"


class Feingedaechtnis:
    """Wie vokabular.Wortgedaechtnis mit startwert=True, nur mit eigenem Wortschatz und Erbe je Stufe."""

    def __init__(self, n):
        self.woerter = ("OK",) + tuple(f"K{i}" for i in range(1, n + 1)) + ("VOLL",)
        self.faktor = 0.5 ** (1 / HALBWERTSZEIT)
        self.gewichte = {w: Counter() for w in self.woerter}
        self.erbe = {w: Counter() for w in self.woerter}
        for i in range(1, n + 1):
            self.erbe[f"K{i}"]["VOLL"] = ERBE

    def beobachte(self, vorher, jetzt):
        if vorher is None:
            return
        zeile = self.gewichte[vorher]
        for folge in zeile:
            zeile[folge] *= self.faktor
        zeile[jetzt] += 1
        if jetzt != vorher:
            geerbt = self.erbe[vorher]
            for folge in geerbt:
                geerbt[folge] *= self.faktor

    def beleg(self, wort):
        return sum(self.gewichte[wort][f] + self.erbe[wort][f] for f in self.woerter)

    def kritisch_binnen(self, wort, horizont):
        return blick_voraus(self.woerter, self.gewichte, self.erbe, wort, horizont, ist_voll)


def lies(pfad):
    meta, werte = koerper.lies_aufnahme(pfad)
    if any(b["takt"] != a["takt"] + 1 for a, b in zip(werte, werte[1:])):
        raise ValueError(f"{pfad.name}: Lücke in den Takten.")
    g = koerper.Grenzen(**meta["grenzen"])
    grob = [stufen_je_signal(w["temp_dc"], w["heap"], w["luecke_us"], g)["speicher"] for w in werte]
    return g, [w["heap"] for w in werte], grob


def aufgabe(arg):
    """Warnung je Takt für ein Verfahren. art: protokoll (pruefung24h) oder fein mit n Stufen."""
    pfad, art, n, horizont = arg
    g, heaps, grob = lies(Path(pfad))
    if art == "protokoll":
        return arg, [p >= SCHWELLE for p in wahrscheinlichkeiten(grob, HOCH, VOLL, 6, horizont)]
    woerter = [feinwort(h, g, n) for h in heaps]
    for w, gw in zip(woerter, grob):  # Die feinen Wörter müssen die groben nur verfeinern.
        if (w == "VOLL") != (gw == VOLL) or (w == "OK") != (gw == "OK"):
            raise ValueError("Feine und grobe Stufen passen nicht zusammen.")
    modell, warn, vorher = Feingedaechtnis(n), [], None
    for w in woerter:
        modell.beobachte(vorher, w)
        warn.append(w != "VOLL" and modell.beleg(w) >= MINDESTBELEG
                    and modell.kritisch_binnen(w, horizont) >= SCHWELLE)
        vorher = w
    return arg, warn


def durchgaenge(grob):
    """Je Lauf außerhalb von OK: (Beginn, Ende exklusiv, Beginn von VOLL oder None, Zahl der VOLL-Läufe)."""
    ergebnis, t, n = [], 0, len(grob)
    while t < n:
        if grob[t] == "OK":
            t += 1
            continue
        a = t
        while t < n and grob[t] != "OK":
            t += 1
        voll = [i for i in range(a, t) if grob[i] == VOLL]
        laeufe = sum(1 for i in voll if i == a or grob[i - 1] != VOLL)
        ergebnis.append((a, t, voll[0] if voll else None, laeufe))
    return ergebnis


def je_durchgang(grob, warn, horizont):
    ende = len(grob) - horizont
    liste = durchgaenge(grob)
    tief, flach, wechsel = [], [], []
    for k, (a, e, b, _) in enumerate(liste):
        if b is None:
            flach.append(any(warn[a:e]))
            continue
        if not horizont <= b < ende:
            continue
        frueh = [s for s in range(b - horizont, b) if warn[s] and grob[s] != VOLL]
        eintrag = (b, b - frueh[0] if frueh else None)
        tief.append(eintrag)
        if k and liste[k - 1][2] is None:
            wechsel.append(eintrag)
    return dict(tief=tief, flach=flach, wechsel=wechsel,
                ok_warn=sum(1 for w, x in zip(grob, warn) if w == "OK" and x),
                mehrfach=sum(1 for *_, laeufe in liste if laeufe > 1))


def vorlauf(eintraege):
    zeiten = [z for _, z in eintraege if z is not None]
    return f"{statistics.median(zeiten):g} ({min(zeiten)})" if zeiten else "–"


def bericht(pfade, ergebnisse):
    out = []
    for pfad in pfade:
        _, heaps, grob = lies(pfad)
        dg = durchgaenge(grob)
        out += ["", f"## {pfad.name}", "",
                f"{len(grob)} Takte, {len(dg)} Durchgänge, davon {sum(b is not None for _, _, b, _ in dg)} tief, "
                f"{sum(b is None for _, _, b, _ in dg)} flach; Durchgänge mit mehr als einem VOLL-Lauf: "
                f"{sum(l > 1 for *_, l in dg)}."]
        for h in HORIZONTE:
            proto = ergebnisse[(str(pfad), "protokoll", 0, h)]
            eins = ergebnisse[(str(pfad), "fein", 1, h)]
            gleich = sum(a == b for a, b in zip(proto, eins))
            out += ["", f"### H = {h}", "",
                    f"Gegenprobe N = 1 gegen „Startwert h6/.6“ aus pruefung24h: {gleich} von {len(proto)} Takten gleich.",
                    "", "| Verfahren | Warnanteil | Präzision | Phasen | ohne Warnung | Wechsel vorgewarnt "
                    "| flache mit Warnung | Warnung in OK | Vorlauf Median (min) | nach Wechsel | Kphase | Ktakt |",
                    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
            verfahren = [("Feste Regel", [w == HOCH for w in grob]), ("Startwert h6/.6", proto)]
            verfahren += [(f"Fein N = {n}", ergebnisse[(str(pfad), "fein", n, h)]) for n in STUFEN]
            verfahren += [("Immer warnen", [w != VOLL for w in grob]), ("Nie warnen", [False] * len(grob))]
            for name, warn in verfahren:
                z, d = zaehlen(grob, warn, h), je_durchgang(grob, warn, h)
                gew = sum(x is not None for _, x in d["wechsel"])
                out.append(
                    f"| {name} | {100 * z['warnanteil']:.2f} % | "
                    + ("–" if z["trefferquote"] is None else f"{100 * z['trefferquote']:.2f} %")
                    + f" | {z['phasen']} | {z['verpasst']} | {gew}/{len(d['wechsel'])} | "
                    f"{sum(d['flach'])}/{len(d['flach'])} | {d['ok_warn']} | {vorlauf(d['tief'])} | "
                    f"{vorlauf(d['wechsel'])} | {z['kosten_phase_r10']} | {z['kosten_takt_r10']} |")
            verpasst = [b for b, x in je_durchgang(grob, proto, h)["wechsel"] if x is None]
            if verpasst:
                out.append(f"\nErster verpasster Wechsel von „Startwert h6/.6“: Takt {verpasst[0]}, "
                           f"nach {verpasst[0] / 3600:.2f} h.")
    return "\n".join(out) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("aufnahmen", nargs="+", type=Path)
    p.add_argument("--prozesse", type=int, default=os.cpu_count())
    arg = p.parse_args(argv)
    auftraege = [(str(pf), "protokoll", 0, h) for pf in arg.aufnahmen for h in HORIZONTE]
    auftraege += [(str(pf), "fein", n, h) for pf in arg.aufnahmen for n in STUFEN for h in HORIZONTE]
    with Pool(arg.prozesse) as pool:
        ergebnisse = dict(pool.imap_unordered(aufgabe, auftraege))
    print("# Feinere Speicherstufen, explorativ\n\nFestlegung: messungen/vorab-feinstufe-2026-11-09.md. "
          "Stufen N = " + ", ".join(map(str, STUFEN)) + ", Horizonte " + ", ".join(map(str, HORIZONTE)) + ".")
    print(bericht(arg.aufnahmen, ergebnisse), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

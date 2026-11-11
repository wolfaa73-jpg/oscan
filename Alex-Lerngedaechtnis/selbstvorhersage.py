"""Selbstvorhersage, Referenz für das Gerät: Der Knoten sagt seine Chiptemperatur 10 und 60 Takte voraus,
lernt die Gewichte mitlaufend und merkt, wenn er sich verschätzt. Gerechnet wird Takt für Takt in einfacher
Genauigkeit und in fester Reihenfolge, so wie es die Firmware später tun soll.

Eingänge je Takt (wie vorhersage.eingaenge, in Grad): 1, Mittel der letzten 5 Takte minus 37 °C, dessen
Änderung gegen 5 Takte davor, Last jetzt, Lastanteil der letzten 60 und 120 Takte.

Lernen: rekursive kleinste Quadrate mit Vergessen. Die Probe von Takt t−h wird gelernt, sobald ihr Ziel bei t
bekannt ist. Ein Deckel auf die Spur der Kovarianz verhindert, dass sie sich in langer Ruhe aufschaukelt.

Überraschung (nur am kurzen Horizont): Fehler der wirklich abgegebenen Vorhersage, über MITTEL Takte gemittelt.
Das Normalmaß ist das verblassende Mittel seines Quadrats. Überrascht ist der Knoten, wenn der Betrag über
FAKTOR mal der Wurzel des Normalmaßes liegt. Solange er überrascht ist, lernt das Normalmaß nicht weiter, die
Gewichte schon: Die Störung bleibt offen, bis die Vorhersage wieder passt.

Herkunft der Konstanten: beispiele/geraetelaeufe-2026-11/selbstvorhersage-2026-11-11.md.

Aufruf: selbstvorhersage.py aufnahme.csv [--vorlauf fruehere.csv …]
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

import koerper

HORIZONTE = (10, 60)            # der erste trägt die Überraschung
BEZUG_DC = 370
VERGESSEN = 0.9995              # je Takt
P_START = 100.0
DECKEL = 600.0                  # Spur der Kovarianz, gleich dem Startwert 6 × P_START
MITTEL = 20                     # Takte, über die der Fehler gemittelt wird
NORM_HALBWERT = 3600            # Takte
NORM_AB = 600                   # so viele Fehler vergehen, bevor das Normalmaß mitzählt
ANLAUF = 1800                   # so viele Fehler vergehen, bevor er überrascht sein darf
FAKTOR = 4.0
N = 6


class Lerner:
    """Rekursive kleinste Quadrate für einen Horizont."""

    def __init__(self, h, typ):
        self.h, self.f = h, typ
        self.w = [typ(0)] * N
        self.p = [[typ(P_START if i == j else 0) for j in range(N)] for i in range(N)]
        self.x = [None] * h          # Eingänge der letzten h Takte
        self.v = [None] * h          # dazu die abgegebenen Vorhersagen
        self.n = 0

    def takt(self, x, y):
        """Lernt die Probe von vor h Takten am Ziel y, sagt dann aus x voraus. Liefert (Vorhersage für in h
        Takten, Fehler der vor h Takten abgegebenen Vorhersage oder None)."""
        f, platz, fehler = self.f, self.n % self.h, None
        alt = self.x[platz]
        if alt is not None:
            fehler = y - self.v[platz]
            pa = [f(0)] * N
            for i in range(N):
                s = f(0)
                for j in range(N):
                    s += self.p[i][j] * alt[j]
                pa[i] = s
            nenner, vor = f(VERGESSEN), f(0)
            for i in range(N):
                nenner += alt[i] * pa[i]
                vor += alt[i] * self.w[i]
            k = [pa[i] / nenner for i in range(N)]
            rest = y - vor
            for i in range(N):
                self.w[i] += k[i] * rest
            neu = [[self.p[i][j] - k[i] * pa[j] for j in range(N)] for i in range(N)]
            spur = f(0)
            for i in range(N):
                spur += neu[i][i]
            teiler = f(VERGESSEN) if spur / f(VERGESSEN) < f(DECKEL) else f(1)
            for i in range(N):
                for j in range(i, N):
                    wert = (neu[i][j] + neu[j][i]) / (f(2) * teiler)
                    self.p[i][j] = self.p[j][i] = wert
        v = f(0)
        for i in range(N):
            v += x[i] * self.w[i]
        self.x[platz], self.v[platz] = x, v
        self.n += 1
        return v, fehler

    def spur(self):
        return float(sum(self.p[i][i] for i in range(N)))


class Selbstvorhersage:
    def __init__(self, typ=np.float32):
        self.f = typ
        self.lerner = [Lerner(h, typ) for h in HORIZONTE]
        self.temp, self.m5, self.last = [], [], []   # Ringe: 5 Temperaturen, 5 Mittel, 120 Lastbits
        self.fehler = []                             # Ring: MITTEL Fehler am kurzen Horizont
        self.fehlerzahl = 0
        self.norm = typ(0)
        self.normzahl = 0
        self.ueberrascht = False
        self.letzte = None

    def eingang(self, temp_dc, last):
        f = self.f
        self.temp = (self.temp + [int(temp_dc)])[-5:]
        self.last = (self.last + [int(last)])[-120:]
        m5 = f(sum(self.temp)) / f(len(self.temp))
        davor = self.m5[0] if self.m5 else m5      # das Mittel von vor 5 Takten, anfangs das erste
        self.m5 = (self.m5 + [m5])[-5:]
        l60 = self.last[-60:]
        return [f(1), (m5 - f(BEZUG_DC)) / f(10), (m5 - davor) / f(10), f(last),
                f(sum(l60)) / f(len(l60)), f(sum(self.last)) / f(len(self.last))]

    def takt(self, temp_dc, last):
        """Liefert dict: v je Horizont (°C), fehler am kurzen Horizont, mittel, grenze, ueberrascht."""
        f = self.f
        if temp_dc is None:          # nicht lesbar: zählt wie die letzte lesbare
            if self.letzte is None:
                return None
            temp_dc = self.letzte
        self.letzte = temp_dc
        x = self.eingang(temp_dc, last)
        y = f(int(temp_dc) - BEZUG_DC) / f(10)
        aus, kurz, felder = {}, None, []
        for k, lerner in enumerate(self.lerner):
            v, fehler = lerner.takt(x, y)
            aus[f"v{lerner.h}"] = float(v) + BEZUG_DC / 10
            felder.append(milli(v) + 100 * BEZUG_DC)
            if k == 0:
                kurz = fehler
        mittel = grenze = None
        if kurz is not None:
            self.fehler = (self.fehler + [kurz])[-MITTEL:]
            self.fehlerzahl += 1
            s = f(0)
            for e in self.fehler:
                s += e
            s /= f(len(self.fehler))
            grenze = f(FAKTOR) * np.sqrt(self.norm)
            self.ueberrascht = bool(self.fehlerzahl > ANLAUF and abs(s) > grenze)
            if self.fehlerzahl > NORM_AB and not self.ueberrascht:
                self.normzahl += 1
                anteil = max(f(1) - f(0.5 ** (1 / NORM_HALBWERT)), f(1) / f(self.normzahl))
                self.norm += anteil * (s * s - self.norm)
            felder += [milli(kurz), milli(s), milli(grenze)]
            mittel, grenze = float(s), float(grenze)
        else:
            felder += ["-", "-", "-"]
        aus["felder"] = felder + [int(self.ueberrascht)]
        aus.update(fehler=None if kurz is None else float(kurz), mittel=mittel, grenze=grenze,
                   ueberrascht=self.ueberrascht)
        return aus


def milli(grad):
    """Tausendstelgrad wie lround im Gerät: kaufmännisch gerundet, aus der doppelt genauen Zahl."""
    d = float(grad) * 1000.0
    return int(math.floor(abs(d) + 0.5)) * (-1 if d < 0 else 1)


KOPF = ("takt", "v10_mg", "v60_mg", "fehler_mg", "mittel_mg", "grenze_mg", "ueberrascht")
# So meldet das Gerät seine Konstanten auf VORHERSAGE 1.
KONSTANTEN = (*HORIZONTE, round(VERGESSEN * 10000), round(DECKEL), MITTEL, NORM_HALBWERT, NORM_AB, ANLAUF,
              round(FAKTOR * 10))


def zeile(takt, aus):
    """Die Zeile, die das Gerät zu diesem Takt sendet, oder None vor der ersten lesbaren Temperatur."""
    return None if aus is None else "VORHERSAGE," + ",".join(map(str, [takt] + aus["felder"]))


def lies(pfad):
    _, werte = koerper.lies_aufnahme(Path(pfad))
    return [w["temp_dc"] for w in werte], [w["reiz"] & 1 for w in werte]


def rechne(temp, last, modell=None):
    modell = modell or Selbstvorhersage()
    zeilen = [modell.takt(t, l) for t, l in zip(temp, last)]
    return modell, zeilen


def ereignisse(flags):
    """(Beginn, Länge) jeder Strecke mit gesetztem Flag, Takte ab 1."""
    aus, t, n = [], 0, len(flags)
    while t < n:
        if flags[t]:
            a = t
            while t < n and flags[t]:
                t += 1
            aus.append((a + 1, t - a))
        else:
            t += 1
    return aus


def bericht(name, temp, zeilen, ab=0):
    temp = np.array(temp, float) / 10
    n = len(temp)
    out = [f"## {name}", "", f"{n} Takte, Temperatur {temp.min():.0f} bis {temp.max():.0f} °C, gewertet ab Takt {ab + 1}.",
           "", "| Horizont | Verfahren | Betragsfehler °C | Wurzelfehler °C | Anteil „bleibt“ (Betrag / Wurzel) |",
           "| ---: | --- | ---: | ---: | ---: |"]
    for h in HORIZONTE:
        i = np.arange(ab, n - h)
        ziel = temp[i + h]
        def f(v):
            d = v - ziel
            return np.mean(np.abs(d)), np.sqrt(np.mean(d * d))
        bleibt = f(temp[i])
        mittel = f((np.cumsum(temp) / np.arange(1, n + 1))[i])
        selbst = f(np.array([z[f"v{h}"] for z in zeilen])[i])
        for titel, (a, w) in (("bleibt", bleibt), ("Mittel bisher", mittel), ("Selbstvorhersage", selbst)):
            out.append(f"| {h} | {titel} | {a:.3f} | {w:.3f} | {100 * a / bleibt[0]:.0f} % / {100 * w / bleibt[1]:.0f} % |")
    flags = [z["ueberrascht"] for z in zeilen[ab:]]
    er = [(a + ab, l) for a, l in ereignisse(flags)]
    out += ["", f"Überrascht in {sum(flags)} von {len(flags)} Takten, {len(er)} Strecken"
            + (f", das sind {3600 * len(er) / len(flags):.2f} je Stunde." if flags else "."),
            "Strecken (Beginn, Länge): " + (", ".join(f"{a} ({l})" for a, l in er[:40]) or "keine") + "."]
    return "\n".join(out) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("aufnahme")
    p.add_argument("--vorlauf", nargs="*", default=[], help="frühere Aufnahmen, an denen er vorher lernt")
    a = p.parse_args(argv)
    modell = Selbstvorhersage()
    for pfad in a.vorlauf:
        rechne(*lies(pfad), modell)
    temp, last = lies(a.aufnahme)
    _, zeilen = rechne(temp, last, modell)
    print("# Selbstvorhersage\n")
    print(bericht(Path(a.aufnahme).name + (" nach Vorlauf" if a.vorlauf else ""), temp, zeilen,
                  0 if a.vorlauf else ANLAUF), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

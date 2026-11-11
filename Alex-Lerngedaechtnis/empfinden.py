"""Empfinden v1, float32-Referenz zu Empfinden.h. Entscheidungen: EMPFINDEN-PLAN.md.

Der schnelle Eingang ist das unveränderte 20-Takt-Fehlermittel der Selbstvorhersage.
Fehlende Temperatur: kein Lernen, keine neuen Wörter. Kalte Starts: 1800 gültige
Takte Anlauf; nach Laden 600. Ein Neustart setzt nur diesen Anlauf zurück.
"""
import math
import struct
import numpy as np

F = np.float32
HM, HL, HG = 600, 86400, 3600
ANLAUF, WIEDERANLAUF, NORM_AB = 1800, 600, 600
KONSTANTEN = (1, HM, HL, HG, ANLAUF, WIEDERANLAUF, NORM_AB, 200, 500, 1500)
KOPF = ("takt", "gerade", "woanders", "anlauf", "gueltig", "mass_gerade_mg", "mass_woanders_mg", "mittel_mg", "langsam_mg")
MAGIE = 0x31464D45
FORMAT = struct.Struct("<8I2i4fI")


def anteil(h):
    return F(1) - F(0.5 ** (1 / h))


def milli(x):
    v = float(x) * 1000
    return (-1 if v < 0 else 1) * math.floor(abs(v) + .5)


def stufe(d, mass, vorher=0):
    """Vergleiche statt Logarithmus. Nur die Grenze 0/1 hat Hysterese 2/1,5."""
    a, grenze, s = abs(F(d)), F(2) * F(mass), 0
    while s < 30 and a >= grenze:
        s += 1
        grenze *= F(2)
    vorzeichen = -1 if d < 0 else 1
    if s == 0 and vorher * vorzeichen > 0 and a >= F(1.5) * F(mass):
        s = 1
    return vorzeichen * s


def summe(daten):
    s = 0
    for b in daten:
        s = (s * 31 + b) & 0xffffffff
    return s


class Empfinden:
    def __init__(self):
        self.n = self.ng = self.nw = self.boot = 0
        self.init = False
        self.aktiv = True
        self.g = self.w = 0
        self.M = self.L = F(0)
        self.qg, self.qw = F(.04), F(.25)

    def neustart(self):
        self.boot = 0
        self.g = self.w = 0

    def takt(self, temp_dc, mittel):
        gueltig = temp_dc is not None
        if gueltig:
            x = F(temp_dc) / F(10)
            gueltig = bool(np.isfinite(x) and -100 <= float(x) <= 200
                            and (mittel is None or np.isfinite(F(mittel))))
        if gueltig:
            self.n = min(16777215, self.n + 1)
            self.boot = min(16777215, self.boot + 1)
            if not self.init:
                self.M = self.L = x
                self.init = True
            self.M += anteil(HM) * (x - self.M)
            self.L += anteil(HL) * (x - self.L)
        anlauf = self.n <= ANLAUF or self.boot <= WIEDERANLAUF
        mg, mw = np.sqrt(self.qg), np.sqrt(self.qw)
        d = self.M - self.L
        self.g = stufe(F(mittel), mg, self.g) if gueltig and not anlauf and mittel is not None else 0
        self.w = stufe(d, mw, self.w) if gueltig and not anlauf else 0
        if gueltig and self.boot > NORM_AB:
            for kanal, wert, h, boden, mass in (("g", None if mittel is None else F(mittel), HG, F(.04), mg),
                                             ("w", d, HL, F(.25), mw)):
                if wert is None or abs(wert) >= F(4) * mass:
                    continue
                n = min(16777215, getattr(self, "n" + kanal) + 1)
                setattr(self, "n" + kanal, n)
                q = getattr(self, "q" + kanal)
                q += anteil(h) * (wert * wert - q)
                setattr(self, "q" + kanal, max(boden, q))
        return [self.g, self.w, int(anlauf), int(gueltig), milli(mg), milli(mw), milli(self.M), milli(self.L)]

    def exportiere(self):
        b = FORMAT.pack(MAGIE, 1, self.n, self.ng, self.nw, self.boot, int(self.init), int(self.aktiv),
                        self.g, self.w, self.M, self.L, self.qg, self.qw, 0)
        return b[:-4] + struct.pack("<I", summe(b[:-4]))

    def importiere(self, daten):
        if len(daten) != FORMAT.size:
            raise ValueError("Empfinden-Stand hat falsche Länge")
        m, v, n, ng, nw, boot, init, aktiv, g, w, M, L, qg, qw, crc = FORMAT.unpack(daten)
        if (m != MAGIE or v != 1 or crc != summe(daten[:-4]) or init not in (0, 1) or aktiv not in (0, 1)
                or not all(0 <= x <= 16777215 for x in (n, ng, nw, boot)) or boot > n or abs(g) > 30 or abs(w) > 30
                or not all(math.isfinite(x) for x in (M, L, qg, qw)) or not -100 <= M <= 200 or not -100 <= L <= 200
                or not F(.04) <= qg <= 1e8 or not F(.25) <= qw <= 1e8):
            raise ValueError("Ungültiger Empfinden-Stand")
        self.n, self.ng, self.nw, self.boot, self.init, self.aktiv = n, ng, nw, boot, bool(init), bool(aktiv)
        self.g, self.w = g, w
        self.M, self.L, self.qg, self.qw = map(F, (M, L, qg, qw))


def zeile(takt, aus):
    return "EMPFINDEN," + ",".join(map(str, [takt] + aus))


def name(s):
    return "normal" if not s else ("wärmer " if s > 0 else "kälter ") + str(abs(s))

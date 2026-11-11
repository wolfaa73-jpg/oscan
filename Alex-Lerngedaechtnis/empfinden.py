"""Empfinden in drei Geschwindigkeiten, explorativ. schnell = Mittel über 5 Takte, mittel = verblassendes
Mittel mit 10 min Halbwertszeit, langsam = 1 Tag. Empfunden wird schnell gegen mittel („passiert mir gerade“)
und mittel gegen langsam („ich bin woanders“), jeweils in Vielfachen der eigenen üblichen Abweichung.
Stufe 0 = normal (unter dem Doppelten), dann je Verdopplung eine Stufe. Das Maßband lernt langsam und nur
aus Takten unter Stufe 2. Nicht Teil der Tests. Ergebnisse: beispiele/geraetelaeufe-2026-11/fahrt-2026-11-11.md
und das Brainstorming vom 11.11.2026.

Aufruf im Laborordner: empfinden.py"""
import sys, math, itertools
import numpy as np
import selbstvorhersage as sv, kunstkoerper as kk

HM, HL = 600, 86400

class Empfinden:
    def __init__(self):
        self.n = 0; self.ring = []; self.M = self.L = None; self.q1 = self.q2 = 0.0; self.n1 = self.n2 = 0
    @staticmethod
    def stufe(e):
        return 0 if e < 2 else int(math.log2(e))
    def takt(self, grad):
        self.n += 1
        self.ring = (self.ring + [grad])[-5:]
        S = sum(self.ring) / len(self.ring)
        if self.M is None: self.M = self.L = S
        d1, d2 = S - self.M, self.M - self.L
        u1, u2 = math.sqrt(self.q1), math.sqrt(self.q2)
        e1 = abs(d1) / u1 if u1 > 0 and self.n > 1800 else 0.0
        e2 = abs(d2) / u2 if u2 > 0 and self.n > 1800 else 0.0
        s1, s2 = self.stufe(e1), self.stufe(e2)
        if s1 < 2:
            self.n1 += 1; self.q1 += max(1 - 0.5 ** (1 / HL), 1 / self.n1) * (d1 * d1 - self.q1)
        if s2 < 2:
            self.n2 += 1; self.q2 += max(1 - 0.5 ** (1 / HL), 1 / self.n2) * (d2 * d2 - self.q2)
        self.M += (1 - 0.5 ** (1 / HM)) * (S - self.M)
        self.L += max(1 - 0.5 ** (1 / HL), 1 / self.n) * (S - self.L)
        return (s1 * (1 if d1 > 0 else -1), s2 * (1 if d2 > 0 else -1), S, self.M, self.L, u1, u2)

def name(s):
    return "normal" if s == 0 else ("wärmer " if s > 0 else "kälter ") + str(abs(s))

def folge(werte, ab=0):
    out, pos = [], ab
    for w, g in itertools.groupby(werte[ab:]):
        d = len(list(g))
        if w != 0: out.append(f"{name(w)} ({pos + 1}–{pos + d})")
        pos += d
    return out


def main():
    D = "beispiele/geraetelaeufe-2026-11/roh/"
    t8, _ = sv.lies(D + "koerper-zufallslast-8h-2026-11-10.csv"); tk, _ = sv.lies(D + "koerper-kaelte-2026-11-10.csv")
    e = Empfinden()
    r8 = [e.takt(t / 10) for t in t8]
    print(f"Nach 8 h: mittel {e.M:.2f} °C, langsam {e.L:.2f} °C; Maßband schnell-gegen-mittel {math.sqrt(e.q1):.2f} °C, mittel-gegen-langsam {math.sqrt(e.q2):.2f} °C")
    for k, titel in ((0, "passiert mir gerade"), (1, "ich bin woanders")):
        z = np.array([abs(r[k]) for r in r8[1800:]])
        print(f"  Ruhiger Lauf, „{titel}“: " + ", ".join(f"Stufe {s}: {100 * np.mean(z == s):.2f} %" for s in range(0, 5)))
    rk = [e.takt(t / 10) for t in tk]
    print(f"\nKälteversuch (nach dem Versuch: mittel {e.M:.2f}, langsam {e.L:.2f}, Maßbänder {math.sqrt(e.q1):.2f} / {math.sqrt(e.q2):.2f} °C)")
    print("Takt | Temp | schnell | mittel | passiert mir gerade | ich bin woanders")
    for i in range(120, 900, 20):
        seg = rk[i:i + 20]
        a = min(seg, key=lambda r: -abs(r[0]))[0]; b = min(seg, key=lambda r: -abs(r[1]))[1]
        print(f"{i + 1:4d} | {tk[i] // 10} | {seg[-1][2]:.1f} | {seg[-1][3]:.1f} | {name(a):9s} | {name(b)}")
    print("\nWortfolge „passiert mir gerade“ ab Stufe 2:", "; ".join(x for x in folge([r[0] if abs(r[0]) >= 2 else 0 for r in rk])))
    print("Wortfolge „ich bin woanders“ ab Stufe 2:", "; ".join(x for x in folge([r[1] if abs(r[1]) >= 2 else 0 for r in rk])))

    # Umzug in den Keller: 8 h wie gewohnt, dann dauerhaft 8 °C kälter, 12 h
    print("\n## Umzug in den Keller (Simulator): 8 h gewohnt, dann 12 h lang 8 °C kälter")
    last = kk.lastreihe(72000, 240, 240, 20261110)
    roh = kk.temperaturen(last, stufe=0, saat=77)
    temp = [round(x - (8.0 * (1 - math.exp(-(i - 28800) / 300)) if i >= 28800 else 0.0)) for i, x in enumerate(roh)]
    e = Empfinden(); r = [e.takt(t) for t in temp]
    for std in (7.9, 8.02, 8.1, 8.25, 8.5, 9, 10, 12, 16, 19.9):
        i = int(std * 3600); x = r[i]
        print(f"  Stunde {std:5.2f}: {temp[i]} °C, mittel {x[3]:.1f}, langsam {x[4]:.1f} | gerade: {name(x[0]):9s} | woanders: {name(x[1])}")
    z = [abs(x[0]) >= 2 for x in r[28800:]]
    print(f"  „passiert mir gerade“ ab Stufe 2 dauert nach dem Umzug {sum(z)} Takte; „woanders“ ab Stufe 2 noch nach 12 h: {abs(r[-1][1]) >= 2}")


if __name__ == "__main__":
    main()

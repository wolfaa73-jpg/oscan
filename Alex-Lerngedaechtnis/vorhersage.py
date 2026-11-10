"""Sagt ein kleines lineares Modell die eigene Chiptemperatur besser voraus als „bleibt, wie es ist“?
Nur vorhandene Aufnahmen, keine Gerätezugriffe. Festlegung: messungen/vorab-vorhersage-2026-11-10.md."""
import sys
from pathlib import Path

import numpy as np

import koerper

HORIZONTE = (30, 60)
ANFANG, BEZUG, SCHRITT = 120, 370.0, 0.05


def lies(pfad):
    _, werte = koerper.lies_aufnahme(Path(pfad))
    if any(w["temp_dc"] is None for w in werte):
        raise ValueError("Fehlende Temperaturwerte.")
    return (np.array([w["temp_dc"] for w in werte], float), np.array([w["reiz"] & 1 for w in werte], float))


def gleitmittel(x, n):
    """Mittel der letzten n Werte bis einschließlich t, vorn mit dem vorhandenen Stück."""
    c = np.cumsum(np.insert(x, 0, 0.0))
    i = np.arange(1, len(x) + 1)
    return (c[i] - c[np.maximum(i - n, 0)]) / np.minimum(i, n)


def seit_wechsel(last):
    seit, z = np.zeros(len(last), int), 0
    for t in range(len(last)):
        z = 0 if t and last[t] != last[t - 1] else z + 1
        seit[t] = z
    return seit


def eingaenge(temp, last):
    m5 = gleitmittel(temp, 5)
    davor = np.concatenate([np.full(5, m5[0]), m5[:-5]])
    koerper_x = np.column_stack([np.ones(len(temp)), m5 - BEZUG, m5 - davor, last,
                                 gleitmittel(last, 60), gleitmittel(last, 120)])
    seit = seit_wechsel(last)
    fach = np.minimum(seit, 239) // 30 + 8 * last.astype(int)
    rhythmus = np.zeros((len(temp), 16))
    rhythmus[np.arange(len(temp)), fach] = 1.0
    return koerper_x, np.column_stack([koerper_x, rhythmus]), seit


def mitlernen(x, ziel, h):
    """Normalisiertes LMS. Die Probe von Takt t−h wird gelernt, sobald ihr Ziel bei t bekannt ist."""
    w, vorhersage = np.zeros(x.shape[1]), np.zeros(len(x))
    for t in range(len(x)):
        if t - h >= 0:
            alt = x[t - h]
            w += SCHRITT * (ziel[t] - alt @ w) * alt / (1e-9 + alt @ alt)
        vorhersage[t] = x[t] @ w
    return vorhersage


def fehler(vorhersage, ziel, maske):
    d = (vorhersage - ziel)[maske] / 10.0
    return np.mean(np.abs(d)), np.sqrt(np.mean(d * d))


def haelften(pfad):
    """Eine Aufnahme: an der ersten Hälfte anpassen, an der zweiten prüfen. Zwischen beiden bleiben
    ANFANG Takte ungewertet. Festlegung: messungen/vorab-zufallslast-2026-11-10.md."""
    temp, last = lies(pfad)
    k, r, seit = eingaenge(temp, last)
    mitte = len(temp) // 2
    print(f"# Temperaturvorhersage, zwei Hälften\n\n{Path(pfad).name}: {len(temp)} Takte, anpassen bis Takt {mitte}, "
          f"prüfen ab Takt {mitte + ANFANG + 1}. Temperatur {temp.min() / 10:.1f} bis {temp.max() / 10:.1f} °C, "
          f"{int((np.diff(last) != 0).sum())} Lastwechsel.")
    for h in HORIZONTE:
        ia, ip = np.arange(ANFANG, mitte - h), np.arange(mitte + ANFANG, len(temp) - h)
        za, zp = temp[ia + h] - BEZUG, temp[ip + h] - BEZUG
        ziel_bei_t = temp - BEZUG  # bei Takt t wird das Ziel der Probe von t−h bekannt
        online = mitlernen(k, ziel_bei_t, h)
        fest = lambda x, spalten: np.einsum("ij,j->i", x[ip][:, spalten],
                                            np.linalg.lstsq(x[ia][:, spalten], za, rcond=None)[0])
        zeilen = [("bleibt", temp[ip] - BEZUG), ("Mittel", np.full(len(ip), temp[:mitte].mean() - BEZUG)),
                  ("ohne Lastgeschichte", fest(k, [0, 1, 2, 3])), ("Körper", fest(k, list(range(6)))),
                  ("Körper, lernt mit", online[ip]), ("mit Takten seit dem Lastwechsel", fest(r, list(range(r.shape[1]))))]
        nah, alle = seit[ip] < 60, np.ones(len(ip), bool)
        massstab = min(fehler(zeilen[0][1], zp, alle)[0], fehler(zeilen[1][1], zp, alle)[0])
        print(f"\n## H = {h}\n\n{len(ip)} Prüftakte, davon {int(nah.sum())} bis 60 Takte nach einem Lastwechsel.\n\n"
              "| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil des besseren Maßstabs |\n"
              "| --- | ---: | ---: | ---: | ---: | ---: |")
        for name, v in zeilen:
            a, w = fehler(v, zp, alle)
            print(f"| {name} | {a:.3f} | {w:.3f} | {fehler(v, zp, nah)[0]:.3f} | {fehler(v, zp, ~nah)[0]:.3f} | "
                  f"{100 * a / massstab:.1f} % |")
    return 0


def main(argv):
    if len(argv) == 2:
        return haelften(argv[1])
    anpass, pruef = argv[1], argv[2]
    ta, la = lies(anpass)
    tp, lp = lies(pruef)
    print(f"# Temperaturvorhersage\n\nAnpassen: {Path(anpass).name}, prüfen: {Path(pruef).name}. "
          f"Mittel der Anpass-Aufnahme {ta.mean() / 10:.2f} °C, der Prüf-Aufnahme {tp.mean() / 10:.2f} °C.")
    ka, ra, sa = eingaenge(ta, la)
    kp, rp, sp = eingaenge(tp, lp)
    for h in HORIZONTE:
        ia, ip = np.arange(ANFANG, len(ta) - h), np.arange(ANFANG, len(tp) - h)
        za, zp = ta[ia + h] - BEZUG, tp[ip + h] - BEZUG
        wk = np.linalg.lstsq(ka[ia], za, rcond=None)[0]
        wr = np.linalg.lstsq(ra[ia], za, rcond=None)[0]
        zielreihe = np.concatenate([tp[h:] - BEZUG, np.zeros(h)])  # Ziel zu Takt t steht bei t+h
        online = mitlernen(kp, np.concatenate([np.zeros(h), zielreihe[:-h]]), h)
        saetze = {
            "Prüf-Aufnahme": (zp, sp[ip], [("bleibt", tp[ip] - BEZUG), ("Mittel", np.full(len(ip), ta.mean() - BEZUG)),
                                           ("Körper, fest", kp[ip] @ wk), ("Körper, lernt mit", online[ip]),
                                           ("Mit Rhythmus, fest", rp[ip] @ wr)]),
            "Anpass-Aufnahme (Kontrolle)": (za, sa[ia], [("bleibt", ta[ia] - BEZUG), ("Körper, fest", ka[ia] @ wk),
                                                          ("Mit Rhythmus, fest", ra[ia] @ wr)]),
        }
        for titel, (ziel, seit, zeilen) in saetze.items():
            nah = seit < 60
            print(f"\n## H = {h}, {titel}\n\n{len(ziel)} Takte, davon {int(nah.sum())} bis 60 Takte nach einem Lastwechsel.\n\n"
                  "| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil von „bleibt“ |\n"
                  "| --- | ---: | ---: | ---: | ---: | ---: |")
            bezug = fehler(zeilen[0][1], ziel, np.ones(len(ziel), bool))[0]
            for name, v in zeilen:
                alle, wurzel = fehler(v, ziel, np.ones(len(ziel), bool))
                print(f"| {name} | {alle:.3f} | {wurzel:.3f} | {fehler(v, ziel, nah)[0]:.3f} | "
                      f"{fehler(v, ziel, ~nah)[0]:.3f} | {100 * alle / bezug:.1f} % |")
        print(f"\nGewichte „Körper, fest“ (Konstante, Mittel5, Steigung, Last, Last60, Last120): "
              + ", ".join(f"{g:.3f}" for g in wk))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

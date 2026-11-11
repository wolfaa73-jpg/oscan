"""Probe am Rechner: Wie schnell und wie sicher fällt ein Kälteeinbruch als Vorhersagefehler auf?
Explorativ, nicht Teil der Tests. Die Formen des Einbruchs in FORMEN sind geschätzt, nicht gemessen. Gerechnet
wird im künstlichen Körper (Saaten 13–24) und am echten Zufallslast-Lauf, auf den der Einbruch aufaddiert wird.
Überraschung: Fehler der Vorhersage h Takte voraus, über n Takte gemittelt, Betrag über dem q-Wert der ersten
Hälfte. Bericht: beispiele/geraetelaeufe-2026-11/probe-kaelte-2026-11-10.md.

Aufruf: kaelteprobe.py [aufnahme.csv]   (dauert einige Minuten)"""
import math
import sys
from pathlib import Path

import numpy as np

import kunstkoerper as kk
import vorhersage as vh

ECHT = sys.argv[1] if len(sys.argv) > 1 else str(
    Path(__file__).parent / "beispiele/geraetelaeufe-2026-11/roh/koerper-zufallslast-8h-2026-11-10.csv")
ANFANG = 120
# Name: (Zeitkonstante beim Abkühlen s, Dauer des Pustens s, Zeitkonstante der Erholung s)
FORMEN = {"schnell": (5.0, 10, 30.0), "träge": (15.0, 20, 60.0)}
TIEFEN = (1.0, 2.0, 3.0)
FENSTER = 300  # Takte nach Beginn, die nicht als Fehlalarm zählen


def einbruch(form, tiefe, laenge=FENSTER):
    tf, dauer, tr = FORMEN[form]
    a = tiefe / (1 - math.exp(-dauer / tf))
    d, x = np.zeros(laenge), 0.0
    for i in range(laenge):
        x += ((-a if i < dauer else 0.0) - x) / (tf if i < dauer else tr)
        d[i] = x
    return d


def restfehler(temp_dc, last, h, modell, mitte):
    """Istwert minus Vorhersage von vor h Takten, in °C. Gewichte nur aus der ersten Hälfte."""
    k, _, _ = vh.eingaenge(temp_dc, last)
    e = np.zeros(len(temp_dc))
    if modell == "bleibt":
        m5 = vh.gleitmittel(temp_dc, 5)
        e[h:] = temp_dc[h:] - m5[:-h]
    else:
        ia = np.arange(ANFANG, mitte - h)
        w = np.linalg.lstsq(k[ia], temp_dc[ia + h] - vh.BEZUG, rcond=None)[0]
        e[h:] = temp_dc[h:] - vh.BEZUG - k[:-h] @ w
    return e / 10.0


def alarmreihe(e, n, q, mitte):
    s = vh.gleitmittel(e, n)
    grenze = np.quantile(np.abs(s[ANFANG:mitte]), q)
    return np.abs(s) > grenze, grenze


def ereignisse(alarm, ab, bis, sperre=60):
    """Beginn jedes Alarms, dem sperre ruhige Takte vorausgingen."""
    aus, letzter = [], -10 ** 9
    for t in np.flatnonzero(alarm[ab:bis]) + ab:
        if t - letzter > sperre:
            aus.append(t)
        letzter = t
    return aus


def werte_aus(temp_roh, last, starts, form, tiefe, h, n, q, modell, stufe=True, zufall=None):
    """temp_roh in °C. Liefert Fehlalarme je Stunde (ohne Einbruch) und je Einbruch Verzug und Ruhezeit."""
    mitte = len(temp_roh) // 2
    runde = (lambda x: np.round(x)) if stufe else (lambda x: x + np.floor(zufall))
    ohne = (np.round(temp_roh) if stufe else temp_roh) * 10
    a0, grenze = alarmreihe(restfehler(ohne, last, h, modell, mitte), n, q, mitte)
    fehl = len(ereignisse(a0, mitte + ANFANG, len(ohne))) / ((len(ohne) - mitte - ANFANG) / 3600)
    if tiefe is None:
        return fehl, grenze
    d = np.zeros(len(temp_roh))
    form_d = einbruch(form, tiefe)
    for s in starts:
        d[s:s + FENSTER] += form_d if stufe else np.floor(form_d + zufall[s])
    mit = (np.round(temp_roh + d) if stufe else temp_roh + d) * 10
    e = restfehler(mit, last, h, modell, mitte)
    s_ = vh.gleitmittel(e, n)
    alarm = np.abs(s_) > grenze
    verzug, ruhe = [], []
    for s in starts:
        if a0[s - 30:s].any():      # stand schon unter Alarm: nicht werten
            continue
        t = np.flatnonzero(alarm[s:s + 120])
        verzug.append(int(t[0]) if len(t) else None)
        u = np.flatnonzero(alarm[s:s + FENSTER])
        ruhe.append(int(u[-1]) + 1 if len(u) else 0)
    return fehl, grenze, verzug, ruhe


def lauf(saat, echt=None):
    if echt is None:
        last = np.array(kk.lastreihe(28800, 240, 240, 20261110), float)
        roh = np.array(kk.temperaturen(last, stufe=0, saat=saat))
        return roh, last, True, None
    temp, last = vh.lies(echt)
    return temp / 10.0, last, False, np.random.default_rng(saat).random(len(temp))


def starts_fuer(n, saat):
    r = np.random.default_rng(1000 + saat)
    mitte = n // 2
    return [int(mitte + ANFANG + 600 + 1200 * i + r.integers(0, 600)) for i in range(11)]


if __name__ == "__main__":
    laeufe = {s: lauf(s) for s in range(13, 25)}
    def sammeln(saaten, form, tiefe, h, n, q, modell, echt=False):
        fehl, verz, ruhe, gr = [], [], [], []
        for s in saaten:
            roh, last, stufe, zuf = lauf(s, ECHT) if echt else laeufe[s]
            f, g, v, r = werte_aus(roh, last, starts_fuer(len(roh), s), form, tiefe, h, n, q, modell, stufe, zuf)
            fehl.append(f); verz += v; ruhe += r; gr.append(g)
        return np.mean(fehl), verz, ruhe, np.mean(gr)
    def zeile(name, fehl, verz, ruhe, gr):
        tr = [v for v in verz if v is not None]
        q = lambda grenze: 100 * sum(v <= grenze for v in tr) / len(verz)
        return (f"| {name} | {gr:.2f} | {fehl:.2f} | {q(2):.0f} % | {q(10):.0f} % | {q(30):.0f} % | {q(120):.0f} % | "
                f"{np.median(tr) if tr else float('nan'):.0f} | {np.median(ruhe):.0f} |")
    kopf = ("| Verfahren | Grenze °C | Fehlalarme/h | ≤ 2 Takte | ≤ 10 | ≤ 30 | ≤ 120 | Verzug Median | Ruhe nach (Median) |\n"
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for echt, titel, saaten in ((False, "Simulator, Saaten 13–24", range(13, 25)), (True, "Echter 8-h-Lauf, Einbruch aufaddiert, 12 Lagen", range(13, 25))):
        print(f"\n## {titel}\n\n" + kopf.replace("Verfahren", "Verfahren, Form, Tiefe"))
        for m, h, n, q in (("Körper", 10, 20, 0.999), ("Körper", 1, 1, 0.999), ("bleibt", 1, 1, 0.999), ("bleibt", 1, 10, 0.999)):
            for form in FORMEN:
                for tiefe in TIEFEN:
                    f, v, r, g = sammeln(saaten, form, tiefe, h, n, q, m, echt)
                    print(zeile(f"{m} h{h} n{n} q{q}, {form}, {tiefe:g} °C", f, v, r, g))

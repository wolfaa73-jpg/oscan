"""Körpervokabular: feste Wörter mit Nummer und Bedeutung, ein Gedächtnis über Wörter, ein weiterer Blick."""
import argparse
import statistics
import sys
from collections import Counter, namedtuple
from pathlib import Path

from koerper import lies_aufnahme, Grenzen

Wort = namedtuple("Wort", "nummer name oberbegriff signal bedeutung")

# Fester Kern, Fassung 1. Nummern ändern sich nie und werden nie neu vergeben,
# neue Wörter kommen nur hinten dazu. Der Oberbegriff übersetzt für Knoten, die
# nur OK, SCHWACH und AUSFALL kennen. 1 bis 4 sind die bisherigen Token.
VOKABULAR = (
    Wort(1, "OK", "OK", None, "nichts Auffälliges"),
    Wort(2, "SCHWACH", "SCHWACH", None, "Oberbegriff: eingeschränkt, aber arbeitsfähig"),
    Wort(3, "AUSFALL", "AUSFALL", None, "Oberbegriff: nicht arbeitsfähig"),
    Wort(4, "VORWARNUNG", None, None, "Meldung: ein Ausfall wird erwartet"),
    Wort(5, "TEMP_HOCH", "SCHWACH", "temperatur", "Chiptemperatur ab der Grenze für hoch"),
    Wort(6, "TEMP_KRITISCH", "AUSFALL", "temperatur", "Chiptemperatur ab der Grenze für kritisch"),
    Wort(7, "SPEICHER_KNAPP", "SCHWACH", "speicher", "freier Speicher bis zur Grenze für knapp"),
    Wort(8, "SPEICHER_VOLL", "AUSFALL", "speicher", "freier Speicher bis zur Grenze für voll"),
    Wort(9, "SCHLEIFE_ZAEH", "SCHWACH", "schleife", "fremde Wartezeit der Hauptschleife ab der Grenze für zäh"),
    Wort(10, "SCHLEIFE_STEHT", "AUSFALL", "schleife", "fremde Wartezeit der Hauptschleife ab der Grenze für steht"),
)
# Vorschläge für den wachsenden Rand: die Richtung der Temperatur. Sie haben noch
# keine Nummer und bekommen erst eine, wenn Alex sie bestätigt.
VORSCHLAEGE = (
    Wort(None, "TEMP_STEIGT", "OK", "temperatur", "unter hoch, aber wärmer als ein Fenster zuvor"),
    Wort(None, "TEMP_SINKT", "OK", "temperatur", "unter hoch und kühler als ein Fenster zuvor"),
    Wort(None, "TEMP_HOCH_STEIGT", "SCHWACH", "temperatur", "hoch und wärmer als ein Fenster zuvor"),
    Wort(None, "TEMP_HOCH_SINKT", "SCHWACH", "temperatur", "hoch und kühler als ein Fenster zuvor"),
)
NACH_NAME = {w.name: w for w in VOKABULAR + VORSCHLAEGE}
# Wörter, die einen Körpertakt beschreiben. Die Oberbegriffe dienen der groben Sicht.
KOERPERWOERTER = ("OK", "TEMP_HOCH", "TEMP_KRITISCH", "SPEICHER_KNAPP", "SPEICHER_VOLL",
                  "SCHLEIFE_ZAEH", "SCHLEIFE_STEHT")
GROBWOERTER = ("OK", "SCHWACH", "AUSFALL")
# Erbe je Signal wie ERBE in kern.py: Auf hoch folgt kritisch, drei feste Beobachtungen.
ERBFOLGEN = (("TEMP_HOCH", "TEMP_KRITISCH"), ("SPEICHER_KNAPP", "SPEICHER_VOLL"),
             ("SCHLEIFE_ZAEH", "SCHLEIFE_STEHT"))
GROBERBE = (("SCHWACH", "AUSFALL"),)


def grob(name):
    return NACH_NAME[name].oberbegriff


def kritisch(name):
    return grob(name) == "AUSFALL"


def koerperwort(temp_dc, heap, luecke_us, g):
    """Das schwerste Wort des Takts, bei gleicher Schwere Temperatur vor Speicher vor Schleife.
    Eine nicht lesbare Temperatur zählt wie in koerper.einstufen nicht."""
    t = temp_dc is not None
    for wort, trifft in (("TEMP_KRITISCH", t and temp_dc >= g.temp_ausfall),
                         ("SPEICHER_VOLL", heap <= g.heap_ausfall),
                         ("SCHLEIFE_STEHT", luecke_us >= g.luecke_ausfall),
                         ("TEMP_HOCH", t and temp_dc >= g.temp_schwach),
                         ("SPEICHER_KNAPP", heap <= g.heap_schwach),
                         ("SCHLEIFE_ZAEH", luecke_us >= g.luecke_schwach)):
        if trifft:
            return wort
    return "OK"


def mit_richtung(woerter, temps, fenster):
    """Vorschlag: OK und TEMP_HOCH nach der Richtung der Temperatur aufteilen.

    Verglichen wird der Median der letzten fünf Takte mit dem Median fünf Takte um fenster
    Takte zuvor. Der Median schluckt das Flackern zwischen zwei Gradstufen."""
    neu = []
    for i, wort in enumerate(woerter):
        jetzt = [t for t in temps[max(0, i - 4):i + 1] if t is not None]
        frueher = [t for t in temps[max(0, i - fenster - 4):max(0, i - fenster + 1)] if t is not None]
        if wort in ("OK", "TEMP_HOCH") and i >= fenster and jetzt and frueher:
            unterschied = statistics.median(jetzt) - statistics.median(frueher)
            if unterschied >= 10 or unterschied <= -10:  # eine ganze Gradstufe, in Zehntelgrad
                wort = ("TEMP_" if wort == "OK" else "TEMP_HOCH_") + ("STEIGT" if unterschied > 0 else "SINKT")
        neu.append(wort)
    return neu


class Wortgedaechtnis:
    """Kontextregel über beliebige Wörter: Die Belege eines Ausgangsworts altern nur, wenn es
    selbst wieder erlebt wird. Das Erbe liegt getrennt und verblasst nie."""

    def __init__(self, woerter, erbfolgen, erbe=3.0, halbwertszeit=6.0):
        self.woerter = tuple(woerter)
        self.faktor = 0.5 ** (1 / halbwertszeit)
        self.gewichte = {w: Counter() for w in self.woerter}
        self.erbe = {w: Counter() for w in self.woerter}
        for vorher, folge in erbfolgen:
            self.erbe[vorher][folge] = erbe

    def beobachte(self, vorher, jetzt):
        if vorher is None:
            return
        zeile = self.gewichte[vorher]
        for folge in zeile:
            zeile[folge] *= self.faktor
        zeile[jetzt] += 1

    def beleg(self, wort):
        return sum(self.gewichte[wort][f] + self.erbe[wort][f] for f in self.woerter)

    def folgen(self, wort):
        beleg = self.beleg(wort)
        if not beleg:
            return {wort: 1.0}  # ohne Erfahrung bleibt es, wie es ist
        return {f: (self.gewichte[wort][f] + self.erbe[wort][f]) / beleg
                for f in self.woerter if self.gewichte[wort][f] + self.erbe[wort][f]}

    def kritisch_binnen(self, wort, horizont):
        """Wie wahrscheinlich folgt binnen horizont Takten ein kritisches Wort? Die gelernte Tabelle
        wird dafür Schritt für Schritt weitergedacht, ein kritisches Wort beendet den Weg."""
        tabelle = {w: self.folgen(w) for w in self.woerter}
        verteilung, gesamt = {wort: 1.0}, 0.0
        for _ in range(horizont):
            weiter = Counter()
            for w, p in verteilung.items():
                for f, q in tabelle[w].items():
                    if kritisch(f):
                        gesamt += p * q
                    else:
                        weiter[f] += p * q
            verteilung = weiter
        return gesamt


def warnungen(woerter, modell, horizont, schwelle=0.6, mindestbeleg=3):
    """Warnung je Takt nach derselben Regel wie im Knoten, nur mit weiterem Blick."""
    ergebnis, vorher = [], None
    for wort in woerter:
        modell.beobachte(vorher, wort)
        ergebnis.append(not kritisch(wort) and modell.beleg(wort) >= mindestbeleg
                        and modell.kritisch_binnen(wort, horizont) >= schwelle)
        vorher = wort
    return ergebnis


def laeufe(merkmal, zusammen=10):
    """Zusammenhängende Läufe wahrer Werte als (Beginn, Ende). Läufe mit höchstens zusammen
    Takten Abstand gelten als einer, das fängt Flackern zwischen zwei Gradstufen ab."""
    ergebnis = []
    for t, wahr in enumerate(merkmal):
        if not wahr:
            continue
        if ergebnis and t - ergebnis[-1][1] <= zusammen:
            ergebnis[-1][1] = t
        else:
            ergebnis.append([t, t])
    return [tuple(lauf) for lauf in ergebnis]


def phasen(woerter, zusammen=10):
    """Kritische Phasen. Eine schon beim ersten Takt laufende Phase zählt nicht, ihr Beginn ist unbekannt."""
    return [p for p in laeufe([kritisch(w) for w in woerter], zusammen) if p[0] > 0]


def bewerte(woerter, warn, horizont, zusammen=10):
    """Hitzephasen, davon vorgewarnt, Alarme, Fehlalarme und Vorwarnzeit bei gegebenem Horizont.

    Ein Alarm ist ein zusammenhängender Warnlauf außerhalb einer Phase. Er ist richtig, wenn
    während des Laufs oder binnen horizont Takten danach eine Phase beginnt. Eine Phase gilt
    als vorgewarnt, wenn in den horizont Takten vor ihrem Beginn gewarnt wurde."""
    liste = phasen(woerter, zusammen)
    beginne = [b for b, _ in liste]
    innen = {t for b, e in liste for t in range(b, e + 1)}
    # Warnläufe verschmelzen nie über eine Phase hinweg, sonst ginge der Alarm
    # nach einer kurzen Phase im richtigen davor auf.
    alarme = []
    for t, w in enumerate(warn):
        if not w or t in innen:
            continue
        if alarme and t - alarme[-1][1] <= zusammen and not any(u in innen for u in range(alarme[-1][1], t)):
            alarme[-1][1] = t
        else:
            alarme.append([t, t])
    falsch = sum(1 for a, e in alarme if not any(a < u <= e + horizont for u in beginne))
    zeiten = []
    for beginn in beginne:
        frueh = [s for s in range(max(0, beginn - horizont), beginn) if warn[s]]
        if frueh:
            zeiten.append(beginn - frueh[0])
    return dict(phasen=len(liste), vorgewarnt=len(zeiten), alarme=len(alarme), fehlalarme=falsch,
                vorwarnzeit=statistics.median(zeiten) if zeiten else None)


def vergleiche_horizont(woerter, temps, horizont, fenster):
    """Fünf Verfahren auf denselben Körpertakten, alle bei demselben Horizont bewertet."""
    grobe = [grob(w) for w in woerter]
    richtung = mit_richtung(woerter, temps, fenster)
    verfahren = (
        ("Feste Regel", [grob(w) == "SCHWACH" for w in woerter]),
        ("Grob, ein Takt", warnungen(grobe, Wortgedaechtnis(GROBWOERTER, GROBERBE), 1)),
        (f"Grob, {horizont} Takte", warnungen(grobe, Wortgedaechtnis(GROBWOERTER, GROBERBE), horizont)),
        (f"Vokabular, {horizont} Takte",
         warnungen(woerter, Wortgedaechtnis(KOERPERWOERTER, ERBFOLGEN), horizont)),
        (f"+ Richtung, {horizont} Takte",
         warnungen(richtung, Wortgedaechtnis(KOERPERWOERTER + tuple(w.name for w in VORSCHLAEGE), ERBFOLGEN),
                   horizont)),
    )
    return [(name, bewerte(woerter, warn, horizont)) for name, warn in verfahren]


def woerter_der_aufnahme(pfad, grenzen=None):
    """Körperwörter und Temperaturen einer Aufnahme, wahlweise mit anderen Grenzen eingestuft."""
    meta, werte = lies_aufnahme(pfad)
    if any(b["takt"] != a["takt"] + 1 for a, b in zip(werte, werte[1:])):
        raise ValueError("Die Aufnahme hat Lücken in den Takten.")
    g = grenzen or Grenzen(**meta["grenzen"])
    woerter = [koerperwort(w["temp_dc"], w["heap"], w["luecke_us"], g) for w in werte]
    return meta, woerter, [w["temp_dc"] for w in werte]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="aktion", required=True)
    sub.add_parser("liste", help="das Vokabular mit Nummer, Oberbegriff und Bedeutung")
    a = sub.add_parser("auswertung", help="Verfahren an einer Körperaufnahme vergleichen")
    a.add_argument("datei", type=Path)
    a.add_argument("--horizont", type=int, nargs="+", default=[30, 60])
    a.add_argument("--fenster", type=int, default=20, help="Vergleichsfenster der Richtung in Takten")
    a.add_argument("--grenzen", type=int, nargs=6, metavar="N", help="wie bei koerper.py spur")
    arg = p.parse_args()
    try:
        if arg.aktion == "liste":
            for w in VOKABULAR + VORSCHLAEGE:
                print(f"{w.nummer or 'neu':>3}  {w.name:16} {w.oberbegriff or '-':8} {w.bedeutung}")
            return
        meta, woerter, temps = woerter_der_aufnahme(arg.datei, Grenzen(*arg.grenzen) if arg.grenzen else None)
        print(f"{len(woerter)} Takte, Wörter: "
              + ", ".join(f"{w} {n}" for w, n in Counter(woerter).most_common())
              + f". Hitzephasen: {len(phasen(woerter))}, Richtungsfenster {arg.fenster} Takte.")
        for h in arg.horizont:
            if h < 1:
                raise ValueError("Der Horizont muss mindestens einen Takt betragen.")
            print(f"\nHorizont {h} Takte: vorgewarnt / Phasen, Fehlalarme / Alarme, Vorwarnzeit (Median)")
            for name, b in vergleiche_horizont(woerter, temps, h, arg.fenster):
                sekunden = None if b["vorwarnzeit"] is None else b["vorwarnzeit"] * meta["intervall_ms"] / 1000
                zeit = "-" if sekunden is None else f"{sekunden:.0f} s"
                print(f"  {name:24} {b['vorgewarnt']:4} / {b['phasen']:<4} {b['fehlalarme']:4} / {b['alarme']:<4}  {zeit}")
    except (OSError, ValueError, KeyError) as fehler:
        p.exit(2, f"Vokabular: {fehler}\n")


if __name__ == "__main__":
    sys.exit(main())

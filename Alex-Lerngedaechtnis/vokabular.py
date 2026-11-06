"""Körpervokabular: feste Wörter mit Nummer und Bedeutung, ein Gedächtnis über Wörter, ein weiterer Blick."""
import argparse
import statistics
import sys
from collections import Counter, namedtuple
from pathlib import Path

from kern import blick_voraus
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
# Je Signal sein hohes und sein kritisches Wort, für die Zählung je Signal.
SIGNALE = tuple((NACH_NAME[hoch].signal, hoch, kritischer) for hoch, kritischer in ERBFOLGEN)


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


def stufen_je_signal(temp_dc, heap, luecke_us, g):
    """Jedes Signal für sich eingestuft, ohne den Vorrang aus koerperwort. So bleibt ein Leck
    sichtbar, auch wenn der Chip zugleich heiß ist. Eine nicht lesbare Temperatur zählt als OK."""
    t = temp_dc is not None

    def stufe(kritischer, hoch, ist_kritisch, ist_hoch):
        return kritischer if ist_kritisch else hoch if ist_hoch else "OK"
    return {"temperatur": stufe("TEMP_KRITISCH", "TEMP_HOCH", t and temp_dc >= g.temp_ausfall,
                                t and temp_dc >= g.temp_schwach),
            "speicher": stufe("SPEICHER_VOLL", "SPEICHER_KNAPP", heap <= g.heap_ausfall, heap <= g.heap_schwach),
            "schleife": stufe("SCHLEIFE_STEHT", "SCHLEIFE_ZAEH", luecke_us >= g.luecke_ausfall,
                              luecke_us >= g.luecke_schwach)}


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
    selbst wieder erlebt wird. Das Erbe liegt getrennt und verblasst nie. Mit startwert verblasst
    es mit jedem eigenen Ausgang aus seinem Wort, wie in kern.Startwertgedaechtnis."""

    def __init__(self, woerter, erbfolgen, erbe=3.0, halbwertszeit=6.0, startwert=False):
        self.woerter = tuple(woerter)
        self.faktor = 0.5 ** (1 / halbwertszeit)
        self.startwert = startwert
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
        if self.startwert and jetzt != vorher:
            geerbt = self.erbe[vorher]
            for folge in geerbt:
                geerbt[folge] *= self.faktor

    def beleg(self, wort):
        return sum(self.gewichte[wort][f] + self.erbe[wort][f] for f in self.woerter)

    def kritisch_binnen(self, wort, horizont):
        """Wie wahrscheinlich folgt binnen horizont Takten ein kritisches Wort? Dieselbe Rechnung
        wie im Knoten (kern.blick_voraus), nur über die Wörter dieses Gedächtnisses."""
        return blick_voraus(self.woerter, self.gewichte, self.erbe, wort, horizont, kritisch)


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


def binnen_vor(kritisch_je_takt, horizont):
    """Die nicht kritischen Takte, auf die binnen horizont Takten ein kritischer folgt."""
    ergebnis, naechster = set(), None
    for t in range(len(kritisch_je_takt) - 1, -1, -1):
        if kritisch_je_takt[t]:
            naechster = t
        elif naechster is not None and naechster - t <= horizont:
            ergebnis.add(t)
    return ergebnis


def bewerte(woerter, warn, horizont, zusammen=10):
    """Kritische Phasen, davon vorgewarnt, Alarme, Fehlalarme und Vorwarnzeit bei gegebenem Horizont.

    Ein Alarm ist ein zusammenhängender Warnlauf außerhalb einer Phase. Er ist richtig, wenn
    während des Laufs oder binnen horizont Takten danach eine Phase beginnt. Eine Phase gilt
    als vorgewarnt, wenn in den horizont Takten vor ihrem Beginn gewarnt wurde.

    Nach Läufen gezählt gewinnt, wer durchgehend warnt, denn ein langer Lauf reicht bis in die
    nächste Phase. Darum zählt auch jeder Takt: Der Warnanteil ist der Teil der nicht kritischen
    Takte mit Warnung, die Trefferquote der Teil der Warntakte, auf die binnen horizont Takten
    ein kritischer Takt folgt. Die Grundrate ist die Trefferquote von „immer warnen“."""
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
    folgt = binnen_vor([kritisch(w) for w in woerter], horizont)
    ruhig = [t for t, w in enumerate(woerter) if not kritisch(w)]
    gewarnt = [t for t in ruhig if warn[t]]
    return dict(phasen=len(liste), vorgewarnt=len(zeiten), alarme=len(alarme), fehlalarme=falsch,
                vorwarnzeit=statistics.median(zeiten) if zeiten else None,
                warnanteil=len(gewarnt) / len(ruhig) if ruhig else None,
                trefferquote=sum(t in folgt for t in gewarnt) / len(gewarnt) if gewarnt else None,
                grundrate=len(folgt) / len(ruhig) if ruhig else None)


def bewerte_je_signal(woerter, stufen, warn, horizont, zusammen=10, je_signal=None):
    """Je Signal seine eigenen kritischen Phasen und wie viele davon vorgewarnt sind, dazu Warnanteil
    und Trefferquote, wenn das Signal selbst auf seiner hohen Stufe steht, gleich welches Wort der Takt
    trägt. Treffer ist nur, worauf binnen horizont Takten seine eigene kritische Stufe folgt. So bekommt
    ein warmer Takt keinen Treffer für ein Leck, das zufällig danach kommt, und ein von Hitze verdecktes
    Vorzeichen zählt als nicht gewarnt. Bei OK zählt jedes kritische Wort. stufen hält je Takt die
    Stufen aus stufen_je_signal. je_signal gibt einem Verfahren mit eigenem Gedächtnis je Signal dessen
    Warnungen, sonst gilt warn für jedes Signal."""
    def anteile(takte, ziel, w):
        gewarnt = [t for t in takte if w[t]]
        return dict(warnanteil=len(gewarnt) / len(takte) if takte else None,
                    trefferquote=sum(t in ziel for t in gewarnt) / len(gewarnt) if gewarnt else None)

    ergebnis = {}
    for signal, hoch, kritischer in SIGNALE:
        w = warn if je_signal is None else je_signal[signal]
        stufe = [s[signal] for s in stufen]
        krit = [x == kritischer for x in stufe]
        liste = [p for p in laeufe(krit, zusammen) if p[0] > 0]
        vorgewarnt = sum(1 for b, _ in liste if any(w[s] for s in range(max(0, b - horizont), b)))
        ergebnis[signal] = dict(phasen=len(liste), vorgewarnt=vorgewarnt,
                                **anteile([t for t, x in enumerate(stufe) if x == hoch], binnen_vor(krit, horizont), w))
    ergebnis["ok"] = anteile([t for t, w in enumerate(woerter) if w == "OK"],
                             binnen_vor([kritisch(w) for w in woerter], horizont), warn)
    return ergebnis


def warnungen_je_signal(stufen, horizont, startwert=False):
    """Ein eigenes Gedächtnis je Signal über dessen eigene Stufen, jedes mit seinem Erbe hoch → kritisch.
    Kein Signal verdeckt so das Vorzeichen eines anderen. Jedes warnt vor seiner kritischen Stufe."""
    return {signal: warnungen([s[signal] for s in stufen],
                              Wortgedaechtnis(("OK", hoch, kritischer), ((hoch, kritischer),), startwert=startwert),
                              horizont)
            for signal, hoch, kritischer in SIGNALE}


def verfahren(woerter, temps, horizont, fenster, stufen=None):
    """Die Verfahren auf denselben Körpertakten, dazu „immer warnen“ als Maßstab, je als (Name,
    Warnung in jedem Takt, Warnungen je Signal oder None). Mit stufen kommt ein eigenes Gedächtnis
    je Signal dazu. Es warnt im Takt, wenn eines seiner Signale warnt und kein Wort kritisch ist.
    „Startwert“ heißt, das Erbe verblasst mit eigenen Ausgängen. Gelernt wird über alle übergebenen Takte."""
    grobe = [grob(w) for w in woerter]
    richtung = mit_richtung(woerter, temps, fenster)
    liste = [
        ("Feste Regel", [grob(w) == "SCHWACH" for w in woerter], None),
        ("Grob, ein Takt", warnungen(grobe, Wortgedaechtnis(GROBWOERTER, GROBERBE), 1), None),
        (f"Grob, {horizont} Takte", warnungen(grobe, Wortgedaechtnis(GROBWOERTER, GROBERBE), horizont), None),
        ("Grob, Startwert",
         warnungen(grobe, Wortgedaechtnis(GROBWOERTER, GROBERBE, startwert=True), horizont), None),
        (f"Vokabular, {horizont} Takte",
         warnungen(woerter, Wortgedaechtnis(KOERPERWOERTER, ERBFOLGEN), horizont), None),
        (f"+ Richtung, {horizont} Takte",
         warnungen(richtung, Wortgedaechtnis(KOERPERWOERTER + tuple(w.name for w in VORSCHLAEGE), ERBFOLGEN),
                   horizont), None),
    ]
    if stufen is not None:
        for name, startwert in ((f"Je Signal, {horizont} Takte", False), ("Je Signal, Startwert", True)):
            je = warnungen_je_signal(stufen, horizont, startwert)
            liste.append((name, [not kritisch(w) and any(je[s][t] for s in je) for t, w in enumerate(woerter)], je))
    liste.append(("Immer warnen", [not kritisch(w) for w in woerter], None))
    return liste


def woerter_der_aufnahme(pfad, grenzen=None):
    """Körperwörter, Temperaturen und Stufen je Signal einer Aufnahme, wahlweise mit anderen
    Grenzen eingestuft."""
    meta, werte = lies_aufnahme(pfad)
    if any(b["takt"] != a["takt"] + 1 for a, b in zip(werte, werte[1:])):
        raise ValueError("Die Aufnahme hat Lücken in den Takten.")
    g = grenzen or Grenzen(**meta["grenzen"])
    woerter = [koerperwort(w["temp_dc"], w["heap"], w["luecke_us"], g) for w in werte]
    stufen = [stufen_je_signal(w["temp_dc"], w["heap"], w["luecke_us"], g) for w in werte]
    return meta, woerter, [w["temp_dc"] for w in werte], stufen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="aktion", required=True)
    sub.add_parser("liste", help="das Vokabular mit Nummer, Oberbegriff und Bedeutung")
    a = sub.add_parser("auswertung", help="Verfahren an einer Körperaufnahme vergleichen")
    a.add_argument("datei", type=Path)
    a.add_argument("--horizont", type=int, nargs="+", default=[30, 60])
    a.add_argument("--fenster", type=int, default=20, help="Vergleichsfenster der Richtung in Takten")
    a.add_argument("--grenzen", type=int, nargs=6, metavar="N", help="wie bei koerper.py spur")
    a.add_argument("--nach", type=int, default=0, metavar="N",
                   help="erst nach den ersten N Takten zählen, gelernt wird über die ganze Aufnahme")
    a.add_argument("--bis", type=int, metavar="N", help="nur die ersten N Takte, wie eine kürzere Aufnahme")
    arg = p.parse_args()
    try:
        if arg.aktion == "liste":
            for w in VOKABULAR + VORSCHLAEGE:
                print(f"{w.nummer or 'neu':>3}  {w.name:16} {w.oberbegriff or '-':8} {w.bedeutung}")
            return
        meta, woerter, temps, stufen = woerter_der_aufnahme(arg.datei,
                                                            Grenzen(*arg.grenzen) if arg.grenzen else None)
        if arg.bis is not None:
            if arg.bis < 1:
                raise ValueError("--bis braucht mindestens einen Takt.")
            woerter, temps, stufen = woerter[:arg.bis], temps[:arg.bis], stufen[:arg.bis]
        print(f"{len(woerter)} Takte, Wörter: "
              + ", ".join(f"{w} {n}" for w, n in Counter(woerter).most_common())
              + f". Kritische Phasen: {len(phasen(woerter))}, Richtungsfenster {arg.fenster} Takte.")
        if not 0 <= arg.nach < len(woerter):
            raise ValueError("--nach muss vor dem Ende der Aufnahme liegen.")
        if arg.nach:
            print(f"Gezählt ab Takt {arg.nach + 1}: {len(phasen(woerter[arg.nach:]))} Phasen. "
                  "Gelernt wird über die ganze Aufnahme.")
        prozent = lambda wert: "-" if wert is None else f"{wert * 100:.0f} %"
        for h in arg.horizont:
            if h < 1:
                raise ValueError("Der Horizont muss mindestens einen Takt betragen.")
            liste = [(name, warn[arg.nach:], None if je is None else {s: w[arg.nach:] for s, w in je.items()})
                     for name, warn, je in verfahren(woerter, temps, h, arg.fenster, stufen)]
            gezaehlt, je_takt = woerter[arg.nach:], stufen[arg.nach:]
            print(f"\nHorizont {h} Takte: vorgewarnt / Phasen, Fehlalarme / Alarme, Vorwarnzeit (Median), "
                  "Warnanteil, Trefferquote")
            for name, warn, _ in liste:
                b = bewerte(gezaehlt, warn, h)
                sekunden = None if b["vorwarnzeit"] is None else b["vorwarnzeit"] * meta["intervall_ms"] / 1000
                zeit = "-" if sekunden is None else f"{sekunden:.0f} s"
                print(f"  {name:24} {b['vorgewarnt']:4} / {b['phasen']:<4} {b['fehlalarme']:4} / {b['alarme']:<4}"
                      f" {zeit:>5} {prozent(b['warnanteil']):>6} {prozent(b['trefferquote']):>6}")
            print(f"\nJe Signal, {h} Takte: vorgewarnt / Phasen, Warnanteil und Trefferquote, wenn das Signal "
                  "selbst hoch steht, zuletzt bei OK")
            print(f"  {'':24} " + " ".join(f"{signal.capitalize():>22}" for signal, _, _ in SIGNALE) + f" {'OK':>12}")
            for name, warn, je in liste:
                s = bewerte_je_signal(gezaehlt, je_takt, warn, h, je_signal=je)
                bloecke = [f"{s[n]['vorgewarnt']:4} / {s[n]['phasen']:<3}{prozent(s[n]['warnanteil']):>6}"
                           f"{prozent(s[n]['trefferquote']):>6}" for n, _, _ in SIGNALE]
                print(f"  {name:24} " + " ".join(bloecke)
                      + f" {prozent(s['ok']['warnanteil']):>6}{prozent(s['ok']['trefferquote']):>6}")
    except (OSError, ValueError, KeyError) as fehler:
        p.exit(2, f"Vokabular: {fehler}\n")


if __name__ == "__main__":
    sys.exit(main())

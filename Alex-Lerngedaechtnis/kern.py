"""Zeit, Beobachtung und Entscheidung eines einzelnen Knotens. Keine Gerätezugriffe."""
import math
from collections import Counter
from dataclasses import dataclass
from typing import Optional

ZUSTAENDE = ("OK", "SCHWACH", "AUSFALL")
MAX_TAKT = 2**32 - 1
# Höchster Blick in Takten, wie maxBlick in Knoten.h. Bei einem Takt je Sekunde sind das
# zehn Minuten, der Chip wärmt sich in etwa einer Minute auf und kühlt in zwei ab.
MAX_BLICK = 600


def ist_ausfall(zustand):
    return zustand == "AUSFALL"


def blick_voraus(woerter, gewichte, erbe, start, blick, kritisch):
    """Wie wahrscheinlich wird binnen blick Takten ein kritischer Zustand erreicht?

    Die gelernte Tabelle wird Schritt für Schritt weitergedacht, ein kritischer Zustand beendet
    den Weg, ein Zustand ohne Beleg bleibt, wie er ist. Summiert wird in der festen Reihenfolge
    von woerter, so rechnet Knoten.h bitgleich nach. Bei blick 1 ist das genau der Anteil der
    kritischen Folgen in der Zeile von start."""
    zeilen = {}
    for w in woerter:
        beleg = sum(gewichte[w][f] + erbe[w][f] for f in woerter)
        zeilen[w] = ([(f, (gewichte[w][f] + erbe[w][f]) / beleg) for f in woerter if gewichte[w][f] + erbe[w][f]]
                     if beleg else [(w, 1.0)])
    verteilung, gesamt = {start: 1.0}, 0.0
    for _ in range(blick):
        weiter = {}
        for w in woerter:
            if w not in verteilung:
                continue
            for f, q in zeilen[w]:
                if kritisch(f):
                    gesamt += verteilung[w] * q
                else:
                    weiter[f] = weiter.get(f, 0.0) + verteilung[w] * q
        verteilung = weiter
    return gesamt


class Gedaechtnis:
    def __init__(self, halbwertszeit: Optional[float] = 24.0):
        if halbwertszeit is not None and (not math.isfinite(halbwertszeit) or halbwertszeit <= 0):
            raise ValueError("Die Halbwertszeit muss positiv und endlich sein.")
        self.halbwertszeit = halbwertszeit
        self.faktor = 1.0 if halbwertszeit is None else 0.5 ** (1 / halbwertszeit)
        self.gewichte = {z: Counter() for z in ZUSTAENDE}
        # Festes Vorwissen, getrennt von eigener Erfahrung. Nur Erbgedaechtnis füllt es.
        self.erbe = {z: Counter() for z in ZUSTAENDE}

    def beobachte(self, vorher, jetzt, schritte=1):
        faktor = self.faktor ** schritte
        for zeile in self.gewichte.values():
            for folge in zeile:
                zeile[folge] *= faktor
        if vorher is not None:
            self.gewichte[vorher][jetzt] += 1

    def schaetze(self, zustand, blick=1):
        """Anteil der Wege, die binnen blick Takten AUSFALL erreichen, und Beleg der eigenen Zeile."""
        zeile, erbe = self.gewichte[zustand], self.erbe[zustand]
        beleg = sum(zeile[z] + erbe[z] for z in ZUSTAENDE)
        anteil = blick_voraus(ZUSTAENDE, self.gewichte, self.erbe, zustand, blick, ist_ausfall) if beleg else 0.0
        return anteil, beleg


class Kontextgedaechtnis(Gedaechtnis):
    """Halbwertszeit in beobachteten Folgen desselben Ausgangszustands."""

    def __init__(self, halbwertszeit=6.0):
        super().__init__(halbwertszeit)

    def beobachte(self, vorher, jetzt, schritte=1):
        if vorher is None:
            return
        zeile = self.gewichte[vorher]
        for folge in zeile:
            zeile[folge] *= self.faktor
        zeile[jetzt] += 1


# Vorwissen von außen als feste Beobachtungen je Übergang. Drei entsprechen dem
# Mindestbeleg einer Warnung. Das Erbe trägt also schon beim ersten schwachen Signal.
ERBE = {("SCHWACH", "AUSFALL"): 3.0}


class Erbgedaechtnis(Kontextgedaechtnis):
    """Festes Erbe und Kontextregel. Erbe und eigene Erfahrung liegen getrennt, das Erbe verblasst nie."""

    def __init__(self, erbe=None):
        super().__init__()
        for (vorher, folge), wert in (ERBE if erbe is None else erbe).items():
            if vorher not in ZUSTAENDE or folge not in ZUSTAENDE or not math.isfinite(wert) or wert < 0:
                raise ValueError("Das Erbe braucht bekannte Zustände und endliche Werte ab null.")
            self.erbe[vorher][folge] = wert


class Startwertgedaechtnis(Erbgedaechtnis):
    """Das Erbe als Startwert. Es verblasst mit jedem eigenen Ausgang aus seinem Zustand, mit der
    Halbwertszeit der Kontextregel, nur in Ausgängen gezählt. Bleiben zählt nicht, es sagt nichts
    darüber, wohin der Zustand führt. So trägt das Erbe die erste Warnung und weicht, wenn der
    Zustand anders endet."""

    def beobachte(self, vorher, jetzt, schritte=1):
        super().beobachte(vorher, jetzt, schritte)
        if vorher is not None and jetzt != vorher:
            zeile = self.erbe[vorher]
            for folge in zeile:
                zeile[folge] *= self.faktor


# Name je Lernregel, gilt für Sicherungsformat, Firmwarevariante und Prüfer.
# Im Gerätestand stehen sie als Regelbyte 1 bis 4, der Startwert im Format AG02 mit seinem Erbe.
REGELN = {"zeit": Gedaechtnis, "kontext": Kontextgedaechtnis, "erbe": Erbgedaechtnis,
          "startwert": Startwertgedaechtnis}


@dataclass(frozen=True)
class Schritt:
    takt: int
    zustand: str
    statusmeldung: bool
    sofort: bool
    vorwarnung: bool
    anteil: float
    beleg: float


class Knoten:
    """blick: wie viele Takte die Vorwarnung vorausdenkt, 1 entscheidet über den nächsten Takt."""

    def __init__(self, gedaechtnis=None, *, alle_senden=False, feste_warnregel=False, blick=1):
        if type(blick) is not int or not 1 <= blick <= MAX_BLICK:
            raise ValueError(f"Der Blick muss 1 bis {MAX_BLICK} Takte betragen.")
        self.gedaechtnis = gedaechtnis
        self.alle_senden = alle_senden
        self.feste_warnregel = feste_warnregel
        self.blick = blick
        self.takt = 0
        self.zustand = None

    def schritt(self, takt, zustand):
        if type(takt) is not int or not self.takt < takt <= MAX_TAKT:
            raise ValueError("Takte müssen positiv, aufsteigend und kleiner als 2^32 sein.")
        if zustand not in ZUSTAENDE:
            raise ValueError(f"Unbekannter Zustand {zustand!r}.")
        abstand = takt - self.takt
        # Über eine Lücke gibt es keinen belegten Übergang. Der erste Zustand
        # danach wird erneut gemeldet, selbst wenn er dem letzten gleicht.
        vorher = self.zustand if abstand == 1 else None
        statusmeldung = self.alle_senden or zustand != vorher
        sofort = zustand == "AUSFALL" and zustand != vorher
        anteil = beleg = 0.0
        warnung = self.feste_warnregel and zustand == "SCHWACH"
        if self.gedaechtnis is not None:
            self.gedaechtnis.beobachte(vorher, zustand, abstand)
            anteil, beleg = self.gedaechtnis.schaetze(zustand, self.blick)
            warnung = zustand != "AUSFALL" and beleg >= 3 and anteil >= 0.6
        self.takt, self.zustand = takt, zustand
        return Schritt(takt, zustand, statusmeldung, sofort, warnung, anteil, beleg)

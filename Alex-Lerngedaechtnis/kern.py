"""Zeit, Beobachtung und Entscheidung eines einzelnen Knotens. Keine Gerätezugriffe."""
import math
from collections import Counter
from dataclasses import dataclass
from typing import Optional

ZUSTAENDE = ("OK", "SCHWACH", "AUSFALL")
MAX_TAKT = 2**32 - 1


class Gedaechtnis:
    def __init__(self, halbwertszeit: Optional[float] = 24.0):
        if halbwertszeit is not None and (not math.isfinite(halbwertszeit) or halbwertszeit <= 0):
            raise ValueError("Die Halbwertszeit muss positiv und endlich sein.")
        self.halbwertszeit = halbwertszeit
        self.faktor = 1.0 if halbwertszeit is None else 0.5 ** (1 / halbwertszeit)
        self.gewichte = {z: Counter() for z in ZUSTAENDE}

    def beobachte(self, vorher, jetzt, schritte=1):
        faktor = self.faktor ** schritte
        for zeile in self.gewichte.values():
            for folge in zeile:
                zeile[folge] *= faktor
        if vorher is not None:
            self.gewichte[vorher][jetzt] += 1

    def schaetze(self, zustand):
        zeile = self.gewichte[zustand]
        beleg = sum(zeile[z] for z in ZUSTAENDE)
        anteil = zeile["AUSFALL"] / beleg if beleg else 0.0
        return anteil, beleg


class Kontextgedaechtnis(Gedaechtnis):
    """Halbwertszeit in beobachteten Folgen desselben Ausgangszustands."""

    def __init__(self):
        super().__init__(6.0)

    def beobachte(self, vorher, jetzt, schritte=1):
        if vorher is None:
            return
        zeile = self.gewichte[vorher]
        for folge in zeile:
            zeile[folge] *= self.faktor
        zeile[jetzt] += 1


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
    def __init__(self, gedaechtnis=None, *, alle_senden=False, feste_warnregel=False):
        self.gedaechtnis = gedaechtnis
        self.alle_senden = alle_senden
        self.feste_warnregel = feste_warnregel
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
            anteil, beleg = self.gedaechtnis.schaetze(zustand)
            warnung = zustand != "AUSFALL" and beleg >= 3 and anteil >= 0.6
        self.takt, self.zustand = takt, zustand
        return Schritt(takt, zustand, statusmeldung, sofort, warnung, anteil, beleg)

"""Zwei simulierte Knoten. Welche Zustände sieht die Gegenstelle bei Paketverlust?"""
from dataclasses import dataclass
from typing import Optional

from kern import ZUSTAENDE
from versuch import RAHMEN, TOKEN

ZUSTAND_JE_TOKEN = {TOKEN[z]: z for z in ZUSTAENDE}


class Empfaenger:
    def __init__(self):
        self.takt = 0
        self.zustand = None

    def empfange(self, paket, jetzt):
        if len(paket) != RAHMEN.size:
            return False
        takt, token = RAHMEN.unpack(paket)
        if not self.takt < takt <= jetzt or token not in ZUSTAND_JE_TOKEN:
            return False
        self.takt, self.zustand = takt, ZUSTAND_JE_TOKEN[token]
        return True

    def sicht(self, jetzt, gueltig):
        if gueltig is not None and jetzt - self.takt >= gueltig:
            return None
        return self.zustand


@dataclass
class Kanalbilanz:
    gesendet: int = 0
    angekommen: int = 0
    falsch: int = 0
    unbekannt: int = 0
    erste_ausfallsicht: Optional[int] = None


def kanal(spur, verluste, intervall, gueltig):
    """Ein gemeinsamer logischer Takt und eine Sitzung. intervall=None sendet nur Änderungen."""
    bilanz = Kanalbilanz()
    empfaenger = Empfaenger()
    vorher = None
    letzter_versand = 0
    for takt, zustand in enumerate(spur, 1):
        faellig = intervall is not None and takt - letzter_versand >= intervall
        if zustand != vorher or faellig:
            paket = RAHMEN.pack(takt, TOKEN[zustand])
            bilanz.gesendet += 1
            letzter_versand = takt
            if takt not in verluste:
                empfaenger.empfange(paket, takt)
                bilanz.angekommen += 1
        aktuell = empfaenger.sicht(takt, gueltig)
        if aktuell is None:
            bilanz.unbekannt += 1
        elif aktuell != zustand:
            bilanz.falsch += 1
        elif zustand == "AUSFALL" and bilanz.erste_ausfallsicht is None:
            bilanz.erste_ausfallsicht = takt
        vorher = zustand
    return bilanz


def main():
    spur = ["OK"] * 5 + ["AUSFALL"] * 20 + ["OK"] * 11
    for name, verluste in (("Genau die Ausfallmeldung fehlt", {6}),
                            ("Verbindung fehlt von Takt 6 bis 25", set(range(6, 26)))):
        print(f"\n{name}. Wahrer Ausfallbeginn: Takt 6.")
        print("Verfahren               Bytes gesendet  Pakete da  Takte falsch  Unbekannt  Ausfall zuerst gesehen")
        for regel, intervall, ttl in (("Jeden Takt", 1, 10), ("Nur Wechsel", None, None),
                                      ("Wechsel + Herzschlag", 5, 10)):
            b = kanal(spur, verluste, intervall, ttl)
            erste = str(b.erste_ausfallsicht) if b.erste_ausfallsicht else "nie"
            print(f"{regel:23}{b.gesendet * RAHMEN.size:15}{b.angekommen:11}"
                  f"{b.falsch:14}{b.unbekannt:11}  {erste}")


if __name__ == "__main__":
    main()

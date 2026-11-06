"""Separater Verweildauer-/Richtungsprototyp; kein Firmware- oder Kernersatz.

Eine Dauer d umfasst d beobachtete Takte desselben Worts; der Ausgang folgt
einen Takt nach dessen letztem Auftreten. Nur vollständige Läufe lernen Dauer.
Der erste linkszensierte Lauf liefert ausschließlich eine Ausgangsrichtung.
"""
import math
from collections import Counter

from vokabular import kritisch


class Verweildauergedaechtnis:
    """Semi-Markov-Modell mit der Warnschnittstelle von Wortgedaechtnis.

    Dauer und Ziel werden getrennt geschätzt, bedingt auf das Ausgangswort.
    Ihre bedingte Unabhängigkeit ist eine Modellannahme, keine Beobachtung.
    Fehlende Dauerabdeckung erzeugt keinen Beleg für Entwarnung: beleg() wird
    dann null. kritisch_binnen() gibt für die bestehende Schnittstelle 0 zurück.
    Ein hypothetisches Erbe bringt je Kante Gewicht erbe und Dauer 1 mit.
    """

    def __init__(self, woerter, erbfolgen, erbe=3.0, halbwertszeit=6.0, startwert=True):
        self.woerter = tuple(woerter)
        if not self.woerter or len(set(self.woerter)) != len(self.woerter):
            raise ValueError("Eindeutiges nichtleeres Wörterbuch erforderlich.")
        for wert, positiv in ((erbe, False), (halbwertszeit, True)):
            if isinstance(wert, bool) or not isinstance(wert, (int, float)) or not math.isfinite(wert) \
                    or (wert <= 0 if positiv else wert < 0):
                raise ValueError("Gewicht und Halbwertszeit müssen gültig und endlich sein.")
        if type(startwert) is not bool:
            raise ValueError("startwert muss bool sein.")
        for w in self.woerter:
            kritisch(w)  # Nur bestehende Wörter; kein heimliches neues Vokabular.
        self.faktor = 0.5 ** (1 / halbwertszeit)
        self.startwert = startwert
        self.richtung = {w: Counter() for w in self.woerter}
        self.dauer = {w: Counter() for w in self.woerter}
        self.erbe = {w: Counter() for w in self.woerter}
        self.erbdauer = {w: Counter() for w in self.woerter}
        for vorher, folge in erbfolgen:
            if vorher not in self.richtung or folge not in self.richtung or vorher == folge:
                raise ValueError("Erbfolge muss einen gültigen Zustandsausgang beschreiben.")
            self.erbe[vorher][folge] += erbe
            self.erbdauer[vorher][1] += erbe
        self.aktuell, self.alter, self.links_offen = None, 0, True
        self._revision = 0
        self._cache = None

    @staticmethod
    def _altere(zaehler, faktor):
        for key in zaehler:
            zaehler[key] *= faktor

    def beobachte(self, vorher, jetzt):
        if jetzt not in self.richtung or vorher is not None and vorher not in self.richtung:
            raise ValueError("Unbekanntes Wort.")
        if self.aktuell is None:
            if vorher is not None:
                raise ValueError("Die erste Beobachtung braucht vorher=None.")
            self.aktuell, self.alter = jetzt, 1
            return
        if vorher != self.aktuell:
            raise ValueError("Beobachtungsfolge unterbrochen; neues Modell erforderlich.")
        if jetzt == vorher:
            self.alter += 1
            return
        self._altere(self.richtung[vorher], self.faktor)
        self.richtung[vorher][jetzt] += 1
        self._altere(self.dauer[vorher], self.faktor)
        if not self.links_offen:
            self.dauer[vorher][self.alter] += 1
        if self.startwert:
            self._altere(self.erbe[vorher], self.faktor)
            self._altere(self.erbdauer[vorher], self.faktor)
        self.aktuell, self.alter, self.links_offen = jetzt, 1, False
        self._revision += 1
        self._cache = None

    def _alter_fuer(self, wort):
        if wort not in self.richtung:
            raise ValueError("Unbekanntes Wort.")
        return self.alter if wort == self.aktuell else 1

    def beleg(self, wort):
        alter = self._alter_fuer(wort)
        if wort == self.aktuell and self.links_offen:
            return 0.0
        richtung = sum(self.richtung[wort].values()) + sum(self.erbe[wort].values())
        dauer = sum(v for d, v in self.dauer[wort].items() if d >= alter)
        dauer += sum(v for d, v in self.erbdauer[wort].items() if d >= alter)
        return min(richtung, dauer)

    def _tabellen(self, horizont):
        if self._cache is not None and self._cache[0:2] == (self._revision, horizont):
            return self._cache[2:]
        dauer, richtung = {}, {}
        for w in self.woerter:
            d = self.dauer[w] + self.erbdauer[w]
            r = self.richtung[w] + self.erbe[w]
            nd, nr = sum(d.values()), sum(r.values())
            dauer[w] = {k: v / nd for k, v in d.items()} if nd else {}
            richtung[w] = {k: v / nr for k, v in r.items()} if nr else {}
        # F[w][h]: Treffer binnen h Takten unmittelbar nach Eintritt in w.
        # Dauer >=1 garantiert, dass nur schon berechnete kleinere h gelesen werden.
        f = {w: [0.0] * (horizont + 1) for w in self.woerter}
        for h in range(1, horizont + 1):
            for w in self.woerter:
                f[w][h] = sum(pd * sum(pr * (1.0 if kritisch(z) else f[z][h - d])
                                                    for z, pr in richtung[w].items())
                              for d, pd in dauer[w].items() if d <= h)
        self._cache = (self._revision, horizont, dauer, richtung, f)
        return dauer, richtung, f

    def kritisch_binnen(self, wort, horizont):
        if type(horizont) is not int or not 1 <= horizont <= 600:
            raise ValueError("Horizont muss ganzzahlig zwischen 1 und 600 liegen.")
        alter = self._alter_fuer(wort)
        if wort == self.aktuell and self.links_offen:
            return 0.0
        dauer, richtung, f = self._tabellen(horizont)
        rest = {d - alter + 1: p for d, p in dauer[wort].items() if d >= alter}
        masse = sum(rest.values())
        if not masse:
            return 0.0
        p = sum(pd / masse * sum(pr * (1.0 if kritisch(z) else f[z][horizont - d])
                                for z, pr in richtung[wort].items())
                for d, pd in rest.items() if d <= horizont)
        return max(0.0, min(1.0, p))

    def zustandsumfang(self):
        """Logische belegte Zellen, keine Behauptung über Python-/Geräte-RAM."""
        return sum(len(c) for t in (self.richtung, self.dauer, self.erbe, self.erbdauer)
                   for c in t.values())

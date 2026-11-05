"""OSCan-Laufzeitversuch: Gedächtnis schlägt vor, ein fester Ablauf disponiert Arbeit.

Die Ressourcen sind ein Primär- und ein Reserve-Arbeiter im eigenen Prozessraum.
Ein Takt ist logisch, keine zugesicherte Echtzeitfrist des Host-Betriebssystems.
"""
import hashlib
import multiprocessing as mp
from dataclasses import dataclass
from typing import Optional

from kern import Erbgedaechtnis, Gedaechtnis, Kontextgedaechtnis, Knoten, MAX_TAKT, ZUSTAENDE

VERFAHREN = ("reflex", "fest", "ohne_verblassen", "zeit", "kontext", "erbe")


def lernknoten(verfahren):
    if verfahren not in VERFAHREN:
        raise ValueError("Unbekanntes Verfahren.")
    fabriken = {"ohne_verblassen": lambda: Gedaechtnis(None), "zeit": Gedaechtnis,
                "kontext": Kontextgedaechtnis, "erbe": Erbgedaechtnis}
    return Knoten(fabriken[verfahren]() if verfahren in fabriken else None,
                  feste_warnregel=verfahren == "fest")


@dataclass(frozen=True)
class Plan:
    takt: int
    zustand: Optional[str]
    ziel: str
    reserve_fuer: Optional[int]
    vorwarnung: bool
    reflex: bool
    grund: str


class Systemkern:
    """Eine Beobachtung, höchstens ein Auftrag und eine Reservierung je Takt.

    Die Lernregel darf weder den aktuellen Ausfallreflex noch die Gültigkeit
    einer Reservierung verändern. None bedeutet fehlendes aktuelles Wissen.
    Dies ist eine Codegrenze, noch keine hardwaregeschützte Vertrauensgrenze.
    """

    def __init__(self, verfahren="erbe"):
        self.knoten = lernknoten(verfahren)
        self.takt = 0
        self.reserve_fuer = None

    def schritt(self, takt, zustand):
        if type(takt) is not int or not self.takt < takt <= MAX_TAKT:
            raise ValueError("Takte müssen positiv, aufsteigend und kleiner als 2^32 sein.")
        if zustand is not None and zustand not in ZUSTAENDE:
            raise ValueError("Unbekannter Zustand.")
        bereit = self.reserve_fuer == takt
        warnung = reflex = False
        if zustand is None:
            ziel, grund = "WARTEN", "Kein aktueller Zustand; Reservierung verwerfen"
        else:
            s = self.knoten.schritt(takt, zustand)
            warnung = s.vorwarnung
            reflex = zustand == "AUSFALL"
            if reflex:
                ziel = "RESERVE" if bereit else "WARTEN"
                grund = "Primär gesperrt; Reserve bereit" if bereit else "Primär gesperrt; Reserve fehlt"
            else:
                ziel, grund = "PRIMAER", "Primär aktuell verfügbar"
        # Ein kritischer Ist-Zustand reserviert unabhängig von der Lernregel.
        reserve = takt + 1 if (warnung or reflex) and takt < MAX_TAKT else None
        self.takt, self.reserve_fuer = takt, reserve
        return Plan(takt, zustand, ziel, reserve, warnung, reflex, grund)


def _arbeiter(kanal):
    try:
        while True:
            nachricht = kanal.recv()
            if nachricht is None:
                return
            takt, daten = nachricht
            kanal.send((takt, hashlib.sha256(daten).hexdigest()))
    except (EOFError, BrokenPipeError):
        pass
    finally:
        kanal.close()


class Arbeitsprozesse:
    """Zwei feste lokale Arbeiter, keine Shell und keine fremden Prozesse.

    Die Reservierung ist hier eine Zulassung zur Nutzung eines bereits gestarteten
    Prozesses. Kosten für echtes Aufwecken oder Energie werden nicht gemessen.
    """

    def __enter__(self):
        self.arbeiter = {}
        kontext = mp.get_context("spawn")
        try:
            for name in ("PRIMAER", "RESERVE"):
                eltern, kind = kontext.Pipe()
                prozess = kontext.Process(target=_arbeiter, args=(kind,), daemon=True)
                try:
                    prozess.start()
                except BaseException:
                    eltern.close()
                    kind.close()
                    raise
                kind.close()
                self.arbeiter[name] = (eltern, prozess)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def ausfuehren(self, plan):
        if plan.ziel == "WARTEN":
            return None
        if plan.ziel not in self.arbeiter:
            raise ValueError("Unzulässiges Arbeitsziel.")
        daten = f"OSCan-Auftrag:{plan.takt}".encode("ascii")
        kanal, _ = self.arbeiter[plan.ziel]
        kanal.send((plan.takt, daten))
        if not kanal.poll(5):
            raise TimeoutError("Arbeiter antwortet nicht innerhalb der Prüffrist.")
        antwort = kanal.recv()
        if antwort != (plan.takt, hashlib.sha256(daten).hexdigest()):
            raise ValueError("Falscher Auftrag oder falsches Arbeitsergebnis.")
        return antwort[1]

    def __exit__(self, *_):
        for kanal, prozess in self.arbeiter.values():
            try:
                kanal.send(None)
            except (OSError, EOFError):
                pass
            kanal.close()
            prozess.join(timeout=2)
            if prozess.is_alive():
                prozess.terminate()
                prozess.join(timeout=2)
            if prozess.is_alive():
                prozess.kill()
                prozess.join()
            prozess.close()

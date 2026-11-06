"""Begrenztes Auftragsregister für einen einzelnen lokalen Ereignisablauf.

Ein Ergebnisverlust führt zu UNGEKLAERT. Es gibt keine automatische zweite
Ausführung. Das Register ist flüchtig, keine dauerhafte Exactly-once-Garantie.
"""
import hashlib
import uuid
from dataclasses import dataclass
from typing import Optional

from kern import MAX_TAKT
from systemkern import Plan


@dataclass(frozen=True)
class Auftrag:
    sitzung: bytes
    plan: Plan


@dataclass(frozen=True)
class Quittung:
    sitzung: bytes
    takt: int
    status: str
    ergebnis: Optional[str] = None
    grund: str = ""


class Auftragsregister:
    def __init__(self, sitzung=None, kapazitaet=1024):
        self.sitzung = uuid.uuid4().bytes if sitzung is None else sitzung
        if type(self.sitzung) is not bytes or len(self.sitzung) != 16 or not any(self.sitzung):
            raise ValueError("Frische 128-Bit-Auftragssitzung erforderlich.")
        if type(kapazitaet) is not int or kapazitaet < 1:
            raise ValueError("Positive Registerkapazität erforderlich.")
        self.kapazitaet = kapazitaet
        self.eintraege = {}

    def bekannt(self, auftrag):
        if not isinstance(auftrag, Auftrag) or auftrag.sitzung != self.sitzung:
            raise ValueError("Fremde Auftragssitzung.")
        p = auftrag.plan
        if not isinstance(p, Plan) or type(p.takt) is not int or not 1 <= p.takt <= MAX_TAKT:
            raise ValueError("Ungültiger Auftrag.")
        if p.ziel not in ("PRIMAER", "RESERVE", "WARTEN"):
            raise ValueError("Ungültiges Arbeitsziel.")
        alt = self.eintraege.get(p.takt)
        if alt is not None:
            if auftrag != alt[0]:
                raise ValueError("Auftragskennung bereits mit anderem Inhalt belegt.")
            return alt[1]
        return None

    def vermerken(self, auftrag, status, grund=""):
        bekannt = self.bekannt(auftrag)
        if bekannt is not None:
            return bekannt
        if len(self.eintraege) >= self.kapazitaet:
            raise OverflowError("Auftragsregister voll; kein alter Eintrag wird automatisch vergessen.")
        quittung = Quittung(self.sitzung, auftrag.plan.takt, status, grund=grund)
        self.eintraege[auftrag.plan.takt] = (auftrag, quittung)
        return quittung

    def ausfuehren(self, auftrag, arbeiter):
        bekannt = self.bekannt(auftrag)
        if bekannt is not None:
            return bekannt
        if auftrag.plan.ziel == "WARTEN":
            return self.vermerken(auftrag, "AUSGESETZT", auftrag.plan.grund)
        # Vor dem Aufruf vermerken: auch ein erneuter Aufruf aus dem Callback
        # selbst darf nicht noch einmal arbeiten.
        self.vermerken(auftrag, "IN_ARBEIT")
        try:
            ergebnis = arbeiter(auftrag)
            erwartet = hashlib.sha256(f"OSCan-Auftrag:{auftrag.plan.takt}".encode("ascii")).hexdigest()
            if ergebnis != erwartet:
                raise ValueError("Arbeitsergebnis passt nicht zum Auftrag.")
        except BaseException as fehler:
            quittung = Quittung(self.sitzung, auftrag.plan.takt, "UNGEKLAERT", grund=type(fehler).__name__)
            self.eintraege[auftrag.plan.takt] = (auftrag, quittung)
            if not isinstance(fehler, Exception):
                raise
            return quittung
        quittung = Quittung(self.sitzung, auftrag.plan.takt, "ERLEDIGT", ergebnis)
        self.eintraege[auftrag.plan.takt] = (auftrag, quittung)
        return quittung

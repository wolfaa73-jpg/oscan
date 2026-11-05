"""Abgefragte Zustände mehrerer Lernknoten mit getrennten Sitzungen und Empfangsfristen."""
import math
import struct
import uuid
import zlib
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from kern import Knoten, MAX_TAKT, ZUSTAENDE
from versuch import TOKEN

KOPF = struct.Struct("!2sBBH16sIIBB")
CRC = struct.Struct("!I")
PAKET_BYTES = KOPF.size + CRC.size
FRAGE, MELDUNG = 0, 1
ZUSTAND_JE_TOKEN = {TOKEN[z]: z for z in ZUSTAENDE}


@dataclass(frozen=True)
class Paket:
    art: int
    knoten: int
    sitzung: bytes
    runde: int
    takt: int = 0
    token: int = 0
    flags: int = 0

    def pruefen(self):
        for wert, minimum, maximum in ((self.art, 0, 1), (self.knoten, 1, 65535),
                                       (self.runde, 1, MAX_TAKT), (self.takt, 0, MAX_TAKT),
                                       (self.token, 0, 3), (self.flags, 0, 3)):
            if type(wert) is not int or not minimum <= wert <= maximum:
                raise ValueError("Paketfeld außerhalb seines Bereichs.")
        if type(self.sitzung) is not bytes or len(self.sitzung) != 16 or not any(self.sitzung):
            raise ValueError("Eine nichtleere 128-Bit-Sitzungskennung wird benötigt.")
        if self.art == FRAGE:
            if self.takt or self.token or self.flags:
                raise ValueError("Eine Abfrage trägt keinen Beobachtungszustand.")
        elif not self.takt or self.token not in ZUSTAND_JE_TOKEN:
            raise ValueError("Eine Meldung braucht Takt und Zustand.")
        elif (self.flags & 2 and self.token != TOKEN["AUSFALL"]) or (self.flags & 1 and self.token == TOKEN["AUSFALL"]):
            raise ValueError("Zustand und Warnflags widersprechen sich.")

    def kodieren(self):
        self.pruefen()
        inhalt = KOPF.pack(b"OC", 1, self.art, self.knoten, self.sitzung,
                           self.runde, self.takt, self.token, self.flags)
        return inhalt + CRC.pack(zlib.crc32(inhalt))

    @classmethod
    def lesen(cls, daten):
        if not isinstance(daten, bytes) or len(daten) != PAKET_BYTES:
            raise ValueError("Ungültige Paketlänge.")
        inhalt = daten[:-CRC.size]
        if CRC.unpack(daten[-CRC.size:])[0] != zlib.crc32(inhalt):
            raise ValueError("Prüfsumme stimmt nicht.")
        magic, version, art, knoten, sitzung, runde, takt, token, flags = KOPF.unpack(inhalt)
        if magic != b"OC" or version != 1:
            raise ValueError("Unbekannte Protokollversion.")
        paket = cls(art, knoten, sitzung, runde, takt, token, flags)
        paket.pruefen()
        return paket


class Messknoten:
    """Eine neue Frage löst eine Beobachtung aus. Wiederholungen liefern die gespeicherte Antwort."""

    def __init__(self, nummer: int, sitzung: bytes, lernen: Knoten,
                 quelle: Callable[[], Tuple[int, str]]):
        Paket(FRAGE, nummer, sitzung, 1).pruefen()
        self.nummer, self.sitzung = nummer, sitzung
        self.lernen, self.quelle = lernen, quelle
        self.runde = 0
        self.letzte_antwort = None

    def antwort(self, daten):
        try:
            p = Paket.lesen(daten)
        except ValueError:
            return None
        if p.art != FRAGE or p.knoten != self.nummer or p.sitzung != self.sitzung:
            return None
        if p.runde < self.runde:
            return None
        if p.runde == self.runde:
            return self.letzte_antwort
        takt, zustand = self.quelle()
        s = self.lernen.schritt(takt, zustand)
        flags = int(s.vorwarnung) | (int(s.sofort) << 1)
        antwort = Paket(MELDUNG, self.nummer, self.sitzung, p.runde,
                        s.takt, TOKEN[s.zustand], flags).kodieren()
        self.runde, self.letzte_antwort = p.runde, antwort
        return antwort


@dataclass
class Verbindung:
    sitzung: bytes
    runde: int = 0
    gefragt: Optional[float] = None
    bestaetigt: Optional[float] = None
    meldung: Optional[Paket] = None
    erledigt: bool = False


@dataclass(frozen=True)
class Sicht:
    zustand: Optional[str]
    takt: Optional[int]
    vorwarnung: bool
    sofort: bool
    alter: Optional[float]
    grund: str


class Zentrale:
    """Zuordnung durch den Betreiber. Datenpakete dürfen keine neue Sitzung anmelden."""

    def __init__(self, erlaubte_knoten, antwortfrist=1.0, gueltigkeit=3.0):
        nummern = tuple(erlaubte_knoten)
        if not nummern or len(set(nummern)) != len(nummern):
            raise ValueError("Eine eindeutige Liste erlaubter Knoten wird benötigt.")
        for nr in nummern:
            if type(nr) is not int or not 1 <= nr <= 65535:
                raise ValueError("Ungültige Knotennummer.")
        if not all(math.isfinite(x) and x > 0 for x in (antwortfrist, gueltigkeit)):
            raise ValueError("Fristen müssen positiv und endlich sein.")
        if antwortfrist > gueltigkeit:
            raise ValueError("Antwortfrist darf die Gültigkeit nicht überschreiten.")
        self.erlaubt = frozenset(nummern)
        self.antwortfrist, self.gueltigkeit = antwortfrist, gueltigkeit
        self.verbindungen: Dict[int, Verbindung] = {}
        self.verwendete_sitzungen = set()
        self.letzte_zeit = -math.inf

    def anmelden(self, nummer, sitzung=None):
        if nummer not in self.erlaubt:
            raise ValueError("Knoten ist nicht vorgesehen.")
        sitzung = uuid.uuid4().bytes if sitzung is None else sitzung
        Paket(FRAGE, nummer, sitzung, 1).pruefen()
        if sitzung in self.verwendete_sitzungen:
            raise ValueError("Eine Sitzung darf nicht erneut benutzt werden.")
        self.verwendete_sitzungen.add(sitzung)
        self.verbindungen[nummer] = Verbindung(sitzung)
        return sitzung

    def zeit_pruefen(self, jetzt):
        if not math.isfinite(jetzt) or jetzt < self.letzte_zeit:
            raise ValueError("Die monotone Empfängerzeit darf nicht zurücklaufen.")
        self.letzte_zeit = jetzt

    def frage(self, nummer, jetzt):
        self.zeit_pruefen(jetzt)
        v = self.verbindungen[nummer]
        if v.runde == MAX_TAKT:
            raise ValueError("Rundenzähler ausgeschöpft. Neue Sitzung anmelden.")
        v.runde += 1
        v.gefragt, v.erledigt = jetzt, False
        return Paket(FRAGE, nummer, v.sitzung, v.runde).kodieren()

    def empfange(self, daten, jetzt):
        self.zeit_pruefen(jetzt)
        try:
            p = Paket.lesen(daten)
        except ValueError:
            return "UNGUELTIG"
        if p.art != MELDUNG:
            return "KEINE_MELDUNG"
        v = self.verbindungen.get(p.knoten)
        if v is None:
            return "UNBEKANNT"
        if p.sitzung != v.sitzung:
            return "ALTE_SITZUNG"
        if v.gefragt is None or p.runde != v.runde:
            return "ALTE_RUNDE"
        if v.erledigt:
            return "DOPPELT"
        if jetzt - v.gefragt >= self.antwortfrist:
            return "ZU_SPAET"
        if v.meldung is not None and p.takt <= v.meldung.takt:
            return "ALTER_MESSWERT"
        # Alter beginnt bei der Frage, nicht bei einer womöglich verspäteten Antwort.
        v.meldung, v.bestaetigt, v.erledigt = p, v.gefragt, True
        return "ANGENOMMEN"

    def sicht(self, nummer, jetzt):
        self.zeit_pruefen(jetzt)
        v = self.verbindungen.get(nummer)
        if v is None or v.meldung is None:
            return Sicht(None, None, False, False, None, "WARTET")
        alter = jetzt - v.bestaetigt
        if alter >= self.gueltigkeit:
            return Sicht(None, None, False, False, alter, "VERALTET")
        p = v.meldung
        return Sicht(ZUSTAND_JE_TOKEN[p.token], p.takt, bool(p.flags & 1),
                     bool(p.flags & 2), alter, "BESTAETIGT")

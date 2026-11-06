"""Begrenzter Speicher für benannte SHA-256-Arbeit und ihr transaktionales Ergebnis.

Die fachliche Wirkung dieses Backends IST der Ergebnisdatensatz. Keine externe
Datei, Zahlung oder Geräteaktion wird durch diese Transaktion abgesichert.
"""
import fcntl
import hashlib
import os
import re
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Hashauftrag:
    kennung: str
    daten: bytes


@dataclass(frozen=True)
class Hashergebnis:
    kennung: str
    sha256: str
    arbeiter: str


def pruefe_auftrag(auftrag):
    if (not isinstance(auftrag, Hashauftrag) or type(auftrag.kennung) is not str
            or re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", auftrag.kennung) is None
            or type(auftrag.daten) is not bytes or len(auftrag.daten) > 1024 * 1024):
        raise ValueError("Benannter Hashauftrag mit höchstens 1 MiB erforderlich.")


def verbinde(pfad):
    # mode=rw: Ein verschwundenes Journal darf beim Arbeiter keine neue DB erzeugen.
    db = sqlite3.connect(Path(pfad).resolve().as_uri() + "?mode=rw", uri=True,
                         isolation_level=None, timeout=.5)
    try:
        db.execute("PRAGMA synchronous=EXTRA")
        db.execute("PRAGMA fullfsync=ON")
        if db.execute("PRAGMA synchronous").fetchone()[0] != 3:
            raise RuntimeError("Dauerhafte Synchronisation fehlt.")
        return db
    except BaseException:
        db.close()
        raise


class Arbeitsspeicher:
    """Ein Supervisor besitzt die Datei; Arbeiter erhalten seine aktuelle Epoche.

    Eine neue Epoche sperrt alte Arbeiter innerhalb derselben Schreibtransaktion.
    Alle Methoden des Besitzers gehören in einen seriellen Ereignisablauf.
    """

    def __init__(self, pfad, kapazitaet=128):
        if type(kapazitaet) is not int or not 1 <= kapazitaet <= 4096:
            raise ValueError("Kapazität zwischen 1 und 4096 erforderlich.")
        self.pfad = Path(pfad).resolve()
        self.kapazitaet = kapazitaet
        self.epoche = uuid.uuid4().hex
        self._besitzer = (os.getpid(), threading.get_ident())
        self._db, self._sperre = None, None
        self._defekt = False
        try:
            fd = os.open(str(self.pfad) + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
            self._sperre = os.fdopen(fd, "r+b")
            try:
                fcntl.flock(self._sperre.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as fehler:
                raise RuntimeError("Arbeitsspeicher hat bereits einen Supervisor.") from fehler
            vorhanden = self.pfad.exists()
            if not vorhanden:
                sqlite3.connect(str(self.pfad)).close()
            self._db = verbinde(self.pfad)
            if vorhanden:
                if (self._db.execute("PRAGMA application_id").fetchone()[0] != 0x4F534152
                        or self._db.execute("PRAGMA user_version").fetchone()[0] != 1
                        or self._db.execute("PRAGMA quick_check").fetchall() != [("ok",)]):
                    raise ValueError("Unbekannter oder beschädigter Arbeitsspeicher.")
                if self._db.execute("SELECT kapazitaet FROM laufzeit").fetchall() != [(kapazitaet,)]:
                    raise ValueError("Kapazität des vorhandenen Speichers stimmt nicht.")
            if self._db.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
                raise RuntimeError("Rollback-Journal erforderlich.")
            self._db.execute("BEGIN IMMEDIATE")
            if not vorhanden:
                self._db.execute(f"PRAGMA application_id={0x4F534152}")
                self._db.execute("PRAGMA user_version=1")
                self._db.execute("CREATE TABLE laufzeit (epoche TEXT NOT NULL, kapazitaet INTEGER NOT NULL)")
                self._db.execute("INSERT INTO laufzeit VALUES (?,?)", (self.epoche, kapazitaet))
                self._db.execute("""CREATE TABLE arbeit (
                    kennung TEXT PRIMARY KEY NOT NULL, daten BLOB NOT NULL,
                    ergebnis TEXT, arbeiter TEXT,
                    CHECK((ergebnis IS NULL AND arbeiter IS NULL) OR
                          (ergebnis IS NOT NULL AND arbeiter IS NOT NULL)))""")
            else:
                if self._db.execute("SELECT count(*) FROM arbeit").fetchone()[0] > kapazitaet:
                    raise ValueError("Speicher überschreitet seine Kapazität.")
                zeilen = self._db.execute("SELECT kennung,daten,ergebnis,arbeiter FROM arbeit")
                for k, d, e, w in zeilen:
                    pruefe_auftrag(Hashauftrag(k, d))
                    if ((e is None) != (w is None) or
                            e is not None and (e != hashlib.sha256(d).hexdigest()
                                              or type(w) is not str or re.fullmatch(r"[0-9a-f]{32}", w) is None)):
                        raise ValueError("Widersprüchliches gespeichertes Ergebnis.")
                # Muss mit noch laufenden alten Schreibern serialisiert werden.
                self._db.execute("UPDATE laufzeit SET epoche=?", (self.epoche,))
            self._db.execute("COMMIT")
        except BaseException:
            self.close()
            raise

    def _offen(self):
        if (os.getpid(), threading.get_ident()) != self._besitzer:
            raise RuntimeError("Arbeitsspeicher gehört seinem erzeugenden Ereignisablauf.")
        if self._db is None or self._defekt:
            raise RuntimeError("Arbeitsspeicher geschlossen oder gesperrt.")

    def registriere(self, auftrag):
        self._offen()
        pruefe_auftrag(auftrag)
        try:
            self._db.execute("BEGIN IMMEDIATE")
            alt = self._db.execute("SELECT daten FROM arbeit WHERE kennung=?", (auftrag.kennung,)).fetchone()
            if alt is not None and alt[0] != auftrag.daten:
                raise ValueError("Fachliche Kennung bereits mit anderem Inhalt belegt.")
            if alt is None:
                if self._db.execute("SELECT count(*) FROM arbeit").fetchone()[0] >= self.kapazitaet:
                    raise OverflowError("Arbeitsspeicher voll; keine alten Kennungen werden vergessen.")
                self._db.execute("INSERT INTO arbeit VALUES (?,?,NULL,NULL)", (auftrag.kennung, auftrag.daten))
            self._db.execute("COMMIT")
        except BaseException as fehler:
            if not isinstance(fehler, (ValueError, OverflowError)):
                self._defekt = True
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    def ergebnis(self, auftrag):
        self._offen()
        pruefe_auftrag(auftrag)
        try:
            zeile = self._db.execute("SELECT daten,ergebnis,arbeiter FROM arbeit WHERE kennung=?",
                                     (auftrag.kennung,)).fetchone()
        except sqlite3.Error:
            self._defekt = True
            raise
        if zeile is None or zeile[0] != auftrag.daten:
            raise ValueError("Auftrag nicht registriert oder widersprüchlich.")
        if zeile[1] is None:
            return None
        if zeile[1] != hashlib.sha256(auftrag.daten).hexdigest():
            self._defekt = True
            raise ValueError("Gespeichertes Ergebnis stimmt nicht mit dem Inhalt überein.")
        return Hashergebnis(auftrag.kennung, zeile[1], zeile[2])

    def offene(self):
        self._offen()
        return tuple(Hashauftrag(k, d) for k, d in self._db.execute(
            "SELECT kennung,daten FROM arbeit WHERE ergebnis IS NULL ORDER BY kennung"))

    def close(self):
        if (os.getpid(), threading.get_ident()) != self._besitzer:
            raise RuntimeError("Nur der Besitzer darf den Speicher schließen.")
        try:
            if self._db is not None:
                self._db.close()
        finally:
            self._db = None
            if self._sperre is not None:
                self._sperre.close()
                self._sperre = None

    def __enter__(self):
        self._offen()
        return self

    def __exit__(self, *_):
        self.close()

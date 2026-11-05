"""Dauerhafte Auftragsquittungen für einen seriellen POSIX-Ereignisablauf.

Vor der Wirkung wird IN_ARBEIT festgeschrieben. Nach einem Neustart wird daraus
UNGEKLAERT, niemals ein automatischer Wiederholungsauftrag. Keine Exactly-once-
Garantie für externe Wirkungen; diese liegen außerhalb der SQLite-Transaktion.
"""
import fcntl
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from auftraege import Auftrag, Quittung
from kern import MAX_TAKT
from systemkern import Plan


def _plantext(auftrag):
    if not isinstance(auftrag, Auftrag):
        raise ValueError("Auftrag erforderlich.")
    if type(auftrag.sitzung) is not bytes or len(auftrag.sitzung) != 16 or not any(auftrag.sitzung):
        raise ValueError("128-Bit-Auftragssitzung erforderlich.")
    p = auftrag.plan
    if (not isinstance(p, Plan) or type(p.takt) is not int or not 1 <= p.takt <= MAX_TAKT
            or p.zustand not in (None, "OK", "SCHWACH", "AUSFALL")
            or p.ziel not in ("PRIMAER", "RESERVE", "WARTEN")
            or type(p.vorwarnung) is not bool or type(p.reflex) is not bool
            or type(p.grund) is not str or len(p.grund) > 1024
            or (p.reserve_fuer is not None and
                (type(p.reserve_fuer) is not int or not p.takt < p.reserve_fuer <= MAX_TAKT))):
        raise ValueError("Ungültiger Auftragsplan.")
    return json.dumps(asdict(p), sort_keys=True, ensure_ascii=True, separators=(",", ":"))


class Auftragsjournal:
    """Ein Besitzer, lokale Platte, neue Auftragssitzung bei jedem Öffnen.

    Bekannte alte Kennungen liefern nur Quittungen. Neue Arbeit muss aus der
    aktuellen Sitzung stammen. Kapazität gilt über alle Sitzungen hinweg.
    Datenbank und .lock-Datei niemals während der Nutzung verschieben/löschen.
    """

    def __init__(self, pfad, kapazitaet=1024):
        if type(kapazitaet) is not int or kapazitaet < 1:
            raise ValueError("Positive Registerkapazität erforderlich.")
        self._besitzer = (os.getpid(), threading.get_ident())
        self._db, self._sperre = None, None
        self._defekt, self._aktiv = False, False
        self.kapazitaet = kapazitaet
        self.sitzung = uuid.uuid4().bytes
        self.pfad = Path(pfad).resolve()
        try:
            fd = os.open(str(self.pfad) + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
            self._sperre = os.fdopen(fd, "r+b")
            try:
                fcntl.flock(self._sperre.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as fehler:
                raise RuntimeError("Auftragsjournal hat bereits einen Besitzer.") from fehler
            # Erst nach der Besitzsperre prüfen: ein anderer Prozess könnte es
            # zwischen Pfadauflösung und Sperrerwerb angelegt haben.
            vorhanden = self.pfad.exists()
            self._db = sqlite3.connect(str(self.pfad), isolation_level=None, timeout=0)
            if vorhanden:
                if (self._db.execute("PRAGMA application_id").fetchone()[0] != 0x4F53434E
                        or self._db.execute("PRAGMA user_version").fetchone()[0] != 1):
                    raise ValueError("Unbekanntes Journalformat; keine automatische Neuerstellung.")
                if self._db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                    raise ValueError("Journal beschädigt.")
                if self._db.execute("SELECT kapazitaet FROM metadaten").fetchall() != [(kapazitaet,)]:
                    raise ValueError("Kapazität stimmt nicht mit dem gespeicherten Journal überein.")
            if self._db.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
                raise RuntimeError("SQLite-Rollback-Journal erforderlich.")
            self._db.execute("PRAGMA synchronous=EXTRA")
            self._db.execute("PRAGMA fullfsync=ON")
            if self._db.execute("PRAGMA synchronous").fetchone()[0] != 3:
                raise RuntimeError("Dauerhafte SQLite-Synchronisation fehlt.")
            with self._transaktion():
                if not vorhanden:
                    self._db.execute("PRAGMA application_id=1330856782")
                    self._db.execute("PRAGMA user_version=1")
                    self._db.execute("CREATE TABLE metadaten (kapazitaet INTEGER NOT NULL)")
                    self._db.execute("INSERT INTO metadaten VALUES (?)", (kapazitaet,))
                    self._db.execute("""CREATE TABLE auftraege (
                        sitzung BLOB NOT NULL CHECK(length(sitzung)=16),
                        takt INTEGER NOT NULL CHECK(takt BETWEEN 1 AND 4294967295),
                        plan TEXT NOT NULL,
                        status TEXT NOT NULL CHECK(status IN
                          ('IN_ARBEIT','ERLEDIGT','AUSGESETZT','VERFALLEN','UNGEKLAERT')),
                        ergebnis TEXT, grund TEXT NOT NULL,
                        PRIMARY KEY(sitzung,takt))""")
                zeilen = self._db.execute("SELECT * FROM auftraege").fetchall()
                if len(zeilen) > kapazitaet:
                    raise ValueError("Journal überschreitet seine Kapazität.")
                for s, t, p, status, ergebnis, grund in zeilen:
                    a = Auftrag(s, Plan(**json.loads(p)))
                    if (_plantext(a) != p or a.plan.takt != t or s == self.sitzung
                            or type(grund) is not str or len(grund) > 1024
                            or status not in ("IN_ARBEIT", "ERLEDIGT", "AUSGESETZT", "VERFALLEN", "UNGEKLAERT")
                            or ergebnis != (self._erwartet(a) if status == "ERLEDIGT" else None)):
                        raise ValueError("Widersprüchlicher Journaleintrag.")
                self._db.execute("""UPDATE auftraege SET status='UNGEKLAERT',
                    grund='Neustart ohne dauerhaft bestätigten Abschluss'
                    WHERE status='IN_ARBEIT'""")
        except BaseException:
            self.close()
            raise

    def _pruefe_offen(self):
        if (os.getpid(), threading.get_ident()) != self._besitzer:
            raise RuntimeError("Journal gehört in den erzeugenden Prozess und Ereignisablauf.")
        if self._db is None or self._defekt:
            raise RuntimeError("Journal geschlossen oder nach Speicherfehler gesperrt.")

    @contextmanager
    def _transaktion(self):
        self._pruefe_offen()
        try:
            self._db.execute("BEGIN IMMEDIATE")
            yield
            self._db.execute("COMMIT")
        except BaseException:
            self._defekt = True
            try:
                if self._db.in_transaction:
                    self._db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise

    @staticmethod
    def _erwartet(auftrag):
        return hashlib.sha256(f"OSCan-Auftrag:{auftrag.plan.takt}".encode("ascii")).hexdigest()

    def bekannt(self, auftrag):
        self._pruefe_offen()
        plan = _plantext(auftrag)
        try:
            alt = self._db.execute("SELECT plan,status,ergebnis,grund FROM auftraege WHERE sitzung=? AND takt=?",
                                   (auftrag.sitzung, auftrag.plan.takt)).fetchone()
        except sqlite3.Error:
            self._defekt = True
            raise
        if alt is not None:
            if alt[0] != plan:
                raise ValueError("Auftragskennung bereits mit anderem Inhalt belegt.")
            return Quittung(auftrag.sitzung, auftrag.plan.takt, *alt[1:])
        if auftrag.sitzung != self.sitzung:
            raise ValueError("Unbekannter Auftrag aus einer alten oder fremden Sitzung.")
        return None

    def vermerken(self, auftrag, status, grund=""):
        alt = self.bekannt(auftrag)
        if alt is not None:
            return alt
        if status not in ("IN_ARBEIT", "AUSGESETZT", "VERFALLEN") or type(grund) is not str or len(grund) > 1024:
            raise ValueError("Ungültiger Anfangszustand.")
        if self._db.execute("SELECT count(*) FROM auftraege").fetchone()[0] >= self.kapazitaet:
            raise OverflowError("Journal voll; alte Kennungen bleiben erhalten.")
        with self._transaktion():
            self._db.execute("INSERT INTO auftraege VALUES (?,?,?,?,?,?)",
                             (auftrag.sitzung, auftrag.plan.takt, _plantext(auftrag), status, None, grund))
        return Quittung(auftrag.sitzung, auftrag.plan.takt, status, grund=grund)

    def uebersicht(self):
        """Aufträge und Quittungen zur Klärung wiederfinden; löst keine Arbeit aus."""
        self._pruefe_offen()
        try:
            zeilen = self._db.execute("SELECT sitzung,plan FROM auftraege ORDER BY rowid").fetchall()
        except sqlite3.Error:
            self._defekt = True
            raise
        auftraege = [Auftrag(s, Plan(**json.loads(p))) for s, p in zeilen]
        return tuple((a, self.bekannt(a)) for a in auftraege)

    def _abschliessen(self, auftrag, status, ergebnis=None, grund=""):
        with self._transaktion():
            cursor = self._db.execute("""UPDATE auftraege SET status=?, ergebnis=?, grund=?
                WHERE sitzung=? AND takt=? AND status='IN_ARBEIT'""",
                (status, ergebnis, grund, auftrag.sitzung, auftrag.plan.takt))
            if cursor.rowcount != 1:
                raise RuntimeError("Arbeitsanfang fehlt im Journal.")
        return Quittung(auftrag.sitzung, auftrag.plan.takt, status, ergebnis, grund)

    def ausfuehren(self, auftrag, arbeiter):
        alt = self.bekannt(auftrag)
        if alt is not None:
            return alt
        if self._aktiv:
            raise RuntimeError("Keine verschachtelte neue Arbeit im seriellen Journal.")
        if auftrag.plan.ziel == "WARTEN":
            return self.vermerken(auftrag, "AUSGESETZT", auftrag.plan.grund)
        self.vermerken(auftrag, "IN_ARBEIT")  # Commit MUSS vor der Wirkung liegen.
        self._aktiv = True
        try:
            try:
                ergebnis = arbeiter(auftrag)
                if ergebnis != self._erwartet(auftrag):
                    raise ValueError("Arbeitsergebnis passt nicht zum Auftrag.")
            except BaseException as fehler:
                q = self._abschliessen(auftrag, "UNGEKLAERT", grund=type(fehler).__name__[:1024])
                if not isinstance(fehler, Exception):
                    raise
                return q
            return self._abschliessen(auftrag, "ERLEDIGT", ergebnis)
        finally:
            self._aktiv = False

    def close(self):
        if (os.getpid(), threading.get_ident()) != self._besitzer:
            raise RuntimeError("Nur der Besitzer darf das Journal schließen.")
        if self._aktiv:
            raise RuntimeError("Journal darf während der Arbeit nicht geschlossen werden.")
        try:
            if self._db is not None:
                self._db.close()
        finally:
            self._db = None
            if self._sperre is not None:
                self._sperre.close()  # Datei behalten; ein neues Inode würde die Sperre umgehen.
                self._sperre = None

    def __enter__(self):
        self._pruefe_offen()
        return self

    def __exit__(self, *_):
        self.close()

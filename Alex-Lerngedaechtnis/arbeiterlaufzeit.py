"""Beaufsichtigte lokale Hasharbeiter mit Bereitschaft, Ausfall und Wiederanlauf.

Nur eigene spawn-Prozesse. Übernahme nach nachgewiesenem Prozessende und
dauerhafter Ergebnisprüfung. Wiederholung ist nur für dieses transaktionale
Hash-Backend zulässig, nicht für beliebige externe Wirkungen.
"""
import hashlib
import json
import math
import multiprocessing as mp
import os
import threading
import time
import uuid
from multiprocessing.connection import wait

from arbeitsspeicher import Arbeitsspeicher, verbinde

STOERUNGEN = ("keine", "vor_commit", "nach_commit", "haengt")


def _sende(kanal, daten):
    paket = json.dumps(daten, allow_nan=False).encode("utf-8")
    if len(paket) > 4096:
        raise ValueError("Nachricht zu groß.")
    kanal.send_bytes(paket)


def _empfange(kanal):
    daten = json.loads(kanal.recv_bytes(4096))
    if type(daten) is not dict:
        raise ValueError("Nachricht muss ein Objekt sein.")
    return daten


def bearbeite(db, epoche, instanz, kennung, stoerung="keine"):
    """Der Ergebnisdatensatz und sein fachlicher Effekt sind dieselbe Transaktion."""
    if stoerung not in STOERUNGEN:
        raise ValueError("Unbekannte Teststörung.")
    try:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT epoche FROM laufzeit").fetchall() != [(epoche,)]:
            raise ValueError("Alte Supervisor-Epoche; kein Schreiben erlaubt.")
        zeile = db.execute("SELECT daten,ergebnis,arbeiter FROM arbeit WHERE kennung=?", (kennung,)).fetchone()
        if zeile is None:
            raise ValueError("Unbekannte fachliche Auftragskennung.")
        daten, ergebnis, ursprung = zeile
        if ergebnis is None:
            ergebnis = hashlib.sha256(daten).hexdigest()
            ursprung = instanz
            db.execute("UPDATE arbeit SET ergebnis=?,arbeiter=? WHERE kennung=?", (ergebnis, ursprung, kennung))
            if stoerung == "vor_commit":
                os._exit(74)
            if stoerung == "haengt":
                while True:
                    time.sleep(1)  # Supervisor muss diesen eigenen Prozess beenden.
        elif ergebnis != hashlib.sha256(daten).hexdigest():
            raise ValueError("Widersprüchlicher gespeicherter Hash.")
        db.execute("COMMIT")
        if stoerung == "nach_commit":
            os._exit(75)
        return ergebnis, ursprung
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise


def _dienst(kanal, pfad, epoche, instanz):
    db = None
    try:
        db = verbinde(pfad)
        if db.execute("SELECT epoche FROM laufzeit").fetchall() != [(epoche,)]:
            return
        _sende(kanal, dict(art="BEREIT", instanz=instanz, epoche=epoche, pid=os.getpid()))
        letzte_folge = 0
        while True:
            anfrage = _empfange(kanal)
            folge = anfrage.get("folge")
            if (anfrage.get("instanz") != instanz or type(folge) is not int
                    or folge != letzte_folge + 1):
                return
            letzte_folge = folge
            antwort = dict(instanz=instanz, folge=folge)
            try:
                if anfrage.get("art") == "PING":
                    if db.execute("SELECT epoche FROM laufzeit").fetchall() != [(epoche,)]:
                        raise ValueError("Alte Epoche")
                    antwort.update(art="BEREIT")
                elif anfrage.get("art") == "ARBEIT":
                    kennung = anfrage["kennung"]
                    ergebnis, ursprung = bearbeite(db, epoche, instanz, kennung, anfrage["stoerung"])
                    antwort.update(art="ERGEBNIS", kennung=kennung, sha256=ergebnis, ursprung=ursprung)
                else:
                    raise ValueError("Unbekannte Aktion")
            except Exception as fehler:
                antwort.update(art="FEHLER", fehler=type(fehler).__name__)
            _sende(kanal, antwort)
    except (EOFError, OSError):
        pass
    finally:
        if db is not None:
            db.close()
        kanal.close()


class Arbeiterfehler(RuntimeError):
    def __init__(self, grund):
        super().__init__(grund)
        self.erkannt_ns = time.perf_counter_ns()


def _frist(wert):
    if type(wert) not in (int, float) or not math.isfinite(wert) or not 0 < wert <= 30:
        raise ValueError("Positive endliche Prüffrist bis 30 Sekunden erforderlich.")


class Arbeiter:
    def __init__(self, pfad, epoche, startfrist=5):
        _frist(startfrist)
        self.instanz = uuid.uuid4().hex
        self.folge, self.bereit = 0, False
        self._besitzer = (os.getpid(), threading.get_ident())
        self._geschlossen = False
        self.exitcode = None
        kontext = mp.get_context("spawn")
        self.kanal, kind = kontext.Pipe()
        self.prozess = kontext.Process(target=_dienst, args=(kind, str(pfad), epoche, self.instanz), daemon=True)
        anfang = time.perf_counter_ns()
        try:
            self.prozess.start()
            kind.close()
            antwort = self._warte(startfrist)
            if antwort != dict(art="BEREIT", instanz=self.instanz, epoche=epoche, pid=self.prozess.pid):
                raise Arbeiterfehler("Falsche Bereitschaftsbestätigung")
            self.bereit = True
            self.bereit_ns = time.perf_counter_ns()
            self.start_ms = (self.bereit_ns - anfang) / 1e6
        except BaseException:
            kind.close()
            self.stop()
            raise

    def _eigen(self):
        if (os.getpid(), threading.get_ident()) != self._besitzer:
            raise RuntimeError("Arbeitersteuerung gehört ihrem erzeugenden Ereignisablauf.")

    def _warte(self, frist):
        ready = wait([self.kanal, self.prozess.sentinel], timeout=frist)
        if self.kanal in ready:
            try:
                return _empfange(self.kanal)
            except (EOFError, OSError, ValueError) as fehler:
                raise Arbeiterfehler("Kanal beendet oder Antwort beschädigt") from fehler
        if self.prozess.sentinel in ready:
            raise Arbeiterfehler("Arbeiterprozess beendet")
        raise Arbeiterfehler("Antwortfrist überschritten")

    def anfrage(self, art, frist, **daten):
        self._eigen()
        _frist(frist)
        if self._geschlossen or not self.bereit or not self.prozess.is_alive():
            raise Arbeiterfehler("Arbeiter nicht bereit")
        self.folge += 1
        anfang = time.perf_counter_ns()
        try:
            _sende(self.kanal, dict(art=art, instanz=self.instanz, folge=self.folge, **daten))
            rest = frist - (time.perf_counter_ns() - anfang) / 1e9
            antwort = self._warte(max(0, rest))
            erwartet = "BEREIT" if art == "PING" else "ERGEBNIS"
            if (antwort.get("instanz") != self.instanz or antwort.get("folge") != self.folge
                    or antwort.get("art") != erwartet):
                raise Arbeiterfehler("Unpassende Arbeiterantwort")
            if art == "ARBEIT" and antwort.get("kennung") != daten.get("kennung"):
                raise Arbeiterfehler("Antwort gehört zu anderem Auftrag")
            return antwort
        except BaseException as fehler:
            self.bereit = False
            if isinstance(fehler, (OSError, EOFError)):
                raise Arbeiterfehler("Arbeiterkanal ausgefallen") from fehler
            raise

    def stop(self):
        """Beendet nur den eigenen Prozess; Erfolg erst nach bestätigtem Ende."""
        self._eigen()
        if self._geschlossen:
            return
        self.bereit = False
        if self.prozess.pid is not None:
            self.prozess.join(timeout=.05)
            if self.prozess.is_alive():
                self.prozess.terminate()
                self.prozess.join(timeout=1)
            if self.prozess.is_alive():
                self.prozess.kill()
                self.prozess.join(timeout=1)
            if self.prozess.is_alive():
                raise RuntimeError("Prozessende nicht bestätigt; keine Übernahme erlaubt.")
            self.exitcode = self.prozess.exitcode
        self.kanal.close()
        self.prozess.close()
        self._geschlossen = True


class Wiederanlauf:
    """Ein aktueller Auftrag; höchstens ein Ersatzversuch; kein unbegrenztes Retry.

    Der Aufrufer behält fachliche Kennungen über Sitzungen hinweg bei. Der
    feste Fehlerpfad braucht keine Prognose, eine Vorwarnung kann die Reserve
    jedoch vorab tatsächlich starten und ihre Bereitschaft bestätigen lassen.
    """

    def __init__(self, pfad, antwortfrist=.5, startfrist=5, kapazitaet=128):
        _frist(antwortfrist)
        _frist(startfrist)
        self.antwortfrist, self.startfrist = antwortfrist, startfrist
        self.primaer, self.reserve = None, None
        self.reserve_start_ms, self.reserve_bereit_ns = 0.0, None
        self._besitzer = (os.getpid(), threading.get_ident())
        self._geschlossen, self._aktiv, self._defekt = False, False, False
        self.speicher = Arbeitsspeicher(pfad, kapazitaet)
        try:
            self.primaer = self._start()
        except BaseException:
            self.close()
            raise

    def _offen(self):
        if (os.getpid(), threading.get_ident()) != self._besitzer or self._geschlossen or self._defekt:
            raise RuntimeError("Laufzeit geschlossen, gesperrt oder fremder Ereignisablauf.")

    def _start(self):
        return Arbeiter(self.speicher.pfad, self.speicher.epoche, self.startfrist)

    def _beende(self, arbeiter):
        try:
            arbeiter.stop()
        except BaseException:
            self._defekt = True
            raise

    def vorbereiten(self):
        self._offen()
        if self._aktiv:
            raise RuntimeError("Keine Vorbereitung innerhalb eines laufenden Auftrags.")
        if self.reserve is None:
            self.reserve = self._start()
            self.reserve_start_ms = self.reserve.start_ms
            self.reserve_bereit_ns = self.reserve.bereit_ns
        else:
            self.reserve.anfrage("PING", self.antwortfrist)
        return self.reserve.start_ms

    def primaer_neustarten(self):
        self._offen()
        if self._aktiv:
            raise RuntimeError("Kein Neustart innerhalb eines laufenden Auftrags.")
        if self.primaer is not None:
            self._beende(self.primaer)
        self.primaer = None
        self.primaer = self._start()
        return self.primaer.start_ms

    def ausfuehren(self, auftrag, stoerung="keine", reserve_stoerung="keine"):
        self._offen()
        if self._aktiv or stoerung not in STOERUNGEN or reserve_stoerung not in STOERUNGEN:
            raise ValueError("Unzulässiger Aufruf oder unbekannte Teststörung.")
        self._aktiv = True
        anfang = time.perf_counter_ns()
        bericht = dict(kennung=getattr(auftrag, "kennung", None), versuche=[],
                       aus_speicher=False, reserve_start_nach_fehler_ms=0.0,
                       wiederanlauf_ms=0.0, uebernahme_nach_bestaetigtem_ende=False)
        fehler_ns = None
        try:
            self.speicher.registriere(auftrag)
            ergebnis = self.speicher.ergebnis(auftrag)
            if ergebnis is not None:
                bericht["aus_speicher"] = True
            for rolle in ("PRIMAER", "RESERVE"):
                if ergebnis is not None:
                    break
                if rolle == "RESERVE":
                    # Nur erreichbar, wenn der alte Arbeiter vollständig beendet ist.
                    bericht["uebernahme_nach_bestaetigtem_ende"] = True
                    if self.reserve is None:
                        self.reserve = self._start()
                        self.reserve_start_ms = self.reserve.start_ms
                        self.reserve_bereit_ns = self.reserve.bereit_ns
                        bericht["reserve_start_nach_fehler_ms"] = self.reserve.start_ms
                arbeiter = self.primaer if rolle == "PRIMAER" else self.reserve
                start = time.perf_counter_ns()
                if rolle == "RESERVE":
                    bericht["reserve_bereit_bis_einsatz_ms"] = (start - self.reserve_bereit_ns) / 1e6
                zeile = dict(rolle=rolle, instanz=arbeiter.instanz if arbeiter else None)
                try:
                    if arbeiter is None:
                        raise Arbeiterfehler("Primär muss erst neu gestartet werden")
                    antwort = arbeiter.anfrage("ARBEIT", self.antwortfrist, kennung=auftrag.kennung,
                                               stoerung=stoerung if rolle == "PRIMAER" else reserve_stoerung)
                    ergebnis = self.speicher.ergebnis(auftrag)
                    if (ergebnis is None or antwort.get("sha256") != ergebnis.sha256
                            or antwort.get("ursprung") != ergebnis.arbeiter):
                        raise Arbeiterfehler("Antwort ohne passenden dauerhaften Abschluss")
                    zeile.update(status="ERLEDIGT", dauer_ms=(time.perf_counter_ns() - start) / 1e6)
                except Arbeiterfehler as fehler:
                    if fehler_ns is None:
                        fehler_ns = fehler.erkannt_ns
                    # Bei nicht bestätigbarem Ende wirft stop(); kein Ersatzversuch.
                    if arbeiter is not None:
                        self._beende(arbeiter)
                    zeile.update(status="AUSFALL", grund=str(fehler),
                                 erkennung_ms=(fehler.erkannt_ns - start) / 1e6,
                                 dauer_ms=(time.perf_counter_ns() - start) / 1e6,
                                 exitcode=arbeiter.exitcode if arbeiter else None,
                                 beendet_bestaetigt=True)
                    if rolle == "PRIMAER":
                        self.primaer = None
                    else:
                        self.reserve = None
                    ergebnis = self.speicher.ergebnis(auftrag)
                    if ergebnis is not None:
                        bericht["aus_speicher"] = True
                bericht["versuche"].append(zeile)
            if ergebnis is None:
                raise Arbeiterfehler("Beide Versuche ohne Abschluss; Auftrag bleibt offen.")
            ende = time.perf_counter_ns()
            bericht["gesamt_ms"] = (ende - anfang) / 1e6
            if fehler_ns is not None:
                bericht["wiederanlauf_ms"] = (ende - fehler_ns) / 1e6
            return ergebnis, bericht
        finally:
            self._aktiv = False

    def close(self):
        if (os.getpid(), threading.get_ident()) != self._besitzer:
            raise RuntimeError("Nur der Besitzer darf die Laufzeit schließen.")
        if self._geschlossen:
            return
        if self._aktiv:
            raise RuntimeError("Laufzeit darf nicht während eines Auftrags geschlossen werden.")
        # Scheitert ein bestätigtes Ende, bleibt die Besitzsperre bestehen.
        for arbeiter in (self.primaer, self.reserve):
            if arbeiter is not None:
                self._beende(arbeiter)
        self.speicher.close()
        self._geschlossen = True

    def __enter__(self):
        self._offen()
        return self

    def __exit__(self, *_):
        self.close()

import hashlib
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from dataclasses import replace
from pathlib import Path

from auftraege import Auftrag
from auftragsjournal import Auftragsjournal
from kern import Knoten, REGELN
from neustartlabor import versuch
from systemkern import disponiere
from verbund import Messknoten
from verbundsystem import Verbundsystem


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pfad = Path(self.tmp.name) / "auftraege.sqlite3"
        self.j = Auftragsjournal(self.pfad, kapazitaet=3)
        self.addCleanup(self.j.close)
        self.a = Auftrag(self.j.sitzung, disponiere(1, "OK", False, False))
        self.aufrufe = 0

    def arbeiter(self, a):
        self.aufrufe += 1
        return hashlib.sha256(f"OSCan-Auftrag:{a.plan.takt}".encode("ascii")).hexdigest()

    def neu(self):
        self.j.close()
        self.j = Auftragsjournal(self.pfad, kapazitaet=3)
        self.addCleanup(self.j.close)

    def test_abgeschlossene_arbeit_ueberlebt_mehrere_neustarts(self):
        q = self.j.ausfuehren(self.a, self.arbeiter)
        for _ in range(3):
            self.neu()
            self.assertNotEqual(self.j.sitzung, self.a.sitzung)
            self.assertEqual(self.j.ausfuehren(self.a, self.arbeiter), q)
        self.assertEqual((q.status, self.aufrufe), ("ERLEDIGT", 1))

    def test_alte_unbenutzte_freigabe_darf_nicht_neu_beginnen(self):
        self.neu()
        with self.assertRaises(ValueError):
            self.j.ausfuehren(self.a, self.arbeiter)
        self.assertEqual(self.aufrufe, 0)

    def test_gleicher_takt_in_neuer_sitzung_ist_explizit_neue_arbeit(self):
        self.j.ausfuehren(self.a, self.arbeiter)
        self.neu()
        neu = replace(self.a, sitzung=self.j.sitzung)
        self.assertEqual(self.j.ausfuehren(neu, self.arbeiter).status, "ERLEDIGT")
        self.assertEqual(self.aufrufe, 2)  # Kennungen, nicht Geschäftsvorgänge, werden dedupliziert.

    def test_alte_kennung_mit_anderem_plan_bleibt_konflikt(self):
        self.j.ausfuehren(self.a, self.arbeiter)
        self.neu()
        with self.assertRaises(ValueError):
            self.j.ausfuehren(replace(self.a, plan=replace(self.a.plan, ziel="RESERVE")), self.arbeiter)
        self.assertEqual(self.aufrufe, 1)

    def test_angefangene_arbeit_wird_beim_oeffnen_ungeklaert(self):
        self.j.vermerken(self.a, "IN_ARBEIT")
        self.neu()
        q = self.j.ausfuehren(self.a, self.arbeiter)
        self.assertEqual(q.status, "UNGEKLAERT")
        self.neu()
        self.assertEqual(self.j.bekannt(self.a), q)
        self.assertEqual(self.aufrufe, 0)

    def test_wiederherstellung_findet_kennungen_ohne_altes_prozessgedaechtnis(self):
        erledigt = self.j.ausfuehren(self.a, self.arbeiter)
        offen = replace(self.a, plan=replace(self.a.plan, takt=2))
        self.j.vermerken(offen, "IN_ARBEIT")
        self.neu()
        eintraege = self.j.uebersicht()
        self.assertEqual(eintraege[0], (self.a, erledigt))
        self.assertEqual((eintraege[1][0], eintraege[1][1].status), (offen, "UNGEKLAERT"))
        self.assertEqual(self.j.uebersicht(), eintraege)
        self.assertEqual(self.aufrufe, 1)

    def test_anfang_ist_auf_platte_bevor_callback_beginnt(self):
        def pruefen(a):
            db = sqlite3.connect(self.pfad)
            try:
                self.assertEqual(db.execute("SELECT status FROM auftraege").fetchall(), [("IN_ARBEIT",)])
            finally:
                db.close()
            return self.arbeiter(a)
        self.assertEqual(self.j.ausfuehren(self.a, pruefen).status, "ERLEDIGT")

    def test_ergebnisverlust_und_falsches_ergebnis_bleiben_ungeklaert(self):
        def verloren(a):
            self.arbeiter(a)
            raise TimeoutError
        for t, callback in ((1, verloren), (2, lambda a: "falsch")):
            a = replace(self.a, sitzung=self.j.sitzung, plan=replace(self.a.plan, takt=t))
            self.assertEqual(self.j.ausfuehren(a, callback).status, "UNGEKLAERT")
            self.neu()
            self.assertEqual(self.j.ausfuehren(a, self.arbeiter).status, "UNGEKLAERT")
        self.assertEqual(self.aufrufe, 1)

    def test_unterbrechung_wird_gespeichert_und_weitergegeben(self):
        def abbrechen(a):
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self.j.ausfuehren(self.a, abbrechen)
        self.neu()
        self.assertEqual(self.j.ausfuehren(self.a, self.arbeiter).status, "UNGEKLAERT")
        self.assertEqual(self.aufrufe, 0)

    def test_reentrante_wiederholung_ist_nur_statusabfrage(self):
        def callback(a):
            self.assertEqual(self.j.ausfuehren(a, self.arbeiter).status, "IN_ARBEIT")
            with self.assertRaises(RuntimeError):
                self.j.ausfuehren(replace(a, plan=replace(a.plan, takt=2)), self.arbeiter)
            with self.assertRaises(RuntimeError):
                self.j.close()
            return self.arbeiter(a)
        self.assertEqual(self.j.ausfuehren(self.a, callback).status, "ERLEDIGT")
        self.assertEqual(self.aufrufe, 1)

    def test_kapazitaet_gilt_ueber_neustarts_ohne_alte_quittungen_zu_loeschen(self):
        alte = []
        for _ in range(3):
            a = replace(self.a, sitzung=self.j.sitzung)
            alte.append((a, self.j.ausfuehren(a, self.arbeiter)))
            self.neu()
        with self.assertRaises(OverflowError):
            self.j.ausfuehren(replace(self.a, sitzung=self.j.sitzung), self.arbeiter)
        for a, q in alte:
            self.assertEqual(self.j.ausfuehren(a, self.arbeiter), q)
        self.assertEqual(self.aufrufe, 3)

    def test_warten_und_verfall_bleiben_wirkungslos_nach_neustart(self):
        warten = replace(self.a, plan=disponiere(1, None, False, False))
        verfall = replace(self.a, plan=replace(self.a.plan, takt=2))
        self.j.ausfuehren(warten, self.arbeiter)
        self.j.vermerken(verfall, "VERFALLEN", "Abgelaufen")
        self.neu()
        for a, status in ((warten, "AUSGESETZT"), (verfall, "VERFALLEN")):
            self.assertEqual(self.j.ausfuehren(a, self.arbeiter).status, status)
        self.assertEqual(self.aufrufe, 0)

    def test_fehler_vor_start_verhindert_wirkung_und_sperrt_instanz(self):
        self.j._db.execute("PRAGMA query_only=ON")  # Echter SQLite-Schreibfehler.
        with self.assertRaises(sqlite3.OperationalError):
            self.j.ausfuehren(self.a, self.arbeiter)
        with self.assertRaises(RuntimeError):
            self.j.ausfuehren(self.a, self.arbeiter)
        self.assertEqual(self.aufrufe, 0)

    def test_fehlgeschlagener_abschluss_wird_nicht_als_erfolg_gemeldet(self):
        def callback(a):
            wert = self.arbeiter(a)
            self.j._db.execute("PRAGMA query_only=ON")
            return wert
        with self.assertRaises(sqlite3.OperationalError):
            self.j.ausfuehren(self.a, callback)
        with self.assertRaises(RuntimeError):
            self.j.bekannt(self.a)
        self.neu()
        self.assertEqual(self.j.ausfuehren(self.a, self.arbeiter).status, "UNGEKLAERT")
        self.assertEqual(self.aufrufe, 1)

    def test_zweiter_besitzer_darf_laufende_arbeit_nicht_als_abgestuerzt_markieren(self):
        self.j.vermerken(self.a, "IN_ARBEIT")
        code = "from auftragsjournal import Auftragsjournal; import sys; Auftragsjournal(sys.argv[1], 3)"
        kind = subprocess.run([sys.executable, "-B", "-c", code, str(self.pfad)],
                              capture_output=True, text=True, timeout=10)
        self.assertNotEqual(kind.returncode, 0)
        self.assertIn("bereits einen Besitzer", kind.stderr)
        self.assertEqual(self.j.bekannt(self.a).status, "IN_ARBEIT")

    def test_zweites_objekt_im_selben_prozess_bekommt_keinen_besitz(self):
        with self.assertRaises(RuntimeError):
            Auftragsjournal(self.pfad, 3)
        self.assertEqual(self.j.ausfuehren(self.a, self.arbeiter).status, "ERLEDIGT")

    def test_fremder_thread_kann_weder_arbeiten_noch_sperre_freigeben(self):
        fehler = []
        def fremd():
            for aktion in (lambda: self.j.ausfuehren(self.a, self.arbeiter), self.j.close):
                try:
                    aktion()
                except RuntimeError:
                    fehler.append("abgewiesen")
        thread = threading.Thread(target=fremd)
        thread.start()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(fehler, ["abgewiesen", "abgewiesen"])
        self.assertEqual(self.aufrufe, 0)
        self.assertEqual(self.j.ausfuehren(self.a, self.arbeiter).status, "ERLEDIGT")

    def test_verlorene_commit_bestaetigung_erzeugt_keinen_neuen_versuch(self):
        # Fehler nach einem erfolgreichen COMMIT: der Aufrufer weiß nicht,
        # ob die Platte den Anfang bzw. Abschluss bereits erhalten hat.
        class VerloreneBestaetigung:
            def __init__(self, db):
                self.db = db
            def __getattr__(self, name):
                return getattr(self.db, name)
            def execute(self, sql, *args):
                result = self.db.execute(sql, *args)
                if sql == "COMMIT":
                    raise OSError("Bestätigung verloren")
                return result
        for start in (True, False):
            a = replace(self.a, sitzung=self.j.sitzung)
            def callback(a):
                wert = self.arbeiter(a)
                self.j._db = VerloreneBestaetigung(self.j._db)
                return wert
            if start:
                self.j._db = VerloreneBestaetigung(self.j._db)
            with self.assertRaises(OSError):
                self.j.ausfuehren(a, callback)
            self.neu()
            q = self.j.ausfuehren(a, self.arbeiter)
            self.assertEqual(q.status, "UNGEKLAERT" if start else "ERLEDIGT")
        self.assertEqual(self.aufrufe, 1)

    def test_fremde_datenbank_wird_nicht_neu_angelegt(self):
        self.j.close()
        fremd = Path(self.tmp.name) / "fremd.db"
        db = sqlite3.connect(fremd)
        db.execute("CREATE TABLE wichtig (inhalt TEXT)")
        db.commit()
        db.close()
        vorher = fremd.read_bytes()
        with self.assertRaises(ValueError):
            Auftragsjournal(fremd)
        self.assertEqual(fremd.read_bytes(), vorher)

    def test_beschaedigung_wird_nicht_als_leeres_journal_behandelt(self):
        self.j.close()
        self.pfad.write_bytes(b"kein SQLite-Journal")
        with self.assertRaises(sqlite3.DatabaseError):
            Auftragsjournal(self.pfad, 3)
        self.assertEqual(self.pfad.read_bytes(), b"kein SQLite-Journal")

    def test_falsche_version_und_kapazitaet_werden_abgewiesen(self):
        self.j.close()
        with self.assertRaises(ValueError):
            Auftragsjournal(self.pfad, 4)
        db = sqlite3.connect(self.pfad)
        db.execute("PRAGMA user_version=99")
        db.close()
        with self.assertRaises(ValueError):
            Auftragsjournal(self.pfad, 3)

    def test_falscher_gespeicherter_erfolg_wird_abgewiesen(self):
        self.j.ausfuehren(self.a, self.arbeiter)
        self.j.close()
        db = sqlite3.connect(self.pfad)
        db.execute("UPDATE auftraege SET ergebnis='falsch'")
        db.commit()
        db.close()
        with self.assertRaises(ValueError):
            Auftragsjournal(self.pfad, 3)

    def test_fremde_sitzung_und_ungueltige_typen_starten_nichts(self):
        for a in (replace(self.a, sitzung=uuid.uuid4().bytes),
                  replace(self.a, sitzung=bytes(16)),
                  replace(self.a, plan=replace(self.a.plan, takt=True)),
                  replace(self.a, plan=replace(self.a.plan, vorwarnung=1)),
                  replace(self.a, plan=replace(self.a.plan, reserve_fuer=0))):
            with self.assertRaises(ValueError):
                self.j.ausfuehren(a, self.arbeiter)
        self.assertEqual(self.aufrufe, 0)

    def test_verbund_startet_nach_neustart_mit_neuen_freigaben(self):
        system = Verbundsystem(register=self.j)
        knoten = {}
        for nr in (1, 2):
            s = system.anmelden(nr)
            knoten[nr] = Messknoten(nr, s, Knoten(REGELN["erbe"]()), lambda: (1, "OK"))
        for nr, frage in system.beginne(1, 1).items():
            system.empfange(knoten[nr].antwort(frage), 1.1)
        a = system.entscheide(1.2)
        q = system.ausfuehren(a, 1.3, self.arbeiter)
        self.neu()
        neu = Verbundsystem(register=self.j)
        self.assertEqual((neu.takt, neu.vorher, neu.offen), (0, None, False))
        self.assertEqual(neu.ausfuehren(a, 2, self.arbeiter), q)
        with self.assertRaises(ValueError):
            neu.entscheide(2)
        self.assertEqual(self.aufrufe, 1)

    def test_harte_prozessabbrueche_an_drei_grenzen(self):
        daten = versuch()
        self.assertEqual([z["status_nach_neustart"] for z in daten["verlauf"]],
                         ["UNGEKLAERT", "UNGEKLAERT", "ERLEDIGT"])
        self.assertEqual([z["wirkungen_nachher"] for z in daten["verlauf"]], [0, 1, 1])

    def test_journalfehler_verwirft_vorsorge_im_verbund(self):
        system = Verbundsystem(register=self.j)
        for nr in (1, 2):
            system.anmelden(nr)
        fragen = system.beginne(1, 1)
        for nr, frage in fragen.items():
            k = Messknoten(nr, system.hub.verbindungen[nr].sitzung,
                          Knoten(REGELN["erbe"]()), lambda: (1, "SCHWACH"))
            system.empfange(k.antwort(frage), 1.1)
        a = system.entscheide(1.2)
        self.assertEqual(a.plan.reserve_fuer, 2)
        self.j._db.execute("PRAGMA query_only=ON")
        with self.assertRaises(sqlite3.OperationalError):
            system.ausfuehren(a, 1.3, self.arbeiter)
        self.assertIsNone(system.vorher)
        self.assertEqual(self.aufrufe, 0)


if __name__ == "__main__":
    unittest.main()

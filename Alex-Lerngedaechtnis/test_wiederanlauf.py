import hashlib
import json
import math
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from arbeitsspeicher import Arbeitsspeicher, Hashauftrag, verbinde
from arbeiterlaufzeit import Arbeiterfehler, Wiederanlauf, bearbeite
from wiederanlauflabor import durchlauf, zusammenfassung


class SpeicherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pfad = Path(self.tmp.name) / "arbeit.sqlite3"
        self.s = Arbeitsspeicher(self.pfad, 2)
        self.addCleanup(self.s.close)
        self.a = Hashauftrag("auftrag:1", b"unveraenderlicher Inhalt")

    def test_fachliche_kennung_ist_sitzungsunabhaengig(self):
        self.s.registriere(self.a)
        db = verbinde(self.pfad)
        try:
            digest, wer = bearbeite(db, self.s.epoche, "1" * 32, self.a.kennung)
        finally:
            db.close()
        alt = self.s.epoche
        self.s.close()
        with Arbeitsspeicher(self.pfad, 2) as neu:
            neu.registriere(self.a)
            self.assertNotEqual(neu.epoche, alt)
            self.assertEqual((neu.ergebnis(self.a).sha256, neu.ergebnis(self.a).arbeiter), (digest, wer))
            self.assertEqual(neu.offene(), ())

    def test_geaenderter_inhalt_unter_gleicher_kennung_ist_konflikt(self):
        self.s.registriere(self.a)
        with self.assertRaises(ValueError):
            self.s.registriere(replace(self.a, daten=b"anders"))
        self.assertEqual(self.s.offene(), (self.a,))
        self.s.registriere(self.a)  # Validierungsfehler sperrt nicht die ganze Instanz.

    def test_volles_register_bewahrt_auch_offene_arbeit(self):
        for name in ("eins", "zwei"):
            self.s.registriere(Hashauftrag(name, b"x"))
        with self.assertRaises(OverflowError):
            self.s.registriere(self.a)
        self.s.close()
        with Arbeitsspeicher(self.pfad, 2) as neu:
            self.assertEqual(len(neu.offene()), 2)
            with self.assertRaises(OverflowError):
                neu.registriere(self.a)

    def test_alte_epoche_darf_auch_ueber_bestehende_verbindung_nicht_schreiben(self):
        self.s.registriere(self.a)
        alt = self.s.epoche
        db = verbinde(self.pfad)
        self.addCleanup(db.close)
        self.s.close()
        with Arbeitsspeicher(self.pfad, 2) as neu:
            with self.assertRaises(ValueError):
                bearbeite(db, alt, "1" * 32, self.a.kennung)
            self.assertIsNone(neu.ergebnis(self.a))
            bearbeite(db, neu.epoche, "2" * 32, self.a.kennung)
            self.assertEqual(neu.ergebnis(self.a).arbeiter, "2" * 32)

    def test_wiederholter_speichervorgang_erhaelt_urspruenglichen_arbeiter(self):
        self.s.registriere(self.a)
        db = verbinde(self.pfad)
        try:
            erst = bearbeite(db, self.s.epoche, "1" * 32, self.a.kennung)
            nochmal = bearbeite(db, self.s.epoche, "2" * 32, self.a.kennung)
            self.assertEqual(erst, nochmal)
            self.assertEqual(db.execute("SELECT count(*) FROM arbeit").fetchone()[0], 1)
        finally:
            db.close()

    def test_zweiter_supervisor_erhaelt_keinen_besitz(self):
        with self.assertRaises(RuntimeError):
            Arbeitsspeicher(self.pfad, 2)
        self.s.registriere(self.a)

    def test_beschaedigte_datei_wird_nicht_ersetzt(self):
        self.s.close()
        self.pfad.write_bytes(b"kaputt")
        with self.assertRaises(sqlite3.DatabaseError):
            Arbeitsspeicher(self.pfad, 2)
        self.assertEqual(self.pfad.read_bytes(), b"kaputt")

    def test_falsches_ergebnis_und_schema_werden_abgewiesen(self):
        self.s.registriere(self.a)
        self.s.close()
        db = sqlite3.connect(self.pfad)
        try:
            db.execute("UPDATE arbeit SET ergebnis='falsch',arbeiter=?", ("1" * 32,))
            db.commit()
            with self.assertRaises(ValueError):
                Arbeitsspeicher(self.pfad, 2)
            db.execute("PRAGMA user_version=99")
            with self.assertRaises(ValueError):
                Arbeitsspeicher(self.pfad, 2)
        finally:
            db.close()

    def test_lesefehler_ist_keine_erlaubnis_zum_wiederholen(self):
        self.s.registriere(self.a)
        self.s._db.execute("DROP TABLE arbeit")
        with self.assertRaises(sqlite3.OperationalError):
            self.s.ergebnis(self.a)
        with self.assertRaises(RuntimeError):
            self.s.registriere(self.a)

    def test_schreibfehler_sperrt_instanz(self):
        self.s._db.execute("PRAGMA query_only=ON")
        with self.assertRaises(sqlite3.OperationalError):
            self.s.registriere(self.a)
        with self.assertRaises(RuntimeError):
            self.s.registriere(self.a)

    def test_ungueltige_groesse_und_kennung_haben_keine_wirkung(self):
        for a in (Hashauftrag("", b"a"), Hashauftrag("../fremd", b"a"),
                  Hashauftrag("x", bytearray(b"a")), Hashauftrag("x", b"a" * (1024 * 1024 + 1))):
            with self.assertRaises(ValueError):
                self.s.registriere(a)
        self.assertEqual(self.s.offene(), ())

    def test_verschwundene_datei_wird_beim_arbeiter_nicht_neu_angelegt(self):
        pfad = Path(self.tmp.name) / "fehlend.sqlite3"
        with self.assertRaises(sqlite3.OperationalError):
            verbinde(pfad)
        self.assertFalse(pfad.exists())


class WiederanlaufTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pfad = Path(self.tmp.name) / "arbeit.sqlite3"
        self.l = Wiederanlauf(self.pfad, antwortfrist=.2)
        self.addCleanup(self.l.close)
        self.a = Hashauftrag("stabile-kennung", b"ein wirklich bearbeiteter Auftrag" * 200)

    def test_bereitschaft_und_ergebnis_stammen_vom_eigenen_prozess(self):
        self.assertTrue(self.l.primaer.bereit)
        self.assertGreater(self.l.primaer.prozess.pid, 0)
        e, b = self.l.ausfuehren(self.a)
        self.assertEqual(e.sha256, hashlib.sha256(self.a.daten).hexdigest())
        self.assertEqual(e.arbeiter, self.l.primaer.instanz)
        self.assertEqual([x["status"] for x in b["versuche"]], ["ERLEDIGT"])

    def test_abriss_vor_commit_rollt_zurueck_und_reserve_uebernimmt(self):
        alt = self.l.primaer
        e, b = self.l.ausfuehren(self.a, "vor_commit")
        self.assertEqual(alt.exitcode, 74)
        self.assertTrue(alt._geschlossen)
        self.assertTrue(b["uebernahme_nach_bestaetigtem_ende"])
        self.assertEqual([x["status"] for x in b["versuche"]], ["AUSFALL", "ERLEDIGT"])
        self.assertEqual(e.arbeiter, self.l.reserve.instanz)

    def test_abriss_nach_commit_wird_ohne_ersatzarbeit_geklaert(self):
        alt = self.l.primaer
        e, b = self.l.ausfuehren(self.a, "nach_commit")
        self.assertEqual((alt.exitcode, e.arbeiter), (75, alt.instanz))
        self.assertTrue(b["aus_speicher"])
        self.assertEqual(len(b["versuche"]), 1)
        self.assertIsNone(self.l.reserve)

    def test_haenger_wird_vor_uebernahme_getoetet_und_join_bestaetigt(self):
        alt = self.l.primaer
        e, b = self.l.ausfuehren(self.a, "haengt")
        self.assertLess(alt.exitcode, 0)
        self.assertTrue(alt._geschlossen)
        self.assertEqual(b["versuche"][0]["grund"], "Antwortfrist überschritten")
        self.assertTrue(b["versuche"][0]["beendet_bestaetigt"])
        self.assertEqual(e.arbeiter, self.l.reserve.instanz)
        self.assertEqual(self.l.speicher.offene(), ())

    def test_vorbereitete_reserve_startet_nicht_erst_nach_ausfall(self):
        self.l.vorbereiten()
        instanz = self.l.reserve.instanz
        e, b = self.l.ausfuehren(self.a, "vor_commit")
        self.assertEqual(e.arbeiter, instanz)
        self.assertEqual(b["reserve_start_nach_fehler_ms"], 0)
        self.assertGreaterEqual(b["reserve_bereit_bis_einsatz_ms"], 0)

    def test_keine_uebernahme_wenn_prozessende_nicht_bestaetigt(self):
        alt = self.l.primaer
        with patch.object(alt, "stop", side_effect=RuntimeError("Ende unbestätigt")):
            with self.assertRaisesRegex(RuntimeError, "Ende unbestätigt"):
                self.l.ausfuehren(self.a, "vor_commit")
        self.assertIsNone(self.l.reserve)
        with self.assertRaisesRegex(RuntimeError, "gesperrt"):
            self.l.ausfuehren(replace(self.a, kennung="keine-neue-arbeit"))
        alt.stop()
        self.assertIsNone(self.l.speicher.ergebnis(self.a))

    def test_auch_die_reserve_kann_ausfallen_ohne_retry_schleife(self):
        with self.assertRaisesRegex(Arbeiterfehler, "Beide Versuche"):
            self.l.ausfuehren(self.a, "vor_commit", "vor_commit")
        self.assertIsNone(self.l.primaer)
        self.assertIsNone(self.l.reserve)
        self.assertEqual(self.l.speicher.offene(), (self.a,))
        self.l.primaer_neustarten()
        self.assertEqual(self.l.ausfuehren(self.a)[0].sha256, hashlib.sha256(self.a.daten).hexdigest())

    def test_neustart_erzeugt_neue_instanz_und_folgeauftrag_laeuft(self):
        alt = self.l.primaer.instanz
        self.l.ausfuehren(self.a, "nach_commit")
        self.l.primaer_neustarten()
        self.assertNotEqual(self.l.primaer.instanz, alt)
        neu = replace(self.a, kennung="folgeauftrag")
        self.assertEqual(self.l.ausfuehren(neu)[0].arbeiter, self.l.primaer.instanz)

    def test_doppelte_anfrage_startet_auch_nach_supervisor_neustart_nichts(self):
        e, _ = self.l.ausfuehren(self.a)
        for _ in range(3):
            nochmal, b = self.l.ausfuehren(self.a)
            self.assertEqual(nochmal, e)
            self.assertEqual(b["versuche"], [])
        self.l.close()
        with Wiederanlauf(self.pfad) as neu:
            nochmal, b = neu.ausfuehren(self.a)
            self.assertEqual(nochmal, e)
            self.assertEqual(b["versuche"], [])

    def test_widerspruechliche_kennung_kommt_nicht_zum_arbeiter(self):
        self.l.ausfuehren(self.a)
        vorher = self.l.primaer.folge
        with self.assertRaises(ValueError):
            self.l.ausfuehren(replace(self.a, daten=b"anders"))
        self.assertEqual(self.l.primaer.folge, vorher)

    def test_stale_antwort_wird_abgewiesen_und_dauerhafter_stand_geprueft(self):
        alt = self.l.primaer
        # Simuliert eine verzögerte Antwort einer anderen Arbeiterinstanz.
        with patch.object(alt, "_warte", return_value=dict(art="ERGEBNIS", instanz="alt", folge=1)):
            e, b = self.l.ausfuehren(self.a)
        self.assertTrue(alt._geschlossen)
        self.assertEqual(e.sha256, hashlib.sha256(self.a.daten).hexdigest())
        self.assertEqual(b["versuche"][0]["status"], "AUSFALL")

    def test_beendete_reserve_gilt_nicht_als_bereit(self):
        self.l.vorbereiten()
        self.l.reserve.stop()
        with self.assertRaisesRegex(Arbeiterfehler, "Beide Versuche"):
            self.l.ausfuehren(self.a, "vor_commit")
        self.assertEqual(self.l.speicher.offene(), (self.a,))

    def test_alter_lebender_arbeiter_wird_durch_neue_epoche_ausgesperrt(self):
        self.l.speicher.registriere(self.a)
        alt = self.l.primaer
        self.l.speicher.close()  # Simuliert Besitzverlust bei noch lebendem Kind.
        with Arbeitsspeicher(self.pfad) as neu:
            with self.assertRaises(Arbeiterfehler):
                alt.anfrage("ARBEIT", .5, kennung=self.a.kennung, stoerung="keine")
            self.assertIsNone(neu.ergebnis(self.a))
        alt.stop()

    def test_ungueltige_fristen_starten_keine_laufzeit(self):
        for frist in (0, -1, math.nan, math.inf, True, "1"):
            with self.assertRaises(ValueError):
                Wiederanlauf(self.pfad, antwortfrist=frist)

    def test_close_beendet_beide_eigenen_prozesse(self):
        self.l.vorbereiten()
        primaer, reserve = self.l.primaer, self.l.reserve
        self.l.close()
        self.assertTrue(primaer._geschlossen and reserve._geschlossen)
        self.assertIsNotNone(primaer.exitcode)
        self.assertIsNotNone(reserve.exitcode)
        with self.assertRaises(RuntimeError):
            self.l.ausfuehren(self.a)


class LaborTests(unittest.TestCase):
    def test_echter_messlauf_und_aggregation_ohne_geschwindigkeitsbehauptung(self):
        daten = [durchlauf("vor_commit", False), durchlauf("nach_commit", True)]
        for z in daten:
            self.assertTrue(z["wiederholung_ohne_arbeit"])
            self.assertTrue(z["supervisor_neustart_ohne_doppelarbeit"])
            self.assertGreater(z["primaer_neustart_ms"], 0)
            self.assertGreater(z["auftrag"]["gesamt_ms"], 0)
            self.assertGreaterEqual(z["inklusive_vorbereitung_ms"], z["auftrag"]["gesamt_ms"])
        gruppen = zusammenfassung(daten)
        self.assertEqual(len(gruppen), 2)
        for z in gruppen:
            self.assertEqual(z["anzahl"], 1)
            self.assertEqual(z["werte"]["gesamt_ms"]["min"], z["werte"]["gesamt_ms"]["max"])
        json.dumps(daten, allow_nan=False)


if __name__ == "__main__":
    unittest.main()

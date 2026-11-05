import tempfile
import unittest
from pathlib import Path

from versuch import Gedaechtnis, beispielspur, durchlauf, lies_spur


class VersuchsTests(unittest.TestCase):
    def test_verlauf_wechselt_bei_gleichem_eingang(self):
        entscheidungen = []
        def erfasse(takt, zustand, anteil, beleg, warnung):
            if zustand == "SCHWACH":
                entscheidungen.append((takt, warnung))
        durchlauf(beispielspur(), "Lernversuch", Gedaechtnis(), beobachter=erfasse)
        warnungen = [takt for takt, warnt in entscheidungen if warnt]
        self.assertEqual(warnungen, list(range(34, 136, 6)))
        self.assertEqual(entscheidungen[-1][1], False)

    def test_gleicher_verlauf_bis_zur_entscheidung(self):
        vorgeschichte = ["SCHWACH", "AUSFALL"] * 8 + ["SCHWACH"]
        def protokoll(ende):
            log = []
            durchlauf(vorgeschichte + ende, "Test", Gedaechtnis(),
                      beobachter=lambda *eintrag: log.append(eintrag))
            return log[:len(vorgeschichte)]
        a = protokoll(["OK"] * 10)
        b = protokoll(["AUSFALL"] * 10)
        self.assertEqual(a, b)
        self.assertTrue(a[-1][-1])

    def test_unbenutzter_beleg_halbiert_sich(self):
        g = Gedaechtnis(4)
        g.beobachte("SCHWACH", "AUSFALL")
        for _ in range(4):
            g.beobachte("OK", "OK")
        anteil, beleg = g.schaetze("SCHWACH")
        self.assertEqual(anteil, 1)
        self.assertAlmostEqual(beleg, 0.5)
        self.assertEqual(g.schaetze("AUSFALL"), (0.0, 0))

    def test_abrufen_verstaerkt_keine_vermutung(self):
        g = Gedaechtnis()
        g.beobachte("SCHWACH", "OK")
        for _ in range(100):
            self.assertEqual(g.schaetze("SCHWACH"), (0.0, 1))

    def test_unbenutztes_muster_loest_keine_warnung_mehr_aus(self):
        spur = ["SCHWACH", "AUSFALL"] * 10 + ["OK"] * 120 + ["SCHWACH"]
        mit = durchlauf(spur, "mit", Gedaechtnis())
        ohne = durchlauf(spur, "ohne", Gedaechtnis(None))
        self.assertEqual(mit.offen, 0)
        self.assertEqual(ohne.offen, 1)

    def test_sofortmeldung_erreicht_jeden_ausfallbeginn(self):
        spur = ["AUSFALL", "AUSFALL", "OK", "AUSFALL"]
        for g, alle in [(None, True), (None, False), (Gedaechtnis(), False)]:
            b = durchlauf(spur, "Test", g, alle_senden=alle)
            self.assertEqual(b.sofortmeldungen, 2)
            self.assertEqual(b.treffer + b.ohne_vorwarnung + b.beginn_unbekannt, 2)
            self.assertEqual(b.nachrichten, 4 if alle else 3)
            self.assertEqual(b.nutzbytes, 5 * b.nachrichten)

    def test_feste_regel_zaehlt_auch_die_letzte_offene_warnung(self):
        b = durchlauf(["SCHWACH", "AUSFALL", "SCHWACH", "OK", "SCHWACH"],
                      "Feste Regel", feste_warnregel=True)
        self.assertEqual((b.treffer, b.fehlalarme, b.offen), (1, 1, 1))
        self.assertEqual(b.sofortmeldungen, 1)
        self.assertEqual(b.nachrichten, 8)

    def test_csv_liest_spur_und_weist_luecken_zurueck(self):
        with tempfile.TemporaryDirectory() as verzeichnis:
            datei = Path(verzeichnis, "spur.csv")
            datei.write_text("zustand\nOK\nSCHWACH\nAUSFALL\n", encoding="utf-8")
            self.assertEqual(lies_spur(datei), ["OK", "SCHWACH", "AUSFALL"])
            for ungueltig in ("status\nOK\nOK", "zustand\nOK", "zustand\nOK\n\nOK",
                              "zustand\nOK\n00", "zustand\nOK,OK"):
                with self.subTest(ungueltig=ungueltig):
                    datei.write_text(ungueltig, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        lies_spur(datei)


if __name__ == "__main__":
    unittest.main()

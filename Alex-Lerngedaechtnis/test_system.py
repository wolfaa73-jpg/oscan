import copy
import unittest

from kern import MAX_TAKT
from labor import FAMILIEN, generiere
from systemkern import Arbeitsprozesse, Systemkern, VERFAHREN, lernknoten
from systemlabor import anpassung, auswerten, paarvergleich, wechselspur
from versuch import durchlauf


class SystemTests(unittest.TestCase):
    def test_vorwarnung_bereitet_genau_naechsten_auftrag_vor(self):
        s = Systemkern("fest")
        a = s.schritt(1, "SCHWACH")
        b = s.schritt(2, "AUSFALL")
        self.assertEqual((a.ziel, a.reserve_fuer), ("PRIMAER", 2))
        self.assertEqual((b.ziel, b.reserve_fuer, b.reflex), ("RESERVE", 3, True))

    def test_reflex_sperrt_primaer_auch_ohne_lernen(self):
        for v in VERFAHREN:
            s = Systemkern(v)
            a, b = s.schritt(1, "AUSFALL"), s.schritt(2, "AUSFALL")
            self.assertEqual((a.ziel, b.ziel), ("WARTEN", "RESERVE"))
            self.assertTrue(a.reflex and b.reflex)

    def test_luecken_und_unbekannt_verwerfen_reservierungen(self):
        for zwischen in (None, "LUECKE"):
            s = Systemkern("fest")
            s.schritt(1, "SCHWACH")
            if zwischen is None:
                self.assertEqual(s.schritt(2, None).ziel, "WARTEN")
            self.assertEqual(s.schritt(3, "AUSFALL").ziel, "WARTEN")
        s = Systemkern("erbe")
        s.schritt(1, "SCHWACH")
        s.schritt(2, None)
        s.schritt(3, "AUSFALL")
        self.assertEqual(sum(map(sum, (z.values() for z in s.knoten.gedaechtnis.gewichte.values()))), 0)

    def test_ungueltiges_ereignis_veraendert_nichts(self):
        s = Systemkern("erbe")
        s.schritt(1, "SCHWACH")
        vorher = copy.deepcopy(s.__dict__)
        for t, z in ((1, "OK"), (0, "OK"), (True, "OK"), (2, "NEU"), (MAX_TAKT + 1, "OK")):
            with self.assertRaises(ValueError):
                s.schritt(t, z)
            self.assertEqual((s.takt, s.reserve_fuer), (vorher["takt"], vorher["reserve_fuer"]))
            self.assertEqual(s.knoten.gedaechtnis.gewichte, vorher["knoten"].gedaechtnis.gewichte)

    def test_zaehlerende_reserviert_nicht_jenseits_des_formats(self):
        self.assertIsNone(Systemkern("fest").schritt(MAX_TAKT, "SCHWACH").reserve_fuer)

    def test_keine_kenntnis_der_zukunft(self):
        for v in VERFAHREN:
            anfang = ["OK", "SCHWACH", "AUSFALL", "OK"] * 8
            a = auswerten(anfang + ["OK"] * 12, v, True)["verlauf"]
            b = auswerten(anfang + ["AUSFALL"] * 12, v, True)["verlauf"]
            self.assertEqual(a[:len(anfang)], b[:len(anfang)])

    def test_neue_laufzeit_behaelt_keinen_alten_reserveplan(self):
        alt = Systemkern("fest")
        alt.schritt(1, "SCHWACH")
        self.assertEqual(Systemkern("fest").schritt(2, "AUSFALL").ziel, "WARTEN")

    def test_zwei_echte_arbeiter_liefern_passende_auftraege(self):
        s = Systemkern("fest")
        with Arbeitsprozesse() as a:
            self.assertIsNotNone(a.ausfuehren(s.schritt(1, "SCHWACH")))
            self.assertIsNotNone(a.ausfuehren(s.schritt(2, "AUSFALL")))
            self.assertIsNone(a.ausfuehren(s.schritt(4, "AUSFALL")))


class AuswertungsTests(unittest.TestCase):
    def test_handgerechnete_bilanz(self):
        r = auswerten(["SCHWACH", "AUSFALL", "OK", "SCHWACH", "OK", "SCHWACH"], "fest")
        for feld, erwartet in dict(treffer=1, fehlalarme=1, verpasst=0, offen=1,
                                   reserve_runden=3, reserve_genutzt=1, reserve_unnoetig=2,
                                   primaer=5, ausgesetzt=0, vorwarnzeit_takte=1,
                                   praezision=.5, recall=1).items():
            self.assertEqual(r[feld], erwartet, feld)

    def test_unbekannt_ist_weder_treffer_noch_fehlalarm(self):
        r = auswerten([(1, "SCHWACH"), (3, "AUSFALL"), (4, "SCHWACH"),
                       (5, None), (6, "AUSFALL"), (7, "SCHWACH")], "fest")
        self.assertEqual((r["treffer"], r["fehlalarme"], r["offen"], r["beginn_unbekannt"]), (0, 0, 3, 2))
        self.assertEqual(r["fehlende_takte"], 1)

    def test_ohne_ereignisse_keine_erfundene_guete(self):
        r = auswerten(["OK"] * 10, "erbe")
        self.assertIsNone(r["recall"])
        self.assertIsNone(r["praezision"])
        self.assertIsNone(r["vorwarnzeit_takte"])
        with self.assertRaises(ValueError):
            auswerten([], "fest")

    def test_warnbilanz_passt_zum_vorhandenen_labor(self):
        for f in FAMILIEN:
            spur = generiere(f, 1981)
            for v in VERFAHREN:
                r = auswerten(spur, v, True)
                k = lernknoten(v)
                b = durchlauf(spur, v, k.gedaechtnis, feste_warnregel=k.feste_warnregel)
                self.assertEqual((r["treffer"], r["fehlalarme"], r["verpasst"], r["offen"]),
                                 (b.treffer, b.fehlalarme, b.ohne_vorwarnung, b.offen))
                self.assertEqual(r["primaer"] + r["reserve_genutzt"] + r["ausgesetzt"], len(spur))
                self.assertEqual(r["ausfallbeginne"], r["treffer"] + r["verpasst"])
                for p in r["verlauf"]:
                    self.assertFalse(p["zustand"] == "AUSFALL" and p["ziel"] == "PRIMAER")
                    self.assertIn(p["reserve_fuer"], (None, p["takt"] + 1))

    def test_anpassung_zeigt_auch_ungeeignete_regeln(self):
        fest = anpassung("fest")
        self.assertEqual(fest[0]["bestaetigt_nach_signalen"], 3)
        self.assertIsNone(fest[1]["bestaetigt_nach_signalen"])
        self.assertTrue(all(z["bestaetigt_nach_signalen"] is not None for z in anpassung("erbe")))

    def test_paarvergleich_reproduzierbar_und_vorzeichen(self):
        zeilen = [dict(familie="Test", seed=s, verfahren=v, beobachtungen=100,
                       reserve_runden=10 if v == "fest" else 5, ausgesetzt=1)
                  for s in range(4) for v in VERFAHREN]
        a = paarvergleich(zeilen, 5, 100)
        self.assertEqual(a, paarvergleich(zeilen, 5, 100))
        self.assertTrue(all(z["delta_pro_1000"] == -50 and z["intervall95"] == [-50, -50] for z in a))


if __name__ == "__main__":
    unittest.main()

"""Künstliche Gerätezeilen, Zählerorakel und absichtliche Schäden; keine Aufnahme nötig."""
import contextlib
import csv
import io
import json
import random
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import koerper
import pruefung24h as p
from kostenlabor import rasterzaehler
import test_labor


class Protokoll24Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.csv = Path(self.tmp.name) / "synthetisch.csv"
        self.g = koerper.ERKUNDUNG
        # Bis über den ersten Flashtermin; jede Art hat schwache/kritische Takte.
        roh = ([(410, 300000, 60)] * 5 + [(520, 300000, 60)] * 3
               + [(610, 300000, 60)] * 2 + [(410, 40000, 60)] * 3
               + [(410, 12000, 60)] * 2 + [(410, 300000, 30000)] * 3
               + [(410, 300000, 250000)] * 2) * 31
        geraet = test_labor.KoerperTests.geraetezeilen(roh, self.g, "startwert", blick=60)
        self.rows = [dict(koerper.lies_koerperzeile(z.encode()), zeit_ms=i*1000)
                     for i, z in enumerate(geraet, 1)]
        self.meta = dict(regel="startwert", blick=60, intervall_ms=1000,
                         sichern_alle=600, fortsetzung=None, grenzen=asdict(self.g))
        self.schreibe()

    def schreibe(self):
        with self.csv.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=koerper.KOPF)
            w.writeheader()
            w.writerows(self.rows)
        self.csv.with_suffix(".json").write_text(json.dumps(self.meta))

    def test_synthetische_geraetezeilen_bestehen_original_und_neuen_pruefer(self):
        self.assertEqual(koerper.pruefen(self.csv)[1], self.rows)
        self.assertEqual(p.vorpruefung(self.csv)[1], self.rows)

    def test_alle_warnabweichungen_werden_gezeigt(self):
        for i in (9, 599):
            self.rows[i]["vorwarnung"] ^= 1
        self.schreibe()
        with self.assertRaises(p.Prueffehler) as caught:
            p.vorpruefung(self.csv)
        self.assertEqual([r[0] for r in caught.exception.abweichungen], [10, 600])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(p.main([str(self.csv)]), 2)
        self.assertIn("Geraeteabweichungen: 2", out.getvalue())
        self.assertNotIn("## H=", out.getvalue())

    def test_fehlender_takt_auch_am_sicherpunkt_wird_nicht_ueberbrueckt(self):
        for index in (0, 49, 599):
            with self.subTest(index=index):
                kaputt = self.rows[:index] + self.rows[index+1:]
                with self.csv.open("w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=koerper.KOPF)
                    w.writeheader()
                    w.writerows(kaputt)
                with self.assertRaisesRegex(p.Prueffehler, "TAKTFOLGE"):
                    p.vorpruefung(self.csv)
                self.schreibe()

    def test_laden_luecke_ist_fuer_diesen_frischen_lauf_unzulaessig(self):
        for w in self.rows[599:]:
            w["takt"] += 1
        self.schreibe()
        with self.assertRaisesRegex(p.Prueffehler, "TAKTFOLGE"):
            p.vorpruefung(self.csv)

    def test_fortsetzungsmetadaten_nicht_nachladen(self):
        self.meta["fortsetzung"] = "andere.csv"
        self.schreibe()
        with self.assertRaisesRegex(p.Prueffehler, "KEIN_FRISCHER"):
            p.vorpruefung(self.csv)

    def test_originalpruefer_ist_verpflichtend(self):
        with patch.object(koerper, "pruefen", side_effect=ValueError("absichtlich")):
            with self.assertRaisesRegex(p.Prueffehler, "GERAET_PYTHON"):
                p.vorpruefung(self.csv)

    def test_falsche_stufe_und_sofortmeldung(self):
        self.rows[3]["zustand"] = "AUSFALL"
        self.rows[7]["sofort"] ^= 1
        self.schreibe()
        with self.assertRaises(p.Prueffehler) as caught:
            p.vorpruefung(self.csv)
        self.assertEqual([r[0] for r in caught.exception.abweichungen], [4, 8])

    def test_keine_metadaten_oder_privaten_pfade_in_fehlerausgabe(self):
        self.meta["regel"] = "INTERNE_MARKIERUNG"
        self.schreibe()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(p.main([str(self.csv)]), 2)
        self.assertNotIn("INTERNE_MARKIERUNG", out.getvalue())
        self.assertNotIn(self.tmp.name, out.getvalue())

    def test_abbruchdatei_verhindert_auswertung(self):
        self.csv.with_name(self.csv.stem + ".abbruch.txt").write_text("synthetischer Abbruch")
        with self.assertRaisesRegex(p.Prueffehler, "ABBRUCHDATEI"):
            p.vorpruefung(self.csv)

    def test_unerwarteter_horizont_und_sicherabstand_werden_nicht_angepasst(self):
        for feld, falsch in (("blick", 30), ("sichern_alle", 0), ("intervall_ms", 500)):
            alt = self.meta[feld]
            self.meta[feld] = falsch
            self.schreibe()
            with self.assertRaisesRegex(p.Prueffehler, "METADATEN"):
                p.vorpruefung(self.csv)
            self.meta[feld] = alt
        self.schreibe()

    def test_boolean_in_json_ersetzt_keine_zahl(self):
        self.meta["blick"] = True
        self.schreibe()
        with self.assertRaisesRegex(p.Prueffehler, "METADATEN"):
            p.vorpruefung(self.csv)

    def test_unvollstaendige_aufnahme_bekommt_keine_guetetabelle(self):
        with self.assertRaisesRegex(p.Prueffehler, "86400"):
            p.druckbericht(self.csv)

    def test_modelle_kausal_und_gegen_langsame_referenz(self):
        words = [w["zustand"] for w in self.rows[:100]]
        for h in (1, 15, 17):
            a = p.vorhersagen(words, "SCHWACH", "AUSFALL", 30, h)
            b = p.vorhersagen(words, "SCHWACH", "AUSFALL", 30, h, True)
            self.assertEqual(a, b)
            self.assertEqual(p.vorhersagen(words[:55], "SCHWACH", "AUSFALL", 30, h),
                             {k: v[:55] for k, v in a.items()})

    def test_speichertermine_werden_ausgewiesen_und_nicht_entfernt(self):
        rows, save = p.auswertung(self.rows, self.g)
        self.assertEqual({z["takt"] for z in save}, {600, 601})
        self.assertEqual(len(save), 2*2*2*len(p.METHODEN))
        self.assertEqual(len(rows), 2*2*7*len(p.METHODEN))
        for z in rows:
            self.assertEqual(z["takte"], len(self.rows)-z["horizont"])
        # Grober Standard ist genau die bei H60 aufgezeichnete Gerätemeldung.
        grobe = p.vorhersagen([w["zustand"] for w in self.rows], "SCHWACH", "AUSFALL", 60, 1)
        self.assertEqual(grobe["Startwert h6/.6"], [bool(w["vorwarnung"]) for w in self.rows])
        self.assertEqual(len(p.hypothesen(rows)), 5)

    def test_handzaehlung_beruecksichtigt_ok_warnungen_und_randfenster(self):
        words = ["OK", "SCHWACH", "AUSFALL", "AUSFALL", "OK", "SCHWACH", "AUSFALL", "OK", "OK"]
        warn = [True, False, True, True, True, True, False, False, False]
        z = p.zaehlen(words, warn, 2)
        self.assertEqual((z["takte"], z["auswertbar"], z["warntakte"], z["treffertakte"], z["zieltakte"]),
                         (7, 4, 3, 3, 4))
        self.assertEqual((z["phasen"], z["vorgewarnt"], z["verpasst"]), (2, 2, 0))
        self.assertEqual((z["kosten_takt_r10"], z["kosten_phase_r10"]), (10, 0))
        high = p.zaehlen(words, warn, 2, True)
        self.assertEqual(high["auswertbar"], 2)
        self.assertEqual(high["phasen"], z["phasen"])

    def test_zaehler_unabhaengig_gegen_kostenlabor_auf_100_zufallsspuren(self):
        rng = random.Random(8675309)
        for _ in range(100):
            words = [rng.choice(("OK", "SCHWACH", "AUSFALL")) for _ in range(80)]
            warn = [bool(rng.randrange(2)) for _ in words]
            h = rng.randint(1, 20)
            a = p.zaehlen(words, warn, h)
            b = rasterzaehler(words, [1 if w else -1 for w in warn], h, (.6,))[0]
            for k, v in b.items():
                if k != "schwelle":
                    self.assertEqual(a[k], v, k)

    def test_nullnenner_bleiben_unbekannt_kein_erfundener_erfolg(self):
        rows, _ = p.auswertung([dict(w, zustand="OK", temp_dc=410, heap=300000, luecke_us=60)
                               for w in self.rows], self.g)
        hs = p.hypothesen(rows)
        self.assertTrue(all(h["status"] == "NICHT_PRUEFBAR" for h in hs))
        never = next(z for z in rows if z["methode"] == "Nie warnen")
        self.assertIsNone(never["trefferquote"])


if __name__ == "__main__":
    unittest.main()

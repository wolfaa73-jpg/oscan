"""Unabhängige Orakel für Parameter, Rasterzählung und eingefrorene Kostenwahl."""
import copy
import csv
import io
import json
import math
import random
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import kostenlabor as k
import signallabor as s
from vokabular import Wortgedaechtnis, warnungen


def oracle(woerter, scores, h, schwelle):
    """Absichtlich ohne Histogramme, binnen_vor oder andere Produktionszähler."""
    ende = len(woerter) - h
    takte = [t for t in range(ende) if woerter[t] != "AUSFALL"]
    gewarnt = [t for t in takte if scores[t] >= schwelle]
    ziel = lambda t: "AUSFALL" in woerter[t + 1:t + h + 1]
    beginne = [b for b in range(h, ende) if woerter[b] == "AUSFALL" and woerter[b - 1] != "AUSFALL"]
    vorgewarnt = sum(any(woerter[t] != "AUSFALL" and scores[t] >= schwelle
                        for t in range(b - h, b)) for b in beginne)
    treffer, zieltakte = sum(map(ziel, gewarnt)), sum(map(ziel, takte))
    return dict(schwelle=schwelle, takte=ende, auswertbar=len(takte), warntakte=len(gewarnt),
                treffertakte=treffer, zieltakte=zieltakte, fehlwarntakte=len(gewarnt) - treffer,
                verpasste_zieltakte=zieltakte - treffer, phasen=len(beginne),
                vorgewarnt=vorgewarnt, verpasst=len(beginne) - vorgewarnt)


def zeile(config, **werte):
    return dict(config, **dict({f: 0 for f in k.FELDER}, **werte))


def auswahl_fixture():
    rows = [dict(signal=signal, **zeile(c)) for signal, _, _ in s.SIGNALE for c in k.defaults()]
    return dict(schema=1, tiebreakversion=1, quellhashes={"fixture": "fest"},
                einstellungen=s.asdict(s.Einstellungen(takte=90)),
                kontrolle=dict(seedstart=900000, anzahl=1), auswahl=list(k.auswahlzeilen(rows)))


class ParameterTests(unittest.TestCase):
    def test_halbwertszeit_sechs_stimmt_mit_bisherigem_startwert_ueberein(self):
        rng = random.Random(91)
        for signal, hoch, krit in s.SIGNALE:
            woerterbuch = ("OK", hoch, krit)
            folge = [rng.choice(woerterbuch) for _ in range(240)]
            alt = Wortgedaechtnis(woerterbuch, ((hoch, krit),), startwert=True)
            neu = k.ParameterGedaechtnis(woerterbuch, ((hoch, krit),), 6)
            vorher = None
            for wort in folge:
                alt.beobachte(vorher, wort)
                neu.beobachte(vorher, wort)
                self.assertEqual(neu.gewichte, alt.gewichte)
                self.assertEqual(neu.erbe, alt.erbe)
                vorher = wort
            scores = k.wahrscheinlichkeiten(folge, hoch, krit, 6)
            erwartet = warnungen(folge, Wortgedaechtnis(woerterbuch, ((hoch, krit),), startwert=True), 30)
            self.assertEqual([p >= .6 for p in scores], erwartet, signal)

    def test_nur_erbe_altert_mit_neuem_parameter_und_nur_beim_ausgang(self):
        modelle = [k.ParameterGedaechtnis(s.GROBWOERTER, s.GROBERBE, h) for h in (None, 1, 24)]
        for m in modelle:
            m.beobachte(None, "SCHWACH")
            for _ in range(7):
                m.beobachte("SCHWACH", "SCHWACH")
            self.assertEqual(m.erbe["SCHWACH"]["AUSFALL"], 3)
            m.beobachte("SCHWACH", "OK")
        self.assertEqual([m.faktor for m in modelle], [0.5 ** (1 / 6)] * 3)
        self.assertEqual(modelle[0].gewichte, modelle[1].gewichte)
        self.assertEqual(modelle[1].gewichte, modelle[2].gewichte)
        self.assertEqual(modelle[0].erbe["SCHWACH"]["AUSFALL"], 3)
        self.assertEqual(modelle[1].erbe["SCHWACH"]["AUSFALL"], 1.5)
        self.assertAlmostEqual(modelle[2].erbe["SCHWACH"]["AUSFALL"], 3 * 0.5 ** (1 / 24))

    def test_ungueltige_halbwertszeiten_und_horizonte(self):
        for h in (-1, 0, True, math.nan, math.inf):
            with self.subTest(h=h), self.assertRaises(ValueError):
                k.ParameterGedaechtnis(s.GROBWOERTER, s.GROBERBE, h)
        for referenz in (False, True):
            m = k.ParameterGedaechtnis(s.GROBWOERTER, s.GROBERBE, 6, referenz)
            for h in (-1, 0, 601, True, 1.0, None):
                with self.subTest(h=h, referenz=referenz), self.assertRaises(ValueError):
                    m.kritisch_binnen("OK", h)

    def test_jede_rastergrenze_nutzt_die_originalrechnung(self):
        m = k.ParameterGedaechtnis(s.GROBWOERTER, s.GROBERBE, 6)
        # Auch andere Grenzen als 0,6 müssen nahe Rundungswechseln abgesichert sein.
        for grenze in k.SCHWELLEN:
            for delta in (-5e-11, 0, 5e-11):
                with mock.patch.object(s.SchnellesDreiergedaechtnis, "kritisch_binnen", return_value=grenze + delta), \
                        mock.patch.object(Wortgedaechtnis, "kritisch_binnen", return_value=.123456) as original:
                    self.assertEqual(m.kritisch_binnen("SCHWACH", 30), .123456)
                    original.assert_called_once()
        with mock.patch.object(s.SchnellesDreiergedaechtnis, "kritisch_binnen", return_value=.371), \
                mock.patch.object(Wortgedaechtnis, "kritisch_binnen", side_effect=AssertionError("unnötige Referenz")):
            self.assertEqual(m.kritisch_binnen("SCHWACH", 30), .371)

    def test_scores_sind_kausal_und_referenzgleiche_warnungen(self):
        rng = random.Random(51)
        woerter = [rng.choice(s.GROBWOERTER) for _ in range(180)]
        for h in (None, 1, 6, 24):
            scores = k.wahrscheinlichkeiten(woerter, "SCHWACH", "AUSFALL", h)
            kurz = k.wahrscheinlichkeiten(woerter[:100], "SCHWACH", "AUSFALL", h)
            self.assertEqual(kurz, scores[:100])
            referenz = k.wahrscheinlichkeiten(woerter, "SCHWACH", "AUSFALL", h, referenz=True)
            for grenze in k.SCHWELLEN:
                self.assertEqual([p >= grenze for p in scores], [p >= grenze for p in referenz])


class RasterTests(unittest.TestCase):
    def test_histogramme_gegen_naive_zaehlung(self):
        rng = random.Random(713)
        for _ in range(25):
            woerter = [rng.choice(s.GROBWOERTER) for _ in range(80)]
            scores = [rng.choice((-1, 0, .05, .6, .95, 1, rng.random())) for _ in woerter]
            for h in (1, 3, 7):
                for schwellen in (k.SCHWELLEN, (0, .37, 1)):
                    erwartet = [oracle(woerter, scores, h, p) for p in schwellen]
                    self.assertEqual(k.rasterzaehler(woerter, scores, h, schwellen), erwartet)

    def test_ok_fehlwarnung_zaehlt_und_unbekannte_zukunft_nicht(self):
        woerter = ["OK"] * 10 + ["SCHWACH"] + ["AUSFALL"] * 3 + ["OK"] * 16
        scores = [-1.] * len(woerter)
        scores[2] = scores[10] = scores[29] = .8
        z, = k.rasterzaehler(woerter, scores, 3, (.6,))
        self.assertEqual((z["warntakte"], z["treffertakte"], z["fehlwarntakte"]), (2, 1, 1))
        self.assertEqual((z["phasen"], z["vorgewarnt"], z["verpasst"]), (1, 1, 0))

    def test_exakte_schwelle_warnt_naechster_kleinerer_float_nicht(self):
        woerter = ["OK"] * 9
        scores = [-1.] * 9
        scores[0], scores[1] = .6, math.nextafter(.6, -math.inf)
        z, = k.rasterzaehler(woerter, scores, 1, (.6,))
        self.assertEqual(z["warntakte"], 1)

    def test_kritische_takte_zaehlen_auch_mit_hohem_score_nicht(self):
        z, = k.rasterzaehler(["AUSFALL"] * 10, [1.] * 10, 2, (.6,))
        self.assertEqual((z["auswertbar"], z["warntakte"], z["phasen"]), (0, 0, 0))
        self.assertEqual(k.quoten(z), dict(warnanteil=None, trefferquote=None, grundrate=None, phasenquote=None))

    def test_raster_weist_ungueltige_eingaben_ab(self):
        w, scores = ["OK"] * 20, [0.] * 20
        for h in (-1, 0, 601, True, 1.0, "3", None):
            with self.subTest(h=h), self.assertRaises(ValueError):
                k.rasterzaehler(w, scores, h)
        for schwellen in ((), (.5, .5), (.8, .2), (math.nan,), (-.1,), (1.1,)):
            with self.subTest(schwellen=schwellen), self.assertRaises(ValueError):
                k.rasterzaehler(w, scores, 3, schwellen)
        for folge in ([0.], [math.nan] * 20, [math.inf] * 20):
            with self.assertRaises(ValueError):
                k.rasterzaehler(w, folge, 3)
        with self.assertRaises(ValueError):
            k.rasterzaehler(w, scores, 10)

    def test_baselines_haben_nachvollziehbare_null_und_vollwarnung(self):
        e = s.Einstellungen(takte=90)
        spur = s.generiere("bloecke", 900100, "entwicklung", e)
        configs = {signal: [k.konfig("immer"), k.konfig("nie")] for signal, _, _ in s.SIGNALE}
        for row in k.signalzeilen(spur, e, configs):
            if row["modell"] == "immer":
                self.assertEqual(row["warntakte"], row["auswertbar"])
                self.assertEqual(row["treffertakte"], row["zieltakte"])
                self.assertEqual(row["verpasst"], 0)
            else:
                self.assertEqual(row["warntakte"], 0)
                self.assertEqual(row["verpasst"], row["phasen"])


class AuswahlTests(unittest.TestCase):
    def test_raster_vollstaendig_und_eindeutig(self):
        configs = k.alle_konfigurationen()
        self.assertEqual(len(configs), 479)
        self.assertEqual(len({c["konfiguration"] for c in configs}), 479)
        self.assertEqual([sum(k.passt(c, suche) for c in configs) for suche in k.SUCHEN], [19, 19, 24, 456])

    def test_kostenverhaeltnis_aendert_die_wahl(self):
        a = zeile(k.konfig("erbe", index=10), fehlwarntakte=4, warntakte=4)
        b = zeile(k.konfig("erbe", index=12), verpasste_zieltakte=1, verpasst=1)
        self.assertEqual(k.waehle([a, b], "takt", 3, "erbe_schwelle"), b)
        self.assertEqual(k.waehle([a, b], "takt", 5, "erbe_schwelle"), a)
        self.assertEqual(k.waehle([a, b], "takt", 4, "erbe_schwelle"), a)  # Gleichstand: weniger verpasst.

    def test_taktkosten_und_phasenkosten_sind_verschiedene_modelle(self):
        a = zeile(k.konfig("erbe", index=10), fehlwarntakte=8, verpasste_zieltakte=10)
        b = zeile(k.konfig("erbe", index=12), verpasste_zieltakte=1, verpasst=1)
        self.assertEqual(k.waehle([a, b], "takt", 10, "erbe_schwelle"), b)
        self.assertEqual(k.waehle([a, b], "phase", 10, "erbe_schwelle"), a)

    def test_tiebreak_ist_reihenfolgeunabhaengig(self):
        kandidaten = [zeile(k.konfig("startwert", h, i)) for h in (5, 7) for i in (11, 13)]
        erwartet = "startwert-h05-s11"
        rng = random.Random(9)
        for _ in range(10):
            rng.shuffle(kandidaten)
            self.assertEqual(k.waehle(kandidaten, "takt", 1, "startwert_gemeinsam")["konfiguration"], erwartet)
        # Weniger Warntakte entscheidet vor der Entfernung zum bisherigen Parameter.
        a = zeile(k.konfig("startwert", 6, 12), warntakte=1, treffertakte=1)
        b = zeile(k.konfig("startwert", 24, 19))
        self.assertEqual(k.waehle([a, b], "takt", 1, "startwert_gemeinsam"), b)

    def test_auswahl_validierung_und_reserve(self):
        with mock.patch.object(k, "quellhashes", return_value={"fixture": "fest"}):
            a = auswahl_fixture()
            configs = k.pruefe_auswahl(a)
            self.assertEqual(len(a["auswahl"]), 2400)
            self.assertEqual(set(configs), {signal for signal, _, _ in s.SIGNALE})
            for fall in ("doppelt", "unvollstaendig", "konflikt", "code", "reserve"):
                b = copy.deepcopy(a)
                if fall == "doppelt": b["auswahl"].append(copy.deepcopy(b["auswahl"][0]))
                if fall == "unvollstaendig": b["auswahl"].pop()
                if fall == "konflikt": b["auswahl"][0]["schwellenindex"] = 1
                if fall == "code": b["quellhashes"] = {}
                if fall == "reserve": b["kontrolle"]["seedstart"] = 9999
                with self.subTest(fall=fall), self.assertRaises(ValueError):
                    k.pruefe_auswahl(b)

    def test_kontrolle_waehlt_nicht_neu(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(k, "quellhashes", return_value={"fixture": "fest"}):
            root = Path(tmp)
            auswahl = auswahl_fixture()
            datei, out = root / "auswahl.json", root / "kontrolle"
            k.json_schreiben(datei, auswahl)
            vorher = datei.read_bytes()
            argv = ["kostenlabor.py", "kontrolle", "--auswahl", str(datei), "--prozesse", "1", "--ausgabe", str(out)]
            with mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()), \
                    mock.patch.object(k, "waehle", side_effect=AssertionError("Kontrolle darf nicht wählen")), \
                    mock.patch.object(k, "auswahlzeilen", side_effect=AssertionError("Kontrolle darf nicht wählen")), \
                    mock.patch.object(s, "generiere", wraps=s.generiere) as generator:
                k.main()
            self.assertEqual(datei.read_bytes(), vorher)
            self.assertEqual(len(generator.call_args_list), 4)
            for call in generator.call_args_list:
                self.assertEqual(call.args[1:3], (900000, "kontrolle"))
            erwartete = {(z["signal"], z["kostenmodell"], z["verhaeltnis"], z["suche"]): z["konfiguration"]
                         for z in auswahl["auswahl"]}
            with (out / "auswahl-pruefung.csv").open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 12000)
            for row in rows:
                key = row["signal"], row["kostenmodell"], int(row["verhaeltnis"]), row["suche"]
                self.assertEqual(row["konfiguration"], erwartete[key])


class KommandoTests(unittest.TestCase):
    def test_entwicklung_und_kontrolle_mit_unbenutzter_testreserve(self):
        script = str(Path(k.__file__).resolve())
        with tempfile.TemporaryDirectory() as tmp:
            dev, control = Path(tmp) / "entwicklung", Path(tmp) / "kontrolle"
            args = [sys.executable, "-B", script, "entwicklung", "--anzahl", "1", "--seedstart", "900100",
                    "--kontrollstart", "900001", "--kontrollanzahl", "1", "--takte", "90",
                    "--prozesse", "1", "--ausgabe", str(dev)]
            subprocess.run(args, capture_output=True, check=True, timeout=60)
            auswahl = dev / "auswahl.json"
            vorher = auswahl.read_bytes()
            choice = json.loads(vorher)
            self.assertEqual(choice["kontrolle"], dict(seedstart=900001, anzahl=1))
            subprocess.run([sys.executable, "-B", script, "kontrolle", "--auswahl", str(auswahl),
                            "--prozesse", "1", "--ausgabe", str(control)],
                           capture_output=True, check=True, timeout=60)
            self.assertEqual(auswahl.read_bytes(), vorher)
            for out, start in ((dev, 900100), (control, 900001)):
                meta = json.loads((out / "manifest.json").read_text())
                self.assertEqual((meta["status"], meta["spuren"], meta["seedstart"]), ("vollstaendig", 4, start))
                for name, digest in meta["ergebnisse"].items():
                    self.assertEqual(k.sha(out / name), digest)
            with (control / "einzel.csv").open() as f:
                self.assertEqual({int(row["seed"]) for row in csv.DictReader(f)}, {900001})
            with (dev / "summen.csv").open() as f:
                self.assertEqual(len(list(csv.DictReader(f))), 7185)
            # Vorhandene Ergebnisse werden nicht unbemerkt ersetzt.
            self.assertNotEqual(subprocess.run(args, capture_output=True, timeout=30).returncode, 0)
            self.assertEqual(auswahl.read_bytes(), vorher)


if __name__ == "__main__":
    unittest.main()

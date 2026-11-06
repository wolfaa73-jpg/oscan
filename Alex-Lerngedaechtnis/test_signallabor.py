"""Invarianten, unabhängige Zählbeispiele und Referenzparität des Signallabors."""
import csv
import json
import math
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import signallabor as s
from kern import Knoten, REGELN
from koerper import ERKUNDUNG
from vokabular import (SIGNALE, Wortgedaechtnis, koerperwort, stufen_je_signal,
                       kritisch, grob, warnungen)


class GeneratorTests(unittest.TestCase):
    def test_reproduzierbar_getrennt_und_gueltige_stufen(self):
        e = s.Einstellungen(takte=180)
        spuren = []
        for f in s.FAMILIEN:
            for satz in s.SAETZE:
                a = s.generiere(f, 42, satz, e)
                self.assertEqual(a, s.generiere(f, 42, satz, e))
                self.assertEqual(len(a), 180)
                for signal, hoch, krit in SIGNALE:
                    self.assertLessEqual({z[signal] for z in a}, {"OK", hoch, krit})
                spuren.append(a)
        for i, a in enumerate(spuren):
            for b in spuren[i + 1:]:
                self.assertNotEqual(a, b)

    def test_parametergrenzen_und_unbekannte_eingaben(self):
        for kwargs in (dict(takte=30), dict(horizont=0), dict(horizont=601),
                       dict(waerme_p=math.nan), dict(ausnahme_p=-0.1), dict(schwelle=2)):
            with self.assertRaises(ValueError):
                s.Einstellungen(**kwargs)
        for f, seed, satz in (("falsch", 0, "entwicklung"), (s.FAMILIEN[0], -1, "kontrolle"),
                              (s.FAMILIEN[0], 0, "unbekannt")):
            with self.assertRaises(ValueError):
                s.generiere(f, seed, satz)

    def test_waerme_extreme_und_seltene_ausnahme(self):
        for p in (0, 1):
            e = s.Einstellungen(takte=600, waerme_p=p, ausnahme_p=p)
            spur = s.generiere("seltene_ausnahme", 10, einstellungen=e)
            self.assertEqual(any(z["temperatur"] == "TEMP_KRITISCH" for z in spur), bool(p))
            self.assertEqual(any(z["speicher"] == "SPEICHER_VOLL" for z in spur), not bool(p))
            # Vollständige hohe Läufe führen bei p=1 immer direkt zu kritisch.
            temp = [z["temperatur"] for z in spur]
            ausgaenge = [b for a, b in zip(temp, temp[1:]) if a == "TEMP_HOCH" and b != a]
            self.assertTrue(ausgaenge)
            self.assertEqual(set(ausgaenge), {"TEMP_KRITISCH" if p else "OK"})

    def test_laengere_spur_veraendert_ihren_praefix_nicht(self):
        for f in s.FAMILIEN:
            kurz = s.generiere(f, 2, einstellungen=s.Einstellungen(takte=120))
            lang = s.generiere(f, 2, einstellungen=s.Einstellungen(takte=500))
            self.assertEqual(kurz, lang[:120])

    def test_waermeparameter_veraendert_keine_fremden_signale(self):
        kalt = s.generiere("bloecke", 9, einstellungen=s.Einstellungen(waerme_p=0))
        heiss = s.generiere("bloecke", 9, einstellungen=s.Einstellungen(waerme_p=1))
        for signal in ("speicher", "schleife"):
            self.assertEqual([z[signal] for z in kalt], [z[signal] for z in heiss])

    def test_zufallsraten_an_vielen_abgeschlossenen_durchgaengen(self):
        folgen = {signal: [] for signal, _, _ in SIGNALE}
        for seed in range(100):
            spur = s.generiere("seltene_ausnahme", seed)
            for signal, hoch, _ in SIGNALE:
                woerter = [z[signal] for z in spur]
                folgen[signal].extend(b for a, b in zip(woerter, woerter[1:]) if a == hoch and b != a)
        for signal, _, krit in SIGNALE:
            quote = folgen[signal].count(krit) / len(folgen[signal])
            ziel = .38 if signal == "temperatur" else .95
            self.assertGreater(len(folgen[signal]), 1000)
            self.assertLess(abs(quote - ziel), .04)

    def test_vorrang_entspricht_roher_einstufung(self):
        roh = [(t, h, l) for t in (None, 499, 500, 600) for h in (16384, 65536, 70000)
               for l in (1000, 20000, 200000)]
        stufen = [stufen_je_signal(*z, ERKUNDUNG) for z in roh]
        self.assertEqual(s.schwerstes(stufen), [koerperwort(*z, ERKUNDUNG) for z in roh])


class VergleichTests(unittest.TestCase):
    def test_letzter_durchgang_kennt_nur_abgeschlossene_vergangenheit(self):
        w = ["OK", "SCHWACH", "AUSFALL", "OK", "SCHWACH", "SCHWACH", "OK", "SCHWACH"]
        self.assertEqual(s.letzter_durchgang(w), [False, False, False, False, True, True, False, False])

    def test_alle_verfahren_sind_kausal(self):
        e = s.Einstellungen(takte=180)
        spur = s.generiere("bloecke", 4, einstellungen=e)
        kurz = list(s.verfahren(spur[:100], e))
        lang = list(s.verfahren(spur, e))
        self.assertEqual(len(kurz), 12)
        for (sicht, name, warn, je), (sicht2, name2, warn2, je2) in zip(kurz, lang):
            self.assertEqual((sicht, name), (sicht2, name2))
            self.assertEqual(warn, warn2[:100])
            self.assertEqual(je, {k: v[:100] for k, v in je2.items()})

    def test_schneller_blick_gegen_original_bei_zufaelligen_tabellen(self):
        rng = random.Random(87)
        for _ in range(100):
            m = s.SchnellesDreiergedaechtnis(s.GROBWOERTER, s.GROBERBE)
            for a in m.woerter:
                for b in m.woerter:
                    m.gewichte[a][b] = rng.random() * 20 if rng.random() < .7 else 0
            for h in (1, 2, 30, 60, 600):
                for w in ("OK", "SCHWACH"):
                    self.assertAlmostEqual(m.kritisch_binnen(w, h),
                                           Wortgedaechtnis.kritisch_binnen(m, w, h), places=11)

    def test_schwellennahe_originalrechnung(self):
        m = s.SchnellesDreiergedaechtnis(s.GROBWOERTER, ())
        m.gewichte["SCHWACH"].update({"OK": 2, "AUSFALL": 3})
        self.assertEqual(m.kritisch_binnen("SCHWACH", 1), 0.6)

    def test_warnungen_gegen_referenz_und_grob_gegen_kern(self):
        for familie in s.FAMILIEN:
            e = s.Einstellungen(takte=180)
            stufen = s.generiere(familie, 19, einstellungen=e)
            self.assertEqual(list(s.verfahren(stufen, e)), list(s.verfahren(stufen, e, referenz=True)))
            grobe = [grob(w) for w in s.schwerstes(stufen)]
            for name, regel in (("Festes Erbe", "erbe"), ("Startwert", "startwert"), ("Ohne Erbe", "kontext")):
                k = Knoten(REGELN[regel](), blick=e.horizont)
                erwartet = [k.schritt(i, w).vorwarnung for i, w in enumerate(grobe, 1)]
                self.assertEqual(s.einzelwarnungen(grobe, s.GROBWOERTER, s.GROBERBE, name, e), erwartet)


class ZaehlTests(unittest.TestCase):
    def test_zaehler_gegen_einfache_unabhaengige_rechnung(self):
        rng = random.Random(951)
        for _ in range(100):
            w = [rng.choice(s.GROBWOERTER) for _ in range(50)]
            warn = [bool(rng.getrandbits(1)) for _ in w]
            for h in (1, 3, 7):
                for nur_hoch in (False, True):
                    maske = [x == "SCHWACH" if nur_hoch else x != "AUSFALL" for x in w]
                    z = s.zaehle(w, warn, h, maske)
                    takte = [t for t in range(len(w)-h) if maske[t]]
                    gewarnt = [t for t in takte if warn[t]]
                    ziel = lambda t: "AUSFALL" in w[t+1:t+h+1]
                    beginne = [t for t in range(h,len(w)-h)
                               if w[t] == "AUSFALL" and w[t-1] != "AUSFALL"]
                    vorgewarnt = sum(any(warn[t] and w[t] != "AUSFALL" for t in range(b-h,b))
                                    for b in beginne)
                    self.assertEqual((z['auswertbar'],z['warntakte'],z['treffertakte'],z['zieltakte'],
                                      z['phasen'],z['vorgewarnt'],z['verpasst']),
                                     (len(takte),len(gewarnt),sum(map(ziel,gewarnt)),sum(map(ziel,takte)),
                                      len(beginne),vorgewarnt,len(beginne)-vorgewarnt))

    def test_zusammenhaengender_ausfall_ist_eine_phase(self):
        w = ["OK", "SCHWACH", "AUSFALL", "AUSFALL", "AUSFALL", "OK",
             "AUSFALL", "AUSFALL", "OK", "OK"]
        warn = [False, True, False, False, False, False, False, False, False, False]
        z = s.zaehle(w, warn, 1, [not kritisch(x) for x in w])
        self.assertEqual((z["phasen"], z["vorgewarnt"], z["verpasst"]), (2, 1, 1))

    def test_unbekannte_zukunft_wird_nicht_als_fehlalarm_gezaehlt(self):
        w = ["OK", "SCHWACH", "AUSFALL", "OK", "OK", "SCHWACH", "OK"]
        warn = [True, True, False, True, True, True, True]
        z = s.zaehle(w, warn, 2, [not kritisch(x) for x in w])
        self.assertEqual({k: z[k] for k in ("auswertbar", "warntakte", "treffertakte", "zieltakte")},
                         dict(auswertbar=4, warntakte=4, treffertakte=2, zieltakte=2))
        self.assertEqual((z["phasen"], z["vorgewarnt"]), (1, 1))
        self.assertEqual(s.anteile(z)["trefferquote"], 0.5)

    def test_randphasen_und_nullnenner(self):
        w = ["AUSFALL", "OK", "AUSFALL", "OK", "OK", "AUSFALL"]
        z = s.zaehle(w, [False] * len(w), 2, [False] * len(w))
        self.assertEqual((z["phasen"], z["verpasst"]), (1, 1))
        self.assertIsNone(s.anteile(z)["warnanteil"])
        self.assertIsNone(s.anteile(z)["trefferquote"])

    def test_immer_warnen_ist_grundrate_und_verdeckung_ist_sichtbar(self):
        e = s.Einstellungen(takte=300)
        stufen = s.generiere("ueberlagerung", 5, einstellungen=e)
        rows = list(s.auswerten(stufen, e))
        self.assertEqual(len(rows), 48)
        for r in rows:
            if r["verfahren"] == "Immer warnen" and (r["sicht"] == "je_signal" or r["signal"] == "gesamt"):
                self.assertEqual(r["warnanteil"], 1)
                self.assertEqual(r["trefferquote"], r["grundrate"])
        self.assertTrue(any(r["verdeckt"] > 0 for r in rows))

    def test_kein_treffer_fuer_fremden_ausfall(self):
        w = ["OK", "TEMP_HOCH", "OK", "OK", "OK"]
        warn = [False, True, False, False, False]
        # Ein fremder Ausfall ist in dieser eigenen Folge schlicht kein Ausfall.
        z = s.zaehle(w, warn, 2, [x == "TEMP_HOCH" for x in w])
        self.assertEqual((z["warntakte"], z["treffertakte"], s.anteile(z)["grundrate"]),
                         (1, 0, 0))


class KommandoTests(unittest.TestCase):
    def test_csv_prozesse_manifest_und_ueberschreibschutz(self):
        script = str(Path(s.__file__).resolve())
        with tempfile.TemporaryDirectory() as tmp:
            ordner = [Path(tmp) / name for name in ("eins", "zwei")]
            for n, ziel in enumerate(ordner, 1):
                args = [sys.executable, "-B", script, "--satz", "entwicklung", "--anzahl", "1",
                        "--takte", "60", "--familien", "bloecke", "--prozesse", str(n), "--ausgabe", str(ziel)]
                subprocess.run(args, capture_output=True, check=True)
                meta = json.loads((ziel / "manifest.json").read_text())
                self.assertEqual(meta["status"], "vollstaendig")
                self.assertEqual(meta["spuren"], 1)
                with (ziel / "einzel.csv").open() as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 48)
                vorher = (ziel / "manifest.json").read_bytes()
                self.assertNotEqual(subprocess.run(args, capture_output=True).returncode, 0)
                self.assertEqual(vorher, (ziel / "manifest.json").read_bytes())
            for name in ("einzel.csv", "summen.csv", "manifest.json"):
                self.assertEqual((ordner[0] / name).read_bytes(), (ordner[1] / name).read_bytes())


if __name__ == "__main__":
    unittest.main()

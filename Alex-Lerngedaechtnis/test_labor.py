import errno
import hashlib
from dataclasses import asdict as dataclasses_asdict
import json
import os
import shutil
import struct
import zlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import koerper
import vokabular
import wiederanlauf
from boardprobe import antwort, vergleiche_board
from kern import Erbgedaechtnis, Gedaechtnis, Kontextgedaechtnis, Knoten, MAX_TAKT, REGELN, ZUSTAENDE
from labor import FAMILIEN, generiere
from messen import klassifizieren, probe
from neustart import kodiert, laden, sichern
from transport import Empfaenger, kanal
from versuch import RAHMEN, beispielspur, durchlauf, lies_spur, vergleiche

ROOT = Path(__file__).resolve().parent


class PipePort:
    """Serielle Schnittstelle über die Pipes eines laufenden Hostsketches."""

    def __init__(self, prozess):
        self.prozess = prozess

    def write(self, daten):
        self.prozess.stdin.write(daten)
        self.prozess.stdin.flush()

    def readline(self):
        return self.prozess.stdout.readline()


class DatenTests(unittest.TestCase):
    def test_luecke_altert_ohne_uebergang(self):
        k = Knoten(Gedaechtnis(4))
        k.schritt(1, "SCHWACH")
        k.schritt(2, "AUSFALL")
        s = k.schritt(6, "AUSFALL")
        self.assertTrue(s.sofort)
        self.assertAlmostEqual(k.gedaechtnis.schaetze("SCHWACH")[1], 0.5)
        self.assertEqual(k.gedaechtnis.schaetze("AUSFALL"), (0, 0))

    def test_luecke_und_ende_lassen_warnungen_offen(self):
        spur = [(1, "SCHWACH"), (3, "AUSFALL"), (4, "SCHWACH")]
        b = durchlauf(spur, "fest", feste_warnregel=True)
        self.assertEqual((b.treffer, b.fehlalarme, b.offen), (0, 0, 2))
        self.assertEqual((b.fehlende_takte, b.sofortmeldungen, b.beginn_unbekannt), (1, 1, 1))
        self.assertEqual(b.ohne_vorwarnung, 0)

    def test_ungueltige_eingabe_veraendert_den_knoten_nicht(self):
        k = Knoten(Gedaechtnis())
        k.schritt(1, "OK")
        for t, z in [(0, "OK"), (1, "SCHWACH"), (2, "kaputt"), (MAX_TAKT + 1, "OK")]:
            with self.assertRaises(ValueError):
                k.schritt(t, z)
        self.assertEqual(k.schritt(2, "SCHWACH").beleg, 0)
        self.assertEqual(k.gedaechtnis.schaetze("OK")[1], 1)

    def test_kontext_verblasst_nur_bei_passender_erfahrung(self):
        g = Kontextgedaechtnis()
        g.beobachte("SCHWACH", "AUSFALL")
        for _ in range(240):
            g.beobachte("OK", "OK")
        self.assertEqual(g.schaetze("SCHWACH"), (1, 1))
        for _ in range(6):
            g.beobachte("SCHWACH", "OK")
        self.assertAlmostEqual(g.gewichte["SCHWACH"]["AUSFALL"], .5)

    def test_csv_mit_absoluten_takten(self):
        with tempfile.TemporaryDirectory() as ort:
            p = Path(ort, "spur.csv")
            p.write_text("takt,zustand\n4,OK\n7,AUSFALL\n")
            self.assertEqual(lies_spur(p), [(4, "OK"), (7, "AUSFALL")])
            for t in ("4", "0", "3", "-1", "5.5", str(MAX_TAKT + 1)):
                p.write_text(f"takt,zustand\n4,OK\n{t},OK\n")
                with self.assertRaises(ValueError):
                    lies_spur(p)

    def test_zaehlidentitaeten_auf_allen_familien(self):
        for familie in FAMILIEN:
            spur = generiere(familie, 1010)
            spur = [(t, z) for t, z in enumerate(spur, 1) if t % 13 != 0]
            for b in vergleiche(spur):
                self.assertEqual(b.sofortmeldungen, b.treffer + b.ohne_vorwarnung + b.beginn_unbekannt)
                self.assertEqual(b.nutzbytes, b.nachrichten * 5)


class ErbeTests(unittest.TestCase):
    def test_erbe_traegt_ab_dem_ersten_schwachen_signal(self):
        self.assertTrue(Knoten(Erbgedaechtnis()).schritt(1, "SCHWACH").vorwarnung)
        self.assertFalse(Knoten(Kontextgedaechtnis()).schritt(1, "SCHWACH").vorwarnung)

    def test_drei_gegenbeispiele_ueberstimmen_das_erbe(self):
        k = Knoten(Erbgedaechtnis())
        warnt = [k.schritt(t, z).vorwarnung for t, z in enumerate(["SCHWACH", "OK"] * 4, 1)]
        self.assertEqual(warnt[::2], [True, True, True, False])

    def test_erbe_bleibt_fest_und_getrennt(self):
        g = Erbgedaechtnis()
        for _ in range(200):
            g.beobachte("SCHWACH", "OK")
            g.schaetze("SCHWACH")
        self.assertEqual((g.erbe["SCHWACH"]["AUSFALL"], g.gewichte["SCHWACH"]["AUSFALL"]), (3, 0))
        # Untergrenze: drei feste gegen höchstens 1 / (1 - 0,5^(1/6)) eigene Belege.
        self.assertAlmostEqual(g.schaetze("SCHWACH")[0], 3 / (3 + 1 / (1 - 0.5 ** (1 / 6))))

    def test_ohne_erbe_gleich_kontextregel(self):
        spur = generiere("Rückkehr", 7)
        self.assertEqual(durchlauf(spur, "x", Kontextgedaechtnis()),
                         durchlauf(spur, "x", Erbgedaechtnis({("SCHWACH", "AUSFALL"): 0})))

    def test_ungueltiges_erbe_wird_abgewiesen(self):
        for erbe in ({("SCHWACH", "kaputt"): 1}, {("SCHWACH", "AUSFALL"): -1},
                     {("SCHWACH", "AUSFALL"): float("nan")}):
            with self.subTest(erbe=erbe):
                with self.assertRaises(ValueError):
                    Erbgedaechtnis(erbe)


class NeustartTests(unittest.TestCase):
    def test_fortsetzung_ist_schrittweise_identisch_auch_an_luecken(self):
        spur = [(t, z) for t, z in enumerate(beispielspur(), 1) if t % 13 != 0]
        with tempfile.TemporaryDirectory() as ort:
            for typ in REGELN.values():
                referenz = Knoten(typ())
                erwartet = [referenz.schritt(t, z) for t, z in spur]
                for grenze in (1, 12, 51, 119, len(spur)-1):
                    k = Knoten(typ())
                    anfang = [k.schritt(t, z) for t, z in spur[:grenze]]
                    p = Path(ort, f"{typ.__name__}-{grenze}.json")
                    sichern(p, "A", k)
                    restauriert = laden(p, "A")
                    self.assertEqual(anfang + [restauriert.schritt(t, z) for t, z in spur[grenze:]], erwartet)

    def test_pruefsumme_quelle_und_version(self):
        with tempfile.TemporaryDirectory() as ort:
            p = Path(ort, "stand")
            k = Knoten(Gedaechtnis())
            k.schritt(1, "OK")
            sichern(p, "A", k)
            with self.assertRaises(ValueError):
                laden(p, "B")
            with self.assertRaises(FileExistsError):
                sichern(p, "B", k)
            original = json.loads(p.read_bytes())
            for key, val in [("format", "v99"), ("takt", True), ("gewichte", [[-1, 0, 0]] * 3),
                             ("regel", "x"), ("vokabular", list(reversed(ZUSTAENDE))),
                             ("erbe", [[0, 0, 0], [0, 0, 3.0], [0, 0, 0]])]:
                d = dict(original["daten"], **{key: val})
                p.write_bytes(kodiert(dict(daten=d, sha256=hashlib.sha256(kodiert(d)).hexdigest())))
                with self.assertRaises(ValueError):
                    laden(p, "A")
            original["daten"]["takt"] = 12
            p.write_bytes(kodiert(original))
            with self.assertRaises(ValueError):
                laden(p, "A")

    def test_unvollstaendiger_schreibvorgang_publiziert_keinen_stand(self):
        with tempfile.TemporaryDirectory() as ort:
            p = Path(ort, "stand")
            k = Knoten(Gedaechtnis())
            k.schritt(1, "OK")
            with patch("neustart.os.fsync", side_effect=OSError("Schreibfehler")):
                with self.assertRaises(OSError):
                    sichern(p, "A", k)
            self.assertEqual(list(Path(ort).iterdir()), [])

    def test_erbe_wird_mitgesichert_und_geprueft(self):
        with tempfile.TemporaryDirectory() as ort:
            k = Knoten(Erbgedaechtnis())
            k.schritt(1, "SCHWACH")
            sichern(Path(ort, "erbe"), "A", k)
            restauriert = laden(Path(ort, "erbe"), "A")
            self.assertIs(type(restauriert.gedaechtnis), Erbgedaechtnis)
            # Nach einer Lücke trägt allein das Erbe die Warnung.
            self.assertTrue(restauriert.schritt(3, "SCHWACH").vorwarnung)
            anders = Knoten(Erbgedaechtnis({("SCHWACH", "AUSFALL"): 0}))
            anders.schritt(1, "OK")
            sichern(Path(ort, "anders"), "A", anders)
            with self.assertRaises(ValueError):
                laden(Path(ort, "anders"), "A")

    def test_stand_ohne_erbe_aus_version_02_bleibt_ladbar(self):
        with tempfile.TemporaryDirectory() as ort:
            p = Path(ort, "stand")
            k = Knoten(Kontextgedaechtnis())
            k.schritt(1, "SCHWACH")
            k.schritt(2, "AUSFALL")
            sichern(p, "A", k)
            d = json.loads(p.read_bytes())["daten"]
            del d["erbe"]
            p.write_bytes(kodiert(dict(daten=d, sha256=hashlib.sha256(kodiert(d)).hexdigest())))
            self.assertEqual(laden(p, "A").gedaechtnis.gewichte["SCHWACH"]["AUSFALL"], 1)


class MessTests(unittest.TestCase):
    def test_reale_loopback_spur(self):
        s = klassifizieren(ROOT / "beispiele/loopback-roh.csv", 20)
        self.assertEqual(s, list(enumerate(["OK"] * 6 + ["AUSFALL"] * 6, 1)))
        self.assertEqual(vergleiche(s)[-1].sofortmeldungen, 1)

    def test_schwelle_und_luecke(self):
        with tempfile.TemporaryDirectory() as ort:
            p = Path(ort, "roh")
            kopf = "takt,start_ms,dauer_ms,ergebnis\n"
            p.write_text(kopf + "1,0,20,VERBUNDEN\n4,300,0.1,ABGELEHNT\n")
            self.assertEqual(klassifizieren(p, 20), [(1, "SCHWACH"), (4, "AUSFALL")])
            for zeile in ("1,0,nan,VERBUNDEN", "1,inf,2,TIMEOUT", "1,0,2,UNBEKANNT", "1,0,-1,TIMEOUT"):
                p.write_text(kopf + zeile)
                with self.assertRaises(ValueError):
                    klassifizieren(p, 20)

    def test_lokaler_fehler_ist_kein_ausfall_des_ziels(self):
        with patch("messen.socket.socket", side_effect=PermissionError(errno.EACCES, "Test")):
            with self.assertRaises(PermissionError):
                probe("127.0.0.1", 1, .01)


class TransportTests(unittest.TestCase):
    def test_herzschlag_repariert_verlorene_zustandsmeldung(self):
        spur = ["OK"]*5 + ["AUSFALL"]*20 + ["OK"]*11
        delta = kanal(spur, {6}, None, None)
        puls = kanal(spur, {6}, 5, 10)
        self.assertEqual((delta.erste_ausfallsicht, delta.falsch), (None, 20))
        self.assertEqual((puls.erste_ausfallsicht, puls.falsch, puls.gesendet), (11, 5, 8))
        aus = kanal(spur, set(range(6,26)), 5, 10)
        self.assertEqual((aus.erste_ausfallsicht, aus.unbekannt), (None, 15))

    def test_empfaenger_lehnt_alte_und_unbekannte_pakete_ab(self):
        e = Empfaenger()
        self.assertTrue(e.empfange(RAHMEN.pack(8, 3), 8))
        for p in (b"", RAHMEN.pack(7, 1), RAHMEN.pack(8, 1), RAHMEN.pack(10, 1), RAHMEN.pack(9, 4)):
            self.assertFalse(e.empfange(p, 9))
        self.assertEqual(e.sicht(17, 10), "AUSFALL")
        self.assertIsNone(e.sicht(18, 10))


class PrueferTests(unittest.TestCase):
    def test_langsamer_start_beantwortet_beide_neustartbefehle(self):
        # Der Prüfer hat NEUER_LAUF wiederholt. Die zweite Bereitmeldung steht vor der ersten Antwort.
        zeilen = iter([b"BEREIT,ZEIT\n", b"BEREIT,ZEIT\n", b"1,OK,0,0\n", b"2,AUSFALL,1,0\n"])
        class Port:
            def write(self, daten):
                pass
            def readline(self):
                return next(zeilen)
        self.assertEqual(vergleiche_board(Port(), ["OK", "AUSFALL"], "zeit"), 2)

    def test_langsamer_flashzugriff_wird_abgewartet(self):
        # Leere Zeilen sind abgelaufene Lesefristen der seriellen Schnittstelle.
        zeilen = iter([b"", b"", b"GESICHERT\r\n"])
        class Port:
            def readline(self):
                return next(zeilen)
        self.assertEqual(antwort(Port(), frist=3.0), b"GESICHERT")


class KoerperTests(unittest.TestCase):
    G = koerper.ERKUNDUNG
    # Temperatur steigt über SCHWACH zu AUSFALL, dann fehlt der Messwert bei langer Lücke.
    ROH = [(410, 300000, 60), (480, 300000, 70), (520, 299000, 80), (610, 298000, 90),
           (None, 298000, 250000), (430, 300000, 60)]

    @staticmethod
    def geraetezeilen(roh, g, regel, last=None):
        """So antwortet das Gerät, wenn es wie Python einstuft und entscheidet."""
        k = Knoten(REGELN[regel]())
        zeilen = []
        for takt, ((t, h, l), phase) in enumerate(zip(roh, last or [0] * len(roh)), 1):
            z = koerper.einstufen(t, h, l, g)
            s = k.schritt(takt, z)
            zeilen.append(f"K,{takt},{z},{int(s.sofort)},{int(s.vorwarnung)},"
                          f"{'-' if t is None else t},{h},{l},{phase}")
        return zeilen

    def test_einstufung_nimmt_den_schlechtesten_wert(self):
        e, g = koerper.einstufen, self.G
        self.assertEqual(e(499, 65537, 19999, g), "OK")
        for wert in ((500, 65537, 19999), (499, 65536, 19999), (499, 65537, 20000)):
            self.assertEqual(e(*wert, g), "SCHWACH")
        for wert in ((600, 65537, 19999), (499, 16384, 19999), (550, 300000, 200000)):
            self.assertEqual(e(*wert, g), "AUSFALL")
        self.assertEqual(e(None, 300000, 50, g), "OK")

    def test_grenzen_muessen_geordnet_sein(self):
        for falsch in ((600, 500, 65536, 16384, 1, 2), (500, 600, 100, 200, 1, 2),
                       (500, 600, 200, 100, 2, 1), (500, 600.0, 200, 100, 1, 2)):
            with self.subTest(grenzen=falsch):
                with self.assertRaises(ValueError):
                    koerper.Grenzen(*falsch)
        self.assertEqual(self.G.befehl(), b"GRENZEN 500 600 65536 16384 20000 200000")

    def test_aufnahme_pruefung_und_neue_einstufung(self):
        phasen = [1, 1, 1, 0, 0, 0]
        antworten = [b"BEREIT,ERBE", b"GRENZEN,ok", b"LAST,ok", b"KOERPER,an",
                     *(z.encode() for z in self.geraetezeilen(self.ROH, self.G, "erbe", phasen))]
        zeilen, gesendet = iter(a + b"\r\n" for a in antworten), []
        class Port:
            def write(self, daten):
                gesendet.append(daten)
            def readline(self):
                return next(zeilen, b"")
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "koerper.csv")
            self.assertEqual(koerper.aufnehmen(Port(), "erbe", self.G, 1000, len(self.ROH), ziel, (3, 3)), 6)
            # Die Last startet vor dem Körpermodus, STOP beendet beides.
            self.assertLess(gesendet.index(b"LAST 3 3\n"), gesendet.index(b"KOERPER 1000\n"))
            self.assertEqual(gesendet[-1], b"STOP\n")
            meta, werte = koerper.pruefen(ziel)
            self.assertEqual(meta["last"], [3, 3])
            self.assertEqual([w["zustand"] for w in werte], ["OK", "OK", "SCHWACH", "AUSFALL", "AUSFALL", "OK"])
            self.assertEqual([w["last"] for w in werte], phasen)
            self.assertIn("Unter Last (3 Takte)", koerper.bericht(meta, werte))
            locker = koerper.Grenzen(550, 700, 65536, 16384, 20000, 300000)
            self.assertEqual([z for _, z in koerper.neu_einstufen(werte, locker)],
                             ["OK", "OK", "OK", "SCHWACH", "SCHWACH", "OK"])
            with self.assertRaises(ValueError):
                koerper.aufnehmen(Port(), "erbe", self.G, 1000, 1, ziel)
            ziel.write_text(ziel.read_text().replace(",SCHWACH,0,1,1", ",SCHWACH,0,0,1"))
            with self.assertRaises(ValueError):
                koerper.pruefen(ziel)

    def test_aufnahme_ohne_lastspalte_bleibt_lesbar(self):
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "alt.csv")
            ziel.with_suffix(".json").write_text(json.dumps(dict(
                regel="erbe", intervall_ms=1000, grenzen=dataclasses_asdict(self.G), beginn="2026-11-05 10:11")))
            ziel.write_text(",".join(koerper.KOPF_ALT) + "\n1,1001,380,371820,326,OK,0,0\n")
            meta, werte = koerper.pruefen(ziel)
            self.assertEqual((werte[0]["last"], werte[0]["temp_dc"]), (0, 380))


class VokabularTests(unittest.TestCase):
    # Fassung 1 des festen Kerns. Wer hier etwas ändert, bricht die Verständigung
    # mit älteren Knoten. Neue Wörter kommen nur hinten an VOKABULAR dazu.
    FASSUNG_1 = [(1, "OK", "OK"), (2, "SCHWACH", "SCHWACH"), (3, "AUSFALL", "AUSFALL"), (4, "VORWARNUNG", None),
                 (5, "TEMP_HOCH", "SCHWACH"), (6, "TEMP_KRITISCH", "AUSFALL"), (7, "SPEICHER_KNAPP", "SCHWACH"),
                 (8, "SPEICHER_VOLL", "AUSFALL"), (9, "SCHLEIFE_ZAEH", "SCHWACH"), (10, "SCHLEIFE_STEHT", "AUSFALL")]

    def test_alte_nummern_bleiben_neue_kommen_hinten_dazu(self):
        v = vokabular.VOKABULAR
        self.assertEqual([(w.nummer, w.name, w.oberbegriff) for w in v[:len(self.FASSUNG_1)]], self.FASSUNG_1)
        self.assertEqual([w.nummer for w in v], list(range(1, len(v) + 1)))
        namen = [w.name for w in v + vokabular.VORSCHLAEGE]
        self.assertEqual(len(namen), len(set(namen)))
        self.assertTrue(all(w.nummer is None and w.bedeutung for w in vokabular.VORSCHLAEGE))
        # Die bisherigen Token im Fünf-Byte-Paket tragen dieselben Nummern.
        from versuch import TOKEN
        self.assertTrue(all(vokabular.NACH_NAME[name].nummer == nummer for name, nummer in TOKEN.items()))
        for hoch, kritisch in vokabular.ERBFOLGEN:
            a, b = vokabular.NACH_NAME[hoch], vokabular.NACH_NAME[kritisch]
            self.assertEqual((a.signal, a.oberbegriff, b.oberbegriff), (b.signal, "SCHWACH", "AUSFALL"))

    def test_grobe_sicht_wie_einstufung_im_geraet(self):
        g = koerper.ERKUNDUNG
        for t in (None, 499, 500, 599, 600):
            for h in (16384, 16385, 65536, 65537):
                for l in (19999, 20000, 199999, 200000):
                    self.assertEqual(vokabular.grob(vokabular.koerperwort(t, h, l, g)),
                                     koerper.einstufen(t, h, l, g), (t, h, l))

    def test_horizont_eins_entscheidet_wie_der_knoten(self):
        spur = generiere("Rückkehr", 3)
        knoten = Knoten(Erbgedaechtnis())
        erwartet = [knoten.schritt(t, z).vorwarnung for t, z in enumerate(spur, 1)]
        modell = vokabular.Wortgedaechtnis(vokabular.GROBWOERTER, vokabular.GROBERBE)
        self.assertEqual(vokabular.warnungen(spur, modell, 1), erwartet)

    def test_weiter_blick_warnt_vor_der_hitze(self):
        rhythmus = ["OK"] * 10 + ["TEMP_HOCH"] * 8 + ["TEMP_KRITISCH"] * 3
        woerter = rhythmus * 10
        neu = lambda: vokabular.Wortgedaechtnis(vokabular.KOERPERWOERTER, vokabular.ERBFOLGEN)
        nah = vokabular.bewerte(woerter, vokabular.warnungen(woerter, neu(), 1), 10)
        weit = vokabular.bewerte(woerter, vokabular.warnungen(woerter, neu(), 10), 10)
        # Bei einem Takt warnt nur das Erbe zu Beginn, mit zehn Takten jede Phase acht Takte vorher.
        self.assertEqual((nah["phasen"], nah["vorgewarnt"]), (10, 1))
        self.assertEqual((weit["vorgewarnt"], weit["fehlalarme"], weit["vorwarnzeit"]), (10, 0, 8))
        m = neu()
        vokabular.warnungen(woerter, m, 1)
        werte = [m.kritisch_binnen("OK", h) for h in range(1, 25)]
        self.assertEqual(werte, sorted(werte))

    def test_alarme_verschmelzen_nicht_ueber_eine_phase(self):
        woerter = ["OK", "OK", "TEMP_HOCH", "TEMP_KRITISCH", "OK", "TEMP_HOCH", "OK", "OK"]
        warn = [False, False, True, False, False, True, False, False]
        b = vokabular.bewerte(woerter, warn, 2)
        self.assertEqual((b["phasen"], b["vorgewarnt"], b["alarme"], b["fehlalarme"]), (1, 1, 2, 1))

    def test_richtung_teilt_nur_ok_und_hoch(self):
        temps = [360] * 25 + [370] * 25
        woerter = ["OK"] * 49 + ["TEMP_KRITISCH"]
        neu = vokabular.mit_richtung(woerter, temps, 20)
        self.assertEqual((neu[24], neu[45], neu[49]), ("OK", "TEMP_STEIGT", "TEMP_KRITISCH"))


@unittest.skipUnless(shutil.which("c++"), "Hostvergleich benötigt einen C++11-Compiler")
class SketchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.binaries = {}
        for regel in REGELN:
            out = Path(cls.tmp.name, regel)
            flags = [] if regel == "zeit" else [f"-DALEX_{regel.upper()}"]
            subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                            *flags, str(ROOT / "esp32/host.cpp"), "-o", str(out)], check=True)
            cls.binaries[regel] = out

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_sketch_paritaet_fuer_demo_und_alle_kontrollspuren(self):
        for regel, binpfad in self.binaries.items():
            eingabe, erwartet = [], ["takt,zustand,sofort,vorwarnung"]
            spuren = [beispielspur()] + [generiere(f, seed) for f in FAMILIEN for seed in range(1000,1020)]
            for spur in spuren:
                k = Knoten(REGELN[regel]())
                eingabe.append("NEUER_LAUF")
                erwartet.append("BEREIT," + regel.upper())
                for t, z in enumerate(spur, 1):
                    s = k.schritt(t, z)
                    eingabe.append(f"{t},{z}")
                    erwartet.append(f"{t},{z},{int(s.sofort)},{int(s.vorwarnung)}")
            res = subprocess.run([str(binpfad)], input="\n".join(eingabe)+"\n", text=True,
                                 capture_output=True, timeout=30, check=True)
            self.assertEqual(res.stdout.splitlines(), erwartet)

    def test_sketch_behaelt_zustand_bei_fehlerhaften_zeilen(self):
        folge = b"1,OK\r\n1,SCHWACH\n4294967296,OK\n2,OK\x00x\n" + b"X"*80 + b"\n5,AUSFALL\n"
        for exe in self.binaries.values():
            r = subprocess.run([str(exe)], input=folge, capture_output=True, timeout=5, check=True)
            self.assertEqual(r.stdout.splitlines()[1:], [b"1,OK,0,0", *([b"FEHLER"]*4), b"5,AUSFALL,1,0"])

    def test_geraetestand_ueber_prozessneustart_und_crc_fehler(self):
        spur = beispielspur()
        teile = [f"{t},{z}" for t, z in enumerate(spur, 1)]
        with tempfile.TemporaryDirectory() as ort:
            for regel, exe in self.binaries.items():
                p = Path(ort, regel)
                def replay(befehle):
                    proc = subprocess.run([str(exe)], input="\n".join(befehle)+"\n", text=True,
                                          capture_output=True, timeout=5, check=True,
                                          env=dict(os.environ, ALEX_TEST_NVS=str(p)))
                    return proc.stdout.splitlines()[1:]
                voll = replay(teile)
                self.assertEqual(replay(teile[:121]+["SICHERN", "SICHERN", "LADEN"])[-3:],
                                 ["GESICHERT", "GESICHERT", "FEHLER"])
                self.assertEqual(replay(["LADEN"]+teile[121:]), ["GELADEN"] + voll[121:])
                daten = bytearray(p.read_bytes())
                self.assertEqual(len(daten), 86)
                self.assertEqual(daten[:4], b"AG01")
                self.assertEqual(daten[4], {"zeit": 1, "kontext": 2, "erbe": 3}[regel])
                self.assertEqual(int.from_bytes(daten[82:], "little"), zlib.crc32(daten[:82]))
                self.assertEqual(int.from_bytes(daten[6:10], "little"), 121)
                k = Knoten(REGELN[regel]())
                for t, z in enumerate(spur[:121], 1):
                    k.schritt(t, z)
                for i, wert in enumerate(struct.unpack_from("<9d", daten, 10)):
                    original = k.gedaechtnis.gewichte[ZUSTAENDE[i//3]][ZUSTAENDE[i%3]]
                    self.assertAlmostEqual(wert, original, places=11)
                daten[10] ^= 1
                p.write_bytes(daten)
                self.assertEqual(replay(["LADEN", "1,OK"]), ["FEHLER", "1,OK,0,0"])
                daten[10:18] = struct.pack("<d", float("nan"))
                daten[82:] = zlib.crc32(daten[:82]).to_bytes(4, "little")
                p.write_bytes(daten)
                self.assertEqual(replay(["LADEN", "1,OK"]), ["FEHLER", "1,OK,0,0"])

    def test_geraetestand_einer_anderen_regel_wird_abgewiesen(self):
        teile = [f"{t},{z}" for t, z in enumerate(beispielspur()[:30], 1)]
        with tempfile.TemporaryDirectory() as ort:
            p = Path(ort, "stand")
            def replay(regel, befehle):
                proc = subprocess.run([str(self.binaries[regel])], input="\n".join(befehle)+"\n", text=True,
                                      capture_output=True, timeout=5, check=True,
                                      env=dict(os.environ, ALEX_TEST_NVS=str(p)))
                return proc.stdout.splitlines()[1:]
            self.assertEqual(replay("kontext", teile + ["SICHERN"])[-1], "GESICHERT")
            self.assertEqual(replay("erbe", ["LADEN"]), ["FEHLER"])
            self.assertEqual(replay("kontext", ["LADEN"]), ["GELADEN"])

    def test_boardpruefer_mit_echtem_sketch_ueber_pipes(self):
        for regel, exe in self.binaries.items():
            with subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as prozess:
                try:
                    self.assertEqual(vergleiche_board(PipePort(prozess), beispielspur(), regel), 240)
                finally:
                    prozess.stdin.close()
                    prozess.wait(timeout=5)

    def test_wiederanlauf_ueber_zwei_prozesse(self):
        spur = beispielspur()
        with tempfile.TemporaryDirectory() as ort:
            env = dict(os.environ, ALEX_TEST_NVS=str(Path(ort, "nvs")))
            def lauf(teil, grenze):
                # Jeder Teil ist ein eigener Prozess, das entspricht einem Neustart des Geräts.
                with subprocess.Popen([str(self.binaries["erbe"])], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, env=env) as prozess:
                    try:
                        return teil(PipePort(prozess), spur, "erbe", grenze)
                    finally:
                        prozess.stdin.close()
                        prozess.wait(timeout=5)
            lauf(wiederanlauf.sichern, 100)
            self.assertEqual(lauf(wiederanlauf.laden, 100), 140)
            # Ein Stand, der nicht genau an der angegebenen Grenze endet, fällt auf.
            for falsch in (90, 110):
                with self.subTest(grenze=falsch):
                    with self.assertRaises(ValueError):
                        lauf(wiederanlauf.laden, falsch)

    def test_koerpertakt_wie_python(self):
        g = koerper.ERKUNDUNG
        roh = KoerperTests.ROH + [(599, 65536, 19999), (600, 16385, 0), (None, 16384, 0)]
        befehle = ["MESSWERT 400 1 1", "GRENZEN 600 500 1 2 3 4", g.befehl().decode()]
        befehle += [f"MESSWERT {'-' if t is None else t} {h} {l}" for t, h, l in roh]
        befehle += ["MESSWERT -5 1 1", "KOERPER 1000", "LAST 1 1", "STOP"]
        for regel, exe in self.binaries.items():
            with self.subTest(regel=regel):
                erwartet = ["FEHLER", "FEHLER", "GRENZEN,ok", *KoerperTests.geraetezeilen(roh, g, regel)]
                # Negative Temperaturen gibt es nicht, Körpermodus und Last nur am Gerät.
                erwartet += ["FEHLER", "FEHLER", "FEHLER", "KOERPER,aus"]
                r = subprocess.run([str(exe)], input="\n".join(befehle) + "\n", text=True,
                                   capture_output=True, timeout=5, check=True)
                self.assertEqual(r.stdout.splitlines()[1:], erwartet)

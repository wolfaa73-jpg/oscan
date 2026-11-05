import errno
import hashlib
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

from boardprobe import vergleiche_board
from kern import Gedaechtnis, Kontextgedaechtnis, Knoten, MAX_TAKT, ZUSTAENDE
from labor import FAMILIEN, generiere
from messen import klassifizieren, probe
from neustart import kodiert, laden, sichern
from transport import Empfaenger, kanal
from versuch import RAHMEN, beispielspur, durchlauf, lies_spur, vergleiche

ROOT = Path(__file__).resolve().parent


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


class NeustartTests(unittest.TestCase):
    def test_fortsetzung_ist_schrittweise_identisch_auch_an_luecken(self):
        spur = [(t, z) for t, z in enumerate(beispielspur(), 1) if t % 13 != 0]
        with tempfile.TemporaryDirectory() as ort:
            for typ in (Gedaechtnis, Kontextgedaechtnis):
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
                             ("regel", "x"), ("vokabular", list(reversed(ZUSTAENDE)))]:
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


@unittest.skipUnless(shutil.which("c++"), "Hostvergleich benötigt einen C++11-Compiler")
class SketchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.binaries = {}
        for regel in ("zeit", "kontext"):
            out = Path(cls.tmp.name, regel)
            flags = ["-DALEX_KONTEXT"] if regel == "kontext" else []
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
                k = Knoten(Kontextgedaechtnis() if regel == "kontext" else Gedaechtnis())
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
        folge = b"1,OK\r\n1,SCHWACH\n4294967296,OK\n2,OK\x00x\n" + b"X"*40 + b"\n5,AUSFALL\n"
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
                self.assertEqual(int.from_bytes(daten[82:], "little"), zlib.crc32(daten[:82]))
                self.assertEqual(int.from_bytes(daten[6:10], "little"), 121)
                typ = Kontextgedaechtnis if regel == "kontext" else Gedaechtnis
                k = Knoten(typ())
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

    def test_boardpruefer_mit_echtem_sketch_ueber_pipes(self):
        for regel, exe in self.binaries.items():
            with subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as prozess:
                class Port:
                    def write(self, daten):
                        prozess.stdin.write(daten)
                        prozess.stdin.flush()
                    def readline(self):
                        return prozess.stdout.readline()
                try:
                    self.assertEqual(vergleiche_board(Port(), beispielspur(), regel), 240)
                finally:
                    prozess.stdin.close()
                    prozess.wait(timeout=5)

"""Bekannte Datensätze, gezielte Beschädigungen und CLI ohne Gerät."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import random
import struct
import tempfile
import unittest

import fahrt
import fahrt_pruefung as p

ROOT = Path(__file__).parent


def satz(t, *, start=False, temp=450, state=0, last=0, reiz=0, bekannt=1, grenze=80):
    # Eigenständiger Drahtformat-Aufbau; verwendet nicht den geprüften Decoder.
    return struct.pack("<IhBBhhhh", t, temp, (state << 4) | last | (64 if start else 0),
                       3 if start else 0, 4500, 4500, 0, grenze) + bytes((reiz, 0, 0, bekannt))


def daten(*rows):
    return fahrt.V2_KOPF + b"".join(rows)


class FahrtPruefungTests(unittest.TestCase):
    def test_v1_v2_und_unbekannte_alte_reize(self):
        raw = [satz(1, start=True), satz(2, last=1, reiz=1)]
        for b, fmt in ((b"".join(r[:16] for r in raw), "v1"), (daten(*raw), "v2")):
            r = p.pruefe(b)
            self.assertEqual(r["status"], "unauffaellig")
            self.assertEqual(r["eingabe"]["format"], fmt)
            self.assertEqual((r["saetze"], r["neustarts"], r["taktuebergaenge_geprueft"]), (2, 1, 1))
            self.assertEqual(r["eingabe"]["sha256"], hashlib.sha256(b).hexdigest())
        self.assertEqual(p.pruefe(daten(satz(1, last=1, bekannt=0)))["status"], "unauffaellig")

    def test_neustart_erlaubt_keinen_ruecksprung(self):
        raw = daten(satz(89), satz(90), satz(61, start=True), satz(62))
        # Der bisherige Decoder akzeptiert diese strukturell gültige Folge.
        self.assertEqual(len(list(fahrt.saetze(raw))), 4)
        r = p.pruefe(raw)
        self.assertEqual(r["befunde"], {"taktruecksprung": 1})
        self.assertEqual(r["beispiele"][0]["satz"], 3)
        self.assertEqual(r["beispiele"][0]["erwartet"], 91)
        self.assertTrue(r["beispiele"][0]["neustart"])
        self.assertEqual(p.exitcode(r), 1)

    def test_doppelte_takte_luecken_und_uint32_ueberlauf(self):
        r = p.pruefe(daten(satz(1), satz(1), satz(4)))
        self.assertEqual(r["befunde"], {"doppelter_takt": 1, "taktluecke": 1})
        self.assertEqual(r["fehlende_taktnummern"], 2)
        self.assertEqual(p.pruefe(daten(satz(0xffffffff), satz(0), satz(1)))["status"], "unauffaellig")

    def test_abgeschnittene_datei_und_reservierte_bytes(self):
        b = daten(satz(1), satz(2))
        r = p.pruefe(b[:-1])
        self.assertEqual(p.exitcode(r), 2)
        self.assertEqual(r["beispiele"][0], dict(art="unvollstaendiger_satz", byteoffset=36, restbytes=19))
        for pos, value in ((8, 3), (12, 16), (33, 1), (34, 1), (35, 2), (32, 64)):
            with self.subTest(pos=pos):
                bad = bytearray(b)
                bad[pos] = value
                self.assertEqual(p.exitcode(p.pruefe(bad)), 2)
        for n in range(1, 16):
            self.assertEqual(p.pruefe(satz(1)[:n], "v1")["status"], "formatfehler")

    def test_v2_kopf_jedes_byte_veraendert_oder_abgeschnitten(self):
        b = daten(satz(1))
        for pos in range(16):
            with self.subTest(pos=pos):
                bad = bytearray(b)
                bad[pos] ^= 1
                self.assertEqual(p.pruefe(bad, "v2")["status"], "formatfehler")
        for n in range(1, 16):
            self.assertEqual(p.pruefe(b[:n], "v2")["status"], "formatfehler")

    def test_beschaedigter_kopf_bei_erwartetem_v2(self):
        # 16 + 4*20 ist durch 16 teilbar: Die Länge schützt nicht vor beschädigter V2-Kennung.
        b = bytearray(daten(*(satz(t) for t in range(1, 5))))
        b[0] ^= 1
        self.assertEqual(p.pruefe(b, "v2")["befunde"], {"format_passt_nicht": 1})
        self.assertEqual(p.pruefe(daten(satz(1)), "v1")["befunde"], {"format_passt_nicht": 1})

    def test_ungueltige_nibbles_und_kein_erfundener_uebergang(self):
        bad = bytearray(satz(2))
        bad[7] = 16
        r = p.pruefe(daten(satz(1), bad, satz(3)))
        self.assertEqual(r["befunde"], {"satz_nicht_dekodierbar": 1})
        self.assertEqual(r["taktuebergaenge_geprueft"], 0)
        self.assertEqual(r["beispiele"][0]["byteoffset"], 36)

    def test_zustand_grenze_und_lastwiderspruch(self):
        for raw, kind in ((satz(1, state=3), "ungueltiger_zustand"),
                          (satz(1, grenze=-1), "negative_vorhersagegrenze"),
                          (satz(1, last=1, reiz=0), "widerspruechliche_lastbits")):
            with self.subTest(kind=kind):
                r = p.pruefe(daten(raw))
                self.assertEqual(p.exitcode(r), 2)
                self.assertEqual(r["befunde"], {kind: 1})

    def test_funkfehler_und_widerspruechliche_funkbits(self):
        r = p.pruefe(daten(satz(1, reiz=56)))
        self.assertEqual(r["befunde"], {"funk_sendefehler": 1})
        self.assertEqual(p.exitcode(r), 1)
        for reiz in (8, 32, 40, 48):
            r = p.pruefe(daten(satz(1, reiz=reiz)))
            self.assertEqual(p.exitcode(r), 2)
            self.assertEqual(r["befunde"]["widerspruechliche_funkbits"], 1)
        for reiz in (0, 16, 24):
            self.assertEqual(p.exitcode(p.pruefe(daten(satz(1, reiz=reiz)))), 0)

    def test_fehlende_und_unplausible_temperatur_sind_keine_formatfehler(self):
        r = p.pruefe(daten(satz(1, temp=-32768), satz(2, temp=2001)))
        self.assertEqual(r["befunde"], {"temperatur_fehlt": 1, "temperatur_unplausibel": 1})
        self.assertEqual(p.exitcode(r), 1)

    def test_keine_vorgetaeuschte_erkennung_beliebiger_bitfehler(self):
        raw = daten(satz(1))
        bad = bytearray(raw)
        bad[16 + 4] ^= 1  # Ein Temperaturbit bleibt plausibel: kein allgemeiner Integritätsnachweis.
        vorher, nachher = p.pruefe(raw), p.pruefe(bad)
        self.assertEqual(nachher["status"], "unauffaellig")
        self.assertNotEqual(vorher["eingabe"]["sha256"], nachher["eingabe"]["sha256"])

    def test_leer_ist_keine_bestaetigte_aufnahme(self):
        for b in (b"", fahrt.V2_KOPF):
            r = p.pruefe(b, "v2")
            self.assertEqual(r["status"], "leer")
            self.assertEqual(p.exitcode(r), 1)

    def test_zaehler_bleiben_vollstaendig_bei_begrenzten_beispielen(self):
        r = p.pruefe(daten(*(satz(i, temp=-32768) for i in range(100))), max_beispiele=3)
        self.assertEqual(r["befunde"]["temperatur_fehlt"], 100)
        self.assertEqual(len(r["beispiele"]), 3)
        self.assertEqual(r["beispiele_ausgelassen"], 97)

    def test_vorhandene_fahrt_42600_saetze(self):
        b = (ROOT / "beispiele/geraetelaeufe-2026-11/roh/fahrt-2026-11-11.bin").read_bytes()
        r = p.pruefe(b, "v1")
        self.assertEqual(r["status"], "unauffaellig")
        self.assertEqual((r["saetze"], r["neustarts"], r["taktuebergaenge_geprueft"]), (42600, 12, 42599))

    def test_cli_dateien_unveraendert_und_keine_privaten_pfade_im_bericht(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "quelle.bin"), Path(d, "bericht.json")
            src.write_bytes(daten(satz(1)))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(p.main([str(src), "--format", "v2", "--json", str(out)]), 0)
                original = out.read_bytes()
                self.assertEqual(p.main([str(src), "--json", str(out)]), 2)
                self.assertEqual(p.main([str(src), "--json", str(src)]), 2)
                self.assertEqual(p.main([str(Path(d, "fehlt"))]), 2)
            self.assertEqual(src.read_bytes(), daten(satz(1)))
            self.assertEqual(out.read_bytes(), original)
            self.assertNotIn(d, out.read_text())
            self.assertNotIn(src.name, out.read_text())

    def test_zufallsbytes_ergeben_immer_einen_begrenzten_bericht(self):
        rng = random.Random(20261116)
        for _ in range(1000):
            b = bytes(rng.randrange(256) for _ in range(rng.randrange(130)))
            r = p.pruefe(b, max_beispiele=2)
            json.dumps(r, allow_nan=False)
            self.assertLessEqual(len(r["beispiele"]), 2)
            self.assertIn(p.exitcode(r), (0, 1, 2))

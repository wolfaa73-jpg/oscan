import csv
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
import selbsterkundung
import vokabular
import wiederanlauf
from boardprobe import antwort, vergleiche_board
from kern import (Erbgedaechtnis, Gedaechtnis, Kontextgedaechtnis, Knoten, MAX_TAKT, REGELN,
                  Startwertgedaechtnis, ZUSTAENDE)
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


class BlickTests(unittest.TestCase):
    def test_ein_takt_ist_genau_der_ausfallanteil(self):
        for f in FAMILIEN:
            k = Knoten(Erbgedaechtnis())
            for t, z in enumerate(generiere(f, 7), 1):
                k.schritt(t, z)
                g = k.gedaechtnis
                for zustand in ZUSTAENDE:
                    zeile, erbe = g.gewichte[zustand], g.erbe[zustand]
                    beleg = sum(zeile[x] + erbe[x] for x in ZUSTAENDE)
                    direkt = (zeile["AUSFALL"] + erbe["AUSFALL"]) / beleg if beleg else 0.0
                    # Bitgleich, nicht nur ungefähr: Sonst entscheidet der Blick 1 anders als bisher.
                    self.assertEqual(g.schaetze(zustand, 1)[0].hex(), direkt.hex())

    def test_weiter_blick_von_hand_gerechnet(self):
        g = Kontextgedaechtnis()
        g.gewichte["SCHWACH"].update(SCHWACH=2.0, AUSFALL=2.0)
        g.gewichte["OK"].update(OK=3.0, SCHWACH=1.0)
        self.assertEqual([g.schaetze("SCHWACH", h)[0] for h in (1, 2, 3)], [0.5, 0.75, 0.875])
        # Von OK: erst SCHWACH mit einem Viertel, dann AUSFALL mit der Hälfte davon.
        self.assertEqual([g.schaetze("OK", h)[0] for h in (1, 2, 3)], [0.0, 0.125, 0.125 + 0.75 * 0.125 + 0.125 * 0.5])
        # Ein Zustand ohne Beleg bleibt, wie er ist.
        self.assertEqual(g.schaetze("AUSFALL", 9), (0.0, 0))

    def test_weiter_blick_waechst_mit_dem_horizont(self):
        k = Knoten(Erbgedaechtnis())
        for t, z in enumerate(generiere("Rückkehr", 2), 1):
            k.schritt(t, z)
        for zustand in ("OK", "SCHWACH"):
            werte = [k.gedaechtnis.schaetze(zustand, h)[0] for h in range(1, 61)]
            self.assertEqual(werte, sorted(werte))
            self.assertLessEqual(werte[-1], 1.0 + 1e-12)  # Rundung darf ein Bit darüber liegen

    def test_blick_hat_grenzen(self):
        for falsch in (0, 601, True, 2.0):
            with self.subTest(blick=falsch):
                with self.assertRaises(ValueError):
                    Knoten(Erbgedaechtnis(), blick=falsch)
        self.assertEqual(Knoten(Erbgedaechtnis(), blick=600).blick, 600)


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

    def test_startwert_verblasst_nur_mit_eigenen_ausgaengen(self):
        g = Startwertgedaechtnis()
        for _ in range(50):
            g.beobachte("SCHWACH", "SCHWACH")
        g.beobachte("OK", "SCHWACH")
        self.assertEqual(g.erbe["SCHWACH"]["AUSFALL"], 3)
        # Jeder Ausgang zählt, auch der in den Ausfall. Dann trägt eigene Erfahrung die Warnung.
        g.beobachte("SCHWACH", "OK")
        self.assertEqual(g.erbe["SCHWACH"]["AUSFALL"], 3 * g.faktor)
        g.beobachte("SCHWACH", "AUSFALL")
        self.assertEqual(g.erbe["SCHWACH"]["AUSFALL"], 3 * g.faktor * g.faktor)

    def test_startwert_traegt_die_erste_warnung_und_laesst_die_ausnahme_zu(self):
        self.assertTrue(Knoten(Startwertgedaechtnis()).schritt(1, "SCHWACH").vorwarnung)
        k = Knoten(Startwertgedaechtnis())
        warnt = [k.schritt(t, z).vorwarnung for t, z in enumerate(["SCHWACH", "OK"] * 4, 1)]
        # Zwei Gegenbeispiele reichen, beim festen Erbe sind es drei.
        self.assertEqual(warnt[::2], [True, True, False, False])
        g = Startwertgedaechtnis()
        for _ in range(200):
            g.beobachte("SCHWACH", "OK")
        # Das feste Erbe hält den Ausfallanteil über 0,24, der Startwert ist so gut wie fort.
        self.assertLess(g.schaetze("SCHWACH")[0], 1e-9)


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

    def test_startwert_stand_traegt_das_verblasste_erbe(self):
        with tempfile.TemporaryDirectory() as ort:
            k = Knoten(Startwertgedaechtnis())
            for t, z in enumerate(["SCHWACH", "OK"] * 3, 1):
                k.schritt(t, z)
            p = Path(ort, "stand")
            sichern(p, "A", k)
            geladen = laden(p, "A").gedaechtnis.erbe["SCHWACH"]["AUSFALL"]
            self.assertEqual(geladen, k.gedaechtnis.erbe["SCHWACH"]["AUSFALL"])
            self.assertLess(geladen, 3)
            d = json.loads(p.read_bytes())["daten"]
            # Ein Erbe wächst nie über seinen Anfang und entsteht nicht, wo die Regel keines hat.
            for i, erbe in enumerate(([[0, 0, 0], [0, 0, 3.5], [0, 0, 0]], [[0.5, 0, 0], [0, 0, 1], [0, 0, 0]],
                                      [[0, 0, 0], [0, 0, -1], [0, 0, 0]], [[0, 0, 0], [0, 0]], "3")):
                with self.subTest(erbe=erbe):
                    falsch = dict(d, erbe=erbe)
                    q = Path(ort, f"falsch-{i}")
                    q.write_bytes(kodiert(dict(daten=falsch, sha256=hashlib.sha256(kodiert(falsch)).hexdigest())))
                    with self.assertRaises(ValueError):
                        laden(q, "A")

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
    def geraetezeilen(roh, g, regel, reize=None, blick=1, knoten=None, ab=1):
        """So antwortet das Gerät, wenn es wie Python einstuft und entscheidet. Mit knoten und ab
        rechnet es von einem geladenen Stand aus weiter."""
        k = knoten or Knoten(REGELN[regel](), blick=blick)
        zeilen = []
        for takt, ((t, h, l), phase) in enumerate(zip(roh, reize or [0] * len(roh)), ab):
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

    @staticmethod
    def port(antworten, gesendet):
        """Ein Gerät, das der Reihe nach diese Zeilen sendet und alles Gesendete sammelt."""
        zeilen = iter(a + b"\r\n" for a in antworten)
        class Port:
            def write(self, daten):
                gesendet.append(daten)
            def readline(self):
                return next(zeilen, b"")
        return Port()

    def test_aufnahme_pruefung_und_neue_einstufung(self):
        phasen = [1, 1, 1, 0, 0, 0]
        antworten = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"LAST,ok", b"KOERPER,an",
                     *(z.encode() for z in self.geraetezeilen(self.ROH, self.G, "erbe", phasen))]
        gesendet = []
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "koerper.csv")
            self.assertEqual(koerper.aufnehmen(self.port(antworten, gesendet), "erbe", self.G, 1000,
                                               len(self.ROH), ziel, (3, 3)), 6)
            # Die Last startet vor dem Körpermodus, STOP beendet beides.
            self.assertLess(gesendet.index(b"LAST 3 3\n"), gesendet.index(b"KOERPER 1000\n"))
            self.assertEqual(gesendet[-1], b"STOP\n")
            meta, werte = koerper.pruefen(ziel)
            self.assertEqual((meta["last"], meta["blick"], meta["leck"]), ([3, 3], 1, None))
            self.assertEqual([w["zustand"] for w in werte], ["OK", "OK", "SCHWACH", "AUSFALL", "AUSFALL", "OK"])
            self.assertEqual([w["reiz"] for w in werte], phasen)
            self.assertIn("Unter Last (3 Takte)", koerper.bericht(meta, werte))
            locker = koerper.Grenzen(550, 700, 65536, 16384, 20000, 300000)
            self.assertEqual([z for _, z in koerper.neu_einstufen(werte, locker)],
                             ["OK", "OK", "OK", "SCHWACH", "SCHWACH", "OK"])
            with self.assertRaises(ValueError):
                koerper.aufnehmen(self.port([], []), "erbe", self.G, 1000, 1, ziel)
            ziel.write_text(ziel.read_text().replace(",SCHWACH,0,1,1", ",SCHWACH,0,0,1"))
            with self.assertRaises(ValueError):
                koerper.pruefen(ziel)

    def test_weiterlernen_ueber_zwei_aufnahmen(self):
        roh = self.ROH + [(410, 300000, 60)]
        with tempfile.TemporaryDirectory() as ort:
            erste, zweite = Path(ort, "erste.csv"), Path(ort, "zweite.csv")
            # Nach den sechs bestellten Takten kommt vor KOERPER,aus noch ein siebter. Er gehört zum Endstand.
            antworten = [b"BEREIT,STARTWERT", b"GRENZEN,ok", b"BLICK,ok", b"SICHERN_ALLE,ok", b"KOERPER,an",
                         *(z.encode() for z in self.geraetezeilen(roh, self.G, "startwert")),
                         b"KOERPER,aus", b"GESICHERT"]
            gesendet = []
            self.assertEqual(koerper.aufnehmen(self.port(antworten, gesendet), "startwert", self.G, 1000, 6, erste,
                                               sichern_alle=4), 7)
            self.assertLess(gesendet.index(b"SICHERN_ALLE 4\n"), gesendet.index(b"KOERPER 1000\n"))
            self.assertEqual(gesendet[-2:], [b"STOP\n", b"SICHERN\n"])
            meta, werte = koerper.pruefen(erste)
            self.assertEqual((meta["sichern_alle"], meta["fortsetzung"], len(werte)), (4, None, 7))
            # Das Gerät lädt den Endstand nach Takt 7 und lässt einen Takt Lücke.
            k = koerper.gelernt_bis(erste, 7)
            self.assertEqual(k.takt, 7)
            weiter = [b"BEREIT,STARTWERT", b"GRENZEN,ok", b"BLICK,ok", b"GELADEN", b"KOERPER,an",
                      *(z.encode() for z in self.geraetezeilen(self.ROH, self.G, "startwert", knoten=k, ab=9))]
            gesendet = []
            self.assertEqual(koerper.aufnehmen(self.port(weiter, gesendet), "startwert", self.G, 1000, 6, zweite,
                                               fortsetzen=erste), 6)
            self.assertLess(gesendet.index(b"LADEN\n"), gesendet.index(b"KOERPER 1000\n"))
            meta, werte = koerper.pruefen(zweite)
            self.assertEqual((meta["fortsetzung"], werte[0]["takt"]), ("erste.csv", 9))
            self.assertIn("Setzt erste.csv fort, mit dem Stand nach Takt 7.", koerper.bericht(meta, werte))
            # Ein Stand nach Takt 6 kann nicht im Gerät liegen: kein Vielfaches von 4 und nicht das Ende.
            falsch = Path(ort, "falsch.csv")
            falsch.write_text(zweite.read_text().replace("\n9,", "\n8,", 1))
            falsch.with_suffix(".json").write_text(zweite.with_suffix(".json").read_text())
            with self.assertRaises(ValueError):
                koerper.pruefen(falsch)
            with self.assertRaises(ValueError):
                koerper.aufnehmen(self.port([], []), "erbe", self.G, 1000, 1, Path(ort, "x.csv"), fortsetzen=erste)

    def test_aufnahme_mit_blick_leck_und_bremse(self):
        # Ein Leck drückt den Speicher unter beide Grenzen, danach steht die Schleife still.
        roh = [(410, 300000, 60), (410, 60000, 60), (410, 16000, 60), (410, 300000, 30000),
               (410, 300000, 250000), (410, 300000, 60)] * 4
        reize = [0, 2, 2, 4, 4, 0] * 4
        antworten = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"LECK,ok", b"BREMSE,ok", b"KOERPER,an",
                     *(z.encode() for z in self.geraetezeilen(roh, self.G, "erbe", reize, blick=5))]
        gesendet = []
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "reize.csv")
            koerper.aufnehmen(self.port(antworten, gesendet), "erbe", self.G, 1000, len(roh), ziel,
                              blick=5, leck=(4096, 12288, 3, 60, 32768, 4278255360), bremse=(10, 10, 300, 5, 60))
            reihe = [gesendet.index(b) for b in (b"GRENZEN 500 600 65536 16384 20000 200000\n", b"BLICK 5\n",
                                                b"LECK 4096 12288 3 60 32768 4278255360\n", b"BREMSE 10 10 300 5 60\n",
                                                b"KOERPER 1000\n")]
            self.assertEqual(reihe, sorted(reihe))
            meta, werte = koerper.pruefen(ziel)
            self.assertEqual((meta["blick"], meta["leck"], meta["bremse"]), (5, [4096, 12288, 3, 60, 32768, 4278255360], [10, 10, 300, 5, 60]))
            bericht = koerper.bericht(meta, werte)
            for teil in ("Blick 5 Takte", "Mit Leck (8 Takte): Temperatur", "Speicher ab 16.000 Byte",
                         "Mit Bremse (8 Takte)", "größte 250.000 µs", "In Ruhe (8 Takte)"):
                self.assertIn(teil, bericht)
            # Mit einem Takt Blick passt dieselbe Aufnahme nicht mehr zu ihren Vorwarnungen.
            daten = json.loads(ziel.with_suffix(".json").read_text())
            ziel.with_suffix(".json").write_text(json.dumps(dict(daten, blick=1)))
            with self.assertRaises(ValueError):
                koerper.pruefen(ziel)
            for falsch in (dict(blick=0), dict(blick=601), dict(leck=(1, 2, 3)), dict(leck=(1, 2, 3, 4, 5)), dict(bremse=(1, 2, 3, 4, -5))):
                with self.subTest(falsch=falsch):
                    with self.assertRaises(ValueError):
                        koerper.aufnehmen(self.port([], []), "erbe", self.G, 1000, 1, Path(ort, "x.csv"), **falsch)

    def test_aufnahme_schreibt_speicherlage_nebenher(self):
        # Am Boden des Lecks und nach der Freigabe folgt der Körperzeile eine Speicherzeile.
        roh = [(410, 300000, 60), (410, 60000, 60), (410, 17804, 60), (410, 17804, 60), (410, 363212, 60),
               (410, 363212, 60)]
        k = [z.encode() for z in self.geraetezeilen(roh, self.G, "erbe", [0, 2, 2, 2, 0, 0])]
        klein = b"SPEICHER,2,KLEIN,1,17804,17804,3968,6,179,83"
        boden = b"SPEICHER,3,BODEN,0,15740,15740,1908,6,181,85"
        frei = b"SPEICHER,5,FREI,0,363212,363212,200704,4,96,0"
        start = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"KOERPER,an"]
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "lage.csv")
            antworten = start + k[:2] + [klein] + k[2:3] + [boden] + k[3:5] + [frei] + k[5:]
            # Speicherzeilen zählen nicht als Takt.
            self.assertEqual(koerper.aufnehmen(self.port(antworten, []), "erbe", self.G, 1000, 6, ziel), 6)
            self.assertEqual(len(koerper.pruefen(ziel)[1]), 6)
            with Path(ort, "lage.speicher.csv").open(newline="") as datei:
                zeilen = list(csv.reader(datei))
            self.assertEqual(zeilen, [list(koerper.SPEICHER_KOPF)] + [z.decode().split(",")[1:]
                                                                      for z in (klein, boden, frei)])
            self.assertEqual(koerper.lies_speicherzeile(klein)["groesster"], 3968)
            # Gibt es die Speicherdatei schon, beginnt keine Aufnahme unter dem Namen.
            Path(ort, "alt.speicher.csv").write_text("bleibt\n")
            with self.assertRaises(ValueError):
                koerper.aufnehmen(self.port(antworten, []), "erbe", self.G, 1000, 6, Path(ort, "alt.csv"))
            self.assertEqual((Path(ort, "alt.speicher.csv").read_text(), Path(ort, "alt.csv").exists()),
                             ("bleibt\n", False))
            # Ohne Speicherzeilen entsteht keine Speicherdatei.
            koerper.aufnehmen(self.port(start + k, []), "erbe", self.G, 1000, 5, Path(ort, "ohne.csv"))
            self.assertFalse(Path(ort, "ohne.speicher.csv").exists())
            # Eine kaputte Speicherzeile bricht ab wie jede unerwartete Zeile.
            for falsch in (b"SPEICHER,3,BODEN,2,1,1,1,1,1,1", b"SPEICHER,3,LEER,1,1,1,1,1,1,1",
                           b"SPEICHER,3,BODEN,1,1,1,1,1,1", b"SPEICHER,3,BODEN,1,1,1,-1,1,1,1"):
                with self.subTest(falsch=falsch):
                    name = f"kaputt{len(list(Path(ort).iterdir()))}.csv"
                    with self.assertRaises(ValueError) as fehler:
                        koerper.aufnehmen(self.port(start + k[:3] + [falsch] + k[3:], []), "erbe", self.G,
                                          1000, 5, Path(ort, name))
                    self.assertIn("nach 3 Takten", str(fehler.exception))
                    self.assertFalse(Path(ort, name).with_name(Path(name).stem + ".speicher.csv").exists())

    def test_neustart_mitten_in_der_aufnahme_bleibt_erhalten(self):
        # Statt der dritten Körperzeile kommen das Startbanner, der Grund aus dem ROM und der aus der Firmware.
        start = [b"ESP-ROM:esp32s3-20210327", b"rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)",
                 b"takt,zustand,sofort,vorwarnung", b"NEUSTART,1,EINSCHALTEN"]
        antworten = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"KOERPER,an",
                     *(z.encode() for z in self.geraetezeilen(self.ROH[:2], self.G, "erbe")), *start]
        gesendet = []
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "reize.csv")
            with self.assertRaises(ValueError) as fehler:
                koerper.aufnehmen(self.port(antworten, gesendet), "erbe", self.G, 1000, 10, ziel)
            for teil in ("nach 2 Takten", "rst:0x1 (POWERON)", "NEUSTART,1,EINSCHALTEN", "reize.abbruch.txt"):
                self.assertIn(teil, str(fehler.exception))
            self.assertEqual(Path(ort, "reize.abbruch.txt").read_text().splitlines(), [z.decode() for z in start])
            self.assertEqual((gesendet[-1], len(koerper.pruefen(ziel)[1])), (b"STOP\n", 2))
            # Eine zweite Aufnahme unter demselben Namen überschreibt nichts.
            ziel.unlink()
            ziel.with_suffix(".json").unlink()
            with self.assertRaises(ValueError):
                koerper.aufnehmen(self.port(antworten, []), "erbe", self.G, 1000, 10, ziel)

    def test_aufnahme_belegt_den_port_allein(self):
        # Am echten Port lässt TIOCEXCL jedes weitere Öffnen scheitern, ein Pseudoterminal unter macOS
        # kennt das nicht. Hier wird deshalb nur geprüft, dass der Rekorder darum bittet.
        import termios

        class Port:
            def fileno(self):
                return 7
        with patch("fcntl.ioctl") as ioctl:
            koerper.exklusiv(Port())
        ioctl.assert_called_once_with(7, termios.TIOCEXCL)

    def test_aeltere_aufnahmen_bleiben_lesbar(self):
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "alt.csv")
            ziel.with_suffix(".json").write_text(json.dumps(dict(
                regel="erbe", intervall_ms=1000, grenzen=dataclasses_asdict(self.G), beginn="2026-11-05 10:11")))
            ziel.write_text(",".join(koerper.KOPF_ALT) + "\n1,1001,380,371820,326,OK,0,0\n")
            meta, werte = koerper.pruefen(ziel)
            self.assertEqual((werte[0]["reiz"], werte[0]["temp_dc"]), (0, 380))
            # Mittags hieß die Spalte noch "last" und kannte nur die Last.
            ziel.write_text(",".join(koerper.KOPF_LAST) + "\n1,1001,380,371820,326,OK,0,0,1\n")
            meta, werte = koerper.pruefen(ziel)
            self.assertEqual(werte[0]["reiz"], koerper.LAST)


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

    def test_grobe_sicht_entscheidet_wie_der_knoten_bei_jedem_blick(self):
        # Die Auswertung am Rechner und der Knoten im Gerät rechnen denselben Blick.
        anders = []
        for blick in (1, 30, 60):
            for f in FAMILIEN:
                spur = generiere(f, 3)
                je_regel = {}
                for regel, startwert in ((Erbgedaechtnis, False), (Startwertgedaechtnis, True)):
                    with self.subTest(blick=blick, familie=f, startwert=startwert):
                        knoten = Knoten(regel(), blick=blick)
                        erwartet = [knoten.schritt(t, z).vorwarnung for t, z in enumerate(spur, 1)]
                        modell = vokabular.Wortgedaechtnis(vokabular.GROBWOERTER, vokabular.GROBERBE,
                                                           startwert=startwert)
                        self.assertEqual(vokabular.warnungen(spur, modell, blick), erwartet)
                        je_regel[startwert] = erwartet
                anders.append(je_regel[False] != je_regel[True])
        # Sonst prüfte der Vergleich den Startwert nur dort, wo er wie das feste Erbe entscheidet.
        self.assertTrue(any(anders))

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

    def test_je_takt_trifft_immer_warnen_nur_die_grundrate(self):
        # Nach Läufen gezählt verliert „immer warnen“ kaum etwas, je Takt zeigt sich der Preis.
        woerter = ["OK", "OK", "TEMP_HOCH", "TEMP_KRITISCH", "OK", "OK", "OK", "OK"]
        immer = vokabular.bewerte(woerter, [not vokabular.kritisch(w) for w in woerter], 2)
        self.assertEqual((immer["vorgewarnt"], immer["fehlalarme"], immer["alarme"]), (1, 1, 2))
        self.assertEqual((immer["warnanteil"], immer["trefferquote"], immer["grundrate"]), (1.0, 2 / 7, 2 / 7))
        b = vokabular.bewerte(woerter, [False, False, True, False, False, True, False, False], 2)
        self.assertEqual((b["warnanteil"], b["trefferquote"]), (2 / 7, 0.5))

    def test_gedaechtnis_je_signal_sieht_verdeckte_vorzeichen(self):
        # Der Speicher wird knapp, während der Chip heiß ist. Das Wort des Takts ist dann TEMP_KRITISCH,
        # die feste Regel sieht das Vorzeichen nie, ein eigenes Gedächtnis für den Speicher schon.
        g = koerper.ERKUNDUNG
        roh = ([(400, 300000, 50)] * 15 + [(610, 60000, 50)] * 3 + [(610, 15000, 50)] * 2) * 4
        woerter = [vokabular.koerperwort(t, h, l, g) for t, h, l in roh]
        stufen = [vokabular.stufen_je_signal(t, h, l, g) for t, h, l in roh]
        self.assertEqual(set(woerter), {"OK", "TEMP_KRITISCH"})
        liste = {name: (warn, je) for name, warn, je in vokabular.verfahren(woerter, [t for t, _, _ in roh], 5, 20, stufen)}
        fest = vokabular.bewerte_je_signal(woerter, stufen, liste["Feste Regel"][0], 5)
        warn, je = liste["Je Signal, 5 Takte"]
        eigen = vokabular.bewerte_je_signal(woerter, stufen, warn, 5, je_signal=je)
        self.assertEqual((fest["speicher"]["phasen"], fest["speicher"]["vorgewarnt"], fest["speicher"]["warnanteil"]),
                         (4, 0, 0.0))
        self.assertEqual((eigen["speicher"]["vorgewarnt"], eigen["speicher"]["warnanteil"],
                          eigen["speicher"]["trefferquote"]), (4, 1.0, 1.0))

    def test_stufen_je_signal_passen_zum_koerperwort(self):
        # Das Körperwort ist die schwerste Stufe, bei gleicher Schwere Temperatur vor Speicher vor Schleife.
        g = koerper.ERKUNDUNG
        for t in (None, 499, 500, 600):
            for h in (16384, 16385, 65536, 65537):
                for l in (19999, 20000, 200000):
                    stufen = vokabular.stufen_je_signal(t, h, l, g)
                    schwerste = next((stufen[s] for schwere in ("AUSFALL", "SCHWACH") for s, _, _ in vokabular.SIGNALE
                                      if vokabular.grob(stufen[s]) == schwere), "OK")
                    self.assertEqual(vokabular.koerperwort(t, h, l, g), schwerste, (t, h, l))

    def test_je_signal_kein_treffer_fuer_fremde_phase(self):
        # Die Warnung beim warmen Takt trifft nur in der Gesamtzählung, weil danach der Speicher voll wird.
        woerter = ["OK", "TEMP_HOCH", "SPEICHER_KNAPP", "SPEICHER_VOLL", "OK", "OK"]
        stufen = [{s: w if w in (hoch, kritischer) else "OK" for s, hoch, kritischer in vokabular.SIGNALE}
                  for w in woerter]
        warn = [False, True, True, False, False, False]
        self.assertEqual(vokabular.bewerte(woerter, warn, 3)["trefferquote"], 1.0)
        s = vokabular.bewerte_je_signal(woerter, stufen, warn, 3)
        self.assertEqual(s["temperatur"], dict(phasen=0, vorgewarnt=0, warnanteil=1.0, trefferquote=0.0))
        self.assertEqual(s["speicher"], dict(phasen=1, vorgewarnt=1, warnanteil=1.0, trefferquote=1.0))
        self.assertEqual(s["schleife"], dict(phasen=0, vorgewarnt=0, warnanteil=None, trefferquote=None))
        self.assertEqual(s["ok"], dict(warnanteil=0.0, trefferquote=None))

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
            # macOS prüft den ersten Start eines frisch gebauten Programms, unter Last dauert das
            # Sekunden. Einmal vorab starten, damit die Fristen der Tests nur den Sketch messen.
            subprocess.run([str(out)], input=b"", capture_output=True, timeout=120, check=True)
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

    def test_sketch_paritaet_mit_weitem_blick(self):
        spuren = [beispielspur()] + [generiere(f, 1000) for f in FAMILIEN]
        for regel, binpfad in self.binaries.items():
            for blick in (2, 60):
                with self.subTest(regel=regel, blick=blick):
                    eingabe, erwartet, nah = [], ["takt,zustand,sofort,vorwarnung"], []
                    for spur in spuren:
                        k, eins = Knoten(REGELN[regel](), blick=blick), Knoten(REGELN[regel]())
                        # Ein neuer Lauf beginnt mit Blick 1, der Blick kommt danach.
                        eingabe += ["NEUER_LAUF", f"BLICK {blick}"]
                        erwartet += ["BEREIT," + regel.upper(), "BLICK,ok"]
                        for t, z in enumerate(spur, 1):
                            s = k.schritt(t, z)
                            nah.append(eins.schritt(t, z).vorwarnung != s.vorwarnung)
                            eingabe.append(f"{t},{z}")
                            erwartet.append(f"{t},{z},{int(s.sofort)},{int(s.vorwarnung)}")
                    res = subprocess.run([str(binpfad)], input="\n".join(eingabe) + "\n", text=True,
                                         capture_output=True, timeout=30, check=True)
                    self.assertEqual(res.stdout.splitlines(), erwartet)
                    # Sonst prüfte der Vergleich nur den bekannten Blick 1.
                    self.assertTrue(any(nah))

    def test_blick_befehl_und_neuer_lauf(self):
        spur = beispielspur()[:60]
        befehle = ["BLICK 0", "BLICK 601", "BLICK 30 1", "BLICK", "BLICK 600", "BLICK 60", "NEUER_LAUF"]
        befehle += [f"{t},{z}" for t, z in enumerate(spur, 1)]
        for regel, exe in self.binaries.items():
            with self.subTest(regel=regel):
                k = Knoten(REGELN[regel]())  # NEUER_LAUF setzt den Blick auf 1 zurück
                erwartet = ["FEHLER"] * 4 + ["BLICK,ok"] * 2 + ["BEREIT," + regel.upper()]
                erwartet += [f"{t},{z},{int(s.sofort)},{int(s.vorwarnung)}"
                             for t, z in enumerate(spur, 1) for s in [k.schritt(t, z)]]
                r = subprocess.run([str(exe)], input="\n".join(befehle) + "\n", text=True,
                                   capture_output=True, timeout=5, check=True)
                self.assertEqual(r.stdout.splitlines()[1:], erwartet)

    def test_reize_ablauf_am_rechner(self):
        quelle = Path(self.tmp.name, "reize.cpp")
        quelle.write_text(r'''#include "Reize.h"
#include <cstdio>
int main() {
    Bremse b;
    std::printf("%d", b.starte(10, 10, 30, 2, 2));
    for (int i = 0; i < 14; ++i) std::printf(" %u", static_cast<unsigned>(b.takt()));
    Leck l;
    std::printf("\n%d", l.starte(4096, 8192, 2, 2));
    unsigned bloecke = 0;  // Nach drei Blöcken ist der Boden erreicht.
    for (int i = 0; i < 12; ++i) {
        const Leck::Aktion a = l.takt();
        if (a == Leck::BELEGEN) {
            if (bloecke < 3) ++bloecke; else l.voll();
        } else if (a == Leck::FREIGEBEN) {
            bloecke = 0;
        }
        std::printf(" %d:%u", static_cast<int>(a), bloecke);
    }
    Bremse x;
    Leck y;
    std::printf("\n%d%d%d%d%d%d%d %d%d%d%d%d%d\n",
                x.starte(0, 0, 1, 1, 1), x.starte(10, 10, 30, 0, 1), x.starte(10, 10, 30, 1, 3601),
                x.starte(40, 10, 30, 1, 1), x.starte(10, 10, 901, 1, 1), x.starte(0, 1, 900, 3600, 3600),
                x.starte(30, 1, 30, 1, 1),
                y.starte(1023, 8192, 1, 1), y.starte(65537, 8192, 1, 1), y.starte(4096, 8191, 1, 1),
                y.starte(4096, 8192, 0, 1), y.starte(4096, 8192, 1, 3601), y.starte(65536, 8192, 3600, 3600));
    Bremse aus;
    Leck still;
    std::printf("%u %d\n", static_cast<unsigned>(aus.takt()), static_cast<int>(still.takt()));
    Leck m;  // Muster 2: nur Durchgang 1 hält am flachen Boden, jeder Durchgang ist sofort am Boden.
    std::printf("%d", m.starte(4096, 8192, 1, 1, 16384, 2));
    for (int i = 0; i < 9; ++i) {
        const Leck::Aktion a = m.takt();
        if (a == Leck::BELEGEN) m.voll();
        std::printf(" %d:%u", static_cast<int>(a), static_cast<unsigned>(m.boden / 1024));
    }
    Leck z;
    std::printf("\n%d%d%d\n", z.starte(4096, 8192, 1, 1, 8191, 1), z.starte(4096, 8192, 1, 1, 8192, 1),
                z.starte(4096, 8192, 1, 1, 0, 0xFFFFFFFFu));
    const uint32_t groessen[] = {4096, 2048, 2047, 1024, 65536, 3000};
    for (uint32_t g : groessen) std::printf(" %u", static_cast<unsigned>(Leck::kleiner(g)));
    std::printf("\n");
}
''')
        exe = Path(self.tmp.name, "reize")
        subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-I", str(ROOT / "esp32/Lernknoten"), str(quelle), "-o", str(exe)], check=True)
        zeilen = subprocess.run([str(exe)], capture_output=True, text=True, timeout=5, check=True).stdout.splitlines()
        # Bremse: Rampe 10, 20, zwei Takte bei 30, zwei Takte ohne, dann von vorn.
        self.assertEqual(zeilen[0], "1 10 20 30 30 0 0 10 20 30 30 0 0 10 20")
        # Leck (1 belegen, 2 freigeben): drei Blöcke, zwei Takte am Boden, zwei Takte frei, wieder wachsen.
        self.assertEqual(zeilen[1], "1 1:1 1:2 1:3 1:3 0:3 2:0 0:0 1:1 1:2 1:3 1:3 0:3")
        self.assertEqual(zeilen[2], "0000011 000001")
        # Ohne Start tut keiner etwas.
        self.assertEqual(zeilen[3], "0 0")
        # Muster: Durchgang 0 bis 8 KiB, Durchgang 1 nur bis 16 KiB, danach wieder tief.
        self.assertEqual(zeilen[4], "1 1:8 2:8 1:16 2:16 1:8 2:8 1:8 2:8 1:8")
        # Ein flacher Boden unter dem tiefen ist ungültig, flach 0 heißt immer tief.
        self.assertEqual(zeilen[5], "011")
        # Passt ein Block in kein Stück mehr, die Hälfte, aber nie unter minBlock.
        self.assertEqual(zeilen[6], " 2048 1024 0 0 32768 1500")

    def test_lastplan_wie_python(self):
        quelle = Path(self.tmp.name, "lastplan.cpp")
        quelle.write_text(r'''#include "Reize.h"
#include <cstdio>
#include <cstdlib>
int main(int, char **argv) {
    Lastplan p;
    p.zufall = static_cast<uint32_t>(std::strtoul(argv[1], nullptr, 10));
    const uint32_t an = static_cast<uint32_t>(std::strtoul(argv[2], nullptr, 10));
    const uint32_t aus = static_cast<uint32_t>(std::strtoul(argv[3], nullptr, 10));
    for (int i = 0; i < 400; ++i) std::printf("%u\n", static_cast<unsigned>(p.dauer(i % 2 ? aus : an)));
}
''')
        exe = Path(self.tmp.name, "lastplan")
        subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-I", str(ROOT / "esp32/Lernknoten"), str(quelle), "-o", str(exe)], check=True)
        for saat, an, aus in ((0, 120, 120), (1, 240, 240), (4294967295, 3600, 1), (20261110, 3, 7), (7, 0, 5)):
            with self.subTest(saat=saat, an=an, aus=aus):
                r = subprocess.run([str(exe), str(saat), str(an), str(aus)], capture_output=True, text=True,
                                   timeout=5, check=True)
                dauern = koerper.lastdauern(saat, an, aus, 400)
                self.assertEqual([int(z) for z in r.stdout.split()], dauern)
                if saat and an and aus:
                    # Ein Viertel bis zum vollen Wert, und nicht immer dasselbe.
                    self.assertTrue(all((h // 4 or 1) <= d <= h for d, h in zip(dauern, [an, aus] * 200)))
                    self.assertGreater(len(set(dauern[::2])), 1 if an < 4 else 2)
        self.assertEqual(koerper.lastdauern(0, 120, 60, 4), [120, 60, 120, 60])

    def test_last_mit_saat_im_befehl(self):
        antworten = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"LAST,ok", b"KOERPER,an",
                     *(z.encode() for z in KoerperTests.geraetezeilen(KoerperTests.ROH, KoerperTests.G, "erbe"))]
        gesendet = []
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "koerper.csv")
            koerper.aufnehmen(KoerperTests.port(antworten, gesendet), "erbe", KoerperTests.G, 1000,
                              len(KoerperTests.ROH), ziel, (240, 240, 77))
            self.assertIn(b"LAST 240 240 77\n", gesendet)
            self.assertEqual(json.loads(ziel.with_suffix(".json").read_text())["last"], [240, 240, 77])
            for falsch in ((240,), (240, 240, 1, 2), (3601, 1), (1, 1, 2**32)):
                with self.assertRaises(ValueError):
                    koerper.aufnehmen(KoerperTests.port(antworten, []), "erbe", KoerperTests.G, 1000,
                                      6, Path(ort, "x.csv"), falsch)

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
                # Ohne Schlüssel im NVS darf keine Meldung des Kerns zwischen die Antworten geraten.
                self.assertEqual(replay(teile[:121]+["LADEN", "SICHERN", "SICHERN", "LADEN"]),
                                 voll[:121] + ["FEHLER", "GESICHERT", "GESICHERT", "FEHLER"])
                self.assertEqual(replay(["LADEN"]+teile[121:]), ["GELADEN"] + voll[121:])
                daten = bytearray(p.read_bytes())
                # Der Startwert trägt sein verblasstes Erbe als AG02 hinter den Gewichten.
                startwert = regel == "startwert"
                n = 158 if startwert else 86
                self.assertEqual(len(daten), n)
                self.assertEqual(daten[:4], b"AG02" if startwert else b"AG01")
                self.assertEqual(daten[4], {"zeit": 1, "kontext": 2, "erbe": 3, "startwert": 4}[regel])
                self.assertEqual(int.from_bytes(daten[n - 4:], "little"), zlib.crc32(daten[:n - 4]))
                self.assertEqual(int.from_bytes(daten[6:10], "little"), 121)
                k = Knoten(REGELN[regel]())
                for t, z in enumerate(spur[:121], 1):
                    k.schritt(t, z)
                g = k.gedaechtnis
                tabellen = [g.gewichte] + ([g.erbe] if startwert else [])
                erwartet = [tab[ZUSTAENDE[i // 3]][ZUSTAENDE[i % 3]] for tab in tabellen for i in range(9)]
                for wert, original in zip(struct.unpack_from(f"<{len(erwartet)}d", daten, 10), erwartet):
                    self.assertAlmostEqual(wert, original, places=11)
                if startwert:
                    self.assertLess(g.erbe["SCHWACH"]["AUSFALL"], 3)
                daten[10] ^= 1
                p.write_bytes(daten)
                self.assertEqual(replay(["LADEN", "1,OK"]), ["FEHLER", "1,OK,0,0"])
                daten[10] ^= 1
                # NaN in den Gewichten, beim Startwert ein gewachsenes und ein neu entstandenes Erbe.
                for stelle, wert in [(10, float("nan"))] + ([(82 + 5 * 8, 3.5), (82, 0.5)] if startwert else []):
                    with self.subTest(regel=regel, stelle=stelle):
                        kaputt = bytearray(daten)
                        kaputt[stelle:stelle + 8] = struct.pack("<d", wert)
                        kaputt[n - 4:] = zlib.crc32(kaputt[:n - 4]).to_bytes(4, "little")
                        p.write_bytes(kaputt)
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

    def test_weiterlernen_ueber_zwei_prozesse(self):
        g = koerper.ERKUNDUNG
        roh = (KoerperTests.ROH * 2)[:12]
        messwerte = [f"MESSWERT {'-' if t is None else t} {h} {l}" for t, h, l in roh]
        with tempfile.TemporaryDirectory() as ort:
            for regel, exe in self.binaries.items():
                with self.subTest(regel=regel):
                    env = dict(os.environ, ALEX_TEST_NVS=str(Path(ort, regel)))
                    lauf = lambda befehle: subprocess.run([str(exe)], input="\n".join(befehle) + "\n", text=True,
                                                          capture_output=True, timeout=5, check=True,
                                                          env=env).stdout.splitlines()[1:]
                    # Gesichert wird still nach Takt 5 und 10, nicht während des Körpermodus einstellbar.
                    self.assertEqual(lauf([g.befehl().decode(), "SICHERN_ALLE 5", *messwerte]),
                                     ["GRENZEN,ok", "SICHERN_ALLE,ok", *KoerperTests.geraetezeilen(roh, g, regel)])
                    k = Knoten(REGELN[regel]())
                    for t, (temp, h, l) in enumerate(roh[:10], 1):
                        k.schritt(t, koerper.einstufen(temp, h, l, g))
                    # Ein neuer Prozess wie nach einer Stromtrennung: Stand nach Takt 10, dann eine Lücke.
                    self.assertEqual(lauf([g.befehl().decode(), "LADEN", *messwerte[:6]]),
                                     ["GRENZEN,ok", "GELADEN",
                                      *KoerperTests.geraetezeilen(roh[:6], g, regel, knoten=k, ab=12)])
                    # NEUER_LAUF vergisst Lücke und Sicherungstakt.
                    self.assertEqual(lauf([g.befehl().decode(), "LADEN", "NEUER_LAUF", g.befehl().decode(),
                                           messwerte[0], "SICHERN_ALLE x"])[2:],
                                     ["BEREIT," + regel.upper(), "GRENZEN,ok",
                                      *KoerperTests.geraetezeilen(roh[:1], g, regel), "FEHLER"])

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
        befehle += ["MESSWERT -5 1 1", "KOERPER 1000", "LAST 1 1", "LECK 4096 12288 3 60",
                    "BREMSE 10 10 300 5 60", "STOP"]
        # Mit weitem Blick auf einer längeren Folge aus Leck und Bremse.
        lang = [(410, 300000, 60), (410, 60000, 60), (410, 16000, 60), (410, 300000, 30000),
                (410, 300000, 250000), (410, 300000, 60)] * 5
        weit = [g.befehl().decode(), "BLICK 30"] + [f"MESSWERT {t} {h} {l}" for t, h, l in lang]
        for regel, exe in self.binaries.items():
            with self.subTest(regel=regel):
                erwartet = ["FEHLER", "FEHLER", "GRENZEN,ok", *KoerperTests.geraetezeilen(roh, g, regel)]
                # Negative Temperaturen gibt es nicht, Körpermodus und Reize nur am Gerät.
                erwartet += ["FEHLER"] * 5 + ["KOERPER,aus"]
                r = subprocess.run([str(exe)], input="\n".join(befehle) + "\n", text=True,
                                   capture_output=True, timeout=5, check=True)
                self.assertEqual(r.stdout.splitlines()[1:], erwartet)
                erwartet = ["GRENZEN,ok", "BLICK,ok", *KoerperTests.geraetezeilen(lang, g, regel, blick=30)]
                r = subprocess.run([str(exe)], input="\n".join(weit) + "\n", text=True,
                                   capture_output=True, timeout=5, check=True)
                self.assertEqual(r.stdout.splitlines()[1:], erwartet)


class Anlage:
    """Chip unter Dauerlast, ein Lüfter an einem Pin. Die Temperatur in Hundertstelgrad nähert sich ihrem Ziel
    um 1/anteil je Takt, der Sensor rauscht und rundet auf ganze Grad wie der des S3. Ganzzahlig wie ANLAGE_CPP."""

    def __init__(self, luefter, saat, anteil=10):
        self.wahr, self.luefter, self.zufall, self.anteil = 3900, luefter, saat, anteil

    def _zufallszahl(self):
        x = self.zufall
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.zufall = x
        return x

    def messe(self):
        return (self.wahr + self._zufallszahl() % 61 - 30 + 50) // 100 * 10

    def schritt(self, luefter_an):
        d = (3600 if luefter_an else 3950) - self.wahr
        self.wahr += d // self.anteil if d >= 0 else -((-d) // self.anteil)


ANLAGE_CPP = r'''
struct Anlage {
    int32_t wahr = 3900, anteil = 10;
    uint8_t luefter = 0;
    uint32_t zufall = 1;
    uint32_t zufallszahl() {
        zufall ^= zufall << 13;
        zufall ^= zufall >> 17;
        zufall ^= zufall << 5;
        return zufall;
    }
    int32_t messe() { return (wahr + static_cast<int32_t>(zufallszahl() % 61) - 30 + 50) / 100 * 10; }
    void schritt(bool an) { wahr += ((an ? 3600 : 3950) - wahr) / anteil; }
};
'''


def erkunde(pins, einstellungen, luefter, takte, umzug=None, fehlend=lambda t: False, anteil=10, saat=777):
    """Geschlossener Kreis aus Anlage und Erkundung: Zeilen je Takt, gemessene Temperaturen, Erkundung."""
    e = selbsterkundung.Erkundung(pins, *einstellungen)
    a = Anlage(luefter, saat, anteil)
    zeilen, temps = {}, []
    for t in range(1, takte + 1):
        if umzug and t == umzug[0]:
            a.luefter = umzug[1]
        temp = a.messe()
        temps.append(None if fehlend(t) else temp)
        zeilen[t] = e.takt(t, temps[-1])
        a.schritt(e.ein[pins.index(a.luefter)])
    return zeilen, temps, e


class ErkundungTests(unittest.TestCase):
    PINS = [4, 5, 7, 12, 21]
    EINST = (40, 40, 15, 5, 4, 300, 12345, 380)  # ruhe an mittel schwelle fenster pruefe saat warm

    def test_findet_den_luefter_regelt_und_merkt_den_umzug(self):
        zeilen, temps, e = erkunde(self.PINS, self.EINST, 12, 12000, umzug=(6000, 5))
        alle = [z for t in sorted(zeilen) for z in zeilen[t]]
        kuehlt = [z.split(",") for z in alle if z.startswith("VERSUCH,") and z.endswith(",KUEHLT")]
        # Nur die Pins mit dem Lüfter kühlen: erst 12, nach dem Umstecken 5.
        self.assertEqual({v[2] for v in kuehlt}, {"12", "5"})
        erster = min(int(v[1]) for v in kuehlt if v[2] == "12")
        neu = min(int(v[1]) for v in kuehlt if v[2] == "5")
        self.assertLess(erster, 1000)  # in der ersten Runde gefunden und zweimal nachgeprüft
        self.assertTrue(6000 < neu < 10000)
        # Dazwischen gibt Pin 12 seinen Status auf, ab dann wird wieder erkundet.
        letzte12 = [v for v in kuehlt if v[2] == "12"][-1]
        self.assertLess(int(letzte12[1]), neu)
        # Die Regelung kühlt spürbar: vor dem Umstecken und nach dem Wiederfinden wärmer als ohne Lüfter nicht.
        mittel = lambda von, bis: sum(temps[von:bis]) / (bis - von)
        self.assertLess(mittel(1000, 6000), mittel(6000, neu - 500) - 8)
        self.assertLess(mittel(neu + 500, 12000), mittel(6000, neu - 500) - 8)
        # Eingeschaltet zum Kühlen wird nur der jeweilige Kühler.
        einsatz = {z.split(",")[2] for z in alle if z.startswith("PIN,") and z.endswith(",EINSATZ")}
        self.assertEqual(einsatz, {"12", "5"})
        self.assertEqual(e.modus, "EINSATZ")
        self.assertEqual(e.nummer[e.kuehler], 5)

    def test_ohne_luefter_kuehlt_nichts_und_jeder_pin_kommt_dran(self):
        e = selbsterkundung.Erkundung(self.PINS, *self.EINST)
        a = Anlage(0, 31)
        versucht = []
        for t in range(1, 4001):
            for z in e.takt(t, a.messe()):
                if z.startswith("VERSUCH,"):
                    versucht.append(z.split(","))
            a.schritt(False)
        self.assertNotIn("KUEHLT", {v[10] for v in versucht})
        self.assertEqual(e.modus, "ERKUNDEN")
        # 4000 Takte sind 50 Versuche, also zehn Runden über fünf Pins: jeder genau zehnmal.
        self.assertEqual(sorted(v[2] for v in versucht), sorted([str(p) for p in self.PINS] * 10))

    def test_fehlender_messwert_macht_den_versuch_ungueltig(self):
        zeilen, _, e = erkunde(self.PINS, self.EINST, 12, 400, fehlend=lambda t: t == 75)
        # Takt 75 liegt im Mittelfenster des ersten Versuchs (Takt 41 bis 80, gemittelt 66 bis 80).
        versuch = [z for z in zeilen[80] if z.startswith("VERSUCH,")][0].split(",")
        self.assertEqual(versuch[4:7], ["-", "-", "-"])
        self.assertEqual(versuch[9:], ["0", "OFFEN"])
        # Auch zu heiße oder negative Werte zählen nicht.
        f = selbsterkundung.Erkundung([1], 2, 2, 1, 5, 3, 0, 1, 380)
        self.assertEqual([f.takt(t, w) for t, w in enumerate((380, 2001, 380, 390), 1)][3][-1],
                         "VERSUCH,4,1,AN,-,-,-,0,0,0,OFFEN")

    def test_ungueltige_einstellungen(self):
        gut = (2, 2, 1, 5, 3, 0, 1, 380)
        for falsch in ((0, 2, 1, 5, 3, 0, 1, 380), (2, 2, 0, 5, 3, 0, 1, 380), (2, 1, 2, 5, 3, 0, 1, 380),
                       (3601, 2, 1, 5, 3, 0, 1, 380), (2, 2, 1, 0, 3, 0, 1, 380), (2, 2, 1, 1001, 3, 0, 1, 380),
                       (2, 2, 1, 5, 2, 0, 1, 380), (2, 2, 1, 5, 9, 0, 1, 380), (2, 2, 1, 5, 3, 86401, 1, 380),
                       (2, 2, 1, 5, 3, 0, 0, 380)):
            with self.subTest(falsch=falsch), self.assertRaises(ValueError):
                selbsterkundung.Erkundung([1], *falsch)
        for pins in ([], [2, 1], [3, 3], list(range(1, 26))):
            with self.subTest(pins=pins), self.assertRaises(ValueError):
                selbsterkundung.Erkundung(pins, *gut)
        selbsterkundung.Erkundung(list(range(1, 25)), 3600, 3600, 3600, 1000, 8, 86400, 2**32 - 1, 380)

    def test_rund_und_kandidaten(self):
        self.assertEqual([selbsterkundung.rund(a, 4) for a in (-6, -5, -2, -1, 0, 1, 2, 5, 6)],
                         [-2, -1, -1, 0, 0, 0, 1, 1, 2])
        self.assertEqual(selbsterkundung.kandidaten({21: "F", 4: "M", 5: "P", 1: "U", 2: "F"}), [2, 4, 21])

    def test_am_rechner_wie_python(self):
        ungueltig = [((0, 2, 1, 5, 3, 0, 1), 1), ((2, 2, 0, 5, 3, 0, 1), 1), ((2, 1, 2, 5, 3, 0, 1), 1),
                     ((3601, 3601, 1, 5, 3, 0, 1), 1), ((2, 2, 1, 0, 3, 0, 1), 1), ((2, 2, 1, 1001, 3, 0, 1), 1),
                     ((2, 2, 1, 5, 2, 0, 1), 1), ((2, 2, 1, 5, 9, 0, 1), 1), ((2, 2, 1, 5, 3, 86401, 1), 1),
                     ((2, 2, 1, 5, 3, 0, 0), 1), ((2, 2, 1, 5, 3, 0, 1), 0), ((2, 2, 1, 5, 3, 0, 1), 25),
                     ((3600, 3600, 3600, 1000, 8, 86400, 4294967295), 24), ((1, 1, 1, 1, 3, 0, 1), 1)]
        faelle = "\n".join(f"    std::printf(\"%d\", x.starte(viele, {n}, {', '.join(map(str, w))}u, 380));"
                           for w, n in ungueltig)
        quelle = r'''#include "Erkundung.h"
#include <cstdio>
''' + ANLAGE_CPP + r'''
int main() {
    const uint8_t pins[] = {4, 5, 7, 12, 21};
    Erkundung e;
    if (!e.starte(pins, 5, 40, 40, 15, 5, 4, 300, 12345, 380)) return 1;
    Anlage a;
    a.luefter = 12;
    a.zufall = 777;
    for (uint32_t t = 1; t <= 12000; ++t) {
        if (t == 6000) a.luefter = 5;
        const int32_t temp = a.messe();
        const bool gueltig = t % 997 != 0;
        e.takt(t, gueltig, gueltig ? temp : 0);
        for (unsigned i = 0; i < e.zeilen(); ++i) std::printf("%s\n", e.zeile(i));
        unsigned luefter = 0;
        for (unsigned i = 0; i < e.anzahl(); ++i)
            if (e.pin(i) == a.luefter) luefter = i;
        a.schritt(e.an(luefter));
    }
    uint8_t viele[25];
    for (unsigned i = 0; i < 25; ++i) viele[i] = static_cast<uint8_t>(i + 1);
    Erkundung x;
''' + faelle + r'''
    std::printf("\n");
    const uint8_t verkehrt[] = {5, 4};
    std::printf("%d%d\n", x.starte(verkehrt, 2, 2, 2, 1, 5, 3, 0, 1, 380), x.starte(pins, 5, 2, 2, 1, 5, 3, 0, 1, 380));
}
'''
        with tempfile.TemporaryDirectory() as ort:
            datei, exe = Path(ort, "erkundung.cpp"), Path(ort, "erkundung")
            datei.write_text(quelle)
            subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-I",
                            str(ROOT / "esp32/Lernknoten"), str(datei), "-o", str(exe)], check=True)
            aus = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30, check=True).stdout.splitlines()
        zeilen, _, _ = erkunde(self.PINS, self.EINST, 12, 12000, umzug=(6000, 5), fehlend=lambda t: t % 997 == 0)
        erwartet = [z for t in sorted(zeilen) for z in zeilen[t]]
        self.assertGreater(len(erwartet), 500)
        self.assertTrue(any(",-,-,-," in z for z in erwartet))  # die fehlenden Messwerte kamen in Versuchen vor
        self.assertEqual(aus[:-2], erwartet)
        geht = []
        for w, n in ungueltig:
            try:
                selbsterkundung.Erkundung(list(range(1, n + 1)), *w, 380)
                geht.append("1")
            except ValueError:
                geht.append("0")
        self.assertEqual(aus[-2], "".join(geht))
        self.assertEqual(aus[-2], "0" * 12 + "11")
        self.assertEqual(aus[-1], "01")

    def test_aufnahme_mit_erkundung(self):
        g = koerper.Grenzen(380, 390, 65536, 16384, 20000, 200000)
        einst = (3, 3, 2, 5, 4, 10, 99)
        klassen = {p: "P" for p in selbsterkundung.ERLAUBTE_PINS}
        klassen.update({4: "M", 5: "F"})
        antwort_erk = b"ERKUNDUNG,ok," + ",".join(f"{p}{k}" for p, k in klassen.items()).encode()
        zeilen, temps, e = erkunde([4, 5], einst + (380,), 4, 120, anteil=2)
        # Eine Aufnahme, die genau mit einem Takt endet, in dem die Erkundung noch etwas meldet.
        ende = max(t for t, z in zeilen.items() if z and t <= 100)
        roh = [(t, 300000, 60) for t in temps[:ende]]
        k = [z.encode() for z in KoerperTests.geraetezeilen(roh, g, "erbe")]
        geraet = []
        for t, kz in enumerate(k, 1):
            geraet += [kz] + [z.encode() for z in zeilen[t]]
        start = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", antwort_erk, b"KOERPER,an"]
        self.assertIn(b"KUEHLT", b"".join(geraet))
        self.assertIn(b"EINSATZ", b"".join(geraet))
        with tempfile.TemporaryDirectory() as ort:
            ziel, gesendet = Path(ort, "erk.csv"), []
            self.assertEqual(koerper.aufnehmen(KoerperTests.port(start + geraet, gesendet), "erbe", g, 1000, ende,
                                               ziel, erkundung=einst), ende)
            self.assertLess(gesendet.index(b"ERKUNDUNG 3 3 2 5 4 10 99\n"), gesendet.index(b"KOERPER 1000\n"))
            meta, _ = koerper.pruefen(ziel)
            self.assertEqual(meta["erkundung"], dict(ruhe=3, an=3, mittel=2, schwelle=5, fenster=4, pruefe=10,
                                                     saat=99, pins={str(p): c for p, c in klassen.items()}))
            # Die Zeilen des letzten Takts kamen nach dessen Körperzeile und fehlen, das ist erlaubt.
            pins = koerper.nebendatei(ziel, ".pin.csv", koerper.PIN_KOPF)
            versuche = koerper.nebendatei(ziel, ".versuch.csv", koerper.VERSUCH_KOPF)
            self.assertEqual(pins + versuche, sorted((z for t in range(1, ende) for z in zeilen[t]),
                                                     key=lambda z: not z.startswith("PIN,")))
            soll = koerper.erkundung_pruefen(ziel, meta, koerper.lies_aufnahme(ziel)[1])
            self.assertIn("Pin 4 kühlt ab Takt", koerper.erkundung_bericht(meta, soll))
            # Eine veränderte Versuchszeile fällt auf, eine fehlende Pinzeile mitten drin auch.
            vdatei, pdatei = Path(ort, "erk.versuch.csv"), Path(ort, "erk.pin.csv")
            original = vdatei.read_text()
            vdatei.write_text(original.replace(",KUEHLT", ",KEINE", 1))
            with self.assertRaisesRegex(ValueError, "weicht von selbsterkundung.py ab"):
                koerper.pruefen(ziel)
            vdatei.write_text(original)
            zeilen_p = pdatei.read_text().splitlines()
            pdatei.write_text("\n".join(zeilen_p[:2] + zeilen_p[3:]) + "\n")
            with self.assertRaisesRegex(ValueError, "erk.pin.csv, Zeile 3"):
                koerper.pruefen(ziel)
            # Pinzeilen ohne Erkundung in der JSON passen nicht zusammen.
            json_pfad = ziel.with_suffix(".json")
            m = json.loads(json_pfad.read_text())
            del m["erkundung"]
            json_pfad.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, "keine Erkundung"):
                koerper.pruefen(ziel)
            # Ohne Erkundung bleibt die JSON wie bisher, ganz ohne das Feld.
            koerper.aufnehmen(KoerperTests.port([b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"KOERPER,an"] + k,
                                                []), "erbe", g, 1000, 3, Path(ort, "ohne.csv"))
            self.assertNotIn("erkundung", json.loads(Path(ort, "ohne.json").read_text()))
            # Antwortet das Gerät nicht mit der Pinübersicht, beginnt keine Aufnahme.
            for falsch in (b"FEHLER", b"ERKUNDUNG,ok", antwort_erk.replace(b",4M,", b",4X,"),
                           antwort_erk.replace(b",5F,", b",6F,")):
                with self.subTest(falsch=falsch), self.assertRaisesRegex(ValueError, "Erkundung nicht gestartet"):
                    koerper.aufnehmen(KoerperTests.port(start[:3] + [falsch], []), "erbe", g, 1000, 3,
                                      Path(ort, f"f{len(list(Path(ort).iterdir()))}.csv"), erkundung=einst)
            # Ungültige Einstellungen weist schon Python ab, bevor etwas gesendet wird.
            gesendet = []
            with self.assertRaises(ValueError):
                koerper.aufnehmen(KoerperTests.port(start, gesendet), "erbe", g, 1000, 3, Path(ort, "x.csv"),
                                  erkundung=(3, 3, 0, 5, 4, 10, 99))
            self.assertEqual(gesendet, [])

    def test_kaputte_pin_und_versuchszeilen_brechen_ab(self):
        g = koerper.Grenzen(380, 390, 65536, 16384, 20000, 200000)
        k = [z.encode() for z in KoerperTests.geraetezeilen([(390, 300000, 60)] * 5, g, "erbe")]
        start = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"KOERPER,an"]
        self.assertEqual(koerper.lies_pinzeile(b"PIN,7,12,1,EINSATZ"), dict(takt=7, pin=12, an=1, grund="EINSATZ"))
        self.assertEqual(koerper.lies_versuchszeile(b"VERSUCH,80,12,AUS,-,-,-,-313,17,3,KUEHLT")["mittel_hg"], -313)
        for falsch in (b"PIN,3,12,2,PROBE", b"PIN,3,12,1,LAUNE", b"PIN,3,-1,1,PROBE", b"PIN,3,12,1",
                       b"VERSUCH,3,12,AN,1,2,3,4,5,6,KUEHL", b"VERSUCH,3,12,EIN,1,2,3,4,5,6,KUEHLT",
                       b"VERSUCH,3,12,AN,-,2,3,4,5,6,KUEHLT", b"VERSUCH,3,12,AN,1,2,3,4,-5,6,KUEHLT",
                       b"VERSUCH,3,12,AN,1,2,3,4,5,6"):
            with self.subTest(falsch=falsch), tempfile.TemporaryDirectory() as ort:
                with self.assertRaises(ValueError) as fehler:
                    koerper.aufnehmen(KoerperTests.port(start + k[:3] + [falsch] + k[3:], []), "erbe", g, 1000, 5,
                                      Path(ort, "a.csv"))
                self.assertIn("nach 3 Takten", str(fehler.exception))
                self.assertFalse(Path(ort, "a.pin.csv").exists() or Path(ort, "a.versuch.csv").exists())

    def test_pins_lesen(self):
        klassen = {p: "F" for p in selbsterkundung.ERLAUBTE_PINS}
        klassen[12] = "M"
        zeile = b"PINS," + ",".join(f"{p}{k}" for p, k in klassen.items()).encode()
        gesendet = []
        self.assertEqual(koerper.pins_lesen(KoerperTests.port([b"BEREIT,STARTWERT", zeile], gesendet), "startwert"),
                         klassen)
        self.assertEqual(gesendet[-1], b"PINS\n")
        with self.assertRaises(ValueError):
            koerper.pins_lesen(KoerperTests.port([b"BEREIT,STARTWERT", b"FEHLER"], []), "startwert")


class KunstkoerperTests(unittest.TestCase):
    def test_lastreihe_folgt_dem_lastplan(self):
        import itertools
        import kunstkoerper
        reihe = kunstkoerper.lastreihe(5000, 240, 240, 20261110)
        laengen = [len(list(g)) for _, g in itertools.groupby(reihe)]
        self.assertEqual(len(reihe), 5000)
        self.assertEqual(reihe[0], 1)
        self.assertEqual(laengen[:-1], koerper.lastdauern(20261110, 240, 240, len(laengen) - 1))
        self.assertEqual(kunstkoerper.lastreihe(500, 120, 120, 0), ([1] * 120 + [0] * 120) * 2 + [1] * 20)

    def test_gemessene_umgebung_trifft_ihre_kennzahlen(self):
        import kunstkoerper
        last = kunstkoerper.lastreihe(14400, 240, 240, 20261110)
        temp = kunstkoerper.temperaturen(last, saat=7)
        self.assertEqual(temp, kunstkoerper.temperaturen(last, saat=7))
        self.assertTrue(all(t == int(t) for t in temp))
        wechsel = sum(a != b for a, b in zip(temp, temp[1:])) / (len(temp) - 1)
        an = [t for t, bit in zip(temp, last) if bit]
        aus = [t for t, bit in zip(temp, last) if not bit]
        # Echte erste Hälfte am 10.11.: 178 Wechsel je 1.000 Takte, unter Last 1,34 °C wärmer als in Ruhe.
        self.assertTrue(0.13 < wechsel < 0.23, wechsel)
        self.assertTrue(1.0 < sum(an) / len(an) - sum(aus) / len(aus) < 1.7)

    def test_alte_annahme_und_ungerundet(self):
        import kunstkoerper
        last = kunstkoerper.lastreihe(2000, 240, 240, 20261110)
        alt = kunstkoerper.temperaturen(last, 15, 1.7, drift=1.0, saat=3)
        roh = kunstkoerper.temperaturen(last, stufe=0, saat=3)
        self.assertNotEqual(alt, kunstkoerper.temperaturen(last, 15, 1.7, saat=3))
        self.assertTrue(any(t != int(t) for t in roh))

    def test_schreibt_eine_lesbare_aufnahme(self):
        import kunstkoerper
        with tempfile.TemporaryDirectory() as ordner:
            ziel = Path(ordner) / "kunst.csv"
            self.assertEqual(kunstkoerper.main([str(ziel), "--takte", "300", "--saat", "5"]), 0)
            meta, werte = koerper.lies_aufnahme(ziel)
            self.assertTrue(meta["kuenstlich"])
            self.assertEqual(len(werte), 300)
            self.assertEqual([w["reiz"] for w in werte], kunstkoerper.lastreihe(300, 240, 240, 20261110))
            with self.assertRaises(FileExistsError):
                kunstkoerper.main([str(ziel), "--takte", "300"])

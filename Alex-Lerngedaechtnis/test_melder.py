import json
import tempfile
import unittest
from pathlib import Path

import koerper
from melder import Melder
import test_labor


class MelderTests(unittest.TestCase):
    @staticmethod
    def zeile(takt, zustand="OK", sofort=0, vorwarnung=0):
        return dict(takt=takt, zustand=zustand, sofort=sofort, vorwarnung=vorwarnung)

    def test_meldet_nur_wechsel_und_herzschlag(self):
        jetzt, gesendet = [100.0], []
        m = Melder(lambda t: gesendet.append(json.loads(t)), herzschlag=30, uhr=lambda: jetzt[0])
        for takt, zustand, warnung, sekunde in ((1, "OK", 0, 100), (2, "OK", 0, 101), (3, "OK", 1, 102),
                                                (4, "OK", 1, 120), (5, "OK", 1, 133), (6, "AUSFALL", 0, 134)):
            jetzt[0] = sekunde
            m.takt(self.zeile(takt, zustand, int(zustand == "AUSFALL"), warnung))
        m.ende()
        self.assertEqual([g.get("takt") for g in gesendet], [1, 3, 5, 6, None])
        self.assertEqual((gesendet[1]["vorwarnung"], gesendet[3]["zustand"], gesendet[3]["sofort"]), (1, "AUSFALL", 1))
        self.assertEqual([g["aktiv"] for g in gesendet], [True] * 4 + [False])

    def test_fehler_beim_senden_stoeren_nicht(self):
        def kaputt(text):
            raise OSError("Broker weg")
        m = Melder(kaputt)
        m.takt(self.zeile(1))
        m.ende()

    def test_aufnahme_meldet_jeden_wechsel(self):
        k = test_labor.KoerperTests
        antworten = [b"BEREIT,ERBE", b"GRENZEN,ok", b"BLICK,ok", b"KOERPER,an",
                     *(z.encode() for z in k.geraetezeilen(k.ROH, k.G, "erbe"))]
        gesendet = []
        m = Melder(lambda t: gesendet.append(json.loads(t)), herzschlag=1e9)
        with tempfile.TemporaryDirectory() as ort:
            ziel = Path(ort, "koerper.csv")
            self.assertEqual(koerper.aufnehmen(k.port(antworten, []), "erbe", k.G, 1000, len(k.ROH), ziel,
                                               melder=m), 6)
            werte = koerper.lies_aufnahme(ziel)[1]
        # Gemeldet wird genau dort, wo sich der Stand gegenüber dem vorigen Takt ändert.
        stand = [(w["zustand"], w["sofort"], w["vorwarnung"]) for w in werte]
        erwartet = [w["takt"] for i, w in enumerate(werte) if i == 0 or stand[i] != stand[i - 1]]
        self.assertEqual([g.get("takt") for g in gesendet], erwartet + [None])
        self.assertFalse(gesendet[-1]["aktiv"])


if __name__ == "__main__":
    unittest.main()

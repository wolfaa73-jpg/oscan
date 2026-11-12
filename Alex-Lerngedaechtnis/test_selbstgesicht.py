"""Selbstgesicht: Der Rechenkern des Displays (esp32/Selbstgesicht/Selbst.h) gegen die Python-Referenzen,
und sein Protokoll gegen die vorhandenen Lesewerkzeuge. Künstliche Eingänge, kein Gerät."""
import random
import subprocess
import tempfile
import unittest
from pathlib import Path

import empfinden as em
import empfinden_auswertung
import fahrt
import selbstvorhersage as sv

ROOT = Path(__file__).parent
NEUSTARTS = (4500, 6000)  # nach so vielen Takten fällt der Strom aus; Vielfache von 30 wie auf dem Gerät


def eingang(n=7500, saat=7):
    """Chip um 45 °C mit eigener Last, ein Kälteeinbruch, ein paar nicht lesbare Werte."""
    z = random.Random(saat)
    temp, last, t, an, rest = [], [], 45.0, 0, 0
    for i in range(n):
        if not rest:
            an, rest = 1 - an, z.randint(60, 240)
        rest -= 1
        ziel = 45.0 + 1.5 * an - (9.0 if 5200 <= i < 5350 else 0.0)
        t += (ziel - t) / 40 + z.gauss(0, 0.05)
        temp.append(None if i in (17, 3000, 3001, 5210) else round(t * 10))
        last.append(an)
    return temp, last


def geraet(temp, last):
    with tempfile.TemporaryDirectory() as ordner:
        prog = Path(ordner) / "selbst"
        subprocess.run(["c++", "-std=c++17", "-O2", "-ffp-contract=off", "-o", str(prog),
                        str(ROOT / "esp32/Selbstgesicht/host.cpp")], check=True)
        zeilen = []
        for i, (t, l) in enumerate(zip(temp, last)):
            if i in NEUSTARTS:
                zeilen.append("N")
            zeilen.append(f"{-32768 if t is None else t} {l}")
        return subprocess.run([str(prog)], input="\n".join(zeilen) + "\n", capture_output=True, text=True,
                              check=True).stdout.splitlines()


class SelbstgesichtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp, cls.last = eingang()
        aus = geraet(cls.temp, cls.last)
        cls.licht = aus.pop()
        cls.vorhersage = [z for z in aus if z.startswith("VORHERSAGE,")]
        cls.empfinden = [z for z in aus if z.startswith("EMPFINDEN,")]
        cls.gesicht = [z.split(",") for z in aus if z.startswith("GESICHT,")]
        cls.saetze = b"".join(bytes.fromhex(z) for z in aus if len(z) == 40 and "," not in z)

    def test_zeilen_gleich_python(self):
        v, e = sv.Selbstvorhersage(), em.Empfinden()
        soll_v, soll_e = [], []
        for i, (t, l) in enumerate(zip(self.temp, self.last)):
            if i in NEUSTARTS:
                e.neustart()
            aus = v.takt(t, l)
            if aus is not None:
                soll_v.append(sv.zeile(i + 1, aus))
            soll_e.append(em.zeile(i + 1, e.takt(t, None if aus is None else aus["mittel"])))
        self.assertEqual(len(self.empfinden), len(self.temp))
        self.assertEqual(self.vorhersage, soll_v)
        self.assertEqual(self.empfinden, soll_e)
        # Der Lauf muss etwas zeigen, sonst prüft die Gleichheit nur Nullen.
        stufen = [int(z.split(",")[2]) for z in self.empfinden]
        self.assertLessEqual(min(stufen[5200:5400]), -2)
        self.assertTrue(all(s == 0 for s in stufen[:1800]))

    def test_protokoll_lesbar_und_nachrechenbar(self):
        self.assertEqual(len(self.saetze), 20 * len(self.temp))
        with tempfile.TemporaryDirectory() as ordner:
            pfad = Path(ordner) / "selbst.bin"
            pfad.write_bytes(fahrt.V2_KOPF + self.saetze)
            liste = list(fahrt.saetze(pfad.read_bytes()))
            _, _, zeilen = empfinden_auswertung.fahrt_lauf(pfad, details=True)
        self.assertEqual([s["temp_dc"] for s in liste], self.temp)
        self.assertEqual([s["last"] for s in liste], self.last)
        self.assertEqual([s["reiz"] for s in liste], self.last)
        self.assertEqual([i for i, s in enumerate(liste) if s["neustart"]], [0, *NEUSTARTS])
        self.assertEqual([s["bei_null"] for s in liste if s["neustart"]], [1, 0, 0])
        self.assertTrue(all(s["zustand"] == "OK" and not s["vorwarnung"] and not s["sofort"] for s in liste))
        # Aus dem Protokoll allein kommt dieselbe Empfindung heraus wie auf dem Gerät.
        self.assertEqual([em.zeile(z["takt"], z["neu"]) for z in zeilen], self.empfinden)
        for s, zeile in zip(liste, self.empfinden):
            g, w, anlauf, gueltig = map(int, zeile.split(",")[2:6])
            if "gerade" in s:
                self.assertEqual((s["gerade"], s["woanders"]), (max(-7, min(7, g)), max(-7, min(7, w))))
            else:
                self.assertTrue(s["neustart"] or anlauf or not gueltig)

    def test_gesicht_folgt_dem_empfinden(self):
        for g, zeile, t in zip(self.gesicht, self.empfinden, self.temp):
            gerade, woanders, anlauf = map(int, zeile.split(",")[2:5])
            self.assertEqual(int(g[2]), -32768 if t is None else t)
            self.assertEqual((int(g[3]), int(g[4])), (gerade, woanders))
            self.assertEqual(int(g[5]), anlauf | (2 if abs(gerade) >= 2 else 0))
            self.assertEqual(g[6], "MESSUNG FEHLT" if t is None else "ANLAUF" if anlauf
                             else "ueberrascht" if abs(gerade) >= 2 else "ruhig")

    def test_lichtplan_wechselt_in_den_gesetzten_abstaenden(self):
        _, wechsel, hell = self.licht.split(",")
        # 100.000 Takte, Phasen gleichverteilt 60 bis 240 Takte: im Mittel 150, also rund 667 Wechsel.
        self.assertTrue(600 <= int(wechsel) <= 740)
        self.assertTrue(45000 <= int(hell) <= 55000)


if __name__ == "__main__":
    unittest.main()

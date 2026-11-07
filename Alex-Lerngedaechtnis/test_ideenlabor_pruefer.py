"""Jeder im Papier benannte absichtliche Defekt besitzt einen Gegenfall."""
import unittest
from ideenlabor_basis import Prueffehler, ziehung
from ideenlabor_pruefer import *

class Defektpruefer(unittest.TestCase):
    def a(self):
        return {"eingabe": {"x": 1}, "belege": [(1, 1, 0)], "rettungen": 0,
                "kosten": 1, "gewertet": True, "gestoert": False}

    def test_a_erfundener_gegenausgang(self):
        e=self.a(); e["belege"].append((1, 0, 0))
        with self.assertRaises(Prueffehler): a_beleg(e, 1, 1, 0)

    def test_a_jeder_erfolg_als_rettung(self):
        e=self.a(); e["rettungen"]=1
        with self.assertRaises(Prueffehler): a_beleg(e, 1, 1, 0)

    def test_a_versteckte_weltkennung(self):
        e=self.a(); e["eingabe"]["welt"]="hilfreich"
        with self.assertRaises(Prueffehler): a_beleg(e, 1, 1, 0)

    def test_a_unbekannt_aus_nenner(self):
        with self.assertRaises(Prueffehler): a_vollstaendig([self.a()], 2, [])

    def test_a_verfahrensabhaengige_stoerung(self):
        with self.assertRaises(Prueffehler): a_vollstaendig([self.a()], 1, [1])

    def test_b_ausgang_vor_prognose(self):
        with self.assertRaises(Prueffehler):
            b_reihenfolge(("eingabe", "ausgang", "prognose", "lernen"),
                          {"wort":"KNAPP", "x":0, "z":1})

    def test_b_geheimes_merkmal_oder_wechsel(self):
        for name in ("c", "wechsel"):
            with self.subTest(name=name), self.assertRaises(Prueffehler):
                eingabe({"wort":"KNAPP", "x":0, "z":1, name:1}, "B")

    def test_b_heimlicher_wortwechsel(self):
        with self.assertRaises(Prueffehler): b_wahl("z", "x", 300)

    def test_b_kostenlose_suchfenster(self):
        with self.assertRaises(Prueffehler): b_speicher(bytes(195), 90)

    def test_b_eingefrorene_ergebnisfenster(self):
        with self.assertRaises(Prueffehler): b_globalfenster([(0,0,0)], [(0,0,0)], (0,0,1))

    def test_c_ausnahme_weggelassen(self):
        with self.assertRaises(Prueffehler): c_rekonstruktion({1:(0,0,0)}, {1:(0,0,1)})

    def test_c_quelle_vertauscht(self):
        with self.assertRaises(Prueffehler): c_antwort("quelle", 1, 1, {1:(0,0,1)}, [])

    def test_c_neue_regel_rueckwirkend(self):
        with self.assertRaises(Prueffehler):
            c_rekonstruktion({1:(0,0,1),2:(0,0,1)}, {1:(0,0,0),2:(0,0,1)})

    def test_c_versteckter_zusatzspeicher(self):
        with self.assertRaises(Prueffehler): c_zustand({"abbild":bytes(8), "cache":{1:1}}, 32)

    def test_c_widerruf_in_kurzfassung_ignoriert(self):
        with self.assertRaises(Prueffehler): c_antwort("historie", 1, 1, {1:(0,0,1)}, [1])

    def test_korrekte_vertraege_werden_akzeptiert(self):
        a_beleg(self.a(), 1, 1, 0); a_vollstaendig([self.a()], 1, [])
        b_reihenfolge(("eingabe","prognose","ausgang","lernen"), {"wort":"KNAPP","x":0,"z":1})
        b_wahl("x", "x", 300); b_speicher(bytes(195), 195)
        b_globalfenster([], [(0,0,1)], (0,0,1)); c_zustand(bytes(32), 32)
        c_rekonstruktion({1:(0,0,1)}, {1:(0,0,1)})
        c_antwort("historie", 1, "WIDERRUFEN", {1:(0,0,1)}, [1])

    def test_pruefseeds_vor_freeze_gesperrt(self):
        with self.assertRaises(Prueffehler): ziehung("B", "pruefung", 0, "basis", 1, "x", 2)

if __name__ == "__main__": unittest.main()

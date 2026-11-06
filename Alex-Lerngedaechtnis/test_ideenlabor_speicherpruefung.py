import unittest
from ideenlabor_basis import Prueffehler
from ideenlabor_pruefer import b_speicher
import ideenlabor_b as b
import ideenlabor_speicherpruefung as p

class SpeicherNachpruefung(unittest.TestCase):
    def test_alle_handfolgen_methoden_und_varianten(self):
        self.assertEqual(p.handfolgen(),73728)

    def test_gekuerzter_serializer_passiert_alt_aber_scheitert_neu(self):
        class Gekuerzt(b.Modell):
            def bild(self): return super().bild()[:67]
        modell=Gekuerzt("kandidat","blatt32")
        bild=modell.bild(); b_speicher(bild,len(bild))
        with self.assertRaises(Prueffehler): p.zustand_pruefen(modell)

    def test_unbekannter_modellcache_wird_abgelehnt(self):
        modell=b.Modell("kandidat","blatt32"); modell.cache=bytes(4096)
        with self.assertRaises(Prueffehler): p.zustand_pruefen(modell)

    def test_unbekannter_blattcache_wird_abgelehnt(self):
        modell=b.Modell("x","blatt32"); modell.fenster["x"][0].cache=[1]
        with self.assertRaises(Prueffehler): p.zustand_pruefen(modell)

    def test_globaler_kandidat_darf_keine_unbilanzierten_blattfenster_halten(self):
        modell=b.Modell("kandidat","global128"); modell.fenster["x"][0]=b.Ring()
        with self.assertRaises(Prueffehler): p.zustand_pruefen(modell)

    def test_redundante_pending_prognose_muss_rekonstruierbar_bleiben(self):
        modell=b.Modell("xz","blatt32")
        modell.prognose({"wort":"KNAPP","x":0,"z":0})
        modell.offen[2]["xz"]=0
        with self.assertRaises(Prueffehler): p.zustand_pruefen(modell)

    def test_publizierte_groessen_gegen_analytische_oracle(self):
        zeile={"methode":"kandidat","variante":"blatt32","wahl":"x",
               "spitze_bytes":207,"nach_auswahl_bytes":102,"ende_bytes":102}
        self.assertEqual(p.rohzeilen_pruefen([zeile]),1)
        zeile["spitze_bytes"]=102
        with self.assertRaises(Prueffehler): p.rohzeilen_pruefen([zeile])

if __name__=="__main__": unittest.main()

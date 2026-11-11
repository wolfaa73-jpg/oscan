import unittest
import empfinden_vergleich as v

class VergleichTests(unittest.TestCase):
    def zeile(self,takt,anlauf,w):
        return dict(takt=takt,n=2000,nw=0,ng=0,alt=1,alte_grenze_mg=800,neu=[2,w,anlauf,1,200,500,37000,37000])

    def test_nenner_und_led_stufe_eins(self):
        a=[self.zeile(3,1,0),self.zeile(4,0,1)]
        b=[self.zeile(3,0,-1),self.zeile(4,0,1)]
        r=v.vergleich(a,b)
        self.assertEqual(r['1']['eigen']['n'],1)
        self.assertEqual(r['2']['eigen']['n'],2)
        self.assertEqual(r['2']['gemeinsam']['n'],1)
        self.assertEqual(r['1']['nach_kalt']['wort_gesperrt'],1)
        self.assertEqual(r['2']['eigen']['woanders_ab_2'],0)
        self.assertEqual(r['2']['eigen']['woanders_led_aktiv'],2)
        self.assertEqual(r['2']['eigen']['woanders_led_impulse'],1)
        self.assertEqual(r['1']['nach_kalt']['alt'],2)

    def test_nicht_ausgerichtete_lauefe_abgelehnt(self):
        with self.assertRaises(ValueError): v.vergleich([self.zeile(3,0,1)],[self.zeile(4,0,1)])

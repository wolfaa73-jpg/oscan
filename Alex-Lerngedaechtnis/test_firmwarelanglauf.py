import random
import sys
import unittest

from firmwarelanglauf import abschnitt,klassifiziere,schrittvorgabe


class LanglaufTests(unittest.TestCase):
    def test_neustart_setzt_den_gespeicherten_lernstand_fort(self):
        rng=random.Random('kunstprobe')
        a,_=abschnitt('startwert',rng,1,64,total=128,tail=8)
        b,d=abschnitt('startwert',rng,65,128,a.saved,total=128,tail=8)
        durch,_=abschnitt('startwert',random.Random('kunstprobe'),1,128,total=128,tail=8)
        self.assertEqual(b.commands[:3],['NEUER_LAUF','BLICK 1','LADEN'])
        self.assertEqual(b.node.takt,durch.node.takt)
        self.assertEqual(b.node.gedaechtnis.gewichte,durch.node.gedaechtnis.gewichte)
        self.assertEqual(b.node.gedaechtnis.erbe,durch.node.gedaechtnis.erbe)
        self.assertEqual((d['horizon1'],d['horizon600']),(56,8))
        self.assertEqual(b.counts['observations'],64)
        self.assertEqual(b.counts['loads'],1)

    def test_regelmaessige_ausgaenge_ohne_luecke(self):
        rng=random.Random(1)
        self.assertEqual([schrittvorgabe(rng,i) for i in (1,2,3)],
            [('OK',1,True),('SCHWACH',1,True),('AUSFALL',1,True)])
        self.assertGreater(schrittvorgabe(rng,997)[1],1)

    def test_keine_vorzeitige_umschaltung_auf_600(self):
        o,d=abschnitt('erbe',random.Random(2),1,20,total=40,tail=10)
        self.assertNotIn('BLICK 600',o.commands)
        self.assertEqual((d['horizon1'],d['horizon600']),(20,0))

    def test_subnormal_ist_nicht_null(self):
        self.assertEqual(klassifiziere(sys.float_info.min),'normal')
        self.assertEqual(klassifiziere(float.fromhex('0x0.0000000000001p-1022')),'subnormal')
        self.assertEqual(klassifiziere(0.0),'null')
        self.assertEqual(klassifiziere(float('nan')),'ungueltig')


if __name__=='__main__':
    unittest.main()

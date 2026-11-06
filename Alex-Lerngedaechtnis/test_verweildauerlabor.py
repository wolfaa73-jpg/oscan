import tempfile
import unittest
from pathlib import Path

import signallabor as s
import verweildauerlabor as v


class VerweildauerLaborTests(unittest.TestCase):
    def test_bestehende_hohe_signalwertung_bleibt_unveraendert(self):
        e = s.Einstellungen(takte=90, horizont=5)
        stufen = s.generiere('ueberlagerung', 900001, 'entwicklung', e)
        neu = {(r['sicht'],r['verfahren'],r['signal'],r['maske']):r for r in v.zeilen(stufen,e)}
        for alt in s.auswerten(stufen,e):
            maske = 'nichtkritisch' if alt['signal']=='gesamt' else 'hoch'
            r = neu[alt['sicht'],alt['verfahren'],alt['signal'],maske]
            # Verdeckt ist lediglich ein bisheriger Zusatzdiagnosezähler, nicht
            # Bestandteil des neuen Kennzahlenvergleichs.
            for feld in s.ZAEHLER[:-1]:
                self.assertEqual(r[feld],alt[feld])

    def test_immer_warnen_hat_sichtabhaengige_semantik(self):
        stufen = [dict(temperatur='TEMP_KRITISCH',speicher='SPEICHER_KNAPP',schleife='OK')]*10
        e = s.Einstellungen(takte=90,horizont=2)
        rows = list(v.zeilen(stufen,e))
        for sicht, erwartet in [('grob',0),('je_signal',8)]:
            r = next(r for r in rows if r['sicht']==sicht and r['signal']=='speicher'
                     and r['maske']=='hoch' and r['verfahren']=='Immer warnen')
            self.assertEqual(r['auswertbar'],8)
            self.assertEqual(r['warntakte'],erwartet)

    def test_zukunftsrand_und_kostenbegriffe(self):
        stufen = [dict(temperatur='OK',speicher='OK',schleife='OK') for _ in range(6)]
        stufen[-1]['speicher']='SPEICHER_VOLL'
        e = s.Einstellungen(takte=90,horizont=2)
        rows = list(v.zeilen(stufen,e))
        r = next(r for r in rows if r['sicht']=='je_signal' and r['signal']=='speicher'
                 and r['maske']=='nichtkritisch' and r['verfahren']=='Nie warnen')
        self.assertEqual((r['takte'],r['zieltakte'],r['verpasste_zieltakte']), (4,1,1))
        self.assertEqual(v.kennzahlen(r)['taktkosten10_pro1000'],2500)
        self.assertEqual(v.kennzahlen(r)['phasenkosten10_pro1000'],0)  # Phase liegt im Zukunftsrand

    def test_neue_kontrolle_braucht_freeze_bevor_spuren_entstehen(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d,'kontrolle')
            with self.assertRaises(ValueError):
                v.run('kontrolle',out)
            self.assertFalse(out.exists())


if __name__=='__main__':
    unittest.main()

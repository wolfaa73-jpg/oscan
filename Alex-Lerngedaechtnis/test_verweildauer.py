import unittest

from verweildauer import Verweildauergedaechtnis
from vokabular import GROBWOERTER, GROBERBE, Wortgedaechtnis, warnungen


def fuettere(modell, woerter):
    vorher = modell.aktuell
    for wort in woerter:
        modell.beobachte(vorher, wort)
        vorher = wort


class VerweildauerTests(unittest.TestCase):
    def modell(self, **kwargs):
        return Verweildauergedaechtnis(GROBWOERTER, (), **kwargs)

    def test_dauer_drei_wird_nicht_ein_takt(self):
        m = self.modell()
        fuettere(m, ['OK'] + ['SCHWACH'] * 3 + ['AUSFALL', 'OK', 'SCHWACH'])
        self.assertEqual(m.kritisch_binnen('SCHWACH', 2), 0)
        self.assertEqual(m.kritisch_binnen('SCHWACH', 3), 1)
        fuettere(m, ['SCHWACH'])
        self.assertEqual(m.kritisch_binnen('SCHWACH', 1), 0)
        self.assertEqual(m.kritisch_binnen('SCHWACH', 2), 1)
        fuettere(m, ['SCHWACH'])
        self.assertEqual(m.kritisch_binnen('SCHWACH', 1), 1)

    def test_verweilen_altert_richtung_und_erbe_nicht(self):
        m = Verweildauergedaechtnis(GROBWOERTER, GROBERBE)
        fuettere(m, ['OK', 'SCHWACH', 'OK', 'SCHWACH'])
        richtung, erbe = m.richtung['SCHWACH'].copy(), m.erbe['SCHWACH'].copy()
        fuettere(m, ['SCHWACH'] * 100)
        self.assertEqual(m.richtung['SCHWACH'], richtung)
        self.assertEqual(m.erbe['SCHWACH'], erbe)
        self.assertEqual(m.beleg('SCHWACH'), 0)  # keine beobachtete so lange Dauer

    def test_unvollstaendiger_erster_lauf_ist_keine_vollstaendige_dauer(self):
        m = self.modell()
        fuettere(m, ['OK'] * 20)
        self.assertEqual(m.beleg('OK'), 0)
        fuettere(m, ['SCHWACH'])
        self.assertFalse(m.dauer['OK'])
        self.assertEqual(m.richtung['OK']['SCHWACH'], 1)
        self.assertFalse(m.dauer['SCHWACH'])  # noch kein Ausgang

    def test_rueckweg_braucht_die_beobachtete_ruhe(self):
        m = self.modell()
        fuettere(m, ['AUSFALL'] + ['OK'] * 5 + ['SCHWACH'] * 3 + ['AUSFALL', 'OK'])
        self.assertEqual(m.kritisch_binnen('OK', 7), 0)
        self.assertEqual(m.kritisch_binnen('OK', 8), 1)

    def test_ausgaenge_zaehlen_jeden_abgeschlossenen_lauf_einmal(self):
        m = self.modell(halbwertszeit=1e300)
        fuettere(m, ['OK'] + (['SCHWACH'] * 50 + ['OK']) * 4)
        self.assertEqual(m.richtung['SCHWACH']['OK'], 4)
        self.assertEqual(m.dauer['SCHWACH'][50], 4)

    def test_korrelation_von_dauer_und_richtung_wird_nicht_erfunden(self):
        m = self.modell(halbwertszeit=1e300)
        fuettere(m, ['OK', 'SCHWACH', 'AUSFALL', 'OK'] + ['SCHWACH'] * 3 +
                 ['OK'] + ['SCHWACH'] * 3)
        # Nur der lange Lauf endete in OK; das getrennte Modell kennt die
        # Kopplung absichtlich nicht. Diese Grenze ist Bestandteil des Plans.
        self.assertEqual(m.kritisch_binnen('SCHWACH', 1), 0.5)

    def test_erbe_verblasst_nur_beim_ausgang(self):
        m = Verweildauergedaechtnis(GROBWOERTER, GROBERBE, halbwertszeit=1)
        fuettere(m, ['OK'] + ['SCHWACH'] * 5 + ['OK'])
        self.assertEqual(m.erbe['SCHWACH']['AUSFALL'], 1.5)
        self.assertEqual(m.erbdauer['SCHWACH'][1], 1.5)

    def test_festes_erbe_bleibt_getrennt(self):
        m = Verweildauergedaechtnis(GROBWOERTER, GROBERBE, startwert=False)
        fuettere(m, ['OK', 'SCHWACH', 'OK'])
        self.assertEqual(m.erbe['SCHWACH']['AUSFALL'], 3)

    def test_warnschnittstelle_und_praefix_ohne_zukunft(self):
        spur = ['OK'] + (['SCHWACH'] * 4 + ['AUSFALL'] * 2 + ['OK'] * 8) * 10
        ganz = warnungen(spur, self.modell(), 5)
        kurz = warnungen(spur[:57], self.modell(), 5)
        self.assertEqual(ganz[:57], kurz)
        self.assertEqual(len(ganz), len(spur))
        self.assertTrue(all(not w for w, z in zip(ganz, spur) if z == 'AUSFALL'))

    def test_reine_abfragen_lernen_nichts(self):
        m = self.modell()
        fuettere(m, ['OK', 'SCHWACH', 'AUSFALL'])
        vorher = (repr(m.dauer), repr(m.richtung), m.zustandsumfang())
        for _ in range(10):
            m.kritisch_binnen('OK', 30)
            m.beleg('OK')
        self.assertEqual(vorher, (repr(m.dauer), repr(m.richtung), m.zustandsumfang()))

    def test_ungueltige_folge_wird_nicht_still_geglattet(self):
        m = self.modell()
        m.beobachte(None, 'OK')
        for a, b in [(None, 'OK'), ('SCHWACH', 'OK'), ('OK', 'FREMD')]:
            with self.assertRaises(ValueError):
                m.beobachte(a, b)
        for h in (0, -1, True, 601, 1.5):
            with self.assertRaises(ValueError):
                m.kritisch_binnen('OK', h)

    def test_ungultige_parameter(self):
        for kwargs in ({'erbe': -1}, {'erbe': float('nan')},
                       {'halbwertszeit': 0}, {'halbwertszeit': True}):
            with self.assertRaises(ValueError):
                self.modell(**kwargs)


if __name__ == '__main__':
    unittest.main()

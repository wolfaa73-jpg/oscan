import csv
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import einheitenbootstrap as b
import koerper
import test_labor as referenz


def z(n=10, warn=5, treffer=3, ziel=6):
    return dict(takte=n, auswertbar=n, warntakte=warn, treffertakte=treffer,
                zieltakte=ziel, phasen=1, vorgewarnt=1 if warn else 0)


def kuenstliche_aufnahme(path, falsch=False):
    roh, reize = [], []
    for t in range(240):
        phase = t % 40
        roh.append((520 if phase < 5 else 610 if phase < 8 else 410,
                    50000 if phase < 5 else 10000 if phase < 8 else 300000,
                    50000 if phase < 5 else 250000 if phase < 8 else 10))
        reize.append(6 if phase < 8 else 0)
    g = koerper.ERKUNDUNG
    zeilen = referenz.KoerperTests.geraetezeilen(roh, g, 'erbe', reize)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(koerper.KOPF)
        for t, line in enumerate(zeilen, 1):
            d = koerper.lies_koerperzeile(line.encode())
            d['zeit_ms'] = t * 1000
            if falsch and t == 50:
                d['vorwarnung'] = 1 - d['vorwarnung']
            w.writerow([d[k] if d[k] is not None else '-' for k in koerper.KOPF])
    path.with_suffix('.json').write_text(json.dumps(dict(regel='erbe', intervall_ms=1000,
        grenzen=asdict(g), blick=1, last=None, leck=[4096,12288,5,120],
        bremse=[10,10,300,5,120], beginn='kuenstlich', fortsetzung=None, sichern_alle=0)), encoding='utf-8')


class EinheitenBootstrapTests(unittest.TestCase):
    def test_identische_paare_exakt_null(self):
        rows = [z(10, 5, 3, 6), z(20, 10, 8, 12)]
        result = b.bootstrap(rows, rows, wiederholungen=60)
        for row in result.values():
            self.assertEqual((row['differenz'], row['unten'], row['oben']), (0, 0, 0))

    def test_konstante_differenz_bekannt(self):
        a, ref = [z(10,5,3,6)] * 4, [z(10,2,1,6)] * 4
        r = b.bootstrap(a, ref, wiederholungen=60)['warnanteil']
        self.assertAlmostEqual(r['differenz'], .3)
        self.assertAlmostEqual(r['unten'], .3)
        self.assertAlmostEqual(r['oben'], .3)

    def test_verhaeltnis_der_summen_statt_einheitenprozente(self):
        rows = [z(1,1,1,1), z(9,0,0,1)]
        self.assertEqual(b.quotient(b.addiere(iter(rows)), 'warnanteil'), .1)
        self.assertNotEqual(b.quotient(b.addiere(rows), 'warnanteil'), .5)

    def test_null_warnungen_sind_undefiniert(self):
        r = b.bootstrap([z(10,0,0,6)]*3, [z()]*3, wiederholungen=30)['trefferquote']
        self.assertIsNone(r['differenz'])
        self.assertIsNone(r['unten'])
        self.assertEqual(r['definiert'], 0)
        self.assertEqual(r['status'], 'undefinierte_ziehungen')

    def test_teilweise_undefiniert_wird_nicht_weggefiltert(self):
        rows = [z(10,0,0,6), z()]
        r = b.bootstrap(rows, rows, wiederholungen=100)['trefferquote']
        self.assertGreater(r['definiert'], 0)
        self.assertLess(r['definiert'], 100)
        self.assertIsNone(r['unten'])

    def test_falsche_paarung_wird_verworfen(self):
        for key in ('takte','auswertbar','zieltakte','phasen'):
            a, ref = z(), z()
            ref[key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                b.bootstrap([a], [ref], wiederholungen=10)

    def test_negative_zaehler_und_falsche_anzahl(self):
        with self.assertRaises(ValueError):
            b.bootstrap([z()], [], wiederholungen=10)
        with self.assertRaises(ValueError):
            b.bootstrap([dict(z(), treffertakte=10)], [z()], wiederholungen=10)

    def test_block8_mindestens_zwei_bloecke(self):
        r = b.bootstrap([z()]*15, [z()]*15, 'block8', wiederholungen=30)['warnanteil']
        self.assertEqual(r['status'], 'zu_wenige_einheiten')
        r = b.bootstrap([z()]*16, [z()]*16, 'block8', wiederholungen=30)['warnanteil']
        self.assertEqual((r['unten'], r['oben']), (0,0))

    def test_determinismus_und_lineare_quantile(self):
        a, ref = [z(), z(10,7,4,6)], [z(), z()]
        self.assertEqual(b.bootstrap(a,ref,wiederholungen=40), b.bootstrap(a,ref,wiederholungen=40))
        self.assertEqual(b.quantil([0,10], .025), .25)

    def test_ganze_zyklen_keine_randfragmente(self):
        werte, stufen = [], []
        for t in range(60):
            leck = any(a <= t < a+3 for a in (0,10,20,40,58))
            bremse = any(a <= t < a+2 for a in (5,25,45,57))
            warm = any(a <= t < a+2 for a in (0,15,31,50))
            werte.append(dict(takt=t+1, reiz=2*leck+4*bremse))
            stufen.append(dict(temperatur='TEMP_HOCH' if warm else 'OK', speicher='OK', schleife='OK'))
        u = b.ganze_einheiten(werte, stufen, 5)
        self.assertEqual(u['leck'], [(10,20),(20,40)])
        self.assertEqual(u['bremse'], [(5,25),(25,45)])
        self.assertEqual(u['hitze'], [(15,31),(31,50)])

    def test_ziel_jenseits_einheit_kommt_aus_originalfolge(self):
        woerter = ['OK','SCHWACH','SCHWACH','AUSFALL','OK']
        r = b.zaehle(woerter,[False,True,True,False,False],[True,True,True,False,True],2,1,3)
        self.assertEqual((r['warntakte'], r['treffertakte']), (2,2))

    def test_fruehe_phase_nur_historisch_mit_verkuerztem_vorfenster(self):
        woerter = ['OK'] * 80
        woerter[4:6] = ['SCHWACH', 'AUSFALL']
        warn = [t == 4 for t in range(80)]
        auswertbar = [w != 'AUSFALL' for w in woerter]
        historisch = b.zaehle(woerter, warn, auswertbar, 30, 0, 80, vollstaendig=False)
        voll = b.zaehle(woerter, warn, auswertbar, 30, 0, 80)
        self.assertEqual((historisch['phasen'], historisch['vorgewarnt']), (1, 1))
        self.assertEqual((voll['phasen'], voll['vorgewarnt']), (0, 0))
        for mass in b.MASSE:
            self.assertEqual(b.quotient(historisch, mass), b.quotient(voll, mass))
        werte = [dict(takt=t+1, reiz=koerper.LECK if t in (1,40,70) else 0) for t in range(80)]
        stufen = [dict(temperatur='TEMP_HOCH' if t == 4 else 'TEMP_KRITISCH' if t == 5 else 'OK',
                       speicher='OK', schleife='OK') for t in range(80)]
        ganz, punkte, _, _ = b.auswerten(werte, stufen, 30, wiederholungen=10)
        historisch = next(r for r in ganz if r['signal'] == 'gesamt' and r['verfahren'] == 'Feste Regel')
        voll = next(r for r in punkte if r['art'] == 'leck' and r['signal'] == 'gesamt'
                    and r['verfahren'] == 'Feste Regel')
        self.assertEqual((historisch['phasen'], historisch['vorgewarnt']), (1, 1))
        self.assertEqual((voll['phasen'], voll['vorgewarnt']), (0, 0))

    def test_24h_wird_vor_lesen_oder_hashen_abgewiesen(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('darf nicht lesen')):
            with self.assertRaises(ValueError):
                b.run(Path('koerper-startwert-24h-2026-11-06.csv'), '6h', Path('unbenutzt'))

    def test_kuenstliche_geraeteaufnahme_validierung_und_vergleiche(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d,'kuenstlich-6h.csv')
            kuenstliche_aufnahme(p)
            werte, stufen, h = b.laden(p,'6h')
            ganz, punkte, intervals, units = b.auswerten(werte, stufen, h, wiederholungen=20)
            self.assertTrue(intervals)
            self.assertTrue(units)
            report = b.bericht(ganz, punkte, '6h')
            self.assertIn('Original: 240 Instrumenttakte; davon 210', report)
            self.assertIn('160 von 210 Instrumenttakten (76.19 %)', report)
            for row in ganz + punkte:
                if row['verfahren'] == 'Immer warnen (eigene Signalreferenz)' and row['auswertbar']:
                    self.assertEqual(row['warnanteil'], 1)
                    self.assertEqual(row['trefferquote'], row['grundrate'])
            self.assertTrue(any(r['referenz'] == 'Je Signal, Erbe fest' for r in intervals))
            kuenstliche_aufnahme(p, falsch=True)
            with self.assertRaises(ValueError):
                b.laden(p,'6h')


if __name__ == '__main__':
    unittest.main()

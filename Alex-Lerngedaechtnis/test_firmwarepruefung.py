"""Gezielte Vertragsregressionen; laufen auch gegen einzelne temporaere Mutanten."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import kern
import neustart
import vokabular
from firmwarepruefung import compile_hosts, difference, random_case, run_host, state_bytes


class PythonRegressionen(unittest.TestCase):
    def test_kern_schwelle_inklusive(self):
        g = kern.Erbgedaechtnis({('SCHWACH','AUSFALL'):3.,('SCHWACH','OK'):2.})
        s = kern.Knoten(g).schritt(1,'SCHWACH')
        self.assertEqual(s.anteil, .6)
        self.assertTrue(s.vorwarnung)

    def test_kern_blick_600(self):
        try: k = kern.Knoten(kern.Erbgedaechtnis(),blick=600)
        except ValueError: self.fail('Gueltiger Blick 600 abgewiesen')
        self.assertEqual(k.blick,600)

    def test_kern_luecke_keine_transition(self):
        k=kern.Knoten(kern.Kontextgedaechtnis())
        k.schritt(1,'OK'); k.schritt(3,'SCHWACH')
        self.assertEqual(sum(sum(r.values()) for r in k.gedaechtnis.gewichte.values()),0)

    def test_kern_startwert_bleiben(self):
        k=kern.Knoten(kern.Startwertgedaechtnis())
        k.schritt(1,'SCHWACH'); k.schritt(2,'SCHWACH')
        self.assertEqual(k.gedaechtnis.erbe['SCHWACH']['AUSFALL'],3)

    def test_vokabular_schwelle_inklusive(self):
        class Modell:
            def beobachte(self,a,b): pass
            def beleg(self,w): return 3
            def kritisch_binnen(self,w,h): return .6
        self.assertEqual(vokabular.warnungen(['SCHWACH'],Modell(),1),[True])

    def test_vokabular_horizont_inklusive(self):
        self.assertEqual(vokabular.binnen_vor([False,False,True],2),{0,1})

    def test_vokabular_anfangsphase(self):
        self.assertEqual(vokabular.phasen(['AUSFALL','OK']),[])

    def test_vokabular_startwert_bleiben(self):
        m=vokabular.Wortgedaechtnis(vokabular.GROBWOERTER,vokabular.GROBERBE,startwert=True)
        m.beobachte(None,'SCHWACH');m.beobachte('SCHWACH','SCHWACH')
        self.assertEqual(m.erbe['SCHWACH']['AUSFALL'],3)

    def _json_state(self, directory):
        path=Path(directory)/'state.json'
        k=kern.Knoten(kern.Gedaechtnis());k.schritt(1,'OK')
        neustart.sichern(path,'synthetisch',k)
        return path,json.loads(path.read_bytes())

    def _resign(self,path,document):
        document['sha256']=hashlib.sha256(neustart.kodiert(document['daten'])).hexdigest()
        path.write_bytes(neustart.kodiert(document))

    def test_neustart_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            p,x=self._json_state(d); x['daten']['takt']=2
            p.write_bytes(neustart.kodiert(x))
            with self.assertRaises(ValueError):neustart.laden(p,'synthetisch')

    def test_neustart_quelle(self):
        with tempfile.TemporaryDirectory() as d:
            p,_=self._json_state(d)
            with self.assertRaises(ValueError):neustart.laden(p,'andere-synthetische-quelle')

    def test_neustart_gesamtmasse(self):
        with tempfile.TemporaryDirectory() as d:
            p,x=self._json_state(d)
            x['daten']['gewichte']=[[.75,.75,0],[0,0,0],[0,0,0]]
            self._resign(p,x)
            with self.assertRaises(ValueError):neustart.laden(p,'synthetisch')

    def test_neustart_bool_takt(self):
        with tempfile.TemporaryDirectory() as d:
            p,x=self._json_state(d);x['daten']['takt']=True;self._resign(p,x)
            with self.assertRaises(ValueError):neustart.laden(p,'synthetisch')


class FirmwareRegressionen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='oscan-regression-')
        cls.root=Path(cls.tmp.name)
        cls.binaries=compile_hosts(cls.root)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_cpp_schwelle_inklusive(self):
        k=kern.Knoten(kern.Erbgedaechtnis()); k.takt=10;k.zustand='OK'
        k.gedaechtnis.gewichte['SCHWACH']['OK']=2
        p=self.root/'threshold';p.write_bytes(state_bytes(k,'erbe'))
        self.assertEqual(run_host(self.binaries['erbe'],['LADEN','11,SCHWACH'],p),
                         ['takt,zustand,sofort,vorwarnung','GELADEN','11,SCHWACH,0,1'])

    def test_cpp_blick_600(self):
        self.assertEqual(run_host(self.binaries['erbe'],['BLICK 600'],self.root/'unused')[-1], 'BLICK,ok')

    def test_cpp_startwert_bleiben(self):
        p=self.root/'dwell'
        run_host(self.binaries['startwert'],['1,SCHWACH','2,SCHWACH','SICHERN'],p)
        import struct
        self.assertEqual(struct.unpack_from('<d',p.read_bytes(),82+5*8)[0],3)

    def test_cpp_gesamtmasse(self):
        k=kern.Knoten(kern.Erbgedaechtnis()); k.takt=10;k.zustand='OK'
        k.gedaechtnis.gewichte['OK']['OK']=6
        k.gedaechtnis.gewichte['OK']['SCHWACH']=4.5
        p=self.root/'total';p.write_bytes(state_bytes(k,'erbe'))
        self.assertEqual(run_host(self.binaries['erbe'],['LADEN','1,SCHWACH'],p),
                         ['takt,zustand,sofort,vorwarnung','FEHLER','1,SCHWACH,0,1'])


class HarnessTests(unittest.TestCase):
    def test_deterministische_spur(self):
        a=random_case('erbe',30,730001);b=random_case('erbe',30,730001)
        self.assertEqual(a.commands,b.commands)
        self.assertEqual(a.expected,b.expected)
        self.assertEqual(a.counts['observations'],48)
        self.assertGreater(a.counts['gaps'],0)
        self.assertEqual(a.counts['loads'],1)

    def test_vergleich_erkennt_fehlende_und_zusaetzliche_zeilen(self):
        self.assertEqual(difference(['a','b'],['a'])['mismatch_lines'],1)
        self.assertEqual(difference(['a'],['a','b'])['mismatch_lines'],1)
        self.assertEqual(difference(['a','b'],['b','a'])['mismatch_lines'],2)

    def test_ag01_wird_in_startwert_fehlerfrei_erkannt(self):
        k=kern.Knoten(kern.Erbgedaechtnis());k.schritt(1,'SCHWACH')
        b=state_bytes(k,'erbe')
        self.assertEqual((b[:4],len(b)),(b'AG01',86))


if __name__=='__main__':unittest.main()

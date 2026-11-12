import copy
import csv
from dataclasses import asdict
import json
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
import empfinden as em
import selbstvorhersage as sv
import kunstkoerper as kk
import koerper
import funkversuch as f

ROOT=Path(__file__).parent

from funkversuch_probe import kuenstlich

class FunkversuchTests(unittest.TestCase):
    def test_nullwirkung_bekannte_waerme_und_lineare_drift(self):
        for bereit,send,drift in ((0,0,0),(2,.5,0),(2,.5,.0002),(0,0,.0002)):
            w,e,_=kuenstlich(bereit,send,drift)
            a=f.auswertung(w,e)['temperatur_kontraste_c']
            self.assertAlmostEqual(a['bereit_minus_aus'],bereit,delta=.02)
            self.assertAlmostEqual(a['senden_minus_bereit'],send,delta=.02)

    def test_defekte_vor_jeder_auswertung_abweisen(self):
        w,e,_=kuenstlich()
        for k,value in (('takt',999),('reiz',32),('temp_dc',None)):
            kaputt=copy.deepcopy(w);kaputt[5500][k]=value
            with self.assertRaises(ValueError):f.auswertung(kaputt,e)
        with self.assertRaises(ValueError):f.auswertung(w[:-1],e)
        kaputt=copy.deepcopy(e);kaputt[4]['gueltig']=0
        with self.assertRaises(ValueError):f.auswertung(w,kaputt)

    def test_vollstaendige_csv_nur_pfad(self):
        w,e,v=kuenstlich();g=koerper.Grenzen(380,390,65536,16384,20000,200000)
        k=koerper.Knoten(koerper.REGELN['startwert'](),blick=60)
        meta=dict(regel='startwert',intervall_ms=1000,blick=60,grenzen=asdict(g),fortsetzung=None,sichern_alle=0,
                  funkversuch=dict(version=1,kanal=6,takte=10800),empfinden=dict(zip(koerper.EMPFINDEN_FELDER,em.KONSTANTEN)),
                  vorhersage=dict(zip(koerper.VORHERSAGE_FELDER,sv.KONSTANTEN)))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d,'kunst.csv');p.with_suffix('.json').write_text(json.dumps(meta))
            with p.open('w',newline='') as out:
                c=csv.DictWriter(out,fieldnames=koerper.KOPF);c.writeheader()
                for z in w:
                    z=dict(z);z['zustand']=koerper.einstufen(z['temp_dc'],z['heap'],z['luecke_us'],g)
                    ent=k.schritt(z['takt'],z['zustand']);z['sofort']=int(ent.sofort);z['vorwarnung']=int(ent.vorwarnung);c.writerow(z)
            with p.with_name('kunst.empfinden.csv').open('w',newline='') as out:
                c=csv.DictWriter(out,fieldnames=em.KOPF);c.writeheader();c.writerows(e)
            with p.with_name('kunst.vorhersage.csv').open('w',newline='') as out:
                c=csv.writer(out);c.writerow(sv.KOPF);c.writerows([i]+z['felder'] for i,z in enumerate(v,1))
            a=f.pruefe(p);self.assertAlmostEqual(a['temperatur_kontraste_c']['bereit_minus_aus'],2,delta=.02)
            p.with_name('kunst.abbruch.txt').write_text('Unterbrechung')
            with self.assertRaises(ValueError):f.pruefe(p)

    def test_funkplan_und_reizbits_im_echten_hostsketch(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d,'sketch')
            subprocess.run(['c++','-std=c++11','-DALEX_STARTWERT','-ffp-contract=off',str(ROOT/'esp32/host.cpp'),'-o',str(exe)],check=True)
            befehle=['NEUER_LAUF','GRENZEN 380 390 65536 16384 20000 200000','EMPFINDEN 1','FUNKPLAN 1']
            befehle+=['MESSWERT 370 300000 300']*10800
            aus=subprocess.check_output([str(exe)],input='\n'.join(befehle)+'\n',text=True)
            self.assertNotIn('FEHLER',aus)
            zeilen=[koerper.lies_koerperzeile(z.encode()) for z in aus.splitlines() if z.startswith('K,')]
            self.assertEqual(len(zeilen),10800)
            for i,z in enumerate(zeilen,1):self.assertEqual(z['reiz'],24 if f.modus(i)==2 else 16 if f.modus(i) else 0)

if __name__=='__main__':unittest.main()
